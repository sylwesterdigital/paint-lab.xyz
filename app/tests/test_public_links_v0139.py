"""v0.1.39: public artwork page/image and artist-gallery links must reach Flask.

These are deployment contracts, not requests to the live production domain. nginx
previously served index.html for /p/ and /u/ even though Flask had valid routes.
"""
import re
import unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]

class PublishedArtworkRoutingTests(unittest.TestCase):
    def test_public_paths_have_explicit_nginx_proxy_locations(self):
        from deploy import install
        conf=install.NGINX
        https=conf[conf.index('listen 443 ssl;'):]
        for prefix in ('/p/','/u/'):
            match=re.search(r'(?m)^\s*location \^~ '+re.escape(prefix)+r' \{(.*?)\n\s*\}', https, re.S)
            self.assertIsNotNone(match,f'Missing public Flask proxy location {prefix}')
            section=match.group(1)
            self.assertIn('proxy_pass http://127.0.0.1:18766;',section)
            self.assertNotIn('proxy_pass http://127.0.0.1:18766/;',section) # URI must be preserved.
            self.assertIn('proxy_set_header Host $host;',section)
            self.assertIn('proxy_set_header X-Forwarded-Proto $scheme;',section)
            self.assertNotIn('try_files',section)
        self.assertIn('location / { try_files $uri $uri/ /index.html; }',https)
        self.assertIn('location /api/ {',https)
        self.assertIn('location = /ws {',https)

    def test_backend_routes_match_proxy_and_publication_links(self):
        backend=(APP/'backend/app.py').read_text()
        for marker in ("@app.get('/p/<token>')", "@app.get('/p/<token>/image.png')", "@app.get('/u/<username>')"):
            self.assertIn(marker,backend)
        self.assertIn("url_for('view_publication',token=token)",backend)
        self.assertIn("url_for('publication_image',token=row['token'])",backend)
        self.assertIn("url_for('public_user_space',username=username)",backend)

    def test_production_requires_public_route_check_after_nginx_reload(self):
        source=(APP/'deploy/install.py').read_text()
        self.assertIn('def check_public_routes(',source)
        self.assertIn('ssl.create_default_context()',source)
        self.assertIn('server_hostname=DOMAIN',source)
        self.assertIn("'/p/paintlabunknownpublication9999/image.png'",source)
        self.assertIn("'/u/PaintLabUnknownPublicUser9999'",source)
        self.assertIn("        reload_nginx()\n        check_public_routes()\n        print('DEPLOYED v'+version)",source)
        self.assertIn("raise DeployError('Public share URL not routed to Flask after ",source)

if __name__=='__main__':
    unittest.main()
