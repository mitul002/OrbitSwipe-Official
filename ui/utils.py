import os
import sys
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QRect

from orbitswipe.core.utils import _log, extract_icon_png, _dwm_strip, get_asset_path

def load_best_icon():
    for fn in ["OrbitSwipe.ico", "OrbitSwipe.png", "OrbitSwipe-01.png"]:
        p = get_asset_path("image", fn)
        if p and os.path.exists(p): return QIcon(p)
    return None

def make_tray_icon():
    for fn in ["OrbitSwipe2.ico", "OrbitSwipe2.png"]:
        p = get_asset_path("image", fn)
        if p and os.path.exists(p): return QIcon(p)
    
    best = load_best_icon()
    if best and not best.isNull(): return best
    pm = QPixmap(32,32); pm.fill(QColor(0,0,0,0))
    p  = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    g  = QRadialGradient(16,16,16)
    g.setColorAt(0, QColor("#a78bfa")); g.setColorAt(1, QColor("#4c1d95"))
    p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(1,1,30,30)
    p.setPen(QPen(QColor("white"),2))
    p.setFont(QFont("Segoe UI",13,QFont.Weight.Bold))
    p.drawText(QRect(0,0,32,32), Qt.AlignmentFlag.AlignCenter,"(")
    p.end(); return QIcon(pm)
