# Studio: «Ristoranti e menu su Barattolo» (24 settembre 2026)

Sola lettura, nessuna modifica al codice, nessun cantiere aperto. Base:
`origin/main` a `782b70e` (i numeri di riga qui sotto sono di quel
commit; i NOMI di funzioni, tabelle e leve sono la cosa da cercare, le
righe si spostano). Il VPS, il nodo e il relay non sono stati toccati.
Fatti esterni verificati sulle fonti in fondo, lette il 24 set 2026;
quel che NON ho potuto verificare da qui è scritto come tale.

**L'idea di Alan.** I ristoratori pubblicano il loro menu su Nostr —
come fa uno sviluppatore su Nostr, «alla DoorDash» — e Barattolo lo
mostra in un'area dedicata con un pin sulla mappa; i clienti ordinano e
pagano in sats; il ristorante diventa anche un punto di ritiro dei
pacchi; fee diversa, e forse senza deposito di garanzia, perché sul cibo
si paga direttamente l'esercente.

**La risposta corta.** Un menu su Barattolo esiste GIÀ per tre quarti:
un piatto è un annuncio con consegna «ritiro», il negozio è il
ristorante, il carrello per venditore è il vassoio, il foglio di
pagamento e la notifica «Hai venduto!» sono quelli di sempre, e ogni
piatto finisce su Nostr da solo come `kind 30402` con `delivery pickup`
(`evento_annuncio`, `tag_commercio`). Quel che MANCA è tutto ciò che fa
di un mercatino un asporto: **il momento** — la fascia di ritiro scelta
da chi compra, l'accettazione del ristorante entro pochi minuti,
«pronto alle 13:15» — più gli orari di apertura e il sold-out a fine
giornata. Sul pagamento, la strada «sats direttamente all'esercente»
non esiste nel codice (ogni ordine passa da `crea_invoice_escrow`) e
costa più di quel che rende; quella che regge è **il deposito che dura
un pranzo**: si paga come sempre nella cassaforte, il ristorante
accetta, e al banco il compratore rivela il suo codice e i sats escono
subito — un gesto umano, mai un timer, come vuole il disarmo. Il pin
sulla mappa non si fa con un ristorante solo (è la stessa condizione
scritta per i punti di ritiro: «quando saranno SPARSI»). E il
ristorante-punto-di-ritiro non è un'idea nuova: **è l'origine stessa
della rete di punti di Barattolo**, nata ad agosto da un ristoratore
di Milano, col catalogo `PUNTI_BARATTOLO` ancora vuoto che aspetta il
primo codice negozio. **Raccomandazione: un pilota con UN ristorante
(quello che si è già offerto, se è ancora lì), solo asporto, tre
cantieri piccoli in quest'ordine — la fascia e l'accettazione, il
codice al banco, la card «🍽️ Da asporto» — con la fee a zero come il
resto del rodaggio e la leva sua dichiarata ma spenta.** Il menu «che
nasce su Nostr» resta la vetrina, non l'ordine: per incassare serve un
venditore di Barattolo.

## Come leggere questo file

- Le cinque domande di Andrea hanno una sezione ciascuna (1-5), più la
  raccomandazione in dieci righe (6) e le fonti.
- «VERIFICATO» = letto sulla documentazione ufficiale o sulla spec.
  «NEL CODICE» = con nome e riga in `server.py` o `miniapp.html`.
  «A VERBALE» = decisione già scritta in `docs/CANTIERI.md` o
  `docs/ARCHITETTURA.md`, col NOME della voce, da non contraddire.
  «DA DECIDERE» = una scelta di Andrea, con le due strade accanto.

## 1. Come modellano menu e ordini gli altri, e cosa vale la pena riprendere

### 1a. DoorDash e Uber Eats (VERIFICATO sulle API per i merchant)

I due modelli sono la stessa cosa detta in due dialetti, e conviene
impararla una volta:

- **Il menu è un albero a quattro piani**: menu → categorie → piatti →
  gruppi di modificatori con le loro opzioni. Uber usa la stessa
  entità «item» sia per il piatto sia per il topping (un'opzione È un
  item, con prezzo e disponibilità sue); DoorDash ha `ItemExtra` e
  `ItemExtraOption`. I gruppi hanno **min/max di scelte distinte**
  (`min_num_options`/`max_num_options` da DoorDash,
  `quantity_info.min_permitted`/`max_permitted` da Uber), quante sono
  gratis, e da che pezzo in poi si paga (`charge_above`). Niente
  annidamento sotto il selettore di quantità.
- **Gli orari stanno su tre livelli**: negozio (per giorno della
  settimana, più le eccezioni per data), menu (Uber: «gli orari del
  negozio sono l'UNIONE degli orari dei suoi menu», cioè il menu del
  pranzo e quello della cena sono due menu), e singolo piatto (DoorDash:
  «vale il più stretto dei due»; sotto i 30 minuti il menu viene
  rifiutato). Un giorno chiuso si OMETTE dall'elenco, non si scrive.
- **Il sold-out è un fatto separato dal menu**: DoorDash ha
  `is_suspended` sul piatto e sull'opzione, con endpoint dedicati e la
  regola sul tablet «esaurito fino a fine giornata, per quattro ore, o
  per sempre»; Uber marca «out of stock» con un periodo. La
  certificazione DoorDash pretende di vedere il «86'ing» (il gergo
  della cucina per «finito») del piatto e dell'opzione, e almeno un
  aggiornamento del menu al giorno.
- **L'ordine arriva pagato e va ACCETTATO in pochi minuti**: DoorDash
  «se non confermi entro 3-8 minuti l'ordine è un fallimento per
  timeout», Uber «devi accettare o rifiutare entro 11,5 minuti, sennò
  scade e si annulla da solo», con una telefonata automatica dopo 90
  secondi di silenzio. Rifiutare ha un motivo a catalogo (negozio
  chiuso, piatto finito, cucina piena, POS spento, ...). Esiste
  l'auto-accettazione (DoorDash, dal tablet).
