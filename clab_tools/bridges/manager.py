"""
Bridge Manager

Handles Linux bridge operations on the host system including creation,
deletion, and management of network bridges based on topology data.
Supports both local and remote bridge operations.
"""

import subprocess
from typing import Optional

import click

from clab_tools.remote import RemoteHostManager


class BridgeManager:
    """Manages Linux bridge operations on the host system or remote host."""

    def __init__(self, db_manager, remote_manager: Optional[RemoteHostManager] = None):
        self.db = db_manager
        self.remote_manager = remote_manager

    def get_bridge_list_from_db(self):
        """Get list of bridges that should exist based on bridge nodes in database."""
        bridges = set()

        # Get all nodes and find bridge types
        nodes = self.db.get_all_nodes()
        for name, kind, mgmt_ip in nodes:
            if kind == "bridge":
                bridges.add(name)

        return sorted(bridges)

    def _execute_command(self, command, capture_output=True, text=True, check=True):
        """Execute command locally or remotely based on configuration."""
        if self.remote_manager and self.remote_manager.is_connected():
            # Remote execution
            command_str = " ".join(command) if isinstance(command, list) else command
            try:
                exit_code, stdout, stderr = self.remote_manager.execute_command(
                    command_str, check=False
                )
                if check and exit_code != 0:
                    # Create a mock CalledProcessError for consistency
                    error = subprocess.CalledProcessError(exit_code, command_str)
                    error.stderr = stderr
                    raise error

                # Create a mock result object for consistency
                class MockResult:
                    def __init__(self, returncode, stdout, stderr):
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr

                return MockResult(exit_code, stdout, stderr)
            except Exception as e:
                if hasattr(e, "stderr"):
                    raise e
                # Convert to CalledProcessError for consistency
                error = subprocess.CalledProcessError(1, command_str)
                error.stderr = str(e)
                raise error
        else:
            # Local execution
            return subprocess.run(
                command, capture_output=capture_output, text=text, check=check
            )

    def check_bridge_exists(self, bridge_name):
        """Check if a Linux bridge exists on the system (local or remote)."""
        try:
            result = self._execute_command(
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
        """Create a VLAN-capable Linux bridge that supports VLANs 1-4094."""
        if self.check_bridge_exists(bridge_name):
            return True, f"Bridge {bridge_name} already exists"

        commands = [
            # Create bridge with VLAN filtering enabled
            self._build_command(
                [
                    "ip",
                    "link",
                    "add",
                    "name",
                    bridge_name,
                    "type",
                    "bridge",
                    "vlan_filtering",
                    "1",
                ]
            ),
            # Bring bridge up
            self._build_command(["ip", "link", "set", bridge_name, "up"]),
            # Add all VLANs 1-4094 to the bridge
            self._build_command(
                ["bridge", "vlan", "add", "vid", "1-4094", "dev", bridge_name, "self"]
            ),
        ]

        location = (
            "remote host"
            if self.remote_manager and self.remote_manager.is_connected()
            else "local system"
        )

        if dry_run:
            click.echo(f"Would create VLAN-capable bridge on {location}: {bridge_name}")
            for cmd in commands:
                click.echo(f"  Command: {' '.join(cmd)}")
            click.echo("Bridge will support VLANs 1-4094")
            return (
                True,
                f"Dry run: would create VLAN-capable {bridge_name} on {location}",
            )

        try:
            for cmd in commands:
                self._execute_command(cmd, capture_output=True, text=True, check=True)
            return (
                True,
                f"Successfully created VLAN-capable bridge {bridge_name} on {location} "
                f"(VLANs 1-4094)",
            )
        except subprocess.CalledProcessError as e:
            return (
                False,
                f"Failed to create bridge {bridge_name} on {location}: {e.stderr}",
            )
        except Exception as e:
            return False, f"Error creating bridge {bridge_name} on {location}: {e}"

    def delete_bridge(self, bridge_name, dry_run=False):
        """Delete a Linux bridge from the system."""
        if not self.check_bridge_exists(bridge_name):
            return True, f"Bridge {bridge_name} does not exist"

        commands = [
            self._build_command(["ip", "link", "set", bridge_name, "down"]),
            self._build_command(["ip", "link", "delete", bridge_name]),
        ]

        location = (
            "remote host"
            if self.remote_manager and self.remote_manager.is_connected()
            else "local system"
        )

        if dry_run:
            click.echo(f"Would delete bridge on {location}: {bridge_name}")
            for cmd in commands:
                click.echo(f"  Command: {' '.join(cmd)}")
            return True, f"Dry run: would delete {bridge_name} on {location}"

        try:
            for cmd in commands:
                self._execute_command(cmd, capture_output=True, text=True, check=True)
            return True, f"Successfully deleted bridge {bridge_name} on {location}"
        except subprocess.CalledProcessError as e:
            return (
                False,
                f"Failed to delete bridge {bridge_name} on {location}: {e.stderr}",
            )
        except Exception as e:
            return False, f"Error deleting bridge {bridge_name} on {location}: {e}"

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
            else:
                # Log the specific error for debugging
                click.echo(f"  ✗ {message}")

        if dry_run:
            return True, f"Dry run: would create {len(missing_bridges)} bridges"
        else:
            if success_count == len(missing_bridges):
                return True, f"Created {success_count}/{len(missing_bridges)} bridges"
            else:
                return (
                    False,
                    f"Created {success_count}/{len(missing_bridges)} bridges. "
                    f"Check errors above for details.",
                )

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

    def _build_command(self, base_command):
        """
        Build a command with conditional sudo based on remote host settings.

        Args:
            base_command: List of command parts without sudo

        Returns:
            List of command parts with sudo prepended if needed
        """
        # If running locally, always use sudo (existing behavior)
        if not self.remote_manager or not self.remote_manager.is_connected():
            return ["sudo"] + base_command

        # If running remotely, check remote host settings
        if self.remote_manager.settings.use_sudo:
            return ["sudo"] + base_command
        else:
            return base_command
