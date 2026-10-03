// Study app: reads ../content/*.json and renders a hash-routed course. No dependencies.
const C = "../content/";
const KEY = "licencia.v1";
const QUIZ_SIZE = 5;
const D = {}; // data, filled by boot()
const S = loadState();

function loadState() {
  try { return { done: {}, pos: {}, ans: {}, optional: false, theme: "auto", ...JSON.parse(localStorage.getItem(KEY)) }; }
  catch { return { done: {}, pos: {}, ans: {}, optional: false, theme: "auto" }; }
}
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch { /* private mode: progress is not kept */ } }

const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const fold = s => String(s).normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
const pad3 = n => String(n).padStart(3, "0");
const pageImg = n => `${C}img/manual/p${pad3(n)}.jpg`;
const pageLink = (n, label = `Manual, p. ${n}`) => `<a href="#" data-zoom="${pageImg(n)}">${esc(label)}</a>`;

// Lesson markup: **bold**, "- " bullets, blank line between paragraphs.
function md(text) {
  return String(text ?? "").split(/\n\s*\n/).map(block => {
    const lines = block.split("\n");
    const inline = s => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    if (block.startsWith("TODO: verify")) return `<p class="warn">⚠ Dato a confirmar ${inline(block.replace(/^TODO: verify\s*/, ""))}</p>`;
    if (lines.every(l => l.trim().startsWith("- "))) return `<ul>${lines.map(l => `<li>${inline(l.trim().slice(2))}</li>`).join("")}</ul>`;
    return `<p>${lines.map(inline).join("<br>")}</p>`;
  }).join("");
}

async function getJSON(path) {
  const r = await fetch(C + path);
  if (!r.ok) throw new Error(path);
  return r.json();
}

async function boot() {
  applyTheme();
  const [manual, questions, notes] = await Promise.all(["manual.json", "questions.json", "notes.json"].map(getJSON));
  const topics = await getJSON("question_topics.json").catch(() => ({}));
  const files = await Promise.all(manual.map(c => getJSON(`lessons/ch${String(c.n).padStart(2, "0")}.json`).catch(() => null)));

  D.chapters = manual.map((c, i) => ({ n: c.n, title: c.title, inB1: c.in_b1, lessons: files[i]?.lessons ?? [] }));
  D.lessons = D.chapters.flatMap(c => c.lessons.map(l => ({ ...l, chapter: c.n })));
  D.lessonById = Object.fromEntries(D.lessons.map(l => [l.id, l]));
  D.questions = questions;
  D.notes = notes.filter(n => n.status !== "no_study_content");

  // Practice questions per section; the bank repeats some questions verbatim, keep one of each.
  D.qBySection = {};
  const seen = new Set();
  for (const q of questions) {
    const sec = topics[q.id];
    if (!sec || seen.has(q.text + q.options.map(o => o.text).join())) continue;
    seen.add(q.text + q.options.map(o => o.text).join());
    (D.qBySection[sec] ??= []).push(q);
  }
  D.signs = questions.filter(q => q.images.length === 1 && q.type === "single" && /siguiente señal indica|tipo de señal/i.test(q.text))
    .map(q => ({ img: C + q.images[0].file, meaning: q.options.find(o => o.correct)?.text, q }))
    .filter(s => s.meaning && !/^(figura|la señal|imagen)/i.test(s.meaning));

  addEventListener("hashchange", route);
  route();
}

function visibleChapters() { return D.chapters.filter(c => c.lessons.length && (c.inB1 || S.optional)); }
function studyLessons() { return visibleChapters().flatMap(c => c.lessons.map(l => D.lessonById[l.id])); }

function route() {
  const [name, a, b] = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  const view = $("#view");
  const pages = { "": home, cap: chapter, l: lesson, senales: signs, extra, buscar: search, ajustes: settings };
  (pages[name] ?? home)(view, a, b);
  view.focus({ preventScroll: true });
  scrollTo(0, 0);
}

