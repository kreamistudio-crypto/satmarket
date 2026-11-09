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
#   1) check.torproject.org dal namespace di mostro: 000 = non esce (due
#      volte, a 30 s: un circuito lento non e' un guasto, 9 nov 2026);
#      IsTor false = esce IN CHIARO (peggio, e non si riprova);
#   2) MOSTRO DENTRO MOSTRO-NET (22 set 2026): il sidecar del 15 set non
#      c'e' piu' (le regole stanno in tor-entrypoint.sh, nel namespace di
#      tor stesso), ma il namespace PRESTATO che resta e' quello di
#      mostro, che vive in quello di mostro-net. Le REDIRECT e il DROP di
#      tor sono scritti per 172.28.1.5 e basta: un mostro ricreato fuori
#      da quel namespace (compose cambiato, `up` con altre opzioni,
#      mostro-net ricreato e mostro no) esce da un'altra strada, e la
#      superficie non lo vede, perche' guarda le regole del gateway e non
#      chi c'e' dietro. Tre pezzi, una forma sola giusta, niente baseline
#      da imparare (come il ponte WireGuard in ronda-superficie.sh):
#      a) stesso inode di /proc/<pid>/ns/net per mostro e mostro-net —
#         e' la prova che decide; NetworkMode serve solo a dire QUALE
#         guasto e' (ricreato fuori, o orfano di un restart di mostro-net);
#      b) l'IP che mostro vede su di se' e' 172.28.1.5;
#      c) il gateway di default di mostro-net e' l'IP di tor.
#      Un mostro FERMO si dice come fermo, non come «fuori dal namespace».
#   3) il DROP del FORWARD (la cura dell'audit) nel namespace VIVO di
#      tor, letto con l'iptables DI TOR (`docker exec`): dal 15 set sera
#      le regole vivono nel suo entrypoint e il namespace e' il suo, non
#      prestato — quindi qui `docker exec` dice il vero. Ripiego con
#      nsenter e l'iptables dell'host; senza nessuno dei due si dice
#      «non misurato», mai «ok».
# Tace se tutto torna; --prova parla coi numeri. Usa ronda-avvisa.sh come
# le altre. Timer: nodo-tor.timer (09:20 UTC, Persistent).
# Vive in /usr/local/bin sul nodo; questa e' la COPIA nel repo
# (deploy/nodo/), con la regola del relay: chi tocca il file di la' lo
# riporta qui nello stesso giro.
set -u
M=${M:-nodo-mostro-1}          # chi deve uscire
N=${N:-nodo-mostro-net-1}      # chi gli presta il namespace
T=${T:-nodo-tor-1}             # chi lo porta fuori
IPM=${IPM:-172.28.1.5}         # l'IP per cui tor-entrypoint.sh scrive REDIRECT e DROP
IMG=${IMG:-curlimages/curl}    # gia' sul nodo dal 15 set; --pull never, che la ronda non dipenda dalla rete
MODO=${1:-}
a=(); q=()

pid_di() { local p; p=$(docker inspect -f '{{.State.Pid}}' "$1" 2>/dev/null) || return 1
           [ -n "$p" ] && [ "$p" != 0 ] && echo "$p"; }
ns_di()  { local p; p=$(pid_di "$1") || return 1; readlink "/proc/$p/ns/net"; }
stato()  { docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null; }

# mostro gira? Se no, e' QUESTO il guasto, e i giudici 1 e 2 non hanno
# niente da misurare: un container fermo non esce e non ha un namespace
SM=$(stato "$M")
if [ -z "$SM" ]; then
  a+=("container $M non trovato: mostro non c'e', non si sa niente dell'uscita")
elif [ "$SM" != running ]; then
  a+=("mostro e' FERMO (stato: $SM): il coordinator non risponde; uscita e namespace non misurati, perche' non c'e' niente da misurare")
