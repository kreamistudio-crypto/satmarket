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

## 18. La cauzione anche sul «Contante per posta»: una riga nel settings.toml del nodo (17 nov 2026, cantiere contante-per-posta; Andrea sulla scheda: «Sì, con cauzione obbligatoria»)

**Perché.** L'app ha il nono metodo P2P, «Contante per posta» (la busta
di banconote spedita). La cauzione di chi prende la decide il NODO, dalla
lista `only_payment_methods` del blocco `[anti_abuse_bond]` (patch 0008 e
0010 del fork): oggi c'è solo «Contanti», quindi chi prende un ordine
scegliendo «Contante per posta» NON blocca niente finché la riga non
cambia. Il client non promette niente da solo: legge la lista dal 38385.
Il confronto è a parola intera, senza maiuscole, voce per voce (la
virgola separa): «Contante per posta» va scritto così, intero. Il perché:
CANTIERI, «Il contante per posta: la nona voce del P2P». Va fatto DOPO la
promozione (prima, nessun client la manda), e a LIBRO FERMO.

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

**B. LA CAUZIONE, SUL NODO.** Va fatto solo quando la leva si accenderà
in produzione (oggi no): finché la voce non si offre a nessuno, la riga
del nodo non serve, e aggiungerla prima non fa danni ma non prova niente.

Sola lettura (NODO):
```
grep -n "only_payment_methods" ~/nodo/mostro/settings.toml
```
Atteso: `only_payment_methods = ["Contanti"]`. Se c'è già «Contante per
posta», non c'è niente da fare.

**Scrive (NODO), a libro fermo:** la copia, la riga, la rilettura, il riavvio.
```
cp -p ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.prima-posta-$(date +%F)
```
```
sed -i 's/^only_payment_methods = \["Contanti"\]$/only_payment_methods = ["Contanti", "Contante per posta"]/' ~/nodo/mostro/settings.toml
```
```
grep -n -A7 "^\[anti_abuse_bond\]" ~/nodo/mostro/settings.toml
```
Atteso: il blocco di sempre, con `only_payment_methods = ["Contanti", "Contante per posta"]`.
```
cd ~/nodo && docker compose restart mostro && sleep 20 && docker compose logs --tail=30 mostro
```
Nei log nessun errore di settings. Poi dal telefono, su un ordine che
accetta «Contante per posta»: scegliendolo alla presa la riga «🔐 La
cauzione di chi prende» compare (col testo «col contante per posta»),
scegliendo SEPA no. Fatta, questa voce si cancella e il nuovo valore va
in PRODUZIONE («LA SALITA ALLA -bar7», il blocco `[anti_abuse_bond]`).

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
