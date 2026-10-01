# -*- coding: utf-8 -*-
"""
CENSIMENTO DELLE SCADENZE — quante fatture incollate sono arrivate al
payout VIVE per un pelo, e quante degli ordini APERTI sono gia' morte?

E' la domanda che l'ordine #152 ha fatto nascere (20 set 2026): il
venditore aveva incollato una fattura quando ha spedito, il payout e'
partito alla consegna confermata quattro giorni dopo, e la fattura era
scaduta da quattro. **Era il primo caso, o con gli altri siamo stati
fortunati?**

NON SCRIVE NIENTE E NON PARLA CON NESSUNO. Il database si apre in
`mode=ro`; la rete non si tocca proprio — la nascita e la scadenza di
una bolt11 stanno scritte DENTRO la bolt11, e si leggono qui.

⚠️ NON IMPORTA server.py, come il suo fratello `censimento_payout.py` e
per le stesse due ragioni (all'avvio quel modulo scrive, e registra il
webhook Telegram). Il lettore qui sotto e' una COPIA DICHIARATA di
`leggi_bolt11`.

COSA GUARDA.
  1. GLI ORDINI PAGATI AL VENDITORE ('released'). La colonna
     `invoice_venditore` dice DA DOVE veniva la fattura:
       piena  -> INCOLLATA a mano: se ne legge nascita e scadenza, e si
                 confronta col momento del payout;
       vuota  -> coniata al volo dal LIGHTNING ADDRESS (o dalla strada
                 di un moderatore): nasce nell'istante in cui si paga,
                 quindi non puo' arrivare scaduta. Non la salviamo: di
                 lei si sa solo questo, ed e' abbastanza.
  2. GLI ORDINI APERTI con una fattura incollata in colonna: quelle GIA'
     SCADUTE, o che scadono entro 7 giorni, sono i prossimi #152. Dal
     20 set 2026 il server non le tenta e ne chiede una nuova con le
     parole giuste — ma saperlo PRIMA e' meglio.
  3. Le righe 'confirmed' SENZA fattura e senza address: chi sta
     aspettando che il venditore ci dia un modo per pagarlo.

⚠️ IL PUNTO CIECO, dichiarato: quando un payout FALLISCE la fattura
incollata si TOGLIE dalla colonna (e' bruciata: LNbits non la ripaga).
Quindi i #152 di IERI — fattura scaduta, tentativo fallito, fattura
cancellata — da qui non si vedono come tali: restano `payout_tentativi`
> 0 e `payout_errore`, che questo script elenca in fondo. La bolt11
morta la tiene solo LNbits, nella riga `failed` di quell'hash.

IL MOMENTO DEL PAYOUT e' `payout_ultimo` (l'ora del tentativo, scritta
dal 14 set 2026) e, dove manca, `aggiornato` — che sul ramo riuscito e'
l'ora della chiusura ma che un gesto successivo puo' aver spostato: per
le righe vecchie il margine e' quindi una stima per ECCESSO di
prudenza (il payout vero e' avvenuto prima o in quell'istante).

USO:  cd ~/satmarket && python3 censimento_scadenze.py
Nessuna dipendenza: solo la libreria standard.
"""
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import config
except ImportError:
    sys.exit("⚠️  Lanciami dalla cartella di Barattolo (cd ~/satmarket).")

DB = getattr(config, "DB", "satmarket.db")
ALFABETO = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
GEN = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)


def leggi_bolt11(bolt11):
    """COPIA DICHIARATA di `leggi_bolt11` in server.py: quando nasce e
    quando scade una bolt11, letto dalla bolt11. None = non si legge."""
    s = str(bolt11 or "").strip().lower()
    sep = s.rfind("1")
    if not s.startswith("ln") or sep < 2:
        return None
    hrp, corpo = s[:sep], s[sep + 1:]
    try:
        v = [ALFABETO.index(c) for c in corpo]
    except ValueError:
        return None
    chk = 1
    for x in ([ord(c) >> 5 for c in hrp] + [0]
              + [ord(c) & 31 for c in hrp] + v):
        alto = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ x
        for i, g in enumerate(GEN):
            if (alto >> i) & 1:
                chk ^= g
    if chk != 1:
        return None
    d = v[:-6]
    if len(d) < 7 + 104:
        return None

    def num(gruppi):
        n = 0
        for g in gruppi:
            n = n * 32 + g
        return n

    quando, scadenza, fine, i = num(d[:7]), 3600, len(d) - 104, 7
    while i + 3 <= fine:
        tipo, lung = d[i], d[i + 1] * 32 + d[i + 2]
        if i + 3 + lung > fine:
            break
        if tipo == 6:
            scadenza = num(d[i + 3:i + 3 + lung])
        i += 3 + lung
    return {"quando": quando, "scadenza": scadenza,
            "scade": quando + scadenza}


def data(ts):
    return time.strftime("%d/%m %H:%M", time.localtime(ts)) if ts else "—"


def durata(s):
    segno, s = ("-" if s < 0 else ""), abs(int(s))
    if s < 5400:
        return f"{segno}{s // 60}m"
    if s < 2 * 86400:
        return f"{segno}{s // 3600}h"
    return f"{segno}{s // 86400}g"


