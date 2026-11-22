#!/usr/bin/env python3
"""Real Chromium regression: brush reveals a filtered COPY OF EXISTING imagery.
The brush paints only an alpha mask. It must never add its own pigment as image data.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
HOOK=r'''
window.__revealQA={
 reset:()=>{
  baseW=640;baseH=360;resize(false);actions=[];head=0;rebuild();
  const l=activeLayer();l.filters=[];invalidateLayerFilterCache(l);strokeStyle='none';
  return {w:l.canvas.width,h:l.canvas.height};
 },
 brush:(kind,layer=activeLayerId,material='chalk',from=145,to=470,y=177)=>{
  const cfg={...snapshot(),mode:0,material,tip:'round',size:74,flow:1,
    strength:1,wetness:.3,density:.95,paintLoad:1,scatter:0,
    color:kind?'#ed1737':'#2174c8',
    styleEngine:'existing-image-fx-v3',
    strokeEffect:kind?{kind,cell:25,amount:1}:null};
  const points=Array.from({length:19},(_,i)=>({x:from+(to-from)*i/18,y,pressure:1,t:i*14,tilt:0,twist:0}));
  const s={kind:'stroke',layerId:layer,cfg,seed:779,points,start:points[0],time:Date.now()};
  usePaintLayer(layers.find(l=>l.id===layer));
  drawStrokeStart(s);for(let i=1;i<points.length;i++)drawStrokeStep(s,points[i]);
  const preview=renderStrokeImageFX(s);
  let previewCount=0;
  if(preview){const d=preview.canvas.getContext('2d',{willReadFrequently:true}).getImageData(0,0,preview.canvas.width,preview.canvas.height).data;
   for(let i=3;i<d.length;i+=4)if(d[i]>50)previewCount++;}
  finishStrokeRender(s);if(hasStrokeImageFX(s))commitStrokeImageFX(s);commit(s);
  return {version:s.cfg.styleEngine,preview:!!preview,previewCount,head};
 },
 color:(x,y,which='layer')=>{const l=activeLayer(),ctx=which==='merged'?(
  (compositeDirty&&composeLayers(),layerCtx)):l.ctx;
  return Array.from(ctx.getImageData(x,y,1,1).data);},
 checks:()=>{
  const l=activeLayer(),w=l.canvas.width,h=l.canvas.height;
  const data=l.ctx.getImageData(0,0,w,h).data;
  let hash=2166136261,count=0,red=0,blue=0;
  for(let y=115;y<245;y+=3)for(let x=110;x<510;x+=3){const i=(y*w+x)*4;
   for(let c=0;c<4;c++)hash=Math.imul(hash^data[i+c],16777619);
   if(data[i+3]>100){count++;if(data[i]>data[i+2]*1.3)red++;if(data[i+2]>data[i]*1.3)blue++;}}
  return {hash:hash>>>0,count,red,blue,head};
 },
 alphaCount:()=>{const l=activeLayer(),d=l.ctx.getImageData(0,0,l.canvas.width,l.canvas.height).data;
   let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>20)n++;return n;},
 newLayer:()=>{const previous=activeLayerId,layerId=id();layerAction({kind:'layer-add',layerId:previous,newId:layerId,name:'Filtered reveal'});setSelectedLayers([layerId],layerId);return layerId;},
 undo:()=>undo(),redo:()=>redo(),rebuild:()=>rebuild(),preset:(name)=>document.querySelector('[data-stroke-style="'+name+'"]').click(),
 current:()=>({style:strokeStyle,filters:activeLayer().filters.length,version:snapshot().styleEngine})
};
'''
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in HTML
HTML=HTML.replace(anchor,HOOK+'\n'+anchor,1)

def main():
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  page=browser.new_page(viewport={'width':1080,'height':770},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(HTML,wait_until='domcontentloaded',timeout=40000)
  page.wait_for_timeout(200)
  def ev(script,*args):return page.evaluate(script,*args) if args else page.evaluate(script)
  # Absolutely no source data means the stroke mask cannot add paint, regardless of selected colour.
  ev('__revealQA.reset()');before=ev('__revealQA.checks()')
  empty=ev('()=>__revealQA.brush("pixelate")');after=ev('__revealQA.checks()')
  assert empty['version']=='existing-image-fx-v3' and before['hash']==after['hash'] and after['count']==0,('empty must remain blank',empty,before,after)
  for kind in ['pixelate','halftone','ascii','symbols','mosaic','invert']:
   ev('__revealQA.reset()');ev('()=>__revealQA.brush(null)');source=ev('__revealQA.checks()')
   assert source['blue']>0 and source['red']==0,('source',kind,source)
   ev('(kind)=>__revealQA.preset(kind)',kind)
   assert ev('__revealQA.checks()')==source,('selection changed artwork',kind)
   result=ev('(kind)=>__revealQA.brush(kind)',kind);converted=ev('__revealQA.checks()')
   assert converted['hash']!=source['hash'] and result['previewCount']>0,('did not transform existing image',kind,result,source,converted)
   assert kind=='invert' or converted['red']==0,('applied new red pigment instead of sampling existing artwork',kind,converted)
   ev('__revealQA.undo()');undone=ev('__revealQA.checks()')
   assert undone['hash']==source['hash'],('undo changed source',kind,undone,source)
   ev('__revealQA.redo()');redone=ev('__revealQA.checks()')
   assert redone['hash']==converted['hash'],('redo not deterministic',kind,redone,converted)
   ev('__revealQA.rebuild()');replayed=ev('__revealQA.checks()')
   assert replayed['hash']==converted['hash'],('reload changed output',kind,replayed,converted)
  # An empty active layer can still reveal previously painted lower-layer imagery.
  ev('__revealQA.reset()');ev('()=>__revealQA.brush(null)')
  base=ev('__revealQA.checks()');ev('__revealQA.newLayer()')
  assert ev('__revealQA.checks()')['count']==0, 'new layer should begin transparent'
  preview=ev('()=>__revealQA.brush("pixelate")')
  upper=ev('__revealQA.checks()')
  assert upper['count']>0 and upper['blue']>0 and upper['red']==0,('lower layer not sampled',preview,upper)
  assert not errors, errors
  browser.close()
  print('PASS Chromium v0.1.36: blank image stays blank, existing paint converted without red pigment, preset selection untouched, Pixel/Halftone/ASCII/Symbols/Mosaic/Invert, undo/redo/rebuild deterministic, underlying layers sampled, JS error-free')
if __name__=='__main__':main()
