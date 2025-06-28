"""
Lab Commands

CLI commands for managing labs in the containerlab tools database.
Provides functionality to create, list, switch between, and delete labs.
"""

from typing import Optional

import click

from clab_tools.config.settings import get_settings
from clab_tools.errors.handlers import error_handler

from ..common.utils import handle_error, handle_success, with_lab_context
from ..db.context import get_lab_db


@click.group(name="lab")
def lab_commands():
    """Lab management commands."""
    pass


@lab_commands.command()
@click.option("--description", "-d", default=None, help="Description for the new lab")
@click.argument("lab_name")
@click.pass_context
@with_lab_context
@error_handler()
def create(ctx, lab_name: str, description: Optional[str]):
    """Create a new lab."""
    db = get_lab_db(ctx.obj)

    db.get_or_create_lab(lab_name, description)

    handle_success(f"Lab '{lab_name}' created successfully")
    if description:
        click.echo(f"  Description: {description}")

    # Ask if user wants to switch to this lab
    if click.confirm(f"Switch to lab '{lab_name}'?", default=True):
        settings = get_settings()
        settings.lab.current_lab = lab_name
        ctx.obj["current_lab"] = lab_name
        handle_success(f"Switched to lab '{lab_name}'")


@lab_commands.command()
@click.pass_context
@with_lab_context
@error_handler()
def list(ctx):
    """List all labs."""
    db = get_lab_db(ctx.obj)
    settings = get_settings()

    labs = db.list_labs()

    if not labs:
        click.echo("No labs found.")
        return

    click.echo("Available labs:")
    click.echo()

    for lab in labs:
        # Get lab statistics
        stats = db.get_lab_stats(lab.name)

        # Mark current lab
        marker = "→ " if lab.name == settings.lab.current_lab else "  "

        click.echo(f"{marker}{lab.name}")

        if lab.description:
            click.echo(f"    Description: {lab.description}")

        click.echo(
            f"    Nodes: {stats.get('nodes', 0)}, "
            f"Connections: {stats.get('connections', 0)}, "
            f"Topologies: {stats.get('topologies', 0)}"
        )

        if lab.created_at:
            click.echo(f"    Created: {lab.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        click.echo()


@lab_commands.command()
@click.argument("lab_name")
@click.pass_context
@with_lab_context
@error_handler()
def switch(ctx, lab_name: str):
    """Switch to a different lab."""
    db = get_lab_db(ctx.obj)
    settings = get_settings()

    # Verify lab exists (this will create it if auto_create_lab is True)
    db.get_or_create_lab(lab_name)

    # Update current lab setting
    settings.lab.current_lab = lab_name
    ctx.obj["current_lab"] = lab_name

    handle_success(f"Switched to lab '{lab_name}'")

    # Show lab stats
    stats = db.get_lab_stats(lab_name)
    click.echo(
        f"  Nodes: {stats.get('nodes', 0)}, "
        f"Connections: {stats.get('connections', 0)}, "
        f"Topologies: {stats.get('topologies', 0)}"
    )


@lab_commands.command()
@click.argument("lab_name")
@click.option("--force", "-f", is_flag=True, help="Force deletion without confirmation")
@click.pass_context
@with_lab_context
@error_handler()
def delete(ctx, lab_name: str, force: bool):
    """Delete a lab and all its data."""
    db = get_lab_db(ctx.obj)
    settings = get_settings()

    # Check if lab exists
    labs = db.list_labs()
    lab_names = [lab.name for lab in labs]

    if lab_name not in lab_names:
        handle_error(f"Lab '{lab_name}' not found")
        return

    # Prevent deletion of current lab without confirmation
    if lab_name == settings.lab.current_lab and not force:
        click.echo(f"⚠ '{lab_name}' is the current active lab", err=True)
        if not click.confirm("Are you sure you want to delete the current lab?"):
            click.echo("Deletion cancelled")
            return

    # Get lab stats before deletion
    stats = db.get_lab_stats(lab_name)

    if not force:
        click.echo(f"This will permanently delete lab '{lab_name}' and all its data:")
        click.echo(f"  • {stats.get('nodes', 0)} nodes")
        click.echo(f"  • {stats.get('connections', 0)} connections")
        click.echo(f"  • {stats.get('topologies', 0)} topology configurations")

        if not click.confirm("Are you sure you want to continue?"):
            click.echo("Deletion cancelled")
            return

    # Delete the lab
    if db.delete_lab(lab_name):
        handle_success(f"Lab '{lab_name}' deleted successfully")

        # Switch to default lab if we deleted the current lab
        if lab_name == settings.lab.current_lab:
            settings.lab.current_lab = "default"
            ctx.obj["current_lab"] = "default"
            handle_success("Switched to 'default' lab")
    else:
        handle_error(f"Failed to delete lab '{lab_name}'")


@lab_commands.command()
@click.pass_context
@with_lab_context
@error_handler()
def current(ctx):
    """Show current lab information."""
    db = get_lab_db(ctx.obj)
    current_lab = db.get_current_lab()

    click.echo(f"Current lab: {current_lab}")

    # Get lab details
    stats = db.get_lab_stats(current_lab)

    if "error" in stats:
        handle_error(stats["error"])
        return

    click.echo(f"  Nodes: {stats.get('nodes', 0)}")
    click.echo(f"  Connections: {stats.get('connections', 0)}")
    click.echo(f"  Topology configurations: {stats.get('topologies', 0)}")

    # Get lab object for additional details
    labs = db.list_labs()
    current_lab_obj = next((lab for lab in labs if lab.name == current_lab), None)

    if current_lab_obj:
        if current_lab_obj.description:
            click.echo(f"  Description: {current_lab_obj.description}")
        if current_lab_obj.created_at:
            click.echo(
                f"  Created: {current_lab_obj.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )


# Export the command group
__all__ = ["lab_commands"]
