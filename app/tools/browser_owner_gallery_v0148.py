#!/usr/bin/env python3
"""Offline routed Chromium test for artist search, hide/show/remove and responsive masonry."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs,urlencode
from datetime import datetime,timezone
import tempfile,sys,json,base64
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from backend import db,public_viewer,public_discovery
PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg=='
with tempfile.TemporaryDirectory() as tmp:
 conn=db.connect(Path(tmp)/'test.sqlite3');conn.close();db.init(Path(tmp)/'test.sqlite3')
 con=db.connect(Path(tmp)/'test.sqlite3')
 a=con.execute("INSERT INTO users(username,password_hash) VALUES('FirstArtist','hash')").lastrowid
 for i,title in enumerate(['Blue portrait','Red lines','Spring ink','Watercolour study','Blue print']):
  token='publication'+chr(97+i)*18
  con.execute('INSERT INTO publications(token,owner_id,title,file_name,created_at) VALUES(?,?,?,?,?)',
   (token,a,title,token+'.png',f'2026-11-22T11:0{i}:00Z'))
 con.commit()
 for kind,width,height in [('desktop',1290,880),('mobile',390,844)]:
  if kind=='mobile':
   token='publication'+'a'*18
   con.execute('INSERT INTO publications(token,owner_id,title,file_name,created_at) VALUES(?,?,?,?,?)',(token,a,'Blue portrait',token+'.png','2026-11-22T11:00:00Z'))
   con.commit()
  def make_page(url):
   parsed=urlparse(url);args={k:v[0] for k,v in parse_qs(parsed.query).items()}
   edit=args.get('edit')=='1';filters=public_discovery.normalized(args)
   rows,total,page=public_discovery.search(con,filters,datetime(2026,11,22,tzinfo=timezone.utc),owner_id=a,include_hidden=edit)
   items=[{'url':'/p/'+r['token'],'image':PNG,'title':r['title'],'username':'FirstArtist',
           'artist_url':'/u/FirstArtist','created_at':r['created_at'],'token':r['token'],'visible':bool(r['is_visible'])} for r in rows]
   def path(**changes):
    fields={'q':filters.q,'sort':filters.sort,'period':filters.period,'from':filters.date_from,'to':filters.date_to,'edit':'1' if edit else None}
    fields.update(changes);return '/u/FirstArtist?'+urlencode({k:v for k,v in fields.items() if v is not None and v!=''})
   pages=max(1,(total+47)//48)
   urls={'period':{x:path(period=x) for x in public_discovery.PERIODS},'prev':path(page=page-1) if page>1 else None,'next':path(page=page+1) if page<pages else None}
   markup=public_viewer.discover_markup(items,filters,total,page,urls,artist='FirstArtist',edit=edit,is_owner=True,csrf='token-test' if edit else '',gallery_url='/u/FirstArtist')
   style=public_viewer.BASE_CSS+public_viewer.DISCOVER_CSS+public_viewer.MANAGE_CSS
   script='<script nonce="t">window.__ownerRequests=[];window.__ownerReload=false;window.fetch=async(url,opts)=>{window.__ownerRequests.push({url,method:opts.method,visible:JSON.parse(opts.body).visible,csrf:opts.headers["X-CSRF-Token"]});return {ok:true,json:async()=>({ok:true})}};'+public_viewer.MANAGE_JS.replace('window.location.reload();','window.__ownerReload=true;')+'</script>' if edit else ''
   return '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+style+'</style></head><body class="gallery-page"><nav><a href="/">Paint Lab</a><a href="/explore">Explore art</a></nav>'+markup+script+'</body></html>'
  with sync_playwright() as playwright:
   browser=playwright.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   context=browser.new_context(viewport={'width':width,'height':height},is_mobile=kind=='mobile',has_touch=kind=='mobile')
   page=context.new_page();page.set_default_timeout(7000);errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
   page.set_content(make_page('http://localhost/u/FirstArtist?edit=1'))
   assert page.locator('.discovery-tile').count()==5
   assert page.locator('.owner-controls').count()==5
   assert page.locator('h1').inner_text()=='@FirstArtist'
   assert page.locator('input[name="edit"]').input_value()=='1'
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
   # Hide an existing public record; check real DOM events and request payload.
   page.locator('button[data-visibility]').first.click()
   page.wait_for_function('window.__ownerRequests.length===1')
   mutation=page.evaluate('window.__ownerRequests[0]')
   assert mutation['method']=='PATCH' and mutation['visible'] is False and mutation['csrf']=='token-test',mutation
   token=mutation['url'].split('/')[-1]
   with con:con.execute('UPDATE publications SET is_visible=0 WHERE token=?',(token,))
   page.set_content(make_page('http://localhost/u/FirstArtist?edit=1'))
   assert page.locator('.owner-hidden .visibility-label').inner_text()=='Hidden from public'
   page.screenshot(path=f'/mnt/data/paintlab_owner_gallery_v0148_{kind}.png',full_page=True)
   page.locator('.owner-hidden button[data-visibility]').click()
   page.wait_for_function('window.__ownerRequests.length===1')
   mutation=page.evaluate('window.__ownerRequests[0]')
   assert mutation['visible'] is True,mutation
   with con:con.execute('UPDATE publications SET is_visible=1 WHERE token=?',(token,))
   page.set_content(make_page('http://localhost/u/FirstArtist?edit=1'))
   assert page.locator('.owner-hidden').count()==0
   # The same SQL filters and sort contract as community discovery.
   page.set_content(make_page('http://localhost/u/FirstArtist?edit=1&q=Blue&sort=az'))
   assert page.locator('.discovery-tile').count()==2
   assert page.locator('.discovery-caption').all_inner_texts()==['Blue portrait','Blue print']
   page.once('dialog',lambda d:d.accept())
   page.locator('button[data-remove]').first.click()
   page.wait_for_function('window.__ownerRequests.length===1')
   mutation=page.evaluate('window.__ownerRequests[0]')
   assert mutation['method']=='DELETE',mutation
   with con:con.execute('DELETE FROM publications WHERE token=?',(mutation['url'].split('/')[-1],))
   page.set_content(make_page('http://localhost/u/FirstArtist?edit=1&q=Blue&sort=az'))
   assert page.locator('.discovery-caption').all_inner_texts()==['Blue print']
   assert not errors,errors
   print('PASS',kind,'owner gallery filters / hide-show / remove / no overflow')
   context.close();browser.close()
 con.close()
