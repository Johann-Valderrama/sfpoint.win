"""Mini floating toolbar — pill-style indicator for current tool and color.

Reuses VPoint's floating window pattern.
Alt+H toggles visibility.
"""

import sys
from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QPixmap, QFont, QAction, QIcon

if sys.platform == "darwin":
    try:
        from ctypes import c_void_p
        import AppKit
        import objc
    except ImportError:
        pass

from config import (
    TOOLBAR_HEIGHT, TOOLBAR_WIDTH, TOOLBAR_OPACITY, TOOLBAR_CORNER_RADIUS,
    TOOLBAR_MARGIN_BOTTOM, TOOLBAR_ICON_SIZE, LOGO_PATH, LOGO_SIZE,
    TOOLBAR_COLLAPSED_WIDTH, TOOLBAR_COLLAPSED_HEIGHT, TOOLBAR_COLLAPSED_COLOR, TOOLBAR_COLLAPSED_OFFSET_X,
    TOOLBAR_COLLAPSED_MARGIN_BOTTOM,
    COLOR_PALETTE, DEFAULT_COLOR_INDEX, DEFAULT_TOOL, DEFAULT_STROKE,
    TOOL_ARROW, TOOL_RECT, TOOL_CIRCLE, TOOL_FREEHAND,
    TOOL_TEXT, TOOL_LASER, TOOL_HIGHLIGHTER,
    LASER_COLOR,
    STROKE_THIN, STROKE_MEDIUM, STROKE_THICK, STROKE_EXTRA, STROKE_HEAVY,
)


_STATE_EXPANDED  = "expanded"
_STATE_COLLAPSED = "collapsed"

TOOL_LABELS = {
    TOOL_ARROW: "Arrow",
    TOOL_RECT: "Rect",
    TOOL_CIRCLE: "Circle",
    TOOL_FREEHAND: "Draw",
    TOOL_TEXT: "Text",
    TOOL_LASER: "Pointer",
    TOOL_HIGHLIGHTER: "Highlight",
}

TOOL_SHORTCUT_LABELS = {
    TOOL_ARROW: "Alt+A",
    TOOL_RECT: "Alt+R",
    TOOL_CIRCLE: "Alt+C",
    TOOL_FREEHAND: "Alt+F",
    TOOL_TEXT: "Alt+T",
    TOOL_LASER: "Alt+P",
    TOOL_HIGHLIGHTER: "",
}


_MENU_STYLE = """
QMenu {
    background-color: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 4px 0;
    color: #e0e0e0;
    font-size: 12px;
}
QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    margin: 1px 4px;
}
QMenu::item:selected {
    background-color: #8B5CF6;
    color: white;
}
QMenu::separator {
    height: 1px;
    background: #333;
    margin: 4px 8px;
}
"""

COLOR_NAMES = ["Morado", "Ambar", "Rojo", "Verde", "Blanco"]

STROKE_LABELS = {STROKE_THIN: "Thin", STROKE_MEDIUM: "Medium", STROKE_THICK: "Thick", STROKE_EXTRA: "Extra", STROKE_HEAVY: "Heavy"}

# Tool display order for context menu
TOOL_ORDER = [TOOL_ARROW, TOOL_RECT, TOOL_CIRCLE, TOOL_FREEHAND, TOOL_TEXT, TOOL_HIGHLIGHTER, TOOL_LASER]


