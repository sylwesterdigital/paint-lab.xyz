#!/usr/bin/env python3
"""Chromium acceptance: stylization transforms the painted stroke image, never whole layer/underlay."""
from pathlib import Path
from playwright.sync_api import sync_playwright
HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
HOOK=r'''
window.__strokeFXQA={
 setup:()=>{
  baseW=650;baseH=350;resize(false);rebuild();ensureLayer();const l=activeLayer();l.filters=[];invalidateLayerFilterCache(l);
  l.ctx.save();l.ctx.setTransform(1,0,0,1,0,0);l.ctx.clearRect(0,0,l.canvas.width,l.canvas.height);
  l.ctx.fillStyle='rgb(15,25,215)';l.ctx.fillRect(35,35,60,60);l.ctx.restore();
  actions=[];head=0;strokeStyle='none';markPaint();return {w:l.canvas.width,h:l.canvas.height};
 },
 pixel:(x,y)=>{const l=activeLayer(),d=l.ctx.getImageData(x,y,1,1).data;return Array.from(d)},
 image:()=>{const l=activeLayer(),w=l.canvas.width,d=l.ctx.getImageData(0,0,w,l.canvas.height).data;let hash=2166136261,alpha=0;for(let y=110;y<300;y++)for(let x=125;x<Math.min(w,630);x++){let i=(y*w+x)*4;hash=Math.imul(hash^d[i],16777619);hash=Math.imul(hash^d[i+1],16777619);hash=Math.imul(hash^d[i+2],16777619);hash=Math.imul(hash^d[i+3],16777619);alpha+=d[i+3]>20?1:0;}return {hash:hash>>>0,alpha}},
 current:()=>({style:strokeStyle,filters:activeLayer().filters.length,actions:head}),
 preset:(name)=>document.querySelector('[data-stroke-style="'+name+'"]').click(),
 stroke:(kind='pixelate',material='oil',commitToHistory=true)=>{
  const cfg={...snapshot(),material,mode:0,tip:'round',size:72,
   color:'#d84c43',strength:1,flow:1,wetness:.35,paintLoad:1,
   strokeEffect:kind==='none'?null:{kind,cell:26,amount:1},styleEngine:'stroke-fx-v2'};
  const p=[];for(let i=0;i<=18;i++){
   const q=i/18;p.push({x:180+i*19,y:170+Math.sin(q*Math.PI*1.4)*32,pressure:1,t:i*12,tilt:0,twist:0});
  }
  const s={kind:'stroke',layerId:activeLayerId,cfg,seed:313,points:p,start:p[0],time:Date.now()};
  drawStrokeStart(s);for(let i=1;i<p.length;i++)drawStrokeStep(s,p[i]);
  const preview=renderStrokeImageFX(s),state={
   fx:!!s._strokeFX, preview:preview?{
    w:preview.canvas.width,h:preview.canvas.height,x:preview.x,y:preview.y,
    alphaCount:(()=>{const d=preview.canvas.getContext('2d',{willReadFrequently:true}).getImageData(0,0,preview.canvas.width,preview.canvas.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>25)n++;return n;})()
   }:null,
   beforeCommit:window.__strokeFXQA.pixel(250,195)};
  finishStrokeRender(s);if(hasStrokeImageFX(s))commitStrokeImageFX(s);
  if(commitToHistory)commit(s);return state;
 },
 history:()=>({head,actions:actions.length,kind:actions[head-1]?.kind,fx:actions[head-1]?.cfg?.strokeEffect}),
 undo:()=>undo(),redo:()=>redo(),
 replay:()=>rebuild()
};
'''
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in HTML
HTML=HTML.replace(anchor,HOOK+'\n'+anchor,1)

def run():
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  page=browser.new_page(viewport={'width':1150,'height':760},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(HTML,wait_until='domcontentloaded',timeout=40000)
  page.wait_for_timeout(150)
  setup=page.evaluate('__strokeFXQA.setup()')
  ref=page.evaluate('__strokeFXQA.image()')
  page.evaluate('__strokeFXQA.preset("pixelate")')
  selected=page.evaluate('__strokeFXQA.current()')
  after_select=page.evaluate('__strokeFXQA.image()')
  assert after_select==ref,'Selecting Pixel incorrectly changes existing layer pixels'
  assert selected['style']=='pixelate' and selected['filters']==0 and selected['actions']==0,selected
  pixel_preview=page.evaluate('__strokeFXQA.stroke("pixelate","oil")')
  assert pixel_preview['fx'] and pixel_preview['preview']['alphaCount']>200,pixel_preview
  assert pixel_preview['beforeCommit'][3]==0,pixel_preview
  pixel_result=page.evaluate('__strokeFXQA.image()')
  assert pixel_result!=ref and page.evaluate('__strokeFXQA.pixel(50,50)')==[15,25,215,255], 'Existing paint changed unexpectedly'
  history=page.evaluate('__strokeFXQA.history()')
  assert history['head']==1 and history['kind']=='stroke' and history['fx']['kind']=='pixelate',history
  page.evaluate('__strokeFXQA.undo()')
  undid=page.evaluate('__strokeFXQA.image()')
  assert undid['alpha']==0, 'Undo did not remove the stylized stroke'
  page.evaluate('__strokeFXQA.redo()')
  redid=page.evaluate('__strokeFXQA.image()')
  assert redid==pixel_result,'Replay did not reproduce the filtered stroke pixels'
  page.evaluate('__strokeFXQA.setup()')
  normal_preview=page.evaluate('__strokeFXQA.stroke("none","oil")')
  normal=page.evaluate('__strokeFXQA.image()')
  assert normal!=pixel_result, 'Pixel output is indistinguishable from original bristle paint'
  for kind in ['halftone','ascii','symbols','mosaic','invert']:
   page.evaluate('__strokeFXQA.setup()')
   p=page.evaluate('(k)=>__strokeFXQA.stroke(k,"chalk")',kind)
   img=page.evaluate('__strokeFXQA.image()')
   assert p['preview']['alphaCount']>0 and img!=ref,(kind,p)
   assert page.evaluate('__strokeFXQA.pixel(50,50)')==[15,25,215,255],kind
  assert not errors,errors
  browser.close()
  print('PASS v0.1.35 Chromium: no change on selection, RGBA stroke preview, painted-stroke transform, source-layer preservation, distinct pixel blocks, undo/redo and deterministic replay, additional filters')
  print('document',setup,'pixel preview',pixel_preview['preview'],'action',history)
if __name__=='__main__':run()
