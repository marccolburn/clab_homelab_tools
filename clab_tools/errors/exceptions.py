"""
Custom Exception Classes

Defines specific exception types for different error conditions in clab-tools.
"""

from typing import Any, Dict, Optional


class ClabToolsError(Exception):
    """Base exception for all clab-tools errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class DatabaseError(ClabToolsError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__

        super().__init__(message, details)
        self.operation = operation
        self.original_error = original_error


class ConfigurationError(ClabToolsError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value

        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class TopologyError(ClabToolsError):
    """Raised when topology generation or processing fails."""

    def __init__(
        self,
        message: str,
        topology_name: Optional[str] = None,
        template_path: Optional[str] = None,
    ):
        details = {}
        if topology_name:
            details["topology_name"] = topology_name
        if template_path:
            details["template_path"] = template_path

        super().__init__(message, details)
        self.topology_name = topology_name
        self.template_path = template_path


class BridgeError(ClabToolsError):
    """Raised when bridge operations fail."""

    def __init__(
        self,
        message: str,
        bridge_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if bridge_name:
            details["bridge_name"] = bridge_name
        if operation:
            details["operation"] = operation

        super().__init__(message, details)
        self.bridge_name = bridge_name
        self.operation = operation


class CSVImportError(ClabToolsError):
    """Raised when CSV import operations fail."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        row_number: Optional[int] = None,
        column: Optional[str] = None,
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if row_number is not None:
            details["row_number"] = row_number
        if column:
            details["column"] = column

        super().__init__(message, details)
        self.file_path = file_path
        self.row_number = row_number
        self.column = column


class ValidationError(ClabToolsError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        if constraint:
            details["constraint"] = constraint

        super().__init__(message, details)
        self.field = field
        self.value = value
        self.constraint = constraint
