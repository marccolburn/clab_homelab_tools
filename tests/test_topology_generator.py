"""Tests for topology generator functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from clab_tools.topology.generator import TopologyGenerator


class TestTopologyGenerator:
    """Test cases for TopologyGenerator."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_db = Mock()
        return mock_db

    def test_template_path_resolution_relative(self, mock_db_manager):
        """Test that relative template paths are resolved relative to package root."""
        generator = TopologyGenerator(
            mock_db_manager,
            template_file="topology_template.j2",
            kinds_file="supported_kinds.yaml",
        )

        # Template file should be resolved to package root
        expected_template_path = Path(__file__).parent.parent / "topology_template.j2"
        assert generator.template_file == expected_template_path

        # Kinds file should be resolved to package root
        expected_kinds_path = Path(__file__).parent.parent / "supported_kinds.yaml"
        assert generator.kinds_file == expected_kinds_path

    def test_template_path_resolution_absolute(self, mock_db_manager):
        """Test that absolute template paths are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "custom_template.j2"
            kinds_path = Path(temp_dir) / "custom_kinds.yaml"

            generator = TopologyGenerator(
                mock_db_manager,
                template_file=str(template_path),
                kinds_file=str(kinds_path),
            )

            # Absolute paths should be preserved
            assert generator.template_file == template_path
            assert generator.kinds_file == kinds_path

    def test_template_loading_from_different_dir(self, mock_db_manager):
        """Test template loading when script runs from different directory."""
        generator = TopologyGenerator(mock_db_manager)

        # Mock the database methods
        mock_db_manager.get_all_nodes.return_value = [
            ("test_node", "test_kind", "192.168.1.1")
        ]
        mock_db_manager.get_all_connections.return_value = []
        mock_db_manager.save_topology_config.return_value = None

        # Change to a different directory temporarily
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)

                # Verify the template file path is still correctly resolved
                package_root = Path(__file__).parent.parent
                expected_template = package_root / "topology_template.j2"
                assert generator.template_file == expected_template

                # The template file should exist (tests path resolution)
                assert (
                    generator.template_file.exists()
                ), f"Template file not found at {generator.template_file}"

        finally:
            os.chdir(original_cwd)

    def test_kinds_file_loading_from_different_dir(self, mock_db_manager):
        """Test kinds file loading when script runs from different directory."""
        generator = TopologyGenerator(mock_db_manager)

        # Change to a different directory temporarily
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)

                # Verify the kinds file path is correctly resolved
                package_root = Path(__file__).parent.parent
                expected_kinds = package_root / "supported_kinds.yaml"
                assert generator.kinds_file == expected_kinds

                # The kinds file should exist (tests path resolution)
                assert (
                    generator.kinds_file.exists()
                ), f"Kinds file not found at {generator.kinds_file}"

        finally:
            os.chdir(original_cwd)

    def test_load_supported_kinds_with_resolved_path(self, mock_db_manager):
        """Test loading supported kinds with properly resolved path."""
        generator = TopologyGenerator(mock_db_manager)

        # Change to a different directory to simulate the original issue
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)

                # Should not raise FileNotFoundError (path resolved correctly)
                kinds = generator.load_supported_kinds()

                # Should return either the loaded kinds or defaults, not an error
                assert isinstance(kinds, dict)
                assert len(kinds) > 0

        finally:
            os.chdir(original_cwd)
