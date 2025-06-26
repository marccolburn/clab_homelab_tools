"""
Test CLI integration for VLAN configuration command.
"""

from click.testing import CliRunner

from clab_tools.main import cli


def test_configure_vlans_command_help():
    """Test that configure-vlans command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["configure-vlans", "--help"])

    assert result.exit_code == 0
    assert "Configure VLANs on bridge interfaces" in result.output
    assert "--bridge" in result.output
    assert "--dry-run" in result.output


def test_configure_vlans_dry_run(tmp_path):
    """Test configure-vlans command with dry-run."""
    # Create a temporary database
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--db-url", f"sqlite:///{db_file}", "configure-vlans", "--dry-run"]
    )

    # Should succeed even with no bridges in database
    assert result.exit_code == 0
    assert "VLAN Configuration" in result.output
    assert "No bridge connections found in database" in result.output


def test_configure_vlans_specific_bridge_dry_run(tmp_path):
    """Test configure-vlans command with specific bridge and dry-run."""
    # Create a temporary database
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "configure-vlans",
            "--bridge",
            "test-bridge",
            "--dry-run",
        ],
    )

    # Should succeed even if bridge doesn't exist
    assert result.exit_code == 0
    assert "VLAN Configuration" in result.output
    assert "Configuring VLANs on bridge: test-bridge" in result.output
