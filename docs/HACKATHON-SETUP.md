# Hackathon RGB di Torino (17-18 ott 2026): l'infrastruttura preparata prima

Stato al 1 ottobre 2026, **aggiornato il 7 ottobre** con le idee di Alan,
**e l'8** (cantiere «chiusura della preparazione»: la leva su main, il
repo `fidelity-points`, la scaletta con la ✓ al sabato), **e l'8
sera** (cantiere «il comando `annuncio` e la scaletta della demo»:
il comando in `identita.mjs` con la sua prova; in §10 il 16 e il 15
un comando per riga; in §11 la demo schermata per schermata, i due
giorni ora per ora, il piano B e la lista di controllo della
roadmap), **e il 9** (cantiere «mutinynet-prep»: Mutinynet coi
servizi degli organizzatori, deciso con Alan — `RGB_CATENA`, i due
`.env`, il backup a due catene, la lista di domenica 11 e quella del 15
per i due portatili di Alan in §10, i numeri della demo e le scene
8-bis in §11, la chiavetta di riserva),
(la demo sui punti fedeltà, **NWC-RGB** — l'estensione NIP-47 per gli
asset RGB —, l'emittente legato a un'identità Nostr: il perché e il
disegno stanno nella parte seconda dello studio; qui c'è COSA si fa e
quando) e **la sera del 7 con le sue quattro decisioni** (studio, parte
seconda, G: il repo separato, il nome NWC-RGB, il NIP-05 anche per gli
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
| **Il tunnel** | dal WSL verso la VM | **Mutinynet (dall'11 ott)**: UNA gamba, `ssh -i ~/.ssh/lnvps -N -L 8787:127.0.0.1:8787 debian@vm-2050.lnvps.cloud` (indexer e proxy sono pubblici: resta solo `rgb_http.py`). **Signet (piano B)**: tre gambe, `ssh -i ~/.ssh/lnvps -N -L 50001:127.0.0.1:50001 -L 3000:127.0.0.1:3000 -L 8787:127.0.0.1:8787 debian@vm-2050.lnvps.cloud` (la chiave è copiata DENTRO il WSL a 600: su `/mnt/c` i permessi sono 777 e ssh la rifiuta) |
| **La catena** (9 ott, studio Mutinynet) | VM e portatile | `RGB_CATENA` = `signet` (default: bitcoind+electrs della VM) o `mutinynet` (il signet degli organizzatori, blocchi da 30 s: Esplora `https://esplora.signet.kaleidoswap.com`, proxy `rpcs://proxy.kaleidoswap.com/json-rpc`, link `https://mutinynet.com/tx/`). Per rgb-lib è `SIGNET` in tutt'e due i casi — il blocco 0 di Mutinynet è quello del signet, verificato — e cambiano indexer, proxy, link e le CARTELLE (`~/rgb/mutinynet` e `~/rgb/backup-mutinynet` sulla VM, `~/wdk-prova/mutinynet/utente` nel WSL): uno stash non vede mai due catene, e `chiavi.json`/`catena.txt` ricordano dove il wallet è nato (si rifiuta di aprirsi sull'altra). Si accende con `source ~/rgb/mutinynet.env` (VM) e `source ~/wdk-prova/mutinynet.env` (WSL): i due file sono `deploy/rgb/mutinynet-vm.env` e `mutinynet-wsl.env`, con le riserve commentate (`https://mutinynet.com/api`, il proxy di Iris). Senza `source` è il signet di sempre: il piano B è non fare niente. Su Mutinynet NON esiste un Electrum pubblico |

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
- **Dall'11 ott (Mutinynet)**: `mutinynet.env` (la copia di
  `deploy/rgb/mutinynet-vm.env`), `mutinynet/<wallet>/` coi tre wallet
  riemessi (`barattolo`, `to-the-mooon`, `usdb`: stessi nomi, chiavi
  nuove, `"rete": "mutinynet"` in chiavi.json) e `backup-mutinynet/` con
  le loro fotografie. `backup-rgb.sh` le mette nell'archivio notturno
  accanto a quelle del signet.
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

