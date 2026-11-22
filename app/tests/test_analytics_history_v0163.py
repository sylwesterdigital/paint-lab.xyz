"""Release contracts for idle Umami and the bounded mobile raster undo path."""
from pathlib import Path
import unittest

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
SERVER=(APP/'backend/app.py').read_text()

class AnalyticsHistory163(unittest.TestCase):
 def test_umami_uses_configured_identity_and_non_blocking_load(self):
  self.assertIn('https://analytics.mielniczuk.com/script.js',HTML)
  self.assertIn('bd5f9b1c-f457-47a5-81e6-e7bbe57bca9d',HTML)
  self.assertIn('requestIdleCallback(start,{timeout:2400})',HTML)
  self.assertIn('tag.async=true',HTML)
  self.assertIn('tag.onerror=()=>{attempted=false;tag.remove();};',HTML)
  self.assertIn("document.visibilityState==='hidden'",HTML)
  self.assertIn('sent>=40',HTML)
  self.assertIn("typeof window.umami?.track!=='function'",HTML)
  self.assertNotIn('JSON.stringify(projectData())',HTML.split('const ALLOWED=',1)[1].split('})();',1)[0])
  self.assertIn('https://analytics.mielniczuk.com',SERVER)
  self.assertIn("window.addEventListener(\"load\"",SERVER)
  self.assertIn("script-src 'nonce-",SERVER)
  self.assertIn("connect-src 'self' https://analytics.mielniczuk.com",SERVER)

 def test_analytics_custom_events_are_coarse_and_only_after_success(self):
  for event in ('gallery_opened','artwork_opened','artwork_saved','artwork_published','artwork_exported','painting_mode_changed','stylization_changed','effects_changed'):
   self.assertIn("'"+event+"'",HTML)
  self.assertIn("paintLabTrack('artwork_saved',{destination:'local'",HTML)
  self.assertIn("paintLabTrack('artwork_published',{destination:'public'});",HTML)
  self.assertNotIn('paintLabTrack(\'stroke\'',HTML)

 def test_bounded_history_preserves_all_project_actions(self):
  self.assertIn('HISTORY_SETTINGS=Object.freeze({undoSteps:20,patchMemoryMB:48})',HTML)
  self.assertIn('function historyUndoFloor()',HTML)
  self.assertIn('function rememberStrokePixelPatch(action)',HTML)
  self.assertIn('function restoreStrokePixelPatch(action,toBefore)',HTML)
  self.assertIn('if(restoreStrokePixelPatch(last,true))',HTML)
  self.assertIn('if(restoreStrokePixelPatch(next,false))',HTML)
  self.assertIn('if(a.touchRollback){rememberStrokePixelPatch(a);delete a.touchRollback;}',HTML)
  self.assertIn('actions:actions.map(a=>',HTML)
  self.assertIn('const next=clamp(pos,historyUndoFloor(),actions.length)',HTML)
  self.assertIn('if(head<=historyUndoFloor()||active||rendering)return;',HTML)
  self.assertIn('if(historyCheckpointValid(s,target)',HTML)

if __name__=='__main__':unittest.main()