else
  # 1) la curl dal namespace di mostro: la sola prova end-to-end.
  # LA SECONDA PROVA (9 nov 2026): alle 09:20 di quel giorno la ronda ha
  # suonato «000» e venti minuti dopo, a mano, tutto rispondeva 200 con
  # le regole al loro posto: un circuito Tor lento oltre il minuto, non
  # un guasto (2 allarmi cosi' in 8 giorni). Un codice diverso da 200 si
  # riprova UNA volta dopo una pausa, e il quadro lo dice («al secondo
  # tentativo»), cosi' --prova e il journal tengono il conto dei buchi.
  # IsTor non true NON si riprova mai: uscire in chiaro anche una volta
  # e' gia' l'allarme, e una seconda curl in chiaro non lo cancella.
  curl_tor() { docker run --rm --pull never --network "container:$M" "$IMG" \
                 -s -m 60 -w '\n%{http_code}' https://check.torproject.org/api/ip 2>/dev/null; }
  RISP=$(curl_tor); PRIMO=''
  CODICE=$(printf '%s' "$RISP" | tail -n 1)
  if [ "$CODICE" != "200" ]; then
    PRIMO=${CODICE:-nulla}
    sleep "${PAUSA:-30}"
    RISP=$(curl_tor)
    CODICE=$(printf '%s' "$RISP" | tail -n 1)
  fi
  CORPO=$(printf '%s' "$RISP" | sed '$d')
  if [ "$CODICE" != "200" ]; then
    a+=("mostro NON ESCE: check.torproject.org risponde ${CODICE:-nulla} dal container $M (anche al secondo tentativo; il primo: $PRIMO)")
  elif ! printf '%s' "$CORPO" | grep -q '"IsTor":true'; then
    a+=("mostro esce IN CHIARO: IsTor non e' true ($CORPO)")
  else
    q+=("esce da Tor ($(printf '%s' "$CORPO" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4))${PRIMO:+ al secondo tentativo (il primo: $PRIMO)}")
  fi

  # 2) mostro dentro mostro-net, con l'IP giusto e tor come gateway
  SN=$(stato "$N")
  if [ "$SN" != running ]; then
    COM="e' ${SN:-sparito (container non trovato)}"
    a+=("mostro-net $COM mentre mostro gira: mostro vive in un namespace senza padrone. Cura: cd ~/nodo && docker compose up -d mostro-net && docker compose up -d --force-recreate mostro")
  else
    NM=$(ns_di "$M"); NN=$(ns_di "$N")
    if [ -z "$NM" ] || [ -z "$NN" ]; then
      a+=("namespace di $M o $N illeggibile (${NM:-?} / ${NN:-?}): non misurato")
    elif [ "$NM" != "$NN" ]; then
      MODE=$(docker inspect -f '{{.HostConfig.NetworkMode}}' "$M" 2>/dev/null)
      IDN=$(docker inspect -f '{{.Id}}' "$N" 2>/dev/null)
      if [ -n "$IDN" ] && [ "$MODE" = "container:$IDN" ]; then
        a+=("mostro in un namespace ORFANO ($NM, mostro-net ha $NN): mostro-net riavviato e mostro no. Cura: cd ~/nodo && docker compose up -d --force-recreate mostro")
      else
        a+=("mostro FUORI dal namespace di mostro-net ($NM contro $NN, NetworkMode ${MODE:-illeggibile}): esce da un'altra strada. Il compose di mostro deve dire network_mode: \"service:mostro-net\"")
      fi
    else
      q+=("mostro nel namespace di mostro-net")
    fi
    PN=$(pid_di "$N")
    if ! command -v nsenter >/dev/null || ! command -v ip >/dev/null; then
      a+=("IP e gateway di mostro non misurati (manca nsenter o ip sull'host)")
    else
      PM=$(pid_di "$M")
      IPV=$(nsenter -t "$PM" -n ip -4 -o addr show 2>/dev/null | awk '$2 != "lo" {sub("/.*", "", $4); print $4}' | paste -sd' ' -)
      if [[ " $IPV " != *" $IPM "* ]]; then
        a+=("mostro vede ${IPV:-nessun IP} e non $IPM: le REDIRECT e il DROP di tor non lo riguardano")
      else
        q+=("IP $IPM")
      fi
      GW=$(nsenter -t "$PN" -n ip -4 route show default 2>/dev/null | awk '{for (i = 1; i < NF; i++) if ($i == "via") { print $(i+1); exit }}')
      IPT=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' "$T" 2>/dev/null)
      if [ -z "${IPT// /}" ]; then
        a+=("IP di $T illeggibile: il gateway di mostro-net (${GW:-nessuno}) non si confronta")
      elif [ -z "$GW" ] || [[ " $IPT " != *" $GW "* ]]; then
        a+=("il gateway di default di mostro-net e' ${GW:-ASSENTE}, non tor ($IPT): il traffico di mostro non passa da Tor")
      else
        q+=("gateway $GW = tor")
      fi
    fi
  fi
fi

# 3) il DROP del FORWARD nel namespace VIVO di tor
PT=$(pid_di "$T")
FWD=''; IPF=''
# un file usa-e-getta SUO (1 ott 2026, B5 del secondo audit), mai un nome
# fisso in /tmp scritto da root
FWDF=$(mktemp /tmp/ronda-tor-fwd.XXXXXX) || FWDF=''
if [ -n "$FWDF" ] && docker exec "$T" iptables -S FORWARD >"$FWDF" 2>/dev/null; then
  FWD=$(cat "$FWDF"); IPF=$(docker exec "$T" cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)
elif [ -n "${PT:-}" ] && command -v nsenter >/dev/null && command -v iptables >/dev/null; then
  FWD=$(nsenter -t "$PT" -n iptables -S FORWARD 2>/dev/null)
  IPF=$(nsenter -t "$PT" -n cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)
fi
[ -n "$FWDF" ] && rm -f "$FWDF"
if [ -n "$IPF" ]; then
  if [ "$IPF" = 1 ] && ! printf '%s' "$FWD" | grep -q -- "-s $IPM/32 -j DROP"; then
    a+=("ip_forward=1 SENZA il DROP -s $IPM nel FORWARD di tor: il buco dell'audit e' riaperto")
  elif [ "$IPF" = 1 ]; then
    q+=("DROP del FORWARD al suo posto")
  else
    q+=("ip_forward=${IPF:-?} in tor (con le regole nell'entrypoint e' 1; a 0 mostro non esce, e lo dice il giudice 1)")
  fi
else
  q+=("DROP del FORWARD non misurato (ne' iptables in tor ne' nsenter+iptables sull'host)")
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
