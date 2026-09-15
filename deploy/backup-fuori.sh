#!/bin/bash
# L'uscita di sicurezza di Barattolo: ogni giorno un archivio cifrato
# ESCE da Hetzner, verso un canale Telegram privato.
#
# Il perche' (ago 2026): il backup giornaliero di prima
# (backup-barattolo.sh) copiava db e config in /root/backup — cioe'
# sullo STESSO disco, col config IN CHIARO. Contro il guasto che conta
# davvero (l'account Hetzner perso: server, snapshot e Volume tutti
# insieme) valeva zero. Questo script e' il rimpiazzo, e la regola e'
# una sola: LA COPIA CHE CONTA E' QUELLA CHE STA FUORI.
#
# Cosa serve sul VPS (una volta sola, da root):
#     apt install age sqlite3
#     cp deploy/barattolo-backup.* /etc/systemd/system/
#     systemctl daemon-reload && systemctl enable --now barattolo-backup.timer
# piu' il file /etc/barattolo-backup.env (chmod 600), MAI nel repo:
#     BOT_TOKEN_BACKUP=...    # bot NUOVO, mai quello di Barattolo:
#                             # mischiare i token lega due mestieri
#     CHAT_ID_BACKUP=...      # il canale privato dei backup
#     AGE_PUBBLICA=age1...    # la meta' PUBBLICA: sa cifrare e basta.
#                             # Il server produce backup che lui stesso
#                             # non sa riaprire; la meta' segreta vive
#                             # su carta + Bitwarden, mai qui.
#
# Dentro l'archivio: il database (backup ATOMICO di sqlite, mai `cp`
# su un db vivo: copierebbe una pagina a meta' scrittura), config.py
# (i segreti viaggiano SOLO dentro il cifrato), buste/ e contenuti/
# (blob gia' cifrati, ma servono le righe), e le config di sistema.
# FUORI: foto/ (171 MB, la tira il PC di Andrea via rclone — vedi
# deploy/RIPRISTINO.md) e tutto cio' che si ricostruisce da git.

set -euo pipefail

ENV_FILE=/etc/barattolo-backup.env
if [ ! -f "$ENV_FILE" ]; then
    echo "manca $ENV_FILE: il backup non sa dove andare" >&2
    exit 1
fi
# shellcheck disable=SC1090
. "$ENV_FILE"
: "${BOT_TOKEN_BACKUP:?manca in $ENV_FILE}"
: "${CHAT_ID_BACKUP:?manca in $ENV_FILE}"
: "${AGE_PUBBLICA:?manca in $ENV_FILE}"

DIR_APP="${BARATTOLO_DIR:-/root/satmarket}"
DIR_OUT="$DIR_APP/backup/fuori"
mkdir -p "$DIR_OUT"

STAMP=$(date +%Y%m%d-%H%M)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# 1) Il database, con il backup vero di sqlite: atomico anche a server
#    acceso. E' la stessa regola del pre-deploy di deploy.sh.
sqlite3 "$DIR_APP/satmarket.db" ".backup '$TMP/satmarket.db'"

# 2) Il resto. config.py contiene la nsec della piattaforma, la chiave
#    dei contenuti e le chiavi LNbits: da qui in poi esiste solo dentro
#    l'archivio cifrato, mai come file nudo fuori da $TMP.
cp "$DIR_APP/config.py" "$TMP/"
[ -d "$DIR_APP/buste" ]     && cp -r "$DIR_APP/buste"     "$TMP/"
[ -d "$DIR_APP/contenuti" ] && cp -r "$DIR_APP/contenuti" "$TMP/"
mkdir -p "$TMP/sistema"
cp /etc/caddy/Caddyfile "$TMP/sistema/" 2>/dev/null || true
cp /etc/systemd/system/barattolo*.service \
   /etc/systemd/system/barattolo*.timer "$TMP/sistema/" 2>/dev/null || true
crontab -l > "$TMP/sistema/crontab-root.txt" 2>/dev/null || true

