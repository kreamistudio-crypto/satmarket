/* sw.js — il service worker PRUDENTE di Barattolo.
   Vive SOLO fuori da Telegram (la guardia sta nella pagina, che dentro
   la Mini App non lo registra proprio). Il suo unico mestiere e' tenere
   in dispensa gli asset statici e mostrare la pagina offline quando la
   rete muore. La regola d'oro: cio' che non tocca, NON lo tocca — le
   API e le pagine passano sempre dalla rete, come se lui non ci fosse.

   REGOLA OPERATIVA: se cambi un file dell'elenco PRECACHE (o il file
   stesso), alza VERSIONE — le dispense vecchie si svuotano da sole. */

const VERSIONE = 'barattolo-v2';
const CACHE_STATICA = `statica-${VERSIONE}`;
const CACHE_FONT = `font-${VERSIONE}`;

// La dispensa: solo asset di casa, immutabili o quasi. Mai pagine HTML
// dell'app (restano sovrane con i loro header anti-cache), mai /api,
// mai /foto (hanno gia' la cache HTTP del browser, coi nomi versionati).
const PRECACHE = [
  '/offline.html',
  '/assets/mascotte.jpeg',
  '/assets/barattolo.jpeg',
  '/assets/tappo.jpeg',
  '/assets/barattolo-hero.png',
  '/assets/icona-192.png',
  '/assets/icona-512.png',
  '/assets/icona-192-maskable.png',
  '/assets/icona-512-maskable.png',
  '/assets/apple-touch-icon.png',
  '/vendor/nostr.js',
];
const IN_DISPENSA = new Set(PRECACHE);

self.addEventListener('install', (e) => {
  // addAll e' atomico: o entra tutto in dispensa, o il SW non si
  // installa (cosi' offline.html trova SEMPRE la sua mascotte).
  // Niente skipWaiting: la versione nuova aspetta la visita successiva.
  e.waitUntil(caches.open(CACHE_STATICA).then((c) => c.addAll(PRECACHE)));
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    // si svuotano le dispense delle versioni passate
    for (const nome of await caches.keys()) {
      if (!nome.endsWith(VERSIONE)) await caches.delete(nome);
    }
    // claim: il fallback offline vale gia' dalla prima visita
    await self.clients.claim();
  })());
});

// cache-first sulla dispensa dei font: se c'e' si serve, altrimenti
// si va in rete e si mette via per la prossima volta
async function fontDallaDispensa(richiesta) {
  const dispensa = await caches.open(CACHE_FONT);
  const pronta = await dispensa.match(richiesta);
  if (pronta) return pronta;
  const fresca = await fetch(richiesta);
  if (fresca.ok || fresca.type === 'opaque') {
    dispensa.put(richiesta, fresca.clone());
  }
  return fresca;
}

self.addEventListener('fetch', (e) => {
  const r = e.request;
  if (r.method !== 'GET') return;              // mai i POST: login, ordini...
  const url = new URL(r.url);

  if (url.origin === location.origin) {
    if (url.pathname.startsWith('/api/')) return;   // il patto: mai toccare le API
    if (url.pathname.startsWith('/foto/')) return;  // cache HTTP gia' in regola

    // le navigazioni (/, /annuncio/*, /negozio/*): rete SEMPRE prima —
    // gli header anti-cache della pagina restano sovrani — e la pagina
    // offline entra in scena solo a rete morta
    if (r.mode === 'navigate') {
      e.respondWith(fetch(r).catch(() => caches.match('/offline.html')));
      return;
    }

    // gli asset in dispensa: prima la dispensa, poi la rete
    if (IN_DISPENSA.has(url.pathname)) {
      e.respondWith(
        caches.match(url.pathname).then((pronta) => pronta || fetch(r))
      );
    }
    return;
  }

  // fuori casa: SOLO i font di Google (URL versionati, di fatto
  // immutabili: sono il vero buco offline della pagina). Tutto il
  // resto — telegram.org in testa: script che gestiscono l'auth —
  // passa oltre senza essere nemmeno sfiorato.
  if (url.hostname === 'fonts.googleapis.com' ||
      url.hostname === 'fonts.gstatic.com') {
    e.respondWith(fontDallaDispensa(r));
  }
});
