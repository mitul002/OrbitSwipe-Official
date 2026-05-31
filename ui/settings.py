import os
import sys
import json
import time
import math
import winreg
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QPushButton, QLineEdit, QCheckBox, 
                             QSlider, QFrame, QListWidget, QStackedWidget, 
                             QScrollArea, QListWidgetItem, QGridLayout, 
                             QRadioButton, QFileDialog, QColorDialog,
                             QApplication, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QPointF, QTimer, QThread, QEvent, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QBrush, QPen

from orbitswipe.core.constants import APP_NAME, APP_VERSION, DEFAULT_CFG, GLASS_PRESETS, ALL_TOOLS, TRIAL_DAYS
from orbitswipe.core.config import save_cfg
from orbitswipe.core.license import get_license_status, activate_license, deactivate_license
from orbitswipe.core.utils import _log
from orbitswipe.ui.utils import make_tray_icon
from orbitswipe.ui.dialogs import AddUrlDlg, AddScriptDlg

class HotkeyRecorder(QPushButton):
    changed = pyqtSignal(str, str)
    def __init__(self, mod, key, parent=None):
        super().__init__(parent)
        self._mod = mod; self._key = key; self._rec = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._upd(); self.setFixedHeight(32)

    def _upd(self):
        txt = f"{self._mod} + {self._key}" if not self._rec else "PRESS ANY KEY…"
        self.setText(txt)
        self.setStyleSheet(
            f"QPushButton{{background:{'#7c3aed' if self._rec else '#1e1b4b'};"
            "color:white;border:1px solid #7c3aed;border-radius:6px;font-weight:bold;"
            "padding: 0 15px; min-width: 100px;}}"
            "QPushButton:hover{background:#6d28d9;}")

    def mousePressEvent(self, e):
        self._rec = True; self._upd(); self.setFocus()
        super().mousePressEvent(e)

    def keyPressEvent(self, e):
        if not self._rec: 
            super().keyPressEvent(e)
            return
        from PyQt6.QtGui import QKeySequence
        k = e.key()
        if k in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta): return
        m = e.modifiers(); ms = []
        if m & Qt.KeyboardModifier.ControlModifier: ms.append("Ctrl")
        if m & Qt.KeyboardModifier.AltModifier:     ms.append("Alt")
        if m & Qt.KeyboardModifier.ShiftModifier:   ms.append("Shift")
        if m & Qt.KeyboardModifier.MetaModifier:    ms.append("Win")
        self._mod = "+".join(ms) if ms else "Alt"
        kn = QKeySequence(k).toString().upper()
        if not kn: kn = "S"
        self._key = kn; self._rec = False; self._upd()
        self.changed.emit(self._mod, self._key)

