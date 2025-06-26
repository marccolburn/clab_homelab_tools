"""Integration tests for CSV import functionality."""

import pytest

from clab_tools.commands.import_csv import import_csv_command
from clab_tools.errors.exceptions import CSVImportError


class TestCSVImport:
    """Integration tests for CSV import."""

    def test_successful_csv_import(
        self, db_manager, sample_nodes_csv, sample_connections_csv
    ):
        """Test successful import of valid CSV files."""
        # Import CSV data
        import_csv_command(
            db_manager, sample_nodes_csv, sample_connections_csv, clear_existing=True
        )

        # Verify nodes were imported
        nodes = db_manager.get_all_nodes()
        assert len(nodes) == 3
        node_names = [node[0] for node in nodes]
        assert "router1" in node_names
        assert "router2" in node_names
        assert "switch1" in node_names

        # Verify connections were imported
        connections = db_manager.get_all_connections()
        assert len(connections) == 3

        # Verify specific connection exists
        conn_pairs = [(conn[0], conn[1]) for conn in connections]
        assert ("router1", "router2") in conn_pairs
        assert ("router1", "switch1") in conn_pairs
        assert ("router2", "switch1") in conn_pairs

    def test_import_with_missing_nodes_file(self, db_manager, sample_connections_csv):
        """Test import behavior with missing nodes file."""
        with pytest.raises(Exception):  # Should raise FileNotFoundError
            import_csv_command(
                db_manager,
                "nonexistent.csv",
                sample_connections_csv,
                clear_existing=False,
            )

    def test_import_with_invalid_nodes_csv(
        self, db_manager, invalid_nodes_csv, sample_connections_csv
    ):
        """Test import behavior with invalid nodes CSV format."""
        with pytest.raises(Exception):  # Should raise KeyError for missing columns
            import_csv_command(
                db_manager,
                invalid_nodes_csv,
                sample_connections_csv,
                clear_existing=False,
            )

    def test_import_without_clearing(
        self, db_manager, sample_nodes_csv, sample_connections_csv
    ):
        """Test importing without clearing existing data."""
        # First import
        import_csv_command(
            db_manager, sample_nodes_csv, sample_connections_csv, clear_existing=True
        )
        initial_node_count = len(db_manager.get_all_nodes())

        # Second import without clearing - should update existing nodes
        import_csv_command(
            db_manager, sample_nodes_csv, sample_connections_csv, clear_existing=False
        )
        final_node_count = len(db_manager.get_all_nodes())

        # Node count should be the same (updated, not duplicated)
        assert final_node_count == initial_node_count

    def test_bridge_nodes_without_mgmt_ip(self, db_manager, temp_dir):
        """Test importing bridge nodes without management IP."""
        # Create CSV with bridge nodes having empty mgmt_ip
        nodes_csv_content = """node_name,kind,mgmt_ip
router1,nokia_srlinux,172.20.20.10
br-main,bridge,
br-access,bridge,N/A
"""
        nodes_csv = temp_dir / "bridge_nodes.csv"
        nodes_csv.write_text(nodes_csv_content)

        connections_csv_content = """node1,node2,type,node1_interface,node2_interface
router1,br-main,veth,eth1,eth1
"""
        connections_csv = temp_dir / "bridge_connections.csv"
        connections_csv.write_text(connections_csv_content)

        # Import should succeed
        import_csv_command(
            db_manager, str(nodes_csv), str(connections_csv), clear_existing=True
        )

        # Verify nodes were imported correctly
        nodes = db_manager.get_all_nodes()
        assert len(nodes) == 3

        # Check bridge nodes have N/A for mgmt_ip
        bridge_nodes = db_manager.get_nodes_by_kind("bridge")
        assert len(bridge_nodes) == 2
        for bridge in bridge_nodes:
            assert bridge.mgmt_ip == "N/A"

    def test_non_bridge_nodes_require_mgmt_ip(self, db_manager, temp_dir):
        """Test that non-bridge nodes still require mgmt_ip."""
        # Create CSV with non-bridge node missing mgmt_ip
        nodes_csv_content = """node_name,kind,mgmt_ip
router1,nokia_srlinux,
router2,cisco_xrd,172.20.20.11
"""
        nodes_csv = temp_dir / "incomplete_nodes.csv"
        nodes_csv.write_text(nodes_csv_content)

        connections_csv_content = """node1,node2,type,node1_interface,node2_interface
router1,router2,veth,eth1,eth1
"""
        connections_csv = temp_dir / "simple_connections.csv"
        connections_csv.write_text(connections_csv_content)

        # Import should fail due to missing mgmt_ip for non-bridge node
        with pytest.raises(
            CSVImportError, match="mgmt_ip is required for non-bridge nodes"
        ):
            import_csv_command(
                db_manager, str(nodes_csv), str(connections_csv), clear_existing=True
            )

    def test_nodes_missing_required_fields(self, db_manager, temp_dir):
        """Test that nodes with missing name or kind fail import."""
        # Create CSV with missing required fields
        nodes_csv_content = """node_name,kind,mgmt_ip
,nokia_srlinux,172.20.20.10
router2,,172.20.20.11
"""
        nodes_csv = temp_dir / "invalid_nodes.csv"
        nodes_csv.write_text(nodes_csv_content)

        connections_csv_content = """node1,node2,type,node1_interface,node2_interface
router1,router2,veth,eth1,eth1
"""
        connections_csv = temp_dir / "simple_connections.csv"
        connections_csv.write_text(connections_csv_content)

        # Import should fail due to missing required fields
        with pytest.raises(CSVImportError, match="node_name and kind are required"):
            import_csv_command(
                db_manager, str(nodes_csv), str(connections_csv), clear_existing=True
            )
