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

## La mappa

| File | Dove va | Cosa fa |
|---|---|---|
| `Dockerfile` | `/opt/relay/` | strfry inchiodato a un **digest** e non a un tag che si muove, più `python3` per il plugin |
| `compose.yml` | `/opt/relay/` | il servizio. Porta due righe che non sono decorative: `user: "1001:1001"` e il `127.0.0.1:` davanti alla porta |
| `strfry.conf` | `/opt/relay/` | il relay. `restrictedReadKinds` tiene i DM leggibili solo a chi li riguarda |
| `policy/chi-scrive.py` | `/opt/relay/policy/` | chi può scrivere. **Fail-closed**: se qualcosa esplode rifiuta |
| `aggiorna-chiavi.sh` | `/opt/relay/` | rinfresca la whitelist da `/api/relay/chiavi`. Legge il token da `token.header` |
| `backup-relay.sh` | `/usr/local/sbin/` | l'archivio cifrato delle 03:45. **Mai il database** — e ha la guardia che lo verifica |
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

## Il debito dichiarato

`strfry.conf` ha `privacy = ""` e `terms = ""`. Si riempiono **il giorno
in cui il relay entra in `RELAY_NOSTR`**, insieme alla riga che «I tuoi
dati» guadagna sul relay: nello stesso commit, o una delle due pagine
mente sull'altra.
