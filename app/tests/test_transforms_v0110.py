"""Document-coordinate transformation, mobile gesture routing, release contracts."""
import unittest
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'frontend/index.html').read_text()
class TestTransforms(unittest.TestCase):
 def test_clone_uses_raw_pixels(self):
  self.assertIn('fresh.ctx.setTransform(1,0,0,1,0,0)',JS)
  self.assertIn("fresh.ctx.drawImage(l.canvas,0,0)",JS)
 def test_transform_action_replay(self):
  self.assertIn("a.kind==='layer-transform'",JS)
  self.assertIn("function transformLayerPixels(target,spec)",JS)
  self.assertIn("function transformShapeValue(shape,spec)",JS)
  self.assertIn("layerAction({kind:'layer-transform'",JS)
  self.assertIn("'layer-order','layer-transform','canvas-clear'",JS)
  self.assertIn('Invalid layer transform',JS)
 def test_touch_canvas_vs_artwork(self):
  self.assertIn("if(transformMode&&startObjectGesture(pair,a,b))",JS)
  self.assertIn("gesture.kind==='object'",JS)
  self.assertIn("function moveObjectGesture(a,b)",JS)
  self.assertIn("mobileOptions.rotateCanvas",JS)
  self.assertIn("const v=gesture.accumulated,dead=.025",JS)
 def test_touch_buttons_and_hotkeys(self):
  for name in ('move','rotate','scale'):
   self.assertIn('data-transform="'+name+'"',JS)
  self.assertIn("if(['g','r','s'].includes(key)&&!e.shiftKey)",JS)
  self.assertIn('id="mobileTransforms"',JS)
 def test_versions(self):
  self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'0.1.49')
  self.assertIn('<meta name="paint-lab-version" content="0.1.49">',JS)
