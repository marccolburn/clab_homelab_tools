"""
Data Management Commands

Handles displaying and managing data stored in the database.
"""

import click


def show_data_command(db_manager):
    """
    Display current data stored in the database.

    Args:
        db_manager: Database manager instance
    """
    click.echo("=== Database Contents ===")

    # Show nodes
    nodes = db_manager.get_all_nodes()
    click.echo(f"\nNodes ({len(nodes)}):")
    if nodes:
        click.echo("  Name               Kind                   Management IP")
        click.echo("  " + "-" * 55)
        for name, kind, mgmt_ip in nodes:
            click.echo(f"  {name:<18} {kind:<22} {mgmt_ip}")
    else:
        click.echo("  No nodes found")

    # Show connections
    connections = db_manager.get_all_connections()
    click.echo(f"\nConnections ({len(connections)}):")
    if connections:
        click.echo("  Node1 -> Node2         Type     Interface1       Interface2")
        click.echo("  " + "-" * 65)
        for node1, node2, conn_type, int1, int2 in connections:
            click.echo(f"  {node1} -> {node2:<12} {conn_type:<8} {int1:<16} {int2}")
    else:
        click.echo("  No connections found")


def clear_data_command(db_manager, force):
    """
    Clear all data from the database.

    Args:
        db_manager: Database manager instance
        force: Whether to proceed without confirmation
    """
    if not force:
        if not click.confirm("This will clear ALL data from the database. Continue?"):
            click.echo("Aborted.")
            return

    click.echo("Clearing database...")
    db_manager.clear_connections()
    db_manager.clear_nodes()

    click.echo("✓ Database cleared successfully")


@click.command()
@click.pass_context
def show_data(ctx):
    """
    Display current data stored in the database.

    Shows all nodes, connections, and topology configurations stored in the database.
    """
    db_manager = ctx.obj["db_manager"]
    show_data_command(db_manager)


@click.command()
@click.option("--force", is_flag=True, help="Proceed without confirmation")
@click.pass_context
def clear_data(ctx, force):
    """
    Clear all data from the database.

    This will remove all nodes, connections, and topology configurations.
    """
    db_manager = ctx.obj["db_manager"]
    clear_data_command(db_manager, force)
