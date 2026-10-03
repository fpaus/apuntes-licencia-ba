# Driving-license study app + quiz skill

## Context

I am learning to drive. I will take a driving course and then the theory exam for a
driving license in the Provincia de Buenos Aires, Argentina. My study material sits in
`Docs/`, scattered across formats. I want one place to study it, and a way to test
myself afterwards.

Target license class: **B1 (auto particular)**. Include the questions "para todas las
clases" and those for "Auto y Camioneta". Exclude the questions for motos and
professional classes.

Write all user-facing text (app UI, content, quiz questions) in Rioplatense Spanish.
Write code, identifiers and comments in English.

## Sources in `Docs/`

- `manual_del_conductor_251003_184543.pdf` — official driver manual, 185 pages,
  10 chapters, text layer extractable with `pdftotext`. It contains many signs and
  diagrams as images. This is the **source of truth**.
- `cuestionario.pdf` — official exam question bank, 229 pages, extractable text.
  Question formats: true/false, A/B/C, a/b/c/d, and multi-select ("Indique cuáles…").
  Some carry the tag "(Pregunta de carácter eliminatorio)". Sections are split by
  license class ("para todas las clases", "Auto y Camioneta", "motos", professional).
  **The correct option is printed in green text.** `pdftotext` drops colour, so read
  the span colour with PyMuPDF (`page.get_text("dict")`). Spot-check the later
  numbered section (`72) … a) b) c)`) by rendering pages: it may lack the green
  marking. About 100 questions include a photo (a road scene, a sign) that the
  question refers to.
- `WhatsApp Image *.jpeg` (13 files) — phone screenshots of study notes: speed limits,
  road lines, braking time, and similar. No OCR tool is installed. Read each image
  visually.

## Phase 1 — Build the corpus

Extract every source into a structured corpus: topics and a question bank, as JSON or
Markdown under `content/`. Every fact and every question cites its source
(file + page, or image filename).

- Group content by the manual's chapters. Place every photo note under the topic it
  belongs to.
- When a photo note disagrees with the manual, keep the manual's version and list the
  conflict in `content/CONFLICTS.md`.
- For each bank question, record its section and class, its options, and the correct
  answer(s). The schema allows more than one correct option. Record how you
  established the answer: `marked` (green text in the PDF) or `derived` (inferred
  from a cited manual page). Record `eliminatoria: true` where the tag appears.
- Extract each question's photo and link it to that question.
- Extract the sign and diagram images the content needs from the manual
  (`pdfimages` or page crops).

Done when: all 10 chapters and all 13 photos map to topics; every bank question is
parsed, with an answer and its provenance; and a parse report gives the counts.

**Stop here.** Show me the topic outline, the parse report, the conflicts, and your
proposed app architecture. Wait for my approval before Phase 2.

## Phase 2 — Study app

Build a local app that turns the corpus into an ordered, interactive and easy-to-digest
course.

- Run it locally with one command, documented in `README.md`. Keep it simple: a static
  site that reads `content/` is enough, and needs no backend.
- Follow the manual's chapter order, in short lessons: one idea per screen, visuals
  first, and key numbers (speeds, distances, times) in tables or cards.
- Add these interactive pieces: a sign gallery with flip cards (image → meaning),
  per-lesson "check yourself" questions from the bank, search across all content,
  and progress tracking that persists in `localStorage`.
- Every lesson links to its source page, so I can check the original.

Done when: every topic in the corpus is reachable from the app's navigation; every
image renders; the run command works on a clean checkout; and the app works at phone
width.

## Phase 3 — Quiz skill

Create a Claude Code skill at `.claude/skills/quiz-licencia/SKILL.md`. I invoke it after
the course to practise for the exam. Load the `writing-for-agents` skill before you
write it.

- It reads the Phase 1 question bank. The bank stays the single source of truth for
  questions and answers.
- It adds **generated** questions in the same style as the bank. Each one comes from a
  specific manual page and is tagged `generada`, with its citation. It targets topics
  the bank covers thinly.
- Flow: ask me for the topic(s) and the number of questions (default 20), or offer
  "simulacro de examen" (mixed topics, eliminatoria questions included). Present one
  question at a time with `AskUserQuestion` (options as choices), and wait for my
  answer. For a question with a photo, open the image with `xdg-open` before asking. After each answer, give right/wrong, the
  correct answer, and a one-line reason with its manual citation.
- At the end, show the score by topic. Flag any failed eliminatoria question.
  Append the results to `progress/quiz-history.md`, so later runs weight my weak topics
  more heavily.

Done when: one full simulacro runs end to end; generated questions carry citations; and
the history file updates.

## Ground rules

- Take every fact from the sources. When a source is unreadable or ambiguous, write
  `TODO: verify` with the location. Leave the gap marked rather than filled from
  general knowledge.
- Put the Phase 1 parser in a script, so I can re-run it if I add documents to `Docs/`.
