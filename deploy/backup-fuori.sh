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
#     apt install age
#     (il comando sqlite3 non serve piu' dal 20 ott 2026: le copie le fa
#     deploy/copia-db.py, col python di sistema)
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
#
# `--copia <file>` (20 ott 2026, cantiere backup-database-occupato): la
# copia del database l'ha gia' fatta deploy.sh, e l'archivio nasce da
# QUELLA invece di rileggere il file vivo. Il 20 ott la seconda lettura,
# fatta col `sqlite3` che non aspetta, e' caduta su «database is locked»
# un attimo dopo che la prima era riuscita.
PRIMA_DEL_DEPLOY=""
COPIA_DATA=""
while [ $# -gt 0 ]; do
    case "$1" in
        --prima-del-deploy)
            PRIMA_DEL_DEPLOY=$(printf '%s' "${2:-}" | tr -cd '0-9a-f' | cut -c1-8)
            [ -n "$PRIMA_DEL_DEPLOY" ] || PRIMA_DEL_DEPLOY="senza-nome"
            shift 2 || shift ;;
        --copia)
            COPIA_DATA="${2:-}"
            shift 2 || shift ;;
        *) shift ;;
    esac
done

DIR_APP="${BARATTOLO_DIR:-/root/satmarket}"
TMP=$(mktemp -d)

