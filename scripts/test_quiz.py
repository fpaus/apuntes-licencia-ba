"""Smoke test for quiz.py: python3 scripts/test_quiz.py"""
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import quiz  # noqa: E402

quiz.HISTORY = Path(tempfile.mkdtemp()) / "history.md"
pool, _ = quiz.load()
failed, passed = pool[0], pool[1]
run = {"mode": "simulacro", "results": [
    {"id": failed["id"], "section": failed["topic"], "ok": False, "eliminatoria": True},
    {"id": passed["id"], "section": passed["topic"], "ok": True},
]}
sys.stdin, out = io.StringIO(json.dumps(run)), sys.stdout
sys.stdout = io.StringIO()
quiz.cmd_record(None)
sys.stdout = out

h = quiz.history()
assert h == {failed["id"]: [False], passed["id"]: [True]}, h
w = dict(zip((q["id"] for q in pool), quiz.weights(pool, h)))
assert w[failed["id"]] > w[passed["id"]], "a failed question must weigh more than a passed one"
assert "DESAPROBADO" in quiz.HISTORY.read_text(), "a failed eliminatoria fails the simulacro"
print("ok")
