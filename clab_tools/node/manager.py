"""
Node Manager

Handles operations on individual containerlab nodes including file uploads
and command execution via SSH.
"""

from pathlib import Path
from typing import List, Optional, Tuple

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

            with SCPClient(ssh.get_transport()) as scp:
                scp.put(str(local_file), remote_path)

            return True

        except Exception as e:
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
            ssh = self._connect_to_node(
                management_ip, username, password, private_key_path
            )

            with SCPClient(ssh.get_transport()) as scp:
                scp.put(str(local_dir), remote_path, recursive=True)

            return True

        except Exception as e:
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

        for node_name, node_kind, mgmt_ip in nodes:
            try:
                if is_directory:
                    success = self.upload_directory_to_node(
                        mgmt_ip,
                        local_source,
                        remote_dest,
                        username,
                        password,
                        private_key_path,
                    )
                else:
                    success = self.upload_file_to_node(
                        mgmt_ip,
                        local_source,
                        remote_dest,
                        username,
                        password,
                        private_key_path,
                    )

                if success:
                    results.append(
                        (node_name, True, f"Successfully uploaded to {mgmt_ip}")
                    )
                else:
                    results.append((node_name, False, f"Upload failed to {mgmt_ip}"))

            except Exception as e:
                results.append((node_name, False, str(e)))

        return results
