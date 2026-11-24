#!/usr/bin/env python3
"""Chromium smoke for Paint Lab v0.1.71 native reference and palette editing."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
MARKER='})();\n</script></body></html>'
assert HTML.count(MARKER)==1
HOOK=r'''
window.__reference171={
 async run(){
   // Build a native 120x60 solid-red image and import as an independent guide.
   baseW=400;baseH=300;resize(false);
   layers=[createLayer({id:'base-layer',name:'Paint'})];activeLayerId='base-layer';ensureLayer();markPaint();
   const source=document.createElement('canvas');source.width=120;source.height=60;
   source.getContext('2d').fillStyle='#ff0000';source.getContext('2d').fillRect(0,0,120,60);
   const blob=await new Promise(r=>source.toBlob(r,'image/png'));
   const file=new File([blob],'guide.png',{type:'image/png'});
   await importReferenceImage(file);
   await new Promise((resolve,reject)=>{let n=0;const check=()=>{if(referenceImage)return resolve();if(++n>100)return reject(Error('reference failed to decode'));setTimeout(check,20)};check()});
   renderLayers();
   const first=referenceRecord;
   if(!first||first.width!==120||first.height!==60||!document.querySelector('#referenceLayerRow'))throw Error('missing native guide');
   if(document.querySelector('#referenceSlot').lastElementChild.id!=='referenceLayerRow')throw Error('guide is not bottom-pinned');
   if(document.querySelector('#referenceLayerRow input[aria-label="Reference Opacity"]')===null)throw Error('opacity not exposed');
   composeLayers();
   const centerPixel=layerCtx.getImageData(Math.round(first.x*dpr),Math.round(first.y*dpr),1,1).data;
   const publishedPixel=createExportCanvas(false).getContext('2d').getImageData(200,150,1,1).data;
   if(centerPixel[0]<200||centerPixel[3]<120||publishedPixel[3]!==0)throw Error('guide composited incorrectly into paint/export');
   const imageSource=first.image;
   first.scale*=1.2;first.angle=42;first.x+=15;first.y-=9;referenceChanged();
   first.scale/=1.2;first.angle=0;
   if(first.image!==imageSource||referenceImage.naturalWidth!==120)throw Error('destructive resampling');
   const moveStart=first.x,historyBefore=actions.length;
   referenceMoveMode=true;
   inputDown({button:0,pointerType:'mouse',pointerId:171,clientX:400,clientY:380,timeStamp:10,preventDefault(){}});
   inputMove({button:0,pointerType:'mouse',pointerId:171,clientX:430,clientY:380,timeStamp:20,preventDefault(){}});
   inputUp({button:0,pointerType:'mouse',pointerId:171,clientX:430,clientY:380,timeStamp:30,preventDefault(){}});
   referenceMoveMode=false;
   if(first.x===moveStart||actions.length!==historyBefore)throw Error('dragging guide changed painting or did not move');
   const encoded=projectData();
   if(encoded.reference?.image!==imageSource)throw Error('reference not persisted');
   if(!loadProject(encoded,null,true))throw Error('loadProject failed');
   await new Promise((resolve,reject)=>{let n=0;const check=()=>{if(referenceImage)return resolve();if(++n>100)return reject(Error('reopen failed'));setTimeout(check,20)};check()});
   if(referenceRecord.x!==first.x||referenceRecord.angle!==0||referenceImage.naturalHeight!==60)throw Error('reference transform not restored');
   const savedReference=referenceRecord.image;
   setPalette(PALETTES.Studio.slice(),'Studio');selectPaletteSwatch(23);
   editSelectedPaletteSwatch('#12ab34');
   if(palette[23]!=='#12ab34'||paletteSource[23]!=='#12ab34')throw Error('selected gradient end cannot be edited');
   if(selectedPaletteIndex!==23)throw Error('selection lost after edit');
   colorTravel=true;colorTravelPingPong=true;
   const cfg={color:'#111111',colorTravel,colorTravelPingPong,travelPalette:['#110000','#220000','#330000'],size:30};
   if(strokeTravelColour(cfg,0)!=='#110000'||strokeTravelColour(cfg,18)!=='#330000'||strokeTravelColour(cfg,27)!=='#220000'||strokeTravelColour(cfg,36)!=='#110000')throw Error('ping-pong flow incorrect');
   if(!currentSettings().colorTravelPingPong||!projectData().colorTravelPingPong)throw Error('ping pong not persisted');
   const link=$('saveOpenLink');$('savePublicLinkWrap').hidden=false;
   if(getComputedStyle(link).textDecorationLine!=='none'||link.target!=='_blank'||!link.rel.includes('noopener'))throw Error('Open link does not behave as a safe button');
   return {reference:[referenceImage.naturalWidth,referenceImage.naturalHeight],referenceOpacity:first.opacity,
     paintingOpacity:centerPixel[3],exportOpacity:publishedPixel[3],paletteEnd:palette[23],
     referenceSaved:savedReference===imageSource,bounce:true,openLinkStyle:getComputedStyle(link).textDecorationLine};
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
    page.set_content(HTML,wait_until='domcontentloaded',timeout=50000)
    page.wait_for_function('!!window.__reference171',timeout=20000)
    result=page.evaluate('async()=>await window.__reference171.run()')
    assert result['reference']==[120,60] and result['exportOpacity']==0 and result['paletteEnd']=='#12ab34',result
    assert not errors,errors
    print(('Mobile' if mobile else 'Desktop')+' Paint Lab v0.1.71 smoke PASS '+str(result))
    page.close()
  browser.close()
