# Configuration Files

wcheck uses YAML configuration files based on the [vcstool](https://github.com/dirk-thomas/vcstool) format to define workspaces.

## File Format

A configuration file defines a set of repositories with their expected versions:

```yaml
repositories:
  <repository-name>:
    type: <vcs-type>
    url: <repository-url>
    version: <branch-tag-or-commit>
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Version control system type (typically `git`) |
| `url` | Yes | Repository URL (SSH or HTTPS) |
| `version` | Yes | Branch name, tag name, or commit SHA |

## Examples

### Basic Configuration

```yaml
repositories:
  my-library:
    type: git
    url: git@github.com:user/my-library.git
    version: main
  
  utils:
    type: git
    url: https://github.com/user/utils.git
    version: v2.0.0
```

### Nested Directories

Repository names can include paths for nested directory structures:

```yaml
repositories:
  src/core:
    type: git
    url: git@github.com:org/core.git
    version: main
  
  src/plugins/auth:
    type: git
    url: git@github.com:org/auth-plugin.git
    version: v1.0.0
  
  external/vendor:
    type: git
    url: https://github.com/vendor/lib.git
    version: release-2.x
```

### Using Commit SHAs

For reproducible builds, use commit SHAs:

```yaml
repositories:
  stable-dep:
    type: git
    url: git@github.com:org/stable-dep.git
    version: a1b2c3d4e5f6789012345678901234567890abcd
```

### Using Tags

For released versions:

```yaml
repositories:
  framework:
    type: git
    url: git@github.com:org/framework.git
    version: v3.2.1
```

## Real-World Example

A robotics workspace configuration:

```yaml
# robot_workspace.yaml
repositories:
  # Core packages
  ros2/core:
    type: git
    url: git@github.com:robotics-org/ros2-core.git
    version: humble
  
  ros2/navigation:
    type: git
    url: git@github.com:robotics-org/navigation2.git
    version: v1.2.0
  
  # Custom packages
  robot_drivers:
    type: git
    url: git@github.com:company/robot-drivers.git
    version: main
  
  robot_description:
    type: git
    url: git@github.com:company/robot-description.git
    version: v2.0.0
  
  # Vendor dependencies
  vendor/lidar_sdk:
    type: git
    url: https://github.com/vendor/lidar-sdk.git
    version: release-3.x
```

## Using with wcheck

### Check Workspace Against Config

```bash
# See which repos differ from config
wcheck wconfig -c robot_workspace.yaml

# Show all repos
wcheck wconfig -c robot_workspace.yaml --full
```

### Compare Multiple Configs

Useful for comparing different robot configurations:

```bash
wcheck config-list -c robot_a.yaml -c robot_b.yaml -c robot_c.yaml
```

### Track Config Changes Across Branches

See how versions changed across releases:

```bash
wcheck config-versions -c robot_workspace.yaml --filter "release/*"
```

## Compatibility

wcheck configuration files are compatible with [vcstool](https://github.com/dirk-thomas/vcstool). You can use the same files with both tools:

```bash
# Import workspace using vcstool
vcs import < workspace.yaml

# Check status using wcheck
wcheck wconfig -c workspace.yaml
```

## Tips

!!! tip "Keep configs in version control"
    Store your workspace configuration files in a git repository to track changes over time. Use `config-versions` to compare across branches.

!!! tip "Use SSH URLs for private repos"
    SSH URLs (`git@github.com:...`) work better with SSH keys for private repositories.

!!! tip "Pin versions for releases"
    Use tags or commit SHAs instead of branch names for release configurations to ensure reproducibility.
