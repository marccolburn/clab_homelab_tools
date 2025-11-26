"""Juniper PyEZ driver implementation."""

import io
import logging
import os
import time
import warnings
from contextlib import redirect_stderr
from typing import Any, Dict, List, Optional, Tuple

from jnpr.junos import Device
from jnpr.junos.exception import (
    CommitError,
    ConfigLoadError,
    ConnectError,
    RpcError,
)
from jnpr.junos.utils.config import Config
from lxml import etree

from clab_tools.node.drivers.base import (
    BaseNodeDriver,
    CommandResult,
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
    ConnectionParams,
)
from clab_tools.node.drivers.registry import register_driver

# Set environment variable to suppress warnings
os.environ["PYTHONWARNINGS"] = "ignore::RuntimeWarning:jnpr.junos.device"

# More aggressive warning suppression
warnings.simplefilter("ignore", RuntimeWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*CLI command is for debug use only.*")
warnings.filterwarnings("ignore", module="jnpr.junos.device")

logger = logging.getLogger(__name__)


def _configure_pyez_logging():
    """Configure PyEZ and related library logging to reduce verbose output."""
    # Suppress ncclient NETCONF XML logging (main source of verbose output)
    logging.getLogger("ncclient.transport.ssh").setLevel(logging.WARNING)
    logging.getLogger("ncclient.transport.session").setLevel(logging.WARNING)
    logging.getLogger("ncclient.operations.rpc").setLevel(logging.WARNING)
    logging.getLogger("ncclient.transport.parser").setLevel(logging.WARNING)

    # Suppress PyEZ device logging
    logging.getLogger("jnpr.junos.device").setLevel(logging.WARNING)
    logging.getLogger("jnpr.junos.rpcmeta").setLevel(logging.WARNING)

    # Suppress paramiko SSH logging
    logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
    logging.getLogger("paramiko.transport.sftp").setLevel(logging.WARNING)


# Configure logging when module is imported
_configure_pyez_logging()


@register_driver("JuniperPyEZDriver")
class JuniperPyEZDriver(BaseNodeDriver):
    """Juniper driver using PyEZ library."""

    def __init__(self, connection_params: ConnectionParams):
        """Initialize Juniper PyEZ driver.

        Args:
            connection_params: Connection parameters
        """
        super().__init__(connection_params)
        self.device = None
        self.config = None

    def connect(self) -> None:
        """Establish connection to Juniper device."""
        if self._connected:
            return

        try:
            # Build PyEZ connection parameters
            device_params = {
                "host": self.connection_params.host,
                "user": self.connection_params.username,
                "port": self.connection_params.port,
                "timeout": self.connection_params.timeout,
                "auto_probe": True,
                "gather_facts": False,
            }

            # Add authentication
            if self.connection_params.password:
                device_params["password"] = self.connection_params.password
            elif self.connection_params.private_key_file:
                device_params["ssh_private_key_file"] = (
                    self.connection_params.private_key_file
                )

            # Create and open device connection
            self.device = Device(**device_params)
            self.device.open()

            # Bind config utility
            self.config = Config(self.device)

            self._connected = True
            logger.debug(f"Connected to {self.connection_params.host}")

        except ConnectError as e:
            raise ConnectionError(f"Failed to connect: {e}")

    def disconnect(self) -> None:
        """Close connection to Juniper device."""
        if self.device and self._connected:
            try:
                self.device.close()
                logger.debug(f"Disconnected from {self.connection_params.host}")
            except Exception as e:
                logger.debug(f"Error during disconnect: {e}")
            finally:
                self._connected = False
                self.device = None
                self.config = None

    def is_connected(self) -> bool:
        """Check if connected to device."""
        return self._connected and self.device is not None

    def execute_command(
        self, command: str, timeout: Optional[int] = None
    ) -> CommandResult:
        """Execute command on Juniper device.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            CommandResult with output
        """
        # Additional warning suppression for this method
        warnings.filterwarnings(
            "ignore", category=RuntimeWarning, module="jnpr.junos.device"
        )

        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        start_time = time.time()

        try:
            # Handle different command types
            if command.startswith("show"):
                # Use CLI for show commands (PyEZ cli() doesn't accept timeout)
                # Note: timeout parameter is not used by PyEZ cli() method
                # Temporarily redirect stderr to suppress PyEZ warning
                stderr_buffer = io.StringIO()
                with redirect_stderr(stderr_buffer):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        output = self.device.cli(command)
            else:
                # Try RPC for other commands
                output = self._execute_rpc_command(command)

            duration = time.time() - start_time

            return CommandResult(
                node_name=self.connection_params.host,
                command=command,
                output=output.strip() if output else "",
                exit_code=0,
                duration=duration,
            )

        except RpcError as e:
            duration = time.time() - start_time
            return CommandResult(
                node_name=self.connection_params.host,
                command=command,
                output="",
                error=str(e),
                exit_code=1,
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(
                node_name=self.connection_params.host,
                command=command,
                output="",
                error=f"Command failed: {e}",
                exit_code=1,
                duration=duration,
            )

    def execute_commands(
        self, commands: List[str], timeout: Optional[int] = None
    ) -> List[CommandResult]:
        """Execute multiple commands on device.

        Args:
            commands: List of commands
            timeout: Command timeout

        Returns:
            List of CommandResult objects
        """
        results = []
        for command in commands:
            result = self.execute_command(command, timeout)
            results.append(result)
        return results

    def load_config(
        self,
        config_content: str,
        format: ConfigFormat = ConfigFormat.TEXT,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        commit_comment: Optional[str] = None,
    ) -> ConfigResult:
        """Load configuration to device.

        Args:
            config_content: Configuration content
            format: Configuration format
            method: Load method
            commit_comment: Commit comment

        Returns:
            ConfigResult with status
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            # Lock configuration
            self.config.lock()

            # Map format to PyEZ format
            pyez_format = self._map_config_format(format)

            # Load configuration
            if method == ConfigLoadMethod.MERGE:
                self.config.load(config_content, format=pyez_format, merge=True)
            elif method == ConfigLoadMethod.OVERRIDE:
                self.config.load(config_content, format=pyez_format, overwrite=True)
            elif method == ConfigLoadMethod.REPLACE:
                self.config.load(config_content, format=pyez_format, replace=True)

            # Get diff
            diff = self.config.diff()

            if diff is None:
                # No changes
                self.config.unlock()
                return ConfigResult(
                    node_name=self.connection_params.host,
                    success=True,
                    message="No configuration changes detected",
                    diff=None,
                )

            # Commit configuration
            self.config.commit(comment=commit_comment)
            self.config.unlock()

            return ConfigResult(
                node_name=self.connection_params.host,
                success=True,
                message="Configuration loaded and committed successfully",
                diff=diff,
            )

        except ConfigLoadError as e:
            self.config.unlock()
            return ConfigResult(
                node_name=self.connection_params.host,
                success=False,
                message="Configuration load failed",
                error=str(e),
            )
        except CommitError as e:
            self.config.unlock()
            return ConfigResult(
                node_name=self.connection_params.host,
                success=False,
                message="Configuration commit failed",
                error=str(e),
            )
        except Exception as e:
            try:
                self.config.unlock()
            except Exception:
                pass
            return ConfigResult(
                node_name=self.connection_params.host,
                success=False,
                message="Configuration operation failed",
                error=str(e),
            )

    def load_config_from_file(
        self,
        device_file_path: str,
        format: ConfigFormat = ConfigFormat.TEXT,
        method: ConfigLoadMethod = ConfigLoadMethod.MERGE,
        commit_comment: Optional[str] = None,
    ) -> ConfigResult:
        """Load configuration from device file.

        Args:
            device_file_path: Path on device (file on the remote Junos device)
            format: Configuration format (text, set, xml, json)
            method: Load method
            commit_comment: Commit comment

        Returns:
            ConfigResult with status
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            # Lock configuration
            self.config.lock()

            # Map format to PyEZ format string
            pyez_format = self._map_config_format(format)

            # Load from device file using url= parameter with explicit format
            # PyEZ's path= parameter expects a local file, but url= can reference
            # files on the device using the format: /path/to/file (without file:// prefix)
            # PyEZ will interpret paths starting with / as device-local files
            # We must specify format= to override PyEZ's extension-based detection
            if method == ConfigLoadMethod.MERGE:
                self.config.load(url=device_file_path, format=pyez_format, merge=True)
            elif method == ConfigLoadMethod.OVERRIDE:
                self.config.load(url=device_file_path, format=pyez_format, overwrite=True)
            elif method == ConfigLoadMethod.REPLACE:
                self.config.load(url=device_file_path, format=pyez_format, replace=True)

            # Get diff
            diff = self.config.diff()

            if diff is None:
                self.config.unlock()
                return ConfigResult(
                    node_name=self.connection_params.host,
                    success=True,
                    message="No configuration changes detected",
                    diff=None,
                )

            # Commit
            self.config.commit(comment=commit_comment)
            self.config.unlock()

            return ConfigResult(
                node_name=self.connection_params.host,
                success=True,
                message=f"Configuration loaded from {device_file_path} and committed",
                diff=diff,
            )

        except Exception as e:
            try:
                self.config.unlock()
            except Exception:
                pass
            return ConfigResult(
                node_name=self.connection_params.host,
                success=False,
                message="Configuration operation failed",
                error=str(e),
            )

    def validate_config(
        self, config_content: str, format: ConfigFormat = ConfigFormat.TEXT
    ) -> Tuple[bool, Optional[str]]:
        """Validate configuration.

        Args:
            config_content: Configuration to validate
            format: Configuration format

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            self.config.lock()

            # Load config without committing
            pyez_format = self._map_config_format(format)
            self.config.load(config_content, format=pyez_format, merge=True)

            # Check if valid
            self.config.commit_check()

            # Rollback and unlock
            self.config.rollback()
            self.config.unlock()

            return (True, None)

        except Exception as e:
            try:
                self.config.rollback()
                self.config.unlock()
            except Exception:
                pass
            return (False, str(e))

    def get_config_diff(self) -> Optional[str]:
        """Get pending configuration diff.

        Returns:
            Diff or None
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            return self.config.diff()
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return None

    def commit_config(
        self, comment: Optional[str] = None, confirmed: bool = False, timeout: int = 0
    ) -> ConfigResult:
        """Commit configuration.

        Args:
            comment: Commit comment
            confirmed: Use confirmed commit
            timeout: Confirmed timeout

        Returns:
            ConfigResult
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            if confirmed and timeout > 0:
                self.config.commit(comment=comment, confirm=True, timeout=timeout)
            else:
                self.config.commit(comment=comment)

            return ConfigResult(
                node_name=self.connection_params.host,
                success=True,
                message="Configuration committed successfully",
            )

        except CommitError as e:
            return ConfigResult(
                node_name=self.connection_params.host,
                success=False,
                message="Commit failed",
                error=str(e),
            )

    def rollback_config(self, rollback_id: Optional[int] = None) -> ConfigResult:
        """Rollback configuration.

        Args:
            rollback_id: Rollback ID or None

        Returns:
            ConfigResult
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            if rollback_id is not None:
                self.config.rollback(rollback_id)
            else:
                self.config.rollback()

            return ConfigResult(
                node_name=self.connection_params.host,
                success=True,
                message="Configuration rolled back successfully",
            )

        except Exception as e:
            return ConfigResult(
                node_name=self.connection_params.host,
                success=False,
                message="Rollback failed",
                error=str(e),
            )

    def get_facts(self) -> Dict[str, Any]:
        """Get device facts.

        Returns:
            Dictionary of facts
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to device")

        try:
            facts = self.device.facts
            return {
                "hostname": facts.get("hostname"),
                "model": facts.get("model"),
                "version": facts.get("version"),
                "serial_number": facts.get("serialnumber"),
                "uptime": facts.get("RE0", {}).get("up_time"),
                "vendor": "Juniper",
            }
        except Exception as e:
            logger.error(f"Failed to get facts: {e}")
            return {}

    def _map_config_format(self, format: ConfigFormat) -> str:
        """Map ConfigFormat to PyEZ format string.

        Args:
            format: ConfigFormat enum

        Returns:
            PyEZ format string
        """
        mapping = {
            ConfigFormat.TEXT: "text",
            ConfigFormat.SET: "set",
            ConfigFormat.XML: "xml",
            ConfigFormat.JSON: "json",
        }
        return mapping.get(format, "text")

    def _execute_rpc_command(self, command: str) -> str:
        """Execute RPC command.

        Args:
            command: RPC command

        Returns:
            Command output
        """
        # This is a simplified implementation
        # In practice, you'd parse the command to determine the RPC
        try:
            result = self.device.rpc.cli(command)
            if isinstance(result, etree._Element):
                return etree.tostring(result, pretty_print=True).decode()
            return str(result)
        except Exception as e:
            raise RpcError(f"RPC command failed: {e}")

    @classmethod
    def get_supported_vendors(cls) -> List[str]:
        """Get supported vendors.

        Returns:
            List of vendor names
        """
        return ["juniper", "junos"]

    @classmethod
    def get_supported_device_types(cls) -> List[str]:
        """Get supported device types.

        Returns:
            List of device types
        """
        return [
            "juniper_vjunosrouter",
            "juniper_vjunosswitch",
            "juniper_vjunosevolved",
            "juniper_vmx",
            "juniper_vsrx",
            "juniper_vqfx",
            "juniper_vjunos",
        ]
