"""Local-only HTTP overlay and telemetry polling service (stdlib HTTP server)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .telemetry import SampleIRSDK, build_snapshot, empty_snapshot

HOST = '127.0.0.1'
PORT = 8766
POLL_INTERVAL = 0.25  # Four read-only snapshots per second.
BASE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
WEB_DIR = BASE_DIR / 'daze_telemetry' / 'web'
MIMES = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.ico': 'image/x-icon'}


class Bridge:
    def __init__(self, *, demo: bool = False) -> None:
        self.demo = demo
        self.lock = threading.Lock()
        self.data = empty_snapshot()
        self.stop_event = threading.Event()
        self._ir = None
        self._connected = False
        self._last_try = 0.0

    def get(self) -> dict:
        with self.lock:
            data = self.data
        # A stalled poller must not leave last race data visible forever.
        if data['connected'] and data['updated_at'] is not None and time.time() - data['updated_at'] > 2.5:
            return empty_snapshot()
        return data

    def _poll_live(self) -> dict:
        if self._ir is None:
            try:
                import irsdk
                self._ir = irsdk.IRSDK()
            except (ImportError, OSError) as exc:
                if not getattr(self, '_import_warned', False):
                    print(f'Cannot load iRacing SDK: {exc}', flush=True)
                    self._import_warned = True
                return empty_snapshot()
        ir = self._ir
        try:
            if not (ir.is_initialized and ir.is_connected):
                if self._connected:
                    ir.shutdown()
                    self._connected = False
                    print('iRacing disconnected; hiding telemetry.', flush=True)
                if time.monotonic() - self._last_try < 1.5:
                    return empty_snapshot()
                self._last_try = time.monotonic()
                if not ir.startup() or not (ir.is_initialized and ir.is_connected):
                    return empty_snapshot()
                print('iRacing connected.', flush=True)
                self._connected = True
            ir.freeze_var_buffer_latest()
            try:
                return build_snapshot(ir)
            finally:
                ir.unfreeze_var_buffer_latest()
        except Exception as exc:
            print(f'iRacing read failed; hiding telemetry: {exc}', flush=True)
            try:
                ir.shutdown()
            except Exception:
                pass
            self._connected = False
            self._last_try = time.monotonic()
            return empty_snapshot()

    def run(self) -> None:
        demo_source = SampleIRSDK() if self.demo else None
        while not self.stop_event.is_set():
            if demo_source is not None:
                snapshot = build_snapshot(demo_source, demo=True)
            else:
                snapshot = self._poll_live()
            with self.lock:
                self.data = snapshot
            self.stop_event.wait(POLL_INTERVAL)


class OverlayHandler(BaseHTTPRequestHandler):
    server_version = 'DazeTelemetry/1.3'

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == '/api/state':
            body = json.dumps(self.server.bridge.get(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            self._send(200, 'application/json', body)
            return
        if path in ('/', '/health'):
            snap = self.server.bridge.get()
            body = json.dumps({'ok': True, 'connected': snap['connected'], 'demo': snap['demo']}).encode()
            self._send(200, 'application/json', body)
            return
        if path in ('/driver', '/driver/'):
            path = '/driver.html'
        elif path in ('/broadcast', '/broadcast/'):
            path = '/broadcast.html'
        # Strict allow-list: never serve local files outside the packaged web folder.
        permitted = {'/driver.html', '/broadcast.html', '/common.css', '/client.js', '/media/daze-logo.png'}
        if path not in permitted:
            self._send(404, 'text/plain', b'Not found')
            return
        file = WEB_DIR.joinpath(path.lstrip('/'))
        try:
            body = file.read_bytes()
        except OSError:
            self._send(404, 'text/plain', b'Not found')
            return
        self._send(200, MIMES.get(file.suffix, 'application/octet-stream') + '; charset=utf-8' if file.suffix in ('.html', '.css', '.js') else MIMES.get(file.suffix, 'application/octet-stream'), body)

    def _send(self, code: int, mime: str, data: bytes) -> None:
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'")
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        if len(args) > 1 and str(args[1]) in ('404', '500'):
            print(f'HTTP: {fmt % args}', flush=True)


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host: str, port: int, bridge: Bridge) -> None:
        super().__init__((host, port), OverlayHandler)
        self.bridge = bridge


def main() -> None:
    p = argparse.ArgumentParser(description='Daze of Thunder local iRacing telemetry overlay (read-only)')
    p.add_argument('--demo', action='store_true', help='Simulated preview data, clearly watermarked in OBS')
    p.add_argument('--port', type=int, default=PORT, help='Local port (default: 8766)')
    args = p.parse_args()
    if not 1024 <= args.port <= 65535:
        p.error('port must be between 1024 and 65535')
    bridge = Bridge(demo=args.demo)
    try:
        server = Server(HOST, args.port, bridge)
    except OSError as exc:
        print(f'Cannot start Daze Telemetry on {HOST}:{args.port}: {exc}', file=sys.stderr)
        print('Close any other running Daze Telemetry instance and retry.', file=sys.stderr)
        sys.exit(1)
    thread = threading.Thread(target=bridge.run, daemon=True, name='DazeSDKPoll')
    thread.start()
    print('DAZE TELEMETRY v1.3  |  read-only  |  local PC only', flush=True)
    if args.demo:
        print('*** DEMO MODE: SIMULATED DATA, NOT FOR BROADCAST ***', flush=True)
    print(f'Driver overlay:   http://{HOST}:{args.port}/driver', flush=True)
    print(f'TV overlay:       http://{HOST}:{args.port}/broadcast', flush=True)
    print(f'Connection state: http://{HOST}:{args.port}/health', flush=True)
    print('Open OBS and iRacing. Close this window to stop the telemetry bridge.\n', flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop_event.set()
        server.server_close()
        if bridge._ir is not None:
            try:
                bridge._ir.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    main()