# 2b) La chiave del servizio nascosto Tor. NON e' un dato di servizio
#     come i vicini: l'indirizzo .onion e' DERIVATO da lei — e' la
#     base32 della sua chiave pubblica — quindi la chiave E'
#     l'indirizzo. Persa, non si rigenera: non c'e' un registro da
#     aggiornare ne' un DNS da rimettere, e ogni link .onion che
#     qualcuno si e' salvato muore. E il caso non e' solo il disastro:
#     una MIGRAZIONE su un'altra macchina la vuole tale e quale, ed e'
#     una cosa che si fa quando tutto va bene.
#
#     Il percorso si LEGGE dal torrc invece di ribatterlo qui: una
#     fonte sola, e se un domani la cartella cambia nome il backup la
#     segue da solo. `cp -a` porta dentro anche i permessi 0700, senza
#     i quali Tor si rifiuta di partire; il proprietario va rimesso al
#     ripristino, e la liturgia sta in deploy/RIPRISTINO.md.
cp /etc/tor/torrc "$TMP/sistema/" 2>/dev/null || true
DIR_ONION=$(awk '$1=="HiddenServiceDir"{print $2; exit}'             /etc/tor/torrc 2>/dev/null || true)
if [ -n "${DIR_ONION:-}" ] && [ -d "$DIR_ONION" ]; then
    # QUESTA copia non tace se fallisce, al contrario dei `|| true`
    # qui sopra: quelli proteggono file che si riscrivono a mano, qui
    # sotto c'e' la sola cosa dell'onion che non si puo' rifare. Si
    # urla e si TIRA DRITTO — un archivio senza la chiave vale molto
    # piu' di nessun archivio, e il db resta la ragione per cui questo
    # script esiste.
    cp -a "$DIR_ONION" "$TMP/sistema/tor-hidden-service" ||       echo "ATTENZIONE: chiave .onion NON copiata da $DIR_ONION - l'archivio e' monco proprio dove conta di piu' (l'indirizzo non si rigenera)" >&2
fi

# 2c) LA CASSAFORTE SUL NODO (set 2026): LNbits self-hosted in
#     /opt/lnbits. Il suo database e' DENARO nello stesso senso di
#     satmarket.db: i sats stanno sul nodo Lightning, ma CHI li ha
#     versati e per quale wallet lo sa solo questo file — senza, il
#     saldo del nodo e' una cifra senza nomi. Quindi lo stesso backup
#     ATOMICO di sqlite, mai `cp` su un db vivo. Attorno: .env (il
#     macaroon e i nomi delle leve), il compose (la versione pinnata),
#     il resto di data/ (il cert TLS di LND e il file del superuser),
#     e l'unit del ponte socat. FUORI i log, che pesano e non servono.
#     Il percorso e' un nome solo, qui: se un giorno LNbits trasloca,
#     e' questa riga a seguirla.
DIR_LNBITS=/opt/lnbits
if [ -d "$DIR_LNBITS" ]; then
    mkdir -p "$TMP/lnbits"
    cp "$DIR_LNBITS/.env" "$DIR_LNBITS/docker-compose.yml" "$TMP/lnbits/" 2>/dev/null || true
    cp -a "$DIR_LNBITS/data" "$TMP/lnbits/data" 2>/dev/null || true
    rm -rf "$TMP/lnbits/data/logs"
    if [ -f "$DIR_LNBITS/data/database.sqlite3" ]; then
        # Sovrascrive la copia "a caldo" fatta dal cp -a con quella
        # atomica: e' questa che si apre, alle due di notte.
        sqlite3 "$DIR_LNBITS/data/database.sqlite3" \
            ".backup '$TMP/lnbits/data/database.sqlite3'" ||           echo "ATTENZIONE: database LNbits NON copiato in modo atomico - i sats sul nodo restano senza nomi in questo archivio" >&2
    fi
    cp /etc/systemd/system/lnd-ponte.service "$TMP/sistema/" 2>/dev/null || true
fi

# 2d) LA CHIAVE DEL CLIENT VERSO IL NODO: il servizio nascosto che
#     espone la REST di LND si vede SOLO con questa chiave x25519
#     (client-auth v3). Si puo' rigenerare — al contrario della chiave
#     dell'onion qui sopra — ma rigenerarla vuol dire un gesto sul
#     nodo e uno sul VPS alle due di notte: la si porta dentro, cosi'
#     il ripristino e' solo rimetterla a posto (proprietario debian-tor,
#     0700/0600, come la cartella dell'onion). Il percorso si LEGGE dal
#     torrc, per la stessa ragione di HiddenServiceDir.
DIR_AUTH=$(awk '$1=="ClientOnionAuthDir"{print $2; exit}' /etc/tor/torrc 2>/dev/null || true)
if [ -n "${DIR_AUTH:-}" ] && [ -d "$DIR_AUTH" ]; then
    cp -a "$DIR_AUTH" "$TMP/sistema/tor-onion-auth" ||       echo "ATTENZIONE: chiave client-auth NON copiata da $DIR_AUTH - senza, al ripristino il ponte verso il nodo va rifatto a mano" >&2
