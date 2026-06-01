import os
import sys
import time
import math
import ctypes
import base64
import subprocess
import threading
import traceback
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QApplication, QMenu, QFileDialog, 
                             QInputDialog, QLineEdit, QColorDialog, QLabel,
                             QDialog, QMessageBox, QPushButton, QFrame,
                             QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import (Qt, pyqtSignal, QTimer, QPoint, QRect, QRectF, 
                          QPointF, QSize, QEvent)
from PyQt6.QtGui import (QPainter, QColor, QBrush, QPen, QFont, QRadialGradient, 
                          QLinearGradient, QConicalGradient, QPainterPath, 
                          QIcon, QPixmap, QTransform, QCursor, QAction, QImage)

from orbitswipe.core.constants import (APP_NAME, APP_VERSION, GLASS_PRESETS, 
                                      ALL_TOOLS, LOG_FILE, APPDATA_DIR, CF)
from orbitswipe.core.config import save_cfg
from orbitswipe.core.utils import _log, extract_icon_png, _dwm_strip, get_asset_path
from orbitswipe.core.engine import Spring, Sound, Stats, MediaController, Hotkey, make_pm
from orbitswipe.ui.utils import make_tray_icon
from orbitswipe.ui.searchbar import SearchBar
from orbitswipe.ui.colorpicker import ColorPicker

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL, cast, POINTER
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

