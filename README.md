# Workspace Check (wcheck)

Compares different versions of git respositories and reports their differences. Possible options of workspace:
- local workspace in a directory, represented by the current git branch of each repository
- workspace defined by a vcs file

Possible comparisions:
- compare local workspace against a configuration file (command=local2config)
- compare two configuration files, e.g. robot_A.vcs with robot_B.vcs (command=config_list)
- compare all git references of a configurion file, this includes all active branches and tags (command=config_versions)


## Usage

General usage
```bash
wcheck [-w <workspace_location>] [-h] [--full] [--gui] [-v] [--show-time] [--references] [--full-path] [<config> .. <config>]
```

Check workspace status
```bash
wcheck [-w <workspace_location>] 
```
Workspace location can be specified with argument _-w_, if not provided, it will use current location. 

Compare workspace to a configuration file:
```bash
wcheck <config_file>
```
The configuration file uses VCSTOOL structure, see an overview below

Compare multiple configuration files
```bash
wcheck <config_A> <config_B> .. <config_N>
```

Compare git references, branches and tags, of the configuration file
```bash
wcheck --references <config> 
```

Optional arguments
```
  -v --verbose: verbose output
  -h --help: show \help
  --full: show full output, not only differences
  --show-time: show elapsed time since last commit and reference creation
  --fetch: fetch repositories before comparing
```

## VCSTOOL Overview

This repo is based on vcstool (do not confuse with [vctools](https://github.com/vcstools/vcstools/), a similar but deprecated tool for working with vcs files). A workspace is defined with a yaml file describing each repository:
Workspace definition

```yaml
  repositories:
    <repo directory name>:
      type: <>
      url: <repo url>
      version: master
```

where *repo directory name* is the name of the directory where the repo is cloned to (including parent folders in any), *repo url* is the url of the repo (using git or https), *repo typ* is the type of repo (git, hg, svn, bzr, etc), and *repo version* is the version of the repo to check against, specified as a branch name, tag name, or commit hash. Example:

```yaml
  repositories:
    vcstool:
      type: git
      url: git@github.com:dirk-thomas/vcstool.git
      version: master
```
## Other multi-repository tools



| Name                                                                         | Status    | Last release  | Language | Git interaction      | Terminal | GUI | Compares configs | Compares versions | Description                                                                                                     |
|------------------------------------------------------------------------------|-----------|---------------|----------|----------------------|----------|-----|------------------|-------------------|-----------------------------------------------------------------------------------------------------------------|
| <a href="https://github.com/davvid/garden/">garden</a>                       | active    | July 2022     | Rust     | native rust          | Yes      | no  | no               | no                | manage git project dependencies and worktrees, custom commands                                                  |
| <a href="https://github.com/nickgerace/gfold">gfold</a>                      | active    | July 2022     | Rust     | native rust          | Yes      | no  |                  |                   | lists status of multiple repositories, readonly, config file, rust                                              |
| <a href="https://github.com/motemen/ghq">ghq</a>                             | active    | May 2022      | Go       |                      | yes      |     |                  |                   | manage remote repository clones                                                                                 |
| <a href="https://github.com/tkrajina/git-plus">git-plus</a>                  | active    | August 2022   | Python   | git cli w/subprocess |          |     |                  |                   | multi: run commands in multiple git repos                                                                       |
| <a href="https://github.com/earwig/git-repo-updater">git-repo-updater</a>    | old       | 2019          | Python   | python gitRepo       |          |     |                  |                   | gitup: update multiple git repos at once                                                                        |
| <a href="https://github.com/nosarthur/gita">gita</a>                         | active    | January 2022  | Python   | git cli w/subprocess |          |     |                  |                   | manage multiple git repos                                                                                       |
| <a href="https://github.com/isacikgoz/gitbatch">gitbatch</a>                 |           |               | Go       |                      |          |     |                  |                   | manage multiple git repos in one place                                                                          |
| <a href="https://github.com/Masterminds/vcs">go-vcs</a>                      | active    | March 2022    | Go       |                      |          |     |                  |                   | version control repository management for Golang                                                                |
| <a href="https://github.com/siemens/kas">kas</a>                             | active    | August 2022   | Python   |                      |          |     |                  |                   | bitbake repository management tool                                                                              |
| <a href="https://github.com/fboender/multi-git-status">mgitstatus</a>        | active    | June 2022     | Bash     | git cli              |          |     |                  |                   | show status in multiple git repos                                                                               |
| <a href="https://manicli.com/">mani</a>                                      | active    | June 2022     |          |                      |          |     |                  |                   | manage multiple repositories, tasks, tags, YAML config, golang                                                  |
| <a href="https://github.com/lindell/multi-gitter">multi-gitter</a>           | active    | August 2022   | Go       |                      |          |     |                  |                   | run command and commit, manipulates pull requests, YAML config, tightly bound to forges (GitHub, GitLab, Gitea) |
| <a href="https://fabioz.github.io/mu-repo/">mu-repo</a>                      | active    | Octover 20220 | Python   |                      |          |     |                  |                   | help working with multiple git repos                                                                            |
| <a href="https://android.googlesource.com/tools/repo">repo</a>               | active    |               |          |                      |          |     |                  |                   | git repository management tool                                                                                  |
| <a href="https://github.com/vcstools/rosinstall">rosinstall</a>              | archived  | 2016          | Python   |                      |          |     |                  |                   | source code workspace management tool                                                                           |
| <a href="https://www.jelmer.uk/silver-platter-intro.html">silver-platter</a> | active    | March 2022    | Python   |                      |          |     |                  |                   | make automated changes in different version control repositories                                                |
| <a href="https://github.com/brandon-rhodes/uncommitted">uncommitted</a>      | active    | January 2021  | Python   |                      |          |     |                  |                   | find uncommitted changes in VCS directories                                                                     |
| <a href="https://github.com/ChristophBerg/dotfiles/blob/master/bin/v">v</a>  | abandoned | 2009          | Bash     |                      |          |     |                  |                   | version control subcommand wrapper                                                                              |
| <a href="https://www.greenend.org.uk/rjk/vcs/">VCS</a>                       | abandoned | 2018          |          |                      |          |     |                  |                   | a wrapper for version control systems                                                                           |
| <a href="https://github.com/xolox/python-vcs-repo-mgr">vcs-repo-mgr</a>      | abandoned | 2018          | Python   |                      |          |     |                  |                   | version control repository manager                                                                              |
| <a href="https://github.com/dirk-thomas/vcstool">vcstool</a>                 | active    |               | Python   | git cli w/subprocess |          |     |                  |                   | work with multiple repositories                                                                                 |
| <a href="https://github.com/vcstools/vcstools">vcstools</a>                  | archived  |               | Python   |                      |          |     |                  |                   | Python API wrapping version control systems                                                                     |
| <a href="https://github.com/vcstools/wstool">wstool</a>                      | archived  |               | Python   |                      |          |     |                  |                   | maintain workspace of projects from multiple VCSes                                                              |