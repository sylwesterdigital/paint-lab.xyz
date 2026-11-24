#!/usr/bin/env python3
"""Paint Lab v0.1.73 browser test: native reference as a selectable pseudo-layer."""
from pathlib import Path
from playwright.sync_api import sync_playwright
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
MARKER='})();\n</script></body></html>'
assert HTML.count(MARKER)==1
HOOK=r'''
window.__reference173={
 async run(){
   baseW=400;baseH=300;resize(false);
   layers=[createLayer({id:'base-layer',name:'Paint'})];activeLayerId='base-layer';ensureLayer();markPaint();
   const source=document.createElement('canvas');source.width=120;source.height=60;
   source.getContext('2d').fillStyle='#ef2300';source.getContext('2d').fillRect(0,0,120,60);
   const blob=await new Promise(r=>source.toBlob(r,'image/png'));
   await importReferenceImage(new File([blob],'native-guide.png',{type:'image/png'}));
   await new Promise((resolve,reject)=>{let n=0;const check=()=>{if(referenceImage)return resolve();if(++n>100)return reject(Error('image did not decode'));setTimeout(check,20)};check()});
   renderLayers();
   const list=$('layersList'),row=$('referenceLayerRow');
   if(!row||list.lastElementChild!==row||!row.classList.contains('layer-row'))throw Error('reference is not a normal bottom row');
   if(document.querySelector('.reference-adjustments, #referenceSlot'))throw Error('duplicate transform UI still present');
   if(!row.querySelector('.layer-thumb,.reference-layer-thumb'))throw Error('reference thumbnail missing');
   if(!row.querySelector('button[aria-label="Hide reference"]'))throw Error('reference visibility missing');
   const r=referenceRecord,src=r.image,originalWidth=referenceImage.naturalWidth;
   if(!referenceSelected||!row.classList.contains('selected'))throw Error('reference not selected');
   if(selectTransformTarget()?.targetKind!=='reference')throw Error('normal transforms do not target reference');
   const save={x:r.x,y:r.y,scale:r.scale,angle:r.angle};
   // Same transform functions and action lifecycle used for normal paint layers.
   if(!isMobileWorkspace()){
     if(!beginDesktopTransform('move'))throw Error('G move did not begin');
   }else{
     setTransformMode('move');
     if(!activeTransformFromPointer({pointerId:23,clientX:300,clientY:260,timeStamp:1}))throw Error('mobile Move did not begin');
   }
   if(active?.targetKind!=='reference')throw Error('G transform target changed');
   active.spec={pivot:{x:r.x,y:r.y},dx:29,dy:-18,scale:1,angle:0};
   compositeDirty=true;composeLayers();finishTransform(true);
   if(Math.abs(r.x-save.x-29)>.001||Math.abs(r.y-save.y+18)>.001)throw Error('G move did not commit');
   if(!isMobileWorkspace()){
     beginDesktopTransform('rotate');
   }else{
     setTransformMode('rotate');activeTransformFromPointer({pointerId:24,clientX:310,clientY:290,timeStamp:2});
   }
   active.spec={pivot:{x:r.x,y:r.y},dx:0,dy:0,scale:1,angle:Math.PI/4};finishTransform(true);
   if(Math.abs(r.angle-45)>.05)throw Error('R rotate not committed');
   if(!isMobileWorkspace()){
     beginDesktopTransform('scale');
   }else{
     setTransformMode('scale');activeTransformFromPointer({pointerId:25,clientX:310,clientY:290,timeStamp:3});
   }
   const oldScale=r.scale;
   active.spec={pivot:{x:r.x,y:r.y},dx:0,dy:0,scale:1.6,angle:0};finishTransform(true);
   if(Math.abs(r.scale-oldScale*1.6)>.001)throw Error('S scale not committed');
   if(r.image!==src||referenceImage.naturalWidth!==originalWidth)throw Error('reference pixels changed');
   // Cancel should restore exactly, without changing the source or transform.
   if(!isMobileWorkspace()){
     beginDesktopTransform('move');active.spec={pivot:{x:r.x,y:r.y},dx:110,dy:0,scale:1,angle:0};cancelDesktopTransform();
   }else{
     setTransformMode('move');activeTransformFromPointer({pointerId:26,clientX:310,clientY:290,timeStamp:4});active.spec={pivot:{x:r.x,y:r.y},dx:110,dy:0,scale:1,angle:0};finishTransform(false);
   }
   if(Math.abs(r.x-save.x-29)>.001)throw Error('cancel mutated guide');
   const p=r.x,q=r.y; referenceSelected=true;
   if(!isMobileWorkspace()){
     const slider=$('referenceLayerRow').querySelector('input[aria-label="Opacity for Reference"]');
     slider.value='31';slider.dispatchEvent(new Event('input',{bubbles:true}));slider.dispatchEvent(new Event('change',{bubbles:true}));
   }else{
     openMobileLayerOpacity('reference');const slider=$('mobileLayerOpacityRange');slider.value='31';slider.dispatchEvent(new Event('input',{bubbles:true}));slider.dispatchEvent(new Event('change',{bubbles:true}));
   }
   if(Math.abs(r.opacity-.31)>.001)throw Error('native reference opacity control failed');
   composeLayers();
   const data=projectData();if(!data.reference||data.reference.image!==src)throw Error('native guide not persisted');
   if(!loadProject(data,null,true))throw Error('project reopen failed');
   await new Promise((resolve,reject)=>{let n=0;const check=()=>{if(referenceImage)return resolve();if(++n>100)return reject(Error('project reference decode failed'));setTimeout(check,20)};check()});
   if(Math.abs(referenceRecord.x-p)>.01||Math.abs(referenceRecord.y-q)>.01||Math.abs(referenceRecord.opacity-.31)>.01||Math.abs(referenceRecord.scale-r.scale)>.01)throw Error('reference metadata not restored');
   if(referenceImage.naturalWidth!==120||document.querySelector('#layersList').lastElementChild.id!=='referenceLayerRow')throw Error('reference pixel/bottom position lost');
   const point=referenceRecord;
   // Output must exclude reference entirely when no paint history exists.
   const out=createExportCanvas(false),pixel=out.getContext('2d').getImageData(200,150,1,1).data;
   if(pixel[3]!==0)throw Error('guide leaked into transparent PNG');
   selectPaintLayer('base-layer');
   if(referenceSelected||selectTransformTarget()?.targetKind!=='layer')throw Error('ordinary paint layer selection broken');
   return {native:[referenceImage.naturalWidth,referenceImage.naturalHeight],move:true,rotate:true,scale:true,cancel:true,opacity:point.opacity,exportAlpha:pixel[3],bottom:true};
 }
};
'''
HTML=HTML.replace(MARKER,HOOK+MARKER)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--disable-gpu','--use-gl=angle','--use-angle=swiftshader'])
 for mobile in (False,True):
  page=browser.new_page(viewport={'width':390 if mobile else 1100,'height':790},is_mobile=mobile,has_touch=mobile)
  page.route('**/*',lambda route: route.abort() if route.request.url.startswith('http') else route.continue_())
  errors=[];page.on('pageerror',lambda error: errors.append(str(error)))
  page.set_content(HTML,wait_until='domcontentloaded',timeout=30000)
  page.wait_for_function('!!window.__reference173',timeout=18000)
  result=page.evaluate('async()=>await window.__reference173.run()')
  assert result['native']==[120,60] and result['exportAlpha']==0,result
  assert not errors,errors
  print(('Mobile' if mobile else 'Desktop')+' unified reference PASS '+str(result),flush=True)
  page.close()
 browser.close()
