"""Tests for the wconfig command."""

import pytest
from click.testing import CliRunner

from wcheck.wcheck import cli, compare_workspace_to_config


class TestWConfigCommand:
    """Tests for the wconfig CLI command."""

    def test_wconfig_help(self):
        """Test wconfig command help displays correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "--help"])
        assert result.exit_code == 0
        assert "Compare the workspace with a configuration file" in result.output

    def test_wconfig_missing_config(self, temp_workspace):
        """Test wconfig command without config file."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace)])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_wconfig_with_config(self, temp_workspace, config_file):
        """Test wconfig command with valid config."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace), "-c", str(config_file)])
        assert result.exit_code == 0

    def test_wconfig_default_workspace(self, temp_workspace, config_file):
        """Test wconfig command uses current directory when no workspace specified."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Copy config to isolated filesystem
            import shutil
            config_copy = "config.yaml"
            shutil.copy(config_file, config_copy)
            result = runner.invoke(cli, ["wconfig", "-c", config_copy])
            assert result.exit_code == 0
            assert "using current directory" in result.output

    def test_wconfig_with_full_flag(self, temp_workspace, config_file):
        """Test wconfig command with --full flag."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace), "-c", str(config_file), "--full"])
        assert result.exit_code == 0

    def test_wconfig_with_verbose_flag(self, temp_workspace, config_file):
        """Test wconfig command with --verbose flag."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace), "-c", str(config_file), "-v"])
        assert result.exit_code == 0

    def test_wconfig_nonexistent_config(self, temp_workspace, tmp_path):
        """Test wconfig command with nonexistent config file."""
        workspace, repos = temp_workspace
        nonexistent_config = tmp_path / "nonexistent.yaml"
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace), "-c", str(nonexistent_config)])
        assert result.exit_code != 0

    def test_wconfig_show_time_flag(self, temp_workspace, config_file):
        """Test wconfig command with --show-time flag."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace), "-c", str(config_file), "--show-time"])
        assert result.exit_code == 0

    def test_wconfig_mismatched_versions(self, temp_workspace, tmp_path):
        """Test wconfig command detects version mismatches."""
        workspace, repos = temp_workspace
        import yaml

        # Create config that doesn't match the workspace
        config_path = tmp_path / "mismatch.yaml"
        config_data = {
            "repositories": {
                "repo_a": {"version": "nonexistent-branch"},
                "repo_b": {"version": "main"},
            }
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        runner = CliRunner()
        result = runner.invoke(cli, ["wconfig", "-w", str(workspace), "-c", str(config_path)])
        assert result.exit_code == 0
        # The output should show the comparison
        assert "repo_a" in result.output or "Workspace" in result.output
