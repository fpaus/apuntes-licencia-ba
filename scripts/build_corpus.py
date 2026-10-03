# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Build content/ from Docs/. Run: uv run scripts/build_corpus.py"""
import hashlib
import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "Docs"
OUT = ROOT / "content"
QPDF = DOCS / "cuestionario.pdf"
MPDF = DOCS / "manual_del_conductor_251003_184543.pdf"

# Colours used by the questionnaire PDF.
GREEN, RED, BODY, GREY = 0x90C852, 0xEE302E, 0x231F20, 0x6D6E71
NOISE = {0x676A6B, 0xFFFFFF, 0x757A7B}  # page header / footer

OPT_RE = re.compile(r"^\.?(?:•|([A-Ha-h])\s*(?:[\)\.\-–]|\s[–-]))\s*")
NUM_RE = re.compile(r"^(\d{1,3})\s*[\)\.]\s*")
HEAD_RE = re.compile(r"^(?:\d{1,2}\)\s*)?P\w*guntas para (?:todas las clases|la clase de|clase de)[\s.:]*|^\d{1,2}\)$", re.I)
VF_RE =re.compile(r"^V\s+F$")
ELIM_RE = re.compile(r"\(?\s*Pregunta\s+de\s+car[aá]cter\s+eliminatorio\s*\)?|\s*\(\s*Pregunta(\s+de(\s+car[aá]cter)?)?\s*$|^(de\s+)?car[aá]cter eliminatorio\)|^eliminatorio\)", re.I)


def q_lines(doc):
    """Yield (page, kind, text, color, bold, spans) per visible line; kind 'img' for images."""
    for pn, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            if b["type"] == 1:
                x0, y0, x1, y1 = b["bbox"]
                if y0 > 90 and (x1 - x0) > 20:  # skip header logo
                    yield pn, "img", b["bbox"], None, False, None
                continue
            for l in b.get("lines", []):
                sp = [s for s in l["spans"] if s["text"].strip()]
                if not sp:
                    continue
                c = sp[0]["color"]
                if any(s["color"] == GREEN and re.search(r"\w", s["text"]) for s in sp):
                    c = GREEN  # partly green line: the answer text is green, the bullet may not be
                t = "".join(s["text"] for s in l["spans"]).strip()
                if re.match(r"^[A-Ha-h]\t", t):  # option letter followed only by a tab
                    t = f"{t[0]}. {t[2:]}"
                if c in NOISE or (c == 0 and ("IF-2019" in t or t.startswith("página"))):
                    continue
                yield pn, "txt", re.sub(r"\s+", " ", t), c, "Bold" in sp[0]["font"], sp


def parse_questions(doc):
    qs, section, cur, prev_heading, klass, bullet, elim = [], None, None, False, "todas", "", False

    def close():
        nonlocal cur
        if cur:
            qs.append(cur)
        cur = None

    def new_q(pn, text):
        close()
        num = NUM_RE.match(text)
        return {
            "page": pn, "section": section, "class": klass, "number": int(num.group(1)) if num else None,
            "text": NUM_RE.sub("", text) if num else text, "options": [], "images": [], "eliminatoria": False,
        }

    for pn, kind, text, color, bold, spans in q_lines(doc):
        if elim and cur:  # the tag belongs to the question the tagged line ended in
            cur["eliminatoria"], elim = True, False
        if pn == 1:
            continue
        if kind == "img":
            if cur:
                cur["images"].append({"page": pn, "bbox": [round(v, 1) for v in text]})
            continue
        if text == "•":  # bullet split from its option text
            bullet = "• "
            continue
        text, bullet = bullet + text, ""
        if ELIM_RE.search(text):
            elim = True
            text = ELIM_RE.sub("", text).strip(" :")
            if not text:
                continue
        if VF_RE.match(text) and cur:
            for s in spans:
                for ch in s["text"]:
                    if ch in "VF":
                        cur["options"].append({"text": "Verdadero" if ch == "V" else "Falso", "correct": s["color"] == GREEN})
            continue
        is_opt = bool(OPT_RE.match(text))
        if (bold and not is_opt and color in (GREY, GREEN)) or (color == GREY and HEAD_RE.match(text)):
            # Section heading; a lower-case start continues the previous heading line.
            close()
            text = re.sub(r"^\d{1,2}\)\s*", "", HEAD_RE.sub("", text)).strip(" :.")
            if not text:
                continue
            section = f"{section} {text}" if prev_heading and text[0].islower() else text
            if "Auto y Camioneta" in text:
                klass = "auto_camioneta"
            elif pn >= 178:
                klass = None  # trucks, motos, professional classes
            prev_heading = True
            continue
        prev_heading = False
        if is_opt and cur:
            cur["options"].append({"text": OPT_RE.sub("", text), "correct": color == GREEN})
            continue
        if cur and cur["options"]:
            last = cur["options"][-1]
            # Wrapped option text starts lower-case or with punctuation.
            if not NUM_RE.match(text) and (text[0].islower() or text[0] in ",;.)"):
                last["text"] += " " + text
                last["correct"] |= color == GREEN
                continue
            cur = new_q(pn, text)
            continue
        if cur and not cur["options"] and not NUM_RE.match(text):
            cur["text"] += " " + text  # wrapped question text
            continue
        cur = new_q(pn, text)
    if elim and cur:
        cur["eliminatoria"] = True
    close()
    return qs


