"""
Error Handlers

Provides decorators and context managers for handling errors gracefully.
"""

import functools
import sys
from contextlib import contextmanager
from typing import Type, Union

import click
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import (
    ClabToolsError,
    CSVImportError,
    DatabaseError,
    ValidationError,
)


def error_handler(
    exceptions: Union[Type[Exception], tuple] = Exception,
    exit_on_error: bool = True,
    log_error: bool = True,
    reraise: bool = False,
):
    """
    Decorator to handle exceptions in CLI commands.

    Args:
        exceptions: Exception type(s) to catch
        exit_on_error: Whether to exit the program on error
        log_error: Whether to log the error
        reraise: Whether to reraise the exception after handling
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    from ..log_config.logger import get_logger

                    logger = get_logger(func.__module__)

                    if isinstance(e, ClabToolsError):
                        logger.error(
                            "Command failed",
                            function=func.__name__,
                            error=e.message,
                            details=e.details,
                        )
                        # Display user-friendly error message
                        click.echo(f"✗ Error: {e.message}", err=True)
                        if e.details and click.get_current_context().obj.get(
                            "debug", False
                        ):
                            click.echo(f"Details: {e.details}", err=True)
                    else:
                        logger.error(
                            "Unexpected error",
                            function=func.__name__,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        click.echo(f"✗ Unexpected error: {e}", err=True)

                if reraise:
                    raise

                if exit_on_error:
                    sys.exit(1)

                return None

        return wrapper

    return decorator


def handle_database_errors(func):
    """Decorator to handle database-specific errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            operation = func.__name__
            raise DatabaseError(
                f"Database operation failed: {operation}",
                operation=operation,
                original_error=e,
            )

    return wrapper


def handle_validation_errors(func):
    """Decorator to handle validation errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Validation failed in {func.__name__}: {str(e)}", field=func.__name__
            )

    return wrapper


@contextmanager
def safe_operation(operation_name: str, logger=None):
    """
    Context manager for safe operations with logging.

    Args:
        operation_name: Name of the operation being performed
        logger: Logger instance (optional)
    """
    if logger is None:
        from ..log_config.logger import get_logger

        logger = get_logger(__name__)

    logger.debug("Starting operation", operation=operation_name)

    try:
        yield
        logger.debug("Operation completed successfully", operation=operation_name)
    except ClabToolsError:
        logger.error("Operation failed", operation=operation_name)
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in operation",
            operation=operation_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise ClabToolsError(
            f"Unexpected error in {operation_name}: {str(e)}",
            details={"operation": operation_name, "error_type": type(e).__name__},
        )


def validate_file_exists(file_path: str) -> None:
    """Validate that a file exists."""
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        raise ValidationError(
            f"File not found: {file_path}",
            field="file_path",
            value=file_path,
            constraint="must_exist",
        )

    if not path.is_file():
        raise ValidationError(
            f"Path is not a file: {file_path}",
            field="file_path",
            value=file_path,
            constraint="must_be_file",
        )


def validate_required_columns(
    data: dict, required_columns: list, source: str = "data"
) -> None:
    """Validate that required columns are present in data."""
    missing_columns = [col for col in required_columns if col not in data]
    if missing_columns:
        raise CSVImportError(
            f"Missing required columns in {source}: {', '.join(missing_columns)}",
            file_path=source if source != "data" else None,
        )
