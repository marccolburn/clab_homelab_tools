"""
Test node upload functionality for file uploads to containerlab nodes.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from clab_tools.main import cli


@pytest.fixture
def setup_test_nodes():
    """Fixture that returns a function to add test nodes to the database."""

    def _setup_nodes(db_file, lab_name="test-lab"):
        from clab_tools.config.settings import get_settings
        from clab_tools.db.manager import DatabaseManager

        settings = get_settings()
        settings.database.url = f"sqlite:///{db_file}"
        db = DatabaseManager(settings.database)

        # Add some test nodes
        db.insert_node("router1", "nokia_srlinux", "192.168.1.1", lab_name=lab_name)
        db.insert_node("router2", "nokia_srlinux", "192.168.1.2", lab_name=lab_name)
        db.insert_node("switch1", "bridge", "192.168.1.10", lab_name=lab_name)

        return db

    return _setup_nodes


@pytest.fixture
def source_file(tmp_path):
    """Create a source file to upload."""
    source_file = tmp_path / "config.txt"
    source_file.write_text("test configuration content")
    return str(source_file)


@pytest.fixture
def source_dir(tmp_path):
    """Create a source directory with files to upload."""
    source_dir = tmp_path / "configs"
    source_dir.mkdir()
    (source_dir / "router.conf").write_text("router config")
    (source_dir / "switch.conf").write_text("switch config")
    return str(source_dir)


def test_node_upload_command_help():
    """Test that node upload command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["node", "upload", "--help"])

    assert result.exit_code == 0
    assert "Upload files or directories to containerlab nodes" in result.output
    assert "--node" in result.output
    assert "--kind" in result.output
    assert "--nodes" in result.output
    assert "--all" in result.output
    assert "--source" in result.output
    assert "--source-dir" in result.output
    assert "--dest" in result.output


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_to_specific_node(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload to specific node by name."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
    ]

    runner = CliRunner()
    # Create lab and add test data first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["node_name"] == "router1"
    assert call_args[1]["remote_dest"] == "/tmp/config.txt"
    assert call_args[1]["kind"] is None
    assert call_args[1]["nodes_list"] is None
    assert call_args[1]["all_nodes"] is False


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_to_all_nodes(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload to all nodes in lab."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
        ("router2", True, "Upload successful"),
        ("switch1", True, "Upload successful"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--all",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["all_nodes"] is True
    assert call_args[1]["node_name"] is None
    assert call_args[1]["kind"] is None
    assert call_args[1]["nodes_list"] is None


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_by_kind(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload to all nodes of specific kind."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
        ("router2", True, "Upload successful"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--kind",
            "nokia_srlinux",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["kind"] == "nokia_srlinux"
    assert call_args[1]["node_name"] is None
    assert call_args[1]["all_nodes"] is False
    assert call_args[1]["nodes_list"] is None


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_to_node_list(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload to comma-separated list of nodes."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
        ("router2", True, "Upload successful"),
        ("switch1", True, "Upload successful"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--nodes",
            "router1,router2,switch1",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["nodes_list"] == ["router1", "router2", "switch1"]
    assert call_args[1]["node_name"] is None
    assert call_args[1]["kind"] is None
    assert call_args[1]["all_nodes"] is False


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_directory(mock_upload, source_dir, tmp_path, setup_test_nodes):
    """Test upload of directory with recursive copy."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Directory uploaded"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--source-dir",
            source_dir,
            "--dest",
            "/etc/configs",
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["is_directory"] is True
    assert source_dir in str(call_args[1]["local_source"])


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_with_custom_credentials(
    mock_upload, source_file, tmp_path, setup_test_nodes
):
    """Test upload with custom SSH credentials."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
            "--user",
            "admin",
            "--password",
            "secret",
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["username"] == "admin"
    assert call_args[1]["password"] == "secret"


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_with_ssh_key(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload with SSH private key authentication."""
    db_file = tmp_path / "test.db"
    key_file = tmp_path / "test_key"
    key_file.write_text("fake private key content")

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
            "--private-key",
            str(key_file),
        ],
    )

    assert result.exit_code == 0
    mock_upload.assert_called_once()

    # Check the call arguments
    call_args = mock_upload.call_args
    assert call_args[1]["private_key_path"] == str(key_file)


def test_upload_missing_source_file(tmp_path):
    """Test upload with missing source file."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--source",
            "/nonexistent/file.txt",
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code != 0
    assert (
        "does not exist" in result.output
        or "No such file" in result.output
        or "not found" in result.output
    )


def test_upload_no_target_specified(source_file, tmp_path):
    """Test upload without specifying target nodes."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code != 0
    assert (
        "Must specify exactly one of: --node, --kind, --nodes, or --all"
        in result.output
    )


def test_upload_multiple_targets_specified(source_file, tmp_path):
    """Test upload with multiple conflicting target options."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--all",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code != 0
    assert (
        "Must specify exactly one of: --node, --kind, --nodes, or --all"
        in result.output
    )


def test_upload_both_source_and_source_dir(source_file, source_dir, tmp_path):
    """Test upload with both --source and --source-dir specified."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--node",
            "router1",
            "--source",
            source_file,
            "--source-dir",
            source_dir,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code != 0
    assert "Must specify exactly one of: --source or --source-dir" in result.output


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_with_failures(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload with some node failures."""
    db_file = tmp_path / "test.db"

    # Mock upload with some failures - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
        ("router2", True, "Upload successful"),
        ("router3", False, "SSH connection failed"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "node",
            "upload",
            "--all",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    # Should exit with error code 1 since there were failures
    assert result.exit_code == 1
    assert "Successful: 2" in result.output
    assert "Failed: 1" in result.output


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_with_quiet_mode(mock_upload, source_file, tmp_path, setup_test_nodes):
    """Test upload with --quiet flag suppresses detailed output."""
    db_file = tmp_path / "test.db"

    # Mock successful upload - return list of tuples as expected
    mock_upload.return_value = [
        ("router1", True, "Upload successful"),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Add nodes to database
    setup_test_nodes(db_file, "test-lab")

    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "--quiet",
            "node",
            "upload",
            "--node",
            "router1",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    assert result.exit_code == 0
    # In quiet mode, output should not have summary
    assert "Upload Summary" not in result.output
