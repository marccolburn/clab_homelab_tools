"""
Tests for remote host management functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from clab_tools.config.settings import RemoteHostSettings
from clab_tools.errors.exceptions import ClabToolsError
from clab_tools.remote import (
    RemoteHostError,
    RemoteHostManager,
    get_remote_host_manager,
)


class TestRemoteHostSettings:
    """Test remote host settings validation."""

    def test_disabled_by_default(self):
        """Test that remote operations are disabled by default."""
        settings = RemoteHostSettings()
        assert not settings.enabled
        assert settings.host is None
        assert settings.username is None
        assert settings.password is None

    def test_validation_when_enabled_without_host(self):
        """Test validation fails when enabled without host."""
        with pytest.raises(ValueError, match="Remote host must be specified"):
            RemoteHostSettings(enabled=True)

    def test_validation_when_enabled_without_username(self):
        """Test validation fails when enabled without username."""
        with pytest.raises(ValueError, match="Remote username must be specified"):
            RemoteHostSettings(enabled=True, host="192.168.1.100")

    def test_valid_enabled_config(self):
        """Test valid enabled configuration."""
        settings = RemoteHostSettings(
            enabled=True, host="192.168.1.100", username="user", password="pass"
        )
        assert settings.enabled
        assert settings.host == "192.168.1.100"
        assert settings.username == "user"
        assert settings.password == "pass"

    def test_has_auth_method(self):
        """Test authentication method detection."""
        # No auth method
        settings = RemoteHostSettings()
        assert not settings.has_auth_method()

        # Password auth
        settings = RemoteHostSettings(password="secret")
        assert settings.has_auth_method()

        # Key auth
        settings = RemoteHostSettings(private_key_path="/path/to/key")
        assert settings.has_auth_method()

        # Both auth methods
        settings = RemoteHostSettings(
            password="secret", private_key_path="/path/to/key"
        )
        assert settings.has_auth_method()

    def test_environment_variable_loading(self):
        """Test loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "CLAB_REMOTE_ENABLED": "true",
                "CLAB_REMOTE_HOST": "192.168.1.200",
                "CLAB_REMOTE_USERNAME": "testuser",
                "CLAB_REMOTE_PASSWORD": "testpass",
                "CLAB_REMOTE_PORT": "2222",
            },
        ):
            settings = RemoteHostSettings()
            assert settings.enabled
            assert settings.host == "192.168.1.200"
            assert settings.username == "testuser"
            assert settings.password == "testpass"
            assert settings.port == 2222


