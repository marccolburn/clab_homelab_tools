"""
Remote Host Management

Provides secure SSH/SFTP connections and operations for remote containerlab hosts.
Supports both password and key-based authentication with credential security.
"""

from pathlib import Path
from typing import Optional, Union

import click
import paramiko
from paramiko import SFTPClient, SSHClient

from clab_tools.config.settings import RemoteHostSettings
from clab_tools.errors.exceptions import ClabToolsError


class RemoteHostError(ClabToolsError):
    """Exception raised for remote host operation errors."""

    pass


class RemoteHostManager:
    """Manages SSH/SFTP connections and operations for remote containerlab hosts."""

    def __init__(self, settings: RemoteHostSettings):
        self.settings = settings
        self._ssh_client: Optional[SSHClient] = None
        self._sftp_client: Optional[SFTPClient] = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def connect(self) -> None:
        """Establish SSH connection to remote host."""
        if not self.settings.enabled:
            raise RemoteHostError("Remote host operations are not enabled")

        if not self.settings.has_auth_method():
            raise RemoteHostError(
                "No authentication method configured (password or private key)"
            )

        try:
            self._ssh_client = SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Prepare authentication parameters
            auth_kwargs = {
                "hostname": self.settings.host,
                "port": self.settings.port,
                "username": self.settings.username,
                "timeout": self.settings.timeout,
            }

            # Use private key if available, otherwise password
            if self.settings.private_key_path:
                key_path = Path(self.settings.private_key_path).expanduser()
                if not key_path.exists():
                    raise RemoteHostError(f"Private key file not found: {key_path}")
                auth_kwargs["key_filename"] = str(key_path)
            elif self.settings.password:
                auth_kwargs["password"] = self.settings.password

            self._ssh_client.connect(**auth_kwargs)
            self._sftp_client = self._ssh_client.open_sftp()

            click.echo(f"✅ Connected to remote host: {self.settings.host}")

        except Exception as e:
            self.disconnect()
            raise RemoteHostError(
                f"Failed to connect to remote host {self.settings.host}: {e}"
            )

    def disconnect(self) -> None:
        """Close SSH and SFTP connections."""
        if self._sftp_client:
            self._sftp_client.close()
            self._sftp_client = None

        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None

    def is_connected(self) -> bool:
        """Check if SSH connection is active."""
        return (
            self._ssh_client is not None
            and self._ssh_client.get_transport() is not None
        )

    def execute_command(self, command: str, check: bool = True) -> tuple[int, str, str]:
        """
        Execute a command on the remote host.

        Args:
            command: Command to execute
            check: If True, raise exception on non-zero exit code

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.is_connected():
            raise RemoteHostError("Not connected to remote host")

        try:
            # Check if command uses sudo and we have a sudo password
            if command.strip().startswith("sudo") and self.settings.sudo_password:
                # Use echo to provide sudo password via stdin
                password = self.settings.sudo_password
                cmd_without_sudo = command[4:].strip()
                full_command = f"echo '{password}' | sudo -S {cmd_without_sudo}"
            else:
                full_command = command

            stdin, stdout, stderr = self._ssh_client.exec_command(full_command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode("utf-8")
            stderr_text = stderr.read().decode("utf-8")

            if check and exit_code != 0:
                raise RemoteHostError(
                    f"Command failed with exit code {exit_code}: {command}\n"
                    f"STDERR: {stderr_text}"
                )

            return exit_code, stdout_text, stderr_text

        except Exception as e:
            if isinstance(e, RemoteHostError):
                raise
            raise RemoteHostError(f"Failed to execute command '{command}': {e}")

    def upload_file(self, local_path: Union[str, Path], remote_path: str) -> None:
        """
        Upload a file to the remote host.

        Args:
            local_path: Local file path
            remote_path: Remote file path
        """
        if not self.is_connected():
            raise RemoteHostError("Not connected to remote host")

        local_path = Path(local_path)
        if not local_path.exists():
            raise RemoteHostError(f"Local file not found: {local_path}")

        try:
            # Ensure remote directory exists
            remote_dir = str(Path(remote_path).parent)
            self.execute_command(f"mkdir -p {remote_dir}")

            self._sftp_client.put(str(local_path), remote_path)
            click.echo(f"📤 Uploaded {local_path} → {self.settings.host}:{remote_path}")

        except Exception as e:
            raise RemoteHostError(
                f"Failed to upload file {local_path} to {remote_path}: {e}"
            )

    def download_file(self, remote_path: str, local_path: Union[str, Path]) -> None:
        """
        Download a file from the remote host.

        Args:
            remote_path: Remote file path
            local_path: Local file path
        """
        if not self.is_connected():
            raise RemoteHostError("Not connected to remote host")

        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            self._sftp_client.get(remote_path, str(local_path))
            click.echo(
                f"📥 Downloaded {self.settings.host}:{remote_path} → {local_path}"
            )

        except Exception as e:
            raise RemoteHostError(
                f"Failed to download file {remote_path} to {local_path}: {e}"
            )

    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists on the remote host."""
        if not self.is_connected():
            raise RemoteHostError("Not connected to remote host")

        try:
            self._sftp_client.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            raise RemoteHostError(f"Failed to check if file exists {remote_path}: {e}")

    def upload_topology_file(
        self,
        local_topology_path: Union[str, Path],
        remote_filename: Optional[str] = None,
    ) -> str:
        """
        Upload a topology file to the remote host's topology directory.

        Args:
            local_topology_path: Local topology file path
            remote_filename: Optional remote filename (defaults to local filename)

        Returns:
            Remote file path
        """
        local_path = Path(local_topology_path)
        if not remote_filename:
            remote_filename = local_path.name

        remote_path = f"{self.settings.topology_remote_dir}/{remote_filename}"
        self.upload_file(local_path, remote_path)
        return remote_path

    def run_bridge_command(
        self, command: str, dry_run: bool = False
    ) -> tuple[bool, str]:
        """
        Execute a bridge-related command on the remote host.

        Args:
            command: Bridge command to execute
            dry_run: If True, only show what would be executed

        Returns:
            Tuple of (success, message)
        """
        if dry_run:
            click.echo(f"Would execute on {self.settings.host}: {command}")
            return True, f"Dry run: would execute '{command}'"

        try:
            exit_code, stdout, stderr = self.execute_command(command, check=False)

            if exit_code == 0:
                return True, (
                    stdout.strip() if stdout else "Command executed successfully"
                )
            else:
                return False, (
                    stderr.strip()
                    if stderr
                    else f"Command failed with exit code {exit_code}"
                )

        except Exception as e:
            return False, str(e)


def get_remote_host_manager(
    settings: Optional[RemoteHostSettings] = None,
) -> Optional[RemoteHostManager]:
    """
    Factory function to create a RemoteHostManager if remote operations are enabled.

    Args:
        settings: Remote host settings (optional, uses global settings if not provided)

    Returns:
        RemoteHostManager instance if enabled, None otherwise
    """
    if settings is None:
        from clab_tools.config.settings import get_settings

        settings = get_settings().remote

    if not settings.enabled:
        return None

    return RemoteHostManager(settings)


def with_remote_host(func):
    """
    Decorator to automatically handle remote host connections for functions.
    The decorated function will receive a 'remote_manager' parameter.
    """

    def wrapper(*args, **kwargs):
        remote_manager = get_remote_host_manager()
        if remote_manager:
            with remote_manager:
                kwargs["remote_manager"] = remote_manager
                return func(*args, **kwargs)
        else:
            kwargs["remote_manager"] = None
            return func(*args, **kwargs)

    return wrapper
