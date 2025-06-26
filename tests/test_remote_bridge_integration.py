"""
Tests for remote bridge management functionality.
"""

from unittest.mock import Mock, patch

import pytest

from clab_tools.bridges.manager import BridgeManager
from clab_tools.commands.bridge_commands import (
    create_bridges_command,
    delete_bridges_command,
)
from clab_tools.config.settings import RemoteHostSettings
from clab_tools.remote import RemoteHostManager


class TestRemoteBridgeManager:
    """Test bridge manager with remote host integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.get_all_nodes.return_value = [
            ("br-switch1", "bridge", None),
            ("router1", "linux", "192.168.1.1"),
            ("br-switch2", "bridge", None),
        ]

        self.remote_settings = RemoteHostSettings(
            enabled=True, host="192.168.1.100", username="testuser", password="testpass"
        )

    def test_local_bridge_manager(self):
        """Test bridge manager without remote host."""
        manager = BridgeManager(self.mock_db)

        assert manager.db == self.mock_db
        assert manager.remote_manager is None

    def test_remote_bridge_manager(self):
        """Test bridge manager with remote host."""
        remote_manager = Mock(spec=RemoteHostManager)
        manager = BridgeManager(self.mock_db, remote_manager)

        assert manager.db == self.mock_db
        assert manager.remote_manager == remote_manager

    def test_get_bridge_list_from_db(self):
        """Test getting bridge list from database."""
        manager = BridgeManager(self.mock_db)
        bridges = manager.get_bridge_list_from_db()

        assert bridges == ["br-switch1", "br-switch2"]

    @patch("subprocess.run")
    def test_local_check_bridge_exists(self, mock_subprocess):
        """Test checking bridge existence locally."""
        mock_subprocess.return_value.returncode = 0

        manager = BridgeManager(self.mock_db)
        exists = manager.check_bridge_exists("br-switch1")

        assert exists
        mock_subprocess.assert_called_with(
            ["ip", "link", "show", "br-switch1"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_remote_check_bridge_exists(self):
        """Test checking bridge existence remotely."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (0, "", "")

        manager = BridgeManager(self.mock_db, remote_manager)
        exists = manager.check_bridge_exists("br-switch1")

        assert exists
        remote_manager.execute_command.assert_called_with(
            "ip link show br-switch1", check=False
        )

    def test_remote_check_bridge_not_exists(self):
        """Test checking non-existent bridge remotely."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (1, "", "Bridge not found")

        manager = BridgeManager(self.mock_db, remote_manager)
        exists = manager.check_bridge_exists("br-nonexistent")

        assert not exists

    @patch("subprocess.run")
    def test_local_create_bridge_success(self, mock_subprocess):
        """Test successful local bridge creation."""
        mock_subprocess.return_value.returncode = 0

        manager = BridgeManager(self.mock_db)

        # Mock bridge doesn't exist
        with patch.object(manager, "check_bridge_exists", return_value=False):
            success, message = manager.create_bridge("br-test")

        assert success
        assert "Successfully created" in message
        assert "local system" in message
        assert "VLAN-capable" in message

    def test_remote_create_bridge_success(self):
        """Test successful remote bridge creation."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (0, "", "")
        # Add settings mock
        mock_settings = Mock()
        mock_settings.use_sudo = True
        remote_manager.settings = mock_settings

        manager = BridgeManager(self.mock_db, remote_manager)

        # Mock bridge doesn't exist
        with patch.object(manager, "check_bridge_exists", return_value=False):
            success, message = manager.create_bridge("br-test")

        assert success
        assert "Successfully created" in message
        assert "remote host" in message
        assert "VLAN-capable" in message

    def test_remote_create_bridge_dry_run(self):
        """Test remote bridge creation in dry run mode."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        # Add settings mock
        mock_settings = Mock()
        mock_settings.use_sudo = True
        remote_manager.settings = mock_settings

        manager = BridgeManager(self.mock_db, remote_manager)

        # Mock bridge doesn't exist
        with patch.object(manager, "check_bridge_exists", return_value=False):
            success, message = manager.create_bridge("br-test", dry_run=True)

        assert success
        assert "Dry run" in message
        assert "remote host" in message
        # Should not call execute_command in dry run
        remote_manager.execute_command.assert_not_called()

    def test_remote_delete_bridge_success(self):
        """Test successful remote bridge deletion."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (0, "", "")
        # Add settings mock
        mock_settings = Mock()
        mock_settings.use_sudo = True
        remote_manager.settings = mock_settings

        manager = BridgeManager(self.mock_db, remote_manager)

        # Mock bridge exists
        with patch.object(manager, "check_bridge_exists", return_value=True):
            success, message = manager.delete_bridge("br-test")

        assert success
        assert "Successfully deleted" in message
        assert "remote host" in message

    def test_create_all_bridges_with_remote(self):
        """Test creating all bridges with remote manager."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (0, "", "")

        manager = BridgeManager(self.mock_db, remote_manager)

        # Mock some bridges missing
        with patch.object(manager, "get_missing_bridges", return_value=["br-switch1"]):
            with patch.object(manager, "create_bridge", return_value=(True, "Created")):
                success, message = manager.create_all_bridges(dry_run=False, force=True)

        assert success
        assert "Created 1/1 bridges" in message


class TestRemoteBridgeCommands:
    """Test bridge commands with remote integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.get_all_nodes.return_value = [
            ("br-switch1", "bridge", None),
            ("router1", "linux", "192.168.1.1"),
        ]

    @patch("clab_tools.commands.bridge_commands.get_remote_host_manager")
    @patch("clab_tools.commands.bridge_commands.BridgeManager")
    def test_create_bridges_command_local(
        self, mock_bridge_manager_class, mock_get_remote
    ):
        """Test create bridges command running locally."""
        mock_get_remote.return_value = None
        mock_manager = Mock()
        mock_bridge_manager_class.return_value = mock_manager
        mock_manager.get_bridge_list_from_db.return_value = ["br-switch1"]
        mock_manager.check_bridge_exists.return_value = False
        mock_manager.get_missing_bridges.return_value = ["br-switch1"]
        mock_manager.create_all_bridges.return_value = (True, "Created 1/1 bridges")

        create_bridges_command(self.mock_db, dry_run=False, force=True)

        # Verify local manager was created
        mock_bridge_manager_class.assert_called_with(self.mock_db)
        mock_manager.create_all_bridges.assert_called_with(dry_run=False, force=True)

    @patch("clab_tools.commands.bridge_commands.get_remote_host_manager")
    @patch("clab_tools.commands.bridge_commands.BridgeManager")
    def test_create_bridges_command_remote(
        self, mock_bridge_manager_class, mock_get_remote
    ):
        """Test create bridges command running remotely."""
        mock_remote_manager = Mock()
        mock_remote_manager.__enter__ = Mock(return_value=mock_remote_manager)
        mock_remote_manager.__exit__ = Mock(return_value=None)
        mock_get_remote.return_value = mock_remote_manager

        mock_manager = Mock()
        mock_bridge_manager_class.return_value = mock_manager
        mock_manager.get_bridge_list_from_db.return_value = ["br-switch1"]
        mock_manager.check_bridge_exists.return_value = False
        mock_manager.get_missing_bridges.return_value = ["br-switch1"]
        mock_manager.create_all_bridges.return_value = (True, "Created 1/1 bridges")

        create_bridges_command(self.mock_db, dry_run=False, force=True)

        # Verify remote manager was used
        mock_bridge_manager_class.assert_called_with(self.mock_db, mock_remote_manager)
        mock_remote_manager.__enter__.assert_called_once()
        mock_remote_manager.__exit__.assert_called_once()

    @patch("clab_tools.commands.bridge_commands.get_remote_host_manager")
    @patch("clab_tools.commands.bridge_commands.BridgeManager")
    def test_delete_bridges_command_remote(
        self, mock_bridge_manager_class, mock_get_remote
    ):
        """Test delete bridges command running remotely."""
        mock_remote_manager = Mock()
        mock_remote_manager.__enter__ = Mock(return_value=mock_remote_manager)
        mock_remote_manager.__exit__ = Mock(return_value=None)
        mock_get_remote.return_value = mock_remote_manager

        mock_manager = Mock()
        mock_bridge_manager_class.return_value = mock_manager
        mock_manager.get_existing_bridges.return_value = ["br-switch1"]
        mock_manager.delete_all_bridges.return_value = (True, "Deleted 1/1 bridges")

        delete_bridges_command(self.mock_db, dry_run=False, force=True)

        # Verify remote manager was used
        mock_bridge_manager_class.assert_called_with(self.mock_db, mock_remote_manager)
        mock_manager.delete_all_bridges.assert_called_with(dry_run=False, force=True)


