#!/usr/bin/env python3
"""Package the claude.ai version of the quiz skill: dist/quiz-licencia-web.zip. Stdlib only.

Upload the zip in claude.ai: Settings > Features > Upload a skill (needs code execution enabled).
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "quiz-licencia-web.zip"
LIMIT = 30 * 1024 * 1024  # claude.ai skill bundle limit, uncompressed

files = {
    "SKILL.md": ROOT / "skill-web" / "SKILL.md",
    "scripts/quiz.py": ROOT / "scripts" / "quiz.py",
    **{f"content/{n}": ROOT / "content" / n for n in ("questions.json", "manual.json", "question_topics.json")},
    **{f"content/img/q/{p.name}": p for p in sorted((ROOT / "content" / "img" / "q").glob("*.jpg"))},
}
size = sum(p.stat().st_size for p in files.values())
assert size < LIMIT, f"bundle is {size / 2**20:.1f} MB, over the 30 MB limit"
OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for arc, src in files.items():
        z.write(src, f"quiz-licencia/{arc}")  # claude.ai expects the skill folder at the zip root
print(f"{OUT.relative_to(ROOT)}: {len(files)} files, {size / 2**20:.1f} MB uncompressed")
