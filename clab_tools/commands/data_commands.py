"""
Data Management Commands

Handles displaying and managing data stored in the database with multi-lab support.
"""

import click

from ..common.utils import handle_success, with_lab_context
from ..db.context import get_lab_db


@click.command()
@click.pass_context
@with_lab_context
def show_data(ctx):
    """
    Display current data stored in the current lab.

    Shows all nodes, connections, and topology configurations stored in the current lab.
    """
    db = get_lab_db(ctx.obj)
    current_lab = db.get_current_lab()

    click.echo(f"=== Lab '{current_lab}' Contents ===")

    # Show nodes
    nodes = db.get_all_nodes()
    click.echo(f"\nNodes ({len(nodes)}):")
    if nodes:
        click.echo("  Name               Kind                   Management IP")
        click.echo("  " + "-" * 55)
        for name, kind, mgmt_ip in nodes:
            click.echo(f"  {name:<18} {kind:<22} {mgmt_ip}")
    else:
        click.echo("  No nodes found")

    # Show connections
    connections = db.get_all_connections()
    click.echo(f"\nConnections ({len(connections)}):")
    if connections:
        click.echo("  Node1 -> Node2         Type     Interface1       Interface2")
        click.echo("  " + "-" * 65)
        for node1, node2, conn_type, int1, int2 in connections:
            click.echo(f"  {node1} -> {node2:<12} {conn_type:<8} {int1:<16} {int2}")
    else:
        click.echo("  No connections found")


@click.command()
@click.option("--force", is_flag=True, help="Proceed without confirmation")
@click.pass_context
@with_lab_context
def clear_data(ctx, force):
    """
    Clear all data from the current lab.

    This will remove all nodes, connections, and topology configurations
    from the current lab only.
    """
    db = get_lab_db(ctx.obj)
    current_lab = db.get_current_lab()

    if not force:
        if not click.confirm(
            f"This will clear ALL data from lab '{current_lab}'. Continue?"
        ):
            click.echo("Aborted.")
            return

    click.echo(f"Clearing data from lab '{current_lab}'...")
    db.clear_connections()
    db.clear_nodes()

    handle_success(f"Lab '{current_lab}' cleared successfully")
