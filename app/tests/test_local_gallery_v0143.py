"""Browser-local gallery cards should open artwork directly, keeping edit tools separate."""
from pathlib import Path
import re
import unittest

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()

class LocalGalleryV0143Tests(unittest.TestCase):
    def test_cards_are_image_first_and_uncropped(self):
        for s in ('.artcard-open{position:absolute;inset:0;',
                  '.artcard-title{', 'background:linear-gradient(',
                  '.galleryGrid{display:grid;', '.artcard img{width:100%;height:auto;object-fit:contain',
                  'className=\'artcard-open\'', "open.setAttribute('aria-label','Open artwork: '",
                  "open.append(title)", 'card.append(frame,open)'):
            self.assertIn(s,HTML)
        self.assertNotIn('className=\'artcard-main\'',HTML)
        gallery=HTML[HTML.index("async function renderGallery()"):HTML.index("function validateData(",HTML.index("async function renderGallery()"))]
        self.assertNotIn("open.textContent='Open'",gallery)

    def test_gallery_open_and_edit_actions_remain_isolated(self):
        code=HTML[HTML.index('async function renderGallery()'):HTML.index('function validateData(',HTML.index('async function renderGallery()'))]
        self.assertIn("open.onclick=async()=>",code)
        self.assertIn('loadProject(item.data,item.id)',code)
        self.assertIn("hideModal('galleryOverlay')",code)
        self.assertIn('if(edit){',code)
        self.assertIn('rename.onclick=async()=>',code)
        self.assertIn('trash.onclick=async()=>',code)
        self.assertIn('confirmAction(`Delete',code)
        self.assertIn("buttons.append(rename,trash);card.append(buttons);",code)
        self.assertIn('type=\'button\'',code)

    def test_project_format_and_public_gallery_are_unaffected(self):
        self.assertIn("format:'paint-lab-webgl',version:4",HTML)
        self.assertIn('id="galleryEdit"',HTML)
        self.assertIn('class="dialog gallery-dialog"',HTML)

if __name__=='__main__':unittest.main()
