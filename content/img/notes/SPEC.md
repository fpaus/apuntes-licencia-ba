# Note illustrations spec

Each study note in `content/notes.json` gets an original illustration that replaces the user's photo (the photos are third-party ads and cannot be published). The app shows it as an `<img>` thumbnail (140 px wide) that opens full-screen on tap, on light and dark pages.

## Format

- One hand-written SVG per note: `content/img/notes/<slug>.svg`, `viewBox="0 0 600 450"`, no `width`/`height` attributes, no external references, no scripts, no raster images.
- First element: a full-size background `<rect>` with `fill="#ffffff"` and `rx="24"` — the page theme cannot reach inside an `<img>`, so the drawing carries its own background.
- Palette, nothing else: ink `#1d2420`, muted `#5d6a62`, line `#d9e0d9`, green `#2f8a4f`, green-soft `#e2f1e6`, red `#c0392b`, red-soft `#fbe7e4`, amber `#c98a00`, road `#4a4f4c`, road-line white `#ffffff`, road-line yellow `#f2c200`.
- Text: `font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif"`, Spanish (Rioplatense), a title at top in ink, 26–30 px bold; labels ≥ 16 px. At most ~25 words of text per drawing: the note's facts list carries the detail, the drawing shows the idea.
- Flat, schematic, diagram style: simple shapes, top-down or side views, clear arrows. No brand names, logos, people's faces, phone numbers.

## Content

Draw only what the note's `facts` (in `content/notes.json`) say — read the note before drawing. The drawing illustrates the main idea; it does not have to show every fact.

## Done when

The file parses as XML (`python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" <file>`), you have rendered it to PNG and looked at it (e.g. `rsvg-convert` or `uv run --with cairosvg python -c "import cairosvg; cairosvg.svg2png(url='<in>', write_to='<out>.png')"`, then Read the PNG), nothing overlaps or is clipped, and text is legible at 140 px wide for the title and at full size for labels.
