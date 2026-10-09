#!/bin/bash
# install-offline.sh — installa sul portatile di Alan (Linux a base Ubuntu
# 22.04: Pop!_OS, ZorinOS) tutto quel che serve a Torino, SENZA RETE, dalla
# chiavetta riempita da chiavetta-prepara.sh. Lo stesso script serve il 15
# (lo Zorin, poi provato col Wi-Fi spento) e il 17 in sala (il Pop!_OS, da
# chiavetta). Non tocca il sistema: tutto sotto $HOME (Node in
# ~/.local/node, wallet in ~/wdk-prova, QVAC in ~/qvac-prova, modelli in
# ~/.qvac/models, nak in ~/bin, rgb-lib in ~/rgb-venv), piu' due righe in
# ~/.bashrc. I .deb di riserva si installano SOLO con --con-deb (sudo).
#
# Uso:  bash install-offline.sh <chiavetta>/torino [--senza-qvac] [--senza-modelli] [--con-deb]
#       bash install-offline.sh --prova <chiavetta>/torino     guarda solo che la chiavetta sia completa
#
# Ogni passo stampa ✓ o ✗ e si va avanti: alla fine il conto, ed esce 1 se
# manca qualcosa. Rilanciabile: quel che c'e' gia' si rifa' uguale.
set -u

T=""; SENZA_QVAC=0; SENZA_MODELLI=0; CON_DEB=0; SOLO_PROVA=0
while [ $# -gt 0 ]; do
    case "$1" in
        --senza-qvac) SENZA_QVAC=1 ;;
        --senza-modelli) SENZA_MODELLI=1 ;;
        --con-deb) CON_DEB=1 ;;
        --prova) SOLO_PROVA=1 ;;
        -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
        *) T="${1%/}" ;;
    esac
    shift
done
[ -n "$T" ] || { echo "✗ dove sta la chiavetta? bash install-offline.sh /media/<utente>/<chiavetta>/torino" >&2; exit 2; }
[ -d "$T" ] || { echo "✗ $T non e' una cartella" >&2; exit 2; }
FALLITI=0
ok() { echo "✓ $*"; }
no() { echo "✗ $*" >&2; FALLITI=$((FALLITI+1)); }

# ---------------------------------------------------------------- la chiavetta e' completa?
N22=$(ls "$T"/node/node-v22*-linux-x64.tar.xz 2>/dev/null | head -1)
N24=$(ls "$T"/node/node-v24*-linux-x64.tar.xz 2>/dev/null | head -1)
RUOTA_RGB=$(ls "$T"/wheels/rgb_lib-*.whl 2>/dev/null | head -1)
RUOTA_PIP=$(ls "$T"/wheels/pip-*.whl 2>/dev/null | head -1)
[ -n "$N22" ] && ok "chiavetta: $(basename "$N22")" || no "chiavetta: manca node/node-v22*-linux-x64.tar.xz"
[ -f "$T/wdk-prova/node_modules.tar.gz" ] && ok "chiavetta: wdk-prova/node_modules.tar.gz" || no "chiavetta: manca wdk-prova/node_modules.tar.gz"
[ -f "$T/nak/nak" ] && ok "chiavetta: nak/nak" || no "chiavetta: manca nak/nak"
[ -n "$RUOTA_RGB" ] && ok "chiavetta: $(basename "$RUOTA_RGB")" || no "chiavetta: manca wheels/rgb_lib-*.whl"
[ -n "$RUOTA_PIP" ] && ok "chiavetta: $(basename "$RUOTA_PIP")" || no "chiavetta: manca wheels/pip-*.whl"
for f in punti.mjs nwc-wdk.mjs identita.mjs consiglio.py qvac.config.json mutinynet-wsl.env; do
    [ -f "$T/script/$f" ] && ok "chiavetta: script/$f" || no "chiavetta: manca script/$f"
done
if [ "$SENZA_QVAC" = 0 ]; then
    [ -n "$N24" ] && ok "chiavetta: $(basename "$N24")" || no "chiavetta: manca node/node-v24*-linux-x64.tar.xz (o --senza-qvac)"
    [ -f "$T/qvac-prova/node_modules.tar.gz" ] && ok "chiavetta: qvac-prova/node_modules.tar.gz" || no "chiavetta: manca qvac-prova/node_modules.tar.gz (o --senza-qvac)"
fi
if [ "$SENZA_MODELLI" = 0 ]; then
    ls "$T"/modelli/*.gguf >/dev/null 2>&1 && ok "chiavetta: modelli/ $(ls "$T"/modelli/*.gguf | wc -l) .gguf" || no "chiavetta: nessun .gguf in modelli/ (o --senza-modelli)"
fi
[ -f "$T/MANIFEST.txt" ] && ok "chiavetta: MANIFEST.txt ($(head -1 "$T/MANIFEST.txt"))" || no "chiavetta: manca MANIFEST.txt"
if [ "$SOLO_PROVA" = 1 ]; then
    [ "$FALLITI" = 0 ] && { echo "✓ la chiavetta e' completa"; exit 0; } || { echo "✗ alla chiavetta mancano $FALLITI voci" >&2; exit 1; }
fi
[ "$FALLITI" = 0 ] || { echo "✗ la chiavetta non e' completa: mi fermo prima di installare" >&2; exit 1; }

# ---------------------------------------------------------------- la macchina
case "$(uname -m)" in x86_64) ok "macchina x86_64" ;; *) no "$(uname -m): i binari della chiavetta sono x86_64"; exit 1 ;; esac
# La glibc: il node_modules della chiavetta e' stato compilato dove si e'
# preparata (chiavetta-prepara.sh sceglie la variante del wallet dalla
# glibc di LA': originale sopra 2.38, override rgb-sdk 1.0.6 + beta.13 sopra
# 2.34). Qui basta che questa macchina non sia PIU' VECCHIA di quella:
# si confronta con la glibc scritta nel manifesto.
GLIBC=$(ldd --version 2>/dev/null | head -1 | awk '{print $NF}')
GLIBC_CHIAVETTA=$(head -1 "$T/MANIFEST.txt" | sed -n 's/.*glibc \([0-9.]*\).*/\1/p')
python3 -c "import sys; a=tuple(int(x) for x in '${GLIBC:-0}'.split('.')[:2]); b=tuple(int(x) for x in '${GLIBC_CHIAVETTA:-2.34}'.split('.')[:2]); sys.exit(0 if a >= max(b, (2, 34)) else 1)" 2>/dev/null \
    && ok "glibc $GLIBC (la chiavetta e' stata preparata su glibc ${GLIBC_CHIAVETTA:-?}; il binario Utexo vuole >= 2.34 o >= 2.38 secondo la variante)" \
    || { no "glibc ${GLIBC:-?}: piu' vecchia della macchina che ha preparato la chiavetta (${GLIBC_CHIAVETTA:-?}) o sotto 2.34: il wallet NON partirebbe, mi fermo"; exit 1; }
grep -m1 "variante:" "$T/wdk-prova/versioni.txt" 2>/dev/null | sed 's/^/· wallet: /'
command -v python3 >/dev/null && ok "python3 $(python3 -V 2>&1 | awk '{print $2}')" || no "manca python3"
command -v xz >/dev/null || no "manca xz (tar -xJ dei Node)"

# ---------------------------------------------------------------- 1) Node 22 e 24, sotto ~/.local/node
mkdir -p "$HOME/.local/node"
metti_node() {   # $1 tarball, $2 nome (22|24)
    rm -rf "$HOME/.local/node/$2" && mkdir -p "$HOME/.local/node/$2" \
        && tar -xJf "$1" -C "$HOME/.local/node/$2" --strip-components=1 \
        && "$HOME/.local/node/$2/bin/node" -v
}
V22=$(metti_node "$N22" 22) && ok "node 22 → ~/.local/node/22 ($V22)" || no "node 22 non si estrae"
if [ "$SENZA_QVAC" = 0 ]; then
    V24=$(metti_node "$N24" 24) && ok "node 24 → ~/.local/node/24 ($V24)" || no "node 24 non si estrae"
fi
# IL BINDING COMPILATO ALTROVE CERCA LA .so A CASA SUA: node-gyp scrive nel
# .node un RUNPATH ASSOLUTO alla cartella dove ha compilato (letto con
# readelf il 9 ott: /tmp/tmp.XXXX/wdk-prova/node_modules/@utexo/…/release/),
# che qui non esiste → «librgblibcffi.so: cannot open shared object file».
# LD_LIBRARY_PATH viene PRIMA del RUNPATH nella ricerca del loader: `node22`
# lo imposta sulla cartella vera della .so, e il modulo si importa.
cat > "$HOME/.local/node/usa.sh" <<'EOF'
# scritto da install-offline.sh (Torino): `node22` per il wallet, `node24` per QVAC
node22() {
  export PATH="$HOME/.local/node/22/bin:$PATH"
  local so d; so=$(find "$HOME/wdk-prova/node_modules" -name librgblibcffi.so 2>/dev/null | head -1)
  [ -n "$so" ] || return 0
  d=$(dirname "$so")
  case ":${LD_LIBRARY_PATH:-}:" in *":$d:"*) ;; *) export LD_LIBRARY_PATH="$d${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;; esac
}
node24() { export PATH="$HOME/.local/node/24/bin:$PATH"; }
EOF
RIGA='source "$HOME/.local/node/usa.sh" && node22   # Torino: Node 22 di default, `node24` per QVAC'
grep -qF '.local/node/usa.sh' "$HOME/.bashrc" 2>/dev/null || echo "$RIGA" >> "$HOME/.bashrc"
RIGA_BIN='export PATH="$HOME/bin:$PATH"   # Torino: nak'
grep -qF 'Torino: nak' "$HOME/.bashrc" 2>/dev/null || echo "$RIGA_BIN" >> "$HOME/.bashrc"
ok "~/.bashrc: node22 di default, node24 a chiamata, ~/bin nel PATH"
export PATH="$HOME/.local/node/22/bin:$HOME/bin:$PATH"
# (LD_LIBRARY_PATH per il wallet lo mette `node22` dopo l'estrazione del node_modules, qui sotto)

# ---------------------------------------------------------------- 2) il wallet: ~/wdk-prova
mkdir -p "$HOME/wdk-prova"
( cd "$HOME/wdk-prova" && rm -rf node_modules && tar -xzf "$T/wdk-prova/node_modules.tar.gz" ) \
    && ok "~/wdk-prova/node_modules dalla chiavetta (gia' compilato su 22.04)" || no "node_modules del wallet non si estrae"
for f in punti.mjs nwc-wdk.mjs identita.mjs; do cp "$T/script/$f" "$HOME/wdk-prova/$f"; done
cp "$T/script/mutinynet-wsl.env" "$HOME/wdk-prova/mutinynet.env"
ok "~/wdk-prova: punti.mjs nwc-wdk.mjs identita.mjs mutinynet.env"
# shellcheck disable=SC1091
source "$HOME/.local/node/usa.sh" && node22
[ -n "${LD_LIBRARY_PATH:-}" ] && ok "LD_LIBRARY_PATH → $(echo "$LD_LIBRARY_PATH" | cut -d: -f1 | sed "s|$HOME|~|")" || no "librgblibcffi.so non trovata sotto ~/wdk-prova/node_modules"
( cd "$HOME/wdk-prova" && node -e "import('@utexo/wdk-wallet-rgb').then(()=>console.log('modulo RGB ok'))" 2>&1 | grep -q "modulo RGB ok" ) \
    && ok "il modulo RGB si importa con $(node -v)" || no "il modulo RGB non si importa (glibc? libatomic1? vedi deb/ e --con-deb)"
( cd "$HOME/wdk-prova" && node -e "import('nostr-tools').then(m=>{if(!m.finalizeEvent)throw 1;console.log('ok')})" 2>&1 | grep -q ok ) \
    && ok "nostr-tools si importa" || no "nostr-tools non si importa"

