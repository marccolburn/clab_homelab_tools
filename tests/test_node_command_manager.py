"""Tests for node command manager."""

from concurrent.futures import Future
from unittest.mock import Mock, patch

import pytest

from clab_tools.db.models import Node
from clab_tools.node.command_manager import CommandManager
from clab_tools.node.drivers.base import CommandResult, ConnectionParams


class TestCommandManager:
    """Test the CommandManager class."""

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
        """Test initializing CommandManager."""
        manager = CommandManager(quiet=False)
        assert manager.quiet is False
        assert manager.console is not None

        manager_quiet = CommandManager(quiet=True)
        assert manager_quiet.quiet is True

    @patch("clab_tools.node.command_manager.DriverRegistry")
    def test_execute_command_single_node(self, mock_registry, mock_nodes):
        """Test command execution on single node."""
        # Setup mock driver with context manager support
        mock_driver = Mock()
        mock_driver.__enter__ = Mock(return_value=mock_driver)
        mock_driver.__exit__ = Mock(return_value=None)
        mock_driver.execute_command.return_value = CommandResult(
            node_name="router1",
            command="show version",
            output="JunOS 20.4R3",
            error=None,
            exit_code=0,
            duration=1.0,
        )
        mock_registry.create_driver.return_value = mock_driver

        manager = CommandManager(quiet=True)
        results = manager.execute_command(
            [mock_nodes[0]], "show version", timeout=30, parallel=False
        )

        assert len(results) == 1
        assert results[0].node_name == "router1"
        assert results[0].command == "show version"
        assert results[0].output == "JunOS 20.4R3"
        assert results[0].exit_code == 0

        # Verify driver was created with proper connection params
        mock_registry.create_driver.assert_called_once()
        conn_params = mock_registry.create_driver.call_args[0][0]
        assert isinstance(conn_params, ConnectionParams)
        assert conn_params.host == "192.168.1.10"
        assert conn_params.username == "user1"
        assert conn_params.vendor == "juniper"

    @patch("clab_tools.node.command_manager.DriverRegistry")
    def test_execute_command_multiple_nodes_sequential(self, mock_registry, mock_nodes):
        """Test sequential execution on multiple nodes."""
        # Setup mock drivers for each node
        mock_drivers = []
        for i, node in enumerate(mock_nodes):
            driver = Mock()
            driver.__enter__ = Mock(return_value=driver)
            driver.__exit__ = Mock(return_value=None)
            driver.execute_command.return_value = CommandResult(
                node_name=node.name,
                command="show interfaces",
                output=f"Output from {node.name}",
                error=None,
                exit_code=0,
                duration=0.5,
            )
            mock_drivers.append(driver)

        mock_registry.create_driver.side_effect = mock_drivers

        manager = CommandManager(quiet=True)
        results = manager.execute_command(mock_nodes, "show interfaces", parallel=False)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.node_name == f"router{i+1}"
            assert result.output == f"Output from router{i+1}"

        # All drivers should have been created
        assert mock_registry.create_driver.call_count == 3

    @patch("clab_tools.node.command_manager.DriverRegistry")
    @patch("clab_tools.node.command_manager.ThreadPoolExecutor")
    def test_execute_command_parallel(
        self, mock_executor_class, mock_registry, mock_nodes
    ):
        """Test parallel execution on multiple nodes."""
        # Setup mock executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        # Setup futures for parallel execution
        futures = []
        for i, node in enumerate(mock_nodes):
            future = Future()
            result = CommandResult(
                node_name=node.name,
                command="show route",
                output=f"Routes from {node.name}",
                error=None,
                exit_code=0,
                duration=0.5,
            )
            future.set_result(result)
            futures.append(future)

        mock_executor.submit.side_effect = futures

        manager = CommandManager(quiet=True)
        results = manager.execute_command(
            mock_nodes, "show route", parallel=True, max_workers=3
        )

        assert len(results) == 3
        assert all(r.exit_code == 0 for r in results)
        mock_executor_class.assert_called_once_with(max_workers=3)
        assert mock_executor.submit.call_count == 3

    def test_execute_command_empty_nodes(self):
        """Test execution with empty node list."""
        manager = CommandManager(quiet=True)
        results = manager.execute_command([], "show version")
        assert results == []

    @patch("clab_tools.node.command_manager.DriverRegistry")
    def test_execute_command_driver_creation_failure(self, mock_registry, mock_nodes):
        """Test handling driver creation failure."""
        mock_registry.create_driver.side_effect = ValueError("No driver found")

        manager = CommandManager(quiet=True)
        results = manager.execute_command([mock_nodes[0]], "show version")

        assert len(results) == 1
        assert results[0].node_name == "router1"
        assert results[0].exit_code == 1
        assert "No driver found" in results[0].error

    @patch("clab_tools.node.command_manager.DriverRegistry")
    def test_execute_command_connection_failure(self, mock_registry, mock_nodes):
        """Test handling connection failure."""
        mock_driver = Mock()
        mock_driver.__enter__ = Mock(side_effect=ConnectionError("Connection refused"))
        mock_driver.__exit__ = Mock(return_value=None)
        mock_registry.create_driver.return_value = mock_driver

        manager = CommandManager(quiet=True)
        results = manager.execute_command([mock_nodes[0]], "show version")

        assert len(results) == 1
        assert results[0].exit_code == 1
        assert "Connection refused" in results[0].error

    @patch("clab_tools.node.command_manager.DriverRegistry")
    def test_execute_command_execution_error(self, mock_registry, mock_nodes):
        """Test handling command execution error."""
        mock_driver = Mock()
        mock_driver.__enter__ = Mock(return_value=mock_driver)
        mock_driver.__exit__ = Mock(return_value=None)
        mock_driver.execute_command.side_effect = Exception("Command failed")
        mock_registry.create_driver.return_value = mock_driver

        manager = CommandManager(quiet=True)
        results = manager.execute_command([mock_nodes[0]], "show version")

        assert len(results) == 1
        assert results[0].exit_code == 1
        assert "Command failed" in results[0].error

    @patch("clab_tools.node.command_manager.get_settings")
    @patch("clab_tools.node.command_manager.DriverRegistry")
    def test_execute_command_with_settings_fallback(
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
        mock_driver.execute_command.return_value = CommandResult(
            node_name="router1",
            command="show version",
            output="Success",
            error=None,
            exit_code=0,
            duration=1.0,
        )
        mock_registry.create_driver.return_value = mock_driver

        manager = CommandManager(quiet=True)
        results = manager.execute_command([node], "show version")

        assert len(results) == 1
        assert results[0].exit_code == 0

        # Verify settings were used
        conn_params = mock_registry.create_driver.call_args[0][0]
        assert conn_params.username == "default_admin"
        assert conn_params.password == "default_pass"
        assert conn_params.port == 22

    def test_format_results_text(self):
        """Test formatting results as text."""
        results = [
            CommandResult(
                node_name="router1",
                command="show version",
                output="JunOS 20.4R3",
                error=None,
                exit_code=0,
                duration=1.0,
            ),
            CommandResult(
                node_name="router2",
                command="show version",
                output="",
                error="Connection timeout",
                exit_code=1,
                duration=0.5,
            ),
        ]

        manager = CommandManager(quiet=True)
        output = manager.format_results(results, output_format="text")

        assert "router1" in output
        assert "JunOS 20.4R3" in output
        assert "router2" in output
        assert "Connection timeout" in output

    def test_format_results_json(self):
        """Test formatting results as JSON."""
        results = [
            CommandResult(
                node_name="router1",
                command="show version",
                output="JunOS 20.4R3",
                error=None,
                exit_code=0,
                duration=1.0,
            )
        ]

        manager = CommandManager(quiet=True)
        output = manager.format_results(results, output_format="json")

        import json

        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["node"] == "router1"
        assert data[0]["command"] == "show version"
        assert data[0]["output"] == "JunOS 20.4R3"
        assert data[0]["exit_code"] == 0

    @patch("clab_tools.node.command_manager.Table")
    def test_format_results_table(self, mock_table):
        """Test formatting results as table."""
        results = [
            CommandResult(
                node_name="router1",
                command="show version",
                output="JunOS 20.4R3",
                error=None,
                exit_code=0,
                duration=1.0,
            )
        ]

        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance

        manager = CommandManager(quiet=True)
        manager.format_results(results, output_format="table")

        # Verify table was created and rows were added
        mock_table.assert_called_once()
        mock_table_instance.add_row.assert_called()

    def test_print_summary(self, capsys):
        """Test printing execution summary."""
        results = [
            CommandResult(
                node_name="router1",
                command="show version",
                output="Success",
                error=None,
                exit_code=0,
                duration=1.0,
            ),
            CommandResult(
                node_name="router2",
                command="show version",
                output="",
                error="Failed",
                exit_code=1,
                duration=0.5,
            ),
        ]

        manager = CommandManager(quiet=False)
        manager.print_summary(results)

        captured = capsys.readouterr()
        assert "Total nodes: 2" in captured.out
        assert "Successful: 1" in captured.out
        assert "Failed: 1" in captured.out
