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
Attesi: nessuna riga `ONCHAIN_`, e nella cartella al più
`swap-barattolo.json` (le parole dello swap automatico, nate il 3 nov
2026: restano dove sono). Se c'è `onchain-barattolo.json`, FERMATI: è nato
su signet e su mainnet non vale (si sposta via con copia, prima del passo
3). Se manca la cartella intera la si crea a mano, come al passo 2 della
voce 9: il server gira come `barattolo` e in `/srv/barattolo`, che è di
root, non può crearla da sé.

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
sudo systemctl start barattolo-backup && sudo journalctl -u barattolo-backup -n 15 --no-pager
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

## 8. Gli USDT negli scambi P2P on-chain, sul collaudo (2 nov 2026, cantiere p2p-onchain-usdt; Andrea: «usdt onchain assolutamente è da fare»)

**Perché.** Negli scambi on-chain col 2-di-3 chi compra bitcoin può
pagare in USDT su Tron o Ethereum al posto degli euro; i sats restano
nel 2-di-3 di sempre. È su `develop` dietro la leva
`P2P_ONCHAIN_USDT_ATTIVO`, spenta, e vale solo dove ci sono già
`P2P_ONCHAIN_ATTIVO` e `P2P_USDT_ATTIVO` (sul collaudo ci sono tutte e
due). Il nodo non c'entra: questi scambi non passano da Mostro. Il
perché di tutto: CANTIERI, «Gli USDT negli scambi P2P on-chain».

**Sola lettura** sulla VM (deve dire `0`):
```
sudo grep -c "^P2P_ONCHAIN_USDT_ATTIVO" /srv/collaudo/barattolo/config.py
```

**Scrive**, dopo che il collaudo ha tirato `develop` col cantiere. La
copia, la riga, il controllo, il riavvio:
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-usdt-onchain
```
```
printf '\nP2P_ONCHAIN_USDT_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi dal telefono, due account admin (Andrea vende, Alan
compra), cifre piccole: nel foglio «Pubblica» con l'interruttore su
On-chain la valuta ₮ USDT, metodo «USDT (Tron)», l'indirizzo Tron di
Andrea in «Dove vuoi gli USDT»; Alan prende, Andrea deposita i sats di
signet, Alan manda gli USDT veri (pochi: sono veri, su Tron serve un po'
di TRX) e incolla l'id; Andrea guarda su Tronscan e libera. Quel che si
vede va nel verbale (CANTIERI, «NON PROVATO»). In produzione la leva
resta spenta fino alla promozione e a un sì di Andrea.

## 9. Lo swap automatico, la prova da 30.000 sats in produzione (2 nov 2026, cantiere swap-auto; Andrea: «ok parti»)

**Perché.** Chi vende in Lightning e ha scelto nel Profilo di ricevere
on-chain riceve in bitcoin: il cambio con SATS Routing lo fa il SERVER
con parole di Barattolo, lui preme solo «Conferma» sull'ordine. È su
`develop` dietro `SWAP_AUTO_ATTIVO`, spenta, e a leva accesa vale solo
per gli admin (`SWAP_AUTO_SOLO_ADMIN`, accesa di serie). Il perché di
tutto: CANTIERI, «Lo swap automatico del mercatino». Si fa DOPO la
promozione (la frase di Andrea), con Andrea e Alan.

**Passo 1, sola lettura** sul VPS (atteso: nessuna riga, e «No such file»
per le parole):
```
grep -n "^SWAP_AUTO" /srv/barattolo/config.py
```
```
sudo ls -l /srv/barattolo/chiavi/
```

**Passo 2, scrive: la copia, la riga, il controllo, il riavvio** (dopo il sì di Andrea):
```
cp -a /srv/barattolo/config.py /root/config-prima-swap-auto-$(date +%F).py
```
```
printf '\nSWAP_AUTO_ATTIVO = True\n' | sudo tee -a /srv/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo && sleep 30 && curl -s -o /dev/null -w 'salute %{http_code}\n' http://127.0.0.1:8080/api/salute
```
La cassaforte `chiavi/`, se non c'è ancora: il server gira come
`barattolo` e `/srv/barattolo` è di root, quindi la cartella non sa
crearla da sé (3 nov 2026: «Crea le parole» rispondeva «non create», nel
journal `PermissionError: … '/srv/barattolo/chiavi'`). Atteso
`drwx------ … barattolo barattolo`:
```
sudo install -d -m 700 -o barattolo -g barattolo /srv/barattolo/chiavi
```
```
sudo ls -ld /srv/barattolo/chiavi
```

**Passo 3, dal telefono (Andrea, admin).** Pannello admin, cassetto «🔁
Parole dello swap»: «Crea le parole», UNA volta. Controllo in sola
lettura, poi SUBITO il backup fuori sede (finché la copia è una sola):
```
sudo ls -l /srv/barattolo/chiavi/
```
```
sudo systemctl start barattolo-backup && sudo journalctl -u barattolo-backup -n 15 --no-pager
```
Atteso `-rw-------` e l'archivio in chat. Il backup a mano è il
giornaliero lanciato adesso: gira da root, come alle 04:30 (come
`barattolo` non entrerebbe in `/root/satmarket`, che sta dentro `/root`).

**Passo 4, la prova.** Alan (venditore): Profilo → «Lightning address» →
«Quando vendi in Lightning, ricevi: On-chain»; la sua card deve mostrare
la moneta ₿ arancione, e il dettaglio «Preferisce ricevere on-chain».
Mette in vendita un oggetto da 30.000 sats; Andrea compra e conferma la
ricezione; Alan riceve in chat «premi «Conferma»» (NON i sats sul
Lightning address), apre l'ordine, controlla l'indirizzo (quello del suo
wallet on-chain, o lo scrive) e preme «Conferma». Dal 14 nov 2026 il
server ritira solo quando i bitcoin bloccati da SATS Routing hanno la
PRIMA CONFERMA della rete (cantiere audit-swap-conferma): di solito una
decina di minuti, a volte di più. Poi deve arrivargli in chat «i tuoi
bitcoin sono partiti» col txid; si guarda su mempool.space. Quel che si vede (tempi, costo, frasi storte) va nel
verbale (CANTIERI, «NON PROVATO»). Per tornare indietro:
`SWAP_AUTO_ATTIVO = False` e riavvio (uno swap già confermato il battito
lo finisce lo stesso: la leva ferma solo i «Conferma» nuovi).

## 10. L'assistenza in app sul collaudo (5 nov 2026, cantiere assistenza; Andrea: «ok porta su develop»)

**Perché.** La chat con lo staff (Profilo → Privacy → «💬 Assistenza») e
la pagina degli admin («💬 Assistenza clienti») sono su `develop` dietro
la leva `ASSISTENZA_ATTIVA`, spenta di serie. Ogni messaggio avvisa ogni
admin sul canale del suo profilo. Il perché di tutto: CANTIERI,
«L'assistenza in app», passi 1 e 2.

