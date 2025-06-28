"""
Lab Commands

CLI commands for managing labs in the containerlab tools database.
Provides functionality to create, list, switch between, and delete labs,
as well as bootstrap and teardown complete lab workflows.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from clab_tools.config.settings import get_settings
from clab_tools.errors.handlers import error_handler

from ..common.utils import handle_error, handle_success, with_lab_context
from ..db.context import get_lab_db
from ..remote import get_remote_host_manager


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

    # Ask if user wants to switch to this lab (unless in quiet mode)
    quiet = ctx.obj.get("quiet", False)
    if not quiet and click.confirm(f"Switch to lab '{lab_name}'?", default=True):
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

    # Save settings to persist the change
    if settings.save_to_file():
        handle_success(f"Switched to lab '{lab_name}'")
    else:
        handle_success(
            f"Switched to lab '{lab_name}' (warning: could not persist setting)"
        )

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

    quiet = ctx.obj.get("quiet", False)

    # Prevent deletion of current lab without confirmation
    if lab_name == settings.lab.current_lab and not force:
        click.echo(f"⚠ '{lab_name}' is the current active lab", err=True)
        if not quiet and not click.confirm(
            "Are you sure you want to delete the current lab?"
        ):
            click.echo("Deletion cancelled")
            return

    # Get lab stats before deletion
    stats = db.get_lab_stats(lab_name)

    if not force and not quiet:
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


@lab_commands.command()
@click.option(
    "--nodes",
    "-n",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Nodes CSV file",
)
@click.option(
    "--connections",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Connections CSV file",
)
@click.option("--output", "-o", required=True, help="Output topology file name")
@click.option("--no-start", is_flag=True, help="Skip starting the topology")
@click.option("--skip-vlans", is_flag=True, help="Skip VLAN configuration")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.pass_context
@with_lab_context
@error_handler()
def bootstrap(ctx, nodes, connections, output, no_start, skip_vlans, dry_run):
    """
    Bootstrap a complete lab from CSV files to running topology.

    This command performs the complete lab setup workflow:
    1. Import CSV data (clears existing data)
    2. Generate topology file with validation
    3. Upload topology to remote host (if configured)
    4. Create bridges
    5. Start containerlab topology
    6. Configure VLANs on bridge interfaces

    Use --dry-run to preview the actions without executing them.
    """
    db = get_lab_db(ctx.obj)
    settings = get_settings()
    quiet = ctx.obj.get("quiet", False)
    current_lab = db.get_current_lab()

    if not quiet:
        click.echo(f"=== Lab Bootstrap: '{current_lab}' ===")
        if dry_run:
            click.echo("DRY RUN - No changes will be made")
        click.echo()

    steps = [
        (
            "Import CSV data",
            f"clab-tools data import -n {nodes} -c {connections} --clear-existing",
        ),
        ("Generate topology", f"clab-tools topology generate -o {output} --validate"),
    ]

    # Add upload step if remote is configured
    remote_manager = get_remote_host_manager()
    if remote_manager and settings.remote.enabled:
        steps.append(("Upload topology", f"clab-tools remote upload-topology {output}"))

    steps.extend(
        [
            ("Create bridges", "clab-tools bridge create"),
        ]
    )

    if not no_start:
        steps.append(("Start topology", f"clab-tools topology start {output}"))

    if not skip_vlans:
        steps.append(("Configure VLANs", "clab-tools bridge configure"))

    # Execute steps
    failed_step = None
    for step_name, command in steps:
        if not quiet:
            click.echo(f"Step: {step_name}")
            click.echo(f"  Command: {command}")

        if dry_run:
            if not quiet:
                click.echo("  Status: [DRY RUN - SKIPPED]")
                click.echo()
            continue

        try:
            # Split command and execute
            cmd_parts = command.split()
            # Replace the first part with the actual module path for internal commands
            if cmd_parts[0] == "clab-tools":
                # Execute as internal command by calling the CLI
                from clab_tools.main import cli

                # Create a new context for the sub-command
                sub_ctx = click.Context(cli)
                sub_ctx.obj = ctx.obj.copy()

                # Remove 'clab-tools' from the command
                sub_args = cmd_parts[1:]

                # Execute the command
                result = cli.main(sub_args, standalone_mode=False, obj=sub_ctx.obj)

                if not quiet:
                    handle_success(f"Completed: {step_name}")
                    click.echo()
            else:
                # External command
                result = subprocess.run(
                    cmd_parts, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    if not quiet:
                        handle_success(f"Completed: {step_name}")
                        if result.stdout:
                            click.echo(result.stdout)
                        click.echo()
                else:
                    failed_step = step_name
                    handle_error(f"Failed: {step_name}")
                    if result.stderr:
                        click.echo(result.stderr, err=True)
                    break

        except Exception as e:
            failed_step = step_name
            handle_error(f"Failed: {step_name} - {e}")
            break

    # Summary
    if not quiet:
        click.echo("=== Bootstrap Summary ===")
        if dry_run:
            click.echo("Dry run completed - no changes made")
        elif failed_step:
            handle_error(f"Bootstrap failed at step: {failed_step}")
            sys.exit(1)
        else:
            handle_success(f"Lab '{current_lab}' bootstrap completed successfully!")
            click.echo(f"Topology file: {output}")
            if not no_start:
                click.echo("Topology is running")


@lab_commands.command()
@click.option("--topology", "-t", required=True, help="Topology file name")
@click.option(
    "--keep-data", is_flag=True, help="Keep database entries (don't clear data)"
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.pass_context
@with_lab_context
@error_handler()
def teardown(ctx, topology, keep_data, dry_run):
    """
    Teardown a complete lab environment.

    This command performs the complete lab cleanup workflow:
    1. Stop containerlab topology
    2. Remove bridges
    3. Clear database entries (optional)

    Use --keep-data to preserve database entries.
    Use --dry-run to preview the actions without executing them.
    """
    db = get_lab_db(ctx.obj)
    quiet = ctx.obj.get("quiet", False)
    current_lab = db.get_current_lab()

    if not quiet:
        click.echo(f"=== Lab Teardown: '{current_lab}' ===")
        if dry_run:
            click.echo("DRY RUN - No changes will be made")
        click.echo()

    steps = [
        ("Stop topology", f"clab-tools topology stop {topology}"),
        ("Remove bridges", "clab-tools bridge cleanup"),
    ]

    if not keep_data:
        steps.append(("Clear data", "clab-tools data clear --force"))

    # Execute steps
    for step_name, command in steps:
        if not quiet:
            click.echo(f"Step: {step_name}")
            click.echo(f"  Command: {command}")

        if dry_run:
            if not quiet:
                click.echo("  Status: [DRY RUN - SKIPPED]")
                click.echo()
            continue

        try:
            # Split command and execute
            cmd_parts = command.split()

            if cmd_parts[0] == "clab-tools":
                # Execute as internal command
                from clab_tools.main import cli

                # Create a new context for the sub-command
                sub_ctx = click.Context(cli)
                sub_ctx.obj = ctx.obj.copy()

                # Remove 'clab-tools' from the command
                sub_args = cmd_parts[1:]

                # Execute the command
                result = cli.main(sub_args, standalone_mode=False, obj=sub_ctx.obj)

                if not quiet:
                    handle_success(f"Completed: {step_name}")
                    click.echo()
            else:
                # External command
                result = subprocess.run(
                    cmd_parts, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    if not quiet:
                        handle_success(f"Completed: {step_name}")
                        if result.stdout:
                            click.echo(result.stdout)
                        click.echo()
                else:
                    # Don't fail teardown for individual step failures, just warn
                    if not quiet:
                        click.echo(f"⚠ Warning: {step_name} had issues", err=True)
                        if result.stderr:
                            click.echo(result.stderr, err=True)

        except Exception as e:
            # Don't fail teardown for individual step failures, just warn
            if not quiet:
                click.echo(f"⚠ Warning: {step_name} failed - {e}", err=True)

    # Summary
    if not quiet:
        click.echo("=== Teardown Summary ===")
        if dry_run:
            click.echo("Dry run completed - no changes made")
        else:
            handle_success(f"Lab '{current_lab}' teardown completed")
            if keep_data:
                click.echo("Database entries preserved")
            else:
                click.echo("Database entries cleared")


# Export the command group
__all__ = ["lab_commands"]
