import os
import sys
import ctypes
import shutil
import subprocess
import time
import winreg
import psutil

APP_NAME = "OrbitSwipe"
APPDATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), APP_NAME)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def kill_processes():
    mypid = os.getpid()
    for p in psutil.process_iter(['name', 'pid', 'cmdline']):
        try:
            cmd = " ".join(p.info['cmdline'] or []).lower()
            n = (p.info['name'] or "").lower()
            if any(x in cmd or x in n for x in ["orbitswipe", "launcher.py", "main.py"]):
                if p.info['pid'] != mypid:
                    p.kill()
        except: pass
    
    # Fallback taskkill
    subprocess.run('taskkill /F /IM python.exe /FI "WINDOWTITLE eq OrbitSwipe*" > NUL 2>&1', shell=True)
    subprocess.run('taskkill /F /IM pyw.exe /FI "WINDOWTITLE eq OrbitSwipe*" > NUL 2>&1', shell=True)
    subprocess.run('taskkill /F /IM orbitswipe.exe /T > NUL 2>&1', shell=True)

def cleanup():
    # 1. Kill processes
    kill_processes()
    time.sleep(2)

    # 2. Find installation path from registry
    install_path = None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}", 0, winreg.KEY_READ)
        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
    except: pass

    # 3. Remove Registry Keys (Keep TrialStart)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}", 0, winreg.KEY_SET_VALUE)
        try: winreg.DeleteValue(key, "InstallPath")
        except: pass
        winreg.CloseKey(key)
    except: pass

    try:
        uninst_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\OrbitSwipe"
        # We delete this key as it's the Add/Remove entry
        def delete_key_recursive(key, subkey):
            try:
                k = winreg.OpenKey(key, subkey, 0, winreg.KEY_ALL_ACCESS)
                while True:
                    try:
                        n = winreg.EnumKey(k, 0)
                        delete_key_recursive(k, n)
                    except: break
                winreg.CloseKey(k)
                winreg.DeleteKey(key, subkey)
            except: pass
        delete_key_recursive(winreg.HKEY_CURRENT_USER, uninst_key)
    except: pass

    # 4. Clean AppData (Preserving security data)
    if os.path.exists(APPDATA_DIR):
        for f in os.listdir(APPDATA_DIR):
            if f.lower() in ["trial.dat", "license.dat"]: continue
            path = os.path.join(APPDATA_DIR, f)
            try:
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): shutil.rmtree(path)
            except: pass

    # 5. Self-Destruct installation folder
    if install_path and os.path.exists(install_path):
        # Create temporary batch to finish job
        bat_path = os.path.join(os.environ["TEMP"], "os_cleanup.bat")
        with open(bat_path, "w") as f:
            f.write(f"@echo off\ntimeout /t 2 /nobreak > NUL\n")
            # Try to delete the code folder recursively
            f.write(f'for /d %%p in ("{install_path}\\*") do rd /s /q "%%p"\n')
            f.write(f'for %%f in ("{install_path}\\*") do (\n')
            f.write(f'  if /i not "%%~nxf"=="trial.dat" if /i not "%%~nxf"=="license.dat" if /i not "%%~nxf"=="cleanup.bat" del /f /q "%%f"\n')
            f.write(f')\n')
            f.write(f'del "%~f0"\n')
        
        subprocess.Popen(f'start /min "" "{bat_path}"', shell=True)
    
    print("Uninstallation Complete!")
    time.sleep(1)

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    else:
        cleanup()
