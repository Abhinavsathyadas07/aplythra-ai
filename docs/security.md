# Security & Privacy

Principles (details in plan section 8b): secrets via environment only; browser never sees DB or service keys; JWT verification + per-resource ownership checks + RLS; private storage; audit log for consequential actions; explicit approval before any submission or email; GDPR export/delete; minimal retention; mock data only in development.

Phase 1 controls in place:
- `.gitignore` blocks `.env*` (except `*.example`) and `*.docx`/`*.pdf` (real CVs); verified by `apps/api/tests/test_repo_hygiene.py`.
- `.claude/settings.json` denies Claude Code from reading `.env*` files.
- Env templates contain placeholders only (tested for secret-like patterns).

Not yet in place (planned): pre-commit secret scanner, RLS, auth, rate limits, budgets, retention job.
