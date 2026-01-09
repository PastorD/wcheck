#!/usr/bin/env python3

import os
import sys
import subprocess

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


class RepoObject:
    def __init__(self, repo, repo_name, ignore_remote=False) -> None:
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

    def selectionchange(self, index):
        print(f"Selection changed to {self.combo_box.currentText()}")
        branch_name = self.combo_box.currentText()
        if branch_name.startswith("origin/"):
            branch_name = branch_name.replace("origin/", "", 1)
        if branch_name != self.active_branch:
            self.checkout_button.setEnabled(True)
        else:
            self.checkout_button.setEnabled(False)

    def checkout_branch(self):
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

    def editor_button_pressed(self):
        print(f"editor button pressed, {self.repo.working_tree_dir}")
        print(f"{self.abs_path}")
        editor_command_name = os.getenv("EDITOR", "code")
        subprocess.run([editor_command_name, self.abs_path], check=True)


class WCheckGUI(QWidget):
    def __init__(self, repos, config_file_path="", config_repo=None):
        super(WCheckGUI, self).__init__()
        self.initUI(repos, config_file_path, config_repo)

    def initUI(
        self,
        repos: list[Repo],
        config_file_path: str = "",
        config_repo: dict | None = None,
    ):
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
    repos: list[Repo], config_file_path: str = "", config_repo: dict | None = None
):
    # Create PyQt5 application with the list of repositories
    app = QApplication(sys.argv)
    window = WCheckGUI(repos, config_file_path, config_repo)
    window.setWindowTitle("Worspace Repositories")
    window.show()
    sys.exit(app.exec())
