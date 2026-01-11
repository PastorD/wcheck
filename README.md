# wcheck

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://pastord.github.io/wcheck/)
[![PyPI version](https://badge.fury.io/py/wcheck.svg)](https://badge.fury.io/py/wcheck)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Manage a workspace of git repositories**

wcheck compares different workspaces of git repositories and reports their differences. It supports:

- **Local workspaces** - directories containing multiple git repositories
- **Configuration files** - YAML files defining expected repository versions (vcstool format)

## Features

- 🔍 Check status of all repositories in a workspace
- 📊 Compare workspace against configuration files
- 🔄 Compare multiple configuration files
- 📈 Track version changes across git branches
- 🖥️ Optional GUI for branch management

## Installation

**Using uv (recommended):**
```bash
uv tool install wcheck
```

**Using pip:**
```bash
pip install wcheck
```

**With GUI support:**
```bash
pip install wcheck[gui]
```

## Quick Start

### Check Workspace Status

```bash
wcheck status
```

Output:
```
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Repo Name             ┃ Current Workspace         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ my-project (2M 1U)    │ feature/new-feature       │
│ another-repo (1↑)     │ main                      │
└───────────────────────┴───────────────────────────┘
```

**Status indicators:**
- `U` - Untracked files
- `M` - Modified files  
- `S` - Staged files
- `↑` - Commits to push
- `↓` - Commits to pull

### Compare with Configuration

```bash
wcheck wconfig -c workspace.yaml
```

### Compare Multiple Configs

```bash
wcheck config-list -c robot_a.yaml -c robot_b.yaml
```

### Compare Across Branches

```bash
wcheck config-versions -c workspace.yaml
```

## Commands

| Command | Description |
|---------|-------------|
| `status` | Check status of repositories in workspace |
| `wconfig` | Compare workspace to configuration file |
| `config-list` | Compare multiple configuration files |
| `config-versions` | Compare config across git branches |

## Common Options

| Option | Description |
|--------|-------------|
| `-w, --workspace-directory` | Workspace path (default: current dir) |
| `-c, --config` | Configuration file path |
| `-f, --full` | Show all repos, not just differences |
| `-v, --verbose` | Verbose output |
| `--show-time` | Show time since last commit |
| `--fetch` | Fetch remotes before checking |
| `--gui` | Launch graphical interface |

## Configuration File Format

wcheck uses [vcstool](https://github.com/dirk-thomas/vcstool)-compatible YAML files:

```yaml
repositories:
  my-project:
    type: git
    url: git@github.com:user/my-project.git
    version: main
  
  another-repo:
    type: git
    url: https://github.com/user/another-repo.git
    version: v1.0.0
```

## Similar Projects

- [vcstool](https://github.com/dirk-thomas/vcstool) - Version control system tool for managing multiple repositories
- [myrepos](https://myrepos.branchable.com/) - Tool to manage all your version control repos
- [repo](https://gerrit.googlesource.com/git-repo/) - Google's tool for managing multiple Git repositories
- [gita](https://github.com/nosarthur/gita) - Manage multiple Git repos with ease
- [mu-repo](https://github.com/fabioz/mu-repo) - Tool to work with multiple Git repositories

## Documentation

📖 **Full documentation:** [https://dpastorm.github.io/wcheck/](https://dpastorm.github.io/wcheck/)

- [Installation Guide](https://dpastorm.github.io/wcheck/installation/)
- [Quick Start](https://dpastorm.github.io/wcheck/quickstart/)
- [CLI Reference](https://dpastorm.github.io/wcheck/cli/)
- [Configuration Files](https://dpastorm.github.io/wcheck/configuration/)
- [API Reference](https://dpastorm.github.io/wcheck/api/)

## Development

```bash
# Clone repository
git clone https://github.com/dpastorm/wcheck.git
cd wcheck

# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Build documentation locally
uv sync --extra docs
uv run mkdocs serve
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Daniel Pastor (danpasmor@gmail.com)
