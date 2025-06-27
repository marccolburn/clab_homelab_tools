"""
Tests for generate_topology command logic.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from clab_tools.commands.generate_topology import generate_topology_command


class TestGenerateTopologyCommand:
    """Test the generate_topology command logic."""

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

    @patch("clab_tools.commands.generate_topology.get_settings")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_uses_config_default_topology_name(
        self, mock_generator_class, mock_get_settings
    ):
        """Test that config default topology name is used when 'generated_lab'."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.topology.default_topology_name = "my_custom_lab"
        mock_settings.topology.default_prefix = "test"
        mock_get_settings.return_value = mock_settings

        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.generate_topology_data.return_value = ([], [], [])

        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp_file:
            try:
                generate_topology_command(
                    db_manager=self.mock_db,
                    output=tmp_file.name,
                    topology_name="generated_lab",  # This should trigger config default
                    prefix="test",
                    mgmt_network="mgmt",
                    mgmt_subnet="192.168.1.0/24",
                    template="template.j2",
                    kinds_config="kinds.yml",
                    validate=False,
                    upload_remote=False,
                )

                # Verify the generator was called with the config default topology name
                mock_generator.generate_topology_file.assert_called_once()
                call_args = mock_generator.generate_topology_file.call_args
                assert call_args[1]["topology_name"] == "my_custom_lab"

            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    @patch("clab_tools.commands.generate_topology.get_settings")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_uses_explicit_topology_name(self, mock_generator_class, mock_get_settings):
        """Test that command uses explicit topology name when provided."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.topology.default_topology_name = "my_custom_lab"
        mock_settings.topology.default_prefix = "test"
        mock_get_settings.return_value = mock_settings

        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.generate_topology_data.return_value = ([], [], [])

        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp_file:
            try:
                generate_topology_command(
                    db_manager=self.mock_db,
                    output=tmp_file.name,
                    # This should NOT trigger config default
                    topology_name="explicit_lab",
                    prefix="test",
                    mgmt_network="mgmt",
                    mgmt_subnet="192.168.1.0/24",
                    template="template.j2",
                    kinds_config="kinds.yml",
                    validate=False,
                    upload_remote=False,
                )

                # Verify the generator was called with the explicit topology name
                mock_generator.generate_topology_file.assert_called_once()
                call_args = mock_generator.generate_topology_file.call_args
                assert call_args[1]["topology_name"] == "explicit_lab"

            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    @patch("clab_tools.commands.generate_topology.get_settings")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_uses_config_default_prefix_when_none(
        self, mock_generator_class, mock_get_settings
    ):
        """Test that command uses config default prefix when prefix is None."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.topology.default_topology_name = "my_custom_lab"
        mock_settings.topology.default_prefix = "config_prefix"
        mock_get_settings.return_value = mock_settings

        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.generate_topology_data.return_value = ([], [], [])

        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp_file:
            try:
                generate_topology_command(
                    db_manager=self.mock_db,
                    output=tmp_file.name,
                    topology_name="test_lab",
                    prefix=None,  # This should trigger config default
                    mgmt_network="mgmt",
                    mgmt_subnet="192.168.1.0/24",
                    template="template.j2",
                    kinds_config="kinds.yml",
                    validate=False,
                    upload_remote=False,
                )

                # Verify the generator was called with the config default prefix
                mock_generator.generate_topology_file.assert_called_once()
                call_args = mock_generator.generate_topology_file.call_args
                assert call_args[1]["prefix"] == "config_prefix"

            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    @patch("clab_tools.commands.generate_topology.get_settings")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_handles_prefix_none(self, mock_generator_class, mock_get_settings):
        """Test that command handles 'none' prefix correctly."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.topology.default_topology_name = "my_custom_lab"
        mock_settings.topology.default_prefix = "test"
        mock_get_settings.return_value = mock_settings

        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_topology_file.return_value = True
        mock_generator.generate_topology_data.return_value = ([], [], [])

        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp_file:
            try:
                generate_topology_command(
                    db_manager=self.mock_db,
                    output=tmp_file.name,
                    topology_name="test_lab",
                    prefix="none",  # This should result in empty string
                    mgmt_network="mgmt",
                    mgmt_subnet="192.168.1.0/24",
                    template="template.j2",
                    kinds_config="kinds.yml",
                    validate=False,
                    upload_remote=False,
                )

                # Verify the generator was called with empty prefix
                mock_generator.generate_topology_file.assert_called_once()
                call_args = mock_generator.generate_topology_file.call_args
                assert call_args[1]["prefix"] == ""

            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    @patch("clab_tools.commands.generate_topology.get_settings")
    @patch("clab_tools.commands.generate_topology.TopologyGenerator")
    def test_exits_when_no_nodes(self, mock_generator_class, mock_get_settings):
        """Test that command exits when no nodes are found in database."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.topology.default_topology_name = "my_custom_lab"
        mock_settings.topology.default_prefix = "test"
        mock_get_settings.return_value = mock_settings

        # Mock empty database
        mock_db_empty = Mock()
        mock_db_empty.get_all_nodes.return_value = []
        mock_db_empty.get_all_connections.return_value = []

        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp_file:
            try:
                with pytest.raises(SystemExit) as exc_info:
                    generate_topology_command(
                        db_manager=mock_db_empty,
                        output=tmp_file.name,
                        topology_name="test_lab",
                        prefix="test",
                        mgmt_network="mgmt",
                        mgmt_subnet="192.168.1.0/24",
                        template="template.j2",
                        kinds_config="kinds.yml",
                        validate=False,
                        upload_remote=False,
                    )

                # Should exit with code 1
                assert exc_info.value.code == 1

            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
