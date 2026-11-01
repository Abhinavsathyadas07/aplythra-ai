# aplythra-ai (JobPilot AI)

Private, cloud-powered AI career agent for job discovery, ATS resume tailoring, application assistance, and intelligent tracking.

- Plan: [`docs/plan/00-implementation-plan.md`](docs/plan/00-implementation-plan.md)
- Conventions and hard rules: [`CLAUDE.md`](CLAUDE.md)
- Skills (operator/dev guidance): [`.claude/skills/`](.claude/skills/)

## Getting started
```bash
scripts/doctor.sh                      # check your toolchain (macOS or Linux)
scripts/dev-db.sh                      # local Postgres 16 + roles (Linux; see script for macOS)
cd apps/api && uv sync && uv run pytest
python3 scripts/lint_skills.py
cd apps/web && pnpm install && pnpm lint && pnpm typecheck && pnpm test:e2e   # needs scripts/dev-db.sh first
```
Copy `apps/api/.env.example` to `apps/api/.env` and fill in values locally. Never commit `.env` files or real CVs.

## Status
Phases 1-2 merged; Phase 3 (frontend foundation) in review. See the plan for the roadmap.
