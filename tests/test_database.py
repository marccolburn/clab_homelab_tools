"""Tests for database manager."""

import pytest

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
