"""
app/utils/logger.py
===================
Logging configuration for the application.
Sets up both file and console handlers with coloured console output.
"""

from __future__ import annotations

import logging
import logging.handlers
import os

from config.settings import LOG_FILE, LOG_LEVEL


def setup_logger() -> None:
    """
    Configure the root logger with:
    - A rotating file handler (5 MB, 3 backups)
    - A coloured console handler
    """
    level = getattr(logging, LOG_LEVEL.upper(), logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding handlers multiple times (e.g. in test runs)
    if root.handlers:
        return

    fmt_file = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fmt_console = logging.Formatter("%(levelname)-8s  %(name)s  %(message)s")

    # ── File handler ──────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setFormatter(fmt_file)
    fh.setLevel(level)
    root.addHandler(fh)

    # ── Console handler ───────────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setFormatter(fmt_console)
    ch.setLevel(logging.INFO)
    root.addHandler(ch)
