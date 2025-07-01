"""Test that environment variables have priority over config file values."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from clab_tools.config.settings import Settings


class TestEnvironmentVariablePriority:
    """Test that environment variables take precedence over config file values."""

    def test_env_vars_override_config_file_for_nested_settings(self):
        """Test env vars override config file values for nested settings."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "remote": {
                    "enabled": True,
                    "host": "config.example.com",
                    "username": "config_user",
                    "password": "ConfigPassword",
                    "sudo_password": None,  # Explicitly set to None in config
                    "use_sudo": True,
                    "port": 2222,
                }
            }
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            # Set environment variables that should override config
            env_vars = {
                "CLAB_REMOTE_SUDO_PASSWORD": "EnvSudoPassword",
                "CLAB_REMOTE_PASSWORD": "EnvPassword",
                "CLAB_REMOTE_PORT": "22",
                "CLAB_CONFIG_FILE": config_file,
            }

            with patch.dict(os.environ, env_vars):
                settings = Settings()

                # Verify environment variables take precedence
                assert (
                    settings.remote.sudo_password == "EnvSudoPassword"
                ), "sudo_password should come from environment variable"
                assert (
                    settings.remote.password == "EnvPassword"
                ), "password should come from environment variable"
                assert (
                    settings.remote.port == 22
                ), "port should come from environment variable"

                # Verify config file values are used when no env var exists
                assert (
                    settings.remote.username == "config_user"
                ), "username should come from config file"
                assert (
                    settings.remote.host == "config.example.com"
                ), "host should come from config file"
                assert (
                    settings.remote.use_sudo is True
                ), "use_sudo should come from config file"

        finally:
            # Cleanup
            Path(config_file).unlink(missing_ok=True)

    def test_env_vars_override_config_file_for_top_level_settings(self):
        """Test env vars override for top-level settings like debug."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {"debug": False, "config_file": "/path/to/config.yaml"}
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            env_vars = {"CLAB_DEBUG": "true", "CLAB_CONFIG_FILE": config_file}

            with patch.dict(os.environ, env_vars):
                settings = Settings()

                # Debug should come from environment
                assert (
                    settings.debug is True
                ), "debug should come from environment variable"

                # Config file path should be the one we specified
                assert (
                    settings.config_file == config_file
                ), "config_file should be set correctly"

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_env_vars_override_null_values_in_config(self):
        """Test that env vars override even when config explicitly sets null."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # YAML null values
            config_data = {
                "remote": {
                    "sudo_password": None,
                    "password": None,
                    "private_key_path": None,
                },
                "node": {"default_password": None, "private_key_path": None},
            }
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            env_vars = {
                "CLAB_REMOTE_SUDO_PASSWORD": "EnvSudo123",
                "CLAB_REMOTE_PASSWORD": "EnvPass123",
                "CLAB_REMOTE_PRIVATE_KEY_PATH": "/env/key",
                "CLAB_NODE_DEFAULT_PASSWORD": "NodePass123",
                "CLAB_NODE_PRIVATE_KEY_PATH": "/env/node/key",
                "CLAB_CONFIG_FILE": config_file,
            }

            with patch.dict(os.environ, env_vars):
                settings = Settings()

                # All values should come from environment, not the null in config
                assert settings.remote.sudo_password == "EnvSudo123"
                assert settings.remote.password == "EnvPass123"
                assert settings.remote.private_key_path == "/env/key"
                assert settings.node.default_password == "NodePass123"
                assert settings.node.private_key_path == "/env/node/key"

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_top_level_settings_env_override(self):
        """Test that top-level settings also respect env var priority."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "debug": False,
                "logging": {"level": "INFO", "enabled": True},
            }
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            env_vars = {
                "CLAB_DEBUG": "true",
                "CLAB_LOG_LEVEL": "DEBUG",
                "CLAB_CONFIG_FILE": config_file,
            }

            with patch.dict(os.environ, env_vars):
                settings = Settings()

                # Debug should come from env
                assert settings.debug is True, "debug should be True from environment"

                # Log level should come from env
                assert (
                    settings.logging.level == "DEBUG"
                ), "log level should be DEBUG from environment"

                # Enabled should come from config
                assert (
                    settings.logging.enabled is True
                ), "logging enabled should come from config"

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_boolean_env_var_conversion(self):
        """Test that boolean env vars are properly converted and override config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "remote": {
                    "use_sudo": True,
                    "enabled": False,
                    "host": "example.com",  # Add required fields
                    "username": "user",  # Add required fields
                },
                "lab": {"use_global_database": True, "auto_create_lab": False},
            }
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            # Test various boolean representations
            env_vars = {
                "CLAB_REMOTE_USE_SUDO": "false",  # Should override True in config
                "CLAB_LAB_USE_GLOBAL_DATABASE": "no",  # Should override True
                "CLAB_LAB_AUTO_CREATE_LAB": "yes",  # Should override False
                "CLAB_CONFIG_FILE": config_file,
            }

            with patch.dict(os.environ, env_vars):
                settings = Settings()

                assert settings.remote.use_sudo is False
                # Don't test enabled since changing it triggers validation
                assert settings.lab.use_global_database is False
                assert settings.lab.auto_create_lab is True

        finally:
            Path(config_file).unlink(missing_ok=True)
