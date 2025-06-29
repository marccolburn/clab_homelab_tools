"""Tests for Juniper node driver."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from clab_tools.node.drivers.base import (
    CommandResult,
    ConfigFormat,
    ConfigLoadMethod,
    ConnectionParams,
)


class TestJuniperDriver:
    """Test the JuniperPyEZDriver class."""

    @pytest.fixture
    def connection_params(self):
        """Create mock connection parameters."""
        return ConnectionParams(
            host="192.168.1.10",
            username="admin",
            password="secret",
            port=22,
            timeout=30,
            vendor="juniper",
            device_type="juniper_vjunosrouter",
        )

    @pytest.fixture
    def mock_device(self):
        """Create a mock PyEZ Device."""
        with patch("clab_tools.node.drivers.juniper.Device") as MockDevice:
            device = MagicMock()
            MockDevice.return_value = device
            yield device, MockDevice

    @pytest.fixture
    def mock_config(self):
        """Create a mock PyEZ Config."""
        with patch("clab_tools.node.drivers.juniper.Config") as MockConfig:
            config = MagicMock()
            MockConfig.return_value = config
            yield config, MockConfig

    def test_driver_imports(self):
        """Test that driver can be imported successfully."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        assert JuniperPyEZDriver is not None

    def test_driver_initialization(self, connection_params):
        """Test initializing Juniper driver."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        driver = JuniperPyEZDriver(connection_params)
        assert driver.connection_params == connection_params
        assert driver.device is None
        assert driver.config is None
        assert not driver._connected

    @patch("clab_tools.node.drivers.juniper.Config")
    def test_connect_success(self, MockConfig, connection_params, mock_device):
        """Test successful connection."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, MockDevice = mock_device
        config_instance = MockConfig.return_value
        device_instance.open.return_value = None

        driver = JuniperPyEZDriver(connection_params)
        driver.connect()

        MockDevice.assert_called_once_with(
            host="192.168.1.10",
            user="admin",
            password="secret",
            port=22,
            timeout=30,
            auto_probe=True,
            gather_facts=False,
        )
        device_instance.open.assert_called_once()
        MockConfig.assert_called_once_with(device_instance)
        assert driver.device == device_instance
        assert driver.config == config_instance
        assert driver._connected is True

    def test_connect_failure(self, connection_params, mock_device):
        """Test connection failure."""
        from jnpr.junos.exception import ConnectError

        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, MockDevice = mock_device
        device_instance.open.side_effect = ConnectError("Connection failed")

        driver = JuniperPyEZDriver(connection_params)
        with pytest.raises(ConnectionError, match="Failed to connect"):
            driver.connect()

    def test_disconnect(self, connection_params, mock_device):
        """Test disconnecting from device."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver._connected = True
        driver.disconnect()

        device_instance.close.assert_called_once()
        assert driver.device is None
        assert driver.config is None
        assert driver._connected is False

    def test_is_connected(self, connection_params):
        """Test is_connected method."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        driver = JuniperPyEZDriver(connection_params)

        assert not driver.is_connected()

        driver._connected = True
        driver.device = Mock()
        assert driver.is_connected()

    def test_execute_command_success(self, connection_params, mock_device):
        """Test successful command execution."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        device_instance.cli.return_value = "JunOS 20.4R3\nModel: vMX"

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver._connected = True

        result = driver.execute_command("show version", timeout=60)

        assert isinstance(result, CommandResult)
        assert result.node_name == "192.168.1.10"
        assert result.command == "show version"
        assert result.output == "JunOS 20.4R3\nModel: vMX"
        assert result.error is None
        assert result.exit_code == 0

        device_instance.cli.assert_called_once_with("show version")

    def test_execute_command_failure(self, connection_params, mock_device):
        """Test command execution failure."""
        from jnpr.junos.exception import RpcError

        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        device_instance.cli.side_effect = RpcError("Invalid command")

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver._connected = True

        result = driver.execute_command("show invalid")

        assert result.node_name == "192.168.1.10"
        assert result.command == "show invalid"
        assert result.output == ""
        assert "Invalid command" in result.error
        assert result.exit_code == 1

    def test_execute_command_not_connected(self, connection_params):
        """Test executing command when not connected."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        driver = JuniperPyEZDriver(connection_params)

        with pytest.raises(ConnectionError, match="Not connected to device"):
            driver.execute_command("show version")

    def test_load_config_merge_success(
        self, connection_params, mock_device, mock_config
    ):
        """Test successful config load with merge method."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        config_instance, _ = mock_config

        config_instance.diff.return_value = "+ set system host-name router1"
        config_instance.commit.return_value = True

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver.config = config_instance
        driver._connected = True

        result = driver.load_config(
            "set system host-name router1",
            format=ConfigFormat.SET,
            method=ConfigLoadMethod.MERGE,
            commit_comment="Test config",
        )

        assert result.success is True
        assert result.node_name == "192.168.1.10"
        assert "successfully" in result.message

        config_instance.lock.assert_called_once()
        config_instance.load.assert_called_once_with(
            "set system host-name router1", format="set", merge=True
        )
        config_instance.commit.assert_called_once_with(comment="Test config")
        config_instance.unlock.assert_called_once()

    def test_load_config_no_changes(self, connection_params, mock_device, mock_config):
        """Test config load with no changes."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        config_instance, _ = mock_config

        config_instance.diff.return_value = None  # No changes

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver.config = config_instance
        driver._connected = True

        result = driver.load_config("set system host-name router1")

        assert result.success is True
        assert "No configuration changes detected" in result.message
        config_instance.commit.assert_not_called()

    def test_validate_config_success(self, connection_params, mock_device, mock_config):
        """Test successful config validation."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        config_instance, _ = mock_config

        config_instance.commit_check.return_value = True

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver.config = config_instance
        driver._connected = True

        is_valid, error = driver.validate_config("set system host-name router1")

        assert is_valid is True
        assert error is None
        config_instance.commit_check.assert_called_once()
        config_instance.rollback.assert_called_once()

    def test_get_config_diff(self, connection_params, mock_device, mock_config):
        """Test getting config diff."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        config_instance, _ = mock_config

        config_instance.diff.return_value = "+ set system host-name router1"

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver.config = config_instance
        driver._connected = True

        diff = driver.get_config_diff()

        assert diff == "+ set system host-name router1"
        config_instance.diff.assert_called_once()

    def test_rollback_config_success(self, connection_params, mock_device, mock_config):
        """Test successful config rollback."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        config_instance, _ = mock_config

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver.config = config_instance
        driver._connected = True

        result = driver.rollback_config()

        assert result.success is True
        assert "rolled back successfully" in result.message
        config_instance.rollback.assert_called_once_with()

    def test_get_facts(self, connection_params, mock_device):
        """Test getting device facts."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, _ = mock_device
        device_instance.facts = {
            "hostname": "router1",
            "model": "vMX",
            "version": "20.4R3",
            "serialnumber": "123456",
            "RE0": {"up_time": "5 days"},
        }

        driver = JuniperPyEZDriver(connection_params)
        driver.device = device_instance
        driver._connected = True

        facts = driver.get_facts()

        assert facts["hostname"] == "router1"
        assert facts["model"] == "vMX"
        assert facts["version"] == "20.4R3"
        assert facts["serial_number"] == "123456"
        assert facts["uptime"] == "5 days"
        assert facts["vendor"] == "Juniper"

    def test_context_manager(self, connection_params, mock_device, mock_config):
        """Test using driver as context manager."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver

        device_instance, MockDevice = mock_device
        config_instance, MockConfig = mock_config

        with JuniperPyEZDriver(connection_params) as driver:
            assert driver._connected is True
            device_instance.open.assert_called_once()

        device_instance.close.assert_called_once()

    def test_driver_registration(self):
        """Test that JuniperPyEZDriver is registered properly."""
        from clab_tools.node.drivers.juniper import JuniperPyEZDriver
        from clab_tools.node.drivers.registry import DriverRegistry

        # The driver should be registered when the module is imported
        assert "JuniperPyEZDriver" in DriverRegistry.list_drivers()

        # Check vendor support
        for vendor in ["juniper", "junos"]:
            assert vendor in DriverRegistry.list_supported_vendors()
            assert DriverRegistry.get_driver_by_vendor(vendor) == JuniperPyEZDriver

        # Check device type support
        device_types = [
            "juniper_vjunosrouter",
            "juniper_vjunosswitch",
            "juniper_vjunosevolved",
            "juniper_vmx",
            "juniper_vsrx",
            "juniper_vqfx",
            "juniper_vjunos",
        ]
        for device_type in device_types:
            assert device_type in DriverRegistry.list_supported_device_types()
            assert (
                DriverRegistry.get_driver_by_device_type(device_type)
                == JuniperPyEZDriver
            )
