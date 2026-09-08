#!/bin/sh
# backup-relay.sh — il backup del relay di Barattolo.
# Si salva cio' che non si ricostruisce: conf, plugin, token, whitelist,
# Caddy e le unit. MAI il database degli eventi, che vive anche sugli
# altri relay e si ritira giu' con `strfry sync`.
set -eu
PUB="age1h6kgk0marj24q8s4hsxntsw4mvepr4uzp6s4z4qd4nnvhphll5rskxh5t0"
DEST=/var/backups/relay
TIENI=14
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
TAR="$TMP/relay.tar"

tar -cf "$TAR" \
    -C /opt --exclude=relay/db relay \
    -C /etc caddy/Caddyfile \
    -C /etc/systemd/system barattolo-chiavi.service barattolo-chiavi.timer \
                           relay-backup.service relay-backup.timer \
    -C /usr/local/sbin backup-relay.sh

LISTA=$(tar -tf "$TAR")
if printf '%s\n' "$LISTA" | grep -q '^relay/db'; then
    echo "il database e' finito nell'archivio: mi fermo" >&2; exit 1
fi
# NOVE nomi e non piu' otto: `router.conf` e' entrato con lo specchio
# del libro P2P. La guardia va allungata NELLO STESSO GIRO del file
# nuovo, o la sua assenza da un archivio non fermerebbe niente — ed e'
# esattamente il buco gia' dichiarato per la ronda.
for f in relay/strfry.conf relay/policy/chi-scrive.py relay/policy/chiavi.txt \
         relay/token.header relay/compose.yml relay/Dockerfile \
         relay/aggiorna-chiavi.sh relay/router.conf caddy/Caddyfile; do
    printf '%s\n' "$LISTA" | grep -qx "$f" || { echo "manca $f: mi fermo" >&2; exit 1; }
done

install -d -m 750 -g barattolo "$DEST"
OUT="$DEST/relay-$(date +%Y%m%d-%H%M).tar.age"
age -r "$PUB" -o "$OUT" "$TAR"
chmod 640 "$OUT" && chgrp barattolo "$OUT"
echo "backup relay: $OUT ($(stat -c %s "$OUT") byte), dentro:"
printf '%s\n' "$LISTA" | sed 's/^/  /'
ls -1t "$DEST"/relay-*.tar.age | tail -n +$((TIENI+1)) | xargs -r rm -f
