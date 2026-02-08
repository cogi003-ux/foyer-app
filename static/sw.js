// Service Worker pour Foyer Magique
const CACHE_NAME = 'foyer-magique-v1.4';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/manifest.json',
  'https://unpkg.com/lucide@latest'
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Cache ouvert');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('Erreur lors de la mise en cache:', error);
      })
  );
  self.skipWaiting();
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Suppression de l\'ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// URLs à ne JAMAIS mettre en cache : login / auth et API de validation
function shouldNeverCache(url) {
  try {
    const u = new URL(url);
    const path = u.pathname || '';
    const search = u.search || '';
    if (path.indexOf('/api/auth') !== -1) return true;
    if (path.indexOf('/api/attente-validation') !== -1) return true;
    if (search.indexOf('login') !== -1 || search.indexOf('parent=1') !== -1) return true;
    if (path === '/' && search.indexOf('parent') !== -1) return true;
    if (path === '/parent' || path === '/admin') return true;
    return false;
  } catch (_) {
    return false;
  }
}

// Stratégie: Network First, puis Cache (sauf login et API validation)
self.addEventListener('fetch', (event) => {
  const url = event.request.url;

  if (shouldNeverCache(url)) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const responseToCache = response.clone();
        caches.open(CACHE_NAME)
          .then((cache) => {
            cache.put(event.request, responseToCache);
          });
        return response;
      })
      .catch(() => {
        return caches.match(event.request)
          .then((response) => {
            if (response) return response;
            return new Response('Mode hors ligne - Contenu non disponible', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({ 'Content-Type': 'text/plain' })
            });
          });
      })
  );
});
