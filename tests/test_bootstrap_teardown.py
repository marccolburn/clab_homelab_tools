"""
Test bootstrap and teardown commands for complete lab lifecycle management.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from clab_tools.main import cli


@pytest.fixture
def topology_file(tmp_path):
    """Create a sample topology file."""
    topology_content = """name: test-topology
topology:
  nodes:
    router1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux
"""
    topology_file = tmp_path / "test-topology.yml"
    topology_file.write_text(topology_content)
    return str(topology_file)


def test_bootstrap_command_help():
    """Test that lab bootstrap command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["lab", "bootstrap", "--help"])

    assert result.exit_code == 0
    assert "Bootstrap a complete lab environment" in result.output
    assert "--nodes" in result.output
    assert "--connections" in result.output
    assert "--output" in result.output
    assert "--no-start" in result.output
    assert "--skip-vlans" in result.output
    assert "--dry-run" in result.output


def test_teardown_command_help():
    """Test that lab teardown command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["lab", "teardown", "--help"])

    assert result.exit_code == 0
    assert "Teardown a complete lab environment" in result.output
    assert "--topology" in result.output
    assert "--keep-data" in result.output
    assert "--dry-run" in result.output


@patch("subprocess.run")
def test_bootstrap_dry_run(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test bootstrap command with dry-run flag."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "DRY RUN" in result.output or "dry run" in result.output
    assert "Would execute" in result.output or "Preview" in result.output
    # Should not actually call subprocess for real operations
    mock_run.assert_not_called()


@patch("subprocess.run")
def test_bootstrap_full_workflow(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test bootstrap command executes full workflow."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0

    # Should call multiple subprocess commands for the workflow
    assert mock_run.call_count >= 3  # At least data import, topology generate, etc.

    # Check that expected workflow steps were mentioned
    assert "Importing CSV data" in result.output
    assert "Generating topology" in result.output


@patch("subprocess.run")
def test_bootstrap_no_start_option(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test bootstrap command with --no-start option."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
            "--no-start",
        ],
    )

    assert result.exit_code == 0

    # Should skip starting topology but still do other steps
    assert (
        "Skipping topology start" in result.output or "start: skipped" in result.output
    )

    # Verify start command was not called
    call_commands = [str(call) for call in mock_run.call_args_list]
    assert not any(
        "topology start" in cmd or "clab deploy" in cmd for cmd in call_commands
    )


@patch("subprocess.run")
def test_bootstrap_skip_vlans_option(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test bootstrap command with --skip-vlans option."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
            "--skip-vlans",
        ],
    )

    assert result.exit_code == 0

    # Should skip VLAN configuration
    assert (
        "Skipping VLAN configuration" in result.output
        or "VLANs: skipped" in result.output
    )

    # Verify bridge configure was not called
    call_commands = [str(call) for call in mock_run.call_args_list]
    assert not any("bridge configure" in cmd for cmd in call_commands)


@patch("subprocess.run")
def test_bootstrap_with_quiet_mode(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test bootstrap command with --quiet flag."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "--quiet",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0

    # Should have minimal output in quiet mode
    lines = result.output.strip().split("\n")
    assert len(lines) < 10  # Arbitrary threshold for "minimal output"


@patch("subprocess.run")
def test_bootstrap_subprocess_failure(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test bootstrap command when subprocess command fails."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    # Mock subprocess failure
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "Command failed"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code != 0
    assert "failed" in result.output.lower() or "error" in result.output.lower()


@patch("subprocess.run")
def test_teardown_dry_run(mock_run, topology_file, tmp_path):
    """Test teardown command with dry-run flag."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "teardown",
            "--topology",
            topology_file,
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "DRY RUN" in result.output or "dry run" in result.output
    assert "Would execute" in result.output or "Preview" in result.output
    # Should not actually call subprocess for real operations
    mock_run.assert_not_called()


@patch("subprocess.run")
def test_teardown_full_workflow(mock_run, topology_file, tmp_path):
    """Test teardown command executes full workflow."""
    db_file = tmp_path / "test.db"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    # Create lab first
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
            "lab",
            "teardown",
            "--topology",
            topology_file,
        ],
    )

    assert result.exit_code == 0

    # Should call multiple subprocess commands
    assert mock_run.call_count >= 2  # At least stop topology and cleanup bridges

    # Check workflow steps
    assert "Stopping topology" in result.output
    assert "Cleaning up bridges" in result.output
    assert "Clearing data" in result.output