def _build_license_tab(layout, parent_dlg):
    """Builds the License settings page inline."""
    from PyQt6.QtWidgets import QProgressBar, QFrame
    from PyQt6.QtCore    import QThread, pyqtSignal as _sig
    class _ActWorker(QThread):
        done = _sig(dict)
        def __init__(self, key, email=None, request_transfer=False):
            super().__init__()
            self._key = key
            self._email = email
            self._req_trans = request_transfer
        def run(self):
            self.done.emit(activate_license(self._key, email=self._email, request_transfer=self._req_trans))
    status = get_license_status()
    trial  = status["trial"]
    # ── Status card ────────────────────────────────────────────────
    card = QWidget(); card.setObjectName("lic_card")
    card.setStyleSheet("""
        QWidget#lic_card {
            background: rgba(30, 27, 75, 180);
            border: 1.5px solid #3b2070; border-radius: 14px;
        }
        QLabel { border: none; }
    """)
    cl = QVBoxLayout(card); cl.setContentsMargins(20,16,20,16); cl.setSpacing(8)
    sr = QHBoxLayout()
    _icon_lbl = QLabel("🔒"); _icon_lbl.setFont(QFont("Segoe UI Emoji", 26))
    _icon_lbl.setStyleSheet("border:none;")
    sr.addWidget(_icon_lbl); sr.addSpacing(10)
    tc = QVBoxLayout()
    _title_lbl = QLabel("Loading…")
    _title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    _title_lbl.setStyleSheet("color:white;border:none;")
    _sub_lbl = QLabel(""); _sub_lbl.setStyleSheet("color:#94a3b8;font-size:9.5pt;border:none;")
    _sub_lbl.setWordWrap(True)
    tc.addWidget(_title_lbl); tc.addWidget(_sub_lbl)
    sr.addLayout(tc); sr.addStretch(); cl.addLayout(sr)
    _trial_w = QWidget()
    tw = QVBoxLayout(_trial_w); tw.setContentsMargins(0,6,0,0); tw.setSpacing(4)
    pr = QHBoxLayout()
    _prog_lbl = QLabel("Trial period:")
    _prog_lbl.setStyleSheet("color:#a78bfa;font-size:9pt;border:none;")
    _days_lbl = QLabel("")
    _days_lbl.setStyleSheet("color:#e2e8f0;font-size:9pt;font-weight:bold;border:none;")
    pr.addWidget(_prog_lbl); pr.addStretch(); pr.addWidget(_days_lbl)
    tw.addLayout(pr)
    _trial_bar = QProgressBar()
    _trial_bar.setRange(0, 100); _trial_bar.setFixedHeight(7); _trial_bar.setTextVisible(False)
    _trial_bar.setStyleSheet("""
        QProgressBar{background:#1e1b4b;border-radius:3px;border:none;}
        QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #7c3aed,stop:1 #a78bfa);border-radius:3px;}
    """)
    tw.addWidget(_trial_bar); cl.addWidget(_trial_w)
    layout.addWidget(card)
    sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet("background:rgba(255,255,255,0.07);max-height:1px;margin:6px 0;")
    layout.addWidget(sep)
    # ── Key input section ─────────────────────────────────────────
    hdr = QLabel("License Key")
    hdr.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    hdr.setStyleSheet("color:#a78bfa;border:none;margin-top:2px;")
    layout.addWidget(hdr)
    hint = QLabel("Enter your license key to unlock OrbitSwipe permanently.\nGet a key at orbitswipe.vercel.app")
    hint.setStyleSheet("color:#64748b;font-size:9pt;border:none;"); hint.setWordWrap(True)
    layout.addWidget(hint)
    _key_edit = QLineEdit(); _key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
    _key_edit.setMaxLength(36)
    _key_edit.setStyleSheet(
        "QLineEdit{background:#0e0c20;color:#e2e8f0;border:1.5px solid #7c3aed;"
        "border-radius:8px;padding:10px 14px;font-family:'Segoe UI';font-size:10.5pt;"
        "min-height:36px;letter-spacing:2px;}"
        "QLineEdit:focus{border-color:#a78bfa;}"
    )
    layout.addWidget(_key_edit)
    
    # ── Email input section ──
    hdr_email = QLabel("Email Address")
    hdr_email.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    hdr_email.setStyleSheet("color:#a78bfa;border:none;margin-top:6px;")
    layout.addWidget(hdr_email)
    
    _email_edit = QLineEdit(); _email_edit.setPlaceholderText("yourname@email.com")
    _email_edit.setStyleSheet(
        "QLineEdit{background:#0e0c20;color:#e2e8f0;border:1.5px solid #7c3aed;"
        "border-radius:8px;padding:10px 14px;font-family:'Segoe UI';font-size:10.5pt;"
        "min-height:36px;}"
        "QLineEdit:focus{border-color:#a78bfa;}"
    )
    layout.addWidget(_email_edit)
    btn_row  = QHBoxLayout(); btn_row.setSpacing(8)
    _act_btn = QPushButton("  ✅  Activate License")
    _act_btn.setFixedHeight(40)
    _act_btn.setStyleSheet(
        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        "stop:0 #7c3aed,stop:1 #4c1d95);color:white;border-radius:8px;"
        "border:none;font-size:10.5pt;font-weight:bold;}"
        "QPushButton:hover{background:#6d28d9;}"
        "QPushButton:disabled{background:#2a1f4a;color:#555;}"
    )
    
    _transfer_btn = QPushButton("  🔄  Request Transfer")
    _transfer_btn.setFixedHeight(40)
    _transfer_btn.setStyleSheet(
        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        "stop:0 #7c3aed,stop:1 #6d28d9);color:white;border-radius:8px;"
        "border:none;font-size:10pt;font-weight:bold;}"
        "QPushButton:hover{background:#5b21b6;}"
        "QPushButton:disabled{background:#1e1b4b;color:#475569;}"
    )
    _transfer_btn.hide()

    _deact_btn = QPushButton("Deactivate")
    _deact_btn.setFixedHeight(36)
    _deact_btn.setStyleSheet(
        "QPushButton{background:transparent;color:#ef4444;border:1px solid #ef4444;"
        "border-radius:6px;padding:6px 14px;font-size:9pt;}"
        "QPushButton:hover{background:#450a0a;}"
    )
    
    btn_row.addWidget(_act_btn, 3)
    btn_row.addWidget(_transfer_btn, 3)
    btn_row.addWidget(_deact_btn, 1)
    layout.addLayout(btn_row)
    
    _msg_lbl = QLabel(""); _msg_lbl.setWordWrap(True)
    _msg_lbl.setStyleSheet("font-size:9.5pt;border:none;margin-top:2px;")
    layout.addWidget(_msg_lbl)
    layout.addStretch()
    _worker = [None]
    def _update():
        st = get_license_status(); tr = st["trial"]
        if st["licensed"]:
            _icon_lbl.setText("✅")
            _title_lbl.setText(f"Licensed — {st['plan']} Plan")
            _title_lbl.setStyleSheet("color:#22c55e;border:none;")
            lic_type = st.get("license_type", "lifetime")
            if lic_type == "annual":
                _sub_lbl.setText(f"Key: {st['key_preview']}  •  Annual License (renews yearly)")
            else:
                _sub_lbl.setText(f"Key: {st['key_preview']}  •  Lifetime License")
            _trial_w.hide(); _deact_btn.show()
        elif tr["expired"]:
            _icon_lbl.setText("🔒")
            _title_lbl.setText("Trial Expired")
            _title_lbl.setStyleSheet("color:#ef4444;border:none;")
            _sub_lbl.setText("Activate a license key to continue using OrbitSwipe.")
            _days_lbl.setText("0 days left"); _trial_bar.setValue(0)
            _trial_w.show(); _deact_btn.hide()
        else:
            sl = tr["sec_left"]
            d = int(sl / 86400)
            h = int((sl % 86400) / 3600)
            m = int((sl % 3600) / 60)
            
            time_str = f"{d}d {h}h {m}m" if d > 0 else f"{h}h {m}m"
            
            _icon_lbl.setText("⏳")
            _title_lbl.setText(f"Free Trial — {time_str} remaining")
            _title_lbl.setStyleSheet("color:#a78bfa;border:none;")
            _sub_lbl.setText("Activate a license to remove this limitation.")
            
            # Format trial time string down to minutes precisely
            if d > 0:
                detailed_str = f"{d} days {h}h {m}m"
            else:
                detailed_str = f"{h}h {m}m"

            _days_lbl.setText(f"{detailed_str} left")
            
            # Compute precise percentage using seconds for smooth progression
            total_sec = TRIAL_DAYS * 86400
            elapsed_sec = max(0, total_sec - sl)
            percent = int((elapsed_sec / total_sec) * 100) if total_sec > 0 else 0
            _trial_bar.setValue(max(0, min(100, percent)))
            _trial_w.show(); _deact_btn.hide()
    _update()
    def _on_activate():
        key = _key_edit.text().strip()
        email = _email_edit.text().strip()
        if not key:
            _msg_lbl.setText("⚠️  Please enter a license key.")
            _msg_lbl.setStyleSheet("color:#f59e0b;font-size:9.5pt;border:none;"); return
        if not email or "@" not in email or "." not in email:
            _msg_lbl.setText("⚠️  Please enter a valid email address.")
            _msg_lbl.setStyleSheet("color:#f59e0b;font-size:9.5pt;border:none;"); return
        _act_btn.setEnabled(False); _act_btn.setText("  ⏳  Validating…"); _msg_lbl.setText("")
        
        is_refresh_mode = "Refresh" in _transfer_btn.text() or "REFRESH" in _transfer_btn.text()
        if not is_refresh_mode:
            _transfer_btn.hide()
        else:
            _transfer_btn.setEnabled(False); _transfer_btn.setText("  ⏳  Refreshing…")
            
        w = _ActWorker(key, email=email); _worker[0] = w
        def _done(r):
            _act_btn.setEnabled(True); _act_btn.setText("  ✅  Activate License")
            if is_refresh_mode:
                _transfer_btn.setEnabled(True); _transfer_btn.setText("  🔄  Refresh Status")
            if r.get("valid"):
                _msg_lbl.setText("🎉  " + r.get("message", "Activated!"))
                _msg_lbl.setStyleSheet("color:#22c55e;font-size:9.5pt;border:none;")
                pending_file = getattr(parent_dlg, '_pending_file', None)
                if pending_file and os.path.exists(pending_file):
                    try:
                        os.remove(pending_file)
                    except Exception:
                        pass
                _key_edit.clear(); _email_edit.clear(); _update()
            else:
                msg = r.get("message", "Activation failed.")
                if r.get("transfer_pending"):
                    _msg_lbl.setText("⏳ " + msg)
                    _msg_lbl.setStyleSheet("color:#f59e0b;font-size:9.5pt;border:none;")
                elif is_refresh_mode and (r.get("can_request_transfer") or "registered to a different device" in msg or "Request a transfer" in msg or "registered to another PC" in msg or "submit a transfer request" in msg or "already in use" in msg):
                    _msg_lbl.setText("❌ Transfer request was rejected by admin. You can submit a new request.")
                    _msg_lbl.setStyleSheet("color:#ef4444;font-size:9.5pt;border:none;")
                    # Restore request transfer button back to purple
                    _transfer_btn.setText("  🔄  Request Transfer")
                    _transfer_btn.setStyleSheet(
                        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                        "stop:0 #7c3aed,stop:1 #6d28d9);color:white;border-radius:8px;"
                        "border:none;font-size:10pt;font-weight:bold;}"
                        "QPushButton:hover{background:#5b21b6;}"
                        "QPushButton:disabled{background:#1e1b4b;color:#475569;}"
                    )
                    if os.path.exists(parent_dlg._pending_file):
                        try:
                            os.remove(parent_dlg._pending_file)
                        except Exception:
                            pass
                else:
                    _msg_lbl.setText("❌  " + msg)
                    _msg_lbl.setStyleSheet("color:#ef4444;font-size:9.5pt;border:none;")
                    if r.get("can_request_transfer") and not is_refresh_mode:
                        _transfer_btn.show()
        w.done.connect(_done); w.start()
        
    def _on_request_transfer():
        key = _key_edit.text().strip() or (get_license_status()["key_preview"] if get_license_status()["licensed"] else "")
        email = _email_edit.text().strip()
        if not key or not email:
            # Fallback if fields got cleared, grab original inputs
            _msg_lbl.setText("⚠️  Please make sure license key and email are filled.")
            _msg_lbl.setStyleSheet("color:#f59e0b;font-size:9.5pt;border:none;"); return
            
        # If already transformed into a refresh button, just call activate check!
        if "REFRESH" in _transfer_btn.text() or "Refresh" in _transfer_btn.text():
            _on_activate()
            return
            
        _transfer_btn.setEnabled(False); _transfer_btn.setText("  ⏳  Submitting Request…")
        w = _ActWorker(key, email=email, request_transfer=True); _worker[0] = w
        def _done(r):
            _transfer_btn.setEnabled(True)
            if r.get("valid"):
                _msg_lbl.setText("🎉  " + r.get("message"))
                _msg_lbl.setStyleSheet("color:#22c55e;font-size:9.5pt;border:none;")
                
                # Save pending status locally
                try:
                    with open(parent_dlg._pending_file, "w") as f:
                        json.dump({"key": key, "email": email, "transfer_requested": True}, f)
                except Exception as e:
                    _log(f"Failed to cache pending transfer status: {e}")
                
                # Transform the button into a premium green REFRESH STATUS button!
                _transfer_btn.setText("  🔄  Refresh Status")
                _transfer_btn.setStyleSheet(
                    "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 #22c55e, stop:1 #15803d); color:white; border-radius:8px;"
                    "border:none; font-size:10pt; font-weight:bold;}"
                    "QPushButton:hover{background:#22c55e;}"
                )
            else:
                _transfer_btn.setText("  🔄  Request Transfer")
                _msg_lbl.setText("❌  " + r.get("message", "Transfer request failed."))
                _msg_lbl.setStyleSheet("color:#ef4444;font-size:9.5pt;border:none;")
        w.done.connect(_done); w.start()
        
    def _on_deactivate():
        deactivate_license(); _update()
        _transfer_btn.hide()
        _msg_lbl.setText("License removed from this device.")
        _msg_lbl.setStyleSheet("color:#94a3b8;font-size:9.5pt;border:none;")
    _act_btn.clicked.connect(_on_activate)
    _transfer_btn.clicked.connect(_on_request_transfer)
    _deact_btn.clicked.connect(_on_deactivate)
    _key_edit.returnPressed.connect(_on_activate)
    
    # Automatically pre-fill pending transfer if cached locally
    if os.path.exists(parent_dlg._pending_file):
        try:
            with open(parent_dlg._pending_file, "r") as f:
                pending = json.load(f)
            p_key = pending.get("key", "")
            p_email = pending.get("email", "")
            if p_key and p_email:
                _key_edit.setText(p_key)
                _email_edit.setText(p_email)
                _transfer_btn.setText("  🔄  Refresh Status")
                _transfer_btn.setStyleSheet(
                    "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 #22c55e, stop:1 #15803d); color:white; border-radius:8px;"
                    "border:none; font-size:10pt; font-weight:bold;}"
                    "QPushButton:hover{background:#22c55e;}"
                )
                _transfer_btn.show()
        except Exception:
            pass
