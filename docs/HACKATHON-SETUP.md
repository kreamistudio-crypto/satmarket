# Hackathon RGB di Torino (17-18 ott 2026): l'infrastruttura preparata prima

Stato al 1 ottobre 2026, **aggiornato il 7 ottobre** con le idee di Alan,
**e l'8** (cantiere «chiusura della preparazione»: la leva su main, il
repo pubblico `fidelity-points`, la scaletta con la ✓ al sabato),
(la demo sui punti fedeltà, **NWC-RGB** — l'estensione NIP-47 per gli
asset RGB —, l'emittente legato a un'identità Nostr: il perché e il
disegno stanno nella parte seconda dello studio; qui c'è COSA si fa e
quando) e **la sera del 7 con le sue quattro decisioni** (studio, parte
seconda, G: il repo pubblico, il nome NWC-RGB, il NIP-05 anche per gli
utenti al livello 2, il centro della demo sul negozio che emette e non
sull'AI; il nome «Cassiere» sparisce — qui dai testi, e dagli
identificatori tecnici l'8 ott, cantiere «chiusura della
preparazione»). È il
verbale del cantiere «preparazione infrastruttura hackathon RGB»: SOLO
setup e prove, su signet, separato da Barattolo. Lo studio che lo precede, coi perché delle scelte, è
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
| **USDB** | `Dollari_di_prova_Barattolo` | `usdb` (impronta 8276ad20, wallet NUOVO dell'8 ott: l'emittente dei dollari non è il mercante né il negozio) | 1.000.000,00 cioè 100.000.000 unità, **precisione 2** («2 for USD», docs.rgb.info) | `rgb:H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A` (emesso l'8 ott 2026, backup `usdb-20261008-0846`) |

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

`rgb.py emetti` ha già l'argomento opzionale `[precisione]` (default 0,
giusto per i punti): per USDB si è passato `2` in coda — la nota del 7
ott che lo dava da aggiungere era sbagliata. **Il nome di USDB ha gli
underscore** perché da PowerShell le virgolette interne di `ssh '… "Dollari
di prova Barattolo" …'` vengono mangiate prima di arrivare alla VM
(`emetti() takes from 4 to 5 positional arguments but 8 were given`:
nessuna emissione partita, rifatta senza spazi); un NIA non si rinomina,
e il nome che l'utente vede lo decide l'annuncio Nostr (studio, parte
seconda, B.1), non il genesis. Il campo `issuer` del genesis resta
`ssi:anonymous`: rgb-lib non lo espone (studio, A.1). I sats del wallet
`usdb` sono arrivati da `to-the-mooon` (`rgb.py btc`, 50.000), non dal
faucet.

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
(**il 7 ott la CLI è alla 0.15 e l'SDK alla 0.21**: prima del 17 si
aggiorna, vedi la lista in sezione 10)
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

**Aggiornamento del 7 ott, letto sulla docs della CLI** (le cose che
cambiano la pagina dell'aiutante, quello che la mattina si chiamava
«Cassiere»: l'alias `cassiere` qui sotto è diventato `consigliami`
l'8 ott, G.4):

- Il modello: Qwen3 1.7B è `QWEN3_1_7B_INST_Q4` (~1 GB), ed è quello che
  la docs usa in TUTTI gli esempi con JSON a schema. In
  `qvac.config.json` ogni voce di `serve.models` è un **alias** che fa da
  campo `model` nelle richieste («requests for unlisted models return
  404»): la nostra si chiamava `cassiere` (oggi `consigliami`), con `"config": {"ctx_size":
  8192}` (il default è 1.024 token: troppo pochi per saldo + regole +
  schema).
- **CORS**: spento finché non si dà un'origine ESATTA con
  `--cors-origin http://127.0.0.1:8080` (ripetibile); `*` non è ammesso;
  `--cors` da solo NON accende niente, controlla solo che un'origine
  esista. La pagina della demo vive su `http://127.0.0.1:8080` (il
  collaudo), quindi niente mixed content.
- **Lo structured output e i `tools` non si combinano** (400
  `invalid_response_format`): l'aiutante usa `response_format` a
  `json_schema` e il conto già fatto, senza tool — la scelta del 1 ott
  era giusta anche per questo.
- **Qwen3 pensa**: con `max_tokens` stretto il `content` resta vuoto;
  si manda `"reasoning_budget": false` nella richiesta.
- `qvac serve openai` è un alias deprecato: si scrive `qvac serve
  --openai`.
- `GET /v1/models/catalog?role=chat` elenca i modelli con peso e
  quantizzazione: utile al Q&A per dire «ecco cosa gira».

**Fatto l'8 ott.** CLI alla 0.15.0; in `qvac.config.json` (copia in
`deploy/rgb/`) l'alias **`consigliami`** → `QWEN3_1_7B_INST_Q4` con
`ctx_size 8192`, scaricato alla prima chiamata (1,06 GB in
`~/.qvac/models`); il 0.6B resta con l'alias di prima. La pagina locale
`C:\Users\Andrea\qvac-prova\consigliami-prova.html` (FUORI dal repo:
titolo «Fidelity Points», bottone «Consigliami») fa la catena intera —
numeri già calcolati, `response_format` a `json_schema`,
`reasoning_budget: false`, il controllo del programma, il fumetto con
«Approva» — ed è stata provata nel Browser pane servita da `python -m
http.server 8081` con `qvac serve --openai --cors-origin
http://127.0.0.1:8081`: il preflight dall'origine dichiarata torna con
`access-control-allow-origin`, da un'altra origine no. Tempi sulla 4090:
0.6B 20,8 s al primo giro (7,2 s al primo token, il modello da caricare)
e 824 ms al secondo; **1.7B 629 ms** (252 token/s) a modello caldo, 23 s
la prima chiamata. Nella demo l'origine sarà `http://127.0.0.1:8080`.
⚠️ Il 1.7B scrive i numeri giusti nel JSON ma SBAGLIA quelli nella
frase del «motivo» («hai risparmiato 4800 sats» per 60): i numeri li
scrive il programma e al modello si chiede una frase senza cifre — da
fare nel «Consigliami» vero, a Torino.

