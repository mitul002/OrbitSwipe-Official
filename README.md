# OrbitSwipe Modular Refactoring

This project has been refactored from a monolithic 5,500-line script into a professional, modular Python package.

## Directory Structure
```text
orbitswipe/
│
├── __init__.py           # Package initialization
├── main.py               # Main entry point (Run this!)
│
├── core/                 # Backend & Logic
│   ├── __init__.py
│   ├── constants.py      # Global variables & App metadata
│   ├── utils.py          # File/Icon utilities & logging
│   ├── config.py         # JSON configuration management
│   ├── license.py        # License & Trial logic
│   └── engine.py         # Background threads & Core classes
│
├── ui/                   # Frontend (PyQt6)
│   ├── __init__.py
│   ├── launcher.py       # Main Radial Menu
│   ├── trigger.py        # Draggable edge trigger
│   ├── settings.py       # Settings dialog
│   ├── searchbar.py      # Global search bar
│   ├── dialogs.py        # Minor popups & Trial gate
│   └── utils.py          # UI-specific helpers (Tray Icon)
│
└── installer/            # Setup logic
    ├── __init__.py
    └── setup.py          # Tkinter installer/uninstaller
```

## How to Test
1.  **Environment:** Ensure you have the required dependencies installed:
    `pip install PyQt6 Pillow pywin32 psutil pycaw comtypes keyboard`
2.  **Execution:** From the parent directory, run the following command to start the application in run mode:
    ```bash
    python -m orbitswipe.main --run
    ```
3.  **Installer Test:** To see the installer/setup GUI:
    ```bash
    python -m orbitswipe.main
    ```

## Notes
- All variables and original logic have been preserved and mapped to their respective modules.
- The original file `orbitswipe_v1_5_1_patched.py` remains untouched and can be used as a fallback.
