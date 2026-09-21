# Audit di sicurezza dei pagamenti — 19 settembre 2026

Sola lettura, nessuna modifica al codice. Base: `origin/main` a `5d58f76`
(i numeri di riga qui sotto sono di quel commit). A lettura finita main è
avanzato di due commit (`22cbc20`): toccano solo le FRASI degli avvisi
P2P, nessun percorso dei soldi — guardati, e annotati in M6. Lavorato in un worktree
isolato; il VPS e il nodo non sono stati toccati, nemmeno in lettura.

**La domanda:** dopo i cantieri del 17-19 set, esiste un modo per far
perdere sats a un cliente, a un venditore o a Barattolo, per farli pagare
due volte, o per bloccarli?

**La risposta corta:** due strade gravi, e nessuna delle due è nata il
17-19 set. La prima è nel pannello 🧊 (un «non è uscito» premuto mentre
il pagamento è ancora in volo fa pagare due volte — riprodotta in locale
con le funzioni vere). La seconda non è nel codice ma nella catena del
deploy: il ref `pronto` non è protetto e il server gira da root, quindi
chi può scrivere sul repo arriva a TUTTI i fondi in un minuto. I cantieri
del 17-19 set (patch 0005-0007, `/api/p2p/sconto`, `/api/p2p/evento`,
recapito, guardiano, zone, sconto a soglia, «riprova») li ho trovati
scritti con cura: i difetti che hanno sono medi o bassi, e stanno più giù.

## Come leggere questo file

- **GRAVE** = soldi persi o doppi, possibile oggi. **ALTA / MEDIA /
  BASSA** = il resto, in ordine.
- Ogni voce ha: lo scenario passo per passo, la prova (riga di codice, o
  una riproduzione che gira in locale), e la cura proposta **come cantiere
  separato** — qui non si è curato niente.
- In fondo: cosa è stato trovato SANO, cosa NON ho potuto verificare (col
  comando di sola lettura da lanciare), e le prove che mancano.

## Cosa ho letto, e quanto a fondo (onestà sul metodo)

LETTO PER INTERO, riga per riga (su una vista di `server.py` senza
commenti, numeri di riga veri): autenticazione e sessioni (initData,
widget, login Nostr, collegamenti e fusione), le cassaforti, `crea_invoice_escrow`,
`invoice_pagata`, `paga_venditore`, `_stato_pagamento`, `_esito_lnbits`,
i quattro timbri (`_timbra_pagamento`, `_in_volo`, `_congela_pagamento`,
`_sospendi_pagamento`), `invoice_da_ln_address`, il cambio, `compra`
(ordine singolo), `verifica_pagamento`, `_incassa_ordine`,
`deposita_invoice`, `_sblocca_sats`, `_rimborsa_compratore`,
`risolvi_disputa`, conferma/disputa/reso/annulla, `controlla_annullati`,
`controlla_abbandonati`, `controlla_scadenze`, `risolvi_pagamenti_in_volo`,
`riprova_pagamenti_sospesi`, `_riprendi_uscita`, la coda 🧊 e
`decidi_pagamento`, `_paga_rimborso` e la sua rotta, `salva_ln_address`,
la consegna digitale, gli sconti (`_sconto_*`, `_codice_vale`,
`_conto_ordine`), le zone (`_zona_*`, `_tariffa_dichiarata`), il guardiano
del ponte, tutto il blocco P2P lato server che tocca soldi o identità
(`/api/p2p/sconto`, `/chiavi`, `/recapito`, `/seme`, `/evento` coi loro
giudici), i due moduli Rust `barattolo_fee.rs` e `barattolo_eventi.rs`, le
patch 0005 e 0006 (gli hunk fuori dal modulo), `deploy.sh`, le due unit
del deploy, il workflow CI, `backup-fuori.sh`.

LETTO A MAGLIE LARGHE (le righe che decidono importi e permessi, non
tutto): il carrello (`_compra_set`), le offerte, le aste (puntate, rilanci,
chiusura), lo sblocco banner e lo slug a pagamento, il punto di ritiro e
le buste, il Punto Barattolo.

