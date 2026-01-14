# wcheck

**Manage a workspace of git repositories**

wcheck is a command-line tool for managing and comparing workspaces containing multiple git repositories. It helps you track the status of repositories, compare them against configuration files, and manage versions across different environments.

## Features

- 🔍 **Status checking** - See the status of all repositories at a glance
- 📊 **Configuration comparison** - Compare workspaces against YAML configuration files (vcstool format)
- 🔄 **Version tracking** - Compare repository versions across git branches and tags
- 🖥️ **GUI support** - Optional graphical interface for branch management (PySide6)
- 💻 **TUI support** - Optional terminal interface for branch management (Textual)

## Quick Example

```bash
# Check status of all repositories
wcheck status

# Compare workspace to a configuration file
wcheck wconfig -c config.yaml

# Interactive terminal interface
wcheck status --tui
```

## Getting Started

<div class="grid cards" markdown>

-   :material-download: **[Installation](installation.md)**

    ---

    Install wcheck using uv or pip, with optional GUI/TUI support

-   :material-rocket-launch: **[Quick Start](quickstart.md)**

    ---

    Get started with basic commands in minutes

-   :material-console: **[CLI Reference](cli.md)**

    ---

    Complete documentation for all commands and options

-   :material-file-cog: **[Configuration](configuration.md)**

    ---

    Learn about YAML configuration file format

</div>

## License

MIT License - see [LICENSE](https://github.com/PastorD/wcheck/blob/main/LICENSE) for details.
