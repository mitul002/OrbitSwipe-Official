import os
import time
import json
import hashlib
import base64
import hmac
import uuid
import ctypes
import winreg
import urllib.request
from orbitswipe.core.constants import (LICENSE_FILE, TRIAL_FILE, TRIAL_DAYS, 
                                      LICENSE_URL, APP_NAME, APP_VERSION, APPDATA_DIR)
from orbitswipe.core.utils import _log

# Marker file written when a paid license is revoked/expired. Cleared on re-activation.
LICENSE_EXPIRED_FILE = os.path.join(APPDATA_DIR, "license_expired.dat")

def mark_license_expired(reason="revoked"):
    """Write a marker file so TrialGateDlg knows this was a paid user whose license ended."""
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        with open(LICENSE_EXPIRED_FILE, "w") as f:
            f.write(reason)
        _log(f"License expiration marker written: {reason}")
    except Exception as e:
        _log(f"mark_license_expired error: {e}")

def clear_license_expired_marker():
    """Remove the expiration marker after successful re-activation."""
    try:
        if os.path.exists(LICENSE_EXPIRED_FILE):
            os.remove(LICENSE_EXPIRED_FILE)
            _log("License expiration marker cleared after successful activation.")
    except Exception as e:
        _log(f"clear_license_expired_marker error: {e}")

def is_license_expired_marker_set():
    """Returns True if the user previously had a paid license that was revoked/expired."""
    return os.path.exists(LICENSE_EXPIRED_FILE)

_LIC_SALT = b"0rb1tSw1p3_X9#mK$vP2@qL7!nR4&wZ"   # keep private
OFFLINE_GRACE_PERIOD = 7 * 86400                    # 7 days lease period in seconds

def _machine_id():
    parts = []
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Cryptography", 0,
                           winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        mid, _ = winreg.QueryValueEx(k, "MachineGuid")
        winreg.CloseKey(k); parts.append(mid)
    except Exception: pass
    try:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetComputerNameW(buf, ctypes.byref(ctypes.c_ulong(260)))
        parts.append(buf.value)
    except Exception: pass
    raw = "_".join(parts) or "fallback"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def _hmac_sign(data):
    key = _LIC_SALT + _machine_id().encode()
    return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()

def _xor_encode(data):
    key = _machine_id()
    out = [chr(ord(ch) ^ ord(key[i % len(key)])) for i, ch in enumerate(data)]
    return base64.b64encode("".join(out).encode("latin-1")).decode()

def _xor_decode(encoded):
    raw = base64.b64decode(encoded.encode()).decode("latin-1")
    key = _machine_id()
    return "".join(chr(ord(ch) ^ ord(key[i % len(key)])) for i, ch in enumerate(raw))

def _write_lic_file(path, payload):
    os.makedirs(APPDATA_DIR, exist_ok=True)
    s = json.dumps(payload); sig = _hmac_sign(s)
    blob = json.dumps({"d": _xor_encode(s), "s": sig})
    with open(path, "w") as f: f.write(blob)

def _read_lic_file(path):
    try:
        with open(path) as f: blob = json.loads(f.read())
        s = _xor_decode(blob["d"])
        if not hmac.compare_digest(_hmac_sign(s), blob["s"]):
            _log("License tamper detected"); return None
        return json.loads(s)
    except Exception as e:
        _log(f"_read_lic_file: {e}"); return None

def _get_stealth_locations():
    # 1. Obvious location (Registry)
    loc1 = {"type": "reg", "path": f"Software\\{APP_NAME}", "val": "TrialStart"}
    # 2. Stealth Registry (Deep CLSID-like)
    loc2 = {"type": "reg", "path": r"Software\Classes\CLSID\{B54F3741-5B07-4214-BE35-A43A6B64C001}", "val": "SysState"}
    # 3. Stealth File (In Microsoft folder)
    ms_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Protect")
    loc3 = {"type": "file", "path": os.path.join(ms_dir, "sys_info.db")}
    # 4. AppData File
    loc4 = {"type": "file", "path": TRIAL_FILE}
    return [loc1, loc2, loc3, loc4]

