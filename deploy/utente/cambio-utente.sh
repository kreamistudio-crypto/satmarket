#!/usr/bin/env bash
#
# IL CAMBIO D'UTENTE: il mercatino smette di girare da root (set 2026,
# audit del 19 set — A1).
#
# PERCHE' UNO SCRIPT E NON DIECI COMANDI INCOLLATI: per qualche secondo
# il sito e' GIU' (fra lo stop e lo start), e in quei secondi non si
# digita. Tutto quel che si puo' controllare si controlla PRIMA di
# fermare qualcosa; se dopo lo stop un passo va storto si TORNA A ROOT
# da soli, e il mercatino riparte com'era.
#
#     bash deploy/utente/cambio-utente.sh            GUARDA e basta: la
#                                                    fotografia e i controlli,
#                                                    non tocca niente
#     bash deploy/utente/cambio-utente.sh --fai      fa il cambio
#     bash deploy/utente/cambio-utente.sh --torna    torna a root
#
# COSA FA --fai, in ordine:
#   prima dello stop  l'utente `barattolo` (di sistema, senza shell),
#                     la regola di sudoers (provata con visudo PRIMA di
#                     posarla), le librerie viste da lui, una copia del
#                     database, i timer di deploy e backup fermati;
#   a sito fermo      /root/satmarket si sposta in /srv/barattolo (in
#                     /root un utente qualunque non entra) e al suo
#                     posto resta un COLLEGAMENTO, cosi' ogni comando di
#                     PRODUZIONE e le unit di deploy e backup valgono
#                     uguali; il database va in dati/ (sqlite scrive il
#                     journal ACCANTO al file: la sua cartella dev'essere
#                     scrivibile dal servizio, quella del CODICE mai) e
#                     anche li' resta il collegamento; i permessi; il
#                     drop-in di systemd; una SCRITTURA di prova sul
#                     database fatta da `barattolo`, e annullata;
#   poi               start, /api/salute, e si guarda CHI gira davvero.
#
# LA REGOLA CHE TIENE INSIEME I PERMESSI: `barattolo` non puo' scrivere
# in NESSUN posto da cui root esegue. Il deploy gira da root DENTRO
# questa cartella (git, python, `from config import …`): se il servizio
# potesse scriverci, chi buca il servizio diventa root al deploy dopo.
# Quindi codice, .git e config.py sono di root; suoi sono soltanto
# dati/, foto/, buste/, contenuti/ e import_tmp/.
#
# I nomi si possono cambiare dall'ambiente SOLO per il banco di prova
# (CAMBIO_*): sul VPS si lancia nudo.

set -uo pipefail

VECCHIA="${CAMBIO_VECCHIA:-/root/satmarket}"
NUOVA="${CAMBIO_NUOVA:-/srv/barattolo}"
UTENTE="${CAMBIO_UTENTE:-barattolo}"
SERVIZIO="${CAMBIO_SERVIZIO:-barattolo}"
SALUTE="${CAMBIO_SALUTE:-http://127.0.0.1:8080/api/salute}"
ETC_SYSTEMD="${CAMBIO_ETC_SYSTEMD:-/etc/systemd/system}"
SUDOERS="${CAMBIO_SUDOERS:-/etc/sudoers.d/barattolo-ponte}"
TIMER="${CAMBIO_TIMER-barattolo-deploy.timer barattolo-backup.timer}"
CERT_LND="${CAMBIO_CERT_LND:-/opt/lnbits/data/tls.cert}"
DROPIN="$ETC_SYSTEMD/$SERVIZIO.service.d/utente.conf"
SUE="dati foto buste contenuti import_tmp"   # le sole cartelle del servizio
LIBRERIE="uvicorn fastapi httpx PIL pillow_heif coincurve cryptography websocket snowballstemmer"

dillo()  { echo "$*"; }
guasto() { echo "❌ $*" >&2; }
avviso() { echo "⚠️ $*"; }     # non ferma niente, e sta in FILA con le altre righe

main() {
  local gesto="${1:-}"
  [[ "$(id -u)" == "0" ]] || { guasto "va lanciato da root"; exit 1; }
  case "$gesto" in
    "")       guarda; exit $? ;;
    --fai)    fai ;;
    --torna)  torna; exit $? ;;
    *)        guasto "non conosco «$gesto»: nudo, --fai o --torna"; exit 2 ;;
  esac
}

# dove sta il codice ADESSO: dopo il trasloco VECCHIA e' un collegamento
cartella() { if [[ -L "$VECCHIA" || ! -e "$VECCHIA" ]]; then echo "$NUOVA"; else echo "$VECCHIA"; fi; }