## 5. Cosa dichiariamo all'arrivo (pre-esistente, NON da giudicare)

Da consegnare scritto il 17 mattina, com'è chiesto dal regolamento:

- Barattolo: il mercatino in sats con deposito di garanzia Lightning
  (custodial, LNbits), il P2P non custodial su Mostro, in produzione dal
  10 ottobre, con XP, livelli, due sconti fedeltà, un client NWC nel
  browser (`clientNwc`), le foto su Blossom (lo studio, §0 e parte
  seconda).
- Una VM su signet con bitcoind, electrs, proxy RGB, rgb-lib Python, il
  banco `rgb.py` e la sua faccia HTTP `rgb_http.py` sul loopback.
- Tre asset NIA emessi prima: JAR e MOON (1 ott), USDB (8 ott,
  asset_id in §2).
- Un wallet utente WDK+RGB (`punti.mjs`) con 60 MOON e 500,00 USDB
  (50.000 unità, tx `ba3523ca5b410c3e71b2a3f04b9662cd
  c97da6c0a71acf4e791aaf70978c6b47` nel blocco 325472 dell'8 ott, id
  spezzato a metà per la guardia dei segreti), che ha già ricevuto e
  riscattato MOON (tx sopra); il servizio NWC «base» `nwc-wdk.mjs` che lo
  espone (evento info, `get_info`, `get_balance`: **nessun metodo
  `rgb_*`**, quelli sono lavoro del weekend — chiesti oggi, rispondono
  `NOT_IMPLEMENTED`).
