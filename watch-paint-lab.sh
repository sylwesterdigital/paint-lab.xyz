#!/usr/bin/env bash
# Paint Lab watcher for macOS -> GitHub main -> Ubuntu, based on FREE-LAB release pipeline.
# Usage: ./watch-paint-lab.sh [--dry-run|--once|--status|--tail|--diagnose|--rollback] [--interval N]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$ROOT" "$@" <<'PAINT_LAB_WATCH_PY'
from __future__ import annotations
import argparse,datetime as dt,fcntl,hashlib,json,os,re,secrets,shlex,shutil,stat,subprocess,sys,tempfile,time,urllib.request,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(sys.argv[1]).resolve();sys.argv=[sys.argv[0]]+sys.argv[2:]
UPDATES=ROOT/'updates';UPLOADS=ROOT/'uploads';STATE=ROOT/'.paint-lab'
VERSION='0.1.2'
ZIP_RE=re.compile(r'^PAINT_LAB_RELEASE_v(\d+\.\d+\.\d+)\.zip$')
REPO='git@github.com:sylwesterdigital/paint-lab.xyz.git'
HOST=os.getenv('PAINT_LAB_SSH_HOST','root@46.62.232.64')
PORT=os.getenv('PAINT_LAB_SSH_PORT','333')
URL=os.getenv('PAINT_LAB_PUBLIC_URL','https://paint-lab.xyz/').rstrip('/')+'/'
LOG=None
class Failure(Exception):pass
class BadArchive(Failure):pass

ANSI={'STEP':'\033[1;36m','PASS':'\033[1;32m','FAIL':'\033[1;37;41m',
      'WARN':'\033[1;33m','INFO':'\033[1;37m'}
RESET='\033[0m';DIM='\033[2m';BOLD='\033[1m'

def colour_on():
    if 'NO_COLOR' in os.environ and os.getenv('NO_COLOR')!='0':return False
    if os.getenv('FORCE_COLOR')=='1' or os.getenv('CLICOLOR_FORCE')=='1':return True
    return sys.stdout.isatty() and os.getenv('TERM','')!='dumb'

def say(message,level='INFO'):
    timestamp=dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    line=f'{timestamp} [{level:5}] {message}'
    if colour_on():
        accent=ANSI.get(level,ANSI['INFO'])
        print(f'{DIM}{timestamp}{RESET} {accent}[{level:5}]{RESET} {message}',flush=True)
    else:print(line,flush=True)
    if LOG:
        with LOG.open('a',encoding='utf-8') as out:out.write(line+'\n')

def banner(message,detail='',level='STEP'):
    """High-visibility, full-width release lifecycle banners (log remains plain text)."""
    width=max(52,min(92,shutil.get_terminal_size((80,20)).columns-2))
    border='━'*width
    icon={'STEP':'▶','PASS':'✔','FAIL':'✖','WARN':'!','INFO':'●'}.get(level,'●')
    heading=f' {icon}  {message.upper()} '
    if colour_on():
        accent=ANSI.get(level,ANSI['INFO'])
        print(f'\n{accent}{border}\n{heading}\n{border}{RESET}',flush=True)
        if detail:print(f'{DIM}{detail}{RESET}',flush=True)
    else:
        print(f'\n{border}\n{heading}\n{border}',flush=True)
        if detail:print(detail,flush=True)
    if LOG:
        with LOG.open('a',encoding='utf-8') as out:
            out.write('\n'+border+'\n'+heading+'\n'+border+'\n')
            if detail:out.write(detail+'\n')

def command(args,*,cwd=None,timeout=100,stdin=None,check=True):
    try:p=subprocess.run([str(x) for x in args],cwd=cwd,text=True,input=stdin,capture_output=True,
                          env={**os.environ,'GIT_TERMINAL_PROMPT':'0'},timeout=timeout)
    except subprocess.TimeoutExpired:raise Failure(str(args[0])+' timed out')
    if check and p.returncode:raise Failure(str(args[0])+' failed: '+(p.stderr or p.stdout)[-1300:])
    return p

