# JobPilot AI — Architecture Validation & Implementation Plan

Status: **DRAFT — awaiting approval. No application code has been written.**
Date: 2026-10-26

## 1. Environment inspection

Important: this session runs in a **Linux cloud container (x86_64, 15 GB RAM)**, not on your MacBook Air M2. "Verify macOS tools" (Phase 1) can only be done by a checklist script you run locally; I cannot verify your Mac from here.

| Tool | Container | Needed for | Action |
|---|---|---|---|
| Python | 3.13.17 | backend (needs 3.12+) | OK (pin 3.12 in `.python-version` to match hosting) |
| uv | 0.11.32 | Python deps/venv | OK — use instead of pip/poetry |
| ruff / black | present | lint/format | Use ruff only (drop black) |
| Node / npm / pnpm | 22.22 / 10.9 / 10.28 | Next.js | OK — use pnpm |
| Git / gh | 2.43 / 2.89 | VCS | OK (GitHub access in-session is via MCP) |
| Docker | CLI only, **daemon unavailable** | local Postgres | Cannot run containers here; see below |
| psql | 16.15 | DB checks | OK |
| Playwright + Chromium | 1.63 / preinstalled | e2e tests, later app assistant | OK |
| LibreOffice | 24.2 | DOCX→PDF | OK for dev; must be in the worker image |
| pandoc | 3.1 | optional | Not needed |
| Supabase CLI | missing | migrations/local stack | Not needed if Alembic owns schema; install on Mac only |
| Vercel/Fly/Railway CLI | missing | deploy | Install at Phase 9 only |
| tesseract | missing | scanned-CV OCR | Skip (YAGNI; reject image-only PDFs) |
| Repo | 1 commit, README + .gitignore | | Greenfield |

Consequence of no Docker daemon: tests run against a PostgreSQL started directly (apt/`pg_ctl`) in the container, or against a Supabase dev project. I propose **local Postgres 16 binaries for CI/dev tests** (same engine as Supabase).

## 2. Architecture validation

Your stack is sound. Recommended adjustments:

1. **Auth: Supabase Auth issues JWTs; FastAPI only verifies them** (JWKS) — no custom password handling. The frontend talks to Supabase Auth directly for login; every data call goes through FastAPI with the bearer token. Browser never gets DB credentials or the service key.
2. **RLS is defense-in-depth, not the primary check.** FastAPI connects via SQLAlchemy as a non-superuser role and sets `request.jwt.claim.sub` per transaction (`SET LOCAL`), so RLS policies apply to API queries too, plus explicit ownership checks in the service layer. Alembic owns the schema *and* policies.
3. **Worker = same Python codebase, separate process.** Scheduling via a Postgres-backed job table (`scheduled_tasks`) polled with `SELECT … FOR UPDATE SKIP LOCKED`. No Redis/Celery in the MVP. Idempotency keys are unique constraints on that table.
4. **LLM use is narrow and structured.** Deterministic code does parsing, dedupe, keyword extraction and scoring arithmetic. Claude handles requirement extraction, evidence-grounded rewriting and explanations, returning JSON validated by Pydantic. Every generated CV claim must carry an `evidence_id`; a validator rejects output with unreferenced claims (this enforces "never invent facts").
5. **Model tiering for cost:** Haiku-class for bulk requirement extraction/classification, Sonnet-class for CV tailoring/cover letters. Prompt caching for the candidate profile. Per-user daily token budget enforced before each call.
6. **Hosting (recommendation):** Vercel (Next.js PWA) + **Fly.io or Railway** (two containers from one image: API and worker; LibreOffice needs a real container, so no serverless) + Supabase (Postgres, Auth, private Storage). Alternative: Render. Final pick deferred to Phase 9.
7. **PDF generation:** LibreOffice headless in the worker image is reliable but heavy (~500 MB image). Alternative is DOCX-only plus WeasyPrint HTML→PDF. Recommendation: keep LibreOffice (faithful to the DOCX the user edits).
8. **Frontend:** Next.js App Router + `@supabase/ssr` for sessions; hand-written service worker/manifest for PWA (avoid heavy PWA plugins). Notifications v1 = in-app + email digest; Web Push later.
9. **Job sources — the biggest real risk.** Candidates for the first source, to be confirmed by a short research spike before Phase 5: **Adzuna API** (free tier, Poland supported), **JustJoin.it** and **Pracuj.pl** (verify ToS / any public API or feed first), **RemoteOK/We Work Remotely** feeds, **company ATS public endpoints** (Greenhouse, Lever, Ashby, SmartRecruiters publish documented public job-board APIs). LinkedIn/Indeed: no scraping. Recommended first source: **Adzuna API** plus a Greenhouse/Lever adapter for target companies, behind a `JobSource` interface.
10. **Do not use browser-automation extensions of Claude Code as a runtime dependency.** Skills in `.claude/skills/` are operator/dev instructions; every capability also exists as a tested backend service in `apps/api/app/services/`.

