from pathlib import Path
import unittest
from unittest.mock import patch

from tools.publication_guard import check_content, scan

ROOT=Path(__file__).resolve().parents[2]


class GuardTests(unittest.TestCase):
    def test_case_insensitive_asset_extension(self):
        self.assertIn('prohibited-extension',check_content('sample.GR2',b'not a real asset'))

    def test_private_path_and_address(self):
        fake_path=('Q'+':'+chr(92)+'private-test').encode()
        self.assertIn('absolute-machine-path',check_content('note.md',fake_path))
        address='.'.join(str(x) for x in (192,0,2,1)).encode()
        self.assertIn('network-address',check_content('note.md',address))

    def test_suspected_secret_and_hash(self):
        self.assertIn('github-token',check_content('note.md',('gh'+'p_'+'x'*36).encode()))
        self.assertIn('asset-fingerprint',check_content('note.md',('a'*64).encode()))

    def test_unapproved_neutral_payload(self):
        self.assertIn('unapproved-asset-payload',check_content('data.json',b'{"meshes":[]}'))
        self.assertIn('synthetic-fixture-not-reproducible',check_content('examples/synthetic_asset/neutral.json',b'{}',synthetic_bytes=b'{"original":true}'))

    def test_staged_blob_not_worktree_substitution(self):
        # Simulated Git plumbing: verifies blob data is scanned, without creating
        # any repository or reading a harmless replacement from the working tree.
        oid=b'0'*40
        with patch('tools.publication_guard.subprocess.check_output',side_effect=[b'100644 '+oid+b' 0\tnote.md\0',b'a'*64]) as git:
            self.assertEqual(scan(ROOT,staged=True)['status'],'FAIL')
            self.assertEqual(git.call_args.args[0],['git','cat-file','blob',oid.decode()])


if __name__=='__main__': unittest.main()
