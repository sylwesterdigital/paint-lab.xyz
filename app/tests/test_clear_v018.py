"""Clear canvas should be reachable on desktop/mobile, safe and undoable."""
import unittest
from pathlib import Path
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
class SafeClearTests(unittest.TestCase):
 def test_accessibility_and_actions(self):
  for ident in ('trashTop','mobileClear','clearAll','clearCanvasOverlay','cancelCanvasClear','confirmCanvasClear','saveBeforeCanvasClear'):
   self.assertIn('id="'+ident+'"',HTML)
  self.assertIn('aria-labelledby="clearCanvasTitle"',HTML)
  self.assertIn("$('clearAll').onclick=openCanvasClear",HTML)
  self.assertIn("$('mobileClear').onclick=",HTML)
 def test_history_and_replay(self):
  self.assertIn("commit({kind:'canvas-clear'",HTML)
  self.assertIn("if(a.kind==='canvas-clear'){clearAllLayerPaint();continue;}",HTML)
  self.assertIn("a.kind==='canvas-clear'?'Clear canvas'",HTML)
  self.assertIn("'canvas-clear'].includes(a.kind)",HTML)
 def test_save_only_after_success(self):
  self.assertIn('pendingClearAfterSave=true',HTML)
  self.assertIn('await storeRecord(record)',HTML)
  self.assertIn('if(clearAfterSave){artId=null',HTML)
  self.assertIn("if(!galleryDb){$('clearCanvasStatus')",HTML)
if __name__=='__main__':unittest.main()