def main():
    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    colonne = {r[1] for r in con.execute("PRAGMA table_info(ordini)")}
    ultimo = "payout_ultimo" if "payout_ultimo" in colonne else "0"
    extra = (", payout_tentativi, payout_errore"
             if "payout_errore" in colonne else
             ", 0 AS payout_tentativi, '' AS payout_errore")
    righe = con.execute(
        f"SELECT o.id, o.stato, o.venditore_id, o.invoice_venditore, "
        f"o.aggiornato, {ultimo} AS ultimo, o.payout_stato, "
        f"COALESCE(u.ln_address,'') AS ln_address, "
        f"COALESCE(u.nome,'') AS nome{extra} "
        f"FROM ordini o LEFT JOIN utenti u ON u.tg_id=o.venditore_id "
        f"ORDER BY o.id").fetchall()
    con.close()
    adesso = int(time.time())

    print("=" * 66)
    print("  1. ORDINI PAGATI AL VENDITORE: da dove veniva la fattura")
    print("=" * 66)
    incollate, address, illeggibili, strette = [], 0, 0, []
    for r in righe:
        if r["stato"] != "released":
            continue
        if not r["invoice_venditore"]:
            address += 1
            continue
        b = leggi_bolt11(r["invoice_venditore"])
        if b is None:
            illeggibili += 1
            continue
        pagata = r["ultimo"] or r["aggiornato"] or 0
        margine = b["scade"] - pagata
        incollate.append((r["id"], r["nome"], b, pagata, margine))
    print(f"  pagati in tutto: {address + len(incollate) + illeggibili}")
    print(f"  · dal Lightning address (fattura coniata all'istante, non "
          f"puo' arrivare scaduta): {address}")
    print(f"  · da una fattura INCOLLATA: {len(incollate)}"
          + (f" (+{illeggibili} che non si leggono)" if illeggibili else ""))
    if incollate:
        print(f"\n  {'ordine':>7}  {'venditore':<14} {'nata':<12} "
              f"{'durata':>7} {'pagata':<12} {'eta al payout':>13} "
              f"{'margine':>8}")
        for oid, nome, b, pagata, margine in incollate:
            spia = ("  ⚠️ MORTA" if margine < 0 else
                    "  ⚠️ per un pelo" if margine < 86400 else "")
            if margine < 86400:
                strette.append(oid)
            print(f"  {'#' + str(oid):>7}  {nome[:14]:<14} "
                  f"{data(b['quando']):<12} {durata(b['scadenza']):>7} "
                  f"{data(pagata):<12} {durata(pagata - b['quando']):>13} "
                  f"{durata(margine):>8}{spia}")
        print(f"\n  → con meno di UN GIORNO di margine (o gia' morte al "
              f"payout): {len(strette)} su {len(incollate)}"
              + (f" — ordini {strette}" if strette else ""))
        print("    («MORTA» su un ordine pagato vuol dire che `aggiornato` "
              "si e' mosso dopo il payout: e' la stima prudente di cui "
              "parla la testata, non un pagamento impossibile.)")

    print("\n" + "=" * 66)
    print("  2. ORDINI APERTI con una fattura incollata: i prossimi #152?")
    print("=" * 66)
    aperti = 0
    for r in righe:
        if r["stato"] not in ("locked", "shipped", "delivered", "confirmed",
                              "dispute") or not r["invoice_venditore"]:
            continue
        aperti += 1
        b = leggi_bolt11(r["invoice_venditore"])
        if b is None:
            print(f"  #{r['id']} ({r['stato']}): fattura che non si legge")
            continue
        vita = b["scade"] - adesso
        spia = ("⚠️ GIA' SCADUTA" if vita <= 0 else
                "⚠️ scade entro 7 giorni" if vita < 7 * 86400 else "ok")
        print(f"  #{r['id']} ({r['stato']}) {r['nome'][:14]:<14} nata "
              f"{data(b['quando'])}, durata {durata(b['scadenza'])}, "
              f"le restano {durata(vita)} — {spia}"
              + (" (ma ha un Lightning address: si paga da li')"
                 if r["ln_address"] and vita <= 0 else ""))
    if not aperti:
        print("  nessuno.")

    print("\n" + "=" * 66)
    print("  3. 'confirmed' SENZA un modo per pagare: chi stiamo aspettando")
    print("=" * 66)
    fermi = [r for r in righe if r["stato"] == "confirmed"
             and not r["invoice_venditore"] and not r["ln_address"]]
    for r in fermi:
        print(f"  #{r['id']} {r['nome'][:14]:<14} fermo dal "
              f"{data(r['aggiornato'])}, tentativi {r['payout_tentativi']}"
              + (f", ultimo errore: {r['payout_errore']}"
                 if r["payout_errore"] else ""))
    if not fermi:
        print("  nessuno.")

    print("\n" + "=" * 66)
    print("  4. Righe con un tentativo FALLITO alle spalle (il punto cieco)")
    print("=" * 66)
    falliti = [r for r in righe if (r["payout_tentativi"] or 0) > 0
               and r["payout_errore"]]
    for r in falliti:
        print(f"  #{r['id']} ({r['stato']}): tentativi "
              f"{r['payout_tentativi']}, «{r['payout_errore']}»")
    if not falliti:
        print("  nessuna.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
