import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


class TestReleaseBuilder(unittest.TestCase):
    def test_windows_zip_structure_and_assets(self):
        with TemporaryDirectory() as temp:
            temp = Path(temp)
            fake_exe = temp / 'DazeTelemetry.exe'
            fake_exe.write_bytes(b'MZTEST_ONLY_NOT_A_REAL_EXE')
            out = temp / 'release.zip'
            subprocess.run([sys.executable, str(ROOT/'scripts/package_release.py'),
                            '--exe', str(fake_exe), '--output', str(out)],
                           check=True, capture_output=True, text=True)
            with ZipFile(out) as z:
                names = z.namelist()
                prefix = 'Daze_of_Thunder_Broadcast_Kit_v1.3/'
                self.assertIn(prefix + 'DazeTelemetry.exe', names)
                self.assertIn(prefix + 'INSTALL_WINDOWS.cmd', names)
                self.assertIn(prefix + 'INSTALL_WINDOWS.ps1', names)
                self.assertIn(prefix + 'START_DAZE.cmd', names)
                self.assertIn(prefix + 'templates/DAZE_UNIVERSAL.template.json', names)
                self.assertIn(prefix + 'assets/media/daze-logo.png', names)
                scene = json.loads(z.read(prefix + 'templates/DAZE_UNIVERSAL.template.json'))
                self.assertEqual(len(scene['scene_order']), 7)


if __name__ == '__main__':
    unittest.main()
