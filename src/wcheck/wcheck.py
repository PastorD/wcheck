#!/usr/bin/env python3

import os
import click
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re

import pendulum

import yaml
from git import Repo

from rich.table import Table
from rich.console import Console

console = Console()
arrow_up = "\u2191"
arrow_down = "\u2193"


def _show_gui(
    repos: dict[str, Repo],
    config_file_path: str = "",
    config_repo: dict[str, str] | None = None,
) -> None:
    """Lazy import and call show_gui to avoid importing PySide6 unless needed.

    Args:
        repos: Dictionary mapping repository names to Repo objects.
        config_file_path: Path to the configuration file.
        config_repo: Dictionary mapping repository names to their configured versions.
    """
    from wcheck.gui import show_gui

    show_gui(repos, config_file_path, config_repo)


def _show_tui(
    repos: dict[str, Repo],
    config_file_path: str = "",
    config_repo: dict[str, str] | None = None,
) -> None:
    """Lazy import and call show_tui to avoid importing Textual unless needed.

    Args:
        repos: Dictionary mapping repository names to Repo objects.
        config_file_path: Path to the configuration file.
        config_repo: Dictionary mapping repository names to their configured versions.
    """
    from wcheck.tui import show_tui

    show_tui(repos, config_file_path, config_repo)


##################################### UTILITLY FUNCTIONS ###################


def matches_any(name: str, patternlist: list[str] | None) -> bool:
    """Match any of the patterns in patternlist.

    Args:
        name: String to match against.
        patternlist: List of regular expressions or exact strings to match with.

    Returns:
        True if any of the patterns match the string, False otherwise.
    """
    if patternlist is None or len(patternlist) == 0:
        return False
    for pattern in patternlist:
        if str(name).strip() == pattern:
            return True
        if re.match("^[a-zA-Z0-9_/]+$", pattern) is None:
            if re.match(pattern, name.strip()) is not None:
                return True
    return False


def fetch_all(repos: dict[str, Repo]) -> None:
    """Fetch all remotes for all repositories.

    Args:
        repos: Dictionary mapping repository names to Repo objects.
    """
    for repo in repos:
        for remote in repos[repo].remotes:
            print(f"Fetching {remote.name} from {remote.name}")
            fetch_result = remote.fetch()
            if len(fetch_result) > 0:
                print(f"Fetch {repo}: {fetch_result}")


def get_status_repo(repo: Repo) -> str:
    """Get a formatted status string for a repository.

    Returns a rich-formatted string showing:
    - Number of untracked files (U)
    - Number of modified files (M)
    - Number of staged files (S)
    - Number of commits ahead/behind remote

    Args:
        repo: Git repository object.

    Returns:
        Formatted status string with rich markup, or empty string if clean.
    """
    # Check if repo has any commits
    try:
        head_commit = repo.head.commit
        has_commits = True
    except ValueError:
        has_commits = False

    if (repo.is_dirty()) or len(repo.untracked_files) > 0:
        if has_commits:
            n_staged = len(repo.index.diff(head_commit))
        else:
            # For repos with no commits, all indexed files are "staged"
            n_staged = len(list(repo.index.entries.keys()))
        n_changes = len(repo.index.diff(None))
        n_untracked = len(repo.untracked_files)
        print_output = " ("
        if n_untracked > 0:
            print_output += "[orange1]" + str(n_untracked) + "U[/orange1]"
        if n_changes > 0:
            print_output += "[bright_red]" + str(n_changes) + "M[/bright_red]"
        if n_staged > 0:
            print_output += "[bright_magenta]" + str(n_staged) + "S[/bright_magenta]"
        print_output += ")"
    else:
        print_output = ""
        n_staged = 0
        n_changes = 0
        n_untracked = 0

    n_push, n_pull = get_remote_status(repo)
    if n_push > 0 or n_pull > 0:
        print_output += " ["
        if n_push > 0:
            print_output += (
                "[bright_green]" + str(n_push) + "[/bright_green]" + arrow_up + " "
            )
        if n_pull > 0:
            print_output += (
                "[bright_yellow]" + str(n_pull) + "[/bright_yellow]" + arrow_down + " "
            )
        print_output += "]"

    return print_output


