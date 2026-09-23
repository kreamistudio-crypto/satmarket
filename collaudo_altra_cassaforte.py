# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «PAGA DA UN'ALTRA CASSAFORTE» (21 set 2026, ordine #152).

L'incasso di chi vende e' appeso in «pending» sul LNbits ospitato: HTLC
bloccato, fattura scaduta la sera stessa, riga mai aggiornata. Il server
paga sempre dalla cassaforte dell'ordine, e quella del nodo — che
funziona — non poteva pagarlo. Da oggi un moderatore puo' cambiare DA
DOVE si paga, se il pagamento d'origine e' provato morto e chi vende ha
dato una fattura nuova; quel che resta appeso di la' diventa un credito
da recuperare.

`prove.py` fa girare le funzioni estratte in un mondo di cartone. Qui
gira il SERVER VERO — il modulo intero, lo schema di `init_db` (anche su
un database di IERI, che le colonne nuove non le ha), le rotte vere, la
coda vera del pannello, il libro mastro vero — su un database
usa-e-getta. Di finto ci sono SOLO le due LNbits (distinte dall'URL,
come in produzione), LND e l'orologio, che qui si sposta: una scadenza
non si aspetta.

  1. lo schema: nasce da `init_db`, e un database di ieri si migra;
  2. IL #152 PER INTERO: appeso sul SaaS → 🧊 → troppo presto → morto
     ma senza fattura → la si chiede → chi vende la incolla → pagato
     DAL NODO → «Arrivati ✓», la nota, il credito, il libro mastro;
  3. il credito rientra da solo quando il pagamento appeso fallisce;
  4. IL RIFIUTO: origine IN_FLIGHT sul nodo, fattura scaduta da un mese
     → 409, e non parte niente.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_altra_cassaforte.py
"""

import asyncio
import sys
import time as _time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
MINUTI = 60
ALFABETO = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

# le due LNbits, ognuna col suo registro: una riga per payment hash
BANCHE = {"saas": {}, "nodo": {}}
ESITO = {"saas": "pending", "nodo": "success"}
POSTE = []            # (banca, hash) di ogni richiesta di pagamento
LND = {}              # hash → stato, per la sola cassaforte del nodo


def hash_di(bolt11):
    """Il payment hash VERO di una `bolt11_finta`, letto a mano e non
    col lettore del server: il campo `p` e' il primo dopo i 7 gruppi
    dell'ora, 3 di intestazione e poi 52 gruppi da 5 bit."""
    dati = bolt11[bolt11.rfind("1") + 1:]
    bit = "".join(f"{ALFABETO.index(c):05b}" for c in dati[10:62])
    return f"{int(bit[:256], 2):064x}"


def banca_di(url):
    return "nodo" if "nodo.finto" in url else "saas"


class _DueLnbits:
    class AsyncClient:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kw):
            corpo = kw.get("json") or {}
            if "decode" in url:
                return banco._Risposta(200, {
                    "amount_msat": 50_000 * 1000,
                    "payment_hash": hash_di(corpo.get("data", ""))})
            dove = banca_di(url)
            h = hash_di(corpo.get("bolt11", ""))
            if h in BANCHE[dove]:          # l'eco: una riga per hash
                return banco._Risposta(201, {"status": BANCHE[dove][h]})
            POSTE.append((dove, h))
            BANCHE[dove][h] = ESITO[dove]
            return banco._Risposta(201, {"payment_hash": h,
                                         "status": ESITO[dove]})

        async def get(self, url, **kw):
            dove, h = banca_di(url), url.rsplit("/", 1)[-1]
            if h not in BANCHE[dove]:
                return banco._Risposta(404, {})
            s = BANCHE[dove][h]
            return banco._Risposta(200, {"status": s, "paid": s == "success"})


class Orologio:
    """L'orologio del server, che qui si sposta in avanti. Tutto quel
    che non e' l'ora di adesso resta del modulo vero."""

    def __init__(self):
        self.avanti = 0

    def time(self):
        return _time.time() + self.avanti

    def localtime(self, t=None):
        return _time.localtime(self.time() if t is None else t)

    def strftime(self, forma, t=None):
        return _time.strftime(forma, t or self.localtime())

    def __getattr__(self, nome):
        return getattr(_time, nome)


