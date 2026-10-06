# Studio: «Bazar e mercatini» (6 ottobre 2026)

Sola lettura, nessuna modifica al codice, nessun cantiere aperto. Base:
`origin/main` a `eea8d6e` (i numeri di riga qui sotto sono di quel
commit; i NOMI di funzioni, tabelle e voci sono la cosa da cercare, le
righe si spostano). Il VPS, il nodo e il relay non sono stati toccati.
Nessuna PR aperta e nessun ramo su origin trattava già l'argomento.
Le decisioni di Andrea, date lo stesso giorno, stanno nella sezione 5
e VINCONO su ogni «raccomando» delle sezioni prima.

**L'idea di Andrea.** Due pezzi.
1) Un badge **«🎪 Bazar e mercatini»** che l'utente prende da sé,
   dichiarandosi disponibile a fare banchetti (eventi bitcoiner,
   convention, sagre, in privato), con l'impegno di esporre un adesivo
   di Barattolo col QR che porta al suo negozio; e un elenco cercabile
   per zona di chi ce l'ha.
2) Un calendario di eventi locali dove si compra e si vende in bitcoin,
   proposti e pubblicizzati dagli utenti, a patto di esporre che sono su
   Barattolo (su fiducia).

**La risposta corta.** Quasi tutto il necessario esiste già in casa
in un'altra forma: la geografia dei comuni con le distanze (gli avvisi
di ricerca), il codice negozio stabile che un adesivo stampato può
portare per sempre, la libreria del QR, il contatore delle visite che
conta quante e mai chi, e il calco di una coda di moderazione (il
banner del negozio). Quel che NON esiste: eventi, calendario, una mappa
qualunque, una zona sull'utente, un QR adatto alla stampa. Il badge NON
può essere un distintivo del catalogo: quelli si guadagnano e non si
tolgono mai, questo si dichiara e si deve poter togliere. Il rischio
più serio non è lo spam ma la sicurezza fisica: un elenco di «chi ha
bitcoin nella zona X», più date e luoghi, è una lista di bersagli.

## Come leggere questo file

- «NEL CODICE» = con nome e riga in `server.py` o `miniapp.html`.
  «A VERBALE» = decisione già scritta in `docs/ARCHITETTURA.md` o
  `docs/CANTIERI.md`, col NOME della voce, da non contraddire.
  «DECISO» = scelta di Andrea del 6 ott 2026 (sezione 5).
- Le stime di costo sono un CALCO su cantieri misurati, non una misura.

## 1. Com'è oggi

### 1a. I distintivi (NEL CODICE)

`DISTINTIVI` (server.py:2839) sono dodici medaglie che **si guadagnano
usando** il mercatino: il criterio si ricalcola sempre dai dati veri
(`_dati_distintivi`), l'assegnazione è append-only (`badge_utente`,
`INSERT OR IGNORE`) e **non si revocano mai** — «un premio che sparisce
ferisce più di un raro immeritato». Il flag `fiducia` decide solo la
precedenza nella sfilza.

Il parente più vicino è 📍 «Punto di ritiro»: l'unico legato a un RUOLO
e non a un merito, ed è `fiducia=False` apposta («ospitare un punto è
un servizio alla rete, non una garanzia su chi vende»).

