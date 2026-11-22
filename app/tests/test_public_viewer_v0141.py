"""v0.1.41: public-image viewer uses published artworks, not cloud projects."""
from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from backend import public_viewer

APP=Path(__file__).resolve().parents[1]

class Reader(HTMLParser):
    def __init__(self):
        super().__init__();self.attrs={};self.tags=[]
    def handle_starttag(self,tag,attrs):
        self.tags.append(tag)
        props=dict(attrs)
        if 'id' in props:self.attrs[props['id']]=props

class PublicArtworkViewerTests(unittest.TestCase):
    def slides(self,n=3):
        return [{'token':'x'*20+str(i),'title':f'Artwork {i}',
                 'url':f'/p/{"x"*20}{i}',
                 'image':f'/p/{"x"*20}{i}/image.png'} for i in range(n)]

    def test_height_fitted_image_no_crop_and_responsive_arrows(self):
        css=public_viewer.VIEWER_CSS
        for part in ('height:100dvh','flex:1;min-height:0','object-fit:contain','max-height:100%',
                     '@media(max-width:620px)','touch-action:pan-y','.art-arrow.prev','.art-arrow.next'):
            self.assertIn(part,css)

    def test_slide_markup_urls_initial_selection_and_buttons(self):
        items=self.slides()
        markup=public_viewer.viewer_markup(items,1,'Artist','/u/Artist')
        parser=Reader();parser.feed(markup)
        self.assertEqual(parser.attrs['publicViewer']['data-index'],'1')
        self.assertEqual(json.loads(parser.attrs['publicViewer']['data-slides']),items)
        self.assertEqual(parser.attrs['artImage']['src'],items[1]['image'])
        self.assertEqual(parser.attrs['artDownload']['href'],items[1]['image'])
        self.assertEqual(parser.attrs['artPrev']['aria-label'],'Previous artwork')
        self.assertEqual(parser.attrs['artNext']['aria-label'],'Next artwork')
        self.assertEqual(parser.attrs['artCounter']['aria-live'],'polite')
        self.assertNotIn('hidden',parser.attrs['artNext'])

    def test_single_publication_hides_controls(self):
        markup=public_viewer.viewer_markup(self.slides(1),0,'User','/u/User')
        parser=Reader();parser.feed(markup)
        self.assertIn('hidden',parser.attrs['artPrev'])
        self.assertIn('hidden',parser.attrs['artNext'])

    def test_titles_and_account_names_cannot_inject_html_or_attributes(self):
        items=self.slides(2)
        items[0]['title']='<img src=x onerror=alert(42)> " & \'</script>'
        markup=public_viewer.viewer_markup(items,0,'<svg onload=alert(1)>','/u/Artist')
        parser=Reader();parser.feed(markup)
        self.assertNotIn('<svg',markup)
        self.assertNotIn('<img src=x',markup)
        self.assertNotIn('</script>',markup)
        self.assertNotIn('onerror=',markup.replace('&lt;img src=x onerror=',''))
        self.assertEqual(json.loads(parser.attrs['publicViewer']['data-slides']),items)
        self.assertEqual(parser.tags.count('img'),1)

    def test_js_keyboard_touch_navigation_history_and_lazy_adjacent_image(self):
        js=public_viewer.VIEWER_JS
        for marker in ('ArrowRight','ArrowLeft','touchstart','touchend','touchcancel','popstate',
                       'history.pushState','Math.abs(dx)','new Image()','document.title','addEventListener'):
            self.assertIn(marker,js)
        self.assertNotIn('innerHTML',js)

    def test_backend_selects_only_published_images_by_same_owner(self):
        app=(APP/'backend/app.py').read_text()
        self.assertIn("WHERE owner_id=? ORDER BY created_at DESC,token DESC LIMIT 50",app)
        self.assertIn("'url':url_for('view_publication',token=item['token'])",app)
        self.assertIn("'image':url_for('publication_image',token=item['token'])",app)
        self.assertIn("public_viewer.viewer_markup(slides,active,row['username'],space)",app)
        self.assertIn("script-src 'nonce-",app)
        self.assertIn("frame-ancestors 'none'",app)
        self.assertIn("resp.headers['Cache-Control']='no-store'",app)

if __name__=='__main__':unittest.main()
