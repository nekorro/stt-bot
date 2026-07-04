"""Threaded HTTP server exposing /metrics, /healthz, /readyz."""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import metrics  # noqa: F401 (ensures BUILD_INFO is registered)

_ready = threading.Event()


def set_ready(value: bool = True) -> None:
    if value:
        _ready.set()
    else:
        _ready.clear()


def is_ready() -> bool:
    return _ready.is_set()


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str = "text/plain") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path == "/metrics":
            self._send(200, generate_latest(), CONTENT_TYPE_LATEST)
        elif self.path == "/healthz":
            self._send(200, b"ok")
        elif self.path == "/readyz":
            if is_ready():
                self._send(200, b"ready")
            else:
                self._send(503, b"not ready")
        else:
            self._send(404, b"not found")

    def log_message(self, *args) -> None:  # silence default stderr logging
        pass


def start_monitoring_server(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
