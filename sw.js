// TASVIA Academy service worker
// HTML is network-first so production fixes are not hidden behind stale cache.
// Firebase/Auth/API traffic is never cached.
const CACHE = "tasvia-v9";
const STATIC_SHELL = [
  "/",
  "/index.html",
  "/parent/index.html",
  "/firebase-config.js",
  "/manifest.json",
  "/logo.png",
  "/icon-192.png",
  "/icon-512.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(STATIC_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE).map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    // Never cache Firebase, authentication, or other third-party application traffic.
    return;
  }

  const isHtml = request.mode === "navigate" || request.destination === "document";
  const isStaticAsset = /\\.(?:css|js|png|jpg|jpeg|webp|svg|ico|woff2?)$/i.test(url.pathname);

  if (isHtml) {
    // Always prefer the current deployed HTML; fall back to cached HTML only offline.
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then(cache => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(request).then(cached => cached || caches.match("/index.html")))
    );
    return;
  }

  if (isStaticAsset) {
    // Versioned static assets can safely use cache-first with network fallback.
    event.respondWith(
      caches.match(request).then(cached =>
        cached || fetch(request).then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then(cache => cache.put(request, copy));
          }
          return response;
        })
      )
    );
  }
});