def finish_questions(qs):
    out, seen = [], set()
    for i, q in enumerate(qs, 1):
        q["text"] = re.sub(r"(\w)- (\w)", r"\1\2", q["text"]).strip()
        opts = []
        for o in q["options"]:
            o["text"] = re.sub(r"(\w)- (\w)", r"\1\2", o["text"]).strip()
            nxt = chr(ord("A") + len(opts) + 1)  # an inline "C. ..." means two options share one line
            head, sep, tail = o["text"].partition(f" {nxt}. ")
            if sep:
                opts += [{"text": head, "correct": o["correct"]}, {"text": tail, "correct": False}]
                continue
            dup = next((x for x in opts if x["text"] == o["text"]), None)
            if dup:  # the PDF repeats some options verbatim
                dup["correct"] |= o["correct"]
                continue
            opts.append(o)
        q["options"] = opts
        n_ok = sum(o["correct"] for o in q["options"])
        # Stable across re-parses: page + text hash (later tools key per-question data by this id).
        base = f"p{q['page']:03d}-{hashlib.sha1(q['text'].encode()).hexdigest()[:6]}"
        q["id"] = base if base not in seen else f"{base}-{sum(k.startswith(base) for k in seen) + 1}"
        seen.add(q["id"])
        q["type"] = ("vf" if {o["text"].rstrip(".") for o in q["options"]} <= {"Verdadero", "Falso"}
                     else "multi" if n_ok > 1 else "single")
        q["answer_source"] = "marked" if n_ok else "unmarked"
        q["source"] = {"file": QPDF.name, "page": q["page"]}
        q["chapters"] = bank_chapters(q["section"] or "")
        out.append(q)
    return out


# Bank section -> manual chapter(s). Coarse: per-question topics come later. "varias" mixes everything.
BANK_CHAPTERS = {
    "actores en la via publica": [1, 4], "USUARIOS DE BICICLETA": [1], "Seguridad": [7], "Documentación": [1, 6],
    "intoxicación": [5], "varias": [], "Semáforo": [3], "Velocidades": [4], "Adelantamiento": [6], "Autopistas": [6],
    "Traccion a Sangre": [1], "Estacionamiento": [6], "Luces": [4], "Giros y rotondas": [6], "SEÑALES DE TRANSITO": [3],
    "Conducción segura": [4], "Seguridad Activa y Pasiva": [7], "Auto y Camioneta": [7],
}


def bank_chapters(section):
    return next((v for k, v in BANK_CHAPTERS.items() if section == k or section.endswith(k) or section.startswith(k)), None)


