#!/bin/sh
# La ronda del nodo: tre misure, e parla SOLO se una è fuori soglia
# (o non si è potuta fare). Dal timer nodo-ronda; a mano con --prova
# parla comunque, coi tre numeri: è il drill del tubo.
# OGNI ORA DAL 28 SET 2026 (prima il lunedì alle 9): il giudice dei
# pagamenti gira a ogni giro, così un pagamento che nessuno spiega si
# vede entro un'ora e non entro una settimana. Il resto — finestra,
# disco, RAM, superficie, backup e il riassunto dei pagamenti di ieri —
# è il GIRO LUNGO, una volta al giorno dalle 9 UTC: sono misure senza
# memoria, e ogni ora ripeterebbero lo stesso allarme ventiquattro
# volte. Vive in ~/nodo sul nodo; questa è la COPIA nel repo
# (deploy/nodo/): chi tocca il file di là lo riporta qui.
# Vedi CANTIERI, «La ronda del nodo riconosce da sola i pagamenti».
set -u
cd "$(dirname "$0")"
. ./telegram.env          # TG_TOKEN e TG_CHAT: lo stesso file di backup-scb.sh

SOGLIA_FINESTRA=500       # blocchi fra punta e pruneheight: sotto, LND si pianta al primo rescan
SOGLIA_DISCO=85           # % del disco usato sul mount di ~/nodo
SOGLIA_RAM=15             # % di memoria ANCORA disponibile (MemAvailable)
TOR_SOCKS=172.28.1.3:9050 # il curl passa da tor, come quello dei backup
PROVA=0; [ "${1:-}" = "--prova" ] && PROVA=1

# IL GIRO LUNGO: il primo giro del giorno dalle 9 UTC in poi, o --prova.
# Il giorno si timbra in fondo, SOLO a giro riuscito: un Telegram
# caduto lo fa rifare all'ora dopo (il riassunto non parte due volte,
# lo ricorda ronda-pagamenti.py). --prova non timbra.
TIMBRO=./.ronda-giro-lungo
OGGI=$(date -u +%F)
LUNGO=0
if [ "$PROVA" = 1 ]; then
  LUNGO=1
elif [ "$(date -u +%H)" -ge 9 ] && [ "$(cat "$TIMBRO" 2>/dev/null)" != "$OGGI" ]; then
  LUNGO=1
fi

if [ "$LUNGO" = 0 ]; then
  # IL GIRO CORTO: solo pagamenti, HTLC e canali. Allarma da solo
  # (ronda-avvisa.sh); qui resta la riga nel journal e il marcatore.
  echo "ronda: giro corto (pagamenti, HTLC, canali); il giro lungo di oggi $( [ "$(cat "$TIMBRO" 2>/dev/null)" = "$OGGI" ] && echo 'è già fatto' || echo 'viene dalle 9 UTC')"
  sudo /usr/local/bin/ronda-nodo.sh
  echo '--- fine ronda'
  exit 0
fi

allarmi=""

# 1) la finestra di potatura: una misura che non riesce è un allarme, non un silenzio
info=$(docker compose exec -T bitcoind bitcoin-cli -datadir=/home/bitcoin/.bitcoin getblockchaininfo 2>/dev/null)
finestra="?"
if [ -z "$info" ]; then
  allarmi="$allarmi
⛔ bitcoind non risponde alla RPC: la finestra di potatura non si è potuta misurare"
else
  finestra=$(printf '%s' "$info" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["blocks"]-d.get("pruneheight",0))')
  [ "$finestra" -lt "$SOGLIA_FINESTRA" ] && allarmi="$allarmi
🔴 Finestra di potatura a $finestra blocchi (soglia $SOGLIA_FINESTRA): LND si pianterà al primo rescan. Guarda cosa mangia il budget"
fi

# 2) il disco: il vincolo di questa macchina
disco=$(df --output=pcent "$HOME/nodo" 2>/dev/null | tail -1 | tr -dc 0-9)
if [ -z "$disco" ]; then
  allarmi="$allarmi
⛔ df non risponde: il disco non si è potuto misurare"
elif [ "$disco" -ge "$SOGLIA_DISCO" ]; then
  allarmi="$allarmi
🔴 Disco al $disco% (soglia $SOGLIA_DISCO%)"
fi

# 3) la memoria: MemAvailable, che è quella che conta (la cache si libera da sola)
ram=$(awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{if(t>0) printf "%d", a*100/t}' /proc/meminfo)
if [ -z "$ram" ]; then
  allarmi="$allarmi
⛔ /proc/meminfo illeggibile: la memoria non si è potuta misurare"
elif [ "$ram" -lt "$SOGLIA_RAM" ]; then
  allarmi="$allarmi
🔴 Memoria disponibile al $ram% (soglia $SOGLIA_RAM%)"
fi

# La riga nel journal c'è SEMPRE: così il silenzio è leggibile
echo "ronda: finestra=$finestra blocchi, disco=$disco%, ram disponibile=$ram%, allarmi: $( [ -n "$allarmi" ] && echo si || echo no)"

# I due sotto-giudici girano SEMPRE, allarmi o no (16 set 2026): prima
# stavano nel solo ramo silenzioso, e una settimana col disco oltre
# soglia lasciava pagamenti, HTLC, backup e superficie non guardati -
# con un messaggio arrivato che faceva sembrare il giro completo.
if [ "$PROVA" = 1 ]; then
  sudo /usr/local/bin/ronda-nodo.sh --prova
else
  sudo /usr/local/bin/ronda-nodo.sh --giorno
fi
sudo /usr/local/bin/ronda-superficie.sh

if [ -z "$allarmi" ] && [ "$PROVA" = 0 ]; then
  echo "$OGGI" > "$TIMBRO"
  echo '--- fine ronda'
  exit 0
fi

if [ "$PROVA" = 1 ]; then
  testo="🧭 Ronda del nodo, PROVA del $(date +%d/%m): finestra $finestra blocchi, disco $disco%, RAM libera $ram%.$allarmi
--- fine ronda"
else
  testo="🧭 Ronda del nodo, $(date +%d/%m):$allarmi
--- fine ronda"
fi

esito=$(curl -s --max-time 90 --socks5-hostname "$TOR_SOCKS" \
  -X POST "https://api.telegram.org/bot$TG_TOKEN/sendMessage" \
  --data-urlencode "chat_id=$TG_CHAT" --data-urlencode "text=$testo" \
  -o /dev/null -w '%{http_code}')
if [ "$esito" != "200" ]; then
  echo "ronda: Telegram ha risposto $esito. L'avviso NON è partito" >&2
  exit 1                  # unità failed: si vede in systemctl, non sparisce
fi
[ "$PROVA" = 0 ] && echo "$OGGI" > "$TIMBRO"
echo '--- fine ronda'
