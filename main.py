import os
import sys
import argparse
import threading
import traceback
import ctypes
import subprocess

# --- PATH HACK FOR MODULAR VERSION ---
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
# ------------------------------------

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QDialog
from PyQt6.QtGui import QAction, QIcon, QCursor
from PyQt6.QtCore import Qt, QTimer, QRect, QThread, pyqtSignal

from orbitswipe.core.constants import APP_NAME, APP_VERSION, PACKAGES, IS_FROZEN, LOG_FILE
from orbitswipe.core.config import load_cfg, save_cfg
from orbitswipe.core.utils import _log
from orbitswipe.core.engine import Hotkey
from orbitswipe.ui.launcher import Launcher
from orbitswipe.ui.trigger import Trigger
from orbitswipe.ui.settings import SettingsDlg
from orbitswipe.ui.utils import make_tray_icon
from orbitswipe.ui.dialogs import TrialGateDlg
from orbitswipe.core.license import is_app_allowed
from orbitswipe.installer.setup import run_installer, run_uninstaller

def pkg_ok(imp):
    import importlib.util
    return importlib.util.find_spec(imp) is not None

class LicenseCheckThread(QThread):
    finished_check = pyqtSignal(dict)
    def run(self):
        try:
            from orbitswipe.core.license import check_license_online_silent
            res = check_license_online_silent()
            self.finished_check.emit(res)
        except Exception as e:
            _log(f"LicenseCheckThread error: {e}")

