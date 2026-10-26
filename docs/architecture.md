# Architecture

Authoritative plan: [`docs/plan/00-implementation-plan.md`](plan/00-implementation-plan.md) (diagram in section 8a).

Summary: Next.js PWA (Vercel) → FastAPI (Railway) → Supabase Postgres/Auth/Storage; a separate Python worker (Railway) runs scheduled discovery, matching and CV generation from a Postgres task table. Anthropic API is called only from the API/worker under budget limits.

Current state (end of Phase 1): repository skeleton, tooling, conventions, skills and CI only. No application logic yet.
