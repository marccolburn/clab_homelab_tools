"""
Generate Topology Command

Handles generating containerlab topology files from database data and
optionally uploading them to remote hosts.
"""

import sys

import click

from ..config.settings import get_settings
from ..remote import get_remote_host_manager
from ..topology.generator import TopologyGenerator


def generate_topology_command(
    db_manager,
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
    Generate containerlab topology file from database data.

    Args:
        db_manager: Database manager instance
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

    generator = TopologyGenerator(db_manager, template, kinds_config)

    click.echo("=== Topology Generation ===")
    click.echo(f"Output file: {output}")
    click.echo(f"Topology name: {topology_name}")

    # Check if we have data
    nodes = db_manager.get_all_nodes()
    connections = db_manager.get_all_connections()

    if not nodes:
        click.echo(
            "⚠ Warning: No nodes found in database. Run 'import-csv' first.", err=True
        )
        sys.exit(1)

    click.echo(
        f"Using {len(nodes)} nodes and {len(connections)} connections from database"
    )

    # Generate topology
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
            click.echo(f"✓ {message}")
        else:
            click.echo(f"✗ {message}", err=True)

    # Upload to remote host if requested
    if upload_remote:
        remote_manager = get_remote_host_manager()
        if remote_manager:
            try:
                with remote_manager:
                    remote_path = remote_manager.upload_topology_file(output)
                    click.echo(f"📤 Uploaded topology to remote host: {remote_path}")
            except Exception as e:
                click.echo(f"✗ Failed to upload to remote host: {e}", err=True)
                sys.exit(1)
        else:
            click.echo(
                "⚠ Remote upload requested but remote host not configured", err=True
            )
            sys.exit(1)

    # Calculate summary
    _, links, bridges = generator.generate_topology_data()
    click.echo("\n=== Generation Complete ===")
    click.echo("Summary:")
    click.echo(f"  - Nodes: {len(nodes)} ({len(bridges)} bridges)")
    click.echo(f"  - Links: {len(links)}")
    if upload_remote:
        click.echo("  - Remote upload: ✓")


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
    Generate containerlab topology file from database data.

    Reads node and connection information from the database and generates
    a containerlab topology YAML file using Jinja2 templating.

    Use --upload to automatically upload the generated topology to the
    configured remote host.
    """
    db_manager = ctx.obj["db_manager"]
    generate_topology_command(
        db_manager,
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