**Su Mutinynet (dall'11 ott 2026) gli asset sono RIEMESSI**: un NIA
vive sulla catena dove è nato, e il wallet utente di Mutinynet è nuovo.
Stessi ticker, nomi, precisioni e quantità (le `SCHEDE` di
`identita.mjs`), id NUOVI, che si incollano qui e in
`ASSET_PER_CATENA.mutinynet` di `deploy/rgb/identita.mjs` (al posto dei
due `INCOLLA_QUI_…`, senza `rgb:`) la domenica, dopo `rgb.py emetti`
(§10, la lista «Domenica 11 ott», punti 4 e 5). JAR non si riemette
(fuori dalla demo). Gli id di signet qui sopra restano veri: sono gli
asset del piano B.

| Ticker | Emittente (wallet, in `~/rgb/mutinynet/`) | Quantità | asset_id su Mutinynet |
|---|---|---|---|
| **MOON** | to-the-mooon | 1.000.000, precisione 0 | ☐ `rgb:…` (si incolla l'11) |
| **USDB** | usdb | 1.000.000,00 cioè 100.000.000 unità, precisione 2 | ☐ `rgb:…` (si incolla l'11) |

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

**Corretto l'8 ott sera, dal vivo sul PC fisso (Andrea)**: QVAC non è
globale e non è nel PATH — sta in `qvac-prova` come dipendenza locale
(`npm install @qvac/sdk @qvac/cli`: 0.21.0 e 0.15.0) e si lancia con
`npx qvac …`; il primo avvio col Wi-Fi porta `--model consigliami
--model qwen3-600m-inst-q4` e scarica i due modelli. E **Qwen3
ragiona prima di rispondere**: una chat completion nuda con
`max_tokens` 80 torna `content: null` e solo `reasoning_content`;
l'interruttore che QVAC rispetta è `"reasoning_budget": false`
(`enable_thinking: false` è ignorato, `/no_think` spegne ma sporca la
risposta: cinque varianti provate la sera stessa), che la pagina manda
già e `consiglio.py` manda dall'8 sera. I dettagli e i comandi in §10,
punti 2 e 3.

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
  asset (MOON e USDB, nella forma della bozza `docs/spec/NIP-RGB-ASSETS.md`,
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

**Prima di tutto: quale catena.** Dall'11 ott la demo sta su
**Mutinynet** (§1, «La catena»), e OGNI riga qui sotto che tocca un
wallet comincia con `source ~/rgb/mutinynet.env` (VM) o `source
~/wdk-prova/mutinynet.env` (WSL): senza, gli stessi comandi parlano col
signet della VM, che è il piano B e resta intatto. Chi sbaglia catena
non rompe niente: `rgb.py` e `punti.mjs` si rifiutano di aprire un
wallet nato sull'altra («il wallet «barattolo» è nato su signet, ma
RGB_CATENA dice mutinynet»).

Sulla VM:

```bash
cd ~/rgb && docker compose up -d && docker compose ps     # i container servono SOLO al signet (piano B): su Mutinynet possono restare su, non disturbano
docker compose exec bitcoind su -c 'bitcoin-cli -signet getblockchaininfo' blits | grep -E '"(blocks|headers|initialblockdownload)"'   # solo per il piano B
source ~/rgb/mutinynet.env                                 # MUTINYNET: da qui ogni rgb.py parla con l'Esplora e il proxy pubblici e coi wallet di ~/rgb/mutinynet
./venv/bin/python rgb.py saldo to-the-mooon               # catena in pari e asset al loro posto (gli asset della seconda tabella di §2)
./venv/bin/python rgb.py backup to-the-mooon              # prima di ogni giorno di demo (in ~/rgb/backup-mutinynet)
```

Sul portatile, nel WSL (finestra 1, resta aperta): il tunnel a UNA
gamba (quella di `rgb_http.py`; indexer e proxy sono pubblici). Per il
piano B signet, le tre gambe di §1.

```bash
ssh -i ~/.ssh/lnvps -N -L 8787:127.0.0.1:8787 debian@vm-2050.lnvps.cloud
```

Nel WSL (finestra 2):

```bash
cd ~/wdk-prova && source mutinynet.env && source ~/.nvm/nvm.sh && node punti.mjs saldo   # il wallet di ~/wdk-prova/mutinynet/utente: USDB 50.000 e MOON 60 (dopo l'11)
```

In Windows (PowerShell):

```powershell
cd C:\Users\Andrea\qvac-prova; qvac serve --openai --port 11434 --host 127.0.0.1
```

Se la VM non risponde: su Mutinynet il wallet utente non ne ha bisogno
(indexer e proxy sono pubblici), manca solo il mercante (`rgb_http.py`);
se l'Esplora di KaleidoSwap risponde 429 o tace, la riserva è
`RGB_INDEXER=https://mutinynet.com/api` nella stessa riga (le fatture
NON portano l'indexer: restano valide); se tace il proxy, la riserva è
`RGB_PROXY=rpcs://proxy.iriswallet.com/0.2/json-rpc` e le fatture aperte
si RIFANNO (il proxy sta dentro la fattura). Sul signet (piano B) gli
endpoint pubblici erano quelli di Utexo/Iris
(`RGB_INDEXER=tcp://46.224.75.237:50001`,
`RGB_PROXY=rpcs://proxy.iriswallet.com/0.2/json-rpc`), ma le fatture
fatte col tunnel portano l'endpoint 127.0.0.1 e vanno rifatte. Se il
portatile muore: la VM ha tutto (`rgb.py` fa anche la parte utente con
un terzo wallet), e il backup del PC riapre lo stash.

Le tre cose nuove dell'8 ott, sul portatile e sulla VM:

```bash
setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown      # WSL: il relay locale (muore col WSL)
cd ~/wdk-prova && source mutinynet.env && source ~/.nvm/nvm.sh && setsid nohup node nwc-wdk.mjs serve > nwc/serve.log 2>&1 < /dev/null & disown   # WSL: il servizio NWC sul wallet di Mutinynet (tiene aperto il wallet: niente punti.mjs intanto); stessa chiave e stessa connection string di prima
```

⚠️ `setsid … & disown`, non il solo `nohup`: lanciato da una chiamata
`wsl.exe -e bash -lc` il servizio NWC è morto quando la chiamata è
finita, e Barattolo ha bussato a vuoto (8 ott, «Busso qualche
secondo… niente conferma»). Per fermarli: `pkill -f "[n]wc-wdk.mjs
serve"` — con le parentesi, o `pkill` uccide la shell che lo lancia.

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && source mutinynet.env && nohup ./venv/bin/python rgb_http.py > rgb_http.log 2>&1 &'   # VM: la faccia HTTP del mercante, sul wallet di Mutinynet
curl -s 127.0.0.1:8787/salute   # → {"ok": true, "wallet": "barattolo", "rete": "mutinynet"}; se dice "signet", è partito senza il source
```

`rgb_http.py` apre il wallet `barattolo` (della catena del suo ambiente)
a ogni richiesta: alle 03:30 il backup apre gli stessi wallet, quindi di
notte si ferma (`pkill -f "[r]gb_http.py"` sulla VM) e si riaccende la
mattina della demo.

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
   `fidelity-points`.
6. **Domenica mattina** — i due testi `docs/spec/NIP-RGB-ASSETS.md` e
   `docs/spec/NWC-RGB.md` rifiniti con quel che
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
seconda, B.2, e in inglese in `docs/spec/NWC-RGB.md` del repo privato
dall'8 ott; la BASE del servizio si fa prima del 17 e si dichiara, i
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
| 14-16 ott | **Backup della VM**, **portatile con tutto scaricato** (modelli QVAC, `nak`, pacchetti del wallet), **prova di riavvio completa** di tutta la catena, nell'ordine di §6 e col tunnel a tre gambe: i comandi qui sotto, uno alla volta | ☐ backup e portatile. ☑ **8 ott sera, la prova di riavvio completa** (punto 3) tutta verde dal vivo sul PC fisso (Andrea): NIP-05 dalla rotta, «wallet collegato», `get_info → ok (nip44_v2)`; le quattro correzioni ai comandi sono scritte nei punti 2 e 3. Il riavvio del VPS è fatto |
| 16 ott | I due annunci di MOON e USDB firmati dalle identità di prova e pubblicati sul relay locale, nella forma di `docs/spec/NIP-RGB-ASSETS.md` (evento addressable, kind segnaposto **38180** — 38172/38173 sono di NIP-87, questo sta subito dopo e non è registrato da nessuno —, `d` = ContractId nudo, `i`/`k` di NIP-73, `n` signet, schema, ticker, name, precision, supply, alt; niente `issuer`, il genesis dice `ssi:anonymous`; niente `u`): il comando `annuncio <nome> <asset_id>` in `identita.mjs`, sul calco di `profilo`, e `annuncio --prova <nome> <asset_id>` che stampa l'evento firmato in JSON SENZA pubblicarlo. È infrastruttura dichiarata: l'evento esiste, nessun codice di Barattolo lo legge prima del 17. La cura di D.3 punto 0 | ☑ **8 ott sera, il comando** (cantiere «il comando `annuncio` e la scaletta della demo», copia in `deploy/rgb/`): la tabella `ASSET` coi valori PUBBLICI di §2 (ticker, nome del genesis con gli underscore, precisione, supply) e un contratto → un emittente (`usdb` non annuncia MOON: D.3 punto 4); l'asset_id con o senza `rgb:`; la firma verificata prima di stampare o pubblicare; la privata mai in output. `prove_annuncio_identita` (46): lo script VERO con identità usa-e-getta, la pubblica di `pubblica` è quella dell'evento, la firma Schnorr riverificata in Python puro, il relay morto non tocca `--prova` e senza `--prova` è un errore; in CI nostr-tools arriva da un passo del workflow fuori dal repo. Provato nel WSL su un `nak serve` di prova (porta 7790): pubblicato, riletto con nostr-tools, il secondo invio sostituisce il primo. ☐ **Il 16**: il lancio con le identità vere, i comandi al punto 4) qui sotto e in §11 |
| 16 ott, e la mattina del 17 e del 18 | **La semina del DB di collaudo** (cantiere «la semina della demo», 9 ott): il DB di collaudo nasce vuoto, e la schermata 3 di §11.2 vuole il negozio To The Mooon — la card «Consigliati» della home lo cerca già col codice `1b9a53e6` del catalogo del client (`RACCONTI` di miniapp.html) e senza di lui dice «Negozio non trovato», la ricerca «Mooon» non trova niente. `semina_demo.py` scrive nel DB di collaudo: il negozio (utente finto 444, codice LETTO dal client, link `/negozio/tothemooon`, la npub pubblica di `tothemooon` di §11, l'avatar dal logo in `assets/consigliati/`, l'insegna dal banner di `assets/scoprire/` — che il client mostra solo con `BANNER_NEGOZIO_ATTIVO = True` nel config e con un link https al sito del negozio, `--insegna-link`), l'annuncio del gioco (un pezzo, ritiro a mano a Torino, PREZZO IN SATS CHE OGGI VALE 4,80 $: lo studio C fissa la cifra in dollari, il cambio lo legge da `cambio_noto` del server, e rilanciarla la mattina della demo lo ritara) e il cliente 111; `ordine` crea l'ordine «creato, non pagato» della mattina. Idempotente: si rilancia senza doppioni. Scrive SOLO con `MODALITA_COLLAUDO = True` e solo su un DB che il server ha già creato; niente rete, niente VPS. Le righe e le risposte attese al punto 5) qui sotto | ☑ 9 ott lo script, provato dal vivo sul PC (server del worktree su un'altra porta, config dal solo esempio: negozio dal codice e dal link, storia e card «Consigliati» che portano al negozio, annuncio in vetrina e in ricerca, ordine in «Ordini» di 111 come «Da pagare»), `prove_semina_demo` in prove.py e `collaudo_semina_demo` sul server vero in CI. ☐ il 16: `py -3 semina_demo.py` sul DB di collaudo vero, poi la controprova nel browser (punto 5) |
| 9 ott | **Mutinynet coi servizi degli organizzatori** (studio del 9, deciso con Alan; i perché nella lista «Domenica 11 ott» qui sotto): il cantiere «mutinynet-prep» — `RGB_CATENA` in rgb.py/rgb_http.py/punti.mjs/nwc-wdk.mjs/identita.mjs con la guardia della catena, i due `.env` (`deploy/rgb/mutinynet-vm.env`, `mutinynet-wsl.env`), `backup-rgb.sh` a due catene, la chiavetta di riserva (`chiavetta-prepara.sh`, `install-offline.sh`), §1, §2, §6, questa sezione, §11 e la bozza NWC-RGB | ☑ 9 ott, solo testo e codice (`prove_mutinynet_prep` in prove.py; la chiavetta provata in due container WSL, Ubuntu 22.04 e 24.04). VM e wallet NON toccati |
| 11 ott (domenica) | **La VM e il portatile su Mutinynet**: file copiati, wallet nuovi, faucet, UTXO, riemissione di USDB e MOON, i due id in §2 e in `identita.mjs`, gli asset al wallet utente e al mercante, `rgb_http` e NWC con l'env, il backup a due catene | ☐ la lista «Domenica 11 ott», punto per punto |
| 15 ott | **I due portatili di Alan** (Pop!_OS 32 GB e Zorin 16 GB) installati a casa di Andrea, con la rete, nell'utente Linux `hackathon`; la chiavetta come riserva (cambio del 9: niente installazione in sala) | ☐ la lista «15 ott» qui sotto |

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
cd C:\Users\Andrea\qvac-prova; npx qvac --version; npx qvac doctor; Get-ChildItem $env:USERPROFILE\.qvac\models
```

**Corretto l'8 ott sera, dal vivo (Andrea)**: QVAC NON è nel PATH —
sta in `qvac-prova` come dipendenza locale (`npm install @qvac/sdk
@qvac/cli`, dopo `npm init -y` se manca `package.json`: oggi
`@qvac/sdk` 0.21.0 e `@qvac/cli` 0.15.0) e il comando è **`npx qvac …`**,
non `qvac` nudo. Il primo avvio, col Wi-Fi, si fa con **`npx qvac serve
--openai --port 11434 --host 127.0.0.1 --model consigliami --model
qwen3-600m-inst-q4`**: così scarica i due modelli subito (doctor tutto
verde, serve ok su 11434), e il 1.7B da 1,06 GB e il 0.6B da 382 MB
stanno in `~/.qvac/models`. Col Wi-Fi spento: `npx qvac serve --openai
--port 11434 --host 127.0.0.1 --cors-origin http://127.0.0.1:8081` e
una chat completion con `"model": "consigliami"` dalla pagina locale
`consigliami-prova.html` (servita da `python -m http.server 8081`):
risponde senza scaricare niente. **Qwen3 ragiona prima di rispondere**
(8 ott sera, dal vivo): una chat completion nuda con `max_tokens` 80
torna `content: null` e solo `reasoning_content`. L'interruttore che
QVAC rispetta è **`"reasoning_budget": false`** nella richiesta
(provato la sera stessa sul 1.7B, cinque varianti: `enable_thinking:
false`, anche in `chat_template_kwargs`, è IGNORATO; `/no_think` nel
sistema spegne il thinking ma la risposta è sporca); con
`response_format` a `json_schema` la grammatica parte subito e il
modello non pensa comunque, ma l'interruttore si manda lo stesso.
`consigliami-prova.html` lo manda già (riga `reasoning_budget: false`);
`consiglio.py` NON lo mandava, aggiunto l'8 sera. I curl verso 8080 e
11434 si fanno da PowerShell con `curl.exe`: dal WSL `127.0.0.1` è
quello di Linux. Sul portatile devono stare anche il clone di
`fidelity-points` e il worktree di Barattolo con le dipendenze pip già
installate (`py -3 -c "import fastapi, uvicorn, httpx"` da PowerShell:
il Python del WSL non ha fastapi).

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
cd C:\Users\Andrea\qvac-prova; npx qvac serve --openai --port 11434 --host 127.0.0.1 --cors-origin http://127.0.0.1:8080
```

Poi Barattolo in collaudo, porta 8080, **da PowerShell** (corretto l'8
ott sera, dal vivo: il Python del WSL non ha fastapi, e il git del WSL
non ha le credenziali di GitHub — `git pull` da PowerShell). Il
`config.py` locale, che aveva la sola `MODALITA_COLLAUDO = True`, ha in
più `MOSTRO_RELAY = "ws://127.0.0.1:9"`, `MOSTRO_RELAY_SPECCHIO =
["ws://127.0.0.1:9"]` (il relay morto) e `NIP05_NOMI` con le due hex di
sopra (aggiunte a mano l'8 sera):

```powershell
cd C:\Users\Andrea\Documents\GitHub\satmarket; git pull; py -3 -m uvicorn server:app --port 8080
curl.exe -s "http://127.0.0.1:8080/.well-known/nostr.json?name=usdb"   # → {"names": {"usdb": "<hex di usdb>"}}
```

(`curl.exe` da PowerShell, non dal WSL: lì `127.0.0.1` è quello di
Linux). Nell'app (identità 111 dall'hash) Profilo → Incassi e pagamenti
→ 👛 Wallet NWC → ⚡ Collega con la stringa di
`nwc/connessione-barattolo.txt` → «wallet collegato», e nel log del
servizio `barattolo: get_info → ok (nip44_v2)`. Il giro è verde quando
ogni riga qui sopra ha dato quel che dice il commento, senza un
comando in più. **Passato tutto verde l'8 ott sera** sul PC fisso
(Andrea): NIP-05, wallet collegato, `get_info ok nip44_v2`. La sera si spegne nell'ordine inverso:
`pkill -f "[n]wc-wdk.mjs serve"; pkill -f "[n]ak serve"` nel WSL,
4) **Il 16, gli annunci** (dopo la prova di riavvio: il relay locale
deve essere su). Dal WSL, uno alla volta. Il comando è `identita.mjs
annuncio` (scritto l'8 ott sera, copia in `deploy/rgb/`: la prima riga
porta in `~/wdk-prova` la copia aggiornata, quella dell'8 mattina non
ce l'ha). Con `--prova` si GUARDA l'evento firmato senza pubblicarlo: la
`pubkey` stampata deve essere la hex di `pubblica <nome>`, il `d` il
ContractId senza `rgb:`. Senza `--prova` si pubblica sul relay locale
(`NWC_RELAY`, default `ws://127.0.0.1:7777`); l'evento è addressable:
rilanciarlo sostituisce il precedente, non lo duplica. L'ultima riga
rilegge i due annunci dal relay con nostr-tools (`nak req` lanciato da
`wsl.exe` stampa muto, lezione 3 di §9): deve elencare USDB e MOON con
le due hex di `pubblica`. Niente relay pubblici: lo script si ferma da
solo se `NWC_RELAY` non è locale.

```bash
cp /mnt/c/Users/Andrea/Documents/GitHub/satmarket/deploy/rgb/identita.mjs ~/wdk-prova/identita.mjs
cd ~/wdk-prova && source ~/.nvm/nvm.sh && (pgrep -fa "[n]ak serve" || (setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown))
node identita.mjs pubblica usdb
node identita.mjs annuncio --prova usdb rgb:H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A
node identita.mjs annuncio usdb rgb:H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A
node identita.mjs pubblica tothemooon
node identita.mjs annuncio --prova tothemooon rgb:9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM
node identita.mjs annuncio tothemooon rgb:9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM
node --input-type=module -e "import {Relay} from 'nostr-tools/relay'; const r=await Relay.connect(process.env.NWC_RELAY||'ws://127.0.0.1:7777'); const got=[]; await new Promise(res=>{const s=r.subscribe([{kinds:[38180]}],{onevent:e=>got.push(e),oneose:()=>{s.close();res()}}); setTimeout(res,4000)}); r.close(); for (const e of got) console.log(e.tags.find(t=>t[0]==='ticker')[1], 'd', e.tags.find(t=>t[0]==='d')[1], 'autore', e.pubkey.slice(0,12)+'…', new Date(e.created_at*1000).toISOString())"
```

Il relay `nak serve` tiene gli eventi in memoria: se il WSL si riavvia
fra il 16 e il 17, la mattina del 17 si rilanciano le due righe
`annuncio` (dieci secondi) prima del kickoff — è nella tabella dei due
giorni (§11). Dopo, l'archivio delle identità non cambia: le chiavi
sono quelle dell'8, non serve rifare il backup.

5) **La semina del DB di collaudo** (il 16 dopo la prova di riavvio, e
di nuovo la mattina del 17 e del 18 per ritarare il prezzo al cambio del
giorno). Da PowerShell, dalla cartella del repo, con Barattolo in collaudo
acceso da almeno un minuto CON LA RETE (è lui a scrivere il dollaro in
`cambio_noto`; sull'hotspot va bene lo stesso, basta che CoinGecko abbia
risposto una volta). Il server può restare acceso: la semina scrive nel
suo stesso database e lui la vede alla richiesta dopo.

```powershell
cd C:\Users\Andrea\Documents\GitHub\satmarket; py -3 semina_demo.py
```

Deve rispondere sei righe, tutte con la spunta (i numeri cambiano col
cambio):

```
🌱 Semina della demo sul database di collaudo: C:\…\satmarket\satmarket.db
   ✓ negozio To The Mooon (nuovo): utente 444, codice 1b9a53e6 (dal catalogo del client), /negozio/tothemooon, npub npub12xql9gw…, avatar av_1b9a53e6_1.jpg
   ✓ insegna ban_1b9a53e6_1.jpg (stato attivo), link https://…
   ✓ NIP05_NOMI['tothemooon'] nel config combacia con la npub seminata
   ✓ annuncio #N «To The Mooon! — il gioco da tavolo che spiega Bitcoin» nuovo: 5.820 sats = 4,80 $ al cambio di 82.473 $/BTC letto dal server alle 09:30 del 16/10, ritiro a mano a Torino (TO), 2 foto
   ✓ cliente 111 c’era: pronto a comprare (identita' dall'hash: tgWebAppData=collaudo:111:Compratore)
   Rilanciabile: niente doppioni. L'ordine della mattina: `py -3 semina_demo.py ordine`.
```

Rilanciata dice «c’era» su ogni riga e «niente da ritoccare» (o
«ritoccato: prezzo 5.820 → 5.790 sats» se il cambio si è mosso: è il
punto). Se la seconda riga dice «NON combacia», la hex in `NIP05_NOMI`
del config non è quella di `node identita.mjs pubblica tothemooon`:
sistemare il config, non lo script. Se si ferma con «il server non ha
ancora letto un cambio $/BTC»: lasciarlo acceso un minuto con la rete e
rilanciare, o `py -3 semina_demo.py --cambio-usd 82473` col numero di
mempool/CoinGecko a mano. Se si ferma con «il database non ha lo schema
del server»: avviare Barattolo una volta su quel database (lo schema lo
fa lui, la semina non ne tiene una copia). `py -3 semina_demo.py stato`
racconta cosa c'è senza scrivere.

**L'insegna** (`banner_foto`, aggiunta il 9 ott): la semina la ritaglia
dal banner di «Da scoprire» (3:1 dalla cima, perché la scritta sta sul
bordo alto) e la mette in stato attivo, ma il client la mostra SOLO con
un link https al sito del negozio sotto (è l'uscita «Esci da
Barattolo?») e con `BANNER_NEGOZIO_ATTIVO = True` nel config di
collaudo (di serie è False, anche nell'esempio). Il sito del negozio
vero non sta scritto da nessuna parte e la semina non lo inventa: la
prima volta `py -3 semina_demo.py --insegna-link https://<sito del
negozio>`; il link resta in colonna e le semine dopo lo tengono. Finché
manca, la riga dell'insegna ha il ⚠️ e lo dice.

La controprova nel browser, identità 111 dall'hash (§11.2): aprire
`http://127.0.0.1:8080/negozio/1b9a53e6#tgWebAppData=collaudo:111:Compratore`
→ la vetrina di To The Mooon con l'insegna in cima (se link e leva ci
sono), la storia («Capire Bitcoin, giocando.»), il logo tondo nella
testata e sotto l'annuncio del gioco col prezzo;
nella home la ricerca «Mooon» lo trova e la card «Consigliati» della fila
delle categorie → To The Mooon! → lo stesso negozio (non più «Negozio
non trovato»). Anche `http://127.0.0.1:8080/negozio/tothemooon` apre lo
stesso negozio.

**L'ordine della mattina della demo** (domenica, §11.3: quello delle
13:30 e poi quello del vivo):

```powershell
py -3 semina_demo.py ordine
```

```
🧾 Ordine #N creato (cliente 111 → annuncio #N, 5.820 sats, ritiro a mano): stato «creato», non pagato, nessuna fattura in sats — payment_hash vuoto, il mietitore non lo tocca. Nato alle 13:02 del 18/10.
```

In «Ordini» di 111 compare «To The Mooon! …» come «Da pagare». Rilanciato
dice «c'è già» e NON ne fa un secondo: per il secondo ordine (quello del
vivo, dopo che il primo è stato pagato in USDB) `py -3 semina_demo.py
ordine --nuovo`. L'ordine nasce SENZA fattura in sats, deliberato: la
demo lo paga in USDB col foglio di sabato, e un ordine senza
`payment_hash` è fuori dalla rete del mietitore (`controlla_abbandonati`
guarda solo chi ne ha uno), quindi resta «creato» tutto il giorno. Il
rovescio, da sapere: il foglio «Paga ora» di OGGI su quell'ordine
bussa a LNbits per la fattura che non c'è, e nel log del server esce un
500 — innocuo, l'ordine non si muove; il foglio di sabato è un altro.

**Domenica 11 ott: Mutinynet coi servizi degli organizzatori — la lista
da spuntare** (studio del 9 ott, deciso con Alan; cantiere
«mutinynet-prep» del 9: il codice e questi testi). Il perché in quattro
righe: gli organizzatori dicono che tutti useranno Mutinynet (signet con
blocchi da 30 s, faucet BTC `https://faucet.mutinynet.com`, faucet RGB
`https://faucet.mutinynet.kaleidoswap.com`); su Mutinynet NON esiste un
Electrum pubblico, si usa l'Esplora di KaleidoSwap via https
(`https://esplora.signet.kaleidoswap.com`, riserva `https://mutinynet.com/api`
che ha dato 429 alla loro CI) e il proxy RGB pubblico
(`rpcs://proxy.kaleidoswap.com/json-rpc`, protocollo 0.2, versione 0.3.0
come il nostro container; riserva `rpcs://proxy.iriswallet.com/0.2/json-rpc`);
il blocco 0 di Mutinynet È quello del signet (verificato), quindi per
rgb-lib la rete resta `SIGNET` e cambiano solo indexer, proxy, link e
CARTELLE. Il signet della VM resta intatto: è il piano B, e ci si torna
non facendo `source`. Un NIA vive sulla catena dove nasce: USDB e MOON si
RIEMETTONO (id nuovi), il wallet utente è nuovo. I wallet di KaleidoSwap
aprono Mutinynet come `SignetCustom`: il wallet Utexo non lo sa fare, noi
restiamo `signet` fra di noi (vedi lo studio, punti 1, 2 e 7). Tutto dal
WSL, un comando per riga, con la risposta attesa dopo `# →`. Niente di
tutto questo tocca il VPS, il nodo o il relay.

☐ **0) I file sulla VM e nel WSL** (dopo `git pull` nel repo):