def ssh(script,timeout=100):
    return command(['ssh','-p',PORT,'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
                    '-o','ConnectTimeout=10',HOST,'bash','-se'],stdin='set -euo pipefail\n'+script+'\n',timeout=timeout).stdout.strip()

def sha(payload):return hashlib.sha256(payload).hexdigest()
def vt(version):return tuple(int(x) for x in version.split('.'))
def deployed():
    try:return json.loads((STATE/'deployed.json').read_text())['version']
    except (OSError,ValueError,KeyError):return '0.0.0'

def verify_watcher(source):
    text=source.decode('utf-8');found=re.search(r"^VERSION='(\d+\.\d+\.\d+)'",text,re.M)
    if not found or vt(found.group(1))<vt(VERSION):raise BadArchive('Watcher is older than installed watcher')
    current=ROOT/'watch-paint-lab.sh'
    if current.exists() and found.group(1)==VERSION and current.read_bytes()!=source:
        raise BadArchive('Watcher changes require a watcher VERSION bump')
    with tempfile.TemporaryDirectory() as t:
        file=Path(t)/'watch.sh';file.write_bytes(source)
        command(['bash','-n',file],timeout=15)
        program=re.search(r"<<'PAINT_LAB_WATCH_PY'\n(.*?)\nPAINT_LAB_WATCH_PY\s*$",text,re.S)
        if not program:raise BadArchive('Missing embedded Python watcher')
        py=Path(t)/'watch.py';py.write_text(program.group(1))
        command([sys.executable,'-m','py_compile',py],timeout=15)