**Sola lettura** (la riga non c'è già: deve dire `0`):
```
sudo grep -c "^ASSISTENZA_ATTIVA" /srv/collaudo/barattolo/config.py
```

**Scrive**, dopo che il collaudo ha tirato `develop` con il cantiere. La
copia di riserva, poi la riga, poi il riavvio:
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-assistenza
```
```
printf '\nASSISTENZA_ATTIVA = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi, dal telefono: con un account di prova scrivi
all'assistenza; da admin guarda che l'avviso arrivi sul tuo canale (il
tasto apre la conversazione), rispondi dall'app, e controlla che l'utente
riceva «ti ha risposto» col tasto che apre la sua chat. In produzione la
leva resta spenta finché Andrea non dice sì, dopo la promozione.

## 11. Il widget di prova, dal telefono (10 nov 2026, cantiere widget-prova)

Niente da scrivere sulla VM: nessuna leva, nessuna riga nel config. Il
collaudo tira `develop` e al riavvio registra da solo il webhook con gli
update dei widget. **Sola lettura**, per vederlo (atteso: la riga
«🔔 Webhook Telegram: Webhook was set»):
```
sudo journalctl -u barattolo-collaudo -n 200 --no-pager | grep "Webhook Telegram"
```
Poi, da un admin del collaudo, con Telegram AGGIORNATO, nella chat
privata con @barattolo_collaudo_bot:
1. `/provawidget` — deve arrivare una scheda con cinque passi, il primo
   acceso. Se arriva «⚠️ sendWidget rifiutato: …», quella frase è il
   risultato della prova: va incollata nella sessione.
2. Tocca «Avanti ▶» dentro la scheda: il passo cambia senza un
   messaggio nuovo e senza suono.
3. Scrivi `/provawidget 5`, poi `/provawidget indietro`: la scheda si
   gira dal lato del bot.
4. Uno screenshot da Android, da iPhone e da desktop, in tema chiaro e
   scuro: è quel che decide la tappa 2 (la scheda vera dell'ordine).

## 12. La scheda dei miei ordini, dal telefono (10 nov 2026, cantiere widget-ordini)

Niente da scrivere sulla VM. Nella chat privata con
@barattolo_collaudo_bot, da un account che sul collaudo ha degli ordini:
1. `/ordini` — arriva la scheda coi tuoi ordini, gli attivi in alto.
2. Tocca un ordine: si apre la sua pagina coi passi. «← I tuoi ordini»
   torna all'elenco, «Apri in Barattolo» lo apre nell'app.
3. Lascia la scheda a schermo e, da un altro account, fai avanzare un
   ordine (per esempio segnalo spedito): entro una ventina di secondi
   l'etichetta deve cambiare da sola. Se non cambia, tocca 🔄: se cambia
   solo così, dillo alla sessione (le richieste da sole non passano).

## 14. Gli ordini P2P in franchi svizzeri: la leva sul collaudo, poi il nodo (14 nov 2026, cantiere p2p-chf; Andrea: «abbiamo stretto una collaborazione con Lugano»)

**Perché.** L'app sa pubblicare, prendere e pagare ordini in CHF (TWINT,
bonifico svizzero, Revolut, Wise, contanti), dietro la leva
`P2P_CHF_ATTIVO`, spenta di serie e di serie solo per gli admin. Il nodo
oggi accetta solo euro e USDT: finché non si fa la B un ordine in CHF il
nodo lo rifiuta. Il prezzo del franco NON vuole righe nuove: i provider
del nodo (yadio, CoinGecko, currency-api, Blockchain.com) danno già
tutte le valute. Il perché di tutto: CANTIERI, «Gli ordini P2P in
franchi svizzeri».

**A. Il collaudo, la leva** (dopo che il collaudo ha tirato `develop`
col cantiere). Sola lettura, deve dire `0`:
```
sudo grep -c "^P2P_CHF_ATTIVO" /srv/collaudo/barattolo/config.py
```
Scrive: la copia, la riga, il controllo, il riavvio.
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-chf
```
```
printf '\nP2P_CHF_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Da admin, nel foglio «Pubblica» la valuta 🇨🇭 CHF e i metodi
svizzeri; un account non admin non vede niente. Senza pubblicare: il
recapito TWINT rifiuta un numero italiano, il bonifico CH un IBAN
italiano o con una cifra sbagliata.

**B. Il nodo, SOLO DOPO la A** (gesto di Andrea, a LIBRO FERMO perché
riavvia Mostro, un comando alla volta). Da qui gli ordini in franchi si
possono pubblicare sul nostro nodo da qualunque app Mostro; in
produzione non li vede nessuno finché la leva là resta spenta.

Sola lettura sul nodo (`ssh … debian@vm-1937.lnvps.cloud`, poi `cd ~/nodo`):
```
grep -n "^fiat_currencies_accepted" ~/nodo/mostro/settings.toml
```
Atteso: `fiat_currencies_accepted = ['EUR', 'USDT']`. Se dice altro, ci
si ferma e si chiede a Claude.
```
sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC').fetchall())"
```
Solo `pending` e stati finali (PRODUZIONE, «IL LIBRO FERMO»): uno
scambio in corso = si ASPETTA.

Scrive: la copia, la valuta (un Python che riscrive LO STESSO file e si
ferma se la riga non è quella), il controllo, il riavvio.
```
cp -p ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.prima-chf
```
```
python3 -c "p='/home/debian/nodo/mostro/settings.toml'; s=open(p).read(); a=\"fiat_currencies_accepted = ['EUR', 'USDT']\"; assert s.count(a)==1, 'riga diversa: fermati'; open(p,'w').write(s.replace(a, \"fiat_currencies_accepted = ['EUR', 'USDT', 'CHF']\")); print('ok')"
```
```
python3 -c "import tomllib; d=tomllib.load(open('/home/debian/nodo/mostro/settings.toml','rb')); print(d['mostro']['fiat_currencies_accepted'])"
```
Atteso: `['EUR', 'USDT', 'CHF']`. Se `tomllib` dice un errore si rimette
la copia (`cp -p ~/nodo/mostro/settings.toml.prima-chf
~/nodo/mostro/settings.toml`) e si chiede a Claude.
```
docker compose restart mostro && sleep 20 && docker compose logs --since 2m mostro | grep -i -E "price|chf|error|warn" | tail -20
```
Atteso: il nodo riparte, i provider dicono «ok (N currencies)», nessun
errore.

**C. La prova a due account sul collaudo**, cifre piccole (10 CHF):
Andrea pubblica «compro sats per 10 CHF via TWINT» (chi paga in franchi
è chi compra i sats), Alan prende, mette il suo numero TWINT, Andrea
paga e segna «Ho inviato i franchi», Alan controlla e libera. A e B
FATTE il 14 nov 2026 verso le 11 (collaudo: salute 200, CHF e i metodi
svizzeri visti da admin; nodo: libro con soli `pending` e stati finali,
riga 111 a `['EUR', 'USDT', 'CHF']`, prezzi pubblicati per 162 valute). Quel che si vede va nel verbale (CANTIERI, «Gli
ordini P2P in franchi svizzeri», «NON PROVATO»). In produzione la leva
resta spenta fino alla promozione e a un sì di Andrea; poi
`P2P_CHF_ATTIVO = True` (solo admin) e, più avanti,
`P2P_CHF_SOLO_ADMIN = False` per tutti.

## 17. Dopo la promozione del cantiere dell'accesso: rientrare con Nostr, a mano (14 nov 2026, cantieri audit-account e audit-parole-bot)

**Perché.** Dal cantiere audit-account la firma del login con Nostr vale
solo per i nomi di casa: barattolo.store, il suo `www.` e l'onion. Le
letture sul VPS le hai già fatte il 14 nov ed erano giuste (stanno in
CANTIERI, «Le parole che avvisano»). Resta la prova col telefono, che
dalla gabbia non si può fare. Va fatta DOPO la promozione su main.

1. Dal telefono, su barattolo.store: esci, e rientra con Nostr come fai
   di solito. Deve entrare come sempre.
2. Se usi l'onion, lo stesso da lì.
3. Sul collaudo (collaudo.barattolo.store) develop è già salito: se lì
   il login con Nostr dicesse «Login Nostr non valido», il nome nel
   config della VM non è quello con cui la apri. Si guarda con:
```
sudo grep -n "^URL_PUBBLICO" /srv/collaudo/barattolo/config.py
```
   Atteso: `https://collaudo.barattolo.store`.

Se uno dei tre non entra, non si tocca niente: si porta la frase
dell'errore alla sessione.

## 18. Il «Contante per posta» sul collaudo: la leva del client (17 nov 2026, cantiere contante-per-posta; Andrea sulla scheda: «Sì, con cauzione obbligatoria»)

**Perché.** L'app ha il nono metodo P2P, «Contante per posta» (la busta
di banconote spedita). La parte del NODO è FATTA (19 nov 2026, col
riavvio della `-bar10`): `only_payment_methods = ["Contanti", "Contante
per posta"]`, quindi chi prende scegliendolo blocca la cauzione
(PRODUZIONE, «LA SALITA ALLA -bar7», il blocco `[anti_abuse_bond]`).
Resta la leva del client sul collaudo, per la prova. Il perché:
CANTIERI, «Il contante per posta: la nona voce del P2P».

