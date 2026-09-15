#!/bin/bash
# ronda-tor.sh — la domanda che il 15 set 2026 nessuno faceva: MOSTRO ESCE,
# E ESCE DA TOR? Quel giorno due restart di tor hanno lasciato il sidecar
# tor-redirect nel namespace di rete VECCHIO (orfano, senza eth0): le
# regole c'erano tutte, lette con `docker exec` — ma in un namespace dove
# non passava piu' un pacchetto. Dal container di mostro ogni curl faceva
# «000», yadio compreso, e gli ordini a prezzo di mercato morivano in
# silenzio per tre ore. La ronda guardava superficie e canali, non se il
# container USCISSE: questa e' la quinta domanda, e la fa dal namespace
# di mostro, cioe' dal punto di vista di chi deve uscire.
# Tre giudici, dal piu' vero al piu' fine:
#   1) check.torproject.org dal namespace di mostro: 000 = non esce;
#      IsTor false = esce IN CHIARO (peggio);
#   2) mentre esiste il sidecar tor-redirect: il suo namespace e quello
#      di tor devono COINCIDERE — e' il guasto del 15 set letto alla
#      radice, prima ancora che la curl fallisca;
#   3) il DROP del FORWARD (la cura dell'audit) nel namespace VIVO di
#      tor, letto con nsenter e l'iptables dell'host: se l'host non ha
#      iptables si dice «non misurato», mai «ok».
# Tace se tutto torna; --prova parla coi numeri. Usa ronda-avvisa.sh come
# le altre. Timer: nodo-tor.timer (09:20 UTC, Persistent).
# Vive in /usr/local/bin sul nodo; questa e' la COPIA nel repo
# (deploy/nodo/), con la regola del relay: chi tocca il file di la' lo
# riporta qui nello stesso giro.
set -u
M=${M:-nodo-mostro-1}          # chi deve uscire
T=${T:-nodo-tor-1}             # chi lo porta fuori
R=${R:-nodo-tor-redirect-1}    # il sidecar, finche' esiste (la cura durevole lo toglie)
IMG=${IMG:-curlimages/curl}    # gia' sul nodo dal 15 set; --pull never, che la ronda non dipenda dalla rete
MODO=${1:-}
a=(); q=()

# 1) la curl dal namespace di mostro: la sola prova end-to-end
if docker inspect "$M" >/dev/null 2>&1; then
  RISP=$(docker run --rm --pull never --network "container:$M" "$IMG" \
           -s -m 60 -w '\n%{http_code}' https://check.torproject.org/api/ip 2>/dev/null)
  CODICE=$(printf '%s' "$RISP" | tail -n 1)
  CORPO=$(printf '%s' "$RISP" | sed '$d')
  if [ "$CODICE" != "200" ]; then
    a+=("mostro NON ESCE: check.torproject.org risponde ${CODICE:-nulla} dal container $M")
  elif ! printf '%s' "$CORPO" | grep -q '"IsTor":true'; then
    a+=("mostro esce IN CHIARO: IsTor non e' true ($CORPO)")
  else
    q+=("esce da Tor ($(printf '%s' "$CORPO" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4))")
  fi
else
  a+=("container $M non trovato: non si sa se mostro esce")
fi

# 2) i namespace: tor e il sidecar devono essere lo stesso, finche' il sidecar c'e'
pid_ns() { local p; p=$(docker inspect -f '{{.State.Pid}}' "$1" 2>/dev/null) || return 1
           [ -n "$p" ] && [ "$p" != 0 ] && readlink "/proc/$p/ns/net"; }
if docker inspect "$R" >/dev/null 2>&1; then
  NT=$(pid_ns "$T"); NR=$(pid_ns "$R")
  if [ -z "$NT" ] || [ -z "$NR" ]; then
    a+=("namespace di $T o $R illeggibile (uno dei due e' fermo?)")
  elif [ "$NT" != "$NR" ]; then
    a+=("il sidecar $R sta in un namespace ORFANO ($NR, tor ha $NT): cura = cd ~/nodo && docker compose up -d --force-recreate tor-redirect")
  else
    q+=("sidecar nel namespace vivo di tor")
  fi
fi

# 3) il DROP del FORWARD nel namespace VIVO di tor
PT=$(docker inspect -f '{{.State.Pid}}' "$T" 2>/dev/null)
if [ -n "${PT:-}" ] && [ "$PT" != 0 ] && command -v nsenter >/dev/null && command -v iptables >/dev/null; then
  FWD=$(nsenter -t "$PT" -n iptables -S FORWARD 2>/dev/null)
  IPF=$(nsenter -t "$PT" -n cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)
  if [ "$IPF" = 1 ] && ! printf '%s' "$FWD" | grep -q -- '-s 172.28.1.5/32 -j DROP'; then
    a+=("ip_forward=1 SENZA il DROP -s 172.28.1.5 nel FORWARD di tor: il buco dell'audit e' riaperto")
  elif [ "$IPF" = 1 ]; then
    q+=("DROP del FORWARD al suo posto")
  else
    q+=("ip_forward=${IPF:-?} in tor (con le regole nell'entrypoint e' 1; a 0 mostro non esce, e lo dice il giudice 1)")
  fi
else
  q+=("DROP del FORWARD non misurato (manca nsenter o iptables sull'host)")
fi

QUADRO=$(IFS='; '; echo "${q[*]:-}")
if [ ${#a[@]} -gt 0 ]; then
  OUT="ALLARME TOR"$'\n'"$(printf -- '- %s\n' "${a[@]}")"$'\n'"$QUADRO"
  echo "$OUT"
  printf '%s\n--- fine ronda tor\n' "$OUT" | /usr/local/bin/ronda-avvisa.sh
  exit 0
fi
if [ "$MODO" = "--prova" ]; then
  OUT="PROVA tor: $QUADRO"
  echo "$OUT"
  printf '%s\n--- fine ronda tor\n' "$OUT" | /usr/local/bin/ronda-avvisa.sh
  exit 0
fi
echo "tor ok  $QUADRO"
exit 0
