#!/usr/bin/env python3
"""Offline Chromium smoke: combined public discovery, filters and mobile masonry."""
from __future__ import annotations
import base64,io,sqlite3,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from backend import db,public_discovery,public_viewer

sizes=[(400,720),(840,240),(600,600),(600,900),(900,350),(450,620)]
images=[]
for i,(w,h) in enumerate(sizes):
    im=Image.new('RGB',(w,h),['#9d8170','#56877f','#a98cba','#bb8c57','#555c8e','#9a735e'][i])
    draw=ImageDraw.Draw(im)
    draw.ellipse((w*.1,h*.1,w*.85,h*.85),fill=['#d8ba90','#99c5bc','#d4c1e0'][i%3])
    draw.line((5,h-5,w-5,5),fill='#2b3138',width=12)
    out=io.BytesIO();im.save(out,format='PNG')
    images.append('data:image/png;base64,'+base64.b64encode(out.getvalue()).decode())

with tempfile.TemporaryDirectory(prefix='paintlab-discovery-browser-') as tmp:
    path=Path(tmp)/'db.sqlite3';db.init(path)
    con=db.connect(path)
    a=con.execute("INSERT INTO users(username,password_hash) VALUES('ArtistOne','x')").lastrowid
    b=con.execute("INSERT INTO users(username,password_hash) VALUES('SecondArtist','x')").lastrowid
    for i in range(65):
        token=f'pub{i:021}'
        title='Dream painting '+str(i) if i%2==0 else 'Blue study '+str(i)
        con.execute('INSERT INTO publications(token,owner_id,title,file_name,created_at) VALUES(?,?,?,?,?)',
            (token,a if i%2 else b,title,token+'.png',f'2026-11-{22-(i%5):02}T11:{i%60:02}:00Z'))
    con.commit()
    def make_page(url):
        args={k:v[0] for k,v in parse_qs(urlsplit(url).query).items()}
        filters=public_discovery.normalized(args)
        rows,total,page=public_discovery.search(con,filters,datetime(2026,11,22,12,tzinfo=timezone.utc))
        cards=[]
        for row in rows:
            i=int(row['token'][3:]);cards.append({'url':'/p/'+row['token'],'image':images[i%len(images)],
                'artist_url':'/u/'+row['username'],'username':row['username'],'title':row['title'],
                'created_at':row['created_at']})
        from urllib.parse import urlencode
        def build_url(**up):
            params={'q':filters.q,'period':filters.period,'sort':filters.sort,'from':filters.date_from,'to':filters.date_to}
            params.update(up)
            return '/explore?'+urlencode({k:v for k,v in params.items() if v})
        urls={'period':{k:build_url(period=k,page=None) for k in public_discovery.PERIODS},
              'prev':build_url(page=page-1) if page>1 else None,
              'next':build_url(page=page+1) if page*48<total else None}
        body=public_viewer.discover_markup(cards,filters,total,page,urls)
        return ('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<style>'+public_viewer.BASE_CSS+public_viewer.DISCOVER_CSS+'</style></head><body class="discover-page">'
                '<nav><a href="/">Paint Lab</a><a href="/explore">Explore art</a></nav>'+body+'</body></html>')

    with sync_playwright() as browser_system:
        browser=browser_system.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for name,width,height in [('desktop',1440,900),('tablet',880,920),('mobile',390,844)]:
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=name=='mobile',has_touch=name=='mobile')
            page=context.new_page();errors=[]
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.set_content(make_page('http://local.test/explore'),wait_until='load')
            page.locator('.discovery-tile img').evaluate_all('(els)=>els.forEach(x=>x.loading="eager")')
            page.wait_for_function('Array.from(document.querySelectorAll(".discovery-tile img")).every(img=>img.complete && img.naturalWidth>0)')
            result=page.evaluate('''() => {
               const images=[...document.querySelectorAll('.discovery-tile img')];
               return {width:innerWidth,documentWidth:document.documentElement.scrollWidth,
                 columns:new Set(images.map(img=>Math.round(img.getBoundingClientRect().left))).size,
                 ratios:images.map(img=>{const b=img.getBoundingClientRect();return {original:img.naturalWidth/img.naturalHeight,display:b.width/b.height}}),
                 count:images.length,heading:document.querySelector('h1').textContent};
            }''')
            assert result['count']==48,result
            assert result['width']+2>=result['documentWidth'],result
            assert all(abs(x['original']-x['display'])<.015 for x in result['ratios']),result
            assert result['columns']>=2 if name!='mobile' else result['columns']==1,result
            assert result['heading']=='Art from everyone.',result
            page.screenshot(path='/tmp/paintlab_discover_v0144_'+name+'.png',full_page=True)
            # Forms and search are server-rendered; simulate the GET responses
            # without navigating to external networking in the sandbox browser.
            assert page.get_by_role('link',name='Today').get_attribute('href').endswith('period=today') or 'period=today' in page.get_by_role('link',name='Today').get_attribute('href')
            page.set_content(make_page('http://local.test/explore?period=today'),wait_until='load')
            assert page.locator('.discovery-tile').count()==13,page.locator('.discovery-tile').count()
            page.locator('#discoverQuery').fill('Blue study')
            page.locator('#discoverSort').select_option('az')
            assert page.locator('#discoverQuery').input_value()=='Blue study'
            assert page.locator('#discoverSort').input_value()=='az'
            page.set_content(make_page('http://local.test/explore?period=today&q=Blue+study&sort=az'),wait_until='load')
            assert page.locator('.discovery-tile').count()==6,page.locator('.discovery-tile').count()
            assert page.locator('.discovery-tile').first.locator('.discovery-caption').inner_text().startswith('Blue study')
            page.set_content(make_page('http://local.test/explore?page=2'),wait_until='load')
            assert page.locator('.discovery-tile').count()==17,page.locator('.discovery-tile').count()
            assert page.locator('a[href="https://rantlist.me/"]').count()==1
            # Same feed can be opened as the existing full-height, cross-artist viewer.
            slides=[{'title':'Alice painting','url':'/p/'+'a'*24+'?browse=explore',
                     'image':images[0],'username':'ArtistOne','artist_url':'/u/ArtistOne'},
                    {'title':'Bob painting','url':'/p/'+'b'*24+'?browse=explore',
                     'image':images[1],'username':'SecondArtist','artist_url':'/u/SecondArtist'}]
            viewer=('<html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<style>'+public_viewer.BASE_CSS+public_viewer.VIEWER_CSS+'</style></head>'
                    '<body class="viewer-page"><nav>Paint Lab</nav><script>history.pushState=function(s,t,u){window.lastNav=u}</script>'+
                    public_viewer.viewer_markup(slides,0,'ArtistOne','/u/ArtistOne',gallery_url='/explore')+
                    '<script>'+public_viewer.VIEWER_JS+'</script></body></html>')
            page.set_content(viewer,wait_until='load')
            page.get_by_role('button',name='Next artwork').click()
            assert page.locator('#artTitle').inner_text()=='Bob painting'
            assert page.locator('#artCreator').inner_text()=='SecondArtist'
            assert page.locator('#artCreator').get_attribute('href')=='/u/SecondArtist'
            assert page.locator('.gallery-link').get_attribute('href')=='/explore'
            assert page.locator('#artCounter').inner_text()=='2 / 2'
            page.get_by_role('button',name='Previous artwork').click()
            assert page.locator('#artCreator').inner_text()=='ArtistOne'
            assert not errors,errors
            print('PASS',name,{'columns':result['columns'],'cards':result['count'],'no_horizontal_overflow':True,'ratio_preserved':True,'filters':True,'pagination':True})
            context.close()
        browser.close()
    con.close()
