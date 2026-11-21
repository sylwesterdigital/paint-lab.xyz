"""Release integrity contracts for both macOS packaging and Ubuntu app-only installs.

Production install.py copies stage/app -> /var/www/paint-lab.xyz/releases/vX.Y.Z.
Neither the watcher nor the manifest is installed adjacent to the application.
"""
import json,re,unittest
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
HTML=(APP/'frontend/index.html').read_text(encoding='utf-8')
CHANGES=json.loads((APP/'changelog.json').read_text(encoding='utf-8'))

class ReleaseIntegrityV131(unittest.TestCase):
    def test_version_matches_entire_embedded_history(self):
        version=json.loads((APP/'version.json').read_text())['version']
        fallback=re.findall(r'^const DEVLOG_FALLBACK=(\{[^\n]+\});$',HTML,re.M)
        self.assertEqual(len(fallback),1)
        self.assertEqual(json.loads(fallback[0]),CHANGES)
        self.assertEqual(version,CHANGES['version'])
        self.assertEqual(CHANGES,json.loads((APP/'frontend/changelog.json').read_text()))
        self.assertIn(f'<meta name="paint-lab-version" content="{version}">',HTML)
        self.assertIn(f'<title>Paint Lab v{version}</title>',HTML)

    def test_full_history_includes_failed_release_and_is_ordered(self):
        history=[entry['version'] for entry in CHANGES['history']]
        self.assertIn('0.1.30',history)
        self.assertIn('0.1.29',history)
        self.assertIn('0.1.26',history)
        self.assertEqual(len(history),len(set(history)))
        self.assertEqual(history,sorted(history,key=lambda v:tuple(map(int,v.split('.'))),reverse=True))
        self.assertGreater(tuple(map(int,CHANGES['version'].split('.'))),tuple(map(int,history[0].split('.'))))

    def test_ui_rejects_stale_network_changelog(self):
        self.assertIn('return devLogValid(data)?data:null;',HTML)
        self.assertIn('data.version===DEVLOG_RELEASE_VERSION',HTML)
        self.assertIn('cancelDevLogFetch();',HTML)
        self.assertIn('devLogRender(remote,{preserveTab:true})',HTML)
        self.assertNotIn('if(remote?.version===data.version',HTML)

    def test_release_builder_and_watcher_layout(self):
        build=(APP/'tools/build_release.py').read_text()
        self.assertIn('validate_or_sync(write=False)',build)
        watcher_path=APP.parent/'watch-paint-lab.sh'
        if watcher_path.is_file():
            watcher=watcher_path.read_text()
            self.assertIn("VERSION='0.1.5'",watcher)
            self.assertIn("if embedded!=main_log or embedded.get('version')!=version:",watcher)
            self.assertIn("server_app=Path(simulated_root)/'releases'/('v'+version)",watcher)
            self.assertIn("shutil.copytree(stage/'app',server_app)",watcher)
        else:
            # Expected Ubuntu runtime layout; still enforce canonical data and
            # application checks. The packaged watcher is checked by the
            # macOS watcher, not by app-only server unit tests.
            self.assertEqual(APP.parent.name,'releases')
            self.assertEqual(APP.name,'v'+CHANGES['version'])

    def test_installer_does_not_ship_local_watcher(self):
        installer=(APP/'deploy/install.py').read_text()
        self.assertIn("shutil.copytree(stage/'app',temp)",installer)
        self.assertIn("run('runuser','-u','paint-lab'",installer)

if __name__=='__main__':unittest.main()
