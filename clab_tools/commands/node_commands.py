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
from ..node.command_manager import CommandManager
from ..node.config_manager import ConfigManager
from ..node.drivers.base import ConfigFormat, ConfigLoadMethod
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


@node_commands.command(name="exec")
@click.option("-c", "--command", required=True, help="Command to execute on nodes")
@click.option("--node", help="Execute on specific node")
@click.option("--kind", help="Execute on all nodes of specific kind")
@click.option("--nodes", help="Execute on comma-separated list of nodes")
@click.option(
    "--all", "all_nodes", is_flag=True, help="Execute on all nodes in current lab"
)
@click.option("--timeout", type=int, default=30, help="Command timeout in seconds")
@click.option(
    "--parallel/--sequential",
    default=True,
    help="Execute commands in parallel or sequentially",
)
@click.option("--max-workers", type=int, default=10, help="Maximum parallel workers")
@click.option(
    "--output-format",
    type=click.Choice(["text", "table", "json"]),
    default="text",
    help="Output format for results",
)
@click.pass_context
@with_lab_context
def exec_command(
    ctx,
    command,
    node,
    kind,
    nodes,
    all_nodes,
    timeout,
    parallel,
    max_workers,
    output_format,
):
    """
    Execute commands on containerlab nodes.

    Execute operational commands on containerlab nodes using their management
    interfaces. Supports parallel execution across multiple nodes with
    various output formats.

    Examples:
    \b
        # Execute on specific node
        clab-tools node exec -c "show ospf neighbor" --node router1

        # Execute on all Juniper nodes
        clab-tools node exec -c "show version" --kind juniper_vjunosrouter

        # Execute on specific nodes with JSON output
        clab-tools node exec -c "show interfaces terse" --nodes router1,router2 \
            --output-format json

        # Execute on all nodes sequentially
        clab-tools node exec -c "show system uptime" --all --sequential
    """
    db = get_lab_db(ctx.obj)
    quiet = ctx.obj.get("quiet", False)

    # Validate input arguments
    selection_count = sum([bool(node), bool(kind), bool(nodes), all_nodes])
    if selection_count != 1:
        handle_error("Must specify exactly one of: --node, --kind, --nodes, or --all")
        return

    # Get target nodes
    target_nodes = []

    if node:
        target_node = db.get_node_by_name(node)
        if not target_node:
            handle_error(f"Node '{node}' not found")
            return
        target_nodes = [target_node]

    elif kind:
        target_nodes = db.get_nodes_by_kind(kind)
        if not target_nodes:
            handle_error(f"No nodes found with kind '{kind}'")
            return

    elif nodes:
        nodes_list = [n.strip() for n in nodes.split(",")]
        for node_name in nodes_list:
            target_node = db.get_node_by_name(node_name)
            if not target_node:
                handle_error(f"Node '{node_name}' not found")
                return
            target_nodes.append(target_node)

    elif all_nodes:
        all_nodes_list = db.get_all_nodes()
        if not all_nodes_list:
            handle_error("No nodes found in current lab")
            return

        # Filter out bridge nodes from --all execution
        target_nodes = [
            n
            for n in all_nodes_list
            if not n.kind.startswith("bridge") and not n.name.startswith("br-")
        ]

        if not target_nodes:
            handle_error("No executable nodes found (bridges are skipped)")
            return

        # Log how many nodes were skipped if any
        skipped_count = len(all_nodes_list) - len(target_nodes)
        if skipped_count > 0 and not quiet:
            click.echo(f"Skipping {skipped_count} bridge node(s)")

    # Initialize command manager
    cmd_manager = CommandManager(quiet=quiet)

    try:
        # Execute commands
        results = cmd_manager.execute_command(
            nodes=target_nodes,
            command=command,
            timeout=timeout,
            parallel=parallel,
            max_workers=max_workers,
        )

        # Format and display results
        output = cmd_manager.format_results(results, output_format)
        click.echo(output)

        # Print summary
        cmd_manager.print_summary(results)

        # Exit with error if any commands failed
        if any(r.exit_code != 0 for r in results):
            sys.exit(1)

    except Exception as e:
        handle_error(f"Command execution failed: {e}")


