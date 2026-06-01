import os
import sys
import shutil
import subprocess
import ctypes
import time
import threading

# --- PATH HACK FOR MODULAR VERSION ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    import psutil
    import winreg
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox
    from orbitswipe.core.constants import APP_NAME, APP_VERSION, PACKAGES, IS_FROZEN, CF, APPDATA_DIR, LOG_FILE, SYSTEM_DRIVE
    from orbitswipe.core.utils import _log, get_asset_path
except ImportError as e:
    # If dependencies are missing, try to show a simple error
    try:
        import tkinter.messagebox as mb
        root = tk.Tk(); root.withdraw()
        mb.showerror("OrbitSwipe Setup Error", f"Missing dependency: {e}\n\nPlease run 'pip install psutil PyQt6 Pillow' first.")
    except:
        print(f"Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Startup error: {e}")
    sys.exit(1)


def set_tk_icon(window):
    try:
        # 1. Try loading directly from the running EXE resource (highly reliable for frozen app)
        if getattr(sys, 'frozen', False):
            window.iconbitmap(sys.executable)
            return
    except:
        pass
    try:
        # 2. Try getting the local asset path via get_asset_path
        icon_p = get_asset_path("image", "OrbitSwipe.ico")
        if icon_p and os.path.exists(icon_p):
            window.iconbitmap(os.path.normpath(icon_p))
            return
    except:
        pass
    try:
        # 3. Try common fallback paths
        fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "image", "OrbitSwipe.ico")
        if os.path.exists(fallback):
            window.iconbitmap(os.path.normpath(fallback))
            return
    except:
        pass
    try:
        # 4. Try current working directory fallback
        cwd_fallback = os.path.join(os.getcwd(), "image", "OrbitSwipe.ico")
        if os.path.exists(cwd_fallback):
            window.iconbitmap(os.path.normpath(cwd_fallback))
    except:
        pass


