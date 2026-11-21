"""Regression contracts: pigment selection must change actual stamp pixels, not merely the UI."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'frontend/index.html').read_text()
class PigmentRenderingTests(unittest.TestCase):
 def test_materials_have_separate_pixel_algorithms(self):
  start=JS.index('function materialStampTexture(')
  end=JS.index('function paintTip(',start)
  part=JS[start:end]
  for condition in ("mat==='pencil'","mat==='chalk'","mat==='watercolor'","else{ // OIL"):
   self.assertIn(condition,part)
  for signature in ('graphite','patches','edgePool','groove','backrun'):
   self.assertIn(signature,part)
  self.assertIn('g.putImageData(pixels,0,0)',part)
  self.assertIn('PIGMENT_STAMP_CACHE.set(cacheKey,result)',part)
 def test_one_texture_creation_per_selected_tip_colour_material(self):
  start=JS.index('function paintTip(')
  end=JS.index('function sampleColor(',start)
  part=JS[start:end]
  self.assertIn('materialStampTexture(mat,t,col,conf)',part)
  self.assertIn('ctx.drawImage(stamp',part)
  self.assertNotIn('createImageData',part)
 def test_material_selection_is_recorded_with_each_stroke(self):
  self.assertIn('function snapshot(){return {color,mode,tip,material,strokeStyle,styleCell,styleAmount,size,',JS)
  self.assertIn('replayStroke(s)',JS)
  self.assertIn('function chooseMaterial(next)',JS)
  self.assertIn('const custom=tintCustomTip(t,col)',JS)
if __name__=='__main__':unittest.main()
