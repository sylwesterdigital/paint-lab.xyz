"""Contracts for editable bundled and personal brush collections."""
import unittest
from pathlib import Path
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
class BrushCollections(unittest.TestCase):
 def test_categories(self):
  for title in ['Dry Media','Gouache','Halftones','Manga','Spatter','Watercolour','My Brushes']:
   self.assertIn("'"+title+"'",HTML)
  self.assertIn('const BRUSH_RECIPES=',HTML)
  self.assertIn('function applyBrushRecipe(recipe)',HTML)
 def test_editable_real_paint_settings(self):
  for key in ['size','strength','flow','spacing','scatter']:
   self.assertIn('id="brushEdit_'+key+'"',HTML)
   self.assertIn('source.dispatchEvent(new Event(\'input\'',HTML)
  for button in ['brushSaveNew','brushUpdate','brushRename','brushDelete','brushExport','brushImportFile']:
   self.assertIn('id="'+button+'"',HTML)
  self.assertIn("BRUSH_STORE_KEY='paint-lab-personal-brushes-v1'",HTML)
 def test_share_window_no_public_list(self):
  share=HTML.split('id="shareOverlay"')[1].split('id="helpOverlay"')[0]
  self.assertNotIn('sharePublications',share)
  self.assertNotIn('My published images',share)
  self.assertNotIn('>Done</button>',share)
  self.assertIn('Manage my public gallery',share)
  self.assertIn('sharePublicSpace',share)
if __name__=='__main__':unittest.main()
