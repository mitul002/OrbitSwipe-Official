import os
import sys
import time
import io
import base64
import ctypes
from orbitswipe.core.constants import APPDATA_DIR, LOG_FILE, IS_FROZEN

def _log(msg):
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 500 * 1024:
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                if len(lines) > 200:
                    with open(LOG_FILE, "w", encoding="utf-8") as f:
                        f.writelines(lines[-200:])
            except Exception:
                pass
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def get_asset_path(fld, fn):
    # Try PyInstaller's _MEIPASS first
    base_path = getattr(sys, '_MEIPASS', None)
    if not base_path:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    _log(f"Asset check: base={base_path}, fld={fld}, fn={fn}")
    
    # Try multiple folder combinations
    checks = [
        os.path.join(base_path, fld, fn),
        os.path.join(base_path, "orbitswipe", fld, fn),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", fld, fn),
        os.path.join(os.getcwd(), fld, fn)
    ]
    
    for p in checks:
        if os.path.exists(p): 
            _log(f"Asset FOUND: {p}")
            return os.path.abspath(p)
    
    _log(f"Asset NOT FOUND: {fld}/{fn}")
    return None



def _dwm_strip(hwnd):
    try:
        import win32gui, win32con
        # Remove caption and thick frame but PRESERVE EX_TOPMOST
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~win32con.WS_CAPTION
        style &= ~win32con.WS_THICKFRAME
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TOPMOST  # Force it back just in case
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        class MARGINS(ctypes.Structure):
            _fields_ = [("l",ctypes.c_int),("r",ctypes.c_int),
                         ("t",ctypes.c_int),("b",ctypes.c_int)]
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
            int(hwnd), ctypes.byref(MARGINS(-1,-1,-1,-1)))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd), 2, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd), 33, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass



def extract_icon_png(path, sz=52):
    try:
        import win32gui, win32ui, win32con
        from PIL import Image, ImageChops
        resolved = path
        if path.lower().endswith('.lnk'):
            try:
                import win32com.client
                sh = win32com.client.Dispatch("WScript.Shell")
                tp = sh.CreateShortcut(path).TargetPath
                if tp and os.path.exists(tp): resolved = tp
            except Exception:
                pass
        hicon = None
        try:
            class SFI(ctypes.Structure):
                _fields_ = [('hIcon',ctypes.c_void_p),('iIcon',ctypes.c_int),
                             ('dwAttr',ctypes.c_ulong),('szDN',ctypes.c_wchar*260),
                             ('szTN',ctypes.c_wchar*80)]
            fi = SFI(); flags = 0x100; attrs = 0
            if os.path.isdir(resolved):
                flags |= 0x10; attrs = 0x10
            ctypes.windll.shell32.SHGetFileInfoW(
                resolved, attrs, ctypes.byref(fi), ctypes.sizeof(fi), flags)
            hicon = fi.hIcon
        except Exception:
            pass
        if not hicon:
            try:
                lg, sm = win32gui.ExtractIconEx(resolved, 0)
                for h in (sm or []):
                    try: win32gui.DestroyIcon(h)
                    except: pass
                if lg: hicon = lg[0]
            except Exception:
                pass
        if not hicon: return None

        # FIX: properly release all GDI objects
        def render(bg):
            screen_dc = win32gui.GetDC(0)
            mdc = win32ui.CreateDCFromHandle(screen_dc)
            cdc = mdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(mdc, sz, sz)
            old_bmp = cdc.SelectObject(bmp)
            cdc.FillSolidRect((0,0,sz,sz), bg)
            win32gui.DrawIconEx(cdc.GetHandleOutput(),0,0,hicon,sz,sz,0,None,win32con.DI_NORMAL)
            bits = bytes(bmp.GetBitmapBits(True))
            cdc.SelectObject(old_bmp)   # deselect before delete
            win32gui.DeleteObject(bmp.GetHandle())
            cdc.DeleteDC()
            mdc.DeleteDC()
            win32gui.ReleaseDC(0, screen_dc)
            return bits

        rb = render(0x000000); rw = render(0xFFFFFF)
        try: win32gui.DestroyIcon(hicon)
        except: pass
        ib = Image.frombuffer('RGBA',(sz,sz),rb,'raw','BGRA',0,1).convert('RGB')
        iw = Image.frombuffer('RGBA',(sz,sz),rw,'raw','BGRA',0,1).convert('RGB')
        dr,dg,db = ImageChops.difference(iw, ib).split()
        alpha = ImageChops.lighter(ImageChops.lighter(dr,dg),db).point(lambda x: 255-x)
        res = ib.copy(); res.putalpha(alpha)
        buf = io.BytesIO(); res.save(buf, 'PNG')
        return buf.getvalue()
    except Exception as e:
        _log(f"icon extract: {e}")
        return None

# ── Pixmap helpers ─────────────────────────────────────────────────────────