def run_app():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"Magnetieght.OrbitSwipe.MainApp.{APP_VERSION}")
    except Exception:
        pass

    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setWindowIcon(make_tray_icon())

    cfg = load_cfg()
    
    # --- RESTORED: License / Trial Gate ---
    # Security consensus validation at boot-up.
    # Checks local cryptographic dat files and stealth registry mirror.
    if not is_app_allowed():
        gate = TrialGateDlg()
        if gate.exec() != QDialog.DialogCode.Accepted or not is_app_allowed():
            sys.exit(0)
    # --------------------------------------

    launcher = Launcher(cfg)
    triggers = []

    def reposition_all_triggers():
        for t in triggers:
            t._repos()

    def update_triggers():
        for t in triggers:
            t.hide()
            t.deleteLater()
        triggers.clear()
        for screen in QApplication.screens():
            t = Trigger(cfg, screen)
            t.launcher = launcher
            t.on_drop  = launcher.add_any_path
            t.fired.connect(launcher.toggle)
            t.moved.connect(launcher._place)
            t.moved.connect(reposition_all_triggers)
            t.show()
            triggers.append(t)
        launcher._trigger = triggers[0] if triggers else None

    update_triggers()
    qapp.screenAdded.connect(lambda _: update_triggers())
    qapp.screenRemoved.connect(lambda _: update_triggers())

    # Hotkey management
    _hk = [None]
    def _start_hk():
        old = _hk[0]
        if old and old.isRunning(): old.stop(); old.wait(600)
        if cfg.get("hotkey_enabled", True):
            ht = Hotkey(cfg)
            ht.fired.connect(launcher.toggle)
            ht.pin_requested.connect(launcher._toggle_current_window_topmost)
            ht.start(); _hk[0] = ht
    _start_hk()

    if "--first-launch" in sys.argv:
        QTimer.singleShot(500, launcher.toggle)

    tray = QSystemTrayIcon(make_tray_icon(), qapp)
    tray.setToolTip(f"{APP_NAME} v{APP_VERSION} — Edge Launcher")
    tm = QMenu()
    tm.setStyleSheet("""
        QMenu{background:#13132b;color:#e2e8f0;border:1px solid #1e1b4b;
              font-family:'Segoe UI';font-size:10pt; padding: 4px 0px;}
        QMenu::item{padding: 8px 30px 8px 20px;}
        QMenu::item:selected{background:#7c3aed; border-radius: 4px; border: 1px solid #c084fc;}
        QMenu::separator{height:1px;background:#1e1b4b;margin:6px 12px;}
    """)
    
    a1 = QAction("⚡  Open Launcher", qapp); a1.triggered.connect(launcher.toggle); tm.addAction(a1)
    tm.addSeparator()
    
    a2 = QAction("⚙️  Settings", qapp)
    def open_settings():
        launcher._in_dialog = True
        launcher._open_m()
        launcher._settings_dlg = SettingsDlg(cfg, launcher)
        dlg = launcher._settings_dlg
        dlg._on_hotkey_change = _start_hk
        def on_done():
            launcher._in_dialog = False
            launcher._settings_dlg = None
            reposition_all_triggers()
            _start_hk()
        dlg.finished.connect(lambda _: on_done())
        dlg.show(); dlg.raise_(); dlg.activateWindow()
    a2.triggered.connect(open_settings); tm.addAction(a2)
    launcher.open_settings_callback = open_settings
    
    a3 = QAction("🔄  Switch Side", qapp)
    def sw():
        cfg["side"] = "left" if cfg["side"]=="right" else "right"
        save_cfg(cfg); reposition_all_triggers(); launcher._place(); launcher.update()
    a3.triggered.connect(sw); tm.addAction(a3)
    tm.addSeparator()
    
    # ─── RESTORED: Silent Background Online Sync & Grace Period ───
    lic_thread = LicenseCheckThread(qapp)
    
    def on_license_check_done(res):
        from orbitswipe.core.license import is_app_allowed
        if res.get("status") in ("revoked", "offline_expired") or not is_app_allowed():
            _log(f"Silent verification lock triggered: status={res.get('status')}. Deactivating.")
            launcher.hide()
            for t in triggers:
                t.hide()
            gate = TrialGateDlg()
            if gate.exec() != QDialog.DialogCode.Accepted or not is_app_allowed():
                qapp.quit()
            else:
                # Successfully reactivated, restore triggers
                update_triggers()

    lic_thread.finished_check.connect(on_license_check_done)

    def trigger_silent_check():
        from orbitswipe.core.license import get_license_status
        if get_license_status()["licensed"] and not lic_thread.isRunning():
            _log("Starting silent background online license verification check...")
            lic_thread.start()

    # Startup Silent Check (Runs 1 second after launcher initialization)
    QTimer.singleShot(1000, trigger_silent_check)

    # Periodic Check (Runs every 6 hours)
    periodic_timer = QTimer(qapp)
    periodic_timer.timeout.connect(trigger_silent_check)
    periodic_timer.start(6 * 3600 * 1000)
    # -------------------------------------------------------------

    a4 = QAction("✕  Quit OrbitSwipe", qapp)
    def quit_all():
        ht = _hk[0]
        if ht: ht.stop()
        try: launcher._stats.stop()
        except Exception: pass
        try: launcher._vol_worker.stop()
        except Exception: pass
        qapp.quit()
    a4.triggered.connect(quit_all); tm.addAction(a4)
    
    tray.setContextMenu(tm)
    tray.activated.connect(
        lambda r: launcher.toggle()
        if r == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()
    
    sys.exit(qapp.exec())

if __name__ == "__main__":
    hw = ctypes.windll.kernel32.GetConsoleWindow()
    if hw: ctypes.windll.user32.ShowWindow(hw, 0)

    if IS_FROZEN:
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        pkpath = os.path.join(base, "PyQt6", "Qt6", "plugins")
        if os.path.exists(pkpath):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = pkpath

    if "--uninstall" in sys.argv:
        run_uninstaller()
    elif "--run" in sys.argv:
        if not IS_FROZEN:
            missing = [(p,i) for p,i in PACKAGES if not pkg_ok(i)]
            if missing:
                _log(f"Auto-installing: {[p for p,_ in missing]}")
                for pname,_ in missing:
                    try:
                        try: subprocess.run(["py", "-m", "pip", "install", pname, "--quiet"],
                                            check=True, creationflags=0x08000000)
                        except: subprocess.run([sys.executable, "-m", "pip", "install", pname, "--quiet"],      
                                               check=True, creationflags=0x08000000)
                    except Exception: pass
        try:
            run_app()
        except Exception as e:
            _log(f"FATAL run_app: {e}\\n{traceback.format_exc()}")
            try:
                import tkinter.messagebox as mb
                mb.showerror("OrbitSwipe crashed", f"{e}\\n\\nCheck {LOG_FILE}")
            except Exception: pass
    else:
        # If running the executable directly from the installation directory, launch the app instead of the installer
        from orbitswipe.core.constants import APPDATA_DIR
        is_installed_dir = False
        if IS_FROZEN:
            exe_path = os.path.abspath(sys.argv[0])
            if exe_path.lower().startswith(APPDATA_DIR.lower()):
                is_installed_dir = True

        if is_installed_dir:
            try:
                run_app()
            except Exception as e:
                _log(f"FATAL run_app: {e}\\n{traceback.format_exc()}")
                try:
                    import tkinter.messagebox as mb
                    mb.showerror("OrbitSwipe crashed", f"{e}\\n\\nCheck {LOG_FILE}")
                except Exception: pass
        else:
            result = run_installer()
            if result and result.get("launch") and result.get("install_path"):
                path    = result["install_path"]
                new_exe = os.path.join(path, "OrbitSwipe.exe")
                if os.path.exists(new_exe):
                    subprocess.Popen([new_exe, "--run", "--first-launch"], cwd=path, creationflags=0x08000000)      
                else:
                    subprocess.Popen([sys.executable, __file__, "--run", "--first-launch"], creationflags=0x08000000)
