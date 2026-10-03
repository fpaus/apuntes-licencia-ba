# Licencia B1 — app de estudio

App local para estudiar el examen teórico de la licencia de conducir B1 de la Provincia de Buenos Aires. Usa el material de `Docs/`: el Manual del Conductor, el cuestionario oficial y las capturas de apuntes.

## Usar la app

**Online:** https://fpaus.github.io/apuntes-licencia-ba/app/ — se puede instalar en el teléfono y funciona sin internet.

Un solo archivo ejecutable, sin instalar nada. Trae todo el contenido adentro.

- **Windows:** copiá `dist/licencia.exe` a la otra computadora y hacé doble clic. Se abre el navegador en `http://127.0.0.1:8642/app/`. Para salir, cerrá la ventana negra.
- **Linux:** `dist/licencia`

El progreso queda guardado en el navegador de esa computadora.

Notas sobre Windows:
- El `.exe` se compila con Go 1.22, que exige **Windows 10 o posterior**. Para Windows 7 u 8, compilá con Go 1.20.
- Windows no reconoce un `.exe` sin firmar y muestra "Windows protegió tu PC". Tocá **Más información → Ejecutar de todas formas**.

## Instalarla en el teléfono (PWA)

La app es una Progressive Web App: se instala como aplicación y funciona sin internet. El navegador del teléfono exige **HTTPS**, así que hay que publicarla en un hosting estático con HTTPS, por ejemplo Cloudflare Pages, Netlify, GitHub Pages o `tailscale serve`.

1. Publicá las carpetas `app/` y `content/` juntas, sin cambiar la estructura. La app se abre en `https://<tu-sitio>/app/`.
2. En el teléfono, abrí esa dirección:
   - **Android (Chrome):** tocá **Instalar** en la pantalla de inicio de la app, o usá el menú ⋮ → *Instalar aplicación*.
   - **iPhone (Safari):** tocá **Compartir → Agregar a inicio**.
3. Abrí la app instalada, andá a **Ajustes → Descargar todo para usar sin internet** y esperá a que diga "Listo".

Ojo: si el sitio es público, también se publican las capturas de `content/img/notes/`, que muestran nombres y teléfonos de los instructores. Para no publicarlas, borrá esa carpeta del sitio: las lecciones y el banco de preguntas siguen funcionando.

En la PC, Chrome y Edge también ofrecen instalarla desde `http://127.0.0.1:8642/app/`.

Si cambiás los íconos: `uv run scripts/make_icons.py`.

## Generar el ejecutable

Requiere Go 1.22 o posterior.

```bash
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o dist/licencia.exe .
```

```bash
go build -ldflags="-s -w" -o dist/licencia .
```

Para probar sin compilar: `go run .`. El flag `-no-open` evita que se abra el navegador.

## Regenerar el contenido

Si cambian los documentos de `Docs/`:

```bash
uv run scripts/build_corpus.py
```

El script lee los PDF y escribe `content/`: `questions.json`, `manual.json`, las imágenes y `REPORT.md`. Después volvé a compilar el ejecutable.

Estos archivos de `content/` los escribimos a mano. El script no los pisa:

| Archivo | Qué tiene |
|---|---|
| `notes.json` | Transcripción de cada captura y el tema al que pertenece |
| `answer_overrides.json` | Respuestas deducidas del manual, correcciones y advertencias |
| `CONFLICTS.md` | Diferencias entre fuentes y qué versión usa la app |
| `lessons/chNN.json` | Las lecciones (formato en `lessons/SPEC.md`) |
| `question_topics.json` | Sección del manual de cada pregunta del banco |

Una captura nueva aparece en `REPORT.md` como pendiente hasta que se agrega a `notes.json`. Las capturas no se publican: cada apunte usa una ilustración propia en `content/img/notes/` (formato en `content/img/notes/SPEC.md`).

## Cuestionarios con Claude

Después del curso, en Claude Code dentro de esta carpeta:

```
/quiz-licencia
```

Hace un simulacro de examen (40 preguntas, 5 eliminatorias, se aprueba con 75 %) o un cuestionario por temas. Mezcla preguntas del banco oficial con preguntas generadas a partir del manual, cada una con su cita. Guarda los resultados en `progress/quiz-history.md`, y la próxima vez pregunta más sobre tus temas flojos.

## Cuestionarios en claude.ai (chat normal)

```bash
python3 scripts/build_web_skill.py
```

Genera `dist/quiz-licencia-web.zip`. Subilo en claude.ai: *Settings → Features → Upload a skill*. Requiere plan Pro o superior y tener activada la ejecución de código. Las instrucciones están en `skill-web/SKILL.md`; los datos se toman de `content/`.

En un chat nuevo pedí, por ejemplo, "haceme un simulacro de la licencia". Respondés escribiendo la letra. Al final, Claude te da un bloque que empieza con `LIC1:`. Pegalo al empezar el próximo chat, así sigue con tus temas flojos.

Después de regenerar el contenido, volvé a correr el script y subí el zip otra vez.

## Servidor en server.pi

Corre en Docker en `~/Projects/licencia_dinamica`, con reinicio automático:

- Desde esta PC: http://server.pi:8642/app/
- Desde otros dispositivos de la red: http://192.168.100.131:8642/app/

Para actualizarlo: `deploy/deploy.sh`. Compila el binario arm64, lo copia y vuelve a crear el contenedor `licencia` con `docker run`. Por HTTP en la red local la app funciona como sitio web, pero no se puede instalar ni usar sin internet: para eso hace falta HTTPS.

## Publicar en GitHub Pages

El workflow `.github/workflows/pages.yml` publica el sitio en cada push a `main`. Usa `scripts/build_site.sh`, que copia solo `app/` y `content/`, sin los archivos internos. En el repo, activá *Settings → Pages → Source: GitHub Actions*. La app queda en `https://<usuario>.github.io/<repo>/app/`, con HTTPS: se puede instalar en el teléfono.

El `.gitignore` deja afuera las capturas originales (`Docs/WhatsApp*`), el historial de cuestionarios (`progress/`) y los binarios (`dist/`).
