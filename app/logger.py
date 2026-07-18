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
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
    return logger

# Create a default instance to be imported across the app
logger = get_logger()
