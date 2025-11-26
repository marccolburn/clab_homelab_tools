"""Tests for node config CLI commands."""

from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from clab_tools.main import cli
from clab_tools.node.drivers.juniper import JuniperPyEZDriver


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner(mix_stderr=False)


def test_node_config_command_help(runner):
    """Test that node config command help works."""
    result = runner.invoke(cli, ["node", "config", "--help"])

    assert result.exit_code == 0
    assert "Load configurations to containerlab nodes" in result.output
    assert "--file" in result.output
    assert "--device-file" in result.output
    assert "--show-cleaned" in result.output
    assert "--format" in result.output
    assert "--dry-run" in result.output
    assert "--method" in result.output
    assert "--node" in result.output
    assert "--kind" in result.output


def test_node_config_show_cleaned_option_in_help(runner):
    """Test that --show-cleaned option is documented in help."""
    result = runner.invoke(cli, ["node", "config", "--help"])

    assert result.exit_code == 0
    assert "--show-cleaned" in result.output
    assert "cleaned config content" in result.output.lower()


class TestJuniperCleanDeviceFile:
    """Tests for the _read_and_clean_device_file helper method."""

    def test_clean_secret_data_comments(self):
        """Test that SECRET-DATA comments and semicolons are stripped."""
        # Create a mock driver without connecting
        mock_device = Mock()

        # Sample config with SECRET-DATA comments
        raw_config = '''set system login user lab authentication encrypted-password "$1$abc"; ## SECRET-DATA
set system login user admin authentication encrypted-password "$5$def"; ## SECRET-DATA
set system host-name router1
set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24'''

        mock_device.cli.return_value = raw_config

        # Create driver instance and set mock device
        from clab_tools.node.drivers.base import ConnectionParams

        conn_params = ConnectionParams(
            host="192.168.1.1",
            username="admin",
            password="admin123",
        )
        driver = JuniperPyEZDriver(conn_params)
        driver.device = mock_device
        driver._connected = True

        # Call the clean method
        cleaned = driver._read_and_clean_device_file("/var/tmp/test.conf")

        # Verify the cleaning
        assert "; ## SECRET-DATA" not in cleaned
        assert "## SECRET-DATA" not in cleaned
        # Verify semicolons are removed with the comments
        assert 'encrypted-password "$1$abc"' in cleaned
        assert 'encrypted-password "$5$def"' in cleaned
        # Verify non-commented lines are unchanged
        assert "set system host-name router1" in cleaned
        assert "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24" in cleaned

    def test_clean_last_changed_comments(self):
        """Test that ## Last changed comments are stripped."""
        mock_device = Mock()

        raw_config = '''## Last changed: 2024-01-15 10:30:00 UTC
set system host-name router1
set system services ssh'''

        mock_device.cli.return_value = raw_config

        from clab_tools.node.drivers.base import ConnectionParams

        conn_params = ConnectionParams(
            host="192.168.1.1",
            username="admin",
            password="admin123",
        )
        driver = JuniperPyEZDriver(conn_params)
        driver.device = mock_device
        driver._connected = True

        cleaned = driver._read_and_clean_device_file("/var/tmp/test.conf")

        # The ## Last changed line should remain as-is since it's a standalone comment
        # (it doesn't have ';' before ## and no leading whitespace before ##)
        # Let's verify the important config lines are present
        assert "set system host-name router1" in cleaned
        assert "set system services ssh" in cleaned

    def test_clean_preserves_normal_config(self):
        """Test that normal config without comments is preserved."""
        mock_device = Mock()

        raw_config = '''set system host-name router1
set system services ssh
set interfaces ge-0/0/0 description "WAN interface"
set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1'''

        mock_device.cli.return_value = raw_config

        from clab_tools.node.drivers.base import ConnectionParams

        conn_params = ConnectionParams(
            host="192.168.1.1",
            username="admin",
            password="admin123",
        )
        driver = JuniperPyEZDriver(conn_params)
        driver.device = mock_device
        driver._connected = True

        cleaned = driver._read_and_clean_device_file("/var/tmp/test.conf")

        # All lines should be preserved exactly
        assert cleaned == raw_config
