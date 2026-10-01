# Hackathon RGB di Torino (17-18 ott 2026): l'infrastruttura preparata prima

Stato al 1 ottobre 2026. È il verbale del cantiere «preparazione
infrastruttura hackathon RGB»: SOLO setup e prove, su signet, separato da
Barattolo. Lo studio che lo precede, coi perché delle scelte, è
`docs/STUDIO-HACKATHON-RGB-2026-10.md`; il regolamento (sezione F di
quello studio) dice che si giudica solo ciò che si costruisce durante
l'evento e che il pre-esistente va DICHIARATO: la sezione 5 di questo
file è quella dichiarazione, pronta da consegnare.

Decisione di Alan, che vale per tutto: versione di prova, su rete di
prova, mai in produzione finché non si decide altrimenti. Niente qui
tocca il VPS di Barattolo, il nodo Mostro o il relay.

## 1. Le macchine e gli accessi (senza segreti)

| Cosa | Dove | Come si entra |
|---|---|---|
| **VM «rgb-prova»** | LNVPS Dublino, `vm-2050.lnvps.cloud` (185.18.221.42), Debian 13, 2 vCPU / 4 GB / 63 GB NVMe, ~10 €/mese in sats | `ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud` (chiave del nodo, impronta ED25519 verificata il 1 ott) |
| **Il portatile della demo** | il PC di Andrea: Windows 11, WSL2 Ubuntu 26.04, RTX 4090 | il wallet utente vive nel WSL (`~/wdk-prova`), QVAC in Windows nativo (`C:\Users\Andrea\qvac-prova`) |
| **Il tunnel** | dal WSL verso la VM | `ssh -i ~/.ssh/lnvps -N -L 50001:127.0.0.1:50001 -L 3000:127.0.0.1:3000 debian@vm-2050.lnvps.cloud` (la chiave è copiata DENTRO il WSL a 600: su `/mnt/c` i permessi sono 777 e ssh la rifiuta) |

Sulla VM, in `/home/debian/rgb/`:

- `compose.yaml`: tre container, bitcoind 30.2 su signet (`txindex`,
  nessuna porta pubblicata: l'RPC resta nella rete di docker), electrs
  0.11.0 (indexer Electrum su **127.0.0.1**:50001) e `rgb-proxy-server`
  0.3.0 (su **127.0.0.1**:3000). Sono le stesse immagini con cui rgb-lib
  fa le sue prove (registro `hashbeam`). Docker scrive in iptables prima
  di ufw: una porta pubblicata su 0.0.0.0 sarebbe aperta al mondo, per
  questo ogni porta è legata a 127.0.0.1 e il portatile ci arriva solo
  dal tunnel. Il firewall (ufw) lascia entrare SOLO la 22.
- `.env` (0600): le credenziali RPC di bitcoind, generate a caso.
- `venv/`: Python con `rgb-lib==0.3.0b7` (la ruota pronta per Linux
  x86_64: zero toolchain Rust).
- `rgb.py`: il banco a comandi (copia in `deploy/rgb/rgb.py`).
- `dati/<wallet>/chiavi.json` (0600) e `dati/<wallet>/wallet/`: la frase
  segreta e lo STASH di rgb-lib. Due wallet: **barattolo** (impronta
  5853f1ef) e **to-the-mooon** (impronta 97a4d0ed).
- `backup/`: le fotografie `.rgb-backup` fatte da rgb-lib.
- Il backup notturno: `/usr/local/sbin/backup-rgb.sh` +
  `rgb-backup.timer` (03:30), archivi in `/var/backups/rgb` a
  `root:pull` 640, cifrati con la sola chiave PUBBLICA age della macchina
  (`age1kjhz9…deacdm`). La segreta sta sul PC
  (`C:\Users\Andrea\BarattoloBackup\rgb-prova.key`) e su Bitwarden: è la
  TERZA chiave age, e apre solo questi archivi. Il PC tira in pull
  (gamba `rgb/` di `pull.ps1`, utente `pull` sulla VM con chiave
  `rgb_backup_ed25519` vincolata a `internal-sftp -R`).

Segreti che NON stanno in questo file né nel repo: `.env`, i due
`chiavi.json`, la segreta age, le chiavi SSH, `seme.txt` del wallet
utente. Chi li vede in chat, li ruota.

## 2. Gli asset emessi (pubblici: sono i nomi, non chiavi)

| Ticker | Nome | Emittente (wallet) | Quantità | asset_id |
|---|---|---|---|---|
| **JAR** | Punti Barattolo | barattolo | 21.000.000, precisione 0 | `rgb:YWIEm~Ts-i9zB8Gt-wAWnJAg-YdGNPLI-X92ivqs-H_lxQNM` |
| **MOON** | Punti To The Mooon | to-the-mooon | 1.000.000, precisione 0 | `rgb:9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM` |

Perché questi nomi: «BRT» ricordava Bartolini e «CAFFE-LUCA» non passa
(il ticker NIA ammette SOLO maiuscole e cifre, da 1 a 8 caratteri:
niente trattini); il negozio di prova è To The Mooon. Un NIA non si
rigonfia: la quantità si decide all'emissione, e JAR ne ha ventun
milioni per non doverlo riemettere mai.

**La ricetta per emetterne un altro** (sulla VM, in `~/rgb`):

```bash
./venv/bin/python rgb.py nuovo <negozio>          # una volta: le chiavi
./venv/bin/python rgb.py indirizzo <negozio>      # l'indirizzo per il faucet
#   faucet: https://signet257.bublina.eu.org/ (o signetfaucet.com); aspetta un blocco
./venv/bin/python rgb.py utxo <negozio> 5         # 5 UTXO colorabili da 1000 sats; un blocco
./venv/bin/python rgb.py emetti <negozio> TICKER "Nome lungo" 1000000   # nessuna tx
./venv/bin/python rgb.py backup <negozio>         # subito dopo: da qui lo stash vale
```

L'emissione non fa transazioni: il genesis vive su un UTXO colorabile.
L'`asset_id` che stampa è il nome pubblico dell'asset e si può scrivere
ovunque (in Barattolo andrà in `impostazioni`, accanto a
`sponsor_slug`: non muove denaro).

## 3. La catena provata end-to-end (transazioni vere su signet)

Il wallet utente è **WDK di Tether col modulo RGB di Utexo**
(`@utexo/wdk-wallet-rgb` 2.0.3, su `@utexo/rgb-sdk` 1.0.3 e
`@utexo/rgb-lib` 0.3.0-beta.8), nel WSL del portatile:
`~/wdk-prova/punti.mjs` (copia in `deploy/rgb/punti.mjs`), con
`~/wdk-prova/utente/seme.txt` (0600) e lo stash in `utente/wallet/`.
Parla con electrs e col proxy della VM attraverso il tunnel.

Il giro fatto il 1 ottobre 2026:
(Gli id delle transazioni, qui e in CANTIERI, sono spezzati a metà con uno
spazio: la guardia dei segreti della CI prende ogni 64-hex per una chiave
privata. Si riuniscono per cercarli su mempool.space.)


1. **Assegnazione** (il negozio dà 100 MOON a un utente che non ha un
   sat): il wallet utente fa una fattura **witness** per «100 unità di
   qualunque asset» (`node punti.mjs fattura - 100 witness`); sulla VM
   il negozio manda (`rgb.py invia to-the-mooon <MOON> 100 '<fattura>'`)
   e deposita il consignment sul proxy; il wallet utente lo scarica, lo
   valida e fa ACK (`node punti.mjs aggiorna`); il negozio trasmette
   (`rgb.py aggiorna to-the-mooon`). Transazione
   `80a922b66b977d42995b34e993ffab4e c09988f08fdef83edc3d7c0da2d119c3`:
   due ingressi, un `OP_RETURN` da 32 byte (l'impegno RGB), l'uscita
   witness da 1000 sats all'utente, il resto, fee 511 sats —
   https://mempool.space/signet/tx/80a922b66b977d42… (id intero: le due metà qui sopra, unite)
2. **Il wallet li vede**: nel libro dell'utente compare MOON, con nome e
   ticker letti dal consignment, 100 unità «future» finché il blocco non
   arriva, poi settled.
3. **Sats all'utente** per poter spendere (fee e UTXO del resto): dal
   wallet barattolo, come un faucet (`rgb.py btc barattolo <indirizzo>
   30000`), tx `e34d42afe504a8ed22dcd6ab549dc2fa 195066af7ef91f7ca377a3b33b73f78f`.
4. **Riscatto** (40 punti tornano al negozio): l'utente crea i suoi UTXO
   colorabili (`node punti.mjs utxo 3`, una tx); il negozio fa una
   fattura **blind** per MOON (`rgb.py fattura to-the-mooon <MOON>`);
   l'utente manda (`node punti.mjs riscatta <MOON> 40 '<fattura>'`, anche
   con gli UTXO non ancora confermati: rgb-lib li accetta); il negozio
   valida e fa ACK (`rgb.py aggiorna to-the-mooon`, stato
   `WAITING_BROADCAST`); l'utente trasmette (`node punti.mjs aggiorna`).
   Transazione
   `26579fd80a2811545d1b715a696929d3 2e9cb50b2f6dacf47594ab93b4955d84`:
   un ingresso, l'`OP_RETURN` e il resto da 691 sats, fee 309 —
   https://mempool.space/signet/tx/26579fd80a281154… (id intero: le due metà qui sopra, unite)
   Al blocco dopo: utente 60 MOON, negozio 999.940.

Lezioni, da non ripagare a Torino:

- **La prima fattura è «qualunque asset»**: un wallet che non ha mai
  visto MOON non può chiedere «100 MOON» per nome
  (`AssetNotFound`); impara l'asset dal primo consignment. Dopo, le
  fatture possono essere per asset.
- **Witness per il primo contatto, blind dopo**: in witness l'uscita la
  paga chi manda (1000 sats), e l'utente parte da zero sats. Per
  spendere, l'utente deve avere sats suoi: glieli dà Barattolo.
- **Le fatture portano l'endpoint del proxy** (`endpoints=rpc://
  127.0.0.1:3000/json-rpc`): sul portatile è il tunnel, sulla VM è il
  container. Se un giorno il proxy sarà pubblico (Caddy, https), le
  fatture lo diranno da sole.
- **beta.7 (Python, RGB-Tools) e beta.8 (Node, Utexo) si capiscono**:
  la fattura di Utexo è stata letta da rgb-lib Python e il consignment
  nostro validato dal wallet Utexo. Era il rischio numero uno dello
  studio, ed è chiuso.
- **Il modulo WDK gira solo su Linux/macOS** (binario nativo linux-x64,
  linux-arm64, darwin-arm64): niente Windows, quindi WSL2; il binding si
  ricompila con node-gyp e vuole `build-essential`. Il pacchetto
  opzionale `@utexo/rgb-lib-linux-x64` non entra da solo con `npm
  install`: si installa a mano (`npm install
  @utexo/rgb-lib-linux-x64@0.3.0-beta.8`).
- **Il proxy in docker vuole il volume di 1000:1000**: l'immagine non ha
  la cartella, il volume nasce di root e il processo (utente `node`)
  muore in `EACCES`. La cura: `docker compose run --rm --user root
  --entrypoint sh proxy -c 'chown -R 1000:1000 /home/node/.rgb-proxy-server'`.
- **La seed da sola non basta**: lo stash (`wallet/`) è ciò che prova i
  propri asset; «never instantiate a wallet in multiple places» (rgb-lib).
  Ogni comando di `rgb.py` apre UN wallet e chiude; il backup delle
  03:30 lo apre da solo, quindi a quell'ora nessun altro processo.

## 4. QVAC sul portatile

In Windows nativo, non nel WSL. `@qvac/cli` 0.14.0 installato globale
(`npm i -g @qvac/cli`); `qvac doctor` verde (Node 24, Vulkan sulla 4090,
ffmpeg). Il progetto: `C:\Users\Andrea\qvac-prova` con `qvac.config.json`
(copia in `deploy/rgb/qvac.config.json`): un modello solo,
`qwen3-600m-inst-q4` (Qwen3 0.6B instruct, ~400 MB, scaricato alla
prima chiamata).

Il server: `qvac serve --openai --port 11434 --host 127.0.0.1` dalla
cartella del progetto. Risponde su `/v1/models` e `/v1/chat/completions`
con `response_format` a `json_schema`.

Il consigliere: `consiglio.py` (copia in `deploy/rgb/consiglio.py`).
Legge il saldo del wallet (il JSON di `punti.mjs saldo`), passa a QVAC
prezzo e punti, riceve `{usa_punti, sconto_sats, asset_id, motivo}` e
POI rifà il conto: il modello propone, la regola decide.

```
python consiglio.py 2000 saldo.json
```

| Prezzo | Tetto (20%) | Proposta | Controllo |
|---|---|---|---|
| 2000 sats | 400 | usa 100 MOON → 100 sats | ok |
| 300 sats | 60 | usa 60 MOON → 60 sats | ok |

La lezione: al primo giro il modello da 0,6 B ha sbagliato l'aritmetica
(1 punto → 200 sats) e il controllo l'ha bocciata. La cura è passargli
il conto già fatto (`massimo_usabile`) e lasciargli solo la scelta. Il
«motivo» che scrive è scarno («Usa massimo»): da provare Qwen3 1.7B
(`qvac configure`, interattivo, cerca «qwen3»), e in sede una pagina
locale che chiami 127.0.0.1:11434 (CORS: `--cors-origin
http://127.0.0.1:8080`, un'origine esatta).

## 5. Cosa dichiariamo all'arrivo (pre-esistente, NON da giudicare)

Da consegnare scritto il 17 mattina, com'è chiesto dal regolamento:

- Barattolo: il mercatino in sats con escrow Lightning, in produzione
  dal 10 ottobre, con XP, livelli e due sconti fedeltà (lo studio, §0).
- Una VM su signet con bitcoind, electrs, proxy RGB, rgb-lib Python e
  il banco `rgb.py`.
- Due asset NIA emessi il 1 ott: JAR e MOON (asset_id sopra).
- Un wallet utente WDK+RGB (`punti.mjs`) che ha ricevuto 100 MOON e li
  ha riscattati (tx sopra).
- QVAC in locale con `consiglio.py` e il JSON a schema.
- Nessuna rotta, nessun modulo, nessuna UI in Barattolo: zero righe di
  integrazione. Quelle si scrivono a Torino, in commit datati.

## 6. Come si riavvia tutto (il giorno prima e il giorno stesso)

Sulla VM:

```bash
cd ~/rgb && docker compose up -d && docker compose ps
docker compose exec bitcoind su -c 'bitcoin-cli -signet getblockchaininfo' blits | grep -E '"(blocks|headers|initialblockdownload)"'
./venv/bin/python rgb.py saldo to-the-mooon      # electrs in pari e asset al loro posto
./venv/bin/python rgb.py backup to-the-mooon      # prima di ogni giorno di demo
```

Sul portatile, nel WSL (finestra 1, resta aperta):

```bash
ssh -i ~/.ssh/lnvps -N -L 50001:127.0.0.1:50001 -L 3000:127.0.0.1:3000 debian@vm-2050.lnvps.cloud
```

Nel WSL (finestra 2):

```bash
cd ~/wdk-prova && source ~/.nvm/nvm.sh && node punti.mjs saldo
```

In Windows (PowerShell):

```powershell
cd C:\Users\Andrea\qvac-prova; qvac serve --openai --port 11434 --host 127.0.0.1
```

Se la VM non risponde: il wallet utente funziona anche con gli endpoint
pubblici di Utexo/Iris (`RGB_INDEXER=tcp://46.224.75.237:50001`,
`RGB_PROXY=rpcs://proxy.iriswallet.com/0.2/json-rpc`), ma le fatture
fatte col tunnel portano l'endpoint 127.0.0.1 e vanno rifatte. Se il
portatile muore: la VM ha tutto (`rgb.py` fa anche la parte utente con
un terzo wallet), e il backup del PC riapre lo stash.

Ripristino della VM da zero: `deploy/rgb/` ha compose, script e unit;
`.env` e `chiavi.json` escono dall'archivio age (`age -d -i
rgb-prova.key`); lo stash si rimette con `rgb.py ripristina <wallet>
<file.rgb-backup>` in una cartella VUOTA (sopra uno stash vivo si
perdono asset). Catena e indice si riscaricano in un'ora.

## 7. La scaletta di Torino (cosa si SCRIVE lì, in ordine)

1. **Sabato mattina** — la leva `RGB_ATTIVO` (già su main spenta dal
   11-12 ott) e la rotta `/api/rgb/punti/<utente>`: legge il saldo del
   wallet utente (prima tappa: lato server, un wallet per utente in una
   cartella per utente, dichiarato «custodial per la demo»; la tappa
   browser solo se il modulo Darkhorse regge).
2. **Sabato pomeriggio** — l'assegnazione: dopo un ordine confermato
   (`released`), il negozio manda i punti (il calco è `invia` di
   `rgb.py`: fattura dall'utente, invio, refresh). Un punto per euro,
   come `XP_PER_EURO`.
3. **Sabato sera** — la UI: il saldo punti nella scheda Ordini o nel
   Profilo, e la riga «usa X punti» nel conto.
4. **Domenica mattina** — QVAC nel conto: la pagina chiama 127.0.0.1:
   11434 (o il server lo fa per lei), mostra la proposta, l'utente
   approva, lo sconto in sats si applica (il calco è `_fedelta_sconto`).
5. **Domenica pomeriggio** — il riscatto (punti al negozio) e il pitch:
   le tx di signet aperte su mempool.space, il wallet WDK che mostra i
   punti, QVAC che propone. Lo swap P2P: una slide.

Prima del 17, da fare FUORI dal repo: la pagina locale che chiama QVAC
(CORS), e il modulo browser Darkhorse provato in Chrome su signet (due
ore, poi si decide).

## 7-bis. L'opzione di Alan: il wallet WDK che parla NWC (solo studio, 1 ott)

L'idea: il wallet WDK sul portatile espone NIP-47 (Nostr Wallet
Connect), così Barattolo, che è GIÀ un client NWC (nel browser usa
`get_info`, `pay_invoice`, `make_invoice`, nip44 e nip04; la connessione
non tocca mai il server), lo usa come wallet self-custodial dell'utente:
paga gli ordini da lì e, con un'estensione nostra, legge i punti RGB e
propone il riscatto.

**Cosa esiste già (verificato sul registro npm il 1 ott):**

- Nel WDK NON c'è un servizio NWC. I moduli Lightning del WDK sono due:
  `@tetherto/wdk-wallet-spark` 1.0.0-beta.28 (Lightning attraverso Spark,
  la L2 di Lightspark con operatori: reti `MAINNET`, `TESTNET`,
  `REGTEST`, **niente signet**; non è un nodo tuo) e
  `@utexo/wdk-rgb-lightning` 0.1.0-beta.15 (un LDK + rgb-lib dentro il
  processo: README su **regtest**, vuole bitcoind RPC, indexer, proxy e
  canali aperti da te, LSP opzionale).
- La parte NIP-47 lato wallet è pronta in `@getalby/sdk` 8.0.3:
  `NWCWalletService` (`publishWalletServiceInfoEvent` con la lista dei
  metodi, `subscribe` con un handler per metodo, `publishNotification`,
  nip44 e nip04 insieme). È il pezzo che mancava, e lo fa già Alby Hub.
- Il relay: NWC viaggia su eventi cifrati (kind 23194/23195) sul relay
  scritto nella connection string. Per la demo un relay LOCALE in docker
  sul portatile (`ws://127.0.0.1:7777`, strfry come il nostro), così
  nessun relay vero e niente pubblicato: in collaudo la CSP di Barattolo
  ammette `ws:` in `connect-src`.

**Cosa andrebbe scritto:** un servizio Node (`nwc-wdk.mjs`, 150-250
righe) che apre il wallet WDK, stampa la connection string
`nostr+walletconnect://<pubkey>?relay=ws://127.0.0.1:7777&secret=…` da
incollare nel Profilo di Barattolo, risponde a `get_info`,
`get_balance`, `make_invoice`, `pay_invoice` col modulo Lightning scelto,
e aggiunge i metodi NOSTRI `rgb_list_assets` (il saldo MOON/JAR) e
`rgb_make_invoice` (la fattura blind per il riscatto): NIP-47 non vieta
metodi fuori lista, il client li scopre da `get_info.methods`. Lato
Barattolo: una decina di righe nel client NWC che, se il wallet dichiara
`rgb_list_assets`, mostra i punti e propone il riscatto — da scrivere a
Torino.

**Il Lightning del WDK su signet basta per la demo? No, oggi.** Spark
non ha signet; `wdk-rgb-lightning` è regtest con canali da aprire verso
un secondo nodo tuo; l'LNbits di Barattolo in collaudo è di cartone e
in produzione è mainnet. Pagare un ordine VERO dal wallet WDK vorrebbe
una regtest sul portatile con due nodi (LND per LNbits e l'LDK
dell'utente), 1-2 giorni solo di quello, e fragile il giorno del pitch.
La parte RGB via NWC (saldo e riscatto) invece non ha bisogno di
Lightning: funziona con `punti.mjs` e signet come sono oggi.

**Tempo:** servizio NWC con relay locale e metodi `rgb_*`: 6-10 ore
(Alby fa il grosso); `pay_invoice` vero su regtest: altre 12-20 ore;
l'aggancio in Barattolo: 2-4 ore, a Torino.

**Prima o a Torino:** la BASE prima (servizio, relay locale, metodi
`rgb_*`, fuori dal repo e dichiarata), perché è infrastruttura come la
VM; l'aggancio nel client NWC di Barattolo e il riscatto nel conto a
Torino, in commit datati. Il pagamento self-custodial via WDK resta una
slide, come lo swap. Perché vale: è il bonus WDK più solido che abbiamo
(il WDK diventa IL wallet dell'utente, non un attrezzo di prova) e
toglie di mezzo il «custodial per la demo» per i punti. Decide Alan.

## 8. Le cose incerte, da chiedere ai mentor (13 ott e sabato mattina)

- Lo stash lato server per utente è accettabile come demo? Qual è la
  loro strada per lo stash nel browser/telefono (VSS? il modulo
  Darkhorse? `rgb-sdk-web`?).
- Gli endpoint pubblici di Utexo (`46.224.75.237:50001`, il proxy)
  reggono il 17-18 e si possono usare in sede? Noi abbiamo i nostri
  sulla VM, ma vorremmo saperlo.
- `min_confirmations = 0` è ammesso per mostrare un trasferimento in
  tempo reale sul palco, o si aspetta il blocco (dieci minuti su
  signet)? Noi prepariamo le tx PRIMA e le mostriamo confermate.
- Interoperabilità beta.7/beta.8: a noi ha funzionato; c'è una versione
  che raccomandano per la settimana dell'evento?
- La fattura «qualunque asset» per il primo contatto è la via giusta, o
  c'è un modo per far conoscere l'asset al wallet prima (un consignment
  del solo genesis)?
- Ticker e nomi: il ticker a 8 maiuscole è un limite dello schema NIA o
  di rgb-lib? Il nome ammette accenti (noi abbiamo evitato «Caffè»)?
- La rete del giudizio: signet va bene o vogliono regtest in sede? E il
  loro faucet, se c'è.
- WDK in browser con RGB: lo considerano «WDK bonus» anche se il wallet
  gira in Node sul portatile?

## 9. Verbale: strade scartate e non provato

- Hetzner per la VM: scartato, l'account è quello della produzione e
  Hetzner vieta i nodi per iscritto. LNVPS come il nodo e il relay.
- Tutto sul portatile senza VM: tenuto come riserva, non scelto (un solo
  punto di guasto il giorno del pitch).
- RGB Lightning Node al posto di rgb-lib: scartato (early alpha, senza
  release, Lightning spenta su mainnet dal fork Utexo). Resta la riserva
  se i mentor lo chiedono.
- bitcoind nostro invece dei soli endpoint pubblici: scelto, per non
  dipendere da un terzo non verificato il giorno del pitch (60 GB
  bastano: la catena signet pesa pochi GB).
- Non provato: Qwen3 1.7B; il modulo browser Darkhorse; `rgb-sdk-web`;
  il proxy pubblico dietro Caddy; un terzo wallet utente sulla VM; il
  ripristino COMPLETO della VM da zero (fatto solo il drill dell'archivio
  e il `ripristina` dello stash su una copia, sul PC).

Nota a margine, fuori cantiere ma scoperta qui: il pull notturno del
backup del NODO falliva dal 7 settembre («permission denied» su
`/var/backups/nodo`: lo script lo richiudeva a 700 ogni notte). Curato
da Andrea il 1 ott (riga 19 di `backup-nodo.sh`, `-g pull -m 750`): il
verbale sta in `docs/NODO-MOSTRO.md`.