**A. LA LEVA DEL CLIENT, SOLO SUL COLLAUDO (17 nov 2026, cantiere
leva-posta; Andrea: «Lasciala spenta la leva per questa funzione. Quando
la porto in produzione, la leva lasciala spenta»).** Il metodo sta dietro
`P2P_POSTA_ATTIVO`, spenta di serie nel codice: in PRODUZIONE NON SI
TOCCA (nessuna riga da aggiungere al config del VPS, la voce non compare
e il pannello «⚙️ Stato delle leve» dice «spento»). Si accende solo
sulla VM di collaudo, dopo che il collaudo ha tirato il commit.

Sola lettura (VM di collaudo):
```
sudo grep -c "^P2P_POSTA_ATTIVO" /srv/collaudo/barattolo/config.py
```
Atteso `0`. Se dice `1`, la riga c'è già: si guarda il valore con
`sudo grep -n "^P2P_POSTA_ATTIVO" /srv/collaudo/barattolo/config.py`.

Scrive (VM di collaudo): la copia, la riga in fondo, il controllo, il riavvio.
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-posta-$(date +%F)
```
```
printf '\n# il contante per posta nel P2P (17 nov 2026): solo qui, in produzione resta spenta\nP2P_POSTA_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso `ok` e `200`. Poi nell'app del collaudo:
P2P → «Pubblica» → «Altri metodi ▾» mostra «Contante per posta», e Info
P2P ha la voce. Senza la riga, la voce non c'è: è il comportamento della
produzione.

## 19. Le raccolte con deposito di garanzia: la leva sul collaudo, per la prova di Alan (17 nov 2026, cantiere raccolta)

**Perché.** Le raccolte fondi arrivano su `develop` con lo zap acceso e il
deposito di garanzia 2-di-3 SPENTO nel codice (`RACCOLTA_GARANTITA_ATTIVA
= False`): è una funzione coi soldi, e la regola del 17 nov vuole prima la
prova di Alan sul collaudo. In produzione NON si accende finché Alan non
dice ok. Il perché di tutto: CANTIERI, «Le raccolte fondi in sats».

**Il collaudo, la leva** (dopo che il collaudo ha tirato `develop` col
cantiere). Sola lettura, deve dire `0`:
```
sudo grep -c "^RACCOLTA_GARANTITA_ATTIVA" /srv/collaudo/barattolo/config.py
```
Scrive: la copia, la riga, il controllo, il riavvio.
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-raccolte
```
```
printf '\nRACCOLTA_GARANTITA_ATTIVA = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. La prova di Alan: un account con 3 vendite e un Lightning
address apre una raccolta con «🛡️ Accetta anche depositi di garanzia»,
un admin le dà il via (Profilo → pannello), un secondo account deposita
50 € dalla scheda, poi si lascia scadere (o la si ferma): il telefono di
chi riceve mette la seconda firma da solo all'apertura dell'app.

## 20. La cauzione del contanti on-chain: il macaroon sul nodo, due righe sul VPS, la prova con Alan (17 nov 2026, cantiere onchain-contanti; Andrea sulla scheda: «In produzione, solo tu e Alan»)

**Perché.** Chi prende in contanti un ordine P2P on-chain blocca prima una
cauzione in Lightning col QR (3%, minimo 1000 sats), che Barattolo tiene
sul nodo e rimanda a fine scambio. Nel codice è SPENTA, e anche accesa la
vede solo un moderatore che prende (`P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN`,
chiusa di serie SENZA nessuna riga da scrivere): per tutti gli altri non
cambia niente. Il perché: CANTIERI, «…terzo pezzo: il metodo scelto alla
presa e la cauzione in Lightning col QR». Va fatto DOPO la promozione
(prima, il server non conosce le righe). Per ora la cauzione TORNA
SEMPRE: il gesto del moderatore che la fa perdere è il pezzo dopo.
(18 nov 2026) Questa voce accende anche la cauzione A SCELTA di chi
pubblica (foglio Pubblica on-chain, «Cauzione di chi prende»): la sua
leva `P2P_ONCHAIN_CAUZIONE_A_SCELTA` è accesa di serie, non c'è nessuna
riga in più da scrivere. Nella prova con Alan: uno pubblica un «Vendi
BTC» on-chain con «🔐 Chiedila» e un metodo online, l'altro lo prende e
deve bloccare la cauzione prima; poi, a deposito confermato, «↩️ Rinuncio»:
la cauzione si perde da sola e nel canale arriva «Cauzione persa da
sola» con la metà da mandare.

**A. SUL NODO (`~/nodo`): il macaroon delle cauzioni, numero 5.**