# QUANDO IL GIORNALIERO CADE, LO DICE IL BOT (20 ott 2026). Prima un
# backup delle 04:30 andato male parlava solo nel canale dei backup — e
# non sempre: un `tar` o un `age` caduti a meta', o l'invio rifiutato,
# restavano nel journal fino al terzo giorno. Adesso, all'uscita, se il
# giornaliero non e' finito bene (o ha trovato il database rotto) parte
# UN avviso nella stanza degli errori, come quelli del deploy, e dice lo
# stato vero: la copia (integra / NON integra / non fatta) e l'archivio
# (partito / resta sul VPS / non fatto). Prima del deploy tace: li'
# parla deploy.sh, che sa anche come e' andato il resto.
# L'avviso lo manda deploy.sh (`--avvisa`): la regola del gruppo e delle
# stanze sta una volta sola. Si chiama da una copia, come fanno le unit,
# e solo se quel deploy.sh conosce `--avvisa`: un deploy.sh di prima
# prenderebbe l'argomento per niente e farebbe un deploy.
STATO_COPIA=""          # integra | non-integra | "" (non fatta)
MOTIVO_COPIA=""
STATO_ARCHIVIO="non fatto"
FERMO=""                # perche' ci si e' fermati prima della copia
ATTENZIONE_LNBITS=""
scappa() { printf '%s' "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g'; }
avvisa_admin() {
    local d="$TMP/deploy-per-avvisare.sh"
    if cp "$DIR_APP/deploy.sh" "$d" 2>/dev/null && grep -q -- '--avvisa' "$d"; then
        BARATTOLO_DIR="$DIR_APP" timeout 60 bash "$d" --avvisa "$1" \
            || echo "avviso agli admin non partito" >&2
    else
        echo "avviso agli admin non partito: $DIR_APP/deploy.sh non sa avvisare" >&2
    fi
}
alla_fine() {
    local codice=$?
    if [ -z "$PRIMA_DEL_DEPLOY" ] && { [ "$codice" -ne 0 ] \
            || [ "$STATO_COPIA" = "non-integra" ] || [ -n "$ATTENZIONE_LNBITS" ]; }; then
        local guarda="Guardare <code>journalctl -u barattolo-backup -n 40</code>."
        local testo
        if [ "$codice" -eq 143 ] || [ "$codice" -eq 130 ]; then
            local copia_detta="non ancora fatta"
            [ -z "$STATO_COPIA" ] || copia_detta="$STATO_COPIA"
            [ "$STATO_COPIA" != "integra" ] || copia_detta="integra (<code>integrity_check</code> ok)"
            testo="⚠️ <b>Il backup giornaliero è stato fermato prima di finire</b> (un segnale: il tempo massimo della unit, o un arresto). Copia del database: $copia_detta; archivio: $STATO_ARCHIVIO. Se è stato fatto, l'archivio resta in <code>backup/fuori/</code>. $guarda"
        elif [ -n "$FERMO" ]; then
            testo="⚠️ <b>Il backup giornaliero non è partito</b>: $(scappa "$FERMO"). Nessuna copia e nessun archivio questa volta. $guarda"
        elif [ -z "$STATO_COPIA" ]; then
            testo="⚠️ <b>Il backup giornaliero non è riuscito</b>: la copia del database non si è fatta ($(scappa "${MOTIVO_COPIA:-motivo sconosciuto}")). Nessun archivio questa volta: gli archivi di prima restano nel canale. $guarda"
        elif [ "$STATO_COPIA" = "non-integra" ]; then
            testo="⚠️ <b>Il backup giornaliero: la copia del database NON è integra</b> ($(scappa "$MOTIVO_COPIA")). Vuol dire che è rotto il database vivo. Archivio: $STATO_ARCHIVIO. Prima di toccare qualcosa si chiede a Claude. $guarda"
        elif [ "$STATO_ARCHIVIO" = "mandato" ]; then
            testo="⚠️ <b>Il backup giornaliero è partito, ma il database di LNbits no</b>: $(scappa "$ATTENZIONE_LNBITS"). La copia del database del mercatino è integra. $guarda"
        else
            testo="⚠️ <b>Il backup giornaliero non è arrivato al canale</b> (codice $codice). La copia del database era integra (<code>integrity_check</code> ok); archivio: $STATO_ARCHIVIO. $guarda"
        fi
        avvisa_admin "$testo"
        # il segno per l'ExecStopPost della unit (deploy/backup-caduto.sh):
        # questo giro l'ha gia' detto, lui non lo ripete
        mkdir -p "$DIR_APP/backup" 2>/dev/null \
            && printf '%s\n' "${INVOCATION_ID:-a-mano}" > "$DIR_APP/backup/.giornaliero-avvisato" \
            || true
    fi
    rm -rf "$TMP"
}
trap alla_fine EXIT
# FERMATO DA FUORI (20 ott 2026, cantiere backup-ritocchi). Quando il
# giornaliero supera i 600 s della unit, systemd manda SIGTERM a tutto il
# gruppo; senza questa riga bash muore lì, la trappola qui sopra non
# parte e nessuno lo sa (provato: con `trap 'exit 143' TERM` parte, col
# codice 143). Se nemmeno questo basta — un SIGKILL, la memoria finita —
# parla l'ExecStopPost della unit.
trap 'exit 143' TERM
trap 'exit 130' INT

# Il file dell'ambiente si puo' spostare solo per le prove (il banco
# di prove.py gira lo script vero con un ambiente finto): sul VPS e'
# sempre questo.
ENV_FILE="${BARATTOLO_BACKUP_ENV:-/etc/barattolo-backup.env}"
if [ ! -f "$ENV_FILE" ]; then
    echo "manca $ENV_FILE: il backup non sa dove andare" >&2
    FERMO="manca $ENV_FILE, il backup non sa dove andare"
    exit 1
fi
# shellcheck disable=SC1090
. "$ENV_FILE"
for v in BOT_TOKEN_BACKUP CHAT_ID_BACKUP AGE_PUBBLICA; do
    if [ -z "${!v:-}" ]; then
        echo "manca $v in $ENV_FILE" >&2
        FERMO="manca $v in $ENV_FILE"
        exit 1
    fi
done

DIR_OUT="$DIR_APP/backup/fuori"
mkdir -p "$DIR_OUT"

STAMP=$(date +%Y%m%d-%H%M)
[ -z "$PRIMA_DEL_DEPLOY" ] || STAMP="$STAMP-deploy-$PRIMA_DEL_DEPLOY"

# Una riga in chat, col bot dei backup. Fail-open: se Telegram e' giu'
# parla il journal.
di_in_chat() {
    curl -sf --max-time 30 \
         -F "chat_id=$CHAT_ID_BACKUP" \
         -F "text=$1" \
         "https://api.telegram.org/bot$BOT_TOKEN_BACKUP/sendMessage" \
         > /dev/null || true
}

# 0+1) IL DATABASE: UNA COPIA, CONTROLLATA (20 ott 2026, cantiere
#    backup-database-occupato). La fa `deploy/copia-db.py`: l'API di
#    backup di sqlite (atomica anche a server acceso, mai `cp` su un db
#    vivo: copierebbe una pagina a meta' scrittura), 30 s di attesa sul
#    lucchetto invece di zero, un tetto di 90 s, e `integrity_check`
#    sulla COPIA. Quel controllo e' anche la domanda «il database e'
#    sano?» del 19 ott (il 18 il file era rotto dalle 09:04 e lo ha
#    detto solo il libro mastro): l'API copia le pagine tali e quali,
#    quindi un vivo rotto da' una copia rotta, e il «no» arriva SUBITO
#    sul canale dei backup — senza tenere il lucchetto del server per un
#    `quick_check` in piu'. Prima del deploy la sorgente e' la copia che
#    deploy.sh ha appena messo da parte (`--copia`): il vivo si legge
#    una volta sola, e qui si ricontrolla un file fermo.
SORGENTE="$DIR_APP/satmarket.db"
[ -z "$COPIA_DATA" ] || SORGENTE="$COPIA_DATA"
CODICE_COPIA=0
MOTIVO_COPIA=$(python3 "$DIR_APP/deploy/copia-db.py" "$SORGENTE" "$TMP/satmarket.db") \
    || CODICE_COPIA=$?
ATTENZIONE_DB=""
case $CODICE_COPIA in
    0) STATO_COPIA="integra" ;;
    3) STATO_COPIA="non-integra"
       ATTENZIONE_DB=" — ⚠️ DATABASE NON SANO"
       echo "⚠️ il database NON e' sano: $MOTIVO_COPIA" >&2
       di_in_chat "⚠️ Barattolo: il database NON e' sano (${MOTIVO_COPIA:0:200}). Prima di toccare qualcosa: si guarda la testata (od -A d -t u1 -N 100) e si chiede a Claude." ;;
    4) echo "⚠️ copia del database NON riuscita ($MOTIVO_COPIA): nessun archivio" >&2
       di_in_chat "⚠️ Barattolo: il database e' rimasto occupato oltre il tetto (${MOTIVO_COPIA:0:200}): la copia NON e' riuscita, nessun archivio questa volta. Gli archivi di prima restano nel canale."
       exit 1 ;;
    *) [ -n "$MOTIVO_COPIA" ] \
           || MOTIVO_COPIA="nessuna risposta dalla copia (codice $CODICE_COPIA)"
       echo "⚠️ copia del database NON riuscita ($MOTIVO_COPIA): nessun archivio" >&2
       di_in_chat "⚠️ Barattolo: il database NON e' sano o non si copia (${MOTIVO_COPIA:0:200}): nessun archivio questa volta. Prima di toccare qualcosa: si guarda la testata (od -A d -t u1 -N 100) e si chiede a Claude."
       exit 1 ;;
