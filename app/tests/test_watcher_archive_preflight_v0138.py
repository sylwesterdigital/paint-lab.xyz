"""Regression: only exact, regular root release ZIP artifacts may be untracked.

The real watcher lives alongside app/ on macOS, but Ubuntu installs app/ only.
These watcher-specific checks run when the script is available and skip only
in the genuine app-only installation layout.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

APP=Path(__file__).resolve().parents[1]
WATCHER=APP.parent/'watch-paint-lab.sh'

class WorktreeArtifactPreflight(unittest.TestCase):
    def load_embedded_watcher(self, repo):
        if not WATCHER.is_file():
            if APP.parent.name!='releases':
                self.fail('Watcher missing outside app-only Ubuntu release layout')
            self.skipTest('Production app-only release correctly does not include watcher')
        source=WATCHER.read_text(encoding='utf-8')
        found=re.search(r"<<'PAINT_LAB_WATCH_PY'\n(.*?)\nPAINT_LAB_WATCH_PY\s*$",source,re.S)
        self.assertIsNotNone(found,'Embedded watcher Python missing')
        old_argv=sys.argv
        ns={'__name__':'watcher_regression','__file__':str(WATCHER)}
        try:
            sys.argv=['watcher-check',str(repo)]
            exec(compile(found.group(1),str(WATCHER),'exec'),ns)
        finally:
            sys.argv=old_argv
        self.assertEqual(ns['VERSION'],'0.1.6')
        self.assertIn("if line.startswith('?? ') and ignorable_untracked(path):continue",source)
        self.assertIn("if line.startswith('?? ') and ignorable_untracked(name):",source)
        return ns

    def test_whitelist_only_root_regular_versioned_zips(self):
        with tempfile.TemporaryDirectory() as t:
            repo=Path(t)
            code=self.load_embedded_watcher(repo)
            ok=repo/'PAINT_LAB_RELEASE_v0.1.36.zip';ok.write_bytes(b'archive')
            self.assertTrue(code['ignorable_untracked'](ok.name))
            self.assertFalse(code['ignorable_untracked']('unexpected.zip'))
            self.assertFalse(code['ignorable_untracked']('other/PAINT_LAB_RELEASE_v0.1.36.zip'))
            self.assertFalse(code['ignorable_untracked']('local_changes.py'))
            self.assertFalse(code['ignorable_untracked']('PAINT_LAB_RELEASE_v0.1.36.zip.tmp'))
            self.assertTrue(code['ignorable_untracked']('updates/processed/old.zip'))
            ok.unlink()
            (repo/'PAINT_LAB_RELEASE_v0.1.36.zip').symlink_to('/dev/null')
            self.assertFalse(code['ignorable_untracked']('PAINT_LAB_RELEASE_v0.1.36.zip'))

    def test_real_git_preflight_blocks_source_changes_but_not_release_zip(self):
        if not shutil.which('git'):self.skipTest('git not installed')
        with tempfile.TemporaryDirectory() as t:
            repo=Path(t)/'repo';repo.mkdir()
            subprocess.run(['git','init','-q','-b','main'],cwd=repo,check=True)
            subprocess.run(['git','remote','add','origin','git@github.com:sylwesterdigital/paint-lab.xyz.git'],cwd=repo,check=True)
            tracked=repo/'tracked.txt';tracked.write_text('clean\n')
            subprocess.run(['git','add','tracked.txt'],cwd=repo,check=True)
            subprocess.run(['git','-c','user.email=test@example.invalid','-c','user.name=Test','commit','-qm','Baseline'],cwd=repo,check=True)
            source=repo/'PAINT_LAB_RELEASE_v0.1.36.zip';source.write_bytes(b'a valid filename is not itself a Git source file')
            ns=self.load_embedded_watcher(repo)
            stage=Path(t)/'stage';stage.mkdir()
            (stage/'watch-paint-lab.sh').write_bytes(WATCHER.read_bytes())
            original_command=ns['command']
            def fake_command(args,**kwargs):
                if list(args[:2])==['git','ls-remote']:
                    return SimpleNamespace(stdout='',stderr='',returncode=0)
                return original_command(args,**kwargs)
            ns['command']=fake_command
            ns['ssh']=lambda script,timeout=100:'SSH_READY'
            ns['preflight'](stage)  # Must accept the exact root release-archive artifact.
            unexpected=repo/'unrelated.py';unexpected.write_text('print(1)\n')
            with self.assertRaisesRegex(ns['Failure'],'Uncommitted worktree changes'):
                ns['preflight'](stage)
            unexpected.unlink()
            tracked.write_text('changed\n')
            with self.assertRaisesRegex(ns['Failure'],'Uncommitted worktree changes'):
                ns['preflight'](stage)
            tracked.write_text('clean\n')
            source.unlink()
            source.symlink_to('/dev/null')
            with self.assertRaisesRegex(ns['Failure'],'Uncommitted worktree changes'):
                ns['preflight'](stage)

if __name__=='__main__':unittest.main()
