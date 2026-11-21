"""Contracts for full layer-reset, legacy migration and stable oil pigment."""
import unittest
from pathlib import Path
S=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
class CleanCanvasReset(unittest.TestCase):
 def test_reset_commits_full_layer_delete(self):
  self.assertIn("commit({kind:'canvas-clear',resetLayers:true",S)
  self.assertIn("layers=[createLayer({id:'base-layer',name:'Background paint'})]",S)
  self.assertIn("selectedLayerIds=new Set(['base-layer'])",S)
 def test_replay_keeps_legacy_compatible(self):
  self.assertIn("if(a.resetLayers)resetCanvasLayers();else clearAllLayerPaint();",S)
  self.assertIn("for(let i=lastReset+1;i<head;i++)",S)
 def test_dialog_clear_describes_layer_deletion(self):
  self.assertIn('Delete the painting and all existing layers.',S)
class OilCleanPigment(unittest.TestCase):
 def test_original_underpainting_only(self):
  self.assertIn('function cacheOilUnderlay(run,x0,y0,x1,y1)',S)
  self.assertIn('const source=originalOilPigment(run,ix+x0,iy+y0)',S)
  self.assertIn('const deposited=pigment;',S)
  self.assertNotIn('br.rgb[ch]=reflectance(br.rgb[ch],pixels[centre+ch]',S)
 def test_bounded_colouroptical_pickup(self):
  self.assertIn('OIL_UNDERLAY_LIMIT=96',S)
  self.assertIn('const budget=(.04+.28*wet)*(.92-.56*load);',S)
