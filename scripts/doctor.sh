#!/usr/bin/env bash
# Checks the local toolchain for JobPilot AI development (macOS and Linux).
# Usage: scripts/doctor.sh   (exit code 1 if a required tool is missing)
set -u

OS="$(uname -s)"
missing=0

hint() { # $1 = macOS (brew) hint, $2 = Linux hint
  if [ "$OS" = "Darwin" ]; then echo "      install: $1"; else echo "      install: $2"; fi
}

version_ge() { # $1 = have, $2 = need (dotted, compared numerically)
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

check() { # name, command, min version ("" = any), required(1/0), mac hint, linux hint
  local name="$1" cmd="$2" min="$3" req="$4" mac="$5" lin="$6" ver
  if ! command -v "$cmd" >/dev/null 2>&1; then
    if [ "$req" = 1 ]; then echo "[MISSING]  $name"; missing=1; else echo "[optional] $name not found"; fi
    hint "$mac" "$lin"
    return
  fi
  ver="$("$cmd" --version 2>&1 | grep -Eo '[0-9]+(\.[0-9]+)+' | head -n1)"
  if [ -n "$min" ] && ! version_ge "${ver:-0}" "$min"; then
    echo "[OUTDATED] $name $ver (need >= $min)"; missing=1; hint "$mac" "$lin"
  else
    echo "[ok]       $name ${ver:-}"
  fi
}

echo "JobPilot AI environment check ($OS $(uname -m))"
check "git"        git        "2.30" 1 "brew install git" "apt install git"
check "python3"    python3    "3.12" 1 "brew install python@3.12" "apt install python3.12"
check "uv"         uv         ""     1 "brew install uv" "curl -LsSf https://astral.sh/uv/install.sh | sh"
check "node"       node       "20.0" 1 "brew install node@22" "use nvm or NodeSource"
check "pnpm"       pnpm       "9.0"  1 "brew install pnpm" "npm install -g pnpm"
check "psql"       psql       "15.0" 1 "brew install postgresql@16" "apt install postgresql-client-16"
check "libreoffice" soffice   ""     1 "brew install --cask libreoffice" "apt install libreoffice-writer"
check "docker"     docker     ""     0 "brew install --cask docker" "apt install docker.io"
check "gh"         gh         ""     0 "brew install gh" "apt install gh"
check "railway CLI" railway   ""     0 "brew install railway" "npm install -g @railway/cli (needed in Phase 9)"
check "supabase CLI" supabase ""     0 "brew install supabase/tap/supabase" "see supabase.com/docs/guides/cli (optional)"

if command -v npx >/dev/null 2>&1 && npx --no-install playwright --version >/dev/null 2>&1; then
  echo "[ok]       playwright $(npx --no-install playwright --version | grep -Eo '[0-9.]+' | head -n1)"
else
  echo "[optional] playwright not installed yet (installed with apps/web in Phase 3)"
fi

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then echo "[ok]       ANTHROPIC_API_KEY is set (value not shown)"; else echo "[note]     ANTHROPIC_API_KEY not set (needed from Phase 5)"; fi

if [ "$missing" = 0 ]; then echo "Result: all required tools present."; else echo "Result: required tools missing — see hints above."; fi
exit "$missing"
