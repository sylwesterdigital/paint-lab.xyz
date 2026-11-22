"""v0.1.40: distinguish Flask public routes from nginx's stale SPA fallback.

The Ubuntu installer verifies the upstream before inspecting HTTPS. Gracefully
reloading nginx is asynchronous, so a short run of 200s during worker rollover
must be retried. An indefinitely wrong route still fails and rolls back.
"""
import contextlib
import io
import unittest
from unittest.mock import patch

from deploy import install


class PublicRouteReloadTests(unittest.TestCase):
    def test_retries_editor_spa_until_all_routes_are_live(self):
        routes=install.PUBLIC_ROUTE_PROBES
        seen=[]
        counts={path:0 for path in routes}

        def direct(route):
            seen.append(route)
            return 404

        def edge(route):
            counts[route]+=1
            if counts[route]==1:
                return 200,'text/html'
            return 404,'text/html'

        output=io.StringIO()
        with patch.object(install,'probe_backend_public_route',side_effect=direct), \
             patch.object(install,'probe_https_public_route',side_effect=edge), \
             patch.object(install.time,'sleep') as sleep, \
             contextlib.redirect_stdout(output):
            install.check_public_routes(max_attempts=3,pause_seconds=.05)
        self.assertEqual(seen,list(routes))
        self.assertTrue(all(counts[path]==2 for path in routes))
        sleep.assert_called_once_with(.05)
        self.assertIn('after 2 nginx probe(s)',output.getvalue())

    def test_incorrect_nginx_route_still_fails_closed(self):
        with patch.object(install,'probe_backend_public_route',return_value=404), \
             patch.object(install,'probe_https_public_route',return_value=(200,'text/html')), \
             patch.object(install.time,'sleep') as sleep, \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(install.DeployError,'Public share URL not routed to Flask after 3 HTTPS checks') as error:
                install.check_public_routes(max_attempts=3,pause_seconds=.05)
        self.assertIn('HTTP 200 (text/html)',str(error.exception))
        self.assertIn('Verify the live 443 vhost',str(error.exception))
        self.assertEqual(sleep.call_count,2)

    def test_backend_mismatch_blocks_deploy_even_if_nginx_404s(self):
        with patch.object(install,'probe_backend_public_route',return_value=200), \
             patch.object(install,'probe_https_public_route') as edge:
            with self.assertRaisesRegex(install.DeployError,'Flask public-route contract failed'):
                install.check_public_routes(max_attempts=2,pause_seconds=0)
        edge.assert_not_called()

    def test_all_routes_must_reach_flask(self):
        def fake_edge(route):
            return (200,'text/html') if route==install.PUBLIC_ROUTE_PROBES[1] else (404,'text/html')
        with patch.object(install,'probe_backend_public_route',return_value=404), \
             patch.object(install,'probe_https_public_route',side_effect=fake_edge), \
             patch.object(install.time,'sleep'), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(install.DeployError,'image.png HTTP 200'):
                install.check_public_routes(max_attempts=2,pause_seconds=0)

    def test_tls_hostname_and_proxy_avoid_external_dns(self):
        source=__import__('pathlib').Path(install.__file__).read_text()
        self.assertIn("socket.create_connection(('127.0.0.1',443)",source)
        self.assertIn('ssl.create_default_context().wrap_socket(raw,server_hostname=DOMAIN)',source)
        self.assertIn("'Host':DOMAIN",source)
        self.assertIn('check_public_routes()\n        print(\'DEPLOYED v\'+version)',source)


if __name__=='__main__':unittest.main()
