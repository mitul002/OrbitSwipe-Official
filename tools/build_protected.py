import os
import subprocess
import sys
import shutil

def run_command(command, description):
    print(f"--- {description} ---")
    print(f"Running: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
        print("Success!\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        sys.exit(1)

def main():
    python_exe = f'"{sys.executable}"'
    # 1. Ensure dependencies are installed
    run_command(f"{python_exe} -m pip install pyarmor pyinstaller", "Installing PyArmor and PyInstaller")

    # 2. Cleanup old builds
    for folder in ['dist', 'build', 'obf']:
        if os.path.exists(folder):
            print(f"Cleaning up {folder}...")
            shutil.rmtree(folder)

    # 3. Build with PyArmor 8+ 
    # We use --pack to integrate with PyInstaller
    # We include our icons and data folders
    # Note: --pack onefile tells PyArmor to call PyInstaller with --onefile
    
    icon_path = os.path.join("image", "OrbitSwipe.ico")
    
    # The actual command using the existing spec file
    # This avoids quoting issues and uses your pre-defined configuration
    cmd = f'{python_exe} -m pyarmor.cli gen --pack OrbitSwipe.spec main.py'
    
    run_command(cmd, "Building Protected Executable with PyArmor using Spec file")

    print("========================================")
    print("Build Complete!")
    
    output_exe = os.path.join("dist", "OrbitSwipe.exe")
    if os.path.exists(output_exe):
        print(f"Protected EXE located in: {os.path.abspath(output_exe)}")
    else:
        # Fallback check if it named it after the script
        output_exe_main = os.path.join("dist", "main.exe")
        if os.path.exists(output_exe_main):
            print(f"Protected EXE located in: {os.path.abspath(output_exe_main)}")
            print("Note: You may want to rename 'main.exe' to 'OrbitSwipe.exe'")
    
    print("\nIMPORTANT SECURITY NOTES:")
    print("1. This build was created using PyArmor (Trial). Check pyarmor.info for license details.")
    print("2. Your source code in 'core/', 'ui/', etc., is now obfuscated inside the EXE.")
    print("3. Always test the EXE on a clean machine to ensure all dependencies are bundled.")
    print("========================================")

if __name__ == "__main__":
    main()
