#!/usr/bin/env python3

import os
import sys
import subprocess
import click
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


def _show_gui(repos, config_file_path="", config_repo=None):
    """Lazy import and call show_gui to avoid importing PySide6 unless needed."""
    from wcheck.gui import show_gui
    show_gui(repos, config_file_path, config_repo)


##################################### UTILITLY FUNCTIONS ###################


def matches_any(name, patternlist):
    """Match any of the patterns in patternliss

    Args:
        name (str): string to match against
        patternlist (str list): list of regular expressions to match with

    Returns:
        bool: if any of the patterns match the string
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


def fetch_all(repos):
    for repo in repos:
        for remote in repos[repo].remotes:
            print(f"Fetching {remote.name} from {remote.name}")
            fetch_result = remote.fetch()
            if len(fetch_result) > 0:
                print(f"Fetch {repo}: {fetch_result}")


def get_status_repo(repo):
    if (repo.is_dirty()) or len(repo.untracked_files) > 0:
        n_staged = len(repo.index.diff(repo.head.commit))
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


def get_repo_head_ref(repo, verbose_output=False):
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
    if repo.head.is_detached:
        return 0, 0  # no remote status for detached head

    # Check if there are any remotes
    if not repo.remotes:
        return 0, 0  # no remotes configured

    # Find index for remote branch matching current branch
    found_remote_ref = False
    index_remote = 0
    index_ref = 0
    for index_remote, remote in enumerate(repo.remotes):
        for index_ref, ref in enumerate(remote.refs):
            if ref.name == remote.name + "/" + repo.active_branch.name:
                found_remote_ref = True
                break
        if found_remote_ref:
            break
    if not found_remote_ref:
        return 0, 0  # branch not tracked by any remote

    # Get remote commit
    remote_commit = repo.remotes[index_remote].refs[index_ref].commit
    commits_remote_accumulated = [remote_commit]
    # commits_remote_frontier = [remote_commit]

    # Get local commit
    local_commit = repo.head.commit
    commits_local_accumulated = [local_commit]
    # commits_local_frontier = [local_commit]

    if local_commit.hexsha == remote_commit.hexsha:
        # print (f"Branch {repo.active_branch.name} is up to date with remote {remote.name}")
        return 0, 0
    else:
        # Revert commits in local and remote repo to find common ancestor
        found_common_ancestor = False
        while not found_common_ancestor:
            if len(local_commit.parents) > 0:
                # for parent in local_commit.parents:
                #     commits_local_frontier.append(parent)
                # local_commit = commits_local_frontier
                # print(f"len parents {len(local_commit.parents)}")
                # if local_parent in commits_local_accumulated:
                #     break
                # commits_local_accumulated.append(local_parent)
                # local_commit = local_parent

                local_commit = local_commit.parents[0]
                for i, commit_remote_to_check in enumerate(commits_remote_accumulated):
                    if local_commit.hexsha == commit_remote_to_check.hexsha:
                        push_counter = len(commits_local_accumulated)
                        pull_counter = i
                        found_common_ancestor = True
                        break
                commits_local_accumulated.append(local_commit)

            if len(remote_commit.parents) > 0:
                # for parent in remote_commit.parents:
                #     commits_remote_frontier.append(parent)
                # remote_commit = commits_remote_frontier.pop()
                remote_commit = remote_commit.parents[0]
                for i, commit_local_to_check in enumerate(commits_local_accumulated):
                    if remote_commit.hexsha == commit_local_to_check.hexsha:
                        pull_counter = len(commits_remote_accumulated)
                        push_counter = i
                        found_common_ancestor = True
                        break

                commits_remote_accumulated.append(remote_commit)

        return push_counter, pull_counter


def get_elapsed_time_repo(repo: Repo) -> str:
    return pendulum.format_diff(
        pendulum.now() - repo.head.commit.committed_datetime, absolute=True
    )


def show_repos_config_versions(
    repos_config_versions: dict, full: bool = False, gui: bool = True
) -> None:
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


def get_workspace_repos(workspace_directory):
    source_repos = {}
    if not workspace_directory.is_dir():
        print(f"{workspace_directory} is not a directory")
        return source_repos

    # Gather all repositories in source directory
    for root, dirs, files in os.walk(workspace_directory):
        for dir_in_source in dirs:
            d = Path(root) / dir_in_source
            # Check if directory is a git repository
            if d.is_dir() and (d / ".git").exists():
                source_repos[dir_in_source] = Repo(d)
    return source_repos


######################################### COMMANDS #################################################


def compare_config_versions(
    config_filename,
    full=False,
    verbose=False,
    show_time=False,
    version_filter=None,
    stash=False,
):
    """
    Compare versions of config files in different repositories

    Args:
        config_filename (str): Name of config file to compare
        full (bool): If true, compare all versions of the config file
        verbose (bool): If true, print more information
        show_time (bool): If true, print elapsed time for each version
        version_filter (list): regular expression to filter versions to compare
        stash (bool): If true, stash all repositories before comparing
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
    *config_files, full=False, verbose=False, show_time=False, full_name=False
):
    """Compare a list of configuration files

    Args:
        full (bool, optional): show the full list. Defaults to False.
        verbose (bool, optional): show more information. Defaults to False.
        show_time (bool, optional): show last time each configuration file was changed. Defaults to False.
        full_name (bool, optional): show the configuration filename full path, not only the filename. Defaults to False.
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
    workspace_directory,
    full=False,
    verbose=False,
    show_time=False,
    fetch=False,
    gui=False,
):
    """Check the status of all repositories in a workspace

    Args:
        workspace_directory (str): path to the workspace
        full (bool, optional): show the full list. Defaults to False.
        verbose (bool, optional): show more information. Defaults to False.
        show_time (bool, optional): show last time each configuration file was changed. Defaults to False.
        fetch (bool, optional): fetch all repositories before checking status. Defaults to False.
        gui (bool, optional): show the GUI. Defaults to False.
    """
    # Load workspace
    source_repos = get_workspace_repos(workspace_directory)

    if gui:
        _show_gui(source_repos)

    if fetch:
        for repo_name in source_repos:
            for remote in source_repos[repo_name].remotes:
                remote.fetch()

    # Get current branch for each repo
    workspace_current_branch_version = {}
    workspace_current_branch_version["Current Workspace"] = {}
    for repo_name in source_repos:
        status_str = get_status_repo(source_repos[repo_name])
        if not full and status_str == "":
            continue
        repo_display_name = repo_name + status_str
        if show_time:
            repo_display_name += (
                " (" + get_elapsed_time_repo(source_repos[repo_name]) + ")"
            )
        workspace_current_branch_version["Current Workspace"][repo_display_name] = (
            get_repo_head_ref(source_repos[repo_name], verbose)
        )

    show_repos_config_versions(workspace_current_branch_version, full=True)


def compare_workspace_to_config(
    workspace_directory,
    config_filename,
    full=False,
    verbose=False,
    show_time=False,
    gui=False,
):
    """Compare the status of all repositories in a workspace with a configuration file

    Args:
        workspace_directory (str): path to the workspace
        config_filename (str): path to the configuration file
        full (bool, optional): show the full list. Defaults to False.
        verbose (bool, optional): show more information. Defaults to False.
        show_time (bool, optional): show last time each configuration file was changed. Defaults to False.
        gui (bool, optional): show the GUI. Defaults to False.
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
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Workspace directory. Use current directory if not specified",
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
def status(workspace_directory, full, verbose, show_time, fetch, gui):
    """Check the status of all repositories in a workspace."""
    if not workspace_directory:
        click.echo("Workspace directory is not specified, using current directory")
        workspace_directory = Path(os.getcwd())
    click.echo(f"Using workspace directory {workspace_directory}")
    check_workspace_status(
        workspace_directory,
        full,
        verbose,
        show_time,
        fetch=fetch,
        gui=gui,
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
def wconfig(workspace_directory, config, full, verbose, show_time, gui):
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


def main():
    cli()


if __name__ == "__main__":
    main()
