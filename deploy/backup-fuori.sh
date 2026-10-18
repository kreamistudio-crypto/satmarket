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

# PRIMA DI OGNI DEPLOY (19 ott 2026, il database rotto due volte, richiesta
# di Andrea): `deploy.sh` chiama questo stesso script con
# `--prima-del-deploy <commit>`, prima del `git reset`. L'archivio e' lo
# stesso del giornaliero, cambiano il nome (`-deploy-<commit>`) e la
# didascalia: sul canale si vede quale versione stava per arrivare.
PRIMA_DEL_DEPLOY=""
if [ "${1:-}" = "--prima-del-deploy" ]; then
    PRIMA_DEL_DEPLOY=$(printf '%s' "${2:-}" | tr -cd '0-9a-f' | cut -c1-8)
    [ -n "$PRIMA_DEL_DEPLOY" ] || PRIMA_DEL_DEPLOY="senza-nome"
fi

# Il file dell'ambiente si puo' spostare solo per le prove (il banco
# di prove.py gira lo script vero con un ambiente finto): sul VPS e'
# sempre questo.
ENV_FILE="${BARATTOLO_BACKUP_ENV:-/etc/barattolo-backup.env}"
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
[ -z "$PRIMA_DEL_DEPLOY" ] || STAMP="$STAMP-deploy-$PRIMA_DEL_DEPLOY"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Una riga in chat, col bot dei backup. Fail-open: se Telegram e' giu'
# parla il journal.
di_in_chat() {
    curl -sf --max-time 30 \
         -F "chat_id=$CHAT_ID_BACKUP" \
         -F "text=$1" \
         "https://api.telegram.org/bot$BOT_TOKEN_BACKUP/sendMessage" \
         > /dev/null || true
}

# 0) IL DATABASE E' SANO? (19 ott 2026) Il 18 ottobre il file era rotto
#    dalle 09:04 e lo ha detto solo il libro mastro, una volta al giorno.
#    Da qui lo chiede ogni backup — quello delle 04:30 e quello prima di
#    ogni deploy — e un «no» arriva SUBITO sul canale dei backup, anche
#    quando la copia poi non si puo' fare. `quick_check` legge tutto il
#    file ma non gli indici uno per uno: sui 40 MB di oggi, un secondo.
SANO=$(sqlite3 "$DIR_APP/satmarket.db" "PRAGMA quick_check;" 2>&1 | head -3 | tr '\n' ' ' | sed 's/ *$//') || true
ATTENZIONE_DB=""
if [ "$SANO" != "ok" ]; then
    ATTENZIONE_DB=" — ⚠️ DATABASE NON SANO"
    echo "⚠️ il database NON e' sano: $SANO" >&2
    di_in_chat "⚠️ Barattolo: il database NON e' sano (${SANO:0:200}). Prima di toccare qualcosa: si guarda la testata (od -A d -t u1 -N 100) e si chiede a Claude."
fi

# 1) Il database, con il backup vero di sqlite: atomico anche a server
#    acceso. E' la stessa regola del pre-deploy di deploy.sh.
if ! sqlite3 "$DIR_APP/satmarket.db" ".backup '$TMP/satmarket.db'"; then
    echo "⚠️ copia del database NON riuscita: nessun archivio" >&2
    di_in_chat "⚠️ Barattolo: la copia del database NON e' riuscita, nessun archivio questa volta. Gli archivi di prima restano nel canale."
    exit 1
fi

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
    # IL PONTE VIA WIREGUARD (21 set 2026): il piano B (il ponte di
    # prima, via tor) e la configurazione del tunnel. wg0.conf NON
    # porta segreti per costruzione: la chiave privata sta in
    # /etc/wireguard/privata.key e NON si copia, apposta — a macchina
    # rifatta si rigenera in cinque minuti (due chiavi pubbliche da
    # scambiare), e nell'archivio c'e' un segreto in meno.
    cp /etc/systemd/system/lnd-ponte-tor.service "$TMP/sistema/" 2>/dev/null || true
    cp /etc/wireguard/wg0.conf "$TMP/sistema/wg0.conf" 2>/dev/null || true
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

