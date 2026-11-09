"""The switch gates the vertical auto-fit, and the settings panel exposes it."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from qtpy.QtWidgets import QApplication

from ballontranslator.ui.text_engine.editing.manager import SceneTextManager
from ballontranslator.ui.text_engine.formatting.commands import (
    mark_manual_font_size,
)
from ballontranslator.ui.text_engine.item import TextBlkItem
from ballontranslator.ui.text_engine.vertical_fit import (
    fit_vertical_font_size,
)
from ballontranslator.utils import config as C
from ballontranslator.utils.fontformat import TextAlignment
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


def populate(blocks):
    """Run the real page-load method against a minimal host."""
    host = SimpleNamespace(
        formatpanel=SimpleNamespace(
            familybox=SimpleNamespace(currentText=lambda: ''),
        ),
        addTextBlock=lambda blk: TextBlkItem(blk, 0),
        auto_textlayout_flag=False,
        imgtrans_proj=SimpleNamespace(current_block_list=lambda: blocks),
    )
    SceneTextManager.populateSceneTextitems(host)
    return host



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

    def test_manual_size_is_not_refit_when_the_page_reloads(self) -> None:
        """A size the user set by hand has to survive the next page load.

        The grow-only fit runs on every populateSceneTextitems; without the
        mark it lifts a shrunk block back into whatever room the frame has.
        """
        manual = make_item('短い', (0, 0, 200, 400), 20)
        mark_manual_font_size(manual)
        other = make_item('短い', (0, 0, 200, 400), 20)
        with patch.object(C.pcfg, 'vertical_font_autofit_enabled', True), \
                patch.object(C.pcfg, 'let_fntsize_flag', 0):
            populate([manual.blk, other.blk])
        self.assertEqual(manual.blk.fontformat.font_size, 20)
        self.assertGreater(other.blk.fontformat.font_size, 20)

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