- Due identità Nostr di prova (gli «emittenti» di USDB e di MOON,
  `identita.mjs`) con kind 0 e NIP-05 sul relay locale (`nak serve`
  sul portatile). **Nessun relay pubblico toccato.** I due annunci di
  asset (MOON e USDB, nella forma della bozza `spec/NIP-RGB-ASSETS.md`,
  kind segnaposto) si firmano con queste identità e si pubblicano sul
  relay locale il **16 ott**, dichiarati: esistono come eventi, nessun
  codice di Barattolo li legge prima del 17 (la cura di D.3 punto 0,
  decisa l'8 ott: la riga «Emesso da ✓» si costruisce il sabato).
- QVAC in locale (Qwen3 1.7B, alias `consigliami`) con `consiglio.py` e
  la pagina locale `consigliami-prova.html` FUORI dal repo che lo chiama
  con lo schema: propone, non paga.
- Il disegno: la parte seconda dello studio (campi, nomi dei metodi,
  schermi), scritta il 7 ott; le due bozze in inglese
  `docs/spec/NIP-RGB-ASSETS.md` e `docs/spec/NWC-RGB.md` nel repo
  privato (scritte l'8 per `fidelity-points`, portate qui la sera), dichiarate come disegno: nessuna issue aperta, nessuna
  PR, nessuna implementazione.
- **Il repo `fidelity-points`** (§10, prima riga): privato, MINIMO
  per scelta di Alan (8 ott sera), solo per trasparenza: il suo README
  dice soltanto «prima: una VM con un nodo Bitcoin signet e un server
  dedicato» e «durante: tutto il resto, nei commit del 17 e 18».
  Questa dichiarazione intera NON sta lì: sta qui, in §10 e in
  `deploy/rgb/`.
- Nessuna rotta, nessun modulo, nessuna UI in Barattolo: zero righe di
  integrazione (solo la leva `RGB_ATTIVO` spenta e la rotta statica
  `/.well-known/nostr.json`, su main dall'8 ott — un cancello chiuso e
  una rotta che risponde vuota finché `NIP05_NOMI` non entra nel
  config del VPS). Quelle si scrivono a Torino, in commit datati.

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

Le tre cose nuove dell'8 ott, sul portatile e sulla VM:

```bash
setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown      # WSL: il relay locale (muore col WSL)
cd ~/wdk-prova && source ~/.nvm/nvm.sh && setsid nohup node nwc-wdk.mjs serve > nwc/serve.log 2>&1 < /dev/null & disown   # WSL: il servizio NWC (tiene aperto il wallet: niente punti.mjs intanto)
```

⚠️ `setsid … & disown`, non il solo `nohup`: lanciato da una chiamata
`wsl.exe -e bash -lc` il servizio NWC è morto quando la chiamata è
finita, e Barattolo ha bussato a vuoto (8 ott, «Busso qualche
secondo… niente conferma»). Per fermarli: `pkill -f "[n]wc-wdk.mjs
serve"` — con le parentesi, o `pkill` uccide la shell che lo lancia.

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && nohup ./venv/bin/python rgb_http.py > rgb_http.log 2>&1 &'   # VM: la faccia HTTP del mercante
```

Il tunnel ha la terza gamba `-L 8787:127.0.0.1:8787`. `rgb_http.py` apre
il wallet `barattolo` a ogni richiesta: alle 03:30 il backup apre lo
stesso wallet, quindi di notte si ferma (`pkill -f rgb_http.py` sulla
VM) e si riaccende la mattina della demo.

Ripristino della VM da zero: `deploy/rgb/` ha compose, script e unit;
`.env` e `chiavi.json` escono dall'archivio age (`age -d -i
rgb-prova.key`); lo stash si rimette con `rgb.py ripristina <wallet>
<file.rgb-backup>` in una cartella VUOTA (sopra uno stash vivo si
perdono asset). Catena e indice si riscaricano in un'ora.

## 7. La scaletta di Torino (cosa si SCRIVE lì, in ordine) — rifatta il 7 ott

Il tema è **«Loyalty / punti fedeltà»** (Alan, 7 ott sera): ogni
esercente emette i propri punti come token RGB, autenticati dal suo
NIP-05, e QVAC aiuta a spenderli al posto dei satoshi — l'AI è un
aiuto, il protagonista è il negozio che emette e l'identità che lo
certifica. Il progetto si chiama **«Fidelity Points»** e l'aiutante
— il bottone e il fumetto — **«Consigliami»** (decisi da Andrea l'8
ott, studio, parte seconda, G.4); nel codice li applica il prossimo
cantiere. Priorità di
COSTRUZIONE, in quest'ordine e senza discussione il sabato: **core**
(checkout in USDB + l'aiutante che consiglia + wallet WDK che paga via
NWC-RGB), poi il **NIP minimo** con l'emittente verificato nella
schermata, poi **budget e salvadanaio** se avanza, la roadmap solo
slide. JAR resta fuori. La tabella ora per ora e le slide stanno nello
studio, parte seconda, D.2; qui l'ordine dei pezzi:

1. **Sabato mattina** — in parallelo: nel wallet (`nwc-wdk.mjs`) i
   quattro metodi `rgb_list_assets`, `rgb_make_invoice`,
   `rgb_pay_invoice` (con conferma dell'utente), `rgb_lookup_transfer`
   sopra `punti.mjs`; nel server, dietro `RGB_ATTIVO`,
   `/api/rgb/fattura` (la fattura blind in USDB del wallet `barattolo`,
   via `rgb_http.py`, importo al cambio) e `/api/rgb/stato`.
2. **Sabato primo pomeriggio** — nel foglio del pagamento «oppure N
   USDB» e «Paga in USDB» → `rgb_pay_invoice` dal `clientNwc` → «in
   arrivo» → `rgb.py aggiorna barattolo` → «Pagato in USDB». **Il primo
   pagamento vero su signet entro le 16:30.** Lessico: «pagamento
   diretto, senza deposito di garanzia» (regola 9).
3. **Sabato pomeriggio, subito dopo il checkout** — «Emesso da … ✓»,
   **il centro del racconto**, spostato qui dalla domenica mattina l'8
   ott (la cura di D.3 punto 0): i due annunci di MOON e USDB stanno
   GIÀ sul relay locale, firmati dalle identità di prova il venerdì 16
   e dichiarati (§10); a Torino si scrive solo la lettura in Barattolo
   per `#d`, la verifica NIP-05 lato server con `url_api_ammesso`
   (niente redirect, cache di 24 ore) e la riga nella card dell'asset,
   accanto a «⚠️ Emittente sconosciuto». Alle 18 del sabato la ✓ c'è:
   se la domenica va storta, la demo è comunque quella decisa il 7 sera.
4. **Sabato tardo pomeriggio** — «Consigliami»: la pagina
   chiama `127.0.0.1:11434` con lo schema, il fumetto col consiglio,
   «Approva» fa il passo 2 da solo. Se CORS morde, la chiamata la fa il
   server e si dichiara.
5. **Sabato sera** — MOON come bonus dopo il pagamento (l'assegnazione
   del 1 ott agganciata al «Pagato»), la card dell'asset completa
   (emittente, ticker, saldo), il giro intero due volte; `git
   format-patch` dei commit del giorno in `barattolo-patches/` del repo
   pubblico.
6. **Domenica mattina** — i due testi `spec/NIP-RGB-ASSETS.md` e
   `spec/NWC-RGB.md` del repo pubblico rifiniti con quel che
   l'implementazione del sabato ha insegnato, e la issue nel repo `nwc`
   aperta entro mezzogiorno; gli errori visibili («wallet non
   collegato», «proxy irraggiungibile», «conferma in arrivo»: «UX:
   error handling» è un criterio); il giro intero una terza volta col
   portatile sull'hotspot, non sulla rete di casa.
7. **Domenica mezzogiorno** — salvadanaio e budget se avanza, e basta.
   Tx del pitch confermate entro le 14:00, niente codice dopo; la sera
   `git format-patch` anche dei commit della domenica.

Lo stato dell'ordine pagato in USDB (dopo l'ACK o dopo il blocco) è una
decisione del sabato, scritta nel commit: gli stati della regola 4 non
cambiano.

**Cosa si RACCONTA, in ordine** (non è l'ordine in cui si costruisce,
ed è voluto: studio, parte seconda, G.4 e D.2): 1) chi siamo, 30
secondi; 2) il problema — i punti oggi sono una riga nel database del
negozio, e un token può chiamarsi come vuole; 3) il negozio che emette:
MOON su RGB, un punto per euro, firmato dall'identità Nostr di To The
Mooon verificata via NIP-05 — la card «Emesso da … ✓» accanto
all'emittente sconosciuto in grigio; 4) il cliente e il suo wallet WDK
che parla NWC-RGB, e la dichiarazione di venerdì; 5) dal vivo il
pagamento: l'aiutante consiglia, il cliente approva, il wallet
conferma, la tx su signet, il bonus dopo — l'AI entra qui; 6)
l'identità per tutti (il NIP-05 gratuito al livello 2) e la roadmap;
7) cosa resta. Il rischio che il centro del racconto fosse l'ultimo
pezzo costruito (studio, D.3 punto 0) è CHIUSO l'8 ott: la ✓ si
costruisce il sabato pomeriggio, subito dopo il checkout, sopra due
annunci che stanno sul relay locale dal venerdì.