@patch("subprocess.run")
def test_teardown_keep_data_option(mock_run, topology_file, tmp_path):
    """Test teardown command with --keep-data option."""
    db_file = tmp_path / "test.db"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    # Create lab first
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
            "lab",
            "teardown",
            "--topology",
            topology_file,
            "--keep-data",
        ],
    )

    assert result.exit_code == 0

    # Should skip data clearing
    assert "Keeping database data" in result.output or "data: kept" in result.output

    # Verify data clear was not called
    call_commands = [str(call) for call in mock_run.call_args_list]
    assert not any("data clear" in cmd for cmd in call_commands)


@patch("subprocess.run")
def test_teardown_with_quiet_mode(mock_run, topology_file, tmp_path):
    """Test teardown command with --quiet flag."""
    db_file = tmp_path / "test.db"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    # Create lab first
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
            "lab",
            "teardown",
            "--topology",
            topology_file,
        ],
    )

    assert result.exit_code == 0

    # Should have minimal output in quiet mode
    lines = result.output.strip().split("\n")
    assert len(lines) < 8  # Arbitrary threshold for "minimal output"


@patch("subprocess.run")
def test_teardown_subprocess_failure(mock_run, topology_file, tmp_path):
    """Test teardown command when subprocess command fails."""
    db_file = tmp_path / "test.db"

    # Mock subprocess failure
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "Command failed"

    runner = CliRunner()
    # Create lab first
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
            "lab",
            "teardown",
            "--topology",
            topology_file,
        ],
    )

    assert result.exit_code != 0
    assert "failed" in result.output.lower() or "error" in result.output.lower()


def test_bootstrap_missing_required_arguments(tmp_path):
    """Test bootstrap command with missing required arguments."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()

    # Missing --nodes
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--connections",
            "connections.csv",
            "--output",
            "topology.yml",
        ],
    )
    assert result.exit_code != 0

    # Missing --connections
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            "nodes.csv",
            "--output",
            "topology.yml",
        ],
    )
    assert result.exit_code != 0

    # Missing --output
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            "nodes.csv",
            "--connections",
            "connections.csv",
        ],
    )
    assert result.exit_code != 0


def test_teardown_missing_topology_argument(tmp_path):
    """Test teardown command with missing --topology argument."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db-url", f"sqlite:///{db_file}", "lab", "teardown"])

    assert result.exit_code != 0
    assert "required" in result.output.lower() or "missing" in result.output.lower()


def test_bootstrap_nonexistent_csv_files(tmp_path):
    """Test bootstrap command with nonexistent CSV files."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "bootstrap",
            "--nodes",
            "/nonexistent/nodes.csv",
            "--connections",
            "/nonexistent/connections.csv",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code != 0
    assert (
        "does not exist" in result.output
        or "No such file" in result.output
        or "not found" in result.output
    )


def test_teardown_nonexistent_topology_file(tmp_path):
    """Test teardown command with nonexistent topology file."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "teardown",
            "--topology",
            "/nonexistent/topology.yml",
        ],
    )

    assert result.exit_code != 0
    assert (
        "does not exist" in result.output
        or "No such file" in result.output
        or "not found" in result.output
    )


@patch("subprocess.run")
def test_bootstrap_preserves_context(
    mock_run, sample_nodes_csv, sample_connections_csv, tmp_path
):
    """Test that bootstrap command preserves context (lab, config) for sub-commands."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    # Mock all subprocess calls to succeed
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Command successful"
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "--lab",
            "custom-lab",
            "lab",
            "bootstrap",
            "--nodes",
            sample_nodes_csv,
            "--connections",
            sample_connections_csv,
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0

    # Check that subprocess calls include the context options
    for call in mock_run.call_args_list:
        call_str = str(call)
        if "data import" in call_str or "topology generate" in call_str:
            assert "--db-url" in call_str
            assert str(db_file) in call_str