NON LETTO: `miniapp.html` (il client: 50 mila righe), quindi niente sul
lato browser del P2P (derivazione del mazzo, tetto dei 250 €, NaN del
foglio) e niente XSS; i sorgenti upstream di mostrod (le patch si
applicano a un albero che qui non c'è, e niente `cargo`); il tabacchino /
Barattozon oltre a quello che passa da `compra`.

STRUMENTI STATICI: `bandit`, `pip-audit` e `semgrep` **non sono installati
su questo PC** e non li ho scaricati di mia iniziativa. Al loro posto una
passata a mano sugli stessi schemi (shell, `eval`/`exec`, `pickle`,
`yaml.load`, `verify=False`, `random` per segreti, SQL composto): esito
nella sezione «sano». I comandi per lanciarli stanno in fondo.

---

# GRAVI

## G1 — «Non è uscito» premuto su un pagamento ancora in volo: si paga due volte

> ✅ **CURATA lo stesso giorno** dal cantiere «I pagamenti in volo» (vedi
> `docs/CANTIERI.md`): il bottone verifica su LNbits e LND prima di
> decidere, ogni ritentativo guarda TUTTI gli hash tentati, e la
> riproduzione qui sotto è diventata una prova di `prove.py` (rossa sul
> codice di prima, verde adesso). La metà «LND» aspetta il macaroon di
> sola lettura e il drill: vedi `docs/PRODUZIONE.md`. Il testo che segue
> resta com'era, perché descrive il codice di PRIMA.

**Chi perde:** Barattolo (il deposito di garanzia, cioè in ultima analisi i
sats degli altri ordini). **Quanto:** il netto dell'ordine, o l'intero
prezzo nella variante del rimborso. **Serve:** un venditore (o un
compratore, nella variante) disonesto, e un moderatore che preme il bottone
sbagliato — ma il pannello **lo porta lì**, vedi la variante B.

### Il meccanismo

1. `decidi_pagamento` (`server.py:18648`) con `esito="non_uscito"` fa UNA
   sola cosa: `UPDATE … SET payout_stato='' WHERE payout_stato='incerto'`.
   **Non chiede a LNbits lo stato di `payout_hash`.** Si fida della persona.
2. Da lì in poi quell'hash è dimenticato: `_timbra_pagamento`
   (`server.py:7862`) al tentativo dopo lo SOVRASCRIVE col nuovo. La
   difesa di `paga_venditore` (`server.py:7722`) guarda solo l'hash della
   fattura che sta per pagare — e una fattura NUOVA ha un hash nuovo.
3. E la fattura nuova nasce da sola: `_sblocca_sats` (`server.py:41441`),
   se `invoice_venditore` è vuota, ne chiede una fresca al Lightning
   address. La prova di casa lo dice con parole sue, `prove.py:4053`:
   «OGNI chiamata conia una fattura NUOVA: e' esattamente il motivo per
   cui un ritentativo pagherebbe due volte».

Chi tiene il primo pagamento «pending» quanto vuole? Chiunque risponda al
proprio Lightning address con una **hold invoice**: l'HTLC resta appeso
finché il destinatario non lo salda o non scade il CLTV (giorni). Per
LNbits è un pagamento `pending`, identico a uno lento.

### Variante A — l'incasso del venditore

1. Il ladro vende (anche a se stesso, con un secondo account: gli costa la
   sola commissione, oggi zero). Il suo Lightning address sta su un server
   suo che conia hold invoice.
2. Il compratore conferma → `_sblocca_sats` → `paga_venditore` → LNbits
   dice `pending` per 8 secondi → `INCERTO` → `in_volo`. Lo stato
   dell'ordine **resta** `delivered`/`shipped` (non passa a `confirmed`).
3. Dopo 30 minuti `risolvi_pagamenti_in_volo` si arrende → `incerto` →
   avviso ai moderatori, riga nella coda 🧊.
4. Il venditore protesta («non mi è arrivato niente», ed è vero). Passano
   ore, LNbits dice sempre `pending`. Il moderatore preme **«non è uscito»**.
5. Il compratore ripreme «Conferma» (`conferma_ricezione`,
   `server.py:42118`: lo stato è ancora fra `locked/shipped/delivered`) →
   `_sblocca_sats` → fattura NUOVA dal Lightning address → pagata subito →
   `released`.
6. Il ladro salda anche la hold invoice del passo 2. **Usciti due netti.**

### Variante B — la più naturale: c'è una disputa

Stessi passi 1-3, poi il compratore (complice) apre la disputa — si può,
lo stato è ancora `delivered`. Il moderatore vuole rimborsarlo, ma
`_rimborsa_compratore` (`server.py:41703`) si rifiuta finché
`payout_stato` è `incerto`. **L'unico modo di sbloccare il rimborso è
dichiarare «non è uscito».** Lo dichiara, rimborsa il prezzo intero al
compratore, e il venditore salda la hold invoice: fuori prezzo + netto.
Qui non serve nemmeno un moderatore distratto: serve uno che fa quel che
il pannello gli chiede.

### Variante C — i rimborsi d'asta, senza complice

Su `rimborsi_asta` lo stato resta `da_riscuotere` durante il volo, quindi
dopo il «non è uscito» l'utente stesso richiama
`POST /api/rimborsi/{id}/invoice` (`server.py:23004`) con una fattura
nuova, o risalva il Lightning address (`server.py:31409`): `_paga_rimborso`
paga la seconda. Stesso difetto su `pagamenti` (sblocco banner).

### La prova

Riprodotto in locale con le funzioni VERE estratte da `server.py`
(`_sblocca_sats`, `paga_venditore`, `_stato_pagamento`, `_esito_lnbits`,
i quattro timbri) contro un LNbits di cartone che tiene `pending` la
prima fattura. Lo script è in appendice (A1): si lancia con
`python riproduci_doppio_payout.py server.py` e non tocca niente. Esito:

```
1) il compratore conferma: parte il payout verso il Lightning address
    {'ok': False, 'stato': 'delivered', 'in_volo': True} ('delivered', 'in_volo', 'hash-di-lnbc-fattura-1')
2) la ronda, dopo 30 minuti di «pending», si arrende: incerto
    ('delivered', 'incerto', 'hash-di-lnbc-fattura-1') — LNbits dice ancora: {'hash-di-lnbc-fattura-1': 'pending'}
3) il moderatore preme «non e' uscito»
    ('delivered', '', 'hash-di-lnbc-fattura-1') — nessuno ha richiesto a LNbits lo stato di quell'hash
4) il compratore ripreme «Conferma»
    {'ok': True, 'stato': 'released'} ('released', 'uscito', 'hash-di-lnbc-fattura-2')
5) ora il venditore salda anche la hold invoice del passo 1
    DOVUTI 1000 sats — USCITI 2000 sats
```

E la copertura di oggi: `decidi_pagamento` ha SOLO sentinelle di testo
(`prove.py:4321` e `prove.py:63091`: cercano una stringa nel sorgente).
Nessuna prova fa girare un «non_uscito».

### La cura proposta (cantiere suo)

1. **Il bottone non si fida della persona.** `decidi_pagamento`, prima di
   accettare `non_uscito`, chiede `_stato_pagamento(payout_hash)`: accetta
   solo `failed` o 404; su `pending` risponde 409 («è ancora in volo: non
   si può dichiarare non uscito finché il nodo non lo chiude») e su
   `success` lo tratta come «uscito». A LNbits muto: 503, niente cambia.
2. **Gli hash non si dimenticano.** Una tabella `payout_tentati(tabella,
   riga_id, hash, quando)` scritta da `_timbra_pagamento`; prima di ogni
   pagamento nuovo si chiedono a LNbits TUTTI gli hash di quella riga, e
   se uno è `pending` o `success` non parte niente.
3. **Il rimborso in disputa non deve passare da una bugia.** Se il
   pagamento al venditore è in volo, il pannello della disputa lo dice e
   aspetta; non offre «non è uscito» come scorciatoia.
4. Da valutare: un tetto al tempo dell'HTLC in uscita (LND `cltv_limit` /
   `timeout_seconds`, se LNbits 1.6.1 li espone) così un volo non dura
   giorni.

**Cosa fare DA SUBITO, senza codice:** regola a voce per chi modera —
«non è uscito» si preme SOLO se su LNbits quel payment hash risulta
`failed` o non esiste. Se dice `pending`, si aspetta, anche giorni.

## G2 — Il ref `pronto` non è protetto e il server gira da root: chi scrive sul repo arriva a tutti i fondi

> ✅ **CURATA NEL CODICE il 21 set 2026** dal cantiere «Il deploy che si
> fida solo di main, e il servizio non root» (vedi `docs/CANTIERI.md`):
> `deploy.sh` tira un commit solo se sta su main, va in avanti, ha la CI
> verde chiesta a GitHub e — a firme accese — la punta firmata da una
> chiave scritta sul VPS. ⚠️ SUL VPS resta la sequenza di
> `docs/PRODUZIONE.md` («IL DEPLOY CHE SI FIDA SOLO DI MAIN»): finché le
> FIRME non sono accese, chi scrive su MAIN passa ancora — è il punto 3
> della cura qui sotto, l'unico che regge a un account bucato. Il testo
> che segue resta com'era, perché descrive il codice di PRIMA.

**Chi perde:** tutti — il wallet LNbits del deposito di garanzia, e (via
A2) i sats dei venditori P2P. **Serve:** le credenziali GitHub di UNO dei
due account con diritto di scrittura, o un token con `contents:write`
finito nel posto sbagliato.

### I fatti, verificati

- `deploy.sh` fa `git fetch origin pronto` e poi `git reset --hard` su
  quello che trova, **senza nessun controllo**: non guarda se il commit
  sta su `main`, non guarda una firma, non chiede alla CI.
- Il repo è privato su un piano gratuito: **la protezione dei rami e i
  ruleset non sono disponibili** (chiesto all'API di GitHub oggi:
  `403 — Upgrade to GitHub Pro or make this repository public`). Quindi
  `pronto` e `main` accettano push da chiunque abbia scrittura.
