#!/bin/sh
# La lista di chi puo' scrivere, chiesta a Barattolo.
# Se qualunque cosa va storta si TIENE QUELLA DI IERI: un relay con la
# lista vecchia lascia fuori un venditore nuovo, un relay con la lista
# rotta li lascia fuori tutti.
NUOVO=/opt/relay/policy/chiavi.nuovo
BUONO=/opt/relay/policy/chiavi.txt

curl -fsS --max-time 20 -H @/opt/relay/token.header \
     https://barattolo.store/api/relay/chiavi -o "$NUOVO" || exit 1

if [ ! -s "$NUOVO" ] || grep -qvE '^[0-9a-f]{64}$' "$NUOVO"; then
    echo "risposta non valida: tengo la lista di ieri" >&2
    rm -f "$NUOVO"
    exit 1
fi

mv "$NUOVO" "$BUONO"
