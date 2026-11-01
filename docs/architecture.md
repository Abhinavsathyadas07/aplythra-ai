# Architecture

Authoritative plan: [`docs/plan/00-implementation-plan.md`](plan/00-implementation-plan.md) (diagram in section 8a).

Summary: Next.js PWA (Vercel) → FastAPI (Railway) → Supabase Postgres/Auth/Storage; a separate Python worker (Railway) runs scheduled discovery, matching and CV generation from a Postgres task table. Anthropic API is called only from the API/worker under budget limits.

Current state (end of Phase 1): repository skeleton, tooling, conventions, skills and CI only. No application logic yet.

## Backend foundation (Phase 2)

```
apps/api/app
  main.py            app factory: CORS, request-id + JSON request logging, generic 500 handler
  config.py          typed settings from env; production refuses unsafe values
  logging.py         JSON logs with request id (path only, no query strings/tokens/emails)
  core/auth.py       JWKS-based JWT verification (RS256/ES256 only; exp+sub required; audience/issuer)
  deps.py            current_user (401 on any failure), get_db (session bound to caller)
  db/session.py      sets request.jwt.claim.sub at the start of EVERY transaction (RLS identity)
  db/models.py       users, audit_logs (more tables arrive with their phases)
  routers/           /health (liveness), /health/ready (DB), /me (first-login provisioning)
alembic/             migration 0001: tables, RLS (ENABLE + FORCE), policies, least-privilege grants
```

Database roles: `jobpilot_owner` owns tables and runs migrations; `jobpilot_app` is the runtime role (no superuser, no BYPASSRLS). `audit_logs` grants only SELECT/INSERT to the runtime role (append-only). Handlers commit explicitly; sessions are closed and rolled back otherwise.

Supabase notes: asymmetric JWT signing keys (JWKS) are required; legacy HS256 shared-secret projects are rejected by design. Set `APP_DB_ROLE` to the role the API connects as.
