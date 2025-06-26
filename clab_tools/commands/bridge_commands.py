"""
Bridge Commands

Handles creating and managing Linux bridges on the host system.
"""

import click

from ..bridges.manager import BridgeManager


def create_bridges_command(db_manager, dry_run, force):
    """
    Create Linux bridges on the host system based on database connections.

    Args:
        db_manager: Database manager instance
        dry_run: Whether to show what would be done without making changes
        force: Whether to proceed without confirmation prompts
    """
    bridge_manager = BridgeManager(db_manager)

    click.echo("=== Bridge Creation ===")

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
        click.echo("✓ All required bridges already exist!")
        return

    click.echo(f"\nNeed to create {len(missing_bridges)} bridges:")
    for bridge in missing_bridges:
        click.echo(f"  - {bridge}")

    if not dry_run and not force:
        if not click.confirm(
            f"\nProceed with creating {len(missing_bridges)} bridges?"
        ):
            click.echo("Aborted.")
            return

    if dry_run:
        click.echo("\n=== DRY RUN MODE ===")

    # Create missing bridges
    success_count = 0
    for bridge in missing_bridges:
        success, message = bridge_manager.create_bridge(bridge, dry_run)
        if success:
            click.echo(f"✓ {message}")
            success_count += 1
        else:
            click.echo(f"✗ {message}")

    if not dry_run:
        click.echo("\n=== Creation Complete ===")
        click.echo(
            f"Successfully created {success_count}/{len(missing_bridges)} bridges"
        )
        if success_count < len(missing_bridges):
            click.echo(
                "Some bridges failed to create. Check permissions and try again."
            )


def cleanup_bridges_command(db_manager, dry_run, force):
    """
    Remove Linux bridges created by this tool.

    Args:
        db_manager: Database manager instance
        dry_run: Whether to show what would be done without making changes
        force: Whether to proceed without confirmation prompts
    """
    bridge_manager = BridgeManager(db_manager)

    click.echo("=== Bridge Cleanup ===")

    # Find existing bridges that match our pattern
    existing_bridges = bridge_manager.get_existing_bridges()

    if not existing_bridges:
        click.echo("No matching bridges found to remove.")
        return

    click.echo(f"Found {len(existing_bridges)} bridges to remove:")
    for bridge in existing_bridges:
        click.echo(f"  - {bridge}")

    if not dry_run and not force:
        if not click.confirm(
            f"\nProceed with removing {len(existing_bridges)} bridges?"
        ):
            click.echo("Aborted.")
            return

    if dry_run:
        click.echo("\n=== DRY RUN MODE ===")

    # Remove bridges
    success_count = 0
    for bridge in existing_bridges:
        success, message = bridge_manager.delete_bridge(bridge, dry_run)
        if success:
            click.echo(f"✓ {message}")
            success_count += 1
        else:
            click.echo(f"✗ {message}")

    if not dry_run:
        click.echo("\n=== Cleanup Complete ===")
        click.echo(
            f"Successfully removed {success_count}/{len(existing_bridges)} bridges"
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
    """
    db_manager = ctx.obj["db_manager"]
    create_bridges_command(db_manager, dry_run, force)


@click.command()
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option("--force", is_flag=True, help="Proceed without confirmation prompts")
@click.pass_context
def cleanup_bridges(ctx, dry_run, force):
    """
    Remove Linux bridges created by this tool.

    This command will remove bridges that match the naming pattern used by this tool.
    Use with caution - only removes bridges matching br-* pattern.
    """
    db_manager = ctx.obj["db_manager"]
    cleanup_bridges_command(db_manager, dry_run, force)
