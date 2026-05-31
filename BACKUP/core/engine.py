import time
import math
import threading
import ctypes
import traceback
import os
import sys
import json
import re
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, Qt
from PyQt6.QtGui import QPixmap, QImage, QColor, QPainter, QFont
from orbitswipe.core.utils import _log, get_asset_path, _dwm_strip, extract_icon_png
from orbitswipe.core.constants import APPDATA_DIR, CF

def make_pm(sz=52, letter="A", color="#7c3aed"):
    pm = QPixmap(sz, sz); pm.fill(QColor(0,0,0,0))
    p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    g = QRadialGradient(sz/2,sz/2,sz/2)
    g.setColorAt(0, QColor(color)); g.setColorAt(1, QColor("#1e003d"))
    p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2,2,sz-4,sz-4)
    p.setPen(QPen(QColor("white")))
    p.setFont(QFont("Segoe UI",sz//3,QFont.Weight.Bold))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, str(letter[:1]).upper())
    p.end(); return pm

from PyQt6.QtGui import QRadialGradient, QBrush, QPen
from PyQt6.QtCore import QRect

class Spring:
    def __init__(self, v=0., k=200, d=18):
        self.v=v; self.vel=0.; self.t=v; self.k=k; self.d=d
    def tick(self, dt=.016):
        self.vel += (self.k*(self.t-self.v) - self.d*self.vel)*dt
        self.v   += self.vel*dt
        return abs(self.t-self.v) > .0005 or abs(self.vel) > .001
    def go(self, t): self.t = t

# ── Sound engine ───────────────────────────────────────────────────────────


class Sound:
    def __init__(self, cfg): self.cfg = cfg
    def _play(self, fn):
        if not self.cfg.get("sound_enabled", True): return
        def _run():
            try:
                sp = get_asset_path("sound", fn)
                if sp and os.path.exists(sp):
                    p = os.path.abspath(sp)
                    al = fn.split(".")[0].replace(" ","_")
                    mci = ctypes.windll.winmm.mciSendStringW
                    mci(f'close {al}', None, 0, 0)
                    res = mci(f'open "{p}" alias {al}', None, 0, 0)
                    if res != 0:
                        mci(f'open "{p}" type mpegvideo alias {al}', None, 0, 0)
                    mci(f'play {al} from 0', None, 0, 0)
                else:
                    _log(f"Sound error: File not found -> {fn}")
            except Exception as e:
                _log(f"MCI Sound Exception: {e}")
        threading.Thread(target=_run, daemon=True).start()
    def open(self):  self._play("bubble up.mp3")
    def close(self): self._play("bubble down.mp3")
    def click(self): self._play("bubble tap.mp3")
    def pin(self):   self._play("pin.mp3")

# ── System stats thread ────────────────────────────────────────────────────


class Stats(QThread):
    updated = pyqtSignal(float, float, bool, float, str, str)
    def __init__(self):
        super().__init__(); self._go = True
        self._last_net = None; self._last_t = time.time()
    def run(self):
        while self._go:
            try:
                import psutil
                cpu  = psutil.cpu_percent(interval=None)
                b    = psutil.sensors_battery()
                bp   = float(b.percent) if b else -1.0
                charging = b.power_plugged if b else False
                ram  = psutil.virtual_memory().percent
                net  = psutil.net_io_counters()
                now  = time.time(); dt = now - self._last_t
                total = net.bytes_sent + net.bytes_recv
                spd = ""
                if self._last_net is not None and dt > 0:
                    bps = (total - self._last_net) / dt
                    if bps > 1024*1024: spd = f"{bps/(1024*1024):.1f} MB/s"
                    elif bps > 1024:    spd = f"{bps/1024:.0f} KB/s"
                    else:               spd = f"{int(bps)} B/s"
                self._last_net = total; self._last_t = now
                self.updated.emit(float(cpu), bp, charging, float(ram), time.strftime("%H:%M"), spd)
            except Exception:
                self.updated.emit(0.0, -1.0, False, 0.0, time.strftime("%H:%M"), "")
            time.sleep(1.0)
    def stop(self): self._go = False; self.quit()

# ── Music Controller ───────────────────────────────────────────────────────


class MediaController:
    def __init__(self, launcher=None):
        self.playing   = False
        self.title     = ""
        self.artist    = ""
        self.app_name  = "System"
        self.app_exe   = ""
        self.launcher  = launcher
        self._go = True
        self._playing = False
        self._track_elapsed  = 0.0
        self._track_duration = 270.0
        self._play_start     = 0.0
        self.peak_vol = 0.0
        self.hwnd = 0
        self._last_active_time = time.time()
        self._started = False

    def start(self):
        if getattr(self, "_started", False): return
        self._started = True
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()
        self._audio_thread = threading.Thread(target=self._audio_monitor, daemon=True)
        self._audio_thread.start()
        self._smtc_thread = threading.Thread(target=self._smtc_monitor, daemon=True)
        self._smtc_thread.start()

    def get_icon_pm(self, sz=52):
        import win32gui, win32con
        if self.app_exe and os.path.exists(self.app_exe):
            data = extract_icon_png(self.app_exe, sz)
            if data: return QPixmap.fromImage(QImage.fromData(data))
        if self.hwnd:
            try:
                hicon = win32gui.SendMessage(self.hwnd, win32con.WM_GETICON, 1, 0)
                if not hicon: hicon = win32gui.GetClassLong(self.hwnd, -14)
                if hicon:
                    pass
            except: pass
        return make_pm(sz, self.app_name[0] if self.app_name and len(self.app_name)>0 else "?")
    @property
    def playing(self): return self._playing

    @playing.setter
    def playing(self, v):
        if v and not getattr(self, "_playing", False):
            self._play_start = time.time()
        elif not v and getattr(self, "_playing", False):
            self._track_elapsed = self._elapsed
            self._play_start = 0.0
        self._playing = v

    @property
    def _elapsed(self):
        if self.playing and self._play_start > 0:
            return self._track_elapsed + (time.time() - self._play_start)
        return self._track_elapsed

    def _monitor(self):
        import win32gui, win32process, psutil, re
        while self._go:
            time.sleep(1.0)
            try:
                target_exes = [
                    "spotify.exe", "vlc.exe", "chrome.exe", "msedge.exe", "brave.exe", 
                    "firefox.exe", "opera.exe", "music.ui.exe", "wmplayer.exe", 
                    "aimp.exe", "foobar2000.exe", "itunes.exe", "microsoft.photos.exe",
                    "video.ui.exe", "plex.exe", "netflix.exe", "microsoft.media.player.exe",
                    "microsoft.zunevideo.exe", "microsoft.zunemusic.exe"
                ]
                
                from pycaw.pycaw import AudioUtilities
                sessions = AudioUtilities.GetAllSessions()
                active_pid = 0
                for s in sessions:
                    if s.Process:
                        pname = s.Process.name().lower()
                        if s.State == 1: # Active audio
                            if pname in target_exes or "player" in pname or "music" in pname or "video" in pname or "photos" in pname:
                                active_pid = s.Process.pid; break
                
                found_h = 0
                def cb(h, _):
                    nonlocal found_h
                    if found_h or not win32gui.IsWindowVisible(h): return
                    _, pid = win32process.GetWindowThreadProcessId(h)
                    if active_pid and pid == active_pid:
                        found_h = h; return
                    if not active_pid:
                        t = win32gui.GetWindowText(h)
                        if not t: return
                        try:
                            p = psutil.Process(pid); name = p.name().lower()
                            if name in target_exes or "photos" in name or "player" in name:
                                # For Photos app, any title is a good title
                                if "photos" in name or " - " in t or name not in t.lower(): found_h = h
                        except: pass
                win32gui.EnumWindows(cb, None)
                self.hwnd = found_h

                if found_h:
                    t = win32gui.GetWindowText(found_h)
                    _, pid = win32process.GetWindowThreadProcessId(found_h)
                    proc = psutil.Process(pid)
                    exe, app = proc.exe(), proc.name().replace(".exe","").capitalize()
                    
                    if t == self.title:
                        if self.playing:
                            if self._elapsed > self._track_duration:
                                self._track_duration = self._elapsed + 40
                        continue

                    # New track detected
                    # IGNORE generic app titles to prevent auto-triggering on launch
                    generic = [app.lower(), "new tab", "google search", "home", "search"]
                    is_generic = t.lower().strip() in generic or not t.strip()
                    
                    self.title, self.app_name, self.app_exe = t, app, exe
                    self._track_elapsed = 0.0
                    self._track_duration = 270.0
                    
                    # Only auto-trigger 'playing' if it looks like a real track (has " - " or " | " or " / ")
                    if not is_generic and (" - " in t or " | " in t or " / " in t):
                        self.playing = True
                    
                    # Try duration detect from window title (e.g. "0:45 / 3:20")
                    m = re.search(r"(\d+):(\d+)\s*/\s*(\d+):(\d+)", t)
                    if m:
                        self._track_elapsed = int(m.group(1))*60 + int(m.group(2))
                        self._track_duration = int(m.group(3))*60 + int(m.group(4))
                        self.playing = True # Definitely a track
                    
                    if self.launcher: self.launcher._on_track_change()
                else:
                    # Window lost, but we don't set playing=False immediately
                    # Silence detection in _audio_monitor will handle it.
                    pass
            except: pass

    def _audio_monitor(self):
        """Fast polling for audio peak volume to drive the visualizer."""
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        import time
        while self._go:
            try:
                target_exes = [
                    "spotify.exe", "vlc.exe", "chrome.exe", "msedge.exe", "brave.exe", 
                    "firefox.exe", "opera.exe", "music.ui.exe", "wmplayer.exe", 
                    "aimp.exe", "foobar2000.exe", "itunes.exe", "microsoft.photos.exe",
                    "video.ui.exe", "plex.exe", "netflix.exe", "microsoft.media.player.exe",
                    "microsoft.zunevideo.exe", "microsoft.zunemusic.exe"
                ]
                sessions = AudioUtilities.GetAllSessions()
                peak = 0.0
                is_active = False
                for s in sessions:
                    if s.Process:
                        pname = s.Process.name().lower()
                        if s.State == 1: # Active audio
                            if pname in target_exes or "player" in pname or "music" in pname or "video" in pname or "photos" in pname:
                                is_active = True
                                try:
                                    meter = s._ctl.QueryInterface(IAudioMeterInformation)
                                    p = meter.GetPeakValue()
                                    if p > peak: peak = p
                                except: pass
                self.peak_vol = peak
                # Trigger playing state ONLY if we actually hear audio (peak > 1%)
                # Idle sessions (is_active) no longer trigger 'playing' state
                if peak > 0.01:
                    self._last_active_time = time.time()
                    self.playing = True
                elif time.time() - self._last_active_time > 3.0:
                    # Only stop playing if SMTC also agrees (handled in _smtc_monitor)
                    # or if we have no window title
                    if not self.hwnd: self.playing = False
            except: pass
            time.sleep(0.03)

    def _smtc_monitor(self):
        """Advanced SMTC monitor via PowerShell to support Photos, Media Player, etc."""
        import subprocess, json
        ps_cmd = "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime] | Out-Null; $m = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync().GetResults(); $s = $m.GetCurrentSession(); if ($s) { $i = $s.TryGetMediaPropertiesAsync().GetResults(); $t = $s.GetTimelineProperties(); $p = $s.GetPlaybackInfo(); $r = @{ title=$i.Title; artist=$i.Artist; app=$s.SourceAppUserModelId; pos=$t.Position.TotalSeconds; dur=$t.EndTime.TotalSeconds; status=$p.PlaybackStatus.ToString() }; $r | ConvertTo-Json -Compress } } catch {}"
        while self._go:
            try:
                res = subprocess.check_output(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], 
                                           creationflags=0x08000000).decode("utf-8", "ignore")
                if res.strip():
                    data = json.loads(res)
                    # Only update if we actually got a title
                    t = data.get("title")
                    if t:
                        self.title = t
                        self.app_name = data.get("app", "").split("!")[0].split(".")[-1].capitalize() or self.app_name
                        # Show widget for both Playing and Paused states
                        self.playing = (data.get("status") in ("Playing", "Paused"))
                        if data.get("status") == "Playing": self._last_active_time = time.time()
                        d = float(data.get("dur", 0))
                        if d > 0: self._track_duration = d
                        # Only sync position if it differs by more than 2 seconds (prevents stuttering)
                        p = float(data.get("pos", 0))
                        if p > 0 and abs(p - self._elapsed) > 2.0:
                            self._track_elapsed = p
                            self._play_start = time.time()
            except: pass
            time.sleep(2.0)
    def play_pause(self):
        try:
            ctypes.windll.user32.keybd_event(0xB3,0,0,0)
            ctypes.windll.user32.keybd_event(0xB3,0,2,0)
        except: pass

    def next_track(self):
        try:
            ctypes.windll.user32.keybd_event(0xB0,0,0,0)
            ctypes.windll.user32.keybd_event(0xB0,0,2,0)
        except: pass

    def prev_track(self):
        try:
            ctypes.windll.user32.keybd_event(0xB1,0,0,0)
            ctypes.windll.user32.keybd_event(0xB1,0,2,0)
        except: pass

    def stop(self):
        self._go = False

# ── Global hotkey — configurable mod+key ──────────────────────────────────


class Hotkey(QThread):
    fired = pyqtSignal()
    pin_requested = pyqtSignal() # New signal for Win+Alt+S
    # Map string names → VK codes
    MOD_MAP = {"Alt": 0x0001, "Ctrl": 0x0002, "Shift": 0x0004, "Win": 0x0008}
    KEY_MAP  = {c: ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
    KEY_MAP.update({"F1":0x70,"F2":0x71,"F3":0x72,"F4":0x73,"F5":0x74,
                     "F6":0x75,"F7":0x76,"F8":0x77,"F9":0x78,"F10":0x79,
                     "F11":0x7A,"F12":0x7B,"SPACE":0x20,"TAB":0x09})

    def _parse_mod(self, s):
        res = 0
        for p in s.split("+"):
            res |= self.MOD_MAP.get(p.strip(), 0)
        return res if res > 0 else 1

    def __init__(self, cfg):
        super().__init__()
        self._cfg = cfg; self._go = True

    def run(self):
        try:
            import ctypes.wintypes
            mod_str = self._cfg.get("hotkey_mod", "Alt")
            key_str = self._cfg.get("hotkey_key", "S").upper()
            mod = self._parse_mod(mod_str)
            vk  = self.KEY_MAP.get(key_str, 0x53)
            
            # Use a Message-Only window for maximum reliability
            HWND_MESSAGE = -3
            hwnd = ctypes.windll.user32.CreateWindowExW(0,"STATIC","",0,0,0,0,0,HWND_MESSAGE,None,None,None)
            
            # Register main launcher trigger (ID 1)
            ctypes.windll.user32.RegisterHotKey(hwnd, 1, mod | 0x4000, vk)
            
            # Register direct WinTop toggle: Configurable (Default Win+Alt+S)
            mod_p_str = self._cfg.get("hotkey_pin_mod", "Win+Alt")
            key_p_str = self._cfg.get("hotkey_pin_key", "S").upper()
            mod_p = self._parse_mod(mod_p_str)
            vk_p  = self.KEY_MAP.get(key_p_str, 0x53)
            ctypes.windll.user32.RegisterHotKey(hwnd, 2, mod_p | 0x4000, vk_p)
            
            msg = ctypes.wintypes.MSG()
            WM_HOTKEY = 0x0312
            while self._go:
                # Process all waiting messages without sleeping in between
                while ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), hwnd, 0, 0, 1):
                    if msg.message == WM_HOTKEY:
                        if msg.wParam == 1:
                            self.fired.emit()
                        elif msg.wParam == 2:
                            self.pin_requested.emit()
                time.sleep(0.02) # Faster polling
            ctypes.windll.user32.UnregisterHotKey(hwnd, 1)
            ctypes.windll.user32.UnregisterHotKey(hwnd, 2)
            ctypes.windll.user32.DestroyWindow(hwnd)
        except Exception as e:
            _log(f"hotkey thread: {e}")

    def stop(self): self._go = False

# ══════════════════════════════════════════════════════════════════════════
#  TRIGGER  — the draggable edge pill
# ══════════════════════════════════════════════════════════════════════════


