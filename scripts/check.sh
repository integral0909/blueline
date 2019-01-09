#!/usr/bin/env bash
# Everything that has to pass before a change is worth keeping.
#
# In this order on purpose. Lint is instant and catches the most noise, types
# come next, and the tests go last because they are the slowest and the only
# one that can tell you the answer is wrong rather than untidy.
set -uo pipefail

cd "$(dirname "$0")/.."
PY=.venv2018/bin

run () {
  printf '%-8s' "$1"
  shift
  if out=$("$@" 2>&1); then
    echo "ok"
  else
    echo "FAILED"
    echo "$out" | tail -20
    exit 1
  fi
}

run lint $PY/flake8 blueline tests
run types $PY/mypy blueline
run tests $PY/pytest tests -q

echo "all clear"