def _get_trial_info():
    now = time.time()
    candidates = []
    
    for loc in _get_stealth_locations():
        try:
            val = None
            if loc["type"] == "reg":
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, loc["path"], 0, winreg.KEY_READ)
                raw, _ = winreg.QueryValueEx(k, loc["val"])
                winreg.CloseKey(k)
                val = float(_xor_decode(raw))
            else:
                if os.path.exists(loc["path"]):
                    data = _read_lic_file(loc["path"])
                    if data: val = data.get("first_run")
            
            if val:
                # Basic clock tamper check
                if val < now + 86400: candidates.append(val)
        except: pass

    # Consensus logic: use the oldest valid date found
    first = min(candidates) if candidates else now
    
    # Sync all locations to ensure persistence
    s_val = _xor_encode(str(first))
    for loc in _get_stealth_locations():
        try:
            if loc["type"] == "reg":
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, loc["path"])
                winreg.SetValueEx(k, loc["val"], 0, winreg.REG_SZ, s_val)
                winreg.CloseKey(k)
            else:
                os.makedirs(os.path.dirname(loc["path"]), exist_ok=True)
                _write_lic_file(loc["path"], {"first_run": first, "machine": _machine_id()})
        except: pass

    elapsed_sec = max(0, now - first)
    total_sec   = TRIAL_DAYS * 86400
    sec_left    = max(0, total_sec - elapsed_sec)
    
    return {
        "first_run": first, 
        "days_used": int(elapsed_sec / 86400), 
        "days_left": int(sec_left / 86400), 
        "sec_left": sec_left,
        "expired": sec_left <= 0
    }

def _validate_license_online(key, email=None, request_transfer=False):
    try:
        import urllib.request
        payload_dict = {"key": key, "machine_id": _machine_id(), "app": "OrbitSwipe", "software_id": "orbitswipe"}
        if email:
            payload_dict["email"] = email
        if request_transfer:
            payload_dict["request_transfer"] = True
        payload = json.dumps(payload_dict).encode()
        req = urllib.request.Request(LICENSE_URL, data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            
            # --- SECURITY CHECK: Verify Server Signature ---
            valid = data.get("valid")
            is_transfer = data.get("message", "").startswith("Transfer request")
            if valid and not is_transfer:
                sig = data.get("signature")
                # Server signs: format_msg + ":" + license_type
                # e.g. "True:{key}:{machine_id}:{license_type}"
                # If someone tampers license_type via proxy, HMAC will fail.
                license_type = data.get("license_type", "lifetime")
                msg = f"True:{key}:{payload_dict['machine_id']}:{license_type}"
                expected_sig = hmac.new(_LIC_SALT, msg.encode(), hashlib.sha256).hexdigest()
                
                if not sig or not hmac.compare_digest(sig, expected_sig):
                    _log("Security: Server signature mismatch or missing!")
                    return {"valid": False, "message": "Security Error: Invalid server response.", "plan": None}
            # -----------------------------------------------
            
            return data
    except Exception as e:
        _log(f"Online license check failed: {e}")
        return {"valid": False, "message": "Network error — check connection and try again.", "plan": None}

def _get_lic_stealth_loc():
    return {"path": r"Software\Classes\CLSID\{B54F3741-5B07-4214-BE35-A43A6B64C002}", "val": "LicToken"}

def _write_license_payload(payload):
    # 1. Write to AppData File
    _write_lic_file(LICENSE_FILE, payload)
    
    # 2. Write to Registry Mirror
    try:
        loc = _get_lic_stealth_loc()
        s = json.dumps(payload)
        sig = _hmac_sign(s)
        blob = json.dumps({"d": _xor_encode(s), "s": sig})
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, loc["path"])
        winreg.SetValueEx(k, loc["val"], 0, winreg.REG_SZ, blob)
        winreg.CloseKey(k)
    except Exception as e:
        _log(f"Registry license backup failed: {e}")

def _read_license_payload():
    # Attempt 1: Read from file
    data = _read_lic_file(LICENSE_FILE)
    if data:
        return data
        
    # Attempt 2: Read from Registry stealth backup (Self-healing recovery)
    try:
        loc = _get_lic_stealth_loc()
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, loc["path"], 0, winreg.KEY_READ)
        raw, _ = winreg.QueryValueEx(k, loc["val"])
        winreg.CloseKey(k)
        
        blob = json.loads(raw)
        s = _xor_decode(blob["d"])
        if hmac.compare_digest(_hmac_sign(s), blob["s"]):
            data = json.loads(s)
            _log("Self-healing: Restoring license file from registry backup.")
            _write_lic_file(LICENSE_FILE, data)
            return data
        else:
            _log("Self-healing: Registry license backup tampered.")
    except Exception as e:
        pass
        
    return None

