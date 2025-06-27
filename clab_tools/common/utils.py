"""Common utilities for clab-tools commands."""

import functools
import sys
from typing import Any, Callable, Optional

import click


def handle_success(message: str) -> None:
    """Display a success message with checkmark.

    Args:
        message: The success message to display
    """
    click.echo(f"✓ {message}")


def handle_error(message: str, exit_code: int = 1) -> None:
    """Display an error message and optionally exit.

    Args:
        message: The error message to display
        exit_code: Exit code (0 to not exit)
    """
    click.echo(f"✗ {message}", err=True)
    if exit_code:
        sys.exit(exit_code)


def with_lab_context(func: Callable) -> Callable:
    """Decorator that ensures lab context is available.

    This decorator checks that the database is initialized and
    available in the Click context before executing the command.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """

    @functools.wraps(func)
    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        if not ctx.obj or not ctx.obj.get("db"):
            raise click.ClickException("Database not initialized")
        return func(ctx, *args, **kwargs)

    return wrapper


def setup_remote_config(
    settings: Any,
    host: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    port: int = 22,
    enable: bool = True,
) -> None:
    """Configure remote settings in a unified way.

    Args:
        settings: Settings object to update
        host: Remote host IP/hostname
        username: Remote username
        password: Remote password
        private_key: Path to SSH private key
        port: SSH port (default: 22)
        enable: Enable remote operations
    """
    if host:
        settings.remote.host = host
    if username:
        settings.remote.username = username
    if private_key:
        settings.remote.private_key_path = private_key

    # Handle password - prompt if needed
    if password:
        settings.remote.password = password
    elif (
        not private_key
        and not settings.remote.private_key_path
        and not settings.remote.password
        and settings.remote.host
    ):
        password = click.prompt("Password", hide_input=True)
        settings.remote.password = password

    if port != 22:
        settings.remote.port = port

    settings.remote.enabled = enable


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format data as a simple ASCII table.

    Args:
        headers: List of column headers
        rows: List of rows (each row is a list of values)

    Returns:
        Formatted table string
    """
    if not rows:
        return "No data available"

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    # Build format string
    format_str = " | ".join(f"{{:<{w}}}" for w in col_widths)

    # Build table
    lines = []
    lines.append(format_str.format(*headers))
    lines.append("-+-".join("-" * w for w in col_widths))

    for row in rows:
        lines.append(format_str.format(*[str(v) for v in row]))

    return "\n".join(lines)


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    return click.confirm(message, default=default)
