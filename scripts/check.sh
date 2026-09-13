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
if [ -f package.json ]; then
  npm run --silent lint  2>/dev/null || warn "no lint script"
  npm run --silent test  2>/dev/null || { echo "tests failed or missing"; fail=1; }
elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  command -v ruff   >/dev/null && ruff check . || warn "ruff not installed"
  command -v pytest >/dev/null && pytest -q     || { echo "tests failed or missing"; fail=1; }
else
  warn "No project checks defined yet."
  warn "Replace this block with real ones before this repo means anything."
fi

echo
[ "$fail" -eq 0 ] && ok "check.sh passed" || printf '\033[31m✗  check.sh failed\033[0m\n'
exit "$fail"
