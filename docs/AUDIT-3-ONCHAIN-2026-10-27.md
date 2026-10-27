# Audit 3 — il pagamento on-chain 2-di-3 del mercatino (27 ott 2026)

Richiesta di Andrea, a chiusura del cantiere della disputa on-chain:
«fai un audit di sicurezza per tutto questo cantiere e dimmi se ci sono
delle decisioni da prendere». Guardato: il codice del ramo `onchain`
(server.py, miniapp.html, collaudo_onchain_ordine.py, backup-fuori.sh)
come sta dopo il cantiere onchain-disputa. Non guardato: il VPS, il nodo,
il bundle bitcoin (è di terzi, auditato Cure53, e la prova doppia lo
confronta con embit). Oggi la rete è SOLO signet: niente di quel che
segue costa sats veri finché non si passa a mainnet.

## In breve

Il disegno regge: nessuna delle tre chiavi da sola sposta i sats, il
telefono rifà l'indirizzo prima di mostrare il QR e rifà i conti prima
di ogni seconda firma, l'incasso del venditore è firmato dal suo seme,
la chiave di Barattolo firma solo dopo una decisione scritta e mai per
un moderatore che è parte. I punti sotto sono in ordine di peso. Le
DECISIONI per Andrea sono segnate così: **DECISIONE**.

## 1. Il server che serve l'app è anche quello che vede tutto (strutturale)

Il seme di ogni utente vive nel suo telefono, ma il codice che lo usa
(`miniapp.html`) lo serve il VPS. Chi prende il VPS può servire una
pagina modificata che legge il seme da `localStorage` e lo manda fuori:
a quel punto ha due chiavi su tre di ogni ordine di chi apre l'app.
Il «non custodial» vale finché la pagina servita è onesta. La CSP
(`script-src 'self'`) chiude l'iniezione da contenuti degli utenti, non
questo caso.

**DECISIONE** (prima di mainnet): accettarlo e dirlo nella scheda Info,
oppure servire la parte che tocca il seme da un posto che il VPS non
può cambiare (l'APK firmato di `barattolo-releases`, o un hash pubblicato
che il telefono controlla). Consiglio: dirlo subito nelle Info, e
legarlo all'APK prima di alzare il tetto.

## 2. Il tetto di 250 € dello studio non c'è nel codice

Lo studio fissa `ONCHAIN_MAX_EURO = 250` per la beta, e anche
`ONCHAIN_TETTO_TOTALE_SATS`. Nel codice nessuna delle due esiste: un
ordine on-chain può valere qualunque cifra. Su signet non conta.

**DECISIONE**: metterli prima di mainnet (consiglio: sì, come il P2P),
con le leve nel pannello.

## 3. «Pagato» lo dice una sola fonte (mempool.space)

L'ordine nasce «locked» quando l'API mempool dice che i sats sono
arrivati con una conferma. Il telefono del venditore non lo ricontrolla.
Un'API sbagliata, manomessa o finta (la leva `ONCHAIN_MEMPOOL_API` sta
nel config, non nel pannello: bene) farebbe spedire un oggetto non
pagato.

**DECISIONE** (prima di mainnet): due fonti che devono dire la stessa
cosa, o il bitcoind del nodo. Consiglio: due API pubbliche diverse per
la beta, il nodo dopo.

## 4. La chiave di Barattolo sul VPS (decisa oggi da Andrea)

Sta in `chiavi/onchain-barattolo.json`, 0600, in chiaro sul disco, e
nell'archivio age del backup. Firma solo dentro `_onchain_decide`.
Rischio residuo: chi prende il VPS ha la terza chiave. Da sola non
basta, ma insieme a una parte sì: un attaccante che compra da un
venditore, paga, riceve l'oggetto e poi si firma il rimborso con la
chiave di Barattolo. Il danno resta limitato agli ordini in cui
l'attaccante è parte. Il punto 1 è più grave di questo.

Il pannello non mostra le parole, ed è voluto. Mostra se l'ultimo
backup fuori sede la contiene.

**DECISIONE**: cifrare il file anche sul disco (con una chiave nel
config, cioè sulla stessa macchina) aggiunge poco. Consiglio: no, e
lasciare il backup age com'è.

## 5. La firma data esce dal nostro controllo