Sola lettura: gli id già usati (il 5 non deve esserci).
```
docker compose exec lnd lncli listmacaroonids
```
Scrive: cuoce il macaroon (sa coniare, annullare, leggere e saldare una
hold; non sa pagare né aprire canali).
```
docker compose exec lnd lncli bakemacaroon --root_key_id 5 --save_to /tmp/barattolo-cauzione.macaroon uri:/invoicesrpc.Invoices/AddHoldInvoice uri:/invoicesrpc.Invoices/CancelInvoice uri:/lnrpc.Lightning/LookupInvoice uri:/invoicesrpc.Invoices/SettleInvoice
```
Lo mostra in esadecimale: una riga lunga, da COPIARE dal terminale (non
va in chat, in un canale o in un file).
```
docker compose exec lnd xxd -p -c 9999 /tmp/barattolo-cauzione.macaroon
```
(Se manca `xxd`: `docker compose exec lnd sh -c "od -An -tx1 -v /tmp/barattolo-cauzione.macaroon | tr -d ' \n'"`.)
Toglie la copia dal container, e riguarda gli id (ora c'è anche il 5).
```
docker compose exec lnd rm /tmp/barattolo-cauzione.macaroon
```
```
docker compose exec lnd lncli listmacaroonids
```

**B. SUL VPS: le due righe.**

Sola lettura, deve dire `0`:
```
sudo grep -c "^LND_PONTE_MACAROON_CAUZIONE\|^P2P_ONCHAIN_CAUZIONE" /srv/barattolo/config.py
```
Scrive: la copia di riserva.
```
sudo cp -p /srv/barattolo/config.py /root/config-prima-cauzione-onchain-$(date +%F).py
```
Scrive: il macaroon. Chiede prima la password di sudo, poi il macaroon,
che non si vede mentre si incolla. Deve dire «Scritto».
```
sudo -v && read -rsp "Macaroon delle cauzioni (esadecimale): " K && echo && if [[ ! "$K" =~ ^[0-9a-fA-F]{40,}$ ]]; then echo "Non è esadecimale: non scrivo niente"; else printf '\n# la cauzione del contanti on-chain (17 nov 2026): macaroon root_key_id 5\nLND_PONTE_MACAROON_CAUZIONE = %s%s%s\n' '"' "$K" '"' | sudo tee -a /srv/barattolo/config.py > /dev/null && echo "Scritto"; fi; unset K
```
Scrive: la leva.
```
printf 'P2P_ONCHAIN_CAUZIONE = True\n' | sudo tee -a /srv/barattolo/config.py > /dev/null
```
Sola lettura: il file si legge ancora (`ok`) e le righe sono due (`2`).
```
sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"
```
```
sudo grep -c "^LND_PONTE_MACAROON_CAUZIONE\|^P2P_ONCHAIN_CAUZIONE" /srv/barattolo/config.py
```
Scrive: il riavvio, e la salute (atteso `200`).
```
sudo systemctl restart barattolo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://barattolo.store/api/salute
```
Sola lettura: il journal deve dire «🔐 Cauzione del contanti on-chain:
ACCESA SOLO PER I MODERATORI, 3% con minimo 1.000 sats».
```
sudo journalctl -u barattolo -n 200 --no-pager | grep "Cauzione del contanti"
```

**C. LA PROVA, tu e Alan** (uno pubblica, l'altro prende; chi PRENDE deve
essere uno di voi due):
1. Uno pubblica un ordine P2P on-chain col solo metodo «Contanti».
2. L'altro lo apre: nel foglio c'è la riga della cauzione, e il bottone
   apre «🔐 Blocca la cauzione» col QR. Si paga col wallet: il foglio si
   chiude da solo e l'ordine è preso.
3. Nella pagina dello scambio chi l'ha messa vede il riquadro della
   cauzione. Si chiude lo scambio (o lo si annulla): entro un minuto la
   cauzione torna nel wallet.
4. Da un account NON moderatore: lo stesso ordine non mostra nessuna
   cauzione.

5. LA CAUZIONE BRUCIATA (un secondo scambio, e serve un TERZO moderatore
   che non sia parte: il secondo account di Andrea). Come sopra fino al
   passo 2; poi uno dei due apre la disputa. Il terzo moderatore apre lo
   scambio, tocca «🔐 Brucia la cauzione» e conferma. Nel canale dei
   moderatori arriva «DA MANDARE A MANO: N sats a…»: li manda dal suo
   wallet e tocca «✅ Metà mandata». Poi decide la disputa come sempre.

Da guardare e riferire: il wallet ha pagato la hold dal QR? È tornata?
Bruciata, i sats sono rimasti fuori dal wallet di chi l'aveva messa?

**PER SPEGNERE:** via la riga `P2P_ONCHAIN_CAUZIONE` e riavvio, LASCIANDO
il macaroon finché ci sono cauzioni vive. **PER APRIRE A TUTTI** (a prova
fatta): la riga `P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN = False` e riavvio.

## 21. L'inglese sul collaudo: la leva `LINGUA_INGLESE` accesa (17 nov 2026 sera, cantiere inglese-tappa-2)

**Perché.** Andrea ha deciso che l'inglese arriva in produzione SPENTO
(«L'inglese della prima parte lascialo spento»): la leva nasce False
nel codice. Sul collaudo invece va ACCESA, per provare l'app in inglese
(`https://collaudo.barattolo.store/?lingua=en`). In produzione non si
tocca niente finché Andrea non lo dice.

**Sola lettura (sulla VM di collaudo):**
```
sudo grep -n "^LINGUA_INGLESE" /srv/collaudo/barattolo/config.py
```

**Poi, se la riga non c'è (sulla VM di collaudo, mai sul VPS):**
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-inglese
printf '\nLINGUA_INGLESE = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/lingua/en.js
```
Atteso: `200`. Poi l'app con `?lingua=en` parla inglese.

## 22. La Rotta per la Luna: la leva sul collaudo (17 nov 2026, cantiere stradina; Andrea: «anche il tabellone lascialo spento per il momento»)

**Perché.** Il tabellone arriva in produzione SPENTO (`STRADINA_ATTIVA =
False` nel codice, eccezione decisa da te alla regola delle leve nuove
accese). Sul collaudo lo accendi per provarlo; in produzione resta spento
finché non dici tu. Il perché: CANTIERI, «La Rotta per la Luna nasce spenta».

**Il collaudo, la leva** (dopo che il collaudo ha tirato `develop` col
cantiere). Sola lettura, deve dire `0`:
```
sudo grep -c "^STRADINA_ATTIVA" /srv/collaudo/barattolo/config.py
```
Scrive: la copia, la riga, il controllo, il riavvio.
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-rotta
```
```
printf '\nSTRADINA_ATTIVA = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi nel bot di collaudo: Profilo → «Livello e recensioni» →
«🚀 Rotta per la Luna». **In produzione** la stessa riga nel config del VPS
la accende per tutti, quando decidi tu.

## 23. Le sottocategorie agli annunci già pubblicati, dopo la promozione (18 nov 2026, cantiere sottocategorie)

**Perché.** Dalla promozione, toccando una categoria in Esplora si apre la
tendina delle sottocategorie. Gli annunci nuovi la sottocategoria la
prendono da soli; quelli vecchi l'hanno presa solo se sono nati dopo
agosto o se nessuno ha mai lanciato lo script. Quelli senza si vedono
sempre in «Tutta la categoria», ma non nelle voci della tendina. Lo script
`assegna_sottocategorie.py` riempie SOLO i vuoti, e dove non è sicuro li
lascia vuoti. Nessuna leva da toccare: `SOTTOCATEGORIE_VETRINA` è accesa
di serie.

**VPS, da root, dopo la promozione.** Il primo comando legge e basta: dice
quante righe sono già assegnate e quante ancora vuote.
```
cd /srv/barattolo && sudo -u barattolo python3 assegna_sottocategorie.py --conta /srv/barattolo/dati/satmarket.db
```
L'anteprima, che non scrive niente: dice cosa farebbe.
```
cd /srv/barattolo && sudo -u barattolo python3 assegna_sottocategorie.py /srv/barattolo/dati/satmarket.db
```
Se l'anteprima ti convince, prima la copia del database:
```
python3 -c "import sqlite3; s=sqlite3.connect('file:/srv/barattolo/dati/satmarket.db?mode=ro', uri=True); d=sqlite3.connect('/root/prima-sottocategorie.db'); s.backup(d); d.close(); s.close(); print('copia ok')"
```
Poi lo scrive, da `barattolo` (non da root: un file nato da root il
servizio non lo sa più riscrivere):
```
cd /srv/barattolo && sudo -u barattolo python3 assegna_sottocategorie.py --scrivi /srv/barattolo/dati/satmarket.db
```
Nessun riavvio: la tendina conta le righe a ogni apertura della vetrina.
Si rilancia quando vuoi, tocca solo i vuoti.

## 24. Le 14 sottocategorie nuove: niente da fare (18 nov 2026, cantiere sottocategorie-nuove)

I 38 annunci delle 14 voci nuove li ha già scritti Andrea il 18 nov
(`sottocategorie_nuove.py`, subito, su sua richiesta: «i 38 rimasti
risolvili adesso»). Si vedono nella tendina con la promozione che porta
l'albero nuovo. Restano senza sottocategoria solo 14 annunci di prova
(«Prova», «Test», «Balu», «Tastiera»).

## 26. L'ordine scaduto che torna nel libro: la prova dal vivo della `-bar11` (19 nov 2026, cantiere ritorno-nel-libro)

**La `-bar11` È SUL NODO dal 19 nov, 11:52 UTC** (passi 1-9 fatti: PRODUZIONE,
«LA `-bar11`»). Resta solo la prova, DOPO la promozione.

La prova dal vivo coi tuoi due account (DOPO la promozione: il server
deve sapere che il tempo parte dal recapito): una vendita col solo SEPA
Instant e il cursore a 15 minuti, presa dall'altro, garanzia pagata.
Prima di «Indica dove ricevere gli euro» l'anello di chi compra dice che
il tempo non è partito; chi vende lo tocca, e da lì partono i 15 minuti.
NON toccare «Ho inviato gli euro». Dopo il quarto d'ora (entro un minuto
in più) lo scambio scade, la garanzia torna, l'ordine è di nuovo nel
libro, e arrivano i due messaggi «⏰ Il tempo per pagare è finito…».

ROLLBACK (solo se la `-bar11` non regge): `cd ~/nodo && cp -p docker-compose.yml.prima-bar11 docker-compose.yml && docker compose up -d mostro`
→ `-bar10`; il database resta quello (la colonna in più la `-bar10` la
ignora), e il sorgente torna con `git -C ~/nodo/mostro-src reset --hard HEAD~1`.
Fatta la prova, questa voce si cancella.

## 27. «↩️ Riprendi i sats» on-chain: la prova in produzione coi due account moderatori (19 nov 2026, cantiere regole-sulla-card; Andrea: «proviamolo direttamente in produzione, ovviamente con una leva accesa solo per me ed Alan»)

**Niente da scrivere nel config**: le due leve sono di serie accesa e
chiusa ai soli moderatori (`P2P_ONCHAIN_RIPRENDI_SCADUTO`,
`P2P_ONCHAIN_RIPRENDI_SCADUTO_SOLO_ADMIN`), e arrivano con la promozione.
Si guardano nel pannello «⚙️ Stato delle leve».

La prova (DOPO la promozione), con due account moderatori:
1. Dal tuo account pubblica un «Vendi BTC» on-chain col SEPA Instant e il
   tempo per pagare a 15 minuti.
2. Dall'altro lo prendi; in cima al foglio deve esserci la riga «⏱ Se lo
   prendi hai 15 minuti…». Nel bot dell'altro, quando il tempo parte,
   arriva «⏳ Tempo per pagare: mancano 15 minuti», che cambia ogni minuto
   senza suonare.
3. Dal tuo account deposita i bitcoin e scrivi dove vuoi gli euro. L'altro
   NON tocca «Ho inviato gli euro».
4. Finiti i 15 minuti, dal tuo account apri lo scambio: tocca «↩️ Riprendi
   i sats», conferma, poi «✍️ Metti la seconda firma».
5. Deve risultare «rimborsato», i bitcoin tornano al tuo indirizzo di
   ritorno, l'ordine è di nuovo nel libro (ritiralo con «🚫 Non
   ripubblicarlo»), e il messaggio del bot dell'altro dice «Il tempo per
   pagare è finito».

Andata bene, la porticina si apre a tutti con UNA riga nel config del VPS e
il riavvio: `P2P_ONCHAIN_RIPRENDI_SCADUTO_SOLO_ADMIN = False`. Fatta, questa
voce si cancella.

## 28. Le due prove dal vivo della `-bar12` (19 nov 2026, cantieri pubblica-col-tempo e recapito-nel-tempo)

La `-bar12` è IN SERVIZIO sul nodo dal 19 nov 2026, 22:16 UTC (PRODUZIONE,
«LA `-bar12`»). Le regole nuove partono quando il server in produzione
le chiede, cioè DOPO LA PROMOZIONE che porta 0f69ee63, a336356e e
e512e213. Poi, coi tuoi due account:

1) Una vendita Lightning col solo SEPA Instant e il cursore a 15 minuti.
Dall'altro account la prendi: la pagina dello scambio deve dire «Chi ha
pubblicato ha fino a 15 minuti per rispondere». Dal primo NON pagare la
garanzia: dopo 15 minuti (entro un minuto in più) l'ordine torna nel
libro e arriva «tornato nel libro». Nel journal del nodo:
`docker compose logs mostro --since 30m | grep "at most 15 minutes"`.

2) «Dove vuoi gli euro»: stessa vendita a 15 minuti, la prendi, dal primo
account paghi la garanzia ma NON tocchi «Indica dove ricevere gli euro».
Arrivano i due promemoria (a 7 minuti e mezzo e a 5 dalla fine); dopo 15
minuti dall'attivo (entro un minuto in più) l'ordine torna nel libro,
arriva «Non hai detto in tempo dove ricevere gli euro» e la garanzia torna.

ROLLBACK (solo se la `-bar12` non regge): `cd ~/nodo && cp -p
docker-compose.yml.prima-bar12 docker-compose.yml && docker compose up -d
mostro` → `-bar11`; il sorgente torna con `git -C ~/nodo/mostro-src reset
--hard HEAD~1`. Fatte le due prove, questa voce si cancella.

## 29. Le gift card di Bitpost sul collaudo (20 nov 2026, cantiere bitpost-gift-card; Andrea: «procedi pure con una implementazione in collaudo per fare dei test»)

Il codice è su develop e il collaudo lo tira da solo; la leva nasce
SPENTA, quindi finché non scrivi queste righe non cambia niente. ⚠️ Il
collaudo qui parla col Bitpost VERO (beta.bitpost.shop) e coi SATS VERI
(mainnet): minimo 42 € a ordine, il tetto nostro resta 250 €.
⚠️ La chiave API e il segreto del webhook mandati da Gabriele il 20 nov
sono finiti in chiaro in chat: prima di questi passi chiedigli una
coppia nuova (regola ferrea 1). I passi, un comando alla volta.

**DAL 21 NOV 2026 BASTA IL PANNELLO, niente ssh** (Andrea: «i segreti
non li puoi mettere nel gruppo config di bitpost gift card?»). Sul
collaudo, dalla Mini App: Profilo → Amministrazione → «⚙️ Stato delle
leve» → gruppo «🎁 Gift card Bitpost». Lì: incolla la chiave API e tocca
«Salva», poi il segreto del webhook e «Salva» (non si rivedono più; a
ogni salvataggio arriva un avviso ai moderatori), poi accendi «Gift card
Shoppy Code via Bitpost» lasciando acceso «Solo gli admin». Se la leva
dice «dal prossimo riavvio», vale al prossimo aggiornamento di develop.
A Gabriele va detto l'indirizzo del webhook del collaudo:
`https://collaudo.barattolo.store/api/bitpost/webhook`. I comandi qui
sotto restano la strada dal VPS, per chi preferisce il config.

La copia del config, prima di toccarlo:
```
sudo cp -p /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-bitpost
```
La chiave API nel suo file (non si vede mentre la incolli; deve dire
«Scritta»):
```
sudo -v && read -rsp "Chiave API di Bitpost: " K && echo && if [ -z "$K" ]; then echo "Vuota: non scrivo niente"; else printf '%s' "$K" | sudo tee /etc/barattolo-collaudo/bitpost_api_key > /dev/null && sudo chown root:collaudo /etc/barattolo-collaudo/bitpost_api_key && sudo chmod 640 /etc/barattolo-collaudo/bitpost_api_key && echo "Scritta"; fi; unset K
```
Il segreto del webhook, uguale:
```
sudo -v && read -rsp "Segreto del webhook di Bitpost: " K && echo && if [ -z "$K" ]; then echo "Vuoto: non scrivo niente"; else printf '%s' "$K" | sudo tee /etc/barattolo-collaudo/bitpost_webhook > /dev/null && sudo chown root:collaudo /etc/barattolo-collaudo/bitpost_webhook && sudo chmod 640 /etc/barattolo-collaudo/bitpost_webhook && echo "Scritto"; fi; unset K
```
Le righe del config (la leva resta solo per i moderatori):
```
printf '\nBITPOST_API_KEY = _segreto("bitpost_api_key")\nBITPOST_WEBHOOK_SEGRETO = _segreto("bitpost_webhook")\nBITPOST_ATTIVO = True\nBITPOST_SOLO_ADMIN = True\nBITPOST_MAX_EURO = 250\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
Il file si legge ancora (deve dire `ok`), poi il riavvio (atteso 200):
```
sudo python3 -c "import ast; ast.parse(open('/srv/collaudo/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo-collaudo && sleep 30 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
La porta del webhook risponde senza firma con 401 (è giusto: vuol dire
che c'è e che chiede la firma):
```
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://collaudo.barattolo.store/api/bitpost/webhook
```
LA PROVA, coi due account moderatori su @barattolo_collaudo_bot (servono
le 12 parole on-chain già al sicuro su tutt'e due):
nella vetrina il bottone «🎁 Gift card» fra Mercato e Lavoro. Dal primo «Compra»: una carta da 50 €
(il minimo è 42), «Chiedi le carte». Dal secondo, scheda «Bitworker»:
«Prendi». Dal primo, «I miei»: paga da Sparrow ESATTAMENTE i sats
mostrati, in una transazione. Dopo le conferme il secondo vede l'email
di Bitpost: compra la carta su Shoppy Code e la regala a quell'email. Il
primo apre la carta («Apri»), la prova e tocca «✅ Funzionano». Il
secondo scrive un SUO indirizzo bc1 e «Chiedi l'incasso», poi «Firma».
Quel che si vede (e gli errori, parola per parola) va nel verbale:
CANTIERI, «Le gift card di Bitpost», «COSA RESTA». Fatta la prova,
questa voce si cancella.

## 30. L'abbonamento a «Bitcoin On»: collegare il canale (20 nov 2026, cantiere abbonamento-canale; Andrea: «chi compra il mio abbonamento accede in maniera diretta al canale Telegram»)

**Perché.** Il codice c'è (leva `ABBONAMENTI_CANALE`, accesa di serie), ma
resta inerte finché il canale non è collegato: serve il bot amministratore
del canale e una riga nel config del VPS. Va fatto DOPO la promozione su
main. Il giro intero: Cantieri, «L'abbonamento a un canale Telegram».

**1) Telegram (dal telefono o dal desktop).** Canale «Bitcoin On» →
Amministratori → Aggiungi amministratore → `@ilbarattolobot`. Permessi:
«Aggiungi iscritti» (o «Invita utenti tramite link») e, se compare,
«Banna utenti». Gli altri permessi non servono: spegnili.

**2) L'id del canale.** Comincia con `-100`. Si legge da
https://web.telegram.org/a aprendo il canale: l'indirizzo finisce con
`#-100…`. (Se vuoi lo legge Claude dal tuo Telegram desktop.)

**3) Sola lettura, sul VPS (root).** Che la riga non ci sia già:
```
grep -n "^CANALI_ABBONAMENTO\|^ABBONAMENTI_CANALE" /srv/barattolo/config.py
```

**4) La riga, sul VPS (root).** Prima la copia, poi la riga. Al posto di
`ID_VENDITORE` il numero dell'account che vende (il tuo principale è
1879103467) e al posto di `ID_CANALE` il numero del passo 2:
```
cp -p /srv/barattolo/config.py /srv/barattolo/config.py.prima-abbonamento
```
```
printf '\nCANALI_ABBONAMENTO = {ID_VENDITORE: ID_CANALE}\n' | sudo tee -a /srv/barattolo/config.py
```
```
systemctl restart barattolo && sleep 5 && journalctl -u barattolo --since "1 min ago" | grep -i "webhook"
```
Deve comparire la riga «🔔 Webhook Telegram»: da lì il bot riceve anche le
richieste d'ingresso.