- **Il tempo di preparazione lo dice il ristorante ACCETTANDO**:
  DoorDash `prep_time` (in UTC, «non ricopiare la nostra stima»), Uber
  `pickup_time` («quando l'ordine sarà pronto, Unix timestamp»); da lì
  il cliente legge «pronto alle 13:15» (Uber
  `estimated_ready_for_pickup_at`). Il tablet lo cambia a scatti di
  cinque minuti.
- **Ritiro e consegna sono lo stesso ordine con un tipo**
  (`is_pickup`, `PICK_UP`/`DELIVERY_BY_UBER`), e gli ordini
  PROGRAMMATI vengono trattenuti dalla piattaforma e sparati al
  ristorante solo quando diventano «come un ASAP».
- **Dopo l'accettazione**: «pronto» (`order_ready_for_pickup`),
  rilascio automatico quando il cliente è vicino (geofence), modifica
  (togli/sostituisci un piatto, rimborso parziale), annullamento con
  motivo. Un merchant che annulla NON è rimborsato; troppe cancellazioni
  spengono il negozio.

**Cosa vale la pena riprendere** (in ordine di peso per un asporto):
l'accettazione con scadenza e motivo; il tempo di preparazione DETTO dal
ristorante al momento in cui accetta, che è ciò che genera «pronto
alle»; il sold-out come gesto a sé, con «fino a fine giornata» come
default; gli orari per giorno con le eccezioni. **Cosa NON riprendere
ora**: l'albero dei modificatori (min/max, gratis fino a N): è la cosa
più cara e la si aggira con un annuncio per variante e la nota del
compratore, vedi 2b; il geofence; la consegna a domicilio, che vuole
rider e non è la domanda.

### 1b. I marketplace Nostr (VERIFICATO sulle spec e sui repo)

- **NIP-15** (kind 30017 stall, 30018 product, checkout via DM kind 4
  con tre messaggi: ordine, richiesta di pagamento, stato) porta oggi
  nell'intestazione la riga **«unrecommended: too complicated, try
  NIP-99 instead»**. Non è cancellato dal README, ma nessuno lo
  costruisce più: Plebeian Market ha fatto il «FINAL pivot to NIP-99» a
  fine 2025 e il rilancio 2.0 a gennaio 2026; l'estensione LNbits
  «Nostr Market» resta NIP-15 e la richiesta di parlare NIP-99 (issue
  #144, dic 2025) è chiusa senza risposta. Il nostro `importa_nostr.py`
  legge ancora 30018 e 30017 (`interroga`, riga 209) — giusto per il
  vecchio parco, ma non è dove si va.
- **NIP-99** (kind 30402) ha `title`, `summary`, `price` con valuta ISO
  (e una frequenza opzionale per gli affitti), `location`, `status`
  active/sold, `t`, `image`, `g` geohash. **Non ha** varianti, quantità,
  spedizione, orari, né un flusso d'ordine: «lascia indefinito tutto
  ciò che viene dopo l'annuncio» (Nostr Compass, lug 2026). Noi ci
  abbiamo già messo sopra `delivery`, `condition` e `stock`
  (`tag_commercio`, 44972), scritti anche in chiaro nel content per i
  client che non li conoscono.
- **Gamma Markets** (spec in bozza, `GammaMarkets/market-spec`, non
  sottoposta come NIP; la usano Shopstr, Plebeian, Cypher, Conduit)
  colma il buco: 30402 esteso con `shipping_option`, `stock`, `type`,
  `visibility`; kind 30406 per le tariffe di spedizione; kind 30405
  collezioni; ordini in **NIP-17** (kind 16 dentro la busta) con
  tipo 1 ordine, 2 richiesta di pagamento, 3 stato
  (pending/confirmed/processing/completed/cancelled), 4 spedizione;
  kind 17 ricevuta; 31555 recensioni. Ha un fork
  (`OpenMarketsFoundation/specification`) con gli stessi kind. È il
  dialetto in cui un ordine «vive su Nostr» oggi; ma anche lì niente
  orari, fasce, accettazione a tempo, modificatori.
- **Menu di ristoranti su Nostr, nel 2026: quasi niente.** L'unico
  progetto a catalogo è **Kartapio** (`vstabile/kartapio`, «a
  decentralized food delivery app built on Nostr», SvelteKit): **7
  commit, l'ultimo il 27 feb 2025**, README di due righe, l'unico kind
  visibile è una lista 10042; alla hackathon bitcoin++ Floripa 2025 è
  piaciuto ma non ha vinto. Quali kind usi per il menu e per l'ordine
  non è documentato: andrebbe letto il codice. **Milk Market / Self-
  Sown** (dal team di Shopstr) è cibo, ma dei PRODUTTORI (latte crudo,
  uova, miele), con NIP-99/17 e «cash al ritiro locale». **BitFood**
  (v1.4.1 del 29 apr 2026, Brasile/USA/Messico) è consegna cibo SOLO
  Lightning con tre app e limiti per livello — ma non è su Nostr.
  Zap Cooking sono ricette. Nessun NIP, bozza o convenzione per «menu»,
  «modifier», «orari» o «ritiro» sul 30402; nessun post 2025-2026 di
  uno sviluppatore che pubblichi un menu come eventi. ⚠️ **Da chiedere
  ad Alan quale progetto intendeva**: se è Kartapio, è fermo da
  diciannove mesi; se è un altro, il link vale più di questa pagina.

**Cosa vale la pena riprendere**: NIP-99 come base (già nostro); i tag
`stock` e `delivery` che già scriviamo; e, il giorno che un ordine
dovesse viaggiare su Nostr, il vocabolario degli stati di Gamma
(kind 16 tipo 3) invece di inventarne uno. **Cosa non riprendere**:
NIP-15 (morto), e l'idea che «il menu nasce su Nostr e Barattolo lo
mostra» basti a fare un ordine — vedi 2c.

## 2. Cosa del nostro codice si riusa, e cosa manca

### 2a. Si riusa così com'è (NEL CODICE)

| Pezzo dell'asporto | Cosa c'è già | Dove |
|---|---|---|
| Il ristorante | il **negozio** del venditore: codice pubblico stabile, pagina `/negozio/{chi}`, widget | `nuovo_codice_negozio`, `renderNegozio` (`miniapp.html:17830`) |
| Il piatto | un **annuncio** in «Alimenti e bevande» (condizione non chiesta: `CATEGORIE_SENZA_CONDIZIONE`, 17822), `consegna='ritiro'`, foto, prezzo in euro o sats, `quantita` come scorta | `MODALITA_CONSEGNA` (18000), `annunci.quantita` |
| Il menu su Nostr | ogni annuncio è un `kind 30402` con `delivery pickup`, `location`=zona, `t`=alimenti, `stock`, `price` in EUR: **il menu su Nostr viene gratis**, un evento per piatto | `evento_annuncio` (45006), `tag_commercio` (44972), `annuncio_su_nostr` (45394) |
| Il vassoio | il **carrello per venditore**, fino a 8 annunci diversi con quantità (`MAX_PACCO`=`MAX_RIGHE_SET`), che nasce ordine unico con righe | `setScelte`/`paccoDati` (`miniapp.html:20248-20266`), `_compra_set` (29886), `ordine_righe` (4492) |
| Il conto e la cassa | preventivo dal server, invoice LNbits con scadenza 15 min, foglio di pagamento, NWC, QR, stadio «in pagamento» | `preventivo_ordine` (30828), `crea_invoice_escrow` (8607), `INVOICE_EXPIRY` (8463), `renderAcquisto`, `stadio_pagamento` (10397) |
| «Hai venduto!» | la notifica al venditore all'incasso, Telegram o DM Nostr NIP-17, e agli admin | `_incassa_ordine` (32997, testo a 33127), `notifica` (13223) |
| Il ritiro | da `locked` il compratore ha già «✅ L'ho ritirato — libera i sats»; il ritiro non ha nessun timer che sposti sats; promemoria alle due parti | A VERBALE «IL RITIRO SI CONFERMA DA 'LOCKED'» (ARCH 1274), `sollecita_ritiri_fermi` (51031) |
| Esaurito | «⏸ Segna esaurito» su un annuncio, che lo lascia in vetrina ma non si compra | `POST /api/listings/{id}/quantita`, A VERBALE ARCH «Segna esaurito» |
| Chiuso per ferie | il negozio in ferie: annunci visibili, acquisto bloccato IN LETTURA, rientro automatico | `in_ferie` (26914), `guardia_ferie` (13056), CANTIERI «Il negozio in ferie 🌴» |
| La nota al venditore | «la taglia, il numero, la variante»: la casella libera dell'ordine | `POST /api/orders/{id}/nota` |
| Il rimborso | il rimborso al compratore esiste (lo usa la disputa) | `_rimborsa_compratore` (48424), `risolvi_disputa` (48584) |
| L'area tematica | i **Consigliati**: una card nella fila delle categorie più una pagina, con un catalogo nel codice acceso da un comando del bot | CANTIERI «I Consigliati», `RACCONTI`/`SLUG_SPONSOR`, `/sponsor` |
| Il codice al banco | tre precedenti di codice coniato dal server e rivelato da una persona: la busta di consegna, il codice del punto Barattolo, la rivelazione del digitale | `busta_codice`, `comando_punti` (14701), `rivelaContenuto` (`miniapp.html:34750`) |

### 2b. Manca, e quanto pesa

1. **La fascia di ritiro.** Non esiste nessun campo «quando». Il
   precedente più vicino sono i SERVIZI: il venditore PROPONE un
   appuntamento e il compratore lo CONFERMA (`proponi_appuntamento`
   33450, `appuntamento_ammesso` 26885) — il verso giusto per una
   lezione, quello sbagliato per un panino, dove è chi compra che dice
   «alle 13» scegliendo da fasce che il ristorante ha dichiarato. Serve
   una colonna sull'ordine (`fascia_ritiro`, un timestamp) scritta in
   cassa, e le fasce del ristorante (un testo semplice tipo «12:00-14:30
   ogni 15 min», al calco di `orari` del catalogo punti; niente albero
   di orari alla DoorDash per un pilota). **A VERBALE, e si rispetta**:
   «mai un valore nuovo di `consegna_scelta`» — la fascia è un
   MODIFICATORE della via ritiro, come `via_punto`, non una via nuova.
2. **L'accettazione rapida con scadenza.** Oggi «il venditore accetta»
   non esiste: l'ordine nasce pagato, va a `locked`, il venditore
   spedisce. Il precedente è l'OFFERTA (`offerte`, `rispondi_offerta`
   28847, `ORE_RISPOSTA_OFFERTA`=48), ma gira al contrario: si accetta
   PRIMA del pagamento e chi accetta non blocca niente («vince chi paga
   per primo»). Per l'asporto l'accettazione arriva DOPO il pagamento,
   entro minuti e non ore, e dice il tempo di preparazione. Serve: due
   colonne (`accettato_il`, `pronto_alle`), una rotta del venditore
   «✅ Lo preparo / ❌ Non posso» con motivo a catalogo (finito, chiusi,
   troppo pieno — le tre ragioni vere delle API), la scadenza
   (`MINUTI_ACCETTAZIONE_RISTORO`, 10 come Uber), e il testo per il
   compratore. ⚠️ **NESSUNO STATO NUOVO** (regola ferrea 4): si resta in
   `locked` con le colonne, come i servizi hanno fatto — «pronto alle
   13:15» è uno STADIO derivato, il calco di `stadio_pagamento`.
3. **Il rifiuto e il mancato-accettato rimborsano.** Oggi
   `annulla_ordine` (49517) vale solo da `creato` (non pagato), e da
   `locked` la disputa la apre SOLO il compratore (`apri_disputa`
   48874). Il ristorante che dice «finito» non ha una strada, e
   nemmeno il compratore che aspetta un'accettazione che non arriva.
   Il rimborso c'è (`_rimborsa_compratore`): mancano i due GESTI che lo
   chiamano. ⚠️ **E IL DISARMO GOVERNA ANCHE QUI** (A VERBALE «IL
   DISARMO DELL'AUTO-SBLOCCO», ARCH 1290: «NESSUN TIMER SPOSTA SATS DA
   UNA PARTE A UN'ALTRA»): Uber annulla da solo a 11,5 minuti, noi NO —
   il timer non rimborsa, **abilita un bottone**: allo scadere il
   compratore vede «⏱ Non hanno risposto — riprendi i sats», e i sats
   si muovono col suo tocco. Stessa forma della rete di punti, dove il
   promemoria bussa e la persona decide.
4. **Il rilascio al banco.** Regola ferrea 5: «consegnato» lo scrive
   solo il compratore, e dall'ago 2026 a mano non lo scrive più
   nessuno; sul digitale «la scrive la rivelazione del codice, che è un
   gesto del compratore». L'asporto è il caso digitale con un banco in
   mezzo: il compratore ha un codice di sei caratteri coniato dal server
   (il calco esatto del codice del punto Barattolo, che il venditore
   non vede mai), lo mostra al banco, il ristorante lo digita nella
   sua coda — e quel gesto, che senza la rivelazione non può avvenire,
   sblocca i sats. È un rilascio da `locked` (esiste già: il ritiro lo
   fa) innescato da un fatto che solo il compratore può produrre.
   **DA DECIDERE** (Andrea): se questa lettura della regola 5 va bene —
   il precedente del digitale dice di sì — oppure se resta il solo
   bottone del compratore «L'ho ritirato», che c'è già e costa zero ma
   lascia al ristorante l'attesa di un tocco altrui.
5. **Gli orari di apertura** non esistono da nessuna parte (l'unico
   «orari» è la stringa del catalogo punti, 18034). Per il pilota
   basta: le fasce dichiarate (punto 1) valgono come orari, e fuori
   fascia il piatto non si compra — un gate IN LETTURA come le ferie,
   che è il patto di casa (`guardia_ferie`). Gli orari per giorno con
   le eccezioni si rimandano.
6. **La disponibilità in tempo reale.** «Segna esaurito» c'è, ma è
   «per sempre finché non lo riaccendi»; ai ristoranti serve «fino a
   fine giornata» come default (DoorDash) — una colonna `esaurito_fino`
   e la ronda che la scade. Piccolo, e va nel secondo giro.
7. **Varianti e aggiunte.** Non esistono: la tabella `annunci` è
   piatta, e l'importatore dei negozi collegati SALTA i prodotti con
   più varianti («le varianti sono un cantiere loro»,
   `importa_negozio.py:240-247`). La strada già percorsa dai negozi
   collegati è **un annuncio per variante** (A VERBALE, «Varianti e
   prodotti digitali dai negozi collegati»): «Margherita», «Margherita senza
   glutine» sono due piatti; le aggiunte vanno nella nota del
   compratore. Basta per un pilota; l'albero min/max è il cantiere più
   caro di tutti e si rimanda finché un ristorante non lo chiede con un
   menu in mano.
8. **Il ristorante al banco ha bisogno di una CODA**, non di un feed:
   gli ordini di oggi in ordine di fascia, con codice atteso, un tocco
   per «accetto» e un campo per il codice. Il precedente è la coda del
   titolare del punto (`GET /api/punto/pacchi`, 34305, e `punto/preso`).
9. **La mappa e il pin**: nessuna mappa grafica esiste (né Leaflet, né
   tile, né geolocalizzazione: `lat`/`lon` vengono dal CSV dei comuni,
   `carica_comuni` 16293, e servono agli avvisi di ricerca con
   `distanza_km` 16635). Il «varco mappa» (`miniapp.html:21529`) è un
   contenitore promesso al tracking via API corrieri. **A VERBALE**
   («LA MAPPA HA LA SUA CONDIZIONE», ARCH 18635): la mappa si fa
   «quando i punti saranno SPARSI», e con uno solo «non è una mappa: è
   una voce nell'elenco». Per i ristoranti vale identico: la card «🍽️
   Da asporto» con l'elenco per comune, e la mappa quando ci saranno
   dieci ristoranti in tre città — non prima, e sarà lo stesso cantiere
   dei punti, non uno suo.

### 2c. Il menu «che nasce su Nostr»: vetrina sì, ordine no (per ora)

Il verso di Alan è: il ristoratore pubblica su Nostr, Barattolo lo
mostra. La lettura c'è (`importa_nostr.py` legge 30402 e 30018 dai
relay di `RELAY_NOSTR_IMPORT`; `importa_nostr_periodico` 53357 ogni
ora), ma **a leva spenta** (`IMPORT_NOSTR_APERTO=False`, che si accende
solo dal VPS con la procedura anti-anello di PRODUZIONE). E un ordine ha
bisogno di un venditore che possa RICEVERE — un'invoice o un Lightning
address per il payout, un canale per la notifica — e di qualcuno che
risponda di una disputa. Le identità solo-Nostr esistono (`notifica`
tratta `tg_id < 0` come Nostr, riga 13248; il login con firma è nella
scala approvata), quindi la strada è aperta per costruzione, ma non
provata: un ristoratore che sta solo su Nostr oggi finisce in vetrina
con un link a lui, non in cassa. **Per il pilota il ristorante è un
venditore di Barattolo che ha ANCHE Nostr**, e il suo menu esce su
Nostr da noi: è il verso che funziona oggi senza scrivere una riga.

## 3. Il pagamento: tre strade

Il fatto da cui partire, NEL CODICE: **non esiste nessun acquisto senza
deposito di garanzia**. Ogni ordine passa da `crea_invoice_escrow`;
«Compra subito» con NWC paga la cassaforte; il PayCode è il codice
Amazon di Barattozon, un'altra cosa. Lo studio Bolt Card l'ha già
scritto: «il deposito resta in mezzo per costruzione, anche se dura un
minuto — il tocco non paga il venditore, riempie la cassaforte».

### A. Paga subito con deposito, come nel mercatino

- **Come**: identico a oggi. `locked` all'incasso, il ristorante
  prepara, al banco il compratore libera i sats (col suo bottone o col
  codice di 2b.4), la fee esce da `netto_venditore` (10562).
- **Pro**: zero codice sul percorso dei soldi, che è l'unico posto dove
  un difetto costa sats veri; disputa, rimborso, XP, recensioni,
  classifica, tutto già in piedi; il compratore è protetto se il piatto
  non c'è.
- **Contro**: il ristorante incassa quando il compratore TOCCA, e un
  cliente che esce col sacchetto senza toccare lascia i sats fermi
  (poi `sollecita_ritiri_fermi` bussa, ma ai due, e senza scadenza). Per
  un ordine da 8 € è un attrito che DoorDash non ha (là il merchant è
  pagato anche se il cliente non ritira).
- **Come lo curano gli altri**: Uber «tieni l'ordine 60 minuti, poi
  segnalo ritirato: il cliente paga e tu sei pagato»; DoorDash «il
  cliente non può chiedere il rimborso, non devi fare niente». Da noi
  l'equivalente sarebbe un timer che sposta sats verso il venditore:
  **vietato dal disarmo**. Il no-show da noi si chiude con un gesto:
  quello del compratore, o del moderatore in disputa — e da `locked` la
  disputa la apre solo il compratore. Il ristorante col sacchetto
  freddo oggi non ha un bottone: nel pilota lo chiama Andrea (un
  ristorante, pochi ordini), nel secondo giro serve «🥡 Non ritirato»
  del venditore che apre la revisione. È lo stesso buco già a verbale
  per i punti («risponde il VENDITORE»), e qui il venditore è il
  ristorante: coerente.

### B. Paga subito senza deposito: sats direttamente al ristorante, con la fee di Barattolo

Due forme, e nessuna delle due è «gratis»:

- **B1, la fattura è del ristorante** (il suo Lightning address o la
  sua NWC), Barattolo non tocca i sats. Lightning non ha lo split
  atomico: se i sats non passano da noi, la fee si incassa a parte — una
  seconda fattura al ristorante (a fine mese, o per ordine), cioè un
  credito da riscuotere, con la sua ronda e i suoi insoluti. In cambio
  si perde TUTTO ciò che l'escrow dà: niente rimborso se il piatto non
  c'è (i sats sono già dal ristorante, e «rimborso dal venditore» non
  esiste come flusso), niente disputa, e il compratore non è protetto
  proprio nell'unico caso che gli importa. È anche un percorso dei
  soldi NUOVO, il terzo dopo cassaforte e P2P — l'audit del 19 set ha
  appena finito di mettere in sicurezza i primi due.
