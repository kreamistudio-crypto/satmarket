# Il collaudo di Barattolo (la vm-2050)

Scritto il 20 ott 2026 (cantiere collaudo-privato), dalle decisioni di
Andrea del 19 e 20 ottobre. Il disegno di partenza è
`docs/STUDIO-ISTANZA-PROVA-2026-10-08.md`; il perché di ogni pezzo sta
in `docs/CANTIERI.md`, voci «L'istanza di prova» (19 ott) e «Il
collaudo privato davvero», «Il recinto dei relay», «Il tetto in sats
del collaudo», «Il collaudo segue develop» (20 ott).

Niente qui dentro è un segreto: i segreti stanno sulla VM, in
`/etc/barattolo-collaudo/` (root:collaudo 750), e non passano mai in
chat, nel repo o in Syncthing.

## 1. Cos'è, in una riga

Una copia di Barattolo che gira come quella vera, sulla VM `vm-2050`
(LNVPS, `vm-2050.lnvps.cloud`, 185.18.221.42), raggiungibile su
**https://collaudo.barattolo.store** e dal bot **@barattolo_collaudo_bot**,
che **segue il ramo `develop`**. Serve a provare dal telefono i cantieri
PRIMA che arrivino in produzione. È privata: chi non è in
`PROVA_SOLO_IDS` vede solo la copertina «🧪 Collaudo privato» col login.

## 2. Il flusso: develop → collaudo → promozione → main

- Le sessioni (anche quelle cloud) pushano su **`develop`**, senza
  chiedere, ma solo a cantiere chiuso: suite e collaudi verdi. Su
  `develop` la CI NON parte (il workflow guarda solo `main`), quindi le
  prove le fa la sessione prima del push.
- Il collaudo, entro un minuto, mette su la punta di `develop` (anche
  un commit non firmato) e la riavvia. Se non regge torna da solo al
  commit di prima e lo dice nel bot di prova.
- Andrea prova dal telefono. Quando approva, **una sessione sul suo PC
  fa la promozione**: rebase dei commit di `develop` su `main`,
  rifirma con `andrea-firma-barattolo`, **un solo push** su `main`
  (solo col suo ok e la sua frase completa), poi la CI fino al verde e
  `pronto` come oggi. La produzione segue `pronto` su `main`, solo
  commit firmati: non cambia niente.
- **Dopo ogni promozione `develop` si rimette uguale a `main`**:
  `git push --force-with-lease origin origin/main:develop`. È l'unico
  force ammesso, solo su `develop` e solo dalla sessione della
  promozione: senza, `develop` (gli originali) e `main` (le copie
  rifirmate) divergerebbero a ogni giro. Il collaudo lo segue da solo.

## 3. I comandi, dal telefono (un'app ssh) o da una sessione

Sulla VM, come `debian`:

```bash
sudo collaudo                  # lo stato: cosa gira, da quale ramo, se in pausa
sudo collaudo pausa            # smette di seguire (per provare con calma)
sudo collaudo riprendi         # torna a seguire develop
sudo collaudo ramo cantiere/x  # segue un altro ramo, finche' non si da' riprendi
sudo collaudo azzera           # database e foto nuovi + la semina finta
```

`azzera` non cancella a mano: sposta il database e le foto vecchie in
`/srv/collaudo/barattolo/azzerati/` e ne tiene gli ultimi tre giri.
**Mai una copia del database vero sul collaudo.**

Il journal: `journalctl -u barattolo-collaudo -n 50` (il server),
`journalctl -u barattolo-collaudo-segui -n 20` (il seguace).

## 4. Le macchine e i pezzi sulla VM