def run_installer():
    try:
        with open(os.path.join(APPDATA_DIR, "debug_args.txt"), "w") as f:
            f.write(str(sys.argv))
    except: pass
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"Magnetieght.OrbitSwipe.Setup.{APP_VERSION}")
    except Exception:
        pass

    import tkinter as tk
    from tkinter import filedialog, ttk

    BG = "#0b0b18"; CARD = "#12122a"; BORDER = "#1e1b4b"
    AC = "#7c3aed"; AC2  = "#a78bfa"; TX = "#e2e8f0"; MUT = "#64748b"

    hw = ctypes.windll.kernel32.GetConsoleWindow()
    if hw: ctypes.windll.user32.ShowWindow(hw, 0)

    def get_special_folder(csidl):
        try:
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
            return buf.value
        except:
            return os.path.join(os.path.expanduser("~"), "Desktop")

    def needs_admin(path):
        if ctypes.windll.shell32.IsUserAnAdmin(): return False
        try:
            test_f = os.path.join(path, "test_write.tmp")
            if not os.path.exists(path): os.makedirs(path, exist_ok=True)
            with open(test_f, "w") as f: f.write("test")
            os.remove(test_f)
            return False
        except:
            return True

    OK = "#10b981"; ERR = "#ef4444"
    is_silent = "/S" in sys.argv or "--silent" in sys.argv or "/VERYSILENT" in sys.argv
    root = tk.Tk()
    if is_silent:
        root.withdraw()
    else:
        root.title(f"{APP_NAME} v{APP_VERSION} Setup")
        set_tk_icon(root)
        root.geometry("720x510"); root.resizable(False, False)
        root.configure(bg=BG); root.update_idletasks()
        x = (root.winfo_screenwidth()  - 720) // 2
        y = (root.winfo_screenheight() - 510) // 2
        root.geometry(f"720x510+{x}+{y}")

    hdr = tk.Canvas(root, width=720, height=175, bg=BG, highlightthickness=0)
    hdr.pack(fill="x")
    for i in range(175):
        r = int(0x0b + i/175*0x18); g = int(0x0b + i/175*0x10); b = int(0x18 + i/175*0x30)
        hdr.create_rectangle(0, i, 720, i+1, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
    hdr.create_oval(530,-80,780,170, fill="#1a1840", outline="")
    hdr.create_oval(570,-40,730,120, fill="#200c4f", outline="")
    hdr.create_oval(-90,50,160,270,  fill="#1a1840", outline="")
    hdr.create_text(88,  88, text="(",          font=("Segoe UI",82,"bold"), fill=AC2, anchor="center")
    hdr.create_text(390, 68, text="OrbitSwipe", font=("Segoe UI",34,"bold"), fill=TX,  anchor="center")
    hdr.create_text(390,108, text=f"Windows Edge Launcher  —  v{APP_VERSION}",
                    font=("Segoe UI",11), fill=AC2, anchor="center")
    hdr.create_text(390,132, text="Smart Radial Launcher • Glass UI • System Monitor",
                    font=("Segoe UI",8),  fill=MUT, anchor="center")

    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=36, pady=(10,0))

    def section(t):
        f = tk.Frame(body, bg=BG); f.pack(fill="x", pady=(10,4))
        tk.Label(f, text=t, bg=BG, fg=TX, font=("Segoe UI",10,"bold")).pack(side="left")

    def card(parent, **kw):
        return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, **kw)

    section("📁  Installation Folder")
    lc = card(body); lc.pack(fill="x", pady=(0,4))
    la = os.environ.get("LOCALAPPDATA", "C:\\Users\\Default\\AppData\\Local")
    dp = os.path.join(la, APP_NAME)

    # Detect existing installation path from registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}", 0, winreg.KEY_READ)
        reg_path, _ = winreg.QueryValueEx(key, "InstallPath")
        if reg_path and os.path.exists(reg_path):
            dp = reg_path
        winreg.CloseKey(key)
    except: pass

    try:
        if "--install-to" in sys.argv:
            idx = sys.argv.index("--install-to")
            dp = sys.argv[idx+1]
    except: pass

    lv = tk.StringVar(value=dp)
    tk.Entry(lc, textvariable=lv, bg=CARD, fg=TX, insertbackground=TX,
             relief="flat", font=("Segoe UI",10), bd=10).pack(side="left",fill="both",expand=True)
    def browse():
        d = filedialog.askdirectory()
        if d: lv.set(os.path.normpath(os.path.join(d, APP_NAME)))
    tk.Button(lc, text=" Browse… ", bg=AC, fg=TX, relief="flat",
              font=("Segoe UI",9,"bold"), padx=10, pady=6, cursor="hand2",
              activebackground=AC2, command=browse).pack(side="right")

    section("⚙️  Options")
    opt = tk.Frame(body, bg=BG); opt.pack(fill="x", pady=(0,8))
    dv=tk.BooleanVar(value=True); lav=tk.BooleanVar(value=True)
    for col,(lbl,var) in enumerate([("🖥️  Desktop Shortcut",dv),("▶️  Launch After Install",lav)]):
        f2=card(opt); f2.grid(row=0,column=col+1,padx=(0,8),sticky="nsew")
        opt.columnconfigure(col+1,weight=1)
        tk.Checkbutton(f2,text=lbl,variable=var,bg=CARD,fg=TX,selectcolor=AC,
                       activebackground=CARD,font=("Segoe UI",9),bd=0,
                       padx=10,pady=9,cursor="hand2").pack(anchor="w")

    pl = tk.Label(body,text="Ready to install.",bg=BG,fg=MUT,font=("Segoe UI",9),anchor="w")
    pl.pack(fill="x", pady=(4,3))
    style = ttk.Style(); style.theme_use("clam")
    style.configure("O.Horizontal.TProgressbar",troughcolor=CARD,background=AC,
                    darkcolor=AC,lightcolor=AC2,bordercolor=BORDER,thickness=9)
    pbar = ttk.Progressbar(body,style="O.Horizontal.TProgressbar",
                           orient="horizontal",mode="determinate")
    pbar.pack(fill="x", pady=(0,10))
    btn_f = tk.Frame(body, bg=BG); btn_f.pack(fill="x")
    ib = tk.Button(btn_f, text="✨   Install OrbitSwipe", bg=AC, fg=TX, relief="flat",
                   font=("Segoe UI",13,"bold"), pady=13, cursor="hand2", activebackground=AC2)
    ib.pack(side="left", fill="x", expand=True, padx=(0,5))

    def check_un():
        if os.path.exists(dp):
            un = tk.Button(btn_f, text="🗑️", bg="#1e293b", fg=TX, relief="flat",
                           font=("Segoe UI",13), pady=13, padx=20, cursor="hand2",
                           activebackground="#334155", activeforeground=TX,
                           command=lambda: run_uninstaller(root))
            un.pack(side="right")
    check_un()

    sl2 = tk.Label(root, text="by Magnetieght EU",
                   bg="#080812", fg=MUT, font=("Segoe UI", 7, "bold"))
    sl2.pack(fill="x", side="bottom", pady=(0,5))
    sl1 = tk.Label(root, text="Developed by Cross Tech",
                   bg="#080812", fg=MUT, font=("Segoe UI", 9, "bold"))
    sl1.pack(fill="x", side="bottom", pady=(5,0))

    result = {"install_path": None, "launch": False}

    def do_install():
        path = lv.get().strip()
        if not path: return

        if needs_admin(path):
            try:
                if getattr(sys, 'frozen', False):
                    args = f'--install-to "{path}"'
                else:
                    args = f'"{os.path.abspath(__file__)}" --install-to "{path}"'
                if is_silent: args += ' /S'
                exe_to_elevate = os.path.abspath(sys.argv[0]) if getattr(sys, 'frozen', False) else sys.executable
                res = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_to_elevate, args, None, 1)
                if res > 32: os._exit(0)
            except Exception as e:
                if not is_silent:
                    import tkinter.messagebox as mb
                    mb.showerror("Elevation Failed", f"Could not gain Admin rights: {e}")
                else:
                    os._exit(1)
                return

        def task():
            try:
                def ui(msg, val=None, color=TX):
                    if is_silent: return
                    def up():
                        pl.config(text=msg, fg=color)
                        if val is not None: pbar["value"] = val
                    root.after(0, up)

                ui(f"[10%] Creating folder: {path}", 10)
                if not os.path.exists(path): os.makedirs(path, exist_ok=True)

                ui("[15%] Closing existing app...", 15)
                try:
                    import psutil, time
                    current_pid = os.getpid()
                    parent_pid = os.getppid()
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == 'OrbitSwipe.exe' and proc.info['pid'] not in (current_pid, parent_pid):
                            proc.kill()
                    time.sleep(0.5) # Ensure file handles are fully released
                except: pass

                real_is_frozen = getattr(sys, 'frozen', False) or sys.argv[0].lower().endswith('.exe')
                if real_is_frozen:
                    ui("[30%] Copying Standalone App…", 30)
                    dst_exe = os.path.join(path, "OrbitSwipe.exe")
                    src_exe = os.path.abspath(sys.argv[0])
                    if os.path.normcase(src_exe) != os.path.normcase(dst_exe):
                        shutil.copy2(src_exe, dst_exe)
                    dst = dst_exe
                else:
                    ui("[20%] Preparing project structure…", 20)
                    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                    
                    # 1. Create the package folder in destination
                    pkg_dst = os.path.join(path, "orbitswipe")
                    if os.path.exists(pkg_dst): shutil.rmtree(pkg_dst, ignore_errors=True)
                    os.makedirs(pkg_dst, exist_ok=True)

                    # 2. Copy the orbitswipe package content
                    src_pkg = os.path.join(root_dir, "orbitswipe")
                    if os.path.exists(src_pkg):
                        shutil.copytree(src_pkg, pkg_dst, dirs_exist_ok=True)
                    
                    # 3. Create the entry point launcher.py at the root of install path
                    dst = os.path.join(path, "launcher.py")
                    with open(dst, "w", encoding="utf-8") as f:
                        f.write("import os\nimport sys\n")
                        f.write(f"sys.path.insert(0, os.path.dirname(__file__))\n")
                        f.write("from orbitswipe.main import run_app\n")
                        f.write("from orbitswipe.installer.setup import run_uninstaller\n")
                        f.write("if __name__ == '__main__':\n")
                        f.write("    if '--uninstall' in sys.argv:\n")
                        f.write("        run_uninstaller()\n")
                        f.write("    else:\n")
                        f.write("        run_app()\n")

                if dv.get():
                    ui("[70%] Creating shortcut…", 70)
                    try:
                        lnk = os.path.join(get_special_folder(0), f"{APP_NAME}.lnk")
                        
                        if real_is_frozen:
                            target = os.path.join(path, "OrbitSwipe.exe")
                            args = "--run"
                            icon_loc = target
                        else:
                            target = "pyw.exe" if shutil.which("pyw.exe") else "py.exe"
                            args = f'"{dst}" --run'
                            icon_loc = icon_path

                        ps_cmd = (
                            f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{lnk}'); "
                            f"$s.TargetPath='{target}'; $s.Arguments='{args}'; "
                            f"$s.WorkingDirectory='{path}'; $s.IconLocation='{icon_loc}'; $s.Save()"
                        )
                        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    except Exception as e:
                        _log(f"Installer: Shortcut creation failed: {e}")

                ui("[95%] Finalizing startup settings.", 95)
                try:
                    import winreg
                    run_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                                             0, winreg.KEY_SET_VALUE)
                    if real_is_frozen:
                        winreg.SetValueEx(run_key, APP_NAME, 0, winreg.REG_SZ, f'"{dst}" --run --silent')
                    else:
                        target = "pyw.exe" if shutil.which("pyw.exe") else "py.exe"
                        winreg.SetValueEx(run_key, APP_NAME, 0, winreg.REG_SZ, f'"{target}" "{dst}" --run --silent')
                    winreg.CloseKey(run_key)
                except Exception as e:
                    _log(f"Installer: Startup registration failed: {e}")

                try:
                    import winreg
                    un_key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"
                    un_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, un_key_path)
                    
                    if real_is_frozen:
                        target = os.path.join(path, "OrbitSwipe.exe")
                        un_cmd = f'"{target}" --uninstall'
                        icon_path = target
                    else:
                        target = "pyw.exe" if shutil.which("pyw.exe") else "py.exe"
                        args = "--uninstall"
                        un_cmd = f'{target} "{dst}" {args}'
                        icon_path = os.path.join(path, "orbitswipe", "image", "OrbitSwipe.ico")

                    winreg.SetValueEx(un_key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                    winreg.SetValueEx(un_key, "UninstallString", 0, winreg.REG_SZ, un_cmd)
                    winreg.SetValueEx(un_key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
                    winreg.SetValueEx(un_key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                    winreg.SetValueEx(un_key, "Publisher", 0, winreg.REG_SZ, "Cross Tech")
                    winreg.CloseKey(un_key)
                except Exception as e:
                    _log(f"Installer: Uninstall registry failed: {e}")

                ui("[100%] Done!", 100)
                if not os.path.exists(APPDATA_DIR): os.makedirs(APPDATA_DIR, exist_ok=True)

                try:
                    import winreg
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}")
                    winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, path)
                    winreg.CloseKey(key)
                except: pass

                ui("✅  Installation Complete!", 100, OK)
                result["install_path"] = path
                result["launch"] = lav.get()

                def finalize_and_exit():
                    result["launch"] = lav.get()
                    root.destroy()

                def finale_ui():
                    def update_btn(*args):
                        ib.config(text="🚀  Launch OrbitSwipe" if lav.get() else "✅  Finish")
                    lav.trace_add("write", update_btn)
                    ib.config(state="normal", text="🚀  Launch OrbitSwipe" if lav.get() else "✅  Finish", bg="#059669")
                    ib.config(command=finalize_and_exit)
                root.after(0, finale_ui)

                try:
                    ulnk = os.path.join(path, f"Uninstall {APP_NAME}.lnk")
                    if real_is_frozen:
                        target = os.path.join(path, "OrbitSwipe.exe")
                        args = "--uninstall"
                    else:
                        target = shutil.which("py.exe") or sys.executable
                        args = f'"{dst}" --uninstall'

                    # Shortcut icon
                    icon_loc = f"{target},0" if real_is_frozen else "shell32.dll,31"
                    if not real_is_frozen:
                        test_icon = os.path.join(path, "orbitswipe", "image", "OrbitSwipe.ico")
                        if os.path.exists(test_icon): icon_loc = test_icon

                    ps_un = (
                        f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{ulnk}'); "
                        f"$s.TargetPath='{target}'; $s.Arguments='{args}'; "
                        f"$s.WorkingDirectory='{path}'; $s.Description='Uninstall OrbitSwipe'; "
                        f"$s.IconLocation='shell32.dll,31'; $s.Save()"
                    )
                    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_un],
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    
                    # Desktop Shortcut is already handled earlier if dv.get() is True
                except Exception as e:
                    _log(f"Un-sc err: {e}")

                # The actual launch will be handled by main.py based on result["launch"]
                # so we don't need to call Popen here.
                pass
                
                if is_silent:
                    os._exit(0)

            except Exception as e:
                try:
                    with open(os.path.join(APPDATA_DIR, "debug_exception.txt"), "w") as f:
                        import traceback
                        f.write(traceback.format_exc())
                except: pass
                _log(f"Installer Error: {e}")
                ui(f"❌ Error: {str(e)[:50]}", 0, ERR)
                with open(os.path.join(path, "installer_error.txt"), "w") as f:
                    import traceback
                    f.write(traceback.format_exc())
                if is_silent:
                    os._exit(1)
                root.after(0, lambda: ib.config(state="normal", text="✨   Retry Install", bg=AC))
                # Removed error dialog box as per request

        if is_silent:
            task()
        else:
            ib.config(state="disabled", text="⌛  Installing…")
            import threading
            threading.Thread(target=task, daemon=True).start()

    ib.config(command=do_install)

    if is_silent:
        try:
            os.makedirs(APPDATA_DIR, exist_ok=True)
            with open(os.path.join(APPDATA_DIR, "debug_silent.txt"), "w") as f:
                f.write(f"Silent mode activated\nsys.executable: {sys.executable}\nsys.argv: {sys.argv}\nsys.frozen: {getattr(sys, 'frozen', False)}")
            do_install()
        except Exception as e:
            try:
                os.makedirs(dp, exist_ok=True)
                with open(os.path.join(dp, "installer_crash.txt"), "w") as f:
                    import traceback
                    f.write(traceback.format_exc())
            except: pass
            os._exit(1)
        os._exit(0)

    if "--install-to" in sys.argv and ctypes.windll.shell32.IsUserAnAdmin():
        root.after(500, do_install)

    root.mainloop()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION  (requires PyQt6 + pywin32 + Pillow + psutil)