- **B2, i sats entrano nella cassaforte ed escono SUBITO** (payout al
  `locked`, al netto della fee). Riusa tutto, la fee si trattiene come
  oggi, e per il ristorante è «pagato quando accetto». Ma è ESATTAMENTE
  la strada A con il rilascio spostato dal banco all'accettazione: i
  sats escono prima che il piatto esista, quindi «non posso» dopo
  l'accettazione vuol dire rimborso di tasca nostra o dal ristorante.
  Il modo pulito è farlo uscire ALL'ACCETTAZIONE, che è un gesto del
  ristorante, non un timer — regge il disarmo — e da lì il compratore
  ha la sola tutela della recensione. Per un pilota con un ristorante
  fidato è accettabile; per una rete no.
- **Pro di B in generale**: il ristorante lo capisce al volo («mi
  pagano»), niente attesa di tocchi; **contro**: B1 è caro e cieco, B2
  è A con meno tutela; in entrambi il lessico «senza deposito» va
  detto in cassa, perché il compratore di Barattolo si aspetta il
  deposito (regola 9) e qui non c'è.

### C. Paga al ritiro, con prenotazione

- **Come**: Barattolo diventa una bacheca di prenotazioni: l'ordine
  nasce senza fattura, il ristorante accetta, si paga al banco (in sats
  al suo POS, o come vuole lui).
