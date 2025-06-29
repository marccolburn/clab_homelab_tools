"""Tests for base node driver interface and data classes."""

import pytest

from clab_tools.node.drivers.base import (
    BaseNodeDriver,
    CommandResult,
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
    ConnectionParams,
)


class TestCommandResult:
    """Test the CommandResult data class."""

    def test_command_result_creation(self):
        """Test creating a CommandResult."""
        result = CommandResult(
            node_name="router1",
            command="show version",
            output="JunOS 20.4R3",
            error=None,
            exit_code=0,
            duration=1.5,
        )
        assert result.node_name == "router1"
        assert result.command == "show version"
        assert result.output == "JunOS 20.4R3"
        assert result.error is None
        assert result.exit_code == 0
        assert result.duration == 1.5

    def test_command_result_with_error(self):
        """Test creating a CommandResult with error."""
        result = CommandResult(
            node_name="router1",
            command="show invalid",
            output="",
            error="Invalid command",
            exit_code=1,
            duration=0.5,
        )
        assert result.node_name == "router1"
        assert result.command == "show invalid"
        assert result.output == ""
        assert result.error == "Invalid command"
        assert result.exit_code == 1
        assert result.duration == 0.5


class TestConfigResult:
    """Test the ConfigResult data class."""

    def test_config_result_creation(self):
        """Test creating a ConfigResult."""
        result = ConfigResult(
            node_name="router1",
            success=True,
            message="Configuration loaded successfully",
            diff="+ set system host-name router1",
            error=None,
            rollback_id=None,
        )
        assert result.node_name == "router1"
        assert result.success is True
        assert result.message == "Configuration loaded successfully"
        assert result.diff == "+ set system host-name router1"
        assert result.error is None
        assert result.rollback_id is None

    def test_config_result_with_error(self):
        """Test creating a ConfigResult with error."""
        result = ConfigResult(
            node_name="router1",
            success=False,
            message="Configuration failed",
            diff=None,
            error="Syntax error at line 10",
            rollback_id=None,
        )
        assert result.node_name == "router1"
        assert result.success is False
        assert result.message == "Configuration failed"
        assert result.diff is None
        assert result.error == "Syntax error at line 10"


class TestConnectionParams:
    """Test the ConnectionParams data class."""

    def test_connection_params_creation(self):
        """Test creating ConnectionParams."""
        params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
            password="secret",
            port=22,
            timeout=30,
            private_key_file=None,
            device_type="juniper_vjunosrouter",
            vendor="juniper",
        )
        assert params.host == "192.168.1.10"
        assert params.username == "admin"
        assert params.password == "secret"
        assert params.port == 22
        assert params.timeout == 30
        assert params.private_key_file is None
        assert params.device_type == "juniper_vjunosrouter"
        assert params.vendor == "juniper"

    def test_connection_params_defaults(self):
        """Test ConnectionParams with default values."""
        params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
        )
        assert params.host == "192.168.1.10"
        assert params.username == "admin"
        assert params.password is None
        assert params.port == 22
        assert params.timeout == 30
        assert params.private_key_file is None
        assert params.device_type is None
        assert params.vendor is None


class TestConfigFormat:
    """Test the ConfigFormat enum."""

    def test_config_format_values(self):
        """Test ConfigFormat enum values."""
        assert ConfigFormat.TEXT.value == "text"
        assert ConfigFormat.SET.value == "set"
        assert ConfigFormat.XML.value == "xml"
        assert ConfigFormat.JSON.value == "json"


class TestConfigLoadMethod:
    """Test the ConfigLoadMethod enum."""

    def test_load_method_values(self):
        """Test ConfigLoadMethod enum values."""
        assert ConfigLoadMethod.MERGE.value == "merge"
        assert ConfigLoadMethod.OVERRIDE.value == "override"
        assert ConfigLoadMethod.REPLACE.value == "replace"


