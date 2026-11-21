"""v0.1.9 mobile painting controls & stable gesture contracts."""
from pathlib import Path
import unittest,json
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
ROOT=Path(__file__).resolve().parents[1]
class Mobile019(unittest.TestCase):
 def test_undo_redo_bottom(self):
  a=HTML.index('id="mobileBottom"');b=HTML.index('id="mobileUndoRedo"');c=HTML.index('id="mobileSheetShade"')
  self.assertTrue(a<b<c)
  self.assertIn('id="mobileUndo"',HTML);self.assertIn('id="mobileRedo"',HTML)
  self.assertIn("$('mobileRedo').onclick=redo",HTML)
  self.assertIn("history:['mobileUndoRedo']",HTML)
  self.assertIn("'mobileRedo'].forEach",HTML)
 def test_custom_slider_and_tip_preview(self):
  self.assertIn('role="slider"',HTML)
  self.assertIn('id="mobileSizeSlider" class="mobile-size-track"',HTML)
  self.assertIn('setPointerCapture(e.pointerId)',HTML)
  self.assertIn('function drawMobileTipPreviews()',HTML)
  self.assertIn('id="mobileBrushImage"',HTML)
 def test_gestures_and_account(self):
  self.assertIn('const pair=[...touchPointers.keys()].slice(0,2)',HTML)
  self.assertIn('if(d<25)return',HTML)
  self.assertIn('rotateCanvas:true',HTML)
  self.assertIn('id="mobileAccountEntry"',HTML)
  self.assertIn('data-mobile-action="account"',HTML)
 def test_release(self):
  self.assertEqual(json.loads((ROOT/'changelog.json').read_text())['version'],'0.1.32')
  self.assertIn('<meta name="paint-lab-version" content="0.1.32">',HTML)