| Cosa | Dove |
|---|---|
| L'utente | `collaudo` (di sistema, senza login), casa `/srv/collaudo` |
| Il codice | `/srv/collaudo/barattolo` (clone con tutti i rami) |
| Python | `/srv/collaudo/venv` (fastapi, uvicorn, httpx, anthropic, websocket-client, pillow, pillow-heif, cryptography, snowballstemmer, coincurve 21: la 19 non ha la ruota per il Python 3.13 della VM) |
| Il config | `/srv/collaudo/barattolo/config.py`, root:collaudo 640, scritto DALLA sezione «L'istanza di prova» di `config_esempio.py`, mai copiato dal VPS |
| I segreti | `/etc/barattolo-collaudo/` (root:collaudo 750): `bot_token` (il bot di prova), `avvisi_chat` (a chi il seguace scrive) |
| Il servizio | `barattolo-collaudo.service` su 127.0.0.1:8090 (`deploy/collaudo/`) |
| Il seguace | `/usr/local/sbin/collaudo-segui` (copia di `deploy/collaudo/segui.sh`) + `barattolo-collaudo-segui.timer` ogni minuto |
| Il comando | `/usr/local/bin/collaudo` (copia di `deploy/collaudo/collaudo.sh`) |
| Il sito | Caddy 2.6 con `deploy/collaudo/Caddyfile` (HTTPS da solo, X-Robots-Tag noindex) |
| I pagamenti | LNbits FakeWallet in Docker, `deploy/collaudo/compose-lnbits.yaml`, solo 127.0.0.1:5001 |
| Il bot di prova | `@barattolo_collaudo_bot`; il canale «Vetrina · prova» è `-1003944008599` |
| Il dominio | record A `collaudo.barattolo.store` → 185.18.221.42 (Register.it, TTL 300). Il DS e la zona non si toccano |

Il seguace e il comando si posano a mano dal clone: una versione nuova
di `segui.sh` non entra da sola (il giudice non si riscrive col commit
che tira, come `deploy.sh`):

```bash
sudo install -m 755 /srv/collaudo/barattolo/deploy/collaudo/segui.sh /usr/local/sbin/collaudo-segui
sudo install -m 755 /srv/collaudo/barattolo/deploy/collaudo/collaudo.sh /usr/local/bin/collaudo
```

## 5. Come arriva il codice: la deploy key

Il repo è privato. La VM lo legge con una **deploy key di sola
lettura**, nata sulla VM per l'utente `collaudo`
(`/srv/collaudo/.ssh/deploy_satmarket`, ed25519, senza passphrase:
serve al timer), impronta `SHA256:HM3wNcioKTPSOriZl0GJgwODtQQD1Da//vJxJpoyjzI`.
Andrea l'ha aggiunta su GitHub → satmarket → Settings → Deploy keys,
**senza «Allow write access»**; un push di prova dalla VM risponde «The
key you are authenticating with has been marked as read only». L'host
di GitHub è in `/srv/collaudo/.ssh/known_hosts`, confrontato con
l'impronta che GitHub pubblica (`gh api meta`). Il codice di un ramo che
gira sulla VM può leggere quella chiave: apre solo la lettura del repo,
cioè quel che il ramo ha già. Per ruotarla: una chiave nuova, la si
aggiunge, si toglie la vecchia da GitHub.

## 6. Cosa è vero e cosa è finto sul collaudo

- **Le persone**: vere. Si entra con la propria identità Telegram (o la
  propria chiave Nostr, bunker compreso) e solo se si è in
  `PROVA_SOLO_IDS`. Chi non c'è: 403 sulle API, la copertina sulle
  pagine, il bot non gli risponde.
- **I dati del mercatino**: finti (la semina), database nuovo.
- **I pagamenti del mercatino**: finti (LNbits FakeWallet: il «paga» si
  fa da un secondo wallet nel pannello, dal tunnel ssh).
- **Nostr**: il server parla solo coi relay di casa della VM (il
  recinto: `RELAY_NOSTR` col relay di prova su 127.0.0.1, o nessuno), con
  una chiave NUOVA. Mai `relay.barattolo.store`, mai i relay pubblici.
- **Il P2P**: VERO (decisione di Andrea con Alan): il coordinatore
  Mostro di produzione, ordini e sats veri, coi paletti — solo gli id in
  lista, ogni ordine al massimo `P2P_MAX_SATS_PROVA` (10.000 sats), sulla
  VM MAI la chiave del moderatore/solver né altre chiavi Mostro di
  produzione. Le dispute degli ordini fatti dal collaudo si risolvono
  dal Barattolo vero.
- **On-chain**: signet (è una costante del codice, `ONCHAIN_RETE`; dal
  20 ott 2026, prima era testnet), solo admin; quando servirà la
  verifica dei pagamenti (tappa 4), l'API pubblica signet di
  mempool.space (`https://mempool.space/signet/api`), nessun nodo
  nostro. Le monete di prova si chiedono a un faucet signet.
