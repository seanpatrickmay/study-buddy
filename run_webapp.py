#!/usr/bin/env python3
"""Launch the Study Buddy FastAPI application."""

import logging
import os
import sys
from pathlib import Path

import uvicorn


LOGGER = logging.getLogger("study_buddy.runner")
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.environ.setdefault("PYTHONPATH", str(SRC_DIR))


def main() -> None:
    """Start the Study Buddy web server using uvicorn."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    LOGGER.info("Starting Study Buddy on http://localhost:8000")
    try:
        uvicorn.run(
            "study_buddy.web.app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
        )
    except KeyboardInterrupt:  # pragma: no cover - interactive use only
        LOGGER.info("Study Buddy stopped by user request")
    except Exception as exc:  # pragma: no cover - startup failures
        LOGGER.exception("Unable to start Study Buddy: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
