"""
Color Picker  —  PowerToys-style with Magnifier
─────────────────────────────────────────────────
Install once:
    pip install pillow pynput pyperclip

Run:
    python color_picker.py

Controls:
    Move mouse        → magnifier follows cursor live
    Scroll wheel      → zoom in / out
    Left click        → pick color
    F1                → pick color (keyboard)
    ESC               → quit
"""

import tkinter as tk
import sys, colorsys, threading

try:
    from PIL import ImageGrab, Image, ImageTk, ImageDraw
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
def grab_region(cx, cy, half):
    try:
        return ImageGrab.grab(bbox=(cx-half, cy-half, cx+half, cy+half), all_screens=True)
    except Exception:
        return ImageGrab.grab(bbox=(cx-half, cy-half, cx+half, cy+half))

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
    return "#000000" if luminance(r,g,b) > 140 else "#ffffff"
def make_shades(r,g,b, n=200):
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
    zoom      = 8          # cells in each direction from center = zoom
    cur_rgb   = (128,128,128)
    history   = []         # newest first, max 20
    running   = True
    pick_now  = False
    over_editor = False    # New flag
s = S()

# ──────────────────────────────────────────────────────────────────────────────
# pynput listeners
# ──────────────────────────────────────────────────────────────────────────────
def _move(x,y):    s.mx, s.my = x, y
def _click(x,y,btn,pressed):
    if pressed and btn == pynmouse.Button.left and not s.over_editor:
        s.pick_now = True
def _scroll(x,y,dx,dy):
    s.zoom = max(2, min(20, s.zoom + (1 if dy>0 else -1)))
def _key(key):
    if key == keyboard.Key.f1:   s.pick_now = True
    elif key == keyboard.Key.esc:
        s.running = False
        return False

for L,kw in [
    (pynmouse.Listener, dict(on_move=_move, on_click=_click, on_scroll=_scroll)),
    (keyboard.Listener, dict(on_press=_key)),
]:
    t = L(**kw); t.daemon = True; t.start()

# ──────────────────────────────────────────────────────────────────────────────
# Magnifier window
# ──────────────────────────────────────────────────────────────────────────────
MAG_PX   = 100   # Much smaller
BAR_H    = 20    # Compact hex bar
CELLS    = 9     # Slightly fewer cells for clarity in smaller size

