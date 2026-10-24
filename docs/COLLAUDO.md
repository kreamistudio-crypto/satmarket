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
- **Le dipendenze arrivano da sole** (dal 20 ott 2026): se il commit
  nuovo cambia `requirements.txt`, il seguace la installa nel venv
  (`pip install -r`, senza `-U`, come il padrone del venv) PRIMA di
  mettere su il codice. Se pip non ce la fa resta sul commit di prima
  senza bocciarlo, lo dice una volta nel bot («📦 Collaudo: le
  dipendenze di … non si installano») e riprova ogni minuto. Niente
  `pip install` a mano sulla VM.
- Quel che un cantiere lascia da fare sul VPS, sul nodo o sul relay
  (leve del config, comandi `lncli`, BotFather) non arriva col push: sta
  in `docs/DA-FARE-ANDREA.md`, coi comandi pronti. La sessione della
  promozione lo legge prima di promuovere.
- Andrea prova dal telefono. Quando approva, **una sessione sul suo PC
  fa la promozione**: rebase dei commit di `develop` su `main`,
  rifirma con `andrea-firma-barattolo`, **un solo push** su `main`
  (solo col suo ok e la sua frase completa), poi la CI fino al verde e
  `pronto` come oggi. La produzione segue `pronto` su `main`, solo
  commit firmati: non cambia niente.
- **Prima di una promozione, i collaudi della CI senza coincurve** (24
  ott 2026, cantiere collaudi-senza-coincurve). Il runner della CI non
  ha coincurve, il PC sì: un collaudo che lo usa nudo è verde qui e
  rosso là, e `pronto` resta fermo (successo con la promozione del 24
  ott). Sull'albero rebasato, un venv con le SOLE dipendenze del
  workflow (le righe `pip install` di `prove.yml`), e lì dentro:
  `python -c "import coincurve"` deve dire ModuleNotFoundError, poi
  `python collaudi_ci.py --elenco ci/collaudi.txt --paralleli 2`.
  `prove_collaudi_senza_coincurve` guarda la forma (nessun import nudo
  di coincurve nei collaudi dell'elenco); il giro nel venv è la prova.
- **La suite severa sul PC senza saltate: nostr-tools fuori dal repo**
  (25 ott 2026, cantiere prove-stabili). `prove_annuncio_identita` fa
  girare `deploy/rgb/identita.mjs`, che importa nostr-tools: senza, la
  sezione si salta e con `PROVE_SEVERE=1` una saltata è rossa. Sul PC
  fisso sta in `C:\Users\Andrea\barattolo-prove\nostr-tools` (fuori
  dal repo: Barattolo non è un progetto npm), installato come fa il
  workflow, alla stessa versione, e la variabile utente
  `IDENTITA_NODE_MODULES` gli punta (la stessa che il workflow dà alla
  prova). Si rifà così, da PowerShell (la cartella prima: npm non la crea):
  `New-Item -ItemType Directory -Force "$env:USERPROFILE\barattolo-prove\nostr-tools"`,
  poi `npm install --no-save --no-package-lock --no-audit --no-fund --prefix "$env:USERPROFILE\barattolo-prove\nostr-tools" nostr-tools@2.25.2`
  e poi
  `[Environment]::SetEnvironmentVariable('IDENTITA_NODE_MODULES', "$env:USERPROFILE\barattolo-prove\nostr-tools", 'User')`.
  La variabile la vedono i terminali e le sessioni aperti DOPO; se il
  workflow sale di versione (la riga `nostr-tools@` di `prove.yml`) si
  rifà `npm install` con la versione nuova. Si toglie cancellando la
  cartella e la variabile (`...SetEnvironmentVariable('IDENTITA_NODE_MODULES', $null, 'User')`).
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
Poi semina il mercatino FINTO di `semina_collaudo.py`: quattro venditori
di prova, quattordici annunci in dodici categorie con foto finte («FOTO
DI PROVA»), due venditori di servizi con undici lavori di prova (uno per
ogni card della sezione Lavoro), e due ordini comprati dal primo id della lista (uno in
corso, uno concluso), per provare liste, carrello, chat e «I miei
ordini». La semina si ferma da sola se non e' un'istanza di prova, se
`URL_PUBBLICO` e' barattolo.store (o non e' dichiarato) e se il database
sta nella cartella della produzione.
**Mai una copia del database vero sul collaudo.**

Il journal: `journalctl -u barattolo-collaudo -n 50` (il server),
`journalctl -u barattolo-collaudo-segui -n 20` (il seguace).

