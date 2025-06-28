"""Tests for database manager."""

import os
import tempfile
from pathlib import Path

import pytest

from clab_tools.config.settings import DatabaseSettings, get_default_database_path
from clab_tools.db.manager import DatabaseManager
from clab_tools.errors.exceptions import DatabaseError


class TestDatabaseManager:
    """Test cases for DatabaseManager."""

    def test_init_database(self, db_manager):
        """Test database initialization."""
        assert db_manager.health_check()

    def test_insert_and_get_node(self, db_manager):
        """Test node insertion and retrieval."""
        # Insert a node
        result = db_manager.insert_node("test-router", "nokia_srlinux", "172.20.20.10")
        assert result is True

        # Retrieve nodes
        nodes = db_manager.get_all_nodes()
        assert len(nodes) == 1
        assert nodes[0] == ("test-router", "nokia_srlinux", "172.20.20.10")

    def test_insert_bridge_node_with_na_ip(self, db_manager):
        """Test inserting bridge node with N/A management IP."""
        # Insert bridge node
        result = db_manager.insert_node("br-main", "bridge", "N/A")
        assert result is True

        # Retrieve nodes
        nodes = db_manager.get_all_nodes()
        assert len(nodes) == 1
        assert nodes[0] == ("br-main", "bridge", "N/A")

        # Verify we can get it by name
        node = db_manager.get_node_by_name("br-main")
        assert node is not None
        assert node.name == "br-main"
        assert node.kind == "bridge"
        assert node.mgmt_ip == "N/A"

    def test_get_bridge_nodes_by_kind(self, db_manager):
        """Test getting bridge nodes specifically."""
        # Insert mixed node types
        db_manager.insert_node("router1", "nokia_srlinux", "172.20.20.10")
        db_manager.insert_node("router2", "cisco_xrd", "172.20.20.11")
        db_manager.insert_node("br-main", "bridge", "N/A")
        db_manager.insert_node("br-access", "bridge", "N/A")

        # Get only bridge nodes
        bridge_nodes = db_manager.get_nodes_by_kind("bridge")
        assert len(bridge_nodes) == 2
        bridge_names = [node.name for node in bridge_nodes]
        assert "br-main" in bridge_names
        assert "br-access" in bridge_names

        # Verify all are bridge type
        for node in bridge_nodes:
            assert node.kind == "bridge"
            assert node.mgmt_ip == "N/A"

    def test_insert_duplicate_node(self, db_manager):
        """Test inserting a node with duplicate name updates existing."""
        # Insert original node
        db_manager.insert_node("router1", "nokia_srlinux", "172.20.20.10")

        # Insert node with same name but different properties
        result = db_manager.insert_node("router1", "cisco_xrd", "172.20.20.20")
        assert result is True

        # Should have only one node with updated properties
        nodes = db_manager.get_all_nodes()
        assert len(nodes) == 1
        assert nodes[0] == ("router1", "cisco_xrd", "172.20.20.20")

    def test_insert_and_get_connection(self, db_manager):
        """Test connection insertion and retrieval."""
        # First insert nodes
        db_manager.insert_node("router1", "nokia_srlinux", "172.20.20.10")
        db_manager.insert_node("router2", "nokia_srlinux", "172.20.20.11")

        # Insert connection
        result = db_manager.insert_connection(
            "router1", "router2", "veth", "eth1", "eth1"
        )
        assert result is True

        # Retrieve connections
        connections = db_manager.get_all_connections()
        assert len(connections) == 1
        assert connections[0] == ("router1", "router2", "veth", "eth1", "eth1")

    def test_insert_connection_nonexistent_node(self, db_manager):
        """Test inserting connection with non-existent node fails."""
        with pytest.raises(DatabaseError, match="Node 'nonexistent' does not exist"):
            db_manager.insert_connection(
                "nonexistent", "router2", "veth", "eth1", "eth1"
            )

    def test_clear_nodes(self, populated_db_manager):
        """Test clearing all nodes."""
        # Verify nodes exist
        nodes = populated_db_manager.get_all_nodes()
        assert len(nodes) > 0

        # Clear nodes
        result = populated_db_manager.clear_nodes()
        assert result is True

        # Verify nodes are cleared
        nodes = populated_db_manager.get_all_nodes()
        assert len(nodes) == 0

    def test_clear_connections(self, populated_db_manager):
        """Test clearing all connections."""
        # Verify connections exist
        connections = populated_db_manager.get_all_connections()
        assert len(connections) > 0

        # Clear connections
        result = populated_db_manager.clear_connections()
        assert result is True

        # Verify connections are cleared
        connections = populated_db_manager.get_all_connections()
        assert len(connections) == 0

    def test_topology_config_operations(self, db_manager):
        """Test topology configuration save and retrieve."""
        # Save config
        result = db_manager.save_topology_config(
            "test-lab", "test", "clab", "172.20.20.0/24"
        )
        assert result is True

        # Retrieve config
        config = db_manager.get_topology_config("test-lab")
        assert config is not None
        assert config == ("test", "clab", "172.20.20.0/24")

        # Retrieve non-existent config
        config = db_manager.get_topology_config("nonexistent")
        assert config is None

    def test_update_topology_config(self, db_manager):
        """Test updating existing topology configuration."""
        # Save initial config
        db_manager.save_topology_config("lab1", "prefix1", "net1", "192.168.1.0/24")

        # Update config
        result = db_manager.save_topology_config(
            "lab1", "prefix2", "net2", "192.168.2.0/24"
        )
        assert result is True

        # Verify updated values
        config = db_manager.get_topology_config("lab1")
        assert config == ("prefix2", "net2", "192.168.2.0/24")

    def test_get_stats(self, populated_db_manager):
        """Test getting database statistics."""
        stats = populated_db_manager.get_stats()

        assert "nodes" in stats
        assert "connections" in stats
        assert "configs" in stats
        assert stats["nodes"] >= 3
        assert stats["connections"] >= 2
        assert stats["configs"] >= 1

    def test_get_node_by_name(self, populated_db_manager):
        """Test getting node by name."""
        node = populated_db_manager.get_node_by_name("router1")
        assert node is not None
        assert node.name == "router1"
        assert node.kind == "nokia_srlinux"

        # Test non-existent node
        node = populated_db_manager.get_node_by_name("nonexistent")
        assert node is None

    def test_delete_node(self, populated_db_manager):
        """Test deleting a node."""
        # Verify node exists
        node = populated_db_manager.get_node_by_name("router1")
        assert node is not None

        # Delete node
        result = populated_db_manager.delete_node("router1")
        assert result is True

        # Verify node is deleted
        node = populated_db_manager.get_node_by_name("router1")
        assert node is None

        # Delete non-existent node
        result = populated_db_manager.delete_node("nonexistent")
        assert result is False

    def test_get_nodes_by_kind(self, populated_db_manager):
        """Test getting nodes by kind."""
        nodes = populated_db_manager.get_nodes_by_kind("nokia_srlinux")
        assert len(nodes) == 2
        assert all(node.kind == "nokia_srlinux" for node in nodes)

        nodes = populated_db_manager.get_nodes_by_kind("bridge")
        assert len(nodes) == 1
        assert nodes[0].kind == "bridge"

        # Test non-existent kind
        nodes = populated_db_manager.get_nodes_by_kind("nonexistent")
        assert len(nodes) == 0


