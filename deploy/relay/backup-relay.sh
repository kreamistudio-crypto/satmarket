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

# N8N-BARATTOLO (25 nov 2026, cantiere quadro-servizi): vive su questa
# macchina e fino a oggi non era in nessun backup. Dentro ci sono i
# flussi (Tappo, le bozze delle novita') e le credenziali, cifrate con la
# N8N_ENCRYPTION_KEY del suo .env: le due cose viaggiano INSIEME, o il
# database ripristinato non si apre. Il database non si copia a file
# vivo (n8n ci scrive): passa da una copia sqlite fatta da python3, la
# stessa idea di copia-db.py sul VPS. Se la cartella non c'e', il resto
# del backup va avanti lo stesso.
N8N=/opt/n8n-barattolo
N8N_OBBLIGATORI=""
if [ -d "$N8N" ]; then
    mkdir -p "$TMP/n8n-copie"
    find "$N8N/dati" -name '*.sqlite' -type f 2>/dev/null | while IFS= read -r db; do
        rel=${db#"$N8N"/}
        mkdir -p "$TMP/n8n-copie/n8n-barattolo/$(dirname "$rel")"
        python3 -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" \
            "$db" "$TMP/n8n-copie/n8n-barattolo/$rel"
    done
    tar -rf "$TAR" -C /opt --exclude='*.sqlite' --exclude='*.sqlite-wal' \
        --exclude='*.sqlite-shm' --exclude='*.sqlite-journal' n8n-barattolo
    tar -rf "$TAR" -C "$TMP/n8n-copie" n8n-barattolo
    N8N_OBBLIGATORI="n8n-barattolo/.env n8n-barattolo/docker-compose.yml"
fi

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
         relay/aggiorna-chiavi.sh relay/router.conf caddy/Caddyfile \
         $N8N_OBBLIGATORI; do
    printf '%s\n' "$LISTA" | grep -qx "$f" || { echo "manca $f: mi fermo" >&2; exit 1; }
done

# e il database di n8n ci deve essere davvero: senza, i flussi sono persi
if [ -n "$N8N_OBBLIGATORI" ] && ! printf '%s\n' "$LISTA" | grep -q '^n8n-barattolo/.*\.sqlite$'; then
    echo "n8n senza database nell'archivio: mi fermo" >&2; exit 1
fi

install -d -m 750 -g barattolo "$DEST"
OUT="$DEST/relay-$(date +%Y%m%d-%H%M).tar.age"
age -r "$PUB" -o "$OUT" "$TAR"
chmod 640 "$OUT" && chgrp barattolo "$OUT"
echo "backup relay: $OUT ($(stat -c %s "$OUT") byte), dentro:"
printf '%s\n' "$LISTA" | sed 's/^/  /'
ls -1t "$DEST"/relay-*.tar.age | tail -n +$((TIENI+1)) | xargs -r rm -f