@node_commands.command(name="config")
@click.option(
    "-f",
    "--file",
    type=click.Path(exists=True, path_type=Path),
    help="Local configuration file to load",
)
@click.option("-d", "--device-file", help="Configuration file path on device")
@click.option("--node", help="Configure specific node")
@click.option("--kind", help="Configure all nodes of specific kind")
@click.option("--nodes", help="Configure comma-separated list of nodes")
@click.option(
    "--all", "all_nodes", is_flag=True, help="Configure all nodes in current lab"
)
@click.option(
    "--format",
    type=click.Choice(["text", "set", "xml", "json"]),
    default="text",
    help="Configuration format (for --file only)",
)
@click.option(
    "--method",
    type=click.Choice(["merge", "override", "replace"]),
    default="merge",
    help="Configuration load method",
)
@click.option("--dry-run", is_flag=True, help="Validate configuration without applying")
@click.option("--comment", help="Commit comment")
@click.option(
    "--parallel/--sequential",
    default=True,
    help="Load configurations in parallel or sequentially",
)
@click.option("--max-workers", type=int, default=5, help="Maximum parallel workers")
@click.option(
    "--output-format",
    type=click.Choice(["text", "table", "json"]),
    default="text",
    help="Output format for results",
)
@click.option("--show-diff/--no-diff", default=True, help="Show configuration diff")
@click.pass_context
@with_lab_context
def config_command(
    ctx,
    file,
    device_file,
    node,
    kind,
    nodes,
    all_nodes,
    format,
    method,
    dry_run,
    comment,
    parallel,
    max_workers,
    output_format,
    show_diff,
):
    """
    Load configurations to containerlab nodes.

    Load configuration from local files or device files to containerlab nodes.
    Supports dry-run mode for validation, multiple load methods, and various
    configuration formats.

    Examples:
    \b
        # Load config from local file to specific node
        clab-tools node config -f router.conf --node router1

        # Load from device file to all Juniper nodes
        clab-tools node config -d /tmp/config.txt --kind juniper_vjunosrouter

        # Dry-run with diff display
        clab-tools node config -f config.set --node router1 --format set --dry-run

        # Replace configuration on multiple nodes
        clab-tools node config -f baseline.conf --nodes router1,router2 \
            --method replace --comment "Baseline configuration"
    """
    db = get_lab_db(ctx.obj)
    quiet = ctx.obj.get("quiet", False)

    # Validate input arguments
    if not file and not device_file:
        handle_error("Must specify either --file or --device-file")
        return

    if file and device_file:
        handle_error("Cannot specify both --file and --device-file")
        return

    selection_count = sum([bool(node), bool(kind), bool(nodes), all_nodes])
    if selection_count != 1:
        handle_error("Must specify exactly one of: --node, --kind, --nodes, or --all")
        return

    # Get target nodes
    target_nodes = []

    if node:
        target_node = db.get_node_by_name(node)
        if not target_node:
            handle_error(f"Node '{node}' not found")
            return
        target_nodes = [target_node]

    elif kind:
        target_nodes = db.get_nodes_by_kind(kind)
        if not target_nodes:
            handle_error(f"No nodes found with kind '{kind}'")
            return

    elif nodes:
        nodes_list = [n.strip() for n in nodes.split(",")]
        for node_name in nodes_list:
            target_node = db.get_node_by_name(node_name)
            if not target_node:
                handle_error(f"Node '{node_name}' not found")
                return
            target_nodes.append(target_node)

    elif all_nodes:
        all_nodes_list = db.get_all_nodes()
        if not all_nodes_list:
            handle_error("No nodes found in current lab")
            return

        # Filter out bridge nodes from --all execution
        target_nodes = [
            n
            for n in all_nodes_list
            if not n.kind.startswith("bridge") and not n.name.startswith("br-")
        ]

        if not target_nodes:
            handle_error("No configurable nodes found (bridges are skipped)")
            return

        # Log how many nodes were skipped if any
        skipped_count = len(all_nodes_list) - len(target_nodes)
        if skipped_count > 0 and not quiet:
            click.echo(f"Skipping {skipped_count} bridge node(s)")

    # Initialize config manager
    config_manager = ConfigManager(quiet=quiet)

    # Convert format and method strings to enums
    config_format = ConfigFormat(format)
    load_method = ConfigLoadMethod(method)

    try:
        # Load configurations
        if file:
            results = config_manager.load_config_from_file(
                nodes=target_nodes,
                file_path=file,
                format=config_format,
                method=load_method,
                dry_run=dry_run,
                commit_comment=comment,
                parallel=parallel,
                max_workers=max_workers,
            )
        else:
            results = config_manager.load_config_from_device(
                nodes=target_nodes,
                device_file_path=device_file,
                format=config_format,
                method=load_method,
                dry_run=dry_run,
                commit_comment=comment,
                parallel=parallel,
                max_workers=max_workers,
            )

        # Format and display results
        output = config_manager.format_results(results, output_format, show_diff)
        click.echo(output)

        # Print summary
        config_manager.print_summary(results)

        # Exit with error if any configurations failed
        if any(not r.success for r in results):
            sys.exit(1)

    except FileNotFoundError as e:
        handle_error(str(e))
    except Exception as e:
        handle_error(f"Configuration operation failed: {e}")


# Export the command group
__all__ = ["node_commands"]
