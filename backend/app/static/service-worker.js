const CACHE_NAME = "rail-inspect-shell-v15";
const APP_SHELL = [
  "/",
  "/static/index.html",
  "/static/styles.css?v=15",
  "/static/app.js?v=15",
  "/static/manifest.webmanifest",
  "/static/icon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys
        .filter((key) => key !== CACHE_NAME)
        .map((key) => caches.delete(key)),
    )),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (event.request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  if (
    url.pathname.startsWith("/inspections")
    || url.pathname.startsWith("/health")
    || url.pathname.startsWith("/documents")
    || url.pathname.startsWith("/docs")
    || url.pathname.startsWith("/openapi.json")
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request)),
  );
});