- **Pro**: zero soldi online, zero rischio di codice sui sats, il
  ristorante incassa come sa fare.
- **Contro**: la fee di Barattolo non ha da dove uscire (resta
  l'abbonamento del ristorante, cioè un'altra cosa); il no-show è tutto
  sul ristorante, che cucina su una promessa; e nessuna app del settore
  lo fa — Square Online «l'unico modo per ordinare per il ritiro è con
  una carta»; Deliveroo ammette il contante ma lo incassa il rider (in
  Italia, tra i tre paesi), col ritiro al banco solo come inciso; TheFork
  e OpenTable per le prenotazioni chiedono la CARTA A GARANZIA o la
  caparra (OpenTable: 2% di servizio sulle penali no-show, tre SMS e
  una telefonata prima dell'addebito; TheFork: quattro no-show in 12
  mesi e l'utente è disattivato; Il Sole 24 Ore: no-show al 3,4% su
  TheFork, caparre da 65 a 250 € a persona nei ristoranti che le
  chiedono). Cioè il settore, quando non fa pagare prima, fa pagare la
  RINUNCIA — e la nostra cassaforte è precisamente una caparra che
  sappiamo già tenere.
- **La variante che ha senso**: la CAPARRA in cassaforte (una quota,
  o un minimo fisso) e il resto al banco. Ma è A con un prezzo diviso
  in due, e un prezzo in due pezzi sul foglio di pagamento e nel conto
  (`_conto_ordine` ha un invariante sulla testata) è un cantiere per
  risparmiare al cliente la parte che paga comunque. Non per il pilota.

