"""SFPoint — Screen Annotation Tool.

Alt+key toggles annotation tools on/off.
Alt+A=arrow, Alt+R=rect, Alt+C=circle, Alt+F=freehand,
Alt+T=text, Alt+P=pointer, Alt+H=hide toolbar, Alt+S=settings.
Esc=deactivate, Alt+Z=undo, Alt+Shift+Z=clear all.
"""

import os
import signal
import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from config import IS_BUNDLE, LOGO_PATH
from core.hotkey import HotkeyListener
from ui.canvas import CanvasManager
from ui.toolbar import ToolbarWidget
from ui.settings import SettingsPanel


def _ensure_accessibility() -> bool:
    """Prompt macOS to grant Accessibility if not trusted. Returns True if already trusted."""
    if sys.platform == "darwin":
        try:
            from ApplicationServices import AXIsProcessTrustedWithOptions
            return AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True})
        except Exception:
            return True
    return True


# --- Launch Agent ---
_BUNDLE_ID = "so.saasfactory.sfpoint"
_LAUNCH_AGENT_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{_BUNDLE_ID}.plist")


def _is_launch_at_login() -> bool:
    if sys.platform == "darwin":
        return os.path.exists(_LAUNCH_AGENT_PATH)
    # TODO: Windows registry startup check
    return False


def _set_launch_at_login(enabled: bool):
    if sys.platform == "darwin":
        import plistlib
        if enabled:
            app_path = "/Applications/SFPoint.app" if IS_BUNDLE else ""
            if not app_path or not os.path.exists(app_path):
                return
            plist = {
                "Label": _BUNDLE_ID,
                "ProgramArguments": ["open", "-a", app_path],
                "RunAtLoad": True,
            }
            os.makedirs(os.path.dirname(_LAUNCH_AGENT_PATH), exist_ok=True)
            with open(_LAUNCH_AGENT_PATH, "wb") as f:
                plistlib.dump(plist, f)
        else:
            if os.path.exists(_LAUNCH_AGENT_PATH):
                os.remove(_LAUNCH_AGENT_PATH)
    else:
        # TODO: Windows registry startup implementation
        pass


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    canvas = CanvasManager()
    toolbar = ToolbarWidget()
    settings = SettingsPanel()
    hotkey = HotkeyListener()

    # --- System Tray (menu bar icon / tray icon) ---
    tray = QSystemTrayIcon()
    tray_icon = QIcon(QPixmap(LOGO_PATH))
    tray.setIcon(tray_icon)

    tray_menu = QMenu()
    settings_action = tray_menu.addAction("Settings")
    settings_action.triggered.connect(settings.toggle)

    tray_menu.addSeparator()

    # Adjust text based on OS
    os_name = "macOS" if sys.platform == "darwin" else "Windows"
    login_action = tray_menu.addAction(f"Start with {os_name}")
    login_action.setCheckable(True)
    login_action.setChecked(_is_launch_at_login())
    login_action.triggered.connect(lambda checked: _set_launch_at_login(checked))

    tray_menu.addSeparator()

    quit_action = tray_menu.addAction("Quit SFPoint")
    quit_action.triggered.connect(app.quit)

    tray.setContextMenu(tray_menu)
    tray.show()

    # --- Connect signals (all QueuedConnection for thread safety) ---

    hotkey.tool_toggled.connect(
        lambda tool: _on_tool_toggled(canvas, toolbar, tool),
        Qt.ConnectionType.QueuedConnection,
    )
    hotkey.deactivated.connect(
        lambda: _on_deactivated(canvas, toolbar),
        Qt.ConnectionType.QueuedConnection,
    )
    hotkey.laser_toggled.connect(
        lambda on: _on_laser_toggled(canvas, toolbar, on),
        Qt.ConnectionType.QueuedConnection,
    )
    hotkey.hide_toolbar.connect(
        toolbar.toggle_visibility,
        Qt.ConnectionType.QueuedConnection,
    )
    hotkey.open_settings.connect(
        settings.toggle,
        Qt.ConnectionType.QueuedConnection,
    )
    hotkey.undo_requested.connect(
        canvas.undo,
        Qt.ConnectionType.QueuedConnection,
    )
    hotkey.clear_requested.connect(
        canvas.clear_all,
        Qt.ConnectionType.QueuedConnection,
    )

    # Settings can update hotkey shortcuts
    settings.shortcuts_changed.connect(
        hotkey.update_shortcuts,
        Qt.ConnectionType.QueuedConnection,
    )

    # --- Context menu signals from toolbar ---
    toolbar.tool_selected.connect(
        lambda tool: _on_context_tool(canvas, toolbar, hotkey, tool),
    )
    toolbar.color_selected.connect(
        lambda idx: _on_context_color(canvas, toolbar, idx),
    )
    toolbar.stroke_selected.connect(
        lambda w: _on_context_stroke(canvas, toolbar, w),
    )
    toolbar.undo_requested.connect(canvas.undo)
    toolbar.clear_requested.connect(canvas.clear_all)
    toolbar.settings_requested.connect(settings.toggle)
    toolbar.quit_requested.connect(app.quit)

    # Right-click anywhere on canvas opens toolbar's context menu
    canvas.context_menu_requested.connect(
        lambda pos: toolbar._show_context_menu(pos),
    )

    # Show UI
    canvas.show()
    toolbar.show()

    # Request Accessibility permission (shows macOS prompt if not granted)
    _ensure_accessibility()

    hotkey.start()

    # --- Hide from Dock (menu bar only) ---
    # MUST be set AFTER all windows are shown
    if sys.platform == "darwin":
        try:
            import AppKit
            AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        except Exception:
            pass

    print("SFPoint running.")
    print("  Alt+A=arrow  Alt+R=rect  Alt+C=circle  Alt+F=freehand")
    print("  Alt+T=text   Alt+P=pointer")
    print("  Alt+H=hide toolbar  Alt+S=settings")
    print("  Alt+Z=undo  Alt+Shift+Z=clear  Esc=deactivate  Right-click=menu")

    exit_code = app.exec()
    hotkey.stop()
    sys.exit(exit_code)


