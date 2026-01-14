# Installation

## Requirements

- Python 3.9 or higher (up to 3.12)
- Git

## Installation Methods

### Using uv (Recommended)

The easiest way to install wcheck is using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install wcheck
```

### Using pip

```bash
pip install wcheck
```

!!! tip "Virtual Environment"
    It's recommended to use a virtual environment:
    ```bash
    python -m venv wcheck-env
    source wcheck-env/bin/activate 
    pip install wcheck
    ```

### From Source

```bash
git clone https://github.com/PastorD/wcheck.git
cd wcheck
uv sync  # or: pip install -e .
```

## Optional Dependencies

### GUI Support (PySide6)

For the graphical interface with branch selection dialogs:

```bash
uv tool install 'wcheck[gui]'
# or: pip install wcheck[gui]
```

Then use `--gui` flag with `status` or `wconfig` commands.

### TUI Support (Textual)

For the interactive terminal interface:

```bash
uv tool install 'wcheck[tui]'
# or: pip install wcheck[tui]
```

Then use `--tui` flag with `status` or `wconfig` commands.

### Development Dependencies

```bash
uv sync --extra dev
# or: pip install wcheck[dev]
```

## Verifying Installation

```bash
wcheck --version
```

## Updating

```bash
uv tool upgrade wcheck
# or: pip install --upgrade wcheck
```
