<p align="center">
  <img src="logo.png" width="120" alt="SFPoint Logo">
</p>

<h1 align="center">SFPoint (Windows Edition)</h1>

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

## What is SFPoint?

SFPoint is a **screen annotation overlay** for Windows. Toggle a hotkey, draw on your screen, keep teaching. Arrows, rectangles, circles, freehand, text, laser pointer — all on a transparent overlay that auto-fades after 3 seconds.

Built as a replacement for premium tools ($6.99+). SFPoint is free, open-source, and fully customizable.

### Features

- **Native Windows app** — lives in the system tray, no terminal needed, starts with your PC
- **7 annotation tools** — arrow, rectangle, circle, freehand, text, laser pointer, highlighter
- **Toggle-based shortcuts** — Alt+key to activate, same key or Esc to deactivate
- **Auto-fade** — annotations disappear after 3 seconds (configurable)
- **Laser pointer** — ambar Google Slides-style, click-through (doesn't block mouse), morado ripple on click
- **No focus stealing** — overlay floats above everything without interrupting your work
- **Click-through** — laser always passes clicks through; other tools only capture when active
- **Floating toolbar** — draggable pill showing current tool and color
- **Rebindable shortcuts** — settings panel (Alt+S) to customize keybindings
- **Brand colors** — morado (#8B5CF6) + ambar (#F59E0B) from SaaS Factory

---

## Quick Start

### Prerequisites

- Windows 10+
- Python 3.12+

### Install (Dev Mode)

```powershell
# Clone
git clone https://github.com/Johann-vn/sfpoint.win.git
cd sfpoint.win

# Python environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py
```

---

## Usage

| Action | Shortcut | Reason |
|--------|----------|--------|
| **Arrow** | `Alt+A` | En Office, Alt + A suele abrir el menú "Archivo", pero si tu app tiene prioridad de capa (overlay), suele funcionar bien. |
| **Rectangle** | `Alt+R` | Evitas conflictos con comandos de edición. |
| **Circle** | `Alt+C` | Evitas el conflicto con Copiar (Ctrl+C). |
| **Freehand** | `Alt+F` | Alternativa segura al "Buscar" (Ctrl+F). |
| **Text** | `Alt+T` | (type, Enter to place) Evitas conflictos de tabulación o tareas. |
| **Laser pointer** | `Alt+P` | Vital: Ctrl + P detendría tu presentación para intentar imprimir. |
| **Hide toolbar** | `Alt+H` | Limpio de comandos de sistema comunes. |
| **Settings** | `Alt+S` | Seguro en la mayoría de contextos de dibujo. |
| **Undo** | `Ctrl+Z` | Estándar universal en Windows. |
| **Clear all** | `Ctrl+Shift+Z` | Estándar para "Rehacer", pero fácil de recordar para limpiar. |
| **Deactivate** | `Esc` | Universal para salir de cualquier modo. |

All tool shortcuts are **toggle-based**: press once to activate, press again (or Esc) to deactivate.

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
- **Qt QueuedConnection** for thread-safe signals between pynput and UI
- **QPainter** for all rendering (shapes, laser trail with radial gradients, text)
- **Toggle-based hotkeys** instead of hold-based for better ergonomics

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
FADE_DURATION = 0.5      # seconds for fade animation

# Laser pointer (subtle, elegant)
LASER_DOT_RADIUS = 5.0
LASER_GLOW_RADIUS = 14.0
LASER_TRAIL_LENGTH = 18  # clean, short trail

# Toolbar
TOOLBAR_HEIGHT = 34
TOOLBAR_WIDTH = 180
```

Custom shortcuts are saved to `settings.json` via the settings panel (Alt+S).

---

## Cost Comparison

| | Premium Tools | SFPoint |
|---|---|---|
| Cost | $6.99+ one-time | Free |
| Customizable | Limited | Fully |
| Open source | No | Yes |
| Laser pointer | Red | Ambar (Google Slides-style) |
| Auto-fade | Yes | Yes (configurable) |
| Rebindable shortcuts | No | Yes |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Python version error | Requires 3.12+ (`list[]` generics, `\|` union syntax) |

---

## License

MIT License. Do whatever you want with it.

---

<p align="center">
  Built with Claude Opus 4.6 in a single session.<br>
  <sub>From <a href="https://github.com/Johann-vn">Johann-vn</a> — <strong>SF</strong>Point (Windows Fork)</sub>
</p>
