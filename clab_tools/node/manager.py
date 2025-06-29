"""
Node Manager

Handles operations on individual containerlab nodes including file uploads
and command execution via SSH.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

import click
import paramiko
from scp import SCPClient

from ..config.settings import NodeSettings
from ..db.manager import DatabaseManager


class NodeConnectionError(Exception):
    """Exception raised for node connection errors."""

    pass


class NodeManager:
    """Manages operations on individual containerlab nodes."""

    def __init__(self, node_settings: NodeSettings):
        """Initialize the NodeManager with node settings."""
        self.settings = node_settings
        self._progress_bar = None
        self._last_file_name = None
        self._total_files = 0
        self._files_completed = 0
        self._is_directory_upload = False

    def _count_files_in_directory(self, directory: Path) -> int:
        """Count total number of files in a directory recursively."""
        count = 0
        for item in directory.rglob("*"):
            if item.is_file():
                count += 1
        return count

    def _progress_callback(self, filename: bytes, size: int, sent: int) -> None:
        """Progress callback for SCP transfers."""
        # Convert filename from bytes to string
        if isinstance(filename, bytes):
            filename = filename.decode("utf-8")

        # Get just the base filename
        base_filename = os.path.basename(filename)

        if self._is_directory_upload:
            # For directory uploads, track file completion
            if base_filename != self._last_file_name:
                # Starting a new file
                if self._last_file_name is not None:
                    # Previous file completed
                    self._files_completed += 1
                    if self._progress_bar:
                        self._progress_bar.update(1)

                self._last_file_name = base_filename

                # Show current file being uploaded
                if self._progress_bar:
                    # Clear the line and show file info
                    msg = (
                        f"\r  [{self._files_completed + 1}/{self._total_files}] "
                        f"Uploading: {base_filename}"
                    )
                    click.echo(f"{msg:<80}", nl=False)

            # Check if this is the last chunk of the current file
            if sent == size and self._files_completed < self._total_files - 1:
                # File transfer complete, but not the last file
                pass
        else:
            # For single file uploads, show file progress
            if base_filename != self._last_file_name:
                if self._progress_bar:
                    self._progress_bar.finish()
                self._progress_bar = click.progressbar(
                    length=size,
                    label=f"  Uploading {base_filename}",
                    show_percent=True,
                    show_pos=True,
                    width=0,  # Auto-width
                    bar_template="%(label)s  [%(bar)s]  %(info)s",
                )
                self._last_file_name = base_filename
                self._progress_bar.__enter__()

            # Update progress
            if self._progress_bar:
                self._progress_bar.update(sent - self._progress_bar.pos)

    def _connect_to_node(
        self,
        management_ip: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
    ) -> paramiko.SSHClient:
        """Establish SSH connection to a node."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Use provided credentials or defaults
        user = username or self.settings.default_username
        pwd = password or self.settings.default_password
        key_path = private_key_path or self.settings.private_key_path

        if not user:
            raise NodeConnectionError(f"No username provided for node {management_ip}")

        try:
            if key_path and Path(key_path).exists():
                # Use private key authentication
                ssh.connect(
                    hostname=management_ip,
                    port=self.settings.ssh_port,
                    username=user,
                    key_filename=key_path,
                    timeout=self.settings.connection_timeout,
                )
            elif pwd:
                # Use password authentication
                ssh.connect(
                    hostname=management_ip,
                    port=self.settings.ssh_port,
                    username=user,
                    password=pwd,
                    timeout=self.settings.connection_timeout,
                )
            else:
                raise NodeConnectionError(
                    f"No authentication method available for node {management_ip}"
                )

            return ssh

        except Exception as e:
            ssh.close()
            raise NodeConnectionError(f"Failed to connect to node {management_ip}: {e}")

    def upload_file_to_node(
        self,
        management_ip: str,
        local_file: Path,
        remote_path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
    ) -> bool:
        """Upload a single file to a node."""
        ssh = None
        try:
            ssh = self._connect_to_node(
                management_ip, username, password, private_key_path
            )

            with SCPClient(
                ssh.get_transport(), progress=self._progress_callback
            ) as scp:
                scp.put(str(local_file), remote_path)

            # Close progress bar if it exists
            if self._progress_bar:
                self._progress_bar.finish()
                self._progress_bar = None
                self._last_file_name = None

            return True

        except Exception as e:
            # Clean up progress bar on error
            if self._progress_bar:
                self._progress_bar.finish()
                self._progress_bar = None
                self._last_file_name = None
            raise NodeConnectionError(f"Failed to upload file to {management_ip}: {e}")
        finally:
            if ssh:
                ssh.close()

    def upload_directory_to_node(
        self,
        management_ip: str,
        local_dir: Path,
        remote_path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
    ) -> bool:
        """Upload a directory and its contents to a node."""
        ssh = None
        try:
            # Set up directory upload tracking
            self._is_directory_upload = True
            self._total_files = self._count_files_in_directory(local_dir)
            self._files_completed = 0
            self._last_file_name = None

            # Create progress bar for total files
            if self._total_files > 0:
                click.echo(f"  Found {self._total_files} files to upload")
                self._progress_bar = click.progressbar(
                    length=self._total_files,
                    label="  Uploading directory",
                    show_percent=True,
                    show_pos=True,
                    width=0,
                    bar_template="%(label)s  [%(bar)s]  %(info)s",
                )
                self._progress_bar.__enter__()

            ssh = self._connect_to_node(
                management_ip, username, password, private_key_path
            )

            with SCPClient(
                ssh.get_transport(), progress=self._progress_callback
            ) as scp:
                scp.put(str(local_dir), remote_path, recursive=True)

            # Close progress bar if it exists
            if self._progress_bar:
                # Count the last file
                if self._last_file_name is not None:
                    self._files_completed += 1
                    self._progress_bar.update(1)
                self._progress_bar.finish()
                click.echo()  # New line after progress
                self._progress_bar = None

            # Reset state
            self._is_directory_upload = False
            self._last_file_name = None
            self._files_completed = 0
            self._total_files = 0

            return True

        except Exception as e:
            # Clean up progress bar on error
            if self._progress_bar:
                self._progress_bar.finish()
                click.echo()  # New line after progress
                self._progress_bar = None

            # Reset state
            self._is_directory_upload = False
            self._last_file_name = None
            self._files_completed = 0
            self._total_files = 0

            raise NodeConnectionError(
                f"Failed to upload directory to {management_ip}: {e}"
            )
        finally:
            if ssh:
                ssh.close()

    def get_nodes_by_criteria(
        self,
        db: DatabaseManager,
        node_name: Optional[str] = None,
        kind: Optional[str] = None,
        nodes_list: Optional[List[str]] = None,
        all_nodes: bool = False,
    ) -> List[Tuple[str, str, str]]:
        """Get nodes based on different criteria."""
        if node_name:
            # Single node
            node = db.get_node_by_name(node_name)
            if not node:
                raise ValueError(f"Node '{node_name}' not found")
            return [node]

        elif kind:
            # Nodes by kind
            nodes = db.get_nodes_by_kind(kind)
            if not nodes:
                raise ValueError(f"No nodes found with kind '{kind}'")
            return nodes

        elif nodes_list:
            # Specific list of nodes
            result = []
            for node_name in nodes_list:
                node = db.get_node_by_name(node_name)
                if not node:
                    raise ValueError(f"Node '{node_name}' not found")
                result.append(node)
            return result

        elif all_nodes:
            # All nodes in current lab
            nodes = db.get_all_nodes()
            if not nodes:
                raise ValueError("No nodes found in current lab")
            return nodes

        else:
            raise ValueError(
                "Must specify one of: node_name, kind, nodes_list, or all_nodes"
            )

    def upload_to_multiple_nodes(
        self,
        db: DatabaseManager,
        local_source: Path,
        remote_dest: str,
        node_name: Optional[str] = None,
        kind: Optional[str] = None,
        nodes_list: Optional[List[str]] = None,
        all_nodes: bool = False,
        is_directory: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
    ) -> List[Tuple[str, bool, str]]:
        """
        Upload file or directory to multiple nodes.

        Returns a list of tuples (node_name, success, message).
        """
        nodes = self.get_nodes_by_criteria(db, node_name, kind, nodes_list, all_nodes)
        results = []

        # Show total count if multiple nodes
        if len(nodes) > 1:
            click.echo(f"\nUploading to {len(nodes)} nodes...")

        for i, node in enumerate(nodes, 1):
            if len(nodes) > 1:
                click.echo(f"\n[{i}/{len(nodes)}] Node: {node.name} ({node.mgmt_ip})")
            try:
                if is_directory:
                    success = self.upload_directory_to_node(
                        node.mgmt_ip,
                        local_source,
                        remote_dest,
                        username,
                        password,
                        private_key_path,
                    )
                else:
                    success = self.upload_file_to_node(
                        node.mgmt_ip,
                        local_source,
                        remote_dest,
                        username,
                        password,
                        private_key_path,
                    )

                if success:
                    results.append(
                        (node.name, True, f"Successfully uploaded to {node.mgmt_ip}")
                    )
                else:
                    results.append(
                        (node.name, False, f"Upload failed to {node.mgmt_ip}")
                    )

            except Exception as e:
                results.append((node.name, False, str(e)))

        return results
