/* ═══ BARATTOLO PER AMAZON (16 nov 2026, cantiere estensione-bz) ═══
   L'estensione del browser di Barattozon, il metodo «Contanti al
   tabacchino» del P2P di Barattolo. Gira SOLO sulle pagine di
   www.amazon.it. Quando nella pagina c'e' un PayCode (l'ordine appena
   fatto con «paga in contanti»), in basso a destra compare il bottone
   «🫙 Pubblica su Barattozon»: apre barattolo.store in una scheda nuova
   con il foglio «Vendi BTC» di Barattozon gia' compilato. Chi l'ha
   aperto rilegge e pubblica LI', con la chiave del suo dispositivo.

   LE REGOLE DI QUESTO FILE (il perche' in docs/CANTIERI.md, «L'estensione
   del browser per Barattozon»):
   - NON PARLA CON NESSUNO: niente fetch, niente cookie, niente
     memoria. Legge la pagina che l'utente ha gia' davanti e, solo al
     suo tocco, apre un link. Nessun permesso oltre a www.amazon.it.
   - I DATI VANNO DOPO IL «#»: il browser non manda il frammento a
     nessun server, quindi il PayCode non finisce nei registri di
     barattolo.store. E il link si apre con `noreferrer`: l'indirizzo
     della pagina Amazon (che porta il numero dell'ordine) non arriva a
     Barattolo.
   - NIENTE CHIAVI E NIENTE ACCESSO: l'estensione non sa chi sei.
     L'ordine lo firma Barattolo, sul dispositivo (regola ferrea 2).
   - NON SI INVENTA NIENTE: un dato che non si trova non parte, e
     Barattolo lo chiede nel foglio. Barattolo poi rigiudica ogni campo
     con i suoi giudici (`datiBzDaFrammentoP2P` in miniapp.html).
   - NIENTE LINK AFFILIATI, MAI: il regolamento Amazon Associates li
     vieta dentro le estensioni.
   - LA FONTE BUONA E' IL LINK DEL PDF del PayCode
     (amsfm7t2lf.execute-api.eu-west-1.amazonaws.com/prod/generate-pdf),
     che porta PayCode, importo, scadenza e codice a barre: e' lo stesso
     che Barattolo sa gia' leggere (`linkPdfPayCodeP2P`). Se nella pagina
     non c'e', si cerca il solo PayCode nel testo, accanto alla parola
     «PayCode»: importo e scadenza li scrive chi pubblica.
   ⚠️ COSA C'E' DAVVERO NELLA PAGINA AMAZON NON E' ANCORA VISTO (16 nov
   2026): le due strade sono scritte sul link del PDF che conosciamo e
   sulla mail. Si confermano con un ordine di prova.

   Le funzioni PURE in cima (niente DOM) le prova prove.py in node,
   ritagliandole da qui; il DOM sta tutto in fondo, sotto «IL BOTTONE». */

const BARATTOLO_P2P = 'https://barattolo.store/p2p';
const PDF_HOST = 'amsfm7t2lf.execute-api.eu-west-1.amazonaws.com';
const PDF_PERCORSO = '/prod/generate-pdf';
const MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
              'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];

/* PURA: «479-868-518» da nove cifre con trattini o spazi facoltativi,
   o '' — la gemella di `payCodeP2P` di Barattolo */
function payCodeBz(testo){
  const m = /^(\d{3})[-\s]?(\d{3})[-\s]?(\d{3})$/.exec(String(testo == null ? '' : testo).trim());
  return m ? m[1] + '-' + m[2] + '-' + m[3] : '';
}

/* PURA: l'importo coi centesimi, «39,99», o '' — al piu' due decimali,
   col punto o con la virgola, il € tollerato */
function importoBz(testo){
  const t = String(testo == null ? '' : testo).replace(/\s*€\s*/g, '').trim();
  if (!/^[0-9]{1,6}(?:[.,][0-9]{1,2})?$/.test(t)) return '';
  const n = Number(t.replace(',', '.'));
  return n > 0 ? n.toFixed(2).replace('.', ',') : '';
}

/* PURA: la scadenza del PDF di Amazon — «domenica, 18 ottobre, 14:32
   MET» — in secondi dall'epoca, nell'ora del browser (chi compra su
   amazon.it e' in Italia). L'anno non c'e': si prende quello che mette
   la scadenza fra un giorno fa e cinque giorni da `adesso` (un PayCode
   dura al piu' 72 ore), anche a cavallo di capodanno. 0 se non torna */
function scadeDaPdfBz(testo, adesso){
  const m = /^\s*[a-zà-ù]{3,}\s*,\s*(\d{1,2})\s+([a-zà-ù]{3,})\s*,\s*(\d{1,2}):(\d{2})\b/i.exec(String(testo || ''));
  if (!m) return 0;
  const mese = MESI.indexOf(m[2].toLowerCase());
  const g = Number(m[1]), h = Number(m[3]), mi = Number(m[4]);
  if (mese < 0 || h > 23 || mi > 59) return 0;
  const ora = Number(adesso);
  const anno = new Date(ora * 1000).getFullYear();
  for (const a of [anno, anno + 1, anno - 1]) {
    const d = new Date(a, mese, g, h, mi, 0, 0);
    if (d.getMonth() !== mese || d.getDate() !== g) continue;
    const s = Math.floor(d.getTime() / 1000);
    if (s >= ora - 86400 && s <= ora + 5 * 86400) return s;
  }
  return 0;
}

/* PURA: i dati dal link del PDF del PayCode, o null. Vale solo con host
   e percorso esatti, in https, senza porta ne' credenziali, col PayCode
   buono: come `linkPdfPayCodeP2P` di Barattolo */