- Hanno scrittura: `kreamistudio-crypto` (admin) e `alanbimbati` (write).
- L'unit gira in `/root/satmarket` e PRODUZIONE.md lo dice in chiaro: il
  guardiano del ponte richiede `User=` vuoto o `root`. Il server web
  pubblico gira da root (da confermare col comando in fondo).

### Lo scenario

1. Qualcuno ottiene un token che scrive sul repo: il PC di Andrea o di
   Alan, un token in una sessione Code, il PAT in `/root/.git-credentials`
   del VPS se non è in sola lettura, una action di terzi aggiunta un
   domani con `contents: write`.
2. `git push origin qualunque:pronto`. **La CI non gira nemmeno:** il job
   `pronto` è l'unico che *dovrebbe* muovere quel ref, ma niente lo impone.
3. Entro un minuto il VPS esegue quel codice, da root. `compileall` e
   `/api/salute` sono gli unici giudici, e un codice ostile li passa.
4. Da root si leggono `config.py` (chiavi admin LNbits, `BOT_TOKEN`,
   `SEGRETI_PROFILO_P2P`), `/opt/lnbits/.env` (il macaroon), le chiavi
   onion. Con la chiave admin LNbits il wallet si svuota con una POST.

CLAUDE.md dice «chi compromette GitHub — o una action di terzi — non
arriva al nodo Lightning». È vero per le **chiavi SSH** (non ci sono), ma
non per il **codice**: il VPS tira ed esegue quel che trova. La frase
andrebbe corretta quando si fa il cantiere.

### La cura proposta (cantiere suo, in ordine di costo)

1. **Subito, gratis:** verificare che il PAT sul VPS sia fine-grained, solo
   su questo repo, `Contents: read`. 2FA su entrambi gli account GitHub.
2. `deploy.sh` rifiuta un `pronto` che non sia antenato di `origin/main`
   (`git merge-base --is-ancestor`): non ferma chi scrive anche su main, ma
   toglie il push diretto «di lato».
3. **La cura vera:** il VPS verifica una FIRMA che GitHub non possiede
   (`git verify-commit` con una chiave che vive solo sul PC di Andrea, o un
   tag firmato come gesto di rilascio). Costa un gesto per deploy; è la
   sola cosa che rende vera la frase di CLAUDE.md.
4. Oppure GitHub Pro (4 $/mese) e un ruleset su `pronto` — ma resta una
   difesa DENTRO GitHub, cioè dentro il perimetro che si vuole non fidato.
5. Separare i privilegi: vedi A1.

---

# ALTA

## A1 — Il server pubblico gira da root

> ✅ **CURATA NEL CODICE il 21 set 2026**, stesso cantiere: utente
> `barattolo`, il guardiano passa da `sudo -n` con una regola di sudoers
> che nomina i soli quattro riavvii, e la copia degli script di deploy
> e backup sta sotto `/run` invece che in `/tmp` (la BASSA qui sotto).
> Il cambio sul VPS lo fa `deploy/utente/cambio-utente.sh`, quando lo
> lancia Andrea: fino ad allora il servizio gira ANCORA da root.

`PONTE_COMANDI` (`server.py:8738`) lancia `systemctl restart tor` e
`systemctl restart lnd-ponte.service`, e per riuscirci il servizio
`barattolo` deve essere root (PRODUZIONE.md, «IL RIAVVIO RICHIEDE ROOT»).
I comandi sono tuple costanti, senza shell e senza niente che arrivi da
fuori: **il guardiano in sé non è iniettabile** (verificato). Il problema
è il contorno: lo stesso processo decodifica immagini caricate da chiunque
(Pillow, pillow-heif), parla con relay Nostr, scarica foto da URL. Un solo
difetto di esecuzione in una di quelle librerie vale la macchina intera —
config, macaroon, chiavi onion, e il deploy stesso.

**Cura proposta:** il servizio torna a un utente senza privilegi, e il
riavvio passa da una riga di `sudoers` (o una regola polkit) che concede
SOLO quei due comandi esatti. Il guardiano non cambia di una riga.

Collegato, BASSA: l'unit del deploy copia lo script in un nome FISSO,
`/tmp/barattolo-deploy.sh`, e lo esegue da root. Su una macchina con soli
utenti root è innocuo; il giorno che un servizio non-root (tor, LNbits in
Docker con un bind mount, il futuro utente di A1) potesse scrivere in
`/tmp`, un symlink messo lì prima diventa esecuzione da root. Cura:
`mktemp` o una cartella sotto `/run` di proprietà di root.

## A2 — Il seme del profilo P2P di chi entra da Telegram lo ricava il SERVER

`_seme_profilo_p2p` (`server.py:34468`) deriva la chiave madre del profilo
di scambio da `SEGRETI_PROFILO_P2P` (in `config.py`) + un sale (nel
database) + il `tg_id`. `/api/p2p/seme` (`server.py:35574`) la consegna
solo al suo titolare, ed è scritta bene: nessun parametro, `tg_id > 0`,
`no-store`. Ma la conseguenza va detta: **chi ha `config.py` e il database
— cioè il server, e chiunque lo comprometta, e chiunque apra un backup —
può ricavare la chiave P2P di ogni utente Telegram.** Con quella chiave si
parla a mostro al posto suo:

- come VENDITORE, un `release` a garanzia pagata: i sats (fino al tetto di
  500.000) vanno al compratore — che è il ladro — senza un euro;
- come COMPRATORE, una fattura nuova nello stato «payout fallito»;
- e si leggono i messaggi cifrati, recapito degli euro compreso.

Non è custodia dei FONDI (quelli li tiene la hold invoice del
coordinatore), ma è custodia di un SEGRETO altrui, e la regola ferrea 2
dice «mai». Il cantiere l'ha decisa sapendolo (serve a ritrovare il
profilo su un altro telefono); qui si registra il prezzo, che cresce con
G2 e A1: la catena «push su `pronto` → root → `config.py`» arriva fino ai
sats dei venditori P2P.

**Cura proposta:** nessuna urgente se G2 e A1 si chiudono. Da valutare:
che il seme derivato firmi solo l'IDENTITÀ (reputazione, restore) e le
trade key nascano da entropia del dispositivo; oppure dichiararlo in chiaro
all'utente, e tenere `SEGRETI_PROFILO_P2P` fuori dal backup che viaggia su
Telegram (oggi c'è dentro, cifrato con age: la chiave privata age sul PC
diventa la chiave di tutto).

## A3 — Il digitale si sblocca da solo anche a leva spenta, e la moderazione AI è ferma

`controlla_scadenze` (`server.py:44119`) tiene i due rami del digitale
FUORI da `AUTO_SBLOCCO_ATTIVO`: 24 ore dopo la rivelazione, o **48 ore dopo
la consegna anche se il compratore non ha mai aperto niente**, i sats vanno
al venditore. È documentato e voluto. Ma oggi si somma a due fatti:
`moderazione_ai` è fail-open (`server.py:13524`: «saltata, nessun blocco»)
e dal 17 set i crediti sono finiti, quindi gli annunci passano col solo
filtro a parole; e `TETTO_DIGITALE_NUOVI` nasce a 0 (spento).

