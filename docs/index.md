# wcheck

**Manage a workspace of git repositories**

wcheck is a command-line tool for managing and comparing workspaces containing multiple git repositories. It helps you track the status of multiple repositories, compare them against configuration files, and manage versions across different environments.

## Features

- 🔍 **Clear Status checking** - See the status of all repositories in a workspace at a glance. 
- 📊 **Configuration comparison** - Compare workspaces against YAML configuration files to use with vcs-tools
- 🔄 **Version tracking** - Compare repository versions across git branches and tags
- 🖥️ **GUI support** - Optional graphical interface for branch management
- ⚡ **Fast and efficient** - Built with modern Python for quick execution

## Quick Example

```bash
# Check status of all repositories in current directory
wcheck status

# Compare workspace to a configuration file
wcheck wconfig -c config.yaml

# Compare multiple configuration files
wcheck config-list -c robot_a.yaml -c robot_b.yaml
```

## Installation

```bash
# Using uv (recommended)
uv tool install wcheck

# Using pip
pip install wcheck
```

## Documentation

- [Installation Guide](installation.md) - Detailed installation instructions
- [Quick Start](quickstart.md) - Get started in minutes
- [CLI Reference](cli.md) - Complete command reference
- [API Reference](api.md) - Python API documentation

## License

MIT License - see [LICENSE](https://github.com/dpastorm/wcheck/blob/main/LICENSE) for details.
