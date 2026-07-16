# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Architettura

- `server.py` — backend FastAPI + SQLite (`satmarket.db`), un solo file.
  Escrow LNbits (invoice key incassa, admin key paga), commissione 1%,
  notifiche via bot Telegram, ricerca AI (Haiku), orologio asyncio per gli
  sblocchi automatici (72h dalla consegna, 10gg dalla spedizione).
- `miniapp.html` — frontend intero in un file (HTML+CSS+JS, zero framework).
  Dentro Telegram: auth vera via initData. Dal browser: modalità demo.
- `config.py` — TUTTE le chiavi e impostazioni. NON è nella repo
  (.gitignore) e NON deve MAI entrarci. `config_esempio.py` è il modello.
- `importa_nostr.py` — importa annunci NIP-99/NIP-15 di un venditore
  consenziente da Nostr (npub e VENDITORE_ID vengono da config.py).

## Produzione

- VPS Hetzner Helsinki `46.62.162.103`, Ubuntu 26.04, servizio systemd
  `barattolo` (uvicorn su 127.0.0.1:8080 dietro Caddy con HTTPS).
- Dominio: https://barattolo.store — Bot: @ilbarattolobot (BotFather URL
  con `?v=2`, innocuo). Header anti-cache già attivi su `/` e
  `/miniapp.html`: non rimuoverli.
- Deploy: commit+push su main → sul server `cd satmarket && git pull &&
  systemctl restart barattolo`. Config e database NON viaggiano mai.

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI chiedere o gestire nsec (chiave privata Nostr) degli utenti.
   Decisione permanente. La via approvata è: badge npub auto-dichiarato →
   firma di sfida (post-lancio) → mai custodia di segreti altrui.
3. Il server pubblico serve SOLO `/`, `/miniapp.html`, `/foto/*` e `/api/*`.
   Non montare mai StaticFiles sull'intera directory (config e .git
   diventerebbero pubblici — falla già successa e chiusa).
4. Stati ordine: creato | locked | shipped | delivered | confirmed |
   released | dispute | return_pending | return_shipped | refund |
   refunded | annullato. Non inventarne di nuovi senza aggiornare
   frontend (STATES, stepper cassaforte) e notifiche.
5. Solo l'ACQUIRENTE può segnare "consegnato" (anti-frode venditore).
   Il venditore è protetto dall'auto-sblocco a 10 giorni e dal sollecito
   (max 1 ogni 24h).
6. Testare sempre in locale (MODALITA_COLLAUDO=True, tre identità finte:
   Compratore 111, Venditore 222, Admin 999) prima del deploy.
   In produzione MODALITA_COLLAUDO deve restare False.
7. Stile del codice esistente: commenti e nomi in italiano, tono caldo,
   niente refactoring di massa non richiesti, diff piccoli e verificabili.

## Stato (lug 2026) e prossimi lavori

Lanciando in rodaggio su community italiana, limite ~100k sats/annuncio.
Backlog concordato: badge npub nel profilo + sugli annunci; banner sulla
demo browser ("l'app vera è su Telegram → @ilbarattolobot"); commissione
minima fissa; poi post-lancio: firma di sfida Nostr, tracking verificato
via API corrieri, feedback/stelle, pubblicazione verso Nostr, NWC,
escrow on-chain 2-di-3, parere legale MiCA prima di crescere.
