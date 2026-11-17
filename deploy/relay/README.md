# La configurazione di relay.barattolo.store

Il sorgente della macchina che serve il nostro relay Nostr. Fino al
7 set 2026 l'unica copia fuori da quella macchina era **l'archivio
cifrato dei backup**, e non è quello il suo mestiere: un archivio si
apre col panico addosso, un repo si legge quando si vuole.

Per **rimettere in piedi** la macchina non si parte da qui: si parte da
**`../RIPRISTINO-RELAY.md`**, che dice l'ordine dei passi e le trappole
(l'utente prima dell'estrazione, l'UID che conta più del nome, il DNS
prima di Caddy). Questa cartella è il *cosa*; quel foglio è il *come*.

## ⚠️ Questa è la COPIA, non quel che gira

Non c'è nessun deploy automatico verso il relay: la macchina non tira
da GitHub e nessuno le dice quando qualcosa cambia qui. **La verità
resta la macchina**, e questa cartella è vera solo finché qualcuno la
tiene in pari.

Quindi la regola, e non è una raccomandazione: **chi tocca un file su
quella macchina lo riporta qui nello stesso giro**. Una configurazione
che diverge in silenzio è peggio di una che manca — quella almeno non
mente il giorno del ripristino.

Il modo onesto di verificarlo è confrontare con l'archivio dell'ultima
notte, che viene dalla macchina e non da qui:

```bash
age -d -i chiave.txt relay-AAAAMMGG-HHMM.tar.age > /tmp/relay.tar
mkdir -p /tmp/dalvivo && tar xf /tmp/relay.tar -C /tmp/dalvivo
diff -ru deploy/relay/policy /tmp/dalvivo/relay/policy   # senza chiavi.txt
diff -u  deploy/relay/strfry.conf /tmp/dalvivo/relay/strfry.conf
```

## ⚠️ Quello che qui NON c'è, e non ci deve entrare

Tre file vivono **solo** sulla macchina e nel suo archivio cifrato.
Sono segreti: in un repo non ci possono stare, e lo scanner della CI li
prenderebbe comunque.

| File | Cos'è | Se manca al ripristino |
|---|---|---|
| `token.header` | l'intestazione con cui il relay chiede la whitelist a `barattolo.store` | il timer delle chiavi non rinfresca più niente: resta la lista del giorno dell'archivio |
| `policy/chiavi.txt` | chi può scrivere, oggi | il plugin ammette la sola piattaforma, che è cablata dentro: i venditori restano fuori finché la lista non torna |
| `telegram.conf` | `BOT_TOKEN` e `CHAT_ID` della ronda | la ronda si ferma dicendolo, e nessuno si accorge più se il backup smette |

⚠️ Manca anche il **`Caddyfile`** (`/etc/caddy/Caddyfile`): non è un
segreto, è una dimenticanza del giro in cui questa cartella è nata — il
comando che ha raccolto i file guardava `/opt/relay` e
`/etc/systemd/system` e saltava `/etc/caddy`. Per adesso viene
dall'archivio, dove il backup lo prende e lo sorveglia.

**Quindi il ripristino ha due gambe e non più una**: il repo per il
codice, l'archivio per i segreti. Se sparisse l'archivio la macchina si
rimette in piedi lo stesso — con una whitelist da riempire a mano e la
ronda muta finché non si rifanno i due file.

## ⚠️ E il rovescio: tre file qui sono l'UNICA copia

`backup-relay.sh` non prende la **ronda**, che è nata dopo di lui:
`ronda-relay.sh`, `relay-ronda.service` e `relay-ronda.timer` non sono
in nessun archivio. Da oggi stanno qui, e qui soltanto.

⚠️ Il buco non si vede da solo: quello script ha una guardia che si
ferma se nell'archivio non trova otto file per nome, e **la ronda in
quell'elenco non c'è** — quindi la sua assenza passerebbe in silenzio.
Va aggiunta al `tar` e alla guardia insieme, o la guardia dirà di sì a
un archivio incompleto.

## LA BUCA DEL COORDINATORE (12 ott 2026)

`policy/chi-scrive.py` ha **due porte**, non più una. La lista di
sempre — chi firma sta in `chiavi.txt` e scrive quel che vuole — e la
**buca delle lettere**: da chiunque, ma solo un messaggio indirizzato al
nostro coordinatore P2P (kind 14, un tag `p` che è la sua chiave, una
scadenza vicina, pochi byte), con tre freni al minuto per indirizzo,
per chiave e in tutto. Sono le richieste dei telefoni — presa,
rilascio, voto — che prima passavano dal solo `relay.mostro.network`.