```bash
cd /mnt/c/Users/Andrea/Documents/GitHub/satmarket && scp -i ~/.ssh/lnvps deploy/rgb/rgb.py deploy/rgb/rgb_http.py deploy/rgb/backup-rgb.sh deploy/rgb/mutinynet-vm.env debian@vm-2050.lnvps.cloud:~/rgb/
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && mv mutinynet-vm.env mutinynet.env && sudo install -m 755 backup-rgb.sh /usr/local/sbin/backup-rgb.sh && rm backup-rgb.sh && grep -c "fotografa mutinynet" /usr/local/sbin/backup-rgb.sh'   # → 1
cp deploy/rgb/punti.mjs deploy/rgb/nwc-wdk.mjs deploy/rgb/identita.mjs ~/wdk-prova/ && cp deploy/rgb/mutinynet-wsl.env ~/wdk-prova/mutinynet.env && grep -c mutinynet ~/wdk-prova/mutinynet.env   # → un numero > 0
```

Il signet non cambia: senza `source` i tre script fanno quel che facevano
ieri (default `RGB_CATENA=signet`, le cartelle di sempre), e `rgb.py` si
RIFIUTA di aprire un wallet nato su una catena con l'ambiente dell'altra
(«il wallet «barattolo» è nato su signet, ma RGB_CATENA dice mutinynet»):
se lo vedi, manca o avanza un `source`.

☐ **1) I wallet nuovi, VM e WSL** (le cartelle `~/rgb/mutinynet/` e
`~/wdk-prova/mutinynet/utente/` nascono qui):

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'source ~/rgb/mutinynet.env && cd ~/rgb && for w in barattolo to-the-mooon usdb; do ./venv/bin/python rgb.py nuovo $w && ./venv/bin/python rgb.py indirizzo $w; done'   # → tre «✓ wallet «…» creato in /home/debian/rgb/mutinynet/… (catena mutinynet)» e tre indirizzi tb1p…
cd ~/wdk-prova && source mutinynet.env && source ~/.nvm/nvm.sh && node punti.mjs nuovo && node punti.mjs indirizzo   # → «✓ wallet utente creato in …/wdk-prova/mutinynet/utente (catena mutinynet)» e un tb1p…
```

`indirizzo` va in rete: è il primo contatto con l'Esplora di KaleidoSwap.
Se dice «Esplora error … 429» si rilancia con la riserva nella stessa
riga: `RGB_INDEXER=https://mutinynet.com/api ./venv/bin/python rgb.py …`.

