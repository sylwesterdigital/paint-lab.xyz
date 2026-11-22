#!/usr/bin/env python3
"""Offline Chromium visual-geometry checks for fluid, non-cropping public gallery."""
from __future__ import annotations
import base64,io,sys
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from backend import public_viewer

DIMENSIONS=[(230,720),(960,230),(600,600),(810,470),(250,650),
            (1030,310),(380,760),(610,240),(640,640),(680,360)]

def image_data(i,size):
    im=Image.new('RGB',size,['#cf837f','#7ab5a4','#9b8dbe','#e6b763'][i%4])
    draw=ImageDraw.Draw(im)
    w,h=size
    draw.rectangle((8,8,w-9,h-9),outline='#f9f2cf',width=6)
    draw.line((8,8,w-9,h-9),fill='#193a45',width=5)
    out=io.BytesIO();im.save(out,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()

items=[{'title':f'{w} × {h} artwork', 'image':image_data(i,(w,h)),
        'url':f'/p/painting{i:020d}'} for i,(w,h) in enumerate(DIMENSIONS)]

def document():
    return ('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>'+public_viewer.BASE_CSS+'</style></head><body class="gallery-page">'
            '<nav><a href="/">Paint Lab</a><span>Public gallery</span></nav>'
            +public_viewer.gallery_markup(items,'Test Artist')+'</body></html>')

def test(browser,width,height,kind):
    context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=2 if width<500 else 1,
                                has_touch=width<500,is_mobile=width<500)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.set_content(document(),wait_until='load')
    page.locator('.gallery img').evaluate_all('(images)=>images.forEach(img=>img.loading="eager")')
    page.wait_for_function('Array.from(document.querySelectorAll(".gallery img")).every(im=>im.complete && im.naturalWidth>0)',timeout=15000)
    page.locator('.gallery img').evaluate_all('(imgs)=>Promise.all(imgs.map(img=>img.decode()))')
    result=page.evaluate('''() => {
      const images=[...document.querySelectorAll('.gallery img')];
      const cards=[...document.querySelectorAll('.gallery .card')];
      const ratios=images.map(img=>{const b=img.getBoundingClientRect();return {
        title:img.alt, natural:img.naturalWidth/img.naturalHeight, rendered:b.width/b.height,
        width:b.width,height:b.height,fit:getComputedStyle(img).objectFit};});
      const rows=cards.map(el=>{const b=el.getBoundingClientRect();return {x:Math.round(b.x),y:Math.round(b.y),height:b.height};});
      return {screen:innerWidth,body:document.documentElement.scrollWidth,columns:new Set(rows.map(r=>r.x)).size,
        cards:rows.length, rows, ratios, heading:document.querySelector('h1').textContent,
        grid:getComputedStyle(document.querySelector('.gallery')).columnWidth,
        galleryWidth:document.querySelector('.gallery').getBoundingClientRect().width};
    }''')
    assert result['cards']==len(DIMENSIONS),result
    assert result['heading']=='Test Artist · Public artworks',result
    assert result['body']<=result['screen']+2,result
    assert len(result['ratios'])==len(DIMENSIONS),result
    for entry in result['ratios']:
        assert entry['fit']=='contain',entry
        assert abs(entry['rendered']/entry['natural']-1)<.009,entry
        assert entry['height']>20,entry
    assert (result['columns']==1 if kind=='mobile' else result['columns']>=2),result
    # Content must have visible natural proportions: portrait much taller than a wide painting.
    assert result['ratios'][0]['height'] > result['ratios'][1]['height']*2.5,result
    assert not errors,errors
    page.screenshot(path='/tmp/paintlab_masonry_v0142_'+kind+'.png',full_page=True)
    print('PASS',kind,{'columns':result['columns'],'artworks':result['cards'],
                       'horizontal_overflow':result['body']-result['screen'],
                       'portrait_ratio':round(result['ratios'][0]['rendered'],3),
                       'wide_ratio':round(result['ratios'][1]['rendered'],3),
                       'gallery_width':round(result['galleryWidth'])})
    context.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        test(browser,2048,960,'desktop')
        test(browser,980,720,'tablet')
        test(browser,390,844,'mobile')
        browser.close()