def b64_pm(b64, sz):
    try:
        d   = base64.b64decode(b64)
        img = QImage.fromData(d)
        if img.isNull(): raise ValueError("null image")
        return QPixmap.fromImage(img).scaled(
            sz, sz,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
    except Exception:
        return make_pm(sz)

class Launcher(QWidget):
    TABS      = ["Recents","Favorites","Toolbox"]
    R_TAB     = 0.40;  R_IN = 0.62;  R_OUT = 0.92
    N_IN_MAX  = 16;    MAX_ITEMS = 36

    def __init__(self, cfg):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint  |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool                 |
            Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self._touch_y = None
        self._pinned  = False
        self._pin_hov = False
        self.cfg      = cfg
        self._tab     = int(cfg.get("last_tab", 2))
        self._open    = False; self._edit = False
        kv = cfg.get("anim_k", 850)
        self._spring  = Spring(0., k=kv, d=int(2*math.sqrt(kv)*0.82))
        self._hov     = -1
        self._rip     = None; self._rip_t = 0.
        self._rot_a   = -81.0; self._vel_a = 0.0
        self._rot_b   = -81.0; self._vel_b = 0.0
        self._drag_y  = None
        self._in_dialog = False
        # FIX: per-tab folder stacks
        self._folder_stk = {0:[], 1:[], 2:[]}
        self._grad_t     = 0.0
        # FIX: dynamically sized hover-scale list
        self._hov_v      = {}
        self._bg_raw     = None
        self._wp_mtime   = -1.0
        self._wp_tint    = None
        self._wp_accent  = None
        try:
            t1, t2 = self._get_wallpaper_tint()
            self._dynamic_tint = t1
            self._dynamic_accent = t2
        except Exception:
            self._dynamic_tint = (40, 20, 80)
            self._dynamic_accent = (124, 58, 237)
        self._clock      = time.strftime("%H:%M")
        self._cpu        = 0.0; self._batt = -1.0; self._charging = False; self._ram = 0.0
        self._net_spd    = ""
        self._slider_mode  = None; self._slider_val = 50; self._slider_drag = False
        self._slider_locked = bool(cfg.get("slider_locked", False))
        self._lock_hov = False
        self._music_vol_drag = False; self._music_prog_drag = False
        self._snd          = Sound(cfg)
        self._media        = MediaController(launcher=self)
        # ── Music widget extra state ───────────────────────────────────────────
        self._title_anim           = Spring(0.0, k=200, d=24)  # track-change slide
        self._music_prog_info      = None   # (x1, x2, y, width) for seek clicks
        self._music_vol_info       = None   # (x1, x2, y, width) for vol clicks
        self._music_vol            = 50     # cached volume 0-100
        self._music_vol_t          = 0.0    # last vol-fetch timestamp
        self._music_app_icon_cache = {}     # {exe_path: QPixmap | bytes | None}
        self._items_cache = None
        self._icache      = {} # icon pixmap cache
        self._last_radius  = -1  # FIX: font cache invalidation
        self._stats        = Stats()
        self._stats.updated.connect(self._on_stats)
        self._workers_started = False
        self._music_scroll = 0.0
        self._music_timer  = QTimer(self)
        self._music_timer.timeout.connect(self._on_music_tick)
        
        # Smart Idle QTimer for UX-Safe Icon Cache Clearing (Clears after 5 mins of closed idle state)
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._clear_icon_cache_on_idle)
        self._last_license_check = 0
        self.open_settings_callback = None
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAcceptDrops(True); self.setMouseTracking(True)
        self._place()
        
        # Start background pre-loader to "warm up" the icon cache
        threading.Thread(target=self._preload_all_icons, daemon=True).start()
        
        self._sb = SearchBar(self); self._sb.launch.connect(self._from_search)
        # Tooltip label
        self._tooltip = QLabel(self)
        self._tooltip.setStyleSheet(
            "background:rgba(13,9,35,240);color:#e2e8f0;"
            "border:1px solid #7c3aed;border-radius:6px;"
            "font-family:'Segoe UI';font-size:9pt;padding:3px 8px;")
        self._tooltip.hide()
        self._vol_iface    = None
        self._vol_com_init = False
        self._last_vol_sent = 50
        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._show_tooltip)
        self._tooltip_idx = -1
        # Drag-reorder state
        self._drag_idx   = -1
        self._drag_px    = 0; self._drag_py = 0
        self._tmr = QTimer(self); self._tmr.timeout.connect(self._tick); self._tmr.start(16)
        self.hide()
        self._overlay = OverlayPanel(self)
        # Trial expiration check timer (every 5 mins)
        self._trial_timer = QTimer(self); self._trial_timer.timeout.connect(self._check_trial)
        self._trial_timer.start(300000) 
        QTimer.singleShot(100, self._check_trial)

    def _check_trial(self):
        from orbitswipe.core.license import get_license_status
        from orbitswipe.ui.dialogs import TrialGateDlg
        st = get_license_status()
        
        # CASE 1: App is Licensed -> Handled centrally by main.py's LicenseCheckThread
        if st["licensed"]:
            return
            
        # CASE 2: App is NOT Licensed (Trial Mode) -> Basic Trial Expiration
        if st["trial"]["expired"]:
            self._trial_timer.stop()
            # Lock launcher if trial expired
            if hasattr(self, "_color_picker_win") and self._color_picker_win:
                self._color_picker_win.hide()
            dlg = TrialGateDlg(self)
            if dlg.exec():
                # If activated, restart timer and continue
                self._trial_timer.start(300000)
            else:
                # If ignored/closed, exit app
                QApplication.quit()

    def _lazy_start_workers(self):
        if getattr(self, "_workers_started", False): return
        self._workers_started = True
        _log("Lazy starting background worker threads (Stats & MediaController) and music timer.")
        self._stats.start()
        self._media.start()
        self._music_timer.start(50)

    def _clear_icon_cache_on_idle(self):
        if not self._open:
            _log("Launcher closed and idle for 5 minutes: clearing QPixmap icon caches and collecting garbage to minimize RAM.")
            self._icache.clear()
            self._music_app_icon_cache.clear()
            import gc
            gc.collect()

    def _on_vol_ready(self, scalar):
        self._slider_val = int(scalar * 100)
        if self._open: self.update()

    def _on_stats(self, cpu, batt, charging, ram, t, spd):
        self._cpu = cpu; self._batt = batt; self._charging = charging; self._ram = ram
        self._clock = t; self._net_spd = spd
        if self._open: self.update()

    def _on_music_tick(self):
        if self._open and self._media.playing:
            self._music_scroll += 1.5
            self.update()

    def _on_track_change(self):
        """Called by MediaController when track title changes."""
        self._title_anim.v   = 1.0    # start fully offset
        self._title_anim.vel = 0.0
        self._title_anim.go(0.0)      # spring animates back to 0
        exe = self._media.app_exe
        if exe and exe not in self._music_app_icon_cache:
            self._music_app_icon_cache[exe] = None   # reserve slot
            def _fetch(path=exe):
                try:
                    raw = extract_icon_png(path, sz=32)
                    self._music_app_icon_cache[path] = raw if raw else b""
                except:
                    self._music_app_icon_cache[path] = b""
            threading.Thread(target=_fetch, daemon=True).start()
        if self._open: self.update()

    def open_settings(self):
        if self.open_settings_callback:
            self.open_settings_callback()
        else:
            # Fallback to Windows settings if no callback is set (unlikely)
            subprocess.Popen("start ms-settings:", shell=True, creationflags=CF)

    def _preload_all_icons(self):
        """Background worker: Warm up the cache with all possible icons."""
        try:
            # 1. Favorites
            for it in self.cfg.get("items", []): self._warm_item(it)
            # 2. Toolbox (The heavy one)
            for it in ALL_TOOLS: self._warm_item(it)
            # 3. Recents
            for it in self.cfg.get("recents", []): self._warm_item(it)
            # 4. Special buttons
            for ic in ["⬅️", "💾", "✏️", "➕"]: self._warm_emoji(ic)
        except Exception as e:
            _log(f"Preload error: {e}")

    def _warm_item(self, it):
        b64 = it.get("icon_b64", "")
        nm  = it.get("name", "?")
        ic  = it.get("icon", "")
        if b64:
            key = b64
            if key not in self._icache:
                self._icache[key] = b64_pm(b64, 64) # Optimized from 96 to 64
        elif ic:
            self._warm_emoji(ic)
        else:
            key = f"text_{nm[:1]}"
            if key not in self._icache:
                self._icache[key] = make_pm(64, nm[:1])

    def _warm_emoji(self, emoji):
        key = f"emoji_{emoji}"
        if key not in self._icache:
            # Optimized resolution for lower RAM
            pm = QPixmap(64, 64); pm.fill(Qt.GlobalColor.transparent)
            p  = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.GlobalColor.white)
            f  = QFont("Segoe UI", 32)
            p.setFont(f)
            p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
            p.end()
            self._icache[key] = pm

    # ── Geometry ──────────────────────────────────────────────────────────
    def _place(self):
        # FIX: use screen at cursor for multi-monitor support
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        sc  = screen.availableGeometry()
        R   = self.cfg.get("radius", 230)
        Ro  = int(R * self.R_OUT)
        PAD = self.cfg.get("icon_size_outer", 48) + 40
        W   = Ro + PAD
        H   = min((Ro+PAD)*2, sc.height()-20)
        self._R  = R; self._W = W; self._H = H
        self._cx = W if self.cfg["side"]=="right" else 0
        self._cy = H // 2
        frac = self.cfg.get("trigger_y", 0.45)
        y = max(sc.y(), min(sc.y()+int(sc.height()*frac)-H//2, sc.y()+sc.height()-H))
        x = (sc.x()+sc.width()-W) if self.cfg["side"]=="right" else sc.x()
        self.setGeometry(x, y, W, H)
        self._rebuild()

    def _rebuild(self):
        W, H   = self._W, self._H
        cx, cy = self._cx, self._cy
        side   = self.cfg["side"]
        Rt, Ri, Ro = self._radii()
        qt_start = 90 if side == "right" else 270
        sweep = 180
        self._p_disk = QPainterPath()
        self._p_disk.moveTo(cx, cy)
        self._p_disk.arcTo(QRectF(cx-Ro, cy-Ro, Ro*2, Ro*2), qt_start, sweep)
        self._p_disk.closeSubpath()
        self._p_outer = QPainterPath()
        self._p_outer.addEllipse(QRectF(cx-Ro,cy-Ro,Ro*2,Ro*2))
        self._p_inner = QPainterPath()
        self._p_inner.addEllipse(QRectF(cx-Ri,cy-Ri,Ri*2,Ri*2))
        WS = [90,150,210] if side=="right" else [30,330,270]
        self._p_tabs = []
        for i in range(3):
            wp = QPainterPath(); wp.moveTo(cx,cy)
            wp.arcTo(QRectF(cx-Rt,cy-Rt,Rt*2,Rt*2), WS[i], 60)
            wp.closeSubpath(); self._p_tabs.append(wp)

        # FIX: only rebuild fonts when radius actually changes
        R = self._R
        if R != self._last_radius:
            self._last_radius = R
            ratio = R / 230.0
            self._fe  = QFont("Segoe UI Emoji", int(14 * ratio))
            self._ft  = QFont("Segoe UI"); self._ft.setPixelSize(max(9, int(11 * ratio)))
            self._fb  = QFont("Segoe UI"); self._fb.setPixelSize(max(9, int(11 * ratio))); self._fb.setBold(True)
            self._fch = QFont("Segoe UI"); self._fch.setPixelSize(max(12, int(18 * ratio))); self._fch.setBold(True)
            self._fca = QFont("Segoe UI"); self._fca.setPixelSize(max(4, int(6 * ratio)))
            self._fcb = QFont("Segoe UI Emoji"); self._fcb.setPixelSize(max(6, int(9 * ratio)))
            self._fcs = QFont("Segoe UI"); self._fcs.setPixelSize(max(5, int(7 * ratio)))

        if hasattr(self, "_sb"): self._sb.setFixedWidth(W)

    def _radii(self):
        R = self._R
        return int(R*self.R_TAB), int(R*self.R_IN), int(R*self.R_OUT)

    # ── Item list ─────────────────────────────────────────────────────────
    def _items(self):
        if self._items_cache is not None: return self._items_cache
        
        if hasattr(self, "_switcher_mode") and self._switcher_mode:
            return self._switcher_items

        stk = self._folder_stk[self._tab]
        if self._tab == 0:
            base = list(self.cfg.get("recents", []))
        elif self._tab == 1:
            base = list(stk[-1] if stk else self.cfg.get("items", []))
        else:
            base = list(self.cfg.get("toolbox", ALL_TOOLS[:33]))

        items = []
        if stk:
            items.append({"type":"back_btn","name":"Back","icon":"⬅️"})

        # Append all base items first
        # We must ALWAYS reserve 1 slot for Edit/Save.
        # The Add button only shows if there's room for it.
        max_user = self.MAX_ITEMS - (1 + (1 if stk else 0))
        items.extend(base[:max_user])
        
        # Append Edit & Add at the end of real items
        items.append({"type":"toggle_edit",
                      "name":"Save" if self._edit else "Edit",
                      "icon":"💾"  if self._edit else "✏️"})
        
        # Only show Add button if we haven't hit the absolute limit of 32
        if self._edit and self._tab in (1, 2) and len(items) < self.MAX_ITEMS:
            items.append({"type":"add_btn","name":"Add","icon":"➕"})

        while len(items) < self.MAX_ITEMS:
            items.append({"type":"placeholder","name":"","icon":""})

        self._items_cache = items
        return items

    # ── Open / close ──────────────────────────────────────────────────────
    def toggle(self):
        if self._open: self._close()
        else:          self._open_m()

    def _open_m(self):
        self._idle_timer.stop()
        self._lazy_start_workers()
        if not self._icache:
            _log("Icon cache was empty (cleared on idle). Warm loading asynchronously...")
            threading.Thread(target=self._preload_all_icons, daemon=True).start()
        self._items_cache = None # Force refresh on open
        self._place()
        if not self._slider_locked:
            self._slider_mode = None
        self._slider_drag = False
        self._sb.hide(); self._bg_blur = None
        try:
            sc = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
            if sc:
                rel = self.geometry().translated(-sc.geometry().topLeft())
                pm = sc.grabWindow(0, rel.x(), rel.y(), rel.width(), rel.height())
                if not pm.isNull(): self._bg_raw = pm
        except Exception as e:
            _log(f"Snapshot err: {e}")
        self._switcher_mode = False
        QTimer.singleShot(60, self._do_snapshot) # Premium 60ms delay for maximum reliability

    def _do_snapshot(self):
        try:
            geom = self.geometry()
            sc = QApplication.screenAt(geom.center()) or QApplication.primaryScreen()
            if sc:
                rel = geom.translated(-sc.geometry().topLeft())
                pm = sc.grabWindow(0, rel.x(), rel.y(), rel.width(), rel.height())
                if not pm.isNull():
                    self._bg_raw = pm
                    self._apply_blur()
                    # Level 2 Promotion: Re-assert topmost after blur is ready
                    try:
                        import win32gui, win32con
                        win32gui.SetWindowPos(self.winId(), win32con.HWND_TOPMOST, 0,0,0,0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                    except: pass
        except Exception as e: _log(f"Snapshot err: {e}")
        try:
            t1, t2 = self._get_wallpaper_tint()
            self._dynamic_tint   = t1
            self._dynamic_accent = t2
        except Exception:
            pass
        self._last_wpath     = None
        self._open = True; self._spring.go(1.)
        self.show(); self.raise_(); self.activateWindow(); self.setFocus()
        
        # Absolute Priority Hammer: Alt-Pulse + Topmost Loop
        try:
            import win32gui, win32con
            hwnd = self.winId()
            # Secret Alt-Pulse trick to bypass SetForegroundWindow restrictions
            import ctypes
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0) # Alt down
            win32gui.SetForegroundWindow(hwnd)
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0) # Alt up
            win32gui.BringWindowToTop(hwnd)
            
            def hammer_top(count):
                if count <= 0 or not self._open: return
                try:
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)
                except: pass
                if self._open: QTimer.singleShot(100, lambda: hammer_top(count-1))
            hammer_top(10)
        except: pass
        
        _dwm_strip(self.winId()); self._snd.open()

    def _close(self):
        if not self._open: return
        self._snd.close()
        self._open = False
        for k in self._folder_stk: self._folder_stk[k].clear()
        self._spring.go(0.)
        if not self._slider_locked:
            self._slider_mode = None
        self._sb.hide()
        self._tooltip.hide()
        if hasattr(self, "_overlay"):
            self._overlay.close_panel()
        # RAM Optimization: Release heavy background snapshots when closed
        self._bg_blur = None; self._bg_raw = None
        self.update()
        
        # Start smart idle timer for 5 minutes (300,000 ms) of closed state
        self._idle_timer.start(300000)
        
        # Aggressive memory cleanup on close
        import gc
        gc.collect()

    def _get_vol_iface(self):
        """Return cached IAudioEndpointVolume using top-level HAS_PYCAW flag."""
        if self._vol_iface is not None: return self._vol_iface
        if not HAS_PYCAW: return None
        try:
            import pythoncom
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL, cast, POINTER
            pythoncom.CoInitialize()
            
            # More robust method using MMDeviceEnumerator
            from pycaw.utils import AudioUtilities
            enumerator = AudioUtilities.GetDeviceEnumerator()
            devices = enumerator.GetDefaultAudioEndpoint(0, 0) # eRender=0, eMultimedia=0
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            
            self._vol_iface = cast(interface, POINTER(IAudioEndpointVolume))
            return self._vol_iface
        except Exception as e:
            _log(f"_get_vol_iface: {e}")
            return None

    def _update_blur(self): pass
    def _apply_blur(self): pass

    def _tick(self):
        chg = self._spring.tick(.016)

        friction = 0.94
        self._rot_a += self._vel_a
        self._rot_b += self._vel_b
        self._vel_a *= friction
        self._vel_b *= friction

        # FIX: dynamically sized hover dict
        items = self._items()
        for i in range(len(items)):
            tv = 1.18 if i == self._hov else 1.0
            cur = self._hov_v.get(i, 1.0)
            ad  = (tv - cur) * 0.28
            if abs(ad) > 0.0001:
                self._hov_v[i] = cur + ad
                chg = True

        if abs(self._vel_a) > 0.01 or abs(self._vel_b) > 0.01: chg = True
        
        # Gradient Animation
        if self.cfg.get("gradient_anim", True):
            self._grad_t = (self._grad_t + 0.008) % 1.0
            if self._open: chg = True # Ensure constant update for smooth gradient
            
        if self._rip_t > 0: self._rip_t = max(0., self._rip_t - .045)
        if self._title_anim.tick(.016): chg = True

        # Check global mouse state to collapse if clicked outside
        if self._open and not self._pinned and not getattr(self, "_in_dialog", False) and not self._edit:
            import ctypes, math
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                # LBUTTON is down
                mx, my = QCursor.pos().x(), QCursor.pos().y()
                
                # Check if click is inside the SearchBar widget (including search results)
                inside_sb = False
                if hasattr(self, "_sb") and self._sb.isVisible():
                    sb_geom_g = QRect(self._sb.mapToGlobal(QPoint(0, 0)), self._sb.size())
                    if sb_geom_g.contains(QPoint(mx, my)):
                        inside_sb = True
                
                if not inside_sb:
                    cx_g = self.geometry().x() + self._cx
                    cy_g = self.geometry().y() + self._cy
                    dist = math.hypot(mx - cx_g, my - cy_g)
                    _, _, Ro = self._radii()
                    # Only close if click is clearly outside the outer ring
                    if dist > Ro + 10:
                        self._close()

        # FIX: only update/show when actually open; pause rendering when hidden
        if self._open or self._spring.v > 0.004:
            if chg or self._rip_t > 0: self.update()
        else:
            # fully closed — hide and let the timer idle without repainting
            if self.isVisible():
                self.hide()

    # ── Tooltip helpers ───────────────────────────────────────────────────
    def _show_tooltip(self):
        if not self._open: return
        if self._tooltip_idx == -100:
            txt = "<b>Lock Button</b><br>Keeps slider active across tabs & windows"
            self._tooltip.setText(txt)
            self._tooltip.adjustSize()
            cp = self.mapFromGlobal(QCursor.pos())
            tx = min(cp.x()+14, self._W - self._tooltip.width() - 4)
            ty = min(cp.y()+14, self._H - self._tooltip.height() - 4)
            self._tooltip.move(max(0,tx), max(0,ty))
            self._tooltip.show(); self._tooltip.raise_()
            return
        if self._tooltip_idx < 0: return
        items = self._items()
        if self._tooltip_idx >= len(items): return
        item  = items[self._tooltip_idx]
        itype = item.get("type","")
        if itype in ("placeholder","toggle_edit","add_btn","back_btn"): return
        name  = item.get("name","")
        extra = item.get("path","") or item.get("url","")
        txt   = name
        if extra and extra != name: txt = f"{name}\n{extra}"
        if not txt.strip(): return
        self._tooltip.setText(txt)
        self._tooltip.adjustSize()
        # Position near cursor but inside widget
        cp = self.mapFromGlobal(QCursor.pos())
        tx = min(cp.x()+14, self._W - self._tooltip.width() - 4)
        ty = min(cp.y()+14, self._H - self._tooltip.height() - 4)
        self._tooltip.move(max(0,tx), max(0,ty))
        self._tooltip.show(); self._tooltip.raise_()

    def _hide_tooltip(self):
        self._tooltip_timer.stop()
        self._tooltip.hide()
        self._tooltip_idx = -1

    # ── Mouse wheel ───────────────────────────────────────────────────────
    def wheelEvent(self, e):
        if not self._open: return
        mx, my = e.position().x(), e.position().y()
        Rt, Ri, Ro = self._radii()
        dist = math.hypot(mx - self._cx, my - self._cy)

        if self._slider_mode:
            Rs = int(self._R * 0.44)
            if abs(dist - Rs) <= 40:
                delta = e.angleDelta().y()
                step  = (delta / 120.0) * 5
                nv    = max(0, min(100, int(self._slider_val + step)))
                if nv != self._slider_val:
                    self._slider_val = nv
                    self._apply_slider(nv)
                    self.update()
                e.accept()
                return
            # If outside the slider, fall through to rotate the wheel

        if dist < Rt:
            import time
            if not hasattr(self, '_last_tab_scroll'): self._last_tab_scroll = 0
            delta = e.angleDelta().y()
            if abs(delta) > 60 and time.time() - self._last_tab_scroll > 0.3:
                if delta > 0: self._tab = (self._tab - 1) % 3
                elif delta < 0: self._tab = (self._tab + 1) % 3
                self._items_cache = None
                self.cfg["last_tab"] = self._tab
                save_cfg(self.cfg, immediate=True)
                for k in self._folder_stk: self._folder_stk[k].clear()
                self._vel_a = 0; self._vel_b = 0
                self.update()
                self._last_tab_scroll = time.time()
            e.accept(); return

        sens  = self.cfg.get("scroll_sensitivity", 0.6)
        delta = e.angleDelta().y() / 120.0
        force = delta * 11.0 * sens
        indep = self.cfg.get("independent_scroll", False)
        if indep:
            if dist > (Ri + (Ro - Ri) * 0.3): self._vel_a += force
            else: self._vel_b += force
        else:
            self._vel_a += force; self._vel_b += force
        e.accept()

    def event(self, e):
        if e.type() == QEvent.Type.TouchBegin:
            if e.points():
                p0 = e.points()[0]
                self._touch_start_y   = p0.globalPosition().y()
                self._touch_y         = self._touch_start_y
                self._touch_start_pos = p0.position()
                self._touch_did_drag  = False
                if self._slider_mode:
                    tx, ty = p0.position().x(), p0.position().y()
                    dist = math.hypot(tx - self._cx, ty - self._cy)
                    Rs = int(self._R * 0.44)
                    if abs(dist - Rs) <= 40:
                        self._update_slider_from_pos(tx, ty)
                        self._slider_drag = True
                        self._touch_did_drag = True # Started slider, so it's a drag
            e.accept(); return True
            e.accept(); return True
        if e.type() == QEvent.Type.TouchUpdate:
            if not e.points(): return True
            p0 = e.points()[0]
            tx, ty = p0.position().x(), p0.position().y()
            if self._slider_mode and self._slider_drag:
                dist = math.hypot(tx - self._cx, ty - self._cy)
                Rs = int(self._R * 0.44)
                if abs(dist - Rs) <= 40:
                    self._update_slider_from_pos(tx, ty)
                    self._touch_did_drag = True
                    e.accept(); return True
                else:
                    self._slider_drag = False
                    self._touch_y = p0.globalPosition().y()
            if hasattr(self, '_touch_start_pos'):
                dist = (p0.position() - self._touch_start_pos).manhattanLength()
                if dist > 25: self._touch_did_drag = True
            if hasattr(self, '_touch_y') and self._touch_y is not None:
                dy   = p0.globalPosition().y() - self._touch_y
                self._touch_y = p0.globalPosition().y()
                sens = self.cfg.get('scroll_sensitivity', 0.6)
                f    = -dy * 0.45 * sens
                indep = self.cfg.get('independent_scroll', False)
                if indep:
                    dist_r = math.hypot(tx - self._cx, ty - self._cy)
                    _, Ri, Ro = self._radii()
                    if dist_r > (Ri + (Ro - Ri) * 0.3): self._vel_a += f
                    else: self._vel_b += f
                else:
                    self._vel_a += f; self._vel_b += f
                self.update()
            e.accept(); return True
        if e.type() == QEvent.Type.TouchEnd:
            self._slider_drag = False
            if hasattr(self, '_touch_did_drag') and not self._touch_did_drag:
                if e.points():
                    p = e.points()[0].position()
                    lx, ly = p.x(), p.y()
                    QTimer.singleShot(30, lambda: self._handle_click(lx, ly))
            self._touch_y = None; self._touch_did_drag = False
            e.accept(); return True
        return super().event(e)

    def _get_hub_metrics(self):
        Rt, _, _ = self._radii()
        hub_r = int(Rt * 0.62)
        side = self.cfg["side"]; sign = -1 if side == "right" else 1
        cent_x = int(self._cx + sign * 4 * hub_r / (3 * 3.14159)) + (sign * 2)
        
        show_c = self.cfg.get("show_clock", True)
        show_s = self.cfg.get("show_stats", True)
        show_b = self.cfg.get("show_battery", True)
        
        # Match the topmost Y coordinate used in _draw_center's Normal Widget
        if show_b or show_c:
            # Keep at topmost level if either info part is visible
            ty = self._cy - int(hub_r * 0.78)
        elif show_s:
            ty = self._cy + int(hub_r * 0.12) + 5
        else:
            ty = self._cy - int(hub_r * 0.2)
            
        return cent_x, ty

    def _get_pin_rect(self):
        Rt, _, _ = self._radii()
        hub_r = int(Rt * 0.62)
        side = self.cfg["side"]; sign = -1 if side == "right" else 1
        sf = hub_r / 70.0
        
        # Check if we are currently showing the music player
        music_mode = self.cfg.get("music_mode", "auto")
        should_show_music = (music_mode == "music") or (music_mode == "auto" and self._media.playing)
        
        if should_show_music:
            # Pin to the side of the app icon in music mode
            cent_x = int(self._cx + sign * 4 * hub_r / (3 * 3.14159)) + (sign * 2)
            y_app = self._cy - int(hub_r * 0.62) - int(4 * sf)
            icon_sz = max(16, int(22 * sf))
            # Opposite of circular = towards screen edge. 
            # For right hub (sign -1), edge is right, so +X.
            # For left hub (sign 1), edge is left, so -X.
            dot_x = cent_x - sign * (icon_sz // 2 + 11)
            dot_y = y_app
        else:
            # Normal dashboard pin position (Top aligned)
            cx, ty = self._get_hub_metrics()
            dot_x = cx - sign * 16
            dot_y = ty - int(self._R * 0.025)
            
        return QRectF(dot_x - 20, dot_y - 20, 40, 40)

    def _pin_hit(self, mx, my):
        if not self._open: return False
        return self._get_pin_rect().contains(QPointF(mx, my))

    def _handle_click(self, mx, my):
        if self._sb.isVisible() and self._sb.geometry().contains(QPoint(int(mx), int(my))):
            return
        if self._pin_hit(mx, my):
            self._pinned = not self._pinned; self.update(); return
        et = self._spring.v**2*(3-2*self._spring.v)
        if self._close_hit(mx, my):
            self._close(); return
        wt = self._wedge_at(mx, my)
        if wt >= 0:
            self._tab = wt; self._edit = False
            self._items_cache = None # Clear item cache on tab change
            self.cfg["last_tab"] = wt
            save_cfg(self.cfg, immediate=True)
            self._vel_a = 0; self._vel_b = 0
            self._sb.hide()
            if not self._slider_locked:
                self._slider_mode = None
            self.update(); return
        
        # Lock checkbox hit
        if self._slider_mode and hasattr(self, "_lock_rect"):
            if self._lock_rect.contains(QPointF(mx, my)):
                self._slider_locked = not self._slider_locked
                self.cfg["slider_locked"] = self._slider_locked
                save_cfg(self.cfg)
                self.update(); return

        inn, out, ni, _, _ = self._all_pos(et)
        items = self._items()
        sz_in  = self.cfg.get("icon_size_inner", 42)
        sz_out = self.cfg.get("icon_size_outer", 48)

        # ── Music widget interactive areas (seek + volume) ────────────────────
        _mm = self.cfg.get("music_mode", "auto")
        _im = (_mm == "music") or (_mm == "auto" and self._media.playing)
        if _im:
            if hasattr(self, "_music_prog_info") and self._music_prog_info:
                x1, x2, py, pw_b = self._music_prog_info
                if abs(my - py) < 12 and x1 - 6 <= mx <= x2 + 6:
                    frac = max(0.0, min(1.0, (mx - x1) / pw_b))
                    new_el = frac * max(1.0, self._media._track_duration)
                    self._media._track_elapsed = new_el
                    self._media._play_start = time.time() if self._media.playing else 0.0
                    self.update(); return
            if hasattr(self, "_music_vol_info") and self._music_vol_info:
                x1, x2, vy, pw_v = self._music_vol_info
                if abs(my - vy) < 12 and x1 - 6 <= mx <= x2 + 6:
                    frac = max(0.0, min(1.0, (mx - x1) / pw_v))
                    self._music_vol   = int(frac * 100)
                    self._music_vol_t = 0.0   # force re-fetch next draw
                    try:
                        iface = self._get_vol_iface()
                        if iface: iface.SetMasterVolumeLevelScalar(self._music_vol / 100.0, None)
                    except: pass
                    self.update(); return

        # Music Controls Click
        music_mode = self.cfg.get("music_mode", "auto")
        is_music = (music_mode == "music") or (music_mode == "auto" and self._media.playing)
        if is_music and hasattr(self, "_music_btns"):
            for act, rect in self._music_btns.items():
                if rect.contains(QPoint(int(mx), int(my))):
                    self._snd.click()
                    if act == "prev": self._media.prev_track()
                    elif act == "play": self._media.play_pause()
                    elif act == "next": self._media.next_track()
                    return

        def _act(i, ix, iy, s_limit):
            if i >= len(items): return False
            it = items[i]; itype = it.get("type","")
            if itype == "placeholder": return True
            is_removable = (self._tab in (0, 1, 2))
            if self._edit and itype not in ("add_btn","toggle_edit","back_btn","placeholder") and is_removable:
                bx = ix+s_limit//2-6; by = iy-s_limit//2-6
                if math.hypot(mx-bx, my-by) < 26:
                    self._remove(it); return True
            if math.hypot(mx-ix, my-iy) < s_limit//2+24:
                if itype == "toggle_edit":
                    self._edit = not self._edit
                    self._items_cache = None # Clear cache to reflect edit state changes
                    if self._edit:
                        # Use a singleShot timer to rotate safely after the click event finishes
                        QTimer.singleShot(50, self._auto_rotate_to_add)
                    else:
                        save_cfg(self.cfg, immediate=True)
                    self.update()
                elif itype == "back_btn":
                    stk = self._folder_stk[self._tab]
                    if stk: stk.pop()
                    self._items_cache = None
                    self.update()
                elif self._edit and itype == "add_btn":
                    self._add_flow(QPoint(int(mx), int(my)))
                elif not self._edit and itype not in ("add_btn","toggle_edit"):
                    self._rip = i; self._rip_t = 1.; self.update()
                    self._snd.click()
                    QTimer.singleShot(180, lambda x=it: self._activate(x))
                return True
            return False

        for i,(ix,iy) in enumerate(inn):
            if _act(i, ix, iy, sz_in): return
        for j,(ix,iy) in enumerate(out):
            if _act(ni+j, ix, iy, sz_out): return

        if self._edit:
            self._edit = False; save_cfg(self.cfg, immediate=True); self.update(); return

        _, _, Ro = self._radii()
        dist = math.hypot(mx - self._cx, my - self._cy)
        if dist > Ro and not self._pinned:
            self._close()

    def changeEvent(self, e):
        if e.type() == QEvent.Type.ActivationChange:
            # We no longer close automatically on focus loss here, 
            # instead we rely on the global click-outside check in _tick()
            pass
        super().changeEvent(e)

    # ── Icon positions ────────────────────────────────────────────────────
    def _ring_pos(self, n, R, et, rot_angle, is_inner=True):
        if n == 0: return [], []
        cx, cy = self._cx, self._cy
        r = R * et
        side = self.cfg["side"]
        sign = -1 if side == "right" else 1
        step = 22.5 if is_inner else 18.0
        positions = []; opacities = []
        for i in range(n):
            a_norm = (i * step) + rot_angle
            a_norm = (a_norm + 180) % 360 - 180
            d = abs(a_norm)
            if d < 78: op = 1.0
            elif d > 102: op = 0.0
            else: op = (102 - d) / 24.0
            ang_rad = math.radians(a_norm)
            px = int(cx + sign * r * math.cos(ang_rad))
            py = int(cy - r * math.sin(ang_rad))
            positions.append((px, py)); opacities.append(op)
        return positions, opacities

    def _all_pos(self, et):
        items = self._items(); n = len(items)
        ni = min(n, self.N_IN_MAX); no = n - ni
        Rt, Ri, Ro = self._radii()
        pi, oi = self._ring_pos(ni, Ri, et, self._rot_b, is_inner=True)
        po, oo = self._ring_pos(no, Ro, et, self._rot_a, is_inner=False)
        return pi, po, ni, oi, oo

    def _wedge_at(self, mx, my):
        cx, cy   = self._cx, self._cy
        Rt, _, _ = self._radii()
        dx       = (cx-mx) if self.cfg["side"]=="right" else (mx-cx)
        dist     = math.hypot(dx, cy-my)
        hub_r    = int(Rt * 0.62)
        if dist < hub_r or dist > Rt: return -1
        ang = math.degrees(math.atan2(cy-my, dx))
        if  30 <= ang <=  90: return 0
        if -30 <= ang <   30: return 1
        if -90 <= ang <  -30: return 2
        return -1

    def _close_hit(self, mx, my):
        return math.hypot(mx-self._cx, my-self._cy) < 22

    # ── Mouse ─────────────────────────────────────────────────────────────
    def mouseMoveEvent(self, e):
        mx, my = e.position().x(), e.position().y()
        ph = self._pin_hit(mx, my)
        if ph != self._pin_hov: self._pin_hov = ph; self.update()

        if self._slider_drag and self._slider_mode:
            dist = math.hypot(mx - self._cx, my - self._cy)
            Rs = int(self._R * 0.44)
            if abs(dist - Rs) <= 40:
                self._update_slider_from_pos(mx, my)
                return
            else:
                self._slider_drag = False

        # Music Player Drags
        if self._music_vol_drag and hasattr(self, "_music_vol_info"):
            x1, x2, vy, pw_v = self._music_vol_info
            frac = max(0.0, min(1.0, (mx - x1) / pw_v))
            val = int(frac * 100)
            self._music_vol = val
            self._slider_val = val # Sync with ring slider
            self._set_master_vol(val)
            self.update(); return

        if self._music_prog_drag and hasattr(self, "_music_prog_info"):
            x1, x2, py, pw_b = self._music_prog_info
            frac = max(0.0, min(1.0, (mx - x1) / pw_b))
            self._media._track_elapsed = frac * max(1.0, self._media._track_duration)
            self._media._play_start = time.time() if self._media.playing else 0.0
            self.update(); return

        # Drag-reorder logic
        if self._edit and self._drag_idx >= 0:
            self._drag_px = int(mx); self._drag_py = int(my)
            self.update(); return

        if self._slider_mode and hasattr(self, "_lock_rect"):
            lh = self._lock_rect.contains(QPointF(mx, my))
            if lh != self._lock_hov:
                self._lock_hov = lh
                self._hide_tooltip()
                if lh:
                    self._tooltip_idx = -100
                    self._tooltip_timer.start(700)
                self.update()

        et   = self._spring.v**2*(3-2*self._spring.v)
        inn, out, ni, _, _ = self._all_pos(et)
        items = self._items()
        prev  = self._hov; self._hov = -1
        sz    = self.cfg.get("icon_size_outer", 48)
        for i,(ix,iy) in enumerate(inn):
            if math.hypot(mx-ix,my-iy) < sz//2+15: self._hov=i; break
        if self._hov == -1:
            for j,(ix,iy) in enumerate(out):
                ii = ni+j
                if ii<len(items) and math.hypot(mx-ix,my-iy)<sz//2+15:
                    self._hov=ii; break

        if self._hov != prev:
            self._hide_tooltip()
            if self._hov >= 0:
                self._tooltip_idx = self._hov
                self._tooltip_timer.start(700)
            self.update()

    def _update_slider_from_pos(self, mx, my):
        cx, cy = self._cx, self._cy
        sign   = -1 if self.cfg["side"]=="right" else 1
        dx     = sign*(mx-cx); dy = cy-my
        ang    = math.degrees(math.atan2(dy, dx))
        val    = int(((ang + 90) / 180.0) * 100)
        val    = max(0, min(100, val))
        if val != self._slider_val:
            self._slider_val = val
            self._apply_slider(val)
        self.update()

    def _apply_slider(self, val):
        try:
            if self._slider_mode == "br":
                subprocess.Popen(
                    f'powershell -windowstyle hidden -c "(gwmi -Ns root/wmi '
                    f'-Cl WmiMonitorBrightnessMethods).WmiSetBrightness(1,{val})"',
                    shell=True, creationflags=CF)
            elif self._slider_mode == "vol":
                self._music_vol = val # Sync with music slider
                self._set_master_vol(val)
        except Exception: pass

    def _set_master_vol(self, val):
        """Shared volume logic used by both ring slider and music player."""
        try:
            iface = self._get_vol_iface()
            if iface is not None:
                iface.SetMasterVolumeLevelScalar(val / 100.0, None)
            else:
                # Fallback system
                diff = val - getattr(self, "_last_vol_sent", 50)
                if abs(diff) >= 2:
                    key = 175 if diff > 0 else 174
                    subprocess.Popen(f'powershell -windowstyle hidden -c "(new-object -com wscript.shell).SendKeys([char]{key})"',
                                     shell=True, creationflags=CF)
                    self._last_vol_sent = val
        except Exception as e:
            _log(f"vol set err: {e}")
            self._vol_iface = None

    def mousePressEvent(self, e):
        from PyQt6.QtGui import QInputDevice
        # IGNORE synthesized touch events (already handled in event())
        if e.device().type() == QInputDevice.DeviceType.TouchScreen:
            return
        if e.button() == Qt.MouseButton.RightButton:
            self._ctx(e); return
        if e.button() != Qt.MouseButton.LeftButton: return
        mx, my = e.position().x(), e.position().y()
        self._hide_tooltip()

        # Check for small 'X' buttons in edit mode before drag
        if self._edit:
            et = self._spring.v**2*(3-2*self._spring.v)
            inn, out, ni, _, _ = self._all_pos(et)
            items = self._items()
            sz_in  = self.cfg.get("icon_size_inner", 42)
            sz_out = self.cfg.get("icon_size_outer", 48)
            def _chk_del(i, ix, iy, s_limit):
                if i >= len(items): return False
                it = items[i]; itype = it.get("type","")
                is_removable = (self._tab in (0, 1, 2))
                if itype not in ("add_btn","toggle_edit","back_btn","placeholder") and is_removable:
                    bx = ix+s_limit//2-6; by = iy-s_limit//2-6
                    if math.hypot(mx-bx, my-by) < 15: # Reduced from 30 to 15
                        self._remove(it); return True
                return False
            for i,(ix,iy) in enumerate(inn):
                if _chk_del(i, ix, iy, sz_in): return
            for j,(ix,iy) in enumerate(out):
                if _chk_del(ni+j, ix, iy, sz_out): return

        # Drag-reorder: start drag immediately in edit mode
        if self._edit:
            et = self._spring.v**2*(3-2*self._spring.v)
            inn, out, ni, _, _ = self._all_pos(et)
            items = self._items()
            sz_in  = self.cfg.get("icon_size_inner", 42)
            sz_out = self.cfg.get("icon_size_outer", 48)
            for i,(ix,iy) in enumerate(inn):
                it = items[i] if i < len(items) else None
                if it and it.get("type","") not in ("placeholder","toggle_edit","add_btn","back_btn"):
                    if math.hypot(mx-ix,my-iy) < sz_in//2+15:
                        self._drag_idx = i
                        self._drag_px = int(mx); self._drag_py = int(my)
                        return
            for j,(ix,iy) in enumerate(out):
                ii = ni+j
                it = items[ii] if ii < len(items) else None
                if it and it.get("type","") not in ("placeholder","toggle_edit","add_btn","back_btn"):
                    if math.hypot(mx-ix,my-iy) < sz_out//2+15:
                        self._drag_idx = ii
                        self._drag_px = int(mx); self._drag_py = int(my)
                        return

        # Slider precedence: check slider hit first with proper angle checks
        _slider_hit = False
        if self._slider_mode:
            dist = math.hypot(mx - self._cx, my - self._cy)
            Rs = int(self._R * 0.44)
            if abs(dist - Rs) <= 40:
                sign = -1 if self.cfg.get("side", "left") == "right" else 1
                dx = sign*(mx-self._cx); dy = self._cy-my
                ang = math.degrees(math.atan2(dy, dx))
                if -110 <= ang <= 110:
                    # Exclude the lock checkbox area from slider drag
                    if hasattr(self, "_lock_rect") and self._lock_rect.contains(QPointF(mx, my)):
                        pass
                    else:
                        _slider_hit = True
                        self._slider_drag = True
                        self._update_slider_from_pos(mx, my)

        if not _slider_hit:
            self._handle_click(mx, my)
        
        # Music Drags Initiation
        music_mode = self.cfg.get("music_mode", "auto")
        is_music = (music_mode == "music") or (music_mode == "auto" and self._media.playing)
        if is_music:
            if hasattr(self, "_music_prog_info") and self._music_prog_info:
                x1, x2, py, pw_b = self._music_prog_info
                if abs(my - py) < 15 and x1 - 10 <= mx <= x2 + 10:
                    self._music_prog_drag = True
            if hasattr(self, "_music_vol_info") and self._music_vol_info:
                x1, x2, vy, pw_v = self._music_vol_info
                if abs(my - vy) < 15 and x1 - 10 <= mx <= x2 + 10:
                    self._music_vol_drag = True

    def mouseReleaseEvent(self, e):
        self._slider_drag = False
        self._music_vol_drag = False
        self._music_prog_drag = False
        # Drag-reorder: finish drop
        if self._edit and self._drag_idx >= 0 and e.button() == Qt.MouseButton.LeftButton:
            mx, my = e.position().x(), e.position().y()
            self._finish_reorder(mx, my)
            self._drag_idx = -1; self.update(); return

    def _finish_reorder(self, mx, my):
        et = self._spring.v**2*(3-2*self._spring.v)
        inn, out, ni, _, _ = self._all_pos(et)
        items_ref = self._items()
        sz_in  = self.cfg.get("icon_size_inner", 42)
        sz_out = self.cfg.get("icon_size_outer", 48)
        drop_idx = -1
        for i,(ix,iy) in enumerate(inn):
            if math.hypot(mx-ix,my-iy) < sz_in//2+24:
                drop_idx = i; break
        if drop_idx < 0:
            for j,(ix,iy) in enumerate(out):
                if math.hypot(mx-ix,my-iy) < sz_out//2+24:
                    drop_idx = ni+j; break
        if drop_idx < 0 or drop_idx == self._drag_idx: return

        # Reorder in the backing list
        stk = self._folder_stk[self._tab]
        if self._tab == 1:
            lst = stk[-1] if stk else self.cfg["items"]
        elif self._tab == 2:
            lst = self.cfg.get("toolbox", [])
        else:
            return  # recents: no reorder

        # items() prepends back_btn and appends system items — offset accordingly
        offset = 1 if stk else 0
        src = self._drag_idx - offset
        dst = drop_idx - offset
        if 0 <= src < len(lst) and 0 <= dst < len(lst):
            lst.insert(dst, lst.pop(src))
            self._items_cache = None # Clear cache
            save_cfg(self.cfg)
        self.update()

    # focusOutEvent moved to below
    # ── Right-click context menu ──────────────────────────────────────────
    def _ctx(self, e):
        mx, my = e.position().x(), e.position().y()
        et     = self._spring.v**2*(3-2*self._spring.v)
        inn, out, ni, _, _ = self._all_pos(et)
        items  = self._items()
        sz     = self.cfg.get("icon_size_outer", 48)
        target = None
        for i,(ix,iy) in enumerate(inn):
            if i<len(items) and math.hypot(mx-ix,my-iy)<sz//2+16:
                target=items[i]; break
        if target is None:
            for j,(ix,iy) in enumerate(out):
                ii=ni+j
                if ii<len(items) and math.hypot(mx-ix,my-iy)<sz//2+16:
                    target=items[ii]; break
        if target is None: return
        itype = target.get("type","")
        if itype in ("placeholder","add_btn","toggle_edit","back_btn"): return
        m = QMenu(self)
        
    def _check_limit(self):
        stk = self._folder_stk[self._tab]
        if self._tab == 0:
            base = self.cfg.get("recents", [])
        elif self._tab == 1:
            base = stk[-1] if stk else self.cfg.get("items", [])
        else:
            base = self.cfg.get("toolbox", [])
        
        # Reserved slots: Edit/Save (1) and Back button (1 if in folder)
        # Add button is dynamic and doesn't count against the base limit unless it's the 32nd slot
        reserved = 1 + (1 if stk else 0)
        if len(base) + reserved >= self.MAX_ITEMS:
            from PyQt6.QtWidgets import QMessageBox
            self._in_dialog = True
            QMessageBox.warning(self, "Limit Reached", 
                f"You have reached the absolute limit of {self.MAX_ITEMS - reserved} items for this section.\n"
                "Please remove some items before adding new ones.")
            self._in_dialog = False
            return False
        return True
        m.setStyleSheet("""
            QMenu{background:#13132b;color:#e2e8f0;border:1px solid #7c3aed;
                  font-family:'Segoe UI';font-size:9pt;padding:4px;border-radius:8px;}
            QMenu::item{padding:7px 18px;border-radius:4px;}
            QMenu::item:selected{background:#7c3aed;}
            QMenu::separator{height:1px;background:#2e1065;margin:4px 8px;}
        """)
        path = target.get("path",""); url = target.get("url","")
        if path and os.path.exists(path):
            a1 = QAction("🛡️  Run as Administrator", self)
            a1.triggered.connect(lambda: self._runas(path)); m.addAction(a1)
            a2 = QAction("📂  Open File Location", self)
            a2.triggered.connect(lambda: subprocess.Popen(["explorer","/select,",path]))
            m.addAction(a2); m.addSeparator()
        if url:
            a3 = QAction("📋  Copy URL", self)
            a3.triggered.connect(lambda: QApplication.clipboard().setText(url))
            m.addAction(a3); m.addSeparator()
        ar = QAction("🗑️  Remove from Launcher", self)
        ar.triggered.connect(lambda: self._remove(target))
        m.addAction(ar)
        self._in_dialog = True
        try:
            m.exec(QCursor.pos())
        finally:
            QTimer.singleShot(300, lambda: setattr(self, "_in_dialog", False))

    def _runas(self, path):
        try: ctypes.windll.shell32.ShellExecuteW(None,"runas",path,None,None,1)
        except Exception: pass
        if not self._pinned: self._close()

    # ── Edit helpers ──────────────────────────────────────────────────────
    def _remove(self, item):
        if self._tab in (0, 1):
            stk = self._folder_stk[self._tab]
            lst = stk[-1] if stk else self.cfg["items" if self._tab==1 else "recents"]
            if item in lst: lst.remove(item)
        elif self._tab == 2:
            self.cfg["toolbox"] = [x for x in self.cfg.get("toolbox",[])
                                   if x.get("action") != item.get("action")]
        self._items_cache = None
        save_cfg(self.cfg); self.update()

    def _add_flow(self, pos=None):
        if pos is None: pos = self.mapFromGlobal(QCursor.pos())
        gpos = self.mapToGlobal(pos) + QPoint(15, 15)
        self._in_dialog = True
        try:
            if self._tab in (0, 1):
                m = QMenu(self)
                m.setStyleSheet("""
                    QMenu{background:#13132b;color:#e2e8f0;border:1px solid #7c3aed;
                          font-family:'Segoe UI';font-size:9pt;padding:4px;border-radius:8px;}
                    QMenu::item{padding:7px 18px;border-radius:4px;}
                    QMenu::item:selected{background:#7c3aed;}
                """)
                stk = self._folder_stk[self._tab]
                items_in_view = stk[-1] if stk else self.cfg.get("items", [])
                self._items_cache = None # Clear cache
                has_search = any(it.get("action") == "search_bar" for it in items_in_view)
                for lbl,fn in [("📄  Add File",            self._add_file),
                               ("📁  Add Folder",          self._add_dir),
                               ("🌐  Add Web Link",         self._add_url),
                               ("📜  Add Custom Script",    self._add_script)]:
                    a = QAction(lbl, self); a.triggered.connect(fn); m.addAction(a)
                if not has_search:
                    a = QAction("🔍  Add Search Bar", self)
                    a.triggered.connect(self._add_search_tool); m.addAction(a)
                a = QAction("🚀  Create App Group", self); a.triggered.connect(self._add_workspace); m.addAction(a)
                a = QAction("📦  Create App Folder", self); a.triggered.connect(self._add_folder); m.addAction(a)
                m.exec(gpos)
            elif self._tab == 2:
                curr  = {x["action"] for x in self.cfg.get("toolbox",[])}
                avail = sorted([t for t in ALL_TOOLS if t["action"] not in curr], key=lambda x: x.get("name", "").lower())
                if not avail: return
                m = QMenu(self)
                m.setStyleSheet("""
                    QMenu{background:#13132b;color:#e2e8f0;border:1px solid #7c3aed;
                          font-family:'Segoe UI';font-size:9pt;padding:4px;}
                    QMenu::item:selected{background:#7c3aed;}
                """)
                for t in avail:
                    a = QAction(f"{t['icon']}  {t['name']}", self)
                    a.triggered.connect(lambda _, tool=dict(t): self._add_tool(tool))
                    m.addAction(a)
                m.exec(gpos)
        finally:
            QTimer.singleShot(300, lambda: setattr(self, "_in_dialog", False))

    def _add_file(self):
        fp,_ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*.*)")
        if fp: self.add_any_path(fp)

    def _add_dir(self):
        dp = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        if dp: self.add_any_path(dp)

    def _add_url(self):
        if not self._check_limit(): return
        from orbitswipe.ui.dialogs import AddUrlDlg
        dlg = AddUrlDlg(self)
        self._in_dialog = True
        if dlg.exec():
            stk = self._folder_stk[self._tab]
            lst = stk[-1] if stk else self.cfg["items"]
            if any(it.get("url") == dlg.result_url for it in lst): 
                self._in_dialog = False; return
            lst.append({"type":"url","name":dlg.result_name,
                         "url":dlg.result_url,"icon":"🌐","icon_b64":dlg.favicon_b64})
            self._items_cache = None
            save_cfg(self.cfg); self.update()
        self._in_dialog = False

    def _add_folder(self):
        if not self._check_limit(): return
        from orbitswipe.ui.dialogs import AddFolderDlg
        dlg = AddFolderDlg(self)
        self._in_dialog = True
        if dlg.exec():
            stk = self._folder_stk[self._tab]
            lst = stk[-1] if stk else self.cfg["items"]
            if any(it.get("type") == "folder" and it.get("name") == dlg.result_name for it in lst): 
                self._in_dialog = False; return
            lst.append({"type":"folder","name":dlg.result_name,"icon":"📂","children":[]})
            self._items_cache = None
            save_cfg(self.cfg); self.update()
        self._in_dialog = False

    def _add_workspace(self):
        if not self._check_limit(): return
        from orbitswipe.ui.dialogs import AddWorkspaceDlg
        dlg = AddWorkspaceDlg(self)
        self._in_dialog = True
        if dlg.exec():
            stk = self._folder_stk[self._tab]
            lst = stk[-1] if stk else self.cfg["items"]
            lst.append({"type":"workspace","name":dlg.result_name,"icon":"🚀","paths":dlg.paths})
            self._items_cache = None
            save_cfg(self.cfg); self.update()
        self._in_dialog = False

    def _add_search_tool(self):
        if not self._check_limit(): return
        it = {"name": "Search", "icon": "🔍", "type": "tool", "action": "search_bar"}
        stk = self._folder_stk[self._tab]
        lst = stk[-1] if stk else self.cfg["items"]
        if any(it_cur.get("action") == "search_bar" for it_cur in lst): return
        lst.append(it)
        self._items_cache = None
        save_cfg(self.cfg); self.update()

    def _add_script(self):
        if not self._check_limit(): return
        from orbitswipe.ui.dialogs import AddScriptDlg
        dlg = AddScriptDlg(self)
        self._in_dialog = True
        if dlg.exec():
            stk = self._folder_stk[self._tab]
            lst = stk[-1] if stk else self.cfg["items"]
            lst.append({"type":"script","name":dlg.result_name,
                         "path":dlg.result_path,"icon":dlg.result_icon})
            self._items_cache = None
            save_cfg(self.cfg); self.update()
        self._in_dialog = False

    def _add_tool(self, tool):
        if not self._check_limit(): return
        t2 = dict(tool); t2["type"] = "tool"
        curr = self.cfg.get("toolbox", list(ALL_TOOLS[:33]))
        curr.append(t2)
        self.cfg["toolbox"] = curr
        self._items_cache = None
        save_cfg(self.cfg); self.update()

    # ── Activate ──────────────────────────────────────────────────────────
    def _activate(self, item):
        if item.get("action") not in ("vol_slider", "br_slider") and not self._slider_locked:
            self._slider_mode = None
        itype = item.get("type","")
        if itype == "folder":
            self._folder_stk[self._tab].append(item.get("children",[]))
            self._items_cache = None
            self.update(); return
        if itype == "script":
            self._run_script(item.get("path","")); return
        if itype == "tool" or item.get("action"):
            act = item.get("action","")
            if act in ("vol_slider","br_slider"):
                self._slider_mode = "vol" if act=="vol_slider" else "br"
                target_val = 50
                try:
                    if self._slider_mode == "vol":
                        iface = self._get_vol_iface()
                        if iface: target_val = int(iface.GetMasterVolumeLevelScalar() * 100)
                    else:
                        out = subprocess.check_output(
                            'powershell -windowstyle hidden -c "(gwmi -Ns root/wmi '
                            '-Cl WmiMonitorBrightness).CurrentBrightness"',
                            shell=True, creationflags=0x08000000).strip()
                        if out: target_val = int(out)
                except: pass
                self._slider_val = target_val
                self.update(); return
            
            if act == "search_bar":
                if self._tab == 2:
                    self._sb.show_bar(self._W, mode="toolbox")
                else:
                    self._sb.show_bar(self._W)
                return
            if act == "window_switcher":
                self._do_window_switcher(); return
            self._do_tool(item); return
        if itype == "url":
            url = item.get("url","")
            if url:
                try:
                    import webbrowser; webbrowser.open(url)
                except Exception: pass
            recs = [r for r in self.cfg.get("recents",[]) if r.get("url")!=url]
            recs.insert(0, item); self.cfg["recents"] = recs[:10]
            save_cfg(self.cfg); return
        path = item.get("path","")
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception: pass
            recs = [r for r in self.cfg.get("recents",[]) if r.get("path")!=path]
            recs.insert(0, item); self.cfg["recents"] = recs[:10]
            save_cfg(self.cfg)
        if itype == "window":
            self._activate_window(item.get("hwnd")); return
        if itype == "workspace":
            for p in item.get("paths", []):
                if os.path.exists(p):
                    try: os.startfile(p)
                    except: pass

    def _run_script(self, path):
        if not path or not os.path.exists(path): return
        path = os.path.abspath(path)
        script_dir = os.path.dirname(path)
        ext = os.path.splitext(path)[1].lower()
        
        CNC = 0x00000010
        
        try:
            if ext == ".ps1":
                # -NoExit keeps window open for user input
                subprocess.Popen(["powershell", "-NoExit", "-ExecutionPolicy", "Bypass", "-File", path],
                                 cwd=script_dir, creationflags=CNC)
            elif ext in (".bat", ".cmd"):
                # Use cmd /k and wrap in quotes to preserve the full path (handles spaces and & symbols)
                subprocess.Popen(f'cmd.exe /k ""{path}""', cwd=script_dir, creationflags=CNC)
            elif ext == ".py":
                # Use current python to run the script and keep window open for input
                subprocess.Popen(f'cmd.exe /k ""{sys.executable}" "{path}""', cwd=script_dir, creationflags=CNC)
            else:
                os.startfile(path)
        except Exception as e:
            _log(f"run_script error: {e}")

    def _auto_rotate_to_add(self):
        try:
            items = self._items()
            ni = self.N_IN_MAX
            add_idx = -1
            for idx, it in enumerate(items):
                if it.get("type") == "add_btn":
                    add_idx = idx; break
            
            if add_idx >= 0:
                if add_idx < ni:
                    # Apply a smooth velocity nudge for inner ring
                    self._vel_b -= 1.4
                else:
                    # Apply a smooth velocity nudge for outer ring
                    self._vel_a -= 1.2
                self.update()
        except Exception as e:
            _log(f"Auto-rotate error: {e}")

    def _do_media(self, action):
        ku = ctypes.windll.user32.keybd_event
        try:
            if   action == "media_playpause": ku(0xB3,0,0,0); ku(0xB3,0,2,0)
            elif action == "media_next":       ku(0xB0,0,0,0); ku(0xB0,0,2,0)
            elif action == "media_prev":       ku(0xB1,0,0,0); ku(0xB1,0,2,0)
            elif action == "media_stop":       ku(0xB2,0,0,0); ku(0xB2,0,2,0)
        except Exception: pass

    def _do_tool(self, item):
        a  = item.get("action","")
        ku = ctypes.windll.user32.keybd_event
        try:
            if   a=="screenshot":  subprocess.Popen("explorer ms-screenclip:", shell=True, creationflags=CF)
            elif a=="vol_up":      ku(0xAF,0,0,0); ku(0xAF,0,2,0)
            elif a=="vol_dn":      ku(0xAE,0,0,0); ku(0xAE,0,2,0)
            elif a=="mute":        ku(0xAD,0,0,0); ku(0xAD,0,2,0)
            elif a=="music_toggle": self._media.play_pause()
            elif a=="music_next":   self._media.next_track()
            elif a=="music_prev":   self._media.prev_track()
            elif a=="window_switcher":
                self._do_window_switcher(); return
            elif a=="br_up":
                subprocess.Popen('powershell -windowstyle hidden -c "$b=(gwmi -Ns root/wmi '
                                 '-Cl WmiMonitorBrightness).CurrentBrightness;'
                                 '(gwmi -Ns root/wmi -Cl WmiMonitorBrightnessMethods)'
                                 '.WmiSetBrightness(1,[Math]::Min(100,$b+10))"',
                                 shell=True, creationflags=CF)
            elif a=="br_dn":
                subprocess.Popen('powershell -windowstyle hidden -c "$b=(gwmi -Ns root/wmi '
                                 '-Cl WmiMonitorBrightness).CurrentBrightness;'
                                 '(gwmi -Ns root/wmi -Cl WmiMonitorBrightnessMethods)'
                                 '.WmiSetBrightness(1,[Math]::Max(0,$b-10))"',
                                 shell=True, creationflags=CF)
            elif a=="taskmgr":     subprocess.Popen(["taskmgr"])
            elif a=="explorer":    subprocess.Popen(["explorer"])
            elif a=="settings":    self.open_settings()
            elif a=="calc":        subprocess.Popen(["calc.exe"])
            elif a=="notepad":     subprocess.Popen(["notepad.exe"])
            elif a=="cmd":         subprocess.Popen(["cmd.exe","/c","start"])
            elif a=="paint":       subprocess.Popen(["mspaint.exe"])
            elif a=="colorpicker":
                # Keep reference on self so it stays alive, but handle C++ deletion safely
                need_create = True
                if hasattr(self, "_color_picker_win") and self._color_picker_win is not None:
                    try:
                        # Access isVisible() to check if C++ object still exists
                        visible = self._color_picker_win.isVisible()
                        need_create = not visible
                    except RuntimeError:
                        # C++ object has been deleted, clear reference
                        self._color_picker_win = None
                        need_create = True
                
                if need_create:
                    self._color_picker_win = ColorPicker(self.cfg)
                    self._color_picker_win.destroyed.connect(lambda: setattr(self, "_color_picker_win", None))
                    self._color_picker_win.show()
                else:
                    self._color_picker_win.close()
            elif a=="clipboard":
                ku(0x5B,0,0,0); ku(0x56,0,0,0); ku(0x56,0,2,0); ku(0x5B,0,2,0)
            elif a=="cleanmgr":    subprocess.Popen(["cleanmgr.exe"])
            elif a=="control":     subprocess.Popen(["control.exe"])
            elif a=="wifi":        subprocess.Popen("start ms-settings:network-wifi",   shell=True, creationflags=CF)
            elif a in ("poweropts", "sleep", "hibernate", "restart", "shutdown", "awake", "lock"):
                mode = a if a in ("sleep", "hibernate", "restart", "shutdown", "awake", "lock") else "shutdown"
                self._sb.hide()
                if not self._slider_locked:
                    self._slider_mode = None
                self._overlay.show_panel("power", mode=mode)
            elif a=="bluetooth":   subprocess.Popen("start ms-settings:bluetooth",      shell=True, creationflags=CF)
            elif a=="display":     subprocess.Popen("start ms-settings:display",        shell=True, creationflags=CF)
            elif a=="sound":       subprocess.Popen("start ms-settings:sound",          shell=True, creationflags=CF)
            elif a=="alarm":       subprocess.Popen("start ms-clock:",                  shell=True, creationflags=CF)
            elif a=="recorder":    subprocess.Popen("start ms-screenclip:",             shell=True, creationflags=CF)
            elif a=="msinfo":      subprocess.Popen(["msinfo32.exe"])
            elif a=="resmon":      subprocess.Popen(["resmon.exe"])
            elif a=="regedit":     subprocess.Popen(["regedit.exe"])
            elif a=="diskmgmt":    subprocess.Popen(["diskmgmt.msc"], shell=True)
            elif a=="devmgmt":     subprocess.Popen(["devmgmt.msc"], shell=True)
            elif a=="services":    subprocess.Popen(["services.msc"], shell=True)
            elif a=="taskschd":    subprocess.Popen(["taskschd.msc"], shell=True)
            elif a=="powershell":  subprocess.Popen(["powershell.exe"])
            elif a=="timedate":    subprocess.Popen(["control.exe", "timedate.cpl"])
            elif a=="appwiz":      subprocess.Popen(["control.exe", "appwiz.cpl"])
            elif a=="ncpa":        subprocess.Popen(["control.exe", "ncpa.cpl"])
            elif a=="firewall":    subprocess.Popen(["wf.msc"], shell=True)
            elif a=="dxdiag":      subprocess.Popen(["dxdiag.exe"])
            elif a=="sysdm":       subprocess.Popen(["control.exe", "sysdm.cpl"])
            elif a=="mstsc":       subprocess.Popen(["mstsc.exe"])
            elif a=="magnify":     subprocess.Popen(["magnify.exe"])
            elif a=="osk":         subprocess.Popen(["osk.exe"])
            elif a=="charmap":     subprocess.Popen(["charmap.exe"])
            elif a=="update":      subprocess.Popen("start ms-settings:windowsupdate",       shell=True, creationflags=CF)
            elif a=="nightlight":  subprocess.Popen("start ms-settings:nightlight",          shell=True, creationflags=CF)
            elif a=="hotspot":     subprocess.Popen("start ms-settings:network-mobilehotspot",shell=True, creationflags=CF)
            elif a=="airplane":    subprocess.Popen("start ms-settings:network-airplanemode", shell=True, creationflags=CF)
            elif a=="location":    subprocess.Popen("start ms-settings:privacy-location",     shell=True, creationflags=CF)
            elif a=="rotation":    subprocess.Popen("start ms-settings:screenrotation",       shell=True, creationflags=CF)
            elif a=="accessibility": subprocess.Popen("start ms-settings:easeofaccess-overview", shell=True, creationflags=CF)
            elif a=="battery":     subprocess.Popen("start ms-settings:batterysaver",         shell=True, creationflags=CF)
            elif a=="captions":    subprocess.Popen("start ms-settings:accessibility-livecaptions", shell=True, creationflags=CF)
            elif a=="cast":
                ku(0x5B,0,0,0); ku(0x4B,0,0,0); ku(0x4B,0,2,0); ku(0x5B,0,2,0)
            elif a=="project":     subprocess.Popen(["DisplaySwitch.exe"])
            elif a=="run_script":
                # Generic run_script tool — opens file dialog if no path stored
                fp,_ = QFileDialog.getOpenFileName(None, "Select Script", "",
                           "Scripts (*.ps1 *.bat *.cmd *.py *.exe);;All Files (*.*)")
                if fp: self._run_script(fp)
        except Exception: pass

    def _toggle_current_window_topmost(self):
        """Instantly toggle topmost status for the currently active window."""
        try:
            import win32gui, win32con
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: return
            
            # Don't toggle the launcher itself via hotkey
            if hwnd == self.winId(): return
            
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            is_top   = bool(ex_style & win32con.WS_EX_TOPMOST)
            
            target = win32con.HWND_TOPMOST if not is_top else win32con.HWND_NOTOPMOST
            win32gui.SetWindowPos(hwnd, target, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
            
            # Small visual/audio feedback
            try:
                self._snd.pin() # Play new pin.mp3
            except: pass
            self._tooltip.setText("📌 Pinned" if not is_top else "📍 Unpinned")
            self._tooltip.show()
            QTimer.singleShot(1500, self._tooltip.hide)
        except Exception as e:
            _log(f"WinTop hotkey toggle failed: {e}")

    def _do_window_switcher(self):
        """Open a popup listing all open windows with pin-to-top support."""
        import win32gui, win32process, os, ctypes
        wins = []
        
        # Check if WE are elevated to determine if anything is actually restricted
        is_launcher_admin = False
        try: is_launcher_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except: pass

        def enum_cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd): return
            title = win32gui.GetWindowText(hwnd)
            if not title or title in ("Program Manager", "Start"): return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == os.getpid(): return
            ex_style = win32gui.GetWindowLong(hwnd, -20)
            if ex_style & 0x00000080: return
            
            exe = None; restricted = False
            try:
                # Method 1: Try to open the process with query rights.
                # If this fails, it's almost certainly elevated/restricted relative to us.
                import win32api, win32con
                try:
                    # PROCESS_QUERY_LIMITED_INFORMATION (0x1000) is often available even for elevated procs
                    # but PROCESS_QUERY_INFORMATION (0x0400) usually fails if elevated
                    h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
                    win32api.CloseHandle(h)
                except:
                    if not is_launcher_admin: restricted = True
                
                # Method 2: Try to get EXE path via psutil
                import psutil
                proc = psutil.Process(pid)
                exe  = proc.exe()
            except:
                # Final fallback for restricted detection
                if not is_launcher_admin: restricted = True
            
            pinned = bool(ex_style & 0x00000008)
            wins.append({"title": title, "hwnd": hwnd, "exe": exe, "pinned": pinned, "restricted": restricted})
        win32gui.EnumWindows(enum_cb, None)

        from orbitswipe.ui.dialogs import SwitcherDlg
        dlg = SwitcherDlg(wins, self._activate_window, snd=self._snd, parent=self)
        self._in_dialog = True
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if hasattr(dlg, "selected_hwnd"):
                self._activate_window(dlg.selected_hwnd)
        self._in_dialog = False

    def focusOutEvent(self, e):
        if getattr(self, "_in_dialog", False):
            return super().focusOutEvent(e)

        # Handle edit mode focus loss (merged from old duplicate)
        def delayed_check():
            from PyQt6.QtWidgets import QApplication
            if self._edit and not QApplication.activeWindow():
                self._edit = False
                from orbitswipe.core.utils import save_cfg
                save_cfg(self.cfg, immediate=True)
                self.update()
        QTimer.singleShot(500, delayed_check)

        if self._edit:
            self._edit = False
            self.update()
        if not self._pinned:
            if hasattr(self, "_sb") and self._sb.isVisible():
                return super().focusOutEvent(e)
            self._close()
        return super().focusOutEvent(e)

    def _activate_window(self, hwnd):
        def _do_activate():
            try:
                import win32gui, win32con, win32process, ctypes

                # 1. Prime the system for focus change using Alt pulse + AllowSetForegroundWindow
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
                ctypes.windll.user32.AllowSetForegroundWindow(-1)

                # 2. Restore if minimized
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                else:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

                # 3. Bring to top and set focus using multiple methods for reliability
                win32gui.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)

                # 4. Use SwitchToThisWindow (internal Alt-Tab API) for final activation
                ctypes.windll.user32.SwitchToThisWindow(hwnd, True)

            except Exception as e:
                _log(f"Window switch err: {e}")

        # Run activation in background thread to avoid blocking GUI
        threading.Thread(target=_do_activate, daemon=True).start()

        # Close the launcher unless pinned
        if not self._pinned:
            self._close()

    def _from_search(self, path):
        if path.startswith("TOOLBOX:"):
            act = path.split(":", 1)[1]
            self._do_tool({"action": act})
            return
        if not self._pinned:
            self._close()
        try: os.startfile(path)
        except Exception: pass

    def add_any_path(self, path):
        if not self._check_limit(): return
        path = os.path.normpath(path)
        name = os.path.basename(path)
        if not name: name = path
        ext = os.path.splitext(path)[1].lower()
        emoji = "📄"
        if os.path.isdir(path):                                        emoji = "📂"
        elif ext in (".jpg",".jpeg",".png",".gif",".bmp",".webp",".ico"): emoji = "🖼️"
        elif ext in (".mp4",".mkv",".avi",".mov",".wmv",".flv"):       emoji = "🎬"
        elif ext in (".mp3",".wav",".flac",".m4a",".ogg"):             emoji = "🎵"
        elif ext == ".pdf":                                             emoji = "📕"
        elif ext in (".doc",".docx",".rtf"):                           emoji = "📝"
        elif ext in (".xls",".xlsx",".csv"):                           emoji = "📊"
        elif ext in (".ppt",".pptx"):                                  emoji = "🎭"
        elif ext in (".zip",".rar",".7z",".tar",".gz"):                emoji = "📚"
        elif ext in (".exe",".msi",".bat",".cmd",".ps1"):              emoji = "⚙️"
        elif ext in (".py",".js",".html",".css",".cpp",".c",".h",".json"): emoji = "💻"
        png  = extract_icon_png(path)
        b64  = base64.b64encode(png).decode() if png else ""
        stk  = self._folder_stk[self._tab]
        lst  = stk[-1] if stk else self.cfg["items"]
        if any(it.get("path") == path for it in lst): return
        lst.append({"type":"app","name":name,"path":path,"icon_b64":b64,
                     "icon": emoji, "children":[]})
        self._items_cache = None
        save_cfg(self.cfg); self.update()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.setDropAction(Qt.DropAction.CopyAction); e.accept()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.setDropAction(Qt.DropAction.CopyAction); e.accept()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            fp = u.toLocalFile()
            if fp: self.add_any_path(fp)
        e.setDropAction(Qt.DropAction.CopyAction); e.acceptProposedAction()

    # ══════════════════════════════════════════════════════════════════════
    #  PAINT
    # ══════════════════════════════════════════════════════════════════════
    def paintEvent(self, e):
        try: self._paint()
        except Exception as ex:
            _log(f"paint: {ex}\n{traceback.format_exc()}")

    def _draw_curved_text(self, p, text, cx, cy, radius, center_angle, et):
        p.save()
        p.setOpacity(et)
        deg_per_px = 57.2958 / radius
        fm = p.fontMetrics()
        total_w = fm.horizontalAdvance(text)
        total_ang = total_w * deg_per_px
        curr_ang = center_angle + (total_ang / 2.0)
        for char in text:
            cw = fm.horizontalAdvance(char)
            char_ang = cw * deg_per_px
            ma = curr_ang - (char_ang / 2.0)
            tx = cx + radius * math.cos(math.radians(ma))
            ty = cy - radius * math.sin(math.radians(ma))
            p.save()
            p.translate(tx, ty)
            p.rotate(90 - ma)
            p.drawText(QRect(-cw//2, -fm.height()//2, cw, fm.height()),
                       Qt.AlignmentFlag.AlignCenter, char)
            p.restore()
            curr_ang -= char_ang
        p.restore()

    def _draw_music_player(self, p, cx, cy, et, tc, tc2):
        Rt, _, _ = self._radii()
        side   = self.cfg["side"]
        sign   = -1 if side == "right" else 1
        hub_r  = int(Rt * 0.65)
        cent_x = int(cx + sign * 4 * hub_r / (3 * math.pi))
        hub_w  = int(hub_r * 1.1)
        alpha  = int(255 * et)
        sf     = hub_r / 70.0

        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── Half-circle clip mask ──────────────────────────────────────────
        bg = QPainterPath()
        bg.addEllipse(QRectF(cx - hub_r, cy - hub_r, hub_r * 2, hub_r * 2))
        clip = QPainterPath()
        if side == "right":
            clip.addRect(QRectF(cx - hub_r * 2, cy - hub_r, hub_r * 2 + 2, hub_r * 2))
        else:
            clip.addRect(QRectF(cx, cy - hub_r, hub_r * 2, hub_r * 2))
        bg = bg.intersected(clip)

        # ── Glass background ───────────────────────────────────────────────
        p.setBrush(QBrush(QColor(6, 4, 20, int(185 * et))))
        p.setPen(QPen(QColor(255, 255, 255, int(25 * et)), 1))
        p.drawPath(bg)

        # ── Theme colours ──────────────────────────────────────────────────
        # (tc, tc2 are now passed as arguments)

        # ── Layout Y positions (Refined spacing) ─────────────────────────────
        y_app    = cy - int(hub_r * 0.62) - int(4 * sf)
        y_ttl    = cy - int(hub_r * 0.37) - int(2 * sf)
        y_prog   = cy + int(hub_r * 0.08)
        y_ctrl   = cy + int(hub_r * 0.38) - 9
        y_vol    = cy + int(hub_r * 0.68) - 5
        viz_base = cy + hub_r
        pw = int(hub_w * 0.72)   # shared bar / text width

        # ── 1. App Icon (Centered, Name removed as requested) ──────────────
        app_icon_pm = None
        exe = self._media.app_exe
        hwnd = getattr(self._media, "hwnd", 0)
        if exe:
            cached = self._music_app_icon_cache.get(exe)
            if isinstance(cached, (bytes, bytearray)) and cached:
                pm = QPixmap(); pm.loadFromData(cached)
                if not pm.isNull():
                    app_icon_pm = pm.scaled(32, 32,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)
                    self._music_app_icon_cache[exe] = app_icon_pm
            elif isinstance(cached, QPixmap) and not cached.isNull():
                app_icon_pm = cached
            else:
                # Advanced icon extraction using GDI/Shell
                pass
        
        if app_icon_pm:
            icon_sz = max(16, int(22 * sf))
            p.drawPixmap(cent_x - icon_sz // 2, y_app - icon_sz // 2, icon_sz, icon_sz, app_icon_pm)
        # Removed app name text as requested (No "System" or app labels)

        # ── 2. Song Title — scrolling + slide-in on track change ──────────
        title = self._media.title or "No Media"
        p.setFont(QFont("Segoe UI", max(7, int(9 * sf))))
        fm2   = p.fontMetrics()
        tw    = fm2.horizontalAdvance(title)
        tx    = cent_x - pw // 2
        trect = QRect(tx, y_ttl - int(11 * sf), pw, int(22 * sf))

        slide_off = int(self._title_anim.v * pw * 0.55)
        fade_op   = max(0.0, 1.0 - self._title_anim.v * 1.4)

        tclip = QPainterPath()
        tclip.addRect(QRectF(tx, y_ttl - int(13 * sf), pw, int(26 * sf)))
        p.setClipPath(tclip.intersected(bg))
        p.setPen(QColor(200, 200, 240, int(215 * et * fade_op)))

        if tw > trect.width():
            off = int(self._music_scroll) % (tw + int(60 * sf))
            for ox in [tx - off + slide_off,
                       tx - off + tw + int(60 * sf) + slide_off]:
                p.drawText(ox, trect.top(), tw, trect.height(),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        else:
            p.drawText(QRect(tx + slide_off, trect.top(), trect.width(), trect.height()),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        p.setClipping(False)

        # ── 3. Progress Bar — live elapsed, frozen on pause, seekable ──────
        elapsed  = self._media._elapsed
        duration = max(1.0, self._media._track_duration)
        prog_val = min(1.0, elapsed / duration)
        e_min, e_sec = int(elapsed) // 60, int(elapsed) % 60

        is_paused = not self._media.playing and elapsed > 0
        pulse_a   = (0.55 + 0.45 * abs(math.sin(time.time() * 2.2))) if is_paused else 1.0

        px1, px2 = cent_x - pw // 2, cent_x + pw // 2
        self._music_prog_info = (px1, px2, y_prog, pw)

        # Background track
        p.setPen(QPen(QColor(255, 255, 255, int(30 * et)), max(2, int(3 * sf)),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(px1, y_prog, px2, y_prog)

        # Filled part (Reverted to thin style)
        fill_x = px1 + int(pw * prog_val)
        if fill_x > px1:
            p.setPen(QPen(QColor(tc2.red(), tc2.green(), tc2.blue(), int(210 * et * pulse_a)),
                          max(2, int(3 * sf)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(px1, y_prog, fill_x, y_prog)

        # Knob (Reverted to thin style)
        p.setBrush(QColor(255, 255, 255, int(230 * et * pulse_a)))
        p.setPen(QPen(QColor(tc2.red(), tc2.green(), tc2.blue(), int(160 * et)), 1.5))
        knob_r = max(3, int(4.5 * sf))
        p.drawEllipse(QPointF(float(fill_x), float(y_prog)), knob_r, knob_r)

        # Elapsed time (Added space above knob)
        p.setPen(QColor(170, 170, 210, int(185 * et)))
        p.setFont(QFont("Segoe UI", max(5, int(7 * sf))))
        p.drawText(QRect(px1, y_prog - int(18 * sf), int(pw * 0.5), int(12 * sf)),
                   Qt.AlignmentFlag.AlignLeft, f"{e_min}:{e_sec:02d}")

        # PAUSED badge removed as requested

        # ── 4. Playback Controls (Restored Original Style) ──────────────────
        bw_c, bh_c = int(17 * sf), int(17 * sf)
        spc        = int(5 * sf)
        total_c    = (bw_c * 3) + (spc * 2)
        bx_c       = cent_x - total_c // 2
        cpos       = self.mapFromGlobal(QCursor.pos())
        cmx, cmy   = cpos.x(), cpos.y()
        self._music_btns = {}

        for i, (act, icon) in enumerate([("prev","⏮"), ("play","⏯"), ("next","⏭")]):
            cr = QRect(bx_c + i * (bw_c + spc), y_ctrl, bw_c, bh_c)
            self._music_btns[act] = cr
            hov = cr.contains(QPoint(int(cmx), int(cmy)))
            if hov:
                p.setBrush(QColor(124, 58, 237, int(120 * et)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(cr.center(), bw_c // 2 + int(2 * sf), bh_c // 2 + int(2 * sf))
            p.setPen(QColor(255, 255, 255, int((255 if hov else 210) * et)))
            p.setFont(QFont("Segoe UI Symbol", int(10 * sf)))
            p.drawText(cr, Qt.AlignmentFlag.AlignCenter, icon)

        # ── 5. Volume Bar — live value, clickable ─────────────────────────
        if self.cfg.get("music_show_vol", True):
            now_t = time.time()
            if now_t - self._music_vol_t > 2.0:
                try:
                    iface = self._get_vol_iface()
                    if iface: self._music_vol = int(iface.GetMasterVolumeLevelScalar() * 100)
                    self._music_vol_t = now_t
                except: pass

            vol_icon_w = max(8, int(11 * sf))
            vol_bar_w  = int(pw * 0.48)
            total_vw   = vol_icon_w + int(4 * sf) + vol_bar_w
            # Balanced shift for both sides
            shift_r    = int(5 * sf)
            vx1        = cent_x - total_vw // 2 + vol_icon_w + int(4 * sf) + shift_r
            vx2        = vx1 + vol_bar_w
            self._music_vol_info = (vx1, vx2, y_vol, vol_bar_w)

            p.setPen(QColor(255, 255, 255, int(170 * et)))
            p.setFont(QFont("Segoe UI Emoji", max(4, int(7 * sf))))
            p.drawText(QRect(cent_x - total_vw // 2 + shift_r, y_vol - int(9 * sf),
                             vol_icon_w, int(18 * sf)), Qt.AlignmentFlag.AlignCenter, "🔊")

            p.setPen(QPen(QColor(255, 255, 255, int(22 * et)), max(2, int(2.5 * sf)),
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(vx1, y_vol, vx2, y_vol)

            vfill_x = vx1 + int(vol_bar_w * self._music_vol / 100.0)
            if vfill_x > vx1:
                vg = QLinearGradient(vx1, y_vol, vfill_x, y_vol)
                vg.setColorAt(0, QColor(tc.red(),  tc.green(),  tc.blue(),  int(150 * et)))
                vg.setColorAt(1, QColor(tc2.red(), tc2.green(), tc2.blue(), int(215 * et)))
                p.setPen(QPen(QBrush(vg), max(2, int(2.5 * sf)),
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(vx1, y_vol, vfill_x, y_vol)

            vkr = max(3, int(4 * sf))
            p.setBrush(QColor(210, 210, 255, int(195 * et)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(float(vfill_x), float(y_vol)), vkr, vkr)
        else:
            self._music_vol_info = None



        # ── 6. Visualizer — height-based gradient + glow on tall bars ─────
        if self.cfg.get("music_show_viz", True):
            p.setClipPath(bg)
            num_bars = 14
            b_w      = max(3, int(hub_w * 0.042))
            b_g      = max(2, int(hub_w * 0.022))
            total_vz = num_bars * (b_w + b_g) - b_g
            vz_x     = cent_x - total_vz // 2
            max_bh   = int(hub_r * 0.46) + 7
            t_now    = time.time()

            for i in range(num_bars):
                if self._media.playing:
                    # Reactive logic: mix sine wave with real peak volume
                    peak = self._media.peak_vol
                    base_h = (math.sin(t_now * 2.5 + i * 0.5) * 0.2 + 0.8)
                    hr = (peak * 1.2 * base_h) + (math.sin(t_now * 5.0 + i) * 0.1)
                    hr = max(0.08, min(1.0, hr))
                else:
                    hr = 0.04 + 0.04 * abs(math.sin(i * 0.55))
                h  = max(3, int(max_bh * hr))
                bx = vz_x + i * (b_w + b_g)

                # Interpolate colour by height: short=theme, tall=accent
                r_c = int(tc.red()   + (tc2.red()   - tc.red())   * hr)
                g_c = int(tc.green() + (tc2.green() - tc.green()) * hr)
                b_c = int(tc.blue()  + (tc2.blue()  - tc.blue())  * hr)
                top_a = int((90  + 145 * hr) * et)
                bot_a = int((175 + 65  * hr) * et)

                bgrad = QLinearGradient(bx, viz_base, bx, viz_base - h)
                bgrad.setColorAt(0, QColor(r_c, g_c, b_c, bot_a))
                bgrad.setColorAt(1, QColor(min(255, r_c+35), min(255, g_c+30),
                                           min(255, b_c+50), top_a))
                p.setBrush(QBrush(bgrad)); p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(bx, viz_base - h, b_w, h, 2, 2)

                # Glow on tall bars when playing
                if self._media.playing and hr > 0.62:
                    gr_r = b_w + int(3 * sf)
                    gr_y = viz_base - h
                    gg   = QRadialGradient(bx + b_w // 2, gr_y, gr_r)
                    gg.setColorAt(0, QColor(tc2.red(), tc2.green(), tc2.blue(), int(75 * et * hr)))
                    gg.setColorAt(1, QColor(tc2.red(), tc2.green(), tc2.blue(), 0))
                    p.setBrush(QBrush(gg))
                    p.drawEllipse(QRectF(bx + b_w//2 - gr_r, gr_y - gr_r, gr_r*2, gr_r*2))

        p.restore()

    def _draw_center(self, p, cx, cy, et, tc, tc2):
        music_mode = self.cfg.get("music_mode", "auto")
        should_show_music = False

        if music_mode == "music":
            should_show_music = True
        elif music_mode == "auto" and self._media.playing:
            should_show_music = True

        if should_show_music:
            self._draw_music_player(p, cx, cy, et, tc, tc2)
            return

        show_c = self.cfg.get("show_clock", True)
        show_s = self.cfg.get("show_stats", True)
        show_b = self.cfg.get("show_battery", True)
        show_n = self.cfg.get("show_network", False)
        if not any([show_c, show_s, show_b, show_n]): return

        Rt, _, _ = self._radii()
        side  = self.cfg["side"]
        sign  = -1 if side == "right" else 1
        hub_r  = int(Rt * 0.65)
        cent_x = int(cx + sign * 4 * hub_r / (3 * math.pi)) + (sign * 2)
        hub_w  = int(hub_r * 1.6)
        alpha  = int(235 * et)

        p.save()
        bg = QPainterPath()
        bg.addEllipse(QRectF(cx - hub_r, cy - hub_r, hub_r * 2, hub_r * 2))
        clip = QPainterPath()
        if side == "right":
            clip.addRect(QRectF(cx - hub_r * 2, cy - hub_r, hub_r * 2 + 2, hub_r * 2))
        else:
            clip.addRect(QRectF(cx, cy - hub_r, hub_r * 2, hub_r * 2))
        bg = bg.intersected(clip)
        p.setBrush(QBrush(QColor(6, 4, 20, int(200 * et))))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(bg)

        # ── Glowing ring around the center hub (conditional on 3D glow theme) ────
        if self.cfg.get("enable_3d_glow", True):
            hub_vc = getattr(self, "_vivid_c", QColor(148, 72, 255))
            hub_vc2 = hub_vc.lighter(145)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(hub_vc.red(), hub_vc.green(), hub_vc.blue(), int(40 * et)), 16))
            p.drawPath(bg)
            p.setPen(QPen(QColor(hub_vc.red(), hub_vc.green(), hub_vc.blue(), int(80 * et)), 6))
            p.drawPath(bg)
            p.setPen(QPen(QColor(hub_vc2.red(), hub_vc2.green(), hub_vc2.blue(), int(200 * et)), 0.8))
            p.drawPath(bg)
        else:
            p.setPen(QPen(QColor(255, 255, 255, int(18 * et)), 1))
            p.drawPath(bg)
        p.restore()

        # ── 1. Glass / Path Calculations ──────────────────────────────────
        p.setOpacity(et)
        sf  = hub_r / 70.0
        # (tc, tc2 are now passed as arguments)
        # Width for text (wider to avoid cropping) and bars (narrower for padding)
        pw_txt = int(hub_w * 0.92)
        pw_bar = int(hub_r * 0.82)
        now = datetime.now()

        # ── 2. Battery (Pure White) ───────────────────────────────────────
        if show_b:
            batt_pct = int(self._batt) if self._batt >= 0 else None
            y_batt = cy - int(hub_r * 0.78) # 2px up
            if batt_pct is not None:
                if self._charging:
                    icon = "⚡"
                else:
                    icon = "🔋" if batt_pct > 20 else "🪫"
                btm_text = f"{icon} {batt_pct}%"
                p.setPen(QColor(255, 255, 255, int(210 * et)))
                p.setFont(QFont("Segoe UI", max(5, int(7 * sf)), QFont.Weight.Bold))
                nudge_x = cent_x + (sign * -5)
                p.drawText(QRect(nudge_x - pw_txt//2, y_batt, pw_txt, int(15*sf)), Qt.AlignmentFlag.AlignCenter, btm_text)

        # ── 3. Day Name & Time (Pure White) ───────────────────────────────
        if show_c:
            day_str = now.strftime("%A").upper()
            y_day = cy - int(hub_r * 0.58) + 3 # 2px more up
            p.setPen(QColor(255, 255, 255, int(220 * et)))
            p.setFont(QFont("Segoe UI", max(5, int(7 * sf)), QFont.Weight.Bold))
            nudge_x = cent_x + (sign * -5)
            p.drawText(QRect(nudge_x - pw_txt//2, y_day - int(5*sf), pw_txt, int(12*sf)), Qt.AlignmentFlag.AlignCenter, day_str)

            time_str = now.strftime("%I:%M")
            y_time = cy - int(hub_r * 0.28) + 3 # 2px more up
            p.setPen(QColor(255, 255, 255, int(255 * et)))
            p.setFont(QFont("Segoe UI", int(19 * sf), QFont.Weight.Bold))
            p.drawText(QRect(cent_x - pw_txt//2, y_time - int(15*sf), pw_txt, int(30*sf)), 
                       Qt.AlignmentFlag.AlignCenter, time_str)

        # ── 4. Resource Bars (CPU / RAM) ──────────────────────────────────
        if show_s:
            def draw_bar(py, label, val_pct):
                bx = cent_x - pw_bar // 2
                bw = pw_bar
                bh = max(2, int(3 * sf))
                # Label & Value (Pure White, 1px more gap: 11->12)
                p.setPen(QColor(255, 255, 255, int(230 * et)))
                p.setFont(QFont("Segoe UI", max(5, int(6 * sf)), QFont.Weight.Bold))
                p.drawText(QRect(bx, py - int(14 * sf), bw, int(10 * sf)), Qt.AlignmentFlag.AlignLeft, label)
                p.drawText(QRect(bx, py - int(14 * sf), bw, int(10 * sf)), Qt.AlignmentFlag.AlignRight, f"{int(val_pct)}%")
                # Track
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 255, 255, int(30 * et)))
                p.drawRoundedRect(bx, py, bw, bh, 2, 2)
                # Fill
                fill_w = int(bw * (val_pct / 100.0))
                if fill_w > 0:
                    grad = QLinearGradient(bx, py, bx + fill_w, py)
                    grad.setColorAt(0, tc)
                    grad.setColorAt(1, tc2)
                    p.setBrush(QBrush(grad))
                    p.drawRoundedRect(bx, py, fill_w, bh, 2, 2)

            draw_bar(cy + int(hub_r * 0.12) + 5, "CPU", self._cpu) # 2px more down
            draw_bar(cy + int(hub_r * 0.35) + 7, "RAM", self._ram) # 2px more down

        # ── 5. Net Speed (Pure White) ─────────────────────────────────────
        if show_n:
            y_net = cy + int(hub_r * 0.54) + 3 # 2px more down
            net_text = f"🌐 {self._net_spd or '0 B/s'}"
            p.setPen(QColor(255, 255, 255, int(210 * et)))
            p.setFont(QFont("Segoe UI", max(5, int(7 * sf))))
            # Shift speed 2px to opposite of curve (towards screen edge)
            side = self.cfg.get("side", "right")
            sign = -1 if side == "right" else 1
            nudge_x = cent_x + (sign * -5)
            p.drawText(QRect(nudge_x - pw_txt//2, y_net, pw_txt, int(12*sf)), Qt.AlignmentFlag.AlignCenter, net_text)
        p.restore()

    def _draw_pin(self, p, et):
        p.save(); p.setOpacity(et); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dot_rect = self._get_pin_rect()
        dot_x, dot_y = dot_rect.center().x(), dot_rect.center().y()
        if self._pinned:   dot_base = QColor(0, 255, 128)
        else:              dot_base = QColor(148, 163, 184)
        if self._pin_hov:  dot_base = dot_base.lighter(160)
        p.setBrush(QBrush(dot_base))
        p.setPen(QPen(QColor(255,255,255, 160 if self._pin_hov else 60), 1.0))
        r_vis = 3.5 if self._pin_hov else 3.0
        p.drawEllipse(QPointF(dot_x, dot_y), r_vis, r_vis)
        if self._pinned or self._pin_hov:
            p.setOpacity(0.5 if self._pin_hov else 0.4)
            halo_c = QColor(0,255,128,180) if self._pinned else QColor(255,255,255,120)
            p.setBrush(QBrush(halo_c))
            p.drawEllipse(QPointF(dot_x, dot_y), r_vis+3.5, r_vis+3.5)
        p.restore()

    def _paint(self):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        v  = self._spring.v
        et = v*v*(3-2*v)
        if et < .005: p.end(); return
        W, H     = self._W, self._H
        cx, cy   = self._cx, self._cy
        side     = self.cfg["side"]
        Rt,Ri,Ro = self._radii()
        sign     = -1 if side=="right" else 1
        preset   = GLASS_PRESETS.get(self.cfg.get("glass_preset","Dark Obsidian"),
                                     GLASS_PRESETS["Dark Obsidian"])

        if preset.get("tint") == "dynamic":
            if not hasattr(self, "_dynamic_tint") or self._dynamic_tint is None:
                t1, t2 = self._get_wallpaper_tint()
                self._dynamic_tint = t1; self._dynamic_accent = t2
            tc  = QColor(*self._dynamic_tint)
            tc2 = QColor(*self._dynamic_accent)
        else:
            tc  = QColor(self.cfg.get("theme_color",  "#4c1d95"))
            tc2 = QColor(self.cfg.get("theme_color2", "#7c3aed"))

        # ── Guaranteed vivid glow color — rescues gray/green wallpaper tints ──
        # Blend tc2 toward a rich violet when it's desaturated (Dynamic Glass on neutral wallpapers)
        _PUR = (148, 72, 255)   # target violet
        _tc2_sat = max(tc2.hsvSaturationF(), 0.0)
        _tc2_val = max(tc2.valueF(), 0.0)
        _blend_f = max(0.0, min(1.0, 0.85 - _tc2_sat * 1.1))
        _vr = min(255, int(tc2.red()   * (1 - _blend_f) + _PUR[0] * _blend_f) + 25)
        _vg = min(255, int(tc2.green() * (1 - _blend_f) + _PUR[1] * _blend_f))
        _vb = min(255, int(tc2.blue()  * (1 - _blend_f) + _PUR[2] * _blend_f) + 40)
        vivid_c  = QColor(_vr, _vg, _vb)          # used for all glow halos & ring blooms
        vivid_c2 = vivid_c.lighter(140)
        self._vivid_c = vivid_c   # accessible in _draw_icon and _draw_center without signature change

        p.setClipRect(self.rect()); p.setPen(Qt.PenStyle.NoPen)

        # Blur layer removed as per user request for a cleaner look and better performance


        ba = preset["base_alpha"]
        if ba == "custom": ba = self.cfg.get("glass_custom_alpha", 100)

        p.setBrush(QBrush(QColor(0, 0, 0, int(ba * 0.15 * et))))
        p.drawPath(self._p_disk)

        tint = preset["tint"]
        if tint == "dynamic": tint = self._dynamic_tint
        if tint == "custom":
            c = QColor(self.cfg.get("glass_custom_color", "#ffffff"))
            tint = (c.red(), c.green(), c.blue())
        elif tint is None:
            tint = (tc.red(), tc.green(), tc.blue())

        # Tint layer - slightly more transparent (0.85 multiplier) to show the blur better
        p.setBrush(QBrush(QColor(*tint, int(ba * 0.85 * et))))
        p.drawPath(self._p_disk)

        if self.cfg.get("enable_3d_glow", True):
            # ── Deep space radial glow — adds the signature dark-purple depth ──
            deep_rg = QRadialGradient(cx + sign * Rt * 0.35, cy, Ro * 0.85)
            deep_rg.setColorAt(0.0, QColor(tc2.red(), tc2.green(), tc2.blue(), int(55 * et)))
            deep_rg.setColorAt(0.3, QColor(tc2.red(), tc2.green(), tc2.blue(), int(28 * et)))
            deep_rg.setColorAt(0.6, QColor(tc.red(), tc.green(), tc.blue(), int(20 * et)))
            deep_rg.setColorAt(1.0, QColor(0, 0, 0, int(70 * et)))
            p.setBrush(QBrush(deep_rg)); p.drawPath(self._p_disk)
            # ── Extra outer-edge nebula bloom ────────────────────────────────────
            edge_rg = QRadialGradient(cx, cy, Ro)
            edge_rg.setColorAt(0.72, QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), 0))
            edge_rg.setColorAt(0.88, QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(22 * et)))
            edge_rg.setColorAt(1.00, QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(8 * et)))
            p.setBrush(QBrush(edge_rg)); p.drawPath(self._p_disk)

        if self.cfg.get("gradient_anim", True):
            grad = QLinearGradient(cx, cy - Ro, cx, cy + Ro)
            off  = math.sin(self._grad_t * math.pi * 2) * 0.25
            grad.setColorAt(0, QColor(tc.red(), tc.green(), tc.blue(), int(ba * 0.3 * et)))
            grad.setColorAt(0.5 + off, QColor(tc2.red(), tc2.green(), tc2.blue(), int(ba * 0.7 * et)))
            grad.setColorAt(1, QColor(tc.red(), tc.green(), tc.blue(), int(ba * 0.3 * et)))
            p.setBrush(QBrush(grad)); p.drawPath(self._p_disk)

        fr = preset.get("frost", 25)
        if fr == "custom": fr = self.cfg.get("glass_custom_frost", 30)
        rg = QRadialGradient(cx, cy, Ro)
        rg.setColorAt(0.00, QColor(255,255,255, int(fr * 0.6 * et)))
        rg.setColorAt(1.00, QColor(0, 0, 0, int(fr * et)))
        p.setBrush(QBrush(rg)); p.drawPath(self._p_disk)

        if self.cfg.get("enable_3d_glow", True):
            # ── Orbital arc lines — faint glowing concentric rings like the reference image ──
            p.save()
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setClipPath(self._p_disk)
            _arc_start_qt = 90 if side == "right" else 270
            for _arc_frac, _arc_alpha in [(self.R_TAB, 28), (self.R_IN, 22), (self.R_OUT, 16)]:
                _arc_r = int(self._R * _arc_frac)
                _arc_rect = QRectF(cx - _arc_r, cy - _arc_r, _arc_r * 2, _arc_r * 2)
                # Soft outer bloom pass
                p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(_arc_alpha * et)), 8.0,
                               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(_arc_rect, _arc_start_qt * 16, 180 * 16)
                # Medium pass
                p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(_arc_alpha * 1.8 * et)), 3.0,
                               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(_arc_rect, _arc_start_qt * 16, 180 * 16)
                # Crisp thin bright line
                _arc_vc2 = vivid_c.lighter(155)
                p.setPen(QPen(QColor(_arc_vc2.red(), _arc_vc2.green(), _arc_vc2.blue(), int(min(255, _arc_alpha * 4.5) * et)), 0.7,
                               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(_arc_rect, _arc_start_qt * 16, 180 * 16)
            p.restore()

            p.setBrush(Qt.BrushStyle.NoBrush)
            # ── Outer ring — triple-pass glow using vivid_c ───────────────────────
            p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(18 * et)), 32))
            p.drawPath(self._p_outer)
            p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(38 * et)), 14))
            p.drawPath(self._p_outer)
            p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(65 * et)), 5))
            p.drawPath(self._p_outer)
            p.setPen(QPen(QColor(vivid_c2.red(), vivid_c2.green(), vivid_c2.blue(), int(230 * et)), 0.8))
            p.drawPath(self._p_outer)
            # ── Inner ring — triple-pass glow using vivid_c ───────────────────────
            vivid_c3 = vivid_c.lighter(170)
            p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(25 * et)), 24))
            p.drawPath(self._p_inner)
            p.setPen(QPen(QColor(vivid_c.red(), vivid_c.green(), vivid_c.blue(), int(50 * et)), 10))
            p.drawPath(self._p_inner)
            p.setPen(QPen(QColor(vivid_c3.red(), vivid_c3.green(), vivid_c3.blue(), int(240 * et)), 0.8))
            p.drawPath(self._p_inner)
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(tc2.red(), tc2.green(), tc2.blue(), int(35 * et)), 12))
            p.drawPath(self._p_outer)
            p.setPen(QPen(QColor(tc2.red(), tc2.green(), tc2.blue(), int(140 * et)), 1.5))
            p.drawPath(self._p_outer)
            p.setPen(QPen(QColor(tc2.red(), tc2.green(), tc2.blue(), int(160 * et)), 1.8))
            p.drawPath(self._p_inner)
            p.setPen(QPen(QColor(tc.red(), tc.green(), tc.blue(), int(80 * et)), 0.8))
            p.drawPath(self._p_inner)

        WEDGE_BASE = [tc.darker(110), tc, tc.darker(130)]
        for ti in range(3):
            active = (ti == self._tab)
            wp = self._p_tabs[ti]
            col = WEDGE_BASE[ti]
            p.setBrush(QBrush(QColor(col.red(),col.green(),col.blue(), int((205 if active else 125)*et))))
            p.setPen(Qt.PenStyle.NoPen); p.drawPath(wp)

            if self.cfg.get("enable_3d_glow", True):
                if active:
                    ws = QLinearGradient(0, 0, 0, H)
                    ts1, ts2 = vivid_c.lighter(160), vivid_c.lighter(110)
                    ws.setColorAt(0, QColor(ts1.red(),ts1.green(),ts1.blue(), int(70*et)))
                    ws.setColorAt(1, QColor(ts2.red(),ts2.green(),ts2.blue(), int(22*et)))
                    p.setBrush(QBrush(ws)); p.drawPath(wp)
                p.setBrush(Qt.BrushStyle.NoBrush)
                if active:
                    # Multi-pass glow border on active tab
                    p.setPen(QPen(QColor(vivid_c.red(),vivid_c.green(),vivid_c.blue(), int(38*et)), 8))
                    p.drawPath(wp)
                    p.setPen(QPen(QColor(vivid_c.red(),vivid_c.green(),vivid_c.blue(), int(90*et)), 2.5))
                    p.drawPath(wp)
                    p.setPen(QPen(QColor(vivid_c2.red(),vivid_c2.green(),vivid_c2.blue(), int(220*et)), 0.7))
                    p.drawPath(wp)
                else:
                    tbord = vivid_c.darker(130)
                    p.setPen(QPen(QColor(tbord.red(),tbord.green(),tbord.blue(), int(55*et)), 0.7))
                    p.drawPath(wp)
            else:
                if active:
                    ws = QLinearGradient(0, 0, 0, H)
                    ts1, ts2 = tc2.lighter(160), tc2.lighter(110)
                    ws.setColorAt(0, QColor(ts1.red(),ts1.green(),ts1.blue(), int(65*et)))
                    ws.setColorAt(1, QColor(ts2.red(),ts2.green(),ts2.blue(), int(20*et)))
                    p.setBrush(QBrush(ws)); p.drawPath(wp)
                p.setBrush(Qt.BrushStyle.NoBrush)
                tbord = tc.lighter(150)
                p.setPen(QPen(QColor(tbord.red(),tbord.green(),tbord.blue(), int(75*et)), 1))
                p.drawPath(wp)

            if side == "right": centers = [120, 180, 240]
            else: centers = [60, 0, 300]
            p.setFont(self._fb if active else self._ft)
            p.setPen(QColor(255,255,255, int((255 if active else 180)*et)))
            Rm = Rt * 0.81
            self._draw_curved_text(p, self.TABS[ti], cx, cy, Rm, centers[ti], et)

        self._draw_center(p, cx, cy, et, tc, tc2)
        self._draw_pin(p, et)

        if self._slider_mode:
            self._draw_slider(p, cx, cy, et, Ri, Ro, tc, tc2)

        items = self._items()
        inn, out, ni, oi, oo = self._all_pos(et)
        sz_in  = self.cfg.get("icon_size_inner", 42)
        sz_out = self.cfg.get("icon_size_outer", 48)
        for i,pos in enumerate(inn):
            if oi[i] > 0:
                self._draw_icon(p, i, *pos, items, sz_in, et, tc, tc2, oi[i])
        for j,pos in enumerate(out):
            if oo[j] > 0:
                self._draw_icon(p, ni+j, *pos, items, sz_out, et, tc, tc2, oo[j])

        # Drag-reorder ghost
        if self._edit and self._drag_idx >= 0 and self._drag_idx < len(items):
            it = items[self._drag_idx]
            if it.get("type","") not in ("placeholder","toggle_edit","add_btn","back_btn"):
                p.setOpacity(0.65)
                self._draw_icon(p, self._drag_idx, self._drag_px, self._drag_py,
                                items, sz_out, et, tc, tc2, 1.0)
                p.setOpacity(1.0)

        real = [x for x in items if x.get("type") not in
                ("toggle_edit","add_btn","back_btn","placeholder")]
        if not real:
            p.setPen(QPen(QColor(162,148,215,int(162*et))))
            p.setFont(QFont("Segoe UI",9))
            hint = ("Drop files/folders here\nor tap Edit → ➕ to add"
                    if self._tab==1 else "No recent apps yet")
            tx2 = cx + sign*int(Ro*0.55)
            p.drawText(QRect(tx2-90,cy-28,180,56), Qt.AlignmentFlag.AlignCenter, hint)


        p.end()

    def _get_wallpaper_tint(self):
        """Returns (primary_rgb, accent_rgb). Caches by file mtime."""
        try:
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.SystemParametersInfoW(0x0073, 512, buf, 0)
            wpath = buf.value
            if not wpath or not os.path.exists(wpath):
                wpath = os.path.join(os.environ.get("APPDATA",""),
                                     "Microsoft\\Windows\\Themes\\TranscodedWallpaper")
            if not os.path.exists(wpath):
                return (40,20,80), (124,58,237)

            # FIX: cache by mtime — only re-process when wallpaper actually changes
            mtime = os.path.getmtime(wpath)
            if mtime == self._wp_mtime and self._wp_tint is not None:
                return self._wp_tint, self._wp_accent

            from PIL import Image
            with Image.open(wpath) as img:
                img    = img.resize((32, 32), resample=Image.Resampling.BOX).convert("RGB")
                pixels = list(img.getdata())
                r_avg  = sum(px[0] for px in pixels) // len(pixels)
                g_avg  = sum(px[1] for px in pixels) // len(pixels)
                b_avg  = sum(px[2] for px in pixels) // len(pixels)
                vibrant = (124, 58, 237); max_v = -1
                for px in pixels[::4]:
                    v = max(px) - min(px)
                    if v > max_v: max_v = v; vibrant = px
                pri = (max(0,r_avg-30), max(0,g_avg-30), max(0,b_avg-30))
                acc = (min(255,vibrant[0]+20), min(255,vibrant[1]+20), min(255,vibrant[2]+20))

            self._wp_mtime  = mtime
            self._wp_tint   = pri
            self._wp_accent = acc
            return pri, acc
        except Exception as e:
            _log(f"Dynamic Tint Err: {e}")
            return (40,20,80), (124,58,237)

    def _draw_slider(self, p, cx, cy, et, Ri, Ro, tc, tc2):
        side  = self.cfg["side"]; sign = -1 if side=="right" else 1
        Rs    = int(self._R * 0.44); span = 180.; start = -90.
        rect  = QRectF(cx-Rs, cy-Rs, Rs*2, Rs*2)
        if side == "left":
            qs = int(start * 16); qf = int(span * 16)
        else:
            qs = int((180 - start) * 16); qf = int(-span * 16)
        p.setPen(QPen(QColor(255,255,255,int(35*et)), 10,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush); p.drawArc(rect, qs, qf)
        
        pct    = self._slider_val / 100.0
        filled = span * pct
        if side == "left": qf_f = int(filled * 16)
        else:              qf_f = int(-filled * 16)
        tcl    = tc.lighter(150)
        p.setPen(QPen(QColor(tcl.red(),tcl.green(),tcl.blue(),int(240*et)),
                      10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, qs, qf_f)
        tang = start + filled
        tx   = int(cx + sign*Rs*math.cos(math.radians(tang)))
        ty   = int(cy - Rs*math.sin(math.radians(tang)))
        
        knob_r = 16
        
        p.setBrush(QBrush(tcl))
        
        # Use theme accent color for the 'locked' state instead of green
        act_col = tc2.lighter(140)
        knob_pen_col = QColor(act_col.red(), act_col.green(), act_col.blue(), int(240*et)) if self._slider_locked else QColor(255, 255, 255, int(220*et))
        
        p.setPen(QPen(knob_pen_col, 2.5))
        p.drawEllipse(tx-knob_r, ty-knob_r, knob_r*2, knob_r*2)
        p.setPen(QPen(QColor(255,255,255,int(255*et))))
        p.setFont(QFont("Segoe UI", max(7, int(9*(self._R/230.0))), QFont.Weight.Bold))
        p.drawText(QRect(tx-knob_r, ty-knob_r, knob_r*2, knob_r*2),
                   Qt.AlignmentFlag.AlignCenter, f"{self._slider_val}")

        # ── Draw Lock Checkbox at the start of the bar (On Top) ─────────────
        lx = int(cx + sign*Rs*math.cos(math.radians(start)))
        ly = int(cy - Rs*math.sin(math.radians(start)))
        lr = 3.5 # Increased 40%
        self._lock_rect = QRectF(lx-15, ly-15, 30, 30) # Maintain large hit area
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._slider_locked:
            # Theme Radial Glow
            glow_r = 8.0
            gg = QRadialGradient(float(lx), float(ly), glow_r)
            gg.setColorAt(0, QColor(act_col.red(), act_col.green(), act_col.blue(), int(160*et)))
            gg.setColorAt(1, QColor(act_col.red(), act_col.green(), act_col.blue(), 0))
            p.setBrush(QBrush(gg)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(float(lx), float(ly)), glow_r, glow_r)
            
        # Use theme accent for the dot when locked, otherwise subtle white
        lock_color = QColor(act_col.red(), act_col.green(), act_col.blue(), int(255*et)) if self._slider_locked else QColor(255, 255, 255, int(150*et))
        if self._lock_hov: lock_color = lock_color.lighter(140)
        p.setBrush(lock_color)
        p.setPen(QPen(QColor(255, 255, 255, int(180*et)), 0.8))
        p.drawEllipse(QPointF(float(lx), float(ly)), lr, lr)
        p.restore()

    def _draw_icon(self, p, idx, ix, iy, items, sz, et, tc, tc2, op=1.0):
        if idx >= len(items): return
        item  = items[idx]; itype = item.get("type","")
        if itype == "placeholder":
            p.setBrush(QBrush(QColor(255,255,255,int(18*et))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(ix-sz//2,iy-sz//2,sz,sz); return
        is_spc = itype in ("toggle_edit","add_btn","back_btn")
        hov    = (idx == self._hov)
        # FIX: dynamically sized hover dict
        sc2    = self._hov_v.get(idx, 1.0)
        isz    = int(sz*sc2); half = isz//2

        if self.cfg.get("enable_3d_glow", True):
            gi  = self.cfg.get("glow_intensity", 1.0)
            if itype == "folder":   btn_c = QColor("#1a4a72"); brd_c = QColor("#5dade2")
            elif itype == "url":    btn_c = QColor("#0d4032"); brd_c = QColor("#1abc9c")
            elif itype == "script": btn_c = QColor("#3d1a00"); brd_c = QColor("#f97316")
            elif itype == "window": btn_c = QColor("#2e1065"); brd_c = QColor("#a78bfa")
            else:                   btn_c = tc.darker(110);    brd_c = tc2.lighter(160)

            bubble_r = float(half + 4)

            # ── Vivid glow color (always purple-biased regardless of wallpaper) ─
            vc  = getattr(self, "_vivid_c", QColor(148, 72, 255))
            vc2 = vc.lighter(145)

            # ── Ambient outer halo (always visible, brighter on hover) ───────
            glow_str = 0.6 if not hov else 1.0
            glow_r   = bubble_r + 14 + (28 * gi * glow_str)
            gh = QRadialGradient(float(ix), float(iy), glow_r)
            gh.setColorAt(0.0,  QColor(vc.red(),vc.green(),vc.blue(), int(100*et*op*glow_str*min(1.0,gi))))
            gh.setColorAt(0.35, QColor(vc.red(),vc.green(),vc.blue(), int(48*et*op*glow_str*min(1.0,gi))))
            gh.setColorAt(0.65, QColor(vc.red(),vc.green(),vc.blue(), int(14*et*op*glow_str*min(1.0,gi))))
            gh.setColorAt(1.0,  QColor(vc.red(),vc.green(),vc.blue(), 0))
            p.setBrush(QBrush(gh)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(ix-glow_r, iy-glow_r, glow_r*2, glow_r*2))

            # ── Deep glass fill (off-center radial: lighter at top-left) ────
            cx_f = ix - bubble_r * 0.22
            cy_f = iy - bubble_r * 0.22
            fill_g = QRadialGradient(cx_f, cy_f, bubble_r * 1.25)
            c_ctr  = btn_c.lighter(160)
            c_mid  = btn_c.lighter(115)
            c_edge = btn_c.darker(115)
            fill_g.setColorAt(0.0, QColor(c_ctr.red(), c_ctr.green(), c_ctr.blue(), int(210*et*op)))
            fill_g.setColorAt(0.5, QColor(c_mid.red(), c_mid.green(), c_mid.blue(), int(195*et*op)))
            fill_g.setColorAt(1.0, QColor(c_edge.red(), c_edge.green(), c_edge.blue(), int(230*et*op)))
            p.setBrush(QBrush(fill_g)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(ix-bubble_r, iy-bubble_r, bubble_r*2, bubble_r*2))

            # ── Multi-pass glowing ring border (vivid purple) ─────────────────
            p.setBrush(Qt.BrushStyle.NoBrush)
            # Pass 1: wide soft outer bloom
            p.setPen(QPen(QColor(vc.red(),vc.green(),vc.blue(),
                                  int((65 if hov else 35)*et*op)), 6.0))
            p.drawEllipse(QRectF(ix-bubble_r, iy-bubble_r, bubble_r*2, bubble_r*2))
            # Pass 2: medium ring
            p.setPen(QPen(QColor(vc.red(),vc.green(),vc.blue(),
                                  int((120 if hov else 68)*et*op)), 2.5))
            p.drawEllipse(QRectF(ix-bubble_r, iy-bubble_r, bubble_r*2, bubble_r*2))
            # Pass 3: crisp thin bright inner edge — THINNER border like image
            p.setPen(QPen(QColor(vc2.red(),vc2.green(),vc2.blue(),
                                  int((255 if hov else 200)*et*op)), 0.7))
            p.drawEllipse(QRectF(ix-bubble_r+1.0, iy-bubble_r+1.0, bubble_r*2-2, bubble_r*2-2))

            # ── Specular highlight (white crescent, top-left) ─────────────────
            sp_r  = bubble_r * 0.52
            sp_cx = ix - bubble_r * 0.28
            sp_cy = iy - bubble_r * 0.38
            sp_g  = QRadialGradient(sp_cx, sp_cy, sp_r)
            sp_g.setColorAt(0.0,  QColor(255, 255, 255, int(85*et*op)))
            sp_g.setColorAt(0.55, QColor(255, 255, 255, int(20*et*op)))
            sp_g.setColorAt(1.0,  QColor(255, 255, 255, 0))
            p.setBrush(QBrush(sp_g)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(sp_cx-sp_r, sp_cy-sp_r, sp_r*2, sp_r*2))
        else:
            if hov:
                gi  = self.cfg.get("glow_intensity", 1.0)
                glow_r = (half + 6) + (24 * gi)
                gh  = QRadialGradient(ix, iy, glow_r)
                tcl = tc.lighter(130)
                gh.setColorAt(0, QColor(tcl.red(),tcl.green(),tcl.blue(), int(95*et*min(1.0,gi))))
                gh.setColorAt(1, QColor(tcl.red(),tcl.green(),tcl.blue(), 0))
                p.setBrush(QBrush(gh)); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QRectF(ix-glow_r, iy-glow_r, glow_r*2, glow_r*2))
            if itype == "folder":   btn_c = QColor("#1a4a72"); brd_c = QColor("#5dade2")
            elif itype == "url":    btn_c = QColor("#0d4032"); brd_c = QColor("#1abc9c")
            elif itype == "script": btn_c = QColor("#3d1a00"); brd_c = QColor("#f97316")
            elif itype == "window": btn_c = QColor("#2e1065"); brd_c = QColor("#a78bfa")
            else:                   btn_c = tc.darker(110);    brd_c = tc.lighter(150)
            p.setBrush(QBrush(QColor(btn_c.red(),btn_c.green(),btn_c.blue(),int(195*et*op))))
            p.setPen(QPen(QColor(brd_c.red(),brd_c.green(),brd_c.blue(),
                                  int((230 if hov else 120)*et*op)), 1.5))
            p.drawEllipse(ix-half-4,iy-half-4,(half+4)*2,(half+4)*2)

        if is_spc or self._tab==2 or itype in ("url","folder","script","window"):
            # Use cached emoji/special pixmap
            ic = item.get("icon","●")
            key = f"emoji_{ic}"
            if key not in self._icache: self._warm_emoji(ic)
            
            cached_pm = self._icache.get(key)
            if cached_pm:
                psz = isz - 10
                p.drawPixmap(ix-psz//2, iy-psz//2, psz, psz, cached_pm)
            else:
                # Fallback (should not happen with pre-loader)
                p.setPen(QPen(QColor(255,255,255,int(252*et*op))))
                self._fe.setPointSize(max(9, isz//3))
                p.setFont(self._fe)
                p.drawText(QRect(ix-half,iy-half,isz,isz), Qt.AlignmentFlag.AlignCenter, ic)

            if itype=="folder":
                nc = len(item.get("children",[]))
                if nc > 0:
                    bx=ix+sz//2-4; by=iy-sz//2-4
                    p.setBrush(QBrush(QColor(92,173,226))); p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(bx-7,by-7,14,14)
                    p.setPen(QPen(QColor(255,255,255)))
                    p.setFont(QFont("Segoe UI",6,QFont.Weight.Bold))
                    p.drawText(QRect(bx-7,by-7,14,14), Qt.AlignmentFlag.AlignCenter, str(nc))
        else:
            b64   = item.get("icon_b64",""); nm = item.get("name","?"); emoji = item.get("icon","")
            if not b64 and emoji:
                key = f"emoji_{emoji}"
                if key not in self._icache: self._warm_emoji(emoji)
                cached_pm = self._icache.get(key)
                if cached_pm:
                    psz = isz - 10
                    p.drawPixmap(ix-psz//2, iy-psz//2, psz, psz, cached_pm)
                else:
                    p.setPen(QPen(QColor(255,255,255,int(252*et*op))))
                    self._fe.setPointSize(max(9, isz//3))
                    p.setFont(self._fe)
                    p.drawText(QRect(ix-half,iy-half,isz,isz), Qt.AlignmentFlag.AlignCenter, emoji)
            else:
                # ICON CACHING SYSTEM: prevents redundant base64 decoding every frame
                psz = isz - 16
                key = b64 if b64 else f"text_{nm[:1]}"
                if key not in self._icache:
                    # Optimized resolution (64px) for lower RAM footprint
                    self._icache[key] = b64_pm(b64, 64) if b64 else make_pm(64, nm[:1])
                
                cached_pm = self._icache[key]
                p.drawPixmap(ix-psz//2, iy-psz//2, psz, psz, cached_pm)
        is_removable = (self._tab in (0, 1, 2))
        if self._edit and itype not in ("add_btn","toggle_edit","back_btn","placeholder") and is_removable:
            bx=ix+sz//2-6; by=iy-sz//2-6
            p.setBrush(QBrush(QColor(239,68,68))); p.setPen(QPen(QColor(255,255,255),1.5))
            p.drawEllipse(bx-8,by-8,16,16)
            p.setPen(QPen(QColor(255,255,255)))
            p.setFont(QFont("Segoe UI",7,QFont.Weight.Bold))
            p.drawText(QRect(bx-8,by-8,16,16), Qt.AlignmentFlag.AlignCenter,"×")
        if self._rip==idx and self._rip_t>0:
            rr  = int(half*(1+(1-self._rip_t)*2.2))
            al  = int(self._rip_t*160)
            tcl = tc.lighter(140)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(tcl.red(),tcl.green(),tcl.blue(),al),2))
            p.drawEllipse(ix-rr,iy-rr,rr*2,rr*2)
        lbl = item.get("name","")[:12]
        p.setPen(QPen(QColor(215,200,248,int(205*et))))
        p.setFont(QFont("Segoe UI",6))
        p.drawText(QRect(ix-36,iy+half+5,72,15), Qt.AlignmentFlag.AlignCenter, lbl)


class OverlayPanel(QWidget):
    """
    A full-screen overlay window.
    Shows the power options panel centered on the active screen.
    """
    closed = pyqtSignal()

    CARD_SS = """
        QFrame#ocard {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 rgba(16,12,45,252), stop:1 rgba(8,5,25,255));
            border: 1.5px solid rgba(124,58,237,200);
            border-radius: 18px;
        }
        QLineEdit, QTextEdit {
            background: rgba(255,255,255,10);
            color: #e2e8f0;
            border: 1px solid rgba(124,58,237,80);
            border-radius: 7px;
            font-family: 'Segoe UI';
            font-size: 10pt;
            padding: 4px 8px;
            selection-background-color: #7c3aed;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid rgba(124,58,237,220);
            background: rgba(255,255,255,14);
        }
    """

    BTN_SS = ("QPushButton{background:rgba(124,58,237,80);color:#e2e8f0;"
              "border-radius:8px;font-family:'Segoe UI';font-size:9pt;"
              "border:1px solid rgba(124,58,237,120);padding:0 10px;}"
              "QPushButton:hover{background:rgba(124,58,237,180);color:#fff;}")

    _POWER_ICONS  = {"shutdown":"⏻","restart":"🔃","hibernate":"❄️","sleep":"💤","lock":"🔒","awake":"☕"}
    _POWER_LABELS = {"shutdown":"Shutdown","restart":"Restart","hibernate":"Hibernate","sleep":"Sleep","lock":"Lock PC","awake":"Awake Mode"}

    def __init__(self, launcher):
        super().__init__(launcher,
            Qt.WindowType.FramelessWindowHint  |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool                 |
            Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._launcher = launcher
        self._current_panel = None
        self._stack = {}
        self._power_remaining = 0
        self._power_ticking = False
        self._power_mode = "shutdown"
        self._awake_active = False
        self._tmr_tick = QTimer(self)
        self._tmr_tick.timeout.connect(self._on_tick)
        self.hide()

    def show_panel(self, name, **kwargs):
        self._current_panel = name
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        geom = screen.geometry()
        self.setGeometry(geom)
        if name in self._stack:
            self._stack[name].deleteLater()
        builder = getattr(self, f"_build_{name}", None)
        if builder is None:
            return
        panel_w = builder(**kwargs)
        if panel_w is None:
            return
        self._stack[name] = panel_w
        panel_w.setParent(self)
        pw = panel_w.width()
        ph = panel_w.height()
        panel_w.setFixedSize(pw, ph)
        panel_w.move((self.width() - pw) // 2, (self.height() - ph) // 2)
        panel_w.show()
        self._launcher._in_dialog = True
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(0, lambda: self._focus_first(panel_w))

    def _focus_first(self, widget):
        for w in widget.findChildren(QLineEdit):
            if w.isVisible() and w.isEnabled():
                w.setFocus(Qt.FocusReason.OtherFocusReason)
                return

    def close_panel(self):
        name = self._current_panel
        if name and name in self._stack:
            self._stack[name].hide()
        self._current_panel = None
        self.hide()
        self._launcher._in_dialog = False
        self.closed.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 140))

    def mousePressEvent(self, e):
        if self._current_panel and self._current_panel in self._stack:
            pw = self._stack[self._current_panel]
            if not pw.geometry().contains(e.pos()):
                self.close_panel()
                return
        super().mousePressEvent(e)

    def _make_card(self, title_icon, title_text, width=360, height=330):
        w = QWidget(self)
        w.setFixedSize(width, height)
        ss = self.CARD_SS
        outer_l = QVBoxLayout(w)
        outer_l.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("ocard")
        card.setStyleSheet(ss)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 14)
        cl.setSpacing(8)
        
        # Header
        hdr = QHBoxLayout()
        color = "#c4b5fd"
        ttl = QLabel(f"{title_icon}  {title_text}")
        ttl.setStyleSheet(f"color:{color};font-size:14px;font-weight:bold;font-family:'Segoe UI';")
        hdr.addWidget(ttl)
        hdr.addStretch()
        
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(30, 30)
        btn_x.setStyleSheet("QPushButton{background:transparent;color:#94a3b8;border:none;"
                            "border-radius:8px;font-weight:bold;font-size:11pt;}"
                            "QPushButton:hover{background:#dc2626;color:white;}")
        btn_x.clicked.connect(self.close_panel)
        hdr.addWidget(btn_x)
        cl.addLayout(hdr)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(124,58,237,80);max-height:1px;")
        cl.addWidget(sep)
        
        outer_l.addWidget(card)
        return w, cl

    def _build_power(self, mode="shutdown"):
        self._power_mode = mode
        icon  = self._POWER_ICONS.get(mode, "⏻")
        label = self._POWER_LABELS.get(mode, "Power")
        w, cl = self._make_card(icon, label, width=390, height=330)

        # Mode switcher
        mrow = QHBoxLayout()
        mrow.setSpacing(5)
        self._pw_mode_btns = {}
        
        # Switcher style
        PURPLE_TAB = ("QPushButton{background:rgba(124,58,237,50);color:#c4b5fd;border-radius:7px;"
                      "font-family:'Segoe UI';font-size:11pt;border:1px solid rgba(124,58,237,70);}"
                      "QPushButton:checked{background:rgba(124,58,237,180);color:#fff;}"
                      "QPushButton:hover{background:rgba(124,58,237,110);}")
        
        for m, ico in self._POWER_ICONS.items():
            b = QPushButton(ico)
            b.setCheckable(True)
            b.setChecked(m == mode)
            b.setFixedHeight(30)
            b.setStyleSheet(PURPLE_TAB)
            b.clicked.connect(lambda _, mo=m: self._pw_switch(mo))
            mrow.addWidget(b)
            self._pw_mode_btns[m] = b
        cl.addLayout(mrow)

        if mode == "awake":
            # Awake Mode UI
            desc = QLabel("Prevents your computer from sleeping or turning off the screen. "
                          "Keep OrbitSwipe running to maintain Awake Mode.")
            desc.setWordWrap(True)
            desc.setStyleSheet("color:#94a3b8;font-family:'Segoe UI';font-size:9.5pt;margin-top:5px;margin-bottom:10px;")
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(desc)

            cl.addStretch()

            self._awake_btn = QPushButton()
            self._awake_btn.setFixedHeight(40)
            self._update_awake_btn_style()
            self._awake_btn.clicked.connect(self._toggle_awake)
            cl.addWidget(self._awake_btn)
            return w

        # Now vs Schedule tabs
        trow = QHBoxLayout()
        trow.setSpacing(6)
        TTAB = ("QPushButton{background:rgba(124,58,237,40);color:#c4b5fd;border-radius:7px;"
                "font-family:'Segoe UI';font-size:9pt;border:1px solid rgba(124,58,237,60);}"
                "QPushButton:checked{background:rgba(124,58,237,160);color:#fff;}"
                "QPushButton:hover{background:rgba(124,58,237,100);}")
        self._pw_now_btn   = QPushButton("⚡ Now")
        self._pw_now_btn.setCheckable(True)
        self._pw_now_btn.setChecked(True)
        self._pw_sched_btn = QPushButton("🕐 Schedule")
        self._pw_sched_btn.setCheckable(True)
        for b in (self._pw_now_btn, self._pw_sched_btn):
            b.setFixedHeight(28)
            b.setStyleSheet(TTAB)
        self._pw_now_btn.clicked.connect(lambda: self._pw_set_now(True))
        self._pw_sched_btn.clicked.connect(lambda: self._pw_set_now(False))
        trow.addWidget(self._pw_now_btn)
        trow.addWidget(self._pw_sched_btn)
        cl.addLayout(trow)

        # Schedule panel
        self._pw_sched_panel = QWidget()
        sched_v = QVBoxLayout(self._pw_sched_panel)
        # Shift down by 33px top margin to utilize bottom space and move bottomward
        sched_v.setContentsMargins(0, 33, 0, 0)
        sched_v.setSpacing(10)

        # Row 1: Time Inputs + Reset Button (Centered)
        trow2 = QHBoxLayout()
        trow2.setSpacing(5)
        trow2.addStretch()

        lbl_time = QLabel("Time:")
        lbl_time.setStyleSheet("color:#94a3b8;font-family:'Segoe UI';font-size:9.5pt;font-weight:bold;")
        trow2.addWidget(lbl_time)

        self._pw_h = QLineEdit("0")
        self._pw_h.setFixedWidth(36)
        self._pw_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pw_m = QLineEdit("10")
        self._pw_m.setFixedWidth(36)
        self._pw_m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pw_s = QLineEdit("0")
        self._pw_s.setFixedWidth(36)
        self._pw_s.setAlignment(Qt.AlignmentFlag.AlignCenter)

        trow2.addWidget(self._pw_h)
        lb_h = QLabel("h")
        lb_h.setStyleSheet("color:#64748b;font-family:'Segoe UI';font-size:9.5pt;")
        trow2.addWidget(lb_h)

        trow2.addWidget(self._pw_m)
        lb_m = QLabel("m")
        lb_m.setStyleSheet("color:#64748b;font-family:'Segoe UI';font-size:9.5pt;")
        trow2.addWidget(lb_m)

        trow2.addWidget(self._pw_s)
        lb_s = QLabel("s")
        lb_s.setStyleSheet("color:#64748b;font-family:'Segoe UI';font-size:9.5pt;")
        trow2.addWidget(lb_s)

        # Reset button right after the seconds input field with small gap
        self._pw_reset_btn = QPushButton("Reset")
        self._pw_reset_btn.setFixedSize(50, 24)
        self._pw_reset_btn.setStyleSheet(
            "QPushButton{background:rgba(124,58,237,30);color:#c4b5fd;"
            "border:1px solid rgba(124,58,237,60);border-radius:6px;"
            "font-family:'Segoe UI';font-size:9pt;font-weight:bold;}"
            "QPushButton:hover{background:rgba(124,58,237,80);color:#fff;}"
        )
        self._pw_reset_btn.clicked.connect(self._pw_reset)

        trow2.addSpacing(8)
        trow2.addWidget(self._pw_reset_btn)
        trow2.addStretch()
        sched_v.addLayout(trow2)

        # Row 2: Presets (Centered)
        prow = QHBoxLayout()
        prow.setSpacing(5)
        prow.addStretch()

        lbl_quick = QLabel("Quick:")
        lbl_quick.setStyleSheet("color:#94a3b8;font-family:'Segoe UI';font-size:9.5pt;font-weight:bold;")
        prow.addWidget(lbl_quick)

        for lbl, m in [("5m", 5), ("15m", 15), ("30m", 30), ("1h", 60), ("2h", 120)]:
            pb = QPushButton(lbl)
            pb.setFixedSize(36, 24)
            pb.setStyleSheet("QPushButton{background:rgba(124,58,237,40);color:#c4b5fd;border-radius:5px;"
                             "font-family:'Segoe UI';font-size:8pt;border:1px solid rgba(124,58,237,60);}"
                             "QPushButton:hover{background:rgba(124,58,237,120);color:#fff;}")
            pb.clicked.connect(lambda _, mi=m: (self._pw_m.setText(str(mi)), self._pw_h.setText("0"), self._pw_s.setText("0")))
            prow.addWidget(pb)

        prow.addStretch()
        sched_v.addLayout(prow)

        self._pw_sched_panel.setVisible(False)
        cl.addWidget(self._pw_sched_panel)

        # Countdown label
        self._pw_cd_lbl = QLabel("")
        self._pw_cd_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pw_cd_lbl.setStyleSheet("color:#c4b5fd;font-size:20pt;font-family:'Segoe UI';font-weight:bold;")
        self._pw_cd_lbl.setVisible(self._power_ticking)
        if self._power_ticking:
            self._update_power_cd()
        cl.addWidget(self._pw_cd_lbl)

        cl.addStretch()

        # Go button
        self._pw_go_btn = QPushButton(f"  {icon}  {label}")
        self._pw_go_btn.setFixedHeight(40)
        self._pw_go_btn.setStyleSheet(
            "QPushButton{background:rgba(124,58,237,200);color:#fff;border-radius:8px;"
            "font-family:'Segoe UI';font-size:10pt;font-weight:bold;"
            "border:1px solid rgba(124,58,237,255);}"
            "QPushButton:hover{background:#6d28d9;}")
        self._pw_go_btn.clicked.connect(self._pw_execute)
        cl.addWidget(self._pw_go_btn)

        # Cancel scheduled
        self._pw_cancel_btn = QPushButton("✕  Cancel Scheduled Action")
        self._pw_cancel_btn.setFixedHeight(32)
        self._pw_cancel_btn.setStyleSheet(self.BTN_SS)
        self._pw_cancel_btn.setVisible(self._power_ticking)
        self._pw_cancel_btn.clicked.connect(self._pw_cancel)
        cl.addWidget(self._pw_cancel_btn)
        return w

    def _pw_switch(self, mode):
        self._power_mode = mode
        self.show_panel("power", mode=mode)

    def _pw_set_now(self, is_now):
        self._pw_now_btn.setChecked(is_now)
        self._pw_sched_btn.setChecked(not is_now)
        self._pw_sched_panel.setVisible(not is_now)
        self._reposition()

    def _pw_execute(self):
        if self._pw_now_btn.isChecked():
            self._run_power(self._power_mode)
            self.close_panel()
        else:
            try:
                h = int(self._pw_h.text() or 0)
                m = int(self._pw_m.text() or 0)
                s = int(self._pw_s.text() or 0)
                total = h * 3600 + m * 60 + s
            except:
                total = 600
            if total <= 0:
                total = 60
            self._power_remaining = total
            self._power_ticking = True
            if self._power_mode in ("shutdown", "restart"):
                flag = "/s" if self._power_mode == "shutdown" else "/r"
                try:
                    subprocess.Popen(f"shutdown {flag} /t {total}", shell=True, creationflags=0x08000000)
                except:
                    pass
            if not self._tmr_tick.isActive():
                self._tmr_tick.start(1000)
            self._pw_cd_lbl.setVisible(True)
            self._pw_cancel_btn.setVisible(True)
            self._update_power_cd()

    def _pw_cancel(self):
        self._power_ticking = False
        self._power_remaining = 0
        self._tmr_tick.stop()
        self._pw_cd_lbl.setVisible(False)
        self._pw_cancel_btn.setVisible(False)
        try:
            subprocess.Popen("shutdown /a", shell=True, creationflags=0x08000000)
        except:
            pass

    def _pw_reset(self):
        if hasattr(self, "_pw_h"): self._pw_h.setText("0")
        if hasattr(self, "_pw_m"): self._pw_m.setText("10")
        if hasattr(self, "_pw_s"): self._pw_s.setText("0")

    def _update_power_cd(self):
        if not hasattr(self, "_pw_cd_lbl"):
            return
        s = self._power_remaining
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        ico = self._POWER_ICONS.get(self._power_mode, "⏻")
        self._pw_cd_lbl.setText(f"{ico}  {h:02d}:{m:02d}:{sec:02d}" if h else f"{ico}  {m:02d}:{sec:02d}")

    @staticmethod
    def _run_power(mode):
        CF = 0x08000000
        try:
            if mode == "shutdown":
                subprocess.Popen("shutdown /s /t 0", shell=True, creationflags=CF)
            elif mode == "restart":
                subprocess.Popen("shutdown /r /t 0", shell=True, creationflags=CF)
            elif mode == "hibernate":
                subprocess.Popen("shutdown /h", shell=True, creationflags=CF)
            elif mode == "sleep":
                subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True, creationflags=CF)
            elif mode == "lock":
                ctypes.windll.user32.LockWorkStation()
        except:
            pass

    def _on_tick(self):
        # Power countdown ticking
        if self._power_ticking:
            self._power_remaining -= 1
            self._update_power_cd()
            if self._power_remaining <= 0:
                self._power_ticking = False
                self._tmr_tick.stop()
                if self._power_mode in ("hibernate", "sleep", "lock"):
                    self._run_power(self._power_mode)
                self.close_panel()

    def _reposition(self):
        if self._current_panel and self._current_panel in self._stack:
            pw = self._stack[self._current_panel]
            pw.move((self.width() - pw.width()) // 2, (self.height() - pw.height()) // 2)

    def _toggle_awake(self):
        self._awake_active = not self._awake_active
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        try:
            if self._awake_active:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception as e:
            _log(f"SetThreadExecutionState error: {e}")
        self._update_awake_btn_style()

    def _update_awake_btn_style(self):
        if not hasattr(self, "_awake_btn"):
            return
        if self._awake_active:
            self._awake_btn.setText("☕  Awake Mode: ACTIVE")
            self._awake_btn.setStyleSheet(
                "QPushButton{background:#10b981;color:#fff;border-radius:8px;"
                "font-family:'Segoe UI';font-size:10pt;font-weight:bold;"
                "border:1px solid #059669;}"
                "QPushButton:hover{background:#059669;}")
        else:
            self._awake_btn.setText("🔌  Enable Awake Mode")
            self._awake_btn.setStyleSheet(
                "QPushButton{background:rgba(124,58,237,80);color:#e2e8f0;border-radius:8px;"
                "font-family:'Segoe UI';font-size:10pt;font-weight:bold;"
                "border:1px solid rgba(124,58,237,120);}"
                "QPushButton:hover{background:rgba(124,58,237,180);color:#fff;}")



