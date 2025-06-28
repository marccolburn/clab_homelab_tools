"""
Test node upload functionality for file uploads to containerlab nodes.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from clab_tools.main import cli


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
def test_upload_to_specific_node(mock_upload, source_file, tmp_path):
    """Test upload to specific node by name."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 1,
        "successful": 1,
        "failed": 0,
        "results": {"router1": {"success": True, "message": "Upload successful"}},
    }

    runner = CliRunner()
    # Create lab and add test data first
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
def test_upload_to_all_nodes(mock_upload, source_file, tmp_path):
    """Test upload to all nodes in lab."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 3,
        "successful": 3,
        "failed": 0,
        "results": {
            "router1": {"success": True, "message": "Upload successful"},
            "router2": {"success": True, "message": "Upload successful"},
            "switch1": {"success": True, "message": "Upload successful"},
        },
    }

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
def test_upload_by_kind(mock_upload, source_file, tmp_path):
    """Test upload to all nodes of specific kind."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 2,
        "successful": 2,
        "failed": 0,
        "results": {
            "router1": {"success": True, "message": "Upload successful"},
            "router2": {"success": True, "message": "Upload successful"},
        },
    }

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
def test_upload_to_node_list(mock_upload, source_file, tmp_path):
    """Test upload to comma-separated list of nodes."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 3,
        "successful": 3,
        "failed": 0,
        "results": {
            "router1": {"success": True, "message": "Upload successful"},
            "router2": {"success": True, "message": "Upload successful"},
            "switch1": {"success": True, "message": "Upload successful"},
        },
    }

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
def test_upload_directory(mock_upload, source_dir, tmp_path):
    """Test upload of directory with recursive copy."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 1,
        "successful": 1,
        "failed": 0,
        "results": {"router1": {"success": True, "message": "Directory uploaded"}},
    }

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
def test_upload_with_custom_credentials(mock_upload, source_file, tmp_path):
    """Test upload with custom SSH credentials."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 1,
        "successful": 1,
        "failed": 0,
        "results": {"router1": {"success": True, "message": "Upload successful"}},
    }

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
def test_upload_with_ssh_key(mock_upload, source_file, tmp_path):
    """Test upload with SSH private key authentication."""
    db_file = tmp_path / "test.db"
    key_file = tmp_path / "test_key"
    key_file.write_text("fake private key content")

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 1,
        "successful": 1,
        "failed": 0,
        "results": {"router1": {"success": True, "message": "Upload successful"}},
    }

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
        "must specify" in result.output
        or "required" in result.output
        or "choose one" in result.output
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
        "mutually exclusive" in result.output
        or "only one" in result.output
        or "conflicting" in result.output
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
    assert (
        "mutually exclusive" in result.output
        or "only one" in result.output
        or "conflicting" in result.output
    )


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_with_failures(mock_upload, source_file, tmp_path):
    """Test upload with some node failures."""
    db_file = tmp_path / "test.db"

    # Mock upload with some failures
    mock_upload.return_value = {
        "total_nodes": 3,
        "successful": 2,
        "failed": 1,
        "results": {
            "router1": {"success": True, "message": "Upload successful"},
            "router2": {"success": True, "message": "Upload successful"},
            "router3": {"success": False, "message": "SSH connection failed"},
        },
    }

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
            "--all",
            "--source",
            source_file,
            "--dest",
            "/tmp/config.txt",
        ],
    )

    # Should still exit successfully but show failure details
    assert result.exit_code == 0
    assert "2/3" in result.output or "successful: 2" in result.output
    assert "failed: 1" in result.output or "1 failed" in result.output


@patch("clab_tools.node.manager.NodeManager.upload_to_multiple_nodes")
def test_upload_with_quiet_mode(mock_upload, source_file, tmp_path):
    """Test upload with --quiet flag suppresses detailed output."""
    db_file = tmp_path / "test.db"

    # Mock successful upload
    mock_upload.return_value = {
        "total_nodes": 1,
        "successful": 1,
        "failed": 0,
        "results": {"router1": {"success": True, "message": "Upload successful"}},
    }

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
    # In quiet mode, output should be minimal
    assert len(result.output.strip()) < 100  # Arbitrary threshold for "minimal"