// ---------- Home ----------
function home(view) {
  const all = studyLessons();
  const done = all.filter(l => S.done[l.id]).length;
  const next = all.find(l => !S.done[l.id]);
  const answered = Object.values(S.ans);
  view.innerHTML = `
    <section class="panel stack">
      <h1>Curso teórico — licencia B1</h1>
      <p class="muted">Manual del Conductor de la Provincia de Buenos Aires, en lecciones cortas. Cada tarjeta cita su página del manual.</p>
      <div class="bar"><i style="width:${all.length ? (100 * done / all.length) : 0}%"></i></div>
      <div class="row spread">
        <span class="small muted">${done} de ${all.length} lecciones vistas · ${answered.filter(Boolean).length}/${answered.length} preguntas bien</span>
        ${next ? `<a class="btn primary" href="#/l/${next.id}/${S.pos[next.id] ?? 0}">${done ? "Seguir" : "Empezar"}: ${esc(next.title)} →</a>` : `<span class="tag">¡Curso completo!</span>`}
      </div>
    </section>
    ${installHint()}
    <h2 style="margin-top:28px">Capítulos</h2>
    <div class="grid">${visibleChapters().map(chapterCard).join("")}</div>`;
  $("#install", view)?.addEventListener("click", async () => { installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; route(); });
}

