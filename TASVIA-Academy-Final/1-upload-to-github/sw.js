// Lets the app open without internet. Data sync is handled by Firebase (it queues changes offline).
const CACHE = "tasvia-v3";
const SHELL = ["./", "index.html", "parent.html", "firebase-config.js", "manifest.json", "logo.png", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (/googleapis\.com$/.test(url.hostname) && !/fonts\.googleapis\.com/.test(url.hostname)) return; // database traffic
  const cacheFirst = /gstatic\.com$|fonts\.googleapis\.com$/.test(url.hostname);
  if (cacheFirst) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
    })));
  } else if (url.origin === location.origin) {
    const page = /parent\.html$/.test(url.pathname) ? "parent.html" : "index.html";
    e.respondWith(fetch(e.request).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return res;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(hit => hit || (e.request.mode === "navigate" ? caches.match(page) : undefined))));
  }
});
