// Service worker: works offline once visited.
// App files and JSON: network first (fresh content when online), cache as fallback.
// Images: cache first (file names are stable; "Descargar todo" in Ajustes fills this cache).
const CACHE = "licencia-v3"; // bump when images change: they are served cache-first
const SHELL = ["./", "index.html", "style.css", "app.js", "manifest.webmanifest", "icon-192.png",
  "../content/manual.json", "../content/questions.json", "../content/notes.json", "../content/question_topics.json",
  ...Array.from({ length: 10 }, (_, i) => `../content/lessons/ch${String(i + 1).padStart(2, "0")}.json`)];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  if (req.destination === "image") {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    })));
    return;
  }
  e.respondWith(fetch(req).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  }).catch(() => caches.match(req, { ignoreSearch: true })));
});