☐ **2) Il faucet BTC** (browser, login GitHub su
`https://faucet.mutinynet.com`): 150.000 sat a ciascuno dei TRE indirizzi
della VM e 50.000 a quello del wallet utente — 500.000 in tutto, sotto
il tetto di 1.000.000 per utente/IP in 24 ore (Alan dallo stesso Wi-Fi
si somma). Un blocco: 30 secondi. Controllo: `rgb.py saldo barattolo`
(con `source`) dice i sats vanilla.

☐ **3) Gli UTXO colorabili** (un blocco dopo il faucet):

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'source ~/rgb/mutinynet.env && cd ~/rgb && for w in barattolo to-the-mooon usdb; do ./venv/bin/python rgb.py utxo $w 5; done'   # → tre «✓ creati 5 UTXO colorabili (una transazione mutinynet, aspetta una conferma)»
cd ~/wdk-prova && source mutinynet.env && source ~/.nvm/nvm.sh && node punti.mjs utxo 3   # → «✓ creati … UTXO colorabili (una transazione mutinynet)»
```

Se un `utxo` dice `InsufficientAllocationSlots` o «insufficient funds»,
il faucet non è ancora confermato: 30 secondi e si rilancia.

☐ **4) La riemissione** (nessuna transazione: il genesis vive su un UTXO
colorabile), poi SUBITO il backup — da qui lo stash vale:

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'source ~/rgb/mutinynet.env && cd ~/rgb && ./venv/bin/python rgb.py emetti usdb USDB Dollari_di_prova_Barattolo 100000000 2 && ./venv/bin/python rgb.py emetti to-the-mooon MOON "Punti To The Mooon" 1000000 && for w in barattolo to-the-mooon usdb; do ./venv/bin/python rgb.py backup $w; done'   # → «✓ emesso USDB …» con l'asset_id, «✓ emesso MOON …» con l'asset_id, tre backup in ~/rgb/backup-mutinynet
```

Il nome di MOON con gli spazi qui passa: siamo dentro `ssh` dal WSL, non
in PowerShell (lezione 1 di §9). I DUE asset_id si copiano: servono al
punto 5.

☐ **5) Gli id nuovi nei file** (li incolla la sessione, tu li dai):
`ASSET_PER_CATENA.mutinynet` di `deploy/rgb/identita.mjs` (al posto di
`INCOLLA_QUI_ID_MOON_MUTINYNET` e `INCOLLA_QUI_ID_USDB_MUTINYNET`, senza
`rgb:` davanti), la tabella di §2 qui sopra, la bozza
`docs/spec/NIP-RGB-ASSETS.md` dove cita gli id. La prova
`prove_annuncio_identita` accetta sia i segnaposto sia due ContractId
veri. Poi `cp deploy/rgb/identita.mjs ~/wdk-prova/`. Controllo senza
relay: `cd ~/wdk-prova && source mutinynet.env && node identita.mjs
annuncio --prova tothemooon rgb:<id di MOON>` → l'evento in JSON, `d` =
l'id nudo, il content dice «RGB (Mutinynet, il signet dell'hackathon)».

☐ **6) Gli asset al wallet utente e al mercante** (come l'8 ott, §3 e
§10: la prima fattura è «qualunque asset», blind perché il wallet ha già
3 UTXO colorabili): 50.000 unità di USDB (500,00) e 60 MOON all'utente,
100 unità di USDB (1,00) al wallet `barattolo` perché conosca l'asset
prima di fare fatture PER asset (lezione 5). Le fatture portano il proxy
PUBBLICO: non serve più il tunnel per il proxy.

```bash
cd ~/wdk-prova && source mutinynet.env && source ~/.nvm/nvm.sh && node punti.mjs fattura - 50000   # → la fattura rgb:… (la riga che comincia con rgb:)
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'source ~/rgb/mutinynet.env && cd ~/rgb && ./venv/bin/python rgb.py invia usdb <id di USDB> 50000 "<la fattura>"'   # → «✓ consignment depositato sul proxy (blind), txid …» e il link https://mutinynet.com/tx/…
cd ~/wdk-prova && source mutinynet.env && node punti.mjs aggiorna   # → l'ACK dell'utente
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'source ~/rgb/mutinynet.env && cd ~/rgb && ./venv/bin/python rgb.py aggiorna usdb'   # → «trasferimento …: WAITING_CONFIRMATIONS» (trasmessa); al blocco, settled
```

Lo stesso giro con `node punti.mjs fattura - 60` e `rgb.py invia
to-the-mooon <id di MOON> 60 "…"`; poi per il mercante la fattura la fa
`rgb_http.py` (punto 7, `curl -s -X POST 127.0.0.1:8787/fattura -d
'{"quantita": 100}'`) e la paga `rgb.py invia usdb <id di USDB> 100 "…"`,
ACK con `curl -s -X POST 127.0.0.1:8787/aggiorna -d '{}'`, `rgb.py aggiorna
usdb`. Controllo finale: `node punti.mjs saldo` → USDB 50.000 e MOON 60
settled; `rgb.py saldo barattolo` → 100 unità di USDB.

☐ **7) La faccia HTTP del mercante, sull'ambiente giusto**, e il tunnel a
UNA gamba:

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'cd ~/rgb && pkill -f "[r]gb_http.py"; source mutinynet.env && nohup ./venv/bin/python rgb_http.py > rgb_http.log 2>&1 & sleep 2; head -1 ~/rgb/rgb_http.log'   # → «🟪 rgb_http su 127.0.0.1:8787, wallet «barattolo» su mutinynet»
ssh -i ~/.ssh/lnvps -N -L 8787:127.0.0.1:8787 debian@vm-2050.lnvps.cloud   # finestra 1 del WSL, resta aperta
curl -s 127.0.0.1:8787/salute   # → {"ok": true, "wallet": "barattolo", "rete": "mutinynet"}
```

Se `/salute` dice `"rete": "signet"`, `rgb_http.py` è partito senza il
`source`: fermarlo e rilanciare la prima riga.

☐ **8) Il servizio NWC sul wallet di Mutinynet** (stessa chiave, stessa
connection string: il Profilo di Barattolo resta collegato; cambia solo
il wallet che apre):

```bash
cd ~/wdk-prova && source mutinynet.env && source ~/.nvm/nvm.sh && (pgrep -fa "[n]ak serve" || (setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown)); pkill -f "[n]wc-wdk.mjs serve"; setsid nohup node nwc-wdk.mjs serve > nwc/serve.log 2>&1 < /dev/null & disown
sleep 2 && head -2 ~/wdk-prova/nwc/serve.log && node nwc-wdk.mjs prova barattolo   # → «🟪 servizio NWC …», poi get_info ok (alias «WDK Barattolo (prova, mutinynet)», network signet), get_balance coi sats del wallet di Mutinynet, rgb_list_assets → NOT_IMPLEMENTED
```

☐ **9) Il backup a due catene**, a mano, e il pull dal PC:

```bash
ssh -i ~/.ssh/lnvps debian@vm-2050.lnvps.cloud 'pkill -f "[r]gb_http.py"; sudo systemctl start rgb-backup.service; sudo journalctl -u rgb-backup.service -n 12 --no-pager | grep -E "wallet:|rgb/mutinynet|backup-mutinynet"'   # → «wallet: signet/barattolo signet/to-the-mooon signet/usdb mutinynet/barattolo mutinynet/to-the-mooon mutinynet/usdb» e le righe rgb/mutinynet/… e rgb/backup-mutinynet/…
```

Poi `pull.ps1` dal PC e il drill `age -d -i rgb-prova.key <archivio> |
tar -t | grep mutinynet` → i tre `chiavi.json` e le tre fotografie di
Mutinynet. Il wallet utente: `node punti.mjs backup` (con `source`:
finisce in `~/wdk-prova/mutinynet/backup`), poi `tar | age -r <pubblica
age della VM>` come l'8, copia in `BarattoloBackup\rgb\`. Riaccendere
`rgb_http.py` (punto 7, prima riga).

☐ **10) Gli annunci del 16** restano quelli di §10 punto 4) e §11.1, con
`source ~/wdk-prova/mutinynet.env` PRIMA (il tag `n` resta `signet`: la
bozza non distingue i signet fra loro, e il ContractId identifica già il
contratto) e i due id nuovi al posto di quelli di signet. La semina
(§10 punto 5) non cambia: non porta asset_id. I numeri della demo
(§11.2) non cambiano. Da qui in avanti, OGNI comando della demo comincia
con `source …/mutinynet.env`: è nelle righe di §6.

**Come si torna al signet in cinque minuti** (se Mutinynet o i servizi
di KaleidoSwap sono giù il 17-18, §11.4): nessun `source`, il tunnel a
tre gambe di §1, `rgb_http.py` rilanciato senza `source` → `/salute` dice
`signet`, il servizio NWC rilanciato senza `source` apre il wallet di
`~/wdk-prova/utente`, gli id di §2 (prima tabella) nel config di
Barattolo al posto di quelli di Mutinynet. I wallet signet sono intatti:
nessuno li ha più toccati dall'8.

**15 ott, i due portatili di Alan, a casa di Andrea, con la rete**
(cambio del 9 ott: niente installazione in sala). Sono DUE Linux a base
Ubuntu — **Pop!_OS 32 GB** (il portatile principale della demo di Alan,
grafica Intel Arc, niente NVIDIA) e **ZorinOS 16 GB** (la riserva,
installato uguale) — e su ognuno si lavora in un **utente Linux
dedicato `hackathon`**: tutto nella SUA home (nvm e Node, `~/wdk-prova`,
`~/qvac-prova`, `~/.qvac/models`, `~/rgb-venv`, `~/bin/nak`), a livello
di sistema SOLO i pacchetti apt e i gruppi `render,video`. Sono la
riserva del portatile di Andrea (§1) per tutto TRANNE il wallet della
demo: lo stash di rgb-lib vive in UN posto solo («never instantiate a
wallet in multiple places», §3), quindi su ciascuno nasce un wallet di
PROVA vuoto, che serve a scrivere i metodi `rgb_*` il sabato senza
toccare quello vero. Le versioni sono quelle del PC di Andrea l'8 ott.
Un comando per riga, nell'ordine; dove c'è `# →` c'è quel che deve
rispondere. I punti 1-9 con la rete, il 10 col Wi-Fi spento. La
chiavetta (`chiavetta-prepara.sh` / `install-offline.sh`, in fondo) è la
RISERVA: se il 15 la rete fa i capricci, o per rifare lo Zorin.

0) **Prima di tutto, la glibc** (dall'utente di Alan, prima di creare
`hackathon`): il binario Utexo del wallet (`librgblibcffi.so` dentro
`@utexo/rgb-lib-linux-x64@0.3.0-beta.8`, quello che `wdk-wallet-rgb
2.0.3` pretende via `@utexo/rgb-sdk 1.0.3`) vuole **glibc ≥ 2.38**: su
una base Ubuntu 22.04 (glibc 2.35: Pop!_OS 22.04, Zorin OS 17) l'import
muore con «GLIBC_2.38 not found» (visto il 9 ott in un container
jammy). Su una base 24.04 (glibc 2.39: Pop!_OS 24.04, Zorin OS 18) gira
com'è.