def _on_tool_toggled(canvas: CanvasManager, toolbar: ToolbarWidget, tool: str):
    canvas.set_tool(tool)
    canvas.set_active(True)
    toolbar.update_tool(tool)
    toolbar.set_active(True)


def _on_deactivated(canvas: CanvasManager, toolbar: ToolbarWidget):
    canvas.set_active(False)
    toolbar.set_active(False)


def _on_laser_toggled(canvas: CanvasManager, toolbar: ToolbarWidget, on: bool):
    canvas.set_laser(on)
    if on:
        toolbar.update_tool("laser")
        toolbar.set_active(True)
    elif not canvas.is_active:
        toolbar.set_active(False)


def _on_context_tool(canvas: CanvasManager, toolbar: ToolbarWidget, hotkey, tool: str):
    from config import TOOL_LASER
    if tool == TOOL_LASER:
        # Toggle laser
        new_state = not canvas.is_laser_active
        canvas.set_laser(new_state)
        if new_state:
            toolbar.update_tool("laser")
            toolbar.set_active(True)
        elif not canvas.is_active:
            toolbar.set_active(False)
        # Sync hotkey internal state
        hotkey.set_laser_state(new_state)
    else:
        # If clicking the already-active tool, deactivate
        if canvas.is_active and canvas.current_tool == tool:
            canvas.set_active(False)
            toolbar.set_active(False)
            hotkey.set_active_tool(None)
        else:
            canvas.set_tool(tool)
            canvas.set_active(True)
            toolbar.update_tool(tool)
            toolbar.set_active(True)
            hotkey.set_active_tool(tool)


def _on_context_color(canvas: CanvasManager, toolbar: ToolbarWidget, idx: int):
    canvas.set_color_index(idx)
    toolbar.update_color(idx)


def _on_context_stroke(canvas: CanvasManager, toolbar: ToolbarWidget, width: float):
    canvas.set_stroke_width(width)
    toolbar.update_stroke(width)


if __name__ == "__main__":
    main()