def apply_overrides(qs):
    """Apply content/answer_overrides.json (hand-written): answers for unmarked questions,
    fixes for wrongly marked ones ("fix": true), and warnings shown next to the official answer."""
    overrides = json.loads((OUT / "answer_overrides.json").read_text())
    used = set()
    for q in qs:
        key = next((k for k in overrides if k[0] != "_" and k == f"{q['page']}|{q['text'][:len(k.split('|', 1)[1])]}"), None)
        if not key:
            continue
        o = overrides[key]
        if q["answer_source"] != "unmarked" and not (o.get("fix") or "warning" in o):
            continue
        used.add(key)
        if "warning" in o:
            q["warning"] = o["warning"]
        if "todo" in o:
            q["answer_source"], q["todo"] = "todo", f"TODO: verify — {o['todo']}"
        if "correct" not in o:
            continue
        for i, opt in enumerate(q["options"]):
            opt["correct"] = i in o["correct"]
        q["answer_source"] = "fixed" if o.get("fix") else "derived"
        q["derived_from"] = {"file": MPDF.name, "page": o["page"], "note": o["note"]}
        q["type"] = "multi" if len(o["correct"]) > 1 else "single" if q["type"] == "multi" else q["type"]
    unused = [k for k in overrides if k[0] != "_" and k not in used]
    assert not unused, f"overrides matched no question: {unused}"


def extract_question_images(doc, qs):
    img_dir = OUT / "img" / "q"
    img_dir.mkdir(parents=True, exist_ok=True)
    for q in qs:
        for k, im in enumerate(q["images"]):
            path = img_dir / f"{q['id']}-{k}.jpg"
            pix = doc[im["page"] - 1].get_pixmap(clip=pymupdf.Rect(im["bbox"]), dpi=110)
            pix.save(path, jpg_quality=80)
            im["file"] = str(path.relative_to(OUT))


CHAPTERS = {  # from the manual's index (page 2); chapters 8-9 are outside class B1
    1: "El conductor", 2: "La vía pública", 3: "Señalamiento vial", 4: "Conducir con seguridad",
    5: "Salud para conducir", 6: "Las reglas de su seguridad", 7: "Funcionamiento del vehículo",
    8: "Funcionamiento de la motocicleta", 9: "Funcionamiento de triciclos y cuatriciclos",
    10: "Las infracciones de tránsito",
}
CHAPTER_COVERS = dict(zip((3, 25, 39, 52, 77, 89, 111, 129, 161, 165), range(1, 11)))  # cover page -> chapter
SECTION_TITLE_FALLBACK = {"6.10": "Estacionamiento"}  # banner has no title text; taken from the page 107-109 content
SEC_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\s*(.*)$")


