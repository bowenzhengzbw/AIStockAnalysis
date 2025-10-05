"""Tests for the lightweight HTTP server."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from urllib.error import HTTPError

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


def test_root_page_lists_available_endpoints():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/") as response:
            body = response.read().decode("utf-8")
            assert "/macro/report" in body
            assert "/policy/report" in body
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


def test_macro_report_endpoint_can_render_html():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/macro/report?format=html"
        ) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8")
            assert "text/html" in content_type
            assert "宏观巡检快照" in body
            assert "指标速览" in body
    finally:
        _stop_server(server, thread)


def test_policy_report_endpoint_returns_expected_structure():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/policy/report") as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["title"] == "政策速览巡航"
            assert payload["highlights"]
            assert payload["markdown"].startswith("# 政策速览巡航")
    finally:
        _stop_server(server, thread)


def test_policy_report_endpoint_can_render_html():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/policy/report?format=html"
        ) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8")
            assert "text/html" in content_type
            assert "政策速览巡航" in body
            assert "关键结论" in body
    finally:
        _stop_server(server, thread)


def test_unknown_endpoint_returns_404():
    server, thread = _start_server()
    host, port = server.server_address
    try:
        try:
            urllib.request.urlopen(f"http://{host}:{port}/unknown")
        except HTTPError as exc:
            assert exc.code == 404
        else:  # pragma: no cover - urllib should raise for 404
            raise AssertionError("Expected HTTP 404")
    finally:
        _stop_server(server, thread)
