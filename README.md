# wcheck

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://pastord.github.io/wcheck/)
[![PyPI version](https://badge.fury.io/py/wcheck.svg)](https://badge.fury.io/py/wcheck)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Manage a workspace of git repositories**

wcheck compares different workspaces of git repositories and reports their differences. It supports local workspaces and YAML configuration files ([vcstool](https://github.com/dirk-thomas/vcstool) format).

## Quick Install

```bash
uv tool install wcheck       # Basic
uv tool install wcheck[gui]  # With GUI (PySide6)
uv tool install wcheck[tui]  # With TUI (Textual)
```

## Quick Example

```bash
# Check status of all repositories
wcheck status

# Compare with configuration file
wcheck wconfig -c workspace.yaml

# Interactive terminal interface
wcheck status --tui
```

## Documentation

📖 **Full documentation:** [https://pastord.github.io/wcheck/](https://pastord.github.io/wcheck/)

- [Installation Guide](https://pastord.github.io/wcheck/installation/) - Detailed installation instructions
- [Quick Start](https://pastord.github.io/wcheck/quickstart/) - Get started in minutes
- [CLI Reference](https://pastord.github.io/wcheck/cli/) - Complete command reference
- [Configuration Files](https://pastord.github.io/wcheck/configuration/) - YAML file format

## License

MIT License - see [LICENSE](LICENSE) for details.
