# Se muore X, si fa così

Il piano unico (25 nov 2026, cantiere quadro-servizi). Una riga per
servizio: chi se ne accorge, cosa si perde, il primo gesto e il foglio
lungo. I fogli lunghi restano dove sono (`RIPRISTINO.md` per il VPS,
`RIPRISTINO-RELAY.md` per il relay); qui sotto ci sono quelli che
mancavano: nodo, n8n, VM collaudo.

## Come ci si accorge

- **Il quadro**: nel pannello admin dell'app, cassetto **🩺 Servizi**.
  Ogni servizio, l'ultimo segnale, l'uptime dei 30 giorni, l'età del
  backup, e i certificati.
- **Gli avvisi**: ogni macchina manda un battito ogni cinque minuti
  (`deploy/battito/`). Un servizio che tace da venti minuti fa partire un
  avviso nella stanza degli errori; quando torna, un secondo avviso.
- **Il VPS lo guarda il relay, da fuori**: se `barattolo.store` non
  risponde per un quarto d'ora, l'avviso parte dal relay su Telegram
  (il VPS morto non può dirlo da solo).
- Restano le ronde di sempre: la ronda del nodo (ogni ora, e il giro
  lungo alle 9 UTC), la ronda tor, la ronda del relay (ogni mattina), la
  sentinella dentro il server.

## La tabella

| Servizio | Macchina | Cosa si perde | Primo gesto | Foglio lungo |
|---|---|---|---|---|
| **Barattolo** (mercatino, bot, sito) | VPS | Le ore dopo l'ultimo archivio (prima di ogni deploy e alle 04:30). I sats NO: stanno sul nodo | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/api/salute` e `journalctl -u barattolo -n 50` sul VPS | `RIPRISTINO.md` |
| **Bot Telegram** | VPS | Niente: vive col server | Il webhook si registra da solo all'avvio (riga «🔔 Webhook Telegram» nel journal) | `RIPRISTINO.md`, passo 6 |
| **Sito .onion** | VPS | L'indirizzo, se la chiave non torna intera | `systemctl status tor@default` sul VPS | `RIPRISTINO.md`, passo 4 (la liturgia dell'onion) |
| **LNbits** (la cassaforte) | VPS | Chi possiede quali sats, se manca il suo database | `docker ps` sul VPS; il ponte: `journalctl -u barattolo \| grep 🌉` | Sotto, «LNbits» |
| **LND** | Nodo | Niente, se seed e SCB ci sono. MAI un `channel.db` vecchio | `cd ~/nodo && docker compose ps` sul nodo | Sotto, «Il nodo» |
| **Mostro** (P2P) | Nodo | Gli scambi aperti, se manca `mostro.db` | `docker compose logs --since 30m mostro` da `~/nodo` | Sotto, «Il nodo» |
| **Relay Nostr** | Relay | Niente: gli eventi sono anche sugli altri relay | `docker compose ps` in `/opt/relay` | `RIPRISTINO-RELAY.md` |
| **n8n** | Relay | I flussi (Tappo, bozze delle novità) e le credenziali | `docker compose ps` in `/opt/n8n-barattolo` | Sotto, «n8n» |
| **Collaudo** | VM collaudo | Niente di vero: si rifà da develop | `sudo collaudo stato` sulla VM | Sotto, «La VM collaudo» |
| **Runner della CI** | VM collaudo | Il deploy si ferma: senza CI verde `pronto` non avanza | `systemctl status ci-runner-vm-2050` sulla VM | Sotto, «La VM collaudo» |

## LNbits (sul VPS)

La cassaforte del mercatino è LNbits sul VPS, coi soldi sul LND del nodo
(il ponte è WireGuard). Il suo archivio è dentro quello del VPS:
`lnbits/` (`.env`, `docker-compose.yml`, `data/` col database copiato a
caldo) e `sistema/wg0.conf` e le unit del ponte.

1. Se è solo LNbits fermo: `cd /opt/lnbits && docker compose up -d`, poi
   la riga 🌉 nel journal di barattolo.
2. Se il VPS è perso: si rifà tutto con `RIPRISTINO.md`; LNbits torna da
   `lnbits/` dell'archivio. La chiave privata di WireGuard NON è
   nell'archivio, apposta: se ne fa una nuova e si scrive la pubblica
   sul nodo (PRODUZIONE, «IL PONTE VIA WIREGUARD»).
3. ⚠️ Un archivio con «database LNbits NON copiato» nella didascalia ha
   i sats senza nomi: si prende quello prima.

## Il nodo (LND e Mostro)

