# Quick Start

This guide will help you get started with wcheck in just a few minutes.

## Basic Workflow

The simpliest way to use wcheck is with [`uvx`](https://docs.astral.sh/uv/):

```bash
uvx wcheck <command> [options]
```
To use with wcheck with the graphical interface, add the `--gui` flag. If you use `uvx`, make sure use the `gui` extra:

```bash
uvx --from 'wcheck[gui]' wcheck <command> --gui [options]
```



To install wcheck, see the [Installation Guide](installation.md).

### 1. Check Repository Status

Navigate to a directory containing multiple git repositories and run:

```bash
wcheck status
```

This will display a table showing the status of each repository:

```
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Repo Name             ┃ Current Workspace         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ my-project (2M 1U)    │ feature/new-feature       │
│ another-repo (1↑)     │ main                      │
└───────────────────────┴───────────────────────────┘
```

#### Status Legend

| Symbol | Meaning |
|--------|---------|
| `U` | Untracked files |
| `M` | Modified files |
| `S` | Staged files |
| `↑` | Commits ahead of remote (to push) |
| `↓` | Commits behind remote (to pull) |

### 2. Compare with Configuration File

If you have a YAML configuration file defining expected repository versions:

```bash
wcheck wconfig -c workspace.yaml
```

This shows which repositories match or differ from the configuration:

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Repo Name     ┃ Workspace version ┃ Config version ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ my-project    │ feature/branch    │ main           │
│ another-repo  │ main              │ main           │
└───────────────┴───────────────────┴────────────────┘
```

### 3. Compare Configuration Files

Compare two or more configuration files to see differences:

```bash
wcheck config-list -c robot_a.yaml -c robot_b.yaml
```

### 4. Compare Versions Across Branches

See how a configuration file differs across git branches:

```bash
wcheck config-versions -c workspace.yaml
```

## Common Options

These options work with most commands:

| Option | Description |
|--------|-------------|
| `-f, --full` | Show all repositories, not just differences |
| `-v, --verbose` | Show detailed output |
| `--show-time` | Show time since last commit |
| `--gui` | Launch graphical interface |
| `-w, --workspace-directory` | Specify workspace path |

## Example Configuration File

Create a `workspace.yaml` file:

```yaml
repositories:
  my-project:
    type: git
    url: git@github.com:user/my-project.git
    version: main
  
  another-repo:
    type: git
    url: git@github.com:user/another-repo.git
    version: v1.0.0
```

## Next Steps

- Read the [CLI Reference](cli.md) for complete command documentation
- Learn about [Configuration Files](configuration.md) in detail
- Check the [API Reference](api.md) if you want to use wcheck programmatically
