"""Simple error handling and logging for gitswitch CLI tool."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional

from .exceptions import GitSwitchError


class LoggerMixin:
    """Simple mixin to provide consistent logger access."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger


def get_log_config(level: str = "INFO", log_file: Optional[Path] = None) -> dict:
    """Get basic logging configuration."""
    if log_file is None:
        log_dir = Path.home() / ".local" / "share" / "gitswitch"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "gitswitch.log"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(levelname)-8s %(message)s"},
            "detailed": {
                "format": "%(asctime)s [%(levelname)-8s] %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {"gitswitch": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": False}},
        "root": {"level": "WARNING", "handlers": ["console"]},
    }

    return config


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None):
    """Set up basic logging configuration."""
    config = get_log_config(level, log_file)
    logging.config.dictConfig(config)

    # Log the startup
    logger = logging.getLogger("gitswitch")
    logger.info(f"Gitswitch logging initialized at level {level}")

    # Set up exception hook for uncaught exceptions
    def exception_hook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = exception_hook


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the gitswitch prefix."""
    if not name.startswith("gitswitch"):
        name = f"gitswitch.{name}"
    return logging.getLogger(name)
