from __future__ import annotations

import logging
from pathlib import Path


DEFAULT_LOG_FILE_PATH = Path("logs/twitch_moderator.log")


def configure_logging(level: int = logging.INFO, log_file_path: str | Path = DEFAULT_LOG_FILE_PATH) -> None:
    path = Path(log_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(path, encoding="utf-8"),
        ],
        force=True,
    )