# la riga ExecStart della unit VERA (mai quella di un nostro drop-in)
exec_di_prima() {
  local unit; unit="$(systemctl show "$SERVIZIO" -p FragmentPath --value 2>/dev/null)"
  [[ -r "$unit" ]] && grep -E '^ExecStart=' "$unit" | tail -1
}

# l'interprete di quella riga: la prima parola dopo `ExecStart=`
interprete() { exec_di_prima | sed -E 's/^ExecStart=[-@!+:]*//' | awk '{print $1}'; }

aspetta_salute() {
  local fine=$((SECONDS + ${1:-60}))
  while ((SECONDS < fine)); do
    curl --fail --silent --max-time 5 "$SALUTE" >/dev/null 2>&1 && return 0
    sleep 2
  done
  return 1
}

# La copia del database con l'API di sqlite DENTRO python, come fa
# deploy.sh, e non col comando `sqlite3`: quello e' un pacchetto a
# parte, e il giorno della prova su una macchina gemella non c'era —
# lo script si sarebbe fermato (prima di toccare niente, ma fermato).
# DAL 20 OTT 2026 (cantiere backup-ritocchi) la fa `deploy/copia-db.py`,
# la stessa di deploy.sh e del giornaliero: qui il server GIRA ancora
# (lo stop viene dopo), e la copia di prima non aveva un tetto ne'
# controllava quel che aveva copiato. Adesso aspetta il lucchetto (30 s,
# tetto 90) e fa `integrity_check`: una copia NON integra vale come una
# copia non riuscita — col database rotto non si trasloca niente, prima
# si guarda lui. Il file resta in backup/, ed e' la prova.
copia_db() {
  local db esito codice=0
  db="$(cd "$1" && python3 -c 'from config import DB; print(DB)' 2>/dev/null)"
  esito="$(cd "$1" && python3 deploy/copia-db.py "${db:-satmarket.db}" "$2")" || codice=$?
  dillo "   la copia: ${esito:-nessuna risposta}"
  return "$codice"
}

# L'UNICO file fuori dalla cartella che il server legge: il certificato
# di LND, per la verita' dei pagamenti (e solo se quella e' accesa).
# Finche' l'utente non esiste non si puo' chiedere A LUI: --fai lo
# richiede dopo averlo creato, prima di fermare qualunque cosa.
cert_leggibile() {
  local qui="$1" cert
  grep -qE '^LND_PONTE_MACAROON_LETTURA' "$qui/config.py" 2>/dev/null || return 0
  cert="$(cd "$qui" && python3 -c 'import config; print(getattr(config, "LND_PONTE_CERT", ""))' 2>/dev/null)"
  cert="${cert:-$CERT_LND}"
  dillo "la verita' dei pagamenti legge: $cert"
  id "$UTENTE" >/dev/null 2>&1 || { dillo "   ($UTENTE non esiste ancora: lo richiedo dopo averlo creato)"; return 0; }
  sudo -u "$UTENTE" test -r "$cert" && return 0
  guasto "ALT: $UTENTE non sa leggere $cert (e' un certificato, cioe' pubblico): o gli si aprono i permessi lungo il percorso, o se ne mette una copia leggibile e la si scrive nel config come LND_PONTE_CERT"
  return 1
}

