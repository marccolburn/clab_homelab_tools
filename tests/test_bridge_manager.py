"""Tests for bridge manager functionality."""

from unittest.mock import Mock, call, patch

import pytest

from clab_tools.bridges.manager import BridgeManager


class TestBridgeManager:
    """Test cases for BridgeManager."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_db = Mock()
        return mock_db

    @pytest.fixture
    def bridge_manager(self, mock_db_manager):
        """Create a BridgeManager instance with mock dependencies."""
        return BridgeManager(mock_db_manager)

    def test_get_bridge_list_from_db_with_bridge_nodes(
        self, bridge_manager, mock_db_manager
    ):
        """Test getting bridge list from database nodes."""
        # Mock database returning nodes including bridge types
        mock_db_manager.get_all_nodes.return_value = [
            ("router1", "nokia_srlinux", "172.20.20.10"),
            ("router2", "cisco_xrd", "172.20.20.11"),
            ("br-main", "bridge", "N/A"),
            ("br-access", "bridge", "N/A"),
            ("switch1", "linux_bridge", "172.20.20.20"),
        ]

        bridges = bridge_manager.get_bridge_list_from_db()

        # Should return only bridge nodes, sorted
        assert bridges == ["br-access", "br-main"]
        mock_db_manager.get_all_nodes.assert_called_once()

    def test_get_bridge_list_from_db_no_bridges(self, bridge_manager, mock_db_manager):
        """Test getting bridge list when no bridge nodes exist."""
        # Mock database returning only non-bridge nodes
        mock_db_manager.get_all_nodes.return_value = [
            ("router1", "nokia_srlinux", "172.20.20.10"),
            ("router2", "cisco_xrd", "172.20.20.11"),
        ]

        bridges = bridge_manager.get_bridge_list_from_db()

        # Should return empty list
        assert bridges == []
        mock_db_manager.get_all_nodes.assert_called_once()

    def test_get_bridge_list_from_db_empty_database(
        self, bridge_manager, mock_db_manager
    ):
        """Test getting bridge list from empty database."""
        mock_db_manager.get_all_nodes.return_value = []

        bridges = bridge_manager.get_bridge_list_from_db()

        assert bridges == []
        mock_db_manager.get_all_nodes.assert_called_once()

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_get_existing_bridges(
        self, mock_subprocess, bridge_manager, mock_db_manager
    ):
        """Test getting existing bridges from system."""
        # Mock database returning bridge nodes
        mock_db_manager.get_all_nodes.return_value = [
            ("br-main", "bridge", "N/A"),
            ("br-access", "bridge", "N/A"),
        ]

        # Mock subprocess to show br-main exists but br-access doesn't
        def subprocess_side_effect(cmd, **kwargs):
            if "br-main" in cmd:
                mock_result = Mock()
                mock_result.returncode = 0
                return mock_result
            else:
                mock_result = Mock()
                mock_result.returncode = 1
                return mock_result

        mock_subprocess.side_effect = subprocess_side_effect

        bridges = bridge_manager.get_existing_bridges()

        assert bridges == ["br-main"]

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_get_existing_bridges_command_fails(
        self, mock_subprocess, bridge_manager, mock_db_manager
    ):
        """Test handling of failed bridge command."""
        # Mock database returning bridge nodes
        mock_db_manager.get_all_nodes.return_value = [("br-main", "bridge", "N/A")]

        # Mock subprocess to raise exception
        mock_subprocess.side_effect = Exception("Command failed")

        bridges = bridge_manager.get_existing_bridges()

        assert bridges == []

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_check_bridge_exists_true(self, mock_subprocess, bridge_manager):
        """Test checking if bridge exists (exists)."""
        # Mock successful ip link show command
        mock_subprocess.return_value.returncode = 0

        exists = bridge_manager.check_bridge_exists("br-main")

        assert exists is True
        mock_subprocess.assert_called_once_with(
            ["ip", "link", "show", "br-main"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_check_bridge_exists_false(self, mock_subprocess, bridge_manager):
        """Test checking if bridge exists (doesn't exist)."""
        # Mock failed ip link show command
        mock_subprocess.return_value.returncode = 1

        exists = bridge_manager.check_bridge_exists("nonexistent-br")

        assert exists is False
        mock_subprocess.assert_called_once()

    def test_get_missing_bridges(self, bridge_manager, mock_db_manager):
        """Test getting missing bridges."""
        # Mock database bridges
        mock_db_manager.get_all_nodes.return_value = [
            ("br-main", "bridge", "N/A"),
            ("br-access", "bridge", "N/A"),
            ("br-trunk", "bridge", "N/A"),
        ]

        # Mock existing bridges
        with patch.object(bridge_manager, "check_bridge_exists") as mock_check:
            # br-main exists, others don't
            def check_side_effect(bridge_name):
                return bridge_name == "br-main"

            mock_check.side_effect = check_side_effect

            missing = bridge_manager.get_missing_bridges()

            assert missing == ["br-access", "br-trunk"]

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_create_bridge_success(self, mock_subprocess, bridge_manager):
        """Test successful VLAN-aware bridge creation."""
        # Mock bridge doesn't exist
        with patch.object(bridge_manager, "check_bridge_exists", return_value=False):
            # Mock successful commands
            mock_subprocess.return_value.returncode = 0

            success, message = bridge_manager.create_bridge("br-test")

            assert success is True
            assert "successfully created" in message.lower()

            # Verify VLAN-aware bridge creation commands
            expected_calls = [
                call(
                    [
                        "sudo",
                        "ip",
                        "link",
                        "add",
                        "name",
                        "br-test",
                        "type",
                        "bridge",
                        "vlan_filtering",
                        "1",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                ),
                call(
                    ["sudo", "ip", "link", "set", "br-test", "up"],
                    capture_output=True,
                    text=True,
                    check=True,
                ),
                call(
                    [
                        "sudo",
                        "bridge",
                        "vlan",
                        "add",
                        "vid",
                        "1-4094",
                        "dev",
                        "br-test",
                        "self",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                ),
            ]
            mock_subprocess.assert_has_calls(expected_calls)

    def test_create_bridge_already_exists(self, bridge_manager):
        """Test creating bridge that already exists."""
        with patch.object(bridge_manager, "check_bridge_exists", return_value=True):
            success, message = bridge_manager.create_bridge("br-existing")

            assert success is True
            assert "already exists" in message

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_create_bridge_dry_run(self, mock_subprocess, bridge_manager):
        """Test bridge creation in dry-run mode."""
        with patch.object(bridge_manager, "check_bridge_exists", return_value=False):
            success, message = bridge_manager.create_bridge("br-test", dry_run=True)

            assert success is True
            assert "would create" in message.lower()

            # Should not execute any actual commands
            mock_subprocess.assert_not_called()

    @patch("clab_tools.bridges.manager.subprocess.run")
    def test_create_bridge_command_failure(self, mock_subprocess, bridge_manager):
        """Test bridge creation command failure."""
        with patch.object(bridge_manager, "check_bridge_exists", return_value=False):
            # Mock command failure
            mock_subprocess.side_effect = Exception("Command failed")

            success, message = bridge_manager.create_bridge("br-test")

            assert success is False
            assert "error" in message.lower()

    def test_create_all_bridges(self, bridge_manager):
        """Test creating all missing bridges."""
        missing_bridges = ["br-main", "br-access"]

        with patch.object(
            bridge_manager, "get_missing_bridges", return_value=missing_bridges
        ):
            with patch.object(bridge_manager, "create_bridge") as mock_create:
                mock_create.return_value = (True, "Bridge created successfully")
                with patch("click.confirm", return_value=True):

                    success, message = bridge_manager.create_all_bridges()

                    assert success is True
                    assert "2/2" in message

                    # Verify create_bridge called for each missing bridge
                    expected_calls = [call("br-main", False), call("br-access", False)]
                    mock_create.assert_has_calls(expected_calls)

    def test_create_all_bridges_dry_run(self, bridge_manager):
        """Test creating all bridges in dry-run mode."""
        missing_bridges = ["br-test"]

        with patch.object(
            bridge_manager, "get_missing_bridges", return_value=missing_bridges
        ):
            with patch.object(bridge_manager, "create_bridge") as mock_create:
                mock_create.return_value = (True, "Would create bridge")

                success, message = bridge_manager.create_all_bridges(dry_run=True)

                assert success is True
                assert "would create" in message.lower()
                mock_create.assert_called_once_with("br-test", True)

    def test_create_all_bridges_no_missing(self, bridge_manager):
        """Test creating all bridges when none are missing."""
        with patch.object(bridge_manager, "get_missing_bridges", return_value=[]):
            success, message = bridge_manager.create_all_bridges()

            assert success is True
            assert "already exist" in message
