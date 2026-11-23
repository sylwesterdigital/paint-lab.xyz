"""Canvas-first mobile UI contract and release metadata."""
import unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'frontend/index.html').read_text()
class MobileStudioTests(unittest.TestCase):
 def test_mobile_interface_controls(self):
  for marker in ['id="mobileStudio"','id="mobileFocus"','id="mobileSwatch"','id="mobilePaletteGrid"','id="mobileBrush"','id="mobileSizeSlider"','id="mobileSettings"','id="mobileSave"','id="mobileSwitches"','data-mobile-sheet="layersPanel"']:
   self.assertIn(marker,SOURCE)
 def test_touch_canvas_and_desktop_separation(self):
  self.assertIn('(pointer:coarse) and (max-width:1024px)',SOURCE)
  self.assertIn('mobile-workspace .surface>.panel:not(.mobile-sheet-active)',SOURCE)
  self.assertIn('function closeMobileSheet()',SOURCE)
  self.assertIn('function toggleMobilePopover(',SOURCE)
  self.assertIn("function mobileStorePreferences()",SOURCE)
 def test_release(self):
  self.assertIn('<meta name="paint-lab-version" content="0.1.64">',SOURCE)
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['version'],'0.1.64')
