#!/usr/bin/env python3
"""Verify every .claude/skills/*/SKILL.md has front matter and the required sections."""
import re
import sys
from pathlib import Path

EXPECTED = [
    "job-discovery", "job-matcher", "ats-analyzer", "cv-tailor", "cover-letter-writer",
    "application-assistant", "application-tracker", "recruiter-assistant", "interview-preparation",
]
SECTIONS = ["Purpose", "Inputs", "Outputs", "Constraints", "Workflow", "Validation"]
root = Path(__file__).resolve().parent.parent / ".claude" / "skills"

errors: list[str] = []
for name in EXPECTED:
    path = root / name / "SKILL.md"
    if not path.is_file():
        errors.append(f"{name}: SKILL.md missing")
        continue
    text = path.read_text(encoding="utf-8")
    fm = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not fm:
        errors.append(f"{name}: front matter missing")
    else:
        meta = dict(line.split(":", 1) for line in fm.group(1).splitlines() if ":" in line)
        if meta.get("name", "").strip() != name:
            errors.append(f"{name}: front matter 'name' must equal directory name")
        if not meta.get("description", "").strip():
            errors.append(f"{name}: front matter 'description' missing")
    headings = {h.strip() for h in re.findall(r"^##\s+(.+)$", text, re.M)}
    for section in SECTIONS:
        if section not in headings:
            errors.append(f"{name}: missing section '## {section}'")

for extra in sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in EXPECTED):
    errors.append(f"{extra}: unexpected skill directory")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(EXPECTED)} skills valid")
