"""
Remote Host CLI Commands

Commands for managing remote containerlab host operations.
"""

from pathlib import Path

import click

from clab_tools.config.settings import get_settings
from clab_tools.remote import RemoteHostError, RemoteHostManager


@click.group()
def remote():
    """Manage remote containerlab host operations."""
    pass


@remote.command()
@click.option("--host", "-h", help="Remote host IP or hostname")
@click.option("--username", "-u", help="SSH username")
@click.option("--password", "-p", help="SSH password (prompt if not provided)")
@click.option("--private-key", "-k", help="SSH private key file path")
@click.option("--port", default=22, help="SSH port")
@click.pass_context
def test_connection(ctx, host, username, password, private_key, port):
    """Test connection to remote containerlab host."""
    settings = get_settings()

    # Override settings with CLI options if provided
    if host:
        settings.remote.host = host
    if username:
        settings.remote.username = username
    if password:
        settings.remote.password = password
    elif (
        not private_key
        and not settings.remote.private_key_path
        and not settings.remote.password
    ):
        # Only prompt for password if no auth method is available and not in quiet mode
        quiet = ctx.obj.get("quiet", False) if ctx.obj else False
        if not quiet:
            password = click.prompt("Password", hide_input=True)
            settings.remote.password = password
        else:
            click.echo(
                "❌ No authentication method available. Use --password, "
                "--private-key, or configure in settings.",
                err=True,
            )
            raise click.Abort()
    if private_key:
        settings.remote.private_key_path = private_key
    if port != 22:
        settings.remote.port = port

    settings.remote.enabled = True

    try:
        with RemoteHostManager(settings.remote) as remote_manager:
            # Test basic command execution
            exit_code, stdout, stderr = remote_manager.execute_command("whoami")
            click.echo(f"✅ Connection successful! Logged in as: {stdout.strip()}")

            # Test containerlab availability
            exit_code, stdout, stderr = remote_manager.execute_command(
                "which containerlab", check=False
            )
            if exit_code == 0:
                click.echo(f"✅ Containerlab found at: {stdout.strip()}")
            else:
                click.echo("⚠️  Containerlab not found in PATH")

    except RemoteHostError as e:
        click.echo(f"❌ Connection failed: {e}", err=True)
        raise click.Abort()


@remote.command()
@click.argument("local_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--remote-path", "-r", help="Remote file path (default: topology directory)"
)
@click.option("--host", "-h", help="Remote host IP or hostname")
@click.option("--username", "-u", help="SSH username")
@click.option("--password", "-p", help="SSH password")
@click.pass_context
def upload_topology(ctx, local_file, remote_path, host, username, password):
    """Upload topology file to remote containerlab host."""
    settings = get_settings()

    # Override settings with CLI options if provided
    if host:
        settings.remote.host = host
    if username:
        settings.remote.username = username
    if password:
        settings.remote.password = password
    elif not settings.remote.private_key_path and not settings.remote.password:
        # Only prompt for password if no auth method is available
        quiet = ctx.obj.get("quiet", False) if ctx.obj else False
        if not quiet:
            password = click.prompt("Password", hide_input=True)
            settings.remote.password = password
        else:
            click.echo(
                "❌ No authentication method available. Use --password, "
                "--private-key, or configure in settings.",
                err=True,
            )
            raise click.Abort()

    settings.remote.enabled = True

    try:
        with RemoteHostManager(settings.remote) as remote_manager:
            if remote_path:
                remote_manager.upload_file(local_file, remote_path)
                click.echo(f"✅ Uploaded topology to: {remote_path}")
            else:
                remote_file = remote_manager.upload_topology_file(local_file)
                click.echo(f"✅ Uploaded topology to: {remote_file}")

    except RemoteHostError as e:
        click.echo(f"❌ Upload failed: {e}", err=True)
        raise click.Abort()


@remote.command()
@click.argument("command")
@click.option("--host", "-h", help="Remote host IP or hostname")
@click.option("--username", "-u", help="SSH username")
@click.option("--password", "-p", help="SSH password")
@click.pass_context
def execute(ctx, command, host, username, password):
    """Execute a command on the remote containerlab host."""
    settings = get_settings()

    # Override settings with CLI options if provided
    if host:
        settings.remote.host = host
    if username:
        settings.remote.username = username
    if password:
        settings.remote.password = password
    elif not settings.remote.private_key_path and not settings.remote.password:
        # Only prompt for password if no auth method is available
        quiet = ctx.obj.get("quiet", False) if ctx.obj else False
        if not quiet:
            password = click.prompt("Password", hide_input=True)
            settings.remote.password = password
        else:
            click.echo(
                "❌ No authentication method available. Use --password, "
                "--private-key, or configure in settings.",
                err=True,
            )
            raise click.Abort()

    settings.remote.enabled = True

    try:
        with RemoteHostManager(settings.remote) as remote_manager:
            exit_code, stdout, stderr = remote_manager.execute_command(
                command, check=False
            )

            if stdout:
                click.echo("STDOUT:")
                click.echo(stdout)
            if stderr:
                click.echo("STDERR:")
                click.echo(stderr, err=True)

            click.echo(f"Exit code: {exit_code}")

    except RemoteHostError as e:
        click.echo(f"❌ Command execution failed: {e}", err=True)
        raise click.Abort()


@remote.command()
def show_config():
    """Show current remote host configuration."""
    settings = get_settings()
    remote_settings = settings.remote

    click.echo("=== Remote Host Configuration ===")
    click.echo(f"Enabled: {remote_settings.enabled}")
    click.echo(f"Host: {remote_settings.host or 'Not configured'}")
    click.echo(f"Port: {remote_settings.port}")
    click.echo(f"Username: {remote_settings.username or 'Not configured'}")
    click.echo(f"Password: {'****' if remote_settings.password else 'Not configured'}")
    click.echo(f"Private Key: {remote_settings.private_key_path or 'Not configured'}")
    click.echo(f"Topology Directory: {remote_settings.topology_remote_dir}")
    click.echo(f"Timeout: {remote_settings.timeout}s")
    click.echo(f"Use Sudo: {remote_settings.use_sudo}")
    sudo_password_display = (
        "****" if remote_settings.sudo_password else "Not configured"
    )
    click.echo(f"Sudo Password: {sudo_password_display}")

    if remote_settings.enabled and remote_settings.has_auth_method():
        click.echo("\n✅ Remote host is properly configured")
    elif remote_settings.enabled:
        click.echo("\n⚠️  Remote host is enabled but missing authentication")
    else:
        click.echo("\n💡 Remote host operations are disabled")
