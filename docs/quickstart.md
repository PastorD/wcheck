# Quick Start

Get started with wcheck in just a few minutes.

## Running wcheck

With [uvx](https://docs.astral.sh/uv/):

```bash
uvx wcheck <command> [options]
```

Or after [installing](installation.md):

```bash
wcheck <command> [options]
```

## Basic Commands

### 1. Check Repository Status

Navigate to a directory with git repositories and run:

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

### 2. Compare with Configuration File

```bash
wcheck wconfig -c workspace.yaml
```

### 3. Compare Multiple Configs

```bash
wcheck config-list -c robot_a.yaml -c robot_b.yaml
```

### 4. Compare Multiple Workspaces

Compare the same repositories across different directories:

```bash
wcheck status -w /path/to/workspace1 -w /path/to/workspace2
```

### 5. Interactive Interface

Use the TUI for interactive branch management:

```bash
wcheck status --tui
```

| Key | Action |
|-----|--------|
| `↑/↓` | Navigate |
| `Enter` | Select branch |
| `e` | Open in editor |
| `q` | Quit |

## Status Indicators

| Symbol | Meaning |
|--------|---------|
| `U` | Untracked files |
| `M` | Modified files |
| `S` | Staged files |
| `↑` | Commits to push |
| `↓` | Commits to pull |

## Common Options

| Option | Description |
|--------|-------------|
| `-f, --full` | Show all repositories |
| `-v, --verbose` | Detailed output |
| `--show-time` | Time since last commit |
| `--gui` | Graphical interface |
| `--tui` | Terminal interface |

## Next Steps

- [CLI Reference](cli.md) - Complete command documentation
- [Configuration](configuration.md) - YAML file format
