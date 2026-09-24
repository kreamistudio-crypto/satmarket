# -*- coding: utf-8 -*-
"""
GLI INCASSI SENZA RIGA — l'incrocio fra il registro di LNbits e il
database, sulle DUE casseforti.

E' il controllo che il libro mastro NON puo' fare: le sue query vivono
in SQL, e una riga cancellata non esiste piu' — l'unico posto dove un
incasso resta scritto e' LNbits. Nato sul VPS come `orfani.py` non
tracciato (10 ago 2026, una cassaforte sola, `ordini` + `rilanci`) e
portato qui a set 2026 con tre cose in piu': la terza tabella che dal
banner emette fatture in entrata (`pagamenti`), le due casseforti lette
per NOME con le chiavi giuste, e il controllo del posto — un hash noto
al database ma in una cassaforte diversa da quella in cui i sats sono
davvero entrati.

COSA FA. Per ogni cassaforte configurata legge il registro intero di
LNbits e tiene gli incassi RIUSCITI (entrate, esito success). Poi
guarda il database: `ordini`, `rilanci` e `pagamenti` col loro
`payment_hash` e la loro colonna `cassaforte`. Da li' tre elenchi:
  • ORFANI: incassi col NOSTRO memo senza nessuna riga. Sats entrati
    per un ordine che non c'e' piu' — devono essere zero.
  • FUORI POSTO: incassi con una riga, ma la riga dice un'altra
    cassaforte. E' l'errore del doppio wallet che non si annulla —
    pagare dal wallet sbagliato — visto dal lato dell'entrata.
  • NON NOSTRI: incassi senza il nostro memo. Non sono orfani: sono il
    capitale (vedi `capitale_cassa.py`) o roba arrivata da fuori, e li
    guarda una persona.

LE CASSEFORTI SI RISOLVONO PER NOME, il calco di `_chiavi_cassaforte`
in server.py: due nomi letterali ('saas', 'nodo'), un terzo che ALZA
invece di ripiegare, e il nodo che vale «non c'e'» finche' le sue righe
nel config sono vuote o il segnaposto. Con una differenza voluta: qui
la chiave che PAGA non si legge. Sola lettura, ed e' verificabile — la
sentinella in prove.py fallisce se in questo file compare il nome della
chiave admin (e per questo qui non lo si scrive nemmeno).

NON SCRIVE NIENTE, ne' nel database ne' su LNbits. Esce con 1 se trova
orfani o righe fuori posto, cosi' si puo' mettere in un cron che tace
quando tutto torna.

USO:  cd ~/satmarket && python3 orfani.py [percorso/altro.db]
Nessuna dipendenza: solo la libreria standard.
"""
import json
import os
import pathlib
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from typing import NamedTuple

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# I memo che scriviamo NOI sulle fatture in entrata. Vivono QUI e in
# nessun altro posto: capitale_cassa.py li importa da qui. Se ne nasce
# un quinto va aggiunto, o un incasso nostro finirebbe fra i «non
# nostri» di la' e fra il capitale di la' — in silenzio tutt'e due.
NOSTRI = ("Barattolo escrow #", "Barattolo escrow set:",
          "Barattolo asta #", "Barattolo sblocco banner #",
          # il pagamento unico di piu' carrelli (24 set 2026)
          "Barattolo escrow carrello #")

# Le tre tabelle che portano una fattura in ENTRATA col suo hash.
# `rimborsi_asta` e `payout_hash` sono uscite: non c'entrano.
TABELLE = ("ordini", "rilanci", "pagamenti")

CASSAFORTE_SAAS, CASSAFORTE_NODO = "saas", "nodo"
CASSAFORTI = (CASSAFORTE_SAAS, CASSAFORTE_NODO)

PAGINA = 100


class Cassaforte(NamedTuple):
    nome: str
    LNBITS_URL: str
    LNBITS_INVOICE_KEY: str      # quella che LEGGE, mai quella che paga


def _configurata(url: str, chiave: str) -> bool:
    """Le righe ci sono davvero: non vuote, non il segnaposto."""
    return bool(url and str(url).startswith("http") and chiave
                and "INCOLLA_QUI" not in str(chiave)
                and "TUA-ISTANZA" not in str(url))


def chiavi_cassaforte(nome: str, cfg) -> Cassaforte:
    """Le chiavi di lettura della cassaforte `nome`, dal config. Un
    nome sconosciuto ALZA: «leggi da qualche parte» non e' una
    risposta, e nel doppio wallet il posto e' meta' del fatto."""
    if nome == CASSAFORTE_NODO:
        return Cassaforte(nome, getattr(cfg, "LNBITS_NODO_URL", ""),
                          getattr(cfg, "LNBITS_NODO_INVOICE_KEY", ""))
    if nome == CASSAFORTE_SAAS:
        return Cassaforte(nome, getattr(cfg, "LNBITS_URL", ""),
                          getattr(cfg, "LNBITS_INVOICE_KEY", ""))
    raise ValueError(f"cassaforte sconosciuta: {nome!r}")


