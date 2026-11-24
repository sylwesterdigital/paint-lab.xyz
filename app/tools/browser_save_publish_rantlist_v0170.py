#!/usr/bin/env python3
"""Chromium smoke: one-click save+publish, public-link actions, optional Rantlist bridge."""
from pathlib import Path
from playwright.sync_api import sync_playwright
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
MARKER='})();\n</script></body></html>'
assert HTML.count(MARKER)==1
HOOK=r'''
window.__share170={
 init(){
  window.__records=[];window.__posted=[];window.__opened=[];window.__wants=[];
  window.__enabled=false;window.__publishFail=false;
  galleryDb={};artId=null;artName='Untitled';artCreated=Date.now();pendingClearAfterSave=false;
  cloudUser={username:'painter'};cloudCSRF='test-token';
  captureLayerSnapshot=async()=>[{id:'base-layer',blob:new Blob(['png'],{type:'image/png'})}];
  captureBaselineSnapshot=async()=>null;
  projectData=()=>({format:'paint-lab-webgl',version:4,title:artName,actions:[],head:0});
  thumbnail=()=>'data:image/jpeg;base64,AAAA';
  storeRecord=async r=>{window.__records.push(r)};
  sharePNGBlob=async()=>new Blob(['png'],{type:'image/png'});
  blobAsDataURL=async()=> 'data:image/png;base64,iVBORw0KGgo=';
  apiCall=async(path,method,body)=>{
    if(path==='/integrations/rantlist')return {enabled:window.__enabled};
    if(path==='/publications'&&method==='POST'){
      window.__posted.push(body);
      if(window.__publishFail)throw Error('Simulated failure');
      return {token:'ABCDEFGHIJKLMNOPQRSTUVWX1234567890',url:'https://paint-lab.xyz/p/ABCDEFGHIJKLMNOPQRSTUVWX1234567890'};
    }
    if(path.includes('/share/rantlist')&&method==='POST'){
      window.__wants.push(path);
      return {ok:true,channel:'lobby',message_id:'message-123456'};
    }
    throw Error('Unexpected request '+path);
  };
  window.open=(url)=>{window.__opened.push(url);return {closed:false};};
  openSave();return true;
 },
 signout(){cloudUser=null;updateSaveHubState();},
 signin(){cloudUser={username:'painter'};updateSaveHubState();},
 enableBridge(){window.__enabled=true;refreshRantlistBridgeStatus();},
 openAgain(){openSave();},
 getArtId(){return artId;}
};
'''
HTML=HTML.replace('initUI();initDesktopToolbar();initDevLog();','initUI();initDesktopToolbar();')
HTML=HTML.replace(MARKER,HOOK+MARKER)

def run(browser,mobile):
 kw={'viewport':{'width':390 if mobile else 1130,'height':780 if mobile else 860},'is_mobile':mobile,'has_touch':mobile}
 page=browser.new_page(**kw);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 page.set_content(HTML,wait_until='domcontentloaded',timeout=40000)
 page.wait_for_function('!!window.__share170',timeout=10000)
 page.evaluate('window.__share170.init()')
 assert page.locator('#saveAndPublish').is_visible()
 # Not signed in means no accidental local save or publication.
 page.evaluate('window.__share170.signout()')
 page.locator('#saveAndPublish').click()
 assert page.evaluate('window.__records.length===0 && window.__posted.length===0')
 assert 'Sign in' in page.locator('#saveStatus').inner_text()
 page.evaluate('window.__share170.signin()')
 page.locator('#artName').fill('Evening Study')
 page.locator('#saveAndPublish').click()
 page.wait_for_function('window.__records.length===1 && window.__posted.length===1')
 page.wait_for_function("document.querySelector('#savePublicLinkWrap').hidden===false")
 assert page.locator('#savePublicLink').input_value().endswith('/ABCDEFGHIJKLMNOPQRSTUVWX1234567890')
 assert page.locator('#saveOpenLink').get_attribute('href').startswith('https://paint-lab.xyz/p/')
 assert page.locator('#saveOpenLink').get_attribute('target')=='_blank'
 assert page.locator('#saveOverlay').evaluate("e=>e.classList.contains('visible')")
 assert page.evaluate('window.__records[0].id === window.__share170.getArtId()')
 # Manual handoff, no external post implied.
 page.wait_for_function("document.querySelector('#saveRantlistInfo').textContent.includes('manually')")
 page.locator('#saveRantlistShare').click()
 page.wait_for_function('window.__opened.length===1')
 assert page.evaluate('window.__wants.length')==0
 assert page.evaluate('window.__opened[0]')=='https://rantlist.me/'
 # Bridge configured and Rantlist confirms durable message.
 page.evaluate('window.__share170.enableBridge()')
 page.wait_for_function("document.querySelector('#saveRantlistInfo').textContent.includes('bot')")
 page.locator('#saveRantlistShare').click()
 page.wait_for_function('window.__wants.length===1')
 assert 'Shared successfully' in page.locator('#saveStatus').inner_text()
 # When public publishing fails, local copy exists and dialog remains open.
 page.evaluate('window.__publishFail=true;window.__share170.openAgain()')
 page.locator('#saveAndPublish').click()
 page.wait_for_function('window.__records.length===2 && window.__posted.length===2')
 page.wait_for_function("document.querySelector('#saveStatus').textContent.includes('Saved as a new local artwork')")
 assert page.locator('#savePublicLinkWrap').is_hidden()
 assert not errors,errors
 dims=page.locator('#saveOverlay .dialog').bounding_box()
 assert dims['height']<=kw['viewport']['height'],dims
 print('PASS', 'mobile' if mobile else 'desktop',{'dialog_height':dims['height'],'saves':2,'publishes':2,'bridge_posts':1})
 page.close()

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=swiftshader'])
 run(browser,False);run(browser,True);browser.close()
