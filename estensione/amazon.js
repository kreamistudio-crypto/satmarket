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
  if (d && d.premio) q.set('premio', String(d.premio));
  const s = q.toString();
  return BARATTOLO_P2P + '#barattozon' + (s ? '?' + s : '');
}

/* PURA: la commissione che chi pubblica offre a chi paga il PayCode
   (17 nov 2026, «deve chiedermi anche quali sono le commissioni
   dell'ordine»): un intero da 0 a 20, il vuoto vale 0, il resto e'
   storto. Su Barattolo diventa il premio del passo 4 col segno meno
   (`premioBz`): chi paga riceve tanti sats in piu' del cambio */
const COMMISSIONE_MAX_BZ = 20;
function commissioneBz(testo){
  const t = String(testo == null ? '' : testo).replace(/\s*%\s*$/, '').trim();
  if (t === '') return {n: 0, storto: false};
  if (!/^\d{1,2}$/.test(t) || Number(t) > COMMISSIONE_MAX_BZ) return {n: 0, storto: true};
  return {n: Number(t), storto: false};
}
function premioBz(commissione){ return commissione > 0 ? -commissione : 0; }

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

/* ═══ COMPRA CON BARATTOZON (17 nov 2026, cantiere compra-con-bz,
   richiesta di Andrea: «prima del carrello o anche nella cassa vorrei il
   pulsante "Compra con Barattozon" e il logo relativo») ═══════════════
   Il percorso INTERO, non solo l'ultimo passo: sulla pagina del prodotto
   e nel carrello un bottone col marchio Barattozon accanto a quelli di
   Amazon, alla cassa un cartello che dice quale pagamento scegliere.
   IL BOTTONE NON SALTA AMAZON: il PayCode nasce solo DOPO l'ordine fatto
   con «paga in contanti», e l'ordine lo fa chi compra, con le sue mani.
   Quindi il bottone fa SOLO il passo innocuo di Amazon che ha accanto —
   «Aggiungi al carrello» sul prodotto, «Procedi all'ordine» nel carrello
   — e MAI «Acquista ora» (con l'1-Click ordinerebbe da solo) ne'
   l'invio dell'ordine: una sentinella di prove.py lo tiene. Alla cassa
   (dal 17 nov, sera) si sceglie il pallino della riga del contanti e
   basta: la conferma del metodo e l'ordine li preme chi compra.
   I selettori sono quelli VISTI sulle pagine vere salvate il 17 nov 2026
   (giro guidato, /mnt/project-files/amazon-contanti/): la cassa no,
   perche' chiede l'accesso; li' si cerca la frase, non un id. */

/* PURA: che pagina di Amazon e', dal solo percorso dell'indirizzo:
   'prodotto' | 'carrello' | 'cassa' | 'grazie' | '' */