## 3. Technical risks

| # | Risk | Likelihood / impact | Mitigation |
|---|---|---|---|
| 1 | No permitted job source with good Polish junior coverage | Med / High | Source-research spike first; adapter interface; company-ATS endpoints |
| 2 | LLM hallucinated CV claims | Med / Critical | Evidence-ID grounding + validator + human review of every generated CV; golden tests |
| 3 | Polish-market reality: many junior roles require Polish; work authorization unknown | High / High | Separate language & authorization match dimensions; hard "blocker" flags, not blended into a score; authorization stays "unverified" until you provide documents |
| 4 | ATS score misread as truth | Med / Med | Label as "internal estimate"; show evidence rather than a single number |
| 5 | Automated applying violating site ToS / account bans | Med / High | Post-MVP only; allow-list of sites; never CAPTCHA/anti-bot bypass; mandatory approval |
| 6 | LLM cost runaway | Med / Med | Budget table, per-run caps, cache by (job hash, profile version) |
| 7 | PII leakage (CVs, logs, prompts) | Med / High | Private bucket + signed URLs, log redaction, no PII in error monitoring, retention job |
| 8 | RLS misconfiguration | Med / High | Policy tests with two users in pytest; deny-by-default |
| 9 | Duplicate/uncontrolled retries | Med / Med | Idempotency keys, unique (user, job) application constraint, bounded retry w/ backoff |
| 10 | Prompt injection via job descriptions | Med / Med | Treat JD as untrusted data; structured output only; no tool use on JD text; never auto-submit |
| 11 | Free-tier limits (Supabase pause, Fly/Railway sleeping) | High / Med | Budget a paid tier at Phase 9 (~$25 Supabase Pro is optional) |
| 12 | Gmail OAuth verification for restricted scopes | Med / Med | Post-MVP; single-user app stays in "testing" mode with your own account |

## 4. Estimated costs (single user, MVP, order of magnitude — verify against current pricing before Phase 9)

| Item | Monthly |
|---|---|
| Anthropic API (≈60 jobs/day extraction on small model + ~10 tailored CVs/week on mid-tier) | **$5–20**; hard cap configurable (default $15) |
| Supabase | $0 (free) – $25 (Pro, for backups/no pausing) |
| Vercel Hobby | $0 |
| API + worker container (Fly/Railway/Render, small) | $5–15 |
| Domain (optional) | ~$1 |
| Error monitoring (Sentry free tier) | $0 |
| Job API (Adzuna free tier) | $0 |
| **Total** | **≈ $10–60/month**, realistic target ≈ $30 |

## 5. Repository structure

