"""v0.1.53 mobile edge brush rail and category tip-picker contracts."""
import unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()

class MobileBrushV152(unittest.TestCase):
    def test_edge_rail_no_background_and_coloured_thumb(self):
        self.assertIn('left:calc(0px + env(safe-area-inset-left,0px))!important;',HTML)
        self.assertIn('background:transparent!important;border:0!important;box-shadow:none!important;',HTML)
        self.assertIn('background:var(--brush-color,#b64b42)!important;',HTML)
        self.assertIn("slider.style.setProperty('--brush-color',color)",HTML)
    def test_real_tip_preview_and_no_paint_writes(self):
        self.assertIn('id="mobileBrushActualTip"',HTML)
        self.assertIn('function drawMobileActualTip()',HTML)
        self.assertIn('size*Math.max(.1,view.zoom||1)',HTML)
        self.assertIn('tintCustomTip(tip,color)',HTML)
        self.assertIn('tipSilhouette(ctx,tip,radius,',HTML)
        body=HTML.split('function drawMobileActualTip(){',1)[1].split('\nfunction showMobileBrushSizePreview()',1)[0]
        self.assertNotIn('markPaint(',body)
        self.assertNotIn('addAction(',body)
    def test_tip_icon_replaces_next_tip_caption(self):
        self.assertIn('id="mobileBrushImage"',HTML)
        self.assertNotIn('<span>Next tip</span>',HTML)
        self.assertIn('id="mobileTipCycle"',HTML)
        self.assertNotIn('id="mobileBrushNext"',HTML)
        self.assertIn('aria-label="Open brush size and tip controls"',HTML)
    def test_long_hold_deferred_until_synthetic_touch_click_ends(self):
        self.assertIn('holdTimer=setTimeout(()=>{holdTimer=null;held=true;},500)',HTML)
        self.assertIn('setTimeout(()=>openMobileTipGallery(),130)',HTML)
        self.assertIn("const button=$('mobileTipCycle')",HTML)
        self.assertIn("if(held||skipTouchClick){e.preventDefault();held=false;skipTouchClick=false;return;}mobileNextTip()",HTML)
    def test_filtered_tip_gallery(self):
        for id in ['mobileTipGallery','mobileTipGalleryCategories','mobileTipGalleryGrid','mobileTipGalleryClose']:
            self.assertIn('id="'+id+'"',HTML)
        self.assertIn('for(const n of TIP_CATEGORIES)',HTML)
        self.assertIn("category:'My Brushes'",HTML)
        self.assertIn('const category=key.startsWith(',HTML)
        self.assertIn('if(entry.recipe)applyBrushRecipe(entry.recipe)',HTML)

if __name__=='__main__':unittest.main()
