/* sw.js — il service worker PRUDENTE di Barattolo.
   Vive SOLO fuori da Telegram (la guardia sta nella pagina, che dentro
   la Mini App non lo registra proprio). Il suo unico mestiere e' tenere
   in dispensa gli asset statici e mostrare la pagina offline quando la
   rete muore. La regola d'oro: cio' che non tocca, NON lo tocca — le
   API e le pagine passano sempre dalla rete, come se lui non ci fosse.

   REGOLA OPERATIVA (emendata set 2026): gli asset che la pagina chiede
   col timbro ?v=<hash> si aggiornano DA SOLI — chiave nuova in
   dispensa, nessun numero da alzare. VERSIONE resta per cio' che
   viaggia senza timbro (offline.html e le richieste del precache):
   se cambi quelli, o l'elenco, alzala e le dispense vecchie si
   svuotano da sole. */

const VERSIONE = 'barattolo-v12';   // v12: offline.html riprova da sola (logout-apk)
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
/* LA DISPENSA A RUNTIME E' PIU' LARGA DELL'INSTALLAZIONE ATOMICA (17 set
   2026). Le due liste facevano due mestieri sotto lo stesso nome, e per
   `/vendor/nostr.js` uno dei due era finito: da quando il match rispetta
   la query (set 2026, «la dispensa che rispetta la query») la voce NUDA
   non risponde piu' a nessuno — la pagina chiede il file col suo timbro
   `?v=`, che e' un'altra chiave — quindi si scaricavano 250 KB a ogni
   salto di VERSIONE per non servire mai. Il gate di sotto invece guarda
   `url.pathname`, e quello serve: il file entra in dispensa al PRIMO USO
   vero, con la sua chiave timbrata, e da li' e' cache-first come gli
   altri.
   ⚠️ ED E' LA META' CHE UN'INSTALLAZIONE FRESCA NON HA, che e' la
   ragione per cui il P2P si rompe la' e non qui: chi ha aperto il P2P
   una volta ha il file appeso al timbro e non chiede piu' niente alla
   rete, chi installa oggi lo prende in quel momento — e se li' qualcosa
   va storto lo dice la guardia del client (`esigiBundleNostr`, che dal
   17 set 2026 distingue «non e' arrivata» da «copia incompleta»).
   IL SALTO DI VERSIONE CHE ACCOMPAGNA QUESTA RIGA NON E' BUROCRAZIA:
   svuotando le dispense vecchie e' l'unica leva che abbiamo per buttare
   via una copia stantia rimasta appesa a quel timbro su un telefono che
   non possiamo toccare. */
/* …e dal 16 ott 2026 anche il bundle BITCOIN, con lo stesso patto e
   per la stessa ragione: sta nella dispensa a RUNTIME e MAI
   nell'addAll atomico dell'installazione — chi non apre mai il banco
   delle chiavi non deve scaricare 334 KB per nessuno. Chi lo apre, al
   secondo giro lo trova qui. */
const IN_DISPENSA = new Set([...PRECACHE, '/vendor/nostr.js',
                             '/vendor/btc.js']);

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

    // gli asset in dispensa: prima la dispensa, poi la rete.
    // IL MATCH E' SULL'URL INTERO, query compresa (set 2026, la cura
    // dei loghi stantii): prima si cercava per pathname, quindi un
    // asset sostituito col cache-buster nuovo (?v=<hash>) riceveva
    // comunque la copia vecchia dalla dispensa — il buco esatto che
    // rendeva inutile il timbro. Ora una versione nuova e' una chiave
    // nuova: manca, si scarica, e si mette via per la prossima volta.
    if (IN_DISPENSA.has(url.pathname)) {
      e.respondWith((async () => {
        const c = await caches.open(CACHE_STATICA);
        const pronta = await c.match(r);
        if (pronta) return pronta;
        const fresca = await fetch(r);
        if (fresca && fresca.ok) c.put(r, fresca.clone());
        return fresca;
      })());
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

/* LE NOTIFICHE SUL TELEFONO (14 nov 2026, cantiere web-push). Il server
   cifra l'avviso per questo telefono e lo spedisce al suo servizio push
   (Google, Mozilla, Apple, Microsoft); qui arriva anche ad app chiusa e
   diventa una notifica. Nell'app di Zapstore Chrome la consegna all'app
   (enableNotifications della 1.5): nome e icona sono di Barattolo.
   Il carico e' {titolo, testo, url}; `url` e' un percorso di CASA:
   `indirizzoDiCasa` non apre mai niente fuori da questa origine, anche se
   un domani il carico dicesse altro. */
function indirizzoDiCasa(u) {
  try {
    const x = new URL(u || '/', self.location.origin);
    if (x.origin === self.location.origin) return x.href;
  } catch (e) { /* storto: la home */ }
  return self.location.origin + '/';
}

self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; }
  catch (err) { d = {testo: e.data ? e.data.text() : ''}; }
  const titolo = String(d.titolo || 'Barattolo').slice(0, 80);
  e.waitUntil(self.registration.showNotification(titolo, {
    body: String(d.testo || 'Hai un avviso nuovo').slice(0, 400),
    icon: '/assets/icona-192.png',
    lang: 'it',
    data: {url: indirizzoDiCasa(d.url)},
  }));
});

/* Il tocco: se Barattolo e' gia' aperto lo si porta davanti e lo si
   manda alla pagina dell'avviso, se no lo si apre li'. */
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const dove = indirizzoDiCasa(e.notification.data && e.notification.data.url);
  e.waitUntil((async () => {
    const aperte = await self.clients.matchAll({type: 'window',
                                                includeUncontrolled: true});
    for (const c of aperte) {
      if (new URL(c.url).origin !== self.location.origin) continue;
      try { await c.focus(); } catch (err) { /* niente fuoco: si naviga lo stesso */ }
      try { if ('navigate' in c) { await c.navigate(dove); return; } }
      catch (err) { /* finestra non nostra: se ne apre una */ }
      break;
    }
    await self.clients.openWindow(dove);
  })());
});

/* Il browser puo' cambiare l'indirizzo da solo (raro, ma succede): ci si
   riscrive con la stessa chiave del timbro e si dice al server qual era
   il vecchio, che se ne va. Il cookie della sessione viaggia da solo
   (stessa origine); se l'utente e' uscito, il server dice 401 e basta. */
self.addEventListener('pushsubscriptionchange', (e) => {
  e.waitUntil((async () => {
    const vecchia = e.oldSubscription;
    const chiave = vecchia && vecchia.options && vecchia.options.applicationServerKey;
    const nuova = e.newSubscription || (chiave ? await self.registration.pushManager
      .subscribe({userVisibleOnly: true, applicationServerKey: chiave}) : null);
    if (!nuova) return;
    const j = nuova.toJSON();
    await fetch('/api/push/iscrivi', {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({endpoint: j.endpoint, p256dh: j.keys.p256dh,
                            auth: j.keys.auth,
                            vecchio: vecchia ? vecchia.endpoint : ''}),
    });
  })().catch(() => {}));
});
