#!/bin/sh
# IL BATTITO (25 nov 2026, cantiere quadro-servizi). Ogni cinque minuti,
# dal timer battito.timer, per ogni servizio di QUESTA macchina: se il
# suo controllo passa, dice al VPS «e' vivo» (POST /api/battito), con
# l'eta' in ore del backup piu' recente quando la riga nomina una
# cartella. Un controllo che fallisce NON manda niente: e' il silenzio
# che il VPS vede, e dopo venti minuti avvisa nella stanza degli errori.
# CHI GUARDA IL VPS (GUARDA_VPS=1, sul relay): se il VPS non risponde a
# /api/salute per TRE giri di fila (un quarto d'ora) parte un avviso su
# Telegram, una volta; quando torna, un secondo. E' l'occhio da fuori:
# il VPS morto non puo' dire di essere morto.
# Il file vive in /usr/local/bin sulle macchine; questa e' la COPIA nel
# repo: chi tocca quello di la' lo riporta qui. Il perche' in CANTIERI,
# «Il quadro dei servizi»; l'installazione in PRODUZIONE, «IL QUADRO DEI
# SERVIZI E I BATTITI».
set -u
CONF=${BATTITO_CONF:-/etc/battito/battito.conf}
SERVIZI=${BATTITO_SERVIZI:-/etc/battito/servizi}
STATO=${BATTITO_STATO:-/var/lib/battito}
[ -r "$CONF" ] || { echo "battito: manca $CONF" >&2; exit 1; }
[ -r "$SERVIZI" ] || { echo "battito: manca $SERVIZI" >&2; exit 1; }
# BATTITO_URL e BATTITO_SEGRETO; facoltativi TOR_SOCKS (il nodo esce
# solo da Tor), GUARDA_VPS, SALUTE_URL, TG_TOKEN e TG_CHAT
. "$CONF"
GUARDA_VPS=${GUARDA_VPS:-0}
SALUTE_URL=${SALUTE_URL:-https://barattolo.store/api/salute}
TOR_SOCKS=${TOR_SOCKS:-}
MACCHINA=${MACCHINA:-$(hostname)}
mkdir -p "$STATO"

# la configurazione di curl: dentro le virgolette la barra rovescia e le
# virgolette sono escape (la lezione di _per_curl in ronda-pagamenti.py)
per_curl() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
socks() { [ -n "$TOR_SOCKS" ] && printf -- '--socks5-hostname\n%s\n' "$TOR_SOCKS"; }

# l'eta' in ore del file piu' recente di una cartella; vuota se non ce n'e'
eta_backup() {
    ultimo=$(ls -1t "$1" 2>/dev/null | head -n1)
    [ -n "$ultimo" ] || return 0
    echo $(( ( $(date +%s) - $(stat -c %Y "$1/$ultimo") ) / 3600 ))
}

# IL SEGRETO NON PASSA DALLA RIGA DI COMANDO: curl legge la sua
# configurazione da stdin (-K -), e `ps` non lo vede.
manda() {   # $1 = corpo JSON; stampa il codice HTTP
    # shellcheck disable=SC2046
    printf 'url = "%s"\nheader = "Authorization: Bearer %s"\nheader = "Content-Type: application/json"\ndata = "%s"\n' \
        "$(per_curl "$BATTITO_URL")" "$(per_curl "$BATTITO_SEGRETO")" \
        "$(per_curl "$1")" \
    | curl -sS --max-time 60 -o /dev/null -w '%{http_code}' $(socks) -K - 2>/dev/null
}

VIVI=""; MUTI=""
while IFS='|' read -r nome controllo cartella; do
    case "$nome" in ''|\#*) continue ;; esac
    if sh -c "$controllo" >/dev/null 2>&1; then
        corpo="{\"servizio\":\"$nome\"}"
        if [ -n "${cartella:-}" ]; then
            ore=$(eta_backup "$cartella")
            [ -n "$ore" ] && corpo="{\"servizio\":\"$nome\",\"backup_ore\":$ore}"
        fi
        codice=$(manda "$corpo")
        VIVI="$VIVI $nome:$codice"
    else
        MUTI="$MUTI $nome"
    fi
done < "$SERVIZI"
echo "battito: vivi${VIVI:- nessuno}; fermi${MUTI:- nessuno}"

[ "$GUARDA_VPS" = 1 ] || exit 0

# --- L'OCCHIO DA FUORI -------------------------------------------------
telegram() {
    [ -n "${TG_TOKEN:-}" ] && [ -n "${TG_CHAT:-}" ] || { echo "battito: niente Telegram per avvisare" >&2; return 1; }
    curl -fsS --max-time 30 $(socks) -o /dev/null -d "chat_id=$TG_CHAT" \
        --data-urlencode "text=$1" "https://api.telegram.org/bot$TG_TOKEN/sendMessage"
}
CONTO="$STATO/vps-muto"
codice=$(curl -sS --max-time 30 $(socks) -o /dev/null -w '%{http_code}' "$SALUTE_URL" 2>/dev/null)
prima=$(cat "$CONTO" 2>/dev/null || echo 0)
if [ "$codice" = 200 ]; then
    if [ "$prima" -ge 3 ]; then
        telegram "🩺 barattolo.store risponde di nuovo (visto da $MACCHINA)." || exit 1
    fi
    echo 0 > "$CONTO"
    echo "battito: VPS ok"
else
    ora=$((prima + 1))
    echo "battito: VPS non risponde ($codice), giro $ora"
    if [ "$ora" -eq 3 ]; then
        telegram "🩺 barattolo.store non risponde da un quarto d'ora (/api/salute: $codice, visto da $MACCHINA). Cosa fare: deploy/SE-MUORE.md, riga «VPS»." \
            || exit 1   # il conto non avanza: si riprova al giro dopo
    fi
    echo "$ora" > "$CONTO"
fi
