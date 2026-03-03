from __future__ import annotations

import logging
from pathlib import Path


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def ensure_results_dir() -> Path:
    path = Path("files/query_results")
    path.mkdir(parents=True, exist_ok=True)
    return path
