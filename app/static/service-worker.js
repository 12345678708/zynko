// Service worker (cache-first) — CACHE_NAME bumped to force clients to refresh
const CACHE_NAME = 'zynko-cache-v2';
const ASSETS = [
  '/',
  '/favicon.ico',
  '/static/style.css',
  '/static/icons/icon-192.svg',
  '/static/icons/icon-512.svg'
];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
});
self.addEventListener('fetch', (event) => {
  event.respondWith(caches.match(event.request).then(res => res || fetch(event.request)));
});