# ------------------------------------------------------------------
# GUARDA: la fotografia. Non tocca niente, e dice ALT se il cambio
# oggi non si puo' fare. La chiama anche --fai, per prima.
# ------------------------------------------------------------------
guarda() {
  local alt=0 qui py riga
  qui="$(cartella)"
  dillo "== LA FOTOGRAFIA =="
  dillo "cartella del codice:  $qui$([[ -L "$VECCHIA" ]] && echo "   ($VECCHIA e' gia' un collegamento)")"
  dillo "il servizio gira come: «$(systemctl show "$SERVIZIO" -p User --value 2>/dev/null)»  (vuoto = root)"
  riga="$(exec_di_prima)"; dillo "la sua riga:          ${riga:-NON TROVATA}"
  [[ -n "$riga" ]] || { guasto "ALT: non trovo la ExecStart di $SERVIZIO"; alt=1; }
  grep -q -- "--workers" <<<"$riga" && dillo "⚠️ c'e' --workers: i lucchetti dei pagamenti sono per processo (audit), da guardare a parte"

  py="$(interprete)"
  case "$py" in
    "$VECCHIA"/*) dillo "interprete:           $py  (un venv DENTRO la cartella: trasloca con lei)" ;;
    /root/*)      guasto "ALT: l'interprete sta in /root ma FUORI dalla cartella ($py): $UTENTE non ci arriva. Da decidere insieme."; alt=1 ;;
    "")           : ;;
    *)            dillo "interprete:           $py" ;;
  esac

  # le librerie installate con `pip install --user` da root stanno in
  # /root/.local: root le vede, un altro utente no
  if [[ -n "$py" && -x "$py" ]]; then
    local dove; dove="$("$py" -c 'import uvicorn; print(uvicorn.__file__)' 2>/dev/null)"
    dillo "uvicorn viene da:     ${dove:-NON SI IMPORTA}"
    case "$dove" in
      "$VECCHIA"/*) : ;;
      /root/*) guasto "ALT: le librerie stanno sotto /root ($dove): $UTENTE non le vedrebbe. Vanno reinstallate per tutti (o in un venv dentro la cartella) PRIMA del cambio."; alt=1 ;;
    esac
  fi

  [[ -f "$qui/config.py" ]] || { guasto "ALT: in $qui non c'e' config.py"; alt=1; }
  local db; db="$(cd "$qui" && python3 -c 'from config import DB; print(DB)' 2>/dev/null)"
  dillo "il database (config): ${db:-?}"
  if [[ "$db" != "satmarket.db" ]]; then
    guasto "ALT: mi aspettavo DB = \"satmarket.db\" e trovo «$db»: il trasloco del database va deciso a mano."; alt=1
  fi
  [[ -e "$qui/satmarket.db-wal" ]] && { guasto "ALT: c'e' un -wal: il database non e' nel modo che conosco"; alt=1; }

  if [[ "$(stat -c %d "$(dirname "$VECCHIA")")" != "$(stat -c %d "$(dirname "$NUOVA")")" ]]; then
    dillo "⚠️ $(dirname "$VECCHIA") e $(dirname "$NUOVA") stanno su dischi diversi: lo spostamento COPIA ($(du -sh "$qui" 2>/dev/null | cut -f1)), e il sito resta giu' per quel tempo"
  else
    dillo "stesso disco:         si' (lo spostamento e' un istante)"
  fi
  [[ -e "$NUOVA" && ! -L "$VECCHIA" ]] && { guasto "ALT: $NUOVA esiste gia' e $VECCHIA non e' un collegamento: non so quale sia quella vera"; alt=1; }

  [[ "$(readlink -f "$(command -v systemctl)")" == "/usr/bin/systemctl" ]] \
    || { guasto "ALT: systemctl non sta in /usr/bin ($(command -v systemctl)): la regola di sudoers e il guardiano nominano quel percorso"; alt=1; }
  command -v sudo >/dev/null && command -v visudo >/dev/null \
    || { guasto "ALT: manca sudo (apt install sudo)"; alt=1; }

  if [[ -r /etc/caddy/Caddyfile ]] && grep -nE "^\s*(root|file_server)\b" /etc/caddy/Caddyfile | grep -q .; then
    dillo "⚠️ Caddy serve dei file da disco: guarda che non sia la cartella del mercatino —"
    grep -nE "^\s*(root|file_server)\b" /etc/caddy/Caddyfile | sed 's/^/     /'
  fi

  dillo "chi altro nomina $VECCHIA (da root continuano a valere, via collegamento):"
  grep -rlF "$VECCHIA" "$ETC_SYSTEMD" /etc/cron.d /etc/crontab /var/spool/cron 2>/dev/null | sed 's/^/     /'

  cert_leggibile "$qui" || alt=1

  if ((alt)); then guasto "oggi il cambio NON si fa: risolvi gli ALT qui sopra (o incollali a Claude)"; return 1; fi
  dillo "== nessun ALT: il cambio si puo' fare =="
  return 0
}

# ------------------------------------------------------------------
# TORNA: a root. Vale da qualunque punto ci si sia fermati, perche'
# quel che `barattolo` sa leggere root lo sa leggere uguale: bastano i
# due collegamenti al loro posto e il drop-in via.
# ------------------------------------------------------------------
torna() {
  local qui
  if [[ ! -e "$VECCHIA" && -d "$NUOVA" ]]; then ln -s "$NUOVA" "$VECCHIA"; fi
  qui="$(cartella)"
  if [[ ! -e "$qui/satmarket.db" && -f "$qui/dati/satmarket.db" ]]; then
    ln -s dati/satmarket.db "$qui/satmarket.db"
  fi
  rm -f "$DROPIN"
  rmdir "$(dirname "$DROPIN")" 2>/dev/null || true
  systemctl daemon-reload
  systemctl restart "$SERVIZIO"
  # shellcheck disable=SC2086
  [[ -n "$TIMER" ]] && systemctl start $TIMER 2>/dev/null
  if aspetta_salute 60; then
    dillo "↩️ tornato a root: il mercatino risponde. (La cartella resta in $NUOVA col collegamento: da root non cambia niente.)"
    return 0
  fi
  guasto "🆘 nemmeno da root risponde: journalctl -u $SERVIZIO -n 50"
  return 1
}

fallito() {
  guasto "$1 — TORNO A ROOT"
  torna
  exit 1
}

# ------------------------------------------------------------------
# FAI
# ------------------------------------------------------------------
fai() {
  local qui py giu_da lib manca="" pid chi
  guarda || exit 1
  qui="$(cartella)"
  py="$(interprete)"

  dillo; dillo "== PRIMA DELLO STOP (il sito e' ancora su) =="
  if ! id "$UTENTE" >/dev/null 2>&1; then
    useradd --system --user-group --home-dir "$NUOVA" --no-create-home \
            --shell /usr/sbin/nologin "$UTENTE" \
      || { guasto "useradd non riuscito: non ho toccato altro"; exit 1; }
    dillo "👤 creato l'utente $UTENTE (di sistema, senza shell, senza password)"
  fi
  cert_leggibile "$qui" || { guasto "non ho fermato niente"; exit 1; }

  # la regola si PROVA prima di posarla: un sudoers rotto spegne sudo
  visudo -cf "$qui/deploy/utente/sudoers-barattolo-ponte" >/dev/null \
    || { guasto "la regola di sudoers non passa visudo: non ho toccato altro"; exit 1; }
  install -m 440 -o root -g root "$qui/deploy/utente/sudoers-barattolo-ponte" "$SUDOERS" \
    && visudo -c >/dev/null \
    || { rm -f "$SUDOERS"; guasto "sudoers non si e' lasciato posare: tolto, non ho toccato altro"; exit 1; }
  dillo "🔑 regola di sudoers posata: $SUDOERS"

  # le librerie viste da lui — solo se l'interprete e' raggiungibile
  # GIA' adesso (quello di sistema). Un venv dentro la cartella si prova
  # dopo il trasloco, a sito fermo, col ritorno a root pronto.
  if [[ "$py" != "$VECCHIA"/* ]]; then
    for lib in $LIBRERIE; do
      if "$py" -c "import $lib" 2>/dev/null \
         && ! (cd / && sudo -u "$UTENTE" "$py" -c "import $lib" 2>/dev/null); then
        manca="$manca $lib"
      fi
    done
    [[ -z "$manca" ]] || { guasto "root importa$manca e $UTENTE no: non ho fermato niente"; exit 1; }
    dillo "📚 le librerie che vede root le vede anche $UTENTE"
  fi

  # shellcheck disable=SC2086
  [[ -n "$TIMER" ]] && systemctl stop $TIMER 2>/dev/null
  while systemctl is-active --quiet barattolo-deploy.service 2>/dev/null; do sleep 2; done
  mkdir -p "$qui/backup" && chmod 700 "$qui/backup"
  copia_db "$qui" "$qui/backup/pre-cambio-utente-$(date +%Y%m%d-%H%M%S).db" \
    || { guasto "la copia del database non e' riuscita o non e' integra: non ho fermato niente"; systemctl start $TIMER 2>/dev/null; exit 1; }
  dillo "💾 copia del database in backup/"

  dillo; dillo "== STOP: da qui il sito e' giu' =="
  giu_da=$SECONDS
  trap 'fallito "interrotto a meta'"'"'"' INT TERM
  systemctl stop "$SERVIZIO" || fallito "lo stop non e' riuscito"

  if [[ ! -L "$VECCHIA" ]]; then
    mv "$VECCHIA" "$NUOVA"   || fallito "lo spostamento non e' riuscito"
    ln -s "$NUOVA" "$VECCHIA" || fallito "il collegamento non e' nato"
  fi
  cd "$NUOVA" || fallito "non entro in $NUOVA"

  if [[ ! -L satmarket.db ]]; then
    mkdir -p dati
    mv satmarket.db dati/ || fallito "il database non si e' spostato"
    # un journal rimasto li' e' una transazione da finire: va CON lui
    [[ -e satmarket.db-journal ]] && mv satmarket.db-journal dati/
    ln -s dati/satmarket.db satmarket.db || fallito "il collegamento del database non e' nato"
  fi

  mkdir -p $SUE backup
  chown root:"$UTENTE" . config.py      || fallito "chown"
  chmod 750 .                           || fallito "chmod"
  chmod 640 config.py
  chmod 700 .git backup
  chown -R "$UTENTE":"$UTENTE" $SUE     || fallito "chown delle cartelle del servizio"
  chmod 700 dati buste contenuti import_tmp
  chmod 750 foto
  chmod 600 dati/satmarket.db

  mkdir -p "$(dirname "$DROPIN")"
  {
    cat deploy/utente/barattolo-utente.conf
    echo "Environment=HOME=$NUOVA"
    if exec_di_prima | grep -qF "$VECCHIA"; then
      echo "; la riga di prima nominava $VECCHIA, dove $UTENTE non entra:"
      echo "ExecStart="
      exec_di_prima | sed "s|$VECCHIA|$NUOVA|g"
    fi
  } | sed "s|^User=.*|User=$UTENTE|; s|^Group=.*|Group=$UTENTE|; s|^WorkingDirectory=.*|WorkingDirectory=$NUOVA|" > "$DROPIN" \
    || fallito "il drop-in non si e' scritto"
  systemctl daemon-reload

  py="${py/#$VECCHIA/$NUOVA}"
  for lib in $LIBRERIE; do
    if "$py" -c "import $lib" 2>/dev/null \
       && ! sudo -u "$UTENTE" "$py" -c "import $lib" 2>/dev/null; then
      fallito "root importa $lib e $UTENTE no"
    fi
  done
  # LA SCRITTURA DI PROVA: /api/salute LEGGE soltanto, e una lettura
  # riesce anche dove il journal non puo' nascere. Si apre una
  # transazione vera, si scrive, e si annulla.
  sudo -u "$UTENTE" "$py" - <<'PY' || fallito "$UTENTE non riesce a SCRIVERE sul database"
import sqlite3
from config import DB
con = sqlite3.connect(DB, timeout=10)
con.execute("BEGIN IMMEDIATE")
con.execute("CREATE TABLE _prova_cambio_utente (x)")
con.rollback()
con.close()
PY
  sudo -u "$UTENTE" test ! -w server.py -a ! -w config.py -a ! -w . \
    || fallito "$UTENTE puo' scrivere sul codice o sul config"

  systemctl start "$SERVIZIO" || fallito "lo start non e' riuscito"
  aspetta_salute 60 || fallito "/api/salute non risponde"
  trap - INT TERM
  dillo "== il sito e' tornato su: giu' per $((SECONDS - giu_da)) secondi =="

  pid="$(systemctl show "$SERVIZIO" -p MainPID --value)"
  chi="$(ps -o user= -p "$pid" 2>/dev/null | tr -d ' ')"
  [[ "$chi" == "$UTENTE" ]] || fallito "il processo gira come «$chi», non come $UTENTE"
  dillo "👤 il processo $pid gira come $chi"

  # il guardiano: i quattro riavvii si', tutto il resto no. `sudo -l
  # <comando>` CHIEDE se e' permesso, non lo esegue.
  # UNA riga sola dice com'e' andata, e il «si'» esce solo se e' vero
  # per tutt'e quattro: al banco da root una mancava, e sotto l'avviso
  # usciva lo stesso «i quattro riavvii si'» — due righe che si
  # smentiscono, e chi legge in fretta crede alla seconda.
  local u senza_mani=0
  for u in tor lnd-ponte.service lnd-ponte-tor.service wg-quick@wg0.service; do
    if ! sudo -u "$UTENTE" sudo -n -l /usr/bin/systemctl restart "$u" >/dev/null 2>&1; then
      avviso "$UTENTE NON puo' riavviare $u: il guardiano resterebbe senza mani"
      senza_mani=1
    fi
  done
  if sudo -u "$UTENTE" sudo -n -l /usr/bin/systemctl restart "$SERVIZIO" >/dev/null 2>&1 \
     || sudo -u "$UTENTE" sudo -n -l /usr/bin/systemctl stop tor >/dev/null 2>&1; then
    avviso "la regola di sudoers e' PIU' LARGA del dovuto"
    senza_mani=1
  fi
  if ((senza_mani)); then
    avviso "il cambio e' FATTO e il sito gira, ma sudo non e' come dev'essere: guarda «sudo -l -U $UTENTE» e rimetti deploy/utente/sudoers-barattolo-ponte"
  else
    dillo "🔑 sudo: i quattro riavvii del guardiano si', il resto no"
  fi

  # shellcheck disable=SC2086
  [[ -n "$TIMER" ]] && systemctl start $TIMER 2>/dev/null
  dillo; dillo "✅ FATTO. Per tornare a root: bash $VECCHIA/deploy/utente/cambio-utente.sh --torna"
}

main "$@"