## 4. Le macchine e i pezzi sulla VM

| Cosa | Dove |
|---|---|
| L'utente | `collaudo` (di sistema, senza login), casa `/srv/collaudo` |
| Il codice | `/srv/collaudo/barattolo` (clone con tutti i rami) |
| Python | `/srv/collaudo/venv` (fastapi, uvicorn, httpx, anthropic, websocket-client, pillow, pillow-heif, cryptography, snowballstemmer, coincurve 21: la 19 non ha la ruota per il Python 3.13 della VM). Dal 20 ott 2026 la lista è `requirements.txt` e la installa il seguace (embit compreso); l'ultima installata è in `/srv/collaudo/stato/requisiti` (la sua impronta) |
| Il config | `/srv/collaudo/barattolo/config.py`, root:collaudo 640: `config_esempio.py` di develop con in fondo il blocco «IL COLLAUDO (vm-2050)», che NON contiene segreti — li legge dai file con `_segreto(nome)`. Mai copiato dal VPS |
| I segreti | `/etc/barattolo-collaudo/` (root:collaudo 750, i file 640): `bot_token` (il bot di prova), `webhook_segreto`, `lnbits_invoice_key` e `lnbits_admin_key` (il wallet «Negozio collaudo»), `nostr_nsec` (la chiave NUOVA del collaudo), `profilo_p2p`, `chiave_contenuti`, `avvisi_chat` (a chi il seguace scrive). Nati sulla VM o arrivati con `read -s`, mai stampati |
| Il servizio | `barattolo-collaudo.service` su 127.0.0.1:8090 (`deploy/collaudo/`), tetto `MemoryMax=700M` |
| Il seguace | `/usr/local/sbin/collaudo-segui` (copia di `deploy/collaudo/segui.sh`) + `barattolo-collaudo-segui.timer` ogni minuto |
| Il comando | `/usr/local/bin/collaudo` (copia di `deploy/collaudo/collaudo.sh`) |
| Il sito | Caddy 2.6 con `deploy/collaudo/Caddyfile` (HTTPS da solo, X-Robots-Tag noindex) |
| I pagamenti | LNbits FakeWallet in Docker, `deploy/collaudo/compose-lnbits.yaml`, solo 127.0.0.1:5001, tetto 400 MB. Il super utente e' di Andrea (KeePass); i wallet «Negozio collaudo» (il server) e «Telefono collaudo» (paga le fatture finte). Il pannello dal PC sulla porta locale **5002**, mai la 5001 (che e' il tunnel verso il LNbits VERO del VPS): `ssh -i ~/.ssh/lnvps -N -L 5002:127.0.0.1:5001 debian@vm-2050.lnvps.cloud`, poi `http://127.0.0.1:5002` |
| Il runner della CI | sulla stessa VM: `ci-runner-vm-2050` (utente `ci`, `MemoryMax` 2,5 GB). Il collaudo non tocca `/home/ci` ne' `/opt/hostedtoolcache` (`collaudo` non e' nel gruppo `ci`), e i suoi pezzi hanno un tetto di memoria apposta |
| Il bot di prova | `@barattolo_collaudo_bot`; il canale «Vetrina · prova» è `-1003944008599` |
| Il dominio | record A `collaudo.barattolo.store` → 185.18.221.42 (Register.it, TTL 300). Il DS e la zona non si toccano |

Il seguace e il comando si posano a mano dal clone: una versione nuova
di `segui.sh` non entra da sola (il giudice non si riscrive col commit
che tira, come `deploy.sh`). ⚠️ Quella del 20 ott 2026 (le dipendenze
prima del codice) va posata una volta: finché gira la vecchia, embit
non arriva e il foglio on-chain dice «manca embit» (il resto vive):

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
  **Per aprirla a tutti** (23 ott 2026): `PROVA_APERTA = True` nel config
  e il riavvio, con la lista che RESTA piena. Mai svuotarla per aprire:
  la lista è anche il segno «questa è una prova», e senza di lei cadono
  il recinto dei relay (annunci e post finirebbero sui relay veri), il
  tetto degli ordini P2P e la semina. Il P2P resta di `P2P_PROVA_IDS`.
- **I dati del mercatino**: finti (la semina), database nuovo.
- **I pagamenti del mercatino**: finti (LNbits FakeWallet: il «paga» si
  fa da un secondo wallet nel pannello, dal tunnel ssh).
