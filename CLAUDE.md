# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Dove sta il resto

I documenti in `docs/` NON sono import: si aprono quando servono.
- `docs/ARCHITETTURA.md` — com'è fatto: le parti, le rotte pubbliche, i
  giudici unici, e il perché di ogni pezzo.
- `docs/CANTIERI.md` — perché è fatto così: un paragrafo per cantiere,
  in ordine di tempo, con le decisioni, le strade scartate e le lezioni.
  Le voci più vecchie di 30 giorni stanno in
  `docs/CANTIERI-ARCHIVIO-2026.md` (intere; in CANTIERI resta l'indice
  dei titoli).
- `docs/PRODUZIONE.md` — la macchina, la catena del deploy, le procedure.
- `docs/NODO-MOSTRO.md` — il coordinator P2P su un'ALTRA macchina:
  audit, timer, sonda, dev fee, coi perché.
- Gli audit `docs/AUDIT-PAGAMENTI-2026-09-19.md` e
  `docs/AUDIT-2-CLIENT-MOSTRO-2026-09-23.md`; gli studi
  `docs/STUDIO-BOLT-CARD-2026-09-24.md`,
  `docs/STUDIO-RISTORANTI-2026-09-24.md`,
  `docs/STUDIO-CONTANTI-A-MANO-2026-09-25.md` e
  `docs/STUDIO-MOSTRO-0190-2026-09-30.md` (la 0.19.0 in preparazione).

