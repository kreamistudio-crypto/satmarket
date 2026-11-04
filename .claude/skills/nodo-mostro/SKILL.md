---
name: nodo-mostro
description: Le regole del nodo Mostro P2P di Barattolo (l'ALTRA macchina, su LNVPS a Dublino): riavvii, ronda, backup, timer, dev fee, macaroon. Usala ogni volta che si parla del nodo, di mostrod, LND, dei canali o si scrivono comandi da far girare là.
---

# Il nodo Mostro (un'ALTRA macchina)

⚠️ Non è il VPS di Barattolo: è il coordinator Mostro P2P su LNVPS
(Dublino, `185.18.221.96`), tutto in container (bitcoind pruned, LND,
tor, mostrod), tre canali (`/canali`, 12 ott 2026): LNBiG [Hub-2] 5M,
ACINQ 1M e ACINQ 400k. Gira il nostro fork di Mostro: la versione e le
patch sono in `docs/PRODUZIONE.md` (cerca «LA SALITA ALLA»). Il verbale
— audit, timer, sonda, dev fee, risposte del team — sta in
`docs/NODO-MOSTRO.md` (cerca la sezione con la skill `cerca-nei-docs`).

Le regole:

- L'AUDIT DI SICUREZZA È FATTO (2 set 2026): non riproporre le sue sei
  domande come «da fare». Il documento `auditnodomostro202609` sta nel
  canale Telegram del nodo, coi perché: si chiede quello. I canali
  Telegram NON sono cifrati end-to-end: lì solo documenti SENZA segreti
  (mai `settings.toml`, nsec, macaroon); per i segreti l'archivio age.
- Modalità guarda-e-riferisci: i comandi li scrivo, li esegue Andrea.
  Il riavvio si fa dal compose, `docker compose restart mostro` da
  `~/nodo` (il container si chiama `nodo-mostro-1`); dopo un `restart
  mostro-net` sempre `up -d --force-recreate mostro` (PRODUZIONE, «IL
  NAMESPACE PRESTATO»).
- LA RONDA finisce con `--- fine ronda`: senza quella riga un `exit 0`
  a metà script si è mangiato un pezzo (successo due volte).
- IL BACKUP non contiene `channel.db`, ed è voluto (per i canali esiste
  solo l'SCB); cifra con la sola chiave pubblica age e il PC tira in pull.
- `pow_first_contact` resta SPENTO finché il termometro degli eventi non
  salta di un ordine di grandezza senza utenti nuovi. `expiration_seconds`
  è 1800 dal 10 ott 2026: è il tempo di chi PRENDE, e non si allunga. Chi
  PUBBLICA ha 3 ore dalla `-bar8` (`maker_expiration_seconds`, decisione del
  12 ott): il contrappeso è la penalità (NODO-MOSTRO, «LA REGOLA, RISCRITTA»).
  `hold_invoice_expiration_window` resta 900: scade solo la richiesta di
  CAUZIONE, la garanzia no (letto sul nodo). La dev fee sta a
  `dev_fee_percentage = 0` per il circuito Tor freddo (difetto upstream):
  NON esentare i due domini LNURL da Tor, un IP che bussa lì si dichiara
  coordinator.
- L'admin macaroon NON serve e non si dà: il ristretto ha retto lo
  scambio vero del 7 set 2026. Il secondo macaroon, dedicato a LNbits e
  revocabile da solo (`root_key_id 1`), vive sul VPS (Cantieri, «Il
  doppio wallet»; il ponte: PRODUZIONE, «IL PONTE VIA WIREGUARD»).
- La scadenza di `expiration_seconds` è PROVATA dal vivo dal lato di chi
  ha pubblicato (10 ott 2026: scambio annullato). Restano NON provati la
  riconsegna al libro e i 576 blocchi del `cltv_delta` (tappa 8).