def casseforti_leggibili(cfg) -> list:
    """Quelle di cui il config ha URL e invoice key. Il SaaS disdetto
    (fase 5) o il nodo non ancora acceso restano fuori, e chi lancia
    lo legge in testa al rapporto."""
    return [cf for cf in (chiavi_cassaforte(n, cfg) for n in CASSAFORTI)
            if _configurata(cf.LNBITS_URL, cf.LNBITS_INVOICE_KEY)]


def esito(p: dict) -> str:
    """Il verdetto che sta dentro la riga di LNbits — il calco di
    `_esito_lnbits` in server.py: nel dubbio 'pending', mai 'success'.
    L'unico caso in cui l'assenza di uno stato vale un successo e'
    l'istanza vecchia che risponde col solo `pending: False`."""
    if p.get("paid") is True:
        return "success"
    stato = str(p.get("status") or "").lower()
    if stato in ("success", "failed", "pending"):
        return stato
    if p.get("pending") is False:
        return "success"
    return "pending"


def quando(p) -> str:
    v = p.get("time")
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(v))
    return str(v)[:16]


def registro(cf: Cassaforte) -> list:
    """Il registro INTERO di una cassaforte, pagina per pagina, finche'
    una pagina torna corta (fermarsi al primo `limit` taglia il
    presente, non il passato: vedi capitale_cassa.py). Un errore a
    meta' ferma tutto: un incrocio su un registro a meta' direbbe
    «orfano» di un incasso che sta nella pagina mai letta."""
    url = cf.LNBITS_URL.rstrip("/")
    tutti, offset = [], 0
    while True:
        req = urllib.request.Request(
            f"{url}/api/v1/payments?limit={PAGINA}&offset={offset}",
            headers={"X-Api-Key": cf.LNBITS_INVOICE_KEY})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                pagina = json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            sys.exit(f"⚠️  [{cf.nome}] LNbits ha risposto {e.code}: il "
                     f"registro non si e' potuto leggere per intero.")
        except Exception as e:
            sys.exit(f"⚠️  [{cf.nome}] Non si e' potuto chiedere a LNbits "
                     f"({type(e).__name__}: {e}).")
        if not isinstance(pagina, list):
            sys.exit(f"⚠️  [{cf.nome}] Risposta inattesa da LNbits: mi "
                     f"aspettavo un elenco di pagamenti.")
        tutti += pagina
        if len(pagina) < PAGINA:
            return tutti
        offset += PAGINA
        if offset > 20000:            # freno: un registro cosi' lungo
            return tutti              # va guardato in un altro modo


def righe_db(con) -> list:
    """Ogni riga di denaro in ENTRATA col suo hash e la sua cassaforte:
    tuple (tabella, id, payment_hash, cassaforte). Le righe senza hash
    (un ordine mai arrivato alla fattura) non contano. Un database
    senza la colonna `cassaforte` e' di prima del doppio wallet: si
    ferma dicendolo, invece di indovinare 'saas' per tutti."""
    righe = []
    for t in TABELLE:
        try:
            cur = con.execute(f"SELECT id, payment_hash, cassaforte FROM {t} "
                              f"WHERE payment_hash IS NOT NULL "
                              f"AND payment_hash <> ''")
        except sqlite3.OperationalError as e:
            sys.exit(f"⚠️  La tabella {t} non ha la forma attesa ({e}): "
                     f"e' un database di prima del doppio wallet? Va "
                     f"avviato il server una volta, che aggiunge le "
                     f"colonne.")
        righe += [(t, r[0], r[1], r[2] or "") for r in cur]
    return righe


