const CACHE_NAME = 'gumaphoto-v12-cache-breaker';

self.addEventListener('install', (event) => {
    // Force the waiting service worker to become the active service worker
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    // Claim any clients immediately, so that the page will be under SW control without reloading.
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Simple network-first approach for dynamic content
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});
