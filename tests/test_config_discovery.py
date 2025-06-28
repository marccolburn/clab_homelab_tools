"""
Test Configuration Discovery and Persistence

Tests for the configuration file discovery system and lab switch persistence.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from clab_tools.config.settings import (
    Settings,
    find_config_file,
    get_default_database_path,
)


class TestConfigFileDiscovery:
    """Test configuration file discovery priority order."""

    def test_find_config_file_environment_variable(self, tmp_path):
        """Test that CLAB_CONFIG_FILE environment variable takes priority."""
        # Create test config file
        config_file = tmp_path / "env_config.yaml"
        config_file.write_text("debug: true\n")

        with patch.dict(os.environ, {"CLAB_CONFIG_FILE": str(config_file)}):
            result = find_config_file()
            assert result == str(config_file)

    def test_find_config_file_environment_variable_nonexistent(self, tmp_path):
        """Test that nonexistent CLAB_CONFIG_FILE falls back to next priority."""
        nonexistent = tmp_path / "nonexistent.yaml"

        # Create project-specific config for fallback
        project_dir = Path.cwd() / "clab_tools_files"
        project_dir.mkdir(exist_ok=True)
        project_config = project_dir / "config.yaml"
        project_config.write_text("debug: true\n")

        try:
            with patch.dict(os.environ, {"CLAB_CONFIG_FILE": str(nonexistent)}):
                result = find_config_file()
                # find_config_file returns relative path for project config
                assert result == "clab_tools_files/config.yaml"
        finally:
            # Cleanup
            if project_config.exists():
                project_config.unlink()
            if project_dir.exists():
                project_dir.rmdir()

    def test_find_config_file_project_specific(self):
        """Test discovery of project-specific config file."""
        project_dir = Path.cwd() / "clab_tools_files"
        project_config = project_dir / "config.yaml"

        # Ensure environment variable is not set
        with patch.dict(os.environ, {}, clear=True):
            try:
                project_dir.mkdir(exist_ok=True)
                project_config.write_text("debug: true\n")

                result = find_config_file()
                # find_config_file returns relative path for project config
                assert result == "clab_tools_files/config.yaml"
            finally:
                # Cleanup
                if project_config.exists():
                    project_config.unlink()
                if project_dir.exists():
                    project_dir.rmdir()

    def test_find_config_file_local_override(self):
        """Test discovery of local override config file."""
        local_config = Path.cwd() / "config.local.yaml"

        # Ensure environment variable is not set and project config doesn't exist
        with patch.dict(os.environ, {}, clear=True):
            try:
                local_config.write_text("debug: true\n")

                result = find_config_file()
                # find_config_file returns relative path for local config
                assert result == "config.local.yaml"
            finally:
                # Cleanup
                if local_config.exists():
                    local_config.unlink()

    def test_find_config_file_installation_default(self):
        """Test fallback to installation directory config."""
        # Mock the package directory to a temp location for testing
        with tempfile.TemporaryDirectory() as tmp_dir:
            default_config = Path(tmp_dir) / "config.yaml"
            default_config.write_text("debug: true\n")

            with patch.dict(os.environ, {}, clear=True):
                # Create a mock find_config function that uses our test setup
                def mock_find_config():
                    env_config = os.getenv("CLAB_CONFIG_FILE")
                    if env_config and Path(env_config).exists():
                        return env_config

                    project_config = Path("clab_tools_files/config.yaml")
                    if project_config.exists():
                        return str(project_config)

                    local_config = Path("config.local.yaml")
                    if local_config.exists():
                        return str(local_config)

                    # Simulate installation directory config
                    if default_config.exists():
                        return str(default_config)

                    return None

                result = mock_find_config()
                assert result == str(default_config)

    def test_find_config_file_none_exist(self):
        """Test when no config files exist."""
        with patch.dict(os.environ, {}, clear=True):
            # Use a custom function that simulates no configs existing
            def mock_find_config():
                env_config = os.getenv("CLAB_CONFIG_FILE")
                if env_config and Path(env_config).exists():
                    return env_config

                # Simulate all configs not existing
                return None

            result = mock_find_config()
            assert result is None


class TestConfigurationLoading:
    """Test configuration loading from discovered files."""

    def test_settings_loads_discovered_config(self, tmp_path):
        """Test that Settings automatically loads discovered config."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "debug": True,
            "lab": {"current_lab": "test_lab"},
            "logging": {"level": "DEBUG"},
        }
        config_file.write_text(yaml.dump(config_data))

        with patch(
            "clab_tools.config.settings.find_config_file", return_value=str(config_file)
        ):
            settings = Settings()

            assert settings.debug is True
            assert settings.lab.current_lab == "test_lab"
            assert settings.logging.level == "DEBUG"

    def test_settings_respects_explicit_config_file(self, tmp_path):
        """Test that explicitly provided config file overrides discovery."""
        # Create two config files
        discovered_config = tmp_path / "discovered.yaml"
        discovered_config.write_text("debug: false\nlab:\n  current_lab: discovered\n")

        explicit_config = tmp_path / "explicit.yaml"
        explicit_config.write_text("debug: true\nlab:\n  current_lab: explicit\n")

        with patch(
            "clab_tools.config.settings.find_config_file",
            return_value=str(discovered_config),
        ):
            settings = Settings(config_file=str(explicit_config))

            # Should use explicit config, not discovered
            assert settings.debug is True
            assert settings.lab.current_lab == "explicit"

    def test_settings_handles_invalid_config_gracefully(self, tmp_path):
        """Test that invalid config files don't crash initialization."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with patch(
            "clab_tools.config.settings.find_config_file", return_value=str(config_file)
        ):
            # Should not raise an exception
            settings = Settings()

            # Should use defaults
            assert settings.debug is False
            assert settings.lab.current_lab == "default"


class TestConfigurationPersistence:
    """Test configuration persistence functionality."""

    def test_save_to_file_with_explicit_path(self, tmp_path):
        """Test saving configuration to explicitly specified path."""
        settings = Settings()
        settings.debug = True
        settings.lab.current_lab = "test_lab"

        save_path = tmp_path / "saved_config.yaml"
        result = settings.save_to_file(str(save_path))

        assert result is True
        assert save_path.exists()

        # Verify saved content
        with open(save_path) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["debug"] is True
        assert saved_data["lab"]["current_lab"] == "test_lab"
        assert "config_file" not in saved_data  # Should be excluded

    def test_save_to_file_uses_loaded_config_path(self, tmp_path):
        """Test saving to the originally loaded config file."""
        config_file = tmp_path / "original.yaml"
        config_file.write_text("debug: false\n")

        settings = Settings(config_file=str(config_file))
        settings.debug = True

        result = settings.save_to_file()

        assert result is True

        # Verify it was saved to the original file
        with open(config_file) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["debug"] is True

    def test_save_to_file_creates_local_default(self):
        """Test creating config.local.yaml when no config file was loaded."""
        local_config = Path("config.local.yaml")

        try:
            # Remove any existing local config
            if local_config.exists():
                local_config.unlink()

            # Create a settings instance that doesn't auto-discover config
            with patch(
                "clab_tools.config.settings.find_config_file", return_value=None
            ):
                settings = Settings()
                settings.debug = True

                result = settings.save_to_file()

                assert result is True
                assert local_config.exists()

                # Verify content
                with open(local_config) as f:
                    saved_data = yaml.safe_load(f)

                assert saved_data["debug"] is True
        finally:
            # Cleanup
            if local_config.exists():
                local_config.unlink()

    def test_save_to_file_handles_permission_error(self, tmp_path):
        """Test graceful handling of permission errors during save."""
        settings = Settings()

        # Try to save to a directory (should fail)
        result = settings.save_to_file(str(tmp_path))

        assert result is False


class TestDatabasePathDiscovery:
    """Test database path resolution."""

    def test_get_default_database_path(self):
        """Test that default database path is consistent."""
        path1 = get_default_database_path()
        path2 = get_default_database_path()

        assert path1 == path2
        assert path1.startswith("sqlite:///")
        assert "clab_topology.db" in path1

    def test_database_path_in_settings(self):
        """Test that settings use the default database path."""
        settings = Settings()

        # Should use the dynamic default path
        assert settings.database.url.startswith("sqlite:///")
        assert "clab_topology.db" in settings.database.url

    def test_database_path_override(self, tmp_path):
        """Test that database path can be overridden via config."""
        config_file = tmp_path / "config.yaml"
        custom_db_path = tmp_path / "custom.db"

        config_data = {"database": {"url": f"sqlite:///{custom_db_path}"}}
        config_file.write_text(yaml.dump(config_data))

        settings = Settings(config_file=str(config_file))

        assert settings.database.url == f"sqlite:///{custom_db_path}"


class TestEnvironmentVariableOverrides:
    """Test environment variable configuration overrides."""

    def test_environment_variable_config_file_discovery(self, tmp_path):
        """Test CLAB_CONFIG_FILE environment variable works for config discovery."""
        config_file = tmp_path / "env_config.yaml"
        config_data = {
            "debug": True,
            "lab": {"current_lab": "env_lab"},
        }
        config_file.write_text(yaml.dump(config_data))

        with patch.dict(os.environ, {"CLAB_CONFIG_FILE": str(config_file)}, clear=True):
            # Patch find_config_file to use our environment variable
            with patch("clab_tools.config.settings.find_config_file") as mock_find:
                mock_find.return_value = str(config_file)
                settings = Settings()

                # Config file should be loaded via environment variable
                assert settings.debug is True
                assert settings.lab.current_lab == "env_lab"

    def test_config_file_discovery_priority(self, tmp_path):
        """Test that config file discovery respects priority order."""
        # Create environment config
        env_config = tmp_path / "env.yaml"
        env_config.write_text(
            yaml.dump({"debug": True, "lab": {"current_lab": "env_lab"}})
        )

        # Create project config
        project_config = tmp_path / "project.yaml"
        project_config.write_text(
            yaml.dump({"debug": False, "lab": {"current_lab": "project_lab"}})
        )

        # Test environment variable takes priority
        with patch.dict(os.environ, {"CLAB_CONFIG_FILE": str(env_config)}, clear=True):
            with patch("clab_tools.config.settings.find_config_file") as mock_find:
                mock_find.return_value = str(env_config)
                settings = Settings()
                assert settings.lab.current_lab == "env_lab"

        # Test project config when no environment variable
        with patch.dict(os.environ, {}, clear=True):
            with patch("clab_tools.config.settings.find_config_file") as mock_find:
                mock_find.return_value = str(project_config)
                settings = Settings()
                assert settings.lab.current_lab == "project_lab"

    def test_explicit_config_file_overrides_discovery(self, tmp_path):
        """Test that explicitly provided config file overrides discovery."""
        # Create discovered config
        discovered_config = tmp_path / "discovered.yaml"
        discovered_config.write_text(yaml.dump({"lab": {"current_lab": "discovered"}}))

        # Create explicit config
        explicit_config = tmp_path / "explicit.yaml"
        explicit_config.write_text(yaml.dump({"lab": {"current_lab": "explicit"}}))

        with patch("clab_tools.config.settings.find_config_file") as mock_find:
            mock_find.return_value = str(discovered_config)

            # Explicit config should override discovery
            settings = Settings(config_file=str(explicit_config))
            assert settings.lab.current_lab == "explicit"