# ══════════════════════════════════════════════════════════════════════════
#  TRIAL GATE DIALOG  (shown when trial expires and no license present)
# ══════════════════════════════════════════════════════════════════════════


class SettingsDlg(QDialog):
    def __init__(self, cfg, launcher, parent=None):
        super().__init__(parent,
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.cfg = cfg; self.launcher = launcher
        self.setWindowIcon(make_tray_icon())
        self.setFixedSize(720, 570)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        sc = QApplication.primaryScreen().availableGeometry()
        self.move(max(0,(sc.width()-720)//2), max(0,(sc.height()-570)//2))
        self._on_hotkey_change = None
        
        from orbitswipe.core.constants import APPDATA_DIR
        self._pending_file = os.path.normpath(os.path.join(APPDATA_DIR, "pending_transfer.json"))
        
        self._build()
        self.setMouseTracking(True)
        self.setWindowOpacity(0.0)

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_in_show_anim", False):
            self.animate_show()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isMinimized() and self.windowOpacity() < 1.0:
                self.animate_show()
        super().changeEvent(event)

    def animate_show(self):
        self._in_show_anim = True
        self.setWindowOpacity(0.0)
        
        g = self.geometry()
        self.setGeometry(QRect(g.x(), g.y() + 30, g.width(), g.height()))
        
        self._show_anim = QPropertyAnimation(self, b"windowOpacity")
        self._show_anim.setDuration(220)
        self._show_anim.setStartValue(0.0)
        self._show_anim.setEndValue(1.0)
        self._show_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._show_geom = QPropertyAnimation(self, b"geometry")
        self._show_geom.setDuration(220)
        self._show_geom.setStartValue(self.geometry())
        self._show_geom.setEndValue(g)
        self._show_geom.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._show_group = QParallelAnimationGroup()
        self._show_group.addAnimation(self._show_anim)
        self._show_group.addAnimation(self._show_geom)
        
        def done():
            self._in_show_anim = False
            
        self._show_group.finished.connect(done)
        self._show_group.start()

    def animate_minimize(self):
        if getattr(self, "_is_minimizing", False):
            return
        self._is_minimizing = True
        
        g = self.geometry()
        self._min_anim = QPropertyAnimation(self, b"windowOpacity")
        self._min_anim.setDuration(180)
        self._min_anim.setStartValue(1.0)
        self._min_anim.setEndValue(0.0)
        self._min_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._min_geom = QPropertyAnimation(self, b"geometry")
        self._min_geom.setDuration(180)
        self._min_geom.setStartValue(g)
        self._min_geom.setEndValue(QRect(g.x(), g.y() + 30, g.width(), g.height()))
        self._min_geom.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._min_group = QParallelAnimationGroup()
        self._min_group.addAnimation(self._min_anim)
        self._min_group.addAnimation(self._min_geom)
        
        def done():
            self.showMinimized()
            self._is_minimizing = False
            self.setWindowOpacity(1.0)
            self.setGeometry(g)
            
        self._min_group.finished.connect(done)
        self._min_group.start()

    def animate_close(self):
        if getattr(self, "_is_closing", False):
            return
        self._is_closing = True
        
        g = self.geometry()
        self._close_anim = QPropertyAnimation(self, b"windowOpacity")
        self._close_anim.setDuration(180)
        self._close_anim.setStartValue(1.0)
        self._close_anim.setEndValue(0.0)
        self._close_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._close_geom = QPropertyAnimation(self, b"geometry")
        self._close_geom.setDuration(180)
        self._close_geom.setStartValue(g)
        self._close_geom.setEndValue(QRect(g.x(), g.y() + 30, g.width(), g.height()))
        self._close_geom.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._close_group = QParallelAnimationGroup()
        self._close_group.addAnimation(self._close_anim)
        self._close_group.addAnimation(self._close_geom)
        
        def done():
            self.close()
            self._is_closing = False
            
        self._close_group.finished.connect(done)
        self._close_group.start()

    def mousePressEvent(self, e):
        self.setFocus()
        if e.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "header") and self.header.geometry().contains(e.pos()):
                self._drag_pos = e.globalPosition().toPoint()
            else:
                self._drag_pos = None
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if hasattr(self, "_drag_pos") and self._drag_pos:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def _get_startup_status(self):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_READ)
            winreg.QueryValueEx(k, APP_NAME); winreg.CloseKey(k); return True
        except: return False

    def _set_startup(self, enable):
        try:
            import shutil
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_SET_VALUE)
            if enable:
                if getattr(sys, 'frozen', False):
                    target_path = sys.executable
                    cmd = f'"{target_path}" --run --silent'
                else:
                    install_path = self.cfg.get("InstallPath")
                    if not install_path:
                        try:
                            rk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}", 0, winreg.KEY_READ)
                            install_path, _ = winreg.QueryValueEx(rk, "InstallPath")
                            winreg.CloseKey(rk)
                        except:
                            install_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    
                    launcher_py = os.path.join(install_path, "launcher.py")
                    if not os.path.exists(launcher_py):
                        launcher_py = os.path.join(install_path, "main.py")
                        
                    target_path = "pyw.exe" if shutil.which("pyw.exe") else "py.exe"
                    cmd = f'"{target_path}" "{launcher_py}" --run --silent'
                
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, cmd)
                _log(f"Autostart configured successfully: {cmd}")
            else:
                try: winreg.DeleteValue(k, APP_NAME)
                except: pass
            winreg.CloseKey(k)
        except Exception as e: _log(f"startup toggle err: {e}")

    def _build(self):
        from PyQt6.QtWidgets import (QListWidget, QStackedWidget, QScrollArea, QScroller)
        
        # --- MAIN LAYOUT ---
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        # --- HEADER ---
        self.header = QWidget(); self.header.setObjectName("header")
        self.header.setFixedHeight(64)
        self.header.setStyleSheet(
            "#header{background:rgba(19, 19, 43, 240); border-top-left-radius:18px;"
            " border-top-right-radius:18px; border:1.5px solid #2e1065; border-bottom:none;}")
        header_layout = QHBoxLayout(self.header); header_layout.setContentsMargins(20,0,20,0)

        logo = QLabel()
        icon = make_tray_icon()
        if icon: logo.setPixmap(icon.pixmap(28, 28))
        header_layout.addWidget(logo)
        
        t = QLabel("OrbitSwipe Settings")
        t.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        t.setStyleSheet("color:white; border:none; margin-left:8px;")
        header_layout.addWidget(t); header_layout.addStretch()
        
        min_btn = QPushButton("—")
        min_btn.setFixedSize(22, 22)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setStyleSheet(
            "QPushButton{background:transparent; color:#94a3b8; font-size:9.5pt; font-weight:bold; border:none;}"
            "QPushButton:hover{color:#3b82f6;}"
        )
        min_btn.clicked.connect(self.animate_minimize)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent; color:#94a3b8; font-size:9.5pt; font-weight:bold; border:none;}"
            "QPushButton:hover{color:#ef4444;}"
        )
        close_btn.clicked.connect(self.animate_close)
        
        header_layout.addWidget(min_btn)
        header_layout.addWidget(close_btn)
        outer.addWidget(self.header)

        # --- CONTENT AREA (Sidebar + Stack) ---
        main_area = QWidget(); main_area.setObjectName("main_area")
        main_area.setStyleSheet(
            "#main_area{background:rgba(19, 19, 43, 100); border:1.5px solid #2e1065; border-top:none;"
            "border-bottom-left-radius:18px; border-bottom-right-radius:18px;}")
        main_layout = QHBoxLayout(main_area); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background: rgba(11, 11, 24, 225); border: none; outline: none; padding-top: 10px;
                border-bottom-left-radius: 16px;
            }
            QListWidget::item {
                color: #cbd5e1; padding: 15px 24px; border-radius: 0px;
                font-family: 'Segoe UI Semibold', 'Segoe UI'; font-weight: 600; font-size: 10.5pt;
            }
            QListWidget::item:selected {
                background: #1e1b4b; color: #a78bfa; border-left: 4px solid #7c3aed;
                font-weight: 700;
            }
            QListWidget::item:hover:!selected {
                background: #161630; color: #f1f5f9;
            }
        """)
        main_layout.addWidget(self.sidebar)

        # Stacked Widget
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        outer.addWidget(main_area)

        # ── Shared widget helpers ────────────────────────────────────────────
        CONTENT_SS = """
            QLabel{color:#e2e8f0;font-family:'Segoe UI';border:none;}
            QPushButton{border-radius:8px;font-family:'Segoe UI';font-weight:bold;border:none;}
            QSlider::groove:horizontal{background:#1e1b4b;height:6px;border-radius:3px;}
            QSlider::handle:horizontal{background:#7c3aed;width:14px;height:14px;
                border-radius:7px;margin:-4px 0;}
            QSlider::sub-page:horizontal{background:#7c3aed;border-radius:3px;}
            QCheckBox{color:#e2e8f0;font-family:'Segoe UI';}
            QCheckBox::indicator{width:16px;height:16px;border-radius:4px;
                border:1.5px solid #7c3aed;background:#1e1b4b;}
            QCheckBox::indicator:checked{background:#7c3aed;}
        """

        # --- PAGE HELPERS ---
        def create_page():
            scroll = QScrollArea(); scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # Custom ScrollBar styling
            scroll.verticalScrollBar().setStyleSheet("""
                QScrollBar:vertical { width: 6px; background: transparent; }
                QScrollBar::handle:vertical { background: #2e1065; border-radius: 3px; }
                QScrollBar::handle:vertical:hover { background: #7c3aed; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """)
            
            content = QWidget(); content.setObjectName("page_content")
            # Apply semi-transparent glass effect to the content area
            content.setStyleSheet("""
                #page_content {
                    background: rgba(11, 11, 24, 0.7);
                    border-bottom-right-radius: 16px;
                }
            """ + CONTENT_SS)
            layout = QVBoxLayout(content); layout.setContentsMargins(20, 12, 20, 12); layout.setSpacing(10)
            scroll.setWidget(content)
            return scroll, layout

        def add_tab(name, icon):
            item = QListWidgetItem(f"{icon}  {name}")
            self.sidebar.addItem(item)
            page, layout = create_page()
            self.stack.addWidget(page)
            return layout

        def section(layout, txt):
            l = QLabel(txt.upper()); l.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            l.setStyleSheet("color:#a78bfa;margin-top:10px;margin-bottom:1px;letter-spacing:0.5px;")
            layout.addWidget(l)

        def divider(layout):
            s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
            s.setStyleSheet("background:rgba(255,255,255,0.1);max-height:1px;margin:4px 0px;")
            layout.addWidget(s)

        def slrow(layout, lbl, lo, hi, val, fn):
            r = QHBoxLayout(); r.addWidget(QLabel(lbl))
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo,hi); sl.setValue(val)
            sl.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
            sl.setStyleSheet("""
                QSlider::groove:horizontal { background: #1e1b4b; height: 6px; border-radius: 3px; }
                QSlider::handle:horizontal { background: #7c3aed; width: 14px; height: 14px; border-radius: 7px; margin: -4px 0; }
                QSlider::sub-page:horizontal { background: #7c3aed; border-radius: 3px; }
            """)
            def _we(e):
                if sl.hasFocus():
                    delta = e.angleDelta().y(); step = 1 if delta > 0 else -1
                    sl.setValue(sl.value() + step); e.accept()
                else: e.ignore()
            sl.wheelEvent = _we
            sl.valueChanged.connect(fn); r.addWidget(sl); layout.addLayout(r)

        def chk_box(lbl, val, fn):
            cb = QCheckBox(lbl); cb.setChecked(val)
            cb.setStyleSheet("""
                QCheckBox { color: #e2e8f0; font-family: 'Segoe UI'; spacing: 8px; border: none; }
                QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1.5px solid #7c3aed; background: #1e1b4b; }
                QCheckBox::indicator:checked { background: #7c3aed; }
            """)
            cb.stateChanged.connect(fn); return cb

        def chk(layout, lbl, val, fn):
            layout.addWidget(chk_box(lbl, val, fn))

        # --- TAB 1: LAYOUT ---
        l1 = add_tab("Layout", "📐")
        section(l1, "🖥️  Trigger Position")
        
        sr = QHBoxLayout(); sr.setSpacing(10); sr.addWidget(QLabel("Trigger Side:"))
        bs = QPushButton("Switch ("+self.cfg["side"].capitalize()+")")
        bs.setFixedSize(140,30)
        bs.setCursor(Qt.CursorShape.PointingHandCursor)
        bs.setStyleSheet(
            f"QPushButton{{background:{self.cfg.get('theme_color','#4c1d95')};"
            "color:white;border-radius:6px;font-weight:bold;}}"
            "QPushButton:hover{background:#374151;}")
        def sw():
            ns = "left" if self.cfg["side"]=="right" else "right"
            self.cfg["side"] = ns; save_cfg(self.cfg)
            self.launcher._place()
            if hasattr(self.launcher, "_trigger"): self.launcher._trigger._repos()
            bs.setText("Switch ("+ns.capitalize()+")")
        bs.clicked.connect(sw); sr.addWidget(bs); sr.addStretch(); l1.addLayout(sr)

        slrow(l1, "Radius:", 220, 350, self.cfg.get("radius", 260),
              lambda v: (self.cfg.update({"radius":v}), save_cfg(self.cfg), self.launcher._place()))

        divider(l1)
        section(l1, "🔲  Icon Size")
        ir = QHBoxLayout(); ir.setSpacing(10); ir.addWidget(QLabel("Icon Size (In/Out):"))
        for k, def_v in [("icon_size_inner", 42), ("icon_size_outer", 48)]:
            s = QSlider(Qt.Orientation.Horizontal)
            s.setRange(32, 82); s.setValue(self.cfg.get(k, def_v))
            s.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
            s.setStyleSheet("""
                QSlider::groove:horizontal { background: #1e1b4b; height: 6px; border-radius: 3px; }
                QSlider::handle:horizontal { background: #7c3aed; width: 14px; height: 14px; border-radius: 7px; margin: -4px 0; }
                QSlider::sub-page:horizontal { background: #7c3aed; border-radius: 3px; }
            """)
            def _we_icon(e, sl=s):
                if sl.hasFocus():
                    step = 1 if e.angleDelta().y() > 0 else -1
                    sl.setValue(sl.value() + step); e.accept()
                else: e.ignore()
            s.wheelEvent = _we_icon
            s.valueChanged.connect(lambda v, k2=k: (self.cfg.update({k2:v}), save_cfg(self.cfg), self.launcher.update()))
            ir.addWidget(s)
        l1.addLayout(ir)

        divider(l1)
        section(l1, "⚙️  Behaviour")
        slrow(l1, "Anim Speed:", 200, 1500, self.cfg.get("anim_k", 600),
              lambda v: (self.cfg.update({"anim_k":v}), save_cfg(self.cfg),
                          setattr(self.launcher._spring,"k",v),
                          setattr(self.launcher._spring,"d",int(2*math.sqrt(v)*0.82))))
        
        chk(l1, "Independent Ring Rotation (scroll separately)", self.cfg.get("independent_scroll", False),
            lambda v: (self.cfg.update({"independent_scroll": bool(v)}), save_cfg(self.cfg)))
        
        chk(l1, "📍  Pin Launcher (Stay open on click)", self.launcher._pinned,
            lambda v: (setattr(self.launcher, "_pinned", bool(v)), self.launcher.update()))
        
        chk(l1, "🔒  Lock Volume/Brightness Sliders", self.cfg.get("slider_locked", False),
            lambda v: (self.cfg.update({"slider_locked": bool(v)}), 
                       setattr(self.launcher, "_slider_locked", bool(v)),
                       save_cfg(self.cfg), self.launcher.update()))
        
        slrow(l1, "Scroll Speed:", 10, 100, int(self.cfg.get("scroll_sensitivity", 0.6)*100),
              lambda v: (self.cfg.update({"scroll_sensitivity": v/100.0}), save_cfg(self.cfg)))
        
        chk(l1, "Auto-hide trigger (hover only)", self.cfg.get("auto_hide", False),
            lambda v: (self.cfg.update({"auto_hide":bool(v)}), save_cfg(self.cfg)))
        
        divider(l1)
        section(l1, "🚀  Startup")
        chk(l1, "Run OrbitSwipe at Windows startup", self._get_startup_status(),
            lambda v: self._set_startup(bool(v)))
        l1.addStretch()

        # --- TAB 2: VISUALS ---
        l2 = add_tab("Visuals", "🎨")
        section(l2, "🎭  Theme")
        
        style_row = QHBoxLayout(); style_row.setSpacing(12)
        
        def get_ms_style(ms):
            cur = self.cfg.get("main_style", "dynamic" if self.cfg.get("glass_preset")=="Dynamic Glass" else "custom")
            act = (cur == ms)
            return (f"QPushButton{{background:{'#7c3aed' if act else '#1e1b4b'};"
                    "color:white;border-radius:10px;font-size:10pt;font-weight:bold;min-height:48px;border:1px solid #2e1065;}}"
                    "QPushButton:hover{background:#6d28d9;}")

        self.color_btns = {}
        def set_ms(ms):
            old_ms = self.cfg.get("main_style", "custom")
            self.cfg["main_style"] = ms
            
            # Intelligent Transition: Grab colors AND set 'Dark Obsidian' as the custom default
            if ms == "custom" and old_ms == "dynamic":
                tint_raw, accent_raw = self.launcher._get_wallpaper_tint()
                if tint_raw:
                    tint = QColor(*tint_raw); accent = QColor(*accent_raw) if accent_raw else tint
                    self.cfg["theme_color"] = tint.name()
                    self.cfg["theme_color2"] = accent.name()
                
                # Factory default for Custom Theme is Dark Obsidian
                self.cfg["glass_preset"] = "Dark Obsidian"
                
                # Update Color Pickers UI
                for k, btn in self.color_btns.items():
                    c = self.cfg.get(k)
                    btn.setStyleSheet(f"QPushButton{{background:{c};border-radius:6px;border:1px solid #7c3aed;}}")
                # Update Preset Buttons UI
                for name2, btn2 in _gp_btns.items():
                    btn2.setStyleSheet(_gp_style(name2))
                if hasattr(self, "custom_pane"): 
                    self.custom_pane.setVisible(self.cfg["glass_preset"] == "Custom Glass")

            if ms == "dynamic": self.cfg["glass_preset"] = "Dynamic Glass"
            save_cfg(self.cfg)
            self.custom_controls.setVisible(ms == "custom")
            btn_dyn.setStyleSheet(get_ms_style("dynamic"))
            btn_cust.setStyleSheet(get_ms_style("custom"))
            self.launcher.update()

        btn_dyn = QPushButton("✨  Dynamic Glass")
        btn_dyn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dyn.clicked.connect(lambda: set_ms("dynamic"))
        
        btn_cust = QPushButton("🎨  Custom Theme")
        btn_cust.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cust.clicked.connect(lambda: set_ms("custom"))
        
        style_row.addWidget(btn_dyn)
        style_row.addWidget(btn_cust)
        l2.addLayout(style_row)
        
        # --- Custom Controls (Colors & Presets) ---
        self.custom_controls = QWidget()
        cc_lo = QVBoxLayout(self.custom_controls); cc_lo.setContentsMargins(0,0,0,0); cc_lo.setSpacing(10)
        l2.addWidget(self.custom_controls)

        divider(cc_lo)
        section(cc_lo, "🎨  Theme Colors")
        
        cr = QHBoxLayout()
        for lbl_txt, cfg_key in [("Primary Color:", "theme_color"), ("Accent Color:", "theme_color2")]:
            cr.addWidget(QLabel(lbl_txt))
            cur_c = self.cfg.get(cfg_key, "#4c1d95" if cfg_key=="theme_color" else "#7c3aed")
            btn = QPushButton(); btn.setFixedSize(52,26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"QPushButton{{background:{cur_c};border-radius:6px;border:1px solid #7c3aed;}}")
            self.color_btns[cfg_key] = btn
            def _pick(_, k=cfg_key, b=btn):
                c = QColorDialog.getColor(QColor(self.cfg.get(k,"#4c1d95")), self)
                if c.isValid():
                    self.cfg[k] = c.name(); save_cfg(self.cfg)
                    b.setStyleSheet(f"QPushButton{{background:{c.name()};border-radius:6px;border:1px solid #7c3aed;}}")
                    self.launcher.update()
                    if hasattr(self.launcher, "_trigger") and self.launcher._trigger:
                        self.launcher._trigger.update()
            btn.clicked.connect(_pick); cr.addWidget(btn); cr.addSpacing(15)
        cc_lo.addLayout(cr)

        divider(cc_lo)
        section(cc_lo, "🎭  Glass Presets")
        grid = QGridLayout(); grid.setSpacing(8)
        _gp_btns = {}
        def _gp_style(pn2):
            act2 = self.cfg.get("glass_preset","") == pn2
            return (f"QPushButton{{background:{'#7c3aed' if act2 else '#1e1b4b'};"
                    "color:white;border-radius:6px;font-size:9pt;font-weight:bold;border:none;}}"
                    "QPushButton:hover{background:#6d28d9;}")
        def _sgp(_, pn2, btns):
            self.cfg["glass_preset"] = pn2; save_cfg(self.cfg)
            self.launcher.update()
            if hasattr(self.launcher, "_trigger") and self.launcher._trigger:
                self.launcher._trigger.update()
            for name2, btn2 in btns.items():
                btn2.setStyleSheet(_gp_style(name2))
            if hasattr(self, "custom_pane"):
                self.custom_pane.setVisible(pn2 == "Custom Glass")
        
        filtered_presets = [pn for pn in GLASS_PRESETS if pn != "Dynamic Glass"]
        for i, pn in enumerate(filtered_presets):
            pb = QPushButton(pn); pb.setFixedHeight(32)
            pb.setStyleSheet(_gp_style(pn))
            pb.setCursor(Qt.CursorShape.PointingHandCursor)
            _gp_btns[pn] = pb
            pb.clicked.connect(lambda _, p2=pn, b=_gp_btns: _sgp(_, p2, b))
            grid.addWidget(pb, i // 3, i % 3)
        cc_lo.addLayout(grid)

        self.custom_pane = QWidget()
        self.custom_pane.setStyleSheet("QLabel{border:none;}")
        cp_lo = QVBoxLayout(self.custom_pane); cp_lo.setContentsMargins(0,0,0,0); cp_lo.setSpacing(12)
        
        gcr = QHBoxLayout(); gcr.addWidget(QLabel("Custom Glass Tint:"))
        gbtn = QPushButton(); gbtn.setFixedSize(52,26)
        gbtn.setCursor(Qt.CursorShape.PointingHandCursor)
        g_col = self.cfg.get("glass_custom_color","#ffffff")
        gbtn.setStyleSheet(f"QPushButton{{background:{g_col};border-radius:6px;border:1px solid #7c3aed;}}")
        def _pick_g():
            c = QColorDialog.getColor(QColor(self.cfg.get("glass_custom_color","#ffffff")), self)
            if c.isValid():
                self.cfg["glass_custom_color"] = c.name(); save_cfg(self.cfg)
                gbtn.setStyleSheet(f"QPushButton{{background:{c.name()};border-radius:6px;border:1px solid #7c3aed;}}")
                self.launcher.update()
        gbtn.clicked.connect(_pick_g); gcr.addWidget(gbtn); gcr.addStretch(); cp_lo.addLayout(gcr)

        slrow(cp_lo, "Glass Transparency:", 0, 255, self.cfg.get("glass_custom_alpha", 100),
              lambda v: (self.cfg.update({"glass_custom_alpha":v}), save_cfg(self.cfg), self.launcher.update()))
        slrow(cp_lo, "Frost Intensity:", 0, 100, self.cfg.get("glass_custom_frost", 30),
              lambda v: (self.cfg.update({"glass_custom_frost":v}), save_cfg(self.cfg), self.launcher.update()))

        cc_lo.addWidget(self.custom_pane)
        self.custom_pane.setVisible(self.cfg.get("glass_preset") == "Custom Glass")
        
        # --- Effects (Always Visible) ---
        divider(l2)
        section(l2, "✨  Effects")
        slrow(l2, "Glow Bloom:", 0, 200, int(self.cfg.get("glow_intensity",1.0)*100),
              lambda v: (self.cfg.update({"glow_intensity":v/100.0}), save_cfg(self.cfg), self.launcher.update()))
        chk(l2, "3D Glowing Effect", self.cfg.get("enable_3d_glow", True),
            lambda v: (self.cfg.update({"enable_3d_glow": bool(v)}), save_cfg(self.cfg), self.launcher.update()))
        chk(l2, "Animated dual-colour gradient", self.cfg.get("gradient_anim",True),
            lambda v: (self.cfg.update({"gradient_anim":bool(v)}), save_cfg(self.cfg), self.launcher.update()))
        
        # Initial state
        cur_ms = self.cfg.get("main_style", "dynamic" if self.cfg.get("glass_preset")=="Dynamic Glass" else "custom")
        btn_dyn.setStyleSheet(get_ms_style("dynamic"))
        btn_cust.setStyleSheet(get_ms_style("custom"))
        self.custom_controls.setVisible(cur_ms == "custom")
        
        l2.addStretch()

        # --- TAB 3: WIDGETS ---
        l3 = add_tab("Widgets", "🎯")
        section(l3, "🎯  Centre Display Mode")
        
        cw_card = QFrame()
        cw_card.setStyleSheet("""
            QFrame { background: #1a1635; border-radius: 12px; border: 1.5px solid #312e81; }
            QLabel { border: none; }
            QRadioButton { color: #e2e8f0; font-size: 10pt; spacing: 10px; border: none; }
            QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px; border: 2px solid #4f46e5; background: #0f172a; }
            QRadioButton::indicator:checked { background: #7c3aed; border: 2px solid #c084fc; }
        """)
        cw_lo = QVBoxLayout(cw_card); cw_lo.setContentsMargins(15,15,15,15); cw_lo.setSpacing(10)
        
        mode_row = QHBoxLayout()
        def set_mode(m):
            if self.cfg.get("music_mode") == m: return
            self.cfg["music_mode"] = m; save_cfg(self.cfg)
            self.stats_pane.setVisible(m != "music")
            self.music_pane.setVisible(m != "normal")
            self.launcher.update()

        def mk_mode(lbl, val):
            rb = QRadioButton(lbl); rb.setChecked(self.cfg.get("music_mode","auto")==val)
            rb.toggled.connect(lambda c, v=val: set_mode(v) if c else None)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            return rb
        
        mode_row.addWidget(mk_mode("🤖 Auto", "auto"))
        mode_row.addWidget(mk_mode("📊 Normal", "normal"))
        mode_row.addWidget(mk_mode("🎵 Music", "music"))
        cw_lo.addLayout(mode_row)
        
        self.stats_pane = QWidget(); self.stats_pane.setLayout(QGridLayout())
        self.stats_pane.layout().setContentsMargins(5,5,5,5); self.stats_pane.layout().setSpacing(12)
        self.stats_pane.layout().addWidget(chk_box("Clock", self.cfg.get("show_clock",True),
            lambda v: (self.cfg.update({"show_clock":bool(v)}), save_cfg(self.cfg), self.launcher.update())), 0, 0)
        self.stats_pane.layout().addWidget(chk_box("CPU/RAM", self.cfg.get("show_stats",True),
            lambda v: (self.cfg.update({"show_stats":bool(v)}), save_cfg(self.cfg), self.launcher.update())), 0, 1)
        self.stats_pane.layout().addWidget(chk_box("Battery", self.cfg.get("show_battery",True),
            lambda v: (self.cfg.update({"show_battery":bool(v)}), save_cfg(self.cfg), self.launcher.update())), 1, 0)
        self.stats_pane.layout().addWidget(chk_box("Net Speed", self.cfg.get("show_network",False),
            lambda v: (self.cfg.update({"show_network":bool(v)}), save_cfg(self.cfg), self.launcher.update())), 1, 1)
        cw_lo.addWidget(self.stats_pane)

        self.music_pane = QWidget(); self.music_pane.setLayout(QGridLayout())
        self.music_pane.layout().setContentsMargins(5,5,5,5); self.music_pane.layout().setSpacing(12)
        self.music_pane.layout().addWidget(chk_box("Volume Slider", self.cfg.get("music_show_vol",True),
            lambda v: (self.cfg.update({"music_show_vol":bool(v)}), save_cfg(self.cfg), self.launcher.update())), 0, 0)
        self.music_pane.layout().addWidget(chk_box("Visualizer", self.cfg.get("music_show_viz",True),
            lambda v: (self.cfg.update({"music_show_viz":bool(v)}), save_cfg(self.cfg), self.launcher.update())), 0, 1)
        cw_lo.addWidget(self.music_pane)
        
        cur_m = self.cfg.get("music_mode", "auto")
        self.stats_pane.setVisible(cur_m != "music")
        self.music_pane.setVisible(cur_m != "normal")
        l3.addWidget(cw_card)
        l3.addStretch()

        # --- TAB 4: HOTKEY ---
        l4 = add_tab("Hotkey", "⌨️")
        section(l4, "⌨️  Global Hotkey")
        
        h_grid = QGridLayout()
        h_grid.setVerticalSpacing(12)
        h_grid.setHorizontalSpacing(24)
        
        h_grid.addWidget(QLabel("Launcher Shortcut:"), 0, 0)
        self.hk_rec = HotkeyRecorder(self.cfg.get('hotkey_mod','Alt'), self.cfg.get('hotkey_key','S'))
        def _hk_changed(m, k):
            self.cfg["hotkey_mod"] = m; self.cfg["hotkey_key"] = k
            save_cfg(self.cfg)
            if self._on_hotkey_change: self._on_hotkey_change()
        self.hk_rec.changed.connect(_hk_changed)
        h_grid.addWidget(self.hk_rec, 0, 1)
        
        h_grid.addWidget(QLabel("Pin Window Shortcut:"), 1, 0)
        self.hk_pin_rec = HotkeyRecorder(self.cfg.get('hotkey_pin_mod','Win+Alt'), self.cfg.get('hotkey_pin_key','S'))
        def _hk_pin_changed(m, k):
            self.cfg["hotkey_pin_mod"] = m; self.cfg["hotkey_pin_key"] = k
            save_cfg(self.cfg)
            if self._on_hotkey_change: self._on_hotkey_change()
        self.hk_pin_rec.changed.connect(_hk_pin_changed)
        h_grid.addWidget(self.hk_pin_rec, 1, 1)
        h_grid.setColumnStretch(2, 1) # Push to left
        
        l4.addLayout(h_grid)

        chk(l4, "Enable global hotkey", self.cfg.get("hotkey_enabled",True),
            lambda v: (self.cfg.update({"hotkey_enabled":bool(v)}), save_cfg(self.cfg)))
        
        divider(l4)
        section(l4, "🔊  Sound")
        
        chk(l4, "Enable interface sounds", self.cfg.get("sound_enabled",True),
            lambda v: (self.cfg.update({"sound_enabled":bool(v)}), save_cfg(self.cfg),
                       setattr(self.launcher._snd,"cfg",self.cfg)))
        l4.addStretch()

        # --- TAB 5: FAVORITES ---
        l5 = add_tab("Data", "🗄️")
        section(l5, "📥 Add Items")

        def add_app():
            fp,_ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*.*)")
            if fp: self.launcher.add_any_path(fp)
        def add_dir():
            dp = QFileDialog.getExistingDirectory(self, "Select Folder", "")
            if dp: self.launcher.add_any_path(dp)
        def add_web():
            dlg2 = AddUrlDlg(self)
            if dlg2.exec():
                deadline = time.time()+1.5
                while time.time()<deadline and dlg2.favicon_b64=="": time.sleep(0.04)
                self.cfg["items"].append({"type":"url","name":dlg2.result_name,
                                          "url":dlg2.result_url,"icon":"🌐",
                                          "icon_b64":dlg2.favicon_b64})
                save_cfg(self.cfg); self.launcher.update()
        def add_scr():
            dlg3 = AddScriptDlg(self)
            if dlg3.exec():
                self.cfg["items"].append({"type":"script","name":dlg3.result_name,
                                          "path":dlg3.result_path,"icon":dlg3.result_icon})
                save_cfg(self.cfg); self.launcher.update()
        def backup_cfg():
            try:
                fp, _ = QFileDialog.getSaveFileName(self, "Backup Config", "", "JSON Files (*.json)")
                if fp:
                    with open(fp, "w", encoding="utf-8") as f: json.dump(self.cfg, f, indent=2)
            except Exception as e: _log(f"backup err: {e}")
        def restore_cfg():
            try:
                fp, _ = QFileDialog.getOpenFileName(self, "Restore Config", "", "JSON Files (*.json)")
                if fp:
                    with open(fp, "r", encoding="utf-8") as f: d = json.load(f)
                    self.cfg.update(d); save_cfg(self.cfg, immediate=True)
                    self.launcher.update(); self.close()
            except Exception as e: _log(f"restore err: {e}")
        
        from PyQt6.QtWidgets import QMessageBox
        def clr():
            ret = QMessageBox.warning(self, "Confirmation", "Clear all favorites?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                self.cfg["items"]=[]; save_cfg(self.cfg, immediate=True); self.launcher.update()
        def rst():
            ret = QMessageBox.critical(self, "Warning", "Reset ALL settings to default?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                self.cfg.clear(); self.cfg.update(DEFAULT_CFG)
                save_cfg(self.cfg, immediate=True); self.launcher.update(); self.close()

        # Grid for buttons
        btn_grid = QGridLayout(); btn_grid.setSpacing(10)
        l5.addLayout(btn_grid)
        
        def bbtn_grid(txt, icon, col, fn, r, c):
            b = QPushButton(f" {icon}  {txt}"); b.setFixedHeight(42)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton{{background:{col};color:white;font-size:10pt;font-weight:bold;border-radius:8px;}}"
                            f"QPushButton:hover{{background:{QColor(col).lighter(115).name()};}}")
            b.clicked.connect(fn); btn_grid.addWidget(b, r, c); return b

        bbtn_grid("Add App", "➕", "#7c3aed", add_app, 0, 0)
        bbtn_grid("Add Folder", "📁", "#1e1b4b", add_dir, 0, 1)
        bbtn_grid("Add Web Link", "🌐", "#0d4032", add_web, 1, 0)
        bbtn_grid("Add Script", "📜", "#3d1a00", add_scr, 1, 1)
        
        divider(l5)
        section(l5, "💾  Configuration")
        br_row = QHBoxLayout()
        def bbtn(txt, icon, col, fn, layout):
            b = QPushButton(f" {icon}  {txt}"); b.setFixedHeight(42)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton{{background:{col};color:white;font-size:10pt;font-weight:bold;border-radius:8px;}}"
                            f"QPushButton:hover{{background:{QColor(col).lighter(115).name()};}}")
            b.clicked.connect(fn); layout.addWidget(b); return b
        
        bbtn("Backup Config", "📤", "#3b2070", backup_cfg, br_row)
        bbtn("Restore Config", "📥", "#3b2070", restore_cfg, br_row)
        l5.addLayout(br_row)
        
        divider(l5)
        section(l5, "⚠️  Maintenance")
        clr_row = QHBoxLayout()
        bbtn("Clear Favorites", "🗑️", "#450a0a", clr, clr_row)
        bbtn("Factory Reset", "🔄", "#450a0a", rst, clr_row)
        l5.addLayout(clr_row)
        l5.addStretch()

        # --- TAB 6: LICENSE ---
        l_lic = add_tab("License", "🔑")
        _build_license_tab(l_lic, self)

        # --- TAB 7: ABOUT ---
        l6 = add_tab("About", "ℹ️")
        l6.addStretch()
        alogo = QLabel()
        if icon: alogo.setPixmap(icon.pixmap(80, 80))
        alogo.setAlignment(Qt.AlignmentFlag.AlignCenter); l6.addWidget(alogo)
        
        v1 = QLabel(f"OrbitSwipe v{APP_VERSION}")
        v1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v1.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        v1.setStyleSheet("color: white; border: none; margin-top: 10px;")
        l6.addWidget(v1)
        
        v2 = QLabel("Developed by Cross Tech")
        v2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v2.setStyleSheet("color: #a78bfa; font-size: 11pt; border: none;")
        l6.addWidget(v2)
        
        v3 = QLabel("by Magnetieght EU")
        v3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v3.setStyleSheet("color: #6b7280; font-size: 9pt; border: none;")
        l6.addWidget(v3)
        l6.addStretch()

        # --- INITIAL TAB ---
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)


# ══════════════════════════════════════════════════════════════════════════
#  TRAY ICON + BOOTSTRAP
