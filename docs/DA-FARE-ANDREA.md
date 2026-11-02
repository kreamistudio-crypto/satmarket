# Da fare sul VPS e sul nodo (la lista per la sessione di Andrea)

Chi lavora su `develop` non entra nel VPS, nel nodo Mostro né nel relay.
Arriva al massimo a collaudo.barattolo.store. Quello che resta da fare
LÀ si scrive qui, coi comandi pronti, e la sessione sul PC di Andrea lo
legge PER PRIMO (prima di una promozione, e a ogni avvio).

Le regole del file:
- una voce per gesto: chi l'ha chiesto e quando, il PERCHÉ in due
  righe, i comandi in sola lettura PRIMA, e poi quelli che scrivono;
- un comando alla volta: Andrea lo lancia e incolla il risultato;
- una voce FATTA si cancella da qui, e quel che si è visto va nel suo
  documento (PRODUZIONE, NODO-MOSTRO, CANTIERI): questo file è una
  lista d'attesa, non un archivio;
- mai segreti qui: niente token, nsec, macaroon, config.

---

## 1. Il pallino degli altri account vuole la leva `PIU_ACCOUNT_OVUNQUE` (21 ott 2026, cantiere puntino-account)

**Perché.** Il pallino sul tappo si accende quando un altro account
aperto ha qualcosa da fare. Dentro Telegram il menu degli account, e
quindi il pallino, c'è SOLO a leva accesa. Senza la leva, in
produzione il cantiere non si vede. Va fatto DOPO la promozione su main.

**Sola lettura:**
```
grep -n "^PIU_ACCOUNT_OVUNQUE" /srv/barattolo/config.py
```
Oppure il pannello admin «⚙️ Stato delle leve», gruppo «👥 Più account».
Se è accesa non c'è niente da fare. Se è spenta, accenderla è una
decisione di Andrea: apre il menu degli account dentro Telegram per
tutti. La procedura è in PRODUZIONE, «PIÙ ACCOUNT OVUNQUE».

## 2. Le fee dei canali ACINQ sul nodo Mostro (21 ott 2026, richiesta di Andrea: «alzare le fee di ACINQ per diventare più attrattivi per il nodo LNBIG»)

**Stato.** IN ATTESA DEL NUMERO, non lanciare il passo 2 finché Andrea
non dice quanti ppm. Oggi (Cantieri, 16 ott): ACINQ (tutti e due i
canali) 1 sat + 500 ppm, LNBiG 1 sat + 2.500 ppm.

**Il dubbio da sciogliere prima.** Un inoltro paga la tariffa del
canale da cui ESCE. Alzare ACINQ rende più caro il passaggio
LNBiG → noi → ACINQ: da quel lato siamo una strada più cara, non più
attraente, ma guadagniamo di più su quel che passa lo stesso. Lo studio
del 5 ott (`STUDIO-INSTRADAMENTO-NODO-2026-10-05.md`, §7) proponeva il
contrario, cioè ACINQ giù a 1 sat + 100 ppm, perché quel verso è un
ribilanciamento fatto da altri e pagato a noi. Se «attrattivi per
LNBiG» vuol dire una regola precisa di LNBiG, va scritta qui prima del
comando.

**Passo 1, sola lettura** (sul nodo, da `~/nodo`):
```
docker compose exec lnd lncli feereport
```
```
docker compose exec lnd lncli listchannels | grep -E '"remote_pubkey"|"channel_point"|"capacity"'
```
ACINQ è `03864ef0…` (due canali: 400k e 1M), LNBiG Hub-2 è `033e9ce4…`.

**Passo 2, scrive: SOLO col numero deciso**, una volta per ogni canale ACINQ:
```
docker compose exec lnd lncli updatechanpolicy --base_fee_msat 1000 --fee_rate_ppm <NUOVO_PPM> --time_lock_delta 80 --chan_point <CHAN_POINT_ACINQ>
```
Poi di nuovo `feereport` per vedere che ha preso. Il risultato e il
perché vanno in `docs/NODO-MOSTRO.md`, e questa voce si cancella.

