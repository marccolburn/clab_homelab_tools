"""
Test quiet mode functionality for non-interactive scripting.
"""

from unittest.mock import patch

from click.testing import CliRunner

from clab_tools.main import cli


def test_quiet_flag_help():
    """Test that --quiet flag appears in help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--quiet" in result.output or "-q" in result.output
    assert "Suppress interactive prompts" in result.output


def test_lab_create_without_quiet_prompts_switch(tmp_path):
    """Test that lab create normally prompts to switch labs."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # First create a lab to make switch prompt appear
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "lab", "create", "existing-lab"],
        input="y\n",  # Confirm switch
    )
    assert result.exit_code == 0

    # Now create another lab which should prompt to switch
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "lab",
            "create",
            "new-lab",
            "-d",
            "Test lab",
        ],
        input="n\n",  # Don't switch
    )

    assert result.exit_code == 0
    assert "Switch to lab 'new-lab'?" in result.output


def test_lab_create_with_quiet_no_prompts(tmp_path):
    """Test that lab create with --quiet doesn't prompt to switch."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # First create a lab
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "--quiet",
            "lab",
            "create",
            "existing-lab",
        ],
    )
    assert result.exit_code == 0

    # Create another lab with quiet mode - should not prompt
    result = runner.invoke(
        cli,
        [
            "--db-url",
            f"sqlite:///{db_file}",
            "--quiet",
            "lab",
            "create",
            "new-lab",
            "-d",
            "Test lab",
        ],
    )

    assert result.exit_code == 0
    assert "Switch to lab" not in result.output
    assert "✓" in result.output  # Should show success message


def test_lab_delete_without_quiet_prompts_confirmation(tmp_path):
    """Test that lab delete normally prompts for confirmation."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # Create a lab first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Try to delete without quiet mode - should prompt
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "lab", "delete", "test-lab"],
        input="y\n",  # Confirm deletion
    )

    assert result.exit_code == 0
    assert "Are you sure" in result.output or "Delete lab" in result.output


def test_lab_delete_with_quiet_no_prompts(tmp_path):
    """Test that lab delete with --quiet doesn't prompt for confirmation."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # Create a lab first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Delete with quiet mode - should not prompt
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "delete", "test-lab"],
    )

    assert result.exit_code == 0
    assert "Are you sure" not in result.output
    assert "Delete lab" not in result.output


def test_lab_delete_with_force_no_prompts(tmp_path):
    """Test that lab delete with --force doesn't prompt (quiet mode alternative)."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # Create a lab first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Delete with force flag - should not prompt
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "lab", "delete", "test-lab", "--force"],
    )

    assert result.exit_code == 0
    assert "Are you sure" not in result.output


def test_data_clear_without_quiet_prompts_confirmation(tmp_path):
    """Test that data clear normally prompts for confirmation."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # Create lab and add some data
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Try to clear without quiet mode - should prompt
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "data", "clear"],
        input="y\n",  # Confirm clearing
    )

    assert result.exit_code == 0
    assert (
        "This will clear ALL data from lab" in result.output
        or "Continue?" in result.output
    )


def test_data_clear_with_quiet_no_prompts(tmp_path):
    """Test that data clear with --quiet doesn't prompt for confirmation."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # Create lab first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Clear with quiet mode - should not prompt
    result = runner.invoke(
        cli, ["--db-url", f"sqlite:///{db_file}", "--quiet", "data", "clear"]
    )

    assert result.exit_code == 0
    assert "Are you sure" not in result.output
    assert "clear all data" not in result.output


def test_data_clear_with_force_no_prompts(tmp_path):
    """Test that data clear with --force doesn't prompt."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()
    # Create lab first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Clear with force flag - should not prompt
    result = runner.invoke(
        cli, ["--db-url", f"sqlite:///{db_file}", "data", "clear", "--force"]
    )

    assert result.exit_code == 0
    assert "Are you sure" not in result.output


def test_quiet_mode_environment_variable(tmp_path):
    """Test that CLAB_QUIET environment variable works."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()

    # Test with environment variable set
    with patch.dict("os.environ", {"CLAB_QUIET": "true"}):
        # Create first lab to enable switching prompt scenario
        result = runner.invoke(
            cli, ["--db-url", f"sqlite:///{db_file}", "lab", "create", "first-lab"]
        )
        assert result.exit_code == 0

        # Create second lab - should not prompt to switch due to env var
        result = runner.invoke(
            cli, ["--db-url", f"sqlite:///{db_file}", "lab", "create", "env-test-lab"]
        )

        assert result.exit_code == 0
        # Should behave as if --quiet was used
        assert "Switch to lab" not in result.output


def test_quiet_flag_overrides_environment(tmp_path):
    """Test that --quiet flag works even without environment variable."""
    db_file = tmp_path / "test.db"

    runner = CliRunner()

    # Test with explicit flag (no env var)
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(
            cli,
            [
                "--db-url",
                f"sqlite:///{db_file}",
                "--quiet",
                "lab",
                "create",
                "flag-test-lab",
            ],
        )

        assert result.exit_code == 0
        assert "Switch to lab" not in result.output


def test_bootstrap_with_quiet_no_prompts(
    tmp_path, sample_nodes_csv, sample_connections_csv
):
    """Test that bootstrap command respects quiet mode."""
    db_file = tmp_path / "test.db"
    output_file = tmp_path / "topology.yml"

    runner = CliRunner()

    # Mock subprocess calls for bootstrap sub-commands
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

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
                "--dry-run",  # Use dry-run to avoid actual system operations
            ],
        )

        assert result.exit_code == 0
        # Should not contain any interactive prompts
        assert "?" not in result.output
        assert "Are you sure" not in result.output


def test_teardown_with_quiet_no_prompts(tmp_path):
    """Test that teardown command respects quiet mode."""
    db_file = tmp_path / "test.db"
    topology_file = tmp_path / "test-topology.yml"
    topology_file.write_text("name: test-topology\ntopology:\n  nodes: {}")

    runner = CliRunner()

    # Create lab first
    result = runner.invoke(
        cli,
        ["--db-url", f"sqlite:///{db_file}", "--quiet", "lab", "create", "test-lab"],
    )
    assert result.exit_code == 0

    # Mock subprocess calls for teardown sub-commands
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        result = runner.invoke(
            cli,
            [
                "--db-url",
                f"sqlite:///{db_file}",
                "--quiet",
                "lab",
                "teardown",
                "--topology",
                str(topology_file),
                "--dry-run",  # Use dry-run to avoid actual system operations
            ],
        )

        assert result.exit_code == 0
        # Should not contain any interactive prompts
        assert "?" not in result.output
        assert "Are you sure" not in result.output