- **Nostr**: il server parla solo coi relay di casa della VM (il
  recinto: `RELAY_NOSTR` col relay di prova su 127.0.0.1, o nessuno: dal
  20 ott nessuno), con una chiave NUOVA. Annunci, post e DM mai su
  `relay.barattolo.store` ne' sui relay pubblici.
- **Il P2P**: VERO (decisione di Andrea con Alan): il coordinatore
  Mostro di produzione, ordini e sats veri, coi paletti — solo gli id in
  lista, ogni ordine al massimo `P2P_MAX_SATS_PROVA` (10.000 sats), sulla
  VM MAI la chiave del moderatore/solver né altre chiavi Mostro di
  produzione. Le dispute degli ordini fatti dal collaudo si risolvono
  dal Barattolo vero. I relay del P2P sono le STESSE righe della
  produzione (`MOSTRO_RELAY`, `_SPECCHIO`, `_CONFERMA`),
  `relay.barattolo.store` compreso (decisione di Andrea, 20 ott: i relay
  veri solo per il P2P).
- **On-chain**: signet (è una costante del codice, `ONCHAIN_RETE`; dal
  20 ott 2026, prima era testnet), solo admin; quando servirà la
  verifica dei pagamenti (tappa 4), l'API pubblica signet di
  mempool.space (`https://mempool.space/signet/api`), nessun nodo
  nostro. Le monete di prova si chiedono a un faucet signet
  (la catena signet di RGB sulla VM resta spenta).
