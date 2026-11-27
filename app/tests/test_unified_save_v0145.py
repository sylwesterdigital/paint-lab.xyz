"""Contracts for explicit Save & Share actions introduced in v0.1.45."""
import json,re,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=(ROOT/'frontend/index.html').read_text()

class UnifiedSaveTests(unittest.TestCase):
 def test_version_history(self):
  current=json.loads((ROOT/'changelog.json').read_text())
  self.assertEqual(current['version'],'0.1.76')
  self.assertEqual(current['history'][0]['version'],'0.1.75')

 def test_each_destination_is_explicit(self):
  for button in ('saveNew','saveOverwrite','savePublish','savePNGWith','savePNGWithout','saveZIP','saveJSON','saveNativeShare'):
   self.assertRegex(PAGE,rf'id="{button}"')
  self.assertIn("$('saveNew').onclick=()=>saveGallery(true)",PAGE)
  self.assertIn("$('saveOverwrite').onclick=()=>saveGallery(false)",PAGE)
  self.assertIn("if(!asNew&&(!artId||pendingClearAfterSave))",PAGE)
  self.assertNotIn('Overwrite saved artwork</h2>',PAGE)
  self.assertNotIn("$('confirmSave').onclick=saveGallery",PAGE)

 def test_publication_is_separate_image_only_action(self):
  self.assertIn('async function publishFromSave()',PAGE)
  self.assertIn("sharePNGBlob(true,$('savePublishBackground').checked)",PAGE)
  self.assertIn("apiCall('/publications','POST',{title:name,image:await blobAsDataURL(image)})",PAGE)
  self.assertIn("setPublishedSaveLink(result)",PAGE)
  self.assertIn("$('saveCopyLink').onclick=copyPublicLinkFromSave",PAGE)
  self.assertIn("if(!cloudUser){saveHubStatus('Sign in",PAGE)

 def test_exports_and_save_before_clear(self):
  self.assertIn("$('saveJSON').onclick=exportJSON",PAGE)
  self.assertIn("$('saveZIP').onclick=exportProjectZIP",PAGE)
  self.assertIn("$('saveNativeShare').onclick=shareFromSave",PAGE)
  self.assertIn("if(clearAfterSave){artId=null;artName='Untitled painting'",PAGE)
  self.assertIn("if($('saveOverlay').classList.contains('visible'))doc.title",PAGE)
  self.assertIn('Save as new. The canvas clears only after',PAGE)

if __name__=='__main__':unittest.main()
