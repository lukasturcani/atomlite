# List all commands.
default:
  @just --list

# Build docs.
docs:
  make -C docs html
  echo Docs are in $PWD/docs/build/html/index.html
