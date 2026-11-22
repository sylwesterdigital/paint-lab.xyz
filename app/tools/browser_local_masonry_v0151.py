#!/usr/bin/env python3
"""Chromium acceptance: full native ratio masonry, legacy thumbnails, filters and actions."""
from __future__ import annotations
import base64,io
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
FRONTEND=Path(__file__).resolve().parents[1]/'frontend'

def image(fill):
    im=Image.new('RGB',(360,220),fill);d=ImageDraw.Draw(im)
    d.ellipse((30,22,325,198),outline='white',width=9)
    d.line((10,195,345,18),fill='#151b28',width=16)
    buf=io.BytesIO();im.save(buf,format='JPEG',quality=88)
    return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode('ascii')

SAMPLES=[image('#ab7e7e'),image('#7d8ea8'),image('#a6b285'),image('#b597c2')]
BASE_HTML=(FRONTEND/'index.html').read_text().replace('const confirmAction=','let confirmAction=').replace('const inputAction=','let inputAction=')
HOOKS=r'''
window.__galleryMasonry={
 async setup(images){
  const now=Date.now();
  window._calls={open:[],rename:[],deleted:[]};
  window._galleryRecords=[
   {id:'portrait',title:'Portrait art',created:now-5000,updated:now-5000,thumbnail:images[0],data:{baseW:600,baseH:1000,title:'Portrait art'}},
   {id:'landscape',title:'Landscape blue',created:now-20000,updated:now-20000,thumbnail:images[1],data:{baseW:1800,baseH:700,title:'Landscape blue'}},
   {id:'square',title:'Square study',created:now-35*86400000,updated:now-35*86400000,thumbnail:images[2],data:{baseW:850,baseH:850,title:'Square study'}},
   {id:'panorama',title:'Wide violet',created:now-3*86400000,updated:now-3*86400000,thumbnail:images[3],data:{baseW:2400,baseH:460,title:'Wide violet'}}
  ];
  galleryDb={};getRecords=async()=>window._galleryRecords;
  storeRecord=async(item)=>{window._calls.rename.push(item.title)};
  deleteRecord=async(id)=>{window._calls.deleted.push(id);window._galleryRecords=window._galleryRecords.filter(x=>x.id!==id)};
  confirmAction=async()=>true;inputAction=async()=>"Renamed art";
  loadProject=(data,id)=>{window._calls.open.push(id)};
  actions=[];
  await openGallery();
 },
 async open(){await openGallery()},
 orderedTitles(){return galleryFilterRecords(window._galleryRecords).map(item=>item.title)},
 async newThumb(){
  createExportCanvas=()=>{const out=document.createElement('canvas');out.width=600;out.height=1200;return out};
  const src=thumbnail();const img=new Image();img.src=src;await img.decode();return {width:img.naturalWidth,height:img.naturalHeight};
 }
};
'''
MARKER='})();\n</script></body></html>'
assert BASE_HTML.count(MARKER)==1
BASE_HTML=BASE_HTML.replace(MARKER,HOOKS+MARKER)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    for width,height in [(1440,900),(800,900),(390,844)]:
        context=browser.new_context(viewport={'width':width,'height':height},has_touch=width<600,is_mobile=width<600,device_scale_factor=1)
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error: errors.append(str(error)))
        page.set_content(BASE_HTML,wait_until='domcontentloaded',timeout=45000)
        page.wait_for_function('!!window.__galleryMasonry')
        page.evaluate('imgs=>window.__galleryMasonry.setup(imgs)',SAMPLES)
        page.wait_for_function('document.querySelectorAll(".artcard").length===4')
        page.evaluate('''() => document.querySelectorAll('.artcard img').forEach(img=>img.loading='eager')''')
        page.wait_for_function('Array.from(document.querySelectorAll(".artcard img")).every(img=>img.complete&&img.naturalWidth>0)')
        geom=page.evaluate('''() => ({
           viewport:innerWidth,docWidth:document.documentElement.scrollWidth,
           gallery:document.querySelector('.galleryGrid').getBoundingClientRect().toJSON(),
           cards:[...document.querySelectorAll('.artcard')].map(card=>{const e=card.querySelector('.artcard-image');const rect=e.getBoundingClientRect(),img=e.querySelector('img');return {name:card.querySelector('.artcard-title').textContent,ratio:rect.width/rect.height,natural:img.naturalWidth/img.naturalHeight,fit:getComputedStyle(img).objectFit,w:rect.width,h:rect.height}})
        })''')
        expected={'Portrait art':.6,'Landscape blue':1800/700,'Square study':1,'Wide violet':2400/460}
        assert len(geom['cards'])==4,geom
        for item in geom['cards']:
            assert abs(item['ratio']-expected[item['name']])<.03, (width,item)
            assert item['w']>100 and item['h']>25,(width,item)
        assert geom['docWidth']<=width+2,(width,geom)
        assert width>500 or page.locator('.galleryGrid').evaluate('(el)=>el.querySelectorAll(".gallery-masonry-column").length')==1
        page.screenshot(path=f'/mnt/data/paintlab_local_masonry_v0151_{width}.png')
        print('RATIOS PASS',width,[(it['name'],round(it['ratio'],3)) for it in geom['cards']])
        page.locator('#gallerySearch').fill('square')
        page.wait_for_function('document.querySelectorAll(".artcard").length===1')
        assert page.locator('.artcard-title').inner_text()=='Square study'
        page.locator('#galleryResetFilters').click()
        page.wait_for_function('document.querySelectorAll(".artcard").length===4')
        page.get_by_role('button',name='7 days').click()
        page.wait_for_function('document.querySelectorAll(".artcard").length===3')
        page.locator('#galleryResetFilters').click()
        page.locator('#gallerySort').select_option('az')
        assert page.evaluate('window.__galleryMasonry.orderedTitles()')==['Landscape blue','Portrait art','Square study','Wide violet']
        page.locator('#gallerySort').select_option('za')
        assert page.evaluate('window.__galleryMasonry.orderedTitles()')==['Wide violet','Square study','Portrait art','Landscape blue']
        page.locator('#gallerySort').select_option('recent')
        page.locator('.artcard-open').first.click(position={'x':15,'y':15})
        assert page.evaluate('window._calls.open')==['portrait']
        assert not page.locator('#galleryOverlay').evaluate('(e)=>e.classList.contains("visible")')
        page.evaluate('window.__galleryMasonry.open()')
        page.locator('#galleryEdit').check()
        page.get_by_role('button',name='Rename Portrait art').click()
        page.wait_for_function('window._calls.rename.length===1')
        assert page.evaluate('window._calls.open')==['portrait']
        page.get_by_role('button',name='Delete Landscape blue').click()
        page.wait_for_function('window._calls.deleted.length===1')
        page.wait_for_function('document.querySelectorAll(".artcard").length===3')
        size=page.evaluate('window.__galleryMasonry.newThumb()')
        assert size['height']==520 and size['width']==260,size
        print('CONTROLS PASS',width,'new thumbnail',size,'js errors',errors)
        assert not errors,errors
        context.close()
    browser.close()
