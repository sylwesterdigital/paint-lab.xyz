"""v0.1.56: one mobile brush launcher, all editing inside its rail."""
from pathlib import Path
import json
import unittest

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()

class SingleBrushLauncherV156(unittest.TestCase):
    def test_current_release(self):
        self.assertEqual(json.loads((APP/'version.json').read_text())['version'],'0.1.56')
    def test_exactly_one_launcher_over_palette(self):
        section=HTML.split('id="mobileBrushTop" class="mobile-brush-top"',1)[1].split('</div>',1)[0]
        self.assertEqual(section.count('<button'),1)
        self.assertIn('id="mobileBrush"',section)
        self.assertIn('id="mobileBrushLauncherImage"',section)
        self.assertNotIn('id="mobileTipCycle"',section)
        self.assertNotIn('mobileBrushNumber',section)
        self.assertNotIn('mobile-size-trigger-caption',section)
    def test_tip_selection_is_inside_size_popup(self):
        popup=HTML.split('<div id="mobileBrushPopover"',1)[1].split('<div id="mobileBrushSizePreview"',1)[0]
        self.assertIn('id="mobileSizeSlider"',popup)
        self.assertIn('id="mobileTipCycle"',popup)
        self.assertIn('id="mobileBrushImage"',popup)
        self.assertNotIn('id="mobileSizeValue"',popup)
        self.assertLess(popup.index('id="mobileSizeSlider"'),popup.index('id="mobileTipCycle"'))
        self.assertIn('for(const id of [\'mobileBrushLauncherImage\',\'mobileBrushImage\'])',HTML)
    def test_no_new_paint_from_size_preview(self):
        self.assertIn('function drawMobileActualTip()',HTML)
        self.assertIn('function mobileSizeChange(value)',HTML)
        self.assertIn("$('mobileBrush').onclick=()=>toggleMobilePopover('mobileBrushPopover')",HTML)
        self.assertIn('function openMobileTipGallery()',HTML)
        self.assertIn('mobileTipGalleryCategory=\'All\';renderMobileTipGallery();',HTML)
    def test_one_dock_and_no_duplicate_labels(self):
        self.assertIn('.mobile-workspace #mobileBrushPopover #mobileTipCycle{',HTML)
        self.assertIn('.mobile-workspace .mobile-bottom #mobileBrushLauncherImage{',HTML)
        self.assertIn('.mobile-workspace #mobileBrushPopover .mobile-size-value{display:none!important}',HTML)
        self.assertNotIn('id="mobileBrushNumber"',HTML)
        self.assertNotIn('id="mobileBrushNext"',HTML)

if __name__=='__main__':unittest.main()