Due casi con la stessa radice: un PSBT con una firma può essere finito
e trasmesso da chi ha l'altra chiave, anche senza passare dal server.
- «Libera i sats»: appena chi compra firma, il venditore ha in mano il
  PSBT e può trasmetterlo con Sparrow anche se poi chi compra apre una
  disputa. Il blocco della seconda firma in disputa è solo del server.
  È come sul Lightning, dove la conferma è definitiva; va detto nel
  foglio di conferma.
- La firma di Barattolo in disputa: per questo non si ridecide (409).

Conseguenza pratica: una transazione trasmessa fuori dal server non
viene vista. La ronda guarda solo gli ordini «in attesa», quindi
l'ordine resterebbe «in disputa» o «spedito» per sempre.

**DECISIONE**: far guardare alla ronda anche gli ordini pagati, e
chiuderli quando le loro monete sono state spese con la transazione
proposta. Consiglio: sì, è piccolo.

## 6. Nessun ramo di recupero a tempo

Se si perdono due chiavi su tre, i sats restano bloccati per sempre.
Per esempio: il venditore sparisce e la chiave di Barattolo va persa,
oppure muore il telefono di chi compra senza backup e poi c'è una
disputa. Lo studio lo mette fra le cose da decidere prima di alzare il
tetto.

**DECISIONE** (prima di mainnet): un ramo «dopo N mesi basta Barattolo
da solo», con il suo peso legale (domanda MiCA dello studio). Oppure
niente ramo e un backup della chiave di Barattolo provato davvero.

## 7. Commissioni alte: i sats possono restare fermi

Il margine per la rete è 3 volte la tariffa al momento della cassa. Se
le commissioni salgono oltre il margine, né il rilascio né il rimborso
passano dal giudice. Manca RBF/CPFP (lo dice già CANTIERI). Su signet
non succede.

**DECISIONE**: alzare il margine, o permettere un'uscita «paga la rete
chi incassa» oltre il margine. Consiglio: la seconda, prima di mainnet.

## 8. La chiave di cartone su mainnet

Senza file e senza `ONCHAIN_XPUB` il server usa la chiave di cartone,
la cui privata è pubblica. Oggi su mainnet non si calcola nessun
indirizzo (`ONCHAIN_RETE` è una costante "signet"), quindi è chiuso. Il
giorno di mainnet serve una serratura che rifiuti la chiave di cartone.
Non è una decisione, è da fare in quel cantiere: lo segno qui perché
non si dimentichi.

## 9. Il moderatore che è parte

On-chain un moderatore che è parte dell'ordine non decide (403, da
oggi). Sul Lightning la stessa guardia non c'è.

**DECISIONE**: estenderla al Lightning. Consiglio: sì, è una riga, ed è
lo stesso principio di trasparenza.

## 10. Il seme nel telefono e nel cloud di Telegram

Nel telefono il seme sta in `localStorage` in chiaro. Le copie stanno
nel CloudStorage di Telegram e in Nostr (NIP-44). Chi ruba l'account
Telegram ritrova il seme nel cloud, a meno che non ci sia il PIN della
«Protezione extra». Lo studio l'ha accettato con la soglia
`ONCHAIN_PROTEZIONE_SOGLIA_EURO`, che nel codice non esiste ancora.

**DECISIONE**: rendere il PIN obbligatorio sopra una soglia, come nello
studio. Consiglio: sì, insieme al tetto del punto 2.

## Cosa è a posto (controllato)

- Il telefono rifà il 2-di-3 dalle tre chiavi prima di mostrare il QR
  («non pagare» se non torna), e prima di ogni firma.
- La destinazione del venditore (indirizzo o vpub) è firmata dal suo
  seme e riletta dal suo telefono prima della co-firma.
- Il server giudica ogni PSBT: le monete giuste, il prezzo esatto, la
  quota esatta, nessuna uscita estranea, niente polvere, la rete dentro
  il margine, la firma di chi propone.
- Le leve dei soldi (`ONCHAIN_XPUB`, `ONCHAIN_MEMPOOL_API`) non si
  cambiano dal pannello.
- La chiave di Barattolo nasce una volta sola (O_EXCL), non esce in
  nessuna risposta, entra nel backup age, firma solo dopo una
  decisione, e ogni firma viene detta agli admin.
- Le rotte sono dietro il cancello (404 a leva spenta), col freno sui
  gesti di firma; chi non è parte di un ordine riceve 404.
