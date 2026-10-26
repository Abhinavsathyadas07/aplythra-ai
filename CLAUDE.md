# CLAUDE.md — JobPilot AI (repo: aplythra-ai)

AI-assisted job application platform for one candidate (Warsaw, junior IT roles). Quality over volume.
Plan of record: `docs/plan/00-implementation-plan.md`. Work one phase at a time and stop for approval between phases.

## Hard rules (never violate)
1. **Never invent candidate facts.** Every CV/cover-letter claim must trace to verified profile data (evidence id). Academic work is not paid professional experience.
2. **No external submission or email send without an explicit approval record.** Declarations, consents and sensitive answers always need human review.
3. **Mock data only in development and tests.** Never commit real CVs, personal data, or `.env*` files (except `.env.example`).
4. **No scraping that violates a source's terms; no CAPTCHA/anti-bot bypass.** Use official APIs/feeds.
5. **Work authorization stays `unverified`** until the user supplies current documents/answers.
6. Match percentages are internal estimates, never "ATS scores". Polish-language and work-authorization requirements are separate dimensions, never blended into one score.
7. Secrets only via environment variables; the browser never receives DB credentials, service keys or API keys.
8. Never claim tests passed unless they were run successfully; report failures verbatim.

## Stack
Python 3.12+ / FastAPI / SQLAlchemy / Alembic (apps/api) · Next.js + TypeScript + Tailwind PWA (apps/web) · Supabase (Postgres, Auth, private Storage) · Anthropic API · Playwright · Railway (API + worker), Vercel (web).

## Commands
- Env check: `scripts/doctor.sh`
- API (from `apps/api`): `uv sync` · `uv run ruff check .` · `uv run ruff format --check .` · `uv run pytest`
- Skill lint: `python3 scripts/lint_skills.py`
- Web (from `apps/web`, from Phase 3): `pnpm install` · `pnpm lint` · `pnpm test`

## Conventions
- Python: ruff (lint + format), type hints everywhere, Pydantic for all I/O, services in `app/services/`, routers thin.
- Every user-owned table has `user_id` + RLS; every endpoint checks ownership; consequential actions write `audit_logs`.
- Expensive/consequential operations take an idempotency key; retries are bounded with backoff.
- LLM output is JSON validated by Pydantic; job descriptions and emails are untrusted data (prompt-injection safe).
- Small PRs, conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`). Add dependencies only with a stated reason.
- Skills in `.claude/skills/` are operator/dev instructions; each needs a matching tested backend service when it runs in production.
