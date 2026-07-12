#!/usr/bin/env bash
set -eu

repository_url="https://github.com/SFEW888/ExamLex"

usage() {
  echo "Usage: ./install.sh [codex|claude|cursor] [--project] [--dry-run] [--force]"
  echo "Repository: $repository_url"
  echo "Clone: git clone $repository_url.git"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

agent="${1:-codex}"
shift || true

case "$agent" in
  codex|claude|cursor) ;;
  *)
    usage >&2
    exit 2
    ;;
esac

project=false
dry_run=false
force=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --project) project=true ;;
    --dry-run) dry_run=true ;;
    --force) force=true ;;
    --no-force) force=false ;;
    --help|-h) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
else
  echo "Python 3.10+ is required for the installer." >&2
  exit 1
fi

if ! "$python_cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  echo "Python 3.10+ is required for the installer." >&2
  exit 1
fi

script="scripts/install_${agent}.py"
set --

if [ "$project" = true ]; then
  case "$agent" in
    codex) set -- "$@" --dest ".agents/skills" ;;
    claude) set -- "$@" --dest ".claude/skills" ;;
    cursor) set -- "$@" --dest ".cursor/skills" ;;
  esac
fi

if [ "$dry_run" = true ]; then
  set -- "$@" --dry-run --json
fi

if [ "$force" = true ]; then
  set -- "$@" --force
fi

"$python_cmd" "$script" "$@"
