"""
Import CSV Command

Handles importing node and connection data from CSV files into the current lab.
"""

import csv

import click

from ..common.utils import handle_success, with_lab_context
from ..db.context import get_lab_db
from ..errors.exceptions import CSVImportError
from ..errors.handlers import (
    safe_operation,
    validate_file_exists,
    validate_required_columns,
)
from ..log_config.logger import get_logger


def import_csv_command(db, nodes_csv, connections_csv, clear_existing):
    """
    Import node and connection data from CSV files into the current lab.

    Args:
        db: DatabaseManager instance
        nodes_csv: Path to nodes CSV file
        connections_csv: Path to connections CSV file
        clear_existing: Whether to clear existing data before import

    Raises:
        CSVImportError: If files are missing or have invalid format
    """
    logger = get_logger(__name__)
    current_lab = db.get_current_lab()

    with safe_operation("CSV Import", logger):
        click.echo(f"=== CSV Import to Lab '{current_lab}' ==")

        # Validate files exist
        validate_file_exists(nodes_csv)
        validate_file_exists(connections_csv)

        if clear_existing:
            click.echo(f"Clearing existing data from lab '{current_lab}'...")
            db.clear_connections()
            db.clear_nodes()

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

                    # Validate required fields (mgmt_ip can be empty for bridge nodes)
                    if not name or not kind:
                        raise CSVImportError(
                            f"node_name and kind are required in row {row_num}",
                            file_path=nodes_csv,
                            row_number=row_num,
                        )

                    # Bridge nodes don't need mgmt_ip, use placeholder
                    if kind == "bridge" and not mgmt_ip:
                        mgmt_ip = "N/A"
                    elif not mgmt_ip:
                        raise CSVImportError(
                            f"mgmt_ip is required for non-bridge nodes in row "
                            f"{row_num}",
                            file_path=nodes_csv,
                            row_number=row_num,
                        )

                    if db.insert_node(name, kind, mgmt_ip):
                        node_count += 1

            handle_success(f"Imported {node_count} nodes from {nodes_csv}")

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

                    if db.insert_connection(
                        node1, node2, conn_type, node1_interface, node2_interface
                    ):
                        connection_count += 1

            handle_success(
                f"Imported {connection_count} connections from {connections_csv}"
            )

        except csv.Error as e:
            raise CSVImportError(f"CSV parsing error: {e}", file_path=connections_csv)

        handle_success(f"Import Complete - Lab '{current_lab}'")


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
@with_lab_context
def import_csv(ctx, nodes_csv, connections_csv, clear_existing):
    """
    Import node and connection data from CSV files into the current lab.

    CSV file formats:
    - Nodes: node_name, kind, mgmt_ip
    - Connections: node1, node2, type, node1_interface, node2_interface
    """
    db = get_lab_db(ctx.obj)
    import_csv_command(db, nodes_csv, connections_csv, clear_existing)
