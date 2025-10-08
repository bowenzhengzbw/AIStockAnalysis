"""Offline macro stock analysis web server without external network dependencies."""
from __future__ import annotations

import html
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "offline_data.json"
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"
STATIC_DIR = BASE_DIR / "static"


class OfflineDataError(RuntimeError):
    """Raised when the offline dataset is missing or corrupted."""


class OfflineDataProvider:
    """Loads and serves cached market, sector, and company data."""

    def __init__(self, data_file: Path) -> None:
        if not data_file.exists():
            raise OfflineDataError(
                "未找到离线数据文件。请确认 `data/offline_data.json` 是否存在。"
            )
        self._file: Path = data_file
        self._raw: Dict[str, Any] = {}
        self._refresh()

    def _refresh(self) -> None:
        try:
            with self._file.open("r", encoding="utf-8") as handle:
                self._raw = json.load(handle)
        except FileNotFoundError as exc:
            raise OfflineDataError("离线数据文件已删除或移动，请恢复后再试。") from exc
        except json.JSONDecodeError as exc:  # noqa: TRY003 - provide helpful message
            raise OfflineDataError("离线数据文件格式无效，请重新生成数据。") from exc

    # ------------------------------------------------------------------
    # Macro layer
    # ------------------------------------------------------------------
    def evaluate_market_cycle(self) -> Dict[str, Any]:
        macro = self._raw.get("macro", {})
        sp500 = macro.get("sp500", {})
        treasury = macro.get("treasury", {})
        vix = macro.get("vix", {})

        if not sp500 or not vix:
            raise OfflineDataError("离线数据缺少宏观指标，请补充后重试。")

        trend = "牛市倾向" if sp500.get("ma50", 0) >= sp500.get("ma200", 0) else "熊市倾向"
        rate_trend = treasury.get("rate_trend", "利率趋势未知")

        return {
            "trend": trend,
            "sp500_level": sp500.get("level"),
            "three_month_return": sp500.get("return_3m"),
            "annualized_vol": sp500.get("annualized_vol"),
            "rate_trend": rate_trend,
            "vix_level": vix.get("level"),
        }

    # ------------------------------------------------------------------
    # Sector layer
    # ------------------------------------------------------------------
    def evaluate_sector(self, sector: str) -> Dict[str, Any]:
        sector = (sector or "").strip()
        if not sector:
            return {"etf": None}

        dataset = self._raw.get("sectors", {})
        record = dataset.get(sector)
        if not record:
            return {"etf": None}

        relative = record.get("etf_return", 0) - record.get("benchmark_return", 0)
        relative_label = "领先市场" if relative >= 0 else "落后市场"

        return {
            "etf": record.get("etf"),
            "etf_return": record.get("etf_return"),
            "benchmark_return": record.get("benchmark_return"),
            "relative": round(relative, 2),
            "relative_label": relative_label,
        }

    # ------------------------------------------------------------------
    # Company layer
    # ------------------------------------------------------------------
    def company_fundamentals(self, ticker: str) -> Dict[str, Any]:
        companies = self._raw.get("companies", {})
        data = companies.get(ticker)
        if not data:
            raise OfflineDataError(
                "当前离线数据未包含该公司，请在 `data/offline_data.json` 中添加基础信息。"
            )

        qualitative: List[str] = []
        if data.get("forwardPE") is not None:
            qualitative.append(
                f"估值: forward P/E {data['forwardPE']:.1f}，结合行业均值判断估值水平。"
            )
        if data.get("profitMargins") is not None:
            qualitative.append(
                f"盈利质量: 利润率 {data['profitMargins']:.1%}，需关注持续性与行业对比。"
            )
        if data.get("returnOnEquity") is not None:
            qualitative.append(
                f"资本效率: ROE {data['returnOnEquity']:.1%}，用于衡量公司竞争力。"
            )
        if data.get("debtToEquity") is not None:
            qualitative.append(
                f"杠杆结构: 债务/权益比 {data['debtToEquity']:.1f}，评估财务稳健。"
            )
        if data.get("freeCashflow") is not None:
            qualitative.append(
                f"现金流: 自由现金流 {data['freeCashflow'] / 1e9:.2f} 十亿美元，支撑投资与回报。"
            )
        if data.get("dividendYield") is not None:
            qualitative.append(
                f"股东回报: 股息率 {data['dividendYield']:.2%}，结合派息可持续性评估。"
            )

        return {"metrics": data, "qualitative": qualitative}

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------
    def perform_analysis(self, ticker: str) -> Dict[str, Any]:
        self._refresh()
        ticker = ticker.strip().upper()
        if not ticker:
            raise ValueError("请输入有效的股票代码。")

        fundamentals = self.company_fundamentals(ticker)
        macro = self.evaluate_market_cycle()
        sector = self.evaluate_sector(fundamentals["metrics"].get("sector", ""))
        commentary = self._build_commentary(macro, sector, fundamentals)

        return {
            "ticker": ticker,
            "company": fundamentals["metrics"].get("longName", ticker),
            "macro": macro,
            "sector": sector,
            "fundamentals": fundamentals,
            "commentary": commentary,
        }

    def _build_commentary(
        self,
        macro: Dict[str, Any],
        sector: Dict[str, Any],
        fundamentals: Dict[str, Any],
    ) -> Dict[str, str]:
        trend = macro.get("trend") or "趋势待确认"
        three_month = _format_percent(macro.get("three_month_return"))
        vol = _format_percent(macro.get("annualized_vol"))
        rate = macro.get("rate_trend") or "利率趋势未知"
        vix = _format_float(macro.get("vix_level"))
        cycle_comment = (
            f"大盘当前{trend}，近三个月收益约 {three_month}，"
            f"波动率 {vol}；利率环境{rate}，VIX 位于 {vix}。"
        )

        if sector.get("etf"):
            etf = _escape(sector.get("etf"))
            etf_return = _format_percent(sector.get("etf_return"))
            benchmark = _format_percent(sector.get("benchmark_return"))
            relative = _format_percent(sector.get("relative"))
            relative_label = _escape(sector.get("relative_label") or "表现待确认")
            sector_comment = (
                f"板块 ETF {etf} 半年收益 {etf_return}，"
                f"标普500 同期 {benchmark}，相对表现 {relative} ({relative_label})。"
            )
        else:
            sector_comment = "离线数据暂未覆盖该板块 ETF，请补充行业轮动信息。"

        if fundamentals["qualitative"]:
            fundamental_comment = " ".join(fundamentals["qualitative"])
        else:
            fundamental_comment = "需补充更多财务指标以完善公司基本面分析。"

        return {
            "cycle": cycle_comment,
            "sector": sector_comment,
            "company": fundamental_comment,
        }


