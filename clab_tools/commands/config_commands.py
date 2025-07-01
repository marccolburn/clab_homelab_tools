"""
Configuration Management Commands

Provides commands for viewing and managing clab-tools configuration settings.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import click
import yaml

from clab_tools.common.utils import handle_error
from clab_tools.config.settings import Settings, find_config_file


def get_config_source(settings: Settings, key_path: str, value: Any) -> str:
    """Determine the source of a configuration value."""
    # Check if value matches an environment variable
    env_prefix = "CLAB_"
    env_key = env_prefix + key_path.upper().replace(".", "_")

    if env_key in os.environ:
        env_value = os.environ[env_key]
        # Convert string to appropriate type for comparison
        if isinstance(value, bool):
            if env_value.lower() in ("true", "1", "yes"):
                env_value = True
            elif env_value.lower() in ("false", "0", "no"):
                env_value = False
        elif isinstance(value, int):
            try:
                env_value = int(env_value)
            except ValueError:
                pass

        if str(env_value) == str(value):
            return "env"

    # Check if value is from config file
    if settings.config_file and Path(settings.config_file).exists():
        with open(settings.config_file, "r") as f:
            config_data = yaml.safe_load(f)

        # Navigate through nested structure
        current = config_data
        for part in key_path.split("."):
            if current and isinstance(current, dict) and part in current:
                current = current[part]
            else:
                current = None
                break

        if current is not None and str(current) == str(value):
            return "file"

    return "default"


def format_settings_tree(
    settings: Settings, show_source: bool = True
) -> Dict[str, Any]:
    """Format settings into a tree structure with sources."""
    result = {}

    # Process each settings section
    for section_name in [
        "database",
        "logging",
        "topology",
        "lab",
        "bridges",
        "remote",
        "node",
        "vendor",
    ]:
        section = getattr(settings, section_name)
        section_dict = {}

        for field_name, field_value in section.model_dump().items():
            key_path = f"{section_name}.{field_name}"

            if show_source:
                source = get_config_source(settings, key_path, field_value)
                section_dict[field_name] = {"value": field_value, "source": source}
            else:
                section_dict[field_name] = field_value

        result[section_name] = section_dict

    # Add top-level settings
    for field_name in ["debug", "config_file"]:
        field_value = getattr(settings, field_name)
        if show_source:
            source = get_config_source(settings, field_name, field_value)
            result[field_name] = {"value": field_value, "source": source}
        else:
            result[field_name] = field_value

    return result


def print_settings_tree(
    data: Dict[str, Any], indent: int = 0, show_source: bool = True
):
    """Print settings in a tree format."""
    for key, value in data.items():
        prefix = "  " * indent

        if isinstance(value, dict) and not (show_source and "value" in value):
            # This is a section
            click.echo(f"{prefix}{click.style(key + ':', fg='cyan', bold=True)}")
            print_settings_tree(value, indent + 1, show_source)
        else:
            # This is a field
            if show_source and isinstance(value, dict) and "value" in value:
                val = value["value"]
                source = value["source"]
                source_color = {
                    "env": "green",
                    "file": "yellow",
                    "default": "white",
                }.get(source, "white")
                source_label = f"[{source}]"

                # Handle sensitive values
                if key in ["password", "default_password", "sudo_password"]:
                    val = "****" if val else None

                click.echo(
                    f"{prefix}{key}: {val} {click.style(source_label, fg=source_color)}"
                )
            else:
                # Handle sensitive values
                if key in ["password", "default_password", "sudo_password"]:
                    value = "****" if value else None
                click.echo(f"{prefix}{key}: {value}")


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["tree", "json", "yaml"]),
    default="tree",
    help="Output format",
)
@click.option(
    "--show-source/--no-show-source",
    "-s",
    default=True,
    help="Show the source of each setting (env/file/default)",
)
@click.option("--section", type=str, help="Show only a specific section")
@click.pass_context
def show(ctx, format, show_source, section):
    """Show current configuration settings and their sources."""
    settings = ctx.obj.get("settings")
    if not settings:
        handle_error("Settings not available in context")
        return

    # Format the settings
    formatted_settings = format_settings_tree(settings, show_source)

    # Filter by section if requested
    if section:
        if section in formatted_settings:
            formatted_settings = {section: formatted_settings[section]}
        else:
            handle_error(f"Unknown section: {section}")
            return

    # Display based on format
    if format == "json":
        click.echo(json.dumps(formatted_settings, indent=2))
    elif format == "yaml":
        click.echo(yaml.dump(formatted_settings, default_flow_style=False))
    else:  # tree format
        # Show config file location if available
        if settings.config_file:
            click.echo(
                f"Configuration file: {click.style(settings.config_file, fg='yellow')}"
            )
        else:
            config_file = find_config_file()
            if config_file:
                click.echo(
                    f"Configuration file found but not loaded: "
                    f"{click.style(config_file, fg='red')}"
                )
            else:
                click.echo(click.style("No configuration file found", fg="red"))
        click.echo()

        print_settings_tree(formatted_settings, show_source=show_source)

        if show_source:
            click.echo()
            click.echo(
                "Sources: "
                + click.style("[env]", fg="green")
                + " environment, "
                + click.style("[file]", fg="yellow")
                + " config file, "
                + click.style("[default]", fg="white")
                + " default value"
            )


@click.command()
@click.pass_context
def list_env(ctx):
    """List all CLAB environment variables."""
    clab_vars = {k: v for k, v in os.environ.items() if k.startswith("CLAB_")}

    if not clab_vars:
        click.echo("No CLAB environment variables set")
        return

    click.echo(click.style("CLAB Environment Variables:", fg="cyan", bold=True))
    for key, value in sorted(clab_vars.items()):
        # Mask sensitive values
        if any(sensitive in key for sensitive in ["PASSWORD", "KEY"]):
            value = "****" if value else ""
        click.echo(f"  {key}={value}")


@click.group()
def config_commands():
    """Configuration management commands."""
    pass


# Add commands to the group
config_commands.add_command(show)
config_commands.add_command(list_env, name="env")
