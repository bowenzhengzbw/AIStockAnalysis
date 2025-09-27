"""Logging utilities aligned with financial industry audit requirements."""

from __future__ import annotations

import logging
from logging import Logger

_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s | trace_id=%(trace_id)s"
)


def get_logger(name: str) -> Logger:
    """Return a logger with consistent formatting.

    金融行业常见的合规需求包括：
    - 统一的日志时间戳与等级显示。
    - 便于审计追踪的 trace id 字段。
    """

    logging.setLoggerClass(_AuditLogger)
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(_LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class _AuditLogger(logging.Logger):
    """Custom logger injecting trace id for compliance-friendly logs."""

    def makeRecord(self, *args, **kwargs):  # type: ignore[override]
        record = super().makeRecord(*args, **kwargs)
        if not hasattr(record, "trace_id"):
            record.trace_id = "N/A"
        return record