# 4) Il limite di un bot Telegram e' 50 MB a file. Il 18 ott 2026
#    l'archivio pesava gia' 37 MB (era ~5 ad agosto): oltre i 45 si
#    SPEZZA in parti da 45 MB (`.parte-00`, `.parte-01`…) e si mandano
#    tutte. Al ripristino si rimettono insieme con
#    `cat barattolo-X.tar.gz.age.parte-* > barattolo-X.tar.gz.age`
#    (deploy/RIPRISTINO.md). L'archivio intero resta qui per il PC.
DIM=$(stat -c%s "$ARCHIVIO")
# (BARATTOLO_BACKUP_PARTE sposta la misura solo per il banco di prove.py)
PARTE="${BARATTOLO_BACKUP_PARTE:-$((45 * 1024 * 1024))}"
if [ "$DIM" -gt "$PARTE" ]; then
    split -b "$PARTE" -d -a 2 "$ARCHIVIO" "$ARCHIVIO.parte-"
    PEZZI=( "$ARCHIVIO".parte-* )
else
    PEZZI=( "$ARCHIVIO" )
fi
if [ "${#PEZZI[@]}" -gt 20 ]; then
    echo "⚠️ archivio da $((DIM / 1024 / 1024)) MB: piu' di 20 parti, NON inviato — serve un'altra strada" >&2
    rm -f "$ARCHIVIO".parte-*
    di_in_chat "⚠️ Barattolo: l'archivio pesa $((DIM / 1024 / 1024)) MB, troppo per il canale. Resta sul VPS per il PC."
    exit 1
fi

# 5) L'invio. Si guarda la risposta — un backup che muore in silenzio
#    e' il modo classico di scoprire di non averne (la lezione di
#    /root/backup). Sul fallimento l'archivio resta comunque qui, dove
#    il pull del PC lo raccoglie: la seconda gamba esiste apposta.
MB=$((DIM / 1024 / 1024)); [ "$MB" -lt 1 ] && MB=1
CAPTION="Barattolo — backup $(date '+%Y-%m-%d %H:%M') (~$MB MB)"
[ -z "$PRIMA_DEL_DEPLOY" ] || CAPTION="$CAPTION · prima del deploy $PRIMA_DEL_DEPLOY"
CAPTION="$CAPTION$ATTENZIONE_DB"
INVIATI=0
for i in "${!PEZZI[@]}"; do
    DIDA="$CAPTION"
    [ "${#PEZZI[@]}" -eq 1 ] || DIDA="$CAPTION · parte $((i + 1)) di ${#PEZZI[@]}"
    if curl -sf --max-time 120 \
            -F "chat_id=$CHAT_ID_BACKUP" \
            -F "document=@${PEZZI[$i]}" \
            -F "caption=$DIDA" \
            "https://api.telegram.org/bot$BOT_TOKEN_BACKUP/sendDocument" \
            | grep -q '"ok":true'; then
        INVIATI=$((INVIATI + 1))
    else
        break
    fi
done
rm -f "$ARCHIVIO".parte-*
if [ "$INVIATI" -eq "${#PEZZI[@]}" ]; then
    date +%s > "$DIR_OUT/.ultimo-successo"
    echo "📦 backup inviato: $(basename "$ARCHIVIO") ($DIM byte, ${#PEZZI[@]} file)"
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
#    scadono); queste sono le copie che il PC specchia. Di quelle prima
#    del deploy, che possono essere dieci al giorno, qui restano le
#    ultime 10: le altre sono nel canale.
ls -1t "$DIR_OUT"/barattolo-*-deploy-*.tar.gz.age 2>/dev/null \
    | tail -n +11 | xargs -r rm -f || true
find "$DIR_OUT" -name 'barattolo-*.tar.gz.age' -mtime +7 -print0 \
| while IFS= read -r -d '' f; do
    data=$(basename "$f" | sed 's/^barattolo-\([0-9]\{8\}\).*/\1/')
    giorno=$(date -d "$data" +%u 2>/dev/null || echo 0)
    if [ "$giorno" = "7" ] && ! find "$f" -mtime +28 | grep -q .; then
        continue    # la domenica resta un mese
    fi
    rm -f "$f"
done
