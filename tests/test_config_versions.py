"""Tests for the config-versions command."""

import pytest
import yaml
from click.testing import CliRunner

from wcheck.wcheck import cli, compare_config_versions


class TestConfigVersionsCommand:
    """Tests for the config-versions CLI command."""

    def test_config_versions_help(self):
        """Test config-versions command help displays correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "--help"])
        assert result.exit_code == 0
        assert "Compare versions of a config file across git branches" in result.output

    def test_config_versions_missing_config(self):
        """Test config-versions command without config file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_config_versions_nonexistent_config(self, tmp_path):
        """Test config-versions command with nonexistent config file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(nonexistent)])
        assert result.exit_code != 0

    def test_config_versions_valid_config_repo(self, config_repo):
        """Test config-versions command with a valid config in a git repo."""
        repo_path, config_path = config_repo
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path)])
        assert result.exit_code == 0

    def test_config_versions_with_full_flag(self, config_repo):
        """Test config-versions command with --full flag."""
        repo_path, config_path = config_repo
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path), "--full"])
        assert result.exit_code == 0

    def test_config_versions_with_verbose_flag(self, config_repo):
        """Test config-versions command with --verbose flag."""
        repo_path, config_path = config_repo
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path), "-v"])
        assert result.exit_code == 0

    def test_config_versions_with_filter(self, config_repo):
        """Test config-versions command with --filter option."""
        repo_path, config_path = config_repo
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path), "--filter", "main"])
        assert result.exit_code == 0

    def test_config_versions_with_multiple_filters(self, config_repo):
        """Test config-versions command with multiple --filter options."""
        repo_path, config_path = config_repo
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path), "--filter", "main", "--filter", "develop"])
        assert result.exit_code == 0

    def test_config_versions_not_in_git_repo(self, tmp_path):
        """Test config-versions command with config not in a git repo."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "repositories": {
                "repo_a": {"version": "main"},
            }
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path)])
        assert result.exit_code == 0
        # Should print message about not being in a git repo
        assert "not inside a git repository" in result.output

    def test_config_versions_dirty_repo_no_stash(self, config_repo):
        """Test config-versions command with dirty repo and no stash."""
        repo_path, config_path = config_repo
        from git import Repo

        repo = Repo(repo_path)

        # Make the repo dirty
        new_file = repo_path / "new_file.txt"
        new_file.write_text("New content\n")
        repo.index.add(["new_file.txt"])

        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path)])
        assert result.exit_code == 0
        # Should mention repo is not clean
        assert "not clean" in result.output

    def test_config_versions_dirty_repo_with_stash(self, config_repo):
        """Test config-versions command with dirty repo and --stash flag."""
        repo_path, config_path = config_repo
        from git import Repo

        repo = Repo(repo_path)

        # Make the repo dirty
        new_file = repo_path / "new_file.txt"
        new_file.write_text("New content\n")
        repo.index.add(["new_file.txt"])

        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path), "--stash"])
        assert result.exit_code == 0
        # Should stash and restore changes
        assert "Stashing" in result.output or "stash" in result.output.lower()

    def test_config_versions_show_time_flag(self, config_repo):
        """Test config-versions command with --show-time flag."""
        repo_path, config_path = config_repo
        runner = CliRunner()
        result = runner.invoke(cli, ["config-versions", "-c", str(config_path), "--show-time"])
        assert result.exit_code == 0


class TestCompareConfigVersions:
    """Tests for the compare_config_versions function directly."""

    def test_compare_config_versions_shows_branches(self, config_repo, capsys):
        """Test that compare_config_versions shows different branch versions."""
        repo_path, config_path = config_repo
        compare_config_versions(str(config_path), full=True)
        captured = capsys.readouterr()
        # Should include output about the comparison
        assert "Comparing" in captured.out or "main" in captured.out or "develop" in captured.out