### La fee «diversa»

`COMMISSIONE_PERCENTO` è **0** («sospesa: cifra da decidere»,
`config_esempio.py:97`), quindi oggi «fee diversa» è 0 contro 0. Due
cose A VERBALE che una fee dei ristoranti deve rispettare: 1) **la fee
non è fotografata sull'ordine** e all'accensione la cintura di
`paga_venditore` rifiuta le invoice depositate col vecchio netto (ARCH,
in testa); la fee dinamica (CANTIERI «La fee dinamica del mercatino, in
anteprima») è in beta proprio perché «accenderla per davvero» vuole il
congelamento sull'ordine, calco di `ordini.sconto_percento`; 2) il P2P
ha già una fee per AREA e per PERSONA (4% listino, 3% in beta, sconto
fedeltà applicato alla fonte da Mostro: CANTIERI «Le commissioni per
persona»). Quindi: una leva `COMMISSIONE_RISTORO_PERCENTO` letta da
`netto_venditore` quando il negozio è un ristorante è dieci righe; ma
nasce insieme alla fotografia sull'ordine, non prima, e nel pilota resta
a zero come il mercatino. **La commissione minima fissa** del backlog
qui morde più che altrove (ordini da 8-15 €, dove le fee di rotta
pesano in proporzione: il precedente è a verbale in CANTIERI, «La causa
vera del payout fallito: il tetto delle fee di rotta») ed è il primo
conto da fare quando la fee si accende.