def parse_manual(doc):
    """Split the manual into chapters > sections > blocks, each block tagged with its page."""
    chapters = {n: {"n": n, "title": t, "in_b1": n not in (8, 9), "sections": []} for n, t in CHAPTERS.items()}
    sec = None
    img_dir = OUT / "img" / "manual"
    img_dir.mkdir(parents=True, exist_ok=True)
    for pn, page in enumerate(doc, 1):
        page.get_pixmap(dpi=90).save(img_dir / f"p{pn:03d}.jpg", jpg_quality=75)
        if pn < 3 or pn >= 180:  # cover, index, alphabetical index
            continue
        if pn in CHAPTER_COVERS:  # text before the first numbered section goes to an intro section
            n = CHAPTER_COVERS[pn]
            sec = {"id": f"{n}.0", "title": "Introducción", "pages": [pn, pn], "blocks": [], "images": []}
            chapters[n]["sections"].append(sec)
        k = 0
        for b in page.get_text("dict", sort=True)["blocks"]:  # sorted: section banners come last in stream order
            if b["type"] == 1:
                x0, y0, x1, y1 = b["bbox"]
                if sec and y0 > 90 and (x1 - x0) > 40 and (y1 - y0) > 40:
                    path = img_dir / f"p{pn:03d}-{k}.jpg"
                    page.get_pixmap(clip=pymupdf.Rect(b["bbox"]), dpi=130).save(path, jpg_quality=80)
                    sec["images"].append({"file": str(path.relative_to(OUT)), "page": pn})
                    k += 1
                continue
            for l in b.get("lines", []):
                sp = [s for s in l["spans"] if s["text"].strip()]
                if not sp:
                    continue
                s0 = sp[0]
                t = re.sub(r"\s+", " ", " ".join(s["text"].strip() for s in sp)).strip()
                if s0["color"] == GREY or (s0["color"] == 0 and ("IF-2019" in t or t.startswith("página"))) or t == "MANUAL DEL CONDUCTOR":
                    continue
                bold, size, white = "Bold" in s0["font"], round(s0["size"]), s0["color"] == 0xFFFFFF
                if white and (t.isdigit() or t.startswith("CAPITULO")):
                    continue  # page number, chapter cover title
                m = SEC_RE.match(t) if white and bold and size >= 20 else None
                if m and int(m.group(1)) in chapters:
                    sec = {"id": f"{m.group(1)}.{m.group(2)}", "title": m.group(3).strip(), "pages": [pn, pn], "blocks": [], "images": []}
                    chapters[int(m.group(1))]["sections"].append(sec)
                    continue
                if not sec:
                    continue
                sec["pages"][1] = pn
                kind = "h" if bold and size >= 14 and not t.isdigit() and len(t) > 2 else "callout" if white else "small" if size <= 10 else "p"
                last = sec["blocks"][-1] if sec["blocks"] else None
                if last and last["kind"] == kind and last["page"] == pn and kind != "h":
                    last["text"] += " " + t  # join wrapped lines; paragraphs are not reconstructed
                else:
                    sec["blocks"].append({"kind": kind, "text": t, "page": pn})
    for c in chapters.values():
        c["sections"] = [x for x in c["sections"] if x["blocks"]]
        for x in c["sections"]:
            x["title"] = x["title"].capitalize() if x["title"] else SECTION_TITLE_FALLBACK.get(x["id"], "TODO: verify")
        c["pages"] = [c["sections"][0]["pages"][0], c["sections"][-1]["pages"][1]]
    return list(chapters.values())


def main():
    OUT.mkdir(exist_ok=True)
    qdoc = pymupdf.open(QPDF)
    qs = finish_questions(parse_questions(qdoc))
    skipped = [q for q in qs if q["class"] and not q["options"]]  # fill-in tables, stray sub-headings
    in_scope = [q for q in qs if q["class"] and q["options"]]
    apply_overrides(in_scope)
    extract_question_images(qdoc, in_scope)
    (OUT / "questions.json").write_text(json.dumps(in_scope, ensure_ascii=False, indent=1))
    print(f"questions parsed: {len(qs)}, in scope: {len(in_scope)}")

    chapters = parse_manual(pymupdf.open(MPDF))
    (OUT / "manual.json").write_text(json.dumps(chapters, ensure_ascii=False, indent=1))
    print(f"manual: {sum(len(c['sections']) for c in chapters)} sections")

    notes = json.loads((OUT / "notes.json").read_text())
    write_report(qs, in_scope, skipped, chapters, notes)


