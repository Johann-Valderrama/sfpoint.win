<p align="center">
  <img src="logo.png" width="120" alt="VPoint Logo">
</p>

<h1 align="center">VPoint — Windows Edition</h1>

<p align="center">
  <strong>Open-source screen annotation tool for Windows. Presentify alternative at $0 cost.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%2B-blue?style=flat-square" alt="Windows">
  <img src="https://img.shields.io/badge/Python-3.12%2B-green?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/UI-PyQt6-purple?style=flat-square" alt="PyQt6">
  <img src="https://img.shields.io/badge/Cost-%240-brightgreen?style=flat-square" alt="Cost">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</p>

---

## What is VPoint?

VPoint is a **screen annotation overlay** for Windows. Toggle a hotkey, draw on your screen, keep teaching. Arrows, rectangles, circles, freehand, text, laser pointer, highlighter — all on a transparent overlay that auto-fades after 3 seconds.

Built as a replacement for premium tools ($6.99+). VPoint is free, open-source, and fully customizable.

> This is the **Windows port** of [SFPoint](https://github.com/daniel-carreon/sfpoint). Original macOS version by [@daniel-carreon](https://github.com/daniel-carreon).

### Features

- **System tray app** — lives in the Windows taskbar tray, no terminal needed
- **7 annotation tools** — arrow, rectangle, circle, freehand, text, laser pointer, highlighter
- **Toggle-based shortcuts** — Alt+key to activate, same key or Esc to deactivate
- **Auto-fade** — annotations disappear after 3 seconds (configurable)
- **Laser pointer** — ambar Google Slides-style, click-through (doesn't block mouse), morado ripple on click
- **No focus stealing** — overlay floats above everything without interrupting your work
- **Click-through** — laser always passes clicks through; other tools only capture when active
- **Floating toolbar** — draggable pill showing current tool and color
- **Right-click context menu** — change tool, color, stroke width, undo, or quit from anywhere on screen
- **Rebindable shortcuts** — settings panel (Alt+S) to customize keybindings
- **Multi-monitor support** — separate overlay per physical screen
- **Brand colors** — morado (#8B5CF6) + ambar (#F59E0B) from VelOS

---

## Quick Start

### Prerequisites

- Windows 10+
- Python 3.12+

### Install (Dev Mode)

```powershell
# Clone
git clone https://github.com/Johann-valderrama/sfpoint.win.git
cd sfpoint.win

# Python environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py
```

Or use the batch launcher:

```powershell
run_sfpoint.bat
```

---

## Shortcuts

All tool shortcuts are **toggle-based**: press once to activate, press again (or Esc) to deactivate.

| Action | Shortcut |
|--------|----------|
| Arrow | `Alt+A` |
| Rectangle | `Alt+R` |
| Circle | `Alt+C` |
| Freehand | `Alt+F` |
| Text | `Alt+T` (type, then Enter to place) |
| Laser pointer | `Alt+P` |
| Hide / show toolbar | `Alt+H` |
| Settings | `Alt+S` |
| Undo | `Alt+Z` |
| Clear all | `Alt+Shift+Z` |
| Deactivate | `Esc` |
| Context menu | Right-click anywhere |

> **Why Alt+key?** Avoids conflicts with standard Windows shortcuts (Ctrl+C = copy, Ctrl+P = print, Ctrl+Z = undo in other apps, etc.).

---

## Architecture

```
Alt+Key (pynput) --> Toggle Tool On/Off --> Canvas Overlay (PyQt6)
                                                    |
                                              QPainter Rendering
                                                    |
                                        Auto-Fade (3s delay + 0.5s fade)
                                                    |
                                          Floating Toolbar (pill UI)
```

Key technical decisions:
- **PyQt6** for native windows that float without stealing focus
- **Qt QueuedConnection** for thread-safe signals between pynput and Qt main thread
- **QPainter** for all rendering (shapes, laser trail with radial gradients, text)
- **Toggle-based hotkeys** instead of hold-based for better ergonomics
- **WindowTransparentForInput** flag for native Windows click-through on laser mode

---

## Customization

All configuration lives in `config.py`:

```python
# Shortcuts (toggle-based Alt+key)
TOOL_SHORTCUTS = {
    "a": TOOL_ARROW, "r": TOOL_RECT, "c": TOOL_CIRCLE,
    "f": TOOL_FREEHAND, "t": TOOL_TEXT, "p": TOOL_LASER,
}

# Fade timing
FADE_DELAY = 3.0        # seconds before fade starts
FADE_DURATION = 0.5     # seconds for fade animation

# Laser pointer (neon bloom — Google Slides-inspired)
LASER_DOT_RADIUS = 7.5
LASER_GLOW_RADIUS = 21.0
LASER_TRAIL_LENGTH = 18  # clean, short trail

# Click ripple (morado expanding ring)
RIPPLE_MAX_RADIUS = 20.0
RIPPLE_DURATION = 0.55  # seconds

# Toolbar
TOOLBAR_HEIGHT = 34
TOOLBAR_WIDTH = 180
```

Custom shortcuts are saved to `settings.json` via the settings panel (Alt+S).

---

## Brand Colors

| Color | Hex | Use |
|-------|-----|-----|
| Morado | `#8B5CF6` | Default annotations, click ripple |
| Ambar | `#F59E0B` | Laser pointer dot + trail |
| Red | `#EF4444` | Palette option |
| Green | `#22C55E` | Palette option |
| White | `#FFFFFF` | Palette option |

Switch colors via the right-click context menu or the toolbar color dot.

---

## Cost Comparison

| | Premium Tools | VPoint |
|---|---|---|
| Cost | $6.99+ | Free |
| Customizable | Limited | Fully |
| Open source | No | Yes |
| Laser pointer | Red | Ambar (Google Slides-style) |
| Auto-fade | Yes | Yes (configurable) |
| Rebindable shortcuts | No | Yes |
| Multi-monitor | Varies | Yes |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Tool doesn't activate | Check no other app is capturing the Alt+key shortcut |
| Python version error | Requires 3.12+ — install from python.org |
| Laser blocks clicks | Update to latest version — laser uses click-through mode |
| No ripple on click | pynput mouse listener may need to be restarted |
| Overlay not visible | Check multi-monitor setup — overlay covers all screens |

---

## What's Not Yet Ported

| Feature | Status |
|---------|--------|
| `.exe` installer / PyInstaller build | TODO |
| Launch at login (Windows registry) | TODO |

---

## License

MIT License. Do whatever you want with it.

---

<p align="center">
  Windows port built with Claude Sonnet 4.6.<br>
  <sub>
    Fork by <a href="https://github.com/Johann-valderrama">Johann-valderrama</a> —
    original by <a href="https://github.com/daniel-carreon">daniel-carreon</a>
  </sub>
</p>
