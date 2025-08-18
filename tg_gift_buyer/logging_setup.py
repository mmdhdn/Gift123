"""Logging configuration for the application."""
from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler


def setup_logging(level: str = "INFO", logfile: Optional[Path] = None) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    handlers = [RichHandler(rich_tracebacks=True)]
    if logfile:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=3))

    logging.basicConfig(level=level.upper(), handlers=handlers, format="%(message)s")

