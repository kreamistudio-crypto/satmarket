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
# --acinq (6 ott 2026) e' la GUARDIA ORARIA: solo la terza domanda, dal
# timer nodo-liquidita-acinq. Gli inoltri spostano l'entrata ACINQ in
# ore, e il giro di ogni giorno la vedeva tardi. Tace se va bene; se e'
# sotto soglia avvisa UNA volta ogni PAUSA_ACINQ_S (il timbro sta in
# TIMBRO_ACINQ, e lo scrive anche la ronda intera quando avvisa lei),
# e quando l'entrata risale il timbro si toglie: il prossimo calo parla
# subito.
# Vive in /usr/local/bin sul nodo; questa e' la COPIA nel repo
# (deploy/nodo/), con la stessa regola del relay: chi tocca il file di
# la' lo riporta qui nello stesso giro.
set -u
L=nodo-lnd-1
NOTI=/var/lib/ronda/canali_noti
LEASE=/home/debian/nodo/lease.txt
# LE LEVE SCRITTE SUL NODO (6 ott 2026): /etc/default/ronda-liquidita,
# righe NOME=numero. Le leggono il timer e anche chi lancia la ronda a
# mano (`sudo ... --prova`): un Environment= nell'unit varrebbe solo
# per il timer, e la prova a mano mentirebbe. NON si fa `source`: la
# ronda gira da root, e un file eseguito da root e' codice; qui passano
# solo i nomi dell'elenco e solo cifre. Una leva gia' nell'ambiente
# vince sul file.
LEVE=/etc/default/ronda-liquidita
if [ -r "$LEVE" ]; then
  while IFS='=' read -r k v; do
    case "$k" in
      SOGLIA_IN|SOGLIA_ACINQ|PEZZO_MAX|USCITA_ACINQ_MIN|PAUSA_ACINQ_S)
        case "$v" in ''|*[!0-9]*) continue;; esac
        [ -z "${!k:-}" ] && export "$k=$v";;
    esac
  done < "$LEVE"
fi
SOGLIA_IN=${SOGLIA_IN:-500000}      # sats: meno di due ordini grossi d'aria
# ACINQ per PREFISSO della pubkey (i 16 caratteri bastano fra i nostri
# peer, e un esadecimale lungo nel repo fa rossa la CI). 300.000 utili
# (6 ott 2026, era 150.000): 150.000 suonava tardi per un ordine P2P da
# 500.000 pagato da Phoenix.
PREFISSO_ACINQ=${PREFISSO_ACINQ:-03864ef025fde8fb}
SOGLIA_ACINQ=${SOGLIA_ACINQ:-300000}
PEZZO_MAX=${PEZZO_MAX:-300000}      # da ACINQ passano pezzi da ~300k, non da ~590k
# LA COPERTURA DELLA CASSAFORTE (6 ott 2026): l'uscita ACINQ e' quella
# che paga i venditori su Phoenix, e il giro su noi stessi la consuma.
# USCITA_ACINQ_MIN e' quanto deve restare dopo il giro (debito della
# Cassaforte nodo verso i venditori + i sats di Alan). Il nodo non la
# puo' leggere — vive su LNbits, sul VPS — quindi la scrive a mano chi
# legge la Cassaforte. VUOTA = nessun importo suggerito: meglio nessun
# numero che un numero che scopre i venditori.
USCITA_ACINQ_MIN=${USCITA_ACINQ_MIN:-}
PAUSA_ACINQ_S=${PAUSA_ACINQ_S:-21600}   # 6 ore, come l'avviso gemello del server
TIMBRO_ACINQ=/var/lib/ronda/acinq_avvisato
TIMBRO_LNCLI=/var/lib/ronda/acinq_lncli_avvisato
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
       echo "$T"
       # la guardia oraria non ripete l'allarme ogni ora: un LND giu'
       # per una notte farebbe dodici messaggi uguali
       if [ "$MODO" = --acinq ] \
          && [ -n "$(find "$TIMBRO_LNCLI" -mmin -$((PAUSA_ACINQ_S / 60)) 2>/dev/null)" ]; then
         exit 1
       fi
       [ "$MODO" = --acinq ] && touch "$TIMBRO_LNCLI"
       printf '%s\n--- fine ronda liquidita\n' "$T" | /usr/local/bin/ronda-avvisa.sh
       exit 1; }
rm -f "$TIMBRO_LNCLI"

