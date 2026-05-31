from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPointF, QEvent, QRect, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QCursor, QRadialGradient, QLinearGradient, QPainterPath, QFont
import math
from orbitswipe.core.config import save_cfg
from orbitswipe.core.engine import Spring

class Trigger(QWidget):
    fired = pyqtSignal()
    moved = pyqtSignal()
    TW, TH = 22, 84

    def __init__(self, cfg, screen=None):
        super().__init__(None,
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool)
        self.cfg = cfg
        self._target_screen = screen
        self._drag = None; self._dorg = QPointF()
        self._pt   = 0.0
        self._op   = Spring(.28, k=140, d=15)
        self._vis  = Spring(1.0, k=80,  d=12)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.TW, self.TH)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self._touch_start_x = None
        self._repos()
        self._tmr = QTimer(self); self._tmr.timeout.connect(self._tick); self._tmr.start(16)
        self._aht = QTimer(self); self._aht.timeout.connect(self._ah);   self._aht.start(80)

    def _repos(self):
        screen = self._target_screen
        if not screen or screen not in QApplication.screens():
            screen = QApplication.primaryScreen()
        sc = screen.availableGeometry()
        y  = int(sc.height() * self.cfg["trigger_y"])
        y  = max(0, min(y, sc.height() - self.TH))
        x  = (sc.x()+sc.width()-self.TW) if self.cfg["side"]=="right" else sc.x()
        self.move(x, sc.y()+y)

    def _ah(self):
        if not self.cfg.get("auto_hide", False):
            self._vis.go(1.0); return
        cp = QCursor.pos()
        screen = self._target_screen
        if not screen or screen not in QApplication.screens():
            screen = QApplication.primaryScreen()
        sc = screen.availableGeometry()
        ex = sc.x()+sc.width()-6 if self.cfg["side"]=="right" else sc.x()+6
        near = abs(cp.x()-ex)<40 and abs(cp.y()-(self.y()+self.TH//2))<80
        self._vis.go(1.0 if near else 0.0)

    def _tick(self):
        self._pt += .04
        c1 = self._op.tick(.016)
        c2 = self._vis.tick(.016)
        if c1 or c2: self.update()

    def enterEvent(self, e): self._op.go(1.)
    def leaveEvent(self, e): self._op.go(.28)

    def event(self, e):
        if e.type() == QEvent.Type.TouchBegin:
            if e.points():
                self._touch_start_x = e.points()[0].globalPosition().x()
                self.fired.emit()
            e.accept(); return True
        if e.type() == QEvent.Type.TouchUpdate:
            if e.points():
                tx = e.points()[0].globalPosition().x()
                if hasattr(self, "_touch_start_x"):
                    dx = tx - self._touch_start_x
                    if abs(dx) > 30: self.fired.emit()
            e.accept(); return True
        if e.type() == QEvent.Type.TouchEnd:
            e.accept(); return True
        return super().event(e)

    def mousePressEvent(self, e):
        from PyQt6.QtGui import QInputDevice
        if e.device().type() == QInputDevice.DeviceType.TouchScreen: return
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint()
            self._dorg = self.pos()

    def mouseMoveEvent(self, e):
        if self._drag and (e.buttons() & Qt.MouseButton.LeftButton):
            ep = e.globalPosition().toPoint()
            np = self._dorg + (ep - self._drag)
            screen = QApplication.screenAt(ep) or QApplication.primaryScreen()
            self._target_screen = screen
            sc = screen.availableGeometry()
            if ep.x() < sc.x()+sc.width()//2:
                np.setX(sc.x()); self.cfg["side"] = "left"
            else:
                np.setX(sc.x()+sc.width()-self.TW); self.cfg["side"] = "right"
            np.setY(max(sc.y(), min(int(np.y()), sc.y()+sc.height()-self.TH)))
            self.move(np)
            self.cfg["trigger_y"] = (np.y()-sc.y()+self.TH/2) / sc.height()
            save_cfg(self.cfg)

    def mouseReleaseEvent(self, e):
        if self._drag:
            if (e.globalPosition().toPoint()-self._drag).manhattanLength() < 6:
                self.fired.emit()
            else:
                self.moved.emit()
        self._drag = None

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.setDropAction(Qt.DropAction.CopyAction); e.accept(); self._op.go(1.)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.setDropAction(Qt.DropAction.CopyAction); e.accept()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            fp = u.toLocalFile()
            if fp:
                if hasattr(self, "on_drop"): self.on_drop(fp)
        e.setDropAction(Qt.DropAction.CopyAction)
        e.acceptProposedAction()

    def paintEvent(self, e):
        p  = QPainter(self)
        p.fillRect(self.rect(), QColor(0,0,0,1))
        va = max(0.0, min(1.0, self._vis.v))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if va < 0.01: p.end(); return
        p.setOpacity(self._op.v * va)
        w, h   = self.TW, self.TH
        pulse  = .5 + .5*math.sin(self._pt)
        if hasattr(self, "launcher") and self.cfg.get("glass_preset") == "Dynamic Glass":
            tc = QColor(*(getattr(self.launcher, "_dynamic_accent", None) or (124, 58, 237)))
        else:
            tc = QColor(self.cfg.get("theme_color","#7c3aed"))
        r,g,b  = tc.red(), tc.green(), tc.blue()
        gi     = self.cfg.get("glow_intensity", 1.0)
        gr = QRadialGradient(w/2, h/2, 24 + (30 * gi))
        gr.setColorAt(0, QColor(r,g,b, int(120 * pulse * min(1.0, gi))))
        gr.setColorAt(1, QColor(r,g,b, 0))
        p.setBrush(QBrush(gr)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(-18, h//2-34, w+36, 68)
        pill = QPainterPath(); pill.addRoundedRect(QRectF(2,4,w-2,h-8), 9,9)
        lg   = QLinearGradient(0,0,0,h); tc2 = tc.lighter(130)
        lg.setColorAt(0,  QColor(r,g,b,230))
        lg.setColorAt(.5, QColor(tc2.red(),tc2.green(),tc2.blue(),215))
        lg.setColorAt(1,  QColor(r,g,b,230))
        p.setBrush(QBrush(lg))
        p.setPen(QPen(QColor(tc2.red(),tc2.green(),tc2.blue(),130), 1.2))
        p.drawPath(pill)
        p.setPen(QPen(QColor(255,255,255,228)))
        p.setFont(QFont("Segoe UI",15,QFont.Weight.Bold))
        p.drawText(QRect(0,0,w,h), Qt.AlignmentFlag.AlignCenter,
                   "(" if self.cfg["side"]=="right" else ")")
        p.end()

# ══════════════════════════════════════════════════════════════════════════
#  SMALL DIALOGS
# ══════════════════════════════════════════════════════════════════════════
_DSS = "background:#13132b;border-radius:16px;border:1.5px solid #2e1065;"
_LSS = "color:#e2e8f0;font-family:'Segoe UI';border:none;"
_ESS = ("QLineEdit{background:#1e1b4b;color:#e2e8f0;border:1px solid #7c3aed;"
        "border-radius:8px;padding:6px 10px;font-family:'Segoe UI';font-size:10pt;}")
_BSS = ("QPushButton{background:#7c3aed;color:white;border-radius:8px;border:none;"
        "padding:6px 18px;font-family:'Segoe UI';font-weight:bold;}"
        "QPushButton:hover{background:#6d28d9;}")
_XSS = ("QPushButton{background:#dc2626;color:white;border-radius:6px;border:none;}"
        "QPushButton:hover{background:#ef4444;}")