function datiDaLinkPdfBz(href, adesso){
  let u;
  try { u = new URL(String(href || '')); } catch(e) { return null; }
  if (u.protocol !== 'https:' || u.hostname !== PDF_HOST || u.port
      || u.username || u.password || u.pathname !== PDF_PERCORSO) return null;
  const pc = payCodeBz(u.searchParams.get('paycode') || '');
  if (!pc) return null;
  const barre = String(u.searchParams.get('barcode') || '').replace(/\s+/g, '');
  return {pc, importo: importoBz(u.searchParams.get('amount') || ''),
          scade: scadeDaPdfBz(u.searchParams.get('expiration_date') || '', adesso),
          barre: /^\d{20,40}$/.test(barre) ? barre : ''};
}

/* PURA: il PayCode dal testo della pagina, solo se sta a due passi
   dalla parola «PayCode» (mai un numero qualunque di nove cifre: la
   pagina di un ordine ne e' piena), o '' */
function payCodeDaTestoBz(testo){
  /* prima delle cifre solo non-cifre, dopo nessuna cifra: mai un pezzo
     di un numero piu' lungo (l'ordine Amazon ne ha 17) */
  const m = /paycode[^0-9]{0,60}?(\d{3}[-\s]?\d{3}[-\s]?\d{3})(?!\d)/i.exec(String(testo || ''));
  return m ? payCodeBz(m[1]) : '';
}

/* PURA: il link che apre Barattolo. I dati dopo il «#», e solo quelli
   che ci sono */
function linkBarattozonBz(d){
  const q = new URLSearchParams();
  if (d && d.pc) q.set('paycode', d.pc.replace(/-/g, ''));
  if (d && d.importo) q.set('importo', d.importo);
  if (d && d.scade) q.set('scade', String(d.scade));
  if (d && d.barre) q.set('barre', d.barre);
  const s = q.toString();
  return BARATTOLO_P2P + '#barattozon' + (s ? '?' + s : '');
}

/* PURA: dai link e dal testo di una pagina, i dati migliori o null.
   Il link del PDF vince sul testo: porta tutto, e l'ha scritto Amazon */
function datiDaPaginaBz(hrefs, testo, adesso){
  for (const h of hrefs || []) {
    const d = datiDaLinkPdfBz(h, adesso);
    if (d) return d;
  }
  const pc = payCodeDaTestoBz(testo);
  return pc ? {pc, importo: '', scade: 0, barre: ''} : null;
}

/* ═══ IL BOTTONE (il solo pezzo che tocca la pagina) ═══════════════
   Un ospite fisso in basso a destra, con un'ombra CHIUSA: il CSS di
   Amazon non lo veste e la pagina non lo legge. Si guarda la pagina
   quando cambia (Amazon disegna a pezzi), con una pausa, e si smette
   appena il bottone c'e', o dopo due minuti. LEGGERA SULLE PAGINE DI
   SEMPRE: il primo controllo e' `textContent` (non ricalcola la
   pagina); `innerText`, il testo che si vede, si chiede solo se la
   parola «PayCode» c'e'. Mai innerHTML con dati della pagina: il
   bottone si costruisce con textContent. */
(function(){
  if (typeof document === 'undefined' || typeof window === 'undefined') return;
  let ospite = null, link = null, sotto = null, attesa = 0;

  function guarda(){
    attesa = 0;
    if (!document.body) return;
    const hrefs = [...document.querySelectorAll('a[href*="' + PDF_HOST + '"]')].map(a => a.href);
    if (!hrefs.length && !/paycode/i.test(document.body.textContent || '')) return;
    const testo = document.body.innerText || '';
    const d = datiDaPaginaBz(hrefs, testo, Math.floor(Date.now() / 1000));
    /* trovato: il bottone c'e' e la pagina non si guarda piu' */
    if (d) { mostra(d); occhio.disconnect(); }
  }

  function mostra(d){
    if (!ospite) {
      ospite = document.createElement('div');
      ospite.setAttribute('data-barattolo', '');
      ospite.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647';
      const ombra = ospite.attachShadow({mode: 'closed'});
      const stile = document.createElement('style');
      stile.textContent =
        'a{display:flex;align-items:center;gap:8px;padding:12px 16px;border-radius:14px;'
        + 'background:#131A26;color:#fff;font:700 15px/1.2 system-ui,sans-serif;text-decoration:none;'
        + 'box-shadow:0 6px 24px rgba(0,0,0,.35);border:2px solid #F7931A}'
        + 'a:hover{background:#1c2638}a:focus-visible{outline:3px solid #F7931A;outline-offset:2px}'
        + 'small{display:block;font-weight:600;font-size:12px;opacity:.8;margin-top:2px}';
      const a = document.createElement('a');
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      const icona = document.createElement('span');
      icona.textContent = '🫙';
      icona.setAttribute('aria-hidden', 'true');
      const parole = document.createElement('span');
      const titolo = document.createElement('span');
      titolo.textContent = 'Pubblica su Barattozon';
      sotto = document.createElement('small');
      parole.append(titolo, sotto);
      a.append(icona, parole);
      ombra.append(stile, a);
      document.documentElement.appendChild(ospite);
      link = a;
    }
    link.href = linkBarattozonBz(d);
    sotto.textContent = 'PayCode ' + d.pc + (d.importo ? ' · ' + d.importo + ' €' : '');
    link.setAttribute('aria-label', 'Pubblica il PayCode ' + d.pc + ' su Barattozon, in una scheda nuova');
  }

  const occhio = new MutationObserver(() => {
    if (!attesa) attesa = setTimeout(guarda, 700);
  });
  occhio.observe(document.documentElement, {childList: true, subtree: true});
  setTimeout(() => occhio.disconnect(), 120000);
  guarda();
})();
