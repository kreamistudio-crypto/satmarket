# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE LEVE DAL PANNELLO (27 ott 2026, cantiere leve-tutte,
Andrea: «tutto devo poter configurare da lì, suddividilo in sezioni,
ogni configurazione richieda una conferma e che possa esistere un
backup») — il giro col SERVER VERO, per HTTP (TestClient, la app vera):
- le «mai» (segreti, indirizzi, serrature) restano chiuse: 404;
- una leva di ogni tipo si cambia, il giudice del tipo dice no a quel
  che non e' suo, il cambio vale SUBITO sul globale e resta nella storia;
- «Torna al config» rimette il valore del config (o di serie);
- «Annulla» dalla storia rimette com'era prima di quel cambio;
- il backup esce col solo deciso dal pannello, e il ripristino prima
  dice cosa cambierebbe, poi lo fa (anche togliendo quel che il backup
  non conosce);
- AL RIAVVIO il pannello si posa sul config prima di ogni import: un
  secondo processo sullo stesso database vede i valori del pannello, e
  col freno a mano (`LEVE_PANNELLO_SPENTE`) no.

USO:  python collaudo_leve_pannello.py
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
if sys.argv[2] == "spente":
    cfg.LEVE_PANNELLO_SPENTE = True
sys.modules["config"] = cfg
sys.path.insert(0, sys.argv[3])
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import server
print(json.dumps({"ORE_CONFERMA": server.ORE_CONFERMA,
                  "LAMPO_SCONTI": server.LAMPO_SCONTI,
                  "CAMBIO_RINFRESCO_S": server.CAMBIO_RINFRESCO_S,
                  "CAMBIO_TTL": server.CAMBIO_TTL}))
