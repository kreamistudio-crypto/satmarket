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

## 3. Il cambio libero sul collaudo, col cartone (27 ott 2026, cantiere cambio-libero: T1 23462f4, T2 9a473b2, T3 2af2b2b su develop)

**Perché.** Il cambio libero (pagina «Cambio», tasto «🔁 Cambia») è su
develop dietro leve spente: sul collaudo si guarda la grafica e il giro
col SATS Routing di cartone (regola di Andrea: mai quello vero). In
produzione NON si accende niente per ora (`SWAP_ATTIVO` è spenta, e
`CAMBIO_BTC_LN_ATTIVO` aspetta la risposta di Massimo su quota partner e
limiti di chiamate). Un gesto alla volta, col sì di Andrea (COLLAUDO.md).

**Sola lettura** (sulla VM): il cartone è vivo? e le righe dello swap
ci sono già (dal 27 ott 08:07)?
```
systemctl status cartone-swap --no-pager | head -5; curl -s http://127.0.0.1:9077/v2/swap/submarine | head -c 200
```
```
grep -n "^SWAP_ATTIVO\|^SWAP_API_BASE\|^SWAP_SOLO_MODERATORI\|^CAMBIO_" /srv/collaudo/barattolo/config.py
```
Se il cartone non risponde (la VM si è riavviata: l'unità è
transitoria), si rilancia come il 27 ott (il comando sta nel thread
«Accendere lo swap sul collaudo»; in breve: `systemd-run --unit=cartone-swap`
sul `python cartone_satsrouting.py --porta 9077` del venv del collaudo).

**Scrive** (copia di riserva prima, poi le due righe in fondo, poi riavvio):
```
sudo cp /srv/collaudo/barattolo/config.py /srv/collaudo/barattolo/config.py.prima-cambio
```
```
printf '\nCAMBIO_LIBERO_ATTIVO = True\nCAMBIO_BTC_LN_ATTIVO = True\n' | sudo tee -a /srv/collaudo/barattolo/config.py > /dev/null
```
```
sudo systemctl restart barattolo-collaudo && sleep 3 && curl -s -o /dev/null -w "%{http_code}\n" https://collaudo.barattolo.store/api/salute
```
Atteso 200. Poi, da moderatore, la pagina «Cambio»: il tasto «🔁
Cambia», le due pillole, 100.000 sats → preventivo (98.842 da ricevere
sulla strada Lightning → bitcoin; 100.818 da mandare su quella
rovesciata), «Incolla», le 12 parole la prima volta, «Conferma». Quel
che si vede va nel verbale (CANTIERI, «Il cambio libero, tappa 3»,
«COSA RESTA») e questa voce si cancella. ATTENZIONE alle copie vecchie
del config: `config.py.prima-prova-aperta` (23 ott) e
`config.py.prima-swap` (27 ott) NON hanno queste righe.

