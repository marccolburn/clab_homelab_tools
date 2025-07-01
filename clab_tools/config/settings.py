"""
Configuration Settings

Handles application configuration using Pydantic for validation.
Supports loading from environment variables and configuration files.
"""

import os
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


def find_config_file() -> Optional[str]:
    """Find configuration file using priority order:
    1. CLAB_CONFIG_FILE environment variable
    2. ./clab_tools_files/config.yaml (project-specific)
    3. ./config.local.yaml (local override)
    4. Installation directory config.yaml (default)
    """
    # 1. Check environment variable
    env_config = os.getenv("CLAB_CONFIG_FILE")
    if env_config and Path(env_config).exists():
        return env_config

    # 2. Check project-specific config
    project_config = Path("clab_tools_files/config.yaml")
    if project_config.exists():
        return str(project_config)

    # 3. Check local override
    local_config = Path("config.local.yaml")
    if local_config.exists():
        return str(local_config)

    # 4. Default to installation directory config
    package_dir = Path(__file__).parent.parent.parent
    default_config = package_dir / "config.yaml"
    if default_config.exists():
        return str(default_config)

    return None


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

    enabled: bool = Field(default=True, description="Enable logging")
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


class NodeSettings(BaseSettings):
    """Node authentication and connection settings."""

    default_username: Optional[str] = Field(
        default="admin", description="Default SSH username for nodes"
    )
    default_password: Optional[str] = Field(
        default=None, description="Default SSH password for nodes"
    )
    ssh_port: int = Field(default=22, description="Default SSH port for nodes")
    connection_timeout: int = Field(
        default=30, description="SSH connection timeout in seconds"
    )
    private_key_path: Optional[str] = Field(
        default=None, description="Default SSH private key for nodes"
    )

    # Command execution settings
    command_timeout: int = Field(
        default=30, description="Default command execution timeout in seconds"
    )
    max_parallel_commands: int = Field(
        default=10, description="Maximum parallel command executions"
    )

    # Configuration settings
    config_timeout: int = Field(
        default=60, description="Configuration operation timeout in seconds"
    )
    max_parallel_configs: int = Field(
        default=5, description="Maximum parallel configuration operations"
    )
    default_commit_comment: Optional[str] = Field(
        default="clab-tools configuration", description="Default commit comment"
    )
    auto_rollback_on_error: bool = Field(
        default=True, description="Auto-rollback configuration on error"
    )

    model_config = ConfigDict(env_prefix="CLAB_NODE_")

    def has_auth_method(self) -> bool:
        """Check if at least one authentication method is configured."""
        return bool(self.default_password or self.private_key_path)


class VendorSettings(BaseSettings):
    """Vendor-specific configuration settings."""

    default_vendor_mappings: Dict[str, str] = Field(
        default={
            "juniper_vjunosrouter": "juniper",
            "juniper_vjunosswitch": "juniper",
            "juniper_vjunosevolved": "juniper",
            "juniper_vmx": "juniper",
            "juniper_vsrx": "juniper",
            "juniper_vqfx": "juniper",
            "nokia_srlinux": "nokia",
            "arista_ceos": "arista",
            "cisco_iosxr": "cisco",
        },
        description="Default vendor mappings for node kinds",
    )

    juniper_gather_facts: bool = Field(
        default=False, description="Gather facts on Juniper device connection"
    )
    juniper_auto_probe: bool = Field(
        default=True, description="Auto-probe Juniper device capabilities"
    )

    model_config = ConfigDict(env_prefix="CLAB_VENDOR_")


class Settings(BaseSettings):
    """Main application settings."""

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    topology: TopologySettings = Field(default_factory=TopologySettings)
    bridges: BridgeSettings = Field(default_factory=BridgeSettings)
    remote: RemoteHostSettings = Field(default_factory=RemoteHostSettings)
    lab: LabSettings = Field(default_factory=LabSettings)
    node: NodeSettings = Field(default_factory=NodeSettings)
    vendor: VendorSettings = Field(default_factory=VendorSettings)

    # General settings
    config_file: Optional[str] = Field(
        default=None, description="Configuration file path"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    model_config = ConfigDict(env_prefix="CLAB_", case_sensitive=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Store which fields were set from environment before loading config
        self._store_env_fields()

        # Auto-detect config file if not explicitly provided
        if not self.config_file:
            self.config_file = find_config_file()

        if self.config_file and Path(self.config_file).exists():
            self._load_from_file(self.config_file)

    def _store_env_fields(self):
        """Store which fields were set from environment variables."""
        self._env_fields = {}
        # Store env-set fields for each subsetting
        for field_name in [
            "database",
            "logging",
            "topology",
            "bridges",
            "remote",
            "lab",
            "node",
            "vendor",
        ]:
            subsetting = getattr(self, field_name)
            if hasattr(subsetting, "model_fields_set"):
                self._env_fields[field_name] = subsetting.model_fields_set.copy()

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
                            # Get fields set from environment for this subsection
                            env_set_fields = self._env_fields.get(key, set())

                            for sub_key, sub_value in value.items():
                                # Skip if this field was set by environment variable
                                if sub_key in env_set_fields:
                                    continue

                                if hasattr(current_value, sub_key):
                                    setattr(current_value, sub_key, sub_value)
                    else:
                        # For top-level fields, check if they were set by env
                        if key not in self.model_fields_set:
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
            "node": self.node.model_dump(),
            "vendor": self.vendor.model_dump(),
            "debug": self.debug,
            "config_file": self.config_file,
        }

    def save_to_file(self, config_path: Optional[str] = None) -> bool:
        """Save current settings to YAML file.

        Args:
            config_path: Optional path to save to. If None, uses the config file
                        that was loaded, or creates config.local.yaml.
        """
        if config_path is None:
            if self.config_file:
                config_path = self.config_file
            else:
                # Create config.local.yaml as default
                config_path = "config.local.yaml"

        try:
            # Convert settings to dict, excluding config_file from output
            config_data = self.to_dict()
            config_data.pop("config_file", None)

            # Save to file
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            return True
        except Exception as e:
            print(f"Warning: Could not save config file {config_path}: {e}")
            return False

    def update_config_setting(
        self, section: str, key: str, value: Any, config_path: Optional[str] = None
    ) -> bool:
        """Update a specific setting without affecting other settings.

        This method only updates the specified setting in the existing config file,
        preserving other settings and not adding environment-only values.

        Args:
            section: The section name (e.g., 'lab', 'remote')
            key: The setting key (e.g., 'current_lab')
            value: The new value
            config_path: Optional path to config file
        """
        if config_path is None:
            if self.config_file:
                config_path = self.config_file
            else:
                # Create config.local.yaml as default
                config_path = "config.local.yaml"

        try:
            # Load existing config file
            config_data = {}
            if Path(config_path).exists():
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f) or {}

            # Update only the specific setting
            if section not in config_data:
                config_data[section] = {}
            config_data[section][key] = value

            # Save back to file
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            return True
        except Exception as e:
            print(f"Warning: Could not update config file {config_path}: {e}")
            return False


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
