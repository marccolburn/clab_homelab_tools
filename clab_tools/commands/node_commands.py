"""
Node Commands

CLI commands for managing individual containerlab nodes including file uploads.
"""

import sys
from pathlib import Path

import click

from ..common.utils import handle_error, handle_success, with_lab_context
from ..config.settings import get_settings
from ..db.context import get_lab_db
from ..node.manager import NodeConnectionError, NodeManager


@click.group(name="node")
def node_commands():
    """Node management commands."""
    pass


@node_commands.command()
@click.option("--node", help="Upload to specific node")
@click.option("--kind", help="Upload to all nodes of specific kind")
@click.option("--nodes", help="Upload to comma-separated list of nodes")
@click.option(
    "--all",
    "all_nodes",
    is_flag=True,
    help="Upload to all nodes in current lab",
)
@click.option(
    "--source",
    type=click.Path(exists=True, path_type=Path),
    help="Local file to upload",
)
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Local directory to upload (recursive)",
)
@click.option("--dest", required=True, help="Remote destination path")
@click.option("--user", help="SSH username (overrides default)")
@click.option("--password", help="SSH password (overrides default)")
@click.option(
    "--private-key",
    type=click.Path(exists=True, path_type=Path),
    help="SSH private key file (overrides default)",
)
@click.pass_context
@with_lab_context
def upload(
    ctx,
    node,
    kind,
    nodes,
    all_nodes,
    source,
    source_dir,
    dest,
    user,
    password,
    private_key,
):
    """
    Upload files or directories to containerlab nodes.

    Upload files directly to containerlab nodes using their management IP addresses.
    Supports uploading to individual nodes, nodes by kind, specific node lists,
    or all nodes.

    Examples:
    \b
        # Upload file to specific node
        clab-tools node upload --node router1 --source config.txt --dest /tmp/config.txt

        # Upload to all SRX nodes
        clab-tools node upload --kind srx --source config.txt --dest /tmp/config.txt

        # Upload to specific nodes
        clab-tools node upload --nodes router1,router2 --source config.txt \
            --dest /tmp/config.txt

        # Upload directory to all nodes
        clab-tools node upload --all --source-dir ./configs --dest /tmp/configs
    """
    settings = get_settings()
    db = get_lab_db(ctx.obj)
    quiet = ctx.obj.get("quiet", False)

    # Validate input arguments
    selection_count = sum([bool(node), bool(kind), bool(nodes), all_nodes])
    if selection_count != 1:
        handle_error("Must specify exactly one of: --node, --kind, --nodes, or --all")
        return

    source_count = sum([bool(source), bool(source_dir)])
    if source_count != 1:
        handle_error("Must specify exactly one of: --source or --source-dir")
        return

    # Determine source and if it's a directory
    local_source = source_dir if source_dir else source
    is_directory = bool(source_dir)

    # Parse nodes list if provided
    nodes_list = None
    if nodes:
        nodes_list = [n.strip() for n in nodes.split(",")]

    # Initialize node manager
    node_manager = NodeManager(settings.node)

    try:
        # Upload to nodes
        results = node_manager.upload_to_multiple_nodes(
            db=db,
            local_source=local_source,
            remote_dest=dest,
            node_name=node,
            kind=kind,
            nodes_list=nodes_list,
            all_nodes=all_nodes,
            is_directory=is_directory,
            username=user,
            password=password,
            private_key_path=str(private_key) if private_key else None,
        )

        # Report results
        successful_uploads = 0
        failed_uploads = 0

        for node_name, success, message in results:
            if success:
                successful_uploads += 1
                if not quiet:
                    handle_success(f"{node_name}: {message}")
            else:
                failed_uploads += 1
                handle_error(f"{node_name}: {message}", exit_code=0)

        # Summary
        if not quiet:
            total = successful_uploads + failed_uploads
            click.echo("\nUpload Summary:")
            click.echo(f"  Total nodes: {total}")
            click.echo(f"  Successful: {successful_uploads}")
            click.echo(f"  Failed: {failed_uploads}")

        # Exit with error code if any uploads failed
        if failed_uploads > 0:
            sys.exit(1)

    except ValueError as e:
        handle_error(str(e))
    except NodeConnectionError as e:
        handle_error(f"Connection error: {e}")
    except Exception as e:
        handle_error(f"Upload failed: {e}")


# Export the command group
__all__ = ["node_commands"]
