// Lets the app open without internet. Data sync is handled by Firebase (it queues changes offline).
const CACHE = "tasvia-v4";
const SHELL = ["./", "index.html", "firebase-config.js", "manifest.json", "logo.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  // Never cache database/auth traffic.
  if (/googleapis\.com$/.test(url.hostname) && !/fonts\.googleapis\.com/.test(url.hostname)) return;
  const cacheFirst = /gstatic\.com$|fonts\.googleapis\.com$/.test(url.hostname);
  if (cacheFirst) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
    })));
  } else if (url.origin === location.origin) {
    e.respondWith(fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
    }).catch(() => caches.match(e.request).then(hit => hit || caches.match("index.html"))));
  }
});