esac

# 2) Il resto. config.py contiene la nsec della piattaforma, la chiave
#    dei contenuti e le chiavi LNbits: da qui in poi esiste solo dentro
#    l'archivio cifrato, mai come file nudo fuori da $TMP.
cp "$DIR_APP/config.py" "$TMP/"
[ -d "$DIR_APP/buste" ]     && cp -r "$DIR_APP/buste"     "$TMP/"
[ -d "$DIR_APP/contenuti" ] && cp -r "$DIR_APP/contenuti" "$TMP/"
#    La chiave di Barattolo dell'on-chain (27 ott 2026, cantiere
#    onchain-disputa): la terza chiave dei 2-di-3, nata dal pannello
#    (`chiavi/onchain-barattolo.json`). Le sue dodici parole esistono
#    SOLO li' e qui dentro: un archivio senza di lei e' un archivio che
#    non ridecide nessuna disputa, quindi si dice forte. `cp -a`: i
#    permessi 0700/0600 viaggiano con lei.
if [ -d "$DIR_APP/chiavi" ]; then
    cp -a "$DIR_APP/chiavi" "$TMP/chiavi" ||       echo "ATTENZIONE: chiave di Barattolo NON copiata da $DIR_APP/chiavi - le dispute on-chain non si ridecidono da questo archivio" >&2