def validate(archive,stage):
    if archive.stat().st_size>32*1024*1024:raise BadArchive('ZIP exceeds 32 MB')
    try:z=zipfile.ZipFile(archive)
    except (zipfile.BadZipFile,OSError) as e:raise BadArchive('Invalid release ZIP: '+str(e))
    with z:
        entries=z.infolist();names=[f.filename for f in entries if not f.is_dir()]
        if len(entries)>256 or sum(f.file_size for f in entries)>90*1024*1024:
            raise BadArchive('Too many files or excessive uncompressed archive size')
        if len(names)!=len(set(names)):raise BadArchive('Duplicate archive file')
        for entry in entries:
            path=PurePosixPath(entry.filename)
            mode=entry.external_attr>>16
            if (entry.filename.startswith('/') or '\\' in entry.filename or '..' in path.parts or
                stat.S_IFMT(mode)==stat.S_IFLNK or entry.flag_bits & 1 or
                entry.compress_type not in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED) or
                entry.file_size>25*1024*1024 or (entry.file_size>1024*1024 and entry.file_size/max(entry.compress_size,1)>200)):
                raise BadArchive('Unsafe ZIP member '+entry.filename)
        if 'manifest.json' not in names:raise BadArchive('Release manifest missing')
        info=json.loads(z.read('manifest.json'));m=ZIP_RE.fullmatch(archive.name)
        version=info.get('version','')
        if not m or version!=m.group(1) or info.get('project')!='paint-lab':raise BadArchive('Release name/version/project mismatch')
        if vt(version)<=vt(deployed()):raise BadArchive('Release is not newer than already verified v'+deployed())
        files=info.get('sha256')
        required={'app/frontend/index.html','app/frontend/version.json','app/version.json','app/requirements.txt',
                  'app/backend/app.py','app/backend/db.py','app/backend/keyvault.py','app/deploy/install.py',
                  'app/tests/test_core.py','app/tests/test_deploy.py','app/README.md'}
        if not isinstance(files,dict) or not required.issubset(files):raise BadArchive('Required files absent')
        if set(names)!=set(files)|{'manifest.json','watch-paint-lab.sh'}:
            raise BadArchive('Release file set differs from checksum manifest')
        watcher=z.read('watch-paint-lab.sh')
        if info.get('watcher',{}).get('sha256')!=sha(watcher):raise BadArchive('Watcher checksum mismatch')
        verify_watcher(watcher)
        for name,digest in files.items():
            if (not name.startswith('app/') or not re.fullmatch(r'[A-Za-z0-9_.\-/]+',name) or
                '..' in PurePosixPath(name).parts or '__pycache__' in PurePosixPath(name).parts or
                not re.fullmatch(r'[a-f0-9]{64}',str(digest))):raise BadArchive('Unsafe tracked path '+name)
            content=z.read(name)
            if sha(content)!=digest:raise BadArchive('SHA256 mismatch: '+name)
            path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        (stage/'manifest.json').write_bytes(z.read('manifest.json'))
        (stage/'watch-paint-lab.sh').write_bytes(watcher)
        for file in ('app/version.json','app/frontend/version.json','app/changelog.json'):
            if json.loads((stage/file).read_text()).get('version')!=version:raise BadArchive('Version marker mismatch: '+file)
        if vt(version)>=(0,1,4):
            documents=('app/ABOUT.md','app/CHANGELOG.md','app/docs/GITHUB_README.md','app/frontend/changelog.json')
            if not all((stage/file).is_file() and file in files for file in documents):
                raise BadArchive('Missing v0.1.4+ public changelog or GitHub documentation')
            main_log=json.loads((stage/'app/changelog.json').read_text())
            public_log=json.loads((stage/'app/frontend/changelog.json').read_text())
            if main_log!=public_log or main_log.get('version')!=version or not isinstance(main_log.get('history'),list):
                raise BadArchive('Public and canonical release histories must match')
            if (not main_log.get('changes') or not isinstance(main_log['changes'],list) or
                not all(isinstance(x,str) and x.strip() for x in main_log['changes'])):
                raise BadArchive('Current release requires development log entries')
            for old in main_log['history']:
                if not re.fullmatch(r'\d+\.\d+\.\d+',str(old.get('version',''))) or vt(old['version'])>=vt(version):
                    raise BadArchive('Invalid historical development log version')
            for file in ('app/ABOUT.md','app/CHANGELOG.md','app/docs/GITHUB_README.md'):
                content=(stage/file).read_text()
                if not content.startswith('# ') or 'https://paint-lab.xyz/' not in content:
                    raise BadArchive('Incomplete public project documentation '+file)
        html=(stage/'app/frontend/index.html').read_text()
        if f'<meta name="paint-lab-version" content="{version}">' not in html:
            raise BadArchive('HTML version marker missing')
        if 'id="toolRail"' not in html or 'id="layersPanel"' not in html or 'id="materialQuick"' not in html:
            raise BadArchive('Required Paint Lab editor controls missing')
        for path in (stage/'app').rglob('*.py'):
            command([sys.executable,'-m','py_compile',path],timeout=15)
        if shutil.which('node'):
            script=re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',html)
            if not script:raise BadArchive('Inline painting app script missing')
            js=stage/'paint-lab-inline-check.js';js.write_text('\n'.join(script))
            command(['node','--check',js],timeout=20);js.unlink()
            for path in (stage/'app/frontend/assets').glob('*.js'):
                command(['node','--check',path],timeout=15)
        else:say('Node not found locally, JavaScript syntax will need browser/server checks','WARN')
        tests=command([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=stage/'app',timeout=90)
        if 'FAILED' in tests.stdout+tests.stderr:raise BadArchive('Tests failed')
        if 'skipped=' in tests.stderr:say('Missing local Flask dependencies: API tests skipped locally; server tests mandatory','WARN')
        for d in (stage/'app').rglob('__pycache__'):shutil.rmtree(d,ignore_errors=True)
        say('ZIP hashes, Python, UI markers, JavaScript syntax (when installed), tests OK','PASS')
        return version,info

def preflight(stage):
    if not (ROOT/'.git').is_dir():raise Failure('Watcher must be at Git repository root')
    if command(['git','branch','--show-current'],cwd=ROOT).stdout.strip()!='main':raise Failure('Only main can deploy')
    origin=command(['git','remote','get-url','origin'],cwd=ROOT).stdout.strip()
    if origin not in (REPO,'ssh://git@github.com/sylwesterdigital/paint-lab.xyz.git'):
        raise Failure('Unexpected Git origin: '+origin)
    changes=[line for line in command(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT).stdout.split('\0') if line]
    for line in changes:
        path=line[3:]
        if line.startswith('?? ') and (path.startswith(('uploads/','updates/','.paint-lab/')) or path=='.DS_Store'):continue
        # Safe in-place watcher upgrades are permitted only if the file matches
        # the validated, checksum-verified watcher bundled in this release.
        if path=='watch-paint-lab.sh' and (ROOT/path).is_file() and (ROOT/path).read_bytes()==(stage/'watch-paint-lab.sh').read_bytes():continue
        raise Failure('Uncommitted worktree changes: '+line)
    remote=command(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,timeout=60).stdout.strip()
    if remote:
        command(['git','fetch','--no-tags','origin','main'],cwd=ROOT,timeout=65)
        check=command(['git','merge-base','--is-ancestor','FETCH_HEAD','HEAD'],cwd=ROOT,check=False)
        if check.returncode:raise Failure('GitHub main ahead/diverged; reconcile before deployment')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+',HOST) or not PORT.isdigit() or not 1<=int(PORT)<=65535:
        raise Failure('Invalid SSH host/port')
    result=ssh('test "$(id -u)" -eq 0; command -v python3 >/dev/null; command -v systemctl >/dev/null; echo SSH_READY',timeout=35)
    if 'SSH_READY' not in result:raise Failure('SSH preflight failed')
    say(f'Git main, GitHub, SSH {HOST}:{PORT} ready','PASS')

def install_remote(stage,version):
    remote='/var/www/.paint-lab-stage-'+version+'-'+secrets.token_hex(5)
    quoted=shlex.quote(remote)
    ssh('mkdir -m 700 -- '+quoted)
    try:
        command(['scp','-r','-P',PORT,'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
                 str(stage/'app'),str(stage/'manifest.json'),HOST+':'+remote+'/'],timeout=210)
        remote_verify=ssh('''python3 - <<'VERIFY'
import hashlib,json,pathlib
p=pathlib.Path('''+repr(remote)+''')
m=json.loads((p/'manifest.json').read_text())
for name,digest in m['sha256'].items():
 f=p/name
 if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise SystemExit('Remote hash failed '+name)
print('REMOTE_HASH_OK')
VERIFY''',timeout=55)
        if 'REMOTE_HASH_OK' not in remote_verify:raise Failure('Remote checksum verification failed')
        say('Remote staged SHA256 verified','PASS')
        deployment=''
        for variable in ('PAINT_LAB_CERTBOT_EMAIL','PAINT_LAB_CERTBOT_ACCOUNT','PAINT_LAB_EXPECTED_IP','PAINT_LAB_INSTALL_PACKAGES'):
            value=os.environ.get(variable)
            if value:
                if not re.fullmatch(r'[A-Za-z0-9@._+\-]+',value):raise Failure('Invalid '+variable)
                deployment+='export '+variable+'='+shlex.quote(value)+'\n'
        deployment+='python3 '+quoted+'/app/deploy/install.py --stage '+quoted+' --version '+shlex.quote(version)
        output=ssh(deployment,timeout=620)
        for line in output.splitlines():
            if line.startswith(('DEPLOYED','SERVER UNIT','PUBLIC URL','DNS_OK','CERTBOT')):say(line,'PASS')
    finally:
        try:ssh('rm -rf -- '+quoted,timeout=35)
        except Exception as e:say('Remote stage cleanup issue: '+str(e),'WARN')

def get_public(path):
    request=urllib.request.Request(URL+path+'?release_check='+str(int(time.time())),
                    headers={'Cache-Control':'no-cache','User-Agent':'PaintLabWatcher/0.1'})
    with urllib.request.urlopen(request,timeout=22) as response:
        if response.status!=200:raise Failure('Public HTTP status '+str(response.status)+' for '+path)
        return response.read(750000)

def verify_public(version):
    health=json.loads(get_public('api/health'))
    marker=json.loads(get_public('version.json'))
    home=get_public('').decode('utf-8','replace')
    if not (health.get('ok') and health.get('storage')=='sqlite' and health.get('websocket') and
            health.get('version')==version and marker.get('version')==version and
            f'<meta name="paint-lab-version" content="{version}">' in home):
        raise Failure('Public HTTPS, Flask, SQLite or frontend version mismatch')
    say('Public HTTPS + Flask + SQLite + version verified: '+URL,'PASS')

def git_publish(stage,version,manifest):
    files=sorted(manifest['sha256'])+['watch-paint-lab.sh']
    for name in files:
        target=ROOT/name;source=stage/name
        if target.is_symlink():raise Failure('Unsafe local source target: '+name)
        if target.exists() and command(['git','ls-files','--error-unmatch','--',name],cwd=ROOT,check=False).returncode:
            if name!='watch-paint-lab.sh' or target.read_bytes()!=source.read_bytes():
                raise Failure('Untracked target collision: '+name)
    for name in files:
        target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stage/name,target)
    (ROOT/'watch-paint-lab.sh').chmod(0o755)
    command(['git','add','--',*files],cwd=ROOT)
    staged=command(['git','diff','--cached','--quiet'],cwd=ROOT,check=False)
    if staged.returncode==1:command(['git','commit','-m','Release Paint Lab v'+version],cwd=ROOT)
    elif staged.returncode:raise Failure('Git staging check failed')
    head=command(['git','rev-parse','HEAD'],cwd=ROOT).stdout.strip()
    pushed=command(['git','push','-u','origin','main'],cwd=ROOT,timeout=160,check=False)
    remote=command(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,timeout=65).stdout
    if not remote.startswith(head+'\t'):
        raise Failure('Server is live but GitHub push verification failed: '+pushed.stderr[-600:])
    say('GitHub origin/main verified at '+head[:12],'PASS')