- **Telegram**: il bot di prova e il solo canale «Vetrina · prova».
- **Lo swap dei venditori** (regola di Andrea): ogni tappa
  si prova QUI col SATS Routing di cartone (`cartone_satsrouting.py`)
  e, dalla tappa 3 (lo swap dal telefono), col regtest di Boltz, prima
  di accendere `SWAP_ATTIVO` in produzione. Sul collaudo: `SWAP_ATTIVO`,
  `SWAP_RETE = "regtest"` e `SWAP_API_BASE` sull'API del regtest. Quella
  base la chiamano il server (le tariffe) e il BROWSER del telefono (lo
  swap, con CORS): va scelta perché regga tutt'e due (PRODUZIONE, «LO
  SWAP DAL TELEFONO: LE LEVE»). Mai SATS Routing vero da qui.
  DALLA TAPPA 4 (24 ott 2026, il server PAGA la fattura dello swap: CANTIERI,
  «Lo swap, tappa 4») la prova sul regtest e' lo swap INTERO, coi sats
  di regtest che si muovono davvero. I passi, ognuno scritto per intero e
  col sì di Andrea prima di farlo:
  1. LA MEMORIA. Il regtest di Boltz (bitcoind, i nodi Lightning,
     l'esplora, il backend, il suo database) non sta nei 3,8 GB accanto
     al runner della CI (2,5 GB): per la durata della prova il runner si
     ferma e `RUNNER_PROVE` torna vuota (la CI va su GitHub), oppure il
     regtest gira su un'altra macchina raggiunta in tunnel. Si decide
     prima, guardando `free -m`.
  2. IL REGTEST. Il repo `BoltzExchange/regtest` a un commit scelto e
     scritto qui, letto prima il suo README (porte, nomi dei nodi,
     comandi di `bitcoin-cli` e `lncli`); su, e si guarda che l'API del
     backend dica le tariffe (`/v2/swap/reverse`) e l'esplora l'altezza
     (`/blocks/tip/height`).
  3. CHI PAGA. Il LNbits della VM e' un FakeWallet: una fattura di
     regtest la paga solo un LND di regtest. Un nodo del regtest diventa
     la fonte di un LNbits di prova (o del LNbits della VM per la durata
     della prova), con un canale verso il nodo di Boltz e liquidita' in
     uscita; chi compra paga con `lncli` di un altro nodo.
  4. LE BASI. Il server legge tariffe e mempool, il BROWSER del telefono
     chiama le stesse basi con CORS: si sceglie come le raggiungono
     tutt'e due (HTTPS per il telefono). Prima si guarda, sola riga,
     `grep -n "^MODALITA_COLLAUDO" config.py`: in collaudo il server
     legge solo da 127.0.0.1, e con basi fuori casa preventivo e
     pagamento direbbero «non risponde» — da decidere li'.
  5. IL CONFIG DELLA VM, in fondo: `SWAP_ATTIVO = True`, `SWAP_RETE =
     "regtest"`, `SWAP_API_BASE` e `SWAP_MEMPOOL_API` sulle basi del
     punto 4, `SWAP_REFERRAL_ID = ""` (il codice partner e' di SATS
     Routing vero), riavvio; il pannello «⚙️ Stato delle leve» li dice.
  6. IL GIRO. Un ordine confermato del moderatore, «₿ On-chain (swap)»,
     le parole, l'indirizzo bcrt1 di un wallet di regtest; nel journal
     «controlli passati», «registrato», «in_volo»; Boltz blocca, il
     telefono ritira, un blocco minato, la fattura si chiude, «pagato» e
     l'ordine chiuso; l'indirizzo riceve i sats (`bitcoin-cli`).
  7. LE ROTTURE. Il telefono chiuso prima del ritiro: il pagamento resta
     in volo, senza 🧊, finche' i blocchi minati non passano la scadenza;
     poi Boltz si riprende i bitcoin e il pagamento torna indietro
     («fallito», l'incasso di nuovo libero). LNbits fermato a meta'
     pagamento: in volo o 🧊, mai un secondo pagamento. Un tetto basso
     nel config: il no, e la frase sul telefono.
  8. LA PULIZIA. Il config com'era, il regtest giu', il runner su.

## 7. Accendere da zero (i gesti, uno alla volta col sì di Andrea)

1. Pacchetti: `caddy`, `sqlite3` (fatto il 20 ott; Caddy fermo finché
   non c'è il servizio).
2. L'utente `collaudo`, `/etc/barattolo-collaudo`, il token del bot
   spostato senza leggerlo (fatto il 20 ott).
3. La deploy key (fatto il 20 ott).
4. Il clone e il venv (fatto il 20 ott).
5. LNbits FakeWallet: `compose-lnbits.yaml` in `/srv/collaudo/lnbits`
   (`docker compose -f … --project-directory /srv/collaudo/lnbits -p
   collaudo-lnbits up -d`: `debian` non entra in quella cartella), poi
   `ss -tln` deve mostrare SOLO `127.0.0.1:5001`; il super utente e i due
   wallet dal pannello, dal tunnel sulla porta 5002 (fatto il 20 ott).
6. Il config: i segreti nati sulla VM (la nsec nuova, il segreto del
   webhook, la chiave dei contenuti, il segreto del profilo P2P) e le due
   chiavi di LNbits arrivate con `read -s`; `config.py` col blocco che li
   legge dai file; il controllo che si importi come `collaudo` (fatto il
   20 ott; npub del collaudo `npub15vddg5h70wyg5sf32e5a5u8x46824f89c8zaeeldu4tawxsv8v0s59pac`).
7. Il codice su develop, il servizio (col drop-in `memoria.conf`),
   Caddy, `ufw allow 80/tcp` e `443/tcp`; Andrea in BotFather: Configure
   Mini App e Menu Button su `https://collaudo.barattolo.store`,
   `/setdomain`; poi `TELEGRAM_MINIAPP_LINK` acceso (fatto il 20 ott). Il
   webhook lo registra il server da solo, sul BOT DI PROVA: un «SSL
   error» in `getWebhookInfo` nei primi secondi e' di quando il
   certificato non era ancora nato, e sparisce alla prima consegna.
8. Il seguace: le due copie, la cartella `/srv/collaudo/stato`,
   `avvisi_chat`, `systemctl enable --now barattolo-collaudo-segui.timer`
   (fatto il 20 ott). IL RITORNO INDIETRO E' PROVATO dal vivo: dal
   commit precedente di develop, una passata con la salute finta
   (`sudo env COLLAUDO_SALUTE=http://127.0.0.1:9/finta COLLAUDO_ATTESA=5
   /usr/local/sbin/collaudo-segui`) ha messo su la punta, non ha visto la
   salute, e' tornata al commit di prima, ha timbrato il bocciato (non
   riprovato al giro dopo) e ha scritto nel bot di prova; tolto il
   timbro, e' tornata in punta. Subito dopo un ritorno la salute dice
   000 per qualche secondo: il servizio si sta riavviando.
9. Il comando e la prima semina (`sudo collaudo azzera`), fatto il 20
   ott: posati da develop il seguace nuovo (le dipendenze prima del
   codice), il comando, le due unita' col tetto e il compose (le copie
   di prima in `/root/prima-del-9`); il seguace ha installato
   `requirements.txt` (embit 0.8.0) e riavviato in pari;
   `ONCHAIN_ATTIVO` e' acceso (solo admin) e `MERCATINO_CHAT_ORDINI =
   True` sta in fondo al config; la semina ha dato 4 venditori, 12
   annunci attivi e 2 venduti, 2 ordini per il primo id della lista.

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
