"""v0.1.79: compact gradient presets, visible Bounce switch and public wordmark."""
from pathlib import Path
import unittest
from backend import public_viewer

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text(encoding='utf-8')
SERVER=(APP/'backend/app.py').read_text(encoding='utf-8')

class PalettePresetsGalleryBrandTests(unittest.TestCase):
 def test_bounce_matches_flow_switch(self):
  self.assertIn('class="palette-travel-toggle"',HTML)
  self.assertIn('class="palette-travel-toggle palette-bounce-toggle"',HTML)
  for toggle in ('paletteTravel','palettePingPong'):
   self.assertIn('id="'+toggle+'" role="switch"',HTML)
  self.assertIn('#palettePanel .palette-travel-toggle input:checked:after{transform:translateX(12px)}',HTML)
  self.assertIn('colorTravelPingPong=e.target.checked;schedulePersist()',HTML)
 def test_custom_gradient_presets_are_editable_persistent_and_deletable(self):
  for marker in ('id="saveGradientPreset"','id="gradientPresets"',
                 "const GRADIENT_PRESETS_KEY='paint-lab-gradient-presets-v1'",
                 'normalizeGradientAnchors(preset.anchors)',
                 'localStorage.setItem(GRADIENT_PRESETS_KEY,JSON.stringify(customGradientPresets))',
                 "gradientAnchors=normalizeGradientAnchors(preset.anchors)",
                 "confirmAction('Delete this saved gradient?",
                 "function saveGradientPreset()"):
   self.assertIn(marker,HTML)
  self.assertNotIn('palette-gradient-name',HTML)
  self.assertIn('const tile=document.createElement(\'div\');tile.className=\'palette-gradient-item\';',HTML)
  self.assertIn('grid-template-columns:repeat(var(--palette-cols,6),minmax(0,1fr))',HTML)
  self.assertNotIn("await inputAction('Save custom gradient'",HTML)
  self.assertIn('preview.style.background=\'linear-gradient(90deg,\'',HTML)
 def test_public_gallery_and_viewer_use_editor_brand_wordmark(self):
  for marker in ('nav .paint-lab-wordmark','linear-gradient(100deg,#ed92ab 3%,#af9fee 29%,#91c4d8 53%,#9fcda8 77%,#edbc8c 100%)',
                 '-webkit-background-clip:text','font-size:28px','font-weight:850'):
   self.assertIn(marker,public_viewer.BASE_CSS)
  self.assertIn('<a class="paint-lab-wordmark" href="/" aria-label="Paint Lab home">Paint-lab</a>',SERVER)
  self.assertIn('class="paint-lab-wordmark" href="/"',HTML)
  self.assertIn('href="/explore">Explore art</a>',SERVER)

if __name__=='__main__':unittest.main()
