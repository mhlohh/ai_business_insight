import logging
import sys


def get_logger(name: str = "litmus7") -> logging.Logger:
    """
    Creates and configures a dedicated logger for the application.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if the logger is already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

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
            logger.info(f"   ├─ Output Data: {event.output}")