fi

# 3) Tar + age. La pubblica cifra, e nessuno su questa macchina sa
#    decifrare: e' il punto di tutto lo script.
ARCHIVIO="$DIR_OUT/barattolo-$STAMP.tar.gz.age"
tar -C "$TMP" -czf - . | age -r "$AGE_PUBBLICA" > "$ARCHIVIO"

# 4) La guardia delle dimensioni: il limite di un bot Telegram e' 50 MB
#    a file. Oggi l'archivio pesa ~5 MB: se si avvicina alla soglia va
#    saputo PRIMA che l'invio cominci a fallire in silenzio.
DIM=$(stat -c%s "$ARCHIVIO")
if [ "$DIM" -ge $((49 * 1024 * 1024)) ]; then
    echo "⚠️ archivio da $((DIM / 1024 / 1024)) MB: oltre il limite Telegram, NON inviato — serve spezzarlo o cambiare strada" >&2
    exit 1
elif [ "$DIM" -ge $((40 * 1024 * 1024)) ]; then
    echo "⚠️ archivio da $((DIM / 1024 / 1024)) MB: si avvicina al limite dei 50 MB di Telegram" >&2
fi

# 5) L'invio. Si guarda la risposta — un backup che muore in silenzio
#    e' il modo classico di scoprire di non averne (la lezione di
#    /root/backup). Sul fallimento l'archivio resta comunque qui, dove
#    il pull del PC lo raccoglie: la seconda gamba esiste apposta.
MB=$((DIM / 1024 / 1024)); [ "$MB" -lt 1 ] && MB=1
CAPTION="Barattolo — backup $(date '+%Y-%m-%d %H:%M') (~$MB MB)"
if curl -sf --max-time 120 \
        -F "chat_id=$CHAT_ID_BACKUP" \
        -F "document=@$ARCHIVIO" \
        -F "caption=$CAPTION" \
        "https://api.telegram.org/bot$BOT_TOKEN_BACKUP/sendDocument" \
        | grep -q '"ok":true'; then
    date +%s > "$DIR_OUT/.ultimo-successo"
    echo "📦 backup inviato: $(basename "$ARCHIVIO") ($DIM byte)"
else
    echo "⚠️ invio a Telegram non riuscito: l'archivio resta in $DIR_OUT" >&2
    # Tre giorni di silenzio non sono un singhiozzo: si prova almeno a
    # dirlo in chat (se Telegram e' giu' fallira' anche questo, e
    # allora parla il journal — e la gamba del PC).
    ULTIMO=$(cat "$DIR_OUT/.ultimo-successo" 2>/dev/null || echo 0)
    if [ $(($(date +%s) - ULTIMO)) -gt $((3 * 86400)) ]; then
        curl -sf --max-time 30 \
             -F "chat_id=$CHAT_ID_BACKUP" \
             -F "text=⚠️ Barattolo: i backup non arrivano da piu' di 3 giorni — guardare il journal di barattolo-backup sul VPS" \
             "https://api.telegram.org/bot$BOT_TOKEN_BACKUP/sendMessage" \
             > /dev/null || true
    fi
    exit 1
fi

# 6) La retention locale: 7 giornaliere, piu' le domeniche per 28
#    giorni. Il canale Telegram tiene tutto da solo (i messaggi non
#    scadono); queste sono le copie che il PC specchia.
find "$DIR_OUT" -name 'barattolo-*.tar.gz.age' -mtime +7 -print0 \
| while IFS= read -r -d '' f; do
    data=$(basename "$f" | sed 's/^barattolo-\([0-9]\{8\}\).*/\1/')
    giorno=$(date -d "$data" +%u 2>/dev/null || echo 0)
    if [ "$giorno" = "7" ] && ! find "$f" -mtime +28 | grep -q .; then
        continue    # la domenica resta un mese
    fi
    rm -f "$f"
done