## 7-bis. Il wallet WDK che parla NWC: l'opzione di Alan, DECISA il 7 ott

(Studio del 1 ott, confermato il 7: è la strada. L'estensione si chiama
**NWC-RGB**, «un NWC su WDK» (Alan, 7 ott sera); i quattro metodi, le
notifiche e gli errori nella forma da bozza stanno nello studio, parte
seconda, B.2, e in inglese nel repo pubblico come `spec/NWC-RGB.md`
dall'8-9 ott; la BASE del servizio si fa prima del 17 e si dichiara, i
metodi `rgb_*` a Torino.)

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
toglie di mezzo il «custodial per la demo» per i punti. **Deciso: si fa**
(Alan, 7 ott). Due precisazioni dopo la rilettura del NIP-47 del 7 ott:
il nucleo ha cinque metodi e un tag `extensions`, e i metodi aggiunti
«SHOULD also appear in content» dell'evento info — `metodiNwc` di
Barattolo li legge già da `get_info.methods`; e i nomi e le forme
ricalcano WebRGB di KaleidoSwap (`assetId`, `invoice`, `txid`,
`transferId`, gli stati di rgb-lib), così la stessa estensione la
implementa in un pomeriggio chi ha già il provider `window.rgb`.

## 8. Le cose incerte, da chiedere ai mentor (13 ott e sabato mattina)

La lista completa, con l'ordine e lo spazio per le risposte, è nello
studio, parte seconda, E (undici domande). La pagina della gara NON
nomina nessun Q&A: la data del 13 viene dalla mail di conferma, e si
verifica lì. In sintesi: 1) il campo `issuer` del genesis e i piani di
rgb-lib; 2) «WebRGB sopra NWC» e cos'è `@utexo/webrgb-walletconnect`,
Rate come wallet; 3) il checkout in asset on-chain conta per «Payments
and checkout»; 4) un USDT di prova su signet da Tether/Utexo, o il
nostro USDB; 5) il disegno del NIP fatto prima e il servizio NWC base:
dichiarabili; 6) signet e `min_confirmations = 0`; 7) «on device» con
`qvac serve` e la UI nella pagina, Qwen3 1.7B o Llama 1B; 8) il bonus
WDK col modulo RGB su signet (la docs dice `mainnet|testnet|regtest`);
9) gli endpoint Utexo, la fattura «qualunque asset» o il consignment
nell'annuncio, beta.7/beta.8; 10) consegna, licenza, pitch, CypherTank;
11) il grant dell'RGB Protocol Association, se esiste.

Restano dalla prima lista, ancora aperte: lo stash lato
browser/telefono (VSS, Darkhorse, `rgb-sdk-web`); ticker e nomi con
accenti; la rete del giudizio e un faucet loro.

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
- Provato l'8 ott, di quel che il 7 era da provare: l'emissione a
  precisione 2 (USDB); la CLI 0.15 con `--cors-origin`;
  `reasoning_budget: false`; Qwen3 1.7B. `NWCWalletService` di
  `@getalby/sdk` NON si è provato e non si userà: ha gli handler
  tipizzati (`getInfo`, `payInvoice`…) e un metodo fuori lista non ci
  passa — `nwc-wdk.mjs` è scritto a mano con nostr-tools (2.25) e il
  metodo sconosciuto risponde `NOT_IMPLEMENTED` come vuole il NIP.
  GitHub Pages è scartato (§11). Resta non provato: il modulo WDK RGB
  su signet contro la docs che dice `mainnet|testnet|regtest`
  (funziona, da chiedere il 13).
