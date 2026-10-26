"""Phase 1 guards: repository conventions that protect secrets and candidate data."""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ENV_TEMPLATES = [
    REPO / ".env.example",
    REPO / "apps/api/.env.example",
    REPO / "apps/web/.env.example",
]
SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),  # JWT
    re.compile(r"postgres(ql)?(\+\w+)?://[^:\s]+:(?!CHANGE_ME)[^@\s]{4,}@"),
]


def test_env_templates_exist_and_hold_no_secrets() -> None:
    for path in ENV_TEMPLATES:
        assert path.is_file(), f"{path} missing"
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(text), f"{path} looks like it contains a secret"


def _ignored(rel: str) -> bool:
    result = subprocess.run(  # noqa: S603
        ["git", "check-ignore", "-q", rel],  # noqa: S607
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def test_sensitive_paths_are_gitignored() -> None:
    for rel in [".env", "apps/api/.env", "apps/web/.env.local", "master_cv.docx", "cv.pdf"]:
        assert _ignored(rel), f"{rel} must be gitignored"
    for rel in [".env.example", "apps/api/.env.example"]:
        assert not _ignored(rel), f"{rel} must be committable"


def test_skills_lint_passes() -> None:
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(REPO / "scripts/lint_skills.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_claude_md_states_hard_rules() -> None:
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8").lower()
    for phrase in [
        "never invent candidate facts",
        "explicit approval",
        "mock data only",
        "unverified",
    ]:
        assert phrase in text, f"CLAUDE.md missing rule: {phrase}"
