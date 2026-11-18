"""Quick actions: the ``T`` drag handle.

Free wrapping left the quick-action bar when upstream's bubble constraint took
over line breaking (v1.5.22 merge, decision D2). The handle only scales the
text and its frame now; the removed wrap cases are covered by
``tests/test_bubble_layout.py``.
"""

import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from qtpy.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from ballontranslator.ui.text_engine.item import TextBlkItem
from ballontranslator.ui.text_quick_actions import (
    DRAG_SPAN,
    drag_progress,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    TextQuickActions,
    scaled_font_size,
)
from ballontranslator.utils.fontformat import TextAlignment
from ballontranslator.utils.textblock import TEXT_LAYOUT_VERSION, TextBlock


def make_item(text, bounds, font_size=30, vertical=True) -> TextBlkItem:
    block = TextBlock(list(bounds), text_layout_version=TEXT_LAYOUT_VERSION)
    block._bounding_rect = list(bounds)
    block.vertical = vertical
    block.alignment = TextAlignment.Left
    block.translation = text
    block.fontformat.font_size = font_size
    block.fontformat.letter_spacing = 1.0
    block.fontformat.vertical = vertical
    return TextBlkItem(block, 0)


class ScaledSizeTest(unittest.TestCase):

    def test_up_and_right_enlarge(self) -> None:
        right = drag_progress(60.0, 0.0)
        up = drag_progress(0.0, -60.0)
        self.assertGreater(scaled_font_size(40.0, right), 40.0)
        self.assertGreater(scaled_font_size(40.0, up), 40.0)
        self.assertAlmostEqual(
            scaled_font_size(40.0, right),
            scaled_font_size(40.0, up),
        )

    def test_down_and_left_shrink(self) -> None:
        self.assertLess(scaled_font_size(40.0, drag_progress(-60.0, 0.0)), 40.0)
        self.assertLess(scaled_font_size(40.0, drag_progress(0.0, 60.0)), 40.0)

    def test_zero_drag_keeps_the_size(self) -> None:
        self.assertAlmostEqual(scaled_font_size(40.0, 0.0), 40.0)

    def test_bounds_are_respected(self) -> None:
        self.assertEqual(scaled_font_size(40.0, -1e6), MIN_FONT_SIZE)
        self.assertEqual(scaled_font_size(40.0, 1e6), MAX_FONT_SIZE)

    def test_full_span_doubles_the_size(self) -> None:
        self.assertAlmostEqual(
            scaled_font_size(40.0, DRAG_SPAN), 80.0, places=6
        )


class ActionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.scene = QGraphicsScene()
        self.items = [make_item('一二三四', (0, 0, 200, 300))]
        self.scene.addItem(self.items[0])
        self.view = QGraphicsView(self.scene)
        self.view.resize(400, 400)
        self.actions = TextQuickActions(self.view, lambda: self.items)
        self.actions.set_target(self.items[0])

    def test_only_the_scale_handle_survives(self) -> None:
        """The wrap button must be gone: upstream owns free wrapping now."""
        self.assertFalse(hasattr(self.actions, 'wrap_button'))
        self.assertFalse(hasattr(self.actions, '_on_wrap_clicked'))
        self.assertTrue(self.actions.scale_button.isVisibleTo(self.view))

    def test_drag_applies_a_scaled_size(self) -> None:
        self.actions.start_scale(100.0, 100.0)
        # up (dy negative) plus right (dx positive) spans one full drag, so
        # the size doubles.
        self.actions.drag_scale(
            100.0 - DRAG_SPAN / 2, 100.0 + DRAG_SPAN / 2
        )
        self.assertAlmostEqual(
            self.items[0].fontformat.font_size, 60.0, places=3
        )
        self.actions.end_scale()

    def _scaled(self, dy: float):
        item = self.items[0]
        self.actions.set_target(item)
        self.actions.start_scale(100.0, 100.0)
        self.actions.drag_scale(100.0 - dy, 100.0)
        self.actions.end_scale()
        return item

    def test_growing_scales_the_frame_with_the_text(self) -> None:
        item = self.items[0]
        frame = item.boundingRect()
        grown = self._scaled(DRAG_SPAN * 0.5)
        self.assertAlmostEqual(grown.boundingRect().width(),
                               frame.width() * 1.5, places=0)

    def test_shrinking_scales_the_frame_down_too(self) -> None:
        item = self.items[0]
        frame = item.boundingRect()
        shrunk = self._scaled(-DRAG_SPAN * 0.5)
        self.assertAlmostEqual(shrunk.boundingRect().width(),
                               frame.width() * 0.5, places=0)

    def test_scaling_keeps_the_frame_centre(self) -> None:
        item = self.items[0]
        before = item.mapToScene(item.boundingRect().center())
        grown = self._scaled(DRAG_SPAN * 0.4)
        after = grown.mapToScene(grown.boundingRect().center())
        self.assertAlmostEqual(after.x(), before.x(), places=1)
        self.assertAlmostEqual(after.y(), before.y(), places=1)

    def test_a_finished_drag_marks_the_size_as_manual(self) -> None:
        """D3: the auto-fit pass must not refit a hand-picked size."""
        item = self._scaled(DRAG_SPAN * 0.5)
        self.assertTrue(item.blk.manual_font_size)

    def test_a_click_without_movement_stays_unmarked(self) -> None:
        item = self._scaled(0.0)
        self.assertFalse(item.blk.manual_font_size)


class NotifyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_binding_notifies_the_quick_actions(self) -> None:
        """The handles follow the control's binding, including clearing."""
        from types import SimpleNamespace

        from qtpy.QtWidgets import QGraphicsScene

        from ballontranslator.ui.text_engine.shape_control import (
            TextBlkShapeControl,
        )

        scene = QGraphicsScene()
        seen = []
        scene.text_quick_actions = SimpleNamespace(
            set_target=lambda item: seen.append(item)
        )
        from qtpy.QtWidgets import QGraphicsView

        view = QGraphicsView(scene)
        view.resize(400, 400)
        control = TextBlkShapeControl(view)
        scene.addItem(control)

        item = make_item('一二', (0, 0, 100, 100))
        control.setBlkItem(item)
        self.assertTrue(seen)
        self.assertIs(seen[-1], item)

        control.setBlkItem(None)
        self.assertIsNone(seen[-1])


class ScalePersistenceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_scale_snapshot_is_undoable(self) -> None:
        """A finished drag must leave one undoable step on the text stack."""
        from ballontranslator.ui.text_engine.formatting.commands import (
            push_scale_snapshot,
        )

        class FakeUndoStack:
            def __init__(self):
                self.commands = []

            def push(self, command):
                self.commands.append(command)
                command.redo()

        class FakeCanvas:
            def __init__(self):
                self.stack = FakeUndoStack()

            def push_text_command(self, command):
                self.stack.push(command)

        item = make_item('一二三', (0, 0, 120, 80), font_size=40)
        before = {
            'size': 40.0, 'pt': 30.75,
            'w': item.boundingRect().width(),
            'h': item.boundingRect().height(),
            'cx': 0.0, 'cy': 0.0,
        }
        canvas = FakeCanvas()
        push_scale_snapshot(
            canvas,
            [item],
            [before],
            [{**before, 'size': 60.0, 'pt': 46.12}],
        )
        self.assertEqual(len(canvas.stack.commands), 1)
        self.assertAlmostEqual(item.fontformat.font_size, 60.0, places=2)
        canvas.stack.commands[0].undo()
        self.assertAlmostEqual(item.fontformat.font_size, 40.0, places=2)
        # Redo used to push another command from inside redo(), which Qt
        # does not allow, so the stack broke and the page saved nothing.
        canvas.stack.commands[0].redo()
        self.assertAlmostEqual(item.fontformat.font_size, 60.0, places=2)

    def test_replay_runs_with_pushes_suspended(self) -> None:
        from ballontranslator.ui.text_engine.formatting.commands import (
            suspend_undo_commands,
            undo_suspended,
        )

        self.assertFalse(undo_suspended())
        with suspend_undo_commands():
            self.assertTrue(undo_suspended())
        self.assertFalse(undo_suspended())


if __name__ == '__main__':
    unittest.main()