- **Lezioni dell'8 ott**, da non ripagare: 1) da PowerShell le
  virgolette doppie DENTRO un argomento di `ssh '…'` spariscono prima
  della VM — nomi senza spazi, o le virgolette singole raddoppiate
  (`''…''`) per far arrivare intera una fattura con `&` dentro;
  2) `getPublicKey` di nostr-tools v2 torna GIÀ una stringa hex: un
  `hex()` sopra la raddoppia a 128 caratteri e nip44 esplode con «bad
  point: got length 65» (curato in `nwc-wdk.mjs`); 3) `nak event` da
  `wsl.exe` stampa muto: il relay si prova con nostr-tools;
  4) `refreshWallet()` del modulo WDK torna `undefined` anche quando ha
  fatto l'ACK: lo stato si legge da `listTransfers(asset_id)`, e senza
  asset_id la lista è vuota; 5) **il wallet mercante `barattolo` non
  conosce USDB**: `rgb_http.py /fattura` con l'`asset_id` di USDB dice
  «rgb-lib dice: asset_id=…» (AssetNotFound), la fattura «qualunque
  asset» passa — prima del 17 gli si manda un USDB (riga in §10), o il
  checkout di Torino fa fatture «qualunque asset» e controlla l'asset
  al refresh; 6) il 1.7B sbaglia i numeri nella frase, non nel JSON
  (§4).
- Scartato il 7 ott: emettere USDB con `issuer = nostr:<pubkey>` dalla
  CLI `rgb` di rgb-protocol o con una patch a rgb-lib PRIMA del 17 (il
  campo c'è, ma sono 4-8 ore e un attrezzo nuovo a dieci giorni
  dall'evento: si dice, con la issue a RGB-Tools, e si fa dopo se il
  cantiere vive). JAR fuori dalla demo (decisione di Alan).

## 10. Prima del 17: la lista (7 ott, aggiornata l'8), tutto dichiarato

Infrastruttura, lecita dal regolamento; niente al VPS prima del 10,
niente al nodo mai. Le stime e i perché nello studio, parte seconda, D.1.

