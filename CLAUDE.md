# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Dove sta il resto

I documenti in `docs/` NON sono import: si aprono quando servono.
- `docs/ARCHITETTURA.md` (com'è fatto, il perché di ogni pezzo),
  `docs/CANTIERI.md` (un paragrafo per cantiere: decisioni, strade
  scartate, lezioni; le voci più vecchie di 30 giorni, intere, in
  `docs/CANTIERI-ARCHIVIO-2026.md`), `docs/PRODUZIONE.md` (la macchina,
  il deploy, le procedure), `docs/NODO-MOSTRO.md` (il nodo P2P),
  `docs/COLLAUDO.md` (la VM), `docs/DA-FARE-ANDREA.md` (i gesti sul VPS),
  `docs/GUIDA-P2P-PASSI.md` (il P2P coi testi esatti, per i tutorial).
- Audit: `docs/AUDIT-PAGAMENTI-2026-09-19.md`,
  `docs/AUDIT-2-CLIENT-MOSTRO-2026-09-23.md`. Studi:
  `docs/STUDIO-BOLT-CARD-2026-09-24.md`, `docs/STUDIO-RISTORANTI-2026-09-24.md`,
  `docs/STUDIO-CONTANTI-A-MANO-2026-09-25.md`, `docs/STUDIO-MOSTRO-0190-2026-09-30.md`,
  `docs/STUDIO-HACKATHON-RGB-2026-10.md` (e `docs/HACKATHON-SETUP.md`),
  `docs/STUDIO-LIQUIDITA-NODO-2026-10-01.md`, `docs/STUDIO-INSTRADAMENTO-NODO-2026-10-05.md`,
  `docs/STUDIO-PROFILO-PERSONALIZZATO-2026-10-06.md`, `docs/STUDIO-MERCATINI-BAZAR-2026-10-06.md`,
  `docs/STUDIO-REGALO-2026-10-06.md`, `docs/STUDIO-ISTANZA-PROVA-2026-10-08.md`.

I FILE GRANDI NON SI LEGGONO MAI INTERI: CANTIERI, ARCHITETTURA,
PRODUZIONE, server.py, miniapp.html e prove.py pesano milioni di
caratteri. Si cerca la SEZIONE e si legge solo quella: il come sta
nella skill `cerca-nei-docs`. Non c'è un indice e non deve nascerne uno.
PRIMA di toccare qualcosa, cercalo lì: se un cantiere l'ha già deciso,
la decisione ha un perché scritto, e rovesciarla senza saperlo è il
modo in cui si rifà un errore già pagato.

LE PROCEDURE LUNGHE SONO SKILL (`.claude/skills/`), e si aprono quando
servono: `chiusura-cantiere` (verbale, prove, firma, push, pulizia),
`promozione-main` (develop su main), `nodo-mostro` (le regole del nodo),
`cerca-nei-docs`.

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
  `git worktree add -b cantiere/<nome> .claude/worktrees/<nome> origin/develop`
  e si fa TUTTO là. Mai `git add -A`, mai `git commit -a`, mai un
  `git stash` nudo (la pila è condivisa).
- IL COMMIT SI FIRMA: il VPS tira solo una punta firmata. Prima di ogni
  push `git cat-file commit HEAD | grep -c '^gpgsig'` deve dire 1.
- IL PUSH È MIO SU `develop`, LA PROMOZIONE SU `main` È SUA (20 ott
  2026): a cantiere chiuso e con prove verdi si pusha su `develop` senza
  chiedere e mai con force (skill `chiusura-cantiere`); `main` solo col
  sì di Andrea e la sua frase intera (skill `promozione-main`). Un «non
  pushare ancora» di Andrea vince finché non lo scioglie.
- LE SESSIONI CLOUD NON ASPETTANO PIÙ LA CI SUL RAMO (da sola parte solo
  su main, 19 ott 2026): la loro prova è suite e collaudi locali.
- IL VPS È FUORI DAL MIO PERIMETRO: niente ssh, niente query, nemmeno in
  sola lettura. I comandi li scrivo, li esegue Andrea e incolla il
  risultato. Il deploy è suo. Lo stesso vale per il nodo Mostro (un'ALTRA
  macchina: skill `nodo-mostro`) e per il relay.
  La VM di collaudo no: un gesto alla volta, col suo ok (`docs/COLLAUDO.md`).
  Quel che resta da fare là si scrive in `docs/DA-FARE-ANDREA.md`, coi
  comandi pronti: la sessione di Andrea lo legge per prima (21 ott 2026).
- MAI RELAY VERI IN COLLAUDO E NEI GIRI DAL VIVO, mai eventi pubblicati:
  il server si ferma da solo (`lettura_simulata`, solo loopback), il
  BROWSER no — nel config del giro `MOSTRO_RELAY` e `MOSTRO_RELAY_SPECCHIO`
  vanno al relay morto (`ws://127.0.0.1:9`) e la nsec a `INCOLLA_QUI`.
  Unica eccezione, il P2P della VM di collaudo: le righe della produzione,
  relay.barattolo.store compreso; annunci, post e DM restano nel recinto.
  Mai copiare il `config.py` locale (ha una nsec di prova). Un collaudo
  nuovo: una riga in `ci/collaudi.txt` e in `ci/compila.txt`, MAI nel
  workflow.
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
  tiene in vita il valore vecchio finché non si cambia a mano, e le leve
  nuove si AGGIUNGONO al config del VPS. Si guarda PRIMA del deploy, in
  sola lettura (skill `promozione-main`).
- DEPLOY AUTOMATICO: il VPS TIRA (`deploy.sh` ogni minuto) un commit SOLO
  se sta su main, va in avanti, ha la CI verde e la punta FIRMATA; sennò
  «⛔ Deploy rifiutato». Config e database NON viaggiano mai. Il freno
  `.deploy-bocciato`, il ref `pronto`, `/api/salute` e le procedure:
  PRODUZIONE.
- IL BACKUP ESCE PRIMA DI OGNI DEPLOY (19 ott 2026, regola di Andrea):
  `deploy.sh` manda su Telegram l'archivio cifrato di `backup-fuori.sh`
  prima del `git reset`, e il giornaliero parte alle 04:30; entrambi
  dicono subito in chat un database non sano. Un cantiere che toglie,
  salta o indebolisce uno dei due non si pusha (`prove_backup_prima_del_deploy`).
- MAI CHIUDERE UN SOCKET O UN FILE DA UN THREAD CHE NON È IL SUO: il
  numero liberato va al database e ci si scrive dentro (successo due
  volte, 18-19 ott 2026: Cantieri, «Il saluto TLS nel database»).
- Webhook del bot: `TELEGRAM_WEBHOOK_SEGRETO` nel config del server e al
  riavvio si registra da solo (riga «🔔 Webhook Telegram» nel journal).
  ATTENZIONE: mai avviare MODALITA_COLLAUDO=False col BOT_TOKEN vero
  fuori dal VPS — ruberebbe il webhook (e quindi i /start) alla
  produzione.

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI nsec (chiave privata Nostr) degli utenti SUL SERVER.
   Decisione permanente: mai custodia di segreti altrui sul server, mai
   firme che richiedano di consegnare chiavi al server. La scala di quel
   che è APPROVATO — badge npub auto-dichiarato, verifica con nota
   pubblica, login con firma di sfida, wallet NWC solo-nel-browser, DM
   NIP-17, sessione bunker NIP-46 conservata, nsec conservata SOLO nel
   browser dell'utente (ott 2026) — col perché di ognuna e quel che
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
   e cosa resta da guardare — va in fondo a `docs/CANTIERI.md` (skill
   `chiusura-cantiere`). Questo file si tocca SOLO se è cambiata una
   REGOLA di qui: rientra intero a ogni sessione e a ogni /compact, e ha
   un tetto provato (`TETTO_CLAUDE_MD` in prove.py). Proponilo come
   commit separato, senza aspettare che Andrea lo chieda.
9. Lessico dell'escrow (lug 2026): nei testi per gli utenti si dice
   sempre «deposito di garanzia» — «(escrow)» solo nella prima
   spiegazione lunga di ogni contesto; azione = «🔒 Compra in
   sicurezza»; MAI «assicurato». «Escrow» resta solo dove il pubblico è
   bitcoiner: memo della invoice LNbits e testi verso Nostr (footer
   NIP-99, presenta_release). Il barattolo 🫙 è dei preferiti, mai
   metafora dell'escrow. La scheda «Affari» si chiama «Ordini» (testi
   utente sempre «Ordini», id interni invariati).
