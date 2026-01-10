# CLI Reference

Complete reference for all wcheck commands and options.

## Global Options

```bash
wcheck [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

---

## status

Check the status of all repositories in a workspace.

```bash
wcheck status [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `-w, --workspace-directory` | PATH | Workspace directory (default: current directory) |
| `-f, --full` | flag | Show all repositories, not only those with changes |
| `-v, --verbose` | flag | Show more detailed information |
| `--show-time` | flag | Show time since last commit |
| `--fetch` | flag | Fetch from remotes before checking status |
| `--gui` | flag | Launch GUI interface |

### Examples

**Check current directory:**

```bash
wcheck status
```

**Check a specific workspace:**

```bash
wcheck status -w /path/to/workspace
```

**Show all repositories including clean ones:**

```bash
wcheck status --full
```

**Fetch and show with timestamps:**

```bash
wcheck status --fetch --show-time
```

**Launch GUI for branch management:**

```bash
wcheck status --gui
```

### Output

```
Using workspace directory /home/user/projects
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Repo Name             ┃ Current Workspace         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ project-a (2M 3U)     │ feature/new-feature       │
│ project-b (1↑ 2↓)     │ main                      │
│ project-c (1S)        │ develop                   │
└───────────────────────┴───────────────────────────┘
```

**Status indicators:**

- `U` - Untracked files (orange)
- `M` - Modified files (red)
- `S` - Staged files (magenta)
- `↑` - Commits to push (green)
- `↓` - Commits to pull (yellow)

---

## wconfig

Compare workspace repository versions with a configuration file.

```bash
wcheck wconfig [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `-w, --workspace-directory` | PATH | Workspace directory (default: current directory) |
| `-c, --config` | PATH | **Required.** Configuration file path |
| `-f, --full` | flag | Show all repositories, not only mismatches |
| `-v, --verbose` | flag | Show more detailed information |
| `--show-time` | flag | Show time since last commit |
| `--gui` | flag | Launch GUI interface |

### Examples

**Compare workspace to config:**

```bash
wcheck wconfig -c workspace.yaml
```

**Compare specific workspace:**

```bash
wcheck wconfig -w /path/to/workspace -c config.yaml
```

**Show all repos including matches:**

```bash
wcheck wconfig -c config.yaml --full
```

**Use GUI for branch switching:**

```bash
wcheck wconfig -c config.yaml --gui
```

### Output

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Repo Name     ┃ Workspace version ┃ Config version ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ project-a     │ feature/branch    │ main           │
│ project-b     │ v1.0.0            │ v1.1.0         │
└───────────────┴───────────────────┴────────────────┘
```

---

## config-list

Compare multiple configuration files side by side.

```bash
wcheck config-list [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `-c, --config` | PATH | **Required.** Config files (can be used multiple times) |
| `-f, --full` | flag | Show all repositories, not only differences |
| `-v, --verbose` | flag | Show more detailed information |
| `--show-time` | flag | Show modification time |
| `--full-name` | flag | Show full file paths instead of filenames |

### Examples

**Compare two config files:**

```bash
wcheck config-list -c robot_a.yaml -c robot_b.yaml
```

**Compare three config files with full paths:**

```bash
wcheck config-list -c /path/to/config1.yaml -c /path/to/config2.yaml -c /path/to/config3.yaml --full-name
```

**Show all repositories:**

```bash
wcheck config-list -c config_a.yaml -c config_b.yaml --full
```

### Output

```
Comparing 2 config files
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Repo Name     ┃ robot_a.yaml   ┃ robot_b.yaml   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ navigation    │ v2.0.0         │ v2.1.0         │
│ perception    │ main           │ develop        │
│ planning      │ v1.0.0         │ N/A            │
└───────────────┴────────────────┴────────────────┘
```

---

## config-versions

Compare repository versions across git branches of a configuration file.

```bash
wcheck config-versions [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `-c, --config` | PATH | **Required.** Configuration file path |
| `-f, --full` | flag | Show all repositories, not only differences |
| `-v, --verbose` | flag | Show more detailed information |
| `--show-time` | flag | Show modification time for each branch |
| `--filter` | TEXT | Filter branches by pattern (can be used multiple times) |
| `--stash` | flag | Stash uncommitted changes before switching branches |

### Examples

**Compare across all branches:**

```bash
wcheck config-versions -c workspace.yaml
```

**Filter specific branches:**

```bash
wcheck config-versions -c workspace.yaml --filter main --filter develop
```

**Stash changes before comparing:**

```bash
wcheck config-versions -c workspace.yaml --stash
```

**Show all with verbose output:**

```bash
wcheck config-versions -c workspace.yaml --full --verbose
```

### Output

```
Comparing config versions in workspace.yaml
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Repo Name     ┃ main       ┃ develop    ┃ release    ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ project-a     │ v1.0.0     │ v1.1.0-dev │ v1.0.0     │
│ project-b     │ main       │ develop    │ v2.0.0     │
└───────────────┴────────────┴────────────┴────────────┘
```

---

## GUI Mode

When using `--gui` with `status` or `wconfig`, a graphical interface opens.

The GUI provides:

- **Branch selector** - Dropdown to select branches/tags
- **Checkout button** - Switch to selected branch
- **Editor button** - Open repository in your editor (uses `$EDITOR` or VS Code)
- **Status indicators** - Visual highlighting for dirty repositories
- **Config comparison** - Shows expected vs actual versions (in wconfig mode)

!!! note "GUI Requirements"
    The GUI requires the optional `gui` dependencies. Install with:
    ```bash
    pip install wcheck[gui]
    ```