def get_repo_head_ref(repo: Repo, verbose_output: bool = False) -> str:
    """Get the current HEAD reference for a repository.

    Returns the branch name, tag name, or commit SHA depending on the state:
    - If on a branch: returns branch name
    - If detached at a tag: returns tag name
    - If detached at a commit: returns commit SHA
    - If no commits: returns branch name with '(no commits)' suffix

    Args:
        repo: Git repository object.
        verbose_output: If True, print additional information about detached HEAD states.

    Returns:
        String representing the current HEAD reference.
    """
    # Check if repo has any commits
    try:
        _ = repo.head.commit
    except ValueError:
        # No commits yet, return branch name or "(no commits)"
        try:
            return repo.active_branch.name + " (no commits)"
        except TypeError:
            return "(no commits)"

    if repo.head.is_detached:
        # Use the head commit
        repo_commit = repo.head.commit.hexsha
        head_ref = repo_commit
        repo_name = repo.working_dir.split("/")[-1]
        if verbose_output:
            print(f"{repo_name} DETACHED head at {repo_commit}")
        for tag in repo.tags:
            if (
                tag.commit.hexsha == repo_commit
            ):  # check if the current commit has an associated tag
                if verbose_output:
                    print(f"{repo_name} TAGGED at {tag.name}")
                return tag.name  # use tag_name instead if available
        return head_ref

    else:  # head points to a branch
        return repo.active_branch.name


def get_remote_status(repo: Repo) -> tuple[int, int]:
    """Get the number of commits ahead and behind the remote tracking branch.

    Compares the current local branch with its remote tracking branch to determine
    how many commits need to be pushed and pulled. Uses efficient iter_commits
    with range notation.

    Args:
        repo: Git repository object.

    Returns:
        Tuple of (commits_to_push, commits_to_pull). Returns (0, 0) if:
        - Repository has no commits
        - HEAD is detached
        - No remotes configured
        - Branch is not tracking a remote
    """
    # Check if repo has any commits
    try:
        _ = repo.head.commit
    except ValueError:
        return 0, 0  # no commits yet

    if repo.head.is_detached:
        return 0, 0  # no remote status for detached head

    # Check if there are any remotes
    if not repo.remotes:
        return 0, 0  # no remotes configured

    # Try to get tracking branch using GitPython's built-in method
    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()

        if tracking is None:
            return 0, 0  # branch not tracking a remote

        # Use efficient iter_commits with range notation
        # Commits ahead (local commits not in remote)
        ahead = sum(1 for _ in repo.iter_commits(f"{tracking.name}..{branch.name}"))

        # Commits behind (remote commits not in local)
        behind = sum(1 for _ in repo.iter_commits(f"{branch.name}..{tracking.name}"))

        return ahead, behind
    except Exception:
        return 0, 0


def get_elapsed_time_repo(repo: Repo) -> str:
    """Get a human-readable string of time since the last commit.

    Args:
        repo: Git repository object.

    Returns:
        Formatted time difference string (e.g., '2 days', '3 hours'),
        or 'no commits' if repository has no commits.
    """
    try:
        return pendulum.format_diff(
            pendulum.now() - repo.head.commit.committed_datetime, absolute=True
        )
    except ValueError:
        return "no commits"


