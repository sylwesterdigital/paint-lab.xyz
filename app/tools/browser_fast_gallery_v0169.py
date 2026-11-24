from pathlib import Path
from playwright.sync_api import sync_playwright
html=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
html=html.replace('const confirmAction=', 'let confirmAction=')
hook=r'''
window.__fastSaveTest={
 init(){
  galleryDb={};storeRecord=async item=>{window.__lastSaved=item;};confirmAction=async()=>true;
  actions=[];head=0;flatHistoryBase=null;preserveSavedStrokeHistory=false;
  layers=[createLayer({id:'base-layer',name:'Base paint'})];activeLayerId='base-layer';ensureLayer();
  layers[0].ctx.fillStyle='#ff0000';layers[0].ctx.fillRect(10,10,35,35);markPaint();
  artName='Red test';artId=null;
  const c=$('saveStrokeHistory');openSave();return {checked:c.checked, link:document.querySelector('.paint-lab-brand-link[href="/explore"]')?.textContent};
 },
 async save(keep){
  $('saveStrokeHistory').checked=keep;
  const good=await saveGallery(true);const r=window.__lastSaved;
  return {good,history:r?.data.actions.length,snapshot:r?.rasterLayers?.length,historyFlag:r?.keepStrokeHistory,blob:r?.rasterLayers?.[0]?.blob instanceof Blob,hasBase:!!r?.baseRasterLayers?.length};
 },
 async load(){
  const r=window.__lastSaved;
  await openSavedGalleryArtwork(r);
  return {red:layers[0]?.ctx.getImageData(12,12,1,1).data[0],history:actions.length,hasBase:!!flatHistoryBase?.length,openingArtwork};
 },
 rebuild(){
  const before=layers[0].ctx.getImageData(12,12,1,1).data[0];
  actions.push({kind:'canvas-clear',resetLayers:false});head=actions.length;rebuild();
  const cleared=layers[0].ctx.getImageData(12,12,1,1).data[0];
  head=0;rebuild();
  const restored=layers[0].ctx.getImageData(12,12,1,1).data[0];
  return {before,cleared,restored};
 },
 async fullHistory(){
  actions=[{kind:'stroke',layerId:'base-layer',cfg:snapshot(),points:[{x:12,y:12,p:1}],seed:1,start:Date.now()}];head=1;artId=null;artName='Keep stroke';
  openSave();return {defaultChecked:$('saveStrokeHistory').checked};
 },
 async portable(){
  const doc=exportEmbeddedBaseline(projectData());doc.actions=[];doc.head=0;
  const has=!!doc.flatBaseline?.[0]?.png;
  await loadPortableDocument(doc,null);
  return {has,red:layers[0]?.ctx.getImageData(12,12,1,1).data[0]};
 }
};
'''
marker='})();\n</script></body></html>'
assert html.count(marker)==1
html=html.replace(marker,hook+marker)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None),headless=True,args=['--disable-gpu','--use-gl=angle','--use-angle=swiftshader'])
 page=browser.new_page(viewport={'width':1100,'height':790})
 errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
 page.set_content(html,wait_until='domcontentloaded',timeout=45000)
 page.wait_for_function('!!window.__fastSaveTest',timeout=30000)
 init=page.evaluate('()=>window.__fastSaveTest.init()')
 assert init=={'checked':False,'link':'Public gallery'},init
 save=page.evaluate('async()=>await window.__fastSaveTest.save(false)')
 assert save['good'] and save['history']==0 and save['snapshot']==1 and save['blob'] and not save['historyFlag'],save
 loaded=page.evaluate('async()=>await window.__fastSaveTest.load()')
 assert loaded['red']==255 and loaded['history']==0 and loaded['hasBase'] and not loaded['openingArtwork'],loaded
 undo=page.evaluate('()=>window.__fastSaveTest.rebuild()')
 assert undo=={'before':255,'cleared':0,'restored':255},undo
 portable=page.evaluate('async()=>await window.__fastSaveTest.portable()')
 assert portable=={'has':True,'red':255},portable
 full=page.evaluate('()=>window.__fastSaveTest.fullHistory()')
 assert full['defaultChecked']==False,full
 saved=page.evaluate('async()=>await window.__fastSaveTest.save(true)')
 assert saved['good'] and saved['history']==1 and saved['historyFlag'] and saved['blob'],saved
 loaded=page.evaluate('async()=>await window.__fastSaveTest.load()')
 assert loaded['red']==255 and loaded['history']==1 and not loaded['openingArtwork'],loaded
 assert not errors, errors
 mobile=browser.new_page(viewport={'width':390,'height':780},is_mobile=True,has_touch=True)
 mobile.set_content(html,wait_until='domcontentloaded',timeout=45000)
 mobile.wait_for_function('!!window.__fastSaveTest',timeout=30000)
 mobile.evaluate('()=>window.__fastSaveTest.init()')
 dialog=mobile.locator('#saveOverlay .dialog').bounding_box()
 print('Mobile save panel height',dialog['height'])
 assert dialog['height']<390,dialog
 print('Browser smoke PASS',{'init':init,'fastSave':save,'fastLoad':loaded,'undo':undo,'portable':portable,'historySave':saved})
 browser.close()
