"""Online macro/industry/company analysis dashboard using live market data."""
from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import pandas as pd
from flask import Flask, jsonify, render_template, request
import requests
from urllib.parse import quote


class SuggestionServiceError(RuntimeError):
    """Raised when the autocomplete service cannot respond."""


class SymbolValidationUnavailable(RuntimeError):
    """Raised when a ticker cannot be validated due to upstream issues."""


class AnalysisError(RuntimeError):
    """Raised when an analysis step fails."""


SECTOR_ETF_MAP: Dict[str, Tuple[str, str]] = {
    "Communication Services": ("XLC", "通信服务"),
    "Consumer Cyclical": ("XLY", "可选消费"),
    "Consumer Defensive": ("XLP", "必需消费"),
    "Energy": ("XLE", "能源"),
    "Financial Services": ("XLF", "金融"),
    "Financial": ("XLF", "金融"),
    "Healthcare": ("XLV", "医疗保健"),
    "Industrials": ("XLI", "工业"),
    "Real Estate": ("XLRE", "房地产"),
    "Technology": ("XLK", "科技"),
    "Basic Materials": ("XLB", "原材料"),
    "Utilities": ("XLU", "公用事业"),
}

BENCHMARK_ETF = "SPY"
SP500_INDEX = "^GSPC"
VIX_INDEX = "^VIX"
TREASURY_INDEX = "^TNX"
YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_QUOTE_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
YAHOO_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)"

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _format_float(value: Any, digits: int = 2, suffix: str = "") -> str:
    try:
        return f"{float(value):.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return "-"


def _format_percent(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "-"


def _request_yahoo_json(
    url: str,
    *,
    params: Dict[str, Any] | None = None,
    timeout: int = 10,
    error_cls: type[Exception] = AnalysisError,
    error_message: str = "无法连接到行情服务，请稍后再试。",
) -> Dict[str, Any]:
    headers = {"User-Agent": YAHOO_USER_AGENT}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:  # noqa: BLE001 - convert to domain errors
        raise error_cls(error_message) from exc
    except ValueError as exc:  # noqa: BLE001 - handle invalid json payloads
        raise error_cls("行情服务返回了无效的数据格式。") from exc


def _chart_to_series(chart_payload: Dict[str, Any], symbol: str) -> pd.Series:
    chart = chart_payload.get("chart") or {}
    error = chart.get("error")
    if error:
        description = error.get("description") if isinstance(error, dict) else None
        message = description or f"无法获取 {symbol} 的行情数据，请确认代码是否正确。"
        raise AnalysisError(message)

    results = chart.get("result") or []
    if not results:
        raise AnalysisError(f"无法获取 {symbol} 的行情数据，请确认代码是否正确。")

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}

    close_values: List[float] | None = None
    adjclose = (indicators.get("adjclose") or [{}])[0]
    if isinstance(adjclose, dict):
        close_values = adjclose.get("adjclose")
    if not close_values:
        quote = (indicators.get("quote") or [{}])[0]
        if isinstance(quote, dict):
            close_values = quote.get("close")

    if not close_values:
        raise AnalysisError(f"{symbol} 缺少收盘价数据，暂无法完成分析。")

    length = min(len(timestamps), len(close_values))
    if length == 0:
        raise AnalysisError(f"{symbol} 缺少收盘价数据，暂无法完成分析。")

    index = pd.to_datetime(timestamps[:length], unit="s")
    series = pd.Series(close_values[:length], index=index)
    series = series.dropna()
    if series.empty:
        raise AnalysisError(f"{symbol} 缺少收盘价数据，暂无法完成分析。")
    return series


def _download_close_series(symbol: str, period: str = "1y") -> pd.Series:
    url = YAHOO_CHART_URL.format(symbol=quote(symbol))
    params = {
        "range": period,
        "interval": "1d",
        "includePrePost": "false",
        "events": "div,split",
        "lang": "en-US",
        "region": "US",
    }
    payload = _request_yahoo_json(
        url,
        params=params,
        error_cls=AnalysisError,
        error_message=f"无法获取 {symbol} 的行情数据，请确认网络连接后重试。",
    )
    return _chart_to_series(payload, symbol)