def show_repos_config_versions(
    repos_config_versions: dict[str, dict[str, str]],
    full: bool = False,
    gui: bool = True,
) -> None:
    """Display a table comparing repository versions across configurations.

    Creates a rich table showing repository versions from different sources
    (e.g., workspace vs config file, or multiple config files). Highlights
    repositories that differ between versions.

    Args:
        repos_config_versions: Nested dictionary where outer keys are version/config
            names and inner dictionaries map repo names to their versions.
        full: If True, show all repositories. If False, only show repositories
            that differ between versions.
        gui: Unused parameter (kept for API compatibility).
    """
    # Get list with all repositories
    repos_set = set()
    for version_name in repos_config_versions:
        for repo_name in repos_config_versions[version_name]:
            repos_set.add(repo_name)

    # Get list with unique repositories
    if len(repos_config_versions) > 1:
        unique_set = set()
        for repo_name in repos_set:
            repo_version = None
            for version_name in repos_config_versions:
                if repo_name not in repos_config_versions[version_name]:
                    if version_name != "Config version":
                        unique_set.add(
                            repo_name
                        )  ## add repo that is not in some version
                    break
                if repo_version is None:  ## first versions
                    repo_version = repos_config_versions[version_name][repo_name]
                elif repo_version != repos_config_versions[version_name][repo_name]:
                    unique_set.add(
                        repo_name
                    )  ## add repo that is different in different versions
                    break
    else:
        unique_set = repos_set

    if full:
        display_set = repos_set
    else:
        display_set = unique_set

    # sort set alphabetically
    display_set = sorted(display_set)

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Repo Name")
    for version_name in repos_config_versions:
        table.add_column(version_name)

    # Compare config
    for repo_name in display_set:
        if repo_name in unique_set:
            row_list = [repo_name]
        else:
            row_list = ["[dim]" + repo_name + "[/dim]"]
        for version_name in repos_config_versions:
            if repo_name in repos_config_versions[version_name]:
                if repo_name in unique_set:
                    row_list.append(repos_config_versions[version_name][repo_name])
                else:
                    row_list.append(
                        "[dim]"
                        + repos_config_versions[version_name][repo_name]
                        + "[/dim]"
                    )

            else:
                row_list.append("[dim]N/A[/dim]")
        table.add_row(*row_list)

    if len(table.rows) > 0:
        console.print(table)
    else:
        print("All configurations are identical")


def get_workspace_repos(workspace_directory: Path) -> dict[str, Repo]:
    """Find all git repositories in a workspace directory.

    Walks the workspace directory and identifies all subdirectories
    that are git repositories (contain a .git folder). Skips nested
    repositories for efficiency.

    Args:
        workspace_directory: Path to the workspace directory to scan.

    Returns:
        Dictionary mapping repository directory names to Repo objects.
        Returns empty dictionary if workspace_directory is not a directory.
    """
    source_repos = {}
    if not workspace_directory.is_dir():
        print(f"{workspace_directory} is not a directory")
        return source_repos

    # Gather all repositories in source directory
    for root, dirs, files in os.walk(workspace_directory):
        # Check each subdirectory
        dirs_to_remove = []
        for dir_in_source in dirs:
            d = Path(root) / dir_in_source
            # Check if directory is a git repository
            if (d / ".git").exists():
                source_repos[dir_in_source] = Repo(d)
                # Don't descend into git repos (skip nested repos)
                dirs_to_remove.append(dir_in_source)
        # Remove git repos from dirs to prevent descending
        for d in dirs_to_remove:
            dirs.remove(d)
    return source_repos


def get_repo_info_parallel(
    repos: dict[str, Repo], include_status: bool = True, include_time: bool = False
) -> dict[str, dict]:
    """Get repository info for multiple repos in parallel.

    Args:
        repos: Dictionary mapping repository names to Repo objects.
        include_status: If True, include status (dirty/untracked/ahead/behind).
        include_time: If True, include time since last commit.

    Returns:
        Dictionary mapping repo names to their info dictionaries.
    """

    def get_single_repo_info(repo_name: str, repo: Repo) -> tuple[str, dict]:
        """Get info for a single repository."""
        info = {
            "head_ref": get_repo_head_ref(repo),
            "status": "",
            "elapsed_time": "",
        }
        if include_status:
            info["status"] = get_status_repo(repo)
        if include_time:
            info["elapsed_time"] = get_elapsed_time_repo(repo)
        return repo_name, info

    if not repos:
        return {}

    results = {}
    with ThreadPoolExecutor(max_workers=min(len(repos), 8)) as executor:
        futures = {
            executor.submit(get_single_repo_info, name, repo): name
            for name, repo in repos.items()
        }
        for future in as_completed(futures):
            repo_name, info = future.result()
            results[repo_name] = info

    return results


