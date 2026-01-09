"""Pytest fixtures for wcheck tests."""

import pytest
import yaml
from git import Repo


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with multiple git repositories."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create multiple repos
    repos = {}
    for repo_name in ["repo_a", "repo_b", "repo_c"]:
        repo_path = workspace / repo_name
        repo_path.mkdir()
        repo = Repo.init(repo_path)

        # Configure git user for commits
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # Create an initial commit
        readme = repo_path / "README.md"
        readme.write_text(f"# {repo_name}\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        repos[repo_name] = repo

    return workspace, repos


@pytest.fixture
def temp_workspace_with_changes(temp_workspace):
    """Create a temporary workspace with uncommitted changes."""
    workspace, repos = temp_workspace

    # Make changes to repo_a (unstaged)
    readme = workspace / "repo_a" / "README.md"
    readme.write_text("# repo_a\nModified content\n")

    # Make changes to repo_b (untracked file)
    new_file = workspace / "repo_b" / "new_file.txt"
    new_file.write_text("New file content\n")

    return workspace, repos


@pytest.fixture
def config_file(tmp_path):
    """Create a sample configuration file."""
    config_path = tmp_path / "config.yaml"
    config_data = {
        "repositories": {
            "repo_a": {"version": "main"},
            "repo_b": {"version": "develop"},
            "repo_c": {"version": "main"},
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    return config_path


@pytest.fixture
def config_file_alt(tmp_path):
    """Create an alternative configuration file for comparison."""
    config_path = tmp_path / "config_alt.yaml"
    config_data = {
        "repositories": {
            "repo_a": {"version": "main"},
            "repo_b": {"version": "main"},  # Different from config_file
            "repo_c": {"version": "feature"},  # Different from config_file
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    return config_path


@pytest.fixture
def config_repo(tmp_path):
    """Create a git repository with a config file and multiple branches."""
    repo_path = tmp_path / "config_repo"
    repo_path.mkdir()
    repo = Repo.init(repo_path, initial_branch="main")

    # Configure git user
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@test.com").release()

    config_path = repo_path / "config.yaml"

    # Create config on main branch
    config_data_main = {
        "repositories": {
            "repo_a": {"version": "v1.0.0"},
            "repo_b": {"version": "v1.0.0"},
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data_main, f)
    repo.index.add(["config.yaml"])
    repo.index.commit("Initial config")

    # Create develop branch with different versions
    repo.create_head("develop")
    repo.heads.develop.checkout()

    config_data_develop = {
        "repositories": {
            "repo_a": {"version": "v1.1.0"},
            "repo_b": {"version": "v1.0.0"},
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data_develop, f)
    repo.index.add(["config.yaml"])
    repo.index.commit("Update config for develop")

    # Go back to main
    repo.heads.main.checkout()

    return repo_path, config_path
