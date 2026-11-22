#!/usr/bin/env python3
"""Chromium acceptance: clickable image cards, title overlay, isolated edit tools."""
from __future__ import annotations
import base64,io,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright

FRONTEND=Path(__file__).resolve().parents[1]/'frontend'

def thumb(size,fill):
    im=Image.new('RGB',size,fill);d=ImageDraw.Draw(im)
    d.rectangle((10,10,size[0]-11,size[1]-11),outline='#ffffff',width=7)
    d.line((10,size[1]-11,size[0]-11,10),fill='#264f4a',width=12)
    b=io.BytesIO();im.save(b,format='JPEG',quality=80)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode('ascii')

IMAGES=[thumb((360,220),'#c5ae94'),thumb((220,350),'#c7b7ca'),thumb((360,300),'#b9c5b0')]

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(FRONTEND),**kw)
    def log_message(self,*args):pass

def run(browser,width,height,kind,base):
    ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,has_touch=width<600,is_mobile=width<600)
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    html=(FRONTEND/'index.html').read_text(encoding='utf-8')
    # Test-only bindings: make confirm helpers replaceable without editing the packaged app.
    html=html.replace('const confirmAction=', 'let confirmAction=').replace('const inputAction=', 'let inputAction=')
    hooks=r"""
window.__galleryTest={
 setup(images){
  window._galleryOpenCalls=[];window._galleryRenameCalls=[];window._galleryDeletes=[];
  window._galleryRecords=[
   {id:'a',title:'Warm pigment',updated:1740000000000,thumbnail:images[0],data:{title:'Warm pigment'}},
   {id:'b',title:'Portrait study',updated:1740000000001,thumbnail:images[1],data:{title:'Portrait study'}},
   {id:'c',title:'Paper sketch',updated:1740000000002,thumbnail:images[2],data:{title:'Paper sketch'}}
  ];
  galleryDb={};
  getRecords=async()=>window._galleryRecords;
  storeRecord=async(item)=>{window._galleryRenameCalls.push(item.title)};
  deleteRecord=async(id)=>{window._galleryDeletes.push(id);window._galleryRecords=window._galleryRecords.filter(item=>item.id!==id)};
  confirmAction=async()=>true;
  inputAction=async()=>"Renamed painting";
  loadProject=(data,id)=>{window._galleryOpenCalls.push(id)};
  actions=[];
 },
 open(){showModal('galleryOverlay');return renderGallery()}
};
"""
    marker='})();\n</script></body></html>'
    assert html.count(marker)==1
    html=html.replace(marker,hooks+marker)
    page.set_content(html,wait_until='domcontentloaded',timeout=30000)
    page.wait_for_function("!!window.__galleryTest && !!document.getElementById('galleryGrid')",timeout=12000)
    page.evaluate('images=>window.__galleryTest.setup(images)',IMAGES)
    page.evaluate('window.__galleryTest.open()')
    page.locator('.artcard').first.wait_for()
    assert page.locator('.artcard').count()==3
    assert page.locator('.artcard-open').count()==3
    assert page.locator('.artcard-title').all_text_contents()==['Warm pigment','Portrait study','Paper sketch']
    assert page.locator('.artcard-main').count()==0
    assert page.get_by_role('button',name='Open',exact=True).count()==0
    assert page.locator('.artcard-actions').count()==0
    page.evaluate("document.querySelectorAll('.artcard img').forEach(img=>{img.loading='eager'})")
    page.wait_for_function('Array.from(document.querySelectorAll(".artcard img")).every(img=>img.complete&&img.naturalWidth>0)',timeout=10000)
    geom=page.evaluate('''()=>{
       const pictures=[...document.querySelectorAll('.artcard img')];
       return {width:innerWidth,scroll:document.documentElement.scrollWidth,
         pictures:pictures.map(img=>{const r=img.getBoundingClientRect();return {
            ratio:r.width/r.height,natural:img.naturalWidth/img.naturalHeight,fit:getComputedStyle(img).objectFit
         }})};
    }''')
    for img in geom['pictures']:
        assert img['fit']=='contain' and abs(img['ratio']-img['natural'])<.02,img
    assert geom['scroll']<=geom['width']+2,geom
    page.locator('.artcard-open').first.click(position={'x':12,'y':12})
    assert page.evaluate('window._galleryOpenCalls')==['a']
    assert not page.locator('#galleryOverlay').evaluate('(el)=>el.classList.contains("visible")')
    page.evaluate("window.__galleryTest.open()")
    page.locator('#galleryEdit').check()
    assert page.locator('.artcard-actions').count()==3
    page.get_by_role('button',name='Rename Warm pigment').click()
    page.wait_for_function('window._galleryRenameCalls.length===1')
    assert page.evaluate('window._galleryOpenCalls')==['a']
    page.get_by_role('button',name='Delete Portrait study').click()
    page.wait_for_function('window._galleryDeletes.length===1')
    assert page.evaluate('window._galleryOpenCalls')==['a']
    assert page.locator('.artcard').count()==2
    page.locator('#galleryEdit').uncheck()
    assert page.locator('.artcard-actions').count()==0
    page.screenshot(path=f'/tmp/paintlab_local_gallery_v0143_{kind}.png')
    print('PASS',kind,'gallery cards + edit + aspect ratios',geom)
    # The drawing engine can log WebGL warnings on software renderers, but JS errors are failures.
    assert not errors,errors
    ctx.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=swiftshader'])
        run(browser,1365,900,'desktop','embedded')
        run(browser,390,844,'mobile','embedded')
        browser.close()
