"""
Color Picker  —  PowerToys-style with Magnifier
─────────────────────────────────────────────────
Install once:
    pip install pillow pynput pyperclip

Run:
    python color_picker.py

Controls (while magnifier is active on screen):
    Move mouse        → magnifier follows cursor
    Scroll wheel up   → zoom in
    Scroll wheel down → zoom out
    Left click        → pick color → opens/updates Editor
    F1                → pick color (keyboard)
    ESC               → quit everything
"""

import tkinter as tk
from tkinter import ttk
import sys, colorsys, time

try:
    from PIL import ImageGrab, Image, ImageTk, ImageDraw, ImageFont
except ImportError:
    sys.exit("Run:  pip install pillow")
try:
    from pynput import keyboard, mouse as pynmouse
except ImportError:
    sys.exit("Run:  pip install pynput")
try:
    import pyperclip
    def clip(t): pyperclip.copy(t)
except ImportError:
    def clip(t): pass

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def grab_region(x, y, r=40):
    x0, y0 = x - r, y - r
    x1, y1 = x + r, y + r
    try:
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
    except Exception:
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1))
    return img

def grab_pixel(x, y):
    try:
        img = ImageGrab.grab(bbox=(x, y, x+1, y+1), all_screens=True)
    except Exception:
        img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
    px = img.getpixel((0, 0))
    return px[0], px[1], px[2]

def to_hex(r,g,b):   return f"#{r:02X}{g:02X}{b:02X}"

def to_hsl(r,g,b):
    h,l,s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return round(h*360), round(s*100), round(l*100)

def to_hsb(r,g,b):
    h,s,v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    return round(h*360), round(s*100), round(v*100)

def luminance(r,g,b):
    return 0.299*r + 0.587*g + 0.114*b

def contrasting(r,g,b):
    return "#000000" if luminance(r,g,b) > 128 else "#ffffff"

def make_shades(r,g,b, n=20):
    h,l,s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    cols = []
    if n <= 1: return [to_hex(r,g,b)]
    for i in range(n):
        nl = 0.95 - (i/(n-1)) * 0.90
        nr,ng,nb = colorsys.hls_to_rgb(h, nl, s)
        cols.append(to_hex(int(nr*255), int(ng*255), int(nb*255)))
    return cols

# ──────────────────────────────────────────────────────────────────────────────
# Shared state
# ──────────────────────────────────────────────────────────────────────────────
class S:
    mx = my = 400
    zoom = 8            # pixels per cell in magnifier
    cur_rgb = (128,128,128)
    history = []        # list of (r,g,b), newest first, max 20
    running  = True
    pick_requested = False   # set by hotkey/click → read by magnifier tick

s = S()

# ──────────────────────────────────────────────────────────────────────────────
# Magnifier overlay window  (follows cursor, always on top)
# ──────────────────────────────────────────────────────────────────────────────
MAG_CELLS   = 11        # odd number so center cell is exact pixel
MAG_CELL_SZ = 15        # px per cell at zoom=1; actual cell = zoom * MAG_CELL_SZ / 8
MAG_SIZE    = 220       # final canvas size
CROSS_COLOR = "#ff0000"

