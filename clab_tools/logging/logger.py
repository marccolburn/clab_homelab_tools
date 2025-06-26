"""
Logging Configuration

Provides structured logging using structlog with support for JSON and console output.
Supports file rotation and configurable log levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

import structlog
from rich.console import Console
from rich.logging import RichHandler

from ..config.settings import LoggingSettings


def setup_logging(settings: LoggingSettings) -> None:
    """
    Setup structured logging based on configuration.

    Args:
        settings: Logging configuration settings
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _get_final_processor(settings),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.level))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    if settings.format == "console":
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
        )
        console_handler.setLevel(getattr(logging, settings.level))
        root_logger.addHandler(console_handler)
    else:
        # JSON console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, settings.level))
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if settings.file_path:
        file_path = Path(settings.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=settings.max_file_size,
            backupCount=settings.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, settings.level))

        if settings.format == "json":
            formatter = logging.Formatter("%(message)s")
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def _get_final_processor(settings: LoggingSettings):
    """Get the final processor based on format setting."""
    if settings.format == "json":
        return structlog.processors.JSONRenderer()
    else:
        return structlog.dev.ConsoleRenderer(colors=True)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class that provides easy access to a logger."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


def log_function_call(func):
    """Decorator to log function calls with arguments and results."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(
            "Function called",
            function=func.__name__,
            args=(
                args[1:] if args and hasattr(args[0], "__class__") else args
            ),  # Skip 'self'
            kwargs=kwargs,
        )
        try:
            result = func(*args, **kwargs)
            logger.debug(
                "Function completed",
                function=func.__name__,
                result=(
                    result
                    if not isinstance(result, (list, dict)) or len(str(result)) < 200
                    else f"{type(result).__name__}(len={len(result)})"
                ),
            )
            return result
        except Exception as e:
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    return wrapper