class ConcreteNodeDriver(BaseNodeDriver):
    """Concrete implementation for testing abstract base class."""

    def connect(self):
        """Mock connect implementation."""
        self._connected = True

    def disconnect(self):
        """Mock disconnect implementation."""
        self._connected = False

    def is_connected(self) -> bool:
        """Mock is_connected implementation."""
        return self._connected

    def execute_command(self, command: str, timeout=None):
        """Mock execute_command implementation."""
        return CommandResult(
            node_name=self.connection_params.host,
            command=command,
            output="Mock output",
            error=None,
            exit_code=0,
            duration=1.0,
        )

    def execute_commands(self, commands, timeout=None):
        """Mock execute_commands implementation."""
        return [self.execute_command(cmd, timeout) for cmd in commands]

    def load_config(
        self,
        config_content,
        format=ConfigFormat.TEXT,
        method=ConfigLoadMethod.MERGE,
        commit_comment=None,
    ):
        """Mock load_config implementation."""
        return ConfigResult(
            node_name=self.connection_params.host,
            success=True,
            message="Mock config loaded",
            diff="+ mock diff",
            error=None,
        )

    def load_config_from_file(
        self, device_file_path, method=ConfigLoadMethod.MERGE, commit_comment=None
    ):
        """Mock load_config_from_file implementation."""
        return ConfigResult(
            node_name=self.connection_params.host,
            success=True,
            message="Mock config loaded from file",
            diff="+ mock diff",
            error=None,
        )

    def validate_config(self, config_content, format=ConfigFormat.TEXT):
        """Mock validate_config implementation."""
        return (True, None)

    def get_config_diff(self):
        """Mock get_config_diff implementation."""
        return "+ mock diff"

    def commit_config(self, comment=None, confirmed=False, timeout=0):
        """Mock commit_config implementation."""
        return ConfigResult(
            node_name=self.connection_params.host,
            success=True,
            message="Mock commit success",
            diff=None,
            error=None,
        )

    def rollback_config(self, rollback_id=None):
        """Mock rollback_config implementation."""
        return ConfigResult(
            node_name=self.connection_params.host,
            success=True,
            message="Mock rollback success",
            diff=None,
            error=None,
        )

    def get_facts(self):
        """Mock get_facts implementation."""
        return {"hostname": "mock-router", "vendor": "mock"}

    @classmethod
    def get_supported_vendors(cls):
        """Mock get_supported_vendors implementation."""
        return ["mock"]

    @classmethod
    def get_supported_device_types(cls):
        """Mock get_supported_device_types implementation."""
        return ["mock_device"]


class TestBaseNodeDriver:
    """Test the BaseNodeDriver abstract base class."""

    @pytest.fixture
    def connection_params(self):
        """Create mock connection parameters."""
        return ConnectionParams(
            host="192.168.1.10",
            username="admin",
            password="secret",
            device_type="mock_device",
            vendor="mock",
        )

    def test_base_driver_initialization(self, connection_params):
        """Test initializing a driver with connection params."""
        driver = ConcreteNodeDriver(connection_params)
        assert driver.connection_params == connection_params
        assert driver.connection_params.host == "192.168.1.10"
        assert driver._connected is False

    def test_base_driver_context_manager(self, connection_params):
        """Test using driver as context manager."""
        driver = ConcreteNodeDriver(connection_params)
        assert not driver.is_connected()

        with driver:
            assert driver.is_connected()

        assert not driver.is_connected()

    def test_base_driver_execute_command(self, connection_params):
        """Test execute_command method."""
        driver = ConcreteNodeDriver(connection_params)
        result = driver.execute_command("show version", timeout=60)

        assert isinstance(result, CommandResult)
        assert result.node_name == "192.168.1.10"
        assert result.command == "show version"
        assert result.exit_code == 0

    def test_base_driver_load_config(self, connection_params):
        """Test load_config method."""
        driver = ConcreteNodeDriver(connection_params)
        result = driver.load_config(
            "set system host-name router1",
            format=ConfigFormat.SET,
            method=ConfigLoadMethod.MERGE,
            commit_comment="Test config",
        )

        assert isinstance(result, ConfigResult)
        assert result.node_name == "192.168.1.10"
        assert result.success is True

    def test_base_driver_abstract_methods(self, connection_params):
        """Test that abstract methods must be implemented."""
        # BaseNodeDriver cannot be instantiated directly
        with pytest.raises(TypeError):
            BaseNodeDriver(connection_params)
