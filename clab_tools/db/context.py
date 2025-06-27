"""
Database Context Helpers

Helper functions for working with the multi-lab database in a simplified way.
"""

from typing import Any, Dict

from .manager import DatabaseManager


class LabAwareDB:
    """A simple wrapper to provide lab context to database operations."""

    def __init__(self, db_manager: DatabaseManager, lab_name: str):
        self.db_manager = db_manager
        self.lab_name = lab_name

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False  # Don't suppress exceptions

    def clear_nodes(self) -> bool:
        return self.db_manager.clear_nodes(self.lab_name)

    def clear_connections(self) -> bool:
        return self.db_manager.clear_connections(self.lab_name)

    def insert_node(self, name: str, kind: str, mgmt_ip: str) -> bool:
        return self.db_manager.insert_node(name, kind, mgmt_ip, self.lab_name)

    def insert_connection(
        self,
        node1: str,
        node2: str,
        conn_type: str,
        node1_interface: str,
        node2_interface: str,
    ) -> bool:
        return self.db_manager.insert_connection(
            node1, node2, conn_type, node1_interface, node2_interface, self.lab_name
        )

    def get_all_nodes(self):
        return self.db_manager.get_all_nodes(self.lab_name)

    def get_all_connections(self):
        return self.db_manager.get_all_connections(self.lab_name)

    def save_topology_config(
        self, name: str, prefix: str, mgmt_network: str, mgmt_subnet: str
    ) -> bool:
        return self.db_manager.save_topology_config(
            name, prefix, mgmt_network, mgmt_subnet, self.lab_name
        )

    def get_topology_config(self, name: str):
        return self.db_manager.get_topology_config(name, self.lab_name)

    def get_node_by_name(self, name: str):
        return self.db_manager.get_node_by_name(name, self.lab_name)

    def delete_node(self, name: str) -> bool:
        return self.db_manager.delete_node(name, self.lab_name)

    def get_nodes_by_kind(self, kind: str):
        return self.db_manager.get_nodes_by_kind(kind, self.lab_name)

    def get_stats(self):
        return self.db_manager.get_stats(self.lab_name)


def get_lab_db(ctx: Dict[str, Any]) -> LabAwareDB:
    """Get a lab-aware database wrapper from the click context."""
    raw_db_manager = ctx["raw_db_manager"]
    current_lab = ctx["current_lab"]
    return LabAwareDB(raw_db_manager, current_lab)
