#!/usr/bin/env python3
"""Chromium acceptance test: stylization operates on existing raster layer pixels."""
from pathlib import Path
from playwright.sync_api import sync_playwright

html=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
hook='''
window.__layerFilterQA={
 undo:()=>undo(), redo:()=>redo(),
 engine:()=>{const c={...snapshot(),material:'oil',mode:0,strokeStyle:'invert',styleEngine:'layer-fx-v1',size:44},s={cfg:c,points:[{x:65,y:180,pressure:1,t:0},{x:175,y:185,pressure:1,t:15}],seed:13};drawStrokeStart(s);drawStrokeStep(s,s.points[1]);return {oil:!!s._run?.oilBristles,pencil:continuousPencil({cfg:{...c,material:'pencil',pencilEngine:'continuous-v1'}})};},
 setup:()=>{ensureLayer();const l=activeLayer();const g=l.ctx;
  g.save();g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,l.canvas.width,l.canvas.height);
  for(let x=40;x<300;x++)for(let y=45;y<125;y++){
    g.fillStyle=`rgb(${Math.round(40+x*.55)},${Math.round(25+y*.75)},${Math.round(110+x*.2)})`;
    g.fillRect(x,y,1,1);
  }
  g.restore();markPaint();return {w:l.canvas.width,h:l.canvas.height};
 },
 stats:()=>{const l=activeLayer(),src=l.ctx.getImageData(0,0,l.canvas.width,l.canvas.height).data;
  const f=getLayerRenderCanvas(l),d=f.getContext('2d',{willReadFrequently:true}).getImageData(0,0,f.width,f.height).data;
  const pixel=(data,x,y)=>Array.from(data.slice((y*l.canvas.width+x)*4,(y*l.canvas.width+x)*4+4));
  const points=[[72,64],[75,66],[84,67],[102,70],[121,91],[300,300]];
  return {filters:cloneLayerFilters(l.filters),style:strokeStyle,source:points.map(([x,y])=>pixel(src,x,y)),rendered:points.map(([x,y])=>pixel(d,x,y)),history:head,kind:actions[head-1]?.kind,label:$('layerFilterTarget').textContent};
 },
 project:async()=>{const zip=await createProjectZIP();const files=readPortableZIP(new Uint8Array(await zip.arrayBuffer()));const doc=JSON.parse(archiveDecoder.decode(files.get('project.json')));return {version:doc.document.version,filters:doc.layers[0]?.filters,actions:doc.document.actions.filter(x=>x.kind==='layer-filter').length};}
};
'''
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in html
html=html.replace(anchor,hook+'\n'+anchor,1)

def run():
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  page=browser.new_page(viewport={'width':1150,'height':760})
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded',timeout=35000)
  page.wait_for_timeout(200)
  canvas=page.evaluate('__layerFilterQA.setup()')
  initial=page.evaluate('__layerFilterQA.stats()')
  assert not initial['filters'] and initial['source'][0]!=initial['source'][1],initial
  # Actual button invokes the same handler as a real user click.
  page.evaluate('document.querySelector(`[data-stroke-style="pixelate"]`).click()')
  filtered=page.evaluate('__layerFilterQA.stats()')
  assert filtered['kind']=='layer-filter' and len(filtered['filters'])==1,filtered
  assert filtered['filters'][0]['kind']=='pixelate',filtered
  assert filtered['source']==initial['source'],'A layer filter must not paint on its source canvas'
  assert filtered['rendered'][0]==filtered['rendered'][1],filtered
  assert filtered['rendered'][0]!=filtered['source'][0],filtered
  assert '1 applied filter' in filtered['label'],filtered
  assert filtered['style']=='pixelate'
  engine=page.evaluate('__layerFilterQA.engine()')
  assert engine['oil'] and engine['pencil'],engine
  # Slider changes render immediately and commit a single undoable filter action.
  page.evaluate('''()=>{const r=document.getElementById('styleCell');r.value=56;r.dispatchEvent(new Event('input',{bubbles:true}));}''')
  drag=page.evaluate('__layerFilterQA.stats()')
  assert drag['filters'][0]['cell']==56,drag
  assert drag['history']==filtered['history'],(drag,filtered)
  page.evaluate('document.getElementById("styleCell").dispatchEvent(new Event("change",{bubbles:true}))')
  after=page.evaluate('__layerFilterQA.stats()')
  assert after['history']==filtered['history']+1,after
  assert after['filters'][0]['cell']==56,after
  page.evaluate('__layerFilterQA.undo()')
  undo=page.evaluate('__layerFilterQA.stats()')
  assert undo['filters'][0]['cell']==24,undo
  page.evaluate('__layerFilterQA.redo()')
  redo=page.evaluate('__layerFilterQA.stats()')
  assert redo['filters'][0]['cell']==56,redo
  # Multiple effects are actual composited stack actions, not brush stamps.
  page.evaluate('document.querySelector(`[data-stroke-style="halftone"]`).click()')
  stacked=page.evaluate('__layerFilterQA.stats()')
  assert [x['kind'] for x in stacked['filters']]==['pixelate','halftone'],stacked
  exported=page.evaluate('__layerFilterQA.project()')
  assert exported['version']==4 and len(exported['filters'])==2 and exported['actions']>=3,exported
  page.evaluate('document.querySelector(`[data-stroke-style="none"]`).click()')
  cleared=page.evaluate('__layerFilterQA.stats()')
  assert not cleared['filters'],cleared
  page.evaluate('__layerFilterQA.undo()')
  restored=page.evaluate('__layerFilterQA.stats()')
  assert len(restored['filters'])==2,restored
  assert not errors,errors
  browser.close()
  print('PASS: one-click pixel effect, source immutability, real image-space blocks, live slider, undo/redo, stacked filters, portable ZIP')
  print('canvas',canvas,'source RGBA',initial['source'][:3],'pixel RGBA',filtered['rendered'][:3],'filters',restored['filters'])

if __name__=='__main__':run()
