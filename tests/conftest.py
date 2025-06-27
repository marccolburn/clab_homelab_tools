"""Test configuration and fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest

from clab_tools.config.settings import DatabaseSettings, LoggingSettings, Settings
from clab_tools.db.context import LabAwareDB
from clab_tools.db.manager import DatabaseManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_db_settings():
    """Create test database settings."""
    return DatabaseSettings(url="sqlite:///:memory:", echo=False, pool_pre_ping=False)


@pytest.fixture
def test_logging_settings():
    """Create test logging settings."""
    return LoggingSettings(level="DEBUG", format="console")


@pytest.fixture
def test_settings(test_db_settings, test_logging_settings):
    """Create test application settings."""
    return Settings(
        database=test_db_settings, logging=test_logging_settings, debug=True
    )


@pytest.fixture
def db_manager(test_db_settings):
    """Create a test database manager."""
    manager = DatabaseManager(settings=test_db_settings)
    return manager


@pytest.fixture
def lab_aware_db(db_manager):
    """Create a LabAwareDB context for testing with a default lab name."""
    return LabAwareDB(db_manager, "testlab")


@pytest.fixture
def populated_db_manager(db_manager):
    """Create a database manager with test data."""
    # Create LabAwareDB context for populating test data
    lab_db = LabAwareDB(db_manager, "testlab")

    # Add test nodes
    lab_db.insert_node("router1", "nokia_srlinux", "172.20.20.10")
    lab_db.insert_node("router2", "nokia_srlinux", "172.20.20.11")
    lab_db.insert_node("switch1", "bridge", "172.20.20.20")

    # Add test connections
    lab_db.insert_connection("router1", "router2", "veth", "eth1", "eth1")
    lab_db.insert_connection("router1", "switch1", "veth", "eth2", "eth1")

    # Add test topology config
    lab_db.save_topology_config("test-lab", "test", "clab", "172.20.20.0/24")

    return db_manager


@pytest.fixture
def populated_lab_aware_db(lab_aware_db):
    """Create a populated LabAwareDB context for testing."""
    # Add test nodes
    lab_aware_db.insert_node("router1", "nokia_srlinux", "172.20.20.10")
    lab_aware_db.insert_node("router2", "nokia_srlinux", "172.20.20.11")
    lab_aware_db.insert_node("switch1", "bridge", "172.20.20.20")

    # Add test connections
    lab_aware_db.insert_connection("router1", "router2", "veth", "eth1", "eth1")
    lab_aware_db.insert_connection("router1", "switch1", "veth", "eth2", "eth1")

    # Add test topology config
    lab_aware_db.save_topology_config("test-lab", "test", "clab", "172.20.20.0/24")

    return lab_aware_db


@pytest.fixture
def sample_nodes_csv(temp_dir):
    """Create a sample nodes CSV file."""
    csv_content = """node_name,kind,mgmt_ip
router1,nokia_srlinux,172.20.20.10
router2,nokia_srlinux,172.20.20.11
switch1,bridge,172.20.20.20
"""
    csv_file = temp_dir / "test_nodes.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def sample_connections_csv(temp_dir):
    """Create a sample connections CSV file."""
    csv_content = """node1,node2,type,node1_interface,node2_interface
router1,router2,veth,eth1,eth1
router1,switch1,veth,eth2,eth1
router2,switch1,veth,eth2,eth2
"""
    csv_file = temp_dir / "test_connections.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def sample_bridge_nodes_csv(temp_dir):
    """Create a sample nodes CSV file with bridge nodes."""
    csv_content = """node_name,kind,mgmt_ip
router1,nokia_srlinux,172.20.20.10
router2,cisco_xrd,172.20.20.11
br-main,bridge,
br-access,bridge,N/A
"""
    csv_file = temp_dir / "bridge_nodes.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def sample_bridge_connections_csv(temp_dir):
    """Create a sample connections CSV file for bridge topology."""
    csv_content = """node1,node2,type,node1_interface,node2_interface
router1,br-main,veth,eth1,eth1
router2,br-main,veth,eth1,eth2
br-main,br-access,veth,trunk1,trunk1
"""
    csv_file = temp_dir / "bridge_connections.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def invalid_nodes_csv(temp_dir):
    """Create an invalid nodes CSV file (missing required columns)."""
    csv_content = """name,type,ip
router1,nokia_srlinux,172.20.20.10
"""
    csv_file = temp_dir / "invalid_nodes.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)
