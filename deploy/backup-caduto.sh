#!/bin/bash
# IL GIORNALIERO FERMATO DA FUORI (20 ott 2026, cantiere backup-ritocchi,
# richiesta di Andrea): l'ultima rete sotto deploy/backup-fuori.sh.
#
# Lo chiama systemd DOPO ogni giro del backup giornaliero
# (`ExecStopPost=` di deploy/barattolo-backup.service), con lo stato del
# giro in $SERVICE_RESULT: success, exit-code, timeout, signal, oom-kill…
# Il backup di solito sa dirlo da solo — la sua trappola d'uscita manda
# l'avviso, anche al SIGTERM dei 600 s — e lascia il segno
# (`backup/.giornaliero-avvisato`, col numero del giro di systemd): allora
# qui si tace. Si parla solo quando il backup non ha potuto: un SIGKILL
# dopo il SIGTERM, la memoria finita, un bash che non e' nemmeno partito.
# Mai due avvisi per lo stesso giro, mai nessuno per un giro andato male.
#
# L'avviso lo manda deploy.sh (`--avvisa`), da una copia e solo se lo
# conosce: la regola del gruppo e delle stanze sta in un posto solo.
# Non fallisce mai: un ExecStopPost rosso non aggiunge niente.

set -uo pipefail

# TUTTO DENTRO UNA FUNZIONE, chiamata sull'ultima riga insieme a `exit`:
# gira dal repo (non da una copia, come fa la unit per backup-fuori.sh),
# e bash rilegge il file dopo ogni comando esterno — un `git reset` a
# meta' giro darebbe la riga dopo di un altro script. Una funzione si
# legge intera prima di partire.
main() {
    DIR_APP="${BARATTOLO_DIR:-/root/satmarket}"
    ESITO="${SERVICE_RESULT:-}"

    # un giro andato bene, o chiamato fuori da systemd: niente da dire
    [ -n "$ESITO" ] && [ "$ESITO" != "success" ] || return 0

    GIA="$(cat "$DIR_APP/backup/.giornaliero-avvisato" 2>/dev/null || true)"
    if [ -n "${INVOCATION_ID:-}" ] && [ "$GIA" = "$INVOCATION_ID" ]; then
        echo "il backup ha gia' avvisato per questo giro"
        return 0
    fi

    case "$ESITO" in
        timeout)   PERCHE="ha superato il tempo massimo della unit e systemd l'ha fermato" ;;
        signal)    PERCHE="è stato ucciso da un segnale (${EXIT_STATUS:-?})" ;;
        core-dump) PERCHE="è caduto con un core dump (${EXIT_STATUS:-?})" ;;
        oom-kill)  PERCHE="è stato ucciso perché la memoria era finita" ;;
        exit-code) PERCHE="è uscito col codice ${EXIT_STATUS:-?} senza riuscire a dirlo da solo" ;;
        *)         PERCHE="è finito male (${ESITO//[^a-z-]/})" ;;
    esac
    TESTO="⚠️ <b>Il backup giornaliero si è fermato prima di finire</b>: $PERCHE. Nessun archivio garantito questa volta; se è stato fatto, resta in <code>backup/fuori/</code>. Guardare <code>journalctl -u barattolo-backup -n 40</code>."

    D="$(mktemp -d)" || return 0
    trap 'rm -rf "$D"' EXIT
    if cp "$DIR_APP/deploy.sh" "$D/deploy.sh" 2>/dev/null && grep -q -- '--avvisa' "$D/deploy.sh"; then
        BARATTOLO_DIR="$DIR_APP" timeout 60 bash "$D/deploy.sh" --avvisa "$TESTO" \
            || echo "avviso agli admin non partito" >&2
    else
        echo "avviso agli admin non partito: $DIR_APP/deploy.sh non sa avvisare" >&2
    fi
}

main "$@"; exit 0
