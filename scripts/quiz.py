#!/usr/bin/env python3
"""Question picker and result log for the quiz-licencia skill. Stdlib only.

  python3 scripts/quiz.py pick --mode simulacro
  python3 scripts/quiz.py pick --mode temas --sections 6.3,6.8 --n 20
  python3 scripts/quiz.py sections            # section ids, titles and bank coverage
  python3 scripts/quiz.py record < results.json
  python3 scripts/quiz.py export              # progress block to paste into a new chat (claude.ai)
  python3 scripts/quiz.py import <block>      # restore that block into the history

QUIZ_HISTORY overrides the history file path (claude.ai: the skill folder is read-only).
"""
import argparse
import base64
import datetime
import json
import random
import re
import os
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
HISTORY = Path(os.environ.get("QUIZ_HISTORY", ROOT / "progress" / "quiz-history.md"))
BLOCK_PREFIX = "LIC1:"
KEEP = 5  # results kept per question in a progress block

# Exam format from the manual, p. 20: at least 40 questions, 5 eliminatorias, pass mark 75 %.
EXAM_SIZE, EXAM_ELIM, PASS = 40, 5, 0.75
THIN = 3  # a section with fewer bank questions than this is "thinly covered"
ROW_RE = re.compile(r"^\| (\S+) \| (\S+) \| (✔|✘) \|")


def load():
    qs = json.loads((CONTENT / "questions.json").read_text())
    topics = json.loads((CONTENT / "question_topics.json").read_text())
    manual = json.loads((CONTENT / "manual.json").read_text())
    sections = {s["id"]: {"title": s["title"], "pages": s["pages"], "chapter": c["n"], "in_b1": c["in_b1"]}
                for c in manual for s in c["sections"]}
    seen, pool = set(), []
    for q in qs:
        sig = q["text"] + "|".join(o["text"] for o in q["options"])
        if sig in seen or q["answer_source"] == "todo":  # repeated in the bank / no verified answer
            continue
        seen.add(sig)
        pool.append({**q, "topic": topics.get(q["id"])})
    return pool, sections


def history():
    """Per-question results of past runs: id -> list of bools, oldest first."""
    res = defaultdict(list)
    if HISTORY.exists():
        for line in HISTORY.read_text().splitlines():
            m = ROW_RE.match(line)
            if m:
                res[m.group(1)].append(m.group(3) == "✔")
    return res


def weights(pool, hist):
    sec_ok = defaultdict(list)
    for q in pool:
        sec_ok[q["topic"]] += hist.get(q["id"], [])
    out = []
    for q in pool:
        h = hist.get(q["id"], [])
        w = 1.0
        if h and not h[-1]:
            w *= 4  # failed last time
        elif not h:
            w *= 1.5  # never asked
        s = sec_ok[q["topic"]]
        if s and sum(s) / len(s) < PASS:
            w *= 2  # weak topic
        out.append(w)
    return out


def sample(pool, w, k, rng):
    """Weighted sampling without replacement."""
    keyed = sorted(zip(pool, w), key=lambda x: rng.random() ** (1 / x[1]), reverse=True)
    return [q for q, _ in keyed[:k]]


def slim(q):
    return {k: q[k] for k in ("id", "topic", "eliminatoria", "type", "text", "options", "page")} | {
        "images": [str(CONTENT / i["file"]) for i in q["images"]],
        **({"warning": q["warning"]} if q.get("warning") else {}),
        **({"derived_from": q["derived_from"]} if q.get("derived_from") else {}),
    }


