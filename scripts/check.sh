#!/usr/bin/env bash
# One command that tells you whether the repo is healthy.
# CI runs exactly this, so "it passes locally" and "it passes in CI" mean the same thing.
set -euo pipefail

fail=0
step() { printf '\n\033[1m── %s\033[0m\n' "$1"; }
warn() { printf '\033[33m!  %s\033[0m\n' "$1"; }
ok()   { printf '\033[32m✓  %s\033[0m\n' "$1"; }

step "Secret scan"
# Catches the mistake that is expensive and silent: a credential file that got
# tracked before .gitignore covered it. .gitignore is not retroactive.
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf '\033[31m✗  Not a git repository — cannot verify what is tracked.\033[0m\n'
  exit 1
fi
tracked_secrets=$(git ls-files | grep -Ei '(^|/)\.env($|\.)|\.pem$|\.p12$|\.pfx$|(^|/)id_rsa|\.tfstate$' | grep -v '\.example$' || true)
if [ -n "$tracked_secrets" ]; then
  printf '\033[31m✗  Tracked files that look like secrets:\033[0m\n%s\n' "$tracked_secrets"
  echo "   Remove with: git rm --cached <file>"
  fail=1
else
  ok "no credential-shaped files tracked"
fi

step "Project checks"
# ruff for lint and formatting, then the tests. pytest is the intended runner (it's in the dev
# extras), but the tests are written so `python -m unittest` runs them too, so a machine without
# pytest still gets a real answer instead of a skipped step.
if command -v ruff >/dev/null; then
  ruff check src tests    || fail=1
  ruff format --check src tests >/dev/null || { echo "run: ruff format src tests"; fail=1; }
else
  warn "ruff not installed; lint skipped"
fi
if command -v pytest >/dev/null; then
  pytest -q || fail=1
else
  warn "pytest not installed; falling back to unittest"
  PYTHONPATH=src python3 -m unittest discover -s tests -q || fail=1
fi

echo
[ "$fail" -eq 0 ] && ok "check.sh passed" || printf '\033[31m✗  check.sh failed\033[0m\n'
exit "$fail"