######################################### COMMANDS #################################################


def compare_config_versions(
    config_filename: str,
    full: bool = False,
    verbose: bool = False,
    show_time: bool = False,
    version_filter: list[str] | None = None,
    stash: bool = False,
) -> None:
    """Compare versions of a config file across different git branches.

    Checks out each branch in the config file's repository and compares
    the repository versions specified in the config file.

    Args:
        config_filename: Path to the configuration file to compare.
        full: If True, show all repositories. If False, only show differences.
        verbose: If True, print additional information during processing.
        show_time: If True, include modification time in the output.
        version_filter: List of regex patterns to filter which branches to compare.
        stash: If True, stash uncommitted changes before switching branches.
    """

    print(f"Comparing config versions in {config_filename}")
    if stash:
        stashed = False
    # Read config file
    try:
        config_repo = Repo(config_filename, search_parent_directories=True)
    except Exception:
        print(f"Config file is not inside a git repository, {config_filename}")
        return

    if config_repo.is_dirty():
        print(
            f"Config repository '{config_repo.working_dir}' is not clean. Commit or stash changes."
        )
        if stash:
            print(f"Stashing changes in {config_repo.working_dir}")
            stashed = True
            config_repo.git.stash()
        else:
            return

    original_branch = config_repo.active_branch.name

    if version_filter is not None:
        print(f"Using filter {version_filter}")

    # Gather branches
    repos_config_versions = {}
    for ref in config_repo.references:
        if version_filter is not None and not matches_any(ref.name, version_filter):
            continue

        config_repo.git.checkout(ref)
        # Read config file
        try:
            with open(config_filename, "r") as file:
                configuration_file_dict = yaml.safe_load(file)["repositories"]
        except yaml.YAMLError:
            if verbose:
                print(f"Config file in {ref} ref is not valid YAML")
            continue

        # Skip remote branches if there are remotes
        if config_repo.remotes and ref.name.startswith(config_repo.remotes[0].name):
            continue  # skip remote branches

        if verbose:
            print(f"parsing {ref}")

        ref_name = ref.name
        if show_time:
            ref_name += (
                " (modified "
                # + pendulum.format_diff(
                # today_datime - ref.commit.authored_datetime, absolute=False
                # )
                + ")"
            )
        repos_config_versions[ref_name] = {}
        for repo_name in configuration_file_dict:
            repos_config_versions[ref_name][repo_name] = configuration_file_dict[
                repo_name
            ]["version"]

    config_repo.git.checkout(original_branch)
    if stash and stashed:
        config_repo.git.stash("pop")
        print(f"Stashed changes back in {config_repo.working_dir}")
        stashed = False

    show_repos_config_versions(repos_config_versions, full)


def compare_config_files(
    *config_files: str,
    full: bool = False,
    verbose: bool = False,
    show_time: bool = False,
    full_name: bool = False,
) -> None:
    """Compare repository versions across multiple configuration files.

    Reads each configuration file and displays a table comparing the
    repository versions specified in each file.

    Args:
        *config_files: Variable number of paths to configuration files.
        full: If True, show all repositories. If False, only show differences.
        verbose: If True, print additional information during processing.
        show_time: If True, include modification time in the output.
        full_name: If True, show full file paths. If False, show only filenames.
    """

    repos_config_versions = {}
    print(f"Comparing {len(config_files)} config files")
    for config_filename in config_files:
        if full_name:
            config_name = config_filename
        else:
            config_name = config_filename.split("/")[-1]
        print(f"Reading {config_filename}")
        try:
            with open(config_filename, "r") as file:
                configuration_file_dict = yaml.safe_load(file)["repositories"]
        except yaml.YAMLError:
            print(f"Config file {config_filename} is not valid YAML")
            continue
        repos_config_versions[config_name] = {}
        for repo_name in configuration_file_dict:
            repos_config_versions[config_name][repo_name] = configuration_file_dict[
                repo_name
            ]["version"]

    show_repos_config_versions(repos_config_versions, full)


