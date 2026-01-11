"""Tests for the status command."""

from click.testing import CliRunner

from wcheck.wcheck import cli, get_workspace_repos


class TestStatusCommand:
    """Tests for the status CLI command."""

    def test_status_help(self):
        """Test status command help displays correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "Check the status of all repositories" in result.output

    def test_status_no_workspace(self, tmp_path):
        """Test status command with current directory (no workspace specified)."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 0
            assert (
                "Workspace directory is not specified, using current directory"
                in result.output
            )

    def test_status_with_workspace(self, temp_workspace):
        """Test status command with a valid workspace."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "-w", str(workspace)])
        assert result.exit_code == 0
        assert f"Using workspace directory {workspace}" in result.output

    def test_status_with_full_flag(self, temp_workspace):
        """Test status command with --full flag."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "-w", str(workspace), "--full"])
        assert result.exit_code == 0

    def test_status_with_verbose_flag(self, temp_workspace):
        """Test status command with --verbose flag."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "-w", str(workspace), "-v"])
        assert result.exit_code == 0

    def test_status_with_changes(self, temp_workspace_with_changes):
        """Test status command detects uncommitted changes."""
        workspace, repos = temp_workspace_with_changes
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "-w", str(workspace)])
        assert result.exit_code == 0
        # Should show repos with changes
        assert "repo_a" in result.output or "repo_b" in result.output

    def test_status_nonexistent_workspace(self, tmp_path):
        """Test status command with a nonexistent workspace."""
        runner = CliRunner()
        nonexistent = tmp_path / "nonexistent"
        result = runner.invoke(cli, ["status", "-w", str(nonexistent)])
        assert result.exit_code != 0

    def test_status_show_time_flag(self, temp_workspace):
        """Test status command with --show-time flag."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(
            cli, ["status", "-w", str(workspace), "--show-time", "--full"]
        )
        assert result.exit_code == 0


class TestGetWorkspaceRepos:
    """Tests for the get_workspace_repos utility function."""

    def test_get_workspace_repos(self, temp_workspace):
        """Test getting repos from a workspace."""
        workspace, repos = temp_workspace
        found_repos = get_workspace_repos(workspace)
        assert len(found_repos) == 3
        assert "repo_a" in found_repos
        assert "repo_b" in found_repos
        assert "repo_c" in found_repos

    def test_get_workspace_repos_empty(self, tmp_path):
        """Test getting repos from an empty workspace."""
        empty_workspace = tmp_path / "empty"
        empty_workspace.mkdir()
        found_repos = get_workspace_repos(empty_workspace)
        assert len(found_repos) == 0

    def test_get_workspace_repos_nonexistent(self, tmp_path):
        """Test getting repos from a nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"
        found_repos = get_workspace_repos(nonexistent)
        assert len(found_repos) == 0
