#!/usr/bin/env python3
"""GUI module for wcheck - provides a PySide6-based interface for managing repositories."""

import os
import sys
import subprocess
from typing import NoReturn

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGridLayout,
)

from git import Repo


def get_repo_head_ref(repo: Repo, verbose_output: bool = False) -> str:
    """Get the current HEAD reference for a repository.

    Returns the branch name, tag name, or commit SHA depending on the state:
    - If on a branch: returns branch name
    - If detached at a tag: returns tag name
    - If detached at a commit: returns commit SHA

    Args:
        repo: Git repository object.
        verbose_output: If True, print additional information about detached HEAD states.

    Returns:
        String representing the current HEAD reference.
    """
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


class RepoObject:
    """Represents a repository in the GUI with associated widgets and actions.

    Manages the UI components for a single repository including:
    - Label showing repository name and status
    - Combo box for branch/tag selection
    - Checkout button to switch branches
    - Editor button to open in external editor

    Attributes:
        repo: The git repository object.
        repo_dirty: Whether the repository has uncommitted changes.
        abs_path: Absolute path to the repository.
        qlabel: QLabel widget showing repository name.
        combo_box: QComboBox widget for branch selection.
        checkout_button: QPushButton to checkout selected branch.
        editor_button: QPushButton to open repository in editor.
        active_branch: Name of the currently active branch.
    """

    def __init__(self, repo: Repo, repo_name: str, ignore_remote: bool = False) -> None:
        """Initialize the RepoObject with repository and UI components.

        Args:
            repo: Git repository object.
            repo_name: Display name for the repository.
            ignore_remote: If True, exclude remote branches from the combo box.
        """
        # status_str = get_status_repo(repo)
        self.repo_dirty = repo.is_dirty()

        self.repo = repo
        self.abs_path = repo.working_tree_dir + "/"
        self.qlabel = QLabel(f"{repo_name} ")
        if self.repo_dirty:
            self.qlabel.setStyleSheet("background-color: Yellow")
        self.combo_box = QComboBox()
        self.checkout_button = QPushButton("Checkout selected")
        self.editor_button = QPushButton("Open in editor")
        self.active_branch = get_repo_head_ref(repo)

        self.checkout_button.clicked.connect(self.checkout_branch)
        self.editor_button.clicked.connect(self.editor_button_pressed)
        self.checkout_button.setEnabled(False)

        self.combo_box.addItem(str(self.active_branch))

        for ref in self.repo.references:
            if ignore_remote and ref.name.startswith(repo.remotes[0].name):
                continue
            if ref.name != self.active_branch:
                self.combo_box.addItem(str(ref))
        self.combo_box.currentIndexChanged.connect(self.selectionchange)

    def selectionchange(self, index: int) -> None:
        """Handle branch selection change in the combo box.

        Enables the checkout button if a different branch is selected,
        disables it if the current branch is selected.

        Args:
            index: Index of the selected item in the combo box.
        """
        print(f"Selection changed to {self.combo_box.currentText()}")
        branch_name = self.combo_box.currentText()
        if branch_name.startswith("origin/"):
            branch_name = branch_name.replace("origin/", "", 1)
        if branch_name != self.active_branch:
            self.checkout_button.setEnabled(True)
        else:
            self.checkout_button.setEnabled(False)

    def checkout_branch(self) -> None:
        """Checkout the selected branch in the repository.

        Handles both local and remote branch names, stripping the 'origin/'
        prefix from remote branches before checkout.
        """
        print(
            f"Checkout button pressed for repo {self.repo.working_tree_dir}, current label {self.qlabel.text()}"
        )
        print(f" - Checking out branch, {self.combo_box.currentText()}")
        # if the branch is from origin, checkout local branch instead of remote
        branch_name = self.combo_box.currentText()
        if branch_name.startswith("origin/"):
            branch_name = branch_name.replace("origin/", "", 1)

        resutl = self.repo.git.checkout(branch_name)
        print(f" - Result: {resutl}")
        self.active_branch = get_repo_head_ref(self.repo)
        self.selectionchange(0)

    def editor_button_pressed(self) -> None:
        """Open the repository in an external editor.

        Uses the EDITOR environment variable, defaulting to 'code' (VS Code).
        """
        print(f"editor button pressed, {self.repo.working_tree_dir}")
        print(f"{self.abs_path}")
        editor_command_name = os.getenv("EDITOR", "code")
        subprocess.run([editor_command_name, self.abs_path], check=True)


