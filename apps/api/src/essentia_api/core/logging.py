from __future__ import annotations

import logging
import sys

import structlog
import structlog.dev


def setup_logging(
    *,
    level: str = "INFO",
    json_logs: bool = True,
) -> None:
    """
    Configure structlog for the application process.

    Production defaults to JSON lines on stdout so Docker/log collectors
    can ingest them without a custom file path. Development uses a
    human-readable console renderer.
    """
    log_level = getattr(
        logging,
        level.upper(),
        logging.INFO,
    )

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )
