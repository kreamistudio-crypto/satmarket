#!/bin/bash
# chiavetta-prepara.sh — riempie la CHIAVETTA per i portatili di Alan
# (hackathon di Torino, 17-18 ott 2026): tutto quel che install-offline.sh
# installa poi SENZA rete. Si lancia CON la rete, su un Linux a base
# Ubuntu 22.04 (lo Zorin il 15 ott, o un container jammy): i moduli
# nativi del wallet si COMPILANO qui (node-gyp, build-essential) e la
# chiavetta porta il node_modules gia' compilato, cosi' in sala non serve
# ne' rete ne' compilatore. Compilare su una glibc piu' nuova (il WSL
# 26.04) darebbe binari che su 22.04 non partono: per questo si prepara
# su jammy.
#
# Uso:  bash chiavetta-prepara.sh <cartella della chiavetta> [--senza-qvac] [--senza-modelli] [--modelli-da DIR]
#   --senza-qvac      salta @qvac/sdk e @qvac/cli (sono centinaia di MB)
#   --senza-modelli   non copia i .gguf (1,4 GB) da ~/.qvac/models
#   --modelli-da DIR  dove stanno i .gguf (default ~/.qvac/models)
#
# Cosa serve sulla macchina che prepara: curl, tar, xz, python3, gcc/g++/
# make (build-essential), git non serve. Node NON serve: si usa quello che
# scarica (lo stesso che finisce sulla chiavetta).
#
# Il risultato: <chiavetta>/torino/ con node/ wdk-prova/ qvac-prova/
# modelli/ wheels/ nak/ script/ deb/ e MANIFEST.txt (versioni e sha256).
set -u

NODE22=v22.23.3                      # quello del PC di Andrea (HACKATHON-SETUP §10)
NODE24_LINEA=latest-v24.x            # QVAC vuole Node >= 22.17; `qvac doctor` sul PC ha chiesto il 24
NAK=v0.21.0
RGBLIB_PY=0.3.0b7
WDK="@utexo/wdk-wallet-rgb@2.0.3 nostr-tools@2.25.2 bip39@3.1.0"
WDK_BIN="@utexo/rgb-lib-linux-x64@0.3.0-beta.8"
QVAC="@qvac/sdk@0.21.0 @qvac/cli@0.15.0"
DEB="libatomic1 libvulkan1 vulkan-tools python3-venv"

QUI=$(cd "$(dirname "$0")" && pwd)
K=""; SENZA_QVAC=0; SENZA_MODELLI=0; MODELLI_DA="$HOME/.qvac/models"
while [ $# -gt 0 ]; do
    case "$1" in
        --senza-qvac) SENZA_QVAC=1 ;;
        --senza-modelli) SENZA_MODELLI=1 ;;
        --modelli-da) shift; MODELLI_DA="$1" ;;
        -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
        *) K="$1" ;;
    esac
    shift
done
[ -n "$K" ] || { echo "✗ dove sta la chiavetta? bash chiavetta-prepara.sh /media/<utente>/<chiavetta>" >&2; exit 2; }
T="$K/torino"
FALLITI=0
ok()  { echo "✓ $*"; }
no()  { echo "✗ $*" >&2; FALLITI=$((FALLITI+1)); }
serve() { command -v "$1" >/dev/null 2>&1 || { no "manca $1 ($2)"; return 1; }; }

echo "📦 Preparo la chiavetta in $T"
serve curl "apt install curl" || exit 2
serve tar "apt install tar" || exit 2
serve xz "apt install xz-utils" || exit 2
serve python3 "apt install python3" || exit 2
for c in gcc g++ make; do serve "$c" "apt install build-essential (node-gyp compila il binding del wallet)" || exit 2; done
case "$(uname -m)" in x86_64) ;; *) echo "✗ $(uname -m): i binari qui sono per x86_64" >&2; exit 2 ;; esac
# LA GLIBC DECIDE LA VARIANTE DEL WALLET (letto nei .so il 9 ott 2026):
# il binario Utexo della beta.8 (quello che @utexo/rgb-sdk 1.0.3, e quindi
# wdk-wallet-rgb 2.0.3, pretende) vuole glibc >= 2.38 — su Ubuntu 22.04
# (glibc 2.35) l'import muore con «GLIBC_2.38 not found». La beta.13 si
# ferma a 2.34, e @utexo/rgb-sdk 1.0.6 la pinna: con `overrides` in
# package.json wdk-wallet-rgb 2.0.3 gira sopra la 1.0.6 (PROVATO su jammy
# il 9 ott: import, nuovo, indirizzo e saldo via Esplora). ATTENZIONE: la
# 1.0.6 deriva le chiavi con un altro keychain (vanillaKeychain 0 e non
# 1): un wallet nato con l'una NON e' lo stesso wallet con l'altra. Va
# bene per il wallet di PROVA di Alan, mai per quello della demo, che
# resta sul PC di Andrea con la variante originale.
GLIBC=$(ldd --version 2>/dev/null | head -1 | awk '{print $NF}')
if python3 -c "import sys; sys.exit(0 if tuple(int(x) for x in '${GLIBC:-0}'.split('.')[:2]) >= (2, 38) else 1)"; then
    VARIANTE="originale (rgb-sdk 1.0.3, binario beta.8, glibc >= 2.38)"
    OVERRIDE=""
    ok "glibc $GLIBC: variante originale del wallet, la stessa del PC di Andrea"
elif python3 -c "import sys; sys.exit(0 if tuple(int(x) for x in '${GLIBC:-0}'.split('.')[:2]) >= (2, 34) else 1)"; then
    VARIANTE="override (rgb-sdk 1.0.6, binario beta.13, glibc >= 2.34)"
    OVERRIDE='{"@utexo/rgb-sdk":"1.0.6"}'
    WDK_BIN="@utexo/rgb-lib-linux-x64@0.3.0-beta.13"
    ok "glibc $GLIBC (< 2.38): variante override del wallet (rgb-sdk 1.0.6 + binario beta.13) — solo per il wallet di PROVA"
else
    echo "✗ glibc ${GLIBC:-?}: troppo vecchia anche per la beta.13 (>= 2.34). Su questa macchina non si prepara." >&2; exit 2
fi
mkdir -p "$T"/node "$T"/wdk-prova "$T"/qvac-prova "$T"/modelli "$T"/wheels "$T"/nak "$T"/script "$T"/deb
LAVORO=$(mktemp -d)
trap 'rm -rf "$LAVORO"' EXIT

