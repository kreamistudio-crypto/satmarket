#!/bin/sh
# tor-entrypoint.sh — le regole del proxy trasparente DENTRO il container
# di tor, riapplicate a ogni avvio, e poi tor.
# PERCHE' (15 set 2026): le regole vivevano in un sidecar (tor-redirect)
# con `network_mode: service:tor`. Un `docker compose restart tor` rifa'
# il namespace di rete di tor, e il sidecar — su da 13 giorni — resta
# nel namespace VECCHIO, orfano e senza eth0: `docker exec` ci mostra
# le regole tutte al loro posto, e nel namespace vivo non c'e' niente.
# Mostro non usciva (curl «000» su ogni host), e gli ordini a prezzo di
# mercato morivano in silenzio. Con le regole QUI non esiste piu' un
# secondo processo che possa restare indietro: chi riavvia tor riavvia
# anche le regole, nello stesso gesto.
# FAIL-CLOSED: se iptables manca o una regola non entra, tor NON parte.
# Un tor senza redirect lascerebbe mostro senza uscita (ip_forward a 0
# di default), che e' gia' chiuso — ma un tor che parte e un errore che
# passa in silenzio e' esattamente la forma di guasto di oggi.
# Vive nel volume del compose del nodo (montato in sola lettura); questa
# e' la COPIA nel repo (deploy/nodo/).
set -eu
MOSTRO=${MOSTRO_IP:-172.28.1.5}
TRANS=${TRANS_PORT:-9040}
DNS=${DNS_PORT:-5353}

command -v iptables >/dev/null || { echo "tor-entrypoint: manca iptables nell'immagine di tor: mi fermo (fail-closed)" >&2; exit 1; }

# le tre REDIRECT, come nel sidecar: DNS (udp e tcp) alla DNSPort, tutto il tcp alla TransPort
iptables -w -t nat -F PREROUTING
iptables -w -t nat -A PREROUTING -s "$MOSTRO" -p udp --dport 53 -j REDIRECT --to-ports "$DNS"
iptables -w -t nat -A PREROUTING -s "$MOSTRO" -p tcp --dport 53 -j REDIRECT --to-ports "$DNS"
iptables -w -t nat -A PREROUTING -s "$MOSTRO" -p tcp -j REDIRECT --to-ports "$TRANS"
# la cura dell'audit (2 set 2026): quel che le tre REDIRECT non coprono
# (udp≠53, icmp) NON si inoltra in chiaro
iptables -w -F FORWARD
iptables -w -A FORWARD -s "$MOSTRO" -j DROP
# ...e la voce aperta dell'audit («il DROP e' solo in iptables e non in
# ip6tables»): su v6 non si inoltra niente, punto
if command -v ip6tables >/dev/null; then
  ip6tables -w -F FORWARD 2>/dev/null && ip6tables -w -A FORWARD -j DROP 2>/dev/null \
    || echo "tor-entrypoint: ip6tables non applicabile qui (v6 spento nel container?): si prosegue" >&2
fi
# l'inoltro: nel compose sta anche come sysctl (net.ipv4.ip_forward=1);
# qui si controlla che sia davvero acceso, o mostro resta muto
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" != 1 ]; then
  echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null \
    || { echo "tor-entrypoint: ip_forward a 0 e non scrivibile: metti sysctls net.ipv4.ip_forward=1 nel compose" >&2; exit 1; }
fi
echo "tor-entrypoint: redirect $MOSTRO -> dns:$DNS trans:$TRANS, FORWARD DROP, ip_forward=1"

# poi tor: col comando del compose se c'e', altrimenti il default dell'immagine
if [ $# -gt 0 ]; then exec "$@"; fi
exec tor -f /etc/tor/torrc
