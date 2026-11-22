"""Mobile Explore must prioritise new artwork while retaining no-JS search."""
from __future__ import annotations
from html.parser import HTMLParser
import unittest
from backend import public_discovery,public_viewer

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[]
    def handle_starttag(self,tag,attrs):
        value=dict(attrs).get('id')
        if value:self.ids.append(value)

class MobileDiscoveryTests(unittest.TestCase):
    def make(self,params=None,artist=None,page=1,n=8):
        f=public_discovery.normalized(params or {})
        items=[{'title':f'Art {i}', 'url':f'/p/{i}', 'image':f'/p/{i}/image.png',
                'username':f'Artist{i%3}', 'artist_url':f'/u/Artist{i%3}',
                'created_at':'2026-11-22T12:00:00Z'} for i in range(n)]
        urls={'period':{k:'/explore?period='+k for k in public_discovery.PERIODS},'prev':None,'next':None}
        return public_viewer.discover_markup(items,f,n,page,urls,artist=artist)
    def test_default_has_four_recent_previews_then_full_masonry(self):
        markup=self.make()
        self.assertIn('class="discovery-wall discovery-featured-mode"',markup)
        self.assertEqual(markup.count('class="discovery-tile'),8)
        self.assertIn('<h2 class="discovery-more-label">More artwork</h2>',markup)
        self.assertLess(markup.index('Art 3'),markup.index('More artwork'))
        self.assertLess(markup.index('More artwork'),markup.index('Art 4'))
        self.assertIn('fetchpriority="high"',markup)
        self.assertIn('.discovery-featured-mode>.discovery-tile:nth-of-type(n+5){grid-column:1/-1}',public_viewer.DISCOVER_CSS)
        self.assertIn('object-fit:contain;max-height:none',public_viewer.DISCOVER_CSS)
    def test_filter_search_and_later_pages_do_not_show_featured_block(self):
        for params,artist,page in [({'q':'Blue'},None,1),({'sort':'az'},None,1),
                                   ({'period':'week'},None,1),({'from':'2026-11-20'},None,1),
                                   ({},None,2),({},'ArtistOne',1)]:
            html=self.make(params,artist,page)
            self.assertNotIn('discovery-featured-mode',html,(params,artist,page))
            self.assertNotIn('More artwork</h2>',html)
    def test_mobile_filters_disclosed_by_native_details_without_javascript(self):
        markup=self.make()
        self.assertIn('<details class="discovery-mobile-controls">',markup)
        self.assertIn('<summary aria-label="Search and filter artworks">',markup)
        self.assertIn('<div class="discovery-desktop-controls">',markup)
        self.assertIn('id="discoverQueryMobile"',markup)
        self.assertIn('id="discoverQuery"',markup)
        self.assertIn('id="discoverSortMobile"',markup)
        parser=IdParser();parser.feed(markup)
        self.assertEqual(len(parser.ids),len(set(parser.ids)))
        filtered=self.make({'q':'<test>&','sort':'az'})
        self.assertIn('Search & filters · Active',filtered)
        self.assertIn('value="&lt;test&gt;&amp;"',filtered)
        self.assertNotIn('value="<test>&"',filtered)
    def test_short_feed_and_own_gallery_still_have_invitation_or_owner_controls(self):
        self.assertIn('discovery-mobile-invite',self.make(n=3))
        owner=self.make(artist='ArtistOne')
        self.assertNotIn('discovery-mobile-controls',owner)
        self.assertIn('class="discovery-form"',owner)

if __name__=='__main__':unittest.main()