**5) I permessi del bot, sul VPS (root, sola lettura: stampa solo due sì/no).**
```
cd /srv/barattolo && sudo -u barattolo python3 -c "import config,json,urllib.request as u; c=list(config.CANALI_ABBONAMENTO.values())[0]; me=json.load(u.urlopen(f'https://api.telegram.org/bot{config.BOT_TOKEN}/getMe'))['result']['id']; r=json.load(u.urlopen(f'https://api.telegram.org/bot{config.BOT_TOKEN}/getChatMember?chat_id={c}&user_id={me}'))['result']; print('invita:', r.get('can_invite_users'), '| banna:', r.get('can_restrict_members'))"
```
Devono essere `True` tutti e due.

**6) L'annuncio.** Dal tuo account: Vendi → «💾 Invio del codice online» →
spunta «🔑 Abbonamento al mio canale Telegram» → prezzo in euro (25 €).

**7) La prova dal vivo, col secondo account (8711624959).** Abbassa il
prezzo per la prova, compra, apri l'ordine, «🔓 Rivela», tocca il link:
devi entrare nel canale, l'ordine chiudersi e i sats arrivarti subito.
Poi rimetti 25 €. Lo stesso link aperto da un terzo account deve essere
rifiutato. L'espulsione si vede solo dopo 33 giorni: la ronda gira da sola.

