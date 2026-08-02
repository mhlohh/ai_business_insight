import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "litmus7.log"


def get_logger(name: str = "litmus7") -> logging.Logger:
    """
    Creates and configures a dedicated logger for the application.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if the logger is already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        try:
            import os
            # Avoid file logs in Vercel or read-only/serverless environments
            if not (os.getenv("VERCEL") or os.getenv("NOW_REGION")):
                LOG_DIR.mkdir(parents=True, exist_ok=True)
                file_handler = RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=5_242_880,
                    backupCount=3,
                    encoding="utf-8",
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        except Exception as e:
            # Fallback gracefully without crashing
            print(f"Warning: Could not initialize file logging: {e}. Logging to stdout only.")

    return logger


# Create a default instance to be imported across the app
logger = get_logger()


def log_agent_event(event) -> None:
    """
    Logs intermediate agent events from Google ADK runner events.
    """
    if not event.partial:
        author = event.author or "System"
        node_path = event.node_info.path if event.node_info else "unknown"
        logger.info(
            f"🔄 [Agent Event] Author: {author} | Node Path: {node_path}"
        )
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    snippet = part.text.strip().replace("\n", " ")
                    if len(snippet) > 100:
                        snippet = snippet[:100] + "..."
                    logger.info(f"   ├─ Output Text: {snippet}")
        if event.output is not None:
            logger.debug(f"   ├─ Output Data: {event.output}")