**Scenario:** annuncio digitale truffa (un «codice regalo») → il
compratore paga → il venditore consegna una stringa qualunque → se il
compratore non guarda l'app per 48 ore, o la guarda e non apre disputa in
24, il ladro è pagato in automatico, su una fattura sua. È l'unico punto
del mercatino in cui i sats escono senza il gesto di nessuno.

**Cura proposta:** finché la moderazione è ferma, accendere
`TETTO_DIGITALE_NUOVI` sul VPS (è una leva, zero codice) e/o portare
`ORE_SILENZIO_DIGITALE` a un valore largo. Poi, cantiere: a moderazione
muta gli annunci DIGITALI vanno in revisione invece di passare.

---

# MEDIA

## M1 — `uscito` non ricorda il VERSO: un ordine può chiudersi dalla parte sbagliata senza pagare

`_sblocca_sats` (`server.py:41445`) e `_rimborsa_compratore`
(`server.py:41722`) trattano `payout_stato == 'uscito'` come «già pagato» e
chiudono, **senza guardare `payout_verso`**. La strada normale
(`_riprendi_uscita`, `decidi_pagamento`) il verso lo rispetta. Ma se la
ripresa salta (un'eccezione fra l'UPDATE a `uscito` e la chiusura —
`server.py:45299-45307` la cattura e la stampa) la riga resta p.es.
`dispute` + `uscito` verso il venditore; se poi il moderatore decide
«rimborso», l'ordine diventa `refunded` **senza che al compratore sia
partito niente**, e i sats del rimborso restano in cassaforte senza
padrone. Nessun doppio pagamento; un cliente che risulta rimborsato e non
lo è. **Cura:** `uscito` vale solo se `payout_verso` è quello di chi sta
chiudendo; altrimenti ci si ferma e si avvisa.

## M2 — SSRF cieca dal Lightning address

`salva_ln_address` valida solo «c'è una @ e un punto» (`server.py:31354`),
poi `invoice_da_ln_address` (`server.py:8131`) fa una GET a
`https://{dominio}/…` **seguendo i redirect**, e una seconda GET al
`callback` che il server remoto dichiara — un URL qualunque, anche
`http://127.0.0.1:5001/…` (LNbits), `:18080` (il ponte), `:2019` (l'admin
di Caddy), `:8080`. La risposta non torna all'attaccante (si usa solo
`pr`), quindi è cieca e di sola GET; ma gira da root, dentro la rete
locale dove LNbits si fida di `127.0.0.1`, e ogni estensione LNbits con
una GET che ha effetti diventerebbe raggiungibile. Si ripete a ogni payout
(il dominio è del venditore).
**Cura:** `follow_redirects=False`; il `callback` deve essere `https`,
stesso dominio (o comunque risolto a un IP pubblico: rifiutare loopback,
privati, link-local, `.onion`); porta 443.

## M3 — Una hold invoice blocca un payout per giorni (anche senza G1)

Anche col bottone curato, chi riceve può tenere appeso l'HTLC fino al
CLTV. Effetti: liquidità del canale impegnata, ordine che non si chiude,
moderatore sotto pressione. Non si perde niente finché nessuno dichiara il
falso. **Cura:** vedi G1.4; e nel testo 🧊 dire chiaro che «pending da
giorni» è il segno di una hold invoice, non di un guasto.

## M4 — La domanda dello sconto gira nel ciclo SERIALE di mostro: fino a 12 s per presa

Lo dice la patch stessa (`barattolo_fee.rs`, `LOOKUP_BUDGET`): «the take
handler runs in the serial message loop, so this is also the longest a
dead server can stall a take». Con Barattolo irraggiungibile (deploy,
rollback, ponte Tor freddo) ogni `take` costa 12 secondi a TUTTO il
coordinatore; una raffica di `take` da chiavi usa-e-getta lo tiene fermo
gratis (pow spento, bond spenti). Non si perdono sats; si fanno scadere le
finestre da 900 s degli scambi altrui. **Cura:** un interruttore locale —
dopo N fallimenti di fila la domanda si salta per un minuto (fee piena,
che è già il fail-closed) — e il battito `/api/salute` che già c'è come
fonte del verdetto.

## M5 — `chiavi_p2p`: una pubkey si registra senza provare di possederla

