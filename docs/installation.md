# Installation

## Requirements

- Python 3.9 or higher (up to 3.12)
- Git

## Installation Methods

### Using uv (Recommended)

The easiest way to install wcheck is using [uv](https://docs.astral.sh/uv/), which installs the package in an isolated environment:

```bash
uv tool install wcheck
```
To use the GUI, install with the `gui` extra:

```bash
uv tool install 'wcheck[gui]'
```
then you can use the flag `--gui` with commands like `status` and `wconfig` to display the graphical interface.

### Using pip

You can also install using pip:

```bash
pip install wcheck
```
It is recommended to use a virtual environment, like venv or conda, to avoid conflicts with other packages. For venv, you can do:

```bash
python -m venv wcheck-env
source wcheck-env/bin/activate 
pip install wcheck
```
To use conda, install it first from a suitable distribution like Anaconda or Miniconda, then create a new environment:

```bash
conda create -n wcheck-env python=3.9
conda activate wcheck-env
pip install wcheck
```

### From Source

To install from source for development:

```bash
git clone https://github.com/dpastorm/wcheck.git
cd wcheck
pip install -e .
```

Or using uv:

```bash
git clone https://github.com/dpastorm/wcheck.git
cd wcheck
uv sync
```

## Optional Dependencies

### GUI Support

To enable the graphical user interface, install with the `gui` extra:

```bash
pip install wcheck[gui]
```

Or with uv:

```bash
uv sync --extra gui
```

This installs PySide6 for the Qt-based GUI.

### Development Dependencies

For development and testing:

```bash
pip install wcheck[dev]
```

Or with uv:

```bash
uv sync --extra dev
```

## Verifying Installation

After installation, verify wcheck is working:

```bash
wcheck --version
```

You should see the version number displayed.

## Updating

To update to the latest version:

```bash
# Using uv
uv tool upgrade wcheck

# Using pip
pip install --upgrade wcheck
```
