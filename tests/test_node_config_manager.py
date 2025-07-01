"""Tests for node configuration manager."""

from concurrent.futures import Future
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from clab_tools.db.models import Node
from clab_tools.node.config_manager import ConfigManager
from clab_tools.node.drivers.base import (
    ConfigFormat,
    ConfigLoadMethod,
    ConfigResult,
)


class TestConfigManager:
    """Test the ConfigManager class."""

    @pytest.fixture
    def mock_nodes(self):
        """Create mock nodes for testing."""
        nodes = []
        for i in range(3):
            node = Mock(spec=Node)
            node.name = f"router{i+1}"
            node.mgmt_ip = f"192.168.1.{i+10}"
            node.kind = "juniper_vjunosrouter"
            node.vendor = "juniper"
            node.username = f"user{i+1}"
            node.password = f"pass{i+1}"
            node.ssh_port = 22
            nodes.append(node)
        return nodes

    def test_manager_initialization(self):
        """Test initializing ConfigManager."""
        manager = ConfigManager(quiet=False)
        assert manager.quiet is False
        assert manager.console is not None

        manager_quiet = ConfigManager(quiet=True)
        assert manager_quiet.quiet is True

    @patch("clab_tools.node.config_manager.DriverRegistry")
    def test_load_config_from_file_single_node(self, mock_registry, mock_nodes):
        """Test loading config from file on single node."""
        # Setup mock driver
        mock_driver = Mock()
        mock_driver.__enter__ = Mock(return_value=mock_driver)
        mock_driver.__exit__ = Mock(return_value=None)
        mock_driver.load_config.return_value = ConfigResult(
            node_name="router1",
            success=True,
            message="Configuration loaded successfully",
            diff="+ set system host-name router1",
            error=None,
        )
        mock_registry.create_driver.return_value = mock_driver

        # Mock file reading and existence
        with (
            patch("builtins.open", mock_open(read_data="set system host-name router1")),
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text", return_value="set system host-name router1"
            ),
        ):
            manager = ConfigManager(quiet=True)
            results = manager.load_config_from_file(
                [mock_nodes[0]],
                Path("test.conf"),
                format=ConfigFormat.SET,
                method=ConfigLoadMethod.MERGE,
                dry_run=False,
                commit_comment="Test config",
                parallel=False,
            )

        assert len(results) == 1
        assert results[0].node_name == "router1"
        assert results[0].success is True
        assert results[0].message == "Configuration loaded successfully"
        assert results[0].diff == "+ set system host-name router1"

        mock_driver.load_config.assert_called_once_with(
            "set system host-name router1",
            ConfigFormat.SET,
            ConfigLoadMethod.MERGE,
            "Test config",
        )

    @patch("clab_tools.node.config_manager.DriverRegistry")
    def test_load_config_from_file_dry_run(self, mock_registry, mock_nodes):
        """Test dry-run mode for config loading."""
        # Setup mock driver
        mock_driver = Mock()
        mock_driver.__enter__ = Mock(return_value=mock_driver)
        mock_driver.__exit__ = Mock(return_value=None)
        mock_driver.validate_config.return_value = (True, None)
        mock_driver.load_config.return_value = ConfigResult(
            node_name="router1",
            success=True,
            message="Configuration validated",
            diff="+ set system host-name router1",
            error=None,
        )
        mock_driver.get_config_diff.return_value = "+ set system host-name router1"
        mock_registry.create_driver.return_value = mock_driver

        with (
            patch("builtins.open", mock_open(read_data="set system host-name router1")),
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text", return_value="set system host-name router1"
            ),
        ):
            manager = ConfigManager(quiet=True)
            results = manager.load_config_from_file(
                [mock_nodes[0]],
                Path("test.conf"),
                dry_run=True,
            )

        assert len(results) == 1
        assert results[0].success is True
        # In dry-run, validate_config should be called
        mock_driver.validate_config.assert_called_once()

    def test_load_config_from_file_empty_nodes(self):
        """Test loading config with empty node list."""
        manager = ConfigManager(quiet=True)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="set system host-name test"),
        ):
            results = manager.load_config_from_file([], Path("test.conf"))

        assert results == []

    @patch("clab_tools.node.config_manager.DriverRegistry")
    def test_load_config_from_file_not_found(self, mock_registry, mock_nodes):
        """Test handling file not found error."""
        manager = ConfigManager(quiet=True)

        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            manager.load_config_from_file(
                [mock_nodes[0]],
                Path("/nonexistent/file.conf"),
            )

    @patch("clab_tools.node.config_manager.DriverRegistry")
    def test_load_config_from_device_single_node(self, mock_registry, mock_nodes):
        """Test loading config from device file."""
        # Setup mock driver
        mock_driver = Mock()
        mock_driver.__enter__ = Mock(return_value=mock_driver)
        mock_driver.__exit__ = Mock(return_value=None)
        mock_driver.load_config_from_file.return_value = ConfigResult(
            node_name="router1",
            success=True,
            message="Configuration loaded from device",
            diff="+ set system host-name router1",
            error=None,
        )
        mock_registry.create_driver.return_value = mock_driver

        manager = ConfigManager(quiet=True)
        results = manager.load_config_from_device(
            [mock_nodes[0]],
            "/tmp/device.conf",
            method=ConfigLoadMethod.OVERRIDE,
            commit_comment="Device config",
            parallel=False,
        )

        assert len(results) == 1
        assert results[0].success is True
        assert "device" in results[0].message.lower()

        mock_driver.load_config_from_file.assert_called_once_with(
            "/tmp/device.conf",
            ConfigLoadMethod.OVERRIDE,
            "Device config",
        )

    @patch("clab_tools.node.config_manager.DriverRegistry")
    @patch("clab_tools.node.config_manager.ThreadPoolExecutor")
    def test_load_config_parallel(self, mock_executor_class, mock_registry, mock_nodes):
        """Test parallel config loading."""
        # Setup mock executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        # Setup futures for parallel execution
        futures = []
        for i, node in enumerate(mock_nodes):
            future = Future()
            result = ConfigResult(
                node_name=node.name,
                success=True,
                message="Config loaded",
                diff=None,
                error=None,
            )
            future.set_result(result)
            futures.append(future)

        mock_executor.submit.side_effect = futures

        with (
            patch("builtins.open", mock_open(read_data="config")),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="config"),
        ):
            manager = ConfigManager(quiet=True)
            results = manager.load_config_from_file(
                mock_nodes,
                Path("test.conf"),
                parallel=True,
                max_workers=3,
            )

        assert len(results) == 3
        assert all(r.success for r in results)
        mock_executor_class.assert_called_once_with(max_workers=3)
        assert mock_executor.submit.call_count == 3

    # NOTE: rollback_config and get_config_diff methods are not implemented
    # at the ConfigManager level - they exist only on individual drivers.
    # These tests have been removed as they test non-existent functionality.

    @patch("clab_tools.node.config_manager.get_settings")
    @patch("clab_tools.node.config_manager.DriverRegistry")
    def test_load_config_with_settings_fallback(
        self, mock_registry, mock_get_settings, mock_nodes
    ):
        """Test using settings for credential fallback."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.node.default_username = "default_admin"
        mock_settings.node.default_password = "default_pass"
        mock_settings.node.ssh_port = 22
        mock_settings.node.connection_timeout = 30
        mock_get_settings.return_value = mock_settings

        # Create a simple object with only the required attributes
        class TestNode:
            def __init__(self):
                self.name = "router1"
                self.mgmt_ip = "192.168.1.10"
                self.kind = "juniper_vjunosrouter"
                # No username, password, ssh_port, or vendor attributes

        node = TestNode()

        mock_driver = Mock()
        mock_driver.__enter__ = Mock(return_value=mock_driver)
        mock_driver.__exit__ = Mock(return_value=None)
        mock_driver.load_config.return_value = ConfigResult(
            node_name="router1",
            success=True,
            message="Success",
            diff=None,
            error=None,
        )
        mock_registry.create_driver.return_value = mock_driver

        with (
            patch("builtins.open", mock_open(read_data="config")),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="config"),
        ):
            manager = ConfigManager(quiet=True)
            results = manager.load_config_from_file([node], Path("test.conf"))

        assert len(results) == 1
        assert results[0].success is True

        # Verify settings were used
        conn_params = mock_registry.create_driver.call_args[0][0]
        assert conn_params.username == "default_admin"
        assert conn_params.password == "default_pass"
        assert conn_params.port == 22

    @patch("clab_tools.node.config_manager.DriverRegistry")
    def test_load_config_driver_creation_failure(self, mock_registry, mock_nodes):
        """Test handling driver creation failure."""
        mock_registry.create_driver.side_effect = ValueError("No driver found")

        with (
            patch("builtins.open", mock_open(read_data="config")),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="config"),
        ):
            manager = ConfigManager(quiet=True)
            results = manager.load_config_from_file([mock_nodes[0]], Path("test.conf"))

        assert len(results) == 1
        assert results[0].success is False
        assert "No driver found" in results[0].error

    def test_format_results_text(self):
        """Test formatting results as text."""
        results = [
            ConfigResult(
                node_name="router1",
                success=True,
                message="Configuration loaded",
                diff="+ set system host-name router1",
                error=None,
            ),
            ConfigResult(
                node_name="router2",
                success=False,
                message="Configuration failed",
                diff=None,
                error="Syntax error",
            ),
        ]

        manager = ConfigManager(quiet=True)
        output = manager.format_results(results, output_format="text", show_diff=True)

        assert "router1" in output
        assert "Configuration loaded" in output
        assert "+ set system host-name router1" in output
        assert "router2" in output
        assert "Syntax error" in output

    def test_format_results_json(self):
        """Test formatting results as JSON."""
        results = [
            ConfigResult(
                node_name="router1",
                success=True,
                message="Configuration loaded",
                diff="+ set system host-name router1",
                error=None,
            )
        ]

        manager = ConfigManager(quiet=True)
        output = manager.format_results(results, output_format="json")

        import json

        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["node"] == "router1"
        assert data[0]["success"] is True
        assert data[0]["message"] == "Configuration loaded"
        assert data[0]["diff"] == "+ set system host-name router1"

    def test_print_summary(self, capsys):
        """Test printing configuration summary."""
        results = [
            ConfigResult(
                node_name="router1",
                success=True,
                message="Success",
                diff=None,
                error=None,
            ),
            ConfigResult(
                node_name="router2",
                success=False,
                message="Failed",
                diff=None,
                error="Error",
            ),
        ]

        manager = ConfigManager(quiet=False)
        manager.print_summary(results)

        captured = capsys.readouterr()
        assert "Total nodes: 2" in captured.out
        assert "Successful: 1" in captured.out
        assert "Failed: 1" in captured.out
