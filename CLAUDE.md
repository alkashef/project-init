# project-init

## Purpose

This repository is the source of the `project-init` Claude Code skill, which sets up new projects.
Run in an empty folder, the skill gives the new project its starting files (`CLAUDE.md` and
path-scoped rules, docs, README, tool configs, starting folders), commits them, creates a GitHub
repository, and pushes. Everything the skill needs is in `skills/project-init/`.

`skills/project-init/assets/` holds the files new projects receive, including their `CLAUDE.md`
master (`CLAUDE_GOLDEN.md`). This file is for working on the skill itself, not part of what a new
project gets.

## Environment

Conda environment: `project-init`. Use it for all testing, linting and type checks in this
repository. Do not use `base`, another project's environment, or the system Python.

Run commands in it with `conda run -n project-init <command>`, for example
`conda run -n project-init python skills/project-init/scripts/build_instance.py <folder> --dry-run`.

## Git

Every commit is followed by a sync: pull (`git pull --rebase`), then `git push` to `origin`. Never
leave a commit only on this machine. If the pull or the push fails, stop and report it.