# ---------------------------------------------------------------- 1) Node
scarica_node() {   # $1 linea (v22.23.3 | latest-v24.x) → stampa il nome del file
    local linea="$1" riga nome sha
    riga=$(curl -fsSL "https://nodejs.org/dist/$linea/SHASUMS256.txt" | grep "linux-x64.tar.xz$") || return 1
    sha=${riga%% *}; nome=${riga##* }
    [ -f "$T/node/$nome" ] || curl -fsSL -o "$T/node/$nome" "https://nodejs.org/dist/$linea/$nome" || return 1
    echo "$sha  $T/node/$nome" | sha256sum -c --quiet >/dev/null || { rm -f "$T/node/$nome"; return 1; }
    echo "$nome"
}
N22=$(scarica_node "$NODE22") && ok "node $N22 (sha256 verificata)" || no "download di Node $NODE22"
N24=$(scarica_node "$NODE24_LINEA") && ok "node $N24 (sha256 verificata)" || no "download di Node 24"
[ -n "${N22:-}" ] || exit 1
mkdir -p "$LAVORO/node22" && tar -xJf "$T/node/$N22" -C "$LAVORO/node22" --strip-components=1
export PATH="$LAVORO/node22/bin:$PATH"
ok "uso $(node -v) / npm $(npm -v) per compilare"

# ---------------------------------------------------------------- 2) il wallet (compilato qui)
# Ogni riga col suo `||`: dentro un `( … ) && ok || no` bash IGNORA set -e,
# e la prima stesura ha detto ✓ sopra un import fallito (9 ott, jammy).
wallet() {
    mkdir -p "$LAVORO/wdk-prova" && cd "$LAVORO/wdk-prova" || return 1
    npm init -y >/dev/null || return 1
    if [ -n "$OVERRIDE" ]; then
        node -e "const p=require('./package.json'); p.overrides=$OVERRIDE; require('fs').writeFileSync('package.json', JSON.stringify(p,null,2)+'\n')" || return 1
    fi
    # shellcheck disable=SC2086
    npm install --no-audit --no-fund $WDK >/dev/null || return 1
    # shellcheck disable=SC2086
    npm install --no-audit --no-fund $WDK_BIN >/dev/null || return 1
    node -e "import('@utexo/wdk-wallet-rgb').then(()=>console.log('modulo RGB ok'))" > "$LAVORO/import.log" 2>&1 \
        && grep -q "modulo RGB ok" "$LAVORO/import.log" || { tail -3 "$LAVORO/import.log" >&2; return 1; }
    tar -czf "$T/wdk-prova/node_modules.tar.gz" node_modules package.json package-lock.json || return 1
    { echo "variante: $VARIANTE"; npm ls --all 2>/dev/null | grep -E "wdk-wallet-rgb|rgb-sdk|rgb-lib|nostr-tools|bip39"; } > "$T/wdk-prova/versioni.txt"
    return 0
}
if wallet; then
    ok "wdk-prova/node_modules.tar.gz ($(du -h "$T/wdk-prova/node_modules.tar.gz" | cut -f1)), $VARIANTE, modulo RGB importato"
else
    rm -f "$T/wdk-prova/node_modules.tar.gz"
    no "il wallet non si installa qui: serve build-essential e python3 per node-gyp (vedi sopra la glibc)"
fi

# ---------------------------------------------------------------- 3) QVAC (con Node 24)
qvac() {
    mkdir -p "$LAVORO/node24" && tar -xJf "$T/node/$N24" -C "$LAVORO/node24" --strip-components=1 || return 1
    export PATH="$LAVORO/node24/bin:$PATH"
    mkdir -p "$LAVORO/qvac-prova" && cd "$LAVORO/qvac-prova" || return 1
    npm init -y >/dev/null || return 1
    # shellcheck disable=SC2086
    npm install --no-audit --no-fund $QVAC >/dev/null || return 1
    npx --no-install qvac --version > "$T/qvac-prova/versione.txt" 2>/dev/null && grep -q . "$T/qvac-prova/versione.txt" || return 1
    tar -czf "$T/qvac-prova/node_modules.tar.gz" node_modules package.json package-lock.json || return 1
    return 0
}
if [ "$SENZA_QVAC" = 1 ]; then
    echo "· QVAC saltato (--senza-qvac)"
elif [ -n "${N24:-}" ]; then
    if (qvac); then
        ok "qvac-prova/node_modules.tar.gz ($(du -h "$T/qvac-prova/node_modules.tar.gz" | cut -f1)), qvac $(tail -1 "$T/qvac-prova/versione.txt")"
    else
        rm -f "$T/qvac-prova/node_modules.tar.gz"
        no "QVAC non si e' installato"
    fi
else
    no "QVAC saltato: manca Node 24"
fi

# ---------------------------------------------------------------- 4) i modelli (copiati, non scaricati)
if [ "$SENZA_MODELLI" = 1 ]; then
    echo "· modelli saltati (--senza-modelli)"
elif ls "$MODELLI_DA"/*.gguf >/dev/null 2>&1; then
    cp "$MODELLI_DA"/*.gguf "$T/modelli/" && ok "modelli: $(ls "$T/modelli" | tr '\n' ' ')"
else
    no "nessun .gguf in $MODELLI_DA: li scarica il primo \`npx qvac serve … --model consigliami --model qwen3-600m-inst-q4\` (HACKATHON-SETUP §10), poi si rilancia; o --senza-modelli"
fi

# ---------------------------------------------------------------- 5) le ruote Python (rgb-lib e pip), da PyPI senza pip
ruota() {   # $1 pacchetto, $2 versione ('' = ultima), $3 filtro sul nome → scarica in wheels/
    local url
    url=$(curl -fsSL "https://pypi.org/pypi/$1/${2:-}${2:+/}json" | python3 -c '
import json, sys
filtro = sys.argv[1]
d = json.load(sys.stdin)
urls = d["urls"] if "urls" in d else []
for u in urls:
    if u["packagetype"] == "bdist_wheel" and filtro in u["filename"]:
        print(u["url"]); break
' "$3") || return 1
    [ -n "$url" ] || return 1
    (cd "$T/wheels" && curl -fsSL -O "$url")
}
ruota rgb-lib "$RGBLIB_PY" "manylinux_2_34_x86_64" && ok "wheels/$(ls "$T/wheels" | grep rgb_lib)" || no "la ruota rgb-lib $RGBLIB_PY per manylinux_2_34_x86_64"
ruota pip "" "py3-none-any" && ok "wheels/$(ls "$T/wheels" | grep '^pip-')" || no "la ruota di pip (serve a installare senza python3-venv)"

# ---------------------------------------------------------------- 6) nak
if [ -f "$T/nak/nak" ] || curl -fsSL -o "$T/nak/nak" "https://github.com/fiatjaf/nak/releases/download/$NAK/nak-$NAK-linux-amd64"; then
    chmod +x "$T/nak/nak" && "$T/nak/nak" --version | grep -q "$NAK" && ok "nak $NAK" || no "nak non parte"
else
    no "download di nak $NAK"
fi

# ---------------------------------------------------------------- 7) gli script di casa
for f in punti.mjs nwc-wdk.mjs identita.mjs consiglio.py qvac.config.json mutinynet-wsl.env install-offline.sh; do
    [ -f "$QUI/$f" ] && cp "$QUI/$f" "$T/script/" || no "manca $QUI/$f"
done
chmod +x "$T/script/install-offline.sh" 2>/dev/null
ok "script/: $(ls "$T/script" | tr '\n' ' ')"

# ---------------------------------------------------------------- 8) i .deb di riserva (jammy): solo se c'e' apt
if command -v apt-get >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    (cd "$T/deb" && apt-get download $DEB >/dev/null 2>&1) && ok "deb/: $(ls "$T/deb" | wc -l) pacchetti jammy di riserva ($DEB)" \
        || echo "· deb/ non riempita (apt-get download ha fallito: non e' grave, sono riserve)"
else
    echo "· deb/ non riempita (niente apt-get qui)"
fi

# ---------------------------------------------------------------- 9) il manifesto
{
    echo "chiavetta per Torino, preparata il $(date -u +%Y-%m-%dT%H:%MZ) su $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-?}") glibc $(ldd --version 2>/dev/null | head -1 | awk '{print $NF}')"
    echo "node: ${N22:-} ${N24:-}"
    echo "wallet: $WDK $WDK_BIN — variante $VARIANTE"
    echo "qvac: $QVAC"
    echo "rgb-lib (python): $RGBLIB_PY"
    echo "nak: $NAK"
    echo
    (cd "$T" && find . -type f ! -name MANIFEST.txt | sort | xargs sha256sum)
} > "$T/MANIFEST.txt"
echo
echo "📦 $T: $(du -sh "$T" | cut -f1), manifesto in MANIFEST.txt"
[ "$FALLITI" = 0 ] && echo "✓ tutto pronto: sul portatile \`bash $T/script/install-offline.sh $T\`" || { echo "✗ $FALLITI voci mancanti (vedi sopra)" >&2; exit 1; }
