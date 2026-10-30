import json
from pathlib import Path
from threading import Thread
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from daze_telemetry.server import Bridge, HOST, Server


class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = Bridge(demo=True)
        cls.server = Server(HOST, 0, cls.bridge)
        cls.port = cls.server.server_address[1]
        cls.poller = Thread(target=cls.bridge.run, daemon=True)
        cls.worker = Thread(target=cls.server.serve_forever, daemon=True)
        cls.poller.start()
        cls.worker.start()
        time.sleep(0.4)

    @classmethod
    def tearDownClass(cls):
        cls.bridge.stop_event.set()
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urlopen(f'http://{HOST}:{self.port}{path}', timeout=3) as res:
            return res.status, res.headers, res.read()

    def test_state_returns_current_snapshot(self):
        status, headers, body = self.get('/api/state')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store, max-age=0')
        data = json.loads(body)
        self.assertEqual(data['session']['track'], 'Demo Circuit')
        self.assertTrue(data['demo'])
        self.assertEqual(len(data['leaderboard']), 12)

    def test_html_is_served_from_packaged_web_directory(self):
        for path in ['/driver', '/broadcast', '/client.js', '/common.css', '/media/daze-logo.png']:
            status, headers, body = self.get(path)
            self.assertEqual(status, 200, path)
            self.assertTrue(body, path)

    def test_static_path_allowlist(self):
        with self.assertRaises(HTTPError) as ex:
            self.get('/not-a-real-page')
        self.assertEqual(ex.exception.code, 404)

    def test_stale_frames_hidden(self):
        old = {'connected': True, 'updated_at': time.time() - 100}
        from daze_telemetry.server import Bridge
        test_bridge = Bridge()
        with test_bridge.lock:
            test_bridge.data = old
        self.assertFalse(test_bridge.get()['connected'])


if __name__ == '__main__':
    unittest.main()