**Il verdetto sul pagamento**: **A, con il rilascio al banco per
codice** (2b.4) e l'accettazione entro dieci minuti. Non è «senza
deposito»: è un deposito che dura un pranzo, e al ristorante si spiega
così — «i sats sono già tuoi, li prendi quando consegni». B2 resta la
carta di riserva se un ristorante la pretende; B1 e C no.

## 4. I ristoranti come punti di ritiro: si incastra da sé

Il piano A VERBALE («LA RETE DI PUNTI DI BARATTOLO 📍», ARCH 18403;
CANTIERI 5069) è NATO da un ristoratore di Milano che si è offerto come
punto: «nessun documento, basta il nome sul pacco». Quindi non c'è
niente da incastrare — c'è da riempire una riga. Le decisioni prese,
che valgono pari pari per un ristorante che vende anche piatti:

- **Il punto è un venditore che c'è già**, identificato dal suo codice
  negozio pubblico (`PUNTI_BARATTOLO`, 18034: id, nome, indirizzo,
  comune, orari, negozio), quindi il ristorante del pilota — che per
  vendere piatti ha un negozio — è per costruzione un candidato punto
  con lo stesso codice. **Una sola entità**, due mestieri.
- **Ingresso su INVITO, uno alla volta**, catalogo nel codice = «nessuno
  finisce nell'elenco pubblico senza che una persona scriva una riga e
  faccia un deploy». Vale doppio per chi cucina: è un'insegna, e oggi
  non verifichiamo l'identità di nessuno. La card «🍽️ Da asporto» va
  costruita sullo stesso stampo (un catalogo `RISTORI` nel codice, o —
  meglio — una colonna `ristoro` nel catalogo dei punti stesso).
- **Incentivi NON-MONETARI**: «il livello dell'incentivo fissa il
  livello della responsabilità». Il ristorante-punto non riceve sats
  per i pacchi; riceve il passaggio di gente, e VENDE i suoi piatti a
  chi viene a ritirare. È l'incentivo giusto, ed è quello che DoorDash
  chiama «pickup» e i ristoranti chiamano «traffico».
- **Chi risponde del pacco è il VENDITORE**, e la presa in carico del
  punto (`punto/preso`, con data) è il fatto che gli dà una prova. Non
  cambia niente col ristorante; anzi, un locale con orari e banco è il
  punto che quel verbale immaginava.
- **La mappa quando saranno sparsi**, e **il modulo di candidatura non
  si fa** finché il collo di bottiglia è a valle (accendere, non
  raccogliere): con «cinque candidature e zero punti accesi» ad agosto,
  il primo gesto utile è accendere IL PRIMO punto, e un ristorante che
  vende anche piatti è la ragione migliore per farlo.
- ⚠️ **L'indirizzo finisce nella storia dei commit**: per un ristorante
  va bene (è pubblico per mestiere), e il messaggio-modello del canale
  lo dice già.

**Cosa cambia con i piatti**: gli `orari` del catalogo diventano due
cose — quando si ritira un pacco (orari del locale) e quando si ritira
un piatto (le fasce). Per il pilota è la stessa stringa. E la coda del
titolare (`/api/punto/pacchi`) e la coda degli ordini da asporto sono
lo stesso schermo con due tipi di riga: si disegna una volta.

## 5. Il pilota minimo, e cosa rimandare

**Un ristorante** (quello di Milano che si è offerto, se c'è ancora;
sennò uno del rodaggio), **solo asporto**, **fasce di ritiro
dichiarate**, **fee a zero** come il resto del mercatino, **nessuna
mappa**, **nessuna variante**, **nessuna consegna**.

Il flusso, in una riga per passo:
1. il ristorante apre il negozio, pubblica i piatti come annunci
   «ritiro» in «Alimenti e bevande» (già oggi), e su Nostr escono da
   soli;
2. Andrea lo accende nel catalogo con la sua stringa di fasce
   (`ristoro` + «12:00-14:30, 19:00-22:00, ogni 15 min») e come punto
   di ritiro, se vuole;
3. il cliente apre «🍽️ Da asporto», sceglie il ristorante, riempie il
   vassoio (carrello di sempre), in cassa sceglie la FASCIA, scrive
   le aggiunte nella nota, paga il deposito di garanzia (foglio di
   sempre);
4. al ristorante arriva «🔒 Hai venduto!» con la fascia e un bottone
   «✅ Lo preparo (pronto alle …)» / «❌ Non posso» + motivo; entro 10
   minuti, sennò il cliente vede «riprendi i sats» e li riprende con un
   tocco;
5. il cliente legge «👨‍🍳 In preparazione, pronto alle 13:15» e ha il
   suo codice; al banco lo mostra, il ristorante lo digita nella coda,
   i sats escono (netto della fee, oggi zero);
6. se non viene: i sats restano in cassaforte, il promemoria bussa,
   nel pilota decide Andrea a mano.

**Stima, in cantieri** (col rapporto prove/produzione di casa, 2-3 a
1; ogni cantiere una-due giornate, col suo verbale):