```
aplythra-ai/
├── CLAUDE.md                     # conventions, commands, hard rules (never invent facts, approval gates)
├── README.md
├── .gitignore  .editorconfig  .env.example (root, no secrets)
├── .claude/
│   ├── settings.json             # permissions (deny reading .env*)
│   └── skills/
│       ├── job-discovery/SKILL.md
│       ├── job-matcher/SKILL.md
│       ├── ats-analyzer/SKILL.md
│       ├── cv-tailor/SKILL.md
│       ├── cover-letter-writer/SKILL.md
│       ├── application-assistant/SKILL.md
│       ├── application-tracker/SKILL.md
│       ├── recruiter-assistant/SKILL.md
│       └── interview-preparation/SKILL.md
├── apps/
│   ├── api/                      # FastAPI
│   │   ├── pyproject.toml  .env.example  Dockerfile
│   │   ├── alembic.ini  alembic/versions/
│   │   ├── app/
│   │   │   ├── main.py  config.py  logging.py  deps.py
│   │   │   ├── core/             # auth (JWT verify), security, errors, rate-limit
│   │   │   ├── db/               # engine, session (RLS claim), models/
│   │   │   ├── routers/          # health, profile, jobs, matches, resumes, applications…
│   │   │   ├── schemas/          # Pydantic
│   │   │   ├── services/         # discovery, matching, ats, cv_tailor, cover_letter, tracker…
│   │   │   ├── sources/          # JobSource interface + adapters
│   │   │   ├── llm/              # Anthropic client, prompts, budget, JSON validation
│   │   │   ├── documents/        # docx builder, pdf conversion, parsing
│   │   │   └── worker/           # scheduler loop, task handlers
│   │   └── tests/                # unit, integration (db), rls, contract
│   └── web/                      # Next.js + TS + Tailwind PWA
│       ├── app/  components/  lib/  public/manifest.webmanifest  public/sw.js
│       └── tests/ (Playwright)
├── packages/                     # (empty until needed — no shared pkg in MVP)
├── scripts/                      # doctor.sh (macOS/Linux env check), seed_mock.py
├── docs/
│   ├── plan/  architecture.md  security.md  runbook.md  data-retention.md
│   └── adr/
└── .github/workflows/ci.yml      # ruff, pytest, tsc, eslint, playwright
```

## 6. Data model (summary; full DDL in Phase 2/4)

All user-owned tables: `id uuid pk`, `user_id uuid fk → users`, `created_at`, `updated_at`; RLS `user_id = auth.uid()`.
Shared (non-RLS, read-only to users): `job_sources`, `job_postings` (global, deduped by `(source_id, external_id)` and a normalized content hash) — per-user state lives in `match_assessments` / `applications`.

Key constraints: `UNIQUE(applications.user_id, job_posting_id)`; `UNIQUE(match_assessments.user_id, job_posting_id, profile_version)`; idempotency key `UNIQUE(user_id, key)` on `scheduled_tasks`/`agent_runs`; FK `ON DELETE CASCADE` from `users` for GDPR deletion; evidence rows link every profile fact (`skills`, `education`, `employment_history`, `projects`) used by `resume_versions.claims[]`. `audit_logs` is append-only (no UPDATE/DELETE grant). Indexes on `(user_id, status)`, `(job_postings.posted_at)`, GIN/trigram on title for search.

## 7. Phase 1 plan (smallest working implementation)

Objective: a reproducible, documented monorepo skeleton with tooling and CI — **no business logic**.

Tasks (one at a time, each committed separately):
1. `scripts/doctor.sh`: checks git, Python ≥3.12, uv, Node ≥20, pnpm, Docker or Postgres, LibreOffice, Playwright; prints install hints for macOS (Homebrew) and Linux. You run it on the Mac.
2. Monorepo directories, `.editorconfig`, extended `.gitignore` (env files, `*.docx`/`*.pdf` of real CVs, `storage/`).
3. `.env.example` files (API, web) with placeholders only; secret-scan pre-commit config.
4. `CLAUDE.md` (stack, commands, conventions, non-negotiable rules) and `.claude/settings.json`.
5. Skill stubs: nine `SKILL.md` files with purpose/inputs/outputs/constraints/workflow/validation sections (filled in the phase that implements each service).
6. `apps/api` minimal `pyproject.toml` (uv) with ruff + pytest config and one smoke test; `apps/web` deliberately **not** scaffolded until Phase 3.
7. `.github/workflows/ci.yml`: ruff + pytest for API.
8. `docs/architecture.md`, `docs/security.md` (initial), ADR-001 (stack decisions above).

