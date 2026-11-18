"""The switch gates the vertical auto-fit, and the settings panel exposes it."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from qtpy.QtWidgets import QApplication

from ballontranslator.ui.text_engine.bubble_layout import fit_text_in_shape
from ballontranslator.ui.text_engine.formatting.commands import (
    mark_manual_font_size,
)
from ballontranslator.ui.text_engine.item import TextBlkItem
from ballontranslator.ui.text_engine.vertical_fit import (
    fit_vertical_font_size,
)
from ballontranslator.utils import config as C
from ballontranslator.utils.bubble_shape import BubbleShape
from ballontranslator.utils.fontformat import FontFormat, TextAlignment
from ballontranslator.utils.textblock import TEXT_LAYOUT_VERSION, TextBlock


def make_item(text, bounds, font_size) -> TextBlkItem:
    block = TextBlock(list(bounds), text_layout_version=TEXT_LAYOUT_VERSION)
    block._bounding_rect = list(bounds)
    block.vertical = True
    block.alignment = TextAlignment.Center
    block.translation = text
    block.fontformat.font_size = font_size
    block.fontformat.letter_spacing = 1.0
    block.fontformat.vertical = True
    return TextBlkItem(block, 0)


def make_bubble_item(text, font_size) -> TextBlkItem:
    """A koharu bubble block, the shape upstream's auto-fit works on."""
    shape = BubbleShape.rectangle((0, 0, 200, 300))
    block = TextBlock(
        [0, 0, 200, 300], _bounding_rect=[0, 0, 200, 300],
        translation=text, det_model='koharu',
        bubble_shape=shape, bubble_layout=True,
        fontformat=FontFormat(
            font_family='Arial', font_size=font_size, vertical=True, alignment=1,
        ),
        text_layout_version=TEXT_LAYOUT_VERSION,
    )
    return TextBlkItem(block, 0)



class AutofitSwitchTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_switch_defaults_to_off(self) -> None:
        """A layout-changing feature must not surprise existing projects."""
        self.assertFalse(C.ProgramConfig().vertical_font_autofit_enabled)

    def test_disabled_switch_leaves_the_font_size_alone(self) -> None:
        item = make_item('短い', (0, 0, 200, 400), 20)
        before = item.fontformat.font_size
        with patch.object(C.pcfg, 'vertical_font_autofit_enabled', False):
            if C.pcfg.vertical_font_autofit_enabled:
                fit_vertical_font_size(item)
        self.assertEqual(item.fontformat.font_size, before)

    def test_enabled_switch_grows_the_block(self) -> None:
        item = make_item('短い', (0, 0, 200, 400), 20)
        before = item.fontformat.font_size
        with patch.object(C.pcfg, 'vertical_font_autofit_enabled', True):
            if C.pcfg.vertical_font_autofit_enabled:
                fit_vertical_font_size(item)
        self.assertGreater(item.fontformat.font_size, before)

    def test_manual_size_is_not_refit_by_the_bubble_auto_fit(self) -> None:
        """A size the user set by hand has to survive the next fit.

        The grow-only fit used to run inside populateSceneTextitems; the
        merged build hands auto-fit to upstream's ``fit_text_in_shape``, so
        the mark is what has to stop it lifting a hand-picked size back into
        whatever room the frame has.
        """
        manual = make_bubble_item('短い', 30)
        mark_manual_font_size(manual)
        other = make_bubble_item('短い', 30)
        self.addCleanup(manual.deleteLater)
        self.addCleanup(other.deleteLater)
        self.assertAlmostEqual(
            fit_text_in_shape(manual, auto_size=True).font_size, 30., places=3
        )
        self.assertGreater(
            fit_text_in_shape(other, auto_size=True).font_size, 30.
        )

    def test_manual_size_mark_is_part_of_the_block_payload(self) -> None:
        """The mark has to reach the project file, not just the live item."""
        block = TextBlock([0, 0, 200, 400])
        self.assertFalse(block.manual_font_size)
        mark_manual_font_size(SimpleNamespace(blk=block))
        self.assertTrue(block.to_dict()['manual_font_size'])
        # blocks restored from an older project simply start unmarked
        self.assertFalse(TextBlock(**{'manual_font_size': False}).manual_font_size)


if __name__ == '__main__':
    unittest.main()
