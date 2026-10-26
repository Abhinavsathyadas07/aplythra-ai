#!/usr/bin/env bash
# Starts a local Postgres 16 cluster (Linux/apt) and applies scripts/dev-db.sql.
# macOS: `brew services start postgresql@16`, then `psql -d postgres -f scripts/dev-db.sql`.
set -euo pipefail
cd "$(dirname "$0")"

if command -v pg_ctlcluster >/dev/null 2>&1; then
  pg_lsclusters | grep -q " online" || pg_ctlcluster 16 main start
  for _ in $(seq 1 20); do pg_isready -q && break; sleep 0.5; done
fi

if [ "$(id -u)" = 0 ] && id postgres >/dev/null 2>&1; then
  install -m 644 dev-db.sql /tmp/jobpilot-dev-db.sql
  su postgres -c "psql -v ON_ERROR_STOP=1 -q -d postgres -f /tmp/jobpilot-dev-db.sql"
  rm -f /tmp/jobpilot-dev-db.sql
else
  psql -v ON_ERROR_STOP=1 -q -d postgres -f dev-db.sql
fi
echo "Postgres ready: databases jobpilot, jobpilot_test; roles jobpilot_owner, jobpilot_app"
