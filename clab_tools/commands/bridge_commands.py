"""
Bridge Commands

Handles creating and managing Linux bridges on the host system or remote hosts.
Multi-lab aware implementation.
"""

import click

from ..bridges.manager import BridgeManager
from ..db.context import LabAwareDB
from ..remote import get_remote_host_manager


def create_bridges_command(db_manager, lab_name, dry_run, force):
    """
    Create Linux bridges on the host system based on database connections.

    Args:
        db_manager: Database manager instance
        lab_name: Name of the lab context
        dry_run: Whether to show what would be done without making changes
        force: Whether to proceed without confirmation prompts
    """
    # Get remote host manager if configured
    remote_manager = get_remote_host_manager()

    with LabAwareDB(db_manager, lab_name) as lab_db:
        if remote_manager:
            with remote_manager:
                bridge_manager = BridgeManager(lab_db, remote_manager)
                _execute_bridge_creation(bridge_manager, dry_run, force, remote=True)
        else:
            bridge_manager = BridgeManager(lab_db)
            _execute_bridge_creation(bridge_manager, dry_run, force, remote=False)


def _execute_bridge_creation(bridge_manager, dry_run, force, remote=False):
    """Execute bridge creation with given manager."""
    location = "remote host" if remote else "local system"
    click.echo(f"=== Bridge Creation ({location}) ===")

    # Get list of required bridges
    required_bridges = bridge_manager.get_bridge_list_from_db()

    if not required_bridges:
        click.echo("No bridge connections found in database.")
        return

    click.echo(f"Found {len(required_bridges)} bridges required by topology:")
    for bridge in required_bridges:
        exists = bridge_manager.check_bridge_exists(bridge)
        status = "EXISTS" if exists else "MISSING"
        click.echo(f"  - {bridge} [{status}]")

    # Filter to only bridges that don't exist
    missing_bridges = bridge_manager.get_missing_bridges()

    if not missing_bridges:
        click.echo(f"✓ All required bridges already exist on {location}!")
        return

    click.echo(f"\nNeed to create {len(missing_bridges)} bridges on {location}:")
    for bridge in missing_bridges:
        click.echo(f"  - {bridge}")

    if not dry_run and not force:
        if not click.confirm(f"Create {len(missing_bridges)} bridges on {location}?"):
            click.echo("Bridge creation cancelled.")
            return

    # Create bridges
    success, message = bridge_manager.create_all_bridges(dry_run=dry_run, force=True)

    if success:
        click.echo(f"✓ {message}")
    else:
        click.echo(f"✗ {message}")


def delete_bridges_command(db_manager, lab_name, dry_run, force):
    """
    Delete Linux bridges from the system.

    Args:
        db_manager: Database manager instance
        lab_name: Name of the lab context
        dry_run: Whether to show what would be done without making changes
        force: Whether to proceed without confirmation prompts
    """
    # Get remote host manager if configured
    remote_manager = get_remote_host_manager()

    with LabAwareDB(db_manager, lab_name) as lab_db:
        if remote_manager:
            with remote_manager:
                bridge_manager = BridgeManager(lab_db, remote_manager)
                _execute_bridge_deletion(bridge_manager, dry_run, force, remote=True)
        else:
            bridge_manager = BridgeManager(lab_db)
            _execute_bridge_deletion(bridge_manager, dry_run, force, remote=False)


def _execute_bridge_deletion(bridge_manager, dry_run, force, remote=False):
    """Execute bridge deletion with given manager."""
    location = "remote host" if remote else "local system"
    click.echo(f"=== Bridge Deletion ({location}) ===")

    # Get list of existing bridges
    existing_bridges = bridge_manager.get_existing_bridges()

    if not existing_bridges:
        click.echo(f"No bridges found on {location}.")
        return

    click.echo(f"Found {len(existing_bridges)} bridges on {location}:")
    for bridge in existing_bridges:
        click.echo(f"  - {bridge}")

    if not dry_run and not force:
        if not click.confirm(
            f"Delete {len(existing_bridges)} bridges from {location}?"
        ):
            click.echo("Bridge deletion cancelled.")
            return

    # Delete bridges
    success, message = bridge_manager.delete_all_bridges(dry_run=dry_run, force=True)

    if success:
        click.echo(f"✓ {message}")
    else:
        click.echo(f"✗ {message}")


def list_bridges_command(db_manager, lab_name):
    """
    List bridge status on the system.

    Args:
        db_manager: Database manager instance
        lab_name: Name of the lab context
    """
    # Get remote host manager if configured
    remote_manager = get_remote_host_manager()

    with LabAwareDB(db_manager, lab_name) as lab_db:
        if remote_manager:
            with remote_manager:
                bridge_manager = BridgeManager(lab_db, remote_manager)
                _execute_bridge_listing(bridge_manager, remote=True)
        else:
            bridge_manager = BridgeManager(lab_db)
            _execute_bridge_listing(bridge_manager, remote=False)