**ROLLBACK.** Togliere la riga (`cp -p
/srv/barattolo/config.py.prima-abbonamento /srv/barattolo/config.py`) e
riavviare: niente link né espulsioni, e gli abbonati già dentro restano.

## 31. «Non hai sats?»: la prova vera del giroconto in produzione, coi moderatori (23 nov 2026, cantiere giroconto-interno)

**Stato.** SCELTA DI ANDREA (23 nov, 21:01): «Produzione, solo tu e Alan».
Va fatta DOPO la promozione che porta il cantiere su main. Il collaudo ha i pagamenti FINTI (LNbits FakeWallet), il deposito non sta
sul nodo e Mostro non lo può saldare, quindi la prova vera si fa in
produzione col tasto visibile ai soli moderatori (`VIA_EURO_SOLO_ADMIN`,
di serie True: arriva con la promozione, nessuna riga da scrivere).

**Perché.** Chi non ha sats compra un oggetto pagando euro nel P2P: Mostro
chiede al server «la saldi tu?», il server controlla la garanzia di chi
vende i sats e paga il deposito dal portafoglio «riserva». Il giro intero:
Cantieri, «Il giroconto interno». Senza i tre pezzi sotto la porta resta
CHIUSA (404) e il tasto non compare a nessuno.

**Ordine dei passi: PRIMA il server (promozione), POI la riserva e il
segreto sul VPS, POI la `-bar13` sul nodo.** Il nodo nuovo davanti a un
server senza porta prende 404 e paga come la `-bar12`.

