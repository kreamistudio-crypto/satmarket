#!/bin/bash
# ronda-nodo.sh — il giudice del NODO, chiamato da ronda.sh con sudo.
# Ogni ora: i pagamenti usciti da LND, gli HTLC vicini alla scadenza e
# il pavimento dei canali (tutto in ronda-pagamenti.py, che allarma da
# solo). Con --giorno (il giro lungo di ronda.sh, una volta al giorno)
# anche il riassunto di ieri e il BACKUP. A mano:
#   sudo /usr/local/bin/ronda-nodo.sh --impara            tutti noti
#   sudo /usr/local/bin/ronda-nodo.sh --impara 5a16471e   solo quello
#   sudo /usr/local/bin/ronda-nodo.sh --prova             riassunto subito
# Fino al 28 set 2026 il giudice dei pagamenti stava qui dentro, e
# chiamava SCONOSCIUTO ogni pagamento non imparato: vedi CANTIERI, «La
# ronda del nodo riconosce da sola i pagamenti».
# Vive in /usr/local/bin sul nodo; questa e' la COPIA nel repo
# (deploy/nodo/), con la regola del relay: chi tocca il file di la' lo
# riporta qui nello stesso giro.
set -u
MODO=${1:-}

# NIENTE `exit` A META': il giudice dei pagamenti che fallisce (lncli
# muto) non deve portarsi via il controllo del backup — e' il difetto
# del marcatore, che non fallisce ma semplicemente non gira.
/usr/bin/python3 /usr/local/bin/ronda-pagamenti.py "$@"

[ "$MODO" = "--impara" ] && exit 0
[ "$MODO" = "--giorno" ] || [ "$MODO" = "--prova" ] || exit 0

U=$(ls -1t /var/backups/nodo/*.tgz.age 2>/dev/null | head -1)
if [ -z "$U" ]; then
  T='ALLARME BACKUP: nessun archivio in /var/backups/nodo'
  echo "$T"; printf '%s' "$T" | /usr/local/bin/ronda-avvisa.sh
else
  ORE=$(( ( $(date +%s) - $(stat -c %Y "$U") ) / 3600 ))
  KB=$(( $(stat -c %s "$U") / 1024 ))
  if [ "$ORE" -gt 48 ] || [ "$KB" -lt 1024 ]; then
    T=$(printf 'ALLARME BACKUP\nultimo archivio: %s h fa, %s KB\n%s\n' "$ORE" "$KB" "$U")
    echo "$T"; printf '%s' "$T" | /usr/local/bin/ronda-avvisa.sh
  else
    echo "backup ok  ultimo ${ORE}h fa  $(du -h "$U" | cut -f1)"
  fi
fi

exit 0
