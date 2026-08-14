/* sw.js — il service worker PRUDENTE di Barattolo.
   Vive SOLO fuori da Telegram (la guardia sta nella pagina, che dentro
   la Mini App non lo registra proprio). Il suo unico mestiere e' tenere
   in dispensa gli asset statici e mostrare la pagina offline quando la
   rete muore. La regola d'oro: cio' che non tocca, NON lo tocca — le
   API e le pagine passano sempre dalla rete, come se lui non ci fosse.

   REGOLA OPERATIVA: se cambi un file dell'elenco PRECACHE (o il file
   stesso), alza VERSIONE — le dispense vecchie si svuotano da sole. */

const VERSIONE = 'barattolo-v5';
const CACHE_STATICA = `statica-${VERSIONE}`;

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
  '/vendor/qrcode.js',
  // I font, da quando stanno in casa (ago 2026): SOLO i tre file del
  // latino, che sono quelli che servono a chiunque scriva in italiano.
  // I `latin-ext` passano dalla rete come ogni file non in dispensa: qui
  // dentro finirebbero nell'addAll ATOMICO, e gonfiare un'installazione
  // che o riesce tutta o non riesce non conviene per un alfabeto che
  // quasi nessuno userà.
  '/vendor/font/baloo2-latin.woff2',
  '/vendor/font/nunito-latin.woff2',
  '/vendor/font/jetbrains-mono-latin.woff2',
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

  // FUORI CASA NON SI TOCCA PIU' NIENTE (ago 2026). Qui c'era il ramo
  // cache-first per i font di Google: da quando i font stanno in
  // vendor/font/ cadono nel ramo di sopra, come ogni altro file
  // nostro, e questo non serve piu'. Tutto il resto — telegram.org in
  // testa: script che gestiscono l'auth — passa oltre senza essere
  // nemmeno sfiorato, come e' sempre stato.
});