**1) La riserva, dal pannello di LNbits nodo** (il tunnel di sempre
dal PC verso il VPS sulla porta 5001, poi `http://127.0.0.1:5001`, super
utente). Nuovo portafoglio «Riserva giroconti». Dentro: «Ricevi» →
20.000 sats per la prova (la scorta vera, 300.000, solo dopo) → paga la
fattura dal telefono. La chiave ADMIN di quel portafoglio si copia SOLO
nel `read -s` del passo 3, mai in chat.

**2) Sola lettura, sul VPS (root).** Che le righe non ci siano già:
```
grep -n "^P2P_GIROCONTO_SEGRETO\|^LNBITS_RISERVA_ADMIN_KEY\|^VIA_EURO" /srv/barattolo/config.py
```

**3) Le due righe, sul VPS (root).** Copia, poi la chiave (incollata al
buio), poi il segreto che nasce lì e non si stampa:
```
cp -p /srv/barattolo/config.py /srv/barattolo/config.py.prima-giroconto
```
```
read -s -p "Admin key della riserva: " K && printf '\nLNBITS_RISERVA_ADMIN_KEY = "%s"\n' "$K" | sudo tee -a /srv/barattolo/config.py >/dev/null && unset K && echo ok
```
```
S=$(python3 -c "import secrets;print(secrets.token_hex(32))") && printf 'P2P_GIROCONTO_SEGRETO = "%s"\n' "$S" | sudo tee -a /srv/barattolo/config.py >/dev/null && echo "impronta: $(printf %s "$S" | sha256sum | cut -c1-8)" && unset S
```
```
systemctl restart barattolo && sleep 5 && curl -s -o /dev/null -w "%{http_code}\n" -X POST https://barattolo.store/api/p2p/giroconto
```
Deve dire `403` (la porta c'è, il segreto no). `404` = manca un pezzo
(la chiave, il segreto o il macaroon delle cauzioni).

**4) La `-bar13` sul nodo.** La procedura è quella della `-bar12`
(PRODUZIONE, «LA `-bar12`»), con la sola `0016-*.patch`:
sorgente pulito sul branch `barattolo/v0.20.2`, albero `deb731c3`;
`git am` della `0016-*.patch` → l'albero deve cominciare con `7408b7fa`
(lo stesso del cloud); i test nello stadio `builder` col filtro di sempre
più `barattolo_giroconto` (4 test nuovi, 0 rossi); nel binario la parola
`BARATTOLO_GIROCONTO_URL`. Il compose `.bar13`: l'immagine
`mostro:v0.20.2-bar13` e due righe accanto a quelle della FINESTRA,
`BARATTOLO_GIROCONTO_URL=https://barattolo.store/api/p2p/giroconto` e
`BARATTOLO_GIROCONTO_SEGRETO` (lo stesso valore del passo 3, copiato dal
terminale del VPS al `read -s` del nodo; impronta uguale). Copia
`docker-compose.yml.prima-bar13`, libro fermo come sempre, poi il cambio.
Nel log del nodo NON deve esserci «giroconto … not set».

**5) La prova, piccola.** Tre account:
- Andrea (principale) pubblica un oggetto da 3-5 €, spedizione a mano.
- Alan pubblica «Vendi BTC» a prezzo di mercato, SEPA Instant o Satispay.
- Il secondo account di Andrea (8711624959, moderatore) SENZA indirizzo
  Lightning né wallet on-chain nel profilo: apre l'oggetto, accanto a
  «Paga» deve esserci «Non hai sats?»; lo tocca, sceglie il metodo,
  «Continua», poi segue il foglio fino a «Ho pagato» (manda davvero gli
  euro ad Alan).
- Alan riceve gli euro e rilascia.
- (24 nov, cantiere chiedi-al-venditore) Una seconda volta con Alan che
  vende a CIFRA FISSA più grande (per esempio 30 € esatti per un oggetto
  da 5 €): a «Continua» il foglio dice che sta cercando; ad Alan arriva il
  bot «Un compratore del mercatino vuole…»; «Sì, va bene» dalla pagina del
  suo ordine lo trasforma in «da 5 a 30 €», e il foglio dell'altro account
  torna al prezzo col «Continua» di sempre.

Deve succedere: l'ordine passa a pagato (locked) da solo; la riserva scende
di quanto il deposito; nel log del nodo
`Order …: giroconto done, the marketplace settled hash …`; nel journal del
VPS niente righe rosse col 🔁. Poi la ronda del nodo:
```
sudo /usr/local/bin/ronda-nodo.sh
```
Se segnala un «PAGAMENTO SCONOSCIUTO» legato alla prova:
`sudo /usr/local/bin/ronda-nodo.sh --impara <prime 8 lettere dell'hash>`.
Quel che si vede va nel verbale (CANTIERI, «Il giroconto interno»).

**ROLLBACK.** Server: `cp -p /srv/barattolo/config.py.prima-giroconto
/srv/barattolo/config.py` e riavvio (porta 404, il tasto sparisce). Nodo:
`cp -p docker-compose.yml.prima-bar13 docker-compose.yml && docker compose
up -d mostro`. I sats rimasti nella riserva restano lì.

## 32. Spegnere il riquadro «fase di test» in produzione (23 nov 2026, cantiere scoprire-quadrati; Andrea: «levamelo quello lì anche, spegnilo dalla lista, il riquadro fase di test»)

**Perché.** La fascia in home se ne va col codice (alla prossima
promozione). Il riquadro che compare una volta al giorno all'apertura
invece lo accende la riga `BANNER_TEST` del config del VPS: si spegne lì,
senza codice. Si può fare anche subito, prima della promozione.

