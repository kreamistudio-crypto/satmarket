# -*- coding: utf-8 -*-
"""
CENSIMENTO DEI PAYOUT — quali affari risultano CHIUSI da noi mentre il
pagamento, dal lato di LNbits, non e' mai andato a buon fine?

E' la domanda che l'ordine 149 ha fatto nascere (14 set 2026): il
mercatino aveva scritto 'released', dato gli XP e annunciato «✅ Ordine
concluso — 67.672 sats al venditore», mentre il pagamento era fallito
per mancanza di rotta. La causa — il numero HTTP scambiato per l'esito —
e' chiusa; questo script risponde all'altra meta' della domanda: **quel
caso era solo?**

NON SCRIVE NIENTE. Il database si apre in `mode=ro`, quindi anche un
errore di battitura verrebbe rifiutato da SQLite prima di toccare i
dati; verso LNbits si fanno solo un decode e una lettura per hash, mai
la chiamata che paga — la chiave che paga questo script non la legge
nemmeno.

⚠️ NON IMPORTA server.py, ed e' deliberato due volte: quel modulo
all'avvio scrive (migrazioni e backfill) e **registra il webhook
Telegram**, cioe' lo ruberebbe alla produzione. Per questo il lettore
del verdetto qui sotto e' una COPIA di `_esito_lnbits`: una copia
dichiarata costa meno di un import che fa danni.

COSA GUARDA — tutte e quattro le bocche che pagano, perche' il difetto
stava nel tubo comune e non in una di loro:
  1. `ordini` 'released'   + `invoice_venditore`   -> l'incasso del venditore
  2. `ordini` 'refunded'   + `invoice_rimborso`    -> il rimborso al compratore
  3. `rimborsi_asta` 'riscosso' + `invoice_riscossione`
  4. `pagamenti` 'rimborsato'   + `invoice_rimborso`

⚠️ E DICHIARA IL SUO PUNTO CIECO, che e' la parte da non dimenticare:
una riga con la colonna della invoice VUOTA e' stata pagata dal
Lightning address, e quella fattura la coniavamo al volo senza salvarla
da nessuna parte. Di quelle righe **non si puo' sapere niente da qui**:
lo script le conta e lo dice, invece di far finta che il censimento sia
completo. (Dal set 2026 non succede piu': `payout_hash` si scrive
sempre.)

I VERDETTI:
  SALDATO       -> c'e' la preimage: i sats sono arrivati. Tutto a posto.
  NON PAGATO    -> LNbits dice 'failed'. E' il caso 149: da recuperare.
  IN VOLO       -> ancora in corso. Non si ripaga: si riguarda dopo.
  NESSUNA TRACCIA -> per quell'hash LNbits non ha niente. Da guardare a
                   mano: o il pagamento e' uscito per un'altra strada, o
                   non e' mai partito.
  ILLEGGIBILE   -> la bolt11 in colonna non si decodifica.
  LNBITS MUTO   -> il canale non ha risposto: non e' un verdetto, e si
                   rilancia. Nel dubbio non si dice mai «e' a posto».

USO:  cd ~/satmarket && python3 censimento_payout.py
      cd ~/satmarket && python3 censimento_payout.py > censimento.txt
Nessuna dipendenza: solo la libreria standard.
"""
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import config
except ImportError:
    sys.exit("⚠️  Lanciami dalla cartella di Barattolo (cd ~/satmarket).")

DB = getattr(config, "DB", "satmarket.db")
URL = config.LNBITS_URL.rstrip("/")
CHIAVE = config.LNBITS_INVOICE_KEY      # quella che LEGGE, mai quella che paga

# Una pausa fra una domanda e l'altra: LNbits e' un servizio di terzi e
# un censimento non ha nessuna fretta. E' la stessa buona educazione del
# giro dei pagamenti sospesi, che bussa a un wallet solo per battito.
PAUSA = 0.3


def chiedi(percorso, dati=None):
    """Una domanda a LNbits. Torna (codice, corpo). Il codice 0 vuol
    dire che non si e' potuto chiedere — che NON e' una risposta."""
    corpo = json.dumps(dati).encode() if dati is not None else None
    req = urllib.request.Request(
        URL + percorso, data=corpo,
        method="POST" if dati is not None else "GET",
        headers={"X-Api-Key": CHIAVE, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            testo = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(testo) if testo.strip() else {})
    except urllib.error.HTTPError as e:
        try:
            testo = e.read().decode("utf-8", "replace")
            return e.code, (json.loads(testo) if testo.strip() else {})
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"_errore": f"{type(e).__name__}: {e}"}


def esito_lnbits(dati):
    """COPIA DICHIARATA di `_esito_lnbits` in server.py — vedi la
    docstring in cima al file per il perche' non si importa. Nel dubbio
    dice 'pending', mai 'success': un censimento che sbaglia per
    ottimismo e' peggio di nessun censimento."""
    if dati.get("paid") is True:
        return "success"
    stato = str(dati.get("status") or "").lower()
    if stato in ("success", "failed", "pending"):
        return stato
    if dati.get("pending") is False:
        return "success"
    return "pending"


