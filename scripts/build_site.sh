#!/usr/bin/env bash
# Assemble the static site for GitHub Pages in _site/: app/ and content/ only, without internal files.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site && mkdir _site
cp -r app content _site/
rm -f _site/content/{REPORT.md,CONFLICTS.md,answer_overrides.json} _site/content/lessons/SPEC.md _site/content/img/notes/SPEC.md
# The app lives in /app/ (it reads ../content/); the site root redirects there.
cat > _site/index.html <<'HTML'
<!doctype html><meta charset="utf-8"><title>Licencia B1</title>
<meta http-equiv="refresh" content="0; url=app/"><a href="app/">Abrir la app</a>
HTML
touch _site/.nojekyll
du -sh _site
