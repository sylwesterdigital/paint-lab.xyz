#!/usr/bin/env python3
"""Chromium tests: bounded undo snapshots, replay yielding, branch safety, pixels."""
from pathlib import Path
from playwright.sync_api import sync_playwright

FRONTEND=Path(__file__).resolve().parents[1]/'frontend'
HOOK=r'''
window.__historyQA={
 reset(){cancelHistoryReplay();baseW=460;baseH=270;resize(false);actions=[];head=0;rebuild();return [layerPixelsW,layerPixelsH];},
 stroke(n){
  const cfg={...snapshot(),mode:0,material:'pencil',tip:'round',size:13,strength:1,flow:1,strokeEffect:null,styleEngine:'normal',color:n%2?'#cc3e36':'#2d76c9'};
  const x=40+(n%19)*20,y=40+(Math.floor(n/19)%8)*22;
  const points=[{x,y,pressure:1,t:0},{x:x+15,y:y+3,pressure:1,t:20},{x:x+29,y:y+6,pressure:1,t:40}];
  const a={kind:'stroke',id:'test'+n,layerId:activeLayerId,cfg,points,start:points[0],seed:4891+n,time:Date.now()};
  usePaintLayer(activeLayer());replayStroke(a);commit(a);return head;
 },
 snapshot(){rememberHistoryCheckpoint();return historyCheckpoints.map(s=>s.head);},
 clear(){clearHistoryCheckpoints();return head;},
 stats(){return {head,actions:actions.length,rendering,snapshots:historyCheckpoints.map(s=>s.head),status:document.querySelector('#status').textContent}},
 hash(){
  const w=layerPixelsW,h=layerPixelsH,d=layerCtx;
  if(compositeDirty)composeLayers();
  const src=d.getImageData(0,0,w,h).data;let hash=2166136261,occupied=0;
  for(let y=0;y<h;y+=2)for(let x=0;x<w;x+=2){const i=(y*w+x)*4;hash=Math.imul(hash^src[i],16777619);hash=Math.imul(hash^src[i+1],16777619);hash=Math.imul(hash^src[i+2],16777619);hash=Math.imul(hash^src[i+3],16777619);if(src[i+3]>20)occupied++;}
  return {hash:hash>>>0,occupied};
 },
 verify(){const a=this.hash();rebuild();const b=this.hash();return {a,b,equal:a.hash===b.hash&&a.occupied===b.occupied};},
 undo:()=>undo(),redo:()=>redo(),seek:n=>seek(n),
 renameLayer(){const l=activeLayer();layerAction({kind:'layer-props',layerId:l.id,props:{name:'QA layer'}});return l.name;},
 newLayer(){addPaintLayer();return activeLayerId;},
 editShape(){
  const cfg={...snapshot(),size:5,fillMode:'none',outlineMode:'clean'};
  const shape={kind:'shape',id:'qa-shape',layerId:activeLayerId,shape:'ellipse',a:{x:110,y:120},b:{x:160,y:170},cfg,seed:99,time:Date.now()};
  drawShape(paint,shape);commit(shape);
  return shape;
 },
 mutateShape(){
  const shape=actions.find(a=>a.id==='qa-shape');
  editShape(shape,{a:{x:160,y:120},b:{x:210,y:170},points:null,rotation:0});
 },
};
'''

def main():
    errors=[]
    html=(FRONTEND/'index.html').read_text()
    anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
    assert anchor in html
    html=html.replace(anchor,HOOK+'\n'+anchor,1)
    with sync_playwright() as p:
      browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
      page=browser.new_page(viewport={'width':980,'height':680},device_scale_factor=1)
      page.on('pageerror',lambda e:errors.append(str(e)))
      page.set_content(html,wait_until='domcontentloaded',timeout=30000)
      page.wait_for_function('!!window.__historyQA',timeout=10000)
      page.wait_for_timeout(250)
      ev=page.evaluate
      ev('__historyQA.reset()')
      for n in range(36):
        ev('(n)=>__historyQA.stroke(n)',n)
        # Explicitly fill cache, including state immediately before last action.
        ev('__historyQA.snapshot()')
      initial=ev('__historyQA.hash()')
      cp=ev('__historyQA.stats()')
      assert cp['snapshots'] and max(cp['snapshots'])==36,cp
      start=ev('performance.now()')
      ev('__historyQA.undo()')
      before=ev('__historyQA.stats()')
      assert not before['rendering'] and before['head']==35,('recent undo did not use checkpoint',before)
      assert ev('__historyQA.verify()')['equal'], 'cached undo differs from deterministic replay'
      ev('__historyQA.redo()')
      assert ev('__historyQA.hash()')==initial, 'redo does not match original pixels'
      fast=round(ev('performance.now()')-start,2)
      # Force a missing cache: reconstruction must yield and finish correctly.
      state=ev('()=>{__historyQA.clear();__historyQA.seek(15);return __historyQA.stats()}')
      assert state['rendering'],('long history replay should be scheduled',state)
      page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      assert ev('__historyQA.verify()')['equal'], 'time-sliced replay pixel mismatch'
      # Rapid navigation must cancel stale batches and settle on latest position.
      ev('__historyQA.clear()')
      ev('__historyQA.seek(33)')
      ev('__historyQA.seek(9)')
      ev('__historyQA.seek(31)')
      page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      assert ev('__historyQA.stats()')['head']==31
      assert ev('__historyQA.verify()')['equal'], 'stale async replay overwrote newest target'
      # A new stroke on an undone branch discards all invalid forward checkpoints.
      ev('__historyQA.stroke(77)')
      assert ev('__historyQA.stats()')['actions']==32
      assert ev('__historyQA.verify()')['equal'], 'branch replay diverged'
      ev('__historyQA.undo()')
      page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      ev('__historyQA.redo()')
      page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      assert ev('__historyQA.verify()')['equal'], 'branch undo redo diverged'
      # Shape edits change previously drawn shapes, so a prior checkpoint must
      # never be reused after an edit without reconstructing those shapes.
      ev('__historyQA.editShape()');ev('__historyQA.snapshot()')
      ev('__historyQA.mutateShape()');ev('__historyQA.snapshot()')
      assert ev('__historyQA.verify()')['equal'], 'vector edit differs after replay'
      ev('__historyQA.undo()');page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      assert ev('__historyQA.verify()')['equal'], 'undo vector edit differs after replay'
      ev('__historyQA.redo()');page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      assert ev('__historyQA.verify()')['equal'], 'redo vector edit differs after replay'
      ev('__historyQA.newLayer()');ev('__historyQA.stroke(99)');ev('__historyQA.snapshot()')
      ev('__historyQA.undo()');page.wait_for_function('!window.__historyQA.stats().rendering',timeout=60000)
      assert ev('__historyQA.verify()')['equal'], 'multi-layer undo mismatch'
      assert not errors,errors
      print('PASS Chromium v0.1.46 history: recent checkpoint fast-undo',fast,'ms; async old-history replay; burst navigation cancel; branch safety; vector edits; layers; deterministic pixels; no JS errors')
      browser.close()

if __name__=='__main__': main()