class ToolbarWidget(QWidget):
    """Pill-style floating toolbar showing current tool and color."""

    # Context menu signals
    tool_selected = pyqtSignal(str)
    color_selected = pyqtSignal(int)
    stroke_selected = pyqtSignal(float)
    undo_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._tool = DEFAULT_TOOL
        self._color_index = DEFAULT_COLOR_INDEX
        self._stroke_width = DEFAULT_STROKE
        self._active = False
        self._drag_pos = None

        # Collapsed state + animación
        self._display_state = _STATE_EXPANDED
        self._current_w = float(TOOLBAR_WIDTH)
        self._current_h = float(TOOLBAR_HEIGHT)
        self._target_w  = float(TOOLBAR_WIDTH)
        self._target_h  = float(TOOLBAR_HEIGHT)
        self._bottom_anchor_y: int = 0

        self._anim_timer = QTimer()
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._animate_size)

        self._bg_color = QColor(15, 15, 15, int(255 * TOOLBAR_OPACITY))

        self._logo = QPixmap(LOGO_PATH)
        if not self._logo.isNull():
            self._logo = self._logo.scaled(
                LOGO_SIZE, LOGO_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(TOOLBAR_WIDTH)
        self.setFixedHeight(TOOLBAR_HEIGHT)

        self._position_on_screen()

    def _position_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if self._display_state == _STATE_COLLAPSED:
                self._bottom_anchor_y = geo.bottom() - TOOLBAR_COLLAPSED_MARGIN_BOTTOM
                x = geo.center().x() + TOOLBAR_COLLAPSED_OFFSET_X - TOOLBAR_COLLAPSED_WIDTH // 2
            else:
                self._bottom_anchor_y = geo.bottom() - TOOLBAR_MARGIN_BOTTOM
                x = geo.center().x() - TOOLBAR_WIDTH // 2
            self.move(x, self._bottom_anchor_y - int(self._current_h))

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "darwin":
            try:
                self._setup_native_macos()
            except Exception as e:
                print(f"Warning: toolbar native setup failed: {e}")

    def _setup_native_macos(self):
        ns_view = objc.objc_object(c_void_p=c_void_p(self.winId().__int__()))
        ns_window = ns_view.window()
        ns_window.setLevel_(AppKit.NSFloatingWindowLevel)
        ns_window.setStyleMask_(
            ns_window.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel
        )
        ns_window.setHidesOnDeactivate_(False)
        ns_window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorStationary
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

    # --- Public API ---

    def update_tool(self, tool: str):
        self._tool = tool
        self.update()

    def update_color(self, index: int):
        self._color_index = index
        self.update()

    def update_stroke(self, width: float):
        self._stroke_width = width
        self.update()

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def toggle_visibility(self):
        """Alt+H toggle."""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def toggle_collapse(self):
        """Ctrl+H: colapsa a círculo o expande de vuelta."""
        if self._display_state == _STATE_EXPANDED:
            self._display_state = _STATE_COLLAPSED
            self._target_w = float(TOOLBAR_COLLAPSED_WIDTH)
            self._target_h = float(TOOLBAR_COLLAPSED_HEIGHT)
            # Reajusta posición a centro bottom (fijo) al colapsar
            self._position_on_screen()
        else:
            self._display_state = _STATE_EXPANDED
            self._target_w = float(TOOLBAR_WIDTH)
            self._target_h = float(TOOLBAR_HEIGHT)
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def _animate_size(self):
        for attr, target_attr in [('_current_w', '_target_w'), ('_current_h', '_target_h')]:
            cur = getattr(self, attr)
            tgt = getattr(self, target_attr)
            diff = tgt - cur
            setattr(self, attr, tgt if abs(diff) < 0.5 else cur + diff * 0.22)

        settled = (abs(self._target_w - self._current_w) < 0.5 and
                   abs(self._target_h - self._current_h) < 0.5)
        if settled:
            self._anim_timer.stop()

        new_w = max(1, int(self._current_w))
        new_h = max(1, int(self._current_h))
        self.setFixedWidth(new_w)
        self.setFixedHeight(new_h)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if self._display_state == _STATE_COLLAPSED:
                x = geo.center().x() + TOOLBAR_COLLAPSED_OFFSET_X - new_w // 2
            else:
                x = geo.center().x() - new_w // 2
            self.move(x, self._bottom_anchor_y - new_h)
        self.update()

    # --- Paint ---

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        # --- Collapsed: pastilla gris (estilo SFlow idle) ---
        if self._display_state == _STATE_COLLAPSED:
            radius = h / 2.0
            path = QPainterPath()
            path.addRoundedRect(0.0, 0.0, float(w), float(h), radius, radius)
            painter.fillPath(path, TOOLBAR_COLLAPSED_COLOR)
            painter.setPen(QPen(QColor(255, 255, 255, 40), 0.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.25, 0.25, w - 0.5, h - 0.5), radius, radius)
            painter.end()
            return

        # Background
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(w), float(h),
                            TOOLBAR_CORNER_RADIUS, TOOLBAR_CORNER_RADIUS)
        painter.fillPath(path, self._bg_color)

        # Subtle border
        if self._active:
            border_color = QColor(COLOR_PALETTE[self._color_index])
            border_color.setAlpha(120)
        else:
            border_color = QColor(255, 255, 255, 20)
        painter.setPen(QPen(border_color, 0.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, w, h, TOOLBAR_CORNER_RADIUS, TOOLBAR_CORNER_RADIUS)

        x_cursor = 8.0

        # Logo
        if not self._logo.isNull():
            ly = (h - LOGO_SIZE) // 2
            painter.drawPixmap(int(x_cursor), ly, self._logo)
            x_cursor += LOGO_SIZE + 8

        # Separator
        painter.setPen(QPen(QColor(255, 255, 255, 30), 0.5))
        painter.drawLine(QPointF(x_cursor, 6), QPointF(x_cursor, h - 6))
        x_cursor += 8

        # Tool icon
        icon_cx = x_cursor + TOOLBAR_ICON_SIZE / 2
        icon_cy = h / 2.0
        color = QColor(COLOR_PALETTE[self._color_index])
        if not self._active:
            color.setAlpha(100)
        self._draw_tool_icon(painter, self._tool, icon_cx, icon_cy, color)
        x_cursor += TOOLBAR_ICON_SIZE + 6

        # Tool label + shortcut
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        label_color = QColor(255, 255, 255, 200 if self._active else 100)
        painter.setPen(label_color)
        label = TOOL_LABELS.get(self._tool, self._tool)
        shortcut = TOOL_SHORTCUT_LABELS.get(self._tool, "")
        display = f"{label} {shortcut}" if shortcut else label
        painter.drawText(
            QRectF(x_cursor, 0, 80, h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            display,
        )
        x_cursor += 62

        # Color dot
        painter.setPen(Qt.PenStyle.NoPen)
        dot_r = 5.0
        dot_cx = w - 16.0
        dot_cy = h / 2.0
        dot_color = QColor(COLOR_PALETTE[self._color_index])
        painter.setBrush(dot_color)
        painter.drawEllipse(QPointF(dot_cx, dot_cy), dot_r, dot_r)

        # Active glow
        if self._active:
            glow_color = QColor(dot_color)
            glow_color.setAlpha(40)
            painter.setBrush(glow_color)
            painter.drawEllipse(QPointF(dot_cx, dot_cy), dot_r + 3, dot_r + 3)

        painter.end()

    def _draw_collapsed_icon(self, painter: QPainter, cx: float, cy: float):
        """Ícono centrado en el círculo. Usa logo; si no carga, dibuja lápiz."""
        if not self._logo.isNull():
            icon_size = min(22, self.width() - 8)
            scaled = self._logo.scaled(
                icon_size, icon_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(
                int(cx - scaled.width() / 2),
                int(cy - scaled.height() / 2),
                scaled,
            )
        else:
            # Fallback: lápiz estilo Lucide con QPainter
            s = min(self.width(), self.height()) * 0.28
            pen = QPen(QColor(255, 255, 255, 200), 1.5,
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                       Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(QPointF(cx - s, cy + s), QPointF(cx + s * 0.5, cy - s * 0.5))
            painter.drawLine(QPointF(cx - s, cy + s), QPointF(cx - s * 0.5, cy + s * 0.6))
            painter.drawLine(QPointF(cx - s * 0.5, cy + s * 0.6), QPointF(cx - s * 0.7, cy + s))

    def _draw_tool_icon(self, painter: QPainter, tool: str, cx: float, cy: float, color: QColor):
        """Draw a mini icon representing the tool."""
        s = TOOLBAR_ICON_SIZE / 2.0
        pen = QPen(color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if tool == TOOL_ARROW:
            painter.drawLine(QPointF(cx - s, cy + s * 0.6), QPointF(cx + s * 0.6, cy - s))
            painter.setBrush(color)
            path = QPainterPath()
            path.moveTo(cx + s * 0.6, cy - s)
            path.lineTo(cx + s * 0.1, cy - s * 0.5)
            path.lineTo(cx + s * 0.3, cy - s * 0.2)
            path.closeSubpath()
            painter.fillPath(path, color)

        elif tool == TOOL_RECT:
            painter.drawRect(QRectF(cx - s * 0.8, cy - s * 0.6, s * 1.6, s * 1.2))

        elif tool == TOOL_CIRCLE:
            painter.drawEllipse(QPointF(cx, cy), s * 0.8, s * 0.6)

        elif tool == TOOL_FREEHAND:
            path = QPainterPath()
            path.moveTo(cx - s, cy + s * 0.3)
            path.cubicTo(cx - s * 0.3, cy - s, cx + s * 0.3, cy + s, cx + s, cy - s * 0.3)
            painter.drawPath(path)

        elif tool == TOOL_TEXT:
            font = QFont()
            font.setPointSize(int(s * 2.2))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(color)
            painter.drawText(QRectF(cx - s, cy - s, s * 2, s * 2),
                             Qt.AlignmentFlag.AlignCenter, "T")

        elif tool == TOOL_LASER:
            # Dynamic color laser dot icon
            painter.setPen(Qt.PenStyle.NoPen)
            ic = QColor(color)
            ic.setAlpha(180)
            painter.setBrush(ic)
            painter.drawEllipse(QPointF(cx, cy), s * 0.5, s * 0.5)
            ic.setAlpha(60)
            painter.setBrush(ic)
            painter.drawEllipse(QPointF(cx, cy), s * 0.8, s * 0.8)

        elif tool == TOOL_HIGHLIGHTER:
            pen2 = QPen(QColor(color.red(), color.green(), color.blue(), 80), s * 0.8,
                        Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen2)
            painter.drawLine(QPointF(cx - s, cy), QPointF(cx + s, cy))

    # --- Context Menu (Right-Click) ---

    def _show_context_menu(self, global_pos):
        menu = QMenu()
        menu.setStyleSheet(_MENU_STYLE)

        # --- Tools ---
        for tool in TOOL_ORDER:
            label = TOOL_LABELS.get(tool, tool)
            shortcut = TOOL_SHORTCUT_LABELS.get(tool, "")
            text = f"  {label}  {shortcut}" if shortcut else f"  {label}"
            action = menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(self._tool == tool and self._active)
            action.triggered.connect(lambda checked, t=tool: self.tool_selected.emit(t))

        menu.addSeparator()

        # --- Colors ---
        color_menu = menu.addMenu("  Color")
        color_menu.setStyleSheet(_MENU_STYLE)
        for i, name in enumerate(COLOR_NAMES):
            action = color_menu.addAction(f"  {name}")
            action.setCheckable(True)
            action.setChecked(self._color_index == i)
            action.triggered.connect(lambda checked, idx=i: self.color_selected.emit(idx))

        # --- Stroke ---
        stroke_menu = menu.addMenu("  Stroke")
        stroke_menu.setStyleSheet(_MENU_STYLE)
        for width, label in STROKE_LABELS.items():
            action = stroke_menu.addAction(f"  {label}")
            action.setCheckable(True)
            action.setChecked(abs(self._stroke_width - width) < 0.1)
            action.triggered.connect(lambda checked, w=width: self.stroke_selected.emit(w))

        menu.addSeparator()

        # --- Actions ---
        undo_action = menu.addAction("  Undo          Alt+Z")
        undo_action.triggered.connect(self.undo_requested.emit)

        clear_action = menu.addAction("  Clear All    Alt+Shift+Z")
        clear_action.triggered.connect(self.clear_requested.emit)

        menu.addSeparator()

        settings_action = menu.addAction("  Settings      Alt+S")
        settings_action.triggered.connect(self.settings_requested.emit)

        menu.addSeparator()

        quit_action = menu.addAction("  Quit VPoint")
        quit_action.triggered.connect(self.quit_requested.emit)

        menu.exec(global_pos)

    # --- Dragging ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self._display_state == _STATE_COLLAPSED:
                self.toggle_collapse()
                event.accept()
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._bottom_anchor_y = self.y() + self.height()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