| Quando | Cosa | Fatto |
|---|---|---|
| 8 ott, per primo | **Il repo `fidelity-points`** sotto `kreamistudio-crypto`, Alan collaboratore, PRIVATO, commit firmati. **MINIMO per scelta di Alan (8 ott sera)**: esiste solo per trasparenza. Dentro: README corto in inglese (il nome «Fidelity Points», estensione di Barattolo per l'hackathon «Agentic Dollars on Bitcoin», Torino 17-18 ott, il team Andrea e Alan; «prima dell'hackathon» SOLO una VM con un nodo Bitcoin signet e un server dedicato; «durante» tutto il resto, dichiarato nei commit del 17 e 18), LICENSE MIT, `.gitignore`. Niente spec, niente descrizione dell'idea, niente roadmap, niente codice. Le due bozze stanno qui in `docs/spec/`; **l'inventario vero dell'infrastruttura resta in `deploy/rgb/` e in questa sezione** (e in §5). Il disegno di G.1 dello studio è superato | ☑ 8 ott: la cartella `GitHub\fidelity-points` preparata dal cantiere «chiusura della preparazione» (README con la dichiarazione di §5 in inglese, `rgb/` senza la chiave age né i percorsi della VM, le due bozze, LICENSE MIT, `.gitignore`; le tre regole dello scanner dei segreti passate: zero), repo creato e pushato da Andrea con `gh` lo stesso giorno (primo commit 1e6fa80, Alan invitato; il comando nel verbale del cantiere, CANTIERI). ☑ 8 ott sera, cantiere «fidelity-points minimo»: `rgb/` tolta (06422bf), poi la linea di Alan — README corto e `spec/` tolta (af445f7), le bozze portate in `docs/spec/` (f2c0b7d). La storia dei primi commit resta com'è (decisione di Andrea: niente riscritture); visibilità PRIVATA, non toccata |
| 8-9 ott | `rgb.py emetti` con la precisione come argomento | ☑ c'era già (`[precisione]`, righe 18 e 152 di rgb.py): la nota del 7 ott era sbagliata |
| 8-9 ott | Sulla VM: `rgb.py nuovo usdb`, sats da `to-the-mooon` (niente faucet), `utxo usdb 5`, `emetti usdb USDB Dollari_di_prova_Barattolo 100000000 2`, `backup usdb`; l'asset_id in §2 | ☑ 8 ott, comandi eseguiti da Andrea uno alla volta; 4 UTXO colorabili liberi e 44.347 sats restano al wallet `usdb` |
| 8-9 ott | 500 USDB (50.000 unità) al wallet utente: fattura «qualunque asset» BLIND (`node punti.mjs fattura - 50000`: il wallet aveva già 3 UTXO colorabili, niente witness), `rgb.py invia usdb …`, i due `aggiorna`; un blocco | ☑ 8 ott, blocco 325472: utente 50.000 settled e spendibili; il wallet utente conosce USDB (precisione 2, 100.000.000 emessi) |
| 8-9 ott | UTXO colorabili al wallet `barattolo` (riceverà i pagamenti) | ☑ non serve: ne ha 4 liberi (ronda dell'8 ott) |
| 8 ott | **1,00 USDB al wallet mercante `barattolo`** (100 unità da `usdb`), perché conosca l'asset prima di fare fatture PER asset (lezione 5 di §9): fattura «qualunque asset» da `rgb_http.py /fattura {"quantita": 100}`, `rgb.py invia usdb …` (Andrea), ACK da `rgb_http.py /aggiorna` (dal tunnel), `rgb.py aggiorna usdb` (Andrea) | ☑ 8 ott, tx `7795d147…` trasmessa (`WAITING_CONFIRMATIONS`); l'emittente resta con 999.499,00 USDB futuri, 4 UTXO colorabili liberi e 44.347 sats; al blocco il mercante vede USDB. Resta aperta la fattura di prova da 480 (idx 2, `WAITING_COUNTERPARTY`): scade da sola in 24 ore |
| 9-10 ott | Due identità Nostr di prova (sezione 11) | ☑ 8 ott: `identita.mjs nuova` per `usdb` e `tothemooon`, kind 0 sul relay locale; le pubbliche in §11 |
| 9-10 ott | Relay locale sul portatile, `ws://127.0.0.1:7777` | ☑ 8 ott: **`nak serve`** (decisione di Andrea: Docker non c'è né in Windows né nel WSL), binario `~/bin/nak` v0.21.0 (45 MB dalle release di fiatjaf), provato con nostr-tools: pubblica e rilegge |
| 11-12 ott | `nwc-wdk.mjs` BASE nel WSL: evento info (13194, `encryption` nip44), `get_info`, `get_balance`, la connection string SU FILE (`nwc/connessione-barattolo.txt`, mai in chat) | ☑ 8 ott, scritto a mano con nostr-tools (copia in `deploy/rgb/`): `connetti barattolo`, `serve`, e il client di prova `prova barattolo` → `get_info` ok, `get_balance` 26.519.000 msat, `rgb_list_assets` → `NOT_IMPLEMENTED`, tutto nip44 |
| 8 ott | La connection string incollata nel Profilo di Barattolo in collaudo (la CSP ammette `ws:`): Andrea, dal suo browser, sul server di collaudo del worktree (porta 8098, config dal solo esempio, identità 111 dall'hash) | ☑ 8 ott: «Incassi e pagamenti → 👛 Wallet NWC → ⚡ Collega»; il log del servizio dice `barattolo: get_info → ok (nip44_v2)` e l'app «wallet collegato», con la nota che manca `pay_invoice` (giusto: la base non ce l'ha). Al primo tentativo il servizio era morto col `nohup` (§6) |
| 11-12 ott | `rgb_http.py` sulla VM, `127.0.0.1:8787` (salute/saldo/fattura/aggiorna/trasferimenti del wallet `barattolo`), gamba `-L 8787:127.0.0.1:8787` nel tunnel | ☑ 8 ott: copiato e avviato da Andrea (`nohup`), dal tunnel `/salute`, `/saldo` (JAR, 4 UTXO liberi), `/fattura` «qualunque asset» ok e per USDB «AssetNotFound» (lezione 5), corpo storto 400, rotta ignota 404; banco di cartone sul PC in più. **Da fermare la sera** (backup delle 03:30) |
| 8 ott (era 11-12) | Il commit su main: `RGB_ATTIVO`/`RGB_PROVA_IDS`/`NIP05_NOMI`, il gruppo nel pannello delle leve, `rgb_ammesso`, la rotta `/.well-known/nostr.json`, `prove_leva_rgb` | ☑ 8 ott, su main PRIMA del lancio (decisione di Andrea: è un cancello chiuso e una rotta che risponde `{"names": {}}` finché `NIP05_NOMI` non entra nel config del VPS — le due hex le dà `node identita.mjs pubblica <nome>`); il nome «Cassiere» tolto anche dagli identificatori, con la prova; suite severa e collaudi della CI nel verbale del push (CANTIERI) |
| 11-12 ott | QVAC: `npm i -g @qvac/cli@latest`, alias `consigliami` → `QWEN3_1_7B_INST_Q4` con `ctx_size 8192`, scaricato; `consigliami-prova.html` FUORI dal repo con `response_format` json_schema e `reasoning_budget: false`; `qvac serve --openai --cors-origin <origine esatta>` | ☑ 8 ott (§4): CLI 0.15.0, 1,06 GB scaricati, pagina provata nel Browser pane col 0.6B e col 1.7B |
| 13 ott | Q&A con le undici domande | ☐ |
| 14-16 ott | §5 riscritta e stampata; gli schermi su carta; il giro provato tre volte; video di riserva della demo | ☐ |
| 14-16 ott | **Backup della VM**, **portatile con tutto scaricato** (modelli QVAC, `nak`, pacchetti del wallet), **prova di riavvio completa** di tutta la catena, nell'ordine di §6 e col tunnel a tre gambe: i comandi qui sotto, uno alla volta | ☐ |
| 16 ott | I due annunci di MOON e USDB firmati dalle identità di prova e pubblicati sul relay locale, nella forma di `spec/NIP-RGB-ASSETS.md` (kind segnaposto): un comando `annuncio <nome> <asset_id>` in `identita.mjs`, sul calco di `profilo`, DA SCRIVERE (è infrastruttura dichiarata: l'evento esiste, nessun codice lo legge). La cura di D.3 punto 0 | ☐ |

**I comandi della riga «14-16 ott»**, nell'ordine, uno alla volta, dal
WSL e non da PowerShell dove c'è `ssh` (lezione 1 di §9: le virgolette
dentro l'argomento spariscono). Niente di tutto questo tocca il VPS, il
nodo o il relay.

1) **Backup della VM** — prima si ferma `rgb_http.py` (apre il wallet
`barattolo`, e il backup lo vuole chiuso), poi il backup notturno fatto
a mano, poi il pull dal PC e il drill senza scrivere niente in chiaro:

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'pkill -f "[r]gb_http.py"; sudo systemctl start rgb-backup.service; sudo journalctl -u rgb-backup.service -n 15 --no-pager; ls -lt /var/backups/rgb | head -3'
```

Poi dal PC `pull.ps1` (la gamba `rgb/`, come ogni notte) e il drill
sull'archivio appena arrivato in `C:\Users\Andrea\BarattoloBackup\rgb\`:
`age -d -i rgb-prova.key <archivio> | tar -t` deve elencare
`rgb/dati/<wallet>/chiavi.json` per `barattolo`, `to-the-mooon` e
`usdb`, e una fotografia `.rgb-backup` per ciascuno. Il wallet utente e le
identità hanno il loro archivio (§11): si rifà solo se è cambiato
qualcosa dall'8 (`node punti.mjs backup`; per identità e NWC lo stesso
`tar | age -r <pubblica age della VM>` dell'8 ott, copia in
`BarattoloBackup\rgb\`).

2) **Portatile con tutto scaricato** — si guarda, non si installa; poi
la controprova col Wi-Fi SPENTO: se qualcosa parte a scaricare, il 17
sull'hotspot non partirebbe.

```bash
cd ~/wdk-prova && source ~/.nvm/nvm.sh && node -v && npm ls --depth=0 2>/dev/null | grep -E 'wdk-wallet-rgb|rgb-lib-linux-x64|nostr-tools|bip39'
~/bin/nak --version && ls -la ~/wdk-prova/identita ~/wdk-prova/nwc
```

```powershell
qvac --version; qvac doctor; Get-ChildItem $env:USERPROFILE\.qvac\models
```

(il 1.7B da 1,06 GB e il 0.6B devono esserci già). Col Wi-Fi spento:
`qvac serve --openai --port 11434 --host 127.0.0.1` e una chat
completion con `"model": "consigliami"` dalla pagina locale
`consigliami-prova.html` (servita da `python -m http.server 8081`, con
`--cors-origin http://127.0.0.1:8081`): risponde senza scaricare
niente. Sul portatile devono stare anche il clone di `fidelity-points`
e il worktree di Barattolo con le dipendenze pip già installate
(`python -c "import fastapi, uvicorn, httpx"`).

3) **Prova di riavvio completa**, nell'ordine di §6 — la VM, il tunnel a
TRE gambe, la faccia HTTP, il relay, il wallet, il servizio NWC, QVAC,
Barattolo in collaudo — con un controllo dopo ogni passo:

```bash
# VM: i tre container, la catena in pari, il wallet mercante, la faccia HTTP
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && docker compose up -d && docker compose ps'
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && ./venv/bin/python rgb.py saldo barattolo'
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && nohup ./venv/bin/python rgb_http.py > rgb_http.log 2>&1 &'
# WSL, finestra 1 (resta aperta): il tunnel a tre gambe
ssh -i ~/.ssh/lnvps -N -L 50001:127.0.0.1:50001 -L 3000:127.0.0.1:3000 -L 8787:127.0.0.1:8787 debian@vm-2050.lnvps.cloud
# WSL, finestra 2: la faccia HTTP dal tunnel, il relay, il wallet, le identità, il servizio NWC
curl -s 127.0.0.1:8787/salute                                   # {"ok": true, "wallet": "barattolo", "rete": "signet"}
setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown
cd ~/wdk-prova && source ~/.nvm/nvm.sh && node punti.mjs saldo   # PRIMA del servizio NWC: USDB 50.000 settled, MOON 60
node identita.mjs pubblica usdb; node identita.mjs pubblica tothemooon   # le due hex per NIP05_NOMI del config di collaudo
setsid nohup node nwc-wdk.mjs serve > nwc/serve.log 2>&1 < /dev/null & disown
node nwc-wdk.mjs prova barattolo                                 # get_info ok (nip44), get_balance, rgb_list_assets → NOT_IMPLEMENTED
```

```powershell
cd C:\Users\Andrea\qvac-prova; qvac serve --openai --port 11434 --host 127.0.0.1 --cors-origin http://127.0.0.1:8080
```

Poi Barattolo in collaudo sul worktree, porta 8080, config dal solo
esempio con `MODALITA_COLLAUDO = True`, `MOSTRO_RELAY` e
`MOSTRO_RELAY_SPECCHIO` al relay morto (`ws://127.0.0.1:9`) e
`NIP05_NOMI` con le due hex di sopra (`uvicorn server:app --port 8080`);
`curl -s "http://127.0.0.1:8080/.well-known/nostr.json?name=usdb"` deve
dare la hex di `usdb`; nell'app (identità 111 dall'hash) Profilo →
Incassi e pagamenti → 👛 Wallet NWC → ⚡ Collega con la stringa di
`nwc/connessione-barattolo.txt` → «wallet collegato», e nel log del
servizio `barattolo: get_info → ok (nip44_v2)`. Il giro è verde quando
ogni riga qui sopra ha dato quel che dice il commento, senza un
comando in più. La sera si spegne nell'ordine inverso:
`pkill -f "[n]wc-wdk.mjs serve"; pkill -f "[n]ak serve"` nel WSL,
`pkill -f "[r]gb_http.py"` sulla VM (il backup delle 03:30 vuole il
wallet chiuso); i container restano su.

## 11. Le due identità Nostr di prova (gli «emittenti»)

Servono a firmare gli annunci di USDB e di MOON (studio, parte seconda,
B.1) e a mostrare «Emesso da … ✓» nella schermata (C). Sono chiavi
NUOVE, di prova: MAI la chiave della piattaforma, MAI nel repo (regola
ferrea 1).

- **Create l'8 ott** con `identita.mjs` (copia in `deploy/rgb/`): le
  private in `~/wdk-prova/identita/usdb.json` e
  `~/wdk-prova/identita/tothemooon.json` (0600, nel WSL). **Archiviate
  l'8 ott** insieme alla chiave del servizio NWC e alle connessioni:
  `~/wdk-prova/backup/identita-nwc-20261008.tar.age`, cifrato con la sola
  chiave PUBBLICA age della VM rgb-prova (la stessa dei backup dello
  stash: la segreta sta sul PC e su Bitwarden), copia in
  `C:\Users\Andrea\BarattoloBackup\rgb\`; drill fatto (si riapre con
  `rgb-prova.key`, elenco letto senza scrivere niente in chiaro). `age`
  nel WSL non c'è: si usa quello di Windows da `/mnt/c/…/WinGet/…/age.exe`.
  Il wallet utente ha il suo backup a parte (`punti.mjs backup`). Le
  pubbliche, scritte in npub perché 64 esadecimali di fila farebbero
  scattare lo scanner dei segreti della CI (l'hex, che è quel che vuole
  `NIP05_NOMI`, lo dà `node identita.mjs pubblica <nome>`):
  - `usdb` → `npub1lc2fj4snzv5etn9nfx8w8d2d9nla028r98akhlml3ms97r84gtaq39k0f9`
  - `tothemooon` → `npub12xql9gw8ru2qv63x8nvhtc2vcqcl06rce5d30sw6vcza4zsjgpns0nr6n4`
  - e il servizio NWC del wallet utente (`nwc-wdk.mjs`, chiave in
    `~/wdk-prova/nwc/servizio.txt`) → `9ad5f2b0…` (solo per riconoscerlo
    nel relay: non è un emittente).
- **Il kind 0**: pubblicato l'8 ott sul relay locale per tutt'e due
  (`identita.mjs profilo`): `name`/`display_name`
  «Dollari_di_prova_Barattolo» / «To The Mooon», `about` che dice «di
  prova, nessun valore reale», `nip05` `usdb@barattolo.store` /
  `tothemooon@barattolo.store`. Manca `picture` (il logo del negozio,
  già in `assets/`): si aggiunge quando serve. Su un relay pubblico SOLO
  se si decide prima (sono chiavi di prova, non segreti della
  piattaforma, ma la regola di casa è «mai eventi pubblicati» nei giri
  di collaudo).
- **Il NIP-05, DECISO il 7 ott sera (Alan, confermato)**: la strada (a),
  una rotta esplicita `/.well-known/nostr.json` su barattolo.store, sul
  calco di `assetlinks.json` (regola 3: file statico, nome in
  whitelist, niente redirect — NIP-05 li vieta — e
  `Access-Control-Allow-Origin: *`), nel commit dell'8 ott, su main lo
  stesso giorno (la rotta risponde vuota finché `NIP05_NOMI` non entra
  nel config del VPS): due nomi (`usdb`, `tothemooon`), zero rischio, e
  la riga nella schermata
  legge «tothemooon@barattolo.store ✓»; ai giudici si dice che il VERO
  negozio avrebbe il suo dominio. La strada (b), GitHub Pages, è
  scartata. **In roadmap (slide, niente codice)**: la stessa rotta, un
  giorno, legge i nomi degli UTENTI — chi arriva al livello 2 del
  mercatino («Bottega avviata»: 50 XP e 1 affare) ottiene gratis
  `<nome>@barattolo.store`, solo su una npub verificata (regola ferrea
  2 intatta: è una mappa nome → chiave pubblica). Le regole del
  cantiere futuro stanno nello studio, parte seconda, G.3.
- **La verifica in Barattolo** (lavoro del weekend): GET del JSON
  attraverso `url_api_ammesso` (solo https, host pubblico, mai
  loopback) con `follow_redirects=False`, confronto `names[<nome>]` ==
  `pubkey` dell'annuncio, cache di 24 ore (se il DNS del portatile
  manca, la riga dice «verificato il 16 ott»).

Nota a margine, fuori cantiere ma scoperta qui: il pull notturno del
backup del NODO falliva dal 7 settembre («permission denied» su
`/var/backups/nodo`: lo script lo richiudeva a 700 ogni notte). Curato
da Andrea il 1 ott (riga 19 di `backup-nodo.sh`, `-g pull -m 750`): il
verbale sta in `docs/NODO-MOSTRO.md`.