# ---------------------------------------------------------------- 3) nak
mkdir -p "$HOME/bin" && cp "$T/nak/nak" "$HOME/bin/nak" && chmod +x "$HOME/bin/nak" \
    && "$HOME/bin/nak" --version 2>&1 | grep -q "nak" && ok "~/bin/nak $("$HOME/bin/nak" --version 2>&1 | awk '{print $NF}')" || no "nak non parte"

# ---------------------------------------------------------------- 4) QVAC: ~/qvac-prova e i modelli
if [ "$SENZA_QVAC" = 1 ]; then
    echo "· QVAC saltato (--senza-qvac)"
else
    mkdir -p "$HOME/qvac-prova"
    ( cd "$HOME/qvac-prova" && rm -rf node_modules && tar -xzf "$T/qvac-prova/node_modules.tar.gz" ) \
        && ok "~/qvac-prova/node_modules dalla chiavetta" || no "node_modules di QVAC non si estrae"
    cp "$T/script/qvac.config.json" "$HOME/qvac-prova/" && cp "$T/script/consiglio.py" "$HOME/qvac-prova/"
    ( cd "$HOME/qvac-prova" && PATH="$HOME/.local/node/24/bin:$PATH" npx --no-install qvac --version 2>&1 | grep -q . ) \
        && ok "qvac $(cd "$HOME/qvac-prova" && PATH="$HOME/.local/node/24/bin:$PATH" npx --no-install qvac --version 2>&1 | tail -1) con Node 24" \
        || no "npx qvac --version non risponde (libatomic1? vedi deb/ e --con-deb)"
fi
if [ "$SENZA_MODELLI" = 1 ]; then
    echo "· modelli saltati (--senza-modelli)"
else
    mkdir -p "$HOME/.qvac/models" && cp "$T"/modelli/*.gguf "$HOME/.qvac/models/" \
        && ok "~/.qvac/models: $(ls "$HOME/.qvac/models"/*.gguf | wc -l) .gguf" || no "i modelli non si copiano"
fi

# ---------------------------------------------------------------- 5) Python rgb-lib in ~/rgb-venv (senza python3-venv: --without-pip + la ruota di pip)
rm -rf "$HOME/rgb-venv"
if python3 -m venv --without-pip "$HOME/rgb-venv" 2>/dev/null \
   && "$HOME/rgb-venv/bin/python" "$RUOTA_PIP/pip" install --quiet --no-index --find-links "$T/wheels" pip "rgb-lib==$(basename "$RUOTA_RGB" | sed 's/rgb_lib-\([^-]*\)-.*/\1/')" 2>/dev/null \
   && "$HOME/rgb-venv/bin/python" -c "import rgb_lib" 2>/dev/null; then
    ok "~/rgb-venv: rgb-lib $(basename "$RUOTA_RGB" | sed 's/rgb_lib-\([^-]*\)-.*/\1/') importato"
else
    no "rgb-lib in ~/rgb-venv (python3 c'e'? la ruota e' manylinux_2_34?)"
fi

# ---------------------------------------------------------------- 6) i .deb di riserva, solo a richiesta
if [ "$CON_DEB" = 1 ]; then
    if ls "$T"/deb/*.deb >/dev/null 2>&1; then
        sudo dpkg -i "$T"/deb/*.deb >/dev/null 2>&1 && ok "deb/: installati $(ls "$T"/deb/*.deb | wc -l) pacchetti" || no "dpkg -i dei .deb (dipendenze? sono riserve jammy)"
    else
        echo "· deb/ vuota: niente da installare"
    fi
else
    echo "· .deb di riserva non toccati (--con-deb per installarli con sudo): libatomic1 vulkan-tools libvulkan1 python3-venv"
fi

# ---------------------------------------------------------------- il conto
echo
if [ "$FALLITI" = 0 ]; then
    echo "✓ tutto installato. Apri un terminale NUOVO (o \`source ~/.bashrc\`) e poi la prova col Wi-Fi spento di HACKATHON-SETUP §10."
else
    echo "✗ $FALLITI passi falliti (vedi sopra)" >&2
    exit 1
fi
