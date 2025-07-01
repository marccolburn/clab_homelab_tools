"""
Tests for configuration management commands.
"""

import json
import os
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from clab_tools.commands.config_commands import (
    config_commands,
    format_settings_tree,
    get_config_source,
    show,
)
from clab_tools.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create a mock settings object for testing."""
    settings = Mock(spec=Settings)

    # Mock database settings
    settings.database = Mock()
    settings.database.url = "sqlite:///test.db"
    settings.database.echo = False
    settings.database.pool_pre_ping = True
    settings.database.model_dump.return_value = {
        "url": "sqlite:///test.db",
        "echo": False,
        "pool_pre_ping": True,
    }

    # Mock logging settings
    settings.logging = Mock()
    settings.logging.enabled = True
    settings.logging.level = "INFO"
    settings.logging.format = "json"
    settings.logging.file_path = None
    settings.logging.max_file_size = 10485760
    settings.logging.backup_count = 5
    settings.logging.model_dump.return_value = {
        "enabled": True,
        "level": "INFO",
        "format": "json",
        "file_path": None,
        "max_file_size": 10485760,
        "backup_count": 5,
    }

    # Mock topology settings
    settings.topology = Mock()
    settings.topology.default_prefix = "clab"
    settings.topology.default_topology_name = "generated_lab"
    settings.topology.default_mgmt_network = "clab"
    settings.topology.default_mgmt_subnet = "172.20.20.0/24"
    settings.topology.template_path = "topology_template.j2"
    settings.topology.output_dir = "."
    settings.topology.model_dump.return_value = {
        "default_prefix": "clab",
        "default_topology_name": "generated_lab",
        "default_mgmt_network": "clab",
        "default_mgmt_subnet": "172.20.20.0/24",
        "template_path": "topology_template.j2",
        "output_dir": ".",
    }

    # Mock lab settings
    settings.lab = Mock()
    settings.lab.current_lab = "default"
    settings.lab.use_global_database = False
    settings.lab.global_database_path = None
    settings.lab.auto_create_lab = True
    settings.lab.model_dump.return_value = {
        "current_lab": "default",
        "use_global_database": False,
        "global_database_path": None,
        "auto_create_lab": True,
    }

    # Mock bridges settings
    settings.bridges = Mock()
    settings.bridges.bridge_prefix = "clab-br"
    settings.bridges.cleanup_on_exit = False
    settings.bridges.model_dump.return_value = {
        "bridge_prefix": "clab-br",
        "cleanup_on_exit": False,
    }

    # Mock remote settings
    settings.remote = Mock()
    settings.remote.enabled = False
    settings.remote.host = None
    settings.remote.port = 22
    settings.remote.username = None
    settings.remote.password = None
    settings.remote.private_key_path = None
    settings.remote.topology_remote_dir = "/tmp/clab-topologies"
    settings.remote.timeout = 30
    settings.remote.use_sudo = True
    settings.remote.sudo_password = None
    settings.remote.model_dump.return_value = {
        "enabled": False,
        "host": None,
        "port": 22,
        "username": None,
        "password": None,
        "private_key_path": None,
        "topology_remote_dir": "/tmp/clab-topologies",
        "timeout": 30,
        "use_sudo": True,
        "sudo_password": None,
    }

    # Mock node settings
    settings.node = Mock()
    settings.node.default_username = "admin"
    settings.node.default_password = None
    settings.node.ssh_port = 22
    settings.node.connection_timeout = 30
    settings.node.private_key_path = None
    settings.node.command_timeout = 30
    settings.node.max_parallel_commands = 10
    settings.node.config_timeout = 60
    settings.node.max_parallel_configs = 5
    settings.node.default_commit_comment = "clab-tools configuration"
    settings.node.auto_rollback_on_error = True
    settings.node.model_dump.return_value = {
        "default_username": "admin",
        "default_password": None,
        "ssh_port": 22,
        "connection_timeout": 30,
        "private_key_path": None,
        "command_timeout": 30,
        "max_parallel_commands": 10,
        "config_timeout": 60,
        "max_parallel_configs": 5,
        "default_commit_comment": "clab-tools configuration",
        "auto_rollback_on_error": True,
    }

    # Mock vendor settings
    settings.vendor = Mock()
    settings.vendor.default_vendor_mappings = {
        "juniper_vjunosrouter": "juniper",
        "nokia_srlinux": "nokia",
    }
    settings.vendor.juniper_gather_facts = False
    settings.vendor.juniper_auto_probe = True
    settings.vendor.model_dump.return_value = {
        "default_vendor_mappings": {
            "juniper_vjunosrouter": "juniper",
            "nokia_srlinux": "nokia",
        },
        "juniper_gather_facts": False,
        "juniper_auto_probe": True,
    }

    # Mock top-level settings
    settings.debug = False
    settings.config_file = None

    return settings


class TestConfigSource:
    """Test configuration source detection."""

    def test_get_config_source_from_env(self, mock_settings):
        """Test detecting configuration from environment variable."""
        with patch.dict(os.environ, {"CLAB_DATABASE_URL": "sqlite:///test.db"}):
            source = get_config_source(
                mock_settings, "database.url", "sqlite:///test.db"
            )
            assert source == "env"

    def test_get_config_source_from_file(self, mock_settings, tmp_path):
        """Test detecting configuration from file."""
        config_file = tmp_path / "config.yaml"
        config_data = {"database": {"url": "sqlite:///test.db"}}
        config_file.write_text(yaml.dump(config_data))
        mock_settings.config_file = str(config_file)

        source = get_config_source(mock_settings, "database.url", "sqlite:///test.db")
        assert source == "file"

    def test_get_config_source_default(self, mock_settings):
        """Test detecting default configuration."""
        source = get_config_source(mock_settings, "database.url", "sqlite:///test.db")
        assert source == "default"

    def test_get_config_source_bool_from_env(self, mock_settings):
        """Test detecting boolean configuration from environment."""
        with patch.dict(os.environ, {"CLAB_DATABASE_ECHO": "true"}):
            source = get_config_source(mock_settings, "database.echo", True)
            assert source == "env"

    def test_get_config_source_int_from_env(self, mock_settings):
        """Test detecting integer configuration from environment."""
        with patch.dict(os.environ, {"CLAB_REMOTE_PORT": "22"}):
            source = get_config_source(mock_settings, "remote.port", 22)
            assert source == "env"


class TestFormatSettingsTree:
    """Test settings tree formatting."""

    def test_format_settings_tree_with_source(self, mock_settings):
        """Test formatting settings with source information."""
        result = format_settings_tree(mock_settings, show_source=True)

        assert "database" in result
        assert "url" in result["database"]
        assert "value" in result["database"]["url"]
        assert "source" in result["database"]["url"]
        assert result["database"]["url"]["value"] == "sqlite:///test.db"
        assert result["database"]["url"]["source"] == "default"

    def test_format_settings_tree_without_source(self, mock_settings):
        """Test formatting settings without source information."""
        result = format_settings_tree(mock_settings, show_source=False)

        assert "database" in result
        assert "url" in result["database"]
        assert result["database"]["url"] == "sqlite:///test.db"

    def test_format_settings_tree_all_sections(self, mock_settings):
        """Test all sections are included in formatted tree."""
        result = format_settings_tree(mock_settings, show_source=False)

        expected_sections = [
            "database",
            "logging",
            "topology",
            "lab",
            "bridges",
            "remote",
            "node",
            "vendor",
        ]
        for section in expected_sections:
            assert section in result

    def test_format_settings_tree_top_level(self, mock_settings):
        """Test top-level settings are included."""
        result = format_settings_tree(mock_settings, show_source=False)

        assert "debug" in result
        assert "config_file" in result


class TestConfigShowCommand:
    """Test config show command."""

    def test_show_command_tree_format(self, mock_settings):
        """Test show command with tree format."""
        runner = CliRunner()

        with patch(
            "clab_tools.commands.config_commands.find_config_file", return_value=None
        ):
            ctx = Mock()
            ctx.obj = {"settings": mock_settings}

            result = runner.invoke(show, ["--format", "tree"], obj=ctx.obj)

            assert result.exit_code == 0
            assert "database:" in result.output
            assert "url: sqlite:///test.db" in result.output
            assert "[default]" in result.output

    def test_show_command_json_format(self, mock_settings):
        """Test show command with JSON format."""
        runner = CliRunner()

        ctx = Mock()
        ctx.obj = {"settings": mock_settings}

        result = runner.invoke(show, ["--format", "json"], obj=ctx.obj)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert "database" in output
        assert output["database"]["url"]["value"] == "sqlite:///test.db"

    def test_show_command_yaml_format(self, mock_settings):
        """Test show command with YAML format."""
        runner = CliRunner()

        ctx = Mock()
        ctx.obj = {"settings": mock_settings}

        result = runner.invoke(show, ["--format", "yaml"], obj=ctx.obj)

        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        assert "database" in output
        assert output["database"]["url"]["value"] == "sqlite:///test.db"

    def test_show_command_specific_section(self, mock_settings):
        """Test show command with specific section."""
        runner = CliRunner()

        ctx = Mock()
        ctx.obj = {"settings": mock_settings}

        result = runner.invoke(show, ["--section", "database"], obj=ctx.obj)

        assert result.exit_code == 0
        assert "database:" in result.output
        assert "logging:" not in result.output

    def test_show_command_invalid_section(self, mock_settings):
        """Test show command with invalid section."""
        runner = CliRunner()

        ctx = Mock()
        ctx.obj = {"settings": mock_settings}

        result = runner.invoke(show, ["--section", "invalid"], obj=ctx.obj)

        assert result.exit_code == 1
        assert "Unknown section: invalid" in result.output

    def test_show_command_no_source(self, mock_settings):
        """Test show command without source information."""
        runner = CliRunner()

        with patch(
            "clab_tools.commands.config_commands.find_config_file", return_value=None
        ):
            ctx = Mock()
            ctx.obj = {"settings": mock_settings}

            result = runner.invoke(show, ["--no-show-source"], obj=ctx.obj)

            assert result.exit_code == 0
            assert "[default]" not in result.output
            assert "[env]" not in result.output
            assert "[file]" not in result.output

    def test_show_command_masks_passwords(self, mock_settings):
        """Test show command masks sensitive values."""
        runner = CliRunner()

        mock_settings.remote.password = "secret123"
        mock_settings.remote.model_dump.return_value["password"] = "secret123"

        ctx = Mock()
        ctx.obj = {"settings": mock_settings}

        result = runner.invoke(show, ["--section", "remote"], obj=ctx.obj)

        assert result.exit_code == 0
        assert "secret123" not in result.output
        assert "****" in result.output


class TestConfigEnvCommand:
    """Test config env command."""

    def test_env_command_no_variables(self):
        """Test env command when no CLAB variables are set."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(config_commands, ["env"])

            assert result.exit_code == 0
            assert "No CLAB environment variables set" in result.output

    def test_env_command_with_variables(self):
        """Test env command with CLAB variables set."""
        runner = CliRunner()

        env_vars = {
            "CLAB_DATABASE_URL": "sqlite:///test.db",
            "CLAB_REMOTE_HOST": "192.168.1.100",
            "CLAB_REMOTE_PASSWORD": "secret",
            "OTHER_VAR": "value",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = runner.invoke(config_commands, ["env"])

            assert result.exit_code == 0
            assert "CLAB Environment Variables:" in result.output
            assert "CLAB_DATABASE_URL=sqlite:///test.db" in result.output
            assert "CLAB_REMOTE_HOST=192.168.1.100" in result.output
            assert "CLAB_REMOTE_PASSWORD=****" in result.output
            assert "OTHER_VAR" not in result.output

    def test_env_command_masks_sensitive_values(self):
        """Test env command masks sensitive environment variables."""
        runner = CliRunner()

        env_vars = {
            "CLAB_REMOTE_PASSWORD": "secret123",
            "CLAB_NODE_DEFAULT_PASSWORD": "node_secret",
            "CLAB_REMOTE_PRIVATE_KEY_PATH": "/path/to/key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = runner.invoke(config_commands, ["env"])

            assert result.exit_code == 0
            assert "secret123" not in result.output
            assert "node_secret" not in result.output
            assert "CLAB_REMOTE_PASSWORD=****" in result.output
            assert "CLAB_NODE_DEFAULT_PASSWORD=****" in result.output
            assert "CLAB_REMOTE_PRIVATE_KEY_PATH=****" in result.output


class TestConfigCommandsGroup:
    """Test the config commands group."""

    def test_config_group_help(self):
        """Test config group help message."""
        runner = CliRunner()
        result = runner.invoke(config_commands, ["--help"])

        assert result.exit_code == 0
        assert "Configuration management commands" in result.output
        assert "show" in result.output
        assert "env" in result.output