```bash
ldd --version | head -1 && cat /etc/os-release | grep -E "^(PRETTY_NAME|UBUNTU_CODENAME)"   # → glibc 2.39 e «noble»: variante ORIGINALE (punto 3a); glibc 2.35 e «jammy»: variante OVERRIDE (punto 3b)
```

La variante override: `@utexo/rgb-sdk 1.0.6` pinna il binario
`0.3.0-beta.13`, che si ferma a glibc 2.34, e con un `overrides` in
`package.json` `wdk-wallet-rgb 2.0.3` ci gira sopra — **provato il 9 ott
su Ubuntu 22.04**: import, `nuovo`, `indirizzo`, `saldo` via l'Esplora
di KaleidoSwap. ATTENZIONE: la 1.0.6 deriva le chiavi con un altro
keychain (`vanillaKeychain` 0 e non 1): un wallet nato con l'una NON è
lo stesso wallet con l'altra. Va bene per il wallet di PROVA di Alan,
MAI per quello della demo, che resta sul PC di Andrea con la variante
originale.

1) **L'utente `hackathon` e i pacchetti di sistema** (dall'utente di
Alan, con sudo): `build-essential` serve a node-gyp per il binding del
wallet (§3), `libatomic1` a QVAC anche in CPU, `libvulkan1
mesa-vulkan-drivers vulkan-tools` all'Arc via Vulkan, `python3-venv`
alla ruota rgb-lib.

```bash
sudo apt update && sudo apt install -y build-essential python3 python3-venv python3-pip git curl tar xz-utils libatomic1 libvulkan1 mesa-vulkan-drivers vulkan-tools
sudo adduser --gecos "Hackathon Torino" hackathon && sudo usermod -aG render,video hackathon && id hackathon   # → … groups=…,render,video
```

Poi **logout e login grafico come `hackathon`** (QVAC e il browser
vogliono una sessione sua; `su - hackathon` basta per i comandi, non
per la prova finale). Tutto quel che segue è da `hackathon`.

