#!/bin/sh
# Runs scripts/check.py with the Python of this project's conda environment, {{PROJECT_NAME}}.
# The git pre-commit hook (.githooks/pre-commit) and the Claude Code hook in
# .claude/settings.json call it. Its arguments go to check.py.

root=$(cd "$(dirname "$0")/.." && pwd)
name="{{PROJECT_NAME}}"

# Print a path in this shell's form (Git Bash on Windows turns C:\x into /c/x).
shell_path() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -u "$1"; else printf '%s\n' "$1"; fi
}

# Print the Python of the environment: the active one if it is this project's, else the one
# under conda's folder (found from $CONDA_EXE or Miniconda's and Anaconda's usual places).
env_python() {
  set --
  if [ "$CONDA_DEFAULT_ENV" = "$name" ] && [ -n "$CONDA_PREFIX" ]; then
    set -- "$(shell_path "$CONDA_PREFIX")"
  fi
  if [ -n "$CONDA_EXE" ]; then
    set -- "$@" "$(dirname "$(dirname "$(shell_path "$CONDA_EXE")")")/envs/$name"
  fi
  for base in "$HOME/AppData/Local/miniconda3" "$HOME/miniconda3" "$HOME/anaconda3"; do
    set -- "$@" "$base/envs/$name"
  done
  for prefix in "$@"; do
    for python in "$prefix/python.exe" "$prefix/bin/python"; do
      if [ -x "$python" ]; then printf '%s\n' "$python"; return 0; fi
    done
  done
  return 1
}

python=$(env_python) || python=""
if [ -z "$python" ]; then
  for candidate in python3 python; do
    if "$candidate" -c "" >/dev/null 2>&1; then python=$candidate; break; fi
  done
fi
if [ -z "$python" ]; then
  # After an edit, say nothing: the pre-commit hook reports it.
  [ "$1" = "--edited" ] && exit 0
  echo "No Python found for the checks. Create the conda environment $name (README, Setup)." >&2
  exit 2
fi
exec "$python" "$root/scripts/check.py" "$@"