**Sola lettura:**
```
grep -n "^BANNER_TEST" /srv/barattolo/config.py
```
Se non esce `BANNER_TEST = True`, non c'è niente da fare.

**Scrive** (dopo il sì di Andrea, già dato il 23 nov):
```
cp -a /srv/barattolo/config.py /root/config-prima-banner-test-$(date +%F).py
```
```
sudo sed -i 's/^BANNER_TEST = True/BANNER_TEST = False/' /srv/barattolo/config.py && grep -n "^BANNER_TEST " /srv/barattolo/config.py
```
```
sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"
```
```
sudo systemctl restart barattolo && sleep 5 && curl -s -o /dev/null -w 'salute %{http_code}\n' http://127.0.0.1:8080/api/salute
```
Atteso `BANNER_TEST = False`, `ok` e `salute 200`. Riaprendo l'app il
riquadro non compare più.

## 34. I prezzi a scalini delle promozioni: guardare il config del VPS (25 nov 2026, cantiere mensola-a-step)

**Perché.** Con la prossima promozione i prezzi delle tre promozioni
vanno a scalini (più posti presi, più costa) e «In evidenza» si chiama
«Mensola». Le leve vecchie dei prezzi fissi (`PROMO_IN_CIMA_SATS`,
`PROMO_EVIDENZA_SATS`, `PROMO_SCOPRIRE_SATS`) non le legge più nessuno:
se sono scritte nel config del VPS restano lì innocue, ma ingannano chi
le legge. Le scale nuove valgono di serie dal codice.

**Sola lettura** (prima della promozione):
```
grep -n "^PROMO_" /srv/barattolo/config.py
```
Se non esce niente, o escono solo `PROMO_IN_CIMA_ORE`,
`PROMO_EVIDENZA_POSTI`, `PROMO_SCOPRIRE_GIORNI` e `PROMO_GIORNI_VENDITORE`,
non c'è niente da fare. Se escono le tre righe `..._SATS`, si possono
togliere a mano (copia del config prima) quando vuoi: non cambiano
niente.

**Dopo la promozione** si vede nel pannello «⚙️ Stato delle leve»,
gruppo delle promozioni: le tre scale coi loro scalini.

## 35. Il resto dell'intervallo torna nel libro: la prova in produzione coi due account moderatori (27 nov 2026, cantiere resto-intervallo; Andrea: «lo proviamo in produzione io e Alan, non nel collaudo»)

**Niente da scrivere nel config**: le due leve sono di serie accesa e
chiusa ai soli moderatori (`P2P_RESTO_INTERVALLO`,
`P2P_RESTO_INTERVALLO_SOLO_ADMIN`), e arrivano con la promozione. Si
guardano nel pannello «⚙️ Stato delle leve».

La prova (DOPO la promozione), dal tuo account e da quello di Alan:
1. Lightning, Vendi: pubblica dal tuo account un ordine a mercato da 10 a
   100 €. Nella scatola arancione deve esserci «Se ne prendono solo una
   parte, il resto torna da solo nel libro.»
2. Alan lo prende per 20 €, paga e tocca «Ho inviato»; tu liberi i sats.
3. Entro un paio di minuti, nel libro e fra i tuoi scambi deve comparire
   un ordine tuo da 10 a 80 €, con gli stessi metodi. Ritiralo se non lo
   vuoi tenere.
4. Lightning, Compra: lo stesso al contrario (tu pubblichi un Compra 10–100
   €, Alan vende 20 €, tu tocchi «Ho inviato», Alan libera): deve
   ricomparire il tuo Compra 10–80 €.
5. On-chain: un Vendi BTC 10–100 € preso per 20 €; a scambio concluso
   deve ricomparire nel libro un ordine 10–80 €.

Se il resto non compare su Lightning, da «Info P2P» tocca «🩺 Copia la
diagnosi» e incollala nel thread: le righe «resto …» dicono cosa ha fatto
il telefono.

Andata bene, si apre a tutti con UNA riga nel config del VPS e il riavvio:
`P2P_RESTO_INTERVALLO_SOLO_ADMIN = False`. Fatta, questa voce si cancella.

## 36. La CI a pezzi: dopo la promozione, guardare `pronto` e spegnere il runner della VM (27 nov 2026, cantiere ci-a-pezzi; Andrea: «sistema la questione delle CI troppo lente»)

**Alla promozione che la porta**: è un commit che cambia
`.github/workflows/prove.yml`, quindi `pronto` potrebbe restare indietro.
A CI verde si guarda (sola lettura, dal PC):
`git ls-remote origin refs/heads/pronto refs/heads/main` — i due sha
devono essere uguali. Se `pronto` è rimasto indietro:
`git push origin origin/main:refs/heads/pronto`.

Il primo giro deve mostrare in Actions undici pezzi che partono insieme
(«pezzo delle prove 1/5» … «pezzo dei collaudi 6/6»), poi `prove` e
`pronto`: in tutto circa 6 minuti invece di 39.

**Poi, quando vuoi (niente fretta, non rompe niente se resta):**
1. GitHub → Settings → Secrets and variables → Actions → Variables:
   cancella `RUNNER_PROVE` (non la legge più nessuno).
2. Sulla vm-2050, da `debian` con sudo, spegni il runner (libera
   processore e memoria al bot di collaudo):
   `sudo systemctl disable --now ci-runner-vm-2050`
   e controlla: `systemctl is-active ci-runner-vm-2050` deve dire
   `inactive`.
3. GitHub → Settings → Actions → Runners: togli `vm-2050` (Remove). Un
   runner nostro collegato a un repo pubblico è una porta che non serve.

Fatti i tre gesti, questa voce si cancella.

## 37. Ritirare da Nostr i badge dei distintivi usciti (27 nov 2026, cantiere badge-nostr-tre; Andrea: «semplifica i badge su Nostr», poi «Ritirarli da Nostr»)

**Dopo la promozione che lo porta in produzione**, dalla Mini App:
pannello admin → «🏺 Badge Nostr» → «🧹 Ritira da Nostr i badge degli
altri distintivi» → «Ritira». Restano su Nostr solo 🫙 Pioniere, 🛡️
Specchiato e i badge degli eventi. Se il messaggio dice «N da riprovare»,
ripremi: chi è già ritirato non si tocca. Poi «🔄 Sincronizza i
distintivi», che dà lo Specchiato a chi ha già 25 affari.

Fatto e con «0 da riprovare», questa voce si cancella.

## Dopo il deploy · i canali come rich message (28 nov 2026, Andrea)
PERCHÉ: i post escono con `sendRichMessage` (tendine vere) e non è provato dal vivo. Dopo il deploy guarda UN post nuovo in ciascun canale (Barattolo Vetrina, Subito Crypto, BitcoinPodcast). Se esce col vecchio formato (foto con citazioni), Telegram ha rifiutato il rich: cerca il motivo nel journal (sola lettura):

    sudo journalctl -u barattolo --since "1 hour ago" | grep "Rich message rifiutato"

Se serve tornare indietro subito: `POST_CANALI_RICH = False` nel config del VPS e riavvio. Fatto e visto, questa voce si cancella.
