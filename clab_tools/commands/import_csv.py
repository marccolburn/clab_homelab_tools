"""
Import CSV Command

Handles importing node and connection data from CSV files into the database.
"""

import csv

import click

from ..errors.exceptions import CSVImportError
from ..errors.handlers import (
    safe_operation,
    validate_file_exists,
    validate_required_columns,
)
from ..logging.logger import get_logger


def import_csv_command(db_manager, nodes_csv, connections_csv, clear_existing):
    """
    Import node and connection data from CSV files into the database.

    Args:
        db_manager: Database manager instance
        nodes_csv: Path to nodes CSV file
        connections_csv: Path to connections CSV file
        clear_existing: Whether to clear existing data before import

    Raises:
        CSVImportError: If files are missing or have invalid format
    """
    logger = get_logger(__name__)

    with safe_operation("CSV Import", logger):
        click.echo("=== CSV Import ===")

        # Validate files exist
        validate_file_exists(nodes_csv)
        validate_file_exists(connections_csv)

        if clear_existing:
            click.echo("Clearing existing data...")
            db_manager.clear_connections()
            db_manager.clear_nodes()

        # Import nodes
        node_count = 0
        try:
            with open(nodes_csv, "r", newline="") as file:
                reader = csv.DictReader(file)
                required_columns = ["node_name", "kind", "mgmt_ip"]

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 since row 1 is header
                    validate_required_columns(row, required_columns, nodes_csv)

                    name = row["node_name"].strip()
                    kind = row["kind"].strip()
                    mgmt_ip = row["mgmt_ip"].strip()

                    if not name or not kind or not mgmt_ip:
                        raise CSVImportError(
                            f"Empty values not allowed in row {row_num}",
                            file_path=nodes_csv,
                            row_number=row_num,
                        )

                    if db_manager.insert_node(name, kind, mgmt_ip):
                        node_count += 1

            click.echo(f"✓ Imported {node_count} nodes from {nodes_csv}")

        except csv.Error as e:
            raise CSVImportError(f"CSV parsing error: {e}", file_path=nodes_csv)

        # Import connections
        connection_count = 0
        try:
            with open(connections_csv, "r", newline="") as file:
                reader = csv.DictReader(file)
                required_columns = [
                    "node1",
                    "node2",
                    "type",
                    "node1_interface",
                    "node2_interface",
                ]

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 since row 1 is header
                    validate_required_columns(row, required_columns, connections_csv)

                    node1 = row["node1"].strip()
                    node2 = row["node2"].strip()
                    conn_type = row["type"].strip()
                    node1_interface = row["node1_interface"].strip()
                    node2_interface = row["node2_interface"].strip()

                    if not all(
                        [node1, node2, conn_type, node1_interface, node2_interface]
                    ):
                        raise CSVImportError(
                            f"Empty values not allowed in row {row_num}",
                            file_path=connections_csv,
                            row_number=row_num,
                        )

                    if db_manager.insert_connection(
                        node1, node2, conn_type, node1_interface, node2_interface
                    ):
                        connection_count += 1

            click.echo(
                f"✓ Imported {connection_count} connections from {connections_csv}"
            )

        except csv.Error as e:
            raise CSVImportError(f"CSV parsing error: {e}", file_path=connections_csv)

        click.echo("=== Import Complete ===")


@click.command()
@click.option(
    "--nodes-csv", "-n", required=True, help="CSV file containing node information"
)
@click.option(
    "--connections-csv",
    "-c",
    required=True,
    help="CSV file containing connection information",
)
@click.option(
    "--clear-existing", is_flag=True, help="Clear existing data before import"
)
@click.pass_context
def import_csv(ctx, nodes_csv, connections_csv, clear_existing):
    """
    Import node and connection data from CSV files into the database.

    CSV file formats:
    - Nodes: node_name, kind, mgmt_ip
    - Connections: node1, node2, type, node1_interface, node2_interface
    """
    db_manager = ctx.obj["db_manager"]
    import_csv_command(db_manager, nodes_csv, connections_csv, clear_existing)
