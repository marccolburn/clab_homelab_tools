"""
Topology Commands

Handles generating containerlab topology files, starting and stopping
containerlab topologies both locally and remotely.
"""

import sys
from pathlib import Path

import click

from ..common.utils import handle_error, handle_success, with_lab_context
from ..config.settings import get_settings
from ..db.context import get_lab_db
from ..remote import get_remote_host_manager
from ..topology.generator import TopologyGenerator


def generate_topology_command(
    db,
    output,
    topology_name,
    prefix,
    mgmt_network,
    mgmt_subnet,
    template,
    kinds_config,
    validate,
    upload_remote=False,
):
    """
    Generate containerlab topology file from current lab data.

    Args:
        db: DatabaseManager instance
        output: Output file path
        topology_name: Name for the topology
        prefix: Topology prefix
        mgmt_network: Management network name
        mgmt_subnet: Management subnet
        template: Template file path
        kinds_config: Kinds configuration file path
        validate: Whether to validate the generated YAML
        upload_remote: Whether to upload to remote host
    """
    settings = get_settings()

    # Use config default prefix if none specified
    if prefix is None:
        prefix = settings.topology.default_prefix
    elif prefix.lower() == "none":
        prefix = ""

    # Use config default topology name if none specified or default
    if topology_name == "generated_lab":
        topology_name = settings.topology.default_topology_name

    current_lab = db.get_current_lab()
    generator = TopologyGenerator(db, template, kinds_config)

    click.echo(f"=== Topology Generation from Lab '{current_lab}' ===")
    click.echo(f"Output file: {output}")
    click.echo(f"Topology name: {topology_name}")

    # Check if we have data in the current lab
    nodes = db.get_all_nodes()
    connections = db.get_all_connections()

    if not nodes:
        handle_error(f"No nodes found in lab '{current_lab}'. Run 'import-csv' first.")

    click.echo(
        f"Using {len(nodes)} nodes and {len(connections)} connections "
        f"from lab '{current_lab}'"
    )

    # Generate topology file
    success = generator.generate_topology_file(
        topology_name=topology_name,
        prefix=prefix,
        mgmt_network=mgmt_network,
        mgmt_subnet=mgmt_subnet,
        output_file=output,
    )

    if not success:
        sys.exit(1)

    # Validate if requested
    if validate:
        is_valid, message = generator.validate_yaml(output)
        if is_valid:
            handle_success(message)
        else:
            handle_error(message)

    # Upload to remote host if requested
    if upload_remote:
        remote_manager = get_remote_host_manager()
        if remote_manager:
            try:
                with remote_manager:
                    remote_path = remote_manager.upload_topology_file(output)
                    handle_success(f"Uploaded topology to remote host: {remote_path}")
            except Exception as e:
                handle_error(f"Failed to upload to remote host: {e}")
        else:
            handle_error("Remote upload requested but remote host not configured")

    # Calculate summary using cached data (already fetched above)
    bridges = [node for node in nodes if "bridge" in node[1].lower()]
    click.echo(f"\n=== Generation Complete - Lab '{current_lab}' ===")
    click.echo("Summary:")
    click.echo(f"  - Nodes: {len(nodes)} ({len(bridges)} bridges)")
    click.echo(f"  - Links: {len(connections)}")
    if upload_remote:
        click.echo("  - Remote upload: Yes")


@click.command()
@click.option("--output", "-o", default="clab.yml", help="Output topology file name")
@click.option("--topology-name", "-t", default="generated_lab", help="Topology name")
@click.option(
    "--prefix",
    "-p",
    default=None,
    help="Topology prefix (defaults to config setting, use 'none' for no prefix)",
)
@click.option(
    "--mgmt-network", "-m", default="mgmtclab", help="Management network name"
)
@click.option(
    "--mgmt-subnet", "-s", default="10.100.100.0/24", help="Management subnet"
)
@click.option("--template", default="topology_template.j2", help="Jinja2 template file")
@click.option(
    "--kinds-config",
    default="supported_kinds.yaml",
    help="Supported kinds configuration file",
)
@click.option("--validate", is_flag=True, help="Validate generated YAML file")
@click.option("--upload", is_flag=True, help="Upload topology file to remote host")
@click.pass_context
@with_lab_context
def generate_topology(
    ctx,
    output,
    topology_name,
    prefix,
    mgmt_network,
    mgmt_subnet,
    template,
    kinds_config,
    validate,
    upload,
):
    """
    Generate containerlab topology file from the current lab data.

    Reads node and connection information from the current lab and generates
    a containerlab topology YAML file using Jinja2 templating.

    Use --upload to automatically upload the generated topology to the
    configured remote host.
    """
    db = get_lab_db(ctx.obj)
    generate_topology_command(
        db,
        output,
        topology_name,
        prefix,
        mgmt_network,
        mgmt_subnet,
        template,
        kinds_config,
        validate,
        upload,
    )


