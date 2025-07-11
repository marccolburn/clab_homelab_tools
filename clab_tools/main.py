#!/usr/bin/env python3
"""
Containerlab Homelab Tools CLI

A comprehensive CLI tool for managing containerlab network topologies with
persistent storage. This is the main entry point that coordinates all the
different command modules.
"""

import os
import sys

import click

from clab_tools import __version__
from clab_tools.commands.bridge_commands import (
    cleanup_bridges,
    configure_vlans,
    create_bridge,
    create_bridges,
    list_bridges,
)
from clab_tools.commands.config_commands import config_commands
from clab_tools.commands.data_commands import clear_data, show_data
from clab_tools.commands.import_csv import import_csv
from clab_tools.commands.lab_commands import lab_commands
from clab_tools.commands.node_commands import node_commands
from clab_tools.commands.remote_commands import remote
from clab_tools.commands.topology_commands import generate_topology, start, stop
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
    "--quiet", "-q", is_flag=True, help="Suppress interactive prompts for scripting"
)
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
    quiet,
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

    # Handle quiet mode from CLI or environment variable
    if not quiet:
        quiet = os.getenv("CLAB_QUIET", "").lower() in ("true", "1", "yes")

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

    # Setup logging only if enabled
    if settings.logging.enabled:
        setup_logging(settings.logging)
        logger = get_logger(__name__)
        logger.info(
            "Starting clab-tools CLI", version=__version__, debug=settings.debug
        )
    else:
        # Get logger without setup - will use structlog defaults (no output)
        logger = get_logger(__name__)

    # Initialize database manager (multi-lab first approach)
    try:
        current_lab = settings.lab.current_lab
        db_manager = DatabaseManager(
            settings=settings.database, default_lab=current_lab
        )
        if not db_manager.health_check():
            logger.error("Database health check failed")
            click.echo("✗ Database connection failed", err=True)
            sys.exit(1)

        # Ensure current lab exists
        db_manager.get_or_create_lab(current_lab)
        if settings.logging.enabled:
            logger.info("Using lab context", lab=current_lab)

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        click.echo(f"✗ Database initialization failed: {e}", err=True)
        sys.exit(1)

    # Store simplified context for commands
    ctx.obj["db"] = db_manager
    ctx.obj["settings"] = settings
    ctx.obj["debug"] = settings.debug
    ctx.obj["quiet"] = quiet
    # Keep these for bridge commands until they're updated
    ctx.obj["db_manager"] = db_manager
    ctx.obj["lab_name"] = current_lab

    logger.debug("CLI initialization completed")


# Create command groups
@cli.group()
def data():
    """Data management commands for importing, exporting, and viewing lab data."""
    pass


@cli.group()
def topology():
    """Topology generation and validation commands."""
    pass


@cli.group()
def bridge():
    """Bridge management commands for network connectivity."""
    pass


# Add individual commands to groups
data.add_command(import_csv, name="import")
data.add_command(show_data, name="show")
data.add_command(clear_data, name="clear")

topology.add_command(generate_topology, name="generate")
topology.add_command(start, name="start")
topology.add_command(stop, name="stop")

bridge.add_command(create_bridges, name="create")
bridge.add_command(create_bridge, name="create-bridge")
bridge.add_command(cleanup_bridges, name="cleanup")
bridge.add_command(configure_vlans, name="configure")
bridge.add_command(list_bridges, name="list")

# Register command groups and existing groups
cli.add_command(lab_commands, name="lab")
cli.add_command(node_commands, name="node")
cli.add_command(remote)
cli.add_command(data)
cli.add_command(topology)
cli.add_command(bridge)
cli.add_command(config_commands, name="config")


if __name__ == "__main__":
    cli()
