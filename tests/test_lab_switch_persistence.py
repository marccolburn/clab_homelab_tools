"""
Test Lab Switch Persistence

Tests for lab switching settings persistence functionality.
"""

from pathlib import Path
from unittest.mock import patch

import yaml

from clab_tools.config.settings import Settings


class TestLabSwitchSettingsPersistence:
    """Test lab settings persistence functionality."""

    def test_lab_setting_saves_to_config_file(self, tmp_path):
        """Test that lab setting changes are saved to config file."""
        # Create a test config file
        config_file = tmp_path / "test_config.yaml"
        initial_config = {"lab": {"current_lab": "default"}, "debug": False}
        config_file.write_text(yaml.dump(initial_config))

        # Create settings instance with the config file
        settings = Settings(config_file=str(config_file))

        # Verify initial state
        assert settings.lab.current_lab == "default"

        # Change lab setting
        settings.lab.current_lab = "new_lab"

        # Save settings
        result = settings.save_to_file()
        assert result is True

        # Verify the config file was updated
        with open(config_file) as f:
            updated_config = yaml.safe_load(f)

        assert updated_config["lab"]["current_lab"] == "new_lab"
        # Other settings should be preserved
        assert updated_config["debug"] is False

    def test_lab_setting_creates_local_config_when_none_exists(self):
        """Test that settings create config.local.yaml when no config exists."""
        local_config = Path("config.local.yaml")

        # Ensure no local config exists
        if local_config.exists():
            local_config.unlink()

        try:
            # Create settings with no config file (disable auto-discovery)
            with patch(
                "clab_tools.config.settings.find_config_file", return_value=None
            ):
                settings = Settings()

                # Change lab setting
                settings.lab.current_lab = "test_lab"

                # Save settings (should create config.local.yaml)
                result = settings.save_to_file()
                assert result is True

                # Verify config.local.yaml was created
                assert local_config.exists()

                # Verify content
                with open(local_config) as f:
                    saved_config = yaml.safe_load(f)

                assert saved_config["lab"]["current_lab"] == "test_lab"
        finally:
            # Cleanup
            if local_config.exists():
                local_config.unlink()

    def test_lab_setting_handles_save_failure_gracefully(self, tmp_path):
        """Test graceful handling when config save fails."""
        # Create a config file in a writable location first
        config_file = tmp_path / "config.yaml"
        config_file.write_text("lab:\n  current_lab: default\n")

        # Create settings instance
        settings = Settings(config_file=str(config_file))

        # Change lab setting
        settings.lab.current_lab = "test_lab"

        # Now make the file non-writable to simulate save failure
        config_file.chmod(0o444)

        try:
            # Attempt to save (should fail gracefully)
            result = settings.save_to_file()
            assert result is False  # Should return False on failure
        finally:
            # Restore permissions for cleanup
            config_file.chmod(0o644)

    def test_lab_setting_preserves_other_settings(self, tmp_path):
        """Test that lab setting changes preserve other configuration settings."""
        # Create a config file with various settings
        config_file = tmp_path / "full_config.yaml"
        initial_config = {
            "database": {"url": "sqlite:///custom.db", "echo": True},
            "logging": {"level": "DEBUG", "format": "console"},
            "topology": {"default_prefix": "custom", "output_dir": "./custom_output"},
            "lab": {"current_lab": "initial_lab", "auto_create_lab": False},
            "debug": True,
        }
        config_file.write_text(yaml.dump(initial_config))

        # Create settings instance
        settings = Settings(config_file=str(config_file))

        # Verify initial state
        assert settings.lab.current_lab == "initial_lab"

        # Change lab setting
        settings.lab.current_lab = "production"

        # Save settings
        result = settings.save_to_file()
        assert result is True

        # Verify the config file was updated with only lab change
        with open(config_file) as f:
            updated_config = yaml.safe_load(f)

        # Lab should be updated
        assert updated_config["lab"]["current_lab"] == "production"

        # Other settings should be preserved exactly
        assert updated_config["database"]["url"] == "sqlite:///custom.db"
        assert updated_config["database"]["echo"] is True
        assert updated_config["logging"]["level"] == "DEBUG"
        assert updated_config["logging"]["format"] == "console"
        assert updated_config["topology"]["default_prefix"] == "custom"
        assert updated_config["topology"]["output_dir"] == "./custom_output"
        assert updated_config["lab"]["auto_create_lab"] is False
        assert updated_config["debug"] is True

    def test_lab_setting_persistence_across_instances(self, tmp_path):
        """Test that lab setting changes persist across settings instances."""
        config_file = tmp_path / "persistence_test.yaml"
        config_file.write_text("lab:\n  current_lab: old_lab\n")

        # First settings instance
        settings1 = Settings(config_file=str(config_file))
        assert settings1.lab.current_lab == "old_lab"

        # Change and save
        settings1.lab.current_lab = "new_lab"
        result = settings1.save_to_file()
        assert result is True

        # Second settings instance (simulates fresh command invocation)
        settings2 = Settings(config_file=str(config_file))

        # Should have the updated lab
        assert settings2.lab.current_lab == "new_lab"

    def test_lab_setting_with_environment_config_override(self, tmp_path):
        """Test lab setting changes when using environment variable config file."""
        env_config = tmp_path / "env_config.yaml"
        env_config.write_text("lab:\n  current_lab: env_lab\n")

        # Mock environment variable and config discovery
        with patch.dict("os.environ", {"CLAB_CONFIG_FILE": str(env_config)}):
            with patch(
                "clab_tools.config.settings.find_config_file",
                return_value=str(env_config),
            ):
                settings = Settings()

                # Verify initial state
                assert settings.lab.current_lab == "env_lab"

                # Change lab setting
                settings.lab.current_lab = "env_switched"

                # Save settings
                result = settings.save_to_file()
                assert result is True

                # Verify the environment config file was updated
                with open(env_config) as f:
                    updated_config = yaml.safe_load(f)

                assert updated_config["lab"]["current_lab"] == "env_switched"
