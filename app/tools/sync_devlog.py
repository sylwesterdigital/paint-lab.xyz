#!/usr/bin/env python3
"""Deterministic development-log embedding from the canonical release JSON.

Use --write when release notes change. Both build_release.py and the production
watcher fail closed if the HTML-embedded copy becomes stale.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
FALLBACK_RE=re.compile(r'(?m)^const DEVLOG_FALLBACK=(\{[^\n]+\});$')


def canonical():
    data=json.loads((APP/'changelog.json').read_text(encoding='utf-8'))
    public=json.loads((APP/'frontend/changelog.json').read_text(encoding='utf-8'))
    version=json.loads((APP/'version.json').read_text(encoding='utf-8'))['version']
    frontend_version=json.loads((APP/'frontend/version.json').read_text(encoding='utf-8'))['version']
    if data!=public or version!=frontend_version or data.get('version')!=version:
        raise ValueError('Canonical, public and version-marker data disagree')
    if data.get('project')!='paint-lab' or not data.get('changes') or not isinstance(data.get('history'),list):
        raise ValueError('Incomplete development history')
    if not isinstance(data.get('title'),str) or version not in data['title']:
        raise ValueError('Development-log title does not contain release version')
    return data


def validate_or_sync(*,write=False):
    data=canonical()
    page=APP/'frontend/index.html'
    html=page.read_text(encoding='utf-8')
    version=data['version']
    if f'<meta name="paint-lab-version" content="{version}">' not in html or f'<title>Paint Lab v{version}</title>' not in html:
        raise ValueError('HTML version marker/title disagree with release')
    matches=list(FALLBACK_RE.finditer(html))
    if len(matches)!=1:
        raise ValueError('Expected exactly one embedded development-log JSON object')
    expected=json.dumps(data,ensure_ascii=True,separators=(',',':'))
    if write:
        page.write_text(html[:matches[0].start(1)]+expected+html[matches[0].end(1):],encoding='utf-8')
    elif matches[0].group(1)!=expected:
        raise ValueError('Stale embedded development log. Run python3 app/tools/sync_devlog.py --write')
    return data


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true',help='Synchronise HTML fallback from canonical JSON')
    args=ap.parse_args()
    try:
        result=validate_or_sync(write=args.write)
    except ValueError as exc:
        ap.exit(1,f'ERROR: {exc}\n')
    print(f'Embedded Paint Lab development history v{result["version"]} validated')
