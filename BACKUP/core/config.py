import os
import json
import threading
from orbitswipe.core.constants import CONFIG_FILE, DEFAULT_CFG, CONFIG_VERSION, APPDATA_DIR
from orbitswipe.core.utils import _log

_save_timer = None
_save_lock  = threading.Lock()

def _migrate(d):
    v = d.get("_cfg_version", 0)
    if v < 1:
        d.setdefault("glass_preset", "Dynamic Glass")
        d.setdefault("glass_custom_color", "#ffffff")
    if v < 2:
        d.setdefault("independent_scroll", False)
        d.setdefault("scroll_sensitivity", 0.6)
    if v < 3:
        d.setdefault("show_network", False)
        d.setdefault("hotkey_mod", "Alt")
        d.setdefault("hotkey_key", "S")
        # rename old hub_stat → show_network
        if d.get("hub_stat") == "network":
            d["show_network"] = True
        d.pop("hub_stat", None)
    if v < 4:
        has_vercel = False
        items = d.get("items", [])
        for item in items:
            if isinstance(item, dict) and item.get("type") == "url" and "orbitswipe.vercel.app" in item.get("url", ""):
                has_vercel = True
                break
        if not has_vercel:
            idx = len(items)
            for i, item in enumerate(items):
                if isinstance(item, dict) and item.get("type") == "tool":
                    idx = i
                    break
            items.insert(idx, {"type":"url","name":"OrbitSwipe","url":"https://orbitswipe.vercel.app/","icon":"🌐","icon_b64":""})
            d["items"] = items
    d["_cfg_version"] = CONFIG_VERSION
    return d



def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            _migrate(d)
            for k, v in DEFAULT_CFG.items():
                d.setdefault(k, v)
            return d
        except Exception as e:
            _log(f"load_cfg error: {e}")
    return dict(DEFAULT_CFG)



def save_cfg(c, immediate=False):
    """Write config to disk.  Normally debounced (300 ms); pass immediate=True
    for critical saves (e.g. user presses Save in edit mode)."""
    global _save_timer
    def _do_save():
        try:
            os.makedirs(APPDATA_DIR, exist_ok=True)
            tmp = CONFIG_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(c, f, indent=2)
            os.replace(tmp, CONFIG_FILE)   # atomic rename, no fsync needed
        except Exception as e:
            _log(f"save_cfg error: {e}")
    if immediate:
        _do_save()
        return
    with _save_lock:
        if _save_timer is not None:
            _save_timer.cancel()
        _save_timer = threading.Timer(0.3, _do_save)
        _save_timer.daemon = True
        _save_timer.start()



