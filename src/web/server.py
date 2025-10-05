"""Lightweight HTTP server exposing Macro Sentinel output."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.agents import MacroSentinelAgent
from src.examples.personal_pipeline import build_runtime

LOGGER = logging.getLogger(__name__)


class MacroReportHandler(BaseHTTPRequestHandler):
    server_version = "AIStockAnalysisHTTP/0.1"

    def _write_json(self, payload: object, *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path.rstrip("/") == "":
            self._write_json({"message": "AIStockAnalysis HTTP endpoint"})
            return
        if self.path == "/health":
            self._write_json({"status": "ok"})
            return
        if self.path == "/macro/report":
            self._handle_macro_report()
            return
        self.send_error(404, "Not Found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - override
        LOGGER.info("%s - - %s", self.client_address[0], format % args)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _handle_macro_report(self) -> None:
        runtime = build_runtime()
        try:
            context = runtime.run()
            agent = MacroSentinelAgent()
            report = agent.generate_report(context)
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to build macro report: %s", exc)
            self._write_json({"error": "internal_error", "detail": str(exc)}, status=500)
            return
        payload = {
            "title": report.title,
            "highlights": report.highlights,
            "metrics": report.metrics,
            "policy_events": report.policy_events,
            "metadata": report.metadata,
            "markdown": report.to_markdown(),
        }
        self._write_json(payload)


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
