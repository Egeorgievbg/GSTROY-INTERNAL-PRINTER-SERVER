from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> None:
    """Wire up a rotating log handler for long-term auditing."""
    log_dir = Path(os.environ.get("GSTROY_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / os.environ.get("GSTROY_LOG_FILE", "gstroy-server.log")
    max_bytes = int(os.environ.get("GSTROY_LOG_MAX_BYTES", 5 * 1024 * 1024))
    backup_count = int(os.environ.get("GSTROY_LOG_BACKUP_COUNT", 5))

    handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )

    root_logger = logging.getLogger()
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == log_file for h in root_logger.handlers):
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%H:%M:%S")
        )
        root_logger.addHandler(stream_handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