2) **Node 22 via nvm, e Node 24 per QVAC** (QVAC vuole ≥ 22.17; `qvac
doctor` sul PC di Andrea ha chiesto il 24):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.nvm/nvm.sh && nvm install 22.23.3 && nvm alias default 22.23.3 && nvm install 24 && nvm use default && node -v   # → v22.23.3
```

3) **I pacchetti del wallet e di Nostr**, nella stessa cartella e con le
stesse versioni del PC di Andrea; il binario `@utexo/rgb-lib-linux-x64`
NON entra da solo (lezione di §3) e si installa a mano. Gli script
arrivano da `deploy/rgb/` del repo di Barattolo (il clone del punto 7,
o la chiavetta).

3a) variante ORIGINALE (glibc ≥ 2.38):

```bash
mkdir -p ~/wdk-prova && cd ~/wdk-prova && npm init -y > /dev/null
npm install @utexo/wdk-wallet-rgb@2.0.3 nostr-tools@2.25.2 bip39@3.1.0
npm install @utexo/rgb-lib-linux-x64@0.3.0-beta.8
npm ls --depth=0   # → @utexo/wdk-wallet-rgb@2.0.3, @utexo/rgb-lib-linux-x64@0.3.0-beta.8, nostr-tools@2.25.2, bip39@3.1.0
```

3b) variante OVERRIDE (glibc 2.34-2.37, base 22.04):

```bash
mkdir -p ~/wdk-prova && cd ~/wdk-prova && npm init -y > /dev/null
node -e "const p=require('./package.json'); p.overrides={'@utexo/rgb-sdk':'1.0.6'}; require('fs').writeFileSync('package.json', JSON.stringify(p,null,2)+'\n')"
npm install @utexo/wdk-wallet-rgb@2.0.3 nostr-tools@2.25.2 bip39@3.1.0
npm install @utexo/rgb-lib-linux-x64@0.3.0-beta.13
npm ls --all 2>/dev/null | grep -E "rgb-sdk|rgb-lib-linux"   # → @utexo/rgb-sdk@1.0.6 overridden, @utexo/rgb-lib-linux-x64@0.3.0-beta.13
```

(Nella variante override `node punti.mjs indirizzo` stampa un oggetto
con l'indirizzo dentro, non la sola stringa: la 1.0.6 risponde così. Il
resto dei comandi è uguale.)

Poi, in tutt'e due le varianti:

```bash
cp <clone di satmarket>/deploy/rgb/{punti.mjs,nwc-wdk.mjs,identita.mjs} ~/wdk-prova/ && cp <clone di satmarket>/deploy/rgb/mutinynet-wsl.env ~/wdk-prova/mutinynet.env
cd ~/wdk-prova && node -e "import('@utexo/wdk-wallet-rgb').then(()=>console.log('modulo RGB ok'))"   # → modulo RGB ok (se dice GLIBC_2.38 not found: variante sbagliata, punto 0)
```

4) **`nak`** (il relay locale e l'attrezzo per Nostr), lo stesso binario
del PC di Andrea: la release v0.21.0 di fiatjaf, `linux-amd64`, in
`~/bin` (che su Pop e Zorin entra nel PATH al login successivo; subito:
`export PATH=$HOME/bin:$PATH`).

```bash
mkdir -p ~/bin && curl -L -o ~/bin/nak https://github.com/fiatjaf/nak/releases/download/v0.21.0/nak-v0.21.0-linux-amd64 && chmod +x ~/bin/nak
~/bin/nak --version   # → nak version v0.21.0
```

5) **QVAC**, dipendenza LOCALE di `~/qvac-prova` con Node 24 (comando
`npx qvac …`, mai `qvac` nudo), il `qvac.config.json` di `deploy/rgb/`
(gli alias `consigliami` → Qwen3 1.7B e `qwen3-600m-inst-q4` → Qwen3
0.6B), e `consiglio.py` accanto:

```bash
source ~/.nvm/nvm.sh && nvm use 24 && mkdir -p ~/qvac-prova && cd ~/qvac-prova && npm init -y > /dev/null && npm install @qvac/sdk@0.21.0 @qvac/cli@0.15.0 && npx qvac --version   # → 0.15.0
cp <clone di satmarket>/deploy/rgb/qvac.config.json <clone di satmarket>/deploy/rgb/consiglio.py ~/qvac-prova/ && npx qvac doctor   # → tutto verde (controlla Node, RAM, disco, host: NON la GPU)
```

**L'Arc e Vulkan.** Su Linux QVAC fa inferenza in GPU solo via **Vulkan
≥ 1.4** (docs: «Vulkan is required for GPU inference. If not available,
it falls back to CPU»); con Intel/AMD passa da Mesa (`libvulkan1
mesa-vulkan-drivers`, punto 1) e vuole l'utente nei gruppi `render,video`
(punto 1). Mesa dà Vulkan 1.4 su ANV (Intel) dalla 24.3: Pop!_OS 24.04 e
Zorin 18 ce l'hanno, una base 22.04 è alla 1.3 e QVAC va in CPU — che
per noi basta (sotto). Il controllo:

```bash
vulkaninfo --summary | grep -E "apiVersion|deviceName|driverName"   # → deviceName «Intel(R) Arc…», driverName «intel» (ANV), apiVersion 1.4.x → GPU; 1.3.x → CPU
```

Se vuoi il 1.4 su una base 22.04: `sudo add-apt-repository
ppa:kisak/kisak-mesa && sudo apt upgrade`, solo con `ppa-purge` a
portata di mano — su un portatile da demo, meglio la CPU. I tempi,
STIME (QVAC non pubblica numeri; esperienza llama.cpp su un portatile
recente): Qwen3 1.7B Q4 in CPU 15-25 token/s in uscita, 0.6B 40-60; la
nostra richiesta (circa 400 token dentro, 80 fuori) sta in 3-5 s col
1.7B e 1-2 s col 0.6B, più 10-20 s la prima volta per caricare il
modello. Con l'Arc su Vulkan si guadagna forse un fattore 2: comodo, non
necessario. Si misura il 15 dal campo `usage` della risposta e da un
cronometro.

6) **I due modelli, già scaricati.** La strada corta (1,4 GB da
chiavetta, nessun download): copiare dal PC di Andrea
`C:\Users\Andrea\.qvac\models` (i due `.gguf`: Qwen3 0.6B Q4_0 da 382 MB
e Qwen3 1.7B Q4_0 da 1,06 GB, coi loro prefissi) in `~/.qvac/models`
(stesso percorso e stessi nomi su Linux). L'alternativa con la rete (la
CLI non ha un comando «scarica»): il primo avvio con i due alias, che li
scarica subito — provato l'8 ott sera sul PC di Andrea:

```bash
cd ~/qvac-prova && source ~/.nvm/nvm.sh && nvm use 24 && npx qvac serve --openai --port 11434 --host 127.0.0.1 --model consigliami --model qwen3-600m-inst-q4   # scarica, poi resta in ascolto: Ctrl-C quando dice che serve
ls -la ~/.qvac/models   # → *_Qwen3-0.6B-Q4_0.gguf e *_Qwen3-1.7B-Q4_0.gguf
```

Il primo `serve` dice nel log quale device ha scelto (`gpu` o `cpu`):
è la controprova del punto 5. Per forzare la CPU nel confronto:
`"device": "cpu"` nel `config` dell'alias in `qvac.config.json`.

7) **Python rgb-lib**, la stessa ruota della VM (`rgb-lib==0.3.0b7`,
`manylinux_2_34`: va su 22.04 e 24.04), in un venv; e i due cloni
(`fidelity-points` è privato: Alan è collaboratore, `gh auth login`
dall'utente `hackathon` o la sua chiave SSH):

```bash
python3 -m venv ~/rgb-venv && ~/rgb-venv/bin/pip install --quiet rgb-lib==0.3.0b7 && ~/rgb-venv/bin/python -c "import rgb_lib; print('rgb-lib ok')"   # → rgb-lib ok
cd ~ && gh repo clone kreamistudio-crypto/fidelity-points && git -C ~/fidelity-points log --oneline | head -3   # → af445f7, 06422bf, 1e6fa80
cd ~ && git clone https://github.com/kreamistudio-crypto/satmarket.git && cd satmarket && python3 -m venv .venv && .venv/bin/pip install --quiet fastapi uvicorn httpx websocket-client pillow cryptography && .venv/bin/python -c "import fastapi, uvicorn, httpx; print('server ok')"   # → server ok (su Linux il server gira da qui: .venv/bin/python -m uvicorn server:app --port 8080)
```

8) **Le identità e la pagina dell'aiutante, dal PC di Andrea, su
chiavetta** — mai in chat, mai in un canale Telegram. L'archivio
`identita-nwc-20261008.tar.age` (§11) si apre SOLO con la chiave
segreta age della VM, che apre anche i backup dello stash: quella NON
si copia. Andrea lo apre sul suo PC in una cartella temporanea
(`age -d -i rgb-prova.key … | tar -x`), mette su chiavetta la sola
cartella `identita/` (i due `.json`, 0600: sono chiavi di PROVA, non
della piattaforma) e `consigliami-prova.html` da
`C:\Users\Andrea\qvac-prova\`, e dopo la copia svuota la cartella e la
chiavetta. Da `hackathon`:

```bash
mkdir -p ~/wdk-prova/identita && cp /media/hackathon/<chiavetta>/identita/*.json ~/wdk-prova/identita/ && chmod 700 ~/wdk-prova/identita && chmod 600 ~/wdk-prova/identita/*.json
cd ~/wdk-prova && node identita.mjs pubblica usdb && node identita.mjs pubblica tothemooon   # → le due npub di §11
cp /media/hackathon/<chiavetta>/consigliami-prova.html ~/qvac-prova/
```

9) **Il wallet di PROVA vuoto** (NON quello della demo), su Mutinynet
come tutto il resto dal 11: la sua frase nasce lì e resta lì.

```bash
cd ~/wdk-prova && source mutinynet.env && node punti.mjs nuovo && node punti.mjs indirizzo   # → «✓ wallet utente creato in …/wdk-prova/mutinynet/utente (catena mutinynet)» e un indirizzo tb1p…
```

(Il faucet, se si vuole qualche sat sul wallet di prova: 50.000 da
`https://faucet.mutinynet.com`, login GitHub di Alan.)

10) **La prova finale, col Wi-Fi SPENTO**: ogni riga deve rispondere
senza scaricare niente. Se una riga prova a scaricare, in sala
sull'hotspot non partirebbe.

```bash
cd ~/wdk-prova && source ~/.nvm/nvm.sh && node -v && npm ls --depth=0   # → v22.23.3 e i quattro pacchetti (nella variante override: @utexo/rgb-sdk@1.0.6 overridden sotto)
(setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown) && sleep 2 && source mutinynet.env && node identita.mjs annuncio --prova tothemooon rgb:<id di MOON su Mutinynet, §2> | head -3   # → l'evento firmato, kind 38180
node nwc-wdk.mjs info   # → la chiave pubblica del servizio e il relay locale
~/rgb-venv/bin/python -c "import rgb_lib; print('rgb-lib ok')"
cd ~/qvac-prova && source ~/.nvm/nvm.sh && nvm use 24 && npx qvac serve --openai --port 11434 --host 127.0.0.1 --cors-origin http://127.0.0.1:8081
```

e in un secondo terminale `python3 -m http.server 8081` in
`~/qvac-prova`, poi `http://127.0.0.1:8081/consigliami-prova.html` nel
browser: «Consigliami» risponde col 1.7B senza scaricare niente (la
prima chiamata carica il modello: ~20 s in CPU; la seconda pochi
secondi). Sul portatile di Alan NON stanno: il wallet della demo (seme e
stash), le chiavi SSH della VM, la segreta age, il `.env` della VM, il
config di Barattolo. Lo Zorin si installa UGUALE, dopo: è la copia.

**La chiavetta di riserva** (`deploy/rgb/chiavetta-prepara.sh` e
`install-offline.sh`, scritti il 9 ott e PROVATI in due container WSL —
Ubuntu 22.04 e 24.04 — la preparazione con la rete e l'installazione
in una distro pulita con la rete STACCATA con `unshare -n`). Serve se
il 15 la rete fa i capricci, per rifare lo Zorin, o se un portatile va
reinstallato. La prepara il PRIMO portatile finito (il Pop!_OS, da
`hackathon`, col Wi-Fi): compila lì il `node_modules` del wallet (la
variante giusta per la sua glibc: una chiavetta preparata su 22.04 va
anche su 24.04, non il contrario) e copia il resto.

```bash
bash ~/satmarket/deploy/rgb/chiavetta-prepara.sh /media/hackathon/<chiavetta>   # → le ✓ di node, wallet, qvac, modelli, ruote, nak, script, deb, e «📦 …/torino: 2,5G»
```

Cosa c'è dentro `<chiavetta>/torino/` (2,5 GB), col `MANIFEST.txt`
(versioni, glibc della macchina che ha preparato, sha256 di ogni file):

| Cartella | Contenuto | Da dove |
|---|---|---|
| `node/` | `node-v22.23.3-linux-x64.tar.xz` e `node-v24.<ultima>-linux-x64.tar.xz` (sha256 verificate) | nodejs.org |
| `wdk-prova/` | `node_modules.tar.gz` (`@utexo/wdk-wallet-rgb@2.0.3`, `nostr-tools@2.25.2`, `bip39@3.1.0`, il binario `@utexo/rgb-lib-linux-x64` beta.8 o beta.13 GIÀ COMPILATO, `package.json` e lock) e `versioni.txt` con la variante | `npm install` sulla macchina che prepara |
| `qvac-prova/` | `node_modules.tar.gz` (`@qvac/sdk@0.21.0`, `@qvac/cli@0.15.0`) e `versione.txt` | `npm install` con Node 24 |
| `modelli/` | i due `.gguf` di Qwen3 (0.6B e 1.7B Q4_0) | `~/.qvac/models` (o `--modelli-da DIR`) |
| `wheels/` | `rgb_lib-0.3.0b7-py3-none-manylinux_2_34_x86_64.whl` e la ruota di `pip` (per installare SENZA `python3-venv`: `venv --without-pip` + `pip` dalla ruota) | PyPI (senza pip: curl + il JSON di PyPI) |
| `nak/` | `nak` v0.21.0 linux-amd64 | le release di fiatjaf |
| `script/` | `punti.mjs`, `nwc-wdk.mjs`, `identita.mjs`, `consiglio.py`, `qvac.config.json`, `mutinynet-wsl.env`, `install-offline.sh` | `deploy/rgb/` |
| `deb/` | riserve jammy: `libatomic1`, `libvulkan1`, `vulkan-tools`, `python3-venv` (si installano SOLO con `--con-deb`) | `apt-get download` |

E sull'altro portatile, senza rete, da `hackathon`:

```bash
bash /media/hackathon/<chiavetta>/torino/script/install-offline.sh --prova /media/hackathon/<chiavetta>/torino   # → le ✓ «chiavetta: …» e «✓ la chiavetta e' completa»
bash /media/hackathon/<chiavetta>/torino/script/install-offline.sh /media/hackathon/<chiavetta>/torino   # → le ✓ di glibc, node 22 e 24, ~/wdk-prova, nak, ~/qvac-prova, modelli, ~/rgb-venv, e «✓ tutto installato»
```

Installa SOLO sotto `$HOME` (Node in `~/.local/node/22` e `/24` con le
funzioni `node22`/`node24` in `~/.bashrc`, il resto nelle stesse
cartelle del punto 3-9), niente nvm; `sudo` solo con `--con-deb`. La
funzione `node22` imposta anche `LD_LIBRARY_PATH` sulla cartella di
`librgblibcffi.so`: il binding compilato da node-gyp porta un RUNPATH
assoluto alla cartella temporanea di chi l'ha compilato (letto con
`readelf` il 9 ott), e senza quella variabile l'import dice
«librgblibcffi.so: cannot open shared object file» — è successo al primo
giro nei container, ed è il motivo per cui il modulo RGB va provato
dopo un terminale NUOVO. Poi la prova finale del punto 10 (con `node24`
al posto di `nvm use 24`).
Non copia identità e `consigliami-prova.html`: quelle restano il punto
8, a mano.

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
  `tothemooon@barattolo.store`. La `picture` (il logo del negozio, già
  in `assets/consigliati/` e servito dal sito) si aggiunge il 16 con
  `identita.mjs profilo <nome> <https://…/logo>` (argomento aggiunto il
  9 ott, solo https; senza, il kind 0 resta quello dell'8): è la riga
  in §11.1. Su un relay pubblico SOLO
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

### 11.1 Il 16 ott: come si lancia (un comando per riga)

I comandi stanno per intero in §10, punto 4), con quel che ogni riga
deve rispondere. In breve, dal WSL, dopo la prova di riavvio:

```bash
cp /mnt/c/Users/Andrea/Documents/GitHub/satmarket/deploy/rgb/identita.mjs ~/wdk-prova/identita.mjs
cd ~/wdk-prova && source ~/.nvm/nvm.sh && (pgrep -fa "[n]ak serve" || (setsid nohup ~/bin/nak serve --port 7777 > ~/wdk-prova/nak.log 2>&1 < /dev/null & disown))
node identita.mjs annuncio --prova usdb rgb:H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A
node identita.mjs annuncio usdb rgb:H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A
node identita.mjs annuncio --prova tothemooon rgb:9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM
node identita.mjs annuncio tothemooon rgb:9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM
node identita.mjs profilo tothemooon https://barattolo.store/assets/consigliati/to-the-moon.webp
```

L'ultima riga (9 ott) rifà il kind 0 di `tothemooon` con la `picture`
— il logo già in `assets/consigliati/`, servito dal sito — e deve
rispondere «✓ kind 0 di «tothemooon» (tothemooon@barattolo.store, con
picture) pubblicato su ws://127.0.0.1:7777»; `usdb` resta senza (non ha
un logo). Poi la riga di rilettura di §10 (nostr-tools): USDB e MOON, autori le
due hex di `pubblica`. Cosa pubblica ogni identità, e con quale kind:
`usdb` UN evento kind 38180 (segnaposto) con `d` =
`H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A` (USDB, precision 2,
supply 100000000); `tothemooon` UN evento kind 38180 con `d` =
`9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM` (MOON, precision 0,
supply 1000000). Nient'altro: niente kind 0 nuovo (c'è dall'8), niente
kind 1, niente raccomandazione (3xxxx+1: non è prevista per il 16).
Sul relay LOCALE, mai su uno pubblico.

### 11.2 La demo di domenica, schermata per schermata

Il pitch è alle 15:00/16:00 di domenica (D.2); il build chiude alle
15:00. Due persone, due ruoli — **da confermare fra voi**, qui la
proposta: **Alan parla** (le slide, il racconto di G.4) e **Andrea tocca**
(il portatile della demo, e dice ad alta voce quel che fa nei passi dal
vivo). Sul tavolo: il portatile di Andrea proiettato, con TRE finestre
visibili — il browser su Barattolo in collaudo (`http://127.0.0.1:8080`,
identità 111 dall'hash, il cliente), il terminale del servizio NWC
(`nwc-wdk.mjs serve`: è lì che «l'utente firma») e il terminale di
`qvac serve` (le richieste che arrivano: l'AI è qui, non in rete); in
una scheda a parte `https://mutinynet.com` (l'esploratore di Mutinynet)
con le tx già confermate. Il portatile di Alan con le slide e il video
di riserva. Il giro dal vivo usa un ordine già creato la mattina
(`creato`, non pagato: lo crea `py -3 semina_demo.py ordine`, §10 punto
5). Con Mutinynet (blocchi da 30 s, dal 9 ott) il blocco del pagamento
dal vivo arriva IN SALA, entro un minuto: il secondo ordine, quello delle
13:30, resta come RISERVA se la rete inciampa e diventa il posto dove si
vede il livello 1 dell'autorizzazione (sotto).

**I numeri della demo, fissati il 9 ott** (studio Mutinynet, punti 11 e
13; se cambiano, cambiano qui, nelle slide e nel codice del sabato
insieme): il gioco costa **4,80 USDB**; la **soglia 3 USDB** per
pagamento e **20 USDB al giorno** è quella che il cliente ha messo nel
suo wallet (il
livello 1 di `docs/spec/NWC-RGB.md`); i punti sono **MOON**, un punto per
dollaro intero, 1 MOON = 1 sat di sconto, **max 20 %** del prezzo; il
premio del negozio è **☕ Caffè gratis = 25 MOON**, riscatto automatico
armato (livello 0); l'**ordine delle 13:30** è da **2,50 USDB** (sotto
soglia: pagato da solo, livello 1, e porta **+2 MOON**); la sequenza dei
MOON del cliente: 60 dall'8 ott, **62** la domenica dopo il bonus delle
13:30, **22** dopo i 40 spesi dal vivo, **27** col **bonus +5**, **2**
dopo il riscatto automatico del caffè — il premio scatta QUANDO ARRIVA
IL BONUS, non prima (22 < 25 ≤ 27): è la catena di tre eventi che
Mutinynet rende visibile in sala. Per questo «riscatta da solo» si
ACCENDE in scena, al passo 7, mentre si aspetta il blocco (un tocco,
detto ad alta voce): armato la mattina, con 62 MOON, scatterebbe subito.
Tre livelli, zero scene in più: il pagamento dal vivo (4,80 > 3) è il
livello 2 e chiede «Approva»; la ricevuta delle 13:30 è il livello 1; il
caffè è il livello 0.

| # | Schermata (cosa si vede) | Chi tocca cosa | Chi parla, e cosa dice |
|---|---|---|---|
| 1 | Slide 1 (chi siamo) | — | Alan, i 30 secondi di D.2: Barattolo, il mercatino in sats in produzione dal 10 ott; oggi i punti fedeltà fatti bene |
| 2 | Slide 2 (il problema) e, accanto, la card grigia «⚠️ Emittente sconosciuto» (screenshot) | — | Alan: «i punti oggi sono una riga nel database del negozio: non sono tuoi, non si portano via; e un token su una chain può chiamarsi come vuole, anche USDT, senza che nessuno sappia chi l'ha emesso» |
| 3 | Barattolo: la vetrina di **To The Mooon** (il negozio di prova) e un suo annuncio; nella scheda di mempool la tx di emissione di MOON | Andrea apre la vetrina e l'annuncio | Alan: «il negozio emette i suoi punti come token RGB su Bitcoin — MOON, un punto per euro — e firma l'annuncio con la sua identità Nostr, verificata da `tothemooon@barattolo.store`». Andrea: «questo è il negozio, questo l'articolo» |
| 4 | Profilo → Incassi e pagamenti → 👛 Wallet NWC: «wallet collegato», coi metodi `rgb_*` nell'elenco; il terminale del servizio NWC accanto | Andrea apre il Profilo e indica il terminale | Alan: «il cliente ha un wallet SUO, WDK di Tether col modulo RGB, self-custodial, sul portatile: Barattolo gli parla con NWC-RGB, un NWC su WDK, e non tiene nessuna chiave»; qui la **dichiarazione** in una riga: «la VM, gli asset, il wallet e il servizio base esistevano venerdì, dichiarati; tutto il resto è di questo weekend» |
| 5 | «🔒 Compra in sicurezza» sull'annuncio → **il foglio del pagamento**: il conto in sats, «oppure 4,80 USDB» col cambio dichiarato; la card **USDB · Dollari di prova** con «hai 500,00 USDB» e la riga «✓ Emesso da Dollari di prova (usdb@barattolo.store)»; sotto la card **MOON** con «hai 60 MOON» e «✓ Emesso da To The Mooon (tothemooon@barattolo.store)» | Andrea tocca «Compra», poi la riga dell'emittente di MOON | Andrea: «la riga non è un'etichetta: l'annuncio è firmato dalla chiave del negozio, e il nome lo conferma il suo dominio». Il dettaglio si apre: ContractId intero, «confronto con l'annuncio: combacia», il link all'evento, la data (16 ott). Alan: «dominio intero, mai abbreviato: NIP-05 identifica, il genesis decide» |
| 6 | Il bottone **«Consigliami»** → il fumetto: «paga 4,80 USDB e usa 40 MOON (40 sats di sconto): ti restano 495,20 USDB e 20 MOON. Motivo: …», con «Approva» e «No, pago in sats», e sotto in piccolo la regola («max 20% in punti»); nel terminale di QVAC la richiesta appena arrivata | Andrea tocca «Consigliami» | Andrea: «l'AI gira su questo portatile, Qwen3 1.7B con QVAC: la pagina le passa i numeri già calcolati e le chiede una scelta dentro la regola; i numeri li scrive il programma, lei la frase». Alan: «propone, non paga: filone 04, "local AI that proposes, you approve"» |
| 7 | **«Approva»** → nel terminale del servizio NWC la riga della policy («4,80 USDB sopra la soglia di 3: chiedo») e la conferma del wallet («pagare 480 unità di USDB a …? s/N», poi i 40 MOON, che passano da soli: punti); il foglio passa a «**Pagamento in arrivo · in attesa del blocco**» col link a mutinynet.com; la riga «pagamento diretto, senza deposito di garanzia» | Andrea tocca «Approva», poi nel terminale scrive `s` (una volta); poi, mentre si aspetta il blocco, apre il premio «☕ Caffè gratis · 25 MOON» nella vetrina e accende «riscatta da solo» | Andrea: «il wallet chiede a me, non a Barattolo: è la mia chiave, e la soglia l'ho messa io nel wallet. E intanto armo il caffè: appena ho 25 punti, se lo prende da solo». Alan: «la tx è su Mutinynet adesso; il blocco arriva in trenta secondi, e intanto vi mostro quello di stamattina» |
| 8 | L'ordine delle 13:30, già confermato: «**Pagato in USDB ✓**» con la riga «pagato da solo: 2,50 USDB sotto la tua soglia di 3 (2,50 di 20 oggi)», il txid, e sotto «**+2 MOON da To The Mooon** — arrivati»; la card MOON nel Profilo | Andrea apre Ordini → l'ordine delle 13:30 | Alan: «sotto una soglia che decide il cliente il wallet paga da solo e lo dice: è il livello 1; sopra, chiede: è quello che avete appena visto. I punti arrivano nel SUO wallet, non in un database» |
| 8-bis | Il foglio del passo 7 torna: il blocco c'è, «**Pagato in USDB ✓**», «**+5 MOON** — arrivati»; e sotto, da sola, la notifica «☕ **Caffè gratis riscattato**: 25 MOON → To The Mooon, ritiro al banco col codice dell'ordine» (il premio armato al passo 7); nel terminale del wallet la riga «25 MOON al negozio: punti, livello 0, nessuna domanda» | Andrea torna al foglio (il blocco è arrivato durante la scena 8) | Alan: «ha pagato in dollari, ha speso 40 punti, ne ha ricevuti 5, e appena i punti bastavano il caffè se l'è preso da solo: punti e basta, mai dollari — il livello più basso, deciso da lui». Andrea: «tre eventi in sala, blocchi da trenta secondi» |
| 9 | Slide 6 (l'identità per tutti e la roadmap), slide 7 (cosa resta, «mostrato ma non in produzione») | — | Alan: il NIP-05 gratuito al livello 2; NWC-RGB al repo `nwc` coi tre livelli; la roadmap (11.5); «in produzione dal 10 ottobre c'è il mercatino; questo weekend è su Mutinynet, dichiarato» |
| 10 | Riserva: se il blocco NON è arrivato alla scena 8-bis, si resta sull'ordine delle 13:30 (che il caffè l'ha già mostrato in mattinata: screenshot nelle slide) | Andrea | Andrea: «il blocco arriva, eccolo» (se no, niente: l'8 l'ha già mostrato) |

Tempi: 1-2 un minuto, 3-4 un minuto e un quarto (la vetrina a 45 s),
5-7 due minuti, 8 e 8-bis un minuto, 9 quaranta secondi, dieci secondi
di riserva: sei minuti. I numeri sono quelli del riquadro qui sopra
(«I numeri della demo, fissati il 9 ott»).

### 11.3 I due giorni, ora per ora (Andrea / Alan)

Il build chiude **domenica alle 15:00**; «Emesso da ✓» sta al **sabato
pomeriggio** (D.3 punto 0). «Claude» qui è la sessione sul portatile di
Andrea. Ogni pezzo è un commit datato nel repo privato, con
`git format-patch` serale in `fidelity-points` (G.1).

| Ora | Andrea (+ Claude) | Alan | Insieme / nota |
|---|---|---|---|
| sab 08:30-09:00 | Accende tutto nell'ordine di §6 (VM, tunnel a tre gambe, `rgb_http.py`, `nak serve`, servizio NWC, QVAC, Barattolo in collaudo), poi `py -3 semina_demo.py` (il negozio, l'annuncio ritarato al cambio del giorno, il cliente: §10 punto 5); se il WSL è stato riavviato, le due righe `annuncio` di §10 punto 4) | Slide e dichiarazione stampata (§5) sul tavolo; il suo portatile acceso con il wallet di prova vuoto | il tunnel va sull'hotspot, non sul Wi-Fi della sala |
| sab 09:00-09:45 | Kickoff | Kickoff; consegna la dichiarazione | niente codice prima della dichiarazione |
| sab 09:45-13:00 | **Server**: `/api/rgb/fattura` (la fattura blind di `barattolo` in USDB via `rgb_http.py`, importo al cambio, la prova del `// 100`: D.3 punto 5 PRIMA della rotta) e `/api/rgb/stato`, dietro `RGB_ATTIVO`; la decisione sullo stato dell'ordine pagato in USDB scritta nel commit | **Wallet**: i quattro metodi `rgb_*` in `nwc-wdk.mjs` sopra `punti.mjs` (lista, fattura, paga con conferma a terminale, lookup), provati col client a riga di comando sul suo wallet vuoto, poi portati sul portatile di Andrea | alle 11 un punto di cinque minuti: i NOMI dei campi fra server e wallet (quelli di `docs/spec/NWC-RGB.md`) |
| sab 13:00-13:45 | pranzo | pranzo | |
| sab 13:45-16:30 | **Client**: nel foglio del pagamento «oppure N USDB», «Paga in USDB» → fattura → `rgb_pay_invoice` via `clientNwc` → «in arrivo» → `rgb.py aggiorna barattolo` → «Pagato». **E la pagina «👛 Wallet NWC» chiama `get_info`/`get_balance` a OGNI apertura** (segnato il 9 ott, visto dal vivo: oggi il terminale del servizio si muove solo al «Collega»): alla schermata 4 il terminale deve muoversi mentre Alan parla | Il wallet sul portatile della demo: `rgb_pay_invoice` risponde alla pagina; poi comincia la lettura dell'annuncio per `#d` (nostr-tools, lato pagina) | **primo pagamento VERO in USDB su signet entro le 16:30**: il core |
| sab 16:30-18:00 | **«Emesso da … ✓»**: la verifica NIP-05 lato server (`url_api_ammesso`, senza redirect, cache di 24 h, «verificato il 16 ott» se il DNS manca) e la riga nella card, accanto a «⚠️ Emittente sconosciuto» | Rilegge i due annunci sul relay, confronta i tag col genesis (`punti.mjs saldo`), scrive la prima pagina dei due testi | **alle 18 la ✓ c'è**: da qui la demo è quella decisa il 7 sera |
| sab 18:00-20:30 | **Consigliami**: la pagina chiama QVAC con lo schema, il fumetto, «Approva» che fa il passo delle 13:45 da solo; se CORS o mixed content mordono, `/api/consigliami/proposta` lato server, dichiarato | Il «motivo» senza cifre (§4: il 1.7B sbaglia i numeri nella frase), la frase di riserva se QVAC tace | |
| sab 20:30-22:00 | **MOON come bonus** dopo «Pagato» (l'assegnazione del 1 ott agganciata, un punto per dollaro intero); **i livelli di autorizzazione dal vivo** (studio del 9, punto 11): 2,50 passa da solo con la riga «sotto la soglia», 4,80 chiede; la card dell'asset completa; il giro intero DUE volte | **La policy nel wallet** (`docs/spec/NWC-RGB.md`, «Authorization levels»): soglia per pagamento e budget del giorno in `nwc/connessioni.json` per il client `barattolo`, il comando `limite` a terminale, `rgb_get_budget`, la riga a terminale per ogni livello, `authorization: auto|confirmed` nella risposta; la seconda istanza di `rgb_http.py` per il negozio (`RGB_HTTP_WALLET=to-the-mooon`, porta 8788: serve al riscatto di domenica); `git format-patch`; le slide 3, 4 e 5 con gli screenshot veri | la sera: `pkill` di `rgb_http.py` sulla VM (backup delle 03:30), §6 |
| dom 08:30-09:00 | Riaccende tutto (§6), `py -3 semina_demo.py` per ritarare il prezzo al cambio del giorno; se serve, le due righe `annuncio` | Slide in ordine | |
| dom 09:00-11:30 | **Il riscatto automatico dei premi** (studio del 9, punto 13; idea di Alan): l'annuncio-premio del negozio seminato («☕ Caffè gratis · 25 MOON», un pezzo, ritiro a mano, prezzo in MOON), l'interruttore «riscatta da solo» sulla card del premio (la regola in localStorage), `/api/premio/riscatta` (la fattura blind in MOON dal wallet del negozio via la seconda istanza di `rgb_http`, l'ordine del premio in `creato`), la pagina che a ogni apertura e a ogni bonus arrivato controlla `rgb_list_assets` e, se bastano, chiama `rgb_pay_invoice` (il wallet: livello 0, firma senza chiedere), la notifica col codice dell'ordine | I **due testi** `docs/spec/NIP-RGB-ASSETS.md` e `NWC-RGB.md` rifiniti con quel che il sabato ha insegnato (i tre livelli come sono usciti); la **issue nel repo `nwc`** entro mezzogiorno; il «resident che riscatta a pagina chiusa» in roadmap (slide 6), non in demo | |
| dom 11:30-12:30 | Gli **errori visibili** («wallet non collegato», «proxy irraggiungibile», «conferma in arrivo», «sopra la soglia: il wallet chiede»: «UX: error handling» è un criterio), compressi, non tolti | Il video di riserva aggiornato (il giro intero registrato, 3 min) | |
| dom 12:30-13:00 | **Se il 13 KaleidoSwap ha detto sì** (studio, punti 7 e 12: un wallet `signet` riceve dal faucet `signetcustom`?): USDT del faucet come seconda card, grigia «⚠️ Emittente sconosciuto», accanto a USDB (30 min: l'asset accettato al checkout diventa una lista). Sennò, **se avanza**, la tool call di Consigliami (studio, punto 8: due chiamate, prima `tools` con `rgb_list_assets`, poi lo schema). Sennò il giro intero una TERZA volta sull'hotspot | La prova a tempo delle slide | |
| dom 13:00-14:00 | **L'ordine delle 13:30**: `py -3 semina_demo.py ordine` da **2,50 USDB** (il prezzo del secondo annuncio seminato, sotto la soglia di 3), pagato da solo (livello 1), il bonus **+2 MOON**; aspettare il blocco; l'ordine del vivo con `py -3 semina_demo.py ordine --nuovo`, lasciato in `creato`; il premio del caffè NON si arma la mattina (con 62 MOON scatterebbe subito): si arma in scena, al passo 7, mentre si aspetta il blocco | Le slide chiuse | **niente codice dopo le 14:00** |
| dom 14:00-15:00 | Prova generale degli undici passi di 11.2 (con l'8-bis), a tempo, con le tre finestre sullo schermo; `git format-patch` della domenica | Prova generale | **15:00: il build chiude** — l'ultimo commit datato prima |
| dom 15:00-16:00 | Consegna; il portatile in standby con tutto su | Pitch | la VM in riserva, l'hotspot acceso, il video sul portatile di Alan |

### 11.4 Il piano B: cosa si mostra se una parte si rompe

Quel che **già funziona dall'8 ott**, e resta vero anche se la domenica
va storta: la VM con la catena in pari e i tre asset (§2); il wallet
utente con 60 MOON e 500,00 USDB, che ha già ricevuto e riscattato MOON
con tx confermate (§3); il servizio NWC base con «wallet collegato» in
Barattolo (`get_info`, `get_balance`); le due identità con kind 0 e
NIP-05 sul relay locale, e la rotta `/.well-known/nostr.json` su main;
QVAC col 1.7B e la pagina `consigliami-prova.html` che fa il giro
intero fuori da Barattolo (§4); da stasera il comando `annuncio` e, dal
16, i due annunci sul relay. Il **video di riserva** della domenica
mattina (11.3) copre tutto. In ordine di probabilità:

| Si rompe | Si mostra | Come si dice |
|---|---|---|
| **QVAC** (il modello non carica, la risposta non è JSON, CORS) | Il fumetto con la proposta di RISERVA calcolata dal programma (la regola del 20%: la stessa che oggi boccia il modello in `consiglio.py`), col testo «consiglio senza AI»; e la pagina `consigliami-prova.html` sul 0.6B, servita da `http.server 8081`, che è il giro dell'8 ott | «l'aiutante propone dentro una regola: senza il modello la regola resta, e ve la mostro sulla pagina di prova» — l'AI è un aiuto, non il centro (G.4) |
| **Il wallet** (i metodi `rgb_*` non rispondono, il servizio muore, la conferma non arriva) | Il pagamento come il 1 ott: dal terminale, `node punti.mjs riscatta <USDB> 480 '<fattura>'` con la fattura presa da `/api/rgb/fattura` (o da `rgb_http.py /fattura`), e `rgb.py aggiorna barattolo`; il foglio passa a «in arrivo» lo stesso perché legge lo stato dal server | «il wallet è self-custodial: lo stesso gesto, dal suo terminale invece che dal bottone; il protocollo NWC-RGB è la bozza che vedete alla slide 4» |
| **La rete** (hotspot morto, VM irraggiungibile, DNS che non risolve) | Senza VM: il wallet sugli endpoint pubblici (`RGB_INDEXER`/`RGB_PROXY` di §6) e `rgb_http.py` di riserva sul portatile; senza NESSUNA rete: il relay locale e QVAC vanno lo stesso (sono sul portatile), la ✓ dice «verificato il 16 ott» dalla cache (D.3 punto 3), il pagamento NON si fa e si mostra l'ordine delle 13:30 già pagato e il video | «tutto quel che è locale — l'identità, l'annuncio, l'AI — lo vedete dal vivo; la transazione su signet l'abbiamo fatta alle 13:30, eccola su mempool» (screenshot già nelle slide) |
| **L'Esplora di KaleidoSwap** (429, giù) | Si cambia una variabile: `RGB_INDEXER=https://mutinynet.com/api` (la riserva commentata nei due `.env`), si riavviano `rgb_http.py` e il servizio NWC; le fatture restano valide (portano il proxy, non l'indexer) | niente: un minuto di pausa, «un attimo che cambio indexer» |
| **Il proxy di KaleidoSwap** giù | `RGB_PROXY=rpcs://proxy.iriswallet.com/0.2/json-rpc` (l'altra riserva), riavvio, e le fatture APERTE si rifanno (il proxy sta dentro la fattura) | come sopra |
| **Mutinynet ferma** (un solo minatore, nessun blocco) | Si mostra l'ordine delle 13:30 e il video; e si TORNA AL SIGNET in cinque minuti (§10, in fondo alla lista di domenica): nessun `source`, tunnel a tre gambe, `rgb_http.py` e NWC rilanciati senza `source`, gli id della prima tabella di §2 nel config di Barattolo; blocchi da dieci minuti, scaletta dell'8 ott (il blocco non arriva in sala) | «la rete di prova degli organizzatori si è fermata: lo stesso giro sul signet pubblico, dove l'abbiamo fatto il 1 ottobre» |
| **La ✓ non si costruisce il sabato** | La card con «Dichiarato da <npub> · identità non verificata» (la forma 3 di C) e l'evento letto dal relay: l'annuncio firmato esiste dal 16 | «l'annuncio è firmato e pubblicato; la verifica del dominio è la riga che manca, ed è nella roadmap di lunedì» |
| **I livelli o il riscatto non si costruiscono** | Il pagamento chiede sempre (il livello 2 è quello di oggi) e il caffè si riscatta a mano dal wallet come il riscatto del 1 ott; la scena 8-bis diventa la riga «e il premio lo riscatterà da solo: è la bozza» | «la soglia e il riscatto automatico sono nella bozza NWC-RGB alla slide 4: oggi vedete il livello che chiede» |
| **Barattolo in collaudo non parte** (db, porta, config) | Il server del worktree con un db nuovo (`MODALITA_COLLAUDO`, le tre identità finte nascono da sole), `py -3 semina_demo.py` su quel db (§10 punto 5) e il giro rifatto; se nemmeno quello, il video | la demo del 1 ott sul terminale resta (§3) |

La regola per il palco: **si cambia strada senza spiegare il guasto**,
una frase e avanti; la spiegazione tecnica va nelle Q&A se la chiedono.

### 11.5 La roadmap (slide 6, niente codice): la lista di controllo

Le quattro voci chieste ci sono tutte, in D.2 dello studio (le slide e
il paragrafo «la roadmap, con una riga di realtà ciascuna») e qui:

- ☑ **Mostro con asset RGB**: un ordine «vendo USDB per euro» con un
  campo in più nel NIP-69 — una proposta, non un cantiere (Mostro non
  ha nozione di asset: VERIFICATO il 1 ott).
- ☑ **Consegne RGB via relay Nostr** al posto del proxy: il consignment
  su Blossom (che Barattolo usa già per le foto delle recensioni) e un
  puntatore firmato sul relay — perché un transfer consignment cresce
  con la storia e i relay tagliano gli eventi grossi.
- ☑ **Certificati di autenticità RGB per le edizioni limitate** (le
  magliette numerate di AGORA): lo schema UDA, uno per maglietta con la
  foto e il numero, **emesso dal negozio con la sua identità Nostr** —
  lo stesso annuncio firmato di oggi, così la card dice «Emesso da
  AGORA ✓» e un certificato senza quella firma resta «emittente
  sconosciuto» (aggiunto l'8 ott sera anche in D.2).
- ☑ **La proposta all'RGB Protocol Association per un grant**, con la
  nota di D.2: l'esistenza di un programma di grant NON è verificata,
  è la domanda 11 del Q&A del 13.

Più le due che stanno già in slide 6: il NIP-05 gratuito al livello 2
del mercatino (G.3) e NWC-RGB come estensione proposta al repo `nwc`.

Nota a margine, fuori cantiere ma scoperta qui: il pull notturno del
backup del NODO falliva dal 7 settembre («permission denied» su
`/var/backups/nodo`: lo script lo richiudeva a 700 ogni notte). Curato
da Andrea il 1 ott (riga 19 di `backup-nodo.sh`, `-g pull -m 750`): il
verbale sta in `docs/NODO-MOSTRO.md`.