def _execute_bridge_listing(bridge_manager, remote=False):
    """Execute bridge listing with given manager."""
    location = "remote host" if remote else "local system"
    click.echo(f"=== Bridge Status ({location}) ===")

    # Get required bridges from database
    required_bridges = bridge_manager.get_bridge_list_from_db()
    existing_bridges = bridge_manager.get_existing_bridges()
    missing_bridges = bridge_manager.get_missing_bridges()

    if not required_bridges:
        click.echo("No bridge connections found in topology database.")
        return

    click.echo(f"\nRequired bridges: {len(required_bridges)}")
    click.echo(f"Existing bridges: {len(existing_bridges)}")
    click.echo(f"Missing bridges: {len(missing_bridges)}")

    if required_bridges:
        click.echo(f"\nBridge Status on {location}:")
        for bridge in required_bridges:
            exists = bridge_manager.check_bridge_exists(bridge)
            status = "✓" if exists else "✗"
            state = "EXISTS" if exists else "MISSING"
            click.echo(f"  {status} {bridge} [{state}]")

    if missing_bridges:
        click.echo("\nMissing bridges that need to be created:")
        for bridge in missing_bridges:
            click.echo(f"  - {bridge}")
    else:
        click.echo("\n✓ All required bridges exist on {}".format(location))


def configure_vlans_command(db_manager, lab_name, bridge_name, dry_run):
    """
    Configure VLANs on bridge interfaces.

    Args:
        db_manager: Database manager instance
        lab_name: Name of the lab context
        bridge_name: Name of the bridge to configure VLANs on (or None for all bridges)
        dry_run: Whether to show what would be done without making changes
    """
    # Get remote host manager if configured
    remote_manager = get_remote_host_manager()

    with LabAwareDB(db_manager, lab_name) as lab_db:
        if remote_manager:
            with remote_manager:
                bridge_manager = BridgeManager(lab_db, remote_manager)
                _execute_vlan_configuration(
                    bridge_manager, bridge_name, dry_run, remote=True
                )
        else:
            bridge_manager = BridgeManager(lab_db)
            _execute_vlan_configuration(
                bridge_manager, bridge_name, dry_run, remote=False
            )


def _execute_vlan_configuration(bridge_manager, bridge_name, dry_run, remote=False):
    """Execute VLAN configuration with given manager."""
    location = "remote host" if remote else "local system"
    click.echo(f"=== VLAN Configuration ({location}) ===")

    # Determine which bridges to configure
    if bridge_name:
        target_bridges = [bridge_name]
        click.echo(f"Configuring VLANs on bridge: {bridge_name}")
    else:
        # Get all required bridges from database
        target_bridges = bridge_manager.get_bridge_list_from_db()
        if not target_bridges:
            click.echo("No bridge connections found in database.")
            return
        click.echo(f"Configuring VLANs on {len(target_bridges)} bridges from topology")

    # Configure VLANs on each bridge
    success_count = 0
    for bridge in target_bridges:
        click.echo(f"\n--- Configuring VLANs on bridge: {bridge} ---")

        # Check if bridge exists first
        if not bridge_manager.check_bridge_exists(bridge):
            click.echo(f"⚠ Bridge {bridge} does not exist - skipping")
            continue

        success, message = bridge_manager.configure_bridge_vlans(bridge, dry_run)

        if success:
            click.echo(f"✓ {message}")
            success_count += 1
        else:
            click.echo(f"✗ {message}")

    # Summary
    click.echo("\n=== VLAN Configuration Summary ===")
    if dry_run:
        click.echo(f"Dry run: would configure VLANs on {len(target_bridges)} bridges")
    else:
        click.echo(
            f"Successfully configured VLANs on "
            f"{success_count}/{len(target_bridges)} bridges"
        )


@click.command()
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option("--force", is_flag=True, help="Proceed without confirmation prompts")
@click.pass_context
def create_bridges(ctx, dry_run, force):
    """
    Create Linux bridges on the host system based on database connections.

    This command will create all bridges required by the topology stored in
    the database. Requires root privileges to create network interfaces.
    Supports both local and remote host operations.
    """
    db_manager = ctx.obj["db_manager"]
    lab_name = ctx.obj["lab_name"]
    create_bridges_command(db_manager, lab_name, dry_run, force)


@click.command()
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option("--force", is_flag=True, help="Proceed without confirmation prompts")
@click.pass_context
def delete_bridges(ctx, dry_run, force):
    """
    Delete Linux bridges from the system.

    This command will remove bridges that are tracked in the database.
    Use with caution - removes bridges based on topology data.
    Supports both local and remote host operations.
    """
    db_manager = ctx.obj["db_manager"]
    lab_name = ctx.obj["lab_name"]
    delete_bridges_command(db_manager, lab_name, dry_run, force)


@click.command()
@click.pass_context
def list_bridges(ctx):
    """
    List bridge status on the system.

    This command shows the status of bridges required by the topology
    and indicates which ones exist and which are missing.
    Supports both local and remote host operations.
    """
    db_manager = ctx.obj["db_manager"]
    lab_name = ctx.obj["lab_name"]
    list_bridges_command(db_manager, lab_name)


@click.command()
@click.option(
    "--bridge",
    help="Name of specific bridge to configure VLANs on "
    "(default: all bridges from topology)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.pass_context
def configure_vlans(ctx, bridge, dry_run):
    """
    Configure VLANs on bridge interfaces.

    This command configures VLAN forwarding on all ports of Linux bridges
    to ensure VLAN traffic can flow properly. It should be run after
    containerlab has created and connected interfaces to bridges.

    By default, configures VLANs on all bridges found in the topology.
    Use --bridge to target a specific bridge.

    Supports both local and remote host operations.
    """
    db_manager = ctx.obj["db_manager"]
    lab_name = ctx.obj["lab_name"]
    configure_vlans_command(db_manager, lab_name, bridge, dry_run)


# Legacy command names for backward compatibility
cleanup_bridges = delete_bridges
