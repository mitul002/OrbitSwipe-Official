"""
OrbitSwipe — Color Picker
A fully custom standalone color picker window.
"""
import math
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QApplication, QSizeGrip
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, QRectF, pyqtSignal
)
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QConicalGradient,
    QRadialGradient, QImage, QPixmap, QPen, QBrush, QFont,
    QCursor
)


# ──────────────────────────────────────────────────────────────────────────────
#  Hue-Saturation-Value square picker
# ──────────────────────────────────────────────────────────────────────────────
class _SVSquare(QWidget):
    """Square that shows saturation (X) vs value (Y) for a given hue."""
    changed = pyqtSignal(float, float)   # s, v  0-1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._hue = 0.0
        self._s   = 1.0
        self._v   = 1.0
        self._drag = False

    def set_hue(self, h):
        self._hue = h
        self.update()

    def set_sv(self, s, v):
        self._s, self._v = s, v
        self.update()

    def _build_image(self):
        img = QImage(self.width(), self.height(), QImage.Format.Format_RGB32)
        w, h = self.width(), self.height()
        for y in range(h):
            v = 1.0 - y / (h - 1)
            for x in range(w):
                s = x / (w - 1)
                c = QColor.fromHsvF(self._hue, s, v)
                img.setPixelColor(x, y, c)
        return img

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        img = self._build_image()
        p.drawImage(0, 0, img)
        # cursor circle
        cx = int(self._s * self.width())
        cy = int((1 - self._v) * self.height())
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPoint(cx, cy), 7, 7)
        p.setPen(QPen(Qt.GlobalColor.black, 1))
        p.drawEllipse(QPoint(cx, cy), 8, 8)

    def _pick(self, pos):
        w, h = self.width(), self.height()
        s = max(0.0, min(1.0, pos.x() / w))
        v = max(0.0, min(1.0, 1.0 - pos.y() / h))
        self._s, self._v = s, v
        self.update()
        self.changed.emit(s, v)

    def mousePressEvent(self,  e): self._drag = True;  self._pick(e.position().toPoint())
    def mouseMoveEvent(self,   e):
        if self._drag: self._pick(e.position().toPoint())
    def mouseReleaseEvent(self, e): self._drag = False


# ──────────────────────────────────────────────────────────────────────────────
#  Hue strip
# ──────────────────────────────────────────────────────────────────────────────
class _HueStrip(QWidget):
    changed = pyqtSignal(float)   # hue 0-1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 220)
        self._hue  = 0.0
        self._drag = False

    def set_hue(self, h):
        self._hue = h
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        for i in range(7):
            grad.setColorAt(i / 6, QColor.fromHsvF(i / 6, 1, 1))
        p.fillRect(self.rect(), grad)
        # cursor line
        y = int(self._hue * self.height())
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawLine(0, y, self.width(), y)
        p.setPen(QPen(Qt.GlobalColor.black, 1))
        p.drawLine(0, y-1, self.width(), y-1)
        p.drawLine(0, y+1, self.width(), y+1)

    def _pick(self, pos):
        h = max(0.0, min(1.0, pos.y() / self.height()))
        self._hue = h
        self.update()
        self.changed.emit(h)

    def mousePressEvent(self,  e): self._drag = True;  self._pick(e.position().toPoint())
    def mouseMoveEvent(self,   e):
        if self._drag: self._pick(e.position().toPoint())
    def mouseReleaseEvent(self, e): self._drag = False


# ──────────────────────────────────────────────────────────────────────────────
#  Alpha strip
# ──────────────────────────────────────────────────────────────────────────────
class _AlphaStrip(QWidget):
    changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 220)
        self._alpha = 1.0
        self._color = QColor(255, 0, 0)
        self._drag  = False

    def set_color(self, c: QColor):
        self._color = c
        self.update()

    def set_alpha(self, a):
        self._alpha = a
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        # checkerboard for transparency
        sz = 6
        for row in range(0, self.height(), sz):
            for col in range(0, self.width(), sz):
                is_light = (row // sz + col // sz) % 2 == 0
                p.fillRect(col, row, sz, sz,
                            QColor(200, 200, 200) if is_light else QColor(140, 140, 140))
        # gradient
        c0 = QColor(self._color); c0.setAlphaF(0.0)
        c1 = QColor(self._color); c1.setAlphaF(1.0)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, c0)
        grad.setColorAt(1, c1)
        p.fillRect(self.rect(), grad)
        # cursor line
        y = int(self._alpha * self.height())
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawLine(0, y, self.width(), y)

    def _pick(self, pos):
        a = max(0.0, min(1.0, pos.y() / self.height()))
        self._alpha = a
        self.update()
        self.changed.emit(a)

    def mousePressEvent(self,  e): self._drag = True;  self._pick(e.position().toPoint())
    def mouseMoveEvent(self,   e):
        if self._drag: self._pick(e.position().toPoint())
    def mouseReleaseEvent(self, e): self._drag = False


