#!/usr/bin/env python3
"""TUI module for wcheck - provides a Textual-based terminal interface for managing repositories."""

import os
import subprocess
from typing import NoReturn

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Label,
    OptionList,
    Static,
)
from textual.widgets.option_list import Option

from git import Repo


def get_repo_head_ref(repo: Repo) -> str:
    """Get the current HEAD reference for a repository.

    Returns the branch name, tag name, or commit SHA depending on the state:
    - If on a branch: returns branch name
    - If detached at a tag: returns tag name
    - If detached at a commit: returns commit SHA

    Args:
        repo: Git repository object.

    Returns:
        String representing the current HEAD reference.
    """
    try:
        _ = repo.head.commit
    except ValueError:
        # No commits yet
        try:
            return repo.active_branch.name + " (no commits)"
        except TypeError:
            return "(no commits)"

    if repo.head.is_detached:
        repo_commit = repo.head.commit.hexsha
        for tag in repo.tags:
            if tag.commit.hexsha == repo_commit:
                return tag.name
        return repo_commit[:8]  # Short SHA for display
    else:
        return repo.active_branch.name


def get_repo_status_indicator(repo: Repo) -> str:
    """Get a status indicator string for a repository.

    Args:
        repo: Git repository object.

    Returns:
        Status indicator string (e.g., '●' for dirty, '○' for clean).
    """
    try:
        _ = repo.head.commit
        has_commits = True
    except ValueError:
        has_commits = False

    if repo.is_dirty() or len(repo.untracked_files) > 0:
        return "[yellow]●[/yellow]"  # Dirty
    elif not has_commits:
        return "[dim]○[/dim]"  # No commits
    else:
        return "[green]○[/green]"  # Clean


def get_ahead_behind(repo: Repo) -> tuple[int, int]:
    """Get commits ahead and behind remote tracking branch.

    Args:
        repo: Git repository object.

    Returns:
        Tuple of (ahead, behind) commit counts.
    """
    try:
        _ = repo.head.commit
    except ValueError:
        return 0, 0

    if repo.head.is_detached or not repo.remotes:
        return 0, 0

    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()

        if tracking is None:
            return 0, 0

        # Commits ahead (local commits not in remote)
        ahead = sum(1 for _ in repo.iter_commits(f"{tracking.name}..{branch.name}"))

        # Commits behind (remote commits not in local)
        behind = sum(1 for _ in repo.iter_commits(f"{branch.name}..{tracking.name}"))

        return ahead, behind
    except Exception:
        return 0, 0


def format_sync_status(ahead: int, behind: int) -> str:
    """Format ahead/behind status for display.

    Args:
        ahead: Number of commits ahead.
        behind: Number of commits behind.

    Returns:
        Formatted string showing sync status.
    """
    if ahead == 0 and behind == 0:
        return "[green]✓[/green]"
    parts = []
    if ahead > 0:
        parts.append(f"[cyan]↑{ahead}[/cyan]")
    if behind > 0:
        parts.append(f"[magenta]↓{behind}[/magenta]")
    return " ".join(parts)


class BranchSelectScreen(ModalScreen[str | None]):
    """Modal screen for selecting a branch to checkout.

    Attributes:
        repo_name: Name of the repository.
        repo: Git repository object.
        current_branch: Currently active branch name.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(
        self,
        repo_name: str,
        repo: Repo,
        current_branch: str,
    ) -> None:
        """Initialize the branch selection screen.

        Args:
            repo_name: Name of the repository.
            repo: Git repository object.
            current_branch: Currently active branch name.
        """
        super().__init__()
        self.repo_name = repo_name
        self.repo = repo
        self.current_branch = current_branch

    def compose(self) -> ComposeResult:
        """Compose the branch selection UI."""
        yield Vertical(
            Label(f"Select branch for [bold]{self.repo_name}[/bold]", id="title"),
            OptionList(id="branch-list"),
            Static(
                "Press [bold]Enter[/bold] to checkout, [bold]Escape[/bold] to cancel",
                id="help",
            ),
            id="branch-dialog",
        )

    def on_mount(self) -> None:
        """Populate the branch list when the screen is mounted."""
        option_list = self.query_one("#branch-list", OptionList)

        # Add current branch first (marked)
        option_list.add_option(
            Option(f"● {self.current_branch} (current)", id=self.current_branch)
        )

        # Add other branches and tags, filtering out HEAD
        added_refs = {self.current_branch, "HEAD"}
        for ref in self.repo.references:
            ref_name = ref.name

            # Skip HEAD references
            if ref_name == "HEAD" or ref_name.endswith("/HEAD"):
                continue

            # Strip origin/ prefix for display but keep for identification
            display_name = ref_name
            if ref_name.startswith("origin/"):
                display_name = ref_name.replace("origin/", "", 1)

            if display_name not in added_refs:
                option_list.add_option(Option(f"  {display_name}", id=ref_name))
                added_refs.add(display_name)

    def action_cancel(self) -> None:
        """Cancel branch selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select the highlighted branch."""
        option_list = self.query_one("#branch-list", OptionList)
        if option_list.highlighted is not None:
            selected = option_list.get_option_at_index(option_list.highlighted)
            if selected.id != self.current_branch:
                self.dismiss(selected.id)
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection via click or enter."""
        if event.option.id != self.current_branch:
            self.dismiss(event.option.id)
        else:
            self.dismiss(None)


