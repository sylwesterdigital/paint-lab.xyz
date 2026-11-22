#!/usr/bin/env python3
"""Exercise production nginx public paths with a disposable local mock upstream.

No TLS, Internet, SSH, SQLite account, certificate or production host is touched.
The nginx location rules are extracted from the shipped HTTPS vhost and run on
an unprivileged local HTTP port to catch accidental SPA fallbacks.
"""
from __future__ import annotations
import http.server
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deploy.install import NGINX


def local_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


class Backend(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/p/'):
            typ='image/png' if self.path.endswith('/image.png') else 'text/html'
            body=b'PNG_FROM_FLASK' if typ=='image/png' else b'PUBLISHED_ART_FROM_FLASK'
        elif self.path.startswith('/u/'):
            typ='text/html';body=b'PUBLIC_GALLERY_FROM_FLASK'
        elif self.path == '/explore':
            typ='text/html';body=b'PAINT_LAB_DISCOVER_FROM_FLASK'
        elif self.path.startswith('/api/'):
            typ='application/json';body=b'{"ok":true}'
        else:
            self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',typ)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

    def log_message(self,*_):pass


def main():
    nginx=shutil.which('nginx')
    if not nginx:
        print('SKIP: nginx is not available')
        return
    upstream=http.server.ThreadingHTTPServer(('127.0.0.1',0),Backend)
    upstream_port=upstream.server_address[1]
    thread=threading.Thread(target=upstream.serve_forever,daemon=True);thread.start()
    nginx_process=None
    try:
        with tempfile.TemporaryDirectory(prefix='paint-lab-public-nginx-') as folder:
            root=Path(folder);root.chmod(0o755);web=root/'frontend';web.mkdir(mode=0o755)
            (web/'index.html').write_text('PAINT_LAB_EDITOR_SPA_FALLBACK')
            nginx_port=local_port()
            start=NGINX.index('server {',NGINX.index('server {')+1)
            site=NGINX[start:]
            site=site.replace('listen 443 ssl;',f'listen 127.0.0.1:{nginx_port};')
            site=site.replace('listen [::]:443 ssl;','')
            site='\n'.join(line for line in site.splitlines() if not line.strip().startswith((
                'ssl_certificate ','ssl_certificate_key ','ssl_protocols ','ssl_session_cache ')))
            site=site.replace('root /var/www/paint-lab.xyz/current/frontend;',f'root {web};')
            site=site.replace('access_log /var/log/nginx/paint-lab.xyz.access.log;',f'access_log {root}/access.log;')
            site=site.replace('error_log /var/log/nginx/paint-lab.xyz.error.log;',f'error_log {root}/error.log;')
            site=site.replace('http://127.0.0.1:18766',f'http://127.0.0.1:{upstream_port}')
            config=root/'nginx.conf'
            def write_config(content):
                config.write_text(f'pid {root}/nginx.pid;\nevents {{ worker_connections 64; }}\nhttp {{\n'+content+'\n}\n')
            # Reproduce v0.1.39's old worker configuration: public URLs
            # initially fall through to the editor SPA before nginx is reloaded.
            legacy=re.sub(r'(?m)^ location \^~ /(?:p|u)/ \{\n.*?^ \}\n','',site,flags=re.S)
            legacy=re.sub(r'(?m)^ location (?:= /explore|\^~ /explore/) \{\n.*?^ \}\n','',legacy,flags=re.S)
            assert legacy!=site and 'location ^~ /p/' not in legacy and 'location ^~ /u/' not in legacy
            write_config(legacy)
            test=subprocess.run([nginx,'-t','-p',str(root),'-c',str(config)],capture_output=True,text=True,timeout=15)
            if test.returncode:raise AssertionError('nginx -t failed: '+test.stderr)
            nginx_process=subprocess.Popen([nginx,'-p',str(root),'-c',str(config),'-g','daemon off;'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            base=f'http://127.0.0.1:{nginx_port}'
            for i in range(50):
                try:
                    with urllib.request.urlopen(base+'/',timeout=.3) as response:
                        assert response.read()==b'PAINT_LAB_EDITOR_SPA_FALLBACK'
                    break
                except (urllib.error.URLError,TimeoutError,ConnectionError):
                    time.sleep(.06)
            else:raise AssertionError('Disposable nginx did not start: '+((root/'error.log').read_text()[-700:] if (root/'error.log').exists() else 'status '+str(nginx_process.poll())))
            with urllib.request.urlopen(base+'/p/paintlabtestpublishedimage',timeout=2) as response:
                assert response.status==200 and response.read()==b'PAINT_LAB_EDITOR_SPA_FALLBACK'
            with urllib.request.urlopen(base+'/explore',timeout=2) as response:
                assert response.status==200 and response.read()==b'PAINT_LAB_EDITOR_SPA_FALLBACK'
            write_config(site)
            test=subprocess.run([nginx,'-t','-p',str(root),'-c',str(config)],capture_output=True,text=True,timeout=15)
            if test.returncode:raise AssertionError('updated nginx -t failed: '+test.stderr)
            reload=subprocess.run([nginx,'-s','reload','-p',str(root),'-c',str(config)],capture_output=True,text=True,timeout=10)
            if reload.returncode:raise AssertionError('nginx reload failed: '+reload.stderr)
            for i in range(50):
                with urllib.request.urlopen(base+'/p/paintlabtestpublishedimage',timeout=2) as response:
                    body=response.read()
                if body==b'PUBLISHED_ART_FROM_FLASK':break
                time.sleep(.06)
            else:raise AssertionError('New public routes did not activate after nginx reload')
            for route,content in [('/p/paintlabtestpublishedimage',b'PUBLISHED_ART_FROM_FLASK'),
                                  ('/p/paintlabtestpublishedimage/image.png',b'PNG_FROM_FLASK'),
                                  ('/u/paintlabtestartist',b'PUBLIC_GALLERY_FROM_FLASK'),
                                  ('/explore',b'PAINT_LAB_DISCOVER_FROM_FLASK'),
                                  ('/api/health',b'{"ok":true}')]:
                with urllib.request.urlopen(base+route,timeout=3) as response:
                    data=response.read();status=response.status
                assert status==200 and data==content,(route,status,data)
            print('PASS: real nginx SPA fallback -> graceful reload -> Flask public page/PNG/gallery/discover/API')
    finally:
        upstream.shutdown();upstream.server_close()
        if nginx_process:
            nginx_process.terminate()
            try:nginx_process.communicate(timeout=5)
            except subprocess.TimeoutExpired:nginx_process.kill();nginx_process.communicate()

if __name__=='__main__':
    main()