`_registra_chiavi_p2p` (`server.py:34616`) è `INSERT OR IGNORE` di
qualunque stringa di 64 hex, 500 per utente, nessuna firma. Un pioniere può
registrare la trade key di un amico (che usa un altro client) e
**prestargli lo sconto fedeltà**: `/api/p2p/sconto` risponde `true` per
quella chiave. Il danno è piccolo (la fee scontata, tetto 1% a parte) ma è
denaro di Barattolo. Non ho trovato il modo di usarlo per dirottare un
recapito: il recapito viaggia cifrato fra i due client, il server manda
solo l'avviso, e `compra == vende` è rifiutato. **Cura:** la registrazione
porta una firma Schnorr della chiave su una sfida del server (la verifica
c'è già: `verifica_evento_login`).

## M6 — Un evento falso dice «sats in garanzia» a chi sta per mandare euro

`/api/p2p/evento` è fatta bene (vedi «sano»), ma il suo segreto è un
Bearer statico e, lato Rust, **ricade su quello dello sconto**
(`ENV_SECRET_FALLBACK`): se sul nodo c'è una sola variabile, i due segreti
sono lo stesso, e chi ne legge uno li ha tutti e due. Con quel segreto si
fabbrica un `hold-invoice-paid` e il compratore riceve «🔒 X ha bloccato i
sats in garanzia» su uno scambio dove non è vero. La pagina dello scambio
legge lo stato da mostro e non dal server, e l'avviso del recapito lo
ricorda («Invia solo se la pagina dice Sats in garanzia») — ma
`garanzia_pagata` quella coda non ce l'ha. E sul main di stasera
(`22cbc20`, arrivato mentre scrivevo) la frase si è fatta più diretta:
a recapito già detto dice «ha bloccato i sats in garanzia e ti ha già
indicato dove inviare gli euro: tocca a te» (`server.py:37760` di quel
commit) — che è giusta quando a dirlo è mostro, ed è esattamente la frase
che un evento falso vorrebbe far arrivare. **Cura:** due segreti distinti
(zero codice); la stessa riga di prudenza in coda a `garanzia_pagata`; da
valutare un HMAC del corpo al posto del Bearer.

## M7 — Comandi di servizio del bot concessi per USERNAME

`e_admin_bot` (`server.py:10631`) accetta `ADMIN_IDS` **oppure** due
username scritti nel codice (`server.py:10620`). Uno username Telegram si
può lasciare e riprendere: chi se lo prende eredita `/canale`, `/sponsor`,
`/punti`, `/vetrina`. `/punti` amministra i Punti Barattolo, cioè DOVE
finiscono i pacchi. Le rotte che muovono sats usano `e_admin` (solo id):
quelle sono a posto. **Cura:** solo id.

## M8 — Nessuna CSP sugli script, e l'initData vale 24 ore

L'unica `Content-Security-Policy` è `frame-ancestors` (`server.py:1605`).
`miniapp.html` ha 289 `innerHTML`; c'è un `esc()` e non ho verificato che
sia usato ovunque (client non letto). Un XSS riuscito legge
`Telegram.WebApp.initData`, che il server accetta per 24 ore
(`ORE_INITDATA`), e con quello cambia il Lightning address della vittima:
il prossimo incasso va al ladro. **Cura:** un cantiere di sola lettura sul
client (ogni `innerHTML` con dato altrui), e una CSP `script-src` — che
con gli script inline di oggi vuol dire nonce o hash.

---

# BASSA

- **B1 — La firma dell'initData si confronta con `!=`** (`server.py:6840`)
  e non con `hmac.compare_digest` come fanno il widget, il webhook e le due
  porte P2P. Non sfruttabile in pratica via rete, ma è l'unica delle cinque.
- **B2 — `prezzo_eur` accetta `inf`/`nan`** (`server.py:9067`): il parser
  JSON di Python legge `Infinity` e `NaN`, `prezzo_eur <= 0` è falso per
  tutti e due, e `round()` alza → 500. Nessun soldo, solo un errore brutto.
- **B3 — `paese` vuoto vale «domestico»** (`server.py:20933`): chi compra
  dall'estero e non manda il paese paga la tariffa di casa. Il venditore se
  ne accorge dall'indirizzo; ci rimette la differenza o apre un contenzioso.
- **B4 — Una disputa aperta DURANTE un payout viene ricoperta**:
  `_sblocca_sats` legge lo stato all'inizio e a fine pagamento scrive
  `released` (o `confirmed`) sopra il `dispute` arrivato nel frattempo. Con
  l'auto-sblocco fisico disarmato riguarda solo il digitale e la finestra è
  di secondi. Il moderatore può riaprire (`sbloccato_auto_il > 0`).
- **B5 — Un ordine ANNULLATO e poi pagato si riacciuffa solo per 30
  minuti** (`controlla_annullati`, `creato >= adesso-1800`). Le fatture
  durano 15, quindi regge — salvo un server fermo più di mezz'ora proprio
  lì: quei sats restano in cassaforte senza ordine. Li vede il controllo
  del libro mastro, non un avviso dedicato.
- **B6 — `BOT_TOKEN` vive dentro l'URL** delle chiamate a Telegram; le
  eccezioni di httpx stampate con `{e}` di norma l'URL non lo portano, ma
  è una distanza di una riga (`raise_for_status`) dal journal. E chi ha il
  `BOT_TOKEN` fabbrica l'initData di chiunque, moderatori compresi.
- **B7 — `_esito_lnbits` legge `pending: false` come `success`**
  (`server.py:7476`) quando manca `status`. Con LNbits 1.6.1 `status` c'è
  sempre; sulla cassaforte SaaS (12 ordini vecchi) la versione non la so.
- **B8 — Il tetto dei 250 € del P2P è nel client** (`maxEuro` in
  `_p2p_leve`): un altro client Mostro non lo vede. A tenere è il tetto in
  sats del coordinatore (`max_order_amount`, 500.000).
- **B9 — Nessun limite di frequenza** sulle rotte che chiamano LNbits a
  ogni colpo (`verifica-pagamento`, `ln-address`, `invoice`): un utente
  autenticato può far lavorare il nodo a vuoto.
- **B10 — `/api/salute` dice a chiunque lo stato del ponte** (`ok`/`giu`):
  un attaccante sa quando gli acquisti falliscono.

---

# Diagrammi degli stati

## Mercatino — `ordini.stato`

| Da | A | Chi lo innesca |
|---|---|---|
| — | `creato` | compratore (`POST /api/orders`): importi TUTTI calcolati dal server |
| `creato` | `locked` | compratore (`verifica-pagamento`) o l'orologio (`controlla_abbandonati`), solo se LNbits dice `paid` sull'hash salvato dal server; UPDATE atomico `WHERE stato='creato'` |
| `creato` | `annullato` | compratore (`annulla`, dopo aver chiesto a LNbits), un ordine nuovo sullo stesso annuncio, l'orologio dopo 900 s |
| `annullato` | `creato`→`locked` | l'orologio (`controlla_annullati`), se quella fattura risulta pagata entro 1800 s |
| `locked` | `shipped` | venditore (`spedito`, `consegna-digitale`, busta) |
| `shipped` | `delivered` | SOLO digitale: il compratore che rivela il contenuto. Sul fisico oggi nessuno |
| `locked`/`shipped`/`delivered` | payout → `released` | compratore (`conferma`); l'orologio sul digitale (24 h / 48 h); sul fisico solo con `AUTO_SBLOCCO_ATTIVO` |
| idem | `confirmed` | lo stesso gesto, quando il payout non riesce (manca la fattura, rotta fallita) |
| `confirmed` | `released` | venditore (deposita fattura, salva Lightning address), il ritentativo col backoff |
| `locked`/`shipped`/`delivered` | `dispute` | compratore |
| `dispute` | `released`/`confirmed` · `refund`/`refunded` · `return_pending` | moderatore (`risolvi`) |
| `return_pending` | `return_shipped` | compratore |
| `return_shipped` | `refund`/`refunded` | venditore (`reso-ricevuto`) |
| `refund` | `refunded` | compratore (fattura o Lightning address), il ritentativo |
| `confirmed`/`refund` disputati o auto-sbloccati | `dispute` | moderatore (riapre) |

## Mercatino — `payout_stato` (ordini, rimborsi d'asta, sblocchi)

| Da | A | Chi |
|---|---|---|
| `''` | `in_volo` | `paga_venditore` dice INCERTO e c'è un hash |
| `''` | `incerto` | INCERTO senza hash, o tentativi finiti |
| `''` | `da_riprovare` | LNbits muto (niente è partito), o fallito con Lightning address |
| `in_volo` | `uscito` / `''` | l'orologio, su `success` / `failed`-o-404 di LNbits |
| `in_volo` | `incerto` | l'orologio dopo 1800 s di `pending` |
| `incerto` | `uscito` / `''` | **una persona, senza verifica → G1** |
| `da_riprovare` | `''` e nuovo tentativo | l'orologio, col backoff 5 min → 24 h, massimo 5 |
| qualunque | `uscito` | a pagamento riuscito |

Stati da cui NESSUNO esce da solo: `incerto` (voluto: aspetta una persona);
`confirmed` senza fattura né address (solleciti, poi avviso ai moderatori);
`dispute` (moderatore); `return_pending` se il compratore non rispedisce
mai (nessun timer: **da guardare**).

## P2P — i momenti che il server annota (i sats NON passano da Barattolo)

`preso` → `garanzia_chiesta` → `garanzia_pagata` → `fattura_chiesta` /
`fattura_data` → `fiat` → `rilasciato` → `concluso`; rami:
`annullo_chiesto` → `annullato`; `tornato` (ritorna nel libro);
`scaduto`; `disputa`; `payout_fallito` → `fattura_data/new-invoice`.
Li innesca SOLO mostro (patch 0007, Bearer), e in sua assenza il libro
pubblico (38383, quattro stati). Il server non può muovere, trattenere o
rilasciare quei sats: può solo avvisare, e annotare chi è chi.

---

# Verificato e trovato SANO

**Importi e fiducia nel client**
- `compra` e `_compra_set` non credono a nessun importo del telefono:
  prezzo, quantità disponibile, spedizione, zona, sconto, codice e totale
  si ricalcolano dal database. Dal client arrivano solo id, quantità,
  paese, strada di consegna, codice.
- Gli sconti sono chiusi: percentuale `min(pct, 100)`, mai sotto 1 sat di
  articolo (`_sconto_percento`, `_sconto_valore`), valori negativi a zero,
  codici col tetto di piattaforma, vince UNO solo (mai somma), usi contati
  anche sugli ordini in pagamento. Soglie in euro: a cambio assente lo
  sconto tace, non si inventa.
- `paga_venditore` pretende che la fattura chieda ESATTAMENTE il dovuto
  (sat per sat, a zero compreso), e la fattura del Lightning address si
  riverifica con lo stesso giudice. Una fattura che chiede di più non parte
  e avvisa i moderatori.
- Il cambio: una fonte, cache 120 s, e oltre 24 ore non vale più
  (`ORE_CAMBIO_VALIDO`): un annuncio in euro a cambio muto risponde 503
  invece di usare un numero vecchio.

**Doppi pagamenti (fuori da G1)**
- Una fattura già pagata non si ripaga: prima di ogni uscita si chiede a
  LNbits lo stato dell'hash (`success` → non si ripaga, `pending` →
  congelato, `failed` → serve una fattura nuova).