def incrocia(incassi: dict, righe: list) -> dict:
    """Il cuore, importabile e provabile. `incassi` e' {nome cassaforte:
    registro grezzo di LNbits}; `righe` viene da `righe_db`. Torna, per
    cassaforte, i numeri e i tre elenchi. Ogni voce degli elenchi
    porta la riga grezza di LNbits, e «fuori posto» anche la riga del
    database che l'ha riconosciuta."""
    dove = {}                       # hash -> [(tabella, id, cassaforte)]
    for t, rid, h, cf in righe:
        dove.setdefault(h, []).append((t, rid, cf))
    rapporto = {}
    for nome, reg in incassi.items():
        entrate = [p for p in reg
                   if int(p.get("amount", 0) or 0) > 0
                   and esito(p) == "success"]
        r = {"movimenti": len(reg), "incassi": len(entrate),
             "riconosciuti": 0, "orfani": [], "fuori_posto": [],
             "non_nostri": []}
        for p in entrate:
            h = str(p.get("payment_hash") or "")
            memo = (p.get("memo") or "").strip()
            nostro = any(memo.startswith(n) for n in NOSTRI)
            if h and h in dove:
                qui = [x for x in dove[h] if x[2] == nome]
                if qui:
                    r["riconosciuti"] += 1
                else:
                    r["fuori_posto"].append((p, dove[h]))
            elif nostro:
                r["orfani"].append(p)
            else:
                r["non_nostri"].append(p)
        rapporto[nome] = r
    return rapporto


def _riga(p, extra=""):
    sats = int(p.get("amount", 0) or 0) // 1000
    memo = (p.get("memo") or "").strip()[:40] or "(senza memo)"
    h = str(p.get("payment_hash") or "")[:16]
    return f"  {quando(p)}  +{sats:>9}  {h}…  {memo}{extra}"


def main(argv) -> int:
    try:
        import config
    except ImportError:
        sys.exit("⚠️  Lanciami dalla cartella di Barattolo (cd ~/satmarket).")
    percorso = argv[1] if len(argv) > 1 else getattr(config, "DB",
                                                     "satmarket.db")
    casseforti = casseforti_leggibili(config)
    if not casseforti:
        sys.exit("⚠️  Nessuna cassaforte leggibile nel config: servono "
                 "LNBITS_URL + LNBITS_INVOICE_KEY (SaaS) e/o "
                 "LNBITS_NODO_URL + LNBITS_NODO_INVOICE_KEY (nodo).")

    if not os.path.isfile(percorso):
        sys.exit(f"⚠️  Database non trovato: {percorso}")
    # In sola lettura, per URI assoluto: un percorso relativo o con
    # caratteri strani dentro un URI e' il modo di aprire un altro file.
    con = sqlite3.connect(pathlib.Path(percorso).resolve().as_uri()
                          + "?mode=ro", uri=True)
    try:
        righe = righe_db(con)
    finally:
        con.close()
    incassi = {cf.nome: registro(cf) for cf in casseforti}
    rapporto = incrocia(incassi, righe)

    print("=" * 68)
    print("  GLI INCASSI SENZA RIGA — sola lettura, due casseforti")
    print(f"  database: {percorso} — {len(righe)} righe con un hash "
          f"({', '.join(TABELLE)})")
    lette = ", ".join(cf.nome for cf in casseforti)
    mute = [n for n in CASSAFORTI if n not in incassi]
    print(f"  casseforti lette: {lette}"
          + (f" — NON configurate: {', '.join(mute)}" if mute else ""))
    if mute:
        fuori = sum(1 for _, _, _, cf in righe if cf in mute)
        print(f"  ⚠️  {fuori} righe del database stanno in una cassaforte "
              f"che qui non si legge: quelle restano non verificate.")
    print("=" * 68)

    guai = 0
    for nome, r in rapporto.items():
        print(f"\n[{nome}] {r['movimenti']} movimenti, {r['incassi']} "
              f"incassi riusciti, {r['riconosciuti']} con la loro riga")
        print(f"  ORFANI (nostro memo, nessuna riga): {len(r['orfani'])}"
              + ("  ← deve essere zero" if r["orfani"] else "  ✓"))
        for p in sorted(r["orfani"], key=quando):
            print(_riga(p))
        print(f"  FUORI POSTO (la riga dice un'altra cassaforte): "
              f"{len(r['fuori_posto'])}"
              + ("  ← deve essere zero" if r["fuori_posto"] else "  ✓"))
        for p, dv in sorted(r["fuori_posto"], key=lambda x: quando(x[0])):
            dice = ", ".join(f"{t} #{i} dice '{cf or '(vuota)'}'"
                             for t, i, cf in dv)
            print(_riga(p, f"  → {dice}"))
        print(f"  NON NOSTRI (senza il nostro memo: capitale o altro, "
              f"guardali tu): {len(r['non_nostri'])}")
        for p in sorted(r["non_nostri"], key=quando):
            print(_riga(p))
        guai += len(r["orfani"]) + len(r["fuori_posto"])

    print("\n" + "=" * 68)
    if guai:
        print(f"  ⚠️  {guai} incassi da guardare. Niente e' stato toccato: "
              f"un libro mastro sbagliato lo guarda una persona.")
        return 1
    print("  ✓ Ogni incasso nostro ha la sua riga, nella sua cassaforte.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
