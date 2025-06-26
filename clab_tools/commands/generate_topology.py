"""
Generate Topology Command

Handles generating containerlab topology files from database data.
"""

import sys

import click

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
    """
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

    # Calculate summary
    _, links, bridges = generator.generate_topology_data()
    click.echo("\n=== Generation Complete ===")
    click.echo("Summary:")
    click.echo(f"  - Nodes: {len(nodes)} ({len(bridges)} bridges)")
    click.echo(f"  - Links: {len(links)}")


@click.command()
@click.option("--output", "-o", default="clab.yml", help="Output topology file name")
@click.option("--topology-name", "-t", default="generated_lab", help="Topology name")
@click.option("--prefix", "-p", default="_lab", help="Topology prefix")
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
):
    """
    Generate containerlab topology file from database data.

    Reads node and connection information from the database and generates
    a containerlab topology YAML file using Jinja2 templating.
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
    )
