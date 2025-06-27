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

    def create_bridge(self, bridge_name, dry_run=False, **options):
        """Create a Linux bridge with configurable options.

        Args:
            bridge_name: Name of the bridge to create
            dry_run: If True, only show what would be done
            **options: Bridge creation options:
                - vlan_filtering: Enable VLAN filtering (default: True)
                - stp: Enable spanning tree protocol (default: False)
                - interfaces: List of interfaces to add to bridge
                - vid_range: VLAN ID range to add (default: "1-4094")

        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.check_bridge_exists(bridge_name):
            return True, f"Bridge {bridge_name} already exists"

        # Parse options with defaults
        vlan_filtering = options.get("vlan_filtering", True)
        stp = options.get("stp", False)
        interfaces = options.get("interfaces", [])
        vid_range = options.get("vid_range", "1-4094")

        commands = []

        # Create bridge command
        bridge_cmd = ["ip", "link", "add", "name", bridge_name, "type", "bridge"]
        if vlan_filtering:
            bridge_cmd.extend(["vlan_filtering", "1"])
        commands.append(self._build_command(bridge_cmd))

        # Bring bridge up
        commands.append(self._build_command(["ip", "link", "set", bridge_name, "up"]))

        # Configure spanning tree if requested
        if not stp:
            commands.append(
                self._build_command(
                    [
                        "ip",
                        "link",
                        "set",
                        bridge_name,
                        "type",
                        "bridge",
                        "stp_state",
                        "0",
                    ]
                )
            )

        # Add VLANs if VLAN filtering is enabled
        if vlan_filtering and vid_range:
            commands.append(
                self._build_command(
                    [
                        "bridge",
                        "vlan",
                        "add",
                        "vid",
                        vid_range,
                        "dev",
                        bridge_name,
                        "self",
                    ]
                )
            )

        # Add interfaces if specified
        for interface in interfaces:
            commands.append(
                self._build_command(
                    ["ip", "link", "set", interface, "master", bridge_name]
                )
            )

        location = (
            "remote host"
            if self.remote_manager and self.remote_manager.is_connected()
            else "local system"
        )

        if dry_run:
            click.echo(f"Would create bridge on {location}: {bridge_name}")
            click.echo(f"  VLAN filtering: {vlan_filtering}")
            click.echo(f"  Spanning Tree: {stp}")
            if interfaces:
                click.echo(f"  Interfaces: {', '.join(interfaces)}")
            if vlan_filtering and vid_range:
                click.echo(f"  VLAN range: {vid_range}")
            for cmd in commands:
                click.echo(f"  Command: {' '.join(cmd)}")
            return (
                True,
                f"Dry run: would create bridge {bridge_name} on {location}",
            )

        try:
            for cmd in commands:
                self._execute_command(cmd, capture_output=True, text=True, check=True)

            # Build feature description
            features = []
            if vlan_filtering:
                features.append(f"VLAN filtering ({vid_range})")
            if not stp:
                features.append("STP disabled")
            if interfaces:
                features.append(f"{len(interfaces)} interfaces")

            feature_str = f" ({', '.join(features)})" if features else ""
            return (
                True,
                f"Successfully created bridge {bridge_name} on {location}{feature_str}",
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

    def create_topology_bridges(self, dry_run=False, force=False):
        """Create all bridges from topology (current behavior)."""
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

    def create_bridge_from_spec(self, spec, dry_run=False):
        """Create bridge from specification (for extensibility).

        Args:
            spec: Dictionary containing bridge specification:
                - name: Bridge name (required)
                - vlan_filtering: Enable VLAN filtering (optional, default: True)
                - stp: Enable spanning tree protocol (optional, default: False)
                - interfaces: List of interfaces to add (optional)
                - vid_range: VLAN ID range (optional, default: "1-4094")
            dry_run: If True, only show what would be done

        Returns:
            Tuple of (success: bool, message: str)
        """
        if "name" not in spec:
            return False, "Bridge specification must include 'name'"

        bridge_name = spec["name"]
        options = {k: v for k, v in spec.items() if k != "name"}

        return self.create_bridge(bridge_name, dry_run=dry_run, **options)

    # Maintain backward compatibility
    def create_all_bridges(self, dry_run=False, force=False):
        """Legacy method - delegates to create_topology_bridges."""
        return self.create_topology_bridges(dry_run=dry_run, force=force)

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

    def configure_bridge_vlans(self, bridge_name, dry_run=False):
        """Configure VLANs on all ports of an existing bridge.

        This method should be called after containerlab has created and connected
        interfaces to the bridge to ensure VLAN traffic can flow properly.

        Args:
            bridge_name: Name of the bridge to configure
            dry_run: If True, only show what would be done

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.check_bridge_exists(bridge_name):
            return False, f"Bridge {bridge_name} does not exist"

        location = (
            "remote host"
            if self.remote_manager and self.remote_manager.is_connected()
            else "local system"
        )

        # Get list of bridge ports
        try:
            cmd = self._build_command(["bridge", "link", "show", "master", bridge_name])
            result = self._execute_command(
                cmd, capture_output=True, text=True, check=True
            )

            # Parse the output to get interface names
            # Output format: "2: eth401@if3: <BROADCAST,MULTICAST,UP,LOWER_UP>
            # mtu 9500 master br-allvlans-1"
            ports = []
            for line in result.stdout.strip().split("\n"):
                if line and "master" in line and bridge_name in line:
                    # Extract interface name (before the '@' or ':')
                    parts = line.split(":")
                    if len(parts) >= 2:
                        interface = parts[1].strip()
                        if "@" in interface:
                            interface = interface.split("@")[0]
                        ports.append(interface)

            if not ports:
                return True, f"No ports found on bridge {bridge_name}"

            # Configure VLANs on each port
            commands = []
            for port in ports:
                # Add all VLANs 1-4094 to this port
                commands.append(
                    self._build_command(
                        ["bridge", "vlan", "add", "vid", "1-4094", "dev", port]
                    )
                )

            if dry_run:
                click.echo(
                    f"Would configure VLANs on {len(ports)} ports of bridge "
                    f"{bridge_name} on {location}"
                )
                for i, port in enumerate(ports):
                    click.echo(f"  Port {i+1}: {port}")
                    click.echo(f"    Command: {' '.join(commands[i])}")
                return True, f"Dry run: would configure VLANs on {len(ports)} ports"

            # Execute commands
            success_count = 0
            for i, cmd in enumerate(commands):
                try:
                    self._execute_command(
                        cmd, capture_output=True, text=True, check=True
                    )
                    success_count += 1
                    click.echo(f"✓ Configured VLANs on port {ports[i]}")
                except Exception as e:
                    click.echo(f"✗ Failed to configure VLANs on port {ports[i]}: {e}")

            if success_count == len(commands):
                return (
                    True,
                    f"Successfully configured VLANs on {success_count}/"
                    f"{len(ports)} ports of {bridge_name}",
                )
            else:
                return (
                    False,
                    f"Configured VLANs on {success_count}/{len(ports)} ports. "
                    f"Some failed.",
                )
        except Exception as e:
            return False, f"Failed to configure bridge VLANs: {e}"

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
