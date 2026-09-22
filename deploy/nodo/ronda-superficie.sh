#!/bin/bash
# ronda-superficie.sh — la quarta domanda della ronda: COSA E' ESPOSTO,
# e da quando? Fotografa quel che ascolta fuori dal loopback, i DNAT di
# Docker, le regole di rete dentro tor (il gateway di mostro) e le
# confronta con una baseline IMPARATA: nomina cosa e' comparso o
# sparito. `--impara` e' un gesto, mai automatico.
# Vive in /usr/local/bin sul nodo; questa e' la COPIA nel repo
# (deploy/nodo/), con la regola del relay: chi tocca il file di la' lo
# riporta qui nello stesso giro.
#
# 22 set 2026, tre ritocchi:
# 1) cercava `nodo-tor-redirect-1`, il sidecar sparito il 15 set quando
#    le regole sono passate in tor-entrypoint.sh: corretto a mano sul
#    nodo in `nodo-tor-1`, e qui riportato.
# 2) IL DNS INTERNO DI DOCKER cambia porta a ogni riavvio del container:
#    le righe DOCKER_OUTPUT/DOCKER_POSTROUTING (127.0.0.11:<porta>) davano
#    un allarme falso a ogni restart di tor. Si maschera il SOLO numero di
#    porta, e su tutt'e due i lati del confronto (baseline compresa, cosi'
#    quella imparata prima non va rifatta): se una di quelle regole
#    sparisce, o ne compare una nuova, o cambia l'indirizzo, suona ancora.
# 3) IL PONTE WIREGUARD (in servizio dal 21 set, deploy/ponte/): la foto
#    di prima guardava solo il TCP, quindi la 51820/udp e la catena
#    WG-PONTE non le vedeva nessuno. Qui NON si imparano: si confrontano
#    con quel che wg0-nodo.conf deve aver montato, regola per regola,
#    perche' una baseline impara anche una regola sbagliata, mentre il
#    firewall del tunnel ha una forma sola giusta. Ogni pezzo che manca
#    ha il suo allarme col suo nome.
set -u
NOTA=/var/lib/ronda/superficie
IMPARA=0; [ "${1:-}" = "--impara" ] && IMPARA=1
mkdir -p "$(dirname "$NOTA")"

# la porta del DNS interno di Docker non e' superficie: cambia da sola
maschera_dns_docker() {
  sed -E '/^gw-nat -A DOCKER_(OUTPUT|POSTROUTING) /{
            s/(127\.0\.0\.11):[0-9]+/\1:PORTA/g
            s/--sport [0-9]+/--sport PORTA/g
          }' | sort -u
}

ORA=$( { ss -tlnH | awk '{print "ascolta " $4}' | grep -vE '^ascolta (127\.|\[::1\])'
         iptables  -t nat -S DOCKER 2>/dev/null | grep -v '^-N ' | sed 's/^/dnat4 /'
         ip6tables -t nat -S DOCKER 2>/dev/null | grep -v '^-N ' | sed 's/^/dnat6 /'
         G=$(docker inspect nodo-tor-1 --format '{{.State.Pid}}' 2>/dev/null)
         if [ -n "${G:-}" ] && [ "$G" != 0 ]; then
           nsenter -t "$G" -n iptables -t nat -S 2>/dev/null | sed 's/^/gw-nat /'
           nsenter -t "$G" -n iptables        -S 2>/dev/null | sed 's/^/gw-flt /'
         else
           echo 'gw-ASSENTE tor (gateway di mostro) non gira'
         fi
       } | maschera_dns_docker )

if [ "$IMPARA" = 1 ]; then
  printf '%s\n' "$ORA" > "$NOTA"
  echo "superficie: baseline scritta"; printf '%s\n' "$ORA" | sed 's/^/  /'; exit 0
fi

# --- il ponte WireGuard: la forma giusta e' una sola (wg0-nodo.conf) ---
WG=wg0; VPS=46.62.162.103; QUI=10.77.0.1; LA=10.77.0.2; REST=18080; PORTA=51820
W=()
# riga di una catena che contiene TUTTI i pezzi dati, separati da «;»
# (ogni pezzo e' una coppia intera, «-i wg0», perche' iptables -S ristampa
# le opzioni in un ordine suo): stampa il suo numero, 0 se non c'e'
riga_con() {
  printf '%s\n' "$1" | awk -v t="$2" '
    BEGIN { n = split(t, p, ";") }
    /^-A / { r++; ok = 1
             for (i = 1; i <= n; i++) if (index($0 " ", p[i] " ") == 0) ok = 0
             if (ok) { print r; trovata = 1; exit } }
    END { if (!trovata) print 0 }'
}
if ! ip link show "$WG" >/dev/null 2>&1; then
  W+=("interfaccia $WG ASSENTE: il ponte verso LND e' giu' (wg-quick@$WG)")