@lru_cache(maxsize=512)
def _symbol_is_tradeable(symbol: str) -> bool:
    """Return True if Yahoo Finance exposes recent pricing for the symbol."""

    url = YAHOO_CHART_URL.format(symbol=quote(symbol))
    params = {
        "range": "5d",
        "interval": "1d",
        "includePrePost": "false",
        "events": "div,split",
        "lang": "en-US",
        "region": "US",
    }

    try:
        payload = _request_yahoo_json(
            url,
            params=params,
            error_cls=SymbolValidationUnavailable,
            error_message="实时验证股票有效性时遇到网络问题，请稍后再试。",
        )
    except AnalysisError as exc:  # noqa: BLE001 - ensure validation specific error type
        raise SymbolValidationUnavailable from exc

    chart = payload.get("chart") or {}
    if chart.get("error"):
        return False

    results = chart.get("result") or []
    if not results:
        return False

    indicators = results[0].get("indicators") or {}
    quote = (indicators.get("quote") or [{}])[0]
    closes = []
    if isinstance(quote, dict):
        closes = quote.get("close") or []

    return any(value is not None for value in closes)


def fetch_symbol_suggestions(query: str, limit: int = 8) -> Dict[str, Any]:
    query = query.strip()
    if not query:
        return {"results": [], "error": None}

    params = {
        "q": query,
        "quotesCount": limit,
        "newsCount": 0,
        "lang": "en-US",
        "region": "US",
    }

    try:
        response = requests.get(
            YAHOO_SEARCH_URL,
            params=params,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise SuggestionServiceError("无法连接到行情搜索服务，请检查网络后重试。") from exc

    quotes = payload.get("quotes") or []
    suggestions: List[Dict[str, str]] = []
    validation_failed = False
    for quote in quotes:
        symbol = quote.get("symbol")
        name = quote.get("longname") or quote.get("shortname") or quote.get("name")
        quote_type = (quote.get("quoteType") or "").upper()
        exch = quote.get("exchDisp") or quote.get("exch")

        if not symbol:
            continue
        if quote_type not in {"EQUITY", "ETF"}:
            continue

        try:
            if not _symbol_is_tradeable(symbol.upper()):
                continue
        except SymbolValidationUnavailable:
            validation_failed = True
            continue

        suggestions.append(
            {
                "symbol": symbol.upper(),
                "name": name or symbol.upper(),
                "exchange": exch or "",
            }
        )
        if len(suggestions) >= limit:
            break

    error_message = None
    if not suggestions and validation_failed:
        error_message = "实时验证股票有效性时遇到网络问题，请稍后再试。"

    return {"results": suggestions, "error": error_message}


# ---------------------------------------------------------------------------
# Macro layer
# ---------------------------------------------------------------------------

def evaluate_macro_cycle() -> Dict[str, Any]:
    sp500 = _download_close_series(SP500_INDEX, period="1y")
    vix = _download_close_series(VIX_INDEX, period="6mo")
    treasury = _download_close_series(TREASURY_INDEX, period="6mo")

    latest_sp = sp500.iloc[-1]
    ma50 = sp500.tail(50).mean() if len(sp500) >= 50 else float("nan")
    ma200 = sp500.tail(200).mean() if len(sp500) >= 200 else float("nan")
    trend = "牛市倾向" if ma50 >= ma200 else "熊市倾向"

    three_month_window = 63
    three_month_return = (latest_sp / sp500.iloc[-three_month_window]) - 1 if len(sp500) > three_month_window else float("nan")

    vol_window = 63
    daily_returns = sp500.pct_change().dropna()
    window_returns = daily_returns.tail(vol_window)
    annualized_vol = window_returns.std() * math.sqrt(252) if not window_returns.empty else float("nan")

    latest_vix = vix.iloc[-1]
    ten_year_yield = treasury.iloc[-1]
    rate_change = treasury.iloc[-1] - treasury.iloc[-21] if len(treasury) > 21 else float("nan")
    if math.isnan(rate_change):
        rate_trend = "利率趋势待确认"
    elif abs(rate_change) < 0.1:
        rate_trend = "利率基本稳定"
    elif rate_change > 0:
        rate_trend = "利率上行"
    else:
        rate_trend = "利率下行"

    return {
        "trend": trend,
        "sp500_level": latest_sp,
        "ma50": ma50,
        "ma200": ma200,
        "three_month_return": three_month_return,
        "annualized_vol": annualized_vol,
        "ten_year_yield": ten_year_yield,
        "rate_trend": rate_trend,
        "vix_level": latest_vix,
    }


# ---------------------------------------------------------------------------
# Sector layer
# ---------------------------------------------------------------------------

def evaluate_sector(sector: str | None) -> Dict[str, Any]:
    sector = (sector or "").strip()
    if not sector:
        return {"available": False}

    etf_info = SECTOR_ETF_MAP.get(sector)
    if not etf_info:
        return {
            "available": False,
            "message": "暂未找到对应板块 ETF，请手动选择最相关的行业基金。",
        }

    etf_symbol, sector_cn = etf_info
    etf_close = _download_close_series(etf_symbol, period="1y")
    benchmark_close = _download_close_series(BENCHMARK_ETF, period="1y")

    six_month_window = 126
    if len(etf_close) <= six_month_window or len(benchmark_close) <= six_month_window:
        raise AnalysisError("板块或基准数据不足以计算半年收益。")

    etf_return = etf_close.iloc[-1] / etf_close.iloc[-six_month_window] - 1
    benchmark_return = benchmark_close.iloc[-1] / benchmark_close.iloc[-six_month_window] - 1
    relative = etf_return - benchmark_return
    relative_label = "领先市场" if relative >= 0 else "落后市场"

    return {
        "available": True,
        "sector_cn": sector_cn,
        "etf": etf_symbol,
        "etf_return": etf_return,
        "benchmark_return": benchmark_return,
        "relative": relative,
        "relative_label": relative_label,
    }


# ---------------------------------------------------------------------------
# Company layer
# ---------------------------------------------------------------------------

def _extract_raw(value: Any) -> Any:
    if isinstance(value, dict):
        if "raw" in value:
            return value.get("raw")
        if "fmt" in value and value.get("fmt") not in {None, "", "N/A"}:
            return value.get("fmt")
    return value


def fetch_company_fundamentals(ticker: str) -> Dict[str, Any]:
    url = YAHOO_QUOTE_SUMMARY_URL.format(symbol=quote(ticker))
    params = {
        "modules": "price,summaryProfile,financialData,defaultKeyStatistics,summaryDetail",
        "lang": "en-US",
        "region": "US",
    }
    payload = _request_yahoo_json(
        url,
        params=params,
        error_cls=AnalysisError,
        error_message="无法获取公司基础数据，请确认股票代码是否有效。",
    )

    summary = payload.get("quoteSummary") or {}
    if summary.get("error"):
        raise AnalysisError("未能检索到公司的基本面信息，请稍后再试。")

    results = summary.get("result") or []
    if not results:
        raise AnalysisError("未能检索到公司的基本面信息，请稍后再试。")

    result = results[0]

    def get_value(*paths: Tuple[str, str]) -> Any:
        for module, field in paths:
            module_data = result.get(module) or {}
            value = module_data.get(field)
            value = _extract_raw(value)
            if value is not None:
                return value
        return None

    metrics = {
        "ticker": ticker,
        "longName": get_value(("price", "longName"), ("price", "shortName")) or ticker,
        "sector": get_value(("summaryProfile", "sector")),
        "industry": get_value(("summaryProfile", "industry")),
        "marketCap": get_value(("price", "marketCap")),
        "forwardPE": get_value(("summaryDetail", "forwardPE"), ("defaultKeyStatistics", "forwardPE")),
        "trailingPE": get_value(("summaryDetail", "trailingPE"), ("defaultKeyStatistics", "trailingPE")),
        "pegRatio": get_value(("defaultKeyStatistics", "pegRatio"), ("summaryDetail", "pegRatio")),
        "profitMargins": get_value(("financialData", "profitMargins")),
        "returnOnEquity": get_value(("financialData", "returnOnEquity")),
        "debtToEquity": get_value(("financialData", "debtToEquity")),
        "freeCashflow": get_value(("financialData", "freeCashflow")),
        "dividendYield": get_value(("summaryDetail", "dividendYield")),
    }

    rows = [
        ("公司名称", metrics["longName"]),
        ("所属板块", metrics.get("sector")),
        ("所属行业", metrics.get("industry")),
        (
            "市值(十亿美元)",
            metrics.get("marketCap") / 1e9 if metrics.get("marketCap") else None,
        ),
        ("Forward P/E", metrics.get("forwardPE")),
        ("Trailing P/E", metrics.get("trailingPE")),
        ("PEG", metrics.get("pegRatio")),
        ("利润率", metrics.get("profitMargins")),
        ("ROE", metrics.get("returnOnEquity")),
        ("债务/权益", metrics.get("debtToEquity")),
        (
            "自由现金流(十亿美元)",
            metrics.get("freeCashflow") / 1e9 if metrics.get("freeCashflow") else None,
        ),
        ("股息率", metrics.get("dividendYield")),
    ]

    display_rows: List[Dict[str, str]] = []
    for label, value in rows:
        if label in {"利润率", "ROE", "股息率"}:
            display_value = _format_percent(value, digits=2)
        elif label == "债务/权益":
            display_value = _format_float(value, digits=1)
        elif label in {"Forward P/E", "Trailing P/E", "PEG"}:
            display_value = _format_float(value, digits=1)
        else:
            display_value = _format_float(value, digits=2) if isinstance(value, (int, float)) else (value or "-")
        display_rows.append({"label": label, "value": display_value})

    qualitative: List[str] = []
    if metrics.get("forwardPE") is not None:
        qualitative.append(
            f"估值: forward P/E {metrics['forwardPE']:.1f}，结合行业均值判断估值水平。"
        )
    if metrics.get("profitMargins") is not None:
        qualitative.append(
            f"盈利质量: 利润率 {metrics['profitMargins']:.1%}，需关注持续性与行业对比。"
        )
    if metrics.get("returnOnEquity") is not None:
        qualitative.append(
            f"资本效率: ROE {metrics['returnOnEquity']:.1%}，用于衡量公司竞争力。"
        )
    if metrics.get("debtToEquity") is not None:
        qualitative.append(
            f"杠杆结构: 债务/权益比 {metrics['debtToEquity']:.1f}，评估财务稳健。"
        )
    if metrics.get("freeCashflow") is not None:
        qualitative.append(
            f"现金流: 自由现金流 {metrics['freeCashflow'] / 1e9:.2f} 十亿美元，支撑投资与回报。"
        )
    if metrics.get("dividendYield") is not None:
        qualitative.append(
            f"股东回报: 股息率 {metrics['dividendYield']:.2%}，结合派息可持续性评估。"
        )

    return {
        "metrics": metrics,
        "rows": display_rows,
        "qualitative": qualitative,
    }


# ---------------------------------------------------------------------------
# Commentary builder
# ---------------------------------------------------------------------------

def build_commentary(macro: Dict[str, Any], sector: Dict[str, Any], fundamentals: Dict[str, Any]) -> List[Dict[str, str]]:
    three_month = _format_percent(macro.get("three_month_return"), digits=2)
    vol = _format_percent(macro.get("annualized_vol"), digits=2)
    yield_level = _format_float(macro.get("ten_year_yield"), digits=2)
    vix_level = _format_float(macro.get("vix_level"), digits=2)
    macro_comment = (
        f"大盘当前{macro.get('trend', '趋势待确认')}，近三个月收益约 {three_month}，"
        f"年化波动率 {vol}；10 年期美债收益率 {yield_level}%，VIX 位于 {vix_level}。"
    )

    if sector.get("available"):
        sector_comment = (
            f"板块 ETF {sector.get('etf')} ({sector.get('sector_cn')}) 半年收益 { _format_percent(sector.get('etf_return')) }，"
            f"标普500 同期 { _format_percent(sector.get('benchmark_return')) }，相对表现 { _format_percent(sector.get('relative')) } ({sector.get('relative_label')})."
        )
    else:
        sector_comment = sector.get("message") or "未能匹配板块 ETF，请关注行业轮动情况。"

    qualitative = fundamentals.get("qualitative") or ["需补充更多财务指标以完善公司基本面分析。"]
    company_comment = " ".join(qualitative)

    return [
        {"title": "宏观周期解读", "content": macro_comment},
        {"title": "行业景气解读", "content": sector_comment},
        {"title": "公司基本面解读", "content": company_comment},
    ]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def perform_analysis(ticker: str) -> Dict[str, Any]:
    ticker = ticker.strip().upper()
    if not ticker:
        raise AnalysisError("请输入有效的股票代码。")

    fundamentals = fetch_company_fundamentals(ticker)
    macro = evaluate_macro_cycle()
    sector = evaluate_sector(fundamentals["metrics"].get("sector"))
    commentary = build_commentary(macro, sector, fundamentals)

    macro_rows = [
        {"label": "指数趋势", "value": macro.get("trend")},
        {"label": "标普500 收盘", "value": _format_float(macro.get("sp500_level"), digits=2)},
        {"label": "近三个月收益", "value": _format_percent(macro.get("three_month_return"), digits=2)},
        {"label": "年化波动率", "value": _format_percent(macro.get("annualized_vol"), digits=2)},
        {"label": "10年期美债收益率", "value": _format_float(macro.get("ten_year_yield"), digits=2, suffix="%")},
        {"label": "利率趋势", "value": macro.get("rate_trend")},
        {"label": "VIX 水平", "value": _format_float(macro.get("vix_level"), digits=2)},
    ]

    if sector.get("available"):
        sector_rows = [
            {"label": "板块 ETF", "value": sector.get("etf")},
            {"label": "板块中文", "value": sector.get("sector_cn")},
            {"label": "半年收益", "value": _format_percent(sector.get("etf_return"), digits=2)},
            {"label": "标普500 同期", "value": _format_percent(sector.get("benchmark_return"), digits=2)},
            {
                "label": "相对表现",
                "value": f"{_format_percent(sector.get('relative'), digits=2)} {sector.get('relative_label')}",
            },
        ]
    else:
        sector_rows = []

    return {
        "ticker": ticker,
        "company": fundamentals["metrics"].get("longName", ticker),
        "macro": {"rows": macro_rows},
        "sector": {"available": sector.get("available"), "rows": sector_rows, "message": sector.get("message")},
        "fundamentals": fundamentals,
        "commentary": commentary,
    }


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    ticker = ""
    analysis: Dict[str, Any] | None = None
    error: str | None = None

    if request.method == "POST":
        ticker = request.form.get("ticker", "").strip().upper()
        try:
            analysis = perform_analysis(ticker)
        except AnalysisError as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001 - surface friendly error
            app.logger.exception("analysis failed for %s", ticker, exc_info=exc)
            error = "获取实时数据时出现异常，请检查网络连接或稍后再试。"

    return render_template("index.html", analysis=analysis, error=error, ticker=ticker)


@app.get("/api/suggest")
def suggest() -> Any:
    query = request.args.get("q", "")
    try:
        payload = fetch_symbol_suggestions(query)
    except SuggestionServiceError as exc:
        return jsonify({"results": [], "error": str(exc)}), 503

    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
