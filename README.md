# Workspace Check (wcheck)

Compares diffent workspaces of git repositories and reports their differences. Two types of workspaces are supported:
- local workspace in a directory, represented by the current git status of each repository
- workspace defined by a vcs file

Possible comparisions:
- compare local workspace against a configuration file (command=wconfig)
- compare two configuration files, e.g. robot_A.vcs with robot_B.vcs (command=config-list)
- compare all git references of a configurion file, this includes all active branches and tags (command=config-versions)


## Usage

General usage
```bash
wcheck <command> <parameters>
```
Command options: status (default), wconfig, config-list, config-versions

Check workspace status
```bash
wcheck status [-w <workspace_location>] [-f,--full] [--gui] [-v,--verbose] [--show-time] 
```
It will show the git status of each repository. The legend is as follows:
- U: number of untracked files 
- M: number of changed files
- S: number of staged files
- ↓(arrow down): number of commits to pull
- ↑(arrow up): number of commits to push.

Workspace location can be specified with argument _-w_, if not provided, it will use current location. 

Compare workspace to a configuration file:
```bash
wcheck wconfig -c <config_file> [--gui] [-v] [--show-time]
```
The configuration file uses VCSTOOL structure, see an overview below

Compare multiple configuration files
```bash
wcheck config-list -c <config_A> <config_B> .. <config_N>
```
It will show a table comparing all configuration files.

Compare git references (branches and tags), of the configuration file
```bash
wcheck config-versions -c <config> [-h] [--full] [-v] [--show-time] [--full-path]
```
It will show a table comparing all versions of the configuration file.

Optional arguments
```
  -v --verbose: verbose output
  -h --help: show help
  --full: show full output, not only differences
  --gui: show graphical user interface
  --show-time: show elapsed time since last commit and reference creation
  --fetch: fetch repositories before comparing
  --full-path: show full path for each configuration file
```

## VCSTOOL Overview

This repo is based on vcstool (do not confuse with [vctools](https://github.com/vcstools/vcstools/), a similar but deprecated tool for working with vcs files). A workspace is defined with a yaml file describing each repository

```yaml
  repositories:
    <repo directory name>:
      type: <repo type>
      url: <repo url>
      version: <repo version>
```

where *repo directory name* is the name of the directory where the repo is cloned to (including parent folders in any), *repo url* is the url of the repo (using git or https), *repo type* is the type of repo (git, hg, svn, bzr, etc), and *repo version* is the version of the repo to check against, specified as a branch name, tag name, or commit hash. Example:

```yaml
  repositories:
    vcstool:
      type: git
      url: git@github.com:dirk-thomas/vcstool.git
      version: master
```