class WCheckGUI(QWidget):
    """Main GUI window for wcheck application.

    Displays a grid of repositories with their current branches and
    provides controls for switching branches and opening in editor.

    Attributes:
        repo_objects: Dictionary mapping repository names to RepoObject instances.
    """

    def __init__(
        self,
        repos: dict[str, Repo],
        config_file_path: str = "",
        config_repo: dict[str, str] | None = None,
    ) -> None:
        """Initialize the WCheckGUI window.

        Args:
            repos: Dictionary mapping repository names to Repo objects.
            config_file_path: Path to the configuration file (displayed in UI).
            config_repo: Dictionary mapping repository names to their configured versions.
        """
        super(WCheckGUI, self).__init__()
        self.initUI(repos, config_file_path, config_repo)

    def initUI(
        self,
        repos: dict[str, Repo],
        config_file_path: str = "",
        config_repo: dict[str, str] | None = None,
    ) -> None:
        """Initialize the user interface.

        Creates the layout with repository controls including:
        - Repository name label
        - Branch selection combo box
        - Checkout button
        - Open in editor button
        - Config version label (if config_repo provided)

        Args:
            repos: Dictionary mapping repository names to Repo objects.
            config_file_path: Path to the configuration file (displayed in UI).
            config_repo: Dictionary mapping repository names to their configured versions.
        """
        layout = QVBoxLayout()
        if config_repo is not None:
            layout.addWidget(QLabel(f"Configuration file: {config_file_path}"))
        repo_layout = QGridLayout()
        layout.addLayout(repo_layout)
        self.repo_objects = {}
        for repo_i, repo_name in enumerate(repos):
            self.repo_objects[repo_name] = RepoObject(repos[repo_name], repo_name)

            repo_layout.addWidget(self.repo_objects[repo_name].qlabel, repo_i, 0)
            repo_layout.addWidget(self.repo_objects[repo_name].combo_box, repo_i, 1)
            repo_layout.addWidget(
                self.repo_objects[repo_name].checkout_button, repo_i, 2
            )
            repo_layout.addWidget(self.repo_objects[repo_name].editor_button, repo_i, 3)
            if config_repo is not None:
                if repo_name in config_repo:
                    label_config = QLabel(f"Config {config_repo[repo_name]}")
                    if (
                        config_repo[repo_name]
                        != self.repo_objects[repo_name].active_branch
                    ):
                        label_config.setStyleSheet("background-color: Red")
                    repo_layout.addWidget(label_config, repo_i, 4)
                else:
                    label_config = QLabel("Not in config")
                    label_config.setStyleSheet("color: Gray")
                    repo_layout.addWidget(label_config, repo_i, 4)
        self.setLayout(layout)


def show_gui(
    repos: dict[str, Repo],
    config_file_path: str = "",
    config_repo: dict[str, str] | None = None,
) -> NoReturn:
    """Launch the GUI application for managing repositories.

    Creates and displays the main WCheckGUI window. This function does not
    return as it enters the Qt event loop and exits the program when the
    window is closed.

    Args:
        repos: Dictionary mapping repository names to Repo objects.
        config_file_path: Path to the configuration file (displayed in UI).
        config_repo: Dictionary mapping repository names to their configured versions.
    """
    app = QApplication(sys.argv)
    window = WCheckGUI(repos, config_file_path, config_repo)
    window.setWindowTitle("Workspace Repositories")
    window.show()
    sys.exit(app.exec())
