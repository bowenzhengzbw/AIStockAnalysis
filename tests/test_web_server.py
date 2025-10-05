"""Tests for the lightweight HTTP server."""

from __future__ import annotations

import json
import threading
import time
import urllib.request

from src.web import create_server


def _start_server():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Wait briefly for the server to start
    time.sleep(0.05)
    return server, thread


def _stop_server(server, thread) -> None:
    server.shutdown()
    thread.join(timeout=1)
    server.server_close()


def test_health_endpoint_serves_json():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/health") as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload == {"status": "ok"}
    finally:
        _stop_server(server, thread)


def test_macro_report_endpoint_returns_expected_structure():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/macro/report") as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["title"] == "宏观巡检快照"
            assert payload["highlights"]
            assert payload["markdown"].startswith("# 宏观巡检快照")
    finally:
        _stop_server(server, thread)