| # | Cantiere | Cosa tocca | Peso |
|---|---|---|---|
| 1 | **La fascia e l'accettazione** | colonne `fascia_ritiro`, `accettato_il`, `pronto_alle`, `rifiuto_motivo`; le fasce in cassa (client) e il gate fuori orario in lettura; rotta accetta/rifiuta con scadenza; il bottone «riprendi i sats» che chiama `_rimborsa_compratore`; lo stadio derivato «in preparazione / pronto alle»; testi e notifiche; STATES fermo | il più grosso: il calco dei SERVIZI (che furono un cantiere intero) |
| 2 | **Il codice al banco** | il codice coniato all'incasso (calco del punto Barattolo), mostrato al compratore, la coda del ristorante col campo codice, il rilascio da `locked` per codice; DA DECIDERE prima (2b.4) | medio: tre precedenti da ricalcare |
| 3 | **La card «🍽️ Da asporto»** | il catalogo nel codice (o la colonna sul catalogo punti), il comando del bot, la card nella fila e la pagina con i ristoranti per comune, orari/fasce in chiaro | piccolo: lo stampo dei Consigliati |

Prima del primo cantiere, **due decisioni di Andrea**: la lettura della
regola 5 per il codice al banco (2b.4), e se il bottone «riprendi i
sats» a scadenza è un gesto che rispetta il disarmo (2b.3: io dico di
sì, perché il timer non muove niente, abilita). E **una domanda ad
Alan**: quale progetto «alla DoorDash» su Nostr intendeva.

