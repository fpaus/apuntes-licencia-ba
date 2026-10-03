---
name: quiz-licencia
description: Cuestionario de práctica para el examen teórico de licencia B1 (Provincia de Buenos Aires), por temas o como simulacro.
disable-model-invocation: true
---

Run an exam-practice quiz for the learner, in Rioplatense Spanish (*vos*). Every answer you explain carries a **cite**: a manual page that states it. The question bank and the manual live in `content/`; `scripts/quiz.py` picks questions and keeps the history.

## 1. Choose the mode

Ask with `AskUserQuestion`:

- **Simulacro de examen** — 40 preguntas, 5 eliminatorias, aprobás con 75 % y todas las eliminatorias bien (formato del manual, p. 20).
- **Por temas** — then ask which topics and how many questions (default 20). Run `python3 scripts/quiz.py sections` to list section ids with their bank coverage and the learner's past accuracy; offer chapters or the weakest sections as options.

Done when you hold a mode, and for *por temas* a section/chapter list and a count.

## 2. Build the set

Run `python3 scripts/quiz.py pick --mode simulacro` or `python3 scripts/quiz.py pick --mode temas --sections <ids> --n <count>`. It returns JSON: `questions` (from the bank, already weighted toward past mistakes and weak topics) and `generate` (sections that need a **generated** question).

For each `generate` entry, write one generated question:

- Read that section's blocks in `content/manual.json` and pick one rule or number the exam would test.
- Match the bank's style: a question with options A/B/C and exactly one correct, or Verdadero/Falso. Wrong options are plausible: the confusions a learner makes (a neighbouring number, the rule's exception).
- Every fact comes from one manual page. Record it as `{"id": "g-<n>", "section", "text", "options": [{"text", "correct"}], "cite": {"page", "quote"}}`, where `quote` is the supporting sentence copied from `manual.json`.
- Append it to `progress/generated-questions.json` (a JSON list; create it if missing). `n` is the next number after the highest `g-<n>` already in that file, so ids never repeat across runs.

Mix the generated questions into the set at random positions. Done when the set has the requested size and every generated question has a `cite` with a `quote`.

## 3. Ask, one question at a time

For each question:

1. Show `Pregunta N de M`, the topic, and a **ELIMINATORIA** mark when `eliminatoria` is true; generated ones show `(generada)`.
2. If it has `images`, show each one in the chat before asking: send it with `SendUserFile` (`display: "render"`). Also open it yourself with `Read`, so your reason can describe what it shows. Where `SendUserFile` is unavailable, print the image path.
3. Ask with `AskUserQuestion`: labels `A`, `B`, `C`, `D` in the original order, each option's text as its `description` (`multiSelect: true` for `type: multi`). A question with more than 4 options: list them lettered in your message and ask for the letters in plain text.
4. Wait for the answer. Then reply in this shape, every time:
   - First line: **✔ Correcto** or **✘ Incorrecto**, then the correct option (letter and text).
   - Then the reason: one or two lines, ending with its **cite** (`Manual, p. N`).
   - Bank question: find the supporting sentence in the manual section named by `topic` (`content/manual.json`). Use `derived_from` when present. When the manual does not cover it, say so and cite the bank page: `Cuestionario oficial, p. N`.
   - `warning` present: show it after the answer.
   - Generated question: use its `cite`.
5. Keep a running record: `{id, section, ok, eliminatoria, generated}`.

Done when every question in the set has an answer and a cited reason.

## 4. Close the run

1. Pipe the record to `python3 scripts/quiz.py record` as `{"mode": "<mode>", "results": [...]}`. It appends to `progress/quiz-history.md` and prints the score, the score by topic, and the failed eliminatorias. The next `pick` reads that file to weight weak topics.
2. Show the learner that summary. For a simulacro, state APROBADO/DESAPROBADO and list every failed eliminatoria with its correct answer.
3. Name the 2–3 weakest sections and the app lesson to review for each: `http://127.0.0.1:8642/app/#/l/<section>/0`.

Done when the history file has the new run and the learner has seen the summary.