def publish_repo_docs():
    """Copy verified, versioned docs into GitHub root after a successful release.

    Works after an older watcher has installed its upgraded successor. Does not
    contact the Ubuntu server; only changes README/ABOUT/CHANGELOG in local Git.
    """
    if vt(deployed())<(0,1,4):
        say('Public GitHub documentation begins with verified release v0.1.4','WARN')
        return False
    if not (ROOT/'.git').is_dir():raise Failure('Git root missing; cannot publish documentation')
    if command(['git','branch','--show-current'],cwd=ROOT).stdout.strip()!='main':
        raise Failure('Only Git main may publish repository docs')
    origin=command(['git','remote','get-url','origin'],cwd=ROOT).stdout.strip()
    if origin not in (REPO,'ssh://git@github.com/sylwesterdigital/paint-lab.xyz.git'):
        raise Failure('Unexpected Git origin; refusing docs sync')
    version=json.loads((ROOT/'app/version.json').read_text())['version']
    if version!=deployed():raise Failure('Local sources do not match last verified deployment')
    docs=[('app/docs/GITHUB_README.md','README.md'),
          ('app/ABOUT.md','ABOUT.md'),('app/CHANGELOG.md','CHANGELOG.md')]
    changes=[]
    for source,target in docs:
        src=ROOT/source;dest=ROOT/target
        if not src.is_file() or src.is_symlink() or dest.is_symlink():
            raise Failure('Unsafe or missing public doc: '+source)
        contents=src.read_bytes()
        if not contents.startswith(b'# ') or len(contents)>100000 or b'https://paint-lab.xyz/' not in contents:
            raise Failure('Malformed public doc: '+source)
        if dest.exists() and command(['git','ls-files','--error-unmatch','--',target],cwd=ROOT,check=False).returncode:
            raise Failure('Refusing untracked public document collision: '+target)
        if command(['git','status','--porcelain','--',target],cwd=ROOT).stdout.strip():
            raise Failure('Refusing to overwrite local edits to '+target)
        if not dest.is_file() or dest.read_bytes()!=contents:
            changes.append((dest,contents))
    if not changes:
        say('GitHub README, ABOUT and CHANGELOG already in sync','PASS')
        return False
    # Do not inadvertently commit unreviewed changes anywhere else.
    changes_all=[line for line in command(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT).stdout.split('\0') if line]
    for line in changes_all:
        name=line[3:]
        if line.startswith('?? ') and (name.startswith(('uploads/','updates/','.paint-lab/')) or name=='.DS_Store'):
            continue
        raise Failure('Unrelated local changes prevent docs publication: '+line)
    remote=command(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,timeout=60).stdout
    head=command(['git','rev-parse','HEAD'],cwd=ROOT).stdout.strip()
    if remote and not remote.startswith(head+'\t'):
        raise Failure('GitHub main differs from local HEAD; reconcile before docs publication')
    backups=[(dest,dest.read_bytes() if dest.is_file() else None) for dest,_ in changes]
    names=[dest.relative_to(ROOT).as_posix() for dest,_ in changes]
    committed=False
    try:
        for dest,contents in changes:
            temp=dest.with_name(dest.name+'.paint-lab-new')
            temp.write_bytes(contents);os.replace(temp,dest)
        command(['git','add','--',*names],cwd=ROOT)
        diff=command(['git','diff','--cached','--quiet'],cwd=ROOT,check=False)
        if diff.returncode==1:command(['git','commit','-m','Publish Paint Lab project docs v'+version],cwd=ROOT)
        elif diff.returncode:raise Failure('Could not verify staged documents')
        committed=True
    except Exception:
        if not committed:
            for dest,old in backups:
                if old is None:dest.unlink(missing_ok=True)
                else:dest.write_bytes(old)
            command(['git','reset','--quiet','--',*names],cwd=ROOT,check=False)
        raise
    expected=command(['git','rev-parse','HEAD'],cwd=ROOT).stdout.strip()
    pushed=command(['git','push','-u','origin','main'],cwd=ROOT,timeout=160,check=False)
    confirmed=command(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,timeout=60).stdout
    if not confirmed.startswith(expected+'\t'):
        raise Failure('Docs committed locally but GitHub push unverified: '+pushed.stderr[-400:])
    say('Published README.md, ABOUT.md, CHANGELOG.md to GitHub main at '+expected[:12],'PASS')
    return True