# ═══════════════════════════════════════════════════════════════════════════════



def run_uninstaller(tk_root=None):
    import psutil, shutil, time, ctypes, subprocess, os, sys
    from tkinter import messagebox
    import tkinter as tk

    # Ensure we have a Tk root for message boxes
    if not tk_root:
        tk_root = tk.Tk()
        tk_root.withdraw()
        set_tk_icon(tk_root)

    is_silent = "/S" in sys.argv or "--silent" in sys.argv or "/VERYSILENT" in sys.argv
    if not is_silent:
        msg = "This will completely remove OrbitSwipe, your settings, and all shortcuts.\n\n(Note: You can take a backup of your settings from the 'Settings' menu before uninstalling.)\n\nContinue?"
        if not messagebox.askyesno("OrbitSwipe Uninstall", msg):
            if not tk_root._windowingsystem == 'win32': # If we created it, destroy it
                 tk_root.destroy()
            return

    try:
        # 1. Close running instances (Aggressive Check)
        mypid = os.getpid()
        for p in psutil.process_iter(['name', 'pid', 'cmdline']):
            try:
                cmd = " ".join(p.info['cmdline'] or []).lower()
                n = (p.info['name'] or "").lower()
                # Check for launcher, main, or orbitswipe in name or cmdline
                if any(x in cmd or x in n for x in ["orbitswipe", "launcher.py", "main.py"]):
                    if p.info['pid'] != mypid:
                        _log(f"Uninstall: Killing process {p.info['pid']} ({n})")
                        p.kill()
                        p.wait(timeout=2)
            except: pass
        
        # Fallback: Taskkill by window title and image name
        try:
            subprocess.run('taskkill /F /IM "pyw.exe" /FI "WINDOWTITLE eq OrbitSwipe*"', 
                           shell=True, capture_output=True, creationflags=0x08000000)
            subprocess.run('taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq OrbitSwipe*"', 
                           shell=True, capture_output=True, creationflags=0x08000000)
        except: pass

        # 2. Find installation folder
        app_dir = None
        # Priority 1: Current script location (if we are launcher.py)
        potential = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.exists(os.path.join(potential, "orbitswipe")):
            app_dir = potential
        
        # Priority 2: Registry
        if not app_dir:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}", 0, winreg.KEY_READ)
                app_dir, _ = winreg.QueryValueEx(key, "InstallPath")
                winreg.CloseKey(key)
            except: pass

        # Priority 3: Default LOCALAPPDATA
        if not app_dir or not os.path.exists(app_dir):
            app_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), APP_NAME)

        _log(f"Uninstall: Identified app_dir as {app_dir}")

        # 3. Remove Shortcuts (Desktop and Start Menu)
        def remove_lnk(path, name):
            lp = os.path.join(path, name)
            if os.path.exists(lp):
                try: os.remove(lp)
                except: pass

        try:
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            # Desktop
            ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf) 
            desk = buf.value
            # Programs (Start Menu)
            ctypes.windll.shell32.SHGetFolderPathW(None, 2, None, 0, buf)
            prog = buf.value
            
            for base_path in [desk, prog]:
                for sn in [f"{APP_NAME}.lnk", f"Uninstall {APP_NAME}.lnk"]:
                    remove_lnk(base_path, sn)
        except: pass

        # 4. Remove Registry (Run and Uninstall)
        try:
            import winreg
            # Remove Startup
            try:
                rk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                try: winreg.DeleteValue(rk, APP_NAME)
                except: pass
                winreg.CloseKey(rk)
            except: pass
            
            # Remove Uninstall info
            try:
                uk_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
                uk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, uk_path, 0, winreg.KEY_ALL_ACCESS)
                try: winreg.DeleteKey(uk, APP_NAME)
                except: pass
                winreg.CloseKey(uk)
            except: pass

            # Remove App Registry (Keep TrialStart)
            try:
                rk = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}", 0, winreg.KEY_SET_VALUE)
                try: winreg.DeleteValue(rk, "InstallPath")
                except: pass
                winreg.CloseKey(rk)
            except: pass
        except: pass

        # 5. Clean AppData and Installation Folder
        _log(f"Uninstall: Cleaning up {app_dir} and {APPDATA_DIR}")
        
        # 6. Self-Destruct (Robust Detached Batch Method)
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))
        bat_path = os.path.join(temp_dir, f"os_uninstall_{int(time.time())}.bat")
        
        if not is_silent:
            messagebox.showinfo("Success", "OrbitSwipe has been removed from your system.\n\nFinal cleanup will complete in a moment.")
        
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'setlocal enabledelayedexpansion\n')
            f.write(f'title OrbitSwipe Cleanup\n')
            f.write(f'echo Finishing uninstallation... Please wait.\n')
            f.write(f'timeout /t 2 /nobreak > NUL\n')
            
            f.write(f'taskkill /F /PID {mypid} > NUL 2>&1\n')
            f.write(f'taskkill /F /IM OrbitSwipe.exe > NUL 2>&1\n')
            
            # Helper logic to delete files except trial/license
            for p in [app_dir, APPDATA_DIR]:
                if not p: continue
                np = os.path.normpath(p)
                f.write(f'if exist "{np}" (\n')
                f.write(f'  for /d %%p in ("{np}\\*") do rd /s /q "%%p" > NUL 2>&1\n')
                f.write(f'  for %%f in ("{np}\\*") do (\n')
                f.write(f'    set "SKIP=0"\n')
                f.write(f'    if /i "%%~nxf"=="trial.dat" set "SKIP=1"\n')
                f.write(f'    if /i "%%~nxf"=="license.dat" set "SKIP=1"\n')
                f.write(f'    if /i "%%~xf"==".json" (\n')
                f.write(f'        if /i not "%%~nxf"=="config.json" set "SKIP=1"\n')
                f.write(f'    )\n')
                f.write(f'    if "!SKIP!"=="0" del /f /q "%%f" > NUL 2>&1\n')
                f.write(f'  )\n')
                f.write(f'  rd "{np}" > NUL 2>&1\n')
                f.write(f')\n')
            
            # Final self-delete of the batch file
            f.write(f'del "%~f0" & exit\n')
        
        # Run the batch file detached
        if os.name == 'nt':
            subprocess.Popen(f'cmd /c start /min "" "{bat_path}"', shell=True, creationflags=0x08000000)
        
        if tk_root: 
            try: tk_root.destroy()
            except: pass
        sys.exit(0)
    except Exception as e:
        _log(f"Uninstall failed: {e}")
        if not is_silent:
            messagebox.showerror("Error", f"Uninstall failed: {e}")
        if tk_root: 
            try: tk_root.destroy()
            except: pass


if __name__ == '__main__': run_installer()
