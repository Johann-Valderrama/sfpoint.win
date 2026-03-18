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
        undo_requested() — Ctrl+Z pressed
        clear_requested() — Ctrl+Shift+Z pressed
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

        char = None
        try:
            char = key.char
        except AttributeError:
            pass

        # Windows VK codes for letters A-Z are 65-90
        if not char and hasattr(key, 'vk') and key.vk is not None:
            vk = key.vk
            if 65 <= vk <= 90:
                char = chr(vk).lower()

        if not char:
            return

        char_lower = char.lower()

        # Ctrl+Z / Ctrl+Shift+Z (undo/clear) — no Alt required
        if self._ctrl_held and not self._alt_held:
            if char_lower == "z":
                if self._shift_held:
                    self.clear_requested.emit()
                else:
                    self.undo_requested.emit()
                return

        # Alt+key shortcuts (toggle-based)
        if not self._alt_held:
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
