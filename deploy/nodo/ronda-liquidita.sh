#!/bin/bash
# ronda-liquidita.sh — il giudice dei CANALI e dell'inbound, ogni giorno.
# Nato il 16 set 2026 col primo lease Magma. Tace se tutto torna;
# --prova parla coi numeri (il drill del tubo); --impara scrive la
# baseline dei canali. Le domande sono DUE e distinte, perche' l'inbound
# scende anche nei giorni buoni (i depositi in cassaforte lo consumano):
#   1) e' sparito o cambiato un canale?  -> baseline in canali_noti
#   2) siamo vicini al muro?             -> inbound ATTIVO sotto SOGLIA_IN
# piu' la scadenza dei lease (lease.txt: «pubkey AAAA-MM-GG nome», una
# riga per canale, # per i commenti) e il thaw_height, che Pool scrive
# e Magma quasi certamente no: se e' 0 non dice niente.
# Vive in /usr/local/bin sul nodo; questa e' la COPIA nel repo
# (deploy/nodo/), con la stessa regola del relay: chi tocca il file di
# la' lo riporta qui nello stesso giro.
set -u
L=nodo-lnd-1
NOTI=/var/lib/ronda/canali_noti
LEASE=/home/debian/nodo/lease.txt
SOGLIA_IN=${SOGLIA_IN:-500000}      # sats: meno di due ordini grossi d'aria
GIORNI_LEASE=${GIORNI_LEASE:-14}    # col giro giornaliero bastano
BLOCCHI_THAW=${BLOCCHI_THAW:-1008}  # ~ una settimana
MODO=${1:-}
mkdir -p "$(dirname "$NOTI")"

# una cartella usa-e-getta SUA (1 ott 2026, B5 del secondo audit): un
# nome fisso in /tmp scritto da root e' un symlink che qualcun altro
# puo' piazzare prima
TMPD=$(mktemp -d /tmp/liq.XXXXXX) || exit 1
trap 'rm -rf "$TMPD"' EXIT
docker exec "$L" lncli listchannels > "$TMPD/ch.json" 2>/dev/null \
  && docker exec "$L" lncli getinfo > "$TMPD/info.json" 2>/dev/null \
  || { T='ALLARME LIQUIDITA: lncli non risponde, canali e inbound non misurati'
       echo "$T"; printf '%s\n--- fine ronda liquidita\n' "$T" | /usr/local/bin/ronda-avvisa.sh
       exit 1; }

OUT=$(NOTI="$NOTI" LEASE="$LEASE" MODO="$MODO" SOGLIA_IN="$SOGLIA_IN" TMPD="$TMPD" \
      GIORNI_LEASE="$GIORNI_LEASE" BLOCCHI_THAW="$BLOCCHI_THAW" python3 - <<'PY'
import json, os, sys, datetime
noti_f=os.environ['NOTI']; lease_f=os.environ['LEASE']; modo=os.environ['MODO']
soglia=int(os.environ['SOGLIA_IN']); giorni=int(os.environ['GIORNI_LEASE'])
blocchi=int(os.environ['BLOCCHI_THAW'])
tmpd=os.environ['TMPD']
ch=json.load(open(tmpd+'/ch.json')).get('channels',[])
altezza=int(json.load(open(tmpd+'/info.json')).get('block_height',0))
def riga(c): return f"{c['channel_point']} {c['capacity']} {c['remote_pubkey']}"

if modo=='--impara':
    with open(noti_f,'w') as f:
        for c in ch: f.write(riga(c)+'\n')
    print(f"baseline: {len(ch)} canali ora noti")
    for c in ch:
        print(f"  {'attivo  ' if c.get('active') else 'INATTIVO'} cap={c['capacity']} "
              f"in={c['remote_balance']} out={c['local_balance']} {c['remote_pubkey'][:16]}")
    sys.exit(0)

a=[]
try: noti={l.split()[0]: l.split() for l in open(noti_f) if l.strip()}
except FileNotFoundError: noti=None
if noti is None:
    a.append("nessuna baseline dei canali: lancia --impara")
else:
    ora={c['channel_point']: c for c in ch}
    for cp,(_,cap,pk) in noti.items():
        c=ora.get(cp)
        if c is None: a.append(f"canale SPARITO: cap {cap} con {pk[:16]}")
        elif not c.get('active'): a.append(f"canale INATTIVO: cap {cap} con {pk[:16]}")
    for cp,c in ora.items():
        if cp not in noti:
            a.append(f"canale NUOVO, non in baseline: cap {c['capacity']} con {c['remote_pubkey'][:16]}")

att=[c for c in ch if c.get('active')]
inb=sum(int(c['remote_balance']) for c in att)
out=sum(int(c['local_balance']) for c in att)
if inb<soglia:
    a.append(f"inbound a {inb} sat (soglia {soglia}): i depositi grossi cominceranno a fallire")

for c in ch:
    th=int(c.get('thaw_height') or 0)
    if th and altezza and th-altezza<blocchi:
        a.append(f"thaw_height fra {th-altezza} blocchi sul canale con {c['remote_pubkey'][:16]}")

oggi=datetime.date.today(); lease=[]
try:
    for l in open(lease_f):
        l=l.strip()
        if not l or l.startswith('#'): continue
        pk,data,*nome=l.split(); nome=' '.join(nome) or pk[:16]
        resta=(datetime.date.fromisoformat(data)-oggi).days
        lease.append((nome,resta))
        if not any(c['remote_pubkey']==pk for c in ch):
            a.append(f"lease «{nome}» SENZA canale aperto")
        elif resta<0:
            a.append(f"lease «{nome}» SCADUTO da {-resta} giorni: il venditore puo' chiudere quando vuole")
        elif resta<=giorni:
            a.append(f"lease «{nome}» scade fra {resta} giorni ({data}): ricomprare ora")
except FileNotFoundError: pass
except Exception as e: a.append(f"lease.txt illeggibile: {e}")

quadro=(f"canali {len(att)}/{len(ch)} attivi  in={inb}  out={out}  "
        f"lease={' '.join(f'{n}:{r}g' for n,r in lease) or 'nessuno'}")
if a:
    print("ALLARME LIQUIDITA\n"+"\n".join("- "+x for x in a)+"\n"+quadro); sys.exit(9)
if modo=='--prova':
    print("PROVA liquidita: "+quadro); sys.exit(8)
print("liquidita ok  "+quadro)
PY
); RC=$?
echo "$OUT"
if [ "$RC" = 9 ] || [ "$RC" = 8 ]; then
  printf '%s\n\nSe un canale nuovo o sparito e voluto:  sudo /usr/local/bin/ronda-liquidita.sh --impara\n--- fine ronda liquidita\n' "$OUT" \
    | /usr/local/bin/ronda-avvisa.sh
fi
exit 0
