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

## 4. Mostro 0.20.2 sul nodo: la salita alla `-bar9` (29 ott 2026, cantiere mostro-0202, decisione di Andrea: «fork intero sulla 0.20.2»)

**Perché.** Dalla nostra 0.19.0 upstream ha fatto sei versioni
(0.19.1 → 0.20.2, 28 ott). La ragione forte è la cura #910 (0.19.1):
oggi un venditore può pagare la garanzia e annullare un istante dopo —
si riprende i sats, e intanto al compratore arriva «pagato, manda gli
euro». Con lei anche le dispute scritte tutte insieme (#923), i limiti
in sats col premio (#1095), la manutenzione da sola se LND resta
indietro (#1065), e la base per gli USDT (spenta, decisione di Andrea
a parte). Il fork è stato RIFATTO sulla `v0.20.2` e, per la prima
volta, compilato e provato nel cloud prima del nodo (`deploy/mostro`,
CANTIERI «Mostro 0.20.2»). La liturgia intera, un comando alla volta,
sta in PRODUZIONE, «LA SALITA ALLA 0.20.2». ⚠️ Due cose che la 0.19.0
non aveva: il `settings.toml` VUOLE la riga `bond_cltv_delta` dentro
`[anti_abuse_bond]` (fra 721 e 864 col nostro `hold_invoice_cltv_delta
= 576`; senza, `mostrod` non parte), e il database prende UNDICI
migrazioni: il ritorno alla `-bar8` vuole la copia del database di
prima, non solo la riga dell'immagine.

**Sola lettura, PRIMA (host NODO, `cd ~/nodo`):**
```
docker inspect nodo-mostro-1 --format '{{.Config.Image}}'
```
```
git -C ~/nodo/mostro-src status --short | wc -l && git -C ~/nodo/mostro-src log --oneline v0.19.0..HEAD | wc -l
```
```
grep -n -E "^hold_invoice_cltv_delta|^escrow_deadline_margin_blocks|^bond_cltv_delta|^expiration_seconds|^maker_expiration_seconds|^maker_timeout_limit|^fiat_currencies_accepted|^\[" ~/nodo/mostro/settings.toml
```
```
grep -c "BARATTOLO_EVENTI_SEGRETO" ~/nodo/docker-compose.yml
```
```
df -h / && docker system df
```
Attesi: `mostro:v0.19.0-bar8`; `0` e `11` (albero pulito, undici
commit); `576`, `24`, NESSUNA riga `bond_cltv_delta`, `1800`, `10800`,
`2`, `['EUR']`, e `[anti_abuse_bond]` come ULTIMA sezione (così la
riga nuova si accoda in fondo al file); `1` per il segreto degli
eventi (se è `0` ci si ferma: col fork nuovo senza quella variabile
gli eventi al server si SPENGONO — M6 dell'audit, mai arrivata sul
nodo); almeno 6 GB liberi (la cucina della build ne prende 3).
Il resto, scrivendo, sta in PRODUZIONE: backup (database con l'API di
sqlite, compose, settings), `git am` delle undici `.patch`, i test
nello stadio `builder`, la build `mostro:v0.20.2-bar9`, la riga
`bond_cltv_delta = 744`, il cambio a zero scambi aperti con un comando
che conta prima di toccare, il controllo (undici migrazioni nel
registro, «Settings correctly loaded», `barattolo_eventi`, il 38385
che dice `mostro_version 0.20.2`), e la prova di Andrea con due
account. Ogni gesto che scrive aspetta il suo ok.
