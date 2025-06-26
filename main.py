#!/usr/bin/env python3
"""
Containerlab Homelab Tools CLI

A comprehensive CLI tool for managing containerlab network topologies with
persistent storage. This is the main entry point that coordinates all the
different command modules.
"""

import sys

import click

from clab_tools.commands.bridge_commands import cleanup_bridges, create_bridges
from clab_tools.commands.data_commands import clear_data, show_data
from clab_tools.commands.generate_topology import generate_topology
from clab_tools.commands.import_csv import import_csv
from clab_tools.config.settings import initialize_settings
from clab_tools.db.manager import DatabaseManager
from clab_tools.errors.handlers import error_handler
from clab_tools.logging.logger import get_logger, setup_logging


@click.group()
@click.option("--db-url", default=None, help="Database URL (overrides config file)")
@click.option("--config", "-c", default=None, help="Path to configuration file")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option(
    "--log-level",
    default=None,
    help="Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option("--log-format", default=None, help="Set log format (json, console)")
@click.pass_context
@error_handler(exit_on_error=True)
def cli(ctx, db_url, config, debug, log_level, log_format):
    """
    Containerlab Homelab Tools - A comprehensive CLI for managing containerlab
    topologies.

    This tool provides commands for importing CSV data, generating topology
    files, and managing host system bridges with persistent SQLite storage.
    """
    ctx.ensure_object(dict)

    # Initialize settings
    settings_kwargs = {}
    if config:
        settings_kwargs["config_file"] = config
    if debug:
        settings_kwargs["debug"] = debug

    settings = initialize_settings(**settings_kwargs)

    # Override with command line arguments
    if db_url:
        settings.database.url = db_url
    if log_level:
        settings.logging.level = log_level.upper()
    if log_format:
        settings.logging.format = log_format.lower()
    if debug:
        settings.debug = debug
        settings.logging.level = "DEBUG"

    # Setup logging
    setup_logging(settings.logging)
    logger = get_logger(__name__)

    logger.info("Starting clab-tools CLI", version="2.0.0", debug=settings.debug)

    # Initialize database manager
    try:
        db_manager = DatabaseManager(settings=settings.database)
        if not db_manager.health_check():
            logger.error("Database health check failed")
            click.echo("✗ Database connection failed", err=True)
            sys.exit(1)
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        click.echo(f"✗ Database initialization failed: {e}", err=True)
        sys.exit(1)

    # Store in context for commands
    ctx.obj["db_manager"] = db_manager
    ctx.obj["settings"] = settings
    ctx.obj["debug"] = settings.debug

    logger.debug("CLI initialization completed")


# Register all command modules
cli.add_command(import_csv)
cli.add_command(generate_topology)
cli.add_command(create_bridges)
cli.add_command(cleanup_bridges)
cli.add_command(show_data)
cli.add_command(clear_data)


if __name__ == "__main__":
    cli()