Tutto il resto resta rifiutato come prima. Il perché, i numeri e la
procedura per portare il file sulla macchina (coi fine riga giusti:
copiato da Windows com'è, il plugin non parte e il relay rifiuta
tutto) stanno in `docs/PRODUZIONE.md`, «LA BUCA DEL COORDINATORE»; a
sorvegliare che la buca resti aperta è la ronda del VPS, stessa pagina,
«LA RONDA DEI RELAY DI MOSTRO».

⚠️ La chiave del coordinatore sta scolpita in DUE file di questa
cartella, `router.conf` (l'autore dello specchio) e il plugin (il
destinatario della buca): se un giorno cambia, si cambiano insieme —
una prova di `prove.py` lo pretende.

## La mappa

| File | Dove va | Cosa fa |
|---|---|---|
| `Dockerfile` | `/opt/relay/` | strfry inchiodato a un **digest** e non a un tag che si muove, più `python3` per il plugin |
| `compose.yml` | `/opt/relay/` | il servizio. Porta due righe che non sono decorative: `user: "1001:1001"` e il `127.0.0.1:` davanti alla porta |
| `strfry.conf` | `/opt/relay/` | il relay. `restrictedReadKinds` tiene i DM leggibili solo a chi li riguarda |
| `router.conf` | `/opt/relay/` | lo **specchio**, due flussi in discesa: il libro del P2P (38383 e 38385 dal coordinator; le buste cifrate c'erano dal 17 al 18 set 2026) e — dal 17 nov 2026 — la **scheda dell'app** come la pubblica Zapstore (32267, 30063, 3063, 1063, 30509 dalla chiave fredda delle release, da `relay.zapstore.dev`). Un autore per flusso; la chiave delle release NON sta in `chiavi.txt` |
| `pesca-eventi.py` | nessun posto fisso: si copia nel container quando serve (`docker cp … relay:/tmp/`) | UNA richiesta a un relay e gli eventi in JSONL per `strfry import`: lo storico che lo specchio non tira (`limit: 0`) e che `strfry sync` non sa chiedere a chi non parla negentropy. Usato il 17 nov 2026 per gli 8 eventi dell'app |
| `policy/chi-scrive.py` | `/opt/relay/policy/` | chi può scrivere: la lista, e la buca del coordinatore coi suoi freni. **Fail-closed**: se qualcosa esplode rifiuta |
| `aggiorna-chiavi.sh` | `/opt/relay/` | rinfresca la whitelist da `/api/relay/chiavi`. Legge il token da `token.header` |
| `backup-relay.sh` | `/usr/local/sbin/` | l'archivio cifrato delle 03:45. **Mai il database** — e ha la guardia che lo verifica (**nove** nomi da quando c'è `router.conf`) |
| `ronda-relay.sh` | `/usr/local/sbin/` | le 08:00: età e peso dell'ultimo archivio, sul canale Telegram |
| `unit/*.service`, `unit/*.timer` | `/etc/systemd/system/` | le **sei** unit: chiavi ogni 10 min, backup 03:45, ronda 08:00 |

## Due cose che il codice dice e vanno lette prima di toccarlo

**Il database degli eventi non si salva, ed è voluto.** Si salva ciò che
non si ricostruisce: gli eventi sono firmati e vivono su molti relay, si
riprendono col `sync`. La whitelist e questa configurazione no — quelle
esistono solo qui. `backup-relay.sh` ha una guardia che si **rifiuta** di
girare se `relay/db` finisce nella lista.

**La whitelist sbaglia dalla parte giusta.** Se `/api/relay/chiavi` non
risponde o risponde male, `aggiorna-chiavi.sh` tiene la lista di ieri e
lo dice. Una lista vecchia lascia scrivere chi scriveva ieri; una vuota
chiuderebbe fuori tutti.

## Il debito dichiarato — pagato (set 2026)

`privacy` porta a `https://barattolo.store/privacy`, e la pagina «I tuoi
dati» ha guadagnato la riga sul relay **nello stesso commit**, che era
la condizione: il pallino Nostr diceva che gli annunci vanno «sui relay,
che sono di altri», e da `c7802e7` uno di quei relay è nostro. Puntare
il NIP-11 a una pagina che dice il contrario sarebbe stato il difetto
che questa nota esisteva per impedire.

`terms` **resta vuoto, e ora è una scelta e non un debito**: Barattolo
non ha una pagina di condizioni d'uso, e un URL che risponde 404 è
peggio del campo vuoto — quello dice «non c'è», il link rotto dice
«c'è, e siamo sciatti». La regola di scrittura vive nel `description`
e la fa rispettare il plugin, non un testo. Si riempie il giorno che
quella pagina esiste.