## 3. L'assistente del bot, prima sul collaudo (28 ott 2026, cantiere bot-assistente)

**Perché.** Andrea ha chiesto un bot che risponda come un assistente AI,
dichiarato come tale, con una persona vera dietro un bottone; ha scelto
l'API di Claude con una chiave separata. Il codice è su `develop`,
spento e senza chiave: sul collaudo non si vede finché non si accende.
Il perché di tutto: CANTIERI, «L'assistente del bot».

**Prima, dal PC (nessun comando):** nella Console di Anthropic un
workspace «barattolo-bot» col suo limite di spesa mensile (10-20 $ per
cominciare) e dentro una chiave nuova. La stessa chiave può servire
collaudo e produzione; due chiavi separate dicono quanto spende ognuno.
In KeePass, mai in chat.

**Sola lettura** (sulla VM del collaudo). Le righe non ci sono già
(deve dire `0`), e il config legge i segreti dai file con `_segreto`
(deve dire `1`):
```
sudo grep -c "^ASSISTENTE_" /srv/collaudo/barattolo/config.py
```
```
sudo grep -c "def _segreto" /srv/collaudo/barattolo/config.py
```

**Scrive**, un comando alla volta. Sul collaudo i segreti stanno in
`/etc/barattolo-collaudo/`, uno per file, e il config li legge (COLLAUDO
§4): la chiave va in un file suo, e nel config solo la riga che lo legge.
La copia di riserva:
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-assistente
```
La chiave nel suo file (chiede la password di sudo, poi la chiave, che
non si vede mentre si incolla; deve dire «Scritta»):
```
sudo -v && read -rsp "Chiave dell'assistente: " K && echo && if [ -z "$K" ]; then echo "Vuota: non scrivo niente"; else printf '%s' "$K" | sudo tee /etc/barattolo-collaudo/assistente_api_key > /dev/null && sudo chown root:collaudo /etc/barattolo-collaudo/assistente_api_key && sudo chmod 640 /etc/barattolo-collaudo/assistente_api_key && echo "Scritta"; fi; unset K
```
Le due righe del config (la chiave dal file, e la leva, che resta solo
per i moderatori):
```
printf '\nASSISTENTE_API_KEY = _segreto("assistente_api_key")\nASSISTENTE_AI_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
Il file si legge ancora (deve dire `ok`), poi il riavvio:
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi, da admin, a @barattolo_collaudo_bot: tre o quattro domande
vere («come funziona il deposito di garanzia?», «quanto costa
vendere?», «dov'è il mio ordine?», una fuori tema) e il bottone «🙋
Parla con una persona». Quel che si vede va nel verbale (CANTIERI,
«L'assistente del bot», «COSA RESTA»). In produzione si accende DOPO la
promozione, con la procedura sua (PRODUZIONE, «L'ASSISTENTE DEL BOT:
LA CHIAVE E LE LEVE»: là la chiave sta nel config); a tutti, quando Andrea
decide, `ASSISTENTE_SOLO_MODERATORI` a False dal pannello. ATTENZIONE
alle copie vecchie del config del collaudo: quelle di prima di oggi non
hanno queste righe.

## 4. L'on-chain in mainnet, solo agli admin, per la prova da 5 € (30 ott 2026, cantiere onchain-mainnet, proposta di Alan: «ok possiamo portarlo su main, con flag onchain attivo solamente per gli admin»)

**Stato.** DOPO LA PROMOZIONE INTERA develop → main (il cantiere è su
develop). L'ordine dei gesti conta: la chiave di Barattolo nasce sulla
rete che il server ha in quel momento, quindi PRIMA la riga della rete e
il riavvio, POI il bottone. La procedura intera e i perché: PRODUZIONE,
«L'ON-CHAIN IN MAINNET».

**Passo 1, sola lettura.** embit c'è? (PY = il Python del servizio,
`systemctl show -p ExecStart barattolo --no-pager`):
```
sudo -u barattolo PY -c "import embit; print('embit c è')"
```
Se manca: PRODUZIONE, «L'ON-CHAIN, TAPPA 2: EMBIT SUL VPS» (un passo alla
volta). Poi le righe on-chain del config e il file della chiave:
```
grep -n "^ONCHAIN_" /srv/barattolo/config.py
```
```
sudo ls -l /root/satmarket/chiavi/
```
Attesi: nessuna riga `ONCHAIN_`, e «No such file or directory». Se c'è un
file, FERMATI: è nato su signet e su mainnet non vale (si sposta via con
copia, prima del passo 3).

