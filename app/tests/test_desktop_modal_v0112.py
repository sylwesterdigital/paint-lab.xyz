"""Desktop modal transforms and provisional duplication must stay click-free."""
from pathlib import Path
import json, unittest
APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
class DesktopModalV0112(unittest.TestCase):
 def test_keyboards_follow_mouse_without_drag(self):
  for marker in ('function beginDesktopTransform(mode,duplicate=false)',
    "window.addEventListener('pointermove',moveDesktopTransform,true)",
    "function confirmDesktopTransform()", "function cancelDesktopTransform()",
    'desktopModal:true,duplicate,pid:null',
    "if(['g','r','s'].includes(key)&&!e.shiftKey)"):
   self.assertIn(marker,HTML)
 def test_shift_d_preview_and_cancel_are_non_destructive(self):
  self.assertIn("if(key==='d'&&e.shiftKey)",HTML)
  self.assertIn("beginDesktopTransform('move',true)",HTML)
  self.assertIn("if(commitChange&&tr.duplicate)",HTML)
  self.assertIn("if(a.transform)transformLayerPixels(fresh,a.transform)",HTML)
  self.assertIn("if(active?.desktopModal){e.preventDefault();cancelDesktopTransform();return;}",HTML)
 def test_keyboard_help_and_release_metadata(self):
  self.assertIn('Shift</kbd> + <kbd>D',HTML)
  self.assertIn('No click-and-drag is needed', (APP/'README.md').read_text())
  self.assertEqual(json.loads((APP/'version.json').read_text())['version'],'0.1.42')
if __name__=='__main__':unittest.main()
