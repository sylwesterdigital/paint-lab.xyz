"""Mobile canvas rotation must remain available while aspect and touch mapping stay stable."""
from pathlib import Path
import unittest,json

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'frontend/index.html').read_text()
class MobileRotation160(unittest.TestCase):
 def test_version(self):
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.73')
 def test_default_rotation_and_explicit_opt_out(self):
  self.assertIn('rotateCanvas:true',SRC)
  self.assertIn('if(!data.rotationUserSet)mobileOptions.rotateCanvas=true',SRC)
  self.assertIn('rotationUserSet:mobileRotationExplicit',SRC)
  self.assertIn('if(!isMobileWorkspace()||mobileOptions.rotateCanvas){',SRC)
 def test_no_surprise_straighten_after_layout_or_resume(self):
  self.assertNotIn('if(on&&!mobileOptions.rotateCanvas&&view.angle)',SRC)
  self.assertNotIn('if(!mobileOptions.rotateCanvas)view.angle=0',SRC)
  self.assertNotIn('if(isMobileWorkspace()&&!mobileOptions.rotateCanvas)view.angle=0',SRC)
  self.assertIn('gesture.startingView',SRC)
 def test_screen_aspect_matches_actual_canvas(self):
  self.assertIn('const bounds=preview.getBoundingClientRect();',SRC)
  self.assertIn('vW=Math.max(1,bounds.width||innerWidth);vH=Math.max(1,bounds.height||innerHeight)',SRC)
  self.assertIn('viewScaleX=viewScaleY=1',SRC)
  self.assertIn('(e.clientX-r.left)*vW/Math.max(1,r.width)',SRC)
  self.assertIn('function applyContext(ctx)',SRC)
if __name__=='__main__':unittest.main()