class Magnifier:
    def __init__(self, root):
        self.root = root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", "")   # no transparency needed
        root.configure(bg="#000000")

        self.canvas = tk.Canvas(root, width=MAG_SIZE, height=MAG_SIZE+28,
                                bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack()
        self._img_ref = None
        self._tick()

    def _tick(self):
        if not s.running:
            self.root.destroy()
            return

        mx, my = s.mx, s.my

        # grab region around cursor
        grab_r = (MAG_CELLS // 2) + 2
        try:
            region = grab_region(mx, my, r=grab_r * s.zoom // 2 + s.zoom)
        except Exception:
            self.root.after(40, self._tick)
            return

        # center pixel color
        try:
            r,g,b = grab_pixel(mx, my)
            s.cur_rgb = (r,g,b)
        except Exception:
            r,g,b = s.cur_rgb

        # resize region to magnifier canvas
        cell = max(2, int(MAG_SIZE // MAG_CELLS))
        total = cell * MAG_CELLS
        zoomed = region.resize((total, total), Image.NEAREST)

        # draw onto PIL image with crosshair + center box highlight
        draw = ImageDraw.Draw(zoomed)
        cx = total // 2
        # crosshair lines
        draw.line([(cx, 0),       (cx, total)],       fill=CROSS_COLOR, width=1)
        draw.line([(0,  cx),      (total, cx)],        fill=CROSS_COLOR, width=1)
        # highlight center cell
        x0,y0 = cx - cell//2, cx - cell//2
        x1,y1 = cx + cell//2, cx + cell//2
        draw.rectangle([x0,y0,x1,y1], outline=CROSS_COLOR, width=2)

        # circular mask  (round magnifier)
        mask = Image.new("L", (total,total), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse([0,0,total-1,total-1], fill=255)
        zoomed_rgba = zoomed.convert("RGBA")
        bg_img = Image.new("RGBA", (total,total), (26,26,26,255))
        bg_img.paste(zoomed_rgba, mask=mask)

        # border ring
        ring = ImageDraw.Draw(bg_img)
        ring.ellipse([0,0,total-1,total-1], outline="#444444", width=3)
        inner_col = to_hex(r,g,b)
        ring.ellipse([2,2,total-3,total-3], outline=inner_col, width=2)

        # color info bar below circle
        bar_h = 28
        full = Image.new("RGBA", (total, total+bar_h), (20,20,20,255))
        full.paste(bg_img, (0,0))

        bar_draw = ImageDraw.Draw(full)
        bar_draw.rectangle([0, total, total, total+bar_h], fill=to_hex(r,g,b))
        hex_str = to_hex(r,g,b)
        try:
            fnt = ImageFont.truetype("arial.ttf", 12)
        except Exception:
            fnt = ImageFont.load_default()
        fg = contrasting(r,g,b)
        # center the text
        try:
            bbox = fnt.getbbox(hex_str)
            tw = bbox[2]-bbox[0]
        except Exception:
            tw = len(hex_str)*7
        tx = (total - tw) // 2
        bar_draw.text((tx, total+6), hex_str, fill=fg, font=fnt)

        photo = ImageTk.PhotoImage(full.resize((MAG_SIZE, MAG_SIZE+bar_h), Image.LANCZOS))
        self.canvas.configure(width=MAG_SIZE, height=MAG_SIZE+bar_h)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=photo)
        self._img_ref = photo

        # position window: offset from cursor so it doesn't cover it
        wx = mx + 24
        wy = my + 24
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if wx + MAG_SIZE + 20 > sw: wx = mx - MAG_SIZE - 24
        if wy + MAG_SIZE + 48 > sh: wy = my - MAG_SIZE - 48
        self.root.geometry(f"{MAG_SIZE}x{MAG_SIZE+bar_h}+{wx}+{wy}")

        # check if pick was requested
        if s.pick_requested:
            s.pick_requested = False
            self.root.after(10, lambda: _do_pick(r,g,b))

        self.root.after(40, self._tick)   # 25 fps — low CPU


# ──────────────────────────────────────────────────────────────────────────────
# Editor window  (panel shown after picking)
# ──────────────────────────────────────────────────────────────────────────────
BG   = "#2d2d2d"
BG2  = "#1e1e1e"
BG3  = "#111111"
FG   = "#ffffff"
FG2  = "#888888"
ROW  = "#0f0f0f"
SEP  = "#3a3a3a"
SWATCH_W = 28
SWATCH_H = 28
HIST_MAX = 20

class Editor:
    def __init__(self, root):
        self.root = root
        root.title("Color Picker")
        root.geometry("360x520+900+100")
        root.resizable(False, False)
        root.configure(bg=BG)
        root.attributes("-topmost", True)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._picked = (182, 206, 199)
        self._build()
        self.refresh((182,206,199))

    def _build(self):
        r = self.root

        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(r, bg=BG, height=40)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎨  Color Picker",
                 font=("Segoe UI", 11, "bold"), bg=BG, fg=FG).pack(side="left", padx=14)
        tk.Label(hdr, text="ESC = quit",
                 font=("Segoe UI", 8), bg=BG, fg=FG2).pack(side="right", padx=10)

        tk.Frame(r, bg=SEP, height=1).pack(fill="x")

        # ── swatch + shade strip ──────────────────────────────────────────────
        top = tk.Frame(r, bg=BG, pady=12)
        top.pack(fill="x", padx=14)

        self.swatch = tk.Canvas(top, width=58, height=58, bd=0,
                                highlightthickness=2,
                                highlightbackground=SEP, bg="#aaaaaa")
        self.swatch.pack(side="left", padx=(0,12))

        strip_fr = tk.Frame(top, bg=BG)
        strip_fr.pack(side="left", fill="both", expand=True)

        self.strip = tk.Canvas(strip_fr, height=38, bd=0,
                               highlightthickness=1,
                               highlightbackground=SEP, bg="#888")
        self.strip.pack(fill="x")
        self.strip.bind("<Button-1>", self._strip_click)
        self.strip.bind("<Configure>", lambda e: self._draw_strip(*self._picked))

        # hex badge under strip
        self.hex_badge = tk.Label(strip_fr, text="#------",
                                  font=("Courier New", 11, "bold"),
                                  bg=BG, fg=FG, anchor="w")
        self.hex_badge.pack(anchor="w", pady=(4,0))

        # ── tabs ──────────────────────────────────────────────────────────────
        tab_fr = tk.Frame(r, bg=BG2)
        tab_fr.pack(fill="x")
        self.tab_var = tk.StringVar(value="Color")
        for t in ("Color", ".NET", "CSS"):
            b = tk.Radiobutton(tab_fr, text=t, variable=self.tab_var, value=t,
                               command=lambda: self.refresh(self._picked),
                               bg=BG2, fg=FG2, selectcolor=BG2,
                               activebackground=BG2, activeforeground=FG,
                               font=("Segoe UI", 10), relief="flat",
                               indicatoron=False, padx=18, pady=6,
                               bd=0, highlightthickness=0)
            b.pack(side="left")

        tk.Frame(r, bg=SEP, height=1).pack(fill="x")

        # ── color rows ────────────────────────────────────────────────────────
        self.rows_fr = tk.Frame(r, bg=BG)
        self.rows_fr.pack(fill="x", padx=10, pady=6)

        # ── history section ───────────────────────────────────────────────────
        tk.Frame(r, bg=SEP, height=1).pack(fill="x")

        hist_hdr = tk.Frame(r, bg=BG2, pady=5)
        hist_hdr.pack(fill="x")
        tk.Label(hist_hdr, text="Color History",
                 font=("Segoe UI", 9, "bold"), bg=BG2, fg=FG2).pack(side="left", padx=14)
        tk.Button(hist_hdr, text="Clear",
                  font=("Segoe UI", 8), bg=BG2, fg=FG2,
                  relief="flat", activebackground=BG2, activeforeground=FG,
                  command=self._clear_history, cursor="hand2").pack(side="right", padx=10)

        self.hist_outer = tk.Frame(r, bg=BG2)
        self.hist_outer.pack(fill="both", expand=True, padx=10, pady=6)

        # canvas + scrollbar for history grid
        self.hist_canvas = tk.Canvas(self.hist_outer, bg=BG2,
                                     highlightthickness=0, height=130)
        sb = tk.Scrollbar(self.hist_outer, orient="vertical",
                          command=self.hist_canvas.yview)
        self.hist_canvas.configure(yscrollcommand=sb.set)
        self.hist_canvas.pack(side="left", fill="both", expand=True)

        self.hist_grid = tk.Frame(self.hist_canvas, bg=BG2)
        self.hist_canvas.create_window((0,0), window=self.hist_grid, anchor="nw")
        self.hist_grid.bind("<Configure>",
            lambda e: self.hist_canvas.configure(
                scrollregion=self.hist_canvas.bbox("all")))

        # ── footer ────────────────────────────────────────────────────────────
        self.status = tk.Label(r, text="", font=("Segoe UI", 8, "italic"),
                               bg=BG, fg="#4ec94e", height=1)
        self.status.pack()

    # ── draw shade strip ──────────────────────────────────────────────────────
    def _draw_strip(self, r,g,b):
        self.strip.update_idletasks()
        sw = self.strip.winfo_width() or 240
        sh = self.strip.winfo_height() or 38
        self.strip.delete("all")
        shades = make_shades(r,g,b, sw)
        for i,col in enumerate(shades):
            self.strip.create_line(i, 0, i, sh, fill=col)
        # marker
        lum = luminance(r,g,b)
        mx = int((1 - lum/255) * (sw-1))
        self.strip.create_line(mx,   0, mx,   sh, fill="white", width=2)
        self.strip.create_line(mx+1, 0, mx+1, sh, fill="black", width=1)

    def _strip_click(self, e):
        sw = self.strip.winfo_width()
        t  = max(0, min(1, e.x / max(sw-1,1)))
        r,g,b = self._picked
        h,l,s = colorsys.rgb_to_hls(r/255,g/255,b/255)
        nl = 0.95 - t*0.90
        nr,ng,nb = colorsys.hls_to_rgb(h,nl,s)
        self.refresh((int(nr*255), int(ng*255), int(nb*255)))

    # ── build color rows ──────────────────────────────────────────────────────
    def _build_rows(self, color):
        for w in self.rows_fr.winfo_children():
            w.destroy()
        r,g,b = color
        hsl = to_hsl(r,g,b)
        hsb = to_hsb(r,g,b)
        hex_ = to_hex(r,g,b)
        tab  = self.tab_var.get()

        if tab == "Color":
            rows = [
                ("HEX", hex_,                                     hex_),
                ("RGB", f"{r}     {g}     {b}",                   f"rgb({r}, {g}, {b})"),
                ("HSL", f"{hsl[0]}°   {hsl[1]}%   {hsl[2]}%",    f"hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)"),
                ("HSB", f"{hsb[0]}°   {hsb[1]}%   {hsb[2]}%",    f"hsb({hsb[0]}, {hsb[1]}%, {hsb[2]}%)"),
            ]
        elif tab == ".NET":
            rows = [
                ("HEX", hex_,                                                              hex_),
                ("RGB", f"Color.FromArgb(255, {r}, {g}, {b})",                            f"Color.FromArgb(255, {r}, {g}, {b})"),
                ("HSL", f"({hsl[0]/360:.3f}, {hsl[1]/100:.3f}, {hsl[2]/100:.3f})",       ""),
                ("HSB", f"({hsb[0]/360:.3f}, {hsb[1]/100:.3f}, {hsb[2]/100:.3f})",       ""),
            ]
        else:  # CSS
            rows = [
                ("HEX", hex_,                                                              hex_),
                ("RGB", f"rgb({r}, {g}, {b})",                                            f"rgb({r}, {g}, {b})"),
                ("HSL", f"hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)",                          f"hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)"),
                ("HSB", hex_,                                                              hex_),
            ]

        for lbl, display, copy_val in rows:
            row = tk.Frame(self.rows_fr, bg=ROW, pady=0)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, width=5,
                     font=("Segoe UI", 9), bg=ROW, fg=FG2,
                     anchor="w", padx=10, pady=9).pack(side="left")
            tk.Label(row, text=display,
                     font=("Courier New", 10), bg=ROW, fg=FG,
                     anchor="w", padx=4, pady=9).pack(side="left", fill="x", expand=True)
            cv = copy_val
            tk.Button(row, text="⧉", font=("Segoe UI",10),
                      bg=ROW, fg=FG2, relief="flat",
                      activebackground="#252525", activeforeground=FG,
                      padx=8, pady=5, cursor="hand2",
                      command=lambda v=cv: self._copy(v)).pack(side="right")

    # ── history grid ──────────────────────────────────────────────────────────
    def _draw_history(self):
        for w in self.hist_grid.winfo_children():
            w.destroy()

        cols = 10
        for i, (r,g,b) in enumerate(s.history):
            hex_ = to_hex(r,g,b)
            row_i, col_i = divmod(i, cols)
            outer = tk.Frame(self.hist_grid, bg=BG2, padx=1, pady=1)
            outer.grid(row=row_i, column=col_i, padx=2, pady=2)
            c = tk.Canvas(outer, width=SWATCH_W, height=SWATCH_H, bd=0,
                          highlightthickness=1, highlightbackground="#555",
                          bg=hex_, cursor="hand2")
            c.pack()
            tip_color = (r,g,b)
            c.bind("<Button-1>",   lambda e, col=tip_color: self.refresh(col))
            c.bind("<Button-3>",   lambda e, col=tip_color: self._copy(to_hex(*col)))
            c.bind("<Enter>",      lambda e, cv=c, hx=hex_: cv.configure(highlightbackground="#ffffff"))
            c.bind("<Leave>",      lambda e, cv=c: cv.configure(highlightbackground="#555555"))

        # tooltip hint
        if s.history:
            tk.Label(self.hist_grid, text="Left-click = select   Right-click = copy hex",
                     font=("Segoe UI", 7), bg=BG2, fg="#555",
                     anchor="w").grid(row=(len(s.history)//cols)+1,
                                      column=0, columnspan=cols, sticky="w", pady=(4,0))

    # ── main refresh ──────────────────────────────────────────────────────────
    def refresh(self, color):
        r,g,b = color
        self._picked = color
        hex_ = to_hex(r,g,b)

        self.swatch.configure(bg=hex_, highlightbackground=hex_)
        self.hex_badge.configure(text=hex_)
        self._draw_strip(r,g,b)
        self._build_rows(color)
        self._draw_history()

    def _copy(self, text):
        clip(text)
        self.status.configure(text=f"Copied: {text}")
        self.root.after(1500, lambda: self.status.configure(text=""))

    def _clear_history(self):
        s.history.clear()
        self._draw_history()

    def _on_close(self):
        s.running = False
        self.root.destroy()


# ──────────────────────────────────────────────────────────────────────────────
# Pick action  (called from magnifier thread → tkinter safe via after())
# ──────────────────────────────────────────────────────────────────────────────
_editor_ref = None

def _do_pick(r,g,b):
    col = (r,g,b)
    if col not in s.history:
        s.history.insert(0, col)
        if len(s.history) > HIST_MAX:
            s.history.pop()
    if _editor_ref:
        _editor_ref.refresh(col)
        _editor_ref.root.deiconify()
        _editor_ref.root.lift()


# ──────────────────────────────────────────────────────────────────────────────
# Global hotkeys + mouse click via pynput
# ──────────────────────────────────────────────────────────────────────────────
def _on_mouse_move(x, y):
    s.mx, s.my = x, y

def _on_mouse_click(x, y, button, pressed):
    if pressed and button == pynmouse.Button.left:
        s.pick_requested = True

def _on_scroll(x, y, dx, dy):
    if dy > 0:
        s.zoom = min(s.zoom + 1, 20)
    else:
        s.zoom = max(s.zoom - 1, 2)

def _on_key(key):
    if key == keyboard.Key.f1:
        s.pick_requested = True
    elif key == keyboard.Key.esc:
        s.running = False
        if _editor_ref:
            _editor_ref.root.after(0, _editor_ref.root.destroy)
        return False

ml = pynmouse.Listener(on_move=_on_mouse_move,
                       on_click=_on_mouse_click,
                       on_scroll=_on_scroll)
ml.daemon = True
ml.start()

kl = keyboard.Listener(on_press=_on_key)
kl.daemon = True
kl.start()

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Magnifier window
    mag_root = tk.Tk()
    mag_root.withdraw()
    mag_root.overrideredirect(True)
    mag_root.attributes("-topmost", True)
    mag_root.configure(bg="#000000")
    mag = Magnifier(mag_root)

    # Editor window
    edit_root = tk.Toplevel(mag_root)
    editor = Editor(edit_root)
    _editor_ref = editor

    mag_root.mainloop()
    s.running = False
