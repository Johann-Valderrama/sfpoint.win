# CLAUDE.md — SFPoint Windows: Complete Setup & Development Guide

> This file is designed for AI agents. If you just cloned this repo, follow the **Quick Start** section to get SFPoint running end-to-end without human intervention.

## What is SFPoint?

SFPoint is a Windows screen annotation tool (Presentify replacement). Toggle-based Alt+key shortcuts activate/deactivate tools. Draw temporary arrows, rectangles, circles, freehand lines, text, laser pointer, or highlighter on a transparent fullscreen overlay. Annotations auto-fade after 3 seconds. Laser pointer is click-through (doesn't block mouse). Multi-monitor support included. SF brand colors: morado #8B5CF6, ambar #F59E0B.

> **Note**: This is the Windows port (`windows-port` branch). The original macOS version lives in the `main` branch of the upstream repo.

---

## Quick Start (Dev Mode)

```powershell
# 1. Clone
git clone https://github.com/Johann-valderrama/sfpoint.win.git
cd sfpoint.win

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

Or use the batch launcher:
```powershell
run_sfpoint.bat
```

### Requirements
- Windows 10+
- Python 3.12+
- Dependencies: `PyQt6`, `pynput`, `numpy`

---

## Usage Details

### Tool Shortcuts (Toggle-Based)

| Action | Shortcut |
|--------|----------|
| Arrow | Alt+A (toggle) |
| Rectangle | Alt+R (toggle) |
| Circle | Alt+C (toggle) |
| Freehand | Alt+F (toggle) |
| Text | Alt+T (toggle, type + Enter to place) |
| Laser pointer | Alt+P (toggle, click-through, ambar dot + morado ripple on click) |
| Hide/show toolbar | Alt+H |
| Settings panel | Alt+S |
| Undo | Alt+Z |
| Clear all | Alt+Shift+Z |
| Deactivate | Esc |

> Alt+key was chosen over Ctrl+key to avoid conflicts with standard Windows shortcuts (Ctrl+C=copy, Ctrl+P=print, etc.).

### Laser Pointer Behavior
- **Click-through**: laser does NOT block mouse clicks, right-click, drag, etc.
- **Cursor tracking**: follows cursor via QCursor.pos() polling (no mouse capture)
- **Ambar dot**: 7.5px radius dot with soft 21px glow halo
- **Trail**: thin fading line (18 points max), decays when mouse stops
- **Ripple on click**: morado (#8B5CF6) expanding ring with ease-out animation (0.55s)
- Detected via pynput mouse listener running alongside keyboard listener

---

## Project Structure

```
sfpoint.win/
├── main.py              # Entry point — tray icon, launch-at-login, signal wiring
├── config.py            # All configuration constants (UI, tools, paths, bundle detection)
├── run_sfpoint.bat      # Windows batch launcher
├── start_sfpoint.sh     # Linux/macOS shell launcher
├── sfpoint.spec         # PyInstaller spec (macOS .app bundle — not yet ported to Windows)
├── build.sh             # macOS build script (not used on Windows)
├── core/
│   ├── hotkey.py        # Global hotkeys (pynput, toggle-based Alt+key)
│   └── drawing.py       # Shape engine (Annotation dataclass + ShapeRenderer)
├── ui/
│   ├── canvas.py        # Multi-monitor transparent overlays with click-through
│   ├── toolbar.py       # Floating pill toolbar (current tool + color)
│   └── settings.py      # Settings panel (rebindable shortcuts)
├── settings.json        # User settings (auto-generated, gitignored in practice)
├── logo.png             # SFPoint logo (full size)
├── logo_small.png       # Small logo (22x22 for tray + toolbar pill)
├── SFPoint.icns         # macOS app icon (legacy)
├── requirements.txt     # PyQt6, pynput, numpy
├── PRP.md               # Project Requirements Plan (original macOS build blueprint)
├── CLAUDE.md            # This file
└── README.md            # Public-facing documentation
```

---

## Critical Implementation Details

### 1. Click-Through Toggle
The canvas overlay uses Qt window flags to toggle between:
- **Inactive**: clicks pass through to apps below (default state)
- **Active (non-laser)**: canvas captures mouse for drawing shapes
- **Active (laser)**: stays click-through, tracks cursor via polling

On macOS, this uses PyObjC `NSWindow.setIgnoresMouseEvents_()`. On Windows, Qt's `WindowTransparentForInput` flag handles click-through natively.

### 2. Qt Signal Threading
pynput keyboard and mouse listeners run on their own threads. ALL signals use explicit `Qt.ConnectionType.QueuedConnection` for thread safety. The laser ripple uses a dedicated `pyqtSignal(float, float)` to safely marshal click coordinates from pynput thread to Qt main thread.

### 3. Multi-Monitor Support
`CanvasManager` creates one `ScreenOverlay` per physical screen using `QApplication.screens()`. Overlays are automatically recreated when screens are added/removed. All annotations are stored in global screen coordinates.

### 4. Floating Window (no focus steal)
On Windows, Qt flags `FramelessWindowHint + WindowStaysOnTopHint + Tool + WindowDoesNotAcceptFocus` ensure the overlay never steals focus. On macOS, this additionally uses PyObjC `NSFloatingWindowLevel + NSWindowStyleMaskNonactivatingPanel`.

### 5. Bundle vs Dev Mode (config.py)
`config.py` detects `sys.frozen` to switch between dev and bundled app:
- **Dev mode**: assets and data live in the project root directory
- **Bundle mode**: read-only assets (logo) come from `sys._MEIPASS`, writable data (settings.json) goes to:
  - Windows: `%APPDATA%\SFPoint\`
  - macOS: `~/Library/Application Support/SFPoint/`

### 6. Desktop App Features (main.py)
- **System Tray**: QSystemTrayIcon with Settings, "Start with Windows" toggle, Quit
- **Launch at Login**: macOS uses LaunchAgent plist; Windows startup is TODO (registry-based)

### 7. Settings Persistence
Custom shortcuts saved to `settings.json` via `config.load_shortcuts()` / `config.save_shortcuts()`. Settings panel (Alt+S) allows live rebinding with automatic conflict resolution.

---

## Brand Colors

| Color | Hex | Use |
|-------|-----|-----|
| Morado | #8B5CF6 | Default annotations, click ripple |
| Ambar | #F59E0B | Laser pointer dot + trail |
| Red | #EF4444 | Palette option |
| Green | #22C55E | Palette option |
| White | #FFFFFF | Palette option |

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Tool doesn't activate | Check that no other app is capturing the Alt+key shortcut |
| Python version error | Requires 3.12+ — install from python.org |
| Laser blocks clicks | Update to latest version — laser now uses click-through mode |
| No ripple on click | pynput mouse listener may need to be restarted |
| Overlay not visible | Check multi-monitor setup — overlay should cover all screens |

---

## Not Yet Ported to Windows

The following macOS features have no Windows equivalent yet:
- **Build script**: `build.sh` generates `.app` bundles; no `.exe` builder exists yet
- **Launch at login**: macOS uses LaunchAgent; Windows registry startup is TODO
- **Hide from Dock**: macOS-specific (`NSApplicationActivationPolicyAccessory`)