// ---------- Install as an app (PWA) ----------
let installPrompt = null; // Chrome/Edge/Android: the browser's install dialog, offered once it fires
addEventListener("beforeinstallprompt", e => { e.preventDefault(); installPrompt = e; if (!location.hash.replace(/^#\/?/, "")) route(); });
const standalone = () => matchMedia("(display-mode: standalone)").matches || navigator.standalone;

function installHint() {
  if (standalone()) return "";
  if (installPrompt) return `<section class="panel row spread" style="margin-top:14px"><span>📲 Instalá la app en este dispositivo para abrirla como una aplicación, incluso sin internet.</span><button class="btn primary" id="install">Instalar</button></section>`;
  if (/iphone|ipad/i.test(navigator.userAgent)) return `<p class="panel small" style="margin-top:14px">📲 Para instalarla en el iPhone: tocá <strong>Compartir</strong> y después <strong>Agregar a inicio</strong>.</p>`;
  return "";
}

function chapterCard(c) {
  const done = c.lessons.filter(l => S.done[l.id]).length;
  return `<a class="panel chapter" href="#/cap/${c.n}">
    <div class="num">Capítulo ${c.n}${c.inB1 ? "" : ` · <span class="tag">opcional</span>`}</div>
    <h3>${esc(c.title)}</h3>
    <div class="bar"><i style="width:${100 * done / c.lessons.length}%"></i></div>
    <div class="small muted" style="margin-top:6px">${done}/${c.lessons.length} lecciones</div></a>`;
}

// ---------- Chapter ----------
function chapter(view, n) {
  const c = D.chapters.find(c => c.n === +n);
  if (!c) return home(view);
  view.innerHTML = `
    <p class="small"><a href="#/">← Inicio</a></p>
    <h1>${c.n}. ${esc(c.title)}</h1>
    ${c.inB1 ? "" : `<p class="warn">Capítulo opcional: no corresponde a la clase B1.</p>`}
    <ul class="lessons panel">${c.lessons.map(l => `
      <li><a href="#/l/${l.id}/0"><span class="check">${S.done[l.id] ? "✅" : "○"}</span>
        <span><strong>${esc(l.id)} ${esc(l.title)}</strong><br><span class="small muted">${esc(l.summary ?? "")}</span></span></a></li>`).join("")}
    </ul>`;
}

// ---------- Lesson ----------
function lesson(view, id, k) {
  const l = D.lessonById[id];
  if (!l) return home(view);
  const n = l.cards.length;
  k = Math.max(0, Math.min(+k || 0, n));
  S.pos[id] = k;
  if (k === n) S.done[id] = true;
  save();
  const order = studyLessons();
  const nextLesson = order[order.indexOf(l) + 1];
  const prev = k > 0 ? `#/l/${id}/${k - 1}` : null;
  const next = k < n ? `#/l/${id}/${k + 1}` : nextLesson ? `#/l/${nextLesson.id}/0` : "#/";

  view.innerHTML = `
    <p class="small"><a href="#/cap/${l.chapter}">← Capítulo ${l.chapter}</a> · ${esc(l.id)} ${esc(l.title)}</p>
    <div class="dots" aria-hidden="true">${Array.from({ length: n + 1 }, (_, i) => `<i class="${i <= k ? "on" : ""}"></i>`).join("")}</div>
    <div id="slot" style="margin:14px 0"></div>
    <div class="row spread">
      <a class="btn" ${prev ? `href="${prev}"` : `aria-disabled="true" style="visibility:hidden"`}>← Anterior</a>
      <span class="small muted">${k < n ? `${k + 1} / ${n}` : "Repaso"}</span>
      <a class="btn primary" href="${next}">${k < n ? "Siguiente →" : nextLesson ? "Próxima lección →" : "Inicio"}</a>
    </div>`;
  const slot = $("#slot", view);
  if (k < n) slot.append(cardEl(l.cards[k]));
  else slot.append(reviewEl(l));
  document.onkeydown = e => {
    if (!location.hash.startsWith("#/l/") || e.target.matches("input")) return;
    if (e.key === "ArrowRight") location.hash = next;
    if (e.key === "ArrowLeft" && prev) location.hash = prev;
  };
}

const tableHtml = t => t ? `<div class="table-wrap"><table>
  <thead><tr>${t.head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
  <tbody>${t.rows.map(r => `<tr>${r.map(cell).join("")}</tr>`).join("")}</tbody></table></div>` : "";
// Effect labels in note tables render as coloured tags.
const EFFECT = { "ahorra": "ok", "gasta más": "bad", "depende": "" };
const cell = c => c in EFFECT ? `<td><span class="tag ${EFFECT[c]}">${esc(c)}</span></td>` : `<td>${esc(c)}</td>`;

function cardEl(card) {
  const el = document.createElement("article");
  el.className = "panel card";
  const table = tableHtml(card.table);
  el.innerHTML = `
    <h2>${esc(card.title)}</h2>
    ${card.image ? `<figure><img src="${C}${esc(card.image)}" data-zoom="${C}${esc(card.image)}" alt="" loading="lazy"></figure>` : ""}
    <div class="body">${md(card.body)}</div>
    ${table}
    ${card.callout ? `<div class="callout">💡 ${esc(card.callout)}</div>` : ""}
    <div class="source muted">Fuente: ${pageLink(card.page)}</div>`;
  return el;
}

function reviewEl(l) {
  const el = document.createElement("div");
  el.className = "stack";
  const qs = (D.qBySection[l.id] ?? []).slice().sort(() => Math.random() - .5).slice(0, QUIZ_SIZE);
  const notes = D.notes.filter(n => n.topics.includes(l.id));
  el.innerHTML = `<section class="panel"><h2>✅ Lección vista</h2>
    <p class="muted">${qs.length ? "Comprobá lo que sabés con preguntas del cuestionario oficial." : "Esta lección no tiene preguntas en el cuestionario oficial."}</p></section>`;
  qs.forEach(q => el.append(questionEl(q)));
  notes.forEach(n => el.append(noteEl(n, "Tus apuntes")));
  return el;
}

// ---------- Question widget ----------
function questionEl(q) {
  const el = document.createElement("section");
  el.className = "panel q";
  const multi = q.type === "multi";
  el.innerHTML = `
    <div class="row small muted spread"><span>${multi ? "Elegí todas las correctas" : "Elegí una"}</span>
      ${q.eliminatoria ? `<span class="badge elim">ELIMINATORIA</span>` : ""}</div>
    <div class="text">${esc(q.text)}</div>
    ${q.images.map(i => `<img src="${C}${esc(i.file)}" data-zoom="${C}${esc(i.file)}" alt="" loading="lazy">`).join("")}
    <div class="opts">${q.options.map((o, i) => `<button class="opt" data-i="${i}">${esc(o.text)}</button>`).join("")}</div>
    ${multi ? `<div class="row" style="margin-top:10px"><button class="btn primary check">Comprobar</button></div>` : ""}
    <div class="feedback"></div>`;
  const opts = [...el.querySelectorAll(".opt")];
  const grade = picked => {
    opts.forEach((b, i) => {
      b.disabled = true;
      if (q.answer_source === "todo") return;
      if (q.options[i].correct) b.classList.add("right");
      else if (picked.has(i)) b.classList.add("wrong");
    });
    $(".check", el)?.remove();
    const fb = $(".feedback", el);
    if (q.answer_source === "todo") { fb.innerHTML = `<p class="warn">Sin respuesta verificada: ${esc(q.todo)}</p>`; return; }
    const ok = q.options.every((o, i) => o.correct === picked.has(i));
    S.ans[q.id] = ok; save();
    fb.innerHTML = `<p><strong>${ok ? "✔ Correcto" : "✘ Incorrecto"}</strong> · <span class="muted">Cuestionario oficial, p. ${q.page}</span></p>
      ${q.derived_from ? `<p class="small">Respuesta según el manual: ${esc(q.derived_from.note)} (${pageLink(q.derived_from.page, `p. ${q.derived_from.page}`)})</p>` : ""}
      ${q.warning ? `<p class="warn">⚠ ${esc(q.warning)}</p>` : ""}`;
  };
  const picked = new Set();
  opts.forEach((b, i) => b.addEventListener("click", () => {
    if (!multi) return grade(new Set([i]));
    picked.has(i) ? picked.delete(i) : picked.add(i);
    b.classList.toggle("picked");
  }));
  $(".check", el)?.addEventListener("click", () => grade(picked));
  return el;
}

// ---------- Notes (photos) ----------
function noteEl(n, heading) {
  const el = document.createElement("section");
  el.className = "panel note stack";
  const src = n.image && C + n.image; // our own illustration: the source photos are third-party ads
  el.innerHTML = `
    <div class="row spread"><h3 style="margin:0">${heading ? `${esc(heading)}: ` : ""}${esc(n.title)}</h3>
      ${n.status === "outside_manual" ? `<span class="tag">no está en el manual</span>` : ""}</div>
    ${n.warning ? `<p class="warn">⚠ ${esc(n.warning)}</p>` : ""}
    ${tableHtml(n.table)}
    <div class="row" style="align-items:flex-start">
      ${src ? `<img src="${src}" data-zoom="${src}" alt="" loading="lazy" style="width:140px" onerror="this.remove()">` : ""}
      <ul style="flex:1;min-width:220px;margin:0">${n.facts.filter(f => !f.startsWith("TODO")).map(f => `<li>${esc(f)}</li>`).join("")}</ul>
    </div>`;
  return el;
}

function extra(view) {
  view.innerHTML = `<h1>Práctica al volante</h1>
    <p class="muted">Consejos de manejo de tus apuntes. Casi nada de esto entra en el examen teórico; sirve para las clases prácticas.</p>
    <div class="stack" id="list"></div>`;
  D.notes.filter(n => n.topics.includes("extra.practica")).forEach(n => $("#list", view).append(noteEl(n)));
}

// ---------- Signs ----------
function signs(view) {
  view.innerHTML = `
    <h1>Señales</h1>
    <p class="muted">Tocá cada señal para ver qué significa. Salen del cuestionario oficial.</p>
    <div class="row" style="margin-bottom:14px"><button class="btn" id="shuffle">🔀 Mezclar</button><button class="btn" id="reveal">Dar vuelta todas</button></div>
    <div class="signs" id="grid"></div>
    <h2 style="margin-top:28px">Láminas del manual</h2>
    <div class="grid">${[43, 44, 45, 46, 48].map(p => `<figure class="panel" style="margin:0">
      <img src="${pageImg(p)}" data-zoom="${pageImg(p)}" alt="" loading="lazy" style="cursor:zoom-in">
      <figcaption class="small muted">Manual, p. ${p}</figcaption></figure>`).join("")}</div>`;
  const draw = list => {
    $("#grid", view).innerHTML = list.map(s => `<button class="flip"><div class="in">
      <div class="face"><img src="${esc(s.img)}" alt="Señal" loading="lazy"></div>
      <div class="face back">${esc(s.meaning)}</div></div></button>`).join("");
  };
  draw(D.signs);
  $("#grid", view).addEventListener("click", e => e.target.closest(".flip")?.classList.toggle("on"));
  $("#shuffle", view).onclick = () => draw(D.signs.slice().sort(() => Math.random() - .5));
  $("#reveal", view).onclick = () => view.querySelectorAll(".flip").forEach(f => f.classList.toggle("on"));
}

// ---------- Search ----------
function search(view, query = "") {
  view.innerHTML = `<h1>Buscar</h1>
    <input type="search" id="q" placeholder="Ej.: rotonda, alcohol, estacionar…" value="${esc(query)}" autofocus>
    <div id="results" style="margin-top:12px"></div>`;
  const input = $("#q", view);
  const run = () => {
    const words = fold(input.value).split(/\s+/).filter(w => w.length > 1);
    const out = $("#results", view);
    if (!words.length) { out.innerHTML = ""; return; }
    const match = t => words.every(w => fold(t).includes(w));
    const mark = t => { let h = esc(t); words.forEach(w => { h = h.replace(new RegExp(`(${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"), "<mark>$1</mark>"); }); return h; };
    const hits = [];
    for (const l of studyLessons()) l.cards.forEach((c, k) => {
      const t = [c.title, c.body, c.callout, ...(c.table?.rows.flat() ?? [])].join(" ");
      if (match(t)) hits.push(`<div class="hit"><a href="#/l/${l.id}/${k}"><strong>${esc(c.title)}</strong></a>
        <span class="small muted">· ${esc(l.id)} ${esc(l.title)}</span><div class="small">${mark((c.body ?? "").replace(/\*\*/g, "").slice(0, 220))}</div></div>`);
    });
    for (const q of D.questions) if (match(q.text)) {
      const ok = q.options.filter(o => o.correct).map(o => o.text).join(" / ");
      hits.push(`<div class="hit"><span class="tag">Pregunta</span> ${mark(q.text)}<div class="small"><strong>Respuesta:</strong> ${esc(ok || "sin verificar")}</div></div>`);
    }
    for (const n of D.notes) if (match([n.title, ...n.facts, ...(n.table?.rows.flat() ?? [])].join(" "))) hits.push(`<div class="hit"><span class="tag">Apunte</span> <a href="#/extra">${mark(n.title)}</a></div>`);
    out.innerHTML = hits.length ? `<p class="small muted">${hits.length} resultados</p>${hits.slice(0, 80).join("")}` : `<p class="muted">Sin resultados.</p>`;
  };
  input.addEventListener("input", () => { history.replaceState(null, "", `#/buscar/${encodeURIComponent(input.value)}`); run(); });
  run();
}

// ---------- Settings ----------
function settings(view) {
  view.innerHTML = `<h1>Ajustes</h1>
    <section class="panel stack">
      <label class="row"><input type="checkbox" id="opt" ${S.optional ? "checked" : ""}> Mostrar capítulos opcionales (motos, triciclos y cuatriciclos)</label>
      <label class="row">Tema
        <select id="theme">${["auto", "light", "dark"].map(t => `<option value="${t}" ${S.theme === t ? "selected" : ""}>${{ auto: "Automático", light: "Claro", dark: "Oscuro" }[t]}</option>`).join("")}</select></label>
      <div class="row"><button class="btn" id="offline">⬇ Descargar todo para usar sin internet</button><span class="small muted" id="offline-status"></span></div>
      <div><button class="btn" id="reset">Borrar mi progreso</button></div>
      <p class="small muted">El progreso se guarda en este navegador.</p>
    </section>`;
  $("#opt", view).onchange = e => { S.optional = e.target.checked; save(); };
  $("#theme", view).onchange = e => { S.theme = e.target.value; save(); applyTheme(); };
  $("#offline", view).onclick = downloadAll;
  $("#reset", view).onclick = () => {
    if (!confirm("¿Borrar lecciones vistas y respuestas?")) return;
    Object.assign(S, { done: {}, pos: {}, ans: {} }); save(); location.hash = "#/";
  };
}

// Put every image in the service worker's cache, so the whole course works offline.
async function downloadAll() {
  const status = $("#offline-status");
  if (!("caches" in window) || !navigator.serviceWorker?.controller) { status.textContent = "Este navegador no permite guardar la app sin conexión."; return; }
  const urls = new Set([
    ...Array.from({ length: 185 }, (_, i) => pageImg(i + 1)),
    ...D.lessons.flatMap(l => l.cards.filter(c => c.image).map(c => C + c.image)),
    ...D.questions.flatMap(q => q.images.map(i => C + i.file)),
    ...D.notes.filter(n => n.image).map(n => C + n.image),
  ]);
  const cache = await caches.open("licencia-v3"); // same name as CACHE in sw.js
  let done = 0, failed = 0;
  const list = [...urls];
  for (let i = 0; i < list.length; i += 8) {
    await Promise.all(list.slice(i, i + 8).map(async u => {
      try { if (!(await cache.match(u))) await cache.add(u); } catch { failed++; }
      status.textContent = `${++done} / ${list.length}`;
    }));
  }
  status.textContent = failed ? `Listo, con ${failed} archivos sin descargar. Probá de nuevo.` : "Listo: la app funciona sin internet.";
}

function applyTheme() {
  if (S.theme === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.dataset.theme = S.theme;
}

// Zoom any image or page link marked with data-zoom.
document.addEventListener("click", e => {
  const z = e.target.closest("[data-zoom]");
  if (!z) return;
  e.preventDefault();
  const box = $("#lightbox");
  $("img", box).src = z.dataset.zoom;
  box.showModal();
});
$("#lightbox").addEventListener("click", e => { if (e.target.id === "lightbox") e.target.close(); });

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => { /* http on a LAN address: no offline mode */ });

boot().catch(err => { $("#view").innerHTML = `<p class="warn">No se pudo cargar el contenido (${esc(err.message)}).</p>`; });