Conseguenza: il badge «Bazar» ha DUE caratteri che il catalogo non
ammette — è **dichiarato** (non c'è criterio da ricalcolare) ed è
**revocabile** (da chi l'ha preso e da un moderatore). Somiglia invece
all'interruttore del negozio in ferie 🌴 (`ferie_fino`, Architettura,
«IL NEGOZIO IN FERIE») o alla npub auto-dichiarata della scala Nostr.

### 1b. La geografia (NEL CODICE)

- `dati/comuni.csv`, circa 7.900 comuni con lat/lon del CENTRO del
  comune, letti in memoria all'avvio da `carica_comuni`
  (server.py:17681; `COMUNI` a 17662): zero rete, zero latenza.
  `COMUNI_LISTA` serve già l'autocomplete del form.
- `distanza_km` (server.py:18023) e `RAGGI_AMMESSI = (10, 25, 50, 100)`
  (server.py:41323), usati dagli avvisi di ricerca (comune + raggio).
- **Nessuna libreria di mappe** nel progetto (niente Leaflet, niente
  tile di terzi).
- **L'utente non ha una colonna «zona»**: la zona vive solo sugli
  annunci, in testo libero.
- Il GPS si usa in un posto solo, la prova di presenza del P2P in
  contanti (`posizionePresenzaP2P`), e solo a casella spuntata.

### 1c. Le mappe: c'è già una decisione (A VERBALE)

Architettura, «LA MAPPA HA LA SUA CONDIZIONE» (riga 19546): per i punti
di ritiro la mappa **«si fa quando i punti saranno SPARSI»**, e niente
ordine per vicinanza finché sono pochi («chiedere la posizione per farlo
sarebbe un dato in più raccolto per un servizio che non si rende»). La
sanzione dichiarata per un punto che non mantiene è **«toglierlo dalla
mappa, e basta»**.

Architettura, «IL MODULO DI CANDIDATURA NON SI FA» (riga 19567): le
candidature arrivano a mano dal canale; un modulo conviene quando quelle
aperte superano i punti che si riescono ad accendere (circa 10 insieme,
o 3-4 al mese), e il collo di bottiglia stava A VALLE. I costi misurati
lì sono il calco di questo studio: **il banner del negozio** (un utente
chiede, va in revisione, un moderatore decide) **circa 2.000 righe**;
**una candidatura circa 900-1.100**, col rapporto prove/produzione di
casa 2-3 a 1.

### 1d. Il negozio, il suo link, le sue visite (NEL CODICE e A VERBALE)

- Il codice negozio (`nuovo_codice_negozio`, server.py:2763) è
  `token_hex(4)`, assegnato una volta e stabile per sempre.
- Architettura, «IL CANONICO DEL NEGOZIO È IL CODICE» (riga 5562):
  username e link a scelta (`negozio_slug`) possono cambiare; il codice
  no. **Un adesivo stampato non si aggiorna, quindi porta il codice.**
- `negozio_visite` (server.py:6187) conta QUANTE aperture per negozio e
  per giorno, MAI CHI: niente tg_id, niente IP, niente cookie.
- Il link `/negozio/…` si apre nel browser: funziona anche per chi non
  ha Telegram, che a una sagra è la maggioranza. Non esiste un deep link
  `startapp`.

### 1e. Il QR (NEL CODICE)

`qrcode.js` 1.5.2 vendorizzato (`caricaQrcode`, miniapp.html:27991);
`disegnaQr` (miniapp.html:28064) disegna su canvas a circa 500 px con
correzione M: giusto per lo schermo, **non per la stampa**. Non esiste
un «QR del negozio»: il tondo Condividi (`condividiNegozio`,
miniapp.html:20202) copia il link. La libreria sa produrre anche SVG
(`createSvgTag`), che è la forma giusta per stampare a qualunque misura.

### 1f. Storie e Consigliati (A VERBALE)

Architettura, «LE PAGINE DEI NEGOZI CONSIGLIATI, IN BOZZA» (riga 3777)
e Cantieri, «Il link condiviso apre la storia» (30 set 2026): le storie
vivono in `RACCONTI` (client) e `racconti.py` (server), con bozza e
pubblicazione decisa da un moderatore; il link del negozio apre già la
storia pubblicata. I Consigliati li sceglie un umano, a mano.

### 1g. Due precedenti utili

- `nostr_badge_live` (server.py:6440): badge NIP-58 delle dirette,
  firmati dalla piattaforma — un oggetto DIVERSO dai distintivi. Un
  domani: «Ero al Bazar di X».
- Lo studio sul contanti a mano (`docs/STUDIO-CONTANTI-A-MANO-2026-09-25.md`,
  «1d. Peach»): Peach ha messo il contanti dentro un PERIMETRO SOCIALE,
  i meetup, invece che dentro una regola di disputa.
- La moderazione degli annunci conosce già il merch: «'Adesivi e gadget
  di Barattolo, lotto da 10' -> OK: cita il mercatino, non lo impersona»
  (server.py:18304).

### 1h. Cosa non c'è

Eventi, calendario, NIP-52, una mappa, una zona sull'utente, un QR per
la stampa, un deep link nella Mini App.

## 2. Il disegno

### 2a. Pezzo 1 — «🎪 Bazar e mercatini»

- **Lo stato si prende dal Profilo**, con un interruttore: l'impegno da
  spuntare («espongo l'adesivo di Barattolo col QR del mio negozio»);
  un **comune** scelto dall'elenco dei comuni (quello dove si muove,
  può essere il capoluogo, NON deve essere casa sua); un **raggio**
  fra i `RAGGI_AMMESSI`; i tipi di banchetto (eventi bitcoiner,
  convention, sagre, privati). Server: qualche colonna su `utenti`
  (dal quando, comune, raggio, tipi, spento dal moderatore sì/no).
- **Requisito**: un negozio con almeno un annuncio vivo — senza, il QR
  porta a una vetrina vuota (DECISO).
- **Nel negozio una pastiglia**, fuori dalla sfilza dei distintivi e
  senza il peso «fiducia»: è un cartello «faccio i mercatini», non una
  medaglia (DECISO).
- **L'elenco `/bazar`**: si sceglie comune e raggio, ordine per
  distanza con `distanza_km` dal centro dei comuni; ogni card è la card
  del negozio che c'è già. Solo per chi ha fatto l'accesso, `noindex`,
  nessuna rotta che restituisca tutto in blocco (DECISO). Niente mappa.
- **Il QR dell'adesivo**: generato nel CLIENT in SVG col `qrcode.js` di
  casa, correzione Q o H (regge un logo al centro e l'usura); punta
  SEMPRE al codice, mai a username o slug; porta un segno di provenienza
  (`?da=adesivo`) perché il venditore veda «N persone arrivate
  dall'adesivo» — quante, mai chi, il patto di `negozio_visite`.
- **Il foglio da stampare**: un A4 con 6-12 adesivi, in PDF/SVG. Dentro
  Telegram la stampa non è affidabile: il bottone apre il browser.
  Questo È il kit fai-da-te (DECISO: subito solo lui).
- **La revoca**: chi l'ha preso lo spegne con lo stesso interruttore;
  il moderatore lo spegne con un comando, e chi è stato spento non lo
  riaccende da solo.

### 2b. Pezzo 2 — gli eventi

- **Chi propone**: solo chi ha lo stato 🎪 (DECISO). Campi: titolo,
  tipo, **comune** (obbligatorio, dall'elenco), **luogo pubblico** in
  testo («Piazza Castello», «Birreria X»), date, un link esterno, e la
  spunta «esporremo che siamo su Barattolo».
- **Moderazione PRIMA della pubblicazione** (DECISO), sul calco del
  banner: chiesto → un moderatore decide → il motivo del no torna a chi
  ha proposto. Il perché: un evento falso non è spam, è un APPUNTAMENTO
  FISICO.
- **Privacy**: mai indirizzi di casa. Un evento privato esce come «su
  invito», col solo comune e il contatto di chi organizza (DECISO).
  Nessuna coordinata precisa salvata: per la distanza basta il centro
  del comune.
- **Il calendario**: l'elenco dei prossimi 60 giorni, filtrabile per
  comune e raggio; su ogni evento i banchetti 🎪 che dicono «ci sarò»
  (è il filo fra i due pezzi); l'evento **scade da solo** dopo la data;
  «Aggiungi al calendario» come file `.ics` fatto nel client.
- **La mappa**: fase 1 niente (DECISO). Più avanti una sagoma SVG
  dell'Italia coi pallini sui comuni, disegnata da noi: niente tile di
  terzi (vedrebbero l'IP di chi guarda), niente CSP da toccare. Rispetta
  la condizione «quando saranno SPARSI» della sezione 1c.

### 2c. I legami

- **Storie**: dopo un bazar riuscito, una storia raccontata come quelle
  dei Consigliati, a mano; l'adesivo di quel negozio la apre già da solo.
- **Consigliati**: SEPARATI. Lo stato 🎪 non è un consiglio nostro, per
  la stessa ragione per cui 📍 è `fiducia=False`.
- **Canale Telegram**: un post per ogni evento approvato.
- **Nostr, più avanti**: NIP-52 per gli eventi, NIP-58 per «c'ero»
  (il calco di `nostr_badge_live`). In collaudo mai relay veri, mai
  eventi pubblicati.

### 2d. Il kit adesivi, tre livelli

- **a) Fai-da-te**: il PDF/SVG da stampare a casa su etichette. Costo
  zero, nasce col pezzo 1. DECISO: subito solo questo.
- **b) Un adesivo generico** col logo e un QR verso `/bazar`, stampato
  da noi, accanto all'etichetta personale fatta a casa. Il QR personale
  per ogni negozio, in piccola tiratura, costa molto di più a pezzo.
  I PREZZI NON SONO VERIFICATI: servono preventivi di un tipografo.
- **c) Il kit venduto in sats** come annuncio (la moderazione già lo
  ammette, 1g), **o regalato ai pionieri**: sarebbe il primo privilegio
  della coorte, che nel backlog «non dà ancora niente».
- b) e c) si valutano DOPO (DECISO). La grafica dell'adesivo la cura
  Andrea.