fi
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
# (BARATTOLO_DIR_LNBITS sposta la cartella solo per il banco di prove.py)
DIR_LNBITS="${BARATTOLO_DIR_LNBITS:-/opt/lnbits}"
if [ -d "$DIR_LNBITS" ]; then
    mkdir -p "$TMP/lnbits"
    cp "$DIR_LNBITS/.env" "$DIR_LNBITS/docker-compose.yml" "$TMP/lnbits/" 2>/dev/null || true
    cp -a "$DIR_LNBITS/data" "$TMP/lnbits/data" 2>/dev/null || true
    rm -rf "$TMP/lnbits/data/logs"
    if [ -f "$DIR_LNBITS/data/database.sqlite3" ]; then
        # Sovrascrive la copia "a caldo" fatta dal cp -a con quella
        # atomica: e' questa che si apre, alle due di notte.
        # La stessa copia del mercatino (attesa, tetto, integrity_check);
        # se non riesce resta la copia a caldo del `cp -a`, com'era.
        # PRIMA DEL DEPLOY IL TETTO E' CORTO (20 ott 2026, cantiere
        # backup-ritocchi): tutto lo script sta sotto i `timeout 120` di
        # deploy.sh, e un LNbits occupato col tetto del giornaliero (90 +
        # 30 s) se li sarebbe presi tutti, facendo cadere l'archivio del
        # mercatino per colpa del suo. Qui al piu' 15 + 10 s, e la
        # cintura di `timeout` a 30; di notte c'e' tempo, e resta il tetto
        # pieno. Un giro troncato non lascia il suo `.parziale`
        # nell'archivio.
        if [ -n "$PRIMA_DEL_DEPLOY" ]; then
            MISURE_LNBITS=(--tetto=15 --attesa=10); CINTURA_LNBITS=30
        else
            MISURE_LNBITS=(); CINTURA_LNBITS=150
        fi
        if ESITO_LNBITS=$(timeout "$CINTURA_LNBITS" python3 "$DIR_APP/deploy/copia-db.py" \
                "$DIR_LNBITS/data/database.sqlite3" \
                "$TMP/lnbits/data/database.sqlite3" --anche-scrittura \
                ${MISURE_LNBITS[@]+"${MISURE_LNBITS[@]}"}); then
            :
        else
            rm -f "$TMP/lnbits/data/database.sqlite3.parziale"
            ATTENZIONE_LNBITS="${ESITO_LNBITS:-copia non riuscita, tetto di tempo}"
            echo "ATTENZIONE: database LNbits NON copiato in modo atomico o non integro ($ATTENZIONE_LNBITS) - i sats sul nodo restano senza nomi in questo archivio" >&2
        fi
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
    STATO_ARCHIVIO="troppo grande per il canale ($((DIM / 1024 / 1024)) MB), resta sul VPS in backup/fuori/ per il PC"
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
    STATO_ARCHIVIO="mandato"
    echo "📦 backup inviato: $(basename "$ARCHIVIO") ($DIM byte, ${#PEZZI[@]} file)"
else
    echo "⚠️ invio a Telegram non riuscito: l'archivio resta in $DIR_OUT" >&2
    STATO_ARCHIVIO="non partito per il canale, resta sul VPS in backup/fuori/ (lo tira il PC)"
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
