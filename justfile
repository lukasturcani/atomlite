# List all commands.
default:
  @just --list

# Build docs.
docs:
  rm -rf docs/source/_autosummary
  make -C docs html
  echo Docs are in $PWD/docs/build/html/index.html

# Do a dev install.
dev:
  pip install -e '.[dev]'

# Run code checks.
check:
  #!/usr/bin/env bash

  error=0
  trap error=1 ERR

  echo
  (set -x; ruff . )

  echo
  ( set -x; ruff format --check . )

  echo
  ( set -x; mypy . )

  echo
  ( set -x; pytest --cov=src --cov-report term-missing )

  echo
  ( set -x; make -C docs doctest )

  test $error = 0

# Auto-fix code issues.
fix:
  ruff format .
  ruff --fix .

# Build a release.
build:
  python -m build
