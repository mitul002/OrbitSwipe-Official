"""
OrbitSwipe — PowerToys-style Screen Color Picker
An advanced, minimalist screen color picker inspired by Microsoft PowerToys.
Features:
- Scroll wheel zoom adjustment (4x to 24x magnification).
- Keyboard-precision navigation (Arrow keys move the cursor pixel-by-pixel).
- Lighter/Darker shades generator panel (interactive shades strip).
- Color History list (persists picked colors).
- Sleek modern dark Obsidian design matching OrbitSwipe aesthetic.
"""
import os
import sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QApplication, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, pyqtSignal, QRectF
)
from PyQt6.QtGui import (
    QPainter, QColor, QPixmap, QImage, QPen, QBrush, QCursor, QFont, QPainterPath
)
from PyQt6.QtWidgets import QButtonGroup
from orbitswipe.core.config import save_cfg

class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            
class _Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 8pt;")
        self.setText("Copied!")
        self.hide()
        
    def show_msg(self):
        self.adjustSize()
        px = (self.parent().width() - self.width()) // 2
        py = self.parent().height() - self.height() - 20
        self.move(px, py)
        self.show()
        self.raise_()
        QTimer.singleShot(1500, self.hide)


# ──────────────────────────────────────────────────────────────────────────────
#  Eyedropper screen picker (Full-screen Overlay)
# ──────────────────────────────────────────────────────────────────────────────
class _EyedropperOverlay(QWidget):
    """Full-screen transparent overlay to pick a pixel from the screen."""
    picked = pyqtSignal(QColor)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.BlankCursor)  # Hide cursor for custom magnifier
        self._screen_img = None
        self._ratio_x = 1.0
        self._ratio_y = 1.0
        self._zoom_pos = QPoint(0, 0)
        self._zoom_level = 8  # Zoom multiplier (default 8x, scroll to adjust)
        self.setMouseTracking(True)

    def capture_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            pm = screen.grabWindow(0, geom.x(), geom.y(), geom.width(), geom.height())
            self._screen_img = pm.toImage()
            self._ratio_x = self._screen_img.width() / max(1, geom.width())
            self._ratio_y = self._screen_img.height() / max(1, geom.height())
        else:
            self._screen_img = QImage()
            self._ratio_x = 1.0
            self._ratio_y = 1.0

    def showEvent(self, e):
        self.capture_screen()
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self._zoom_pos = QCursor.pos()
        super().showEvent(e)

    def _color_at(self, pos):
        if not self._screen_img or self._screen_img.isNull():
            return QColor(Qt.GlobalColor.white)
        px = int(pos.x() * self._ratio_x)
        py = int(pos.y() * self._ratio_y)
        if 0 <= px < self._screen_img.width() and 0 <= py < self._screen_img.height():
            return QColor(self._screen_img.pixel(px, py))
        return QColor(Qt.GlobalColor.white)

    def paintEvent(self, _):
        if not self._screen_img or self._screen_img.isNull():
            return
        
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pos = self._zoom_pos
        zoom = self._zoom_level
        radius = 70  # Width of magnifier circle
        size = radius * 2
        
        # Calculate screen physical coordinates
        phys_x = int(pos.x() * self._ratio_x)
        phys_y = int(pos.y() * self._ratio_y)
        
        # Get high-DPI device pixel ratio
        dpr = self.devicePixelRatioF()
        phys_size = int(size * dpr)
        
        # Calculate sub-image to scale in physical pixels
        phys_src_w = phys_size // zoom
        phys_src_h = phys_size // zoom
        phys_src_x = phys_x - phys_src_w // 2
        phys_src_y = phys_y - phys_src_h // 2
        
        phys_src_rect = QRect(phys_src_x, phys_src_y, phys_src_w, phys_src_h)
        
        # Crop the region from screen image (physical pixels)
        cropped_img = self._screen_img.copy(phys_src_rect)
        
        # Scale to physical magnifier size
        scaled_img = cropped_img.scaled(
            phys_size, phys_size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        
        # Draw pixel grid overlay directly onto the physical image
        qp = QPainter(scaled_img)
        qp.setPen(QPen(QColor(255, 255, 255, 20), 1))
        for x in range(0, phys_size, zoom):
            qp.drawLine(x, 0, x, phys_size)
        for y in range(0, phys_size, zoom):
            qp.drawLine(0, y, phys_size, y)
        qp.end()
        
        # Convert physical image to QPixmap and set device pixel ratio
        pix = QPixmap.fromImage(scaled_img)
        pix.setDevicePixelRatio(dpr)
        
        # Offset magnifier so it is centered on the cursor
        mx, my = pos.x(), pos.y()
        
        # Magnifier border and background
        path = QPainterPath()
        path.addEllipse(QRectF(mx - radius, my - radius, size, size))
        
        p.save()
        p.setClipPath(path)
        p.drawPixmap(mx - radius, my - radius, pix)
        p.restore()
        
        # Central target pixel indicator (hollow square)
        cell_w = zoom / dpr
        p.setPen(QPen(Qt.GlobalColor.white, 1.5))
        p.drawRect(QRectF(mx - cell_w / 2, my - cell_w / 2, cell_w, cell_w))
        p.setPen(QPen(Qt.GlobalColor.black, 0.5))
        p.drawRect(QRectF(mx - cell_w / 2 - 1 / dpr, my - cell_w / 2 - 1 / dpr, cell_w + 2 / dpr, cell_w + 2 / dpr))
        
        # Circular outer bounds pen
        p.setPen(QPen(QColor(124, 58, 237), 3))  # Violet border
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPoint(mx, my), radius, radius)
        
        # Render hex text box below/above the circle dynamically to fit screen
        cur_c = self._color_at(pos)
        hex_text = cur_c.name().upper()
        
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        text_w = 65
        text_h = 22
        tx = mx - text_w // 2
        ty = my + radius + 10 if my + radius + 10 + text_h < self.height() else my - radius - 10 - text_h
        
        # Background bubble for text (dynamic color)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(cur_c))
        p.drawRoundedRect(QRectF(tx, ty, text_w, text_h), 5, 5)
        
        # Add a subtle border
        p.setPen(QPen(QColor(255, 255, 255, 80), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(tx, ty, text_w, text_h), 5, 5)
        
        # Determine text color based on brightness
        bri = (cur_c.red() * 299 + cur_c.green() * 587 + cur_c.blue() * 114) / 1000
        text_col = Qt.GlobalColor.black if bri > 130 else Qt.GlobalColor.white
        shadow_col = QColor(255,255,255,150) if bri > 130 else QColor(0,0,0,150)
        
        # Render clean text shadow
        p.setPen(shadow_col)
        p.drawText(QRect(tx + 1, ty + 1, text_w, text_h), Qt.AlignmentFlag.AlignCenter, hex_text)
        p.setPen(text_col)
        p.drawText(QRect(tx, ty, text_w, text_h), Qt.AlignmentFlag.AlignCenter, hex_text)

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
            self.cancelled.emit()

    def wheelEvent(self, e):
        # Adjust zoom level between 4x and 24x
        delta = e.angleDelta().y()
        if delta > 0:
            self._zoom_level = min(24, self._zoom_level + 2)
        else:
            self._zoom_level = max(4, self._zoom_level - 2)
        self.update()

    def keyPressEvent(self, e):
        # Keyboard precision navigation with arrow keys
        step = 1
        pos = QCursor.pos()
        
        if e.key() == Qt.Key.Key_Left:
            QCursor.setPos(pos.x() - step, pos.y())
        elif e.key() == Qt.Key.Key_Right:
            QCursor.setPos(pos.x() + step, pos.y())
        elif e.key() == Qt.Key.Key_Up:
            QCursor.setPos(pos.x(), pos.y() - step)
        elif e.key() == Qt.Key.Key_Down:
            QCursor.setPos(pos.x(), pos.y() + step)
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            c = self._color_at(pos)
            self.hide()
            self.picked.emit(c)
            return
        elif e.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
            return
            
        self._zoom_pos = QCursor.pos()
        self.update()


# ──────────────────────────────────────────────────────────────────────────────
#  Palette Shade Widget (Interactive shades selection)
# ──────────────────────────────────────────────────────────────────────────────
class _ShadesWidget(QWidget):
    shadeSelected = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self._shades = []
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color: QColor):
        h, s, l, a = color.getHslF()
        self._shades = []
        # Generate 3 darker, 1 active, and 3 lighter shades
        factors = [0.4, 0.6, 0.8, 1.0, 1.15, 1.3, 1.45]
        for f in factors:
            new_l = min(1.0, max(0.0, l * f if f <= 1.0 else l + (1.0 - l) * (f - 1.0)))
            self._shades.append(QColor.fromHslF(h, s, new_l, a))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._shades:
            return
        
        w_item = self.width() / len(self._shades)
        h = self.height()
        
        for i, c in enumerate(self._shades):
            rx = i * w_item
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            # Rounded outer edges
            if i == 0:
                p.drawRoundedRect(QRectF(rx, 0, w_item + 1, h), 4, 4)
                p.drawRect(QRectF(rx + w_item/2, 0, w_item/2 + 1, h))
            elif i == len(self._shades) - 1:
                p.drawRoundedRect(QRectF(rx - 1, 0, w_item + 1, h), 4, 4)
                p.drawRect(QRectF(rx - 1, 0, w_item/2 + 1, h))
            else:
                p.drawRect(QRectF(rx - 1, 0, w_item + 2, h))

    def mousePressEvent(self, e):
        if not self._shades:
            return
        w_item = self.width() / len(self._shades)
        idx = int(e.position().x() // w_item)
        idx = max(0, min(len(self._shades) - 1, idx))
        self.shadeSelected.emit(self._shades[idx])


# ──────────────────────────────────────────────────────────────────────────────
#  Color History Widget
# ──────────────────────────────────────────────────────────────────────────────
class _HistoryWidget(QWidget):
    colorSelected = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._colors = []
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_colors(self, colors):
        self._colors = [QColor(c) for c in colors[:9]]
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._colors:
            return
            
        spacing = 6
        size = 28
        for i, c in enumerate(self._colors):
            cx = i * (size + spacing)
            p.setBrush(QBrush(c))
            p.setPen(QPen(QColor(255, 255, 255, 30), 1))
            p.drawRoundedRect(QRectF(cx, 0, size, size), 6, 6)

    def mousePressEvent(self, e):
        spacing = 6
        size = 28
        mx = e.position().x()
        for i in range(len(self._colors)):
            cx = i * (size + spacing)
            if cx <= mx <= cx + size:
                self.colorSelected.emit(self._colors[i])
                break


# ──────────────────────────────────────────────────────────────────────────────
#  Main PowerToys-Style Color Picker window
# ──────────────────────────────────────────────────────────────────────────────
class ColorPicker(QWidget):
    def __init__(self, cfg=None, parent=None):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 510)

        # ── Configuration & History ───────────────────────────────────────────
        self.cfg = cfg if cfg is not None else {}
        if "color_history" not in self.cfg:
            self.cfg["color_history"] = []

        # ── internal state ────────────────────────────────────────────────────
        self._drag_pos = None
        self._eyedrop = _EyedropperOverlay()
        self._eyedrop.picked.connect(self._on_eye_pick)
        self._eyedrop.cancelled.connect(self._on_cancelled)
        
        # Load the last picked color or a default
        last_color_hex = self.cfg["color_history"][0] if self.cfg["color_history"] else "#7C3AED"
        self._current_color = QColor(last_color_hex)
        
        self._toast = _Toast(self)
        self._is_centered = False
        
        # ── Build UI ─────────────────────────────────────────────────────────
        self._build_ui()
        self._update_values()

    def showEvent(self, e):
        super().showEvent(e)
        if not self._is_centered:
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                x = geom.x() + (geom.width() - self.width()) // 2
                y = geom.y() + (geom.height() - self.height()) // 2
                self.move(x, y)
                self._is_centered = True

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

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            QWidget#card {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(16,12,45,252), stop:1 rgba(8,5,25,255));
                border: 1.5px solid rgba(124,58,237,200);
                border-radius: 18px;
            }
            QLabel {
                color: #e2e8f0;
                font-family: 'Segoe UI';
            }
        """)
        outer.addWidget(card)

        vl = QVBoxLayout(card)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(42)
        hdr.setStyleSheet("background-color: transparent; border-top-left-radius: 18px; border-top-right-radius: 18px;")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(12, 0, 8, 0)
        
        # Title
        ttl = QLabel("💧  Color Picker")
        ttl.setStyleSheet("color:#a78bfa;font-size:14px;font-weight:bold;font-family:'Segoe UI';border:none;")
        hdr_layout.addWidget(ttl)
        
        hdr_layout.addStretch()
        
        # Shortcut display
        curr_mod = getattr(self, "cfg", {}).get("hotkey_color_mod", "Win+Alt")
        curr_key = getattr(self, "cfg", {}).get("hotkey_color_key", "C").upper()
        sttl = QLabel(f"{curr_mod} + {curr_key}")
        sttl.setStyleSheet("color:rgba(124,58,237,180);font-size:10px;font-family:'Segoe UI';border:none;margin-right:8px;")
        hdr_layout.addWidget(sttl)
        
        # Close Button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #94a3b8; font-size: 11pt; border: none; font-weight: bold; border-radius: 8px;}
            QPushButton:hover { color: white; background: #dc2626; border-radius: 8px;}
        """)
        close_btn.clicked.connect(self.close)
        hdr_layout.addWidget(close_btn)
        
        vl.addWidget(hdr)
        
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(124,58,237,80);max-height:1px;border:none;margin:2px 12px;")
        vl.addWidget(sep)

        # ── Body ───────────────────────────────────────────────────────────
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 18)
        body_layout.setSpacing(14)
        
        # Active Color Swatch Display
        self._swatch_frame = QFrame()
        self._swatch_frame.setFixedHeight(72)
        self._swatch_layout = QHBoxLayout(self._swatch_frame)
        self._swatch_layout.setContentsMargins(0, 0, 0, 0)
        self._swatch_layout.setSpacing(12)
        
        # Swatch Rounded Widget
        self._swatch_box = QWidget()
        self._swatch_box.setFixedSize(72, 72)
        self._swatch_box.setStyleSheet("border-radius: 10px; border: 1.5px solid rgba(255,255,255,10);")
        self._swatch_layout.addWidget(self._swatch_box)
        
        # Quick info label
        self._info_layout = QVBoxLayout()
        self._info_layout.setContentsMargins(0, 4, 0, 4)
        self._info_layout.setSpacing(2)
        
        self._color_title = QLabel("HEX COLOR")
        self._color_title.setStyleSheet("font-size: 8pt; font-weight: 700; color: #7c3aed;")
        
        self._color_subtitle = QLabel("#7C3AED")
        self._color_subtitle.setStyleSheet("font-size: 16pt; font-weight: 700; color: #ffffff;")
        
        self._info_layout.addWidget(self._color_title)
        self._info_layout.addWidget(self._color_subtitle)
        self._swatch_layout.addLayout(self._info_layout)
        self._swatch_layout.addStretch()
        
        # Dropper Activation Button
        self._dropper_btn = QPushButton("💧 Pick Color")
        self._dropper_btn.setFixedHeight(36)
        self._dropper_btn.setToolTip("Pick a color from screen")
        self._dropper_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dropper_btn.setStyleSheet("""
            QPushButton { background: rgba(124,58,237,40); color: white; border-radius: 8px; font-size: 10pt; font-weight: bold; padding: 0 12px; border: 1px solid rgba(124,58,237,100); }
            QPushButton:hover { background: #7c3aed; }
        """)
        self._dropper_btn.clicked.connect(self._start_eyedrop)
        self._swatch_layout.addWidget(self._dropper_btn)
        
        body_layout.addWidget(self._swatch_frame)

        # Shades Widget Panel
        self._shades = _ShadesWidget()
        self._shades.shadeSelected.connect(self._on_shade_selected)
        body_layout.addWidget(self._shades)
        
        # Interactive Color History Row
        self._hist_label = QLabel("RECENT COLORS")
        self._hist_label.setStyleSheet("font-size: 8pt; font-weight: 700; color: #64748b; margin-top: 4px;")
        body_layout.addWidget(self._hist_label)
        
        self._history = _HistoryWidget()
        self._history.colorSelected.connect(self._on_shade_selected)
        self._history.set_colors(self.cfg["color_history"])
        body_layout.addWidget(self._history)

        # Separator Line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2e2a47; background: #2e2a47; max-height: 1px;")
        body_layout.addWidget(sep)
        
        # Tabs
        self._tab_layout = QHBoxLayout()
        self._tab_group = QButtonGroup(self)
        self._tabs = ["Color", ".NET", "CSS"]
        self._current_tab = "Color"
        
        for i, t in enumerate(self._tabs):
            btn = QPushButton(t)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #64748b; font-weight: bold; border: none; padding: 4px; }
                QPushButton:checked { color: #e2e8f0; border-bottom: 2px solid #7c3aed; }
                QPushButton:hover:!checked { color: #94a3b8; }
            """)
            if i == 0: btn.setChecked(True)
            self._tab_group.addButton(btn, i)
            self._tab_layout.addWidget(btn)
        self._tab_layout.addStretch()
        self._tab_group.idClicked.connect(self._on_tab_clicked)
        body_layout.addLayout(self._tab_layout)
        
        # Color values display blocks
        self._hex_row = self._create_value_row("HEX")
        self._rgb_row = self._create_value_row("RGB")
        self._hsl_row = self._create_value_row("HSL")
        self._hsv_row = self._create_value_row("HSV")
        
        body_layout.addWidget(self._hex_row["widget"])
        body_layout.addWidget(self._rgb_row["widget"])
        body_layout.addWidget(self._hsl_row["widget"])
        body_layout.addWidget(self._hsv_row["widget"])
        body_layout.addStretch()
        
        vl.addWidget(body)

    def _on_tab_clicked(self, id):
        self._current_tab = self._tabs[id]
        self._update_values()

    def _create_value_row(self, name):
        w = ClickableFrame()
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        w.setStyleSheet("""
            QFrame {
                background: #111119;
                border: 1px solid #2e2a47;
                border-radius: 6px;
            }
            QFrame:hover {
                background: #1e1e2d;
            }
        """)
        w.setFixedHeight(34)
        lo = QHBoxLayout(w)
        lo.setContentsMargins(10, 0, 10, 0)
        lo.setSpacing(10)
        
        lbl = QLabel(name)
        lbl.setFixedWidth(30)
        lbl.setStyleSheet("color: #7c3aed; font-size: 8pt; font-weight: 700; border: none; background: transparent;")
        
        val = QLineEdit()
        val.setReadOnly(True)
        val.setCursor(Qt.CursorShape.PointingHandCursor)
        val.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        val.setStyleSheet("color: #e2e8f0; font-size: 9pt; border: none; background: transparent; font-family: 'Segoe UI';")
        
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(24, 24)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        copy_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #64748b; border-radius: 4px; font-size: 10pt; }
        """)
        
        lo.addWidget(lbl)
        lo.addWidget(val)
        lo.addWidget(copy_btn)
        
        row_dict = {"widget": w, "val": val, "copy": copy_btn, "val_str": ""}
        w.clicked.connect(lambda d=row_dict: self._copy_value(d))
        
        return row_dict

    def _update_values(self):
        c = self._current_color
        hex_str = c.name().upper()
        
        # Update color swatch block
        self._swatch_box.setStyleSheet(
            f"background-color: {hex_str}; border-radius: 10px; border: 1.5px solid rgba(255,255,255,10);"
        )
        self._color_subtitle.setText(hex_str)
        
        # Load palette shades
        self._shades.set_color(c)
        
        r, g, b, _ = c.getRgb()
        h, s, l, _ = c.getHsl()
        hv, sv, v, _ = c.getHsv()
        h = max(0, h)
        s = int(s/2.55)
        l = int(l/2.55)
        sv = int(sv/2.55)
        v = int(v/2.55)
        
        # Update text input boxes based on tab
        if self._current_tab == "Color":
            self._hex_row["val"].setText(hex_str)
            self._hex_row["val_str"] = hex_str
            self._rgb_row["val"].setText(f"{r}, {g}, {b}")
            self._rgb_row["val_str"] = f"rgb({r}, {g}, {b})"
            self._hsl_row["val"].setText(f"{h}°, {s}%, {l}%")
            self._hsl_row["val_str"] = f"hsl({h}, {s}%, {l}%)"
            self._hsv_row["val"].setText(f"{h}°, {sv}%, {v}%")
            self._hsv_row["val_str"] = f"hsb({h}, {sv}%, {v}%)"
            self._hsv_row["widget"].show()
        elif self._current_tab == ".NET":
            self._hex_row["val"].setText(hex_str)
            self._hex_row["val_str"] = hex_str
            self._rgb_row["val"].setText(f"Color.FromArgb(255,{r},{g},{b})")
            self._rgb_row["val_str"] = f"Color.FromArgb(255,{r},{g},{b})"
            self._hsl_row["val"].setText(f"({h/360:.3f}, {s/100:.3f}, {l/100:.3f})")
            self._hsl_row["val_str"] = f"({h/360:.3f}, {s/100:.3f}, {l/100:.3f})"
            self._hsv_row["val"].setText(f"({h/360:.3f}, {sv/100:.3f}, {v/100:.3f})")
            self._hsv_row["val_str"] = f"({h/360:.3f}, {sv/100:.3f}, {v/100:.3f})"
            self._hsv_row["widget"].show()
        else: # CSS
            self._hex_row["val"].setText(hex_str)
            self._hex_row["val_str"] = hex_str
            self._rgb_row["val"].setText(f"rgb({r}, {g}, {b})")
            self._rgb_row["val_str"] = f"rgb({r}, {g}, {b})"
            self._hsl_row["val"].setText(f"hsl({h}, {s}%, {l}%)")
            self._hsl_row["val_str"] = f"hsl({h}, {s}%, {l}%)"
            self._hsv_row["widget"].hide()

    # ── Eyedropper overlay trigger ────────────────────────────────────────────
    def _start_eyedrop(self):
        self.hide()
        QTimer.singleShot(150, self._show_overlay)

    def _show_overlay(self):
        self._eyedrop.show()

    def _on_eye_pick(self, color: QColor):
        self._current_color = color
        self._update_values()
        
        # Prepend to history & save configuration
        hex_str = color.name().upper()
        hist = self.cfg["color_history"]
        if hex_str in hist:
            hist.remove(hex_str)
        hist.insert(0, hex_str)
        self.cfg["color_history"] = hist[:9]  # Keep last 9 items
        save_cfg(self.cfg)
        
        # Refresh history swatches row
        self._history.set_colors(self.cfg["color_history"])
        
        # Auto copy picked value to clipboard
        QApplication.clipboard().setText(hex_str)
        
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_cancelled(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_shade_selected(self, color: QColor):
        self._current_color = color
        self._update_values()
        QApplication.clipboard().setText(color.name().upper())

    # ── Clipboard copy ────────────────────────────────────────────────────────
    def _copy_value(self, row_dict):
        text = row_dict["val_str"] if "val_str" in row_dict and row_dict["val_str"] else row_dict["val"].text()
        QApplication.clipboard().setText(text)
        
        btn = row_dict["copy"]
        btn.setText("✅")
        btn.setStyleSheet("QPushButton { background: transparent; border: none; color: #10b981; font-size: 10pt; }")
        self._toast.show_msg()
        QTimer.singleShot(1000, lambda: (
            btn.setText("📋"),
            btn.setStyleSheet("QPushButton { background: transparent; border: none; color: #64748b; border-radius: 4px; font-size: 10pt; }")
        ))

    # ── Screen placement ──────────────────────────────────────────────────────
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


# ── Standalone open method ───────────────────────────────────────────────────
def open_color_picker():
    """Builds and launches the Advanced Color Picker widget."""
    picker = ColorPicker()
    picker.show()
    return picker

if __name__ == "__main__":
    import sys
    import os
    # Add root folder to path so package imports resolve correctly
    _parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    app = QApplication(sys.argv)
    picker = ColorPicker()
    picker.show()
    sys.exit(app.exec())
