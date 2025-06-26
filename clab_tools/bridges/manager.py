"""
Bridge Manager

Handles Linux bridge operations on the host system including creation,
deletion, and management of network bridges based on topology data.
"""

import subprocess
from collections import defaultdict

import click


class BridgeManager:
    """Manages Linux bridge operations on the host system."""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_bridge_list_from_db(self):
        """Get list of bridges that should exist based on database connections."""
        bridges = set()
        bridge_counter = defaultdict(int)

        connections = self.db.get_all_connections()
        for node1, node2, conn_type, node1_interface, node2_interface in connections:
            if conn_type == "bridge":
                bridge_counter[(node1, node2)] += 1

                node1_int_clean = node1_interface.replace("/", "").replace("-", "")
                node2_int_clean = node2_interface.replace("/", "").replace("-", "")
                bridge_name = f"br-{node1}-{node1_int_clean}-{node2}-{node2_int_clean}"
                bridges.add(bridge_name)

        return sorted(bridges)

    def check_bridge_exists(self, bridge_name):
        """Check if a Linux bridge exists on the system."""
        try:
            result = subprocess.run(
                ["ip", "link", "show", bridge_name],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_existing_bridges(self):
        """Get list of existing bridges that match our naming pattern."""
        required_bridges = self.get_bridge_list_from_db()
        existing = []

        for bridge in required_bridges:
            if self.check_bridge_exists(bridge):
                existing.append(bridge)

        return existing

    def get_missing_bridges(self):
        """Get list of bridges that need to be created."""
        required_bridges = self.get_bridge_list_from_db()
        missing = []

        for bridge in required_bridges:
            if not self.check_bridge_exists(bridge):
                missing.append(bridge)

        return missing

    def create_bridge(self, bridge_name, dry_run=False):
        """Create a Linux bridge on the system."""
        if self.check_bridge_exists(bridge_name):
            return True, f"Bridge {bridge_name} already exists"

        commands = [
            ["ip", "link", "add", "name", bridge_name, "type", "bridge"],
            ["ip", "link", "set", bridge_name, "up"],
        ]

        if dry_run:
            click.echo(f"Would create bridge: {bridge_name}")
            for cmd in commands:
                click.echo(f"  Command: {' '.join(cmd)}")
            return True, f"Dry run: would create {bridge_name}"

        try:
            for cmd in commands:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Successfully created bridge {bridge_name}"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to create bridge {bridge_name}: {e.stderr}"
        except Exception as e:
            return False, f"Error creating bridge {bridge_name}: {e}"

    def delete_bridge(self, bridge_name, dry_run=False):
        """Delete a Linux bridge from the system."""
        if not self.check_bridge_exists(bridge_name):
            return True, f"Bridge {bridge_name} does not exist"

        commands = [
            ["ip", "link", "set", bridge_name, "down"],
            ["ip", "link", "delete", bridge_name],
        ]

        if dry_run:
            click.echo(f"Would delete bridge: {bridge_name}")
            for cmd in commands:
                click.echo(f"  Command: {' '.join(cmd)}")
            return True, f"Dry run: would delete {bridge_name}"

        try:
            for cmd in commands:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Successfully deleted bridge {bridge_name}"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to delete bridge {bridge_name}: {e.stderr}"
        except Exception as e:
            return False, f"Error deleting bridge {bridge_name}: {e}"

    def create_all_bridges(self, dry_run=False, force=False):
        """Create all missing bridges."""
        missing_bridges = self.get_missing_bridges()

        if not missing_bridges:
            return True, "All required bridges already exist"

        if not dry_run and not force:
            if not click.confirm(f"Create {len(missing_bridges)} bridges?"):
                return False, "Operation cancelled by user"

        success_count = 0
        messages = []

        for bridge in missing_bridges:
            success, message = self.create_bridge(bridge, dry_run)
            messages.append(message)
            if success:
                success_count += 1

        if dry_run:
            return True, f"Dry run: would create {len(missing_bridges)} bridges"
        else:
            return (
                success_count == len(missing_bridges)
            ), f"Created {success_count}/{len(missing_bridges)} bridges"

    def delete_all_bridges(self, dry_run=False, force=False):
        """Delete all existing bridges that match our pattern."""
        existing_bridges = self.get_existing_bridges()

        if not existing_bridges:
            return True, "No bridges found to delete"

        if not dry_run and not force:
            if not click.confirm(f"Delete {len(existing_bridges)} bridges?"):
                return False, "Operation cancelled by user"

        success_count = 0
        messages = []

        for bridge in existing_bridges:
            success, message = self.delete_bridge(bridge, dry_run)
            messages.append(message)
            if success:
                success_count += 1

        if dry_run:
            return True, f"Dry run: would delete {len(existing_bridges)} bridges"
        else:
            return (
                success_count == len(existing_bridges)
            ), f"Deleted {success_count}/{len(existing_bridges)} bridges"