I DOCUMENTI GRANDI NON SI LEGGONO MAI INTERI: CANTIERI (2 MB),
ARCHITETTURA (2 MB) e PRODUZIONE sono da migliaia di righe, e una
lettura intera costa più di tutto il cantiere. Si cerca la SEZIONE che
serve — `grep -n "sconto carrello" docs/*.md` sul titolo o sulla parola
chiave, che ogni voce porta nella prima riga — e si legge SOLO quella
(`sed -n` sull'intervallo). Non c'è un indice e non deve nascerne uno.
I rimandi già scritti nel codice («vedi Architettura, "IL SUPPLEMENTO
PER PEZZO"») sono indirizzi da cercare così.
PRIMA di toccare qualcosa, cercalo lì: se un cantiere l'ha già deciso,
la decisione ha un perché scritto, e rovesciarla senza saperlo è il
modo in cui si rifà un errore già pagato.

## Come si lavora in ogni sessione

- SOLO QUELLO CHE CHIEDE (regola di Andrea): si consegna esattamente la
  cosa chiesta, con le sue prove. Quel che si nota strada facendo va in
  fondo alla risposta come elenco, una riga per voce, e lì si ferma
  finché non arriva un sì. Unica eccezione: riparare una regressione
  introdotta da me facendo la cosa chiesta.
- LAVORO DIRETTO: niente Workflow né fan-out di subagenti per un
  cantiere normale, anche con «ultracode» acceso. Un fan-out si PROPONE
  in una riga e si aspetta il sì.
- PRIMA DI APRIRE UN CANTIERE: `git fetch`, `gh pr list --state open` e
  `git ls-remote --heads origin` — Alan lavora per PR e altre sessioni
  pushano: lo stesso argomento può essere già in revisione.
- IL WORKTREE È LA CARTELLA DI LAVORO, sempre. Andrea tiene più sessioni
  aperte sulla stessa working copy, quindi lì dentro compaiono modifiche
  altrui che non si toccano e non si committano. Si lavora in
  `git worktree add -b cantiere/<nome> .claude/worktrees/<nome> origin/main`
  e si fa TUTTO là: edit, prove, commit, push. Se le prove vogliono
  `config.py`, la copia nel worktree si cancella prima del commit (è un
  segreto in una cartella in più). Mai `git add -A`, mai `git commit -a`,
  mai un `git stash` nudo (la pila è condivisa).
- IL COMMIT SI FIRMA, e la punta si controlla PRIMA del push: il VPS tira
  solo una punta firmata, e una CI verde non lo dice. `git commit` firma
  da solo (config globale); `git commit-tree` è plumbing e firma SOLO
  con `-S`. Prima di ogni push:
  `git cat-file commit HEAD | grep -c '^gpgsig'` deve dire 1.
- IL PUSH È MIO, IL DEPLOY È SUO. Si pusha su `main` (mai su un ramo: il
  deploy prende solo main) SENZA chiedere, a due condizioni: cantiere
  CHIUSO (committato, provato, collaudato, verbale scritto) e prove
  verdi nel worktree con `PROVE_SEVERE=1 python prove.py` più i collaudi
  della CI. Poi `git push origin HEAD:main` e la CI fino al verde
  (`gh run watch --exit-status`). Un «non pushare ancora» di Andrea
  vince sulla regola finché non lo scioglie. Se main è corso nel
  frattempo: rebase, sezioni toccate + collaudi, push; nel verbale si
  scrive COSA è girato su QUALE albero. I commit non miei che il push
  porta con sé si NOMINANO nel rapporto.
- IL VPS È FUORI DAL MIO PERIMETRO: niente ssh, niente query, nemmeno in
  sola lettura. I comandi li scrivo, li esegue Andrea e incolla il
  risultato. Il deploy è suo. Lo stesso vale per il nodo Mostro e per il
  relay.
- MAI RELAY VERI IN COLLAUDO E NEI GIRI DAL VIVO, mai eventi pubblicati:
  il server si ferma da solo (`lettura_simulata`, solo loopback), il
  BROWSER no — nel config del giro `MOSTRO_RELAY` e
  `MOSTRO_RELAY_SPECCHIO` vanno al relay morto (`ws://127.0.0.1:9`) e la
  nsec a `INCOLLA_QUI`. Mai copiare il `config.py` locale (ha una nsec
  di prova). Un collaudo nuovo si prova prima nella gabbia
  (`python collaudi_ci.py collaudo_x`).
- PULIZIA A FINE GIRO, dopo il push verde: si esce dal worktree,
  `git worktree remove --force <il mio>`, `git worktree prune`, e via i
  rami dei cantieri già su origin/main (`git branch --merged origin/main
  --list "cantiere/*"` + `-d`). Un worktree altrui con modifiche non
  committate si LASCIA e si dice perché.
- COSA NON SI TOCCA: `config.py`, `*.db`, `foto/`, chiavi, token (regola
  ferrea 1); gli header anti-cache di `/` e `/miniapp.html`; il ref
  `pronto` (spostarlo è un gesto di deploy: si chiede ad Andrea); il
  numero `TETTO_CLAUDE_MD` in `prove.py` se non cambiano davvero le
  regole. Dopo ogni ritocco a questo file: `wc -l CLAUDE.md` sotto il
  tetto, o la CI è rossa e il deploy non parte.

## Produzione

- VPS Hetzner Helsinki `46.62.162.103`, Ubuntu 26.04, servizio systemd
  `barattolo` (uvicorn su 127.0.0.1:8080 dietro Caddy con HTTPS), che
  gira da `barattolo`, MAI da root.
- Dominio: https://barattolo.store — Bot: @ilbarattolobot (BotFather URL
  con `?v=2`, innocuo). Header anti-cache già attivi su `/` e
  `/miniapp.html`: non rimuoverli.
- IL CONFIG DEL VPS VINCE SUL DEFAULT DEL CODICE: una riga esplicita là
  (es. `MAX_PREFERITI = 20`, mentre il codice dice 10) tiene in vita il
  valore vecchio finché non si cambia o cancella a mano, e riavvia. Si
  guarda PRIMA del deploy, in sola lettura: `grep -n "MAX_PREFERITI"
  ~/satmarket/config.py`. Le leve nuove (`P2P_ATTIVO`, `MOSTRO_NPUB`...)
  si AGGIUNGONO al config del VPS: non compaiono da sole.
- DEPLOY AUTOMATICO: commit+push su main, e basta; entro un minuto è
  online se la CI è verde. Config e database NON viaggiano mai. IL VPS
  TIRA (`deploy.sh` ogni minuto) e dal 21 set 2026 tira un commit SOLO
  se sta su main, va in avanti, ha la CI verde (token di SOLA LETTURA)
  e la punta FIRMATA da una chiave scritta sul VPS; sennò «⛔ Deploy
  rifiutato». IL FRENO: un commit bocciato dal rollback si timbra in
  `.deploy-bocciato` e non si riprova da solo — si spinge un commit
  nuovo, o `./deploy.sh --forza` a mano guardando. Dopo un commit che
  tocca `.github/workflows/` il ref `pronto` può restare indietro: si
  guarda (`git ls-remote origin refs/heads/pronto refs/heads/main`), non
  si dà per scontato. La catena intera, `/api/salute`, il backup
  pre-deploy, le procedure (leve del P2P, import Nostr, anello,
  `/setdomain`, dipendenze pip): PRODUZIONE.
- Webhook del bot: `TELEGRAM_WEBHOOK_SEGRETO` nel config del server e al
  riavvio si registra da solo (riga «🔔 Webhook Telegram» nel journal).
  ATTENZIONE: mai avviare MODALITA_COLLAUDO=False col BOT_TOKEN vero
  fuori dal VPS — ruberebbe il webhook (e quindi i /start) alla
  produzione.

## Il nodo Mostro (un'ALTRA macchina)

⚠️ Non è il VPS di Barattolo: è il coordinator Mostro P2P su LNVPS
(Dublino, `185.18.221.96`), tutto in container (bitcoind pruned, LND,
tor, mostrod), canale da 400.000 sat verso ACINQ. Gira il nostro fork
di Mostro (immagine `mostro:v0.18.8-bar5`: PRODUZIONE, «LA SALITA A
MOSTRO 0.18.8»). Tutto il verbale — audit, timer, sonda, dev fee,
risposte del team — sta in `docs/NODO-MOSTRO.md`. Le regole che valgono
in ogni sessione:
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
  salta di un ordine di grandezza senza utenti nuovi. I 900 secondi di
  `expiration_seconds` restano 900 (opzione gratuita sul cambio: la cura
  sono i bond, non la finestra). La dev fee sta a `dev_fee_percentage =
  0` per il circuito Tor freddo (difetto upstream): NON esentare i due
  domini LNURL da Tor, un IP che bussa lì si dichiara coordinator.
- L'admin macaroon NON serve e non si dà: il ristretto ha retto lo
  scambio vero del 7 set 2026. Il secondo macaroon, dedicato a LNbits e
  revocabile da solo (`root_key_id 1`), vive sul VPS (Cantieri, «Il
  doppio wallet»; il ponte: PRODUZIONE, «IL PONTE VIA WIREGUARD»).
- Restano NON provati la scadenza di `expiration_seconds`, la riconsegna
  al libro e i 576 blocchi del `cltv_delta` (tappa 8 del client P2P).

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI chiedere o gestire nsec (chiave privata Nostr) degli utenti.
   Decisione permanente: mai custodia di segreti altrui, mai firme che
   richiedano di consegnare chiavi al server. La scala di quel che è
   APPROVATO — badge npub auto-dichiarato, verifica con nota pubblica,
   login con firma di sfida, wallet NWC solo-nel-browser, DM NIP-17,
   sessione bunker NIP-46 conservata — col perché di ognuna e quel che
   è stato RESPINTO (il secret NWC salvato sul server, anche cifrato)
   sta in `docs/ARCHITETTURA.md`, alla voce «LA SCALA NOSTR APPROVATA».
3. Il server pubblico non monta MAI StaticFiles su una directory
   (config e .git diventerebbero pubblici — falla già successa e
   chiusa): ogni file servito ha la sua rotta esplicita, e i nomi che
   arrivano dal client passano da una whitelist. Non c'è più NESSUN
   mount: anche `/foto/*` è una rotta con la sua whitelist di FORME
   (`NOME_FOTO`). L'elenco completo sta in `docs/ARCHITETTURA.md`, alla
   voce «LE ROTTE PUBBLICHE». Una sentinella di `prove.py` fallisce se
   in server.py ricompare `app.mount(` o l'import di StaticFiles, e una
   seconda conta le rotte-pagina contro l'elenco di `prove_anteprime`.
4. Stati ordine: creato | locked | shipped | delivered | confirmed |
   released | dispute | return_pending | return_shipped | refund |
   refunded | annullato. Non inventarne di nuovi senza aggiornare
   frontend (STATES, stepper cassaforte) e notifiche.
5. Solo l'ACQUIRENTE può segnare "consegnato" (anti-frode venditore).
   Dall'ago 2026 A MANO non la scrive più NESSUNO (il bottone «È
   arrivato» è stato tolto perché puniva chi lo premeva). LA REGOLA
   RESTA: il giorno del tracking verificato quella data la scriverà il
   corriere, cioè un fatto, mai la parte che ci rimette; sul digitale
   la scrive la rivelazione del codice, gesto del compratore. Il
   venditore è protetto dall'auto-sblocco a 10 giorni (oggi disarmato:
   al suo posto il promemoria) e dal sollecito (max 1 ogni 24h).