function paginaBz(percorso){
  const p = String(percorso || '');
  if (/thankyou/i.test(p)) return 'grazie';
  if (/^\/(?:[^/]+\/)?(?:dp|gp\/product)\/[A-Z0-9]{10}(?:[/?]|$)/.test(p)) return 'prodotto';
  if (/^\/(?:gp\/cart\/view\.html|cart(?:\/smart-wagon)?)(?:[/?]|$)/.test(p)) return 'carrello';
  if (/^\/(?:checkout|gp\/buy)\//.test(p)) return 'cassa';
  return '';
}

/* PURA: la riga del pagamento in contanti, dalla sua frase (Amazon la
   scrive «Paga in Contanti nel Punto Vendita più vicino»; mai una parola
   sola: «contanti» sta anche nelle note legali) */
function rigaContantiBz(testo){
  return /paga\s+in\s+contanti/i.test(String(testo || ''));
}

/* il marchio Barattozon, lettere bianche su trasparente (assets/barattozon.webp
   ridotto a 178x56): DENTRO il file, perche' l'estensione non ha permessi
   per servire immagini alla pagina e non chiede niente a nessuno */
const LOGO_BZ = 'data:image/webp;base64,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';
const BLU_BZ = '#191D29';

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

  /* (17 nov 2026) il riquadro chiede anche LA COMMISSIONE per chi paga
     il PayCode, ogni volta (l'estensione non ricorda niente): il link si
     riscrive a ogni tasto, e una commissione storta lo spegne finche'
     non torna buona. Su Barattolo diventa il premio del passo 4 */
  let dati = null, campo = null, riga = null;

  function aggiorna(){
    const c = commissioneBz(campo.value);
    if (c.storto) {
      link.removeAttribute('href');
      link.setAttribute('aria-disabled', 'true');
      riga.textContent = 'Scrivi un numero intero da 0 a ' + COMMISSIONE_MAX_BZ + '.';
      riga.className = 'storto';
      return;
    }
    link.removeAttribute('aria-disabled');
    link.href = linkBarattozonBz(Object.assign({}, dati, {premio: premioBz(c.n)}));
    riga.textContent = c.n
      ? 'Chi paga il PayCode riceve il ' + c.n + '% di sats in più del cambio.'
      : 'Nessuna commissione: chi paga riceve i sats al cambio pieno.';
    riga.className = '';
  }

  function mostra(d){
    if (!ospite) {
      ospite = document.createElement('div');
      ospite.setAttribute('data-barattolo', '');
      ospite.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:320px';
      const ombra = ospite.attachShadow({mode: 'closed'});
      const stile = document.createElement('style');
      stile.textContent =
        'section{background:' + BLU_BZ + ';color:#fff;border:2px solid #F7931A;border-radius:14px;padding:12px 14px;'
        + 'box-shadow:0 6px 24px rgba(0,0,0,.35);font:13px/1.4 system-ui,sans-serif}'
        + 'section>img{height:28px;width:auto;display:block;margin-bottom:4px}'
        + 'small{display:block;font-weight:600;font-size:12px;opacity:.8}'
        + 'label{display:flex;align-items:center;gap:8px;margin:10px 0 2px;font-weight:700}'
        + 'input{width:52px;padding:6px 8px;border-radius:8px;border:1px solid #F7931A;background:#fff;color:#111;'
        + 'font:700 15px system-ui,sans-serif;text-align:center}'
        + 'p{margin:2px 0 10px;font-size:12px;opacity:.85}p.storto{color:#ff9b8a;opacity:1}'
        + 'a{display:block;text-align:center;padding:10px 14px;border-radius:20px;background:#F7931A;color:' + BLU_BZ + ';'
        + 'font:700 15px/1.2 system-ui,sans-serif;text-decoration:none;cursor:pointer}'
        + 'a:hover{background:#ffa733}a:focus-visible{outline:3px solid #fff;outline-offset:2px}'
        + 'a[aria-disabled]{opacity:.45;cursor:not-allowed}';
      const s = document.createElement('section');
      const icona = document.createElement('img');
      icona.src = LOGO_BZ;
      icona.alt = 'Barattozon';
      sotto = document.createElement('small');
      const etichetta = document.createElement('label');
      const parola = document.createElement('span');
      parola.textContent = 'Commissione a chi paga';
      campo = document.createElement('input');
      campo.type = 'text';
      campo.inputMode = 'numeric';
      campo.maxLength = 3;
      campo.placeholder = '0';
      campo.setAttribute('aria-label', 'Commissione a chi paga il PayCode, in percento da 0 a ' + COMMISSIONE_MAX_BZ);
      const pc = document.createElement('span');
      pc.textContent = '%';
      etichetta.append(parola, campo, pc);
      riga = document.createElement('p');
      riga.setAttribute('aria-live', 'polite');
      const a = document.createElement('a');
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = 'Pubblica su Barattozon';
      /* un link spento non apre niente, nemmeno col tocco */
      a.addEventListener('click', ev => { if (a.hasAttribute('aria-disabled')) ev.preventDefault(); });
      campo.addEventListener('input', aggiorna);
      s.append(icona, sotto, etichetta, riga, a);
      ombra.append(stile, s);
      document.documentElement.appendChild(ospite);
      link = a;
    }
    dati = d;
    sotto.textContent = 'PayCode ' + d.pc + (d.importo ? ' · ' + d.importo + ' €' : '');
    link.setAttribute('aria-label', 'Pubblica il PayCode ' + d.pc + ' su Barattozon, in una scheda nuova');
    aggiorna();
  }

  const occhio = new MutationObserver(() => {
    if (!attesa) attesa = setTimeout(guarda, 700);
  });
  occhio.observe(document.documentElement, {childList: true, subtree: true});
  setTimeout(() => occhio.disconnect(), 120000);
  guarda();
})();