class WCheckTUI(App[None]):
    """Main TUI application for wcheck.

    Displays a table of repositories with their current branches and status,
    providing controls for switching branches and opening in editor.

    Attributes:
        repos: Dictionary mapping repository names to Repo objects.
        config_file_path: Path to the configuration file.
        config_repo: Dictionary mapping repository names to their configured versions.
        output_messages: Dictionary storing output messages for each repo.
    """

    CSS = """
    #branch-dialog {
        align: center middle;
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #title {
        text-align: center;
        width: 100%;
        padding-bottom: 1;
    }

    #help {
        text-align: center;
        width: 100%;
        padding-top: 1;
        color: $text-muted;
    }

    #branch-list {
        height: auto;
        max-height: 20;
    }

    DataTable {
        height: 1fr;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "select_branch", "Branch"),
        Binding("e", "open_editor", "Editor"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "fetch", "Fetch"),
        Binding("p", "pull", "Pull"),
        Binding("P", "push", "Push"),
        Binding("F", "fetch_all", "Fetch All"),
    ]

    def __init__(
        self,
        repos: dict[str, Repo],
        config_file_path: str = "",
        config_repo: dict[str, str] | None = None,
    ) -> None:
        """Initialize the WCheckTUI application.

        Args:
            repos: Dictionary mapping repository names to Repo objects.
            config_file_path: Path to the configuration file.
            config_repo: Dictionary mapping repository names to their configured versions.
        """
        super().__init__()
        self.repos = repos
        self.config_file_path = config_file_path
        self.config_repo = config_repo
        self.output_messages: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the main UI layout."""
        yield Header()
        if self.config_file_path:
            yield Static(f"Config: {self.config_file_path}", id="config-label")
        yield DataTable(id="repo-table")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the data table when the app is mounted."""
        table = self.query_one("#repo-table", DataTable)
        table.cursor_type = "row"

        # Add columns
        table.add_column("Status", key="status", width=6)
        table.add_column("Repository", key="repo", width=25)
        table.add_column("Branch", key="branch", width=25)
        table.add_column("Sync", key="sync", width=10)
        if self.config_repo is not None:
            table.add_column("Config", key="config", width=15)
        table.add_column("Output", key="output", width=35)

        self._populate_table()

    def _populate_table(self) -> None:
        """Populate or refresh the repository table."""
        table = self.query_one("#repo-table", DataTable)
        table.clear()

        for repo_name in sorted(self.repos.keys()):
            repo = self.repos[repo_name]
            status = get_repo_status_indicator(repo)
            branch = get_repo_head_ref(repo)
            ahead, behind = get_ahead_behind(repo)
            sync_status = format_sync_status(ahead, behind)
            output = self.output_messages.get(repo_name, "")

            row_data = [status, repo_name, branch, sync_status]

            if self.config_repo is not None:
                if repo_name in self.config_repo:
                    config_version = self.config_repo[repo_name]
                    if config_version != branch:
                        config_version = f"[red]{config_version}[/red]"
                else:
                    config_version = "[dim]N/A[/dim]"
                row_data.append(config_version)

            row_data.append(output)
            table.add_row(*row_data, key=repo_name)

    def _get_selected_repo(self) -> tuple[str, Repo] | None:
        """Get the currently selected repository.

        Returns:
            Tuple of (repo_name, Repo) or None if no selection.
        """
        table = self.query_one("#repo-table", DataTable)
        if table.cursor_row is not None:
            row_data = table.get_row_at(table.cursor_row)
            # The repo name is in the second column (index 1)
            repo_name = row_data[1]
            if repo_name in self.repos:
                return repo_name, self.repos[repo_name]
        return None

    def _set_output(self, repo_name: str, message: str) -> None:
        """Set output message for a repository and refresh table.

        Args:
            repo_name: Name of the repository.
            message: Output message to display.
        """
        self.output_messages[repo_name] = message
        self._populate_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection (Enter key) on the DataTable."""
        self.action_select_branch()

    def action_select_branch(self) -> None:
        """Open the branch selection dialog for the selected repository."""
        selected = self._get_selected_repo()
        if selected is None:
            self.notify("No repository selected", severity="warning")
            return

        repo_name, repo = selected
        current_branch = get_repo_head_ref(repo)

        def handle_branch_selection(branch: str | None) -> None:
            """Handle the result of branch selection."""
            if branch is not None:
                # Strip origin/ prefix if present
                checkout_branch = branch
                if checkout_branch.startswith("origin/"):
                    checkout_branch = checkout_branch.replace("origin/", "", 1)
                try:
                    repo.git.checkout(checkout_branch)
                    self._set_output(repo_name, f"[green]→ {checkout_branch}[/green]")
                    self.notify(f"Checked out {checkout_branch} in {repo_name}")
                except Exception as e:
                    self._set_output(repo_name, f"[red]Error: {str(e)[:25]}[/red]")
                    self.notify(f"Checkout failed: {e}", severity="error")

        self.push_screen(
            BranchSelectScreen(repo_name, repo, current_branch),
            handle_branch_selection,
        )

    def action_open_editor(self) -> None:
        """Open the selected repository in an external editor."""
        selected = self._get_selected_repo()
        if selected is None:
            self.notify("No repository selected", severity="warning")
            return

        repo_name, repo = selected
        editor_command = os.getenv("EDITOR", "code")
        repo_path = repo.working_tree_dir

        try:
            subprocess.Popen([editor_command, repo_path])
            self._set_output(repo_name, f"[blue]Opened in {editor_command}[/blue]")
            self.notify(f"Opened {repo_name} in {editor_command}")
        except Exception as e:
            self._set_output(repo_name, "[red]Editor error[/red]")
            self.notify(f"Failed to open editor: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the repository table."""
        self._populate_table()
        self.notify("Refreshed")

    def action_fetch(self) -> None:
        """Fetch from remote for the selected repository."""
        selected = self._get_selected_repo()
        if selected is None:
            self.notify("No repository selected", severity="warning")
            return

        repo_name, repo = selected

        if not repo.remotes:
            self._set_output(repo_name, "[yellow]No remotes[/yellow]")
            self.notify(f"No remotes configured for {repo_name}", severity="warning")
            return

        try:
            self._set_output(repo_name, "[dim]Fetching...[/dim]")
            results = []
            for remote in repo.remotes:
                fetch_info = remote.fetch()
                for info in fetch_info:
                    if info.flags & info.NEW_HEAD:
                        results.append(f"new: {info.name}")
                    elif info.flags & info.FAST_FORWARD:
                        results.append(f"ff: {info.name}")

            if results:
                self._set_output(
                    repo_name, f"[green]Fetched: {', '.join(results[:2])}[/green]"
                )
            else:
                self._set_output(repo_name, "[green]Up to date[/green]")
            self._populate_table()
            self.notify(f"Fetched {repo_name}")
        except Exception as e:
            self._set_output(repo_name, f"[red]Fetch error: {str(e)[:20]}[/red]")
            self.notify(f"Fetch failed: {e}", severity="error")

    def action_pull(self) -> None:
        """Pull from remote for the selected repository."""
        selected = self._get_selected_repo()
        if selected is None:
            self.notify("No repository selected", severity="warning")
            return

        repo_name, repo = selected

        if not repo.remotes:
            self._set_output(repo_name, "[yellow]No remotes[/yellow]")
            self.notify(f"No remotes configured for {repo_name}", severity="warning")
            return

        if repo.head.is_detached:
            self._set_output(repo_name, "[yellow]Detached HEAD[/yellow]")
            self.notify(
                f"Cannot pull: detached HEAD in {repo_name}", severity="warning"
            )
            return

        try:
            self._set_output(repo_name, "[dim]Pulling...[/dim]")
            origin = repo.remotes[0]
            pull_info = origin.pull()

            if pull_info:
                info = pull_info[0]
                if info.flags & info.FAST_FORWARD:
                    self._set_output(repo_name, "[green]Pulled (ff)[/green]")
                elif info.flags & info.HEAD_UPTODATE:
                    self._set_output(repo_name, "[green]Already up to date[/green]")
                else:
                    self._set_output(repo_name, "[green]Pulled[/green]")
            else:
                self._set_output(repo_name, "[green]Pulled[/green]")

            self._populate_table()
            self.notify(f"Pulled {repo_name}")
        except Exception as e:
            error_msg = str(e)[:25]
            self._set_output(repo_name, f"[red]Pull error: {error_msg}[/red]")
            self.notify(f"Pull failed: {e}", severity="error")

    def action_push(self) -> None:
        """Push to remote for the selected repository."""
        selected = self._get_selected_repo()
        if selected is None:
            self.notify("No repository selected", severity="warning")
            return

        repo_name, repo = selected

        if not repo.remotes:
            self._set_output(repo_name, "[yellow]No remotes[/yellow]")
            self.notify(f"No remotes configured for {repo_name}", severity="warning")
            return

        if repo.head.is_detached:
            self._set_output(repo_name, "[yellow]Detached HEAD[/yellow]")
            self.notify(
                f"Cannot push: detached HEAD in {repo_name}", severity="warning"
            )
            return

        try:
            self._set_output(repo_name, "[dim]Pushing...[/dim]")
            origin = repo.remotes[0]
            push_info = origin.push()

            if push_info:
                info = push_info[0]
                if info.flags & info.UP_TO_DATE:
                    self._set_output(repo_name, "[green]Already up to date[/green]")
                elif info.flags & info.REJECTED:
                    self._set_output(repo_name, "[red]Push rejected[/red]")
                elif info.flags & info.ERROR:
                    self._set_output(repo_name, "[red]Push error[/red]")
                else:
                    self._set_output(repo_name, "[green]Pushed[/green]")
            else:
                self._set_output(repo_name, "[green]Pushed[/green]")

            self._populate_table()
            self.notify(f"Pushed {repo_name}")
        except Exception as e:
            error_msg = str(e)[:25]
            self._set_output(repo_name, f"[red]Push error: {error_msg}[/red]")
            self.notify(f"Push failed: {e}", severity="error")

    def action_fetch_all(self) -> None:
        """Fetch all remotes for all repositories."""
        self.notify("Fetching all repositories...")

        for repo_name in sorted(self.repos.keys()):
            repo = self.repos[repo_name]

            if not repo.remotes:
                self.output_messages[repo_name] = "[yellow]No remotes[/yellow]"
                continue

            try:
                self.output_messages[repo_name] = "[dim]Fetching...[/dim]"
                results = []
                for remote in repo.remotes:
                    fetch_info = remote.fetch()
                    for info in fetch_info:
                        if info.flags & info.NEW_HEAD:
                            results.append("new")
                        elif info.flags & info.FAST_FORWARD:
                            results.append("ff")

                if results:
                    self.output_messages[repo_name] = (
                        f"[green]Fetched ({len(results)} refs)[/green]"
                    )
                else:
                    self.output_messages[repo_name] = "[green]Up to date[/green]"
            except Exception as e:
                self.output_messages[repo_name] = f"[red]Error: {str(e)[:15]}[/red]"

        self._populate_table()
        self.notify("Fetched all repositories")


def show_tui(
    repos: dict[str, Repo],
    config_file_path: str = "",
    config_repo: dict[str, str] | None = None,
) -> NoReturn:
    """Launch the TUI application for managing repositories.

    Creates and runs the WCheckTUI application. This function does not
    return as it enters the Textual event loop.

    Args:
        repos: Dictionary mapping repository names to Repo objects.
        config_file_path: Path to the configuration file (displayed in UI).
        config_repo: Dictionary mapping repository names to their configured versions.
    """
    app = WCheckTUI(repos, config_file_path, config_repo)
    app.run()