def release(archive,dry_run):
    with tempfile.TemporaryDirectory(prefix='paint-lab-archive-',dir=STATE) as folder:
        stage=Path(folder)
        say('Validating ZIP, SHA256, scripts and tests','STEP')
        version,manifest=validate(archive,stage)
        if dry_run:
            say(f'DRY RUN PASSED v{version} (no SSH, Git, DNS or deployment changes)','PASS');return
        say('Checking GitHub main and SSH server','STEP');preflight(stage)
        say('Deploying Ubuntu service with checks and rollback','STEP');install_remote(stage,version)
        say('Verifying public HTTPS version and API','STEP');verify_public(version)
        say('Publishing release source to GitHub','STEP');git_publish(stage,version,manifest)
        tmp=STATE/'deployed.json.new';tmp.write_text(json.dumps({'version':version,'url':URL,'utc':dt.datetime.now(dt.timezone.utc).isoformat()},indent=2)+'\n');os.replace(tmp,STATE/'deployed.json')
        say('RELEASE COMPLETE v'+version,'PASS')

def main():
    global LOG
    ap=argparse.ArgumentParser(description='Versioned Paint Lab watcher for Git main and Ubuntu')
    options=ap.add_mutually_exclusive_group()
    for arg in ('dry-run','once','status','tail','diagnose','rollback','publish-docs'):options.add_argument('--'+arg,action='store_true')
    ap.add_argument('--interval',type=int,default=3);args=ap.parse_args()
    if args.interval<1:ap.error('--interval must be positive')
    for path in (UPDATES,UPLOADS,STATE,STATE/'logs',UPDATES/'processed',UPDATES/'rejected',UPDATES/'superseded'):path.mkdir(parents=True,exist_ok=True)
    STATE.chmod(0o700)
    if args.publish_docs:
        publish_repo_docs();return 0
    if args.status:
        say('Watcher v'+VERSION+' · last verified release '+deployed())
        try:say('Public health '+str(json.loads(get_public('api/health'))),'PASS')
        except Exception as e:say(str(e),'WARN')
        return 0
    if args.tail:
        logs=sorted((STATE/'logs').glob('*.log'),reverse=True)
        if logs:print('\n'.join(logs[0].read_text().splitlines()[-100:]))
        return 0
    if args.diagnose:
        script="""echo === Paint Lab ===; systemctl status paint-lab --no-pager --lines=16 || true; echo === nginx ===; nginx -t || true; echo === local health ===; curl --max-time 3 -sS http://127.0.0.1:18766/api/health || true; echo; echo === journal ===; journalctl -u paint-lab -n 15 --no-pager || true"""
        print(ssh(script,timeout=45));return 0
    if args.rollback:
        say(ssh('python3 /var/www/paint-lab.xyz/current/deploy/install.py --rollback',timeout=160),'WARN')
        say('Server release rolled back; SQLite data and Git history were not rolled back','WARN');return 0
    lock=(STATE/'watch.lock').open('w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise Failure('Another watcher already running')
    banner('Paint Lab watcher started',f'v{VERSION}  •  updates/ + uploads/  •  {URL}','INFO')
    say('Ready to process newer, versioned Paint Lab releases','PASS')
    # The previous watcher completes the release, then reloads this version.
    # Publish canonical GitHub-root docs on startup; skip during --dry-run/--once.
    if not (args.once or args.dry_run) and vt(deployed())>=(0,1,4):
        try:publish_repo_docs()
        except Exception as e:say('Repository documentation sync deferred: '+str(e),'WARN')

    retry={}
    while True:
        candidates=[]
        for file in [*UPDATES.glob('*.zip'),*UPLOADS.glob('*.zip')]:
            m=ZIP_RE.fullmatch(file.name)
            if not m:continue
            version=vt(m.group(1))
            if version<=vt(deployed()):
                if not args.dry_run and not args.once:
                    target=UPDATES/'superseded'/file.name
                    if target.exists():target=target.with_name(str(int(time.time()))+'-'+file.name)
                    file.rename(target)
                continue
            candidates.append((version,file))
        highest=max((item[0] for item in candidates),default=None)
        newest=[file for version,file in candidates if version==highest] if highest else []
        if not newest and (args.once or args.dry_run):say('No release ZIP in updates/ or uploads/','WARN');return 1
        failed=False
        for file in newest:
            if not args.once and not args.dry_run and (time.time()-file.stat().st_mtime<5 or retry.get(str(file),0)>time.time()):continue
            LOG=STATE/'logs'/(dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+file.stem+'.log')
            try:
                banner('Deployment started',file.name,'STEP')
                say('BEGIN '+file.name,'STEP')
                release(file,args.dry_run)
                banner('Validation passed' if args.dry_run else 'Deployment succeeded',file.name,'PASS')
                if not args.dry_run:
                    dest=UPDATES/'processed'/file.name
                    if dest.exists():dest=dest.with_name(str(int(time.time()))+'-'+file.name)
                    file.rename(dest)
            except BadArchive as e:
                failed=True;banner('Release rejected',file.name,'FAIL');say('ZIP REJECTED: '+str(e),'FAIL')
                if not args.dry_run:file.rename(UPDATES/'rejected'/file.name)
            except Exception as e:
                failed=True;banner('Deployment failed',file.name,'FAIL');say('DEPLOY FAILED: '+str(e),'FAIL')
                if not args.dry_run:
                    retry[str(file)]=time.time()+90
                    say('ZIP retained. Confirm server and Git state before retrying.','WARN')
            finally:
                say(('FAILED ' if failed else 'FINISHED ') +file.name,'FAIL' if failed else 'PASS')
                banner('Release ended with errors' if failed else 'Release finished',file.name,'FAIL' if failed else 'PASS')
                LOG=None
            if not failed and not args.once and not args.dry_run:
                latest=ROOT/'watch-paint-lab.sh'
                marker=re.search(r"^VERSION='(\d+\.\d+\.\d+)'",latest.read_text(),re.M)
                if marker and vt(marker.group(1))>vt(VERSION):
                    os.execv(str(latest),[str(latest),'--interval',str(args.interval)])
        if args.once or args.dry_run:return 1 if failed else 0
        time.sleep(args.interval)

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:print('\nWatcher stopped');sys.exit(0)
    except Exception as e:say(str(e),'FAIL');sys.exit(1)
PAINT_LAB_WATCH_PY