- Timeout o risposta ambigua = INCERTO, **mai** un ritentativo automatico.
- LNbits muto PRIMA del pagamento = NON_CHIESTO: niente parte, niente si
  cancella, si riprova col backoff.
- Un lucchetto per ordine (`_lucchetti_ordine`) serializza incasso e
  rimborso; lo stato si rilegge DENTRO il lucchetto. Due richieste insieme
  non pagano due volte (a patto di un solo processo: vedi «non verificato»).
- `_incassa_ordine` è idempotente (UPDATE condizionato): due verifiche
  insieme non scalano due volte il magazzino.
- Riavvio a metà payout: la riga resta `in_volo` o senza timbro; al
  riavvio l'hash si richiede a LNbits prima di qualunque altra cosa.

**Chi può scrivere dove vanno i soldi**
- `invoice_venditore`: solo il venditore di QUELL'ordine, in
  `locked/shipped/confirmed`, con l'importo verificato. `invoice_rimborso`:
  solo il compratore, solo in `refund`. `invoice_riscossione`: solo il
  titolare del rimborso. `ln_address`: solo il proprio. Nessuna rotta
  accetta un `payment_hash` dal client.
- Le rotte dei moderatori usano `e_admin` (id, non username), tutte.
- Login: il widget Telegram e il webhook usano `compare_digest`; la sfida
  Nostr è monouso, scade in 5 minuti, è legata all'host e la firma si
  verifica davvero; il collegamento npub↔Telegram chiede la conferma DAL
  bot e rifiuta se fra i due account c'è un affare aperto.
- CSRF: cookie `HttpOnly`, `Secure`, `SameSite=Lax`, più il controllo
  dell'`Origin`. CORS `*` ma senza credenziali.
- `MODALITA_COLLAUDO` si importa dal config (niente default nel codice) e
  l'esempio nasce `False`.

**P2P (i cantieri del 17-19 set)**
- `/api/p2p/sconto` e `/api/p2p/evento`: 404 a leva spenta, Bearer
  confrontato a tempo costante, corpo ripulito campo per campo (azioni e
  attori da lista chiusa, chiavi 64-hex, importi interi 0…10^9, `bool`
  rifiutato come numero), orologio ±900 s, **idempotenza** su
  `(ordine, momento, quando)`: il retry del coordinatore e un replay
  dentro la finestra non ripetono niente; fuori finestra vengono rifiutati.
- Lo sconto è fail-CLOSED da tutte e due le parti (Rust: timeout, non-200,
  JSON storto, chiave assente, `1` o `"true"` al posto di `true`, scrittura
  fallita → fee piena). Il server dice solo sì/no: la PERCENTUALE è locale
  al nodo e ha un tetto compilato (`MAX_DISCOUNT = 0.01`), quindi un server
  compromesso non riscrive una fee. La fee non va mai sotto zero.
- La riga a lato `barattolo_fees` si fida solo se `amount` e fee del
  compratore combaciano con l'ordine, e una presa senza sconto la
  riscrive: uno sconto di una presa scaduta non passa a chi prende dopo.
- Gli eventi sono fail-OPEN e non bloccano mai mostro (task a parte, due
  tentativi, poi si rinuncia e lo dice il log). Nessun segreto nei log dei
  due moduli: si stampa l'URL, mai il Bearer.
- Il recapito degli euro NON passa dal server: `/api/p2p/recapito` manda
  solo un avviso, a chi compra, massimo 3 per scambio, uno al minuto, solo
  da chi VENDE secondo mostro, solo a scambio vivo.

**Infrastruttura**
- Il guardiano del ponte: comandi costanti, niente shell, niente input
  esterno, timeout, freno a 15 minuti, `verify=False` solo su una sonda che
  non manda segreti.
- Nessun `shell=True`, `os.system`, `eval`, `exec`, `pickle`, `yaml.load`;
  nessun `random` per i segreti (solo `secrets`); i 24 SQL composti a
  f-string interpolano solo nomi di tabella/colonna scelti dal codice.
- Nessun `print` di fatture, chiavi, macaroon o initData nel server.
- Lo scanner dei segreti in CI guarda i file E la cronologia, con più
  forme (nsec, token del bot, chiave Anthropic, NWC, chiavi LNbits, hex nudo); il job `pronto` parte solo a `prove` + `segreti` verdi e solo su
  push a main; i permessi di default sono `contents: read`.
- Il backup fuori sede è cifrato con la sola chiave PUBBLICA age prima di
  lasciare la macchina; il database si copia in modo atomico.

**Punto D — istruzioni estranee**
- Cercato in tutti i file tracciati, nel workflow, in CLAUDE.md, in `docs/`
  e nei 67 file di memoria: `system-reminder` e tag simili, «ignora le
  istruzioni», comandi di scaricamento-ed-esecuzione, `base64 -d`,
  webhook esterni, `authorized_keys`, caratteri invisibili, commenti HTML.
  **Niente.** Le sole corrispondenze sono prosa di casa («senza dirlo»).