OUT=$(NOTI="$NOTI" LEASE="$LEASE" MODO="$MODO" SOGLIA_IN="$SOGLIA_IN" TMPD="$TMPD" \
      GIORNI_LEASE="$GIORNI_LEASE" BLOCCHI_THAW="$BLOCCHI_THAW" \
      PREFISSO_ACINQ="$PREFISSO_ACINQ" SOGLIA_ACINQ="$SOGLIA_ACINQ" PEZZO_MAX="$PEZZO_MAX" \
      USCITA_ACINQ_MIN="$USCITA_ACINQ_MIN" PAUSA_ACINQ_S="$PAUSA_ACINQ_S" \
      TIMBRO_ACINQ="$TIMBRO_ACINQ" \
      python3 - <<'PY'
import json, os, sys, datetime, time
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
oraria = modo=='--acinq'    # la guardia oraria: solo la terza domanda
try: noti={l.split()[0]: l.split() for l in open(noti_f) if l.strip()}
except FileNotFoundError: noti=None
if oraria: pass
elif noti is None:
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
if inb<soglia and not oraria:
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
out_ac=sum(utile_out(c) for c in acinq)
def commissione(x): return max(50, x*3//1000)
# LO SCID, NON IL chan_id (6 ott 2026): su questo LND `listchannels`
# da' in `chan_id` il channel_id di BOLT 2 (32 byte in esadecimale) e lo
# short channel id numerico in `scid`, che e' quello che `payinvoice
# --outgoing_chan_id` vuole. Il primo giro suggerito portava l'esadecimale.
# Un chan_id numerico (gli LND di prima) vale da ripiego; niente dei due
# = niente comando, mai un numero tirato a indovinare.
def scid(c):
    for k in ('scid','chan_id'):
        v=str(c.get(k) or '')
        if v.isdigit(): return v
    return None
# LA COPERTURA (6 ott 2026): il giro piu' la sua commissione escono
# dall'uscita ACINQ, e dopo deve restarne almeno USCITA_ACINQ_MIN.
# Vuota = non si sa quanto deve la Cassaforte, e allora nessun importo.
min_txt=os.environ.get('USCITA_ACINQ_MIN','').strip()
uscita_min=int(min_txt) if min_txt.isdigit() else None
if uscita_min is None: spazio=None
else:
    margine=out_ac-uscita_min
    spazio=max(0, margine*1000//1003//1000*1000)
    while spazio>0 and spazio+commissione(spazio)>margine: spazio-=1000
acinq_basso = in_ac<soglia_ac
if acinq_basso:
    a.append(f"entrata ACINQ a {in_ac} sat utili (soglia {soglia_ac}, {len(acinq)} canali attivi): "
             "Phoenix paga solo da li', e gli acquisti piu' grossi falliscono PRIMA del nostro nodo")
    altri=[c for c in att if not c['remote_pubkey'].startswith(pref)]
    da=max(acinq, key=utile_out, default=None)
    verso=max(altri, key=utile_in, default=None)
    amt=0
    if da and verso:
        amt=min(2*soglia_ac-in_ac, pezzo_max, utile_out(da), utile_in(verso))//1000*1000
    if spazio is not None: amt=min(amt, spazio)
    if uscita_min is None:
        a.append("ribilancio: nessun importo, USCITA_ACINQ_MIN non e' scritta "
                 f"(uscita ACINQ {out_ac}): la ronda non sa quanto deve la Cassaforte. "
                 "Leggila sul VPS (debito verso i venditori + Alan), scrivila in "
                 "/etc/default/ronda-liquidita e rilancia --prova")
    elif spazio<10000:
        a.append(f"ribilancio: no, la copertura non lascia spazio (uscita ACINQ {out_ac}, "
                 f"USCITA_ACINQ_MIN {uscita_min}): un giro o uno swap dal canale ACINQ "
                 "scoprirebbero i venditori. L'entrata torna coi payout; se non basta, "
                 "un canale ACINQ nuovo con sats freschi")
    elif amt>=10000 and scid(da) is None:
        a.append(f"ribilancio: {amt} sat fuori dal canale ACINQ {da['channel_point'][:8]}, "
                 "ma listchannels non da' lo scid numerico (ne' in scid ne' in chan_id): "
                 "il comando non si scrive, si legge lo scid a mano")
    elif amt>=10000:
        fee=commissione(amt)
        a.append(f"ribilancio suggerito: {amt} sat fuori dal canale ACINQ {scid(da)} "
                 f"e dentro da {verso['remote_pubkey'][:16]} (commissione massima {fee}; "
                 f"dopo, l'uscita ACINQ resta sopra USCITA_ACINQ_MIN {uscita_min}: "
                 "se la Cassaforte e' cresciuta, prima si aggiorna la leva), "
                 "un comando alla volta, da ~/nodo:\n"
                 f"  docker compose exec lnd lncli addinvoice --amt {amt} --memo ribilancio-acinq\n"
                 "  docker compose exec lnd lncli --macaroontimeout 300 payinvoice --allow_self_payment "
                 f"--outgoing_chan_id {scid(da)} --last_hop {verso['remote_pubkey']} "
                 f"--fee_limit {fee} <payment_request di sopra>\n"
                 "  poi la ronda dei pagamenti lo vedra' uscire: sudo /usr/local/bin/ronda-nodo.sh "
                 "--impara <prime 8 cifre del r_hash>")
    else:
        a.append("ribilancio: il giro su noi stessi non ha spazio "
                 f"(uscita ACINQ {max((utile_out(c) for c in acinq), default=0)}, "
                 f"entrata altrove {max((utile_in(c) for c in altri), default=0)}): "
                 "uno swap in uscita DAL canale ACINQ, come il 5 ott (STUDIO-LIQUIDITA), "
                 f"al massimo {spazio} per la copertura")

for c in ([] if oraria else ch):
    th=int(c.get('thaw_height') or 0)
    if th and altezza and th-altezza<blocchi:
        a.append(f"thaw_height fra {th-altezza} blocchi sul canale con {c['remote_pubkey'][:16]}")

oggi=datetime.date.today(); lease=[]
try:
    for l in ([] if oraria else open(lease_f)):
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
        f"acinq_out={out_ac}  copertura={uscita_min if uscita_min is not None else 'non scritta'}  "
        f"lease={' '.join(f'{n}:{r}g' for n,r in lease) or 'nessuno'}")
# IL TIMBRO DELLA GUARDIA ORARIA: chi avvisa dell'entrata ACINQ bassa
# lo scrive (anche la ronda intera, cosi' l'ora dopo non ripete), chi la
# trova risalita lo toglie. La ronda intera avvisa comunque: e' il
# quadro del giorno, uno solo.
timbro=os.environ.get('TIMBRO_ACINQ','')
def timbra():
    if timbro:
        with open(timbro,'w') as f: f.write(str(in_ac)+'\n')
if not acinq_basso and timbro:
    try: os.remove(timbro)
    except FileNotFoundError: pass
if oraria:
    if not a:
        print("acinq ok  "+quadro); sys.exit(0)
    try: eta=time.time()-os.path.getmtime(timbro)
    except OSError: eta=None
    if eta is not None and eta<int(os.environ.get('PAUSA_ACINQ_S') or 21600):
        print(f"acinq ancora sotto soglia, gia' avvisato {int(eta//60)} minuti fa  "+quadro)
        sys.exit(0)
    timbra()
    print("ALLARME LIQUIDITA (guardia oraria ACINQ)\n"+"\n".join("- "+x for x in a)+"\n"+quadro)
    sys.exit(9)
if a:
    if acinq_basso: timbra()
    print("ALLARME LIQUIDITA\n"+"\n".join("- "+x for x in a)+"\n"+quadro); sys.exit(9)
if modo=='--prova':
    print("PROVA liquidita: "+quadro); sys.exit(8)
print("liquidita ok  "+quadro)
PY
); RC=$?
echo "$OUT"
if [ "$MODO" = --acinq ] && [ "$RC" = 9 ]; then
  printf "%s\n\nLa guardia oraria non ripete questo avviso prima di %s ore, finche' l'entrata resta bassa.\n--- fine ronda liquidita\n" \
    "$OUT" "$((PAUSA_ACINQ_S / 3600))" | /usr/local/bin/ronda-avvisa.sh
elif [ "$RC" = 9 ] || [ "$RC" = 8 ]; then
  printf '%s\n\nSe un canale nuovo o sparito e voluto:  sudo /usr/local/bin/ronda-liquidita.sh --impara\n--- fine ronda liquidita\n' "$OUT" \
    | /usr/local/bin/ronda-avvisa.sh
fi
exit 0