def check_workspace_status(
    workspace_directory: Path,
    full: bool = False,
    verbose: bool = False,
    show_time: bool = False,
    fetch: bool = False,
    gui: bool = False,
    tui: bool = False,
) -> None:
    """Check and display the status of all repositories in a workspace.

    Scans the workspace for git repositories and displays their current
    branch, uncommitted changes, and remote sync status.

    Args:
        workspace_directory: Path to the workspace directory containing repositories.
        full: If True, show all repositories. If False, only show those with changes.
        verbose: If True, print additional information about each repository.
        show_time: If True, include time since last commit in the output.
        fetch: If True, fetch from remotes before checking status.
        gui: If True, launch the GUI interface instead of console output.
        tui: If True, launch the TUI interface instead of console output.
    """
    # Load workspace
    source_repos = get_workspace_repos(workspace_directory)

    if gui:
        _show_gui(source_repos)
        return

    if tui:
        _show_tui(source_repos)
        return

    if fetch and source_repos:
        # Fetch in parallel
        def fetch_repo(repo: Repo) -> None:
            for remote in repo.remotes:
                remote.fetch()

        with ThreadPoolExecutor(max_workers=min(len(source_repos), 8)) as executor:
            executor.map(fetch_repo, source_repos.values())

    # Get repo info in parallel
    repo_info = get_repo_info_parallel(source_repos, include_status=True, include_time=show_time)

    # Get current branch for each repo
    workspace_current_branch_version = {}
    workspace_current_branch_version["Current Workspace"] = {}
    for repo_name in sorted(repo_info.keys()):
        info = repo_info[repo_name]
        status_str = info["status"]
        if not full and status_str == "":
            continue
        repo_display_name = repo_name + status_str
        if show_time:
            repo_display_name += " (" + info["elapsed_time"] + ")"
        workspace_current_branch_version["Current Workspace"][repo_display_name] = info["head_ref"]

    show_repos_config_versions(workspace_current_branch_version, full=True)


def compare_workspaces(
    workspace_directories: tuple[Path, ...],
    full: bool = False,
    verbose: bool = False,
    show_time: bool = False,
    fetch: bool = False,
) -> None:
    """Compare repository statuses across multiple workspaces.

    Displays a side-by-side table showing the branch and status of each
    repository across different workspaces. Useful for comparing the same
    set of repositories in different environments or configurations.

    Args:
        workspace_directories: Tuple of workspace directory paths to compare.
        full: If True, show all repositories. If False, only show those with
            differences or changes.
        verbose: If True, print additional information about each repository.
        show_time: If True, include time since last commit in the output.
        fetch: If True, fetch from remotes before checking status.
    """
    repos_by_workspace: dict[str, dict[str, str]] = {}

    # Use basename for column names, with disambiguation for duplicates
    workspace_names: list[str] = []
    for ws_path in workspace_directories:
        name = ws_path.name
        # If duplicate basename, use parent/name
        count = sum(1 for w in workspace_directories if w.name == name)
        if count > 1:
            name = f"{ws_path.parent.name}/{name}"
        workspace_names.append(name)

    # Collect repos from each workspace in parallel
    def process_workspace(ws_index: int) -> tuple[str, dict[str, str]]:
        workspace_directory = workspace_directories[ws_index]
        ws_name = workspace_names[ws_index]
        source_repos = get_workspace_repos(workspace_directory)

        if fetch and source_repos:
            # Fetch in parallel within workspace
            def fetch_repo(repo: Repo) -> None:
                for remote in repo.remotes:
                    remote.fetch()

            with ThreadPoolExecutor(max_workers=min(len(source_repos), 4)) as executor:
                executor.map(fetch_repo, source_repos.values())

        # Get repo info in parallel
        repo_info = get_repo_info_parallel(source_repos, include_status=True, include_time=show_time)

        ws_repos = {}
        for repo_name in repo_info:
            info = repo_info[repo_name]
            branch = info["head_ref"]
            status_str = info["status"]

            # Format: "branch (status)" or just "branch" if clean
            if status_str:
                display_value = f"{branch}{status_str}"
            else:
                display_value = branch

            if show_time:
                display_value += f" ({info['elapsed_time']})"

            ws_repos[repo_name] = display_value

        return ws_name, ws_repos

    # Process workspaces (can be parallelized for multiple workspaces)
    for i, workspace_directory in enumerate(workspace_directories):
        click.echo(f"Scanning workspace: {workspace_directory}")
        ws_name, ws_repos = process_workspace(i)
        repos_by_workspace[ws_name] = ws_repos

    show_repos_config_versions(repos_by_workspace, full)