# ──────────────────────────────────────────────────────────────────────────────
#  Preview swatch
# ──────────────────────────────────────────────────────────────────────────────
class _Swatch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self._color = QColor(255, 0, 0)

    def set_color(self, c):
        self._color = c
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # checkerboard
        sz = 6
        for row in range(0, self.height(), sz):
            for col in range(0, self.width(), sz):
                is_light = (row // sz + col // sz) % 2 == 0
                p.fillRect(col, row, sz, sz,
                            QColor(200, 200, 200) if is_light else QColor(140, 140, 140))
        p.setBrush(QBrush(self._color))
        p.setPen(QPen(QColor(80, 60, 120), 1))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


# ──────────────────────────────────────────────────────────────────────────────
#  Eyedropper screen picker
# ──────────────────────────────────────────────────────────────────────────────
class _EyedropperOverlay(QWidget):
    """Full-screen transparent overlay to pick a pixel from the screen."""
    picked = pyqtSignal(QColor)

    def __init__(self):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._screen_img = None
        self._zoom_pos   = QPoint(0, 0)
        self.setMouseTracking(True)

    def capture_screen(self):
        screen = QApplication.primaryScreen()
        self._screen_img = screen.grabWindow(0).toImage()

    def showEvent(self, e):
        self.capture_screen()
        geo = QApplication.primaryScreen().geometry()
        self.setGeometry(geo)
        super().showEvent(e)

    def _color_at(self, pos):
        if self._screen_img and 0 <= pos.x() < self._screen_img.width() \
                and 0 <= pos.y() < self._screen_img.height():
            return QColor(self._screen_img.pixel(pos.x(), pos.y()))
        return QColor(Qt.GlobalColor.white)

    def paintEvent(self, _):
        if not self._screen_img:
            return
        p   = QPainter(self)
        pos = self._zoom_pos
        # magnifier
        zoom = 8; radius = 60; size = radius * 2 + 1
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        src_x = max(0, pos.x() - radius // zoom)
        src_y = max(0, pos.y() - radius // zoom)
        src_w = size // zoom + 1
        src_h = size // zoom + 1
        src_rect = QRect(src_x, src_y, src_w, src_h)
        pix = QPixmap.fromImage(self._screen_img).copy(src_rect)
        pix = pix.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.FastTransformation)
        # draw magnifier circle
        mx, my = pos.x() + 80, pos.y() - 80
        p.setPen(QPen(QColor(255, 255, 255, 200), 3))
        p.setBrush(QBrush(pix))
        p.drawEllipse(QPoint(mx, my), radius, radius)
        # crosshair in magnifier
        p.setPen(QPen(QColor(255, 255, 255, 180), 1))
        p.drawLine(mx - radius, my, mx + radius, my)
        p.drawLine(mx, my - radius, mx, my + radius)
        # current color dot
        cur_c = self._color_at(pos)
        p.setBrush(QBrush(cur_c))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawEllipse(QPoint(mx, my), 8, 8)

    def mouseMoveEvent(self, e):
        self._zoom_pos = e.position().toPoint()
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            c = self._color_at(e.position().toPoint())
            self.hide()
            self.picked.emit(c)
        elif e.button() == Qt.MouseButton.RightButton:
            self.hide()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()


# ──────────────────────────────────────────────────────────────────────────────
#  Main Color Picker window
# ──────────────────────────────────────────────────────────────────────────────
class ColorPicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(320)

        # ── internal state ────────────────────────────────────────────────────
        self._hue   = 0.0
        self._sat   = 1.0
        self._val   = 1.0
        self._alpha = 1.0
        self._block = False        # prevent feedback loops
        self._drag_pos = None
        self._eyedrop  = _EyedropperOverlay()
        self._eyedrop.picked.connect(self._on_eye_pick)

        # ── build UI ─────────────────────────────────────────────────────────
        self._build_ui()
        self._refresh_all()

    # ── drag to move ─────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── UI layout ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # outer container
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            QWidget#card {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #12082e, stop:1 #0c061f);
                border: 1.5px solid #7c3aed;
                border-radius: 14px;
            }
        """)
        outer.addWidget(card)

        vl = QVBoxLayout(card)
        vl.setContentsMargins(14, 12, 14, 14)
        vl.setSpacing(10)

        # ── Title bar ─────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("🎨  Color Picker")
        title.setStyleSheet("color:#c4b5fd;font-family:'Segoe UI';font-size:10pt;font-weight:600;")
        hdr.addWidget(title)
        hdr.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#94a3b8;font-size:11pt;border:none;}"
            "QPushButton:hover{color:#fff;}"
        )
        close_btn.clicked.connect(self.close)
        hdr.addWidget(close_btn)
        vl.addLayout(hdr)

        # ── Picker row: [SV square] [hue strip] [alpha strip] ─────────────────
        row = QHBoxLayout(); row.setSpacing(8)
        self._sv   = _SVSquare();     row.addWidget(self._sv)
        self._hue_s = _HueStrip();   row.addWidget(self._hue_s)
        self._alp   = _AlphaStrip(); row.addWidget(self._alp)
        vl.addLayout(row)

        # signals
        self._sv.changed.connect(self._on_sv)
        self._hue_s.changed.connect(self._on_hue)
        self._alp.changed.connect(self._on_alpha)

        # ── Preview + hex row ─────────────────────────────────────────────────
        prev_row = QHBoxLayout(); prev_row.setSpacing(10)
        self._swatch = _Swatch()
        prev_row.addWidget(self._swatch)

        fields = QVBoxLayout(); fields.setSpacing(5)

        # HEX input
        hex_row = QHBoxLayout(); hex_row.setSpacing(6)
        hex_lbl = QLabel("HEX")
        hex_lbl.setStyleSheet("color:#64748b;font-family:'Segoe UI';font-size:8pt;")
        hex_lbl.setFixedWidth(32)
        self._hex_e = QLineEdit()
        self._hex_e.setMaxLength(9)
        self._hex_e.setStyleSheet(self._input_style())
        self._hex_e.editingFinished.connect(self._from_hex)
        hex_row.addWidget(hex_lbl)
        hex_row.addWidget(self._hex_e)
        fields.addLayout(hex_row)

        # RGB input
        rgb_row = QHBoxLayout(); rgb_row.setSpacing(4)
        rgb_lbl = QLabel("RGB")
        rgb_lbl.setStyleSheet("color:#64748b;font-family:'Segoe UI';font-size:8pt;")
        rgb_lbl.setFixedWidth(32)
        self._r_e = QLineEdit(); self._r_e.setPlaceholderText("R")
        self._g_e = QLineEdit(); self._g_e.setPlaceholderText("G")
        self._b_e = QLineEdit(); self._b_e.setPlaceholderText("B")
        for w in (self._r_e, self._g_e, self._b_e):
            w.setMaxLength(3)
            w.setStyleSheet(self._input_style())
            w.editingFinished.connect(self._from_rgb)
        rgb_row.addWidget(rgb_lbl)
        rgb_row.addWidget(self._r_e)
        rgb_row.addWidget(self._g_e)
        rgb_row.addWidget(self._b_e)
        fields.addLayout(rgb_row)

        prev_row.addLayout(fields)
        vl.addLayout(prev_row)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)

        eye_btn = QPushButton("🔍  Pick from Screen")
        eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        eye_btn.setStyleSheet(self._outline_btn_style())
        eye_btn.clicked.connect(self._start_eyedrop)
        btn_row.addWidget(eye_btn)

        self._copy_btn = QPushButton("📋  Copy HEX")
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet(self._fill_btn_style())
        self._copy_btn.clicked.connect(self._copy)
        btn_row.addWidget(self._copy_btn)

        vl.addLayout(btn_row)

    # ── Styles ────────────────────────────────────────────────────────────────
    def _input_style(self):
        return ("QLineEdit{background:rgba(255,255,255,10);border:1px solid #3b2070;"
                "border-radius:6px;color:#e2e8f0;font-family:'Segoe UI';font-size:9pt;"
                "padding:3px 6px;}"
                "QLineEdit:focus{border:1px solid #7c3aed;}")

    def _fill_btn_style(self):
        return ("QPushButton{background:#7c3aed;color:#fff;border:none;border-radius:7px;"
                "font-family:'Segoe UI';font-size:9pt;padding:6px 12px;}"
                "QPushButton:hover{background:#6d28d9;}"
                "QPushButton:pressed{background:#5b21b6;}")

    def _outline_btn_style(self):
        return ("QPushButton{background:transparent;color:#c4b5fd;border:1px solid #7c3aed;"
                "border-radius:7px;font-family:'Segoe UI';font-size:9pt;padding:6px 12px;}"
                "QPushButton:hover{background:rgba(124,58,237,0.18);}"
                "QPushButton:pressed{background:rgba(124,58,237,0.30);}")

    # ── Current color ─────────────────────────────────────────────────────────
    def _current_color(self) -> QColor:
        c = QColor.fromHsvF(self._hue, self._sat, self._val)
        c.setAlphaF(self._alpha)
        return c

    # ── Refresh all widgets from internal HSV+alpha state ─────────────────────
    def _refresh_all(self):
        if self._block:
            return
        self._block = True
        try:
            c = self._current_color()
            # sub-widgets
            self._sv.set_hue(self._hue)
            self._sv.set_sv(self._sat, self._val)
            self._hue_s.set_hue(self._hue)
            self._alp.set_color(c)
            self._alp.set_alpha(self._alpha)
            self._swatch.set_color(c)
            # text fields
            if self._alpha < 1.0:
                self._hex_e.setText(c.name(QColor.NameFormat.HexArgb))
            else:
                self._hex_e.setText(c.name())
            self._r_e.setText(str(c.red()))
            self._g_e.setText(str(c.green()))
            self._b_e.setText(str(c.blue()))
        finally:
            self._block = False

    # ── Slot: SV square changed ───────────────────────────────────────────────
    def _on_sv(self, s, v):
        self._sat, self._val = s, v
        self._refresh_all()

    # ── Slot: Hue strip changed ───────────────────────────────────────────────
    def _on_hue(self, h):
        self._hue = h
        self._refresh_all()

    # ── Slot: Alpha strip changed ─────────────────────────────────────────────
    def _on_alpha(self, a):
        self._alpha = a
        self._refresh_all()

    # ── Slot: user edited HEX field ──────────────────────────────────────────
    def _from_hex(self):
        if self._block:
            return
        text = self._hex_e.text().strip()
        c = QColor(text)
        if c.isValid():
            self._set_from_qcolor(c)

    # ── Slot: user edited RGB fields ──────────────────────────────────────────
    def _from_rgb(self):
        if self._block:
            return
        try:
            r = int(self._r_e.text())
            g = int(self._g_e.text())
            b = int(self._b_e.text())
            c = QColor(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            c.setAlphaF(self._alpha)
            self._set_from_qcolor(c)
        except ValueError:
            pass

    def _set_from_qcolor(self, c: QColor):
        h, s, v, a = c.hsvHueF(), c.hsvSaturationF(), c.valueF(), c.alphaF()
        if h < 0:
            h = 0.0
        self._hue, self._sat, self._val, self._alpha = h, s, v, a
        self._refresh_all()

    # ── Eyedropper ────────────────────────────────────────────────────────────
    def _start_eyedrop(self):
        self.hide()
        QTimer.singleShot(150, self._show_overlay)

    def _show_overlay(self):
        self._eyedrop.show()

    def _on_eye_pick(self, color: QColor):
        self._set_from_qcolor(color)
        self.show()
        self.raise_()
        self.activateWindow()

    # ── Copy to clipboard ─────────────────────────────────────────────────────
    def _copy(self):
        c = self._current_color()
        if self._alpha < 1.0:
            text = c.name(QColor.NameFormat.HexArgb)
        else:
            text = c.name()
        QApplication.clipboard().setText(text)
        # brief feedback
        original = self._copy_btn.text()
        self._copy_btn.setText("✅  Copied!")
        self._copy_btn.setStyleSheet(
            "QPushButton{background:#16a34a;color:#fff;border:none;border-radius:7px;"
            "font-family:'Segoe UI';font-size:9pt;padding:6px 12px;}")
        QTimer.singleShot(1500, lambda: (
            self._copy_btn.setText(original),
            self._copy_btn.setStyleSheet(self._fill_btn_style())
        ))

    # ── Center on screen before showing ──────────────────────────────────────
    def show(self):
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
        super().show()
        self.raise_()
        self.activateWindow()


# ── Convenience launcher ──────────────────────────────────────────────────────
def open_color_picker():
    """Call this from launcher._do_tool(). Creates and shows the picker."""
    picker = ColorPicker()
    picker.show()
    return picker          # caller must keep a reference!
