"""Tests for node driver registry."""

import pytest

from clab_tools.node.drivers.base import (
    BaseNodeDriver,
    CommandResult,
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
    ConnectionParams,
)
from clab_tools.node.drivers.registry import DriverRegistry, register_driver


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

    @classmethod
    def get_supported_vendors(cls):
        """Get list of supported vendor names."""
        return ["mock"]

    @classmethod
    def get_supported_device_types(cls):
        """Get list of supported device types."""
        return ["mock_device"]

    def get_facts(self):
        """Get device facts/information."""
        return {
            "hostname": self.connection_params.host,
            "vendor": "mock",
            "model": "mock_device",
            "version": "1.0.0",
        }


class TestDriverRegistry:
    """Test the DriverRegistry class."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear the registry before each test."""
        DriverRegistry.clear_registry()
        yield
        DriverRegistry.clear_registry()

    def test_register_driver(self):
        """Test registering a driver."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        assert "MockDriver" in DriverRegistry.list_drivers()
        assert DriverRegistry.get_driver_class("MockDriver") == ConcreteNodeDriver

    def test_register_driver_with_vendor_mappings(self):
        """Test that vendor mappings are registered."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        assert "mock" in DriverRegistry.list_supported_vendors()
        assert DriverRegistry.get_driver_by_vendor("mock") == ConcreteNodeDriver

    def test_register_driver_with_device_type_mappings(self):
        """Test that device type mappings are registered."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        assert "mock_device" in DriverRegistry.list_supported_device_types()
        assert (
            DriverRegistry.get_driver_by_device_type("mock_device")
            == ConcreteNodeDriver
        )

    def test_get_driver_by_vendor_case_insensitive(self):
        """Test vendor lookup is case-insensitive."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        assert DriverRegistry.get_driver_by_vendor("MOCK") == ConcreteNodeDriver
        assert DriverRegistry.get_driver_by_vendor("Mock") == ConcreteNodeDriver
        assert DriverRegistry.get_driver_by_vendor("mock") == ConcreteNodeDriver

    def test_get_driver_by_device_type_case_insensitive(self):
        """Test device type lookup is case-insensitive."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        assert (
            DriverRegistry.get_driver_by_device_type("MOCK_DEVICE")
            == ConcreteNodeDriver
        )
        assert (
            DriverRegistry.get_driver_by_device_type("Mock_Device")
            == ConcreteNodeDriver
        )
        assert (
            DriverRegistry.get_driver_by_device_type("mock_device")
            == ConcreteNodeDriver
        )

    def test_create_driver_by_vendor(self):
        """Test creating driver instance by vendor."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        conn_params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
            vendor="mock",
        )

        driver = DriverRegistry.create_driver(conn_params)
        assert isinstance(driver, ConcreteNodeDriver)
        assert driver.connection_params == conn_params

    def test_create_driver_by_device_type(self):
        """Test creating driver instance by device type."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        conn_params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
            device_type="mock_device",
        )

        driver = DriverRegistry.create_driver(conn_params)
        assert isinstance(driver, ConcreteNodeDriver)
        assert driver.connection_params == conn_params

    def test_create_driver_vendor_takes_precedence(self):
        """Test that vendor takes precedence over device type."""

        # Register two different drivers
        class AnotherDriver(ConcreteNodeDriver):
            @classmethod
            def get_supported_vendors(cls):
                return ["another"]

            @classmethod
            def get_supported_device_types(cls):
                return ["mock_device"]  # Same device type as ConcreteNodeDriver

        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")
        DriverRegistry.register_driver(AnotherDriver, "AnotherDriver")

        # Connection params with both vendor and device_type
        conn_params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
            vendor="mock",  # Should use MockDriver
            device_type="mock_device",  # Could match either driver
        )

        driver = DriverRegistry.create_driver(conn_params)
        assert isinstance(driver, ConcreteNodeDriver)  # Vendor match wins

    def test_create_driver_no_match(self):
        """Test creating driver with no matching vendor or device type."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        conn_params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
            vendor="unknown",
            device_type="unknown_device",
        )

        with pytest.raises(ValueError, match="No driver found"):
            DriverRegistry.create_driver(conn_params)

    def test_create_driver_no_vendor_or_device_type(self):
        """Test creating driver with neither vendor nor device type."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        conn_params = ConnectionParams(
            host="192.168.1.10",
            username="admin",
        )

        with pytest.raises(ValueError, match="No driver found"):
            DriverRegistry.create_driver(conn_params)

    def test_list_drivers(self):
        """Test listing all registered drivers."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")

        drivers = DriverRegistry.list_drivers()
        assert len(drivers) == 1
        assert "MockDriver" in drivers

    def test_clear_registry(self):
        """Test clearing the registry."""
        DriverRegistry.register_driver(ConcreteNodeDriver, "MockDriver")
        assert len(DriverRegistry.list_drivers()) == 1

        DriverRegistry.clear_registry()
        assert len(DriverRegistry.list_drivers()) == 0
        assert len(DriverRegistry.list_supported_vendors()) == 0
        assert len(DriverRegistry.list_supported_device_types()) == 0

    def test_register_driver_decorator(self):
        """Test the @register_driver decorator."""

        @register_driver("DecoratedDriver")
        class DecoratedNodeDriver(ConcreteNodeDriver):
            @classmethod
            def get_supported_vendors(cls):
                return ["decorated"]

        assert "DecoratedDriver" in DriverRegistry.list_drivers()
        assert "decorated" in DriverRegistry.list_supported_vendors()
        assert DriverRegistry.get_driver_class("DecoratedDriver") == DecoratedNodeDriver

    def test_register_driver_decorator_no_name(self):
        """Test the @register_driver decorator without explicit name."""

        @register_driver()
        class AutoNamedDriver(ConcreteNodeDriver):
            @classmethod
            def get_supported_vendors(cls):
                return ["autonamed"]

        assert "AutoNamedDriver" in DriverRegistry.list_drivers()
        assert "autonamed" in DriverRegistry.list_supported_vendors()
