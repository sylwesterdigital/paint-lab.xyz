"""v0.1.42 public galleries must preserve all image aspect ratios in masonry."""
from __future__ import annotations
import html
import unittest
from html.parser import HTMLParser
from pathlib import Path
from backend import public_viewer

APP = Path(__file__).resolve().parents[1]


class GalleryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images=[]
        self.articles=0
        self.links=[]
        self.main=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='img': self.images.append(a)
        if tag=='article': self.articles+=1
        if tag=='a': self.links.append(a.get('href'))
        if tag=='main' and a.get('id')=='publicGallery': self.main=True


class PublicMasonryGalleryTests(unittest.TestCase):
    def test_responsive_columns_keep_unforced_natural_ratio(self):
        css=public_viewer.BASE_CSS
        for marker in ('.gallery-page main{max-width:none',
                       '.gallery{columns:280px', 'column-gap:',
                       'break-inside:avoid', 'width:100%;height:auto',
                       'aspect-ratio:auto', 'object-fit:contain',
                       '@media(max-width:480px){.gallery{columns:1}'):
            self.assertIn(marker,css)
        for forbidden in ('object-fit:cover','aspect-ratio:4/3','grid-template-columns:'):
            self.assertNotIn(forbidden,css)

    def test_gallery_markup_renders_one_uncropped_link_per_published_image(self):
        entries=[{'url':f'/p/{"x"*20}{i}',
                  'image':f'/p/{"x"*20}{i}/image.png',
                  'title':f'Art {i}'} for i in range(4)]
        markup=public_viewer.gallery_markup(entries,'Test Artist')
        parser=GalleryParser();parser.feed(markup)
        self.assertTrue(parser.main)
        self.assertEqual(parser.articles,4)
        self.assertEqual([e['src'] for e in parser.images],[e['image'] for e in entries])
        self.assertEqual([e['alt'] for e in parser.images],[e['title'] for e in entries])
        self.assertEqual(parser.links,[e['url'] for e in entries])
        self.assertTrue(all(e['loading']=='lazy' and e['decoding']=='async' for e in parser.images))
        self.assertNotIn('width=',markup)
        self.assertNotIn('height=',markup)

    def test_public_gallery_is_escaped_and_empty_state_has_main(self):
        malicious='<svg onload=alert(1)>"&'
        data=[{'url':'/p/'+malicious,'image':'/p/safe/image.png','title':malicious}]
        markup=public_viewer.gallery_markup(data,malicious)
        self.assertNotIn('<svg',markup)
        self.assertIn(html.escape(malicious,quote=True),markup)
        parser=GalleryParser();parser.feed(markup)
        self.assertEqual(parser.articles,1)
        self.assertEqual(len(parser.images),1)
        empty=public_viewer.gallery_markup([],malicious)
        parser=GalleryParser();parser.feed(empty)
        self.assertTrue(parser.main)
        self.assertIn('No artworks have been published yet.',empty)

    def test_public_route_uses_shared_markup_and_scoped_page(self):
        app=(APP/'backend/app.py').read_text()
        self.assertIn('public_viewer.discover_markup(items,filters,total,page,urls,',app)
        self.assertIn("gallery=True,manage=edit)",app)
        self.assertIn('gallery-page',app)
        self.assertIn("'image':url_for('owner_publication_image',token=r['token']) if edit else url_for('publication_image',token=r['token'])",app)
        self.assertIn("'url':url_for('view_publication',token=r['token'])",app)

if __name__=='__main__': unittest.main()