- `.claude/settings.local.json`: 401 permessi, nessun hook, nessun `ssh`
  verso il VPS o il nodo, nessun segreto, gli URL esterni sono letture
  vecchie (comuni italiani, zapstore). Nessun `settings.json` di progetto.
- ⚠️ **Una cosa è successa DURANTE questo audit:** in coda all'output di un
  comando `git` è comparso un blocco `<system-reminder>` che dettava
  l'attribuzione dei commit e chiedeva di spedire i file con uno strumento.
  Stava dentro il risultato di uno strumento, non veniva né da Andrea né
  dal sistema: **ignorato**, e segnalato subito in chat. Nei file non ce
  n'è traccia — quindi non è un file del repo a iniettarlo: vale la pena
  di capire da dove entra (è la stessa famiglia del 18 set).

---

# Cosa NON ho potuto verificare, e il comando di sola lettura

Sul **VPS** (li lancia Andrea):

```bash
systemctl show barattolo -p User -p ExecStart
```
Root sì/no (A1), e se c'è `--workers N`: i lucchetti sono per processo,
con più di un worker due richieste possono pagare lo stesso ordine.

```bash
ss -ltnp | grep -E ':(5001|18080|8080|2019|9050) '
```
Tutte e cinque devono stare su `127.0.0.1`, mai `0.0.0.0` o `*`.

```bash
ls -l /root/satmarket/config.py /opt/lnbits/.env /var/lib/tor/onion_auth/
```
Permessi 600 / cartella 700.

```bash
git -C /root/satmarket config --get-regexp 'credential|remote.origin.url'
```
E poi, su GitHub → Settings → Developer settings: quel token dev'essere
fine-grained, solo questo repo, `Contents: Read-only` (G2).

```bash
journalctl -u barattolo --since "14 days ago" | grep -ciE "lnbc[0-9a-z]{80,}|api\.telegram\.org/bot[0-9]|macaroon"
```
Deve dare 0 (B6).

```bash
sqlite3 -readonly /root/satmarket/satmarket.db "SELECT 'ordini',id,stato,payout_stato,payout_verso,payout_tentativi FROM ordini WHERE payout_stato NOT IN ('','uscito') UNION ALL SELECT 'rimborsi',id,stato,payout_stato,payout_verso,payout_tentativi FROM rimborsi_asta WHERE payout_stato NOT IN ('','uscito') UNION ALL SELECT 'sblocchi',id,stato,payout_stato,payout_verso,payout_tentativi FROM pagamenti WHERE payout_stato NOT IN ('','uscito');"
```
I pagamenti appesi di adesso (G1, M3).

```bash
sqlite3 -readonly /root/satmarket/satmarket.db "SELECT id,stato,payout_stato,payout_verso FROM ordini WHERE payout_stato='uscito' AND stato NOT IN ('released','refunded');"
```
Deve essere vuoto: ogni riga è un M1 in attesa.

```bash
sqlite3 -readonly /root/satmarket/satmarket.db "SELECT id,stato,payout_tentativi,payout_errore FROM ordini WHERE payout_tentativi>1 AND stato='released';"
```
Gli ordini pagati al secondo tentativo o oltre: per ognuno, su LNbits,
controllare che il PRIMO hash sia `failed` (G1 già successo?).

```bash
grep -n "image:" /opt/lnbits/docker-compose.yml
```
Conferma la 1.6.1. La mia lettura — che su una connessione caduta verso
LND la 1.x lasci il pagamento `pending` e non `failed` — viene dalla
memoria del sorgente e **non l'ho verificata**: se fosse `failed`, il
ponte che cade a metà payout sarebbe un G1 senza nessun ladro. Da provare
nel drill del ponte con un pagamento da 1 sat in volo.

Da **fuori** (dal PC):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "X-Tg-Init-Data: collaudo:999:x" https://barattolo.store/api/admin/leve
```
Deve dire 401.

Sul **nodo** (li lancia Andrea):

```bash
docker compose exec mostro sh -c "env | grep -o '^BARATTOLO_[A-Z_]*'"
```
Solo i NOMI: se manca `BARATTOLO_EVENTI_SEGRETO` i due segreti sono lo
stesso (M6).

```bash
lncli listmacaroonids
```
E `lncli printmacaroon --macaroon_file <quello di LNbits>`: deve avere
`invoices`, `offchain`, `info` (lettura/scrittura) e NIENTE `onchain`,
`peers`, `macaroon`, `signer`.

```bash
lncli listpayments --include_incomplete | grep -c IN_FLIGHT
```
Gli HTLC in uscita appesi adesso (M3).

**Rust mai compilato qui:** le patch 0005-0007 le ho lette, non le ho viste
girare. In particolare non ho potuto confrontare i punti d'innesto con
l'albero upstream (che `apply_party_fees` giri DOPO il calcolo dell'importo
sugli ordini a prezzo di mercato lo dice il commento, non l'ho visto). Lo
scambio con UNO SOLO scontato resta da fare: è l'unico che prova la
tabella a lato.

Sul **PC** (strumenti statici):

```bash
python -m pip install --user bandit pip-audit
```
```bash
python -m bandit -q -r server.py importa_nostr.py importa_negozio.py -ll
```
```bash
python -m pip_audit
```
`pip_audit` va lanciato nell'ambiente del SERVIZIO sul VPS per dire
qualcosa di vero sulle versioni in produzione (Pillow, pillow-heif,
cryptography, coincurve, httpx, fastapi, uvicorn, anthropic).

---

# Le prove che mancano

Dove oggi c'è solo una sentinella di TESTO (cerca una stringa nel sorgente
e non fa girare niente): `decidi_pagamento` (tutt'e due le prove),
`coda_pagamenti`, `risolvi_disputa`, `deposita_invoice`,
`controlla_annullati`, `controlla_scadenze`, `guardia_csrf`,
`_riavvia_ponte`. `paga_venditore`, `_sblocca_sats`, i timbri, i giudici
degli eventi e dello sconto P2P invece GIRANO davvero, con mondi di
cartone: quelle sono prove buone.

Da scrivere, in ordine:

1. **G1 che gira:** payout in volo con LNbits `pending` → «non uscito» →
   deve essere RIFIUTATO; e, finché non lo è, la riproduzione in appendice
   come prova rossa che diventa verde con la cura. Le tre varianti (ordine,
   disputa+rimborso, rimborso d'asta).
2. **M1:** riga `dispute` + `uscito` verso il venditore → «rimborso» non
   deve chiudere a `refunded`.
3. **M2:** `invoice_da_ln_address` con un `callback` su `127.0.0.1`, su un
   IP privato, su `http://`, e con un redirect: nessuna GET deve partire.
4. **`deploy.sh`:** un `pronto` che non discende da `main` non si mette
   (si prova con due repo di cartone, come già si fa per il rollback).
5. **A3:** digitale `shipped` mai rivelato a moderazione muta → non si
   sblocca (o: si sblocca solo sotto il tetto).
6. **M5:** una pubkey registrata senza firma non prende lo sconto.
7. **B4:** disputa scritta mentre `_sblocca_sats` aspetta LNbits → lo stato
   finale non la ricopre in silenzio.