def write_report(all_qs, qs, skipped, chapters, notes):
    from collections import Counter

    def table(counter, head):
        return [f"| {head} | n |", "|---|---|"] + [f"| {k} | {v} |" for k, v in counter.most_common()]

    photos = {p.name for p in DOCS.glob("*.jpeg")}
    noted = {n["file"] for n in notes}
    pending = sorted(photos - noted)  # new photos: transcribe them into content/notes.json
    multi = [q for q in qs if q["type"] == "multi"]
    lines = [
        "# Parse report", "", "Generated by `scripts/build_corpus.py`. Do not edit.", "",
        "## Question bank (`cuestionario.pdf`)", "",
        f"- Questions parsed (all classes): {len(all_qs)}",
        f"- In scope for B1 (todas las clases + Auto y Camioneta): {len(qs)}",
        f"- Out of scope (trucks, motos, professional): {sum(1 for q in all_qs if not q['class'])}",
        f"- Skipped, no options (fill-in table or stray heading): {len(skipped)} — "
        + "; ".join(f"p. {q['page']} '{q['text'][:60]}'" for q in skipped),
        f"- Eliminatorias: {sum(q['eliminatoria'] for q in qs)}",
        f"- With photo: {sum(bool(q['images']) for q in qs)} ({sum(len(q['images']) for q in qs)} images)", "",
        *table(Counter(q["answer_source"] for q in qs), "answer_source"), "",
        *table(Counter(q["type"] for q in qs), "type"), "",
        *table(Counter(f"{q['class']} · {q['section']}" for q in qs), "class · section"), "",
        "### Multi-answer questions (check against the PDF)", "",
        *[f"- {q['id']} p. {q['page']}: {q['text'][:90]} ({sum(o['correct'] for o in q['options'])}/{len(q['options'])} correct)" for q in multi], "",
        "### Answers still open (TODO: verify)", "",
        *[f"- {q['id']} p. {q['page']}: {q['text'][:90]} — {q['todo']}" for q in qs if q["answer_source"] == "todo"], "",
        "## Manual (`manual_del_conductor_*.pdf`)", "",
        "| Ch. | Title | Pages | Sections | B1 | Bank questions* |", "|---|---|---|---|---|---|",
        *[f"| {c['n']} | {c['title']} | {c['pages'][0]}–{c['pages'][1]} | {len(c['sections'])} | {'yes' if c['in_b1'] else 'no'} | "
          f"{sum(1 for q in qs if c['n'] in q['chapters'])} |" for c in chapters], "",
        "\\* Coarse count by bank section. The 78 'varias' questions are not assigned yet; several belong to "
        "chapters 2 and 10, so a 0 here is not a coverage gap.", "",
        f"Section images extracted: {sum(len(s['images']) for c in chapters for s in c['sections'])}. "
        f"Page renders: content/img/manual/pNNN.jpg.", "",
        "## Photos (`WhatsApp Image *.jpeg`)", "",
        f"- {len(photos) - len(pending)} of {len(photos)} photos mapped.",
        *[f"- pending (no note yet): {p}" for p in pending], "",
        *table(Counter(n["status"] for n in notes), "status"), "",
    ]
    lines += ["## Lessons and question topics (hand-written)", "", *check_lessons(chapters, qs)]
    (OUT / "REPORT.md").write_text("\n".join(lines))


def check_lessons(chapters, qs):
    """Problems in content/lessons/*.json and content/question_topics.json, as report lines."""
    out, ids = [], {s["id"] for c in chapters for s in c["sections"]}
    for c in chapters:
        f = OUT / "lessons" / f"ch{c['n']:02d}.json"
        if not f.exists():
            out.append(f"- ch{c['n']:02d}: missing")
            continue
        lessons = {l["id"]: l for l in json.loads(f.read_text())["lessons"]}
        missing = [s["id"] for s in c["sections"] if s["id"] not in lessons]
        cards = [card for l in lessons.values() for card in l["cards"]]
        bad = [f"{l['id']}: '{card['title']}' ({p})" for l in lessons.values() for card in l["cards"]
               for p in [None if "page" in card else "no page", card.get("image") and not (OUT / card["image"]).exists() and "image not found"] if p]
        todo = sum("TODO" in json.dumps(card, ensure_ascii=False) for card in cards)
        out.append(f"- ch{c['n']:02d}: {len(lessons)} lessons, {len(cards)} cards"
                   + (f"; sections without lesson: {missing}" if missing else "") + (f"; TODO: {todo}" if todo else ""))
        out += [f"  - {b}" for b in bad]
    tf = OUT / "question_topics.json"
    topics = json.loads(tf.read_text()) if tf.exists() else {}
    unmapped = [q["id"] for q in qs if q["id"] not in topics]
    unknown = sorted({v for v in topics.values() if v and v not in ids})
    out.append(f"- question_topics.json: {len(qs) - len(unmapped)}/{len(qs)} questions mapped"
               + (f"; unknown sections: {unknown}" if unknown else ""))
    return out


if __name__ == "__main__":
    main()