**Passo 2, scrive: la copia e le quattro righe** (dopo il sì di Andrea):
```
cp -a /srv/barattolo/config.py /root/config-prima-mainnet-$(date +%F).py
```
```
printf '\nONCHAIN_RETE = "mainnet"\nONCHAIN_ATTIVO = True\nONCHAIN_SOLO_ADMIN = True\nONCHAIN_MAX_EURO = 10\n' | sudo tee -a /srv/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo && sleep 5 && curl -s -o /dev/null -w 'salute %{http_code}\n' http://127.0.0.1:8080/api/salute
```
Atteso `ok` e `salute 200`. Nel journal nessuna riga «[onchain] ONCHAIN_RETE … resta signet»:
```
journalctl -u barattolo -n 60 --no-pager | grep -n "onchain" || echo "nessuna riga onchain"
```

**Passo 3, dal telefono (Andrea, admin).** Pannello «⚙️ Stato delle
leve», gruppo «⛓️ Pagamento on-chain»: deve dire «Rete dell'on-chain:
mainnet» e la terza chiave in ALLARME («⚠️ di cartone su MAINNET:
l'on-chain è FERMO»). Poi, nel cassetto «⛓️ Chiave di Barattolo», il
bottone «⛓️ Crea la chiave di Barattolo», UNA volta. Controllo in sola
lettura:
```
sudo ls -l /root/satmarket/chiavi/ && sudo python3 -c "import json; d=json.load(open('/root/satmarket/chiavi/onchain-barattolo.json')); print(d['rete'], d['strada'], d['xpub'][:8])"
```
Atteso `-rw-------`, `mainnet m/48'/0'/0'/2' xpub6…`. SUBITO il backup
fuori sede (finché la copia è una sola, su mainnet quella chiave vale
sats):
```
cd /srv/barattolo && sudo -u barattolo ./deploy/backup-fuori.sh
```
Il pannello delle leve deve poi dire «sul VPS (impronta …)» senza l'avviso del backup.

**Passo 4, la prova da 5 €.** Andrea e Alan aprono la Mini App (l'on-chain
si accende da solo con la xpub di mainnet); Profilo → «⛓️ On-chain» →
Tecnico dice in rosso «Rete Bitcoin (mainnet): i sats sono veri». Alan
mette in vendita un oggetto sotto i 10 €; Andrea sceglie ⛓️ alla cassa,
paga il `bc1q…` da un wallet vero, aspetta UNA conferma, tocca «🔓
Libera i sats»; Alan riapre l'app e il suo telefono co-firma. Quel che
si vede (txid, tempi, commissioni, frasi storte) va nel verbale
(CANTIERI, «L'on-chain in mainnet», «COSA RESTA»). Per tornare indietro:
`ONCHAIN_ATTIVO = False` e riavvio (PRODUZIONE dice perché la RETE non
si rimette su signet con ordini aperti).


## 5. Gli scambi P2P on-chain (2-di-3) sul collaudo (30 ott 2026, cantiere p2p-onchain-2di3)

**Perché.** Il secondo libro del P2P, con la garanzia 2-di-3 al posto
della hold invoice di Mostro, è su `develop` dietro la leva
`P2P_ONCHAIN_ATTIVO`, spenta di serie. Sul collaudo l'on-chain
(`ONCHAIN_ATTIVO`) e il P2P sono già accesi: manca solo questa riga.
Il perché di tutto: CANTIERI, «La garanzia 2-di-3 negli scambi P2P
on-chain».

**Sola lettura** (la riga non c'è già: deve dire `0`):
```
sudo grep -c "^P2P_ONCHAIN_ATTIVO" /srv/collaudo/barattolo/config.py
```

**Scrive**, dopo che il collaudo ha tirato `develop` con il cantiere. La
copia di riserva, poi la riga, poi il riavvio:
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-p2p-onchain
```
```
printf '\nP2P_ONCHAIN_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi, da admin, nel P2P: in cima al libro la riga «⛓️
Scambi on-chain», da lì «Pubblica» (vendo 50.000 sats per X €), e con
il secondo account «Prendi»; il deposito è su signet (i sats di prova
del faucet), chi vende li manda all'indirizzo 2-di-3, chi compra tocca
«Ho inviato gli euro», chi vende «Ricevuti: libera i sats», e il
telefono di chi compra mette la seconda firma da solo. Quel che si vede
va nel verbale (CANTIERI, «NON PROVATO»). In produzione la leva resta
spenta finché Alan non ha rivisto le parti 2-di-3 e non c'è il parere
MiCA. ATTENZIONE alle copie vecchie del config del collaudo: quelle di
prima di oggi non hanno questa riga.

## 6. La cancellazione dell'account sul collaudo (1 nov 2026, cantiere cancella-account, richiesta di Andrea)

**Perché.** Il gesto «🗑 Cancella il mio account» è su `develop` dietro
la leva `ACCOUNT_CANCELLABILE`, spenta di serie. Va guardato dal telefono
sul collaudo prima di pensare alla produzione. Il perché di tutto:
CANTIERI, «La cancellazione dell'account».

**Sola lettura** (la riga non c'è già: deve dire `0`):
```
sudo grep -c "^ACCOUNT_CANCELLABILE" /srv/collaudo/barattolo/config.py
```

**Scrive**, dopo che il collaudo ha tirato `develop` con il cantiere. La
copia di riserva, poi la riga, poi il riavvio:
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-cancella-account
```
```
printf '\nACCOUNT_CANCELLABILE = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi, dal telefono, con un account di PROVA (mai il proprio
admin: gli admin non si cancellano, e il foglio lo dice): Profilo →
Privacy → «🗑 Cancella il mio account». Con un ordine in corso il foglio
deve elencarlo senza bottone; senza niente in corso, scrivere CANCELLA e
confermare. Il gesto NON si annulla. In produzione la leva resta spenta
finché Andrea non dice sì, dopo la promozione.

## 7. Gli ordini P2P in USDT: la leva sul collaudo, poi il nodo (1 nov 2026, cantiere p2p-usdt; Andrea: «Tron + Polygon mettiamo anche ethereum. tetto 250 €, NODO solo dopo le prove»)

**Perché.** L'app sa pubblicare, prendere e pagare ordini in USDT (le
tre reti, il controllo della rete sbagliata, il QR con la catena, l'id
della transazione), dietro la leva `P2P_USDT_ATTIVO`, spenta di serie e
di serie solo per gli admin. Il nodo però oggi accetta solo l'euro
(`fiat_currencies_accepted = ['EUR']`): finché non si fa il gesto qui
sotto un ordine in USDT il nodo lo rifiuta. Il perché di tutto:
CANTIERI, «Gli ordini P2P in USDT».

**A e B FATTE il 2 nov 2026, 07:40-07:47 UTC** (Andrea, un comando alla
volta). Collaudo: `P2P_USDT_ATTIVO = True` in fondo al config, copia
`config.py.prima-usdt`, salute 200. Nodo a libro fermo (3 `pending`, il
resto finito): riga 111 `['EUR', 'USDT']`, `[price.providers.pegged]`
alle righe 305-307, copia `~/nodo/mostro/settings.toml.prima-usdt`,
riavvio dal compose, nel log «pegged ok (6 currencies)» (il provider le
calcola tutte, `only` fa passare solo USDT) e nessun errore. Due
differenze dai comandi qui sotto: la valuta è stata cambiata con un
Python che riscrive LO STESSO file e si ferma se la riga non è quella
(non `sed -i`, che fa un file nuovo), e al posto dei `tail` si sono
usati `grep` mirati (le righe vicine non si stampano). Resta la C.

**A. Il collaudo, la leva** (si può fare subito, dopo che il collaudo ha
tirato `develop` col cantiere). Sola lettura, deve dire `0`:
```
sudo grep -c "^P2P_USDT_ATTIVO" /srv/collaudo/barattolo/config.py
```
Scrive: la copia, la riga, il controllo, il riavvio.
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-usdt
```
```
printf '\nP2P_USDT_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Da admin, nel foglio «Pubblica» compare la valuta ₮ USDT e
i metodi diventano le tre reti; un altro account non admin non vede
niente. Da guardare a mano qui, senza pubblicare: il recapito di prova
che rifiuta un indirizzo Tron su Ethereum e uno bitcoin su Tron. (Dal
2 nov le reti sono due, Tron ed Ethereum: Polygon è stato tolto.)

**B. Il nodo, SOLO DOPO le prove della parte A** (gesto di Andrea, a
libro fermo, un comando alla volta). Da qui gli ordini in USDT si
possono pubblicare sul nostro nodo da QUALUNQUE app Mostro (Andrea l'ha
saputo e ha detto sì il 2 nov 2026); i nostri utenti in produzione non
li vedono finché la leva lì resta spenta.

Sola lettura sul nodo (`ssh … debian@vm-1937.lnvps.cloud`, poi `cd ~/nodo`):
```
grep -n -E "^fiat_currencies_accepted|^\[price|^\[" ~/nodo/mostro/settings.toml
```
Atteso: `fiat_currencies_accepted = ['EUR']`, e NESSUNA riga
`[price.providers.pegged]`. Se c'è già, ci si ferma e si chiede a Claude.
```
sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC').fetchall())"
```
Devono comparire SOLO `pending` e stati finali (lo stesso controllo
della salita alla 0.20.2, PRODUZIONE, «IL LIBRO FERMO»): uno scambio in
corso = si ASPETTA.

Scrive: la copia, la valuta, il provider, il controllo, il riavvio.
```
cp -p ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.prima-usdt
```
```
sed -i "s/^fiat_currencies_accepted = \['EUR'\]$/fiat_currencies_accepted = ['EUR', 'USDT']/" ~/nodo/mostro/settings.toml && grep -n "^fiat_currencies_accepted" ~/nodo/mostro/settings.toml
```
Atteso: `fiat_currencies_accepted = ['EUR', 'USDT']`.
```
printf '\n[price.providers.pegged]\nenabled = true\nonly = ["USDT"]\n' >> ~/nodo/mostro/settings.toml && tail -4 ~/nodo/mostro/settings.toml
```
```
python3 -c "import tomllib; d=tomllib.load(open('/home/debian/nodo/mostro/settings.toml','rb')); print(d['mostro']['fiat_currencies_accepted'], d['price']['providers']['pegged'])"
```
Atteso: `['EUR', 'USDT'] {'enabled': True, 'only': ['USDT']}`. Se
`tomllib` dice un errore, si rimette la copia (`cp -p
~/nodo/mostro/settings.toml.prima-usdt ~/nodo/mostro/settings.toml`) e
si chiede a Claude.
```
docker compose restart mostro && sleep 20 && docker compose logs --since 2m mostro | grep -i -E "price|pegged|usdt|error|warn" | tail -20
```
Atteso: il nodo riparte, i provider dicono «ok», nessun avviso su USDT.

**C. La prova a due account sul collaudo**, cifre piccole (10 USDT):
Andrea pubblica «vendo sats per 10 USDT su Tron» (su Tron serve un po'
di TRX per la commissione; Ethereum costa di più), un secondo account
admin (Alan, se è in `ADMIN_IDS` del collaudo) prende, mette il suo indirizzo, Andrea manda gli USDT e incolla
l'id della transazione, Alan controlla sull'explorer e libera. Quel che
si vede va nel verbale (CANTIERI, «Gli ordini P2P in USDT», «NON
PROVATO»). In produzione la leva resta spenta fino alla promozione e a
un sì di Andrea; poi `P2P_USDT_ATTIVO = True` (solo admin) e, più
avanti, `P2P_USDT_SOLO_ADMIN = False` per tutti.