class TestRemoteHostManager:
    """Test remote host manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = RemoteHostSettings(
            enabled=True,
            host="192.168.1.100",
            username="testuser",
            password="testpass",
            port=22,
            timeout=30,
        )

    def test_initialization(self):
        """Test manager initialization."""
        manager = RemoteHostManager(self.settings)
        assert manager.settings == self.settings
        assert manager._ssh_client is None
        assert manager._sftp_client is None

    def test_not_enabled_raises_error(self):
        """Test that disabled settings raise error on connect."""
        disabled_settings = RemoteHostSettings(enabled=False)
        manager = RemoteHostManager(disabled_settings)

        with pytest.raises(RemoteHostError, match="not enabled"):
            manager.connect()

    def test_no_auth_method_raises_error(self):
        """Test that missing auth method raises error."""
        no_auth_settings = RemoteHostSettings(
            enabled=True, host="192.168.1.100", username="testuser"
        )
        manager = RemoteHostManager(no_auth_settings)

        with pytest.raises(RemoteHostError, match="No authentication method"):
            manager.connect()

    @patch("clab_tools.remote.SSHClient")
    def test_successful_password_connection(self, mock_ssh_class):
        """Test successful SSH connection with password."""
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        manager = RemoteHostManager(self.settings)
        manager.connect()

        # Verify SSH client setup
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        mock_ssh.connect.assert_called_once_with(
            hostname="192.168.1.100",
            port=22,
            username="testuser",
            password="testpass",
            timeout=30,
        )
        mock_ssh.open_sftp.assert_called_once()

        assert manager._ssh_client == mock_ssh
        assert manager._sftp_client == mock_sftp
        assert manager.is_connected()

    @patch("clab_tools.remote.SSHClient")
    @patch("clab_tools.remote.Path")
    def test_successful_key_connection(self, mock_path_class, mock_ssh_class):
        """Test successful SSH connection with private key."""
        # Setup key-based settings
        key_settings = RemoteHostSettings(
            enabled=True,
            host="192.168.1.100",
            username="testuser",
            private_key_path="~/.ssh/id_rsa",
        )

        # Mock path operations
        mock_path = Mock()
        mock_path.expanduser.return_value = mock_path
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda self: "/home/user/.ssh/id_rsa"
        mock_path_class.return_value = mock_path

        # Mock SSH client
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        manager = RemoteHostManager(key_settings)
        manager.connect()

        # Verify key file path was used
        mock_ssh.connect.assert_called_once_with(
            hostname="192.168.1.100",
            port=22,
            username="testuser",
            timeout=30,
            key_filename="/home/user/.ssh/id_rsa",
        )

    @patch("clab_tools.remote.SSHClient")
    def test_connection_failure(self, mock_ssh_class):
        """Test connection failure handling."""
        mock_ssh = Mock()
        mock_ssh.connect.side_effect = Exception("Connection failed")
        mock_ssh_class.return_value = mock_ssh

        manager = RemoteHostManager(self.settings)

        with pytest.raises(RemoteHostError, match="Failed to connect"):
            manager.connect()

    @patch("clab_tools.remote.SSHClient")
    def test_execute_command_success(self, mock_ssh_class):
        """Test successful command execution."""
        # Setup connected manager
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        # Mock command execution
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b"command output"
        mock_stderr.read.return_value = b""

        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        manager = RemoteHostManager(self.settings)
        manager.connect()

        exit_code, stdout, stderr = manager.execute_command("ls -la")

        assert exit_code == 0
        assert stdout == "command output"
        assert stderr == ""
        mock_ssh.exec_command.assert_called_with("ls -la")

    @patch("clab_tools.remote.SSHClient")
    def test_execute_command_failure(self, mock_ssh_class):
        """Test command execution failure."""
        # Setup connected manager
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        # Mock failed command execution
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"command failed"

        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        manager = RemoteHostManager(self.settings)
        manager.connect()

        with pytest.raises(RemoteHostError, match="Command failed"):
            manager.execute_command("false")

    @patch("clab_tools.remote.SSHClient")
    def test_upload_file(self, mock_ssh_class):
        """Test file upload functionality."""
        # Setup connected manager
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        # Mock successful command execution for mkdir
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b""
        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        manager = RemoteHostManager(self.settings)
        manager.connect()

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_file = f.name

        try:
            manager.upload_file(temp_file, "/remote/path/file.txt")

            # Verify mkdir was called
            mock_ssh.exec_command.assert_called_with("mkdir -p /remote/path")
            # Verify file upload
            mock_sftp.put.assert_called_with(temp_file, "/remote/path/file.txt")
        finally:
            os.unlink(temp_file)

    @patch("clab_tools.remote.SSHClient")
    def test_upload_topology_file(self, mock_ssh_class):
        """Test topology file upload."""
        # Setup connected manager
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        # Mock successful command execution for mkdir
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b""
        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        manager = RemoteHostManager(self.settings)
        manager.connect()

        # Create temporary topology file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("name: test-topology")
            temp_file = f.name

        try:
            remote_path = manager.upload_topology_file(temp_file)

            expected_path = (
                f"{self.settings.topology_remote_dir}/{Path(temp_file).name}"
            )
            assert remote_path == expected_path

            # Verify upload was called
            mock_sftp.put.assert_called_with(temp_file, expected_path)
        finally:
            os.unlink(temp_file)

    @patch("clab_tools.remote.SSHClient")
    def test_context_manager(self, mock_ssh_class):
        """Test context manager functionality."""
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_class.return_value = mock_ssh

        manager = RemoteHostManager(self.settings)

        with manager:
            assert manager.is_connected()

        # Verify cleanup was called
        mock_sftp.close.assert_called_once()
        mock_ssh.close.assert_called_once()

    def test_disconnect_safety(self):
        """Test that disconnect is safe to call multiple times."""
        manager = RemoteHostManager(self.settings)

        # Should not raise error when not connected
        manager.disconnect()
        manager.disconnect()

    @patch("clab_tools.config.settings.get_settings")
    def test_factory_function_enabled(self, mock_get_settings):
        """Test factory function with enabled remote settings."""
        mock_settings_obj = Mock()
        mock_settings_obj.remote = self.settings
        mock_get_settings.return_value = mock_settings_obj

        manager = get_remote_host_manager()

        assert isinstance(manager, RemoteHostManager)
        assert manager.settings == self.settings

    @patch("clab_tools.config.settings.get_settings")
    def test_factory_function_disabled(self, mock_get_settings):
        """Test factory function with disabled remote settings."""
        disabled_settings = RemoteHostSettings(enabled=False)
        mock_settings_obj = Mock()
        mock_settings_obj.remote = disabled_settings
        mock_get_settings.return_value = mock_settings_obj

        manager = get_remote_host_manager()

        assert manager is None


class TestRemoteHostError:
    """Test remote host error handling."""

    def test_remote_host_error_inheritance(self):
        """Test that RemoteHostError inherits from ClabToolsError."""
        error = RemoteHostError("Test error")
        assert isinstance(error, ClabToolsError)
        assert str(error) == "Test error"
