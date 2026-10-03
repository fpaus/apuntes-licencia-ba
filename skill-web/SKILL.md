---
name: quiz-licencia
description: Exam-practice quiz for the Provincia de Buenos Aires B1 driving-licence theory test (licencia de conducir, examen teórico, simulacro), built from the official question bank and the Manual del Conductor. Use when the user asks to practise or be quizzed for the licence exam, asks for a simulacro, or pastes a progress block starting with "LIC1:".
---

Run an exam-practice quiz for the learner, in Rioplatense Spanish (*vos*). Every answer you explain carries a **cite**: a manual page that states it.

This folder holds the data and a picker: `content/questions.json` (bank), `content/manual.json` (manual text by section), `content/question_topics.json`, `content/img/q/` (question photos) and `scripts/quiz.py`. The folder is read-only: run every `quiz.py` command with `QUIZ_HISTORY=/tmp/quiz-history.md`, and keep generated questions in `/tmp/generated-questions.json`. Below, `quiz` means `QUIZ_HISTORY=/tmp/quiz-history.md python3 <this folder>/scripts/quiz.py`.

## 1. Restore progress

The chat starts with no history. If the user's message contains a block starting with `LIC1:`, run `quiz import "<block>"`, then tell them how many questions it restored. Otherwise, mention once that they can paste the progress block from a previous chat.

Done when the block, if any, is imported.

## 2. Choose the mode

Ask the learner (they answer by typing):

- **Simulacro de examen** — 40 preguntas, 5 eliminatorias, aprobás con 75 % y todas las eliminatorias bien (formato del manual, p. 20).
- **Por temas** — then ask which topics and how many questions (default 20). `quiz sections` lists section ids with bank coverage and past accuracy; offer chapters or the weakest sections.

Done when you hold a mode, and for *por temas* a section/chapter list and a count.

## 3. Build the set

Run `quiz pick --mode simulacro` or `quiz pick --mode temas --sections <ids> --n <count>`. It returns JSON: `questions` (weighted toward past mistakes and weak topics) and `generate` (sections that need a **generated** question).

For each `generate` entry, write one generated question:

- Read that section's blocks in `content/manual.json` and pick one rule or number the exam would test.
- Match the bank's style: options A/B/C with exactly one correct, or Verdadero/Falso. Wrong options are plausible confusions (a neighbouring number, the rule's exception).
- Every fact comes from one manual page. Record it as `{"id": "g-<n>", "section", "text", "options": [{"text", "correct"}], "cite": {"page", "quote"}}`, `quote` copied from `manual.json`, `n` the next free number in `/tmp/generated-questions.json`.

Mix the generated questions in at random positions. Done when the set has the requested size and every generated question has a `cite` with a `quote`.

## 4. Ask, one question at a time

For each question:

1. Show `Pregunta N de M`, the topic, and a **ELIMINATORIA** mark when `eliminatoria` is true; generated ones show `(generada)`.
2. If it has `images`, show each image to the learner in the chat before asking. Look at it yourself too, so your reason can describe it. If you cannot show images in this chat, rebuild the set with `--no-images` added to the same `pick` command and continue from question 1.
3. Write the options lettered A, B, C, D in their original order. For `type: multi`, say they may pick several. Wait for the typed answer.
4. Reply in this shape, every time:
   - First line: **✔ Correcto** or **✘ Incorrecto**, then the correct option (letter and text).
   - Then the reason: one or two lines, ending with its **cite** (`Manual, p. N`). For a bank question, find the supporting sentence in the manual section named by `topic`; use `derived_from` when present; when the manual does not cover it, say so and cite `Cuestionario oficial, p. N`. Show `warning` when present. A generated question uses its `cite`.
5. Keep a running record: `{id, section, ok, eliminatoria, generated}`.

Done when every question has an answer and a cited reason.

## 5. Close the run

1. Pipe the record to `quiz record` as `{"mode": "<mode>", "results": [...]}`. It prints the score, the score by topic and the failed eliminatorias.
2. Show that summary. For a simulacro, state APROBADO/DESAPROBADO and list every failed eliminatoria with its correct answer. Name the 2–3 weakest sections to review.
3. Run `quiz export` and give the learner its one-line output in a code block, with: "Guardá este bloque y pegalo al empezar el próximo chat: así sigo con tus temas flojos."

Done when the learner has the summary and the progress block.
