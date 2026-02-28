// Service Worker für EVT Mobile – BRK Feucht
// Empfängt Web-Push-Nachrichten und zeigt System-Benachrichtigungen

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

// Push-Event: Nachricht vom Server empfangen
self.addEventListener('push', (event) => {
  let data = { title: 'NEUER EINSATZ', body: '' };
  try {
    data = event.data.json();
  } catch (_) {
    data.body = event.data ? event.data.text() : '';
  }

  const options = {
    body: data.body || '',
    tag: 'evt-alarm',
    requireInteraction: true,
    vibrate: [400, 120, 400, 120, 800, 500, 400, 120, 400, 120, 800],
    data: { url: '/evt' },
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'NEUER EINSATZ', options)
  );
});

// Klick auf Notification → App öffnen/fokussieren
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/evt';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const c of clients) {
        if (c.url.includes('/evt') && 'focus' in c) return c.focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
