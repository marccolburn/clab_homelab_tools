"""
Tests for topology generation with remote upload functionality.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from clab_tools.commands.generate_topology import generate_topology_command
from clab_tools.remote import RemoteHostManager


class TestTopologyGenerationWithRemote:
    """Test topology generation with remote upload integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.get_all_nodes.return_value = [
            ("router1", "linux", "192.168.1.1"),
            ("switch1", "bridge", None),
        ]
        self.mock_db.get_all_connections.return_value = [
            ("router1", "eth0", "switch1", "eth1"),
        ]

    @patch("clab_tools.commands.generate_topology.get_remote_host_manager")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_without_remote_upload(
        self, mock_generator_class, mock_get_remote
    ):
        """Test topology generation without remote upload."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.validate_yaml.return_value = (True, "Valid YAML")
        mock_generator.generate_topology_data.return_value = ([], [], [])
        mock_get_remote.return_value = None

        generate_topology_command(
            db_manager=self.mock_db,
            output="test.yml",
            topology_name="test",
            prefix="test",
            mgmt_network="mgmt",
            mgmt_subnet="192.168.1.0/24",
            template="template.j2",
            kinds_config="kinds.yml",
            validate=True,
            upload_remote=False,
        )

        # Verify topology was generated
        mock_generator.generate_topology_file.assert_called_once()
        mock_generator.validate_yaml.assert_called_with("test.yml")

        # Verify remote manager was not used
        mock_get_remote.assert_not_called()

    @patch("clab_tools.commands.generate_topology.get_remote_host_manager")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_with_remote_upload_success(
        self, mock_generator_class, mock_get_remote
    ):
        """Test topology generation with successful remote upload."""
        # Setup topology generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.validate_yaml.return_value = (True, "Valid YAML")
        mock_generator.generate_topology_data.return_value = ([], [], [])

        # Setup remote manager
        mock_remote_manager = Mock(spec=RemoteHostManager)
        mock_remote_manager.__enter__ = Mock(return_value=mock_remote_manager)
        mock_remote_manager.__exit__ = Mock(return_value=None)
        mock_remote_manager.upload_topology_file.return_value = "/remote/path/test.yml"
        mock_get_remote.return_value = mock_remote_manager

        generate_topology_command(
            db_manager=self.mock_db,
            output="test.yml",
            topology_name="test",
            prefix="test",
            mgmt_network="mgmt",
            mgmt_subnet="192.168.1.0/24",
            template="template.j2",
            kinds_config="kinds.yml",
            validate=True,
            upload_remote=True,
        )

        # Verify topology was generated
        mock_generator.generate_topology_file.assert_called_once()

        # Verify remote upload was attempted
        mock_get_remote.assert_called_once()
        mock_remote_manager.__enter__.assert_called_once()
        mock_remote_manager.upload_topology_file.assert_called_with("test.yml")
        mock_remote_manager.__exit__.assert_called_once()

    @patch("clab_tools.commands.generate_topology.get_remote_host_manager")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_with_remote_upload_no_remote_configured(
        self, mock_generator_class, mock_get_remote
    ):
        """Test topology generation with remote upload but no remote configured."""
        # Setup topology generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.validate_yaml.return_value = (True, "Valid YAML")
        mock_generator.generate_topology_data.return_value = ([], [], [])

        # No remote manager configured
        mock_get_remote.return_value = None

        with pytest.raises(SystemExit):
            generate_topology_command(
                db_manager=self.mock_db,
                output="test.yml",
                topology_name="test",
                prefix="test",
                mgmt_network="mgmt",
                mgmt_subnet="192.168.1.0/24",
                template="template.j2",
                kinds_config="kinds.yml",
                validate=True,
                upload_remote=True,
            )

    @patch("clab_tools.commands.generate_topology.get_remote_host_manager")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_with_remote_upload_failure(
        self, mock_generator_class, mock_get_remote
    ):
        """Test topology generation with remote upload failure."""
        # Setup topology generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.validate_yaml.return_value = (True, "Valid YAML")
        mock_generator.generate_topology_data.return_value = ([], [], [])

        # Setup remote manager with upload failure
        mock_remote_manager = Mock(spec=RemoteHostManager)
        mock_remote_manager.__enter__ = Mock(return_value=mock_remote_manager)
        mock_remote_manager.__exit__ = Mock(return_value=None)
        mock_remote_manager.upload_topology_file.side_effect = Exception(
            "Upload failed"
        )
        mock_get_remote.return_value = mock_remote_manager

        with pytest.raises(SystemExit):
            generate_topology_command(
                db_manager=self.mock_db,
                output="test.yml",
                topology_name="test",
                prefix="test",
                mgmt_network="mgmt",
                mgmt_subnet="192.168.1.0/24",
                template="template.j2",
                kinds_config="kinds.yml",
                validate=True,
                upload_remote=True,
            )

    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_with_no_nodes(self, mock_generator_class):
        """Test topology generation with no nodes in database."""
        # Empty database
        self.mock_db.get_all_nodes.return_value = []

        with pytest.raises(SystemExit):
            generate_topology_command(
                db_manager=self.mock_db,
                output="test.yml",
                topology_name="test",
                prefix="test",
                mgmt_network="mgmt",
                mgmt_subnet="192.168.1.0/24",
                template="template.j2",
                kinds_config="kinds.yml",
                validate=True,
                upload_remote=False,
            )

    @patch("clab_tools.commands.generate_topology.get_remote_host_manager")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_topology_failure(self, mock_generator_class, mock_get_remote):
        """Test handling of topology generation failure."""
        # Setup failing topology generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = False

        with pytest.raises(SystemExit):
            generate_topology_command(
                db_manager=self.mock_db,
                output="test.yml",
                topology_name="test",
                prefix="test",
                mgmt_network="mgmt",
                mgmt_subnet="192.168.1.0/24",
                template="template.j2",
                kinds_config="kinds.yml",
                validate=True,
                upload_remote=False,
            )

    @patch("clab_tools.commands.generate_topology.get_remote_host_manager")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_generate_with_validation_failure(
        self, mock_generator_class, mock_get_remote
    ):
        """Test topology generation with validation failure."""
        # Setup topology generator with validation failure
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.validate_yaml.return_value = (False, "Invalid YAML")
        mock_generator.generate_topology_data.return_value = ([], [], [])

        # Should not raise SystemExit, just log the validation error
        generate_topology_command(
            db_manager=self.mock_db,
            output="test.yml",
            topology_name="test",
            prefix="test",
            mgmt_network="mgmt",
            mgmt_subnet="192.168.1.0/24",
            template="template.j2",
            kinds_config="kinds.yml",
            validate=True,
            upload_remote=False,
        )

        # Verify validation was called
        mock_generator.validate_yaml.assert_called_with("test.yml")


class TestRemoteTopologyUpload:
    """Test specific remote topology upload functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_file = None

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_file and os.path.exists(self.temp_file):
            os.unlink(self.temp_file)

    def test_upload_topology_file(self):
        """Test topology file upload to remote host."""
        # Create temporary topology file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(
                """
name: test-topology
topology:
  nodes:
    router1:
      kind: linux
      image: alpine:latest
"""
            )
            self.temp_file = f.name

        # Mock remote manager
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.settings.topology_remote_dir = "/tmp/clab-topologies"

        # Mock SFTP operations
        mock_sftp = Mock()
        remote_manager._sftp_client = mock_sftp
        remote_manager.is_connected.return_value = True

        # Mock mkdir command
        remote_manager.execute_command.return_value = (0, "", "")

        # Test upload
        result = remote_manager.upload_topology_file(self.temp_file, "custom-name.yml")

        expected_path = "/tmp/clab-topologies/custom-name.yml"
        assert result == expected_path

        # Verify upload was called
        remote_manager.upload_file.assert_called_with(self.temp_file, expected_path)

    def test_upload_topology_file_default_name(self):
        """Test topology file upload with default filename."""
        # Create temporary topology file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("name: test-topology")
            self.temp_file = f.name

        # Mock remote manager
        remote_manager = Mock(spec=RemoteHostManager)
        remote_manager.settings.topology_remote_dir = "/tmp/clab-topologies"

        # Test upload with default name
        result = remote_manager.upload_topology_file(self.temp_file)

        expected_filename = os.path.basename(self.temp_file)
        expected_path = f"/tmp/clab-topologies/{expected_filename}"
        assert result == expected_path

        # Verify upload was called
        remote_manager.upload_file.assert_called_with(self.temp_file, expected_path)
