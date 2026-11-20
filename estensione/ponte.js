/* ═══ IL PONTE DI BARATTOZON (20 nov 2026, cantiere bz-integrata) ═══
   Andrea: «vorrei che si integrasse proprio in barattolo, quindi nella
   stessa sessione del browser, se si è loggati si è in quell'account
   [...] automaticamente deve inserire il paycode in barattozon, deve
   solamente chiedere la commissione e così si crea l'ordine».

   Il ponte e' lo sfondo dell'estensione, e fa SOLO due cose:
   1. L'INTENTO: chi tocca «Compra con Barattozon» su un prodotto o nel
      carrello lo dice qui; alla cassa amazon.js chiede «e' un acquisto
      Barattozon?» e solo allora sceglie i contanti da solo (un acquisto
      qualunque su Amazon resta com'e'). Vale tre ore.
   2. L'ORDINE: dalla pagina del PayCode arrivano i dati (PayCode,
      importo, scadenza, codice a barre, premio dalla commissione); il
      ponte apre UNA scheda nuova su barattolo.store e li tiene per
      QUELLA scheda e basta (il suo id), al piu' mezz'ora. Li' barattolo.js
      li chiede, il ponte li consegna una volta e li cancella.
   PERCHE' UN PONTE E NON PIU' IL LINK COI DATI: un link lo puo' scrivere
   chiunque, e Barattolo un ordine da solo non deve pubblicarlo per un
   link arrivato da fuori (un PayCode altrui farebbe vendere i tuoi
   sats). Un dato consegnato dal ponte alla scheda che il ponte stesso
   ha aperto viene per forza da un tocco su «Crea l'ordine» qui.
   NIENTE RETE, NIENTE CHIAVI: il ponte non parla con nessun server e
   non sa chi sei; l'ordine lo firma Barattolo nella scheda, con la
   chiave del tuo dispositivo, nella sessione dove sei gia' entrato.
   La memoria e' `storage.session`: sparisce chiudendo il browser. */

const API = (typeof browser !== 'undefined' && browser.runtime) ? browser : chrome;
const BARATTOLO_BZ = 'https://barattolo.store/p2p#barattozon-estensione';
const INTENTO_S = 3 * 3600;     // l'acquisto Barattozon vale tre ore
const ORDINE_S = 30 * 60;       // i dati aspettano la scheda mezz'ora
const CAMPI = ['pc', 'importo', 'scade', 'barre', 'premio'];

function adesso(){ return Math.floor(Date.now() / 1000); }

/* PURA: tiene solo i campi noti, come testo corto. Il giudice vero e'
   la dogana di Barattolo (`datiBzDaFrammentoP2P`), che li rigiudica */
function pulisci(d){
  const o = {};
  for (const k of CAMPI) {
    const v = d && d[k] != null ? String(d[k]).slice(0, 60) : '';
    if (v) o[k] = v;
  }
  return o;
}

API.runtime.onMessage.addListener((msg, chi, rispondi) => {
  const tipo = msg && msg.tipo;
  (async () => {
    if (tipo === 'intento') {
      await API.storage.session.set({intento: adesso()});
      return {ok: true};
    }
    if (tipo === 'intento?') {
      const v = await API.storage.session.get('intento');
      const t = Number(v.intento) || 0;
      return {intento: t > 0 && adesso() - t <= INTENTO_S};
    }
    if (tipo === 'crea') {
      const d = pulisci(msg.d);
      if (!d.pc) return {ok: false};
      const scheda = await API.tabs.create({url: BARATTOLO_BZ});
      await API.storage.session.set({ordine: {scheda: scheda.id, t: adesso(), d}});
      /* l'acquisto e' finito: il prossimo alla cassa riparte da capo */
      await API.storage.session.remove('intento');
      return {ok: true};
    }
    if (tipo === 'prendi') {
      const v = await API.storage.session.get('ordine');
      const o = v.ordine;
      /* SOLO la scheda che il ponte ha aperto, e solo entro mezz'ora */
      if (!o || !chi.tab || chi.tab.id !== o.scheda || adesso() - o.t > ORDINE_S) return {d: null};
      await API.storage.session.remove('ordine');
      return {d: o.d};
    }
    return {};
  })().then(rispondi, () => rispondi({}));
  return true;   // la risposta arriva dopo (sendResponse asincrono)
});
