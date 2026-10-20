#!/bin/bash
# collaudo — I COMANDI DELLA VM DI COLLAUDO (20 ott 2026, cantiere
# collaudo-privato; procedura: docs/COLLAUDO.md). Si posa come
# /usr/local/bin/collaudo e si usa con sudo:
#   sudo collaudo                 lo stato: cosa gira, da quale ramo, se e' in pausa
#   sudo collaudo pausa           il collaudo smette di seguire il ramo
#   sudo collaudo riprendi        torna a seguire develop (e toglie la pausa)
#   sudo collaudo ramo <nome>     segue un altro ramo (es. cantiere/x) finche'
#                                 non si da' `riprendi`
#   sudo collaudo azzera          database e foto NUOVI, piu' la semina finta
#                                 (semina_collaudo.py: venditori, annunci, ordini):
#                                 i vecchi si spostano in azzerati/ (gli
#                                 ultimi tre), niente si cancella a mano
# Le variabili COLLAUDO_* servono solo alle prove; sulla VM non si toccano.
set -euo pipefail

DIR="${COLLAUDO_DIR:-/srv/collaudo/barattolo}"
STATO="${COLLAUDO_STATO:-/srv/collaudo/stato}"
SERVIZIO="${COLLAUDO_SERVIZIO:-barattolo-collaudo}"
SEGUI_UNITA="${COLLAUDO_SEGUI_UNITA:-barattolo-collaudo-segui}"
SALUTE="${COLLAUDO_SALUTE:-http://127.0.0.1:8090/api/salute}"
PY="${COLLAUDO_PY:-/srv/collaudo/venv/bin/python}"
AZZERATI_TENUTI=3
if [ -n "${COLLAUDO_COME+x}" ]; then
  read -r -a COME <<< "$COLLAUDO_COME"
else
  COME=(runuser -u collaudo --)
fi
git_() { "${COME[@]}" git -C "$DIR" "$@"; }
ramo_seguito() { if [ -s "$STATO/ramo" ]; then head -1 "$STATO/ramo"; else echo develop; fi; }
nome_buono() { [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$ ]] && [[ "$1" != *..* ]]; }

mkdir -p "$STATO"
case "${1:-stato}" in
  stato)
    echo "ramo seguito: $(ramo_seguito)$([ -e "$STATO/pausa" ] && echo '  (IN PAUSA)')"
    echo "gira:         $(git_ log -1 --format='%h %s' | cut -c1-90)"
    [ -s "$STATO/bocciato" ] && echo "bocciato:     $(cut -c1-8 "$STATO/bocciato") (non si riprova finche' il ramo non va oltre)"
    echo "servizio:     $(systemctl is-active "$SERVIZIO" 2> /dev/null || true)"
    journalctl -u "$SEGUI_UNITA" -n 4 --no-pager -o cat 2> /dev/null || true
    ;;
  pausa)
    touch "$STATO/pausa"
    echo "⏸️ in pausa: il collaudo resta su $(git_ log -1 --format=%h)"
    ;;
  riprendi)
    rm -f "$STATO/pausa" "$STATO/ramo"
    echo "▶️ torno a seguire develop"
    systemctl start "$SEGUI_UNITA" || true
    ;;
  ramo)
    nuovo="${2:-}"
    nome_buono "$nuovo" || { echo "uso: collaudo ramo <nome del ramo>"; exit 2; }
    git_ fetch -q --prune origin
    git_ rev-parse --verify -q "refs/remotes/origin/$nuovo^{commit}" > /dev/null \
      || { echo "il ramo $nuovo non c'e' su origin"; exit 1; }
    echo "$nuovo" > "$STATO/ramo"
    rm -f "$STATO/pausa"
    echo "🔀 seguo $nuovo (per tornare a develop: collaudo riprendi)"
    systemctl start "$SEGUI_UNITA" || true
    ;;
  azzera)
    ora="$(date +%Y%m%d-%H%M%S)"
    systemctl stop "$SERVIZIO"
    "${COME[@]}" mkdir -p "$DIR/azzerati"
    for f in dati/satmarket.db dati/satmarket.db-wal dati/satmarket.db-shm; do
      [ -e "$DIR/$f" ] && mv "$DIR/$f" "$DIR/azzerati/$(basename "$f")-$ora"
    done
    [ -d "$DIR/foto" ] && mv "$DIR/foto" "$DIR/azzerati/foto-$ora"
    "${COME[@]}" mkdir -p "$DIR/foto" "$DIR/dati"
    # degli azzerati si tengono gli ultimi tre giri; i piu' vecchi vanno
    ls -1dt "$DIR"/azzerati/satmarket.db-2* 2> /dev/null | tail -n +$((AZZERATI_TENUTI + 1)) \
      | while read -r v; do rm -f "$v"; done
    ls -1dt "$DIR"/azzerati/foto-2* 2> /dev/null | tail -n +$((AZZERATI_TENUTI + 1)) \
      | while read -r v; do rm -rf "$v"; done
    systemctl start "$SERVIZIO"
    for _ in $(seq 1 45); do curl -fsS -m 3 "$SALUTE" > /dev/null 2>&1 && break; sleep 1; done
    (cd "$DIR" && "${COME[@]}" "$PY" semina_collaudo.py)
    echo "🧹 azzerato ($ora): database e foto nuovi, semina fatta"
    ;;
  *)
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
