# -*- coding: utf-8 -*-
"""
IL CAPITALE NOSTRO — quanti sats abbiamo messo NOI in cassaforte, cioe'
quelli che non vengono da nessun ordine. Dal set 2026 su DUE casseforti:
un totale per ciascuna e uno complessivo.

Serve al polso 23 del libro mastro (il conto di cassa, che dal doppio
wallet e' PER CASSAFORTE: un numero solo non combacerebbe con nessun
wallet) e a nient'altro.

⚠️ E QUEL POLSO NON E' UN ALLARME (decisione di Andrea, 15 set 2026):
la cassaforte e' un wallet MISTO — escrow degli ordini e sats suoi — e il
confronto col saldo vero non deve tornare. Un rilevatore che non torna
mai e' peggio di nessun rilevatore: insegna a ignorare la riga. Questo
numero serve a sapere QUANTA PARTE di ogni wallet e' nostra, che e' un
fatto contabile utile per se'; la protezione dei sats di chi scambia sta
altrove, ed e' per ORDINE — hash scritto nella riga, esito chiesto per
hash, ritentativo, avviso ai moderatori.

NON SCRIVE NIENTE, ne' qui ne' su LNbits: legge il registro dei pagamenti
e basta. Il database non lo apre affatto, e la chiave che PAGA non la
legge nemmeno.

LE CASSEFORTI PER NOME, LE CHIAVI, IL REGISTRO E I MEMO VENGONO DA
`orfani.py`: e' lo stesso mestiere — leggere il registro di ogni
cassaforte configurata con la sola invoice key, risolta come fa
`_chiavi_cassaforte` in server.py — e due copie sarebbero due copie da
tenere in pari. I quattro memo nostri vivono la', in un posto solo.

COME DISTINGUE. Gli incassi che vengono dagli utenti li abbiamo emessi
noi, e portano un memo nostro. Un incasso RIUSCITO senza uno di quei memi
non puo' venire da un ordine: e' capitale. Le fatture in entrata mai
pagate non contano (esito letto come fa il server: nel dubbio «pending»,
mai «success»).

⚠️ E DICHIARA IL SUO MEZZO PUNTO CIECO, invece di indovinare: sulle
USCITE il memo non lo scriviamo noi — lo scrive il wallet di chi riceve —
quindi da li' non si puo' capire se un pagamento fosse un payout a un
venditore o un prelievo nostro. Lo script le elenca TUTTE, cassaforte per
cassaforte, e lascia riconoscere a una persona i (pochi, o zero) prelievi
da sottrarre. La macchina fa la parte che sa fare e nomina quella che
non sa.

⚠️⚠️ E LA STRADA CHE NON SI PRENDE, perche' viene in mente per prima:
«capitale = saldo di oggi meno il movimento del mercatino». E' circolare
— farebbe leggere ZERO al polso 23 per sempre, murandoci dentro
qualunque buco ci sia adesso. Il capitale si legge dal registro, o non si
legge.

USO:  cd ~/satmarket && python3 capitale_cassa.py
Nessuna dipendenza: solo la libreria standard (e orfani.py, accanto).
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from orfani import NOSTRI, casseforti_leggibili, esito, quando, registro
except ImportError:
    sys.exit("⚠️  Mi serve orfani.py nella stessa cartella (cd ~/satmarket).")

# La chiave di `impostazioni` in cui il polso 23 legge il capitale di
# ogni cassaforte: una per nome. (`capitale_nostro_sats`, quella di
# prima del doppio wallet, il polso la legge ancora come ripiego per il
# solo SaaS — era l'unico wallet che c'era.)
CHIAVE = {"saas": "capitale_saas_sats", "nodo": "capitale_nodo_sats"}


def conta(movimenti: list) -> dict:
    """Il cuore, importabile e provabile: il registro grezzo di UNA
    cassaforte diviso in capitale (entrate riuscite senza memo nostro),
    mercatino (entrate riuscite col memo nostro, solo la somma) e
    uscite (tutte, da guardare a mano)."""
    capitale, mercatino, uscite = [], 0, []
    for x in movimenti:
        sats = int(x.get("amount", 0) or 0) // 1000
        memo = (x.get("memo") or "").strip()
        if sats < 0:
            uscite.append((quando(x), sats, memo))
        elif sats == 0 or esito(x) != "success":
            continue
        elif any(memo.startswith(n) for n in NOSTRI):
            mercatino += sats
        else:
            capitale.append((quando(x), sats, memo))
    return {"capitale": sorted(capitale),
            "totale": sum(s for _, s, _ in capitale),
            "mercatino": mercatino, "uscite": sorted(uscite)}


def main():
    try:
        import config
    except ImportError:
        sys.exit("⚠️  Lanciami dalla cartella di Barattolo (cd ~/satmarket).")
    casseforti = casseforti_leggibili(config)
    if not casseforti:
        sys.exit("⚠️  Nessuna cassaforte leggibile nel config: servono "
                 "LNBITS_URL + LNBITS_INVOICE_KEY (SaaS) e/o "
                 "LNBITS_NODO_URL + LNBITS_NODO_INVOICE_KEY (nodo).")

    print("=" * 68)
    print("  IL CAPITALE NOSTRO — sola lettura, per cassaforte")
    print(f"  casseforti lette: {', '.join(cf.nome for cf in casseforti)}")
    print("=" * 68)

    conti = {}
    for cf in casseforti:
        p = registro(cf)
        c = conta(p)
        conti[cf.nome] = c
        print(f"\n[{cf.nome}] {len(p)} movimenti nel registro", end="")
        if p:
            date = sorted(quando(x) for x in p)
            print(f", dal {date[0]} al {date[-1]}", end="")
        print()
        print("  GLI INCASSI CHE NON VENGONO DA UN ORDINE = il capitale:")
        if not c["capitale"]:
            print("    nessuno: questo wallet non ha mai ricevuto sats da fuori")
        for q, sats, memo in c["capitale"]:
            print(f"    {q}  +{sats:>10}  {memo[:44] or '(senza memo)'}")
        print(f"    {'TOTALE':>16}  +{c['totale']:>10} sats")
        print(f"  [per confronto] incassi del mercatino riconosciuti: "
              f"{c['mercatino']} sats")
        print(f"  LE USCITE — {len(c['uscite'])}: guardale tu, il memo qui "
              f"lo scrive il wallet di chi riceve. Sono quasi tutte payout "
              f"a venditori e rimborsi;\n  se fra queste c'e' un PRELIEVO "
              f"che hai fatto per te, sottrailo dal totale di QUESTA "
              f"cassaforte.")
        for q, sats, memo in c["uscite"]:
            print(f"    {q}  {sats:>11}  {memo[:44] or '(senza memo)'}")

    print("\n" + "=" * 68)
    for nome, c in conti.items():
        print(f"  CAPITALE {nome:<5} (prima di togliere eventuali prelievi): "
              f"{c['totale']} sats")
    print(f"  CAPITALE COMPLESSIVO: {sum(c['totale'] for c in conti.values())}"
          f" sats")
    print("\n  Per dichiararlo, sul VPS, una riga per cassaforte:")
    for nome, c in conti.items():
        print(f"    sqlite3 ~/satmarket/satmarket.db \"INSERT OR REPLACE INTO "
              f"impostazioni(chiave,valore) VALUES('{CHIAVE[nome]}',"
              f"'{c['totale']}');\"")
    print("\n  Serve al polso 23 del libro mastro, che dal doppio wallet e'"
          "\n  PER CASSAFORTE e resta un POLSO, non un allarme: su un wallet"
          "\n  misto quel confronto non deve tornare, e non e' da li' che si"
          "\n  sorvegliano i pagamenti.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
