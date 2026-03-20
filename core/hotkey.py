"""Global hotkey listener for screen annotation.

Toggle-based: Alt+key toggles tools on/off.
Alt+A=arrow, Alt+R=rect, Alt+C=circle, Alt+F=freehand,
Alt+T=text, Alt+P=laser pointer, Alt+H=hide toolbar,
Alt+S=settings, Esc=deactivate.

Uses pynput with Qt signals (QueuedConnection required).
"""

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal
from config import TOOL_SHORTCUTS, TOOL_LASER, SHORTCUT_HIDE_TOOLBAR, SHORTCUT_SETTINGS


class HotkeyListener(QObject):
    """Toggle-based Alt+key hotkey listener.

    Signals:
        tool_toggled(tool: str) — Alt+tool key pressed (toggle on/off)
        deactivated() — Esc pressed or tool toggled off
        hide_toolbar() — Alt+H pressed
        open_settings() — Alt+S pressed
        undo_requested() — Alt+Z pressed
        clear_requested() — Alt+Shift+Z pressed
    """

    tool_toggled = pyqtSignal(str)
    deactivated = pyqtSignal()
    laser_toggled = pyqtSignal(bool)  # independent laser on/off
    hide_toolbar = pyqtSignal()
    open_settings = pyqtSignal()
    undo_requested = pyqtSignal()
    clear_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._alt_held = False
        self._ctrl_held = False
        self._shift_held = False
        self._active_tool: str | None = None
        self._laser_on = False
        self._shortcuts = dict(TOOL_SHORTCUTS)
        self._listener: keyboard.Listener | None = None

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def update_shortcuts(self, shortcuts: dict):
        self._shortcuts = dict(shortcuts)

    def set_laser_state(self, on: bool):
        """Sync internal laser state (called from toolbar context menu)."""
        self._laser_on = on

    def set_active_tool(self, tool: str | None):
        """Sync internal active tool state (called from toolbar context menu)."""
        self._active_tool = tool

    def _on_press(self, key):
        # Track modifiers
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt):
            self._alt_held = True
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_held = True
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_held = True

        # Esc = deactivate
        if key == keyboard.Key.esc:
            if self._active_tool:
                self._active_tool = None
                self.deactivated.emit()
            return

        # Detectar el carácter usando el código de tecla virtual (más robusto en Windows para Ctrl+Z, etc.)
        char = None
        vk = getattr(key, 'vk', None)
        if vk is not None and 65 <= vk <= 90:
            char = chr(vk).lower()
        else:
            try:
                char = key.char
            except AttributeError:
                pass

        if not char:
            return

        char_lower = char.lower()

        # Alt+key shortcuts (toggle-based)
        if not self._alt_held:
            return

        # Alt+Z / Alt+Shift+Z (undo/clear)
        if char_lower == "z":
            if self._shift_held:
                self.clear_requested.emit()
            else:
                self.undo_requested.emit()
            return

        # Alt+H = hide/show toolbar
        if char_lower == SHORTCUT_HIDE_TOOLBAR:
            self.hide_toolbar.emit()
            return

        # Alt+S = settings
        if char_lower == SHORTCUT_SETTINGS:
            self.open_settings.emit()
            return

        # Tool shortcuts
        if char_lower in self._shortcuts:
            tool = self._shortcuts[char_lower]
            if tool == TOOL_LASER:
                self._laser_on = not self._laser_on
                self.laser_toggled.emit(self._laser_on)
            elif self._active_tool == tool:
                self._active_tool = None
                self.deactivated.emit()
            else:
                self._active_tool = tool
                self.tool_toggled.emit(tool)
            return

    def _on_release(self, key):
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt):
            self._alt_held = False
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_held = False
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_held = False
