#!/bin/sh
# backup-rgb.sh — il backup della VM «rgb-prova» (signet E mutinynet,
# hackathon di Torino).
# Calco di backup-relay.sh. Si salva cio' che non si ricostruisce: le
# chiavi dei wallet (chiavi.json), lo STASH di rgb-lib (la seed da sola
# NON basta a ritrovare gli asset), le fotografie .rgb-backup, .env,
# compose.yaml e rgb.py — per TUTT'E DUE le catene (rgb/dati e
# rgb/mutinynet). MAI la catena signet ne' l'indice di electrs:
# si riscaricano in un'ora.
# Cifra con la sola chiave PUBBLICA age della macchina: il server produce
# copie che lui stesso non sa riaprire; il PC le tira giu' in pull con
# l'utente «pull», che non possiede niente.
set -eu
PUB="age1kjhz94pvfjsjgzakqpg735jjp2mkscdgtjvwt67sjclrljysdfhsdeacdm"
# Le cartelle sono quelle della VM; le variabili servono SOLO alla prova
# di prove.py, che fa girare questo script dentro una casa finta con
# runuser e age di cartone. Sulla VM non si impostano mai.
HOME_DEBIAN=${BACKUP_RGB_HOME:-/home/debian}
CASA=$HOME_DEBIAN/rgb
DEST=${BACKUP_RGB_DEST:-/var/backups/rgb}
UNIT_DIR=${BACKUP_RGB_UNIT_DIR:-/etc/systemd/system}
SBIN_DIR=${BACKUP_RGB_SBIN_DIR:-/usr/local/sbin}
TIENI=14            # archivi notturni tenuti sulla macchina (il PC tiene la storia)
FOTO_PER_WALLET=3   # .rgb-backup tenuti in ~/rgb/backup per ogni wallet
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
TAR="$TMP/rgb.tar"

# 1) la fotografia coerente di rgb-lib, wallet per wallet, come debian.
#    Apre il wallet da solo: «never instantiate a wallet in multiple
#    places» — alle 03:30 nessun altro processo deve averlo aperto.
#    DUE CATENE (9 ott 2026, studio Mutinynet): i wallet del signet in
#    rgb/dati con le fotografie in rgb/backup; quelli di Mutinynet in
#    rgb/mutinynet con le fotografie in rgb/backup-mutinynet, aperti con
#    l'ambiente della catena (RGB_CATENA, RGB_BASE, RGB_BACKUP: gli
#    stessi nomi di mutinynet.env), sennò rgb.py si rifiuta. La seconda
#    cartella c'e' solo da domenica 11: finche' manca si salta, e la
#    riga finale lo dice.
WALLET=""        # «catena/nome», per le guardie di sotto
DENTRO=""        # le cartelle che finiscono nell'archivio
fotografa() {    # $1 catena, $2 cartella dei wallet, $3 cartella delle fotografie
    [ -d "$CASA/$2" ] || return 0
    DENTRO="$DENTRO rgb/$2"
    for w in "$CASA/$2"/*/; do
        n=$(basename "$w")
        [ -f "$w/chiavi.json" ] || continue
        runuser -u debian -- env RGB_CATENA="$1" RGB_BASE="$CASA/$2" RGB_BACKUP="$CASA/$3" \
            "$CASA/venv/bin/python" "$CASA/rgb.py" backup "$n" >/dev/null
        ls -1t "$CASA/$3/$n-"*.rgb-backup | tail -n +$((FOTO_PER_WALLET+1)) | xargs -r rm -f
        WALLET="$WALLET $1/$n"
    done
    [ -d "$CASA/$3" ] && DENTRO="$DENTRO rgb/$3"
    return 0
}
fotografa signet dati backup
fotografa mutinynet mutinynet backup-mutinynet
[ -n "$WALLET" ] || { echo "nessun wallet in $CASA/dati ne' in $CASA/mutinynet: mi fermo" >&2; exit 1; }

# 2) l'archivio: chiavi + stash grezzo + fotografie + config + script + unit
#    (DENTRO porta rgb/dati rgb/backup e, se ci sono, rgb/mutinynet
#    rgb/backup-mutinynet: si espande apposta senza virgolette)
# shellcheck disable=SC2086
tar -cf "$TAR" \
    -C "$HOME_DEBIAN" $DENTRO rgb/.env rgb/compose.yaml rgb/rgb.py \
    -C "$UNIT_DIR" rgb-backup.service rgb-backup.timer \
    -C "$SBIN_DIR" backup-rgb.sh

# 3) le guardie: ogni wallet con le sue chiavi e una fotografia, i tre
#    file di casa, e un archivio che non pesi come una catena.
LISTA=$(tar -tf "$TAR")
for f in rgb/.env rgb/compose.yaml rgb/rgb.py; do
    printf '%s\n' "$LISTA" | grep -qx "$f" || { echo "manca $f: mi fermo" >&2; exit 1; }
done
for cn in $WALLET; do
    c=${cn%/*}; n=${cn#*/}
    case "$c" in signet) d=dati; b=backup ;; *) d=$c; b="backup-$c" ;; esac
    printf '%s\n' "$LISTA" | grep -qx "rgb/$d/$n/chiavi.json" || { echo "manca chiavi.json di $cn: mi fermo" >&2; exit 1; }
    printf '%s\n' "$LISTA" | grep -q "^rgb/$b/$n-.*\.rgb-backup$" || { echo "manca la fotografia di $cn: mi fermo" >&2; exit 1; }
done
PESO=$(stat -c %s "$TAR")
[ "$PESO" -lt 209715200 ] || { echo "archivio da $PESO byte: c'e' finito qualcosa di grosso, mi fermo" >&2; exit 1; }

install -d -m 750 -g pull "$DEST"
OUT="$DEST/rgb-$(date +%Y%m%d-%H%M).tar.age"
age -r "$PUB" -o "$OUT" "$TAR"
chmod 640 "$OUT" && chgrp pull "$OUT"
echo "backup rgb-prova: $OUT ($(stat -c %s "$OUT") byte), wallet:$WALLET, dentro:"
printf '%s\n' "$LISTA" | grep -v '/wallet/' | sed 's/^/  /'
ls -1t "$DEST"/rgb-*.tar.age | tail -n +$((TIENI+1)) | xargs -r rm -f
