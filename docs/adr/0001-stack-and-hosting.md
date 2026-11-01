# ADR-0001: Stack and hosting

Status: accepted (2026-10-26)

- Backend: Python 3.12+, FastAPI, SQLAlchemy, Alembic; worker is the same codebase in a separate process.
- Scheduler: Postgres task table with `FOR UPDATE SKIP LOCKED` and idempotency keys; no Redis/Celery in the MVP.
- Frontend: Next.js + TypeScript + Tailwind PWA on Vercel.
- Data/Auth/Storage: Supabase; the API verifies Supabase JWTs and never handles passwords.
- API + worker hosting: **Railway** (user decision). Container image includes LibreOffice for DOCX→PDF.
- First job sources: Adzuna API and public Greenhouse/Lever endpoints, subject to a terms check before Phase 5.
- CI: GitHub Actions.
- Dev database: local Postgres 16 for tests plus a Supabase dev project.

Consequences: no serverless for the API (document conversion needs a full container); Docker daemon is unavailable in the cloud dev container, so tests use Postgres binaries directly.