'''


def main():
    print("=" * 58)
    print("  LE LEVE DAL PANNELLO — il giro vero")
    print("=" * 58)
    db = banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)

    def leva(chi, chiave, **corpo):
        come(chi, admin=(chi == 999))
        return c.post(f"/api/admin/leve/{chiave}", json=corpo)

    def scheda(chiave):
        come(999, admin=True)
        for g in c.get("/api/admin/leve").json()["gruppi"]:
            for v in g["voci"]:
                if v["chiave"] == chiave:
                    return v
        return None

    # ---- 1) chi si apre e chi no ------------------------------------------
    print("\n[le «mai» restano chiuse, il resto si apre]")
    come(999, admin=True)
    d = c.get("/api/admin/leve").json()
    voci = [v for g in d["gruppi"] for v in g["voci"]]
    aperte = {v["chiave"] for v in voci if v.get("scrivibile")}
    prova("il pannello apre la gran parte delle leve (oltre 150)", True,
          len(aperte) > 150)
    prova("...e nessuna delle «mai»", set(),
          aperte & SRV.LEVE_MAI_DAL_PANNELLO)
    for k in ("MODALITA_COLLAUDO", "ADMIN_IDS", "NOSTR_NSEC_PIATTAFORMA",
              "UN_TOKEN_MAI_VISTO"):
        prova(f"{k}: 404", 404, leva(999, k, valore=True).status_code)
    prova("chi non e' admin: 403", 403,
          leva(111, "ORE_CONFERMA", valore=48).status_code)

    # ---- 2) un tipo alla volta --------------------------------------------
    print("\n[ogni tipo col suo giudice, e il cambio vale subito]")
    prova("un intero: testo no", 400, leva(999, "ORE_CONFERMA", valore="tante").status_code)
    prova("...negativo no", 400, leva(999, "ORE_CONFERMA", valore=-3).status_code)
    r = leva(999, "ORE_CONFERMA", valore=48)
    prova("...48 sì, dal pannello, subito", (200, 48, "pannello", True),
          (r.status_code, r.json().get("valore"), r.json().get("origine"),
           r.json().get("subito")))
    prova("...e il globale del server e' gia' 48", 48, SRV.ORE_CONFERMA)
    r = leva(999, "LAMPO_SCONTI", valore=[15, 25])
    prova("una lista di numeri", (200, [15, 25]), (r.status_code, r.json().get("valore")))
    prova("...una lista con dentro un testo no", 400,
          leva(999, "LAMPO_SCONTI", valore=[15, "tanti"]).status_code)
    k_si_no = next(v["chiave"] for v in voci if v.get("scrivibile", {}).get("tipo") == "si_no"
                   and v["chiave"] not in SRV.LEVE_SCRIVIBILI)
    prima = getattr(SRV, k_si_no)
    r = leva(999, k_si_no, valore=not prima)
    prova(f"un sì/no ({k_si_no}) si rovescia", (200, not prima),
          (r.status_code, getattr(SRV, k_si_no)))
    r = leva(999, "CAMBIO_RINFRESCO_S", valore=90)
    prova("una letta all'avvio: si scrive, e dice «dal riavvio»", (200, False),
          (r.status_code, r.json().get("subito")))
    prova("la scheda dice da dove arriva", "pannello",
          scheda("ORE_CONFERMA")["scrivibile"]["origine"])

    # ---- 3) torna al config e annulla -------------------------------------
    print("\n[«Torna al config» e «Annulla»]")
    r = leva(999, "ORE_CONFERMA", torna_al_config=True)
    prova("«Torna al config»: 72, quello del config", (200, 72, "config"),
          (r.status_code, SRV.ORE_CONFERMA, r.json().get("origine")))
    come(999, admin=True)
    st = c.get("/api/admin/leve-storia").json()["storia"]
    prova("la storia ha i cambi, il piu' nuovo per primo",
          ("ORE_CONFERMA", 48, 72), (st[0]["chiave"], st[0]["prima"], st[0]["dopo"]))
    r = c.post(f"/api/admin/leve-storia/{st[0]['id']}/annulla")
    prova("«Annulla» il ritorno al config: di nuovo 48 dal pannello",
          (200, 48, "pannello"), (r.status_code, SRV.ORE_CONFERMA, r.json().get("origine")))
    primo = [x for x in c.get("/api/admin/leve-storia").json()["storia"]
             if x["chiave"] == "ORE_CONFERMA"][-1]
    r = c.post(f"/api/admin/leve-storia/{primo['id']}/annulla")
    prova("«Annulla» il primo cambio, che veniva dal config: torna al config",
          (200, 72, "config"), (r.status_code, SRV.ORE_CONFERMA, r.json().get("origine")))
    righe = SRV.db().execute("SELECT COUNT(*) FROM moderazione_log WHERE strato='leva'").fetchone()[0]
    prova("ogni gesto lascia una riga nel registro", True, righe >= 6)

    # ---- 4) il backup -----------------------------------------------------
    print("\n[il backup: esce, e rientra con l'anteprima]")
    leva(999, "ORE_CONFERMA", valore=36)
    come(999, admin=True)
    b = c.get("/api/admin/leve-backup").json()
    prova("il backup ha le leve decise dal pannello, coi loro valori",
          (1, 36, [15, 25], 90),
          (b["barattolo_leve"], b["leve"].get("ORE_CONFERMA"), b["leve"].get("LAMPO_SCONTI"),
           b["leve"].get("CAMBIO_RINFRESCO_S")))
    prova("...e nessun config intero dentro (il resto non e' del pannello)", False,
          "BOT_TOKEN" in json.dumps(b))
    # dopo il backup si cambia ancora: il ripristino lo deve riportare
    leva(999, "ORE_CONFERMA", valore=24)
    leva(999, "SCONTO_PACCO_SCONTI", valore=[5, 50])
    come(999, admin=True)
    r = c.post("/api/admin/leve-ripristina", json={"backup": {"leve": {}}})
    prova("un file che non e' un backup: 400", 400, r.status_code)
    r = c.post("/api/admin/leve-ripristina", json={"backup": b})
    cambi = {x["chiave"]: x for x in r.json()["cambi"]}
    prova("l'anteprima: ORE_CONFERMA torna a 36, lo sconto nato dopo torna al config",
          ((24, 36), True), ((cambi["ORE_CONFERMA"]["adesso"], cambi["ORE_CONFERMA"]["dopo"]),
                             cambi["SCONTO_PACCO_SCONTI"]["al_config"]))
    prova("...e l'anteprima non ha toccato niente", 24, SRV.ORE_CONFERMA)
    storto = dict(b, leve=dict(b["leve"], MODALITA_COLLAUDO=False, ORE_CONFERMA=36))
    r = c.post("/api/admin/leve-ripristina", json={"backup": storto, "applica": True})
    prova("applicato: 36, e lo sconto di dopo e' tornato al config",
          (200, 36, [5, 10, 15, 20]), (r.status_code, SRV.ORE_CONFERMA, list(SRV.SCONTO_PACCO_SCONTI)))
    prova("...e una «mai» dentro il backup si salta e si dice", ["MODALITA_COLLAUDO"],
          [x["chiave"] for x in r.json()["saltate"]])
    r = c.post("/api/admin/leve-backup/telegram")
    prova("il file dal bot: in collaudo si ferma prima di Telegram", (200, False, True),
          (r.status_code, r.json().get("ok"), r.json().get("collaudo")))

    # ---- 5) il riavvio ----------------------------------------------------
    print("\n[al riavvio il pannello si posa sul config, prima di ogni import]")
    qui = os.path.dirname(os.path.abspath(__file__))

    def figlio(modo):
        out = subprocess.run([sys.executable, "-c", FIGLIO, db, modo, qui],
                             capture_output=True, text=True, timeout=300, cwd=qui)
        try:
            return json.loads(out.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError):
            print(out.stderr[-2000:])
            return {}

    f = figlio("normale")
    prova("il server nuovo ha i valori del pannello (anche quella letta all'avvio, "
          "e chi ne dipende)", (36, [15, 25], 90, 180),
          (f.get("ORE_CONFERMA"), f.get("LAMPO_SCONTI"), f.get("CAMBIO_RINFRESCO_S"),
           f.get("CAMBIO_TTL")))
    f = figlio("spente")
    prova("...col freno a mano tirato vale solo il config", (72, 60),
          (f.get("ORE_CONFERMA"), f.get("CAMBIO_RINFRESCO_S")))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
