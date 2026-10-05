#!/bin/bash
# ronda-liquidita.sh — il giudice dei CANALI e dell'inbound, ogni giorno.
# Nato il 16 set 2026 col primo lease Magma. Tace se tutto torna;
# --prova parla coi numeri (il drill del tubo); --impara scrive la
# baseline dei canali. Le domande sono DUE e distinte, perche' l'inbound
# scende anche nei giorni buoni (i depositi in cassaforte lo consumano):
#   1) e' sparito o cambiato un canale?  -> baseline in canali_noti
#   2) siamo vicini al muro?             -> inbound ATTIVO sotto SOGLIA_IN
#   3) Phoenix ci puo' pagare?           -> entrata UTILE dei canali ACINQ
#      sotto SOGLIA_ACINQ (5 ott 2026): Phoenix paga SOLO passando da
#      ACINQ, e un acquisto da 56.459 e' fallito con ~29.000 di entrata
#      ACINQ e milioni altrove — prima del nostro nodo, senza una riga
#      di log. Gli inoltri la spostano in ore: l'allarme porta con se'
#      il ribilancio suggerito, coi numeri di quel giorno.
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
# ACINQ per PREFISSO della pubkey (i 16 caratteri bastano fra i nostri
# peer, e un esadecimale lungo nel repo fa rossa la CI). 150.000 utili:
# quasi tre volte l'acquisto fallito il 5 ott, e il ribilancio porta a
# due volte la soglia.
PREFISSO_ACINQ=${PREFISSO_ACINQ:-03864ef025fde8fb}
SOGLIA_ACINQ=${SOGLIA_ACINQ:-150000}
PEZZO_MAX=${PEZZO_MAX:-300000}      # da ACINQ passano pezzi da ~300k, non da ~590k
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
      GIORNI_LEASE="$GIORNI_LEASE" BLOCCHI_THAW="$BLOCCHI_THAW" \
      PREFISSO_ACINQ="$PREFISSO_ACINQ" SOGLIA_ACINQ="$SOGLIA_ACINQ" PEZZO_MAX="$PEZZO_MAX" \
      python3 - <<'PY'
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

# L'ENTRATA DA ACINQ, a parte: quel che hanno LORO meno la riserva che
# devono tenere (remote_constraints), cioe' quel che possono davvero
# mandarci. Il ribilancio e' un giro su noi stessi: si esce dal canale
# ACINQ con piu' uscita e si rientra dal peer non-ACINQ con piu'
# entrata (oggi LNBiG), cosi' l'entrata si sposta su ACINQ.
pref=os.environ['PREFISSO_ACINQ']; soglia_ac=int(os.environ['SOGLIA_ACINQ'])
pezzo_max=int(os.environ['PEZZO_MAX'])
def riserva(c,lato): return int((c.get(lato+'_constraints') or {}).get('chan_reserve_sat') or 0)
def utile_in(c): return max(0, int(c['remote_balance'])-riserva(c,'remote'))
def utile_out(c): return max(0, int(c['local_balance'])-riserva(c,'local'))
acinq=[c for c in att if c['remote_pubkey'].startswith(pref)]
in_ac=sum(utile_in(c) for c in acinq)
if in_ac<soglia_ac:
    a.append(f"entrata ACINQ a {in_ac} sat utili (soglia {soglia_ac}, {len(acinq)} canali attivi): "
             "Phoenix paga solo da li', e gli acquisti piu' grossi falliscono PRIMA del nostro nodo")
    altri=[c for c in att if not c['remote_pubkey'].startswith(pref)]
    da=max(acinq, key=utile_out, default=None)
    verso=max(altri, key=utile_in, default=None)
    amt=0
    if da and verso:
        amt=min(2*soglia_ac-in_ac, pezzo_max, utile_out(da), utile_in(verso))//1000*1000
    if amt>=10000:
        fee=max(50, amt*3//1000)
        a.append(f"ribilancio suggerito: {amt} sat fuori dal canale ACINQ {da['chan_id']} "
                 f"e dentro da {verso['remote_pubkey'][:16]} (commissione massima {fee}), "
                 "un comando alla volta, da ~/nodo:\n"
                 f"  docker compose exec lnd lncli addinvoice --amt {amt} --memo ribilancio-acinq\n"
                 "  docker compose exec lnd lncli --macaroontimeout 300 payinvoice --allow_self_payment "
                 f"--outgoing_chan_id {da['chan_id']} --last_hop {verso['remote_pubkey']} "
                 f"--fee_limit {fee} <payment_request di sopra>\n"
                 "  poi la ronda dei pagamenti lo vedra' uscire: sudo /usr/local/bin/ronda-nodo.sh "
                 "--impara <prime 8 cifre del r_hash>")
    else:
        a.append("ribilancio: il giro su noi stessi non ha spazio "
                 f"(uscita ACINQ {max((utile_out(c) for c in acinq), default=0)}, "
                 f"entrata altrove {max((utile_in(c) for c in altri), default=0)}): "
                 "uno swap in uscita DAL canale ACINQ, come il 5 ott (STUDIO-LIQUIDITA)")

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

quadro=(f"canali {len(att)}/{len(ch)} attivi  in={inb}  out={out}  acinq_in={in_ac}  "
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