def load_template() -> str:
    if not TEMPLATE_PATH.exists():
        raise OfflineDataError("未找到网页模板文件 `templates/index.html`。")
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _format_float(value: Any, digits: int = 2, suffix: str = "") -> str:
    try:
        return f"{float(value):.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return "-"


def _format_percent(value: Any, digits: int = 2, ratio: bool = False) -> str:
    try:
        numeric = float(value) * (100 if ratio else 1)
        return f"{numeric:.{digits}f}%"
    except (TypeError, ValueError):
        return "-"


def build_error_block(error: str | None) -> str:
    if not error:
        return ""
    return f'<div class="alert alert-error">{_escape(error)}</div>'


def build_commentary_block(commentary: Dict[str, str]) -> str:
    parts = []
    for title, content in (
        ("宏观周期解读", commentary.get("cycle", "")),
        ("行业景气解读", commentary.get("sector", "")),
        ("公司基本面解读", commentary.get("company", "")),
    ):
        parts.append(
            "<div class=\"commentary-card\">"
            f"<h3>{_escape(title)}</h3><p>{_escape(content)}</p>"
            "</div>"
        )
    return "".join(parts)


def build_macro_block(macro: Dict[str, Any]) -> str:
    rows = [
        ("指数趋势", macro.get("trend")),
        ("标普500 收盘", _format_float(macro.get("sp500_level"))),
        ("近三个月收益", _format_percent(macro.get("three_month_return"))),
        ("年化波动率", _format_percent(macro.get("annualized_vol"))),
        ("利率趋势", macro.get("rate_trend")),
        ("VIX 水平", _format_float(macro.get("vix_level"))),
    ]
    items = [
        f"<li><span>{_escape(label)}</span><strong>{_escape(value)}</strong></li>"
        for label, value in rows
    ]
    return "<ul class=\"metric-list\">" + "".join(items) + "</ul>"


def build_sector_block(sector: Dict[str, Any]) -> str:
    if not sector.get("etf"):
        return "<p>尚无板块 ETF 数据，请补充离线数据。</p>"

    rows = [
        ("板块 ETF", sector.get("etf")),
        ("半年收益", _format_percent(sector.get("etf_return"))),
        ("标普500 同期", _format_percent(sector.get("benchmark_return"))),
        (
            "相对表现",
            f"{_format_percent(sector.get('relative'))} {_escape(sector.get('relative_label'))}",
        ),
    ]
    items = [
        f"<li><span>{_escape(label)}</span><strong>{_escape(value)}</strong></li>"
        for label, value in rows
    ]
    return "<ul class=\"metric-list\">" + "".join(items) + "</ul>"


