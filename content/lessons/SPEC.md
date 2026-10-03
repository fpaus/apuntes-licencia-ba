# Lesson file spec

One file per chapter: `content/lessons/chNN.json` (NN = 01…10). The study app renders it as a course: one **card** per screen.

## Sources

- `content/manual.json` — the manual's text by chapter > section > block, each block with its page. This is the **source of truth**.
- `content/img/manual/pNNN.jpg` — a render of every manual page. The text layer scrambles **tables, diagrams and sign charts**: read those from the page render (open the image), never from `manual.json` text.
- `content/img/manual/pNNN-K.jpg` — raster images cut from the page, listed per section under `images` in `manual.json`.

## Schema

```json
{
  "chapter": 4,
  "lessons": [
    {
      "id": "4.3",
      "title": "La velocidad potencia el riesgo",
      "summary": "Una oración: qué vas a aprender.",
      "cards": [
        {
          "title": "Límites en zona urbana",
          "body": "Párrafo corto con **negrita**.\n\n- viñeta\n- viñeta",
          "page": 57,
          "table": {"head": ["Lugar", "Máxima", "Mínima"], "rows": [["Calles", "40 km/h", "20 km/h"]]},
          "image": "img/manual/p057.jpg",
          "callout": "Dato clave para memorizar."
        }
      ]
    }
  ]
}
```

- `id`: the section id from `manual.json`, one lesson per section, in manual order. Include the `N.0` intro sections.
- `body`: plain text. Allowed markup: `**bold**`, lines starting `- ` (bullets), blank line between paragraphs. 60 words maximum.
- `page`: required — the manual page the card's facts come from.
- `table`, `image`, `callout`: optional. `image` is a path relative to `content/` and must exist. Prefer a cut image (`pNNN-K.jpg`); use the full page render only for a chart that has no cut image.

## Writing rules

- Rioplatense Spanish, addressed to the learner with *vos* ("respetá", "tenés"). Plain language: short sentences, active voice.
- **One idea per card.** 2–8 cards per lesson; an intro section gets 1–2.
- Every fact comes from the cited page. Leave out anything the manual does not say. When a page is unreadable or ambiguous, write `TODO: verify (p. N)` in the body rather than filling the gap.
- Put every **key number** (speeds, distances, times, ages, alcohol limits, deadlines, fines) in a `table` or a `callout` — the exam asks about them.
- Prefer what the theory exam tests (rules, limits, priorities, obligations, sign meanings) over history and exposition; compress exposition to one card or drop it.

## Done when

Every section of the chapter in `manual.json` has a lesson; every card has a `page`; every `image` path exists; the file parses as JSON (`python3 -m json.tool content/lessons/chNN.json`).
