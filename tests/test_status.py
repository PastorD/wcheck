"""Tests for the status command."""

from click.testing import CliRunner
from git import Repo

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


class TestMultiWorkspaceComparison:
    """Tests for comparing multiple workspaces side by side."""

    def test_status_multiple_workspaces(self, tmp_path):
        """Test status command with multiple workspaces."""
        # Create two separate workspaces
        workspace1 = tmp_path / "workspace1"
        workspace2 = tmp_path / "workspace2"
        workspace1.mkdir()
        workspace2.mkdir()

        # Create repos in workspace1
        for repo_name in ["repo_a", "repo_b"]:
            repo_path = workspace1 / repo_name
            repo_path.mkdir()
            repo = Repo.init(repo_path)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()
            readme = repo_path / "README.md"
            readme.write_text(f"# {repo_name}\n")
            repo.index.add(["README.md"])
            repo.index.commit("Initial commit")

        # Create repos in workspace2 (with different branches)
        for repo_name in ["repo_a", "repo_c"]:
            repo_path = workspace2 / repo_name
            repo_path.mkdir()
            repo = Repo.init(repo_path)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()
            readme = repo_path / "README.md"
            readme.write_text(f"# {repo_name}\n")
            repo.index.add(["README.md"])
            repo.index.commit("Initial commit")
            if repo_name == "repo_a":
                repo.create_head("develop")
                repo.heads.develop.checkout()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["status", "-w", str(workspace1), "-w", str(workspace2), "--full"],
        )
        assert result.exit_code == 0
        assert "Comparing 2 workspaces" in result.output
        assert "workspace1" in result.output
        assert "workspace2" in result.output

    def test_status_multiple_workspaces_shows_differences(self, tmp_path):
        """Test that multi-workspace comparison highlights differences."""
        workspace1 = tmp_path / "ws1"
        workspace2 = tmp_path / "ws2"
        workspace1.mkdir()
        workspace2.mkdir()

        # Create same repo in both, but different branches
        for ws, branch in [(workspace1, "main"), (workspace2, "develop")]:
            repo_path = ws / "shared_repo"
            repo_path.mkdir()
            repo = Repo.init(repo_path)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()
            readme = repo_path / "README.md"
            readme.write_text("# shared_repo\n")
            repo.index.add(["README.md"])
            repo.index.commit("Initial commit")
            if branch != "main":
                repo.create_head(branch)
                repo.heads[branch].checkout()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["status", "-w", str(workspace1), "-w", str(workspace2)],
        )
        assert result.exit_code == 0
        # Both should appear since branches differ
        assert "shared_repo" in result.output

    def test_status_multiple_workspaces_gui_not_supported(self, tmp_path):
        """Test that GUI mode is not supported for multi-workspace comparison."""
        workspace1 = tmp_path / "ws1"
        workspace2 = tmp_path / "ws2"
        workspace1.mkdir()
        workspace2.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["status", "-w", str(workspace1), "-w", str(workspace2), "--gui"],
        )
        assert "GUI mode is not supported for multi-workspace comparison" in result.output

    def test_status_single_workspace_unchanged_behavior(self, temp_workspace):
        """Test that single workspace behavior is unchanged."""
        workspace, repos = temp_workspace
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "-w", str(workspace)])
        assert result.exit_code == 0
        assert f"Using workspace directory {workspace}" in result.output
        # Should NOT say "Comparing X workspaces"
        assert "Comparing" not in result.output

    def test_status_help_shows_multiple_option(self):
        """Test that help text mentions multiple workspaces."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "multiple" in result.output.lower() or "compare" in result.output.lower()