def compare_workspace_to_config(
    workspace_directory: Path,
    config_filename: str,
    full: bool = False,
    verbose: bool = False,
    show_time: bool = False,
    gui: bool = False,
    tui: bool = False,
) -> None:
    """Compare workspace repository versions with a configuration file.

    Displays a table comparing the current branch/version of each repository
    in the workspace with the version specified in the configuration file.

    Args:
        workspace_directory: Path to the workspace directory containing repositories.
        config_filename: Path to the YAML configuration file specifying expected versions.
        full: If True, show all repositories. If False, only show mismatches.
        verbose: If True, print additional information during processing.
        show_time: If True, include time since last commit in the output.
        gui: If True, launch the GUI interface instead of console output.
        tui: If True, launch the TUI interface instead of console output.
    """

    # Load workspace
    source_repos = get_workspace_repos(workspace_directory)

    # Get current branch for each repo
    workspace_current_branch_version = {}
    for repo_name in source_repos:
        workspace_current_branch_version[repo_name] = get_repo_head_ref(
            source_repos[repo_name], verbose
        )

    # Read config file
    with open(config_filename, "r") as file:
        configuration_file_dict = yaml.safe_load(file)["repositories"]

    # Check if source directory exists
    for repo_local_path in configuration_file_dict:
        if not os.path.exists(workspace_directory / repo_local_path) and verbose:
            print(f"{configuration_file_dict[repo_local_path]} does not exist")

    config_file_version = {}
    for config_file_path in configuration_file_dict:
        repo_local_path = config_file_path.split("/")[-1]
        config_file_version[repo_local_path] = configuration_file_dict[
            config_file_path
        ]["version"]

    if gui:
        _show_gui(source_repos, config_filename, config_file_version)
        return

    if tui:
        _show_tui(source_repos, config_filename, config_file_version)
        return

    repos_workspace_config_versions = {}
    repos_workspace_config_versions["Workspace version"] = (
        workspace_current_branch_version
    )
    repos_workspace_config_versions["Config version"] = config_file_version

    show_repos_config_versions(repos_workspace_config_versions, full)


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """Manage a workspace of git repositories."""
    pass


