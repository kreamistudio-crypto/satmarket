#!/bin/sh
# backup-rgb.sh — il backup della VM «rgb-prova» (signet, hackathon di Torino).
# Calco di backup-relay.sh. Si salva cio' che non si ricostruisce: le
# chiavi dei wallet (chiavi.json), lo STASH di rgb-lib (la seed da sola
# NON basta a ritrovare gli asset), le fotografie .rgb-backup, .env,
# compose.yaml e rgb.py. MAI la catena signet ne' l'indice di electrs:
# si riscaricano in un'ora.
# Cifra con la sola chiave PUBBLICA age della macchina: il server produce
# copie che lui stesso non sa riaprire; il PC le tira giu' in pull con
# l'utente «pull», che non possiede niente.
set -eu
PUB="age1kjhz94pvfjsjgzakqpg735jjp2mkscdgtjvwt67sjclrljysdfhsdeacdm"
CASA=/home/debian/rgb
DEST=/var/backups/rgb
TIENI=14            # archivi notturni tenuti sulla macchina (il PC tiene la storia)
FOTO_PER_WALLET=3   # .rgb-backup tenuti in ~/rgb/backup per ogni wallet
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
TAR="$TMP/rgb.tar"

# 1) la fotografia coerente di rgb-lib, wallet per wallet, come debian.
#    Apre il wallet da solo: «never instantiate a wallet in multiple
#    places» — alle 03:30 nessun altro processo deve averlo aperto.
WALLET=""
for w in "$CASA"/dati/*/; do
    n=$(basename "$w")
    [ -f "$w/chiavi.json" ] || continue
    runuser -u debian -- "$CASA/venv/bin/python" "$CASA/rgb.py" backup "$n" >/dev/null
    ls -1t "$CASA/backup/$n-"*.rgb-backup | tail -n +$((FOTO_PER_WALLET+1)) | xargs -r rm -f
    WALLET="$WALLET $n"
done
[ -n "$WALLET" ] || { echo "nessun wallet in $CASA/dati: mi fermo" >&2; exit 1; }

# 2) l'archivio: chiavi + stash grezzo + fotografie + config + script + unit
tar -cf "$TAR" \
    -C /home/debian rgb/dati rgb/backup rgb/.env rgb/compose.yaml rgb/rgb.py \
    -C /etc/systemd/system rgb-backup.service rgb-backup.timer \
    -C /usr/local/sbin backup-rgb.sh

# 3) le guardie: ogni wallet con le sue chiavi e una fotografia, i tre
#    file di casa, e un archivio che non pesi come una catena.
LISTA=$(tar -tf "$TAR")
for f in rgb/.env rgb/compose.yaml rgb/rgb.py; do
    printf '%s\n' "$LISTA" | grep -qx "$f" || { echo "manca $f: mi fermo" >&2; exit 1; }
done
for n in $WALLET; do
    printf '%s\n' "$LISTA" | grep -qx "rgb/dati/$n/chiavi.json" || { echo "manca chiavi.json di $n: mi fermo" >&2; exit 1; }
    printf '%s\n' "$LISTA" | grep -q "^rgb/backup/$n-.*\.rgb-backup$" || { echo "manca la fotografia di $n: mi fermo" >&2; exit 1; }
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
