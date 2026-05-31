import os
import sys
import time
import base64
import subprocess
import urllib.request
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QApplication,
                             QScrollArea, QWidget, QListWidget, QListWidgetItem,
                             QFileDialog, QScroller)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QRect, QPoint, QSize, QEvent, QPointF, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QBrush, QPen, QPainterPath, QAction

from orbitswipe.core.constants import APP_NAME, APP_VERSION, TRIAL_DAYS
from orbitswipe.core.utils import _log, extract_icon_png
from orbitswipe.core.engine import make_pm
from orbitswipe.core.license import _get_trial_info, activate_license, get_license_status
from orbitswipe.ui.utils import make_tray_icon

_DSS = "background:#13132b;border-radius:16px;border:1.5px solid #2e1065;"
_LSS = "color:#e2e8f0;font-family:'Segoe UI';border:none;"
_ESS = ("QLineEdit{background:#1e1b4b;color:#e2e8f0;border:1px solid #7c3aed;"
        "border-radius:8px;padding:8px 12px;font-family:'Segoe UI';font-size:10pt;"
        "min-height:30px;}")
_BSS = ("QPushButton{background:#7c3aed;color:white;border-radius:8px;border:none;"
        "padding:6px 18px;font-family:'Segoe UI';font-weight:bold;}"
        "QPushButton:hover{background:#6d28d9;}")
_XSS = ("QPushButton{background:#dc2626;color:white;border-radius:6px;border:none;}"
        "QPushButton:hover{background:#ef4444;}")

class AddUrlDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌐 Add Web Link")
        self.setFixedWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.result_url = ""; self.result_name = ""; self.favicon_b64 = ""
        
        lo = QVBoxLayout(self)
        self.cont = QWidget(); self.cont.setObjectName("cont")
        self.cont.setStyleSheet("""
            #cont { background: #130d2b; border: 2px solid #7c3aed; border-radius: 15px; }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; }
            QLineEdit { background: #1e1b4b; color: #fff; border: 1px solid #4438ca;
                       border-radius: 6px; padding: 6px; font-size: 10pt; }
            QPushButton { background: #4438ca; color: #fff; border-radius: 6px;
                         padding: 8px; font-weight: bold; }
            QPushButton:hover { background: #6366f1; }
        """)
        
        clo = QVBoxLayout(self.cont); lo.addWidget(self.cont)
        
        hdr = QHBoxLayout()
        icon_lbl = QLabel("🌐"); icon_lbl.setStyleSheet("font-size: 14pt; border: none;")
        hdr.addWidget(icon_lbl)
        ttl = QLabel("Add Web Link"); ttl.setStyleSheet("font-size: 12pt; font-weight: bold; border: none;")
        hdr.addWidget(ttl); hdr.addStretch()
        qbtn = QPushButton("✕"); qbtn.setFixedWidth(40); qbtn.clicked.connect(self.reject)
        qbtn.setStyleSheet("background: #ef4444; border: none; border-radius: 6px;")
        hdr.addWidget(qbtn)
        clo.addLayout(hdr)
        
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #7c3aed; max-height: 1px; border: none; margin: 5px 0;")
        clo.addWidget(line)

        clo.addWidget(QLabel("Display Name:"))
        self._ne = QLineEdit(); self._ne.setPlaceholderText("e.g.  Google")
        clo.addWidget(self._ne)
        
        clo.addSpacing(10)
        clo.addWidget(QLabel("URL:"))
        self._ue = QLineEdit(); self._ue.setPlaceholderText("https://…")
        clo.addWidget(self._ue)
        
        clo.addSpacing(15)
        btn_lo = QHBoxLayout()
        btn_lo.addStretch()
        ok_btn = QPushButton("✨ Add Link"); ok_btn.setMinimumWidth(140)
        ok_btn.clicked.connect(self._go)
        btn_lo.addWidget(ok_btn)
        clo.addLayout(btn_lo)
        
        sc = QApplication.primaryScreen().availableGeometry()
        self.move(sc.x() + (sc.width() - self.sizeHint().width()) // 2, 
                  sc.y() + (sc.height() - self.sizeHint().height()) // 2)

    def _go(self):
        url  = self._ue.text().strip()
        name = self._ne.text().strip()
        if url:
            if not url.startswith(("http://","https://")): url = "https://"+url
            if not name:
                try: name = url.split("/")[2].replace("www.","")
                except: name = url[:24]
            self.result_url  = url
            self.result_name = name
            self.favicon_b64 = ""
            def _fetch():
                try:
                    from urllib.request import urlopen, Request
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    base   = f"{parsed.scheme}://{parsed.netloc}"
                    req = Request(
                        f"https://www.google.com/s2/favicons?sz=64&domain_url={base}",
                        headers={"User-Agent":"Mozilla/5.0"})
                    self.favicon_b64 = base64.b64encode(
                        urlopen(req, timeout=5).read()).decode()
                except Exception: pass
            threading.Thread(target=_fetch, daemon=True).start()
            self.accept()



class AddFolderDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📂 Create App Folder")
        self.setFixedWidth(370)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.result_name = ""
        
        lo = QVBoxLayout(self)
        self.cont = QWidget(); self.cont.setObjectName("cont")
        self.cont.setStyleSheet("""
            #cont { background: #130d2b; border: 2px solid #7c3aed; border-radius: 15px; }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; }
            QLineEdit { background: #1e1b4b; color: #fff; border: 1px solid #4438ca;
                       border-radius: 6px; padding: 6px; font-size: 10pt; }
            QPushButton { background: #4438ca; color: #fff; border-radius: 6px;
                         padding: 8px; font-weight: bold; }
            QPushButton:hover { background: #6366f1; }
        """)
        
        clo = QVBoxLayout(self.cont); lo.addWidget(self.cont)
        
        hdr = QHBoxLayout()
        icon_lbl = QLabel("📂"); icon_lbl.setStyleSheet("font-size: 14pt; border: none;")
        hdr.addWidget(icon_lbl)
        ttl = QLabel("Create App Folder"); ttl.setStyleSheet("font-size: 12pt; font-weight: bold; border: none;")
        hdr.addWidget(ttl); hdr.addStretch()
        qbtn = QPushButton("✕"); qbtn.setFixedWidth(40); qbtn.clicked.connect(self.reject)
        qbtn.setStyleSheet("background: #ef4444; border: none; border-radius: 6px;")
        hdr.addWidget(qbtn)
        clo.addLayout(hdr)
        
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #7c3aed; max-height: 1px; border: none; margin: 5px 0;")
        clo.addWidget(line)

        clo.addWidget(QLabel("Folder Name:"))
        self._ne = QLineEdit(); self._ne.setPlaceholderText("e.g.  Work Tools")
        clo.addWidget(self._ne)
        
        clo.addSpacing(15)
        btn_lo = QHBoxLayout()
        btn_lo.addStretch()
        ok_btn = QPushButton("✨ Create Folder"); ok_btn.setMinimumWidth(140)
        ok_btn.clicked.connect(self._go)
        btn_lo.addWidget(ok_btn)
        clo.addLayout(btn_lo)

        sc = QApplication.primaryScreen().availableGeometry()
        self.move(sc.x() + (sc.width() - self.sizeHint().width()) // 2, 
                  sc.y() + (sc.height() - self.sizeHint().height()) // 2)

    def _go(self):
        n = self._ne.text().strip()
        if n: self.result_name = n; self.accept()

# ── NEW: Custom Script Dialog ──────────────────────────────────────────────


class AddScriptDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📜 Add Custom Script")
        self.setFixedWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.result_name = ""; self.result_path = ""; self.result_icon = "📜"
        
        lo = QVBoxLayout(self)
        self.cont = QWidget(); self.cont.setObjectName("cont")
        self.cont.setStyleSheet("""
            #cont { background: #130d2b; border: 2px solid #7c3aed; border-radius: 15px; }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; }
            QLineEdit { background: #1e1b4b; color: #fff; border: 1px solid #4438ca;
                       border-radius: 6px; padding: 6px; font-size: 10pt; }
            QPushButton { background: #4438ca; color: #fff; border-radius: 6px;
                         padding: 8px; font-weight: bold; }
            QPushButton:hover { background: #6366f1; }
        """)
        
        clo = QVBoxLayout(self.cont); lo.addWidget(self.cont)
        
        hdr = QHBoxLayout()
        icon_lbl = QLabel("📜"); icon_lbl.setStyleSheet("font-size: 14pt; border: none;")
        hdr.addWidget(icon_lbl)
        ttl = QLabel("Add Custom Script"); ttl.setStyleSheet("font-size: 12pt; font-weight: bold; border: none;")
        hdr.addWidget(ttl); hdr.addStretch()
        qbtn = QPushButton("✕"); qbtn.setFixedWidth(40); qbtn.clicked.connect(self.reject)
        qbtn.setStyleSheet("background: #ef4444; border: none; border-radius: 6px;")
        hdr.addWidget(qbtn)
        clo.addLayout(hdr)
        
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #7c3aed; max-height: 1px; border: none; margin: 5px 0;")
        clo.addWidget(line)

        clo.addWidget(QLabel("Display Name:"))
        self._ne = QLineEdit(); self._ne.setPlaceholderText("e.g. Daily Backup")
        clo.addWidget(self._ne)
        
        clo.addSpacing(10)
        clo.addWidget(QLabel("Script Path (.ps1, .bat, .cmd, .py, .exe):"))
        row_p = QHBoxLayout()
        self._pe = QLineEdit(); self._pe.setPlaceholderText("Paste path or browse...")
        row_p.addWidget(self._pe)
        pbtn = QPushButton("📂"); pbtn.setFixedWidth(44); pbtn.clicked.connect(self._browse)
        row_p.addWidget(pbtn)
        clo.addLayout(row_p)
        
        clo.addSpacing(10)
        clo.addWidget(QLabel("Emoji Icon (optional):"))
        self._ie = QLineEdit(); self._ie.setPlaceholderText("📜")
        self._ie.setMaxLength(4)
        clo.addWidget(self._ie)
        
        clo.addSpacing(15)
        btn_lo = QHBoxLayout()
        btn_lo.addStretch()
        cbtn = QPushButton("✨ Add Script"); cbtn.setMinimumWidth(140)
        cbtn.clicked.connect(self._go)
        btn_lo.addWidget(cbtn)
        clo.addLayout(btn_lo)
        
        sc = QApplication.primaryScreen().availableGeometry()
        self.move(sc.x() + (sc.width() - 400) // 2, 
                  sc.y() + (sc.height() - self.sizeHint().height()) // 2)

    def _browse(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Script", "",
                   "Scripts (*.ps1 *.bat *.cmd *.py *.exe);;All Files (*.*)")
        if fp:
            self._pe.setText(os.path.normpath(fp))
            if not self._ne.text():
                self._ne.setText(os.path.splitext(os.path.basename(fp))[0])

    def _go(self):
        name = self._ne.text().strip()
        path = self._pe.text().strip()
        if name and path:
            self.result_name = name
            self.result_path = path
            icon = self._ie.text().strip()
            if icon: self.result_icon = icon
            self.accept()



class AddWorkspaceDlg(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("🚀 Create App Group")
        self.setFixedWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.paths = []; self.result_name = ""
        
        lo = QVBoxLayout(self)
        self.cont = QWidget(); self.cont.setObjectName("cont")
        self.cont.setStyleSheet("""
            #cont { background: #130d2b; border: 2px solid #7c3aed; border-radius: 15px; }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; }
            QLineEdit { background: #1e1b4b; color: #fff; border: 1px solid #4438ca;
                       border-radius: 6px; padding: 6px; font-size: 10pt; }
            QPushButton { background: #4438ca; color: #fff; border-radius: 6px;
                         padding: 8px; font-weight: bold; }
            QPushButton:hover { background: #6366f1; }
            #rm_btn { background: #ef4444; border-radius: 4px; padding: 2px; font-size: 8pt; }
            #rm_btn:hover { background: #f87171; }
        """)
        
        clo = QVBoxLayout(self.cont); lo.addWidget(self.cont)
        
        hdr = QHBoxLayout()
        icon_lbl = QLabel("🚀"); icon_lbl.setStyleSheet("font-size: 14pt; border: none;")
        hdr.addWidget(icon_lbl)
        ttl = QLabel("Create App Group"); ttl.setStyleSheet("font-size: 12pt; font-weight: bold; border: none;")
        hdr.addWidget(ttl); hdr.addStretch()
        qbtn = QPushButton("✕"); qbtn.setFixedWidth(40); qbtn.clicked.connect(self.reject)
        qbtn.setStyleSheet("background: #ef4444; border: none; border-radius: 6px;")
        hdr.addWidget(qbtn)
        clo.addLayout(hdr)
        
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #7c3aed; max-height: 1px; border: none; margin: 5px 0;")
        clo.addWidget(line)

        clo.addWidget(QLabel("Group Name:"))
        self.ne = QLineEdit(); self.ne.setPlaceholderText("e.g. Daily Work / Gaming Mode"); clo.addWidget(self.ne)
        clo.addSpacing(10); clo.addWidget(QLabel("Search Apps to Add:"))
        self.se = QLineEdit(); self.se.setPlaceholderText("Type app name..."); clo.addWidget(self.se)
        self.slist = QListWidget()
        self.slist.setStyleSheet("QListWidget{background:#1e1b4b; border:none; border-radius:6px; color:#cbd5e1;}")
        self.slist.setFixedHeight(80); self.slist.hide(); clo.addWidget(self.slist)
        clo.addSpacing(10); clo.addWidget(QLabel("Current Group Items:"))
        self.plist = QListWidget()
        self.plist.setStyleSheet("QListWidget{background:#1e1b4b; border:none; border-radius:6px; color:#cbd5e1;}")
        self.plist.setFixedHeight(100); clo.addWidget(self.plist)
        btn_lo = QHBoxLayout()
        abtn = QPushButton("📂 Browse Files"); abtn.clicked.connect(self._add_files)
        cbtn = QPushButton("✨ Create Group"); cbtn.clicked.connect(self._done)
        btn_lo.addWidget(abtn); btn_lo.addWidget(cbtn)
        clo.addLayout(btn_lo)
        
        sc = QApplication.primaryScreen().availableGeometry()
        self.move(sc.x() + (sc.width() - 400) // 2, 
                  sc.y() + (sc.height() - self.sizeHint().height()) // 2)

        self._all_apps = []
        self.se.textChanged.connect(self._do_search)
        self.slist.itemClicked.connect(self._add_from_search)
        QTimer.singleShot(100, self._scan_apps)

    def _scan_apps(self):
        roots = [
            os.path.join(os.environ.get("ProgramData",""), "Microsoft\\Windows\\Start Menu\\Programs"),
            os.path.join(os.environ.get("AppData",""), "Microsoft\\Windows\\Start Menu\\Programs"),
        ]
        for r in roots:
            if not os.path.exists(r): continue
            for root, dirs, files in os.walk(r):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        self._all_apps.append((f[:-4], os.path.join(root, f)))

    def _do_search(self, txt):
        self.slist.clear()
        if not txt or len(txt) < 1:
            self.slist.hide(); return
        matches = [a for a in self._all_apps if txt.lower() in a[0].lower()]
        if matches:
            self.slist.show()
            for name, path in matches[:10]:
                it = QListWidgetItem(name)
                it.setData(Qt.ItemDataRole.UserRole, path)
                self.slist.addItem(it)
        else:
            self.slist.hide()

    def _add_from_search(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and path not in self.paths:
            self._add_item_to_list(item.text(), path)
            self.se.clear(); self.slist.hide()

    def _add_item_to_list(self, name, path):
        if path in self.paths: return
        self.paths.append(path)
        it = QListWidgetItem(self.plist); it.setSizeHint(QSize(0, 35))
        w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(10, 2, 5, 2)
        lbl = QLabel(name); l.addWidget(lbl); l.addStretch()
        rb = QPushButton("✕"); rb.setObjectName("rm_btn"); rb.setFixedSize(24, 24)
        rb.clicked.connect(lambda: self._remove_item(it, path))
        l.addWidget(rb); self.plist.setItemWidget(it, w)

    def _remove_item(self, item, path):
        if path in self.paths: self.paths.remove(path)
        row = self.plist.row(item); self.plist.takeItem(row)

    def _add_files(self):
        fns, _ = QFileDialog.getOpenFileNames(self, "Select Files to Group", "", "All Files (*.*)")
        if fns:
            for f in fns:
                p = os.path.normpath(f)
                self._add_item_to_list(os.path.basename(p), p)

    def _done(self):
        n = self.ne.text().strip()
        if n and self.paths:
            self.result_name = n; self.accept()

# ══════════════════════════════════════════════════════════════════════════
#  SEARCH BAR  — improved: queries Windows Search Index
# ══════════════════════════════════════════════════════════════════════════


class SwitcherDlg(QDialog):
    def __init__(self, wins, activate_fn, snd=None, parent=None):
        from PyQt6.QtCore import Qt
        super().__init__(parent,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.wins = wins; self.activate_fn = activate_fn; self.snd = snd
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420); self.setMouseTracking(True)
        self._drag_pos = None
        try:
            self._build()
        except Exception as e:
            _log(f"Switcher build err: {e}")
        
        from PyQt6.QtWidgets import QApplication
        sc = QApplication.primaryScreen().availableGeometry()
        self.move(sc.x()+sc.width()//2-210, sc.y()+sc.height()//2-self.sizeHint().height()//2)

    def _build(self):
        from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, 
                                    QLabel, QFrame, QScrollArea, QWidget, QScroller)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap
        
        outer = QVBoxLayout(self); outer.setContentsMargins(10, 10, 10, 10); outer.setSpacing(0)

        self.card = QFrame(); self.card.setObjectName("swcard")
        self.card.setStyleSheet("""
            QFrame#swcard {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(16,12,45,245), stop:1 rgba(8,5,25,252));
                border: 1.5px solid rgba(124,58,237,180);
                border-radius: 18px;
            }
        """)
        cl = QVBoxLayout(self.card); cl.setContentsMargins(12, 12, 12, 12); cl.setSpacing(6)

        self.header = QWidget()
        hdr = QHBoxLayout(self.header); hdr.setContentsMargins(10,5,5,5)
        ttl = QLabel("🪟  WinTop Manager")
        ttl.setStyleSheet("color:#a78bfa;font-size:14px;font-weight:bold;font-family:'Segoe UI';border:none;")
        hdr.addWidget(ttl); hdr.addStretch()
        # Dynamic hotkey display
        curr_mod = self.snd.cfg.get("hotkey_pin_mod", "Win+Alt")
        curr_key = self.snd.cfg.get("hotkey_pin_key", "S").upper()
        sttl = QLabel(f"{curr_mod} + {curr_key}")
        sttl.setStyleSheet("color:rgba(124,58,237,180);font-size:10px;font-family:'Segoe UI';border:none;margin-right:8px;")
        hdr.addWidget(sttl)

        btn_close = QPushButton("✕"); btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
            QPushButton{background:transparent;color:white;border-radius:8px;font-weight:bold;border:none;}
            QPushButton:hover{background:#dc2626;color:white;}
        """)
        btn_close.clicked.connect(self.reject); hdr.addWidget(btn_close)

        cl.addWidget(self.header)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(124,58,237,80);max-height:1px;border:none;margin:2px 0;")
        cl.addWidget(sep)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:rgba(255,255,255,8);width:4px;border-radius:2px;}"
            "QScrollBar::handle:vertical{background:#7c3aed;border-radius:2px;}")
        
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        rows_w = QWidget(); rows_w.setStyleSheet("background:transparent;")
        rows_l = QVBoxLayout(rows_w); rows_l.setContentsMargins(0,0,5,0); rows_l.setSpacing(5)

        ROW_SS = """
            QPushButton#row {
                background:rgba(255,255,255,10);color:#cbd5e1;
                font-family:'Segoe UI';font-size:12px;
                border:1px solid rgba(255,255,255,8);
                border-radius:8px;text-align:left;padding:6px 10px;
            }
            QPushButton#row:hover{background:rgba(124,58,237,100);color:#fff;}
        """
        PIN_OFF = "QPushButton#pin{background:rgba(255,255,255,8);color:#4b5563;border-radius:6px;}"
        PIN_ON  = "QPushButton#pin{background:rgba(124,58,237,200);color:#fff;border-radius:6px;}"

        for w in self.wins:
            row_h = QHBoxLayout(); row_h.setSpacing(6)
            icon_lbl = QLabel(); icon_lbl.setFixedSize(24, 24)
            if w["exe"]:
                try:
                    b = extract_icon_png(w["exe"], sz=24)
                    if b:
                        pm = QPixmap(); pm.loadFromData(b)
                        if not pm.isNull(): icon_lbl.setPixmap(pm)
                except: pass

            disp_title = w["title"][:38] + ("..." if len(w["title"])>38 else "")
            rb = QPushButton(disp_title); rb.setObjectName("row"); rb.setFixedHeight(36)
            rb.setStyleSheet(ROW_SS); rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.clicked.connect(lambda _, h=w["hwnd"]: (setattr(self, "selected_hwnd", h), self.accept()))

            restricted = w.get("restricted", False)
            pb = QPushButton("🚫" if restricted else "📌")
            pb.setObjectName("pin"); pb.setFixedSize(32, 32)
            
            if restricted:
                pb.setStyleSheet("QPushButton#pin{background:rgba(220,38,38,60);color:#fca5a5;border-radius:6px;border:1px solid rgba(220,38,38,100);}")
                pb.setToolTip("Restricted: This app is running as Admin. Please run OrbitSwipe as Admin to pin it.")
                pb.setCursor(Qt.CursorShape.ForbiddenCursor)
            else:
                pb.setCheckable(True); pb.setChecked(w["pinned"])
                pb.setStyleSheet(PIN_ON if w["pinned"] else PIN_OFF)
                pb.setCursor(Qt.CursorShape.PointingHandCursor)
            
            def _toggle_pin(checked, hwnd=w["hwnd"], btn=pb):
                try:
                    import win32gui, win32con
                    target = win32con.HWND_TOPMOST if checked else win32con.HWND_NOTOPMOST
                    # 0x0013 = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                    win32gui.SetWindowPos(hwnd, target, 0,0,0,0, 0x0013)
                    btn.setStyleSheet(PIN_ON if checked else PIN_OFF)
                    if self.snd: self.snd.pin()
                except Exception as e:
                    _log(f"WinTop manual pin failed: {e}")
            
            if not restricted:
                pb.clicked.connect(_toggle_pin)
            
            row_h.addWidget(icon_lbl); row_h.addWidget(rb, 1); row_h.addWidget(pb)
            rows_l.addLayout(row_h)

        rows_l.addStretch()
        scroll.setWidget(rows_w)
        scroll.setFixedHeight(min(len(self.wins)*46 + 10, 360))
        cl.addWidget(scroll)

        outer.addWidget(self.card)

    def mousePressEvent(self, e):
        from PyQt6.QtCore import Qt
        if e.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "header") and self.header.geometry().contains(e.pos()):
                self._drag_pos = e.globalPosition().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)





class TrialGateDlg(QDialog):
    def __init__(self, parent=None):
        import ctypes
        self._acquired_mutex = False
        self._already_open = False
        try:
            # Check if this TrialGate is already showing in any process on this system
            mutex_name = "Global\\OrbitSwipe_TrialGate_Mutex"
            self._mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
            last_err = ctypes.windll.kernel32.GetLastError()
            if last_err == 183: # ERROR_ALREADY_EXISTS
                _log("TrialGateDlg: Another trial gate window is already open. Preventing double display.")
                if self._mutex_handle:
                    ctypes.windll.kernel32.CloseHandle(self._mutex_handle)
                    self._mutex_handle = None
                self._already_open = True
            else:
                self._acquired_mutex = True
        except Exception as e:
            _log(f"TrialGateDlg: Mutex initialization error: {e}")

        super().__init__(parent,
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._worker = None
        self._drag_pos = None
        
        from orbitswipe.core.constants import APPDATA_DIR
        self._pending_file = os.path.normpath(os.path.join(APPDATA_DIR, "pending_transfer.json"))
        
        self._build()
        self._resize_and_center(520, 580)  # Generous fixed height to prevent any text cropping
        self.setWindowOpacity(0.0)

    def exec(self):
        if getattr(self, "_already_open", False):
            return QDialog.DialogCode.Rejected
        return super().exec()

    def accept(self):
        self._cleanup_mutex()
        super().accept()

    def reject(self):
        self._cleanup_mutex()
        super().reject()

    def closeEvent(self, event):
        self._cleanup_mutex()
        super().closeEvent(event)

    def _cleanup_mutex(self):
        if getattr(self, "_acquired_mutex", False) and getattr(self, "_mutex_handle", None):
            try:
                import ctypes
                ctypes.windll.kernel32.ReleaseMutex(self._mutex_handle)
                ctypes.windll.kernel32.CloseHandle(self._mutex_handle)
            except:
                pass
            self._mutex_handle = None
            self._acquired_mutex = False

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
            self.reject()
            self._is_closing = False
            
        self._close_group.finished.connect(done)
        self._close_group.start()

    def _resize_and_center(self, w, h):
        self.setFixedSize(w, h)
        sc = QApplication.primaryScreen().availableGeometry()
        self.move((sc.width()-w)//2, (sc.height()-h)//2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_drag_pos") and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _build(self):
        from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
        from PyQt6.QtCore    import QThread, pyqtSignal as _sig
        
        # Determine display state: offline lease, license revoked, or plain trial ended
        lic_status = get_license_status()
        trial = lic_status["trial"]
        is_lease_expired = lic_status.get("lease_expired", False)

        # Check if user previously had a paid license that got revoked/expired
        try:
            from orbitswipe.core.license import is_license_expired_marker_set
            is_license_revoked = is_license_expired_marker_set()
        except Exception:
            is_license_revoked = False
        
        o  = QVBoxLayout(self); o.setContentsMargins(15,15,15,15)
        c  = QWidget(); c.setObjectName("c")

        # Border color differs per state: orange for revoked, purple for trial
        if is_license_revoked and not is_lease_expired:
            border_color = "#f59e0b"   # amber — license was revoked/expired
        else:
            border_color = "#7c3aed"   # purple — standard trial ended

        c.setStyleSheet(f"""
            #c {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0f0b25, stop:1 #160d3d);
                 border-radius: 24px; border: 1.5px solid {border_color}; }}
            QLabel {{ color: #e2e8f0; font-family: 'Segoe UI'; border: none; }}
        """)
        
        # Glow color matches border
        shadow = QGraphicsDropShadowEffect()
        if is_license_revoked and not is_lease_expired:
            shadow.setBlurRadius(25); shadow.setColor(QColor(245, 158, 11, 100))
        else:
            shadow.setBlurRadius(25); shadow.setColor(QColor(124, 58, 237, 100))
        shadow.setOffset(0,0); c.setGraphicsEffect(shadow)

        cl = QVBoxLayout(c); cl.setContentsMargins(40,10,40,24); cl.setSpacing(14)
        o.addWidget(c)

        # Top Window Controls
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent; color:#94a3b8; font-size:9.5pt; font-weight:bold; border:none;}"
            "QPushButton:hover{color:#ef4444;}"
        )
        close_btn.clicked.connect(self.animate_close)
        
        min_btn = QPushButton("—")
        min_btn.setFixedSize(22, 22)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setStyleSheet(
            "QPushButton{background:transparent; color:#94a3b8; font-size:9.5pt; font-weight:bold; border:none;}"
            "QPushButton:hover{color:#3b82f6;}"
        )
        min_btn.clicked.connect(self.animate_minimize)
        
        top_row.addStretch()
        top_row.addWidget(min_btn)
        top_row.addWidget(close_btn)
        cl.addLayout(top_row)

        # ── Determine texts for each state ────────────────────────────────────
        if is_lease_expired:
            # STATE 1: Offline grace period expired (7 days without internet)
            title_text  = "Offline Verification Required"
            desc_text   = "Your 7-day offline grace period has expired. Please connect to the internet to verify your license."
            emoji_text  = "📶"
            activate_btn_text = "⚡  VERIFY LICENSE"
            title_color = "#f8fafc"

        elif is_license_revoked:
            # STATE 2: Previously paid user whose license was revoked or expired by server
            title_text  = "License Expired or Revoked"
            desc_text   = "Your premium OrbitSwipe license has expired or was revoked by the server. Please renew to continue."
            emoji_text  = "🔑"
            activate_btn_text = "🔄  RENEW LICENSE"
            title_color = "#fbbf24"   # amber title for premium expired

        else:
            # STATE 3: Free trial period ended — never had a paid license
            days_str    = str(int(TRIAL_DAYS)) if int(TRIAL_DAYS) == TRIAL_DAYS else f"{TRIAL_DAYS:.1f}"
            t_msg       = f"Your {days_str}-day trial" if TRIAL_DAYS >= 1 else "Your trial period"
            title_text  = "OrbitSwipe Trial Ended"
            desc_text   = f"{t_msg} has reached its limit. Unlock the full power of OrbitSwipe with a license key."
            emoji_text  = "✨"
            activate_btn_text = "⚡  ACTIVATE PRO"
            title_color = "#f8fafc"
        # ──────────────────────────────────────────────────────────────────────

        il = QLabel(emoji_text); il.setFont(QFont("Segoe UI Emoji", 26))
        il.setFixedHeight(30)
        il.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(il)

        t1 = QLabel(title_text)
        t1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        t1.setFixedHeight(30)  # Elegant title height (lifted 5px)
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet(f"color:{title_color}; border:none; letter-spacing: 0.5px;"); cl.addWidget(t1)

        t2 = QLabel(desc_text)
        t2.setWordWrap(True); t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setFixedHeight(45)  # Elegant description height (lifted 5px)
        t2.setStyleSheet("color:#94a3b8; font-size:10.5pt; border:none; line-height: 140%;"); cl.addWidget(t2)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(124,58,237,0.15); max-height:1px; margin: 2px 0;"); cl.addWidget(sep)

        kl = QLabel("ENTER LICENSE KEY & EMAIL")
        kl.setStyleSheet("color:#a78bfa; font-size:9pt; font-weight:bold; border:none; letter-spacing:1.5px;")
        cl.addWidget(kl)
        
        self._ke = QLineEdit(); self._ke.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self._ke.setMaxLength(36); self._ke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ke.setFixedHeight(44)
        self._ke.setStyleSheet(
            "QLineEdit{background:rgba(15,10,40,200); color:#f8fafc; border:1.5px solid #4c1d95;"
            "border-radius:10px; padding:8px 12px; font-family:'Consolas', 'Segoe UI';"
            "font-size:11pt; font-weight:bold; letter-spacing:2px;}"
            "QLineEdit:focus{border-color:#7c3aed; background:rgba(20,15,50,250);}"
        ); cl.addWidget(self._ke)

        self._ee = QLineEdit(); self._ee.setPlaceholderText("yourname@email.com")
        self._ee.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ee.setFixedHeight(44)
        self._ee.setStyleSheet(
            "QLineEdit{background:rgba(15,10,40,200); color:#f8fafc; border:1.5px solid #4c1d95;"
            "border-radius:10px; padding:8px 12px; font-family:'Segoe UI';"
            "font-size:11pt;}"
            "QLineEdit:focus{border-color:#7c3aed; background:rgba(20,15,50,250);}"
        ); cl.addWidget(self._ee)

        btn_lo = QHBoxLayout(); btn_lo.setSpacing(12); btn_lo.setContentsMargins(0, 0, 0, 0)
        self._ab = QPushButton(f"  {activate_btn_text}"); self._ab.setFixedHeight(48)
        self._ab.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7c3aed, stop:1 #6d28d9); color:white; border-radius:12px;"
            "border:none; font-size:11pt; font-weight:bold; letter-spacing: 0.5px;}"
            "QPushButton:hover{background:#7c3aed; border:1px solid #a78bfa;}"
            "QPushButton:pressed{background:#4c1d95;}"
            "QPushButton:disabled{background:#1e1b4b; color:#475569;}"
        ); self._ab.clicked.connect(self._activate); btn_lo.addWidget(self._ab, 1)

        self._tb = QPushButton("  🔄  REQUEST TRANSFER")
        self._tb.setFixedHeight(48)
        self._tb.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7c3aed, stop:1 #6d28d9); color:white; border-radius:12px;"
            "border:none; font-size:10pt; font-weight:bold; letter-spacing: 0.5px;}"
            "QPushButton:hover{background:#7c3aed; border:1px solid #a78bfa;}"
            "QPushButton:pressed{background:#4c1d95;}"
            "QPushButton:disabled{background:#1e1b4b; color:#475569;}"
        )
        self._tb.clicked.connect(self._request_transfer)
        self._tb.hide()  # Hidden by default, behaves exactly like the settings panel
        btn_lo.addWidget(self._tb, 1)
        cl.addLayout(btn_lo)

        self._ml = QLabel(""); self._ml.setWordWrap(True)
        self._ml.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ml.setStyleSheet("font-size:10pt; font-weight:500; border:none;")
        self._ml.setMinimumHeight(65)  # Enforce minimum height so Qt layout compressor can never crop the text!
        cl.addWidget(self._ml)

        cl.addStretch(1)  # Stretchable layout spacer to absorb all excess card height cleanly

        bl = QLabel('<a href="https://orbitswipe.vercel.app" style="color:#a78bfa; text-decoration:none;">Don\'t have a key? Buy at <b>orbitswipe.vercel.app</b></a>')
        bl.setOpenExternalLinks(True); bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.setStyleSheet("font-size:9pt; border:none;"); cl.addWidget(bl)
        self._ke.returnPressed.connect(self._activate)
        self._ee.returnPressed.connect(self._activate)

        # Automatically pre-fill pending transfer if cached locally
        if os.path.exists(self._pending_file):
            try:
                with open(self._pending_file, "r") as f:
                    pending = json.load(f)
                p_key = pending.get("key", "")
                p_email = pending.get("email", "")
                if p_key and p_email:
                    self._ke.setText(p_key)
                    self._ee.setText(p_email)
                    self._tb.setText("  🔄  REFRESH STATUS")
                    self._tb.setStyleSheet(
                        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                        "stop:0 #22c55e, stop:1 #15803d); color:white; border-radius:12px;"
                        "border:none; font-size:10pt; font-weight:bold; letter-spacing: 0.5px;}"
                        "QPushButton:hover{background:#22c55e; border:1px solid #86efac;}"
                        "QPushButton:pressed{background:#166534;}"
                        "QPushButton:disabled{background:#14532d; color:#86efac;}"
                    )
                    self._tb.show()
            except Exception:
                pass

        class _W(QThread):
            done = _sig(dict)
            def __init__(self, key, email=None, request_transfer=False):
                super().__init__()
                self._key = key
                self._email = email
                self._req_trans = request_transfer
            def run(self):
                self.done.emit(activate_license(self._key, email=self._email, request_transfer=self._req_trans))
        self._WCls = _W

    def _activate(self):
        key = self._ke.text().strip()
        email = self._ee.text().strip()
        if not key:
            self._ml.setText("⚠️  Please enter your license key")
            self._ml.setStyleSheet("color:#fbbf24; border:none;"); return
        if not email or "@" not in email or "." not in email:
            self._ml.setText("⚠️  Please enter a valid email address")
            self._ml.setStyleSheet("color:#fbbf24; border:none;"); return
        
        self._ab.setEnabled(False); self._ab.setText("  ⌛  VALIDATING...")
        
        is_refresh_mode = "REFRESH" in self._tb.text()
        if not is_refresh_mode:
            self._tb.hide()
        else:
            self._tb.setEnabled(False); self._tb.setText("  ⌛  REFRESHING...")

        w = self._WCls(key, email=email); self._worker = w
        def _done(r):
            self._ab.setEnabled(True); self._ab.setText("  ⚡  ACTIVATE PRO")
            if is_refresh_mode:
                self._tb.setEnabled(True); self._tb.setText("  🔄  REFRESH STATUS")

            if r.get("valid"):
                self._ml.setText("✨  SUCCESS! License Activated.")
                self._ml.setStyleSheet("color:#22c55e; border:none;")
                if os.path.exists(self._pending_file):
                    try:
                        os.remove(self._pending_file)
                    except Exception:
                        pass
                QTimer.singleShot(1500, self.accept)
            else:
                msg = r.get("message", "Invalid key")
                msg_lower = msg.lower()
                is_declined = (r.get("can_request_transfer") or 
                               "decline" in msg_lower or 
                               "reject" in msg_lower or 
                               "registered to a different device" in msg_lower or 
                               "request a transfer" in msg_lower or 
                               "registered to another pc" in msg_lower or 
                               "submit a transfer request" in msg_lower or 
                               "already in use" in msg_lower)
                
                if r.get("transfer_pending"):
                    self._ml.setText("⏳ " + msg)
                    self._ml.setStyleSheet("color:#fbbf24; border:none;")
                    # Keep showing refresh button if a transfer is currently pending
                    self._tb.show()
                elif is_refresh_mode and is_declined:
                    self._ml.setText("❌ Transfer request was rejected by admin. You can submit a new request.")
                    self._ml.setStyleSheet("color:#f87171; border:none;")
                    
                    # Restore request transfer button back to purple so they can request again!
                    self._tb.setText("  🔄  REQUEST TRANSFER")
                    self._tb.setStyleSheet(
                        "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                        "stop:0 #7c3aed, stop:1 #6d28d9); color:white; border-radius:12px;"
                        "border:none; font-size:10pt; font-weight:bold; letter-spacing: 0.5px;}"
                        "QPushButton:hover{background:#7c3aed; border:1px solid #a78bfa;}"
                        "QPushButton:pressed{background:#4c1d95;}"
                        "QPushButton:disabled{background:#1e1b4b; color:#475569;}"
                    )
                    self._tb.setEnabled(True)
                    self._tb.show()
                    
                    # Clear locally saved pending cache
                    if os.path.exists(self._pending_file):
                        try:
                            os.remove(self._pending_file)
                        except Exception:
                            pass
                else:
                    self._ml.setText("❌  " + msg)
                    self._ml.setStyleSheet("color:#f87171; border:none;")
                    if r.get("can_request_transfer"):
                        # If server tells us we can request a transfer, restore/show the purple transfer button
                        self._tb.setText("  🔄  REQUEST TRANSFER")
                        self._tb.setStyleSheet(
                            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                            "stop:0 #7c3aed, stop:1 #6d28d9); color:white; border-radius:12px;"
                            "border:none; font-size:10pt; font-weight:bold; letter-spacing: 0.5px;}"
                            "QPushButton:hover{background:#7c3aed; border:1px solid #a78bfa;}"
                            "QPushButton:pressed{background:#4c1d95;}"
                            "QPushButton:disabled{background:#1e1b4b; color:#475569;}"
                        )
                        self._tb.setEnabled(True)
                        self._tb.show()
        w.done.connect(_done); w.start()

    def _request_transfer(self):
        key = self._ke.text().strip()
        email = self._ee.text().strip()
        if not key or not email:
            self._ml.setText("⚠️  Please enter key and email address")
            self._ml.setStyleSheet("color:#fbbf24; border:none;"); return
        
        # If already transformed into a refresh button, just call activate check!
        if "REFRESH" in self._tb.text():
            self._activate()
            return

        self._tb.setEnabled(False); self._tb.setText("  ⌛  SUBMITTING REQUEST...")
        w = self._WCls(key, email=email, request_transfer=True); self._worker = w
        def _done(r):
            self._tb.setEnabled(True)
            if r.get("valid"):
                self._ml.setText("🎉  " + r.get("message"))
                self._ml.setStyleSheet("color:#22c55e; border:none;")
                
                # Save pending status locally
                try:
                    with open(self._pending_file, "w") as f:
                        json.dump({"key": key, "email": email, "transfer_requested": True}, f)
                except Exception as e:
                    _log(f"Failed to cache pending transfer status: {e}")
                
                # Transform the button into a premium green REFRESH STATUS button!
                self._tb.setText("  🔄  REFRESH STATUS")
                self._tb.setStyleSheet(
                    "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 #22c55e, stop:1 #15803d); color:white; border-radius:12px;"
                    "border:none; font-size:10pt; font-weight:bold; letter-spacing: 0.5px;}"
                    "QPushButton:hover{background:#22c55e; border:1px solid #86efac;}"
                    "QPushButton:pressed{background:#166534;}"
                    "QPushButton:disabled{background:#14532d; color:#86efac;}"
                )
            else:
                self._ml.setText("❌  " + r.get("message", "Request failed"))
                self._ml.setStyleSheet("color:#f87171; border:none;")
        w.done.connect(_done); w.start()

# ══════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════════════════