@cli.command()
@click.option(
    "-w",
    "--workspace-directory",
    "workspace_directories",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    multiple=True,
    help="Workspace directory. Can be specified multiple times to compare workspaces. Uses current directory if not specified.",
)
@click.option(
    "-f",
    "--full",
    is_flag=True,
    help="Show all repositories, not only those with changes",
)
@click.option("-v", "--verbose", is_flag=True, help="Show more information")
@click.option("--show-time", is_flag=True, help="Show last modified time")
@click.option("--fetch", is_flag=True, help="Fetch remote branches")
@click.option("--gui", is_flag=True, help="Use GUI to change branches")
@click.option("--tui", is_flag=True, help="Use TUI to change branches")
def status(workspace_directories, full, verbose, show_time, fetch, gui, tui):
    """Check the status of all repositories in a workspace.

    When a single workspace is specified (or none, using current directory),
    shows the status of each repository.

    When multiple workspaces are specified with multiple -w options,
    displays a side-by-side comparison table.
    """
    if not workspace_directories:
        click.echo("Workspace directory is not specified, using current directory")
        workspace_directories = (Path(os.getcwd()),)

    if len(workspace_directories) == 1:
        # Single workspace: use original behavior
        click.echo(f"Using workspace directory {workspace_directories[0]}")
        check_workspace_status(
            workspace_directories[0],
            full,
            verbose,
            show_time,
            fetch=fetch,
            gui=gui,
            tui=tui,
        )
    else:
        # Multiple workspaces: compare side by side
        if gui or tui:
            click.echo("GUI/TUI mode is not supported for multi-workspace comparison")
            return
        click.echo(f"Comparing {len(workspace_directories)} workspaces")
        compare_workspaces(
            workspace_directories,
            full,
            verbose,
            show_time,
            fetch=fetch,
        )


@cli.command()
@click.option(
    "-w",
    "--workspace-directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Workspace directory. Use current directory if not specified",
)
@click.option(
    "-c",
    "--config",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="VCS Configuration file",
)
@click.option(
    "-f",
    "--full",
    is_flag=True,
    help="Show all repositories, not only those that don't match",
)
@click.option("-v", "--verbose", is_flag=True, help="Show more information")
@click.option("--show-time", is_flag=True, help="Show last modified time")
@click.option("--gui", is_flag=True, help="Use GUI to change branches")
@click.option("--tui", is_flag=True, help="Use TUI to change branches")
def wconfig(workspace_directory, config, full, verbose, show_time, gui, tui):
    """Compare the workspace with a configuration file."""
    if not workspace_directory:
        click.echo("Source directory is not specified, using current directory")
        workspace_directory = Path(os.getcwd())
    compare_workspace_to_config(
        workspace_directory,
        str(config),
        full,
        verbose,
        show_time,
        gui,
        tui,
    )


@cli.command("config-list")
@click.option(
    "-c",
    "--config",
    required=True,
    multiple=True,
    type=click.Path(exists=True, dir_okay=False),
    help="VCS Configuration files to compare",
)
@click.option(
    "-f",
    "--full",
    is_flag=True,
    help="Show all repositories, not only those that differ",
)
@click.option("-v", "--verbose", is_flag=True, help="Show more information")
@click.option("--show-time", is_flag=True, help="Show last modified time")
@click.option("--full-name", is_flag=True, help="Use full filename for config table")
def config_list(config, full, verbose, show_time, full_name):
    """Compare multiple configuration files."""
    compare_config_files(
        *config,
        full=full,
        verbose=verbose,
        show_time=show_time,
        full_name=full_name,
    )


@cli.command("config-versions")
@click.option(
    "-c",
    "--config",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="VCS Configuration file",
)
@click.option(
    "-f",
    "--full",
    is_flag=True,
    help="Show all repositories, not only those that differ",
)
@click.option("-v", "--verbose", is_flag=True, help="Show more information")
@click.option("--show-time", is_flag=True, help="Show last modified time")
@click.option(
    "--filter",
    "version_filter",
    multiple=True,
    default=None,
    help="Filter versions to compare (can be used multiple times)",
)
@click.option("--stash", is_flag=True, help="Stash changes before comparing")
def config_versions(config, full, verbose, show_time, version_filter, stash):
    """Compare versions of a config file across git branches."""
    version_filter_list = list(version_filter) if version_filter else None
    compare_config_versions(
        config,
        full=full,
        verbose=verbose,
        show_time=show_time,
        version_filter=version_filter_list,
        stash=stash,
    )


def main() -> None:
    """Entry point for the wcheck command-line tool."""
    cli()


if __name__ == "__main__":
    main()