### Phase 1 acceptance criteria
- [ ] `git clone` + `scripts/doctor.sh` runs on macOS and Linux and reports missing tools with install commands (Linux run verified here; **macOS run is yours to confirm**).
- [ ] Directory layout matches section 5 (web app placeholder only).
- [ ] `.gitignore` blocks `.env*` (except `.env.example`), real CV files, venvs, `node_modules`, build output; verified by `git check-ignore`.
- [ ] No secrets in repo; secret scan passes.
- [ ] `CLAUDE.md` exists and states the hard rules (no fabricated facts, explicit approval for submit/send, mock data only, no scraping bypass).
- [ ] Nine `SKILL.md` files exist with all required sections; a lint script verifies section presence.
- [ ] `uv run ruff check` and `uv run pytest` pass locally; CI workflow file is valid and passes on the PR.
- [ ] Documentation updated; test results reported honestly.

## 8. Phase roadmap and MVP cut

The MVP (spec §11) maps to Phases 1–6 plus the tracker and scheduler pieces of 8/9, deployed in 9. Order: 1 → 2 → 3 → 4 → 5 → 6 → (tracker subset of 8) → 9 → 10 → 7 and the rest of 8 after the MVP is stable. Each phase ends with a test report and a stop for your approval.

## 8a. Architecture diagram

```
 MacBook / Android (PWA)                       Supabase
 ┌────────────────────┐   login (JWT)    ┌──────────────────────┐
 │ Next.js on Vercel  │ ───────────────► │ Auth                 │
 │ (no secrets, no DB │                  │ Postgres (RLS)       │
 │  access)           │                  │ Private Storage      │
 └─────────┬──────────┘                  └───────▲──────────▲───┘
           │ HTTPS + bearer JWT                  │          │
           ▼                                     │          │
 ┌────────────────────┐   enqueue tasks   ┌──────┴──────────┴───┐
 │ FastAPI API        │ ────────────────► │ Worker + scheduler  │
 │ (verify JWT, authz,│  (scheduled_tasks │ discovery, matching,│
 │  audit, budgets)   │   table, SKIP     │ CV build (DOCX→PDF),│
 └────────────────────┘   LOCKED)         │ follow-up checks    │
                                          └───┬────────────┬────┘
                                              ▼            ▼
                                     Anthropic API   Permitted job sources
                                     (budget-capped) (APIs/feeds only)
 Post-MVP: Playwright application assistant (approval-gated), Gmail OAuth (read + draft only)
```

## 8b. Security considerations

- **Secrets:** env vars only; `.env*` gitignored; secret scanning in pre-commit and CI; service-role key and Anthropic key exist only in API/worker.
- **AuthN/AuthZ:** Supabase Auth JWT verified in FastAPI; ownership check on every user-owned resource plus RLS deny-by-default; two-user cross-access tests in CI.
- **Data protection:** TLS everywhere; private bucket with short-lived signed URLs; CV text and personal data redacted from logs and error monitoring; mock data only in development.
- **Consequential actions:** submission, email sending, and declarations require an explicit approval row (`application_approvals`) tied to a document version; all such actions write to append-only `audit_logs`.
- **Abuse and cost control:** per-user rate limits, daily token/cost budgets, idempotency keys, bounded retries with backoff, kill switch for scheduled tasks.
- **Untrusted input:** job descriptions and recruiter emails are treated as data (prompt-injection safe: structured outputs, no tool execution driven by them).
- **Compliance:** GDPR export and delete endpoints, retention job for old documents/logs, documented lawful basis and subprocessors (Anthropic, Supabase, hosting).
- **Platform rules:** no CAPTCHA/anti-bot bypass, no scraping of sources that forbid it; per-source ToS recorded in `job_sources`.
- **Sessions:** short-lived access tokens, refresh rotation, httpOnly cookies via `@supabase/ssr`, session-expiry tests in Phase 10.

## 9. Decisions I need from you

1. **Hosting for API/worker:** Fly.io, Railway, or Render? (default: Railway, simplest)
2. **First job source:** OK to start with Adzuna + Greenhouse/Lever adapters after a source-research spike? (default: yes)
3. **Dev database:** local Postgres 16 for tests plus a Supabase dev project you create (default), or Supabase only?
4. **Work authorization:** you'll supply status/documents during Phase 4; until then it is stored as `unverified` and never put in applications.
5. **CI:** OK to use GitHub Actions on this repo?
6. **Polish-language level** (for the separate language-match dimension): to be entered in your profile in Phase 4.
