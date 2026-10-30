# -*- coding: utf-8 -*-
"""
LA RETE DELL'ON-CHAIN DAL PANNELLO (30 ott 2026, cantiere
onchain-rete-pannello, Andrea: «signet e mainnet devono essere
automatici nelle descrizioni, e devono essere un tasto configurabile
direttamente dalle impostazioni») — il giro col SERVER VERO, per HTTP:
- la scheda è un tasto a due scelte, signet e mainnet;
- una parola storta: 400; «mainnet»: si scrive, ma il server di ADESSO
  resta su signet (vale al riavvio) e la scheda lo dice;
- un secondo processo sullo stesso database riparte su mainnet;
- «Torna al config» toglie il cambio in attesa;
- da mainnet, con un ordine aperto coi sats veri: 400 sia per signet sia
  per «Torna al config»; e se la riga di signet c'è già, al riavvio il
  server resta su mainnet e lo dice (`trattenuta`);
- chiuso l'ordine, si va.

USO:  python collaudo_onchain_rete_pannello.py
"""
import json
import os
import subprocess
import sys

import collaudo_lnbits_muto as banco
from collaudo_lnbits_muto import come, prova


# il secondo processo: lo stesso config del banco, sullo stesso database
FIGLIO = r'''
import sys, json, types
cfg = types.ModuleType("config")
for k, v in dict(BOT_TOKEN="0:collaudo", ANTHROPIC_API_KEY="INCOLLA_QUI",
                 LNBITS_URL="http://127.0.0.1:1", LNBITS_INVOICE_KEY="INCOLLA_QUI",
                 LNBITS_ADMIN_KEY="INCOLLA_QUI", ADMIN_IDS=[999],
                 MODALITA_COLLAUDO=True, COMMISSIONE_PERCENTO=0,
                 PROTEZIONE_PERCENTO=0, ORE_CONFERMA=72, GIORNI_AUTO_SBLOCCO=10,
                 MODELLO_RICERCA="claude-haiku-4-5-20251001", DB=sys.argv[1]).items():
    setattr(cfg, k, v)
sys.modules["config"] = cfg
sys.path.insert(0, sys.argv[2])
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import server
print(json.dumps({"ONCHAIN_RETE": server.ONCHAIN_RETE,
                  "STRADA": server.ONCHAIN_STRADA_CONTO,
                  "TRATTENUTA": server.ONCHAIN_RETE_TRATTENUTA}))
'''


