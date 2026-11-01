# Security & Privacy

Principles (details in plan section 8b): secrets via environment only; browser never sees DB or service keys; JWT verification + per-resource ownership checks + RLS; private storage; audit log for consequential actions; explicit approval before any submission or email; GDPR export/delete; minimal retention; mock data only in development.

Phase 1 controls in place:
- `.gitignore` blocks `.env*` (except `*.example`) and `*.docx`/`*.pdf` (real CVs); verified by `apps/api/tests/test_repo_hygiene.py`.
- `.claude/settings.json` denies Claude Code from reading `.env*` files.
- Env templates contain placeholders only (tested for secret-like patterns).

Phase 2 controls in place (tested in `apps/api/tests`):
- JWT verification: bad signature, expired, wrong audience/issuer, non-UUID subject, HS256/alg-confusion all return 401; error bodies never echo the token.
- RLS on `users` and `audit_logs` (ENABLE + FORCE) using the runtime role; two-user isolation, no-identity-sees-nothing, forged-insert and cross-user-update tests.
- `audit_logs` is append-only for the runtime role (UPDATE/DELETE denied).
- Identity is set per transaction (`set_config(..., true)`) and verified not to leak across transactions.
- Logs: JSON, request id, path only (no query strings, tokens or emails); unhandled errors return a generic 500.
- Production config guard: refuses missing JWKS URL, wildcard CORS and the dev DB password.

Known gaps (planned): pre-commit secret scanner, rate limiting, LLM budgets, retention job, security headers at the edge, error monitoring with PII scrubbing.