def _validate_license_offline(key):
    data = _read_license_payload()
    if not data: return {"valid": False, "message": "No offline license found.", "plan": None}
    if data.get("key") != key: return {"valid": False, "message": "License key mismatch.", "plan": None}
    if data.get("machine") != _machine_id():
        return {"valid": False, "message": "License is bound to a different machine.", "plan": None}
    exp = data.get("expires", 0)
    if exp and time.time() > exp: return {"valid": False, "message": "License has expired.", "plan": None}
    return {"valid": True, "message": "License valid (offline).", "plan": data.get("plan", "Pro"), "license_type": data.get("license_type", "lifetime")}

def activate_license(key, email=None, request_transfer=False):
    key = key.strip().upper()
    if not key: return {"valid": False, "message": "Please enter a license key.", "plan": None}
    result = _validate_license_online(key, email=email, request_transfer=request_transfer)
    if result.get("valid") and not request_transfer:
        _write_license_payload({
            "key": key, "machine": _machine_id(),
            "plan": result.get("plan", "Pro"),
            "license_type": result.get("license_type", "lifetime"),
            "expires": result.get("expires", 0),
            "activated_at": time.time(),
            "last_online_check": time.time(),
        })
        # Clear expiration marker — user has successfully re-activated
        clear_license_expired_marker()
        _log(f"License activated: {key[:8]}… plan={result.get('plan')}")
    return result

def get_license_status():
    data  = _read_license_payload()
    trial = _get_trial_info()
    if data and data.get("machine") == _machine_id():
        # Enforce 7-day offline grace period lease limit!
        last_check = data.get("last_online_check", data.get("activated_at", 0))
        elapsed = time.time() - last_check
        if elapsed > OFFLINE_GRACE_PERIOD:
            _log("Offline lease period expired. Verification required.")
            return {"licensed": False, "plan": None, "key_preview": "", "trial": trial, "lease_expired": True}

        exp = data.get("expires", 0)
        if exp == 0 or time.time() < exp:
            k = data.get("key", "")
            preview = (k[:4] + "-****-****-" + k[-4:]) if len(k) >= 8 else k
            return {"licensed": True, "plan": data.get("plan", "Pro"),
                    "license_type": data.get("license_type", "lifetime"),
                    "key_preview": preview, "trial": trial}
    return {"licensed": False, "plan": None, "key_preview": "", "trial": trial}

def is_app_allowed():
    st = get_license_status()
    if st.get("lease_expired", False):
        return False
    return st["licensed"] or not st["trial"]["expired"]

def deactivate_license():
    # 1. Write expiration marker BEFORE deleting license data
    mark_license_expired("revoked")

    # 2. Delete AppData license file
    try:
        if os.path.exists(LICENSE_FILE): os.remove(LICENSE_FILE)
    except Exception as e: _log(f"deactivate file: {e}")
    
    # 3. Delete Registry mirror
    try:
        import winreg
        loc = _get_lic_stealth_loc()
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, loc["path"])
        _log("Stealth license registry mirror successfully deleted.")
    except Exception as e:
        pass

def check_license_online_silent():
    data = _read_license_payload()
    if not data:
        return {"valid": False, "status": "no_license"}
        
    key = data.get("key")
    if not key:
        return {"valid": False, "status": "no_key"}
        
    # Attempt online validation
    result = _validate_license_online(key)
    
    # CASE A: Explicit Revocation (Server says invalid, and NOT a network/connection error)
    if result.get("valid") is False and "Network error" not in result.get("message", ""):
        _log(f"License revoked online by server: {result.get('message')}. Deactivating...")
        deactivate_license()
        return {"valid": False, "status": "revoked"}
        
    # CASE B: Online Validation Successful
    elif result.get("valid") is True:
        _log("License silently verified online successfully.")
        data["last_online_check"] = time.time()
        # Refresh plan & license_type from server response (in case admin changed them)
        if result.get("plan"):
            data["plan"] = result.get("plan")
        if result.get("license_type"):
            data["license_type"] = result.get("license_type")
        _write_license_payload(data)
        return {"valid": True, "status": "verified"}
        
    # CASE C: User is Offline / Network Error
    else:
        last_check = data.get("last_online_check", data.get("activated_at", 0))
        elapsed = time.time() - last_check
        
        if elapsed < OFFLINE_GRACE_PERIOD:
            days_left = int((OFFLINE_GRACE_PERIOD - elapsed) / 86400)
            _log(f"Offline launch approved. {days_left} days remaining on lease.")
            return {"valid": True, "status": "offline_approved"}
        else:
            _log("Offline grace period expired. Internet required for verification.")
            return {"valid": False, "status": "offline_expired"}



