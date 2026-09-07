#!/bin/sh
# ronda-relay.sh — il termometro del backup del relay.
# Manda SEMPRE: una ronda che tace non si distingue da una morta.
set -eu
CONF=/opt/relay/telegram.conf
DEST=/var/backups/relay
ORE_MAX=${ORE_MAX:-48}
# 10 KB: l'archivio sano ne pesa ~40. NON e' l'1 MB del nodo, che qui
# suonerebbe ogni notte su una macchina a posto.
BYTE_MIN=${BYTE_MIN:-10240}

[ -r "$CONF" ] || { echo "manca $CONF" >&2; exit 1; }
. "$CONF"

ALLARME=0
ULTIMO=$(ls -1t "$DEST"/relay-*.tar.age 2>/dev/null | head -n1 || true)

if [ -z "$ULTIMO" ]; then
    ALLARME=1
    CORPO="NESSUN archivio in $DEST"
else
    ORE=$(( ( $(date +%s) - $(stat -c %Y "$ULTIMO") ) / 3600 ))
    PESO=$(stat -c %s "$ULTIMO")
    UMANO=$(du -h "$ULTIMO" | cut -f1)
    QUANTI=$(ls -1 "$DEST"/relay-*.tar.age | wc -l)
    CORPO="Ultimo backup: ${ORE}h fa, ${UMANO} (${QUANTI} archivi)"
    if [ "$ORE" -gt "$ORE_MAX" ]; then
        ALLARME=1
        CORPO="$CORPO
Ha piu' di ${ORE_MAX}h: il backup non gira."
    fi
    if [ "$PESO" -lt "$BYTE_MIN" ]; then
        ALLARME=1
        CORPO="$CORPO
Pesa meno di ${BYTE_MIN} byte: archivio troncato."
    fi
fi

if [ "$ALLARME" -eq 1 ]; then TESTA="⚠️ ronda relay"; else TESTA="🧭 Ronda relay"; fi
MSG="$TESTA - $(date '+%d %b %H:%M')
$CORPO
--- fine ronda"

echo "$MSG"
curl -fsS --max-time 20 \
     -d chat_id="$CHAT_ID" \
     --data-urlencode text="$MSG" \
     "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" >/dev/null

exit "$ALLARME"