class Magnifier:
    def __init__(self, root):
        self.win = root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.wm_attributes("-disabled", False)
        # Make sure it's visible immediately
        root.geometry(f"{MAG_PX}x{MAG_PX+BAR_H}+100+100")
        root.deiconify()

        self.cv = tk.Canvas(root, width=MAG_PX, height=MAG_PX+BAR_H,
                            bg="#1a1a1a", highlightthickness=0,
                            cursor="none")
        self.cv.pack()
        self._ref = None
        self._after_id = None
        self._tick()

    def _tick(self):
        if not s.running:
            try: self.win.destroy()
            except: pass
            return

        if s.over_editor:
            self.win.withdraw()
            self._after_id = self.win.after(100, self._tick)
            return
        else:
            self.win.deiconify()

        mx, my = s.mx, s.my
        half = s.zoom * (CELLS // 2 + 1)

        # --- grab screen region ---
        try:
            region = grab_region(mx, my, half)
            r,g,b  = grab_pixel(mx, my)
        except Exception:
            r,g,b = s.cur_rgb
            self._after_id = self.win.after(40, self._tick)
            return

        s.cur_rgb = (r,g,b)

        # --- scale to canvas ---
        zoomed = region.resize((MAG_PX, MAG_PX), Image.NEAREST)

        # --- draw pixel grid lines (subtle) ---
        draw = ImageDraw.Draw(zoomed)
        cell_px = MAG_PX / CELLS
        # grid
        for i in range(1, CELLS):
            x = int(i * cell_px)
            draw.line([(x,0),(x,MAG_PX)], fill=(60,60,60,180), width=1)
            draw.line([(0,x),(MAG_PX,x)], fill=(60,60,60,180), width=1)

        # --- red crosshair on center cell ---
        cx = MAG_PX // 2
        draw.line([(cx,0),(cx,MAG_PX)],   fill=(220,30,30), width=1)
        draw.line([(0,cx),(MAG_PX,cx)],   fill=(220,30,30), width=1)
        # highlight center cell box
        x0 = int((CELLS//2)     * cell_px)
        x1 = int((CELLS//2 + 1) * cell_px)
        draw.rectangle([x0,x0,x1,x1], outline=(220,30,30), width=2)

        # --- circular clip mask ---
        mask = Image.new("L", (MAG_PX, MAG_PX), 0)
        ImageDraw.Draw(mask).ellipse([0,0,MAG_PX-1,MAG_PX-1], fill=255)
        bg   = Image.new("RGB", (MAG_PX, MAG_PX), (26,26,26))
        bg.paste(zoomed, mask=mask)

        # --- outer ring colored by current pixel ---
        ring = ImageDraw.Draw(bg)
        ring.ellipse([0,0,MAG_PX-1,MAG_PX-1],
                     outline=(r,g,b), width=4)
        ring.ellipse([4,4,MAG_PX-5,MAG_PX-5],
                     outline=(40,40,40), width=2)

        # --- hex bar ---
        full = Image.new("RGB", (MAG_PX, MAG_PX+BAR_H), (20,20,20))
        full.paste(bg, (0,0))
        bd = ImageDraw.Draw(full)
        bd.rectangle([0, MAG_PX, MAG_PX, MAG_PX+BAR_H], fill=(r,g,b))
        hex_s = to_hex(r,g,b)
        fg_col = contrasting(r,g,b)
        # center text manually (default font ~6px wide per char)
        tx = (MAG_PX - len(hex_s)*7) // 2
        bd.text((tx, MAG_PX+7), hex_s, fill=fg_col)

        photo = ImageTk.PhotoImage(full)
        self.cv.delete("all")
        self.cv.create_image(0,0, anchor="nw", image=photo)
        self._ref = photo   # keep reference!

        # --- position window near cursor, avoid edge ---
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        ox, oy = 5, 5   # Extreme proximity
        wx = mx + ox
        wy = my + oy
        if wx + MAG_PX + 4 > sw:  wx = mx - MAG_PX - ox
        if wy + MAG_PX + BAR_H + 4 > sh: wy = my - MAG_PX - BAR_H - oy
        self.win.geometry(f"{MAG_PX}x{MAG_PX+BAR_H}+{wx}+{wy}")

        # --- pick? ---
        if s.pick_now:
            s.pick_now = False
            self.win.after(10, lambda: do_pick(r,g,b))

        self._after_id = self.win.after(30, self._tick)  # ~33fps


# ──────────────────────────────────────────────────────────────────────────────
# Editor window
# ──────────────────────────────────────────────────────────────────────────────
BG   = "#2d2d2d"
BG2  = "#1e1e1e"
FG   = "#ffffff"
FG2  = "#888888"
ROW  = "#111111"
SEP  = "#3a3a3a"
HIST_MAX = 20

_editor = None

def do_pick(r,g,b):
    col = (r,g,b)
    if s.history and s.history[0] == col:
        pass
    else:
        s.history.insert(0, col)
        if len(s.history) > HIST_MAX:
            s.history.pop()
    if _editor:
        _editor.refresh(col)
        _editor.win.deiconify()
        _editor.win.lift()

class Editor:
    def __init__(self, win):
        self.win = win
        win.title("Color Picker")
        win.geometry("360x530+20+20")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", self._close)

        # Bind enter/leave events to pause magnifier
        win.bind("<Enter>", lambda e: self._set_over(True))
        win.bind("<Leave>", lambda e: self._set_over(False))

        self._col = (182,206,199)
        self._build()
        self.refresh(self._col)

    def _set_over(self, val):
        s.over_editor = val

    def _build(self):
        w = self.win
        # header
        hdr = tk.Frame(w, bg=BG, height=36)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Color Picker", font=("Segoe UI",11,"bold"),
                 bg=BG, fg=FG).pack(side="left", padx=12)
        tk.Label(hdr, text="ESC = quit  |  F1 / click = pick",
                 font=("Segoe UI",8), bg=BG, fg=FG2).pack(side="right", padx=8)
        tk.Frame(w, bg=SEP, height=1).pack(fill="x")

        # top: swatch + strip
        top = tk.Frame(w, bg=BG, pady=10)
        top.pack(fill="x", padx=12)
        self.swatch = tk.Canvas(top, width=56, height=56, bd=0,
                                highlightthickness=2, highlightbackground=SEP)
        self.swatch.pack(side="left", padx=(0,10))

        sf = tk.Frame(top, bg=BG)
        sf.pack(side="left", fill="both", expand=True)
        self.strip = tk.Canvas(sf, height=36, bd=0,
                               highlightthickness=1, highlightbackground=SEP)
        self.strip.pack(fill="x")
        self.strip.bind("<Button-1>", self._strip_click)
        self.strip.bind("<Configure>", lambda e: self._draw_strip(*self._col))
        self.hex_lbl = tk.Label(sf, text="#------",
                                font=("Courier New",12,"bold"),
                                bg=BG, fg=FG, anchor="w")
        self.hex_lbl.pack(anchor="w", pady=(4,0))

        # tabs
        tf = tk.Frame(w, bg=BG2)
        tf.pack(fill="x")
        self.tab = tk.StringVar(value="Color")
        for t in ("Color", ".NET", "CSS"):
            tk.Radiobutton(tf, text=t, variable=self.tab, value=t,
                           command=lambda: self.refresh(self._col),
                           bg=BG2, fg=FG2, selectcolor=BG2,
                           activebackground=BG2, activeforeground=FG,
                           font=("Segoe UI",10), relief="flat",
                           indicatoron=False, padx=16, pady=5,
                           bd=0, highlightthickness=0).pack(side="left")
        tk.Frame(w, bg=SEP, height=1).pack(fill="x")

        # rows
        self.rows_fr = tk.Frame(w, bg=BG)
        self.rows_fr.pack(fill="x", padx=8, pady=4)

        # history
        tk.Frame(w, bg=SEP, height=1).pack(fill="x")
        hh = tk.Frame(w, bg=BG2, pady=4)
        hh.pack(fill="x")
        tk.Label(hh, text="History (up to 20)",
                 font=("Segoe UI",9,"bold"), bg=BG2, fg=FG2).pack(side="left", padx=12)
        tk.Button(hh, text="Clear", font=("Segoe UI",8),
                  bg=BG2, fg=FG2, relief="flat",
                  activebackground="#333", activeforeground=FG,
                  cursor="hand2",
                  command=self._clear_hist).pack(side="right", padx=8)

        self.hist_fr = tk.Frame(w, bg=BG2)
        self.hist_fr.pack(fill="x", padx=10, pady=6)

        # status
        self.status = tk.Label(w, text="", font=("Segoe UI",8,"italic"),
                               bg=BG, fg="#4ec94e")
        self.status.pack(pady=2)

    def _draw_strip(self,r,g,b):
        self.strip.update_idletasks()
        sw = self.strip.winfo_width() or 240
        sh = self.strip.winfo_height() or 36
        self.strip.delete("all")
        shades = make_shades(r,g,b, sw)
        for i,c in enumerate(shades):
            self.strip.create_line(i,0,i,sh, fill=c)
        lum = luminance(r,g,b)
        mx  = int((1-lum/255)*(sw-1))
        self.strip.create_line(mx,0,mx,sh,     fill="white", width=2)
        self.strip.create_line(mx+1,0,mx+1,sh, fill="black", width=1)

    def _strip_click(self,e):
        sw = self.strip.winfo_width()
        t  = max(0.0, min(1.0, e.x/max(sw-1,1)))
        r,g,b = self._col
        h,l,s2 = colorsys.rgb_to_hls(r/255,g/255,b/255)
        nl = 0.95 - t*0.90
        nr,ng,nb = colorsys.hls_to_rgb(h,nl,s2)
        self.refresh((int(nr*255),int(ng*255),int(nb*255)))

    def _build_rows(self,r,g,b):
        for w in self.rows_fr.winfo_children(): w.destroy()
        hsl  = to_hsl(r,g,b)
        hsb  = to_hsb(r,g,b)
        hex_ = to_hex(r,g,b)
        tab  = self.tab.get()

        if tab=="Color":
            rows=[("HEX", hex_,                                    hex_),
                  ("RGB", f"{r}    {g}    {b}",                    f"rgb({r}, {g}, {b})"),
                  ("HSL", f"{hsl[0]}°  {hsl[1]}%  {hsl[2]}%",     f"hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)"),
                  ("HSB", f"{hsb[0]}°  {hsb[1]}%  {hsb[2]}%",     f"hsb({hsb[0]}, {hsb[1]}%, {hsb[2]}%)")]
        elif tab==".NET":
            rows=[("HEX", hex_,                                                                    hex_),
                  ("RGB", f"Color.FromArgb(255,{r},{g},{b})",                                     f"Color.FromArgb(255,{r},{g},{b})"),
                  ("HSL", f"({hsl[0]/360:.3f}, {hsl[1]/100:.3f}, {hsl[2]/100:.3f})",             ""),
                  ("HSB", f"({hsb[0]/360:.3f}, {hsb[1]/100:.3f}, {hsb[2]/100:.3f})",             "")]
        else:
            rows=[("HEX", hex_,                                                    hex_),
                  ("RGB", f"rgb({r}, {g}, {b})",                                  f"rgb({r}, {g}, {b})"),
                  ("HSL", f"hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)",                f"hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)"),
                  ("HSB", hex_,                                                    hex_)]

        for lbl,disp,cv in rows:
            row = tk.Frame(self.rows_fr, bg=ROW)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, width=5, font=("Segoe UI",9),
                     bg=ROW, fg=FG2, anchor="w", padx=10, pady=8).pack(side="left")
            tk.Label(row, text=disp, font=("Courier New",10),
                     bg=ROW, fg=FG, anchor="w", padx=4, pady=8).pack(side="left", fill="x", expand=True)
            v=cv
            tk.Button(row, text="⧉", font=("Segoe UI",10),
                      bg=ROW, fg=FG2, relief="flat",
                      activebackground="#222", activeforeground=FG,
                      padx=8, pady=4, cursor="hand2",
                      command=lambda x=v: self._copy(x)).pack(side="right")

    def _draw_hist(self):
        for w in self.hist_fr.winfo_children(): w.destroy()
        per_row = 10
        for i,(r,g,b) in enumerate(s.history):
            ri,ci = divmod(i, per_row)
            hex_ = to_hex(r,g,b)
            c = tk.Canvas(self.hist_fr, width=26, height=26, bd=0,
                          highlightthickness=1, highlightbackground="#555",
                          bg=hex_, cursor="hand2")
            c.grid(row=ri, column=ci, padx=2, pady=2)
            col=(r,g,b)
            c.bind("<Button-1>", lambda e,x=col: self.refresh(x))
            c.bind("<Button-3>", lambda e,x=col: self._copy(to_hex(*x)))
            c.bind("<Enter>",    lambda e,cv=c: cv.configure(highlightbackground="white"))
            c.bind("<Leave>",    lambda e,cv=c: cv.configure(highlightbackground="#555"))

    def refresh(self,color):
        r,g,b = color
        self._col = color
        hex_ = to_hex(r,g,b)
        self.swatch.configure(bg=hex_, highlightbackground=hex_)
        self.hex_lbl.configure(text=hex_)
        self._draw_strip(r,g,b)
        self._build_rows(r,g,b)
        self._draw_hist()

    def _copy(self,text):
        clip(text)
        self.status.configure(text=f"Copied  {text}")
        self.win.after(1400, lambda: self.status.configure(text=""))

    def _clear_hist(self):
        s.history.clear()
        self._draw_hist()

    def _close(self):
        s.running = False
        self.win.destroy()


# ──────────────────────────────────────────────────────────────────────────────
# Bootstrap
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()   # hide the root; we use Toplevels

    # Magnifier — use a plain Toplevel so it sits in the same mainloop
    mag_win = tk.Toplevel(root)
    mag = Magnifier(mag_win)

    # Editor panel
    edit_win = tk.Toplevel(root)
    editor   = Editor(edit_win)
    _editor  = editor

    # Watch s.running and quit cleanly
    def _watch():
        if not s.running:
            try: root.destroy()
            except: pass
            return
        root.after(200, _watch)
    root.after(200, _watch)

    root.mainloop()
