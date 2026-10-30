import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestOBSExport(unittest.TestCase):
    def test_import_has_7_scenes_with_local_live_sources(self):
        obj = json.loads((ROOT / 'packaging/templates/DAZE_UNIVERSAL.template.json').read_text('utf-8'))
        self.assertEqual(len(obj['scene_order']), 7)
        sources = {s['name']: s for s in obj['sources']}
        for name, suffix in [('DAZE | DRIVER POV - LIVE TELEMETRY', '/driver'),
                             ('DAZE | BROADCAST TEAM - LIVE TELEMETRY', '/broadcast')]:
            self.assertIn(name, sources)
            s = sources[name]['settings']
            self.assertFalse(s['is_local_file'])
            self.assertEqual(s['url'], 'http://127.0.0.1:8766' + suffix)
            self.assertEqual(s['width'], 1920)
            self.assertEqual(s['height'], 1080)
        self.assertNotIn('8765', str(obj))

    def test_no_placeholder_words_in_live_overlays(self):
        for name in ('driver.html', 'broadcast.html', 'client.js', 'common.css'):
            content = (ROOT / 'daze_telemetry/web' / name).read_text('utf-8').lower()
            for bad in ('to be announced', 'tba', 'next race', 'oliver grant'):
                self.assertNotIn(bad, content)


if __name__ == '__main__':
    unittest.main()
