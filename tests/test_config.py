"""Tests for configuration settings."""

import os
from unittest.mock import patch

import pytest

from clab_tools.config.settings import (
    BridgeSettings,
    DatabaseSettings,
    LoggingSettings,
    Settings,
    TopologySettings,
    get_settings,
    initialize_settings,
)


class TestDatabaseSettings:
    """Test cases for DatabaseSettings."""

    def test_default_values(self):
        """Test default database settings."""
        settings = DatabaseSettings()
        # Should be a SQLite URL with absolute path to project directory
        assert settings.url.startswith("sqlite:///")
        assert "clab_topology.db" in settings.url
        assert settings.echo is False
        assert settings.pool_pre_ping is True

    def test_environment_variables(self):
        """Test loading from environment variables."""
        os.environ["CLAB_DB_URL"] = "postgresql://test:test@localhost/test"
        os.environ["CLAB_DB_ECHO"] = "true"

        try:
            settings = DatabaseSettings()
            assert settings.url == "postgresql://test:test@localhost/test"
            assert settings.echo is True
        finally:
            # Clean up environment
            os.environ.pop("CLAB_DB_URL", None)
            os.environ.pop("CLAB_DB_ECHO", None)


class TestLoggingSettings:
    """Test cases for LoggingSettings."""

    def test_default_values(self):
        """Test default logging settings."""
        settings = LoggingSettings()
        assert settings.level == "INFO"
        assert settings.format == "json"
        assert settings.file_path is None

    def test_level_validation(self):
        """Test log level validation."""
        # Valid levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = LoggingSettings(level=level)
            assert settings.level == level

        # Invalid level should raise validation error
        with pytest.raises(ValueError, match="Log level must be one of"):
            LoggingSettings(level="INVALID")

    def test_format_validation(self):
        """Test log format validation."""
        # Valid formats
        for fmt in ["json", "console"]:
            settings = LoggingSettings(format=fmt)
            assert settings.format == fmt

        # Invalid format should raise validation error
        with pytest.raises(ValueError, match="Log format must be one of"):
            LoggingSettings(format="invalid")


class TestSettings:
    """Test cases for main Settings class."""

    def test_default_values(self):
        """Test default application settings."""
        # Disable config file discovery to test actual defaults
        with patch("clab_tools.config.settings.find_config_file", return_value=None):
            settings = Settings()
            assert isinstance(settings.database, DatabaseSettings)
            assert isinstance(settings.logging, LoggingSettings)
            assert isinstance(settings.topology, TopologySettings)
            assert isinstance(settings.bridges, BridgeSettings)
            assert settings.debug is False

    def test_config_file_loading(self, temp_dir):
        """Test loading configuration from YAML file."""
        config_content = """
database:
  url: "sqlite:///test.db"
  echo: true

logging:
  level: "DEBUG"
  format: "console"

topology:
  default_prefix: "testlab"
  default_topology_name: "test_lab"

debug: true
"""
        config_file = temp_dir / "test_config.yaml"
        config_file.write_text(config_content)

        settings = Settings(config_file=str(config_file))

        assert settings.database.url == "sqlite:///test.db"
        assert settings.database.echo is True
        assert settings.logging.level == "DEBUG"
        assert settings.logging.format == "console"
        assert settings.topology.default_prefix == "testlab"
        assert settings.topology.default_topology_name == "test_lab"
        assert settings.debug is True

    def test_invalid_config_file(self, temp_dir):
        """Test handling of invalid config file."""
        # Non-existent file should not cause error
        settings = Settings(config_file="nonexistent.yaml")
        # Should use dynamic default path
        assert settings.database.url.startswith("sqlite:///")
        assert "clab_topology.db" in settings.database.url

    def test_to_dict(self):
        """Test converting settings to dictionary."""
        # Use patch to ensure consistent test results regardless of config files
        with patch("clab_tools.config.settings.find_config_file", return_value=None):
            settings = Settings()
            config_dict = settings.to_dict()

        assert "database" in config_dict
        assert "logging" in config_dict
        assert "topology" in config_dict
        assert "bridges" in config_dict
        assert "debug" in config_dict


class TestGlobalSettings:
    """Test cases for global settings management."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_initialize_settings(self):
        """Test initializing settings with custom values."""
        # Disable config discovery to test parameter override
        with patch("clab_tools.config.settings.find_config_file", return_value=None):
            custom_settings = initialize_settings(debug=True)
            assert custom_settings.debug is True

        # get_settings should return the initialized instance
        settings = get_settings()
        assert settings is custom_settings
        assert settings.debug is True


class TestTopologySettings:
    """Test cases for TopologySettings."""

    def test_default_values(self):
        """Test default topology settings."""
        settings = TopologySettings()
        assert settings.default_prefix == "clab"
        assert settings.default_topology_name == "generated_lab"
        assert settings.default_mgmt_network == "clab"
        assert settings.default_mgmt_subnet == "172.20.20.0/24"
        assert settings.template_path == "topology_template.j2"
        assert settings.output_dir == "."

    def test_environment_variables(self):
        """Test loading from environment variables."""
        os.environ["CLAB_TOPOLOGY_DEFAULT_PREFIX"] = "mylab"
        os.environ["CLAB_TOPOLOGY_DEFAULT_TOPOLOGY_NAME"] = "my_topology"
        os.environ["CLAB_TOPOLOGY_DEFAULT_MGMT_NETWORK"] = "mgmt"

        try:
            settings = TopologySettings()
            assert settings.default_prefix == "mylab"
            assert settings.default_topology_name == "my_topology"
            assert settings.default_mgmt_network == "mgmt"
        finally:
            # Clean up environment
            os.environ.pop("CLAB_TOPOLOGY_DEFAULT_PREFIX", None)
            os.environ.pop("CLAB_TOPOLOGY_DEFAULT_TOPOLOGY_NAME", None)
            os.environ.pop("CLAB_TOPOLOGY_DEFAULT_MGMT_NETWORK", None)