def main():
    print("=" * 58)
    print("  PAGA DA UN'ALTRA CASSAFORTE — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    SRV.httpx = _DueLnbits
    orologio = Orologio()
    SRV.time = orologio
    # le chiavi di cartone col setattr e da un dizionario: la forma
    # `NOME = "valore"` e' quella di un config, e lo scanner dei segreti
    # non puo' distinguere una chiave finta da una vera
    for nome, valore in {
            "LNBITS_URL": "http://saas.finto",
            "LNBITS_INVOICE_KEY": "lettura-saas",
            "LNBITS_ADMIN_KEY": "paga-saas",
            "LNBITS_NODO_URL": "http://nodo.finto",
            "LNBITS_NODO_INVOICE_KEY": "lettura-nodo",
            "LNBITS_NODO_ADMIN_KEY": "paga-nodo"}.items():
        setattr(SRV, nome, valore)

    async def lnd_finto(payment_hash):
        return LND.get(payment_hash, SRV.LND_ASSENTE)

    SRV._chiedi_lnd = lnd_finto
    a1, a2, a3, a4 = banco.semina()

    def rifiuto(fn, *args, corpo=None):
        try:
            return banco.chiama(fn, *args, corpo=corpo)
        except SRV.HTTPException as e:
            return e

    def esegui(sql, *par):
        con = SRV.db()
        con.execute(sql, par)
        con.commit()
        con.close()

    def leggi(sql, *par):
        con = SRV.db()
        r = con.execute(sql, par).fetchall()
        con.close()
        return [tuple(x) for x in r]

    def fattura(n, vita=3600):
        return bolt11_finta(50_000, vita, int(orologio.time()), phash=n)

    def h(n):
        return f"{n:064x}"

    def moderatore():
        banco.come(999, admin=True)

    def posso(oid):
        moderatore()
        return asyncio.run(SRV.posso_altra_cassaforte("ordine", oid, "", ""))

    def paga(oid, **k):
        moderatore()
        return rifiuto(SRV.paga_da_altra_cassaforte, None, "", "",
                       corpo={"tipo": "ordine", "id": oid, **k})

    def coda(oid):
        moderatore()
        return next((r for r in SRV.coda_pagamenti("", "")
                     if r["tipo"] == "ordine" and r["id"] == oid), {})

    def stadio(oid, chi):
        banco.come(chi)
        for o in SRV.miei_ordini(0, "", ""):
            if o["id"] == oid:
                return o.get("pagamento") or {}
        return {}

    # ---- 1) lo schema ---------------------------------------------
    print("\n[lo schema]")
    colonne = lambda t: {r[1] for r in leggi(f"PRAGMA table_info({t})")}
    prova("init_db: la tabella dei crediti, e le colonne nuove",
          (True, True, True),
          (bool(colonne("crediti_cassaforte")),
           {"cassaforte", "scade"} <= colonne("payout_tentati"),
           {"cassaforte_payout", "payout_nota"} <= colonne("ordini")))
    # un database di IERI: la memoria degli hash senza le due colonne
    esegui("DROP TABLE payout_tentati")
    esegui("CREATE TABLE payout_tentati(tabella TEXT NOT NULL, riga_id "
           "INTEGER NOT NULL, hash TEXT NOT NULL, quando INTEGER NOT NULL "
           "DEFAULT 0, esito TEXT NOT NULL DEFAULT '', "
           "PRIMARY KEY(tabella, riga_id, hash))")
    SRV.init_db()
    prova("un database di ieri si migra da solo al riavvio", True,
          {"cassaforte", "scade"} <= colonne("payout_tentati"))

    # ---- 2) il #152, per intero ------------------------------------
    print("\n[il #152: appeso sul SaaS, pagato dal nodo]")
    F1 = fattura(1)
    oid = banco.ordine_pagato(a1)
    banco.fattura_di_ieri(oid, F1)
    prova("l'ordine nasce sul SaaS", "saas", banco.riga(oid)["cassaforte"])
    banco.DETTO.clear(); banco.AVVISI.clear()
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid, None)
    prova("confermato: il payout parte dal SaaS e resta appeso",
          ("in_volo", [("saas", h(1))]),
          (banco.riga(oid)["payout_stato"], POSTE))
    prova("la memoria ricorda da dove e quando scade",
          [("saas", True)],
          [(c, s > 0) for c, s in leggi(
              "SELECT cassaforte, scade FROM payout_tentati WHERE hash=?",
              h(1))])
    orologio.avanti = 40 * MINUTI
    asyncio.run(SRV.risolvi_pagamenti_in_volo())
    prova("dopo mezz'ora: 🧊", "incerto", banco.riga(oid)["payout_stato"])
    c = coda(oid)
    # M1 (23 set 2026): senza LND il bottone e' acceso, e a decidere e'
    # LNbits al tocco — «pending» e' vivo, si apre solo con un «failed»
    prova("la coda vera dice da dove esce, e il bottone e' ACCESO",
          ("saas", True),
          (c.get("cassaforte"), (c.get("altra_cassaforte") or {}).get("forse")))
    r = posso(oid)
    prova("troppo presto: «viva», la fattura non e' ancora scaduta",
          (False, "viva"), (r.get("ok"), r.get("codice")))
    prova("...e la rotta rifiuta: 409", 409, getattr(
        paga(oid, cassaforte="nodo", conferma=True), "status_code", None))
    orologio.avanti = 130 * MINUTI
    prova("scaduta da 70 minuti: il bottone si accende", True,
          (coda(oid).get("altra_cassaforte") or {}).get("forse"))
    r = posso(oid)
    prova("scaduta da 70 minuti e ancora «pending»: VIVA (M1, niente calendario)",
          ("viva", True), (r.get("codice"), "resta vivo" in (r.get("perche") or "")))
    prova("...e la rotta rifiuta: 409", 409, getattr(
        paga(oid, cassaforte="nodo", conferma=True), "status_code", None))
    BANCHE["saas"][h(1)] = "failed"
    r = posso(oid)
    prova("LNbits dice «failed»: morta, ma manca la fattura nuova",
          "manca_fattura", r.get("codice"))
    r = paga(oid, azione="chiedi_fattura")
    prova("la si chiede a chi vende", "chiesta", r.get("esito"))
    prova("...che riceve UN messaggio", 1, sum(
        1 for chi, t in banco.DETTO if chi == 222 and "fattura nuova" in t))
    s = stadio(oid, 222)
    prova("...e nell'ordine gli si apre il campo",
          ("in_verifica", True), (s.get("passo"), s.get("gesto_venditore")))
    prova("...l'ordine e' rimasto 'locked' (il ramo mite non cambia lo "
          "stato): e' il caso in cui la porta diceva «troppo presto»",
          "locked", banco.riga(oid)["stato"])
    prova("...chi compra legge lo stesso stadio, e a lui non si chiede "
          "niente", "in_verifica", stadio(oid, 111).get("passo"))
    F2 = fattura(2)
    banco.come(222)
    r = banco.chiama(SRV.deposita_invoice, oid, None, "", "",
                     corpo={"invoice": F2})
    prova("chi vende la incolla: non parte niente, attende un moderatore",
          (True, 1), (r.get("attende_moderatore"), len(POSTE)))
    prova("...e ai moderatori arriva l'avviso", 1, sum(
        1 for a in banco.AVVISI if "📥" in a))
    r = posso(oid)
    prova("adesso si puo': da saas a nodo, e SENZA credito (l'origine e' «failed»)",
          (True, "saas", ["nodo"], 50_000, 0),
          (r.get("ok"), r.get("origine"), r.get("destinazioni"),
           r.get("sats"), len(r.get("crediti") or [])))
    prova("senza conferma esplicita: 400", 400, getattr(
        paga(oid, cassaforte="nodo"), "status_code", None))
    r = paga(oid, cassaforte="nodo", conferma=True)
    prova("PAGATO DAL NODO", (True, "released"),
          (r.get("ok"), r.get("stato")))
    prova("...la POST nuova e' andata al nodo", [("saas", h(1)), ("nodo", h(2))],
          POSTE)
    o = banco.riga(oid)
    prova("...`cassaforte` resta saas, `cassaforte_payout` dice nodo, "
          "l'hash e' quello nuovo",
          ("released", "uscito", "saas", "nodo", h(2)),
          (o["stato"], o["payout_stato"], o["cassaforte"],
           o["cassaforte_payout"], o["payout_hash"]))
    prova("...la nota resta sull'ordine", True,
          "pagato dalla cassaforte nodo invece di saas, deciso da 999"
          in o["payout_nota"])
    prova("...chi vende sente «Arrivati ✓»", 1, sum(
        1 for chi, t in banco.DETTO if chi == 222 and "Arrivati ✓" in t))
    moderatore()
    crediti = SRV.lista_crediti("", "")
    prova("...e nel pannello non c'e' nessun credito",
          [],
          [(c["cassaforte"], c["hash"], c["sats"], c["pagato_da"], c["stato"])
           for c in crediti])
    prova("secondo click: 409, nessun pagamento in piu'", (409, 2),
          (getattr(paga(oid, cassaforte="nodo", conferma=True),
                   "status_code", None), len(POSTE)))
    banco.AVVISI.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    prova("il libro mastro VERO non grida niente: ne' credito ne' deviazione",
          (0, False, False),
          (len(banco.AVVISI),
           "credito da recuperare su un'altra cassaforte"
           in " ".join(banco.AVVISI),
           "incasso deviato senza verbale" in " ".join(banco.AVVISI)))

    # ---- 3) il credito rientra -------------------------------------
    print("\n[il credito]")
    # un credito nasce dove LND vede un FAILED che LNbits non ha ancora
    # recepito: qui lo si scrive a mano, con l'origine ancora «pending»,
    # per provare la SORVEGLIANZA
    esegui("INSERT INTO crediti_cassaforte(tabella, riga_id, cassaforte, hash, "
           "sats, pagato_da, motivo, deciso_da, deciso_il) "
           "VALUES('ordini',?,'saas',?,50000,'nodo','prova',999,?)",
           oid, h(1), int(orologio.time()))
    BANCHE["saas"][h(1)] = "pending"
    banco.AVVISI.clear()
    orologio.avanti += 3600
    asyncio.run(SRV.sorveglia_crediti())
    prova("ancora appeso: aperto, in silenzio", ("aperto", 0),
          (leggi("SELECT stato FROM crediti_cassaforte")[0][0],
           len(banco.AVVISI)))
    BANCHE["saas"][h(1)] = "failed"
    orologio.avanti += 3600
    asyncio.run(SRV.sorveglia_crediti())
    prova("il pagamento appeso fallisce: rientrato, e lo si dice",
          ("rientrato", 1),
          (leggi("SELECT stato FROM crediti_cassaforte")[0][0],
           sum(1 for a in banco.AVVISI if "Credito rientrato" in a)))

    # ---- 4) il rifiuto: origine IN_FLIGHT ---------------------------
    print("\n[origine IN_FLIGHT sul nodo: non si scavalca]")
    orologio.avanti = 0
    F3 = fattura(3)
    oid2 = banco.ordine_pagato(a2)
    esegui("UPDATE ordini SET cassaforte='nodo' WHERE id=?", oid2)
    banco.fattura_di_ieri(oid2, F3)
    ESITO["nodo"] = "pending"
    LND[h(3)] = SRV.LND_IN_FLIGHT
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid2, None)
    orologio.avanti = 40 * MINUTI
    asyncio.run(SRV.risolvi_pagamenti_in_volo())
    prova("appeso sul nodo, e 🧊", "incerto",
          banco.riga(oid2)["payout_stato"])
    orologio.avanti = 30 * 86400
    esegui("UPDATE ordini SET invoice_venditore=? WHERE id=?",
           fattura(4), oid2)
    r = posso(oid2)
    prova("LND dice IN_FLIGHT: «viva», anche a fattura scaduta da un mese",
          (False, "viva"), (r.get("ok"), r.get("codice")))
    prima = len(POSTE)
    e = paga(oid2, cassaforte="saas", conferma=True)
    prova("la rotta RIFIUTA: 409, con la frase chiara", (409, True),
          (getattr(e, "status_code", None),
           "IN VOLO" in str(getattr(e, "detail", ""))))
    o = banco.riga(oid2)
    prova("...e non si e' mosso niente",
          (prima, "incerto", "", 1),
          (len(POSTE), o["payout_stato"], o["cassaforte_payout"],
           len(leggi("SELECT 1 FROM crediti_cassaforte"))))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
