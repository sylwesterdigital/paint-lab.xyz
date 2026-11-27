"""v0.1.77: public viewing uses preview assets while downloads preserve the original PNG."""
from __future__ import annotations
import io, tempfile, unittest
from pathlib import Path
from PIL import Image
from backend import public_previews, public_viewer

class PublicPreviewOriginalTests(unittest.TestCase):
 def test_preview_is_distinct_webp_and_smaller_than_original_when_published(self):
  with tempfile.TemporaryDirectory() as root:
   src=Path(root)/'original.png'
   Image.new('RGBA',(1600,1200),'#8844cc').save(src)
   preview=public_previews.make_preview(src, public_previews.preview_path(Path(root),'t'*28))
   with Image.open(preview) as img:
    self.assertEqual(img.format,'WEBP')
    self.assertLessEqual(max(img.size),720)
   self.assertNotEqual(preview.suffix.lower(),src.suffix.lower())
   self.assertLess(preview.stat().st_size, src.stat().st_size)

 def test_public_viewer_shows_preview_but_downloads_original(self):
  slide={'token':'Z'*28,'title':'Shown as preview','url':'/p/'+'Z'*28,'image':'/p/'+'Z'*28+'/image.png','preview':'/p/'+'Z'*28+'/preview.webp'}
  markup=public_viewer.viewer_markup([slide],0,'Artist','/u/artist')
  self.assertIn('id="artImage" src="/p/'+'Z'*28+'/preview.webp"',markup)
  self.assertIn('id="artDownloadFile" href="/p/'+'Z'*28+'/image.png"',markup)
  self.assertIn('Download original PNG',markup)

 def test_simple_gallery_cards_prefer_preview(self):
  markup=public_viewer.gallery_markup([{'url':'/p/x','title':'Example','image':'/p/x/image.png','preview':'/p/x/preview.webp'}],'Artist')
  self.assertIn('src="/p/x/preview.webp"',markup)
  self.assertIn('data-fallback-src="/p/x/image.png"',markup)

if __name__=='__main__':unittest.main()
