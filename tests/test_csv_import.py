"""Integration tests for CSV import functionality."""

import pytest

from clab_tools.commands.import_csv import import_csv_command


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
