#!/usr/bin/env python3
"""Mobile browser pixel QA: cheap strokes, bounded Undo and optional Umami."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in HTML
hook=r'''
window.__qa163={
 reset(){cancelHistoryReplay();clearHistoryPixelPatches();actions=[];head=0;baseW=390;baseH=600;resize(false);rebuild();return {head,width:layerPixelsW,height:layerPixelsH};},
 stroke(n){
  const cfg={...snapshot(),mode:0,material:'pencil',tip:'round',size:18,strength:1,flow:1,strokeEffect:null,styleEngine:'normal',color:n%2?'#fa3155':'#06a0ce'};
  const x=30+(n%11)*29,y=50+Math.floor(n/11)*68;
  const points=[{x,y,pressure:1,t:0},{x:x+16,y:y+7,pressure:1,t:20},{x:x+24,y:y+11,pressure:1,t:40}];
  const a={kind:'stroke',layerId:activeLayerId,cfg,points:[points[0]],start:points[0],seed:48911+n,time:Date.now(),touchRollback:{layerId:activeLayerId,tiles:new Map(),overflow:false}};
  usePaintLayer(activeLayer());captureTouchStrokeTiles(a,points[0],points[0]);drawStrokeStart(a);
  for(let i=1;i<points.length;i++){captureTouchStrokeTiles(a,points[i-1],points[i]);a.points.push(points[i]);drawStrokeStep(a,points[i]);}
  finishStrokeRender(a);delete a._run;delete a.loadedColor;
  rememberStrokePixelPatch(a);delete a.touchRollback;commit(a);
  return {head,floor:historyUndoFloor(),patches:historyPixelPatches.size,bytes:historyPixelPatchBytes};
 },
 hash(){if(compositeDirty)composeLayers();const data=layerCtx.getImageData(0,0,layerPixelsW,layerPixelsH).data;
  let hash=2166136261,occupied=0;
  for(let p=0;p<data.length;p+=16){hash=Math.imul(hash^data[p],16777619);hash=Math.imul(hash^data[p+1],16777619);hash=Math.imul(hash^data[p+2],16777619);hash=Math.imul(hash^data[p+3],16777619);occupied+=(data[p+3]>10?1:0);}return {hash:hash>>>0,occupied};},
 state(){return {head,actions:actions.length,floor:historyUndoFloor(),patches:historyPixelPatches.size,bytes:historyPixelPatchBytes,rendering,historyText:$('historyCount').textContent}},
 undo(){undo();return this.state()},redo(){redo();return this.state()},
 save(){return projectData().actions.length},
 fullRebuild(){rebuild();return this.hash()},
 reopenReplay(){clearHistoryCheckpoints();clearHistoryPixelPatches();rebuildHistoryWithoutBlocking({opening:true});return this.state()},
 testTrack(){window.__events=[];window.umami={track:(event,data)=>{window.__events.push({event,data});return Promise.resolve();}};
  paintLabTrack('artwork_saved',{destination:'local',kind:'new'});
  paintLabTrack('artwork_saved',{destination:'local',kind:'new'});
  paintLabTrack('artwork_published',{destination:'public'});
  paintLabTrack('private_password',{value:'secret'});
  return window.__events;}
};
'''
html=HTML.replace('initUI();initDevLog();','initUI();').replace(anchor,hook+anchor,1)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (320,390,430):
        context=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
        page=context.new_page(); errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('https://analytics.mielniczuk.com/**',lambda r:r.abort())
        page.set_content(html,wait_until='domcontentloaded')
        page.wait_for_function('!!window.__qa163')
        qa=lambda expr:page.evaluate('__qa163.'+expr)
        qa('reset()')
        states=[]
        for n in range(25):
            states.append(qa(f'stroke({n})'))
        assert states[-1]['patches']<=20,states[-1]
        assert states[-1]['floor']==5,states[-1]
        full=qa('hash()')
        assert full['occupied']>0,(width,full)
        # Time-cost is bounded by changed tiles, not the entire visible history.
        start=page.evaluate('performance.now()'); und=qa('undo()'); duration=page.evaluate('performance.now()')-start
        assert und['head']==24 and not und['rendering'] and duration<150,(width,und,duration)
        redo=qa('redo()')
        assert redo['head']==25 and qa('hash()')==full,(width,'redo canvas pixel mismatch')
        for _ in range(20): qa('undo()')
        below=qa('undo()')
        assert below['head']==5 and not below['rendering'],(width,below)
        # All earlier painting remains visible even though Undo cannot reach it.
        assert qa('hash()')['occupied']>0,(width,'base artwork vanished')
        for _ in range(20): qa('redo()')
        assert qa('hash()')==full,(width,'20-step redo diverged')
        assert qa('save()')==25,'Retained editable actions were silently lost'
        assert qa('fullRebuild()')==full,(width,'Raster patches disagree with editable replay')
        # Reopen a project with no in-memory patches: final twenty raster
        # states are re-captured as the editable history is reconstructed.
        replay=qa('reopenReplay()')
        assert replay['rendering']
        page.wait_for_function('!window.__qa163.state().rendering',timeout=60000)
        reopened=qa('state()')
        assert reopened['patches']>=18,(width,'Loaded painting lacks recent Undo acceleration',reopened)
        assert qa('hash()')==full,(width,'Reopened artwork pixel mismatch')
        first=qa('undo()')
        assert first['head']==24 and not first['rendering'],(width,'Loaded artwork Undo replayed all actions')
        assert qa('redo()')['head']==25 and qa('hash()')==full
        events=qa('testTrack()')
        assert len(events)==2 and {e['event'] for e in events}=={'artwork_saved','artwork_published'},events
        page.wait_for_timeout(2600)
        assert not errors,(width,errors)
        print('PASS',width,'pixel-perfect twenty-step Undo/Redo, bounded patch budget, preserved earlier painted history, fail-open analytics',round(duration,2),'ms',flush=True)
        context.close()
    browser.close()