- **Telegram**: il bot di prova e il solo canale «Vetrina · prova».
- **Lo swap dei venditori** (regola di Andrea): ogni tappa
  si prova QUI col SATS Routing di cartone (`cartone_satsrouting.py`)
  e, dalla tappa 3 (lo swap dal telefono), col regtest di Boltz, prima
  di accendere `SWAP_ATTIVO` in produzione. Sul collaudo: `SWAP_ATTIVO`,
  `SWAP_RETE = "regtest"` e `SWAP_API_BASE` sull'API del regtest. Quella
  base la chiamano il server (le tariffe) e il BROWSER del telefono (lo
  swap, con CORS): va scelta perché regga tutt'e due (PRODUZIONE, «LO
  SWAP DAL TELEFONO: LE LEVE»). Mai SATS Routing vero da qui.

## 7. Accendere da zero (i gesti, uno alla volta col sì di Andrea)

1. Pacchetti: `caddy`, `sqlite3` (fatto il 20 ott; Caddy fermo finché
   non c'è il servizio).
2. L'utente `collaudo`, `/etc/barattolo-collaudo`, il token del bot
   spostato senza leggerlo (fatto il 20 ott).
3. La deploy key (fatto il 20 ott).
4. Il clone e il venv (fatto il 20 ott).
5. LNbits FakeWallet: `compose-lnbits.yaml` in `/srv/collaudo/lnbits`,
   `up -d`, poi `ss -tln` deve mostrare SOLO `127.0.0.1:5001`; i due
   wallet (il negozio e «il telefono») dal pannello, dal tunnel
   `ssh -N -L 5001:127.0.0.1:5001`.
6. Il config dalla sezione di prova, i segreti nati sulla VM (la nsec
   nuova, il segreto del webhook, la chiave dei contenuti, il segreto del
   profilo P2P), e il relay di prova se lo si vuole.
7. Il servizio, poi Caddy, poi `ufw allow 80,443/tcp`; Andrea in
   BotFather: Configure Mini App e Menu Button su
   `https://collaudo.barattolo.store`, `/setdomain` per il login dal
   browser.
8. Il seguace: le due copie, `systemctl enable --now
   barattolo-collaudo-segui.timer`.
9. Il comando e la prima semina.

## 8. Spegnere

`sudo systemctl disable --now barattolo-collaudo-segui.timer
barattolo-collaudo caddy` e `docker compose -p collaudo-lnbits down` (i
dati di LNbits restano nel volume). Il dominio può restare: senza Caddy
non risponde niente.

## 9. Gli avanzi di RGB che restano (decisione di Andrea, 20 ott)

RGB non si usa più (HACKATHON-SETUP §14.5) e sulla VM restano, apposta:
`~/rgb` (i sei wallet, 75 MB), i volumi della catena signet (31,2 GB) e
dell'indice (1,8 GB) coi container fermi e `restart=no`, l'utente `pull`
con la sua chiave vincolata a `internal-sftp -R`, gli archivi in
`/var/backups/rgb`, e sul PC la gamba `rgb/` di `pull.ps1` (non trova
archivi nuovi). Liberare i 33 GB è un gesto a parte, che decide Andrea.

## 10. Passare alla strada A (il ref `produzione`), più avanti

Oggi la produzione segue `pronto` su `main` e il collaudo `develop`
(strada B). Se un giorno Andrea vorrà che anche ciò che è su `main`
arrivi in produzione solo con un suo gesto: STUDIO-ISTANZA-PROVA §5, in
breve —
1. `git push origin origin/main:refs/heads/produzione` sul commit che
   GIÀ gira in produzione (il VPS non si muove);
2. sul VPS il drop-in
   `/etc/systemd/system/barattolo-deploy.service.d/produzione.conf`
   con `[Service]` e `Environment=BARATTOLO_RAMO=produzione`, poi
   `systemctl daemon-reload` (lo esegue Andrea: il VPS è fuori dal
   perimetro delle sessioni);
3. da lì la produzione si muove solo col gesto di Andrea,
   `git fetch origin && git push origin origin/pronto:refs/heads/produzione`
   (in avanti veloce, mai `--force`). `deploy.sh` e il suo giudice non
   cambiano di una riga.