6. Testare sempre in locale (MODALITA_COLLAUDO=True, tre identità finte:
   Compratore 111, Venditore 222, Admin 999) prima del deploy.
   In collaudo e nei giri dal vivo mai relay veri (vedi sopra).
   In produzione MODALITA_COLLAUDO deve restare False.
7. Stile del codice esistente: commenti e nomi in italiano, tono caldo,
   niente refactoring di massa non richiesti, diff piccoli e verificabili.
8. A fine cantiere, PRIMA del commit finale: la voce del cantiere —
   cosa si è deciso, i perché, le strade scartate, cosa è stato provato
   e cosa resta da guardare — va in fondo a `docs/CANTIERI.md`.
   L'architettura va in `docs/ARCHITETTURA.md`, le procedure di
   produzione in `docs/PRODUZIONE.md`, il nodo in `docs/NODO-MOSTRO.md`.
   Questo file si tocca SOLO se è cambiata una REGOLA di qui: rientra
   intero a ogni sessione e a ogni /compact, e ha un tetto provato
   (`TETTO_CLAUDE_MD` in prove.py). Proponilo come commit separato,
   senza aspettare che Andrea lo chieda. Ritocchi minori (testi,
   tarature, fix) non lo richiedono.
9. Lessico dell'escrow (lug 2026): nei testi per gli utenti si dice
   sempre «deposito di garanzia» — «(escrow)» solo nella prima
   spiegazione lunga di ogni contesto; azione = «🔒 Compra in
   sicurezza»; MAI «assicurato». «Escrow» resta solo dove il pubblico è
   bitcoiner: memo della invoice LNbits e testi verso Nostr (footer
   NIP-99, presenta_release). Il barattolo 🫙 è dei preferiti, mai
   metafora dell'escrow. La scheda «Affari» si chiama «Ordini» (testi
   utente sempre «Ordini», id interni invariati).

## Adesso

Lanciando in rodaggio su community italiana, senza limiti di prezzo
attivi (la leva `TETTO_SATS_ANNUNCIO` esiste ma è spenta). Quali leve
sono ACCESE lo dice il pannello «⚙️ Stato delle leve» dell'admin, che
chiede al valore VIVO e non alla costante nel codice.

Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri (che porterà la MAPPA dei punti nel
varco-mappa della pagina), escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.

Da riprendere quando i cantieri in corso saranno chiusi (ago 2026,
segnati da Andrea — non sono ancora decisi, sono da riprendere): il
LUOGO DEL RITIRO A MANO salvato e richiamato a ogni annuncio; «I MIEI
ANNUNCI» resa più fruibile; i PRIVILEGI DEI PIONIERI (la coorte esiste
già, non dà ancora niente); il LOCKER DI RISERVA (un secondo punto se il
primo non va).
