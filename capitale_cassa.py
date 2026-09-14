# -*- coding: utf-8 -*-
"""
IL CAPITALE NOSTRO — quanti sats abbiamo messo NOI in cassaforte, cioe'
quelli che non vengono da nessun ordine.

Serve al controllo 23 del libro mastro (il conto di cassa). Senza quella
voce il conto legge il capitale come uno scarto inspiegato, cioe' come
«sats dati per pagati e ancora qui»: un falso positivo garantito, che
renderebbe inutile proprio l'allarme che deve restare raro.

NON SCRIVE NIENTE, ne' qui ne' su LNbits: legge il registro dei pagamenti
e basta. Il database non lo apre affatto, e la chiave che PAGA non la
legge nemmeno.

COME DISTINGUE. Gli incassi che vengono dagli utenti li abbiamo emessi
noi, e portano un memo nostro: «Barattolo escrow #», «Barattolo escrow
set:», «Barattolo asta #», «Barattolo sblocco banner #». Un incasso
SENZA uno di quei memi non puo' venire da un ordine: e' capitale.

⚠️ E DICHIARA IL SUO MEZZO PUNTO CIECO, invece di indovinare: sulle
USCITE il memo non lo scriviamo noi — lo scrive il wallet di chi riceve —
quindi da li' non si puo' capire se un pagamento fosse un payout a un
venditore o un prelievo nostro. Lo script le elenca TUTTE e lascia
riconoscere a una persona i (pochi, o zero) prelievi da sottrarre. La
macchina fa la parte che sa fare e nomina quella che non sa.

⚠️⚠️ E LA STRADA CHE NON SI PRENDE, perche' viene in mente per prima:
«capitale = saldo di oggi meno il movimento del mercatino». E' circolare
— farebbe leggere ZERO al controllo 23 per sempre, murandoci dentro
qualunque buco ci sia adesso. Il capitale si legge dal registro, o non si
legge.

USO:  cd ~/satmarket && python3 capitale_cassa.py
Nessuna dipendenza: solo la libreria standard.
"""
import json
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import config
except ImportError:
    sys.exit("⚠️  Lanciami dalla cartella di Barattolo (cd ~/satmarket).")

URL = config.LNBITS_URL.rstrip("/")
CHIAVE = config.LNBITS_INVOICE_KEY      # quella che LEGGE, mai quella che paga

# I memo che scriviamo NOI sulle fatture in entrata. Se un giorno ne
# nasce un quinto, va aggiunto qui: un memo nostro non riconosciuto
# diventerebbe «capitale», cioe' gonfierebbe il numero in silenzio.
NOSTRI = ("Barattolo escrow #", "Barattolo escrow set:",
          "Barattolo asta #", "Barattolo sblocco banner #")

PAGINA = 100


def quando(p):
    v = p.get("time")
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(v))
    return str(v)[:16]


def tutti_i_pagamenti():
    """Il registro INTERO, pagina per pagina. Si scorre con `offset`
    finche' una pagina torna corta: fermarsi al primo `limit` e' il modo
    in cui, il 14 set 2026, un elenco ordinato in modo crescente ha
    fatto credere che un pagamento non esistesse — tagliava il presente,
    non il passato."""
    tutti, offset = [], 0
    while True:
        req = urllib.request.Request(
            f"{URL}/api/v1/payments?limit={PAGINA}&offset={offset}",
            headers={"X-Api-Key": CHIAVE})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                pagina = json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            sys.exit(f"⚠️  LNbits ha risposto {e.code}: il registro non si "
                     f"e' potuto leggere per intero, e un conto a meta' "
                     f"sarebbe peggio di nessun conto.")
        except Exception as e:
            sys.exit(f"⚠️  Non si e' potuto chiedere a LNbits "
                     f"({type(e).__name__}: {e}).")
        if not isinstance(pagina, list):
            sys.exit("⚠️  Risposta inattesa da LNbits: mi aspettavo un "
                     "elenco di pagamenti.")
        tutti += pagina
        if len(pagina) < PAGINA:
            return tutti
        offset += PAGINA
        if offset > 20000:            # freno: un registro cosi' lungo
            return tutti              # va guardato in un altro modo


def main():
    p = tutti_i_pagamenti()
    print("=" * 68)
    print("  IL CAPITALE NOSTRO — sola lettura")
    print(f"  {len(p)} movimenti nel registro")
    if p:
        date = sorted(quando(x) for x in p)
        print(f"  dal {date[0]} al {date[-1]}")
    print("=" * 68)

    capitale, mercatino, uscite = [], 0, []
    for x in p:
        sats = int(x.get("amount", 0)) // 1000
        memo = (x.get("memo") or "").strip()
        if sats < 0:
            uscite.append((quando(x), sats, memo))
        elif any(memo.startswith(n) for n in NOSTRI):
            mercatino += sats
        else:
            capitale.append((quando(x), sats, memo))

    print("\n[GLI INCASSI CHE NON VENGONO DA UN ORDINE = il capitale]")
    if not capitale:
        print("  nessuno: il wallet non ha mai ricevuto sats da fuori")
    for q, sats, memo in sorted(capitale):
        print(f"  {q}  +{sats:>10}  {memo[:44] or '(senza memo)'}")
    somma = sum(s for _, s, _ in capitale)
    print(f"  {'TOTALE':>16}  +{somma:>10} sats")

    print(f"\n[per confronto] incassi del mercatino riconosciuti: "
          f"{mercatino} sats")

    print(f"\n[LE USCITE — {len(uscite)}: guardale tu, il memo qui lo "
          f"scrive il wallet di chi riceve]")
    print("  Sono quasi tutte payout a venditori e rimborsi. Se fra "
          "queste\n  c'e' un PRELIEVO che hai fatto per te, sottrailo dal "
          "totale.")
    for q, sats, memo in sorted(uscite):
        print(f"  {q}  {sats:>11}  {memo[:44] or '(senza memo)'}")

    print("\n" + "=" * 68)
    print(f"  CAPITALE (prima di togliere eventuali prelievi): {somma} sats")
    print("\n  Per dichiararlo, sul VPS:")
    print(f"    sqlite3 ~/satmarket/satmarket.db \"INSERT OR REPLACE INTO "
          f"impostazioni(chiave,valore) VALUES('capitale_nostro_sats',"
          f"'{somma}');\"")
    print("\n  Poi il controllo 23 del libro mastro smette di dire NO e "
          "dà un\n  saldo atteso confrontabile col saldo vero di LNbits.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
