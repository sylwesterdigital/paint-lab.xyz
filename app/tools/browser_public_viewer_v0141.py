#!/usr/bin/env python3
"""Offline Chromium regression for published image preview, arrows, touch swipes."""
from __future__ import annotations
import base64, io, sys
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from backend import public_viewer

TOKENS=['v'*20+str(i) for i in range(3)]

def png_data(i):
    sizes=[(320,840),(960,300),(600,600)]
    im=Image.new('RGB',sizes[i],['#e09e93','#82b8be','#beb692'][i])
    d=ImageDraw.Draw(im);w,h=im.size
    d.rectangle((w*.12,h*.12,w*.88,h*.88),outline='#223a48',width=5)
    d.line((20,30,w-20,h-30),fill='#ffffcf',width=9)
    buffer=io.BytesIO();im.save(buffer,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode('ascii')

SLIDES=[{'token':token,'title':name,'url':'/p/'+token,'image':png_data(i)}
        for i,(token,name) in enumerate(zip(TOKENS,['Portrait study','Wide painting','Square painting']))]

# This sandbox's Chromium policy blocks URL navigation. The actual viewer runs
# in page.set_content with in-memory PNGs, and a History spy checks share URLs.
def document():
    markup=public_viewer.viewer_markup(SLIDES,0,'Artist','/u/Artist')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>'+public_viewer.BASE_CSS+public_viewer.VIEWER_CSS+'</style></head>'
            '<body class="viewer-page"><nav><a href="/">Paint Lab</a><span>Public gallery</span></nav>'
            +markup+'<script>window.__shareNav=[];history.pushState=(state,title,url)=>window.__shareNav.push(url);</script>'
            '<script>'+public_viewer.VIEWER_JS+'</script></body></html>')

def check(browser,mobile=False):
    kind='mobile' if mobile else 'desktop'
    ctx=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1365,'height':768},
                            device_scale_factor=3 if mobile else 1,has_touch=mobile,is_mobile=mobile)
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(document(),wait_until='load')
    first=page.evaluate('''() => {const s=document.getElementById('artStage').getBoundingClientRect();
      const img=document.getElementById('artImage'),r=img.getBoundingClientRect();
      return {screen:innerHeight,scroll:document.documentElement.scrollHeight,stage:s.height,image:r.height,
      css:getComputedStyle(img).objectFit,natural:img.naturalHeight,arrow:document.getElementById('artNext').getBoundingClientRect().width};}''')
    assert first['css']=='contain' and first['natural']==840,first
    assert first['image']>first['screen']*.50 and first['image']<=first['stage']+1,first
    assert first['scroll']<=first['screen']+2,first
    assert first['arrow']>=44,first
    assert page.locator('#artCounter').inner_text()=='1 / 3'
    page.locator('#artNext').click()
    assert page.locator('#artTitle').inner_text()==SLIDES[1]['title']
    assert page.evaluate('__shareNav.at(-1)')==SLIDES[1]['url']
    assert page.locator('#artDownload').get_attribute('href')==SLIDES[1]['image']
    page.keyboard.press('ArrowRight')
    assert page.locator('#artTitle').inner_text()==SLIDES[2]['title']
    page.keyboard.press('ArrowRight')
    assert page.locator('#artTitle').inner_text()==SLIDES[0]['title']
    page.keyboard.press('ArrowLeft')
    assert page.locator('#artTitle').inner_text()==SLIDES[2]['title']
    if mobile:
        page.evaluate('''() => {const s=document.getElementById('artStage');const r=s.getBoundingClientRect();
          const x=r.x+r.width*.8,y=r.y+r.height*.5;
          const a=new Touch({identifier:1,target:s,clientX:x,clientY:y});
          const b=new Touch({identifier:1,target:s,clientX:x-200,clientY:y+7});
          s.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,touches:[a],targetTouches:[a],changedTouches:[a]}));
          s.dispatchEvent(new TouchEvent('touchend',{bubbles:true,touches:[],targetTouches:[],changedTouches:[b]}));}''')
        assert page.locator('#artTitle').inner_text()==SLIDES[0]['title'],'swipe left failure'
        page.evaluate('''() => {const s=document.getElementById('artStage');const r=s.getBoundingClientRect();
          const x=r.x+r.width*.2,y=r.y+r.height*.5;
          const a=new Touch({identifier:1,target:s,clientX:x,clientY:y});
          const b=new Touch({identifier:1,target:s,clientX:x+200,clientY:y+5});
          s.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,touches:[a],targetTouches:[a],changedTouches:[a]}));
          s.dispatchEvent(new TouchEvent('touchend',{bubbles:true,touches:[],targetTouches:[],changedTouches:[b]}));}''')
        assert page.locator('#artTitle').inner_text()==SLIDES[2]['title'],'swipe right failure'
    assert page.evaluate('__shareNav.length')>=4
    assert not errors,errors
    page.screenshot(path='/tmp/paintlab_viewer_v0141_'+kind+'.png')
    print('PASS Chromium',kind,first,'arrows, keyboard, history URLs',', touch swipes' if mobile else '')
    ctx.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        check(browser,False);check(browser,True)
        browser.close()
