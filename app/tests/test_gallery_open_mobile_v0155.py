"""Version 0.1.55 browser-open and independently reachable mobile tool controls."""
from pathlib import Path
import json
import unittest
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class GalleryOpeningMobile155(unittest.TestCase):
 def test_busy_overlay_and_incremental_replay(self):
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.57')
  for marker in ('id="artworkOpening" hidden role="status"','function showArtworkOpening(title)',
   'await nextPaintFrame();await nextPaintFrame();',
   'rebuildHistoryWithoutBlocking({opening:true,onProgress:setArtworkOpeningProgress',
   'if((item.point&31)===0&&performance.now()-start>budget)break;',
   'function hideArtworkOpening()'):
   self.assertIn(marker,HTML)
 def test_single_brush_launcher_cycles_when_size_is_open(self):
  for marker in ('id="mobileBrush"','id="mobileBrushLauncherImage"',
   'id="mobileSizeSlider"','function handleMobileBrushTap()',
   'function initMobileBrushController()','function initMobileSizeSlider()'):
   self.assertIn(marker,HTML)
  launcher=HTML.split('id="mobileBrushTop"',1)[1].split('</div>',1)[0]
  self.assertEqual(launcher.count('<button'),1)
  popover=HTML.split('id="mobileBrushPopover" class=',1)[1].split('</div>\n    <div id="mobileBrushSizePreview"',1)[0]
  self.assertNotIn('<button',popover)
  self.assertNotIn('id="mobileTipCycle"',HTML)
  self.assertIn('mobileNextTip();showMobileBrushSizePreview();',HTML)
 def test_active_names_and_icons_remain_in_the_buttons(self):
  for marker in ('id="mobileEffects"','id="mobileStylize"','mobile-icon-choice',
   "setMobileModeTile('mobileEffects',effectText","setMobileModeTile('mobileStylize',styleText",
   'function announceMobileChoice(kind,value)'):
   self.assertIn(marker,HTML)
if __name__=='__main__':unittest.main()