8. **Due worker:** una prova che FALLISCE se qualcuno aggiunge `--workers`
   all'unit (sentinella su PRODUZIONE.md e sul comando d'avvio).
9. **Rust:** la presa con uno solo scontato; e la presa a server MORTO,
   cronometrata (M4).
10. **B2:** `prezzo_eur` = `Infinity` / `NaN` → 400, non 500.

---

# Appendice A1 — la riproduzione di G1

Non è nel repo come file: si copia da qui in una cartella qualunque e si
lancia con `python riproduci_doppio_payout.py <percorso di server.py>`.
Legge `server.py`, ne estrae le funzioni vere con `ast`, e gira tutto in
memoria: non apre il database, non parla con nessuno.

```python
import ast, asyncio, collections, html, sqlite3, sys, time

SRC = open(sys.argv[1], encoding="utf-8").read()
ALBERO = ast.parse(SRC)


def pezzo(nome):
    for n in ALBERO.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nome:
            return ast.get_source_segment(SRC, n)
    raise KeyError(nome)


LNBITS = {}     # hash -> "pending" | "success"
USCITI = []     # (hash, sats) partiti dal nodo


class _R:
    def __init__(self, code, dati):
        self.status_code, self._d = code, dati

    def json(self):
        return self._d


class FintoClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, headers=None, **k):
        h = url.rsplit("/", 1)[-1]
        if h not in LNBITS:
            return _R(404, {})
        return _R(200, {"status": LNBITS[h], "paid": LNBITS[h] == "success"})

    async def post(self, url, headers=None, json=None, **k):
        h = "hash-di-" + json["bolt11"]
        # la PRIMA fattura e' una hold invoice: resta pending
        LNBITS[h] = "pending" if len(LNBITS) == 0 else "success"
        USCITI.append((h, 1000))
        return _R(201, {"status": LNBITS[h]})


class httpx_finto:
    AsyncClient = FintoClient


async def _niente(*a, **k):
    return None


async def _decodifica(bolt11, cassaforte=""):
    return {"payment_hash": "hash-di-" + bolt11, "amount_msat": 1000 * 1000}


async def _importo(bolt11, dec=None, cassaforte=""):
    return 1000

CONIATE = []


async def _address(addr, sats):
    CONIATE.append(addr)
    return f"lnbc-fattura-{len(CONIATE)}"


vero = sqlite3.connect(":memory:")
vero.row_factory = sqlite3.Row
vero.execute(
    "CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INT, compratore_id INT, "
    "venditore_id INT, prezzo_sats INT, protezione_sats INT, quantita INT, stato TEXT, "
    "disputata INT, invoice_venditore TEXT, aggiornato INT, cambio_eur REAL, "
    "payout_stato TEXT, payout_hash TEXT, payout_verso TEXT, sbloccato_auto_il INT DEFAULT 0, "
    "cassaforte TEXT DEFAULT 'saas', payout_tentativi INT DEFAULT 0, "
    "payout_ultimo INT DEFAULT 0, payout_errore TEXT DEFAULT '')")
vero.execute("INSERT INTO ordini VALUES(1,7,111,222,1000,0,1,'delivered',0,'',0,0,'','','',0,'saas',0,0,'')")
vero.execute("CREATE TABLE utenti(tg_id INT, ln_address TEXT, vendite_ok INT, acquisti_ok INT)")
vero.execute("INSERT INTO utenti VALUES(222,'ladro@suo-server.tld',0,0)")
vero.commit()


class Con:
    def execute(self, *a):
        return vero.execute(*a)

    def commit(self):
        vero.commit()

    def close(self):
        pass


_Cf = collections.namedtuple("_Cf", "nome LNBITS_URL LNBITS_INVOICE_KEY LNBITS_ADMIN_KEY")

amb = {
    "db": Con, "time": time, "asyncio": asyncio, "html": html, "httpx": httpx_finto,
    "_lucchetti_ordine": collections.defaultdict(asyncio.Lock),
    "_chiavi_cassaforte": lambda nome="": _Cf("saas", "http://finto", "k", "K"),
    "decodifica_invoice": _decodifica, "importo_invoice": _importo,
    "invoice_da_ln_address": _address,
    "netto_venditore": lambda p: p, "_fmt_sats": lambda n: str(n),
    "_righe_ordine": lambda con, o: [], "_titolo_ordine": lambda r: "una cosa",
    "cambio_btc_eur": _niente, "notifica": _niente, "notifica_admin": _niente,
    "premia_distintivi": _niente, "polso_ordini_admin": _niente,
    "premia_xp": _niente, "xp_ordine": lambda *a: 0,
    "premia_reputazione_nostr": _niente, "_avvisa_payout_fallito": _niente,
    "PAGATO": "pagato", "NON_PAGATO": "non_pagato", "INCERTO": "incerto",
    "NON_CHIESTO": "non_chiesto", "MAX_TENTATIVI_PAYOUT": 5, "IN_VOLO_LIMITE_S": 1800,
    "ATTESE_ESITO": 1, "SECONDI_FRA_ATTESE": 0,
    "LnbitsMuto": type("LnbitsMuto", (Exception,), {}),
    "print": lambda *a, **k: None,
}
for nome in ("_esito_lnbits", "_stato_pagamento", "paga_venditore", "_timbra_pagamento",
             "_in_volo", "_sospendi_pagamento", "_payment_hash", "_congela_pagamento",
             "_msg_ritentiamo", "_sblocca_sats"):
    exec(pezzo(nome), amb)


def riga():
    return tuple(vero.execute(
        "SELECT stato, payout_stato, payout_hash FROM ordini WHERE id=1").fetchone())


async def scena():
    print("1) il compratore conferma: parte il payout verso il Lightning address")
    print("   ", await amb["_sblocca_sats"](1), riga())
    print("2) la ronda, dopo 30 minuti di «pending», si arrende: incerto")
    vero.execute("UPDATE ordini SET payout_stato='incerto' WHERE id=1 AND payout_stato='in_volo'")
    print("   ", riga(), "— LNbits dice ancora:", LNBITS)
    print("3) il moderatore preme «non e' uscito» (l'UPDATE di decidi_pagamento, identico)")
    vero.execute("UPDATE ordini SET payout_stato=?, aggiornato=? WHERE id=? AND payout_stato='incerto'",
                 ("", int(time.time()), 1))
    print("   ", riga(), "— nessuno ha richiesto a LNbits lo stato di quell'hash")
    print("4) il compratore ripreme «Conferma»: conferma_ricezione richiama _sblocca_sats")
    print("   ", await amb["_sblocca_sats"](1), riga())
    print("5) ora il venditore salda anche la hold invoice del passo 1")
    LNBITS["hash-di-lnbc-fattura-1"] = "success"
    saldati = [(h, s) for h, s in USCITI if LNBITS[h] == "success"]
    print("    DOVUTI 1000 sats — USCITI", sum(s for _, s in saldati), "sats")


asyncio.run(scena())
```