@click.command()
@click.argument("topology_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--path", "-p", help="Custom path for topology file (overrides remote dir)"
)
@click.option("--remote", is_flag=True, help="Force remote execution")
@click.option("--local", is_flag=True, help="Force local execution")
@click.pass_context
@with_lab_context
def start(ctx, topology_file, path, remote, local):
    """
    Start a containerlab topology.

    By default, runs locally. Use --remote to force remote execution.
    If remote host is configured, uses remote.topology_remote_dir unless
    --path is specified.
    """
    settings = get_settings()
    quiet = ctx.obj.get("quiet", False)

    # Determine execution mode
    remote_manager = get_remote_host_manager()
    use_remote = False

    if local and remote:
        handle_error("Cannot specify both --local and --remote flags")
        return

    if remote:
        use_remote = True
    elif local:
        use_remote = False
    elif remote_manager and settings.remote.enabled:
        use_remote = True

    if use_remote and not remote_manager:
        handle_error("Remote execution requested but remote host not configured")
        return

    # Build topology file path
    if use_remote:
        if path:
            topology_path = path
        else:
            # Use remote topology directory
            remote_dir = settings.remote.topology_remote_dir
            # Handle both Path objects and strings
            if isinstance(topology_file, Path):
                filename = topology_file.name
            else:
                filename = Path(topology_file).name
            topology_path = f"{remote_dir}/{filename}"

        # Execute remote start
        try:
            with remote_manager:
                command = f"clab deploy -t {topology_path}"
                if not quiet:
                    click.echo(f"Starting topology remotely: {topology_path}")

                exit_code, stdout, stderr = remote_manager.execute_command(
                    command, check=False
                )

                if exit_code == 0:
                    handle_success("Topology started successfully on remote host")
                    if stdout and not quiet:
                        click.echo(stdout)
                else:
                    handle_error(f"Failed to start topology (exit code: {exit_code})")
                    if stderr:
                        click.echo(stderr, err=True)

        except Exception as e:
            handle_error(f"Remote execution failed: {e}")
    else:
        # Execute local start
        if path:
            topology_path = path
        else:
            topology_path = str(topology_file)

        if not quiet:
            click.echo(f"Starting topology locally: {topology_path}")

        try:
            import subprocess

            result = subprocess.run(
                ["clab", "deploy", "-t", topology_path],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                handle_success("Topology started successfully")
                if result.stdout and not quiet:
                    click.echo(result.stdout)
            else:
                handle_error(
                    f"Failed to start topology (exit code: {result.returncode})"
                )
                if result.stderr:
                    click.echo(result.stderr, err=True)

        except FileNotFoundError:
            handle_error(
                "Containerlab (clab) not found in PATH. Please install containerlab."
            )
        except Exception as e:
            handle_error(f"Failed to start topology: {e}")


@click.command()
@click.argument("topology_file", type=click.Path(path_type=Path))
@click.option(
    "--path", "-p", help="Custom path for topology file (overrides remote dir)"
)
@click.option("--remote", is_flag=True, help="Force remote execution")
@click.option("--local", is_flag=True, help="Force local execution")
@click.pass_context
@with_lab_context
def stop(ctx, topology_file, path, remote, local):
    """
    Stop a containerlab topology.

    By default, runs locally. Use --remote to force remote execution.
    If remote host is configured, uses remote.topology_remote_dir unless
    --path is specified.
    """
    settings = get_settings()
    quiet = ctx.obj.get("quiet", False)

    # Determine execution mode
    remote_manager = get_remote_host_manager()
    use_remote = False

    if local and remote:
        handle_error("Cannot specify both --local and --remote flags")
        return

    if remote:
        use_remote = True
    elif local:
        use_remote = False
    elif remote_manager and settings.remote.enabled:
        use_remote = True

    if use_remote and not remote_manager:
        handle_error("Remote execution requested but remote host not configured")
        return

    # Build topology file path
    if use_remote:
        if path:
            topology_path = path
        else:
            # Use remote topology directory
            remote_dir = settings.remote.topology_remote_dir
            # Handle both Path objects and strings
            if isinstance(topology_file, Path):
                filename = topology_file.name
            else:
                filename = Path(topology_file).name
            topology_path = f"{remote_dir}/{filename}"

        # Execute remote stop
        try:
            with remote_manager:
                command = f"clab destroy -t {topology_path}"
                if not quiet:
                    click.echo(f"Stopping topology remotely: {topology_path}")

                exit_code, stdout, stderr = remote_manager.execute_command(
                    command, check=False
                )

                if exit_code == 0:
                    handle_success("Topology stopped successfully on remote host")
                    if stdout and not quiet:
                        click.echo(stdout)
                else:
                    handle_error(f"Failed to stop topology (exit code: {exit_code})")
                    if stderr:
                        click.echo("Error output:", err=True)
                        click.echo(stderr, err=True)
                    if stdout:
                        click.echo("Command output:", err=True)
                        click.echo(stdout, err=True)

        except Exception as e:
            handle_error(f"Remote execution failed: {e}")
    else:
        # Execute local stop
        if path:
            topology_path = path
        else:
            topology_path = str(topology_file)

        if not quiet:
            click.echo(f"Stopping topology locally: {topology_path}")

        try:
            import subprocess

            result = subprocess.run(
                ["clab", "destroy", "-t", topology_path],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                handle_success("Topology stopped successfully")
                if result.stdout and not quiet:
                    click.echo(result.stdout)
            else:
                handle_error(
                    f"Failed to stop topology (exit code: {result.returncode})"
                )
                if result.stderr:
                    click.echo(result.stderr, err=True)

        except FileNotFoundError:
            handle_error(
                "Containerlab (clab) not found in PATH. Please install containerlab."
            )
        except Exception as e:
            handle_error(f"Failed to stop topology: {e}")
