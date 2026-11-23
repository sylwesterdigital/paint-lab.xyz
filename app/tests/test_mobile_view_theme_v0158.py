"""Regression contracts for mobile view integrity and appearance controls (v0.1.58)."""
from pathlib import Path
import json,unittest

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()

class MobileViewAndThemes158(unittest.TestCase):
 def test_release_and_app_history(self):
  data=json.loads((APP/'changelog.json').read_text())
  self.assertEqual(data['version'],'0.1.67')
  self.assertEqual(data['history'][0]['version'],'0.1.66')
  self.assertIn('<meta name="paint-lab-version" content="0.1.67">',HTML)
 def test_mobile_border_and_shadow_reach_zero(self):
  for marker in ('--pl-border-alpha','root.dataset.plBorders=uiAppearance.border===0',
    "root.dataset.plShadows=uiAppearance.shadows&&uiAppearance.shadowStrength>0",
    ':root.mobile-workspace .mobile-bottom .mobile-ui-button',
    ':root[data-pl-shadows="off"].mobile-workspace',
    ':root[data-pl-borders="off"].mobile-workspace',
    'shadowStrength:clamp(Number(data.shadowStrength??defaults.shadowStrength),0,100)'):
   self.assertIn(marker,HTML)
 def test_star_generates_another_theme(self):
  for marker in ('id="generateTheme"','aria-label="Generate another interface theme"',
    '<use href="#pl-star"/>','function generateAlternativeTheme()',
    "$('generateTheme').onclick=generateAlternativeTheme",
    "localStorage.setItem('paint-lab-generated-theme-seed'", "setTheme('generated')"):
   self.assertIn(marker,HTML)
 def test_interrupted_gestures_and_default_rotation(self):
  for marker in ('rotateCanvas:true','if(!data.rotationUserSet)mobileOptions.rotateCanvas=true',
    'mobileRotationExplicit=true;', 'gesture.startingView',
    "window.addEventListener('pageshow'",'function recoverMobileViewport()',
    "document.addEventListener('visibilitychange'",'window.visualViewport.addEventListener'):
   self.assertIn(marker,HTML)
 def test_touch_coordinates_consistent_with_displayed_canvas(self):
  for marker in ('function pointerScreenPosition(e)',
    '(e.clientX-r.left)*vW/Math.max(1,r.width)',
    '(e.clientY-r.top)*vH/Math.max(1,r.height)',
    'function getPoint(e){const pos=pointerScreenPosition(e)',
    'function touchPointRecord(e){return pointerScreenPosition(e);}',
    'const {x,y}=pointerScreenPosition(e)'):
   self.assertIn(marker,HTML)

if __name__=='__main__':unittest.main()
