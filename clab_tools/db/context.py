"""
Database Context Helpers

Helper functions for working with the multi-lab database in a simplified way.
"""

from typing import Any, Dict

from .manager import DatabaseManager


def get_lab_db(ctx: Dict[str, Any]) -> DatabaseManager:
    """Get the database manager from the click context.

    Args:
        ctx: Click context dictionary

    Returns:
        DatabaseManager instance configured for the current lab
    """
    return ctx["db"]
