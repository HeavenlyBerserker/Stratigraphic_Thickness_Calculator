const CACHE_NAME = "stc-mobile-v21";
const ASSETS = [
  "./index.html",
  "./app-info.js",
  "./batch-schema.js",
  "./batch.js",
  "./desktop-formula-where.js",
  "./manifest.json",
  "../logo.png",
  "../source/models.py",
  "../diagrams/Fig_T1.svg",
  "../diagrams/Fig_T2.svg",
  "../diagrams/Fig_T3.svg",
  "../diagrams/Fig_T4.svg",
  "../diagrams/Fig_T5.svg",
  "../diagrams/Fig_T6.svg",
  "../diagrams/Fig_T7.svg",
  "../diagrams/Fig_T8.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type !== "basic") return response;
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      });
    })
  );
});