## 3. Costo (calco, non misura)

| Pezzo | Righe (produzione + prove) | Sessioni |
|---|---|---|
| 1: stato, elenco, QR e foglio | 1.200-1.800 | 2-3 |
| 2: eventi, coda di moderazione, calendario | 2.000-2.800 | 3-4 |
| Sagoma SVG coi pallini | 300-500 | 1 |
| Kit b/c | soldi e logistica, quasi niente codice | — |

Rotte nuove tutte esplicite (regola 3), collaudi nella gabbia prima
della CI.

## 4. Rischi

1. **Sicurezza fisica** — il più serio. Un elenco cercabile di «chi ha
   bitcoin nella zona X», più date e luoghi, è una lista di bersagli
   (il *wrench attack*). Cure: il comune lo sceglie l'utente; elenco
   solo dopo l'accesso, `noindex`, niente rotta in blocco; un avviso
   sobrio negli eventi; mai «porta i tuoi sats».
2. **Responsabilità.** Vendere su aree pubbliche vuole permessi
   (tesserino hobbisti, regole regionali). Noi non organizziamo,
   segnaliamo, e il testo lo dice. Non è un parere legale: va nella coda
   del parere MiCA del backlog.
3. **Il marchio in mano ad altri.** Chi espone l'adesivo e si comporta
   male sporca Barattolo, e su uno stato dichiarato non c'è prova. Cura:
   il testo lo dice, la revoca è facile.
