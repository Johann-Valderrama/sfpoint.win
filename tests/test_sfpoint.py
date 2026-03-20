"""tests/test_sfpoint.py — Unit tests for SFPoint core logic.

Run: pytest tests/test_sfpoint.py -v
No display required (all Qt widgets are mocked).
"""

import json
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Test 1: ShapeRenderer._setup_stroke y dispatch de render()
# ---------------------------------------------------------------------------

class TestShapeRendererSetupAndDispatch:
    """Verifica que _setup_stroke configura QPainter correctamente
    y que render() despacha al metodo correcto segun el tool."""

    def test_setup_stroke_sets_pen_and_brush(self):
        """_setup_stroke debe configurar pen con color, ancho, y brush NoBrush."""
        from PyQt6.QtGui import QColor, QPen
        from core.drawing import ShapeRenderer

        mock_painter = MagicMock()
        color = QColor(255, 0, 0)
        stroke_width = 5.0

        ShapeRenderer._setup_stroke(mock_painter, color, stroke_width)

        assert mock_painter.setPen.called
        pen_arg = mock_painter.setPen.call_args[0][0]
        assert isinstance(pen_arg, QPen)
        assert mock_painter.setBrush.called

    def test_render_dispatches_all_known_tools(self):
        """render() debe despachar correctamente todos los tools conocidos."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor

        tools_and_methods = {
            "arrow": "draw_arrow",
            "rect": "draw_rect",
            "circle": "draw_circle",
            "freehand": "draw_freehand",
            "text": "draw_text",
            "highlighter": "draw_highlighter",
        }

        for tool, method_name in tools_and_methods.items():
            mock_painter = MagicMock()
            ann = Annotation(tool=tool, points=[(0, 0), (50, 50)], color=QColor(255, 255, 255))
            with patch.object(ShapeRenderer, method_name) as mock_method:
                ShapeRenderer.render(mock_painter, ann)
                mock_method.assert_called_once_with(mock_painter, ann)

    def test_render_unknown_tool_does_nothing(self):
        """render() con tool desconocido no debe crashear."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor

        mock_painter = MagicMock()
        ann = Annotation(tool="nonexistent_tool", points=[(0, 0)], color=QColor(0, 0, 0))
        ShapeRenderer.render(mock_painter, ann)

    def test_draw_arrow_with_zero_length(self):
        """draw_arrow con mismos puntos (longitud 0) debe retornar sin crashear."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor

        mock_painter = MagicMock()
        ann = Annotation(tool="arrow", points=[(50, 50), (50, 50)], color=QColor(255, 0, 0))
        ShapeRenderer.draw_arrow(mock_painter, ann)
        mock_painter.drawLine.assert_not_called()

    def test_draw_freehand_with_exactly_2_points(self):
        """draw_freehand con exactamente 2 puntos debe usar lineTo, no quadTo."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor

        mock_painter = MagicMock()
        ann = Annotation(
            tool="freehand",
            points=[(10, 20), (30, 40)],
            color=QColor(0, 255, 0),
            stroke_width=3.0,
        )
        ShapeRenderer.draw_freehand(mock_painter, ann)
        assert mock_painter.drawPath.called

    def test_draw_methods_with_single_point_return_early(self):
        """Todos los draw de formas geometricas con 1 punto no deben crashear."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor

        single_point_tools = ["arrow", "rect", "circle", "freehand", "highlighter"]
        for tool in single_point_tools:
            mock_painter = MagicMock()
            ann = Annotation(tool=tool, points=[(100, 200)], color=QColor(255, 255, 255))
            method = getattr(ShapeRenderer, f"draw_{tool}")
            method(mock_painter, ann)
            mock_painter.drawLine.assert_not_called()
            mock_painter.drawRect.assert_not_called()
            mock_painter.drawEllipse.assert_not_called()


# ---------------------------------------------------------------------------
# Test 2: HotkeyListener - gestion de estado (toggle, laser, active_tool)
# ---------------------------------------------------------------------------

class TestHotkeyListenerState:
    """Verifica la logica de toggle, laser state y active_tool
    sin necesidad de iniciar el listener real de pynput."""

    @pytest.fixture(autouse=True)
    def _setup_app(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield

    @pytest.fixture
    def listener(self):
        from core.hotkey import HotkeyListener
        return HotkeyListener()

    def test_initial_state(self, listener):
        """Estado inicial: sin tool activo, laser off, alt no presionado."""
        assert listener._active_tool is None
        assert listener._laser_on is False
        assert listener._alt_held is False
        assert listener._shift_held is False

    def test_tool_toggle_on(self, listener):
        """Presionar Alt+A con ningun tool activo emite tool_toggled('arrow')."""
        from pynput import keyboard

        signals = []
        listener.tool_toggled.connect(lambda t: signals.append(('tool', t)))

        listener._on_press(keyboard.Key.alt_l)
        assert listener._alt_held is True

        mock_key = MagicMock()
        mock_key.vk = 65  # 'A'
        mock_key.char = 'a'
        listener._on_press(mock_key)

        assert listener._active_tool == "arrow"
        assert len(signals) == 1
        assert signals[0] == ('tool', 'arrow')

    def test_tool_toggle_off(self, listener):
        """Presionar Alt+A dos veces: primero activa, luego desactiva."""
        deactivated_signals = []
        listener.deactivated.connect(lambda: deactivated_signals.append(True))

        listener._alt_held = True
        mock_key = MagicMock()
        mock_key.vk = 65
        listener._on_press(mock_key)
        assert listener._active_tool == "arrow"

        listener._on_press(mock_key)
        assert listener._active_tool is None
        assert len(deactivated_signals) == 1

    def test_tool_switch(self, listener):
        """Alt+A seguido de Alt+R cambia de arrow a rect sin deactivar."""
        signals = []
        listener.tool_toggled.connect(lambda t: signals.append(t))

        listener._alt_held = True

        key_a = MagicMock()
        key_a.vk = 65
        listener._on_press(key_a)
        assert listener._active_tool == "arrow"

        key_r = MagicMock()
        key_r.vk = 82  # 'R'
        listener._on_press(key_r)
        assert listener._active_tool == "rect"
        assert signals == ["arrow", "rect"]

    def test_laser_toggle(self, listener):
        """Alt+P togglea el laser independientemente del tool activo."""
        laser_signals = []
        listener.laser_toggled.connect(lambda on: laser_signals.append(on))

        listener._alt_held = True
        key_p = MagicMock()
        key_p.vk = 80  # 'P'

        listener._on_press(key_p)
        assert listener._laser_on is True
        assert laser_signals == [True]

        listener._on_press(key_p)
        assert listener._laser_on is False
        assert laser_signals == [True, False]

    def test_esc_deactivates(self, listener):
        """Esc desactiva el tool activo."""
        from pynput import keyboard

        deactivated = []
        listener.deactivated.connect(lambda: deactivated.append(True))

        listener._active_tool = "arrow"
        listener._on_press(keyboard.Key.esc)

        assert listener._active_tool is None
        assert len(deactivated) == 1

    def test_esc_without_active_tool_no_signal(self, listener):
        """Esc sin tool activo no emite deactivated."""
        from pynput import keyboard

        deactivated = []
        listener.deactivated.connect(lambda: deactivated.append(True))

        listener._on_press(keyboard.Key.esc)
        assert len(deactivated) == 0

    def test_set_laser_state_syncs(self, listener):
        """set_laser_state sincroniza el estado interno."""
        listener.set_laser_state(True)
        assert listener._laser_on is True
        listener.set_laser_state(False)
        assert listener._laser_on is False

    def test_set_active_tool_syncs(self, listener):
        """set_active_tool sincroniza el estado interno."""
        listener.set_active_tool("circle")
        assert listener._active_tool == "circle"
        listener.set_active_tool(None)
        assert listener._active_tool is None

    def test_undo_and_clear_signals(self, listener):
        """Alt+Z emite undo, Alt+Shift+Z emite clear."""
        undo = []
        clear = []
        listener.undo_requested.connect(lambda: undo.append(True))
        listener.clear_requested.connect(lambda: clear.append(True))

        listener._alt_held = True
        key_z = MagicMock()
        key_z.vk = 90  # 'Z'

        listener._shift_held = False
        listener._on_press(key_z)
        assert len(undo) == 1
        assert len(clear) == 0

        listener._shift_held = True
        listener._on_press(key_z)
        assert len(undo) == 1
        assert len(clear) == 1

    def test_modifier_release_tracking(self, listener):
        """Soltar Alt/Shift/Ctrl actualiza los flags correctamente."""
        from pynput import keyboard

        listener._alt_held = True
        listener._shift_held = True
        listener._ctrl_held = True

        listener._on_release(keyboard.Key.alt_l)
        assert listener._alt_held is False

        listener._on_release(keyboard.Key.shift)
        assert listener._shift_held is False

        listener._on_release(keyboard.Key.ctrl)
        assert listener._ctrl_held is False

    def test_update_shortcuts(self, listener):
        """update_shortcuts reemplaza el mapeo de atajos."""
        new_shortcuts = {"x": "arrow", "y": "rect"}
        listener.update_shortcuts(new_shortcuts)
        assert listener._shortcuts == new_shortcuts

        listener._alt_held = True
        signals = []
        listener.tool_toggled.connect(lambda t: signals.append(t))

        key_a = MagicMock()
        key_a.vk = 65
        key_a.char = 'a'
        listener._on_press(key_a)
        assert len(signals) == 0

    def test_no_action_without_alt(self, listener):
        """Sin Alt presionado, las teclas de tool no hacen nada."""
        signals = []
        listener.tool_toggled.connect(lambda t: signals.append(t))

        listener._alt_held = False
        key_a = MagicMock()
        key_a.vk = 65
        listener._on_press(key_a)
        assert len(signals) == 0


# ---------------------------------------------------------------------------
# Test 3: config.py load_shortcuts / save_shortcuts con datos corruptos
# ---------------------------------------------------------------------------

class TestConfigShortcuts:
    """Prueba la persistencia de shortcuts con archivos corruptos,
    vacios, con tipos incorrectos, etc."""

    def test_load_defaults_when_file_missing(self, tmp_path):
        """Sin archivo, debe retornar TOOL_SHORTCUTS por defecto."""
        import config
        settings_file = str(tmp_path / "settings.json")
        with patch.object(config, 'SETTINGS_PATH', settings_file):
            result = config.load_shortcuts()
            assert result == dict(config.TOOL_SHORTCUTS)

    def test_load_with_valid_file(self, tmp_path):
        """Con archivo valido, debe retornar los shortcuts guardados."""
        import config
        settings_file = str(tmp_path / "settings.json")
        custom = {"x": "arrow", "y": "rect"}
        with open(settings_file, 'w') as f:
            json.dump({"shortcuts": custom}, f)

        with patch.object(config, 'SETTINGS_PATH', settings_file):
            result = config.load_shortcuts()
            assert result == custom

    def test_load_with_corrupted_json(self, tmp_path):
        """Con JSON invalido, debe retornar defaults sin crashear."""
        import config
        settings_file = str(tmp_path / "settings.json")
        with open(settings_file, 'w') as f:
            f.write("{corrupted json!!!")

        with patch.object(config, 'SETTINGS_PATH', settings_file):
            result = config.load_shortcuts()
            assert result == dict(config.TOOL_SHORTCUTS)

    def test_load_with_empty_file(self, tmp_path):
        """Con archivo vacio, debe retornar defaults."""
        import config
        settings_file = str(tmp_path / "settings.json")
        with open(settings_file, 'w') as f:
            f.write("")

        with patch.object(config, 'SETTINGS_PATH', settings_file):
            result = config.load_shortcuts()
            assert result == dict(config.TOOL_SHORTCUTS)

    def test_load_with_wrong_type_shortcuts(self, tmp_path):
        """BUG DOCUMENTADO: Si shortcuts no es dict, load_shortcuts lo retorna tal cual."""
        import config
        settings_file = str(tmp_path / "settings.json")
        with open(settings_file, 'w') as f:
            json.dump({"shortcuts": "not_a_dict"}, f)

        with patch.object(config, 'SETTINGS_PATH', settings_file):
            result = config.load_shortcuts()
            # BUG: retorna "not_a_dict" en lugar de defaults
            assert result == "not_a_dict"

    def test_load_with_missing_shortcuts_key(self, tmp_path):
        """Sin clave 'shortcuts', debe retornar defaults."""
        import config
        settings_file = str(tmp_path / "settings.json")
        with open(settings_file, 'w') as f:
            json.dump({"other_key": "value"}, f)

        with patch.object(config, 'SETTINGS_PATH', settings_file):
            result = config.load_shortcuts()
            assert result == dict(config.TOOL_SHORTCUTS)

    def test_save_creates_file(self, tmp_path):
        """save_shortcuts debe crear el archivo con contenido correcto."""
        import config
        settings_file = str(tmp_path / "settings.json")
        custom = {"x": "arrow", "z": "circle"}
        with patch.object(config, 'SETTINGS_PATH', settings_file):
            config.save_shortcuts(custom)

        with open(settings_file) as f:
            data = json.load(f)
        assert data == {"shortcuts": custom}

    def test_save_overwrites_existing(self, tmp_path):
        """save_shortcuts debe sobrescribir datos previos."""
        import config
        settings_file = str(tmp_path / "settings.json")
        with open(settings_file, 'w') as f:
            json.dump({"shortcuts": {"old": "data"}}, f)

        new_shortcuts = {"n": "freehand"}
        with patch.object(config, 'SETTINGS_PATH', settings_file):
            config.save_shortcuts(new_shortcuts)

        with open(settings_file) as f:
            data = json.load(f)
        assert data["shortcuts"] == new_shortcuts

    def test_save_to_readonly_location_raises(self):
        """DEFECTO DOCUMENTADO: save_shortcuts no maneja errores de escritura."""
        import config
        bad_path = "/nonexistent_dir/impossible/settings.json"
        with patch.object(config, 'SETTINGS_PATH', bad_path):
            with pytest.raises((FileNotFoundError, OSError)):
                config.save_shortcuts({"a": "arrow"})

    def test_roundtrip_save_load(self, tmp_path):
        """Guardar y cargar debe retornar los mismos datos."""
        import config
        settings_file = str(tmp_path / "settings.json")
        custom = {"a": "arrow", "r": "rect", "c": "circle",
                  "f": "freehand", "t": "text", "p": "laser"}
        with patch.object(config, 'SETTINGS_PATH', settings_file):
            config.save_shortcuts(custom)
            loaded = config.load_shortcuts()
        assert loaded == custom


# ---------------------------------------------------------------------------
# Test 4: Annotation dataclass edge cases
# ---------------------------------------------------------------------------

class TestAnnotationDataclass:
    """Verifica comportamiento del dataclass Annotation con datos limite."""

    def test_default_values(self):
        """Annotation con solo tool debe tener defaults razonables."""
        from core.drawing import Annotation
        ann = Annotation(tool="arrow")
        assert ann.tool == "arrow"
        assert ann.points == []
        assert ann.stroke_width == 3.0
        assert ann.text == ""
        assert ann.opacity == 1.0
        assert ann.created_at <= time.time()
        assert ann.color is not None

    def test_independent_point_lists(self):
        """Cada Annotation debe tener su propia lista de puntos (no compartida)."""
        from core.drawing import Annotation
        a1 = Annotation(tool="arrow")
        a2 = Annotation(tool="rect")
        a1.points.append((10, 20))
        assert len(a2.points) == 0

    def test_opacity_boundaries(self):
        """Opacity en 0.0 y 1.0 no debe causar problemas."""
        from core.drawing import Annotation, _color_with_alpha
        from PyQt6.QtGui import QColor

        ann_full = Annotation(tool="arrow", opacity=1.0, color=QColor(255, 0, 0))
        result = _color_with_alpha(ann_full.color, ann_full.opacity)
        assert result.alphaF() == pytest.approx(1.0, abs=0.01)

        ann_zero = Annotation(tool="arrow", opacity=0.0, color=QColor(255, 0, 0))
        result = _color_with_alpha(ann_zero.color, ann_zero.opacity)
        assert result.alphaF() == pytest.approx(0.0, abs=0.01)

    def test_negative_opacity_clamped_by_qt(self):
        """_color_with_alpha con opacity negativa: Qt clampea internamente."""
        from core.drawing import _color_with_alpha
        from PyQt6.QtGui import QColor
        result = _color_with_alpha(QColor(255, 0, 0), -0.5)
        assert result.alphaF() >= 0.0

    def test_color_with_alpha_preserves_rgb(self):
        """_color_with_alpha no debe cambiar los componentes RGB."""
        from core.drawing import _color_with_alpha
        from PyQt6.QtGui import QColor
        original = QColor(100, 150, 200)
        result = _color_with_alpha(original, 0.5)
        assert result.red() == 100
        assert result.green() == 150
        assert result.blue() == 200

    def test_annotation_with_many_points(self):
        """Annotation con miles de puntos no debe crashear."""
        from core.drawing import Annotation
        points = [(float(i), float(i * 2)) for i in range(10000)]
        ann = Annotation(tool="freehand", points=points)
        assert len(ann.points) == 10000


# ---------------------------------------------------------------------------
# Test 5: Drawing methods con inputs edge case
# ---------------------------------------------------------------------------

class TestDrawingEdgeCases:
    """Prueba metodos de dibujo con inputs extremos y atipicos."""

    def test_draw_arrow_empty_points(self):
        """draw_arrow con lista vacia no debe crashear."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(tool="arrow", points=[], color=QColor(255, 0, 0))
        ShapeRenderer.draw_arrow(mock_painter, ann)
        mock_painter.drawLine.assert_not_called()

    def test_draw_rect_with_same_start_end(self):
        """draw_rect con inicio=fin debe dibujar un rect de 0x0 sin crashear."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(tool="rect", points=[(50, 50), (50, 50)], color=QColor(0, 255, 0))
        ShapeRenderer.draw_rect(mock_painter, ann)
        assert mock_painter.drawRect.called

    def test_draw_circle_with_negative_coordinates(self):
        """draw_circle con coordenadas negativas debe funcionar."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(
            tool="circle",
            points=[(-100, -200), (100, 200)],
            color=QColor(0, 0, 255),
        )
        ShapeRenderer.draw_circle(mock_painter, ann)
        assert mock_painter.drawEllipse.called

    def test_draw_text_empty_string(self):
        """draw_text con texto vacio debe retornar sin dibujar."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(tool="text", points=[(10, 20)], text="", color=QColor(255, 255, 255))
        ShapeRenderer.draw_text(mock_painter, ann)
        mock_painter.drawText.assert_not_called()

    def test_draw_text_with_valid_data(self):
        """draw_text con texto y punto validos debe dibujar."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(tool="text", points=[(100, 200)], text="Hello", color=QColor(255, 255, 255))
        ShapeRenderer.draw_text(mock_painter, ann)
        assert mock_painter.drawText.called

    def test_draw_highlighter_with_collinear_points(self):
        """draw_highlighter con puntos en linea recta debe funcionar."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        points = [(0, 100), (50, 100), (100, 100), (150, 100)]
        ann = Annotation(tool="highlighter", points=points, color=QColor(255, 255, 0))
        ShapeRenderer.draw_highlighter(mock_painter, ann)
        assert mock_painter.drawPath.called

    def test_draw_laser_with_none_pos_and_empty_trail(self):
        """draw_laser con pos=None y trail vacio no debe crashear."""
        from core.drawing import ShapeRenderer
        mock_painter = MagicMock()
        ShapeRenderer.draw_laser(mock_painter, None, [])

    def test_draw_laser_with_single_trail_point(self):
        """draw_laser con 1 punto en trail debe dibujar solo el dot."""
        from core.drawing import ShapeRenderer
        mock_painter = MagicMock()
        ShapeRenderer.draw_laser(mock_painter, (100, 200), [(100, 200)])
        assert mock_painter.drawRect.called

    def test_draw_ripple_progress_at_boundary(self):
        """draw_ripple con progress=1.0 debe retornar sin dibujar."""
        from core.drawing import ShapeRenderer
        mock_painter = MagicMock()
        ShapeRenderer.draw_ripple(mock_painter, (50, 50), 1.0)
        mock_painter.drawEllipse.assert_not_called()

    def test_draw_ripple_progress_zero(self):
        """draw_ripple con progress=0.0 debe dibujar el ripple completo."""
        from core.drawing import ShapeRenderer
        mock_painter = MagicMock()
        ShapeRenderer.draw_ripple(mock_painter, (50, 50), 0.0)
        assert mock_painter.drawEllipse.called

    def test_draw_freehand_with_many_points(self):
        """draw_freehand con muchos puntos usa quadTo para suavizado."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        points = [(i, i * 2) for i in range(100)]
        ann = Annotation(tool="freehand", points=points, color=QColor(255, 0, 255), stroke_width=2.0)
        ShapeRenderer.draw_freehand(mock_painter, ann)
        assert mock_painter.drawPath.called

    def test_draw_arrow_very_short_line(self):
        """draw_arrow con linea de 0.5px (< 1) debe retornar sin dibujar."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(tool="arrow", points=[(100, 100), (100.3, 100.4)], color=QColor(255, 0, 0))
        ShapeRenderer.draw_arrow(mock_painter, ann)
        mock_painter.drawLine.assert_not_called()

    def test_draw_arrow_with_large_stroke(self):
        """draw_arrow con stroke_width muy grande debe escalar la cabeza sin crashear."""
        from core.drawing import ShapeRenderer, Annotation
        from PyQt6.QtGui import QColor
        mock_painter = MagicMock()
        ann = Annotation(
            tool="arrow",
            points=[(0, 0), (500, 500)],
            color=QColor(255, 0, 0),
            stroke_width=50.0,
        )
        ShapeRenderer.draw_arrow(mock_painter, ann)
        assert mock_painter.drawLine.called
