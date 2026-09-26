/* الطوخي للحج والعمرة — Service Worker
   VERSION bump to invalidate old caches on release.
   Strategy:
     - Assets (css/js/images): cache-first, then network + cache
     - HTML/navigation:        network-first, fallback to cache then /offline/
*/
'use strict';

var VERSION = 'v1.2.0';
var CACHE_ASSETS = 'eltokhey-assets-' + VERSION;
var CACHE_PAGES = 'eltokhey-pages-' + VERSION;
var CACHE_PREFIX = 'eltokhey-';

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_PAGES)
      .then(function (cache) { return cache.add('/offline/'); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(
          keys
            .filter(function (key) {
              return key.indexOf(CACHE_PREFIX) === 0 &&
                     key.indexOf(VERSION) === -1;
            })
            .map(function (key) { return caches.delete(key); })
        );
      })
      .then(function () { return self.clients.claim(); })
  );
});

function isAsset(url) {
  return /\.(css|js|json|webmanifest|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot)$/.test(url.pathname);
}

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') return;

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  /* 1) HTML / navigation: network-first */
  if (request.mode === 'navigate' || request.headers.get('accept').indexOf('text/html') !== -1) {
    event.respondWith(
      fetch(request)
        .then(function (response) {
          if (response && response.ok) {
            var copy = response.clone();
            caches.open(CACHE_PAGES).then(function (cache) {
              cache.put(request, copy);
            });
          }
          return response;
        })
        .catch(function () {
          return caches.match(request).then(function (cached) {
            return cached || caches.match('/offline/');
          });
        })
    );
    return;
  }

  /* 2) Static assets: cache-first */
  if (isAsset(url) || url.pathname.indexOf('/manifest') !== -1) {
    event.respondWith(
      caches.match(request).then(function (cached) {
        if (cached) return cached;
        return fetch(request).then(function (response) {
          if (response && response.ok) {
            var copy = response.clone();
            caches.open(CACHE_ASSETS).then(function (cache) {
              cache.put(request, copy);
            });
          }
          return response;
        }).catch(function () { return cached; });
      })
    );
    return;
  }

  /* 3) Everything else: network-first with asset cache fallback */
  event.respondWith(
    fetch(request).catch(function () {
      return caches.match(request);
    })
  );
});