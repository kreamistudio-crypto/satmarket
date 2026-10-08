# Studio: un'istanza di PROVA di Barattolo, privata, dove ogni push arriva prima (8 ottobre 2026)

Sola lettura, nessun codice toccato, nessuna modifica al VPS, al nodo, al
relay o a un config. Base: `origin/main` a `213d708` (i nomi di funzioni,
leve e file sono la cosa da cercare; i numeri di riga si spostano). I
fatti sulla macchina vengono da `docs/PRODUZIONE.md`, da `deploy.sh`,
dalle unit in `deploy/` e da `deploy/RIPRISTINO.md`: quel che da qui NON
si può leggere (RAM, CPU e disco liberi oggi; i record DNS esatti del
dominio) è scritto come tale, coi comandi che lo dicono, in sola lettura,
da eseguire Andrea. I fatti esterni (listino Hetzner, procedura DNSSEC di
Cloudflare) vengono dalle fonti in fondo, lette l'8 ottobre 2026.

**La domanda di Andrea e Alan.** Oggi ogni push su `main` con la CI verde
sposta il ref `pronto`, e il VPS lo tira da solo in produzione entro un
minuto. Si vuole un'istanza di PROVA, privata, dove ogni push arrivi
PRIMA; la produzione si aggiorna solo dopo che Andrea ha provato sul
telefono e ha fatto un gesto esplicito. Niente dati personali veri e
niente sats veri nella prova.

**La risposta corta.** Si fa, costa poco, e il grosso della catena c'è
già: `deploy.sh` è PARAMETRICO (`BARATTOLO_RAMO`, `BARATTOLO_DIR`,
`BARATTOLO_SERVIZIO`, `BARATTOLO_SALUTE` sono variabili d'ambiente con un
default), quindi la stessa unit, lo stesso script e lo stesso giudice
possono seguire DUE ref: `pronto` (che la CI alza oggi) per la prova, e
un ref nuovo `produzione` che muove SOLO Andrea, dal PC, con un push in
avanti veloce. Il giudice del VPS non cambia di una riga: su main, in
avanti, firmato, CI verde. La prova vive meglio su un VPS piccolo a parte
(circa 6-7 € al mese IVA inclusa, Hetzner o LNVPS), con un bot Telegram
suo, un LNbits suo in Docker con il portafoglio FINTO (`FakeWallet`: sats
di cartone, invoice vere nella forma), un database nuovo e vuoto, i relay
spenti e il P2P spento. Due righe di codice vanno cambiate prima: oggi
`URL_PUBBLICO` e `LINK_BOT` sono COSTANTI in `server.py`
(`https://barattolo.store`), e una prova che le eredita registrerebbe il
webhook del bot di prova sull'indirizzo di produzione e metterebbe link
di produzione in ogni notifica. Prima del 10 ottobre NON si tocca niente
sul VPS e niente nel flusso; si può solo aprire il bot di prova su
BotFather, leggere le risorse della macchina e, volendo, ordinare la
macchina della prova. Il DNS è un cantiere a parte, da fare DOPO il
lancio e con calma: spostare la zona su Cloudflare (o deSEC) in sola
modalità DNS è ragionevole, ma con DNSSEC acceso l'ORDINE dei passi è
tutto, e fatto male spegne il dominio per tutti per uno o due giorni.

---

## 1. Com'è fatto oggi il deploy

**La catena, dal push al servizio** (PRODUZIONE, «LA CATENA DEL DEPLOY»
e «IL DEPLOY CHE SI FIDA SOLO DI MAIN»):

1. Un push su `main` fa partire `.github/workflows/prove.yml`: i job
   `prove` (la suite di `prove.py`, i collaudi in gabbia) e `segreti`
   (lo scanner delle chiavi), tutti in sola lettura.
2. Il job `pronto` — SOLO su `main`, SOLO su un push, `needs: [prove,
   segreti]`, l'unico con `contents: write` — fa `git push origin
   HEAD:refs/heads/pronto`, senza `--force`: il ref `pronto` può solo
   AVANZARE lungo main. È il campanello, non la prova.
3. Sul VPS il timer `barattolo-deploy.timer` (ogni minuto, `OnBootSec`
   di 2 minuti) lancia `barattolo-deploy.service`, che gira DA ROOT,
   copia `deploy.sh` in `/run/barattolo-deploy/` e lo esegue da lì (bash
   legge il file mentre lo esegue: un `git reset` a metà corsa lo
   cambierebbe sotto i piedi).
4. `deploy.sh` fa `git fetch` di `pronto` E di `main` (refspec
   espliciti), e se `pronto` si è mosso GIUDICA il commit, prima di
   toccare qualsiasi cosa: a) sta su `main` (antenato di `origin/main`);
   b) va IN AVANTI rispetto a quel che gira; c) la PUNTA è firmata da una
   chiave di `/etc/barattolo-deploy/firmatari` (ssh `allowed_signers`,
   fuori dal repo, di root: firmatari `andrea` e `alan` dal 21 set); d)
   la CI è verde SU DI LUI, chiesta alle Actions da `giudice_deploy.py`
   col token di SOLA LETTURA di `/root/.git-credentials`, e contano solo
   i giri nati da un push su main coi job `prove` e `segreti` in
   `success`. Tre esiti: tira, RIFIUTA (journal, «⛔ Deploy rifiutato» ai
   moderatori una volta, timbro `.deploy-rifiutato`), ASPETTA (riprova al
   giro dopo, «⏳ Deploy fermo» dopo dieci minuti).
5. Se tira: copia del database PRIMA (`backup/pre-deploy-*.db`, API
   `backup` di sqlite, le ultime 5), `git reset --hard` sul commit
   giudicato, `python3 -m compileall server.py`, `systemctl restart
   barattolo`, poi 45 secondi a `/api/salute` (che TOCCA il database, una
   lettura minima, e risponde 503 se non si apre). Se tace: torna al
   commit di prima, riavvia, timbra `.deploy-bocciato` e NON riprova da
   solo. Ogni esito finisce nel journal e in un messaggio ai moderatori
   («🚀 Barattolo aggiornato» coi titoli dei commit, `novita_brevi`).
6. Il riavvio è DOLCE dal 1 ott 2026: Caddy aspetta il backend fino a 30
   secondi (`lb_try_duration`) invece di rispondere 502, e il drop-in
   `riavvio-dolce.conf` dà a uvicorn 10 secondi di uscita pulita.

**Il servizio.** `barattolo.service` più il drop-in
`barattolo.service.d/utente.conf` (copia in `deploy/utente/`):
`User=barattolo`, `Group=barattolo`, `WorkingDirectory=/srv/barattolo`,
`UMask=0027`. Uvicorn su `127.0.0.1:8080`, Python di sistema (nessun
venv: le librerie sono installate per tutti), un processo solo.

**Caddy.** `/etc/caddy/Caddyfile`, FUORI dal repo (sta nel backup come
`sistema/Caddyfile`), due blocchi: il sito `barattolo.store` con HTTPS
automatico (Let's Encrypt) e HTTP/3, e il blocco dell'onion; entrambi
`reverse_proxy` verso `127.0.0.1:8080`. Il blocco onion è servito dal
tor del VPS (`HiddenServiceDir` nel torrc, la chiave è l'indirizzo).

**Dove sta cosa** (`/srv/barattolo`, con `/root/satmarket` come
collegamento, PRODUZIONE «LA SEQUENZA PER IL VPS», passo 3):

| Cosa | Dove | Di chi |
|---|---|---|
| codice e `.git` | `/srv/barattolo` | root (il servizio non scrive dove root esegue) |
| `config.py` | `/srv/barattolo/config.py` | `root:barattolo 640` |
| database | `/srv/barattolo/dati/satmarket.db` (il collegamento `satmarket.db` accanto al codice) | `barattolo` |
| foto, buste, contenuti digitali, import | `foto/`, `buste/`, `contenuti/`, `import_tmp/` | `barattolo` |
| copie pre-deploy | `/srv/barattolo/backup/` | root 700 |
| timbri del deploy | `.deploy-bocciato`, `.deploy-rifiutato`, `.deploy-attesa` nella cartella | root |
| firmatari | `/etc/barattolo-deploy/firmatari` | root, fuori dal repo |
| token GitHub di sola lettura | `/root/.git-credentials` | root 600 |
| cert di LND per il server | `/etc/barattolo/lnd-tls.cert` (`LND_PONTE_CERT`) | root, 644 |
| LNbits «nodo» | `/opt/lnbits` (Docker, `lnbits/lnbits:v1.6.1`, `127.0.0.1:5001`) | root |
| ponte verso LND | `lnd-ponte.service` (socat `127.0.0.1:18080` → `10.77.0.1:18080` via WireGuard `wg0`) | root; il piano B `lnd-ponte-tor.service` spento |

**I collegamenti con le altre macchine.** Il NODO Mostro (LNVPS Dublino,
`185.18.221.96`): LND dietro il ponte WireGuard, da cui il server legge
la «verità dei pagamenti» col macaroon di sola lettura
(`LND_PONTE_MACAROON_LETTURA`) e LNbits paga; mostrod, che parla col
server SOLO via relay Nostr (`MOSTRO_RELAY`) e col webhook degli eventi
(`P2P_EVENTI_SEGRETO`, `RONDA_NODO_SEGRETO`). Il RELAY
(`relay.barattolo.store`, `185.18.221.118`, strfry): è lo specchio del
libro P2P (`MOSTRO_RELAY_SPECCHIO`) e uno dei relay su cui il server
pubblica gli annunci NIP-99 firmati con `NOSTR_NSEC_PIATTAFORMA`. Il
guardiano del ponte riavvia tor e wg via `sudo` (le quattro righe di
`sudoers-barattolo-ponte`).

**Il bot Telegram.** `BOT_TOKEN` nel config; all'avvio
`registra_webhook_telegram` chiama `setWebhook` su
`{URL_PUBBLICO}/api/telegram/aggiornamenti` con
`TELEGRAM_WEBHOOK_SEGRETO` — SALTATO in collaudo e col segnaposto. L'URL
della Mini App sta su BotFather (`?v=2`). ⚠️ `URL_PUBBLICO` e `LINK_BOT`
NON sono leve: sono due costanti in `server.py` («Barattolo su Nostr: gli
annunci in piazza»), `https://barattolo.store` e
`https://t.me/ilbarattolobot`, usate in 76 punti (webhook, link nelle
notifiche, foto nei post, `dominio_pubblico` verso il client). È il
primo ostacolo concreto per una seconda istanza (§3 e §6).

**Backup.** `barattolo-backup.timer` ogni giorno: archivio `age` (db con
backup atomico, config, buste, contenuti, Caddyfile, unit, torrc e chiave
onion) verso il canale Telegram privato dei backup (bot SUO, mai quello
di Barattolo) più il pull sul PC di Andrea; la metà segreta di age vive
su carta e Bitwarden. Più la copia pre-deploy di sopra.

**Notifiche.** Solo Telegram (bot, canali `TELEGRAM_CANALE_*`, post
automatici) e Nostr (DM, NIP-99). Nessuna email: in `server.py` non c'è
una riga di smtp. Altre API che il server chiama da solo: CoinGecko (il
cambio), Anthropic (la ricerca, `ANTHROPIC_API_KEY`), le API dei negozi
coi connettori, i wallet LNURL dei venditori (`invoice_da_ln_address`,
dietro `url_api_ammesso`), i relay Nostr.

---

## 2. Dove far vivere la prova

### (a) Stesso VPS, servizio e cartella separati

Com'è: `/srv/barattolo-prova` (clone suo, utente di sistema
`barattolo-prova`, database in `dati/`), `barattolo-prova.service` su
`127.0.0.1:8081` (drop-in gemello di `utente.conf`), un TERZO blocco nel
Caddyfile per `prova.barattolo.store`, una unit e un timer di deploy
gemelli con `Environment=BARATTOLO_DIR=/srv/barattolo-prova`,
`BARATTOLO_SERVIZIO=barattolo-prova`,
`BARATTOLO_SALUTE=http://127.0.0.1:8081/api/salute`, `BARATTOLO_RAMO`
al ref della prova. Il token GitHub e i firmatari si condividono.

- Costo: 0 €. Tempo: mezza giornata (è la ricetta di `cambio-utente.sh`
  rifatta per una seconda cartella).
- Rischio per la produzione: la separazione è SOLO di permessi di file.
  Stessa RAM, stessa CPU, stesso disco (un bug della prova che riempie il
  disco o mangia la CPU rallenta il mercatino vero), stesso IP (un limite
  di api.telegram.org o di un relay colpisce entrambi), stesso Caddy (un
  Caddyfile storto, pur mitigato da `caddy validate` e dal `reload` che
  tiene la vecchia, è un gesto a mano sulla macchina dei sats), stesso
  `/opt/lnbits` a due passi. E il rischio più vero è UMANO: un
  `config.py` della prova fatto copiando quello vero porta nella prova
  il `BOT_TOKEN` di produzione (ruberebbe il webhook ai `/start` veri,
  CLAUDE.md lo dice) o la `LNBITS_NODO_ADMIN_KEY` (paga sats veri). La
  superficie dell'audit di settembre cresce: un secondo servizio, un
  secondo utente, una seconda porta, sulla macchina che ha le chiavi.
- Le cinture se si sceglie (a): `MemoryMax=` e `CPUQuota=` nella unit
  della prova, `TasksMax`, una quota di disco (o `dati/` su una cartella
  con `du` nella ronda), NIENTE accesso a `/opt/lnbits`, al ponte, a
  `sudo`; il `config.py` della prova si SCRIVE da `config_esempio.py`,
  mai copiato da quello vero.
- Risorse di oggi, da leggere in sola lettura (Andrea incolla l'uscita):

```bash
uptime && nproc && free -h && df -h / && swapon --show
ps -o rss=,etimes=,cmd= -p "$(systemctl show -p MainPID --value barattolo)"
du -sh /srv/barattolo/foto /srv/barattolo/dati /opt/lnbits 2>/dev/null
docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.CPUPerc}}'
hostnamectl | grep -iE 'hardware|operating'
```

  (`free -h` dice RAM totale e libera; `ps … rss` quanto pesa oggi il
  mercatino; `hostnamectl` il modello della macchina. Niente di questo
  scrive.) Il metro: se dopo il mercatino, LNbits, tor e Caddy restano
  meno di 1,5 GB liberi, la (a) non si fa.

### (b) Un VPS piccolo a parte (RACCOMANDATA)

Com'è: una macchina nuova, Ubuntu, Caddy, Python, l'utente `barattolo`,
le due unit di deploy — la stessa sequenza di `deploy/RIPRISTINO.md` e di
PRODUZIONE «LA SEQUENZA PER IL VPS», meno backup, tor, LNbits vero, ponte
e WireGuard. Un clone del repo, un token GitHub di sola lettura SUO (così
si revoca da solo), lo stesso file `firmatari` (copiato a mano: sono
chiavi PUBBLICHE).

- Costo: Hetzner, taglio minimo (CX23: 2 vCPU, 4 GB; o CAX11 ARM),
  listino del 15 giugno 2026 intorno a 5,49-5,99 € al mese IVA esclusa,
  circa 6,70-7,30 € con IVA; i prezzi sono saliti due volte nel 2026 e
  ad agosto la linea CX risultava «currently not available» a tratti,
  quindi si legge il listino al momento dell'ordine (fonti in fondo).
  Alternativa: LNVPS (dove già girano nodo e relay), pagabile in sats,
  taglio paragonabile. Il divieto «nodo su Hetzner» riguarda il NODO
  (concentrazione del rischio), non la prova.
- Rischio per la produzione: nessuno per processo, disco, IP, Caddy. I
  soli fili in comune sono GitHub (il repo) e il DNS (un record A in
  più). Un errore sulla prova resta sulla prova.
- Tempo: mezza giornata di Andrea con i comandi scritti, come per il
  cambio d'utente. ED È UN DRILL GRATIS del foglio del panico: rimettere
  in piedi Barattolo su una macchina nuova è esattamente quel che
  RIPRISTINO.md promette di saper fare, e che dal 26 ago non si rifà.
- Nessun backup da fare (dati finti), nessun tor, nessun onion.

### Vercel e simili: perché NO per questa app

Vercel è una piattaforma per frontend e FUNZIONI brevi (serverless/edge):
ogni richiesta sveglia una funzione che muore dopo pochi secondi, e il
filesystem è effimero. Barattolo è l'opposto: UN processo uvicorn che
vive a lungo, con sqlite in una cartella (`dati/`), le foto su disco,
l'orologio dei giri (ogni dieci minuti), il webhook di Telegram, le
websocket verso i relay, la registrazione all'avvio. Niente di questo
gira su Vercel senza riscrivere l'app (database esterno, storage
esterno, scheduler esterno), cioè senza smettere di provare QUESTO
codice. Le piattaforme a container con volume (Fly.io, Railway, Render)
lo farebbero girare, ma: costano come un VPS; sono un fornitore in più
da imparare; il deploy là è PUSH dal CI con una chiave nei secret, che è
la direzione che la catena rifiuta per scelta (nessuna chiave della
macchina su GitHub); e soprattutto la prova serve a provare ANCHE il
deploy — systemd, `deploy.sh`, il giudice, il riavvio dolce, le
migrazioni di `init_db` — che là non esisterebbe. Una prova che non
somiglia alla produzione prova un'altra cosa.

**Scelta:** (b). La (a) resta il ripiego a costo zero se la RAM libera lo
permette e se si accettano le cinture, ma mette un secondo cantiere
sulla macchina dei sats, e la regola di settembre era ridurre quella
superficie, non allargarla.

---

## 3. Cosa usa la prova al posto delle cose vere

**Database: nuovo e VUOTO**, creato da `init_db` al primo avvio, con il
seme demo del catalogo finché non ci sono dati vivi (il client lo fa già:
`listings` finto finché `datiVivi`). NON una copia anonimizzata: il
database ha 59 tabelle, e i dati personali stanno in `utenti`,
`ordini`, `ordine_righe` (indirizzi), `offerte`, `feedback`, `sessioni`,
`punti_ritiro`, nelle `buste/` e nei `contenuti/` cifrati, nelle foto.
Anonimizzare BENE è un cantiere a sé (ogni tabella, ogni colonna libera,
ogni foto), e un'anonimizzazione sbagliata è una fuga di dati su una
macchina meno protetta: non vale il rischio per quel che la prova deve
fare, cioè provare il CODICE e le MIGRAZIONI, non i dati. Se un giorno
servirà un volume realistico (mille annunci, cento ordini) si scrive un
GENERATORE di dati finti (uno script, nomi inventati, foto di cartone):
cantiere futuro, non ora. Il reset è un gesto: fermare il servizio,
cancellare `dati/satmarket.db`, `foto/`, `buste/`, `contenuti/`,
riavviare. Le migrazioni di `init_db` girano sulla prova PRIMA che in
produzione: è il secondo regalo dell'istanza.

**Pagamenti: LNbits di prova, in Docker sulla macchina della prova, col
portafoglio finto.** LNbits ha la funding source `FakeWallet`
(`LNBITS_BACKEND_WALLET_CLASS=FakeWallet` nel `.env`): le invoice sono
VERE nella forma (bolt11 che il codice legge, hash, scadenza) ma si
pagano solo DENTRO quell'istanza, da un secondo wallet del pannello, e
nessun satoshi esiste. Nel config della prova `LNBITS_URL` e
`LNBITS_NODO_URL` puntano entrambe lì (`http://127.0.0.1:5001`), con le
chiavi di quei wallet; `CASSAFORTE_NUOVA = True`;
`LND_PONTE_MACAROON_LETTURA = ""` (LND «spento»: decide LNbits, con le
regole del pending); `GUARDIANO_PONTE = False`; `CONTROLLO_LIBRO_MASTRO`
e `RICONCILIA_PAYOUT` possono restare accesi (parlano col LNbits finto).
Cosa si prova: tutto il ciclo degli stati, i promemoria, i rilasci, le
notifiche, il 🧊, il pannello. Cosa NON si prova: pagare dal wallet del
telefono (un'invoice finta non la paga nessun wallet vero) — il «paga»
lo fa Andrea dal pannello LNbits della prova, dal PC o dal telefono via
`ssh -L` come oggi per il pannello del nodo. L'alternativa «LNbits su
signet/Mutinynet con un LND di prova» è più vera (il telefono paga con
un wallet signet) ma vuole un nodo in più da tenere acceso: si rimanda a
quando servirà davvero (il tracking, l'escrow 2-di-3). Le due regole
della prova: MAI una chiave di un wallet vero nel suo config, e MAI il
`LNBITS_NODO_*` del VPS.

**Mostro e relay: SPENTI.** `P2P_ATTIVO = False` di serie nella prova.
Quando una sessione deve provare il P2P sulla prova, le quattro leve al
relay morto (`MOSTRO_RELAY` e `MOSTRO_RELAY_SPECCHIO` a
`ws://127.0.0.1:9`): il libro resta vuoto, nessun evento esce. Un
mostrod di prova (container, LND regtest, relay suo) NON ora: sono
settimane, e il coordinatore di cartone dei collaudi (`collaudi_ci.py`)
copre già i gesti. Niente nsec: `NOSTR_NSEC_PIATTAFORMA` al segnaposto
(fail-open dichiarato: non si pubblica nulla), `RELAY_NOSTR = []`,
`RELAY_NOSTR_IMPORT = []`, `IMPORT_NOSTR_APERTO = False`,
`TRASLOCO_NOSTR = False`, `SEGRETI_PROFILO_P2P = {}`. Così la prova NON
parla con nessun relay vero, che è la regola di CLAUDE.md estesa a una
macchina in più.

**Bot Telegram di prova, separato.** Un bot nuovo da BotFather (es.
`@ilbarattoloprovabot`), `BOT_TOKEN` suo, `TELEGRAM_WEBHOOK_SEGRETO` suo,
Mini App URL `https://prova.barattolo.store`. `ADMIN_IDS` e `FONDATORI`
con gli id di Andrea e Alan (gli id Telegram sono gli stessi su ogni bot:
si entra con la PROPRIA identità, non con le tre finte del collaudo,
quindi `MODALITA_COLLAUDO = False` anche in prova). I messaggi del deploy
(«🚀 aggiornato», «⛔ rifiutato») arrivano dal bot di prova: si distingue
a colpo d'occhio da quello vero. `TELEGRAM_CANALE_ID`,
`TELEGRAM_CANALE_RIEPILOGO`, `TELEGRAM_CANALE_VETRINA` vuoti,
`POST_AUTOMATICI = False`, `RIEPILOGO_SETTIMANALE = False`.

**Spente o di cartone:** `ANTHROPIC_API_KEY` al segnaposto (la ricerca
ripiega come già fa senza chiave); `CONNETTORI_NEGOZIO_APERTI = False` e
`CONNETTORI_NEGOZIO_PER_TUTTI = False` (la prova non bussa alle API dei
negozi veri); `ONION_HOST = ""`; `BANNER_TEST = True` con un testo che
dice «Questa è l'istanza di PROVA: dati finti, sats finti» (il cartello
esiste già, una volta al giorno per dispositivo). Email: non ce n'è.
`CHIAVE_CONTENUTI_DIGITALI` una chiave sua, generata lì (per provare
anche la cifratura), mai quella vera.

**Il pezzo di codice che manca (piccolo, PRIMA della prova):**
`URL_PUBBLICO` e `LINK_BOT` devono diventare leve lette dal config con
il default di oggi (`getattr(config, "URL_PUBBLICO",
"https://barattolo.store")`, una riga ciascuna; i 76 usi non cambiano).
Senza, la prova registra il webhook del bot di prova su
`barattolo.store/api/telegram/aggiornamenti` (la produzione lo
rifiuterebbe con 403 per il segreto diverso, ma il bot di prova
resterebbe sordo) e ogni notifica porterebbe link alla produzione. Il
config del VPS NON ha bisogno della riga: il default è quello di oggi.

---

## 4. Accesso privato

**Indirizzo: `prova.barattolo.store`**, un record A verso la macchina
della prova nel DNS di oggi (Register.it) con TTL basso (300). Caddy
chiede il certificato a Let's Encrypt da solo. Due cose da sapere: il
NOME finisce nei registri pubblici di Certificate Transparency (chiunque
può scoprire che `prova.barattolo.store` esiste: la privatezza non può
stare nel nome), e il record deve esistere PRIMA di accendere Caddy, o
il challenge fallisce e Let's Encrypt conta i tentativi. Un dominio a
parte non serve.

**Protezione, su due strati.**

1. **Nel server, la lista degli ammessi** (cantiere piccolo, la vera
   protezione): una leva nuova, `PROVA_SOLO_IDS = [id di Andrea, id di
   Alan]`, vuota di serie (= nessun filtro, la produzione non cambia). Se
   non è vuota, un middleware risponde 403 «Istanza di prova, privata» a
   OGNI richiesta che non arrivi da una sessione di uno di quegli id —
   anche la vetrina anonima —, tranne `/api/salute`,
   `/api/telegram/aggiornamenti` (Telegram deve poter suonare), la pagina
   d'ingresso con lo script di Telegram e le rotte del login (altrimenti
   nessuno riesce a identificarsi). Chi invitare si aggiunge alla lista
   e si riavvia. Esiste già la stessa forma per il P2P (`P2P_PROVA_IDS`):
   si copia quella.
2. **In Caddy, le cinture che non costano**: `header X-Robots-Tag
   "noindex, nofollow, noarchive"` su tutto (vale anche per foto e
   sitemap), `respond /robots.txt "User-agent: *\nDisallow: /" 200` prima
   del proxy, e nessun link alla prova in nessun canale o post. Volendo
   un filtro sugli User-Agent dei crawler noti.

**Cosa NON funziona e perché.** La password di Caddy (`basic_auth`)
davanti a tutto: la Mini App si apre nella webview di Telegram, che non
mostra il prompt della password in modo affidabile, e Telegram stesso
dovrebbe passare per il webhook; si può fare «basic_auth tranne il
webhook e la Mini App», ma a quel punto protegge solo il browser del PC.
La lista di IP: Andrea prova dal TELEFONO, con l'IP del cellulare che
cambia a ogni cella. Cloudflare Access (Zero Trust, gratis fino a 50
utenti, login via email o Telegram-no): protegge anche la webview col
cookie, ma vuole la zona su Cloudflare col proxy acceso (§DNS: lo
sconsiglio per `barattolo.store`; sarebbe accettabile per il SOLO
sottodominio della prova, se il DNS un giorno fosse là).

**Niente indicizzazione** è la somma di: `X-Robots-Tag`, `robots.txt`
che vieta tutto, il 403 agli anonimi (un crawler non ha sessione), e la
`sitemap.xml` del server che, con la leva `URL_PUBBLICO` a
`prova.barattolo.store`, elenca indirizzi della prova che il robots
vieta — e che comunque il 403 nasconde.

---

## 5. Il nuovo flusso

**Due ref, un solo giudice.**

- `pronto` resta com'è: lo alza la CI a ogni push verde su main. Lo
  segue la PROVA (`deploy.sh` col default `BARATTOLO_RAMO=pronto`).
- `produzione` è un ref NUOVO che muove SOLO Andrea. Lo segue il VPS: la
  sola modifica là è un drop-in
  `/etc/systemd/system/barattolo-deploy.service.d/produzione.conf` con
  `[Service]` e `Environment=BARATTOLO_RAMO=produzione`, più
  `daemon-reload` (copia in `deploy/utente/`, come `utente.conf`). La
  unit nel repo non cambia; `deploy.sh` non cambia; il giudice NON cambia
  — un commit su `produzione` deve ancora stare su main, andare in
  avanti, essere firmato e avere la CI verde — e il messaggio «⚠️
  qualcuno ha spostato «pronto» a mano» dirà «produzione», perché il
  testo usa `$RAMO`.
- Il primo giro: `git push origin origin/main:refs/heads/produzione` sul
  commit che GIÀ gira (così il VPS non si muove), poi il drop-in.

**Il gesto di Andrea, dal PC**, dopo aver provato sul telefono:

```bash
git fetch origin && git push origin origin/pronto:refs/heads/produzione
```

Porta in produzione ESATTAMENTE quel che la prova sta facendo girare. Se
vuole fermarsi a un commit preciso (la prova è già più avanti):
`git push origin <sha>:refs/heads/produzione`. Il push è un AVANTI
VELOCE: se non lo è, GitHub lo rifiuta da solo, e il rifiuto è la
notizia (storia riscritta: ci si ferma). Mai `--force`. Perché un ref e
non un tag o un comando sul VPS: `deploy.sh` segue già un ref, un ref
«va avanti» per natura (un tag no), si legge da chiunque con
`git ls-remote origin refs/heads/produzione refs/heads/pronto` («cosa
gira» e «cosa sta in prova» in una riga), e non chiede a Andrea nessun
ssh. Un gesto dal telefono, se servirà: un workflow `promuovi.yml` con
`workflow_dispatch` che fa quel push, lanciabile dall'app GitHub; NON
aggiunge sicurezza (chi scrive su main scrive anche il workflow: la
difesa resta la firma e il giudice sul VPS), aggiunge comodità. Da
decidere dopo, non serve al primo giro.

**I tempi.** Push → CI verde (3-5 minuti) → prova aggiornata entro un
minuto → Andrea prova → gesto → produzione entro un minuto. Un hotfix fa
la stessa strada, solo più in fretta.

**Come si torna indietro se la produzione si rompe.** Tre casi:

1. *Non parte o `/api/salute` tace*: lo fa già `deploy.sh` da solo
   (torna al commit di prima, riavvia, timbra `.deploy-bocciato`, «↩️
   Deploy annullato»). Niente da cambiare.
2. *Parte ma fa una cosa sbagliata*: la strada di sempre è IN AVANTI —
   `git revert` del commit (o dei commit) su main, CI verde, `pronto`
   avanza, la prova mostra che il ritorno funziona, Andrea promuove.
   Cinque-dieci minuti. Il giudice RIFIUTA per scelta i ritorni indietro
   del ref (controllo b), e spostare `produzione` indietro non serve a
   niente: resta «rifiutato».
3. *Emergenza, non si può aspettare la CI*: sul VPS, a mano, tre
   comandi — `git -C /srv/barattolo reset --hard <sha-buono>`,
   `echo <sha-rotto> > /srv/barattolo/.deploy-bocciato` (SENZA questa
   riga il timer, un minuto dopo, vede `produzione` avanti e lo rimette),
   `systemctl restart barattolo`. Poi il revert vero per la via normale,
   che al passaggio rimuove il timbro.

Le migrazioni di `init_db` vanno solo avanti (le tabelle restano: lo
dicono già le voci di PRODUZIONE «IL ROLLBACK è il commit precedente»):
il codice vecchio con una colonna nuova in più funziona, ed è per questo
che si torna indietro di codice e non di database. Per un bug che
CORROMPE dati c'è la copia `backup/pre-deploy-*.db` fatta un minuto
prima, e il backup del giorno.

**Un rischio nuovo del flusso: la promozione dimenticata.** Con il
vecchio flusso main e produzione coincidevano; col nuovo, main può
correre di dieci commit mentre la produzione resta indietro, e un
hotfix porta con sé tutto il resto. Due cure a costo zero: il verbale di
ogni push dice «in PROVA, non in produzione», e Andrea promuove spesso,
a piccoli passi, non una volta al mese. Volendo, una riga nella ronda:
se `produzione` è dietro `pronto` da più di 7 giorni, un «📦 c'è roba in
prova da N giorni» agli admin.

---

## 6. Cosa cambia per le sessioni Claude Code

- **CLAUDE.md, la regola «IL PUSH È MIO, IL DEPLOY È SUO»** diventa
  letterale: il push su `main` porta in PROVA, e la produzione la muove
  SOLO Andrea col gesto del §5. La regola delle due condizioni (cantiere
  chiuso, prove verdi) RESTA identica: la prova non è un posto dove
  mandare roba a metà, perché è anche quel che Andrea guarda dal
  telefono. «Entro un minuto è online» diventa «entro un minuto è sulla
  prova». Nel verbale del push si scrive «in prova», e la frase «cosa è
  girato su quale albero» resta.
- **Il ref `pronto`**: lo muove la CI; spostarlo a mano resta un gesto
  che si chiede. Il ref `produzione` NON lo tocca nessuna sessione, mai,
  nemmeno se Andrea lo chiede in chat senza il contesto: è il suo gesto,
  dal suo PC, come la firma.
- **La CI** non cambia: il job `pronto` resta, le sentinelle di
  `prove.py` sul semaforo (`needs`, `HEAD:refs/heads/pronto`, no
  `--force`, solo main, solo push), su `deploy.sh`
  (`RAMO="${BARATTOLO_RAMO:-pronto}"`, i quattro controlli, l'ordine) e
  sulla unit passano identiche, perché il default resta `pronto` e la
  produzione lo CAMBIA da fuori, col drop-in. Un `promuovi.yml` futuro
  vorrebbe una sentinella sua (solo `workflow_dispatch`, push in avanti
  veloce senza `--force`).
- **Il cantiere di codice che apre tutto** (uno, piccolo, con le sue
  prove): le due leve `URL_PUBBLICO`/`LINK_BOT`; la leva `PROVA_SOLO_IDS`
  col middleware e le sue esenzioni; una sezione «L'ISTANZA DI PROVA» in
  `config_esempio.py` che elenca riga per riga il config della prova
  (quelle del §3), così si scrive da lì e non copiando; in `deploy/`: il
  drop-in `produzione.conf`, lo spezzone di Caddyfile della prova, e una
  procedura `deploy/PROVA.md` (installazione, reset del database,
  rotazione del token); in PRODUZIONE la voce del flusso a due ref.
  Facoltativa: una leva `SALUTE_DICE_VERSIONE` (vuota di serie) che SOLO
  sulla prova fa aggiungere a `/api/salute` lo sha che gira — in
  produzione la salute non racconta niente di sé per scelta, e resta
  così.
- **Le sessioni e la prova**: la macchina della prova è FUORI PERIMETRO
  come il VPS (niente ssh, i comandi li esegue Andrea). Una sessione può
  leggere `https://prova.barattolo.store/api/salute` (esente dal 403) per
  sapere che il deploy è arrivato, e niente altro: con `PROVA_SOLO_IDS` il
  Browser pane non entra, e va bene così. I giri dal vivo restano in
  locale col relay morto, come oggi; la prova è il banco di Andrea, non
  il mio.
- **I collaudi non cambiano**: `MODALITA_COLLAUDO` resta il mondo delle
  tre identità finte in locale; la prova gira con `MODALITA_COLLAUDO =
  False` e identità Telegram vere, che è il punto.

---

## 7. Costi, rischi, prima e dopo il 10 ottobre

**Tempo** (mezze giornate):

| Pezzo | Chi | Mezze giornate |
|---|---|---|
| Macchina (b): ordine, Ubuntu, Caddy, Python, utente, unit, token, firmatari | Andrea coi comandi scritti | 1 |
| Codice: leve `URL_PUBBLICO`/`LINK_BOT`, `PROVA_SOLO_IDS`, config d'esempio, drop-in, Caddy, PROVA.md, prove e verbale | sessione | 1 |
| Bot di prova, record DNS, LNbits FakeWallet in Docker, config della prova | Andrea | 1 |
| Primo giro intero: push → prova → gesto → produzione; revert di prova; emergenza a mano provata | insieme | 1 |

Quattro mezze giornate in tutto, due di Andrea; nessuna prima del 10.

**Euro al mese:** (b) circa 6-7 € IVA inclusa (listino giugno 2026, da
rileggere); (a) 0. Il bot, il DNS, LNbits FakeWallet, Let's Encrypt: 0.

**Rischi e cure.**

- *Un segreto vero nel config della prova* (il rischio che conta): il
  `BOT_TOKEN` vero là ruba il webhook alla produzione; una chiave LNbits
  vera paga sats veri. Cura: il config della prova si scrive da
  `config_esempio.py`, sezione dedicata, e il `config.py` del VPS non
  lascia mai il VPS (già regola del backup: viaggia solo cifrato).
- *La prova diventa una seconda macchina da curare*: aggiornamenti di
  Ubuntu, dipendenze pip, token GitHub che scade (il deploy si ferma e lo
  dice: «⏳ … (401)»). Cura: è piccola, non ha dati, e se muore si rifà
  in mezza giornata; nessun backup.
- *Falsa sicurezza*: la prova ha dati finti, e un bug che morde solo i
  dati veri (una migrazione su una colonna piena) passa. Cura: il backup
  pre-deploy resta, e il generatore di dati finti è il cantiere che
  riduce il buco.
- *La promozione dimenticata* (§5) e *la tentazione di provare meno in
  locale* perché «tanto c'è la prova»: la regola delle due condizioni non
  si allenta.
- *Il nome `prova.barattolo.store` nei registri CT*: chi lo scopre trova
  un 403. Va bene.

**PRIMA del lancio del 10 ottobre: niente sul VPS, niente nel codice del
flusso, niente sul DNS.** Si può fare, a rischio zero: aprire il bot di
prova su BotFather (e NON metterne il token da nessuna parte); leggere le
risorse del VPS coi comandi del §2 (servono anche a decidere (a) o (b));
ordinare la macchina della prova e installarla SENZA record DNS pubblico
(si raggiunge per IP, Caddy senza TLS finché non c'è il nome); leggere
sul pannello di Register.it l'elenco COMPLETO dei record della zona
(serve al §DNS e al record della prova).

**DOPO (dall'11-12 ottobre), nell'ordine:** 1) il cantiere di codice
(leve, middleware, config d'esempio, procedura), push su main con la CI
verde: va in produzione col flusso di OGGI, e non cambia niente di
visibile perché i default sono quelli di oggi; 2) la macchina della
prova con `pronto` come ref: da qui ogni push arriva anche là; 3) il
record A e il bot di prova, il primo login di Andrea e Alan, il cartello
«istanza di prova»; 4) il ref `produzione` creato sul commit che gira e
il drop-in sul VPS: da questo momento la produzione si muove SOLO col
gesto; 5) il primo giro intero e le due prove del ritorno indietro
(revert per la via normale, emergenza a mano); 6) il verbale in
PRODUZIONE e la riga in CLAUDE.md (commit separato: cambia una REGOLA).
Il DNS (sotto) è indipendente: dopo tutto questo, in una settimana
tranquilla.

---

## Il DNS: restare su Register.it o spostare la zona

**Cosa è successo.** Il 7 ottobre `ns2.register.it` non rispondeva. Il
dominio ha DUE nameserver autoritativi, entrambi di Register.it; con uno
muto un resolver dovrebbe cavarsela con l'altro, ma una parte degli
utenti riceveva SERVFAIL dai resolver del proprio operatore. Due
spiegazioni possibili, e da qui non si distingue: (1) anche `ns1`
rispondeva male o a singhiozzo (sovraccarico da tutti i resolver che
ripiegavano su di lui), oppure (2) con DNSSEC acceso, un resolver che
convalida è più severo: una risposta incompleta o una firma che non
torna da un autoritativo in difficoltà diventa SERVFAIL invece di un
tentativo in più. L'8 ottobre Register.it ha sistemato. La lezione vale
in ogni caso: i due NS stanno nella stessa casa, e quando la casa ha un
problema il dominio non ha un piano B.

**Come stanno le cose, da inventariare (sul pannello di Register.it e
con `dig`, sola lettura, da incollare):**

```bash
dig +short NS barattolo.store @1.1.1.1
dig +short DS barattolo.store @1.1.1.1
dig +short A barattolo.store @8.8.8.8 ; dig +short A relay.barattolo.store @8.8.8.8
dig +short MX barattolo.store @1.1.1.1 ; dig +short TXT barattolo.store @1.1.1.1
dig +short CAA barattolo.store @1.1.1.1
dig +dnssec A barattolo.store @1.1.1.1 | grep -E 'flags|RRSIG' | head -3
```

(il `DS` deve mostrare il 47673 che Andrea cita; `TXT` dice SPF, DKIM,
DMARC e verifiche varie; il `flags: … ad` dell'ultimo dice che la
convalida DNSSEC passa oggi.) L'elenco COMPLETO dei record si prende dal
pannello, perché `dig` non elenca una zona: A, AAAA, CNAME, MX, TXT (SPF,
DKIM `*._domainkey`, DMARC `_dmarc`), SRV, CAA, e ogni sottodominio
(`relay`, la futura `prova`, eventuali `mail`, `autoconfig`).

**Opzione 1 — restare su Register.it.** Pro: zero lavoro, DNSSEC già
acceso, email e MX che funzionano, nessun account in più da proteggere.
Contro: due NS dello stesso fornitore sulla stessa rete, l'incidente del
7, nessuna leva nostra se ricapita. Cose che si possono fare RESTANDO:
una ronda DNS dal VPS (un `dig` ogni dieci minuti verso 1.1.1.1, 8.8.8.8,
9.9.9.9 e un resolver italiano, e un «📡 il DNS non risolve da X» su
Telegram alla prima risposta diversa da NOERROR: è lo stile di
`ronda-*.sh`, mezza giornata, e serve ANCHE dopo un eventuale trasloco);
chiedere a Register.it se ammette NS secondari esterni (un terzo NS in
un'altra casa: da verificare sul pannello, molti registrar con DNS
incluso non lo permettono).

**Opzione 2 — spostare la GESTIONE della zona (non il dominio) su un
servizio DNS anycast.** Il dominio resta registrato su Register.it (che
resta anche il posto dove si scrivono NS e DS); cambia solo chi risponde
alle domande. Candidati: **Cloudflare DNS** (gratuito, anycast su
centinaia di sedi, DNSSEC con un pulsante, API; il più usato) in sola
modalità DNS — NUVOLA GRIGIA su ogni record: il proxy arancione farebbe
passare da Cloudflare il traffico del sito e del relay, nasconderebbe al
server l'IP vero di chi chiama (i limiti per IP), cambierebbe il
certificato visto dal client, e non è quel che si vuole decidere qui.
**deSEC** (no-profit tedesco, gratuito, DNSSEC sempre acceso, API):
più vicino allo spirito del progetto, meno conosciuto. Hetzner DNS
(gratuito con l'account): DNSSEC da verificare prima di sceglierlo.
Pro: la zona risponde da decine di sedi indipendenti, un incidente di un
fornitore non spegne il dominio, DNSSEC gestito bene. Contro: un
fornitore in più (USA, nel caso di Cloudflare) e un ACCOUNT in più che
diventa un punto critico — chi entra lì sposta `barattolo.store` dove
vuole: 2FA con chiave hardware, email dedicata, niente login da
telefoni di passaggio; e la finestra di rischio del trasloco, sotto.

**I passi, nell'ORDINE, se si sceglie l'opzione 2** (Cloudflare lo
scrive così nei suoi documenti: con DNSSEC acceso, cambiare i NS senza
prima togliere il DS fa fallire la convalida, cioè SERVFAIL per tutti):

1. Inventario completo dei record (sopra) e copia in un file nel backup.
2. Creare la zona dal nuovo fornitore, ricopiare TUTTI i record (gli MX e
   i TXT dell'email sono quelli che si dimenticano), nuvola grigia
   ovunque; verificare interrogando DIRETTAMENTE i nuovi NS, prima che
   siano autoritativi: `dig @<ns-nuovo> barattolo.store A`, `MX`, `TXT`,
   `relay.barattolo.store A`. Tutto deve combaciare con oggi.
3. **Togliere il DS su Register.it** (spegnere DNSSEC), e ASPETTARE: il
   DS vive nella cache dei resolver per il suo TTL al registro di
   `.store` (di solito 24 ore, Cloudflare consiglia almeno un TTL intero,
   meglio una volta e mezza, cioè 24-48 ore). Si verifica con
   `dig +short DS barattolo.store @1.1.1.1` e `@8.8.8.8`: VUOTO da
   entrambi, due volte a distanza di ore. In questa finestra il dominio
   funziona, solo senza DNSSEC.
4. **Cambiare i NS su Register.it** verso quelli nuovi. Aspettare il TTL
   dei NS al registro (un'ora o più); verificare `dig +short NS` da più
   resolver e che il sito, il relay (`wss://relay.barattolo.store`) e
   l'email rispondano.
5. Qualche giorno di quiete, con la ronda DNS accesa.
6. **Riaccendere DNSSEC dal nuovo fornitore** e scrivere il NUOVO DS su
   Register.it (il pannello deve ammettere un DS «esterno» con NS non
   suoi: da verificare PRIMA di cominciare; se non lo ammette, si resta
   senza DNSSEC o si valuta il trasferimento del dominio, che è un'altra
   decisione). Verificare `dig +dnssec` con `ad` e un controllo esterno
   (DNSViz).

**Cosa si rompe se fatto male.** NS cambiati col DS vecchio ancora in
giro → SERVFAIL per TUTTI i resolver che convalidano, fino a 48 ore:
peggio del 7 ottobre. MX o TXT dimenticati → email che rimbalza o finisce
in spam, in silenzio. Il record di `relay` dimenticato → lo specchio del
libro P2P sparisce e il relay «risponde zero» (che il client legge come
«nessun ordine»). Un record scritto con l'IP sbagliato resta in cache
per il suo TTL: i TTL si abbassano a 300 PRIMA del trasloco, su
Register.it, qualche giorno avanti. Il webhook di Telegram, la Mini App,
il rinnovo dei certificati di Caddy non si accorgono di nulla finché il
record A risolve. **Quando:** non prima del 10, non nei giorni
dell'hackathon (17-18): una settimana tranquilla dopo il 20 ottobre,
cominciando dal passo 3 un lunedì, così i passi 4-6 cadono in settimana.
Mezza giornata di lavoro, due giorni di attenzione.

**Raccomandazione sul DNS:** la ronda DNS subito dopo il lancio in ogni
caso; il trasloco su Cloudflare (o deSEC) in sola modalità DNS, con
l'ordine dei passi qui sopra, se Andrea e Alan accettano un account in
più da proteggere come una chiave. Non è urgente: è un incidente in un
anno, già risolto dal fornitore; è prudente, perché la prossima volta
non ci sarà niente da fare se non aspettare.

---

## Fonti (lette l'8 ottobre 2026)

- Hetzner, listino e rincari 2026: [Hetzner, price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/);
  [wz-it, Hetzner price increase June 2026](https://wz-it.com/en/blog/hetzner-price-increase-june-2026-cpx-ccx-alternatives/);
  [findstack, Hetzner price increase 2026](https://findstack.com/resources/hetzner-price-increase-2026);
  [heise, Cloud hoster Hetzner adjusts prices again](https://heise.de/-11333037);
  [vincentschmalbach.com, Hetzner cheap cloud unavailable](https://www.vincentschmalbach.com/hetzner-cheap-cloud-unavailable-price-increases/).
- Cloudflare, DNSSEC e trasloco di una zona con DNSSEC acceso:
  [DNSSEC](https://developers.cloudflare.com/dns/dnssec/);
  [Disable DNSSEC before adding a domain](https://developers.cloudflare.com/learning-paths/get-started/add-domain-to-cf/disable-dnssec);
  [DNS best practices, phase 1](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-1);
  [Transfer to Cloudflare](https://developers.cloudflare.com/registrar/domain-transfers/transfer-to-cloudflare).
- Sull'incidente di Register.it del 7 ottobre 2026 non ho trovato una
  fonte pubblica: la cronologia è quella riferita da Andrea.
- Il resto è letto nel repo: `deploy.sh`, `giudice_deploy.py`,
  `.github/workflows/prove.yml`, `deploy/*.service`, `deploy/utente/`,
  `deploy/RIPRISTINO.md`, `deploy/RIPRISTINO-RELAY.md`,
  `config_esempio.py`, `server.py` (`URL_PUBBLICO`, `LINK_BOT`,
  `registra_webhook_telegram`, `relay_di_casa`, `_host_con_hsts`),
  `docs/PRODUZIONE.md` (le voci citate).