def cmd_pick(a):
    pool, sections = load()
    rng = random.Random(a.seed)
    hist = history()
    coverage = Counter(q["topic"] for q in pool)
    if a.mode == "simulacro":
        pool = [q for q in pool if not (a.no_images and q["images"])]
        elim = [q for q in pool if q["eliminatoria"]]
        rest = [q for q in pool if not q["eliminatoria"]]
        n_gen = a.generated if a.generated is not None else 4
        picked = sample(elim, weights(elim, hist), EXAM_ELIM, rng) + sample(rest, weights(rest, hist), EXAM_SIZE - EXAM_ELIM - n_gen, rng)
        targets = [s for s, v in sections.items() if v["in_b1"] and not s.endswith(".0")]
    else:
        wanted = set(a.sections.split(",")) if a.sections else None
        cand = [q for q in pool if not (a.no_images and q["images"]) and (not wanted or q["topic"] in wanted or (q["topic"] or "").split(".")[0] in wanted)]
        n_gen = a.generated if a.generated is not None else max(1, a.n // 5)
        picked = sample(cand, weights(cand, hist), a.n - n_gen, rng)
        targets = [s for s in sections if not wanted or s in wanted or s.split(".")[0] in wanted]
    rng.shuffle(picked)
    # Generated questions go to the thinnest-covered target sections first.
    targets = sorted((s for s in targets if not s.endswith(".0")), key=lambda s: (coverage[s], rng.random()))
    gen = [{"section": s, "title": sections[s]["title"], "pages": sections[s]["pages"], "bank_questions": coverage[s]}
           for s in (targets * n_gen)[:n_gen]]
    json.dump({"mode": a.mode, "questions": [slim(q) for q in picked], "generate": gen,
               "pass_mark": PASS, "eliminatorias": sum(q["eliminatoria"] for q in picked)},
              sys.stdout, ensure_ascii=False, indent=1)


def cmd_sections(_):
    pool, sections = load()
    hist = history()
    coverage = Counter(q["topic"] for q in pool)
    for s, v in sections.items():
        res = [r for q in pool if q["topic"] == s for r in hist.get(q["id"], [])]
        acc = f"{100 * sum(res) / len(res):.0f}% de {len(res)}" if res else "-"
        print(f"{s}\t{v['title']}\tB1={'sí' if v['in_b1'] else 'no'}\tbanco={coverage[s]}{' (poco)' if coverage[s] < THIN else ''}\taciertos={acc}")


def cmd_record(_):
    run = json.load(sys.stdin)
    rs = run["results"]
    ok = sum(r["ok"] for r in rs)
    failed_elim = [r for r in rs if r.get("eliminatoria") and not r["ok"]]
    passed = ok / len(rs) >= PASS and not failed_elim
    by_topic = defaultdict(lambda: [0, 0])
    for r in rs:
        by_topic[r["section"]][0] += r["ok"]
        by_topic[r["section"]][1] += 1
    lines = [
        f"\n## {datetime.datetime.now():%Y-%m-%d %H:%M} — {run['mode']}", "",
        f"Resultado: {ok}/{len(rs)} ({100 * ok / len(rs):.0f}%)"
        + (f" — {'APROBADO' if passed else 'DESAPROBADO'}" if run["mode"] == "simulacro" else ""),
        f"Eliminatorias falladas: {', '.join(r['id'] for r in failed_elim) or 'ninguna'}", "",
        "| pregunta | sección | ok | origen |", "|---|---|---|---|",
        *[f"| {r['id']} | {r['section']} | {'✔' if r['ok'] else '✘'} | {'generada' if r.get('generated') else 'banco'} |" for r in rs], "",
        "Por tema: " + "; ".join(f"{s} {a}/{b}" for s, (a, b) in sorted(by_topic.items())),
    ]
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY.exists():
        HISTORY.write_text("# Historial de cuestionarios\n\nLo escribe `scripts/quiz.py record`. Las filas pesan la próxima selección.\n")
    with HISTORY.open("a") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def cmd_export(_):
    """History as one pasteable line: last results per question, zlib + base64."""
    h = {k: "".join("1" if r else "0" for r in v[-KEEP:]) for k, v in history().items()}
    print(BLOCK_PREFIX + base64.b64encode(zlib.compress(json.dumps(h, separators=(",", ":")).encode(), 9)).decode())


def cmd_import(a):
    block = a.block.strip()
    if not block.startswith(BLOCK_PREFIX):
        sys.exit(f"not a progress block (expected {BLOCK_PREFIX}...)")
    h = json.loads(zlib.decompress(base64.b64decode(block[len(BLOCK_PREFIX):])))
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    rows = [f"| {qid} | - | {'✔' if r == '1' else '✘'} | importado |" for qid, rs in h.items() for r in rs]
    with HISTORY.open("a") as f:
        f.write("\n## Progreso importado\n\n| pregunta | sección | ok | origen |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print(f"{len(h)} preguntas con historial importadas ({len(rows)} respuestas).")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("pick")
    pk.add_argument("--mode", choices=["simulacro", "temas"], required=True)
    pk.add_argument("--sections", help="comma-separated section or chapter ids, e.g. 6.3,6.8 or 4")
    pk.add_argument("--n", type=int, default=20)
    pk.add_argument("--generated", type=int, help="how many generated questions to request")
    pk.add_argument("--seed", type=int)
    pk.add_argument("--no-images", action="store_true", help="skip questions that need a photo")
    pk.set_defaults(fn=cmd_pick)
    sub.add_parser("sections").set_defaults(fn=cmd_sections)
    sub.add_parser("record").set_defaults(fn=cmd_record)
    sub.add_parser("export").set_defaults(fn=cmd_export)
    im = sub.add_parser("import")
    im.add_argument("block")
    im.set_defaults(fn=cmd_import)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
