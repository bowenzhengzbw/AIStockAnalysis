"""Lightweight HTTP server exposing Macro Sentinel output."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from src.agents import MacroSentinelAgent
from src.examples.personal_pipeline import build_runtime

LOGGER = logging.getLogger(__name__)


class MacroReportHandler(BaseHTTPRequestHandler):
    server_version = "AIStockAnalysisHTTP/0.1"

    def _write_json(self, payload: object, *, status: int = 200, send_body: bool = True) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _write_html(self, body: str, *, status: int = 200, send_body: bool = True) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self._dispatch(send_body=True)

    def do_HEAD(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self._dispatch(send_body=False)

    def _dispatch(self, *, send_body: bool) -> None:
        parsed = urlsplit(self.path)
        path = parsed.path or "/"
        query = parse_qs(parsed.query)

        if path in {"", "/"}:
            index_html = (
                "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
                "<title>AIStockAnalysis 服务</title>"
                "<style>body{font-family:'Noto Sans SC',system-ui,sans-serif;margin:2rem;background-color:#f1f5f9;color:#0f172a;}"
                "h1{font-size:2rem;margin-bottom:1rem;}ul{padding-left:1.2rem;}li{margin:0.5rem 0;}a{color:#2563eb;text-decoration:none;}"
                "a:hover{text-decoration:underline;}</style></head><body><h1>AIStockAnalysis 预览服务</h1>"
                "<p>可用端点：</p><ul><li><a href=\"/health\">/health</a> — 健康检查</li>"
                "<li><a href=\"/macro/report\">/macro/report</a> — 宏观巡检 JSON</li>"
                "<li><a href=\"/macro/report?format=html\">/macro/report?format=html</a> — 宏观巡检 HTML 预览</li>"
                "</ul></body></html>"
            )
            self._write_html(index_html, send_body=send_body)
            return
        if path == "/health":
            self._write_json({"status": "ok"}, send_body=send_body)
            return
        if path == "/macro/report":
            response_format = query.get("format", ["json"])[0].lower()
            self._handle_macro_report(
                response_format=response_format, send_body=send_body
            )
            return
        if send_body:
            self.send_error(404, "Not Found")
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - override
        LOGGER.info("%s - - %s", self.client_address[0], format % args)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _handle_macro_report(
        self, *, response_format: str = "json", send_body: bool = True
    ) -> None:
        runtime = build_runtime()
        try:
            context = runtime.run()
            agent = MacroSentinelAgent()
            report = agent.generate_report(context)
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to build macro report: %s", exc)
            self._write_json({"error": "internal_error", "detail": str(exc)}, status=500)
            return
        if response_format == "html":
            self._write_html(report.to_html(), send_body=send_body)
            return

        payload = {
            "title": report.title,
            "highlights": report.highlights,
            "metrics": report.metrics,
            "policy_events": report.policy_events,
            "metadata": report.metadata,
            "markdown": report.to_markdown(),
        }
        self._write_json(payload, send_body=send_body)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    server: ThreadingHTTPServer = ThreadingHTTPServer((host, port), MacroReportHandler)
    return server


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(host, port)
    LOGGER.info("Serving AIStockAnalysis HTTP endpoints on %s:%s", host, server.server_address[1])
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        LOGGER.info("Shutting down server")
    finally:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    run()
