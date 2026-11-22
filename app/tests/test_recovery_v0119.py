"""Regression guards for cancellable and raster-cached recovery."""
import unittest
from pathlib import Path
SRC=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
class RecoverySafety(unittest.TestCase):
 def test_user_clear_cancels_legacy_restore(self):
  self.assertIn("function clearCanvasPaint(){\n  if(rendering)return;\n  cancelDraftRecovery('Canvas clear');",SRC)
  self.assertIn("if(epoch!==recoveryEpoch)return false;",SRC)
  self.assertIn("function cancelDraftRecovery(reason",SRC)
 def test_draft_snapshots_match_editable_history(self):
  self.assertIn('const rasterLayers=await captureLayerSnapshot(revision);',SRC)
  self.assertIn("tx.objectStore('drafts').put(record)",SRC)
  self.assertIn('async function restoreRasterSnapshot(draft,epoch)',SRC)
  self.assertIn("if(!cached){bootStage('Restoring drawing · 0%')",SRC)
 def test_old_pre_clear_strokes_are_skipped(self):
  self.assertIn("if(i<lastClear)continue;",SRC)
  self.assertIn("else if(i>=lastClear){",SRC)
 def test_user_can_stop_legacy_replay_safely(self):
  self.assertIn('id="skipRestore"',SRC)
  self.assertIn("title:'Recovery backup · '+new Date().toLocaleString()",SRC)
 def test_ui_and_log_throttling(self):
  self.assertIn('letter-spacing:-.032em;padding:0 .16em .09em',SRC)
  self.assertIn('lastBootLoggedPercent',SRC)