else
  if command -v wg >/dev/null; then
    LP=$(wg show "$WG" listen-port 2>/dev/null)
    [ "$LP" = "$PORTA" ] || W+=("$WG ascolta su ${LP:-nessuna porta}, atteso $PORTA")
    NP=$(wg show "$WG" peers 2>/dev/null | grep -c .)
    [ "$NP" = 1 ] || W+=("$WG ha $NP peer, atteso 1 (il solo VPS): una peer in piu' e' una porta in piu'")
  else
    W+=("comando wg assente: porta e peer del tunnel non misurati")
  fi
  CAT=$(iptables -w -S WG-PONTE 2>/dev/null)
  if [ -z "$CAT" ]; then
    W+=("catena WG-PONTE ASSENTE: il tunnel e' su senza il suo firewall")
  else
    P1=$(riga_con "$CAT" " -i $WG; -s $LA/32; -d $QUI/32; -p tcp; --dport $REST; -j ACCEPT")
    P2=$(riga_con "$CAT" " -i $WG; -j DROP")
    P3=$(riga_con "$CAT" " -d $QUI/32; -j DROP")
    P4=$(riga_con "$CAT" " -s $VPS/32; -p udp; --dport $PORTA; -j ACCEPT")
    P5=$(riga_con "$CAT" " -p udp; --dport $PORTA; -j DROP")
    [ "$P1" != 0 ] || W+=("WG-PONTE: manca l'ACCEPT di $LA verso $QUI:$REST")
    [ "$P2" != 0 ] || W+=("WG-PONTE: manca il DROP di tutto il resto che arriva da $WG")
    [ "$P3" != 0 ] || W+=("WG-PONTE: manca il DROP verso $QUI dalle altre interfacce")
    [ "$P4" != 0 ] || W+=("WG-PONTE: manca l'ACCEPT della $PORTA/udp dal VPS")
    [ "$P5" != 0 ] || W+=("WG-PONTE: manca il DROP della $PORTA/udp per tutti gli altri: il tunnel risponde al mondo")
    { [ "$P1" = 0 ] || [ "$P2" = 0 ] || [ "$P1" -lt "$P2" ]; } \
      || W+=("WG-PONTE: il DROP di $WG sta SOPRA l'ACCEPT della $REST: il ponte e' chiuso")
    { [ "$P4" = 0 ] || [ "$P5" = 0 ] || [ "$P4" -lt "$P5" ]; } \
      || W+=("WG-PONTE: il DROP della $PORTA sta SOPRA l'ACCEPT del VPS: il ponte e' chiuso")
    NR=$(printf '%s\n' "$CAT" | grep -c '^-A ')
    [ "$NR" = 5 ] || W+=("WG-PONTE ha $NR regole, attese 5: $(printf '%s\n' "$CAT" | grep '^-A ' | sed 's/^-A WG-PONTE //' | paste -sd'|' -)")
  fi
  PRIMA=$(iptables -w -S INPUT 2>/dev/null | grep '^-A ' | head -n 1)
  [ "$PRIMA" = "-A INPUT -j WG-PONTE" ] \
    || W+=("WG-PONTE non e' in cima a INPUT (la prima e': ${PRIMA:-nessuna})")
  FWD=$(iptables -w -S FORWARD 2>/dev/null)
  [ "$(riga_con "$FWD" " -i $WG; -j DROP")" != 0 ] || W+=("FORWARD: manca il DROP di cio' che ENTRA da $WG (chi prende il VPS arriva ai container)")
  [ "$(riga_con "$FWD" " -o $WG; -j DROP")" != 0 ] || W+=("FORWARD: manca il DROP di cio' che ESCE verso $WG")
  if iptables -w -S DOCKER-USER >/dev/null 2>&1; then
    [ "$(riga_con "$(iptables -w -S DOCKER-USER)" " -i $WG; -j DROP")" != 0 ] \
      || W+=("DOCKER-USER: manca il DROP di $WG (Docker si rimette in cima a FORWARD e scavalca le due righe)")
  fi
  if command -v ip6tables >/dev/null; then
    [ "$(riga_con "$(ip6tables -w -S INPUT 2>/dev/null)" " -p udp; --dport $PORTA; -j DROP")" != 0 ] \
      || W+=("ip6tables: la $PORTA/udp e' APERTA su v6 (manca il DROP in INPUT)")
  fi
fi

D=''
[ -f "$NOTA" ] && D=$(diff <(maschera_dns_docker < "$NOTA") <(printf '%s\n' "$ORA") | grep -E '^[<>]')
if [ -n "$D" ] || [ ${#W[@]} -gt 0 ]; then
  T='ALLARME SUPERFICIE'
  [ -n "$D" ] && T+=$'\n'"$D"$'\n\n(> comparso, < sparito)\nSe e tuo:  sudo /usr/local/bin/ronda-superficie.sh --impara'
  [ ${#W[@]} -gt 0 ] && T+=$'\n\nPONTE WIREGUARD (non si impara: la forma giusta sta in deploy/ponte/wg0-nodo.conf)\n'"$(printf -- '- %s\n' "${W[@]}")"
  echo "$T"; printf '%s\n' "$T" | /usr/local/bin/ronda-avvisa.sh
fi
[ -f "$NOTA" ] || echo "superficie: nessuna baseline, lancia --impara"
[ -f "$NOTA" ] && [ -z "$D" ] && echo "superficie ok  $(printf '%s\n' "$ORA" | wc -l) righe invariate"
[ ${#W[@]} -eq 0 ] && echo "ponte wg ok  WG-PONTE in cima a INPUT, 5 regole, $PORTA/udp al solo VPS"
exit 0
