#!/usr/bin/env python3
"""Offline Chromium: compressed discovery previews and free-download/support viewer."""
from __future__ import annotations
import io,sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from backend import public_discovery,public_viewer

png=io.BytesIO();Image.new('RGB',(280,560),'#70aa9c').save(png,format='PNG')
webp=io.BytesIO();Image.new('RGB',(280,560),'#70aa9c').save(webp,format='WEBP',quality=76)
from base64 import b64encode
pic='data:image/png;base64,'+b64encode(png.getvalue()).decode()

def gallery():
 items=[{'token':f'item{i:024}','title':f'Gallery item {i}',
  'url':f'/p/item{i:024}','image':pic,'preview':f'https://gallery.example/thumb/{i}.webp',
  'dimensions':(280,560),'artist_url':'/u/TestArtist','username':'TestArtist',
  'created_at':'2026-11-23T01:00:00Z'} for i in range(30)]
 urls={'period':{x:'/explore' for x in ('all','today','week','month')},'prev':None,'next':None}
 body=public_viewer.discover_markup(items,public_discovery.normalized({}),30,1,urls)
 return ('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+public_viewer.BASE_CSS+public_viewer.DISCOVER_CSS+'</style></head><body class="discover-page"><nav><a href="/explore">Explore art</a></nav>'+body+'<script>'+public_viewer.DISCOVERY_JS+'</script></body></html>')

def viewer():
 slides=[{'token':f'v{i:024}','title':f'Public painting {i}',
   'url':f'/p/v{i:024}','image':pic,'username':'TestArtist','artist_url':'/u/TestArtist'} for i in range(3)]
 body=public_viewer.viewer_markup(slides,0,'TestArtist','/u/TestArtist',csrf='test-csrf')
 return ('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+public_viewer.BASE_CSS+public_viewer.VIEWER_CSS+'</style></head><body class="viewer-page"><nav>Paint Lab</nav>'+body+
 '<script>history.pushState=()=>{};window.events=[];window.umami={track:(name,data)=>events.push({name,data})};</script><script>'+public_viewer.VIEWER_JS+'</script></body></html>')

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,w,h in [('desktop',1280,800),('mobile',390,844)]:
  context=browser.new_context(viewport={'width':w,'height':h},is_mobile=(name=='mobile'),has_touch=(name=='mobile'))
  page=context.new_page();errors=[];requested=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def thumb_route(route):
   requested.append(route.request.url)
   route.fulfill(status=200,body=webp.getvalue(),content_type='image/webp')
  page.route('https://gallery.example/thumb/*.webp',thumb_route)
  page.set_content(gallery(),wait_until='load')
  page.wait_for_timeout(400)
  initial=len(requested)
  assert initial >= 4 and initial < 30,(name,initial)
  assert page.locator('img[data-preview-src]').count()>0
  ratios=page.locator('.discovery-tile img').evaluate_all('els=>els.map(el=>{const r=el.getBoundingClientRect();return [r.width,r.height]})')
  assert all(abs(wi/hi-.5)<.02 for wi,hi in ratios[4:] if hi>0),ratios
  assert all(abs(wi/hi-1)<.02 for wi,hi in ratios[:4]) if name=='mobile' else all(abs(wi/hi-.5)<.02 for wi,hi in ratios[:4]),ratios
  page.evaluate('window.scrollTo(0,document.body.scrollHeight/2)')
  page.wait_for_timeout(400)
  later=len(requested)
  assert later>initial,(name,initial,later)
  print(name,'gallery initial',initial,'after scrolling',later,'total',30)
  page.set_content(viewer(),wait_until='load')
  assert page.locator('#artTitle').inner_text()=='Public painting 0'
  assert page.evaluate('events.map(x=>x.name)')==['artwork_view']
  page.locator('#artNext').click()
  assert page.locator('#artTitle').inner_text()=='Public painting 1'
  assert [e['data']['publication'] for e in page.evaluate('events')]==['v000000000000000000000000','v000000000000000000000001']
  page.locator('#artDownload').click()
  assert page.locator('#supportDialog').evaluate('el=>el.open')
  assert page.locator('#artDownloadFile').get_attribute('href')==pic
  assert page.locator('button[data-support-amount]:disabled').count()==3
  assert page.locator('#supportDialog').bounding_box()['height']<=h
  page.locator('#supportClose').click()
  assert not page.locator('#supportDialog').evaluate('el=>el.open')
  assert not errors,errors
  print(name,'viewer artwork views, arrows, dialog, free PNG, disabled Stripe: PASS')
  context.close()
 browser.close()
