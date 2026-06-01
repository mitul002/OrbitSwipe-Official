import os
import subprocess
from PyQt6.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QEvent, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor
from orbitswipe.core.utils import _dwm_strip

class SearchBar(QWidget):
    launch = pyqtSignal(str)
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        self._res = []; self._sel = 0
        lo = QVBoxLayout(self); lo.setContentsMargins(10,6,10,6); lo.setSpacing(0)
        lo.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._container = QWidget(); lo.addWidget(self._container); lo.addStretch()
        self._container.setStyleSheet(
            "QWidget{background:rgba(13,9,35,235);border:1.5px solid #7c3aed;border-radius:12px;}")
        clo = QHBoxLayout(self._container); clo.setContentsMargins(12,0,8,0); clo.setSpacing(5)
        self._e = QLineEdit()
        self._e.setPlaceholderText("🔍  Search apps & files…")
        self._e.setStyleSheet("background:transparent;border:none;color:#e2e8f0;"
                               "font-family:'Segoe UI';font-size:10pt;padding:5px 0;")
        self._e.textChanged.connect(self._on_text)
        self._e.installEventFilter(self)
        clo.addWidget(self._e)
        self._xb = QPushButton("✕"); self._xb.setFixedSize(26, 26)
        self._xb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._xb.setStyleSheet(
            "QPushButton{background:transparent;color:#94a3b8;font-weight:bold;font-size:12pt;border:none;}"
            "QPushButton:hover{color:#ffffff;}")
        self._xb.clicked.connect(self.hide); clo.addWidget(self._xb)
        self._list = QWidget(self)
        self._list.setStyleSheet(
            "background:rgba(10,7,28,245);border-radius:10px;border:1px solid #3b2070;")
        self._lL = QVBoxLayout(self._list)
        self._lL.setContentsMargins(4,4,4,4); self._lL.setSpacing(2)
        self._list.hide()
        # Debounce timer to prevent crashes during rapid typing
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search_sync)

    def show_bar(self, w, mode="global"):
        self._mode = mode
        if mode == "toolbox":
            self._e.setPlaceholderText("🔍  Search Toolbox...")
        else:
            self._e.setPlaceholderText("🔍  Search apps & files…")
        self.setFixedWidth(w); self.move(0,0)
        self._e.clear(); self._list.hide()
        self.setFixedHeight(54); self.show(); self._e.setFocus()

    def _on_text(self, text):
        """Triggered on every keystroke, but debounced to prevent overloading."""
        if not text:
            self._list.hide(); self.setFixedHeight(54); return
        # Wait 150ms before searching to handle fast typing
        self._search_timer.start(150)

    def _do_search_sync(self):
        """The actual search logic, now safely debounced and wrapped."""
        text = self._e.text()
        # Clear previous results first
        while self._lL.count():
            item = self._lL.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        self._res = []
        if not text or len(text) < 1:
            self._list.hide(); self.setFixedHeight(54); return
        
        try:
            tl = text.lower()
            
            if self._mode == "toolbox":
                from orbitswipe.core.constants import ALL_TOOLS
                for t in ALL_TOOLS:
                    if tl in t.get("name", "").lower():
                        self._res.append(t)
                        if len(self._res) >= 8: break
                
                for t in self._res:
                    nm = t.get("name", "")
                    ic = t.get("icon", "")
                    btn = QPushButton(f"  {ic}  {nm}"); btn.setFixedHeight(30)
                    btn.setStyleSheet(
                        "QPushButton{background:rgba(255,255,255,12);color:#e2e8f0;"
                        "text-align:left;border-radius:6px;border:none;"
                        "font-family:'Segoe UI';font-size:9pt;padding:0 8px;}"
                        "QPushButton:hover{background:#7c3aed;}")
                    btn.clicked.connect(lambda _, item=t: self._launch_toolbox_item(item))
                    self._lL.addWidget(btn)
            else:
                # Restore stable search locations
                for base in [
                    os.path.join(os.environ.get("APPDATA",""), r"Microsoft\Windows\Start Menu\Programs"),
                    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
                    os.path.join(os.environ.get("LOCALAPPDATA",""), r"Microsoft\Windows\Start Menu\Programs"),
                ]:
                    if not os.path.isdir(base): continue
                    for root2,_,files in os.walk(base):
                        for fn in files:
                            if tl in fn.lower() and fn.lower().endswith((".lnk",".exe")):
                                self._res.append(os.path.join(root2, fn))
                                if len(self._res) >= 8: break
                        if len(self._res) >= 8: break

                for fp in self._res:
                    nm  = os.path.splitext(os.path.basename(fp))[0]
                    btn = QPushButton(f"  {nm}"); btn.setFixedHeight(30)
                    btn.setStyleSheet(
                        "QPushButton{background:rgba(255,255,255,12);color:#e2e8f0;"
                        "text-align:left;border-radius:6px;border:none;"
                        "font-family:'Segoe UI';font-size:9pt;padding:0 8px;}"
                        "QPushButton:hover{background:#7c3aed;}")
                    btn.setToolTip(fp)
                    btn.clicked.connect(lambda _,p=fp: self._launch(p))
                    self._lL.addWidget(btn)

            if self._res:
                h = len(self._res)*34+10
                self._list.setGeometry(10, 64, self.width()-20, h)
                self._list.show(); self.setFixedHeight(64+h+6)
                self._container.raise_()
            else:
                self._list.hide(); self.setFixedHeight(54)
        except Exception as e:
            _log(f"Search error: {e}")
            self._list.hide(); self.setFixedHeight(54)

    def _launch(self, path):
        self.launch.emit(path); self.hide(); self._list.hide()

    def _launch_toolbox_item(self, item):
        # We can just emit the action or path. Let's create a custom signal or use launch
        # Let's emit a string starting with "TOOLBOX:"
        act = item.get("action", "")
        if act:
            self.launch.emit(f"TOOLBOX:{act}")
        self.hide(); self._list.hide()

    def eventFilter(self, obj, ev):
        if obj is self._e and ev.type() == QEvent.Type.KeyPress:
            if ev.key() == Qt.Key.Key_Escape:
                self.hide(); self._list.hide(); return True
            if ev.key() == Qt.Key.Key_Return:
                if self._res:
                    if getattr(self, "_mode", "global") == "toolbox":
                        self._launch_toolbox_item(self._res[0])
                    else:
                        self._launch(self._res[0])
                return True
        return super().eventFilter(obj, ev)

# ── Switcher Dialog ───────────────────────────────────────────────────────