VERDETTI = {"success": "SALDATO", "failed": "NON PAGATO",
            "pending": "IN VOLO"}


def guarda(bolt11):
    """Dalla bolt11 al verdetto: decode per avere l'hash, poi la
    lettura per hash. Torna (verdetto, hash, sats_chiesti, nota)."""
    codice, dec = chiedi("/api/v1/payments/decode", {"data": bolt11})
    time.sleep(PAUSA)
    if codice in (400, 422):
        return "ILLEGGIBILE", "", 0, "la bolt11 non si decodifica"
    if codice != 200:
        return "LNBITS MUTO", "", 0, f"decode: HTTP {codice}"
    phash = str(dec.get("payment_hash", ""))[:100]
    sats = int(dec.get("amount_msat", 0)) // 1000
    if not phash:
        return "ILLEGGIBILE", "", sats, "il decode non da' il payment_hash"
    codice, p = chiedi("/api/v1/payments/" + phash)
    time.sleep(PAUSA)
    if codice == 404:
        return "NESSUNA TRACCIA", phash, sats, "LNbits non ha questa riga"
    if codice != 200:
        return "LNBITS MUTO", phash, sats, f"lettura: HTTP {codice}"
    return VERDETTI[esito_lnbits(p)], phash, sats, ""


# Le quattro bocche: (etichetta, tabella, dove, colonna invoice,
#                     colonna importo, colonna stato-payout)
BOCCHE = [
    ("incasso del venditore", "ordini", "stato='released'",
     "invoice_venditore", "prezzo_sats", "payout_stato"),
    ("rimborso al compratore", "ordini", "stato='refunded'",
     "invoice_rimborso", "prezzo_sats", "payout_stato"),
    ("rimborso d'asta", "rimborsi_asta", "stato='riscosso'",
     "invoice_riscossione", "importo_sats", "payout_stato"),
    ("rimborso dello sblocco", "pagamenti", "stato='rimborsato'",
     "invoice_rimborso", "importo_sats", "payout_stato"),
]


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    print("=" * 66)
    print("  CENSIMENTO DEI PAYOUT — sola lettura")
    print(f"  database: {DB}")
    print("=" * 66)

    sospetti, ciechi, guardati = [], [], 0
    for nome, tabella, dove, col_inv, col_imp, col_pay in BOCCHE:
        try:
            righe = con.execute(
                f"SELECT id, {col_inv} AS inv, {col_imp} AS importo, "
                f"{col_pay} AS payout, payout_hash, aggiornato "
                f"FROM {tabella} WHERE {dove}").fetchall()
        except sqlite3.OperationalError as e:
            print(f"\n[{nome}] tabella saltata: {e}")
            continue
        con_invoice = [r for r in righe if (r["inv"] or "").strip()]
        senza = len(righe) - len(con_invoice)
        ciechi.append((nome, senza))
        print(f"\n[{nome}] {len(righe)} righe chiuse, "
              f"{len(con_invoice)} con la fattura in colonna")
        for r in con_invoice:
            verdetto, phash, sats, nota = guarda(r["inv"].strip())
            guardati += 1
            quando = time.strftime("%Y-%m-%d %H:%M",
                                   time.localtime(r["aggiornato"] or 0))
            segno = "  " if verdetto == "SALDATO" else "⚠️"
            extra = f" — {nota}" if nota else ""
            # l'importo della fattura accanto a quello della riga: se
            # non combaciano e' un'anomalia sua, indipendente dall'esito
            print(f" {segno} #{r['id']:<6} {quando}  {verdetto:<15} "
                  f"fattura {sats} sats  (riga {r['importo']} sats, "
                  f"payout '{r['payout'] or ''}'){extra}")
            if verdetto != "SALDATO":
                sospetti.append((nome, tabella, r["id"], verdetto, phash,
                                 sats, nota))

    con.close()
    print("\n" + "=" * 66)
    print(f"  {guardati} pagamenti guardati, {len(sospetti)} da guardare "
          f"a mano")
    for nome, tabella, rid, verdetto, phash, sats, nota in sospetti:
        print(f"    {verdetto:<15} {tabella} #{rid} — {nome}, {sats} sats"
              + (f"  [{phash[:20]}]" if phash else ""))
    if not sospetti:
        print("    nessuno: tutti i payout con una fattura in colonna "
              "risultano saldati")
    print("\n  IL PUNTO CIECO — righe pagate dal Lightning address, di "
          "cui\n  da qui non si puo' sapere niente:")
    for nome, quante in ciechi:
        print(f"    {quante:>4}  {nome}")
    print("  (dal set 2026 non se ne creano piu': `payout_hash` si "
          "scrive sempre)")
    print("=" * 66)
    return 1 if sospetti else 0


if __name__ == "__main__":
    sys.exit(main())