class TestBridgeManagerExecuteCommand:
    """Test the _execute_command method in BridgeManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()

    @patch("subprocess.run")
    def test_local_execution(self, mock_subprocess):
        """Test local command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        manager = BridgeManager(self.mock_db)
        result = manager._execute_command(["ip", "link", "show"])

        assert result.returncode == 0
        assert result.stdout == "success output"
        mock_subprocess.assert_called_with(
            ["ip", "link", "show"], capture_output=True, text=True, check=True
        )

    def test_remote_execution(self):
        """Test remote command execution."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (0, "success output", "")

        manager = BridgeManager(self.mock_db, remote_manager)
        result = manager._execute_command(["ip", "link", "show"])

        assert result.returncode == 0
        assert result.stdout == "success output"
        remote_manager.execute_command.assert_called_with("ip link show", check=False)

    def test_remote_execution_failure(self):
        """Test remote command execution failure."""
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.is_connected.return_value = True
        remote_manager.execute_command.return_value = (1, "", "command failed")

        manager = BridgeManager(self.mock_db, remote_manager)

        with pytest.raises(Exception) as exc_info:
            manager._execute_command(["ip", "link", "show"], check=True)

        assert hasattr(exc_info.value, "stderr")
        assert exc_info.value.stderr == "command failed"


class TestBridgeManagerSudoCommands:
    """Test sudo command building functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.get_bridge_nodes_by_kind.return_value = []

    def test_build_command_local_always_uses_sudo(self):
        """Test that local commands always use sudo."""
        manager = BridgeManager(self.mock_db)  # No remote manager

        command = manager._build_command(["ip", "link", "show"])
        assert command == ["sudo", "ip", "link", "show"]

    def test_build_command_remote_with_sudo_enabled(self):
        """Test remote commands with sudo enabled."""
        remote_settings = RemoteHostSettings(
            enabled=True,
            host="10.1.1.1",
            username="testuser",
            password="testpass",
            use_sudo=True,
        )

        remote_manager = Mock()
        remote_manager.is_connected.return_value = True
        remote_manager.settings = remote_settings

        manager = BridgeManager(self.mock_db, remote_manager)

        command = manager._build_command(["ip", "link", "show"])
        assert command == ["sudo", "ip", "link", "show"]

    def test_build_command_remote_with_sudo_disabled(self):
        """Test remote commands with sudo disabled (e.g., root user)."""
        remote_settings = RemoteHostSettings(
            enabled=True,
            host="10.1.1.1",
            username="root",
            password="testpass",
            use_sudo=False,
        )

        remote_manager = Mock()
        remote_manager.is_connected.return_value = True
        remote_manager.settings = remote_settings

        manager = BridgeManager(self.mock_db, remote_manager)

        command = manager._build_command(["ip", "link", "show"])
        assert command == ["ip", "link", "show"]

    def test_build_command_remote_not_connected(self):
        """Test that disconnected remote manager falls back to local (with sudo)."""
        remote_manager = Mock()
        remote_manager.is_connected.return_value = False

        manager = BridgeManager(self.mock_db, remote_manager)

        command = manager._build_command(["ip", "link", "show"])
        assert command == ["sudo", "ip", "link", "show"]

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_create_bridge_uses_conditional_sudo(self, mock_subprocess_run):
        """Test that bridge creation uses conditional sudo commands."""
        from clab_tools.config.settings import RemoteHostSettings

        # Mock successful subprocess calls
        mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Test with sudo disabled (root user scenario)
        remote_settings = RemoteHostSettings(
            enabled=True,
            host="10.1.1.1",
            username="root",
            password="testpass",
            use_sudo=False,
        )

        remote_manager = Mock()
        remote_manager.is_connected.return_value = True
        remote_manager.settings = remote_settings
        remote_manager.execute_command.return_value = (0, "", "")

        manager = BridgeManager(self.mock_db, remote_manager)
        manager.check_bridge_exists = Mock(return_value=False)

        success, message = manager.create_bridge("test-bridge", dry_run=False)

        # Verify that remote commands were called without sudo
        expected_calls = [
            "ip link add name test-bridge type bridge vlan_filtering 1",
            "ip link set test-bridge up",
            "bridge vlan add vid 1-4094 dev test-bridge self",
        ]

        assert remote_manager.execute_command.call_count == 3
        for i, expected_cmd in enumerate(expected_calls):
            actual_call = remote_manager.execute_command.call_args_list[i]
            assert actual_call[0][0] == expected_cmd