def build_fundamental_block(fundamentals: Dict[str, Any]) -> str:
    metrics = fundamentals.get("metrics", {})
    display_pairs: List[Tuple[str, Any]] = [
        ("公司名称", metrics.get("longName")),
        ("所属板块", metrics.get("sector")),
        ("所属行业", metrics.get("industry")),
        (
            "市值(十亿美元)",
            _format_float(
                metrics.get("marketCap") / 1e9 if metrics.get("marketCap") is not None else None,
                digits=1,
            ),
        ),
        ("Forward P/E", _format_float(metrics.get("forwardPE"), digits=1)),
        ("Trailing P/E", _format_float(metrics.get("trailingPE"), digits=1)),
        ("PEG", _format_float(metrics.get("pegRatio"), digits=1)),
        ("利润率", _format_percent(metrics.get("profitMargins"), digits=1, ratio=True)),
        ("ROE", _format_percent(metrics.get("returnOnEquity"), digits=1, ratio=True)),
        ("债务/权益", _format_float(metrics.get("debtToEquity"), digits=1)),
        (
            "自由现金流(十亿美元)",
            _format_float(
                metrics.get("freeCashflow") / 1e9
                if metrics.get("freeCashflow") is not None
                else None,
                digits=2,
            ),
        ),
        ("股息率", _format_percent(metrics.get("dividendYield"), digits=2, ratio=True)),
    ]

    items = []
    for label, raw_value in display_pairs:
        value = raw_value if raw_value not in (None, "None") else "-"
        items.append(
            f"<li><span>{_escape(label)}</span><strong>{_escape(value)}</strong></li>"
        )
    qualitative = "".join(
        f"<li>{_escape(text)}</li>" for text in fundamentals.get("qualitative", [])
    )

    return (
        "<div class=\"fundamental-grid\">"
        + "".join(items)
        + "</div><div class=\"qualitative\"><ul>"
        + qualitative
        + "</ul></div>"
    )


def build_analysis_block(analysis: Dict[str, Any] | None) -> str:
    if not analysis:
        return ""

    return f"""
    <section class=\"analysis\">
      <header>
        <h2>{_escape(analysis['company'])} ({_escape(analysis['ticker'])})</h2>
      </header>
      <div class=\"grid\">
        <div class=\"card\">
          <h3>宏观周期</h3>
          {build_macro_block(analysis['macro'])}
        </div>
        <div class=\"card\">
          <h3>行业/板块</h3>
          {build_sector_block(analysis['sector'])}
        </div>
        <div class=\"card\">
          <h3>公司基本面</h3>
          {build_fundamental_block(analysis['fundamentals'])}
        </div>
      </div>
      <div class=\"commentary\">
        {build_commentary_block(analysis['commentary'])}
      </div>
    </section>
    """


class AnalysisHTTPRequestHandler(BaseHTTPRequestHandler):
    provider = OfflineDataProvider(DATA_PATH)
    template = load_template()

    def do_GET(self) -> None:  # noqa: N802 - HTTP method name
        if self.path.startswith("/static/"):
            self.serve_static()
            return
        self.respond_page()

    def do_POST(self) -> None:  # noqa: N802 - HTTP method name
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)
        ticker = params.get("ticker", [""])[0]

        analysis = None
        error = None
        try:
            analysis = self.provider.perform_analysis(ticker)
        except (ValueError, OfflineDataError) as exc:
            error = str(exc)

        self.respond_page(analysis, error, ticker)

    # ------------------------------------------------------------------
    def serve_static(self) -> None:
        relative = self.path.lstrip("/")
        file_path = (BASE_DIR / relative).resolve()
        try:
            file_path.relative_to(STATIC_DIR)
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif file_path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg"}:
            content_type = f"image/{file_path.suffix.lstrip('.')}"
        else:
            content_type = "application/octet-stream"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()
        with file_path.open("rb") as handle:
            self.wfile.write(handle.read())

    def respond_page(
        self,
        analysis: Dict[str, Any] | None = None,
        error: str | None = None,
        ticker: str = "",
    ) -> None:
        body = self.template.replace("${error_block}", build_error_block(error))
        body = body.replace("${analysis_block}", build_analysis_block(analysis))
        body = body.replace("${ticker_value}", _escape(ticker))

        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - match BaseHTTPRequestHandler signature
        """Silence default logging to keep console clean."""
        return


def run_server() -> None:
    port = int(os.environ.get("PORT", "5000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AnalysisHTTPRequestHandler)
    print(f"离线宏观分析仪表盘已启动: http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
