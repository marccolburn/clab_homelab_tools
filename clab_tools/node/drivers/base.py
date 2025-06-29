"""Base driver interface for vendor-agnostic node operations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ConfigFormat(Enum):
    """Configuration format types."""

    TEXT = "text"
    SET = "set"
    XML = "xml"
    JSON = "json"


class ConfigLoadMethod(Enum):
    """Configuration load methods."""

    MERGE = "merge"
    OVERRIDE = "override"
    REPLACE = "replace"


@dataclass
class CommandResult:
    """Result from command execution."""

    node_name: str
    command: str
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    duration: float = 0.0


@dataclass
class ConfigResult:
    """Result from configuration operation."""

    node_name: str
    success: bool
    message: str
    diff: Optional[str] = None
    error: Optional[str] = None
    rollback_id: Optional[int] = None


@dataclass
class ConnectionParams:
    """Parameters for device connection."""

    host: str
    username: str
    password: Optional[str] = None
    port: int = 22
    timeout: int = 30
    private_key_file: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None


class BaseNodeDriver(ABC):
    """Abstract base class for vendor-specific node drivers."""

    def __init__(self, connection_params: ConnectionParams):
        """Initialize driver with connection parameters.

        Args:
            connection_params: Connection parameters for the device
        """
        self.connection_params = connection_params
        self._connected = False

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the device.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the device."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to device.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def execute_command(
        self, command: str, timeout: Optional[int] = None
    ) -> CommandResult:
        """Execute a command on the device.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            CommandResult with output and status
        """
        pass

    @abstractmethod
    def execute_commands(
        self, commands: List[str], timeout: Optional[int] = None
    ) -> List[CommandResult]:
        """Execute multiple commands on the device.

        Args:
            commands: List of commands to execute
            timeout: Command timeout in seconds

        Returns:
            List of CommandResult objects
        """
        pass

    @abstractmethod
    def load_config(
        self,
        config_content: str,
        format: ConfigFormat = ConfigFormat.TEXT,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        commit_comment: Optional[str] = None,
    ) -> ConfigResult:
        """Load configuration to the device.

        Args:
            config_content: Configuration content to load
            format: Configuration format
            method: Load method (merge, override, replace)
            commit_comment: Optional commit comment

        Returns:
            ConfigResult with status and details
        """
        pass

    @abstractmethod
    def load_config_from_file(
        self,
        device_file_path: str,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        commit_comment: Optional[str] = None,
    ) -> ConfigResult:
        """Load configuration from a file on the device.

        Args:
            device_file_path: Path to config file on device
            method: Load method (merge, override, replace)
            commit_comment: Optional commit comment

        Returns:
            ConfigResult with status and details
        """
        pass

    @abstractmethod
    def validate_config(
        self, config_content: str, format: ConfigFormat = ConfigFormat.TEXT
    ) -> Tuple[bool, Optional[str]]:
        """Validate configuration without applying.

        Args:
            config_content: Configuration to validate
            format: Configuration format

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_config_diff(self) -> Optional[str]:
        """Get configuration diff for pending changes.

        Returns:
            Configuration diff or None if no changes
        """
        pass

    @abstractmethod
    def commit_config(
        self, comment: Optional[str] = None, confirmed: bool = False, timeout: int = 0
    ) -> ConfigResult:
        """Commit configuration changes.

        Args:
            comment: Optional commit comment
            confirmed: Use confirmed commit
            timeout: Confirmed commit timeout in seconds

        Returns:
            ConfigResult with commit status
        """
        pass

    @abstractmethod
    def rollback_config(self, rollback_id: Optional[int] = None) -> ConfigResult:
        """Rollback configuration.

        Args:
            rollback_id: Specific rollback ID or None for last

        Returns:
            ConfigResult with rollback status
        """
        pass

    @abstractmethod
    def get_facts(self) -> Dict[str, Any]:
        """Get device facts/information.

        Returns:
            Dictionary of device facts
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    @classmethod
    @abstractmethod
    def get_supported_vendors(cls) -> List[str]:
        """Get list of supported vendor names.

        Returns:
            List of vendor names this driver supports
        """
        pass

    @classmethod
    @abstractmethod
    def get_supported_device_types(cls) -> List[str]:
        """Get list of supported device types.

        Returns:
            List of device types this driver supports
        """
        pass