def main():
    print("=" * 58)
    print("  LA RETE DELL'ON-CHAIN DAL PANNELLO — il giro vero")
    print("=" * 58)
    db = banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    qui = os.path.dirname(os.path.abspath(__file__))

    def leva(chi, **corpo):
        come(chi, admin=(chi == 999))
        return c.post("/api/admin/leve/ONCHAIN_RETE", json=corpo)

    def scheda():
        come(999, admin=True)
        for g in c.get("/api/admin/leve").json()["gruppi"]:
            for v in g["voci"]:
                if v["chiave"] == "ONCHAIN_RETE":
                    return v
        return {}

    def figlio():
        out = subprocess.run([sys.executable, "-c", FIGLIO, db, qui],
                             capture_output=True, text=True, timeout=300, cwd=qui)
        try:
            return json.loads(out.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError):
            print(out.stderr[-2000:])
            return {}

    # ---- 1) la scheda -------------------------------------------------------
    print("\n[la scheda: due tasti, signet di serie]")
    w = scheda().get("scrivibile") or {}
    prova("un tasto a due scelte, signet adesso, niente in attesa",
          ("scelta", ["signet", "mainnet"], "signet", "", False, ""),
          (w.get("tipo"), w.get("scelte"), w.get("attuale"),
           w.get("dal_riavvio"), w.get("subito"), w.get("trattenuta")))
    prova("chi non è admin: 403", 403, leva(111, valore="mainnet").status_code)
    prova("una parola storta: 400", 400, leva(999, valore="testnet").status_code)

    # ---- 2) verso mainnet, al riavvio --------------------------------------
    print("\n[«mainnet»: si scrive, vale al riavvio]")
    r = leva(999, valore="mainnet")
    prova("scritta, dal pannello, e non subito",
          (200, "mainnet", "pannello", False),
          (r.status_code, r.json().get("valore"), r.json().get("origine"),
           r.json().get("subito")))
    prova("...il server di adesso resta tutto signet", ("signet", "m/48'/1'/0'/2'"),
          (SRV.ONCHAIN_RETE, SRV.ONCHAIN_STRADA_CONTO))
    w = scheda()["scrivibile"]
    prova("...e la scheda dice quella del riavvio", ("signet", "mainnet"),
          (w.get("attuale"), w.get("dal_riavvio")))
    come(999, admin=True)
    st = c.get("/api/admin/leve-storia").json()["storia"][0]
    prova("la storia: da signet a mainnet", ("ONCHAIN_RETE", "signet", "mainnet"),
          (st["chiave"], st["prima"], st["dopo"]))
    f = figlio()
    prova("un server nuovo sullo stesso database riparte su mainnet, tutto insieme",
          ("mainnet", "m/48'/0'/0'/2'", ""),
          (f.get("ONCHAIN_RETE"), f.get("STRADA"), f.get("TRATTENUTA")))
    r = leva(999, torna_al_config=True)
    prova("«Torna al config»: niente più in attesa", (200, "signet", ""),
          (r.status_code, r.json().get("valore"),
           scheda()["scrivibile"].get("dal_riavvio")))

    # ---- 3) i sats veri non si lasciano indietro ---------------------------
    print("\n[da mainnet, con un ordine aperto coi sats veri]")
    con = SRV._onchain_db_ordini()
    try:
        con.execute(
            "INSERT INTO onchain_indirizzi(rete, compratore_id, venditore_id,"
            " xpub_compratore, numero_compratore, xpub_venditore,"
            " numero_venditore, xpub_barattolo, numero_barattolo,"
            " chiave_compratore, chiave_venditore, chiave_barattolo,"
            " descrittore, indirizzo) VALUES ('mainnet', 111, 222, 'xc', 0,"
            " 'xv', 0, 'xb', 0, 'kc', 'kv', 'kb', 'wsh(...)', 'bc1qprova')")
        iid = con.execute("SELECT id FROM onchain_indirizzi WHERE "
                          "indirizzo='bc1qprova'").fetchone()[0]
        con.execute(
            "INSERT INTO onchain_ordini(indirizzo_id, annuncio_id,"
            " compratore_id, venditore_id, prezzo_sats, margine_sats,"
            " importo_sats, incasso, rimborso, stato, ricevuti_sats, scade,"
            " creato, aggiornato) VALUES (?, 1, 111, 222, 10000, 1000,"
            " 11000, 'bc1qv', 'bc1qc', 'pagato', 11000, 0, 0, 0)", (iid,))
        con.commit()
    finally:
        con.close()
    SRV.ONCHAIN_RETE = "mainnet"      # il server che gira su mainnet
    r = leva(999, valore="signet")
    prova("verso signet: 400 col perché, e niente scritto (resta il valore di serie)",
          (400, True, "codice"),
          (r.status_code, "1 ordini on-chain aperti coi sats veri"
           in r.json().get("detail", ""),
           scheda()["scrivibile"].get("origine")))
    prova("...anche «Torna al config» (che è signet)", 400,
          leva(999, torna_al_config=True).status_code)
    # la riga di signet scritta PRIMA che l'ordine nascesse
    SRV.ONCHAIN_RETE = "signet"
    prova("(da signet la riga si scrive)", 200, leva(999, valore="signet").status_code)
    f = figlio()
    prova("al riavvio il server resta su mainnet, e dice perché",
          ("mainnet", "m/48'/0'/0'/2'", True),
          (f.get("ONCHAIN_RETE"), f.get("STRADA"),
           "1 ordini on-chain hanno ancora i sats veri" in f.get("TRATTENUTA", "")))
    SRV.ONCHAIN_RETE = "mainnet"
    con = SRV._onchain_db_ordini()
    try:
        con.execute("UPDATE onchain_ordini SET stato='rilasciato', txid_uscita='ab'")
        con.commit()
    finally:
        con.close()
    prova("chiuso l'ordine, verso signet si va", 200,
          leva(999, valore="signet").status_code)
    f = figlio()
    prova("...e al riavvio è signet", ("signet", ""),
          (f.get("ONCHAIN_RETE"), f.get("TRATTENUTA")))
    SRV.ONCHAIN_RETE = "signet"

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