class TestDatabaseLocation:
    """Test cases for database location behavior."""

    def test_default_database_path_function(self):
        """Test that get_default_database_path returns correct path."""
        db_path = get_default_database_path()

        # Should be a sqlite URL
        assert db_path.startswith("sqlite:///")

        # Should be an absolute path
        path_part = db_path.replace("sqlite:///", "")
        assert Path(path_part).is_absolute()

        # Should end with clab_topology.db
        assert path_part.endswith("clab_topology.db")

        # Should be in the package directory (3 levels up from settings.py)
        expected_dir = Path(__file__).parent.parent
        expected_path = expected_dir / "clab_topology.db"
        assert path_part == str(expected_path.absolute())

    def test_database_settings_default_factory(self):
        """Test that DatabaseSettings uses the default_factory correctly."""
        settings = DatabaseSettings()

        # Should use the dynamically generated path
        assert settings.url.startswith("sqlite:///")
        assert "clab_topology.db" in settings.url

        # Should be an absolute path
        path_part = settings.url.replace("sqlite:///", "")
        assert Path(path_part).is_absolute()

    def test_database_location_consistency_across_directories(self):
        """Test database path consistency across directories."""
        original_cwd = os.getcwd()

        try:
            # Get path from original directory
            original_path = get_default_database_path()

            # Change to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)

                # Get path from different directory
                temp_path = get_default_database_path()

                # Should be the same
                assert original_path == temp_path

                # Both should be absolute paths
                assert Path(original_path.replace("sqlite:///", "")).is_absolute()
                assert Path(temp_path.replace("sqlite:///", "")).is_absolute()

        finally:
            # Always restore original directory
            os.chdir(original_cwd)

    def test_database_manager_with_default_path(self):
        """Test DatabaseManager works with default path configuration."""
        # Create database manager (using memory for testing to avoid file conflicts)
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_url = f"sqlite:///{temp_db.name}"

        try:
            # Override with temp database for testing
            test_settings = DatabaseSettings(url=temp_db_url)
            db_manager = DatabaseManager(settings=test_settings)

            # Should initialize successfully
            assert db_manager.health_check()

            # Should be able to perform basic operations
            result = db_manager.insert_node("test-node", "test-kind", "192.168.1.1")
            assert result is True

            nodes = db_manager.get_all_nodes()
            assert len(nodes) == 1
            assert nodes[0] == ("test-node", "test-kind", "192.168.1.1")

        finally:
            # Clean up temp database
            if Path(temp_db.name).exists():
                Path(temp_db.name).unlink()

    def test_database_url_override_precedence(self):
        """Test that explicit URL overrides the default path."""
        custom_url = "sqlite:///custom_test.db"

        # Create settings with custom URL
        settings = DatabaseSettings(url=custom_url)

        # Should use the custom URL, not the default
        assert settings.url == custom_url
        assert settings.url != get_default_database_path()

    def test_database_path_in_package_directory(self):
        """Test that default database path is in the package root directory."""
        db_path = get_default_database_path()
        path_part = db_path.replace("sqlite:///", "")

        # Should be in the package root (where setup.py, pyproject.toml would be)
        package_root = Path(__file__).parent.parent
        expected_path = package_root / "clab_topology.db"

        assert Path(path_part) == expected_path.absolute()

        # Verify this is indeed the package root by checking for key files
        assert (package_root / "pyproject.toml").exists()
        assert (package_root / "clab_tools").exists()

    def test_database_settings_immutable_after_creation(self):
        """Test that database path is determined at creation time."""
        original_cwd = os.getcwd()

        try:
            # Create settings in original directory
            settings1 = DatabaseSettings()
            path1 = settings1.url

            # Change directory and create new settings
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                settings2 = DatabaseSettings()
                path2 = settings2.url

                # Both should point to the same absolute location
                assert path1 == path2

                # And it should be the package directory, not the temp directory
                assert temp_dir not in path1
                assert temp_dir not in path2

        finally:
            os.chdir(original_cwd)

    def test_database_directory_structure(self):
        """Test that the database path resolves to expected directory structure."""
        db_path = get_default_database_path()
        path_part = db_path.replace("sqlite:///", "")
        db_file_path = Path(path_part)

        # Parent directory should be the package root
        package_dir = db_file_path.parent

        # Should contain expected package structure
        assert (package_dir / "clab_tools").is_dir()
        assert (package_dir / "tests").is_dir()
        assert (package_dir / "pyproject.toml").is_file()

        # Database file should be named correctly
        assert db_file_path.name == "clab_topology.db"
