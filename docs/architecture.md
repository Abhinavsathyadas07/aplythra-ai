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

## Frontend foundation (Phase 3)

```
apps/web (Next.js 16, TypeScript, Tailwind 4; Cache Components deliberately off: every page is per-user)
  proxy.ts               refreshes the Supabase session cookie; every page except /login requires sign-in
  app/login              email+password sign-in / create account (one generic error, safe ?next= redirects)
  app/(app)/layout.tsx   server-side auth re-check, then the responsive shell
  components/app-shell   desktop sidebar; mobile bottom tab bar (44px+ tap targets, safe-area aware)
  lib/api.ts             fetch wrapper: bearer token from the Supabase session, 8s timeout, typed errors
  lib/supabase/*         browser and server clients (anon key only)
tests/e2e                Playwright (desktop + Pixel 7) against the production build
```

Test stack: the e2e run starts a **fake Supabase auth server** (`tests/e2e/fake-supabase.mjs`, test-only) that signs real RS256 tokens and serves a JWKS, the **real FastAPI backend** on a dedicated `jobpilot_e2e` database, and the built web app. There is no auth bypass in the application code.

Dashboard calls `GET /health/ready` and `GET /me` from the browser, so CORS between the web origin and the API is exercised for real.
