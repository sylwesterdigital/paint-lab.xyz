"""Native-proportion IndexedDB gallery and scoped browser-local filter contracts."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend/index.html').read_text()
class LocalMasonryV0151Tests(unittest.TestCase):
 def test_release_versions_and_changelog(self):
  data=json.loads((ROOT/'changelog.json').read_text())
  self.assertEqual(data['version'],'0.1.63')
  self.assertEqual(data['history'][0]['version'],'0.1.62')
  self.assertIn('<meta name="paint-lab-version" content="0.1.63">',HTML)
 def test_native_ratio_thumbnail_and_legacy_preservation(self):
  for fragment in ('const src=createExportCanvas(true),scale=Math.min(520/src.width,520/src.height,1);',
    'c.height=Math.max(1,Math.round(src.height*scale))',
    'const w=Number(item.data?.baseW),h=Number(item.data?.baseH);',
    'frame.style.aspectRatio=`${w} / ${h}`;',
    'frame.append(pic)',
    'const cols=Array.from({length:colCount}',
    '.gallery-masonry-column{display:flex;flex-direction:column;flex:1;',
    '#galleryOverlay .artcard-image img{display:block;width:100%;height:100%;object-fit:fill;'):
   self.assertIn(fragment,HTML)
  self.assertNotIn('c.width=360;c.height=220;',HTML)
 def test_filters_and_owner_edit(self):
  for fragment in ('id="gallerySearch"','id="gallerySort"','id="galleryFrom"',
       'id="galleryTo"','id="galleryResetFilters"','data-gallery-period="all"',
       'data-gallery-period="today"','data-gallery-period="week"','data-gallery-period="month"',
       "function galleryFilterRecords(records)","if(edit){",
       "open.onclick=()=>openSavedGalleryArtwork(item)", "rename.onclick=async()=>", "trash.onclick=async()=>",
       "openSavedGalleryArtwork(item)","hideModal('galleryOverlay')",
       "window.addEventListener('resize',()=>{if($('galleryOverlay').classList.contains('visible'))renderGallery();});"):
   self.assertIn(fragment,HTML)
  self.assertIn('confirmAction(`Delete',HTML)
 def test_project_format_unchanged(self):
  self.assertIn("format:'paint-lab-webgl',version:4",HTML)
  self.assertIn("galleryDb.transaction('artworks','readwrite')",HTML)
if __name__=='__main__':unittest.main()