**Cosa rimandare a dopo, con la condizione che lo riapre:**
- *varianti e aggiunte a menu* (l'albero min/max) → quando un
  ristorante lo chiede con un menu in mano; fino ad allora un annuncio
  per variante e la nota;
- *orari per giorno con eccezioni, sold-out «fino a fine giornata»* →
  al secondo ristorante;
- *la fee dei ristoranti* → con la fotografia della fee sull'ordine,
  che è il cantiere che riaccende ANCHE quella del mercatino; e con la
  commissione minima fissa del backlog, che qui pesa di più;
- *«🥡 Non ritirato» del ristorante* (il no-show senza Andrea) →
  quando il pilota ne conta uno;
- *la mappa e il pin* → «quando saranno sparsi», insieme ai punti;
- *il menu che nasce su Nostr* (import a leva accesa, ristoratore
  solo-Nostr con payout al suo address) → quando ne esiste uno che lo
  chiede, e comunque dopo la procedura anti-anello di PRODUZIONE;
- *consegna a domicilio* → mai, finché non abbiamo rider: non è la
  domanda e non è il mestiere;
- *ordini su Nostr in dialetto Gamma (kind 16)* → se un giorno un
  client terzo dovesse ordinare da un nostro menu; oggi non c'è.

**Strade scartate, col perché, così non si ripropongono.**
- *Uno stato ordine nuovo («accettato», «pronto»)*: regola ferrea 4 e
  la lezione dei servizi — le colonne sotto `locked` costano metà e non
  ereditano le SELECT sbagliate.
- *L'annullamento automatico a scadenza* (Uber 11,5 min): un timer che
  sposta sats, vietato dal disarmo; il timer abilita il bottone.
- *Sats direttamente al ristorante* (B1): la fee da riscuotere a parte,
  nessuna tutela, un terzo percorso dei soldi.
- *Pagamento al banco* (C): nessuna app lo fa senza carta a garanzia, e
  la garanzia noi la sappiamo già tenere.
- *NIP-15 per il menu*: «unrecommended» nella spec stessa.
- *Il menu come albero (menu → categorie → piatti)*: la categoria è
  già «Alimenti e bevande» con le sue sottocategorie, e un ristorante
  del pilota ha dieci piatti, non cento.

## 6. Raccomandazione, in dieci righe

1. Sì al pilota, con UN ristorante e solo asporto: l'ottanta per cento
   è già nel codice (negozio, annunci, carrello, cassa, Nostr).
2. Il pagamento è quello di sempre: deposito di garanzia che dura un
   pranzo. Niente «sats diretti», niente «paga al banco».
3. Il rilascio al banco per codice rivelato dal compratore, se Andrea
   conferma la lettura della regola 5; sennò il bottone che c'è già.
4. Accettazione entro dieci minuti con motivo; a scadenza il timer
   ABILITA «riprendi i sats», non li muove: il disarmo resta intero.
5. Nessuno stato nuovo: colonne sotto `locked`, stadio derivato.
6. Tre cantieri, in ordine: fascia+accettazione, codice al banco, card.
7. Fee a zero come il rodaggio; la leva dei ristoranti nasce con la
   fotografia della fee sull'ordine, e con la commissione minima fissa.
8. Il ristorante è già il primo punto di ritiro del piano di agosto:
   stessa entità, stesso codice negozio, stessi incentivi non monetari.
9. Niente mappa e niente varianti finché non ci sono più ristoranti.
10. Chiedere ad Alan il link del progetto Nostr che aveva in mente.

## Fonti

Consultate il 24 set 2026. Le pagine dei merchant di DoorDash e Uber
sono documentazione pubblica per gli integratori; le help sono quelle
dei ristoranti.

**DoorDash (developer.doordash.com, help.doordash.com)**
- Menu integration: https://developer.doordash.com/en-US/docs/marketplace/how_to/menu_integration/
  (albero menu/categorie/item/extra, update a menu intero)
- Menu configuration reference: https://developer.doordash.com/en-US/docs/marketplace/explainers/menu_configuration_reference/
  (`min_num_options`/`max_num_options`, `num_free_options`, `is_suspended`, special hours)
- Item level hours: https://developer.doordash.com/en-US/docs/marketplace/how_to/item_level_hours/
  («vale il più stretto dei due»); FAQ orari: https://developer.doordash.com/en-US/docs/marketplace/faq/menu_hours/
- Order integration: https://developer.doordash.com/en-US/docs/marketplace/how_to/order_integration/
  (conferma entro 3-8 minuti, `prep_time`, motivi di rifiuto)
- Ordini, campi e ciclo: https://developer.doordash.com/en-US/docs/marketplace/retail/orders/overview/ ;
  FAQ ordini programmati: https://developer.doordash.com/en-US/docs/marketplace/faq/order/
- Cancellazioni e modifiche: https://developer.doordash.com/en-US/docs/marketplace/faq/order_cancel_and_adjustment_endpoints/
  («i merchant non sono rimborsati per le cancellazioni che inducono»)
- Tablet: https://help.doordash.com/en-us/merchants/article/tablet-order-manager-overview
  (auto-conferma, prep time a 5 minuti, esaurito fino a fine giornata)
- Ordini mai ritirati: https://help.doordash.com/en-us/merchants/article/what-if-a-dasher-or-customer-never-picked-up-the-order
- Rimborsi: https://help.doordash.com/en-us/merchants/article/refund-orders (7 giorni, uno per ordine)

**Uber Eats (developer.uber.com/docs/eats, help.uber.com)**
- Menu integration: https://developer.uber.com/docs/eats/guides/menu-integration
  (item/modifier group/categoria/menu, «unione degli orari dei menu», `visibility_info`)
- Esempi di menu: https://developer.uber.com/docs/eats/references/api/v2/example-menu-payloads (`quantity_info`, `overrides`)
- Order integration: https://developer.uber.com/docs/eats/guides/order-integration (11,5 minuti, robocall a 90 s)
- Get order v2: https://developer.uber.com/docs/eats/references/api/v2/get-eats-order-orderid
  (stati, tipi, `estimated_ready_for_pickup_at`)
- Accept: https://developer.uber.com/docs/eats/references/api/v1/post-eats-order-orderid-acceptposorder (`pickup_time`);
  Deny: https://developer.uber.com/docs/eats/references/api/v1/post-eats-order-orderid-denyposorder ;
  Cancel: https://developer.uber.com/docs/eats/references/api/v1/post-eats-order-orderid-cancel
- Self pickup FAQ (60 minuti, poi «segna ritirato»): https://help.uber.com/en/merchants-and-restaurants/article/self-pickup-faqs?nodeId=408a8353-b004-4c6d-8e4e-668e1bc382ff
- Quando il merchant è pagato: https://help.uber.com/en/merchants-and-restaurants/article/do-we-get-paid-for-canceled-or-unfulfilled-orders--?nodeId=078867b0-26e6-4633-a030-518812801981 ;
  «Why was my order cancelled» (10 minuti): https://help.uber.com/ubereats/restaurants/article/why-was-my-order-cancelled?nodeId=a6de8cca-f3a6-448b-82d3-5653baa5fd98

**Pagamento al ritiro, caparre, no-show**
- Square Online (solo con carta): https://community.squareup.com/t5/Online-Store/After-placing-an-Square-Online-order-can-my-customers-pay-in/m-p/246599
- Deliveroo, contante (UAE, Kuwait, Italia): https://api-docs.deliveroo.com/docs/cash-on-delivery-orders
- OpenTable, 2% sulle penali no-show (Philadelphia Inquirer, 14 gen 2026): https://www.inquirer.com/food/restaurants/opentable-service-fee-no-show-restaurant-reservation-20260114.html
  (le pagine help di OpenTable non si sono aperte: «CSS Error»)
- TheFork, carta a garanzia e caparra: https://www.theforkmanager.com/it/blog/strumenti-thefork/fenomeno-no-show-con-thefork-tanti-strumenti-arginarlo ;
  quattro no-show in 12 mesi: https://www.theforkmanager.com/en/fight-no-shows
  (la pagina support sulla pre-autorizzazione non si è aperta)
- Il Sole 24 Ore, no-show al 3,4%, caparre 65-250 €: https://www.ilsole24ore.com/art/ristoranti-come-hotel-trattenuta-carta-credito-chi-non-rispetta-prenotazione-AEzv3JSB

**Nostr**
- NIP-15 («unrecommended: too complicated, try NIP-99»): https://github.com/nostr-protocol/nips/blob/master/15.md
- NIP-99: https://github.com/nostr-protocol/nips/blob/master/99.md
- Gamma Markets spec (30402 esteso, 30405, 30406, kind 16/17, 31555): https://github.com/GammaMarkets/market-spec/blob/main/spec.md ;
  fork: https://github.com/OpenMarketsFoundation/specification
- Nostr Compass, lug 2026 («NIP-15 is legacy», Gamma): https://nostrcompass.org/en/newsletters/2026-07-15-newsletter/ ;
  catalogo progetti: https://nostrcompass.org/en/projects/
- Plebeian Market, pivot a NIP-99 (29 nov 2025) e 2.0 (23 gen 2026):
  https://plebeianmarket.substack.com/p/plebeian-market-nip-99pivot-drops ,
  https://plebeianmarket.substack.com/p/plebeian-market-20-freedom-tech-is
- LNbits Nostr Market (NIP-15) e la issue #144: https://github.com/lnbits/nostrmarket , https://github.com/lnbits/nostrmarket/issues/144
- Shopstr (NIP-99/17/44/47/57/60/61/85): https://github.com/shopstr-eng/shopstr , https://shopstrmarkets.com/faq
- Kartapio («decentralized food delivery app built on Nostr», 7 commit, ultimo 27 feb 2025): https://github.com/vstabile/kartapio ;
  bitcoin++ Floripa 2025: https://gist.github.com/supertestnet/9808060c7e03fd1001f17d242da5f30b
- Milk Market / Self-Sown: https://github.com/shopstr-eng/milk-market , https://self-sown.com/
- BitFood (Lightning, non Nostr; v1.4.1 del 29 apr 2026): http://www.bitfood.app/

**Bitcoin al banco**
- BTCPay Server PoS e Forms (l'esempio ufficiale con «tavolo, allergie, richieste»):
  https://docs.btcpayserver.org/Apps/ , https://docs.btcpayserver.org/Forms/ , https://blog.btcpayserver.org/bitcoin-pos/
- Modificatori sul PoS BTCPay, ancora in revisione (PR #7403, giu 2026): https://github.com/btcpayserver/btcpayserver/discussions/5515
- Bitcoin Jungle (zero commissioni, pagamento in presenza): https://blog.btcpayserver.org/case-study-bitcoin-jungle-cr/ , https://www.bitcoinjungle.app/project
- Blink, cassa per i negozi: https://www.blink.sv/en/merchant-tools

**Non verificati** (solo da snippet di ricerca): la pre-autorizzazione
TheFork «72 ore prima, rilascio entro 3 giorni»; il POS di Coinos; il
contante di DoorDash Drive; Toast senza pagamento al ritiro.
