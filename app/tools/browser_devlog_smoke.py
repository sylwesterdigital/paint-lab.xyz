#!/usr/bin/env python3
"""Real Chromium regression for current, stale and offline development logs.

No production, localhost or external network access: HTML is loaded directly into
an isolated headless tab, with release-JSON fetches and storage deterministically
simulated. Requires Chromium and Python's playwright module.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text()
CHANGES=json.loads((APP/'changelog.json').read_text())
VERSION=CHANGES['version']

def document(*,mode='healthy',seen=False):
    data=CHANGES if mode!='stale' else dict(CHANGES,version='0.1.26',title='Paint Lab v0.1.26 — stale CDN copy')
    payload=json.dumps(data,ensure_ascii=True)
    initial={"paint-lab-devlog-seen-v1":VERSION} if seen else {}
    shim=f'''<script>
    const __qaStorage={json.dumps(initial)};
    Object.defineProperty(window,'localStorage',{{configurable:true,value:{{
      getItem:key=>Object.prototype.hasOwnProperty.call(__qaStorage,key)?__qaStorage[key]:null,
      setItem:(key,val)=>{{__qaStorage[key]=String(val)}},
      removeItem:key=>{{delete __qaStorage[key]}},clear:()=>{{for(const k of Object.keys(__qaStorage))delete __qaStorage[k]}}
    }}}});
    window.fetch=(url,options)=>{{
      if(!String(url).includes('changelog.json'))return Promise.reject(new TypeError('Simulated offline backend'));
      if('{mode}'==='offline')return Promise.reject(new TypeError('Simulated offline changelog'));
      return new Promise(resolve=>setTimeout(()=>resolve(new Response(JSON.stringify({payload}),{{status:200,headers:{{'content-type':'application/json'}}}})),300));
    }};
    </script>'''
    return HTML.replace('<script>',shim+'\n<script>',1).replace('initUI();initDevLog();','window.__devlogQA={open:openDevLog};initUI();initDevLog();',1)

def check(page,failures,reason):
    page.wait_for_selector('#devLogOverlay.visible',timeout=10000)
    title=page.locator('#devLogTitle').inner_text()
    assert VERSION in title,(reason,title)
    assert page.locator('#devLogItems li').count()==len(CHANGES['changes']),(reason,'latest changes')
    assert page.locator('#devLogArchive details').count()==len(CHANGES['history']),(reason,'history length')
    assert CHANGES['history'][0]['version'] in page.locator('#devLogArchive details').first.locator('summary').inner_text(),(reason,'history head')
    assert not failures,(reason,failures)

def main():
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        page=browser.new_page(viewport={'width':1300,'height':840})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content(document(),wait_until='domcontentloaded',timeout=35000)
        check(page,errors,'connected')
        page.locator('#devLogHistory').click()
        assert page.locator('#devLogArchive').is_visible()
        page.wait_for_timeout(450)
        assert page.locator('#devLogHistory').get_attribute('aria-selected')=='true','Remote refresh changed selected tab'
        page.locator('#devLogClose').click()
        assert page.evaluate("localStorage.getItem('paint-lab-devlog-seen-v1')")==VERSION
        page.evaluate('__devlogQA.open(false)')
        assert not page.locator('#devLogOverlay').is_visible(),'Seen release unexpectedly reopened'
        page.locator('#devLogTop').click()
        check(page,errors,'manual reopened')
        page.close()
        # Fully fresh page, but the version was already seen.
        page=browser.new_page(viewport={'width':1300,'height':840})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content(document(seen=True),wait_until='domcontentloaded')
        page.wait_for_timeout(1080)
        assert not page.locator('#devLogOverlay').is_visible(),'Seen version triggered auto-popup'
        page.locator('#devLogTop').click();check(page,errors,'manual seen release')
        page.close()
        for mode in ('stale','offline'):
            page=browser.new_page(viewport={'width':1300,'height':840})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.set_content(document(mode=mode),wait_until='domcontentloaded')
            check(page,errors,mode)
            page.wait_for_timeout(460)
            assert VERSION in page.locator('#devLogTitle').inner_text(),mode
            page.close()
        browser.close()
    assert not errors,errors
    print(f'PASS: Chromium v{VERSION} development-log display, full history, offline, stale JSON, seen-once and selected tab')

if __name__=='__main__':main()