I sats del nodo (canali e cassaforte) si salvano con **due cose sole**:
le 24 parole (offline, su carta) e l'**SCB** (`channel.backup`), che
entra ogni notte alle 03:30 nell'archivio del nodo (`backup-nodo.sh`,
cifrato con la chiave age DEL NODO, diversa da quella di Barattolo) e il
PC lo tira giù in `BarattoloBackup`.

1. **Un container fermo**: `cd ~/nodo && docker compose up -d`; dopo un
   `restart mostro-net` sempre `up -d --force-recreate mostro`
   (PRODUZIONE, «IL NAMESPACE PRESTATO»).
2. **Disco pieno**: la ronda suona all'85%. Le immagini vecchie di
   Mostro si tolgono una per una, mai quella in servizio né quella di
   ritorno, mai i dati di LND.
3. **Macchina persa**: macchina nuova, lo stesso `docker compose` dal
   repo (`deploy/nodo/`), LND ripristinato **dalle 24 parole più l'SCB**.
   L'SCB non riapre i canali: li CHIUDE, e i sats tornano on-chain nel
   wallet del nodo (servono giorni). Poi si riaprono i canali.
   ⚠️ **MAI un `channel.db` da un archivio**: uno stato vecchio di un
   canale fa perdere i fondi. Per questo l'archivio non lo contiene.
4. Mostro vuole indietro `mostro.db`, `settings.toml` e la sua chiave:
   senza la chiave è un altro coordinatore e gli scambi aperti restano
   orfani. ⚠️ `backup-nodo.sh` NON è nel repo (vive solo sul nodo):
   che l'archivio del nodo li contenga tutti e tre NON è verificato da
   qui. Lo dice la prova di giugno, o prima un `tar -t` sull'archivio.
5. Il ponte verso il VPS va rifatto (la pubblica WireGuard nuova).

## n8n (sul relay)

Dal 25 nov 2026 entra nel backup del relay (`backup-relay.sh`): la
cartella `/opt/n8n-barattolo` intera, col database copiato a caldo e il
`.env` con la `N8N_ENCRYPTION_KEY`. Le due cose vanno insieme: senza la
chiave le credenziali nel database non si aprono.

1. **Fermo**: `cd /opt/n8n-barattolo && docker compose up -d`.
2. **Macchina persa**: dopo il relay (`RIPRISTINO-RELAY.md`), si
   decifra l'ultimo archivio del relay, si rimette `n8n-barattolo/` in
   `/opt`, `docker compose up -d`. Il blocco `n8nb` del Caddyfile è già
   nell'archivio del relay (solo `/webhook*` aperto, il resto 404).
3. Se il nome del dominio cambia, va cambiato `WEBHOOK_URL` nel `.env`
   e l'indirizzo che il VPS chiama.

## La VM collaudo (collaudo e runner della CI)

Niente qui è vero: il collaudo segue develop e si rifà.

1. **Il collaudo fermo**: `sudo collaudo stato`, poi
   `sudo systemctl restart barattolo-collaudo`.
2. **Il runner fermo**: la CI resta «Queued» e il deploy aspetta.
   `sudo systemctl restart ci-runner-vm-2050`. Se la VM non torna:
   `RUNNER_PROVE` nelle variabili del repo riporta il job su GitHub
   (PRODUZIONE, «IL RUNNER DELLA CI SULLA VM-2050»).
3. **Macchina persa**: si rifà da `docs/COLLAUDO.md`. Il suo config è un
   segreto a sé (bot di prova): non è nei backup, si riscrive.

## Le scadenze scritte a mano

Quelle che nessuna macchina rinnova da sola. I certificati dei domini li
rinnova Caddy, e il quadro li guarda ogni dodici ore.

| Cosa | Scade | Dove si rifà |
|---|---|---|
| Il macaroon di LND copiato sul VPS | 22 ott 2027 | PRODUZIONE, «LA CASSAFORTE SUL NODO» |
| Il token di sola lettura del deploy sul VPS | nov 2027 | `/root/.git-credentials` sul VPS |

## La prova di ripristino, ogni tre mesi

Un backup mai aperto è una speranza. Una macchina alla volta, senza
toccare la produzione: si apre l'ultimo archivio e si controlla che
dentro ci sia tutto.

| Quando | Macchina | Cosa si prova |
|---|---|---|
| dicembre 2026 | VPS | Il drill di `RIPRISTINO.md` (archivio, database, contenuti digitali) |
| marzo 2027 | Relay + n8n | L'archivio del relay si apre, e il database di n8n con lui |
| giugno 2027 | Nodo | L'archivio del nodo si apre, l'SCB ha tutti i canali, Mostro ha db, settings e chiave |
| settembre 2027 | VM collaudo | Si rifà da zero seguendo `docs/COLLAUDO.md` |