10. Una tariffa per le commissioni del mercatino non va MAI al venditore:
    al più al compratore, visibile prima di pagare (15 ott 2026).

## Adesso

Stato al 12 ott 2026 (parola di Andrea):
- P2P PUBBLICO DAL 10 OTT 2026 (lancio fatto): `P2P_IN_VETRINA` sta nel
  config del VPS, nel codice è False (PRODUZIONE, «LE CARD P2P IN VETRINA»).
- I PIONIERI sono congelati a 101. La cassaforte del mercatino è «nodo»
  (LNbits self-hosted col LND del nodo: Cantieri, «Il doppio wallet»).
- Il nodo gira Mostro 0.19.0 (`-bar8` dal 13 ott, patch 0010-0012): la cauzione solo a chi
  prende scegliendo «Contanti»; `P2P_CAUZIONE_SUL_METODO` ACCESA sul VPS.
- TETTI. Mercatino: nessun prezzo massimo (`TETTO_SATS_ANNUNCIO` spenta).
  P2P in beta: 250 € per TUTTI gli ordini (`P2P_MAX_EURO = 250` sul VPS, 0
  nel codice), a fine beta salirà; contanti di persona 250 €, di serie
  (`P2P_CONTANTI_MAX_EURO`). Valori VIVI: pannello «⚙️ Stato delle leve».

Backlog concordato: commissione minima fissa; a lancio fatto, il tracking
verificato via API corrieri (con la MAPPA dei punti), l'escrow on-chain
2-di-3, il parere legale MiCA prima di crescere. Da riprendere (ago 2026,
segnati da Andrea, non ancora decisi): il luogo del ritiro a mano
salvato e richiamato a ogni annuncio; «I miei annunci» più fruibile; i
privilegi dei pionieri (la coorte esiste, non dà ancora niente); il
locker di riserva (un secondo punto se il primo non va).
