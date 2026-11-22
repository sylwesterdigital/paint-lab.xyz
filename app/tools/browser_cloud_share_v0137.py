#!/usr/bin/env python3
"""Chromium browser-side account/PNG API contract smoke; no production requests."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/'frontend/index.html').read_text()
HOOK=r'''
window.__cloudShareQA={
 reset:()=>{
  baseW=480;baseH=320;resize(false);actions=[];head=0;rebuild();
  artName='Cloud format 4';cloudUser={id:8,username:'browser_test',role:'user'};
  cloudProjectId=null;cloudCSRF='mock';cloudUI();
  const l=activeLayer();usePaintLayer(l);l.ctx.fillStyle='#287dc9';l.ctx.fillRect(25,35,150,80);markPaint();
  return {version:projectData().version,w:l.canvas.width,h:l.canvas.height};
 },
 save:async()=>{
  let record=null;
  const originalFetch=window.fetch;
  window.fetch=async(url,opts={})=>{
   const path=String(url);
   if(path==='/api/projects'&&opts.method==='POST'){
    record=JSON.parse(opts.body);
    return {ok:true,json:async()=>({ok:true,id:'22222222-2222-4222-8222-222222222222'})};
   }
   if(path==='/api/projects'&&(!opts.method||opts.method==='GET'))return {ok:true,json:async()=>({projects:[]})};
   return {ok:false,status:404,json:async()=>({error:'Unexpected mock endpoint '+path})};
  };
  try{await saveCloud(true);}finally{window.fetch=originalFetch;}
  return {format:record?.document?.format,version:record?.document?.version,
   thumb:record?.thumbnail?.startsWith('data:image/jpeg;base64,'),
   savedId:cloudProjectId,status:document.getElementById('cloudMessage').textContent};
 },
 share:async()=>{
  const blob=await sharePNGBlob(true);
  const signature=Array.from(new Uint8Array(await blob.slice(0,8).arrayBuffer()));
  let image=null;
  const originalFetch=window.fetch;
  window.fetch=async(url,opts={})=>{
   const path=String(url);
   if(path==='/api/publications'&&opts.method==='POST'){
    const payload=JSON.parse(opts.body);image=payload.image;
    return {ok:true,json:async()=>({ok:true,url:'https://paint-lab.xyz/p/test',token:'test',title:payload.title})};
   }
   if(path==='/api/publications'&&(!opts.method||opts.method==='GET'))return {ok:true,json:async()=>({publications:[]})};
   return {ok:false,status:404,json:async()=>({error:'Unexpected mock endpoint '+path})};
  };
  try{await publishArtwork();}finally{window.fetch=originalFetch;}
  return {mime:blob.type,size:blob.size,signature,started:image?.startsWith('data:image/png;base64,'),
   publicStatus:document.getElementById('shareMessage').textContent,
   url:document.getElementById('shareLink').value};
 }
};
'''
anchor="window.addEventListener('resize',()=>{resize();requestAnimationFrame(constrainAllPanels);});"
assert anchor in HTML
HTML=HTML.replace(anchor,HOOK+'\n'+anchor,1)

def main():
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  page=browser.new_page(viewport={'width':1000,'height':800},device_scale_factor=1)
  page.on('pageerror',lambda exc:errors.append(str(exc)))
  page.set_content(HTML,wait_until='domcontentloaded',timeout=35000)
  page.wait_for_timeout(250)
  ready=page.evaluate('__cloudShareQA.reset()')
  saved=page.evaluate('__cloudShareQA.save()')
  assert ready['version']==4,ready
  assert saved['format']=='paint-lab-webgl' and saved['version']==4 and saved['thumb'],saved
  assert saved['savedId']=='22222222-2222-4222-8222-222222222222',saved
  assert 'Saved to server' in saved['status'],saved
  shared=page.evaluate('__cloudShareQA.share()')
  assert shared['mime']=='image/png' and shared['signature']==[137,80,78,71,13,10,26,10],shared
  assert shared['started'] and shared['size']<=7*1024*1024,shared
  assert shared['url']=='https://paint-lab.xyz/p/test' and 'Published.' in shared['publicStatus'],shared
  assert not errors,errors
  browser.close()
  print('PASS Chromium v0.1.37: browser sends editable format v4 to private account, thumbnail JPEG, PNG-only publish wire payload and public link UI (mock server, no network)')

if __name__=='__main__':main()
