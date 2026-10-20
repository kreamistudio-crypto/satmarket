#!/bin/bash
# segui.sh — IL COLLAUDO SEGUE DEVELOP (20 ott 2026, cantiere
# collaudo-privato, decisione di Andrea; procedura: docs/COLLAUDO.md).
#
# Sulla VM di collaudo (vm-2050) gira ogni minuto dal timer
# `barattolo-collaudo-segui`, da root, da una COPIA in
# /usr/local/sbin/collaudo-segui: il giudice non si riscrive da solo col
# commit che tira (la stessa regola di deploy.sh, «il giudice e' sempre
# quello di prima»). Una versione nuova di questo file si posa a mano.
#
# NON E' deploy.sh, ed e' voluto. deploy.sh e' la PRODUZIONE: tira solo
# commit su main, in avanti, firmati da una chiave del VPS e con la CI
# verde. Il collaudo invece:
#   - segue `develop` (o il ramo scelto con `collaudo ramo <nome>`);
#   - accetta commit NON firmati (le sessioni cloud) e senza CI (su
#     develop la CI non parte);
#   - accetta un develop rimesso uguale a main dopo una promozione, cioe'
#     non per forza in avanti;
#   - sta fermo se c'e' la pausa (`collaudo pausa`).
# A ogni cambio: checkout, compileall, riavvio, /api/salute entro ATTESA
# secondi; se non regge torna al commit di prima e TIMBRA il bocciato,
# che non si riprova finche' il ramo non va oltre. Una riga al bot di
# prova, se in /etc/barattolo-collaudo c'e' a chi mandarla.
#
# Le variabili COLLAUDO_* servono SOLO alle prove di prove.py, che fanno
# girare questo script su un repo finto. Sulla VM non si impostano mai.
set -uo pipefail

DIR="${COLLAUDO_DIR:-/srv/collaudo/barattolo}"
STATO="${COLLAUDO_STATO:-/srv/collaudo/stato}"
SERVIZIO="${COLLAUDO_SERVIZIO:-barattolo-collaudo}"
SALUTE="${COLLAUDO_SALUTE:-http://127.0.0.1:8090/api/salute}"
ATTESA="${COLLAUDO_ATTESA:-45}"
PY="${COLLAUDO_PY:-/srv/collaudo/venv/bin/python}"
SEGRETI="${COLLAUDO_SEGRETI:-/etc/barattolo-collaudo}"
RIAVVIA="${COLLAUDO_RIAVVIA:-systemctl restart $SERVIZIO}"
# git lo fa girare l'utente del collaudo: il repo e la deploy key sono suoi
if [ -n "${COLLAUDO_COME+x}" ]; then
  read -r -a COME <<< "$COLLAUDO_COME"
else
  COME=(runuser -u collaudo --)
fi

dillo() { echo "🧪 collaudo: $*"; }
avvisa() {
  # il token e la chat dai file dei segreti, e il token MAI sulla riga di
  # comando: curl lo legge dalla sua configurazione, sullo stdin
  local t="$SEGRETI/bot_token" c="$SEGRETI/avvisi_chat"
  [ -r "$t" ] && [ -s "$c" ] || return 0
  printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$(tr -d '\r\n' < "$t")" \
    | curl -s -m 10 -K - --data-urlencode "chat_id=$(head -1 "$c" | tr -d '\r')" \
           --data-urlencode "text=$1" > /dev/null || true
}
git_() { "${COME[@]}" git -C "$DIR" "$@"; }

mkdir -p "$STATO"
[ -e "$STATO/pausa" ] && exit 0
RAMO=develop
[ -s "$STATO/ramo" ] && RAMO="$(head -1 "$STATO/ramo" | tr -d '\r')"
if ! [[ "$RAMO" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$ ]] || [[ "$RAMO" == *..* ]]; then
  dillo "in $STATO/ramo non c'e' un nome di ramo: resto fermo"
  exit 1
fi
git_ fetch -q --prune origin 2> /dev/null || { dillo "fetch non riuscito: riprovo al giro dopo"; exit 0; }
LA="$(git_ rev-parse --verify -q "refs/remotes/origin/$RAMO^{commit}")" \
  || { dillo "il ramo $RAMO non c'e' su origin: resto dove sono"; exit 0; }
QUI="$(git_ rev-parse HEAD)"
[ "$LA" = "$QUI" ] && exit 0
[ "$LA" = "$(cat "$STATO/bocciato" 2> /dev/null)" ] && exit 0

dillo "aggiorno: ${QUI:0:8} → ${LA:0:8} ($RAMO)"
# --force e' quello di checkout (i file tracciati tornano quelli del
# commit), MAI quello di push: i file NON tracciati — config.py, dati/,
# foto/ — restano dove sono
git_ checkout -q --force --detach "$LA" || { dillo "checkout non riuscito: resto su ${QUI:0:8}"; exit 1; }
if ! "${COME[@]}" "$PY" -m compileall -q -l "$DIR" > /dev/null; then
  esito=compila
elif ! $RIAVVIA; then
  esito=riavvio
else
  esito=salute
  for _ in $(seq 1 "$ATTESA"); do
    if curl -fsS -m 3 "$SALUTE" > /dev/null 2>&1; then esito=ok; break; fi
    sleep 1
  done
fi
if [ "$esito" = ok ]; then
  rm -f "$STATO/bocciato"
  echo "$LA" > "$STATO/gira"
  dillo "fatto: ${LA:0:8}"
  avvisa "🧪 Collaudo aggiornato: ${LA:0:8} ($RAMO) — $(git_ log -1 --format=%s "$LA" | cut -c1-80)"
  exit 0
fi
dillo "${LA:0:8} non regge ($esito): torno a ${QUI:0:8}"
echo "$LA" > "$STATO/bocciato"
git_ checkout -q --force --detach "$QUI"
$RIAVVIA || true
avvisa "↩️ Collaudo: ${LA:0:8} ($RAMO) non regge ($esito), torno a ${QUI:0:8}"
exit 1
