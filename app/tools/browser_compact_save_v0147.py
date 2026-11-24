#!/usr/bin/env python3
"""Chromium acceptance for the v0.1.45 explicit Save & Share destination hub."""
from pathlib import Path
from playwright.sync_api import sync_playwright

FRONTEND=Path(__file__).resolve().parents[1]/'frontend'
MARKER='})();\n</script></body></html>'
HOOK=r"""
window.__saveHubTest={
 setup(){
  window.__stored=[];window.__downloads=[];window.__publishes=[];window.__clearCount=0;
  galleryDb={};artId=null;artName='Untitled painting';actions=[];
  storeRecord=async record=>{window.__stored.push({id:record.id,title:record.title,created:record.created,updated:record.updated,document:record.data});};
  thumbnail=()=> 'data:image/jpeg;base64,ABCD';
  projectData=()=>({format:'paint-lab-webgl',version:4,title:artName,created:artCreated,actions:[]});
  download=(blob,name)=>{window.__downloads.push({name,size:blob.size});};
  createExportCanvas=()=>({toBlob:done=>done(new Blob(['png'],{type:'image/png'}))});
  createProjectZIP=async()=>new Blob(['zip'],{type:'application/zip'});
  clearCanvasPaint=()=>{window.__clearCount++;};
  sharePNGBlob=async(resize,withPaper)=>{window.__shareArgs={resize,withPaper};return new Blob(['test png'],{type:'image/png'});};
  blobAsDataURL=async()=> 'data:image/png;base64,iVBORw0KGgo=';
  apiCall=async(path,method,data)=>{if(path==='/publications'&&method==='POST'){
   window.__publishes.push({path,method,data});return {token:'ABCDEFGHIJKLMNOPQRSTUVWX1234567890',url:'https://paint-lab.xyz/p/ABCDEFGHIJKLMNOPQRSTUVWX1234567890'};}
   throw Error('Unexpected API request: '+path);
  };
  cloudUser=null;cloudCSRF='csrf';
  openSave(false);
 },
 open(){openSave(false);},
 currentId(){return artId;},
 login(){cloudUser={username:'test-artist'};updateSaveHubState();},
 clearFlow(){pendingClearAfterSave=true;updateSaveHubState();}
};
"""

def run(browser,viewport,kind):
 context=browser.new_context(viewport=viewport,has_touch=kind=='mobile',is_mobile=kind=='mobile')
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 html=(FRONTEND/'index.html').read_text()
 assert html.count(MARKER)==1
 html=html.replace('initUI();initDevLog();','initUI();').replace(MARKER,HOOK+MARKER)
 page.set_content(html,wait_until='domcontentloaded',timeout=30000)
 page.wait_for_function('!!window.__saveHubTest',timeout=12000)
 page.evaluate('window.__saveHubTest.setup()')
 assert page.get_by_role('heading',name='Save & share').is_visible()
 assert page.locator('#saveNew').is_enabled()
 assert page.locator('#saveOverwrite').is_disabled()
 assert page.locator('#saveSignIn').is_visible()
 assert page.locator('#saveStatus').inner_text()==''
 names=[page.locator('#'+x).inner_text() for x in ['savePNGWith','savePNGWithout','saveZIP','saveJSON','saveNativeShare']]
 assert len(names)==5,names
 page.locator('#artName').fill('A brand new painting')
 page.locator('#saveNew').click()
 page.wait_for_function('window.__stored.length===1')
 new_id=page.evaluate('window.__stored[0].id')
 assert page.evaluate('window.__stored[0].title')=='A brand new painting'
 assert not page.locator('#saveOverlay').evaluate('e=>e.classList.contains("visible")')
 page.evaluate('window.__saveHubTest.open()')
 assert page.locator('#saveOverwrite').is_enabled()
 page.locator('#artName').fill('Updated painting')
 page.locator('#saveOverwrite').click()
 page.wait_for_function('window.__stored.length===2')
 assert page.evaluate('window.__stored[1].id')==new_id
 assert page.evaluate('window.__stored[1].title')=='Updated painting'
 page.evaluate('window.__saveHubTest.open()')
 # Publishing while unsigned does not upload or take a detour into another dialog.
 page.locator('#savePublish').click()
 assert page.evaluate('window.__publishes.length')==0
 assert 'Sign in' in page.locator('#saveStatus').inner_text()
 page.evaluate('window.__saveHubTest.login()')
 assert not page.locator('#saveSignIn').is_visible()
 page.locator('#artName').fill('Public art name')
 page.locator('#savePublishBackground').uncheck()
 page.locator('#savePublish').click()
 page.wait_for_function('window.__publishes.length===1')
 assert page.evaluate('window.__publishes[0].data.title')=='Public art name'
 assert page.evaluate('window.__shareArgs')=={'resize':True,'withPaper':False}
 assert page.locator('#savePublicLinkWrap').is_visible()
 assert page.locator('#savePublicLink').input_value()=='https://paint-lab.xyz/p/ABCDEFGHIJKLMNOPQRSTUVWX1234567890'
 assert page.locator('#saveOverlay').evaluate('e=>e.classList.contains("visible")')
 # Exports are direct and use the draft title; no intermediate modal.
 page.locator('#artName').fill('Export revised name')
 page.locator('#savePNGWith').click()
 page.wait_for_function('window.__downloads.length===1')
 page.locator('#savePNGWithout').click()
 page.wait_for_function('window.__downloads.length===2')
 page.locator('#saveJSON').click()
 page.wait_for_function('window.__downloads.length===3')
 page.locator('#saveZIP').click()
 page.wait_for_function('window.__downloads.length===4')
 names=page.evaluate('window.__downloads.map(x=>x.name)')
 assert names==['Export-revised-name-paper.png','Export-revised-name-transparent.png','Export-revised-name.json','Export-revised-name.paintlab.zip'],names
 # Saving before clearing cannot overwrite and only clears after Save as new.
 page.evaluate('window.__saveHubTest.clearFlow()')
 assert page.locator('#saveOverwrite').is_disabled()
 page.locator('#saveNew').click()
 page.wait_for_function('window.__clearCount===1')
 assert page.evaluate('window.__stored.length')==3
 assert page.evaluate('window.__saveHubTest.currentId()') is None
 page.evaluate('window.__saveHubTest.open()')
 assert page.locator('#saveOverwrite').is_disabled()
 layout=page.evaluate('''()=>{
  const dialog=document.querySelector('.save-hub-dialog'),body=document.querySelector('.save-hub-body');
  const a=dialog.getBoundingClientRect(),b=body.getBoundingClientRect();
  return {width:innerWidth,height:innerHeight,dialog:{x:a.x,y:a.y,width:a.width,height:a.height},body:{height:b.height,scrollHeight:body.scrollHeight,overflow:getComputedStyle(body).overflowY},pageScroll:document.documentElement.scrollWidth};
 }''')
 assert layout['dialog']['height']<=layout['height']+2,layout
 assert layout['dialog']['height']<470,layout
 assert layout['dialog']['x']>=-1 and layout['dialog']['x']+layout['dialog']['width']<=layout['width']+2,layout
 assert layout['pageScroll']<=layout['width']+2,layout
 page.screenshot(path=f'/mnt/data/paintlab_compact_save_v0147_{kind}.png')
 print('PASS',kind,'save-new/overwrite/publish/download/clear safeguards',layout)
 assert not errors,errors
 context.close()

if __name__=='__main__':
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=swiftshader'])
  run(browser,{'width':1280,'height':820},'desktop')
  run(browser,{'width':390,'height':780},'mobile')
  browser.close()