/* ═══ I BOTTONI «COMPRA CON BARATTOZON» (il pezzo che li disegna) ═════
   Ognuno nel suo ospite con l'ombra CHIUSA, come il bottone del PayCode.
   Sul prodotto e nel carrello l'ospite va SUBITO SOTTO il bottone di
   Amazon che fa il passo (si vede accanto, si capisce cosa fara'); alla
   cassa un cartello fisso in basso a destra, che si chiude con la ×.
   Amazon ridisegna a pezzi: si riguarda alle modifiche, con una pausa,
   per due minuti, e un ospite gia' messo non si rimette. */
(function(){
  if (typeof document === 'undefined' || typeof window === 'undefined') return;
  const tipo = paginaBz(location.pathname);
  if (!tipo || tipo === 'grazie') return;
  let messo = null, attesa = 0, segnata = null, scelto = false, primoPasso = null;

  function vesti(ombra, extra){
    const stile = document.createElement('style');
    stile.textContent =
      ':host{all:initial}'
      + 'button{all:unset;box-sizing:border-box;width:100%;display:flex;align-items:center;justify-content:center;'
      + 'gap:8px;min-height:40px;padding:6px 14px;border-radius:20px;background:' + BLU_BZ + ';color:#fff;'
      + 'font:700 14px/1.2 system-ui,sans-serif;cursor:pointer;border:2px solid #F7931A}'
      + 'button:hover{background:#262c3d}button:focus-visible{outline:3px solid #F7931A;outline-offset:2px}'
      + 'img{height:24px;width:auto;display:block}'
      + 'p{margin:6px 2px 0;font:12px/1.35 system-ui,sans-serif;color:#565959;text-align:center}'
      + (extra || '');
    ombra.append(stile);
  }

  function marchio(){
    const i = document.createElement('img');
    i.src = LOGO_BZ;
    i.alt = 'Barattozon';
    return i;
  }

  /* prodotto e carrello: il bottone sotto quello di Amazon, che al tocco
     preme proprio quello (mai un altro) */
  function bottone(dopo, premi, nota){
    const ospite = document.createElement('div');
    ospite.setAttribute('data-barattolo', 'compra');
    ospite.style.cssText = 'display:block;margin:8px 0 4px';
    const ombra = ospite.attachShadow({mode: 'closed'});
    vesti(ombra);
    const b = document.createElement('button');
    b.type = 'button';
    const parole = document.createElement('span');
    parole.textContent = 'Compra con';
    b.append(parole, marchio());
    b.setAttribute('aria-label', 'Compra con Barattozon: ' + nota);
    b.addEventListener('click', () => { const x = premi(); if (x) x.click(); });
    const p = document.createElement('p');
    p.textContent = nota;
    ombra.append(b, p);
    dopo.insertAdjacentElement('afterend', ospite);
    return ospite;
  }

  /* la cassa: il cartello coi tre passi, e la riga del contanti segnata */
  function cartello(){
    const ospite = document.createElement('div');
    ospite.setAttribute('data-barattolo', 'cassa');
    ospite.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:330px';
    const ombra = ospite.attachShadow({mode: 'closed'});
    vesti(ombra,
      'section{position:relative;background:' + BLU_BZ + ';color:#fff;border:2px solid #F7931A;border-radius:14px;'
      + 'padding:12px 14px 12px;box-shadow:0 6px 24px rgba(0,0,0,.35);font:13px/1.4 system-ui,sans-serif}'
      + 'section img{height:26px;margin-bottom:6px}'
      + 'b{font-weight:700}ol{margin:4px 0 0;padding-left:20px}li{margin:3px 0}'
      + '.chiudi{all:unset;position:absolute;top:6px;right:8px;width:24px;height:24px;line-height:24px;'
      + 'text-align:center;cursor:pointer;font-size:18px;border-radius:12px}.chiudi:hover{background:#262c3d}');
    const s = document.createElement('section');
    s.setAttribute('role', 'note');
    s.setAttribute('aria-label', 'Compra con Barattozon: come pagare');
    const x = document.createElement('button');
    x.className = 'chiudi';
    x.type = 'button';
    x.textContent = '×';
    x.setAttribute('aria-label', 'Chiudi');
    x.addEventListener('click', () => ospite.remove());
    const titolo = document.createElement('b');
    titolo.textContent = 'Compra con Barattozon, in 3 passi';
    const ol = document.createElement('ol');
    for (const r of ['Come pagamento scegli «Paga in Contanti nel Punto Vendita più vicino» (la prima volta sta in «Aggiungi una modalità di pagamento»).',
                     'Completa l\'ordine: Amazon ti dà un PayCode, valido 72 ore.',
                     'Sulla pagina del PayCode tocca «Pubblica su Barattozon»: chi compra i tuoi sats lo paga in contanti.']) {
      const li = document.createElement('li');
      li.textContent = r;
      ol.append(li);
      if (!primoPasso) primoPasso = li;
    }
    s.append(x, marchio(), titolo, ol);
    ombra.append(s);
    document.documentElement.appendChild(ospite);
    return ospite;
  }

  /* la riga del contanti: la frase piu' piccola che la contiene, e il
     suo contenitore; il contorno, e (17 nov 2026, «barattozon deve
     inserire da solo come metodo di pagamento i contanti») la SCELTA:
     si preme il SOLO pallino (`input[type=radio]`) che sta dentro quella
     riga, una volta per pagina e solo se non e' gia' scelto. Mai altro:
     la conferma del metodo e l'ordine restano a chi compra */
  function scegliContanti(r){
    if (scelto) return;
    /* il pallino della label, o l'UNICO della riga: con due pallini nella
       stessa riga non si sa quale sia, e non si preme niente */
    const tutti = r.querySelectorAll('input[type="radio"]');
    const pallino = (r.control && r.control.type === 'radio') ? r.control : (tutti.length === 1 ? tutti[0] : null);
    if (!pallino || pallino.disabled) return;
    scelto = true;
    if (!pallino.checked) pallino.click();
    if (primoPasso) primoPasso.textContent = '✓ Ho scelto io «Paga in Contanti nel Punto Vendita più vicino»: controlla e conferma il metodo di pagamento.';
  }

  function segnaContanti(){
    if (segnata && document.contains(segnata)) { scegliContanti(segnata); return; }
    const giro = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = giro.nextNode(); n; n = giro.nextNode()) {
      if (!rigaContantiBz(n.nodeValue)) continue;
      const el = n.parentElement;
      if (!el || el.closest('[data-barattolo]')) continue;
      const riga = el.closest('label, li, [role="radio"], .a-row') || el;
      riga.style.outline = '3px solid #F7931A';
      riga.style.outlineOffset = '3px';
      riga.style.borderRadius = '6px';
      segnata = riga;
      scegliContanti(riga);
      return;
    }
  }

  function guarda(){
    attesa = 0;
    if (!document.body) return;
    if (tipo === 'cassa') {
      if (!messo) messo = cartello();
      segnaContanti();
      return;
    }
    if (messo && document.contains(messo)) return;
    if (tipo === 'prodotto') {
      const atc = document.getElementById('add-to-cart-button');
      const casa = atc && (atc.closest('.a-button') || atc);
      if (casa) messo = bottone(casa, () => document.getElementById('add-to-cart-button'),
        'Lo metti nel carrello, poi alla cassa paghi in contanti con un PayCode che salda un altro utente: tu paghi in sats.');
    } else if (tipo === 'carrello') {
      const ptc = document.getElementById('sc-buy-box-ptc-button');
      if (ptc) messo = bottone(ptc, () => document.querySelector('input[name="proceedToRetailCheckout"]'),
        'Vai alla cassa: lì scegli «Paga in contanti», e il PayCode lo pubblichi su Barattozon.');
    }
  }

  const occhio = new MutationObserver(() => {
    if (!attesa) attesa = setTimeout(guarda, 700);
  });
  occhio.observe(document.documentElement, {childList: true, subtree: true});
  setTimeout(() => occhio.disconnect(), 120000);
  guarda();
})();
