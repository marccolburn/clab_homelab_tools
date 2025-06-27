#!/usr/bin/env python3
"""
Containerlab Homelab Tools CLI

A comprehensive CLI tool for managing containerlab network topologies with
persistent storage. This is the main entry point that coordinates all the
different command modules.
"""

import sys

import click

from clab_tools import __version__
from clab_tools.commands.bridge_commands import (
    cleanup_bridges,
    configure_vlans,
    create_bridges,
    list_bridges,
)
from clab_tools.commands.data_commands import clear_data, show_data
from clab_tools.commands.generate_topology import generate_topology
from clab_tools.commands.import_csv import import_csv
from clab_tools.commands.lab_commands import lab_commands
from clab_tools.commands.remote_commands import remote
from clab_tools.config.settings import initialize_settings
from clab_tools.db.manager import DatabaseManager
from clab_tools.errors.handlers import error_handler
from clab_tools.log_config.logger import get_logger, setup_logging


@click.group()
@click.version_option(version=__version__, prog_name="clab-tools")
@click.option("--db-url", default=None, help="Database URL (overrides config file)")
@click.option("--config", "-c", default=None, help="Path to configuration file")
@click.option("--lab", "-l", default=None, help="Lab name to use (overrides config)")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option(
    "--log-level",
    default=None,
    help="Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option("--log-format", default=None, help="Set log format (json, console)")
@click.option(
    "--remote-host", default=None, help="Remote containerlab host IP/hostname"
)
@click.option("--remote-user", default=None, help="Remote host username")
@click.option("--remote-password", default=None, help="Remote host password")
@click.option("--remote-port", default=None, type=int, help="Remote host SSH port")
@click.option("--remote-key", default=None, help="Path to SSH private key file")
@click.option("--enable-remote", is_flag=True, help="Enable remote host operations")
@click.pass_context
@error_handler(exit_on_error=True)
def cli(
    ctx,
    db_url,
    config,
    lab,
    debug,
    log_level,
    log_format,
    remote_host,
    remote_user,
    remote_password,
    remote_port,
    remote_key,
    enable_remote,
):
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

    # Override lab settings with command line arguments
    if lab:
        settings.lab.current_lab = lab

    # Override remote settings with command line arguments
    if enable_remote or remote_host:
        settings.remote.enabled = True
    if remote_host:
        settings.remote.host = remote_host
    if remote_user:
        settings.remote.username = remote_user
    if remote_password:
        settings.remote.password = remote_password
    if remote_port:
        settings.remote.port = remote_port
    if remote_key:
        settings.remote.private_key_path = remote_key

    # Setup logging
    setup_logging(settings.logging)
    logger = get_logger(__name__)

    from clab_tools import __version__

    logger.info("Starting clab-tools CLI", version=__version__, debug=settings.debug)

    # Initialize database manager (multi-lab first approach)
    try:
        db_manager = DatabaseManager(settings=settings.database)
        if not db_manager.health_check():
            logger.error("Database health check failed")
            click.echo("✗ Database connection failed", err=True)
            sys.exit(1)

        # Ensure current lab exists
        current_lab = settings.lab.current_lab
        db_manager.get_or_create_lab(current_lab)
        logger.info("Using lab context", lab=current_lab)

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        click.echo(f"✗ Database initialization failed: {e}", err=True)
        sys.exit(1)

    # Store in context for commands
    ctx.obj["raw_db_manager"] = db_manager
    ctx.obj["db_manager"] = db_manager  # For compatibility with bridge commands
    ctx.obj["current_lab"] = current_lab
    ctx.obj["lab_name"] = current_lab  # For compatibility with bridge commands
    ctx.obj["settings"] = settings
    ctx.obj["debug"] = settings.debug

    logger.debug("CLI initialization completed")


# Register all command modules
cli.add_command(import_csv)
cli.add_command(generate_topology)
cli.add_command(create_bridges)
cli.add_command(cleanup_bridges)
cli.add_command(configure_vlans)
cli.add_command(list_bridges)
cli.add_command(show_data)
cli.add_command(clear_data)

# Command groups
cli.add_command(remote)
cli.add_command(lab_commands)


if __name__ == "__main__":
    cli()