4. **Fiducia senza verifica.** L'impegno non si controlla. Il segnale
   morbido sono le scansioni dell'adesivo nel giorno dell'evento; la
   sanzione resta quella scritta per i punti: togliere dalla lista.
5. **Carico di moderazione.** Ogni evento passa da Andrea o da Alan.
6. **La stampa da Telegram.** Va provata sul telefono prima di dire che
   funziona.
7. **I tempi.** Il 10 ott il lancio del P2P, il 17-18 l'hackathon:
   niente prima del 19 ottobre.
8. **La vendita al banco non passa da Barattolo.** È marketing, non
   incasso. Una «cassa del banchetto» sarebbe un altro cantiere (vicino
   allo studio Bolt card).

## 5. Le decisioni di Andrea (6 ott 2026)

1. **Natura**: stato del negozio, revocabile, FUORI dai distintivi.
2. **Requisito**: un negozio con almeno un annuncio vivo.
3. **Elenco**: solo per chi ha fatto l'accesso, senza indicizzazione.
4. **Eventi**: li propone solo chi ha lo stato 🎪, con moderazione
   PRIMA della pubblicazione.
5. **Eventi privati**: ammessi, come «su invito», col solo comune.
6. **Mappa**: fase 1 solo elenco; la sagoma SVG coi pallini più avanti.
7. **Kit**: subito solo il fai-da-te (PDF/SVG da stampare); l'adesivo
   generico stampato da noi e il kit per i pionieri si valutano dopo.
   La grafica la cura Andrea.
8. **Ordine**: il pezzo 1 dopo il 18 ottobre 2026; il pezzo 2 quando gli
   stati 🎪 accesi arrivano a circa 15.
9. **Nome**: «Bazar e mercatini», con 🎪.

## 6. Cosa resta aperto quando si apre il pezzo 1

- La grafica dell'adesivo (di Andrea) e il formato delle etichette del
  foglio (6 o 12 per A4).
- Il testo dell'impegno e dell'avviso di sicurezza, in tono di casa.
- La prova della stampa sul telefono, dentro e fuori Telegram.
- Come si conta «circa 15» per aprire il pezzo 2: stati accesi oggi, non
  presi una volta.
