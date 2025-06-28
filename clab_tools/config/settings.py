"""
Configuration Settings

Handles application configuration using Pydantic for validation.
Supports loading from environment variables and configuration files.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


def get_default_database_path() -> str:
    """Get default database path relative to the package installation directory."""
    # Get the directory where this settings.py file is located
    package_dir = Path(__file__).parent.parent.parent
    # Create the database path in the package root directory
    db_path = package_dir / "clab_topology.db"
    return f"sqlite:///{db_path.absolute()}"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(
        default_factory=get_default_database_path, description="Database URL"
    )
    echo: bool = Field(default=False, description="Enable SQL echo logging")
    pool_pre_ping: bool = Field(
        default=True, description="Enable connection pool pre-ping"
    )

    model_config = ConfigDict(env_prefix="CLAB_DB_")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format: json or console")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(
        default=10485760, description="Max log file size in bytes (10MB)"
    )
    backup_count: int = Field(default=5, description="Number of log file backups")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        valid_formats = ["json", "console"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()

    model_config = ConfigDict(env_prefix="CLAB_LOG_")


class TopologySettings(BaseSettings):
    """Topology generation settings."""

    default_prefix: str = Field(default="clab", description="Default topology prefix")
    default_topology_name: str = Field(
        default="generated_lab", description="Default topology name"
    )
    default_mgmt_network: str = Field(
        default="clab", description="Default management network"
    )
    default_mgmt_subnet: str = Field(
        default="172.20.20.0/24", description="Default management subnet"
    )
    template_path: str = Field(
        default="topology_template.j2", description="Topology template file path"
    )
    output_dir: str = Field(
        default=".", description="Output directory for generated files"
    )

    model_config = ConfigDict(env_prefix="CLAB_TOPOLOGY_")


class LabSettings(BaseSettings):
    """Lab management settings."""

    current_lab: str = Field(default="default", description="Current active lab name")
    use_global_database: bool = Field(
        default=False, description="Use global database instead of current directory"
    )
    global_database_path: Optional[str] = Field(
        default=None, description="Path to global database directory"
    )
    auto_create_lab: bool = Field(
        default=True, description="Automatically create lab if it doesn't exist"
    )

    model_config = ConfigDict(env_prefix="CLAB_LAB_")


class BridgeSettings(BaseSettings):
    """Bridge management settings."""

    bridge_prefix: str = Field(
        default="clab-br", description="Prefix for created bridges"
    )
    cleanup_on_exit: bool = Field(
        default=False, description="Cleanup bridges on application exit"
    )

    model_config = ConfigDict(env_prefix="CLAB_BRIDGE_")


class RemoteHostSettings(BaseSettings):
    """Remote containerlab host configuration settings."""

    enabled: bool = Field(default=False, description="Enable remote host operations")
    host: Optional[str] = Field(default=None, description="Remote host IP or hostname")
    port: int = Field(default=22, description="SSH port")
    username: Optional[str] = Field(default=None, description="SSH username")
    password: Optional[str] = Field(default=None, description="SSH password")
    private_key_path: Optional[str] = Field(
        default=None, description="SSH private key file path"
    )
    topology_remote_dir: str = Field(
        default="/tmp/clab-topologies",
        description="Remote directory for topology files",
    )
    timeout: int = Field(default=30, description="SSH connection timeout in seconds")
    use_sudo: bool = Field(
        default=True, description="Use sudo for bridge management commands"
    )
    sudo_password: Optional[str] = Field(
        default=None, description="Sudo password (if different from SSH password)"
    )

    model_config = ConfigDict(env_prefix="CLAB_REMOTE_")

    @field_validator("host")
    @classmethod
    def validate_host_when_enabled(cls, v, info):
        """Validate that host is provided when remote operations are enabled."""
        if info.data.get("enabled", False) and not v:
            raise ValueError(
                "Remote host must be specified when remote operations are enabled"
            )
        return v

    @field_validator("username")
    @classmethod
    def validate_username_when_enabled(cls, v, info):
        """Validate that username is provided when remote operations are enabled."""
        if info.data.get("enabled", False) and not v:
            raise ValueError(
                "Remote username must be specified when remote operations are enabled"
            )
        return v

    def has_auth_method(self) -> bool:
        """Check if at least one authentication method is configured."""
        return bool(self.password or self.private_key_path)


class Settings(BaseSettings):
    """Main application settings."""

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    topology: TopologySettings = Field(default_factory=TopologySettings)
    bridges: BridgeSettings = Field(default_factory=BridgeSettings)
    remote: RemoteHostSettings = Field(default_factory=RemoteHostSettings)
    lab: LabSettings = Field(default_factory=LabSettings)

    # General settings
    config_file: Optional[str] = Field(
        default=None, description="Configuration file path"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    model_config = ConfigDict(env_prefix="CLAB_", case_sensitive=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.config_file and Path(self.config_file).exists():
            self._load_from_file(self.config_file)

    def _load_from_file(self, config_path: str):
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

            # Update settings with file data
            for key, value in config_data.items():
                if hasattr(self, key):
                    if isinstance(value, dict):
                        # Handle nested settings
                        current_value = getattr(self, key)
                        if hasattr(current_value, "__dict__"):
                            for sub_key, sub_value in value.items():
                                if hasattr(current_value, sub_key):
                                    setattr(current_value, sub_key, sub_value)
                    else:
                        setattr(self, key, value)
        except Exception as e:
            # Don't fail startup on config file errors, just log
            print(f"Warning: Could not load config file {config_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "database": self.database.model_dump(),
            "logging": self.logging.model_dump(),
            "topology": self.topology.model_dump(),
            "bridges": self.bridges.model_dump(),
            "remote": self.remote.model_dump(),
            "lab": self.lab.model_dump(),
            "debug": self.debug,
            "config_file": self.config_file,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def initialize_settings(**kwargs) -> Settings:
    """Initialize settings with custom values."""
    global _settings
    _settings = Settings(**kwargs)
    return _settings
