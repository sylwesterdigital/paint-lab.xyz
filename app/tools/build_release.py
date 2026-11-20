#!/usr/bin/env python3
"""Build deterministic, checksum-verified Paint Lab release ZIP from Git repository root."""
from __future__ import annotations
import hashlib,json,re,zipfile,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'app'
VERSION=json.loads((APP/'version.json').read_text())['version']
WATCHER=ROOT/'watch-paint-lab.sh'

def build():
    if not re.fullmatch(r'\d+\.\d+\.\d+',VERSION):raise SystemExit('Invalid version')
    for file in (APP/'frontend/version.json',APP/'changelog.json'):
        if json.loads(file.read_text()).get('version')!=VERSION:raise SystemExit('Version mismatch: '+str(file))
    if f'<meta name="paint-lab-version" content="{VERSION}">' not in (APP/'frontend/index.html').read_text():
        raise SystemExit('Version mismatch: HTML')
    if not WATCHER.is_file():raise SystemExit('Missing watch-paint-lab.sh')
    paths=[]
    for path in APP.rglob('*'):
        if path.is_symlink():raise SystemExit('Symlink not allowed in release: '+str(path))
        if not path.is_file():continue
        rel=path.relative_to(ROOT).as_posix()
        if any(part in rel.split('/') for part in ('.venv','var','__pycache__','.git')) or rel.endswith(('.pyc','.pyo','.sqlite3','.sqlite3-shm','.sqlite3-wal')):continue
        if rel.endswith('.env') or '/.env' in rel:raise SystemExit('Secret-like env file found: '+rel)
        paths.append((rel,path))
    files={rel:hashlib.sha256(path.read_bytes()).hexdigest() for rel,path in sorted(paths)}
    manifest={'project':'paint-lab','version':VERSION,'format':1,'sha256':files,'watcher':{
        'path':'watch-paint-lab.sh','sha256':hashlib.sha256(WATCHER.read_bytes()).hexdigest()}}
    destination=ROOT/'updates';destination.mkdir(exist_ok=True)
    out=destination/f'PAINT_LAB_RELEASE_v{VERSION}.zip'
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as zipf:
        for name,path in sorted(paths):
            item=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=(0o100644<<16)
            zipf.writestr(item,path.read_bytes())
        item=zipfile.ZipInfo('watch-paint-lab.sh',date_time=(2026,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=(0o100755<<16)
        zipf.writestr(item,WATCHER.read_bytes())
        item=zipfile.ZipInfo('manifest.json',date_time=(2026,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=(0o100644<<16)
        zipf.writestr(item,(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode())
    print(out)
    return out

if __name__=='__main__':build()
