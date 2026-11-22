"""Cross-artist public feed: isolated SQLite data, sorting, dates and HTML security."""
from __future__ import annotations
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import sqlite3,tempfile,unittest
from backend import db,public_discovery,public_viewer
from deploy import install

FIXED=datetime(2026,11,22,12,0,0,tzinfo=timezone.utc)

class DiscoveryParser(HTMLParser):
    def __init__(self):
        super().__init__();self.images=[];self.links=[];self.forms=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='img':self.images.append(a)
        if tag=='a':self.links.append(a)
        if tag=='form':self.forms.append(a)

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='paintlab_discovery_');self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'db.sqlite3';db.init(self.path)
        self.connection=db.connect(self.path);self.addCleanup(self.connection.close)
        self.a=self.connection.execute("INSERT INTO users(username,password_hash) VALUES('ArtistOne','secret')").lastrowid
        self.b=self.connection.execute("INSERT INTO users(username,password_hash) VALUES('ZebraTwo','secret')").lastrowid
        self.connection.execute("INSERT INTO projects(id,owner_id,title,document) VALUES('private',?,?,?)",(self.a,'Secret hidden canvas','PRIVATE_HISTORY_NEVER_PUBLIC'))
        for token,owner,title,when in (
            ('a'*24,self.a,'Blue % landscape','2026-11-22T08:15:00Z'),
            ('b'*24,self.b,'Yellow hills','2026-11-21T08:15:00Z'),
            ('c'*24,self.a,'Apple tree','2026-11-15T11:00:00Z'),
            ('d'*24,self.b,'Zebra _ sketch','2026-10-21T08:15:00Z')):
            self.connection.execute('INSERT INTO publications(token,owner_id,title,file_name,created_at) VALUES(?,?,?,?,?)',
                (token,owner,title,token+'.png',when))
        self.connection.commit()

    def query(self, params=None):
        return public_discovery.search(self.connection,public_discovery.normalized(params or {}),FIXED)

    def test_newest_combines_accounts_and_never_includes_private_projects(self):
        rows,total,page=self.query()
        self.assertEqual((total,page),(4,1))
        self.assertEqual([row['title'] for row in rows],['Blue % landscape','Yellow hills','Apple tree','Zebra _ sketch'])
        self.assertEqual({row['username'] for row in rows},{'ArtistOne','ZebraTwo'})
        self.assertNotIn('Secret hidden canvas',[row['title'] for row in rows])
        self.assertNotIn('document',rows[0].keys())
        self.assertIsNotNone(self.connection.execute("SELECT name FROM sqlite_master WHERE name='idx_publications_recent'").fetchone())

    def test_title_artist_and_literal_percent_underscore_search(self):
        for search,title in [('blue','Blue % landscape'),('ARTISTONE','Blue % landscape'),('%','Blue % landscape'),('_','Zebra _ sketch')]:
            rows,total,_=self.query({'q':search})
            self.assertIn(title,[row['title'] for row in rows])
        rows,total,_=self.query({'q':'no matching title'})
        self.assertEqual(total,0)
        self.assertEqual(len(rows),0)
        self.assertEqual(len(self.query({'q':'PRIVATE_HISTORY_NEVER_PUBLIC'})[0]),0)

    def test_dates_presets_and_custom_bounds(self):
        tests=[({'period':'today'},['Blue % landscape']),
               ({'period':'week'},['Blue % landscape','Yellow hills']),
               ({'period':'month'},['Blue % landscape','Yellow hills','Apple tree']),
               ({'from':'2026-11-15','to':'2026-11-21'},['Yellow hills','Apple tree']),
               ({'from':'2026-11-23'},[]),
               ({'to':'2026-10-22'},['Zebra _ sketch'])]
        for params,wanted in tests:
            self.assertEqual([row['title'] for row in self.query(params)[0]],wanted,params)

    def test_sort_a_to_z_z_to_a_oldest_artist_and_invalid_input(self):
        for sort,titles in [
            ('az',['Apple tree','Blue % landscape','Yellow hills','Zebra _ sketch']),
            ('za',['Zebra _ sketch','Yellow hills','Blue % landscape','Apple tree']),
            ('oldest',['Zebra _ sketch','Apple tree','Yellow hills','Blue % landscape']),
            ('artist',['Blue % landscape','Apple tree','Yellow hills','Zebra _ sketch'])]:
            self.assertEqual([row['title'] for row in self.query({'sort':sort})[0]],titles)
        f=public_discovery.normalized({'page':'999999','sort':'drop table','period':'oops',
            'from':'2026-99-99','to':'<x>','q':'x'*300})
        self.assertEqual((f.page,f.sort,f.period,f.date_from,f.date_to,len(f.q)),(100,'recent','all','','',100))

    def test_pagination_is_stable_and_bounded(self):
        for i in range(52):
            self.connection.execute('INSERT INTO publications(token,owner_id,title,file_name,created_at) VALUES(?,?,?,?,?)',
                (f'p{i:023}',self.a,f'Extra {i}',f'p{i}.png',f'2026-11-22T11:{i:02}:00Z'))
        self.connection.commit()
        first,total,page=self.query({'page':'1'})
        second,_,page2=self.query({'page':'2'})
        self.assertEqual(total,56)
        self.assertEqual((len(first),len(second),page,page2),(48,8,1,2))
        self.assertFalse(set(r['token'] for r in first)&set(r['token'] for r in second))
        self.assertEqual(self.query({'page':'9999'})[2],2)

    def test_safe_uncropped_html_and_external_collaboration_link(self):
        filters=public_discovery.normalized({'q':'<svg onload=alert(1)>'})
        item={'url':'/p/abc','image':'/p/abc/image.png','artist_url':'/u/ArtistOne',
              'username':'ArtistOne','title':'<svg onload=alert(1)>&','created_at':'2026-11-22T12:00:00Z'}
        urls={'period':{key:'/explore?period='+key for key in public_discovery.PERIODS},'prev':None,'next':None}
        markup=public_viewer.discover_markup([item],filters,1,1,urls)
        parser=DiscoveryParser();parser.feed(markup)
        self.assertEqual(len(parser.images),1)
        self.assertEqual(parser.images[0]['alt'],item['title'])
        self.assertNotIn('<svg onload',markup)
        self.assertIn('&lt;svg onload=',markup)
        self.assertIn('&lt;svg',markup)
        self.assertIn('name="sort"',markup)
        self.assertIn('type="date"',markup)
        self.assertIn('https://rantlist.me/',markup)
        self.assertTrue(any(a.get('href')=='https://rantlist.me/' and 'noopener' in a.get('rel','') for a in parser.links))
        self.assertEqual(parser.forms,[{'class':'discovery-form','action':'/explore','method':'get'}]*2)
        self.assertIn('.discovery-wall{columns:270px',public_viewer.DISCOVER_CSS)
        self.assertIn('height:auto;object-fit:contain',public_viewer.DISCOVER_CSS)

    def test_explore_viewer_switches_artist_and_can_return_to_search(self):
        slides=[{'token':'a'*24,'title':'First art','url':'/p/'+'a'*24+'?browse=explore',
                 'image':'/p/'+'a'*24+'/image.png','username':'ArtistOne','artist_url':'/u/ArtistOne'},
                {'token':'b'*24,'title':'Second art','url':'/p/'+'b'*24+'?browse=explore',
                 'image':'/p/'+'b'*24+'/image.png','username':'ZebraTwo','artist_url':'/u/ZebraTwo'}]
        markup=public_viewer.viewer_markup(slides,0,'ArtistOne','/u/ArtistOne',gallery_url='/explore?q=blue')
        parser=DiscoveryParser();parser.feed(markup)
        self.assertIn('id="artCreator"',markup)
        self.assertIn('href="/explore?q=blue"',markup)
        self.assertIn('creator.textContent = item.username',public_viewer.VIEWER_JS)
        self.assertIn('creator.href = item.artist_url',public_viewer.VIEWER_JS)
        self.assertIn("slide.url.split('?')[0]",public_viewer.VIEWER_JS)
        server=(Path(__file__).resolve().parents[1]/'backend/app.py').read_text()
        self.assertIn("request.args.get('browse')=='explore'",server)
        self.assertIn("gallery_url=url_for('discover_artworks',**query_args)",server)
        self.assertIn("browse='explore',**query_args",server)

    def test_nginx_and_studio_public_entry_points(self):
        self.assertIn('location = /explore {',install.NGINX)
        self.assertIn('location ^~ /explore/ {',install.NGINX)
        self.assertIn('/explore/paintlabunknownroute9999',install.PUBLIC_ROUTE_PROBES)
        source=(Path(__file__).resolve().parents[1]/'backend/app.py').read_text()
        self.assertIn("@app.get('/explore')",source)
        self.assertIn('public_discovery.search(con(),filters)',source)
        frontend=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
        self.assertIn('href="/explore"',frontend)
        self.assertIn('Explore public gallery',frontend)
        self.assertIn('https://rantlist.me/',frontend)

if __name__=='__main__':unittest.main()
