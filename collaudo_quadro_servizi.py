# -*- coding: utf-8 -*-
"""
IL QUADRO DEI SERVIZI, col SERVER VERO (25 nov 2026, cantiere
quadro-servizi). Per HTTP, sul banco di `collaudo_lnbits_muto`:
- senza BATTITO_SEGRETO la porta dei battiti non esiste (404);
- col segreto: sbagliato 403, nome sconosciuto 400, corpo che non e' un
  oggetto 400, battito buono 200;
- il quadro: chi non e' admin 403; l'admin vede il relay «su» col suo
  backup, e i servizi che non hanno mai battuto «mai»;
- il giro dell'orologio batte per il VPS da solo.
I giudici, con l'orologio finto, stanno in prove.py
(`prove_quadro_servizi`).

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete.

USO:  python collaudo_quadro_servizi.py
"""
import sys
import time

import collaudo_lnbits_muto as banco
from collaudo_lnbits_muto import come, prova


def main():
    print("=" * 58)
    print("  IL QUADRO DEI SERVIZI — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    segreto = "battito-" + "di-collaudo"
    giusto = {"Authorization": "Bearer " + segreto}

    print("\n[la porta dei battiti]")
    SRV.BATTITO_SEGRETO = ""
    r = c.post("/api/battito", json={"servizio": "relay"}, headers=giusto)
    prova("senza segreto la rotta non esiste: 404", 404, r.status_code)
    SRV.BATTITO_SEGRETO = segreto
    r = c.post("/api/battito", json={"servizio": "relay"},
               headers={"Authorization": "Bearer altro"})
    prova("segreto sbagliato: 403", 403, r.status_code)
    r = c.post("/api/battito", json={"servizio": "posta"}, headers=giusto)
    prova("un servizio sconosciuto: 400", 400, r.status_code)
    r = c.post("/api/battito", json=["relay"], headers=giusto)
    prova("un corpo che non e' un oggetto: 400", 400, r.status_code)
    r = c.post("/api/battito", json={"servizio": "relay", "backup_ore": "5"},
               headers=giusto)
    prova("un'eta' del backup che non e' un numero: 400", 400, r.status_code)
    r = c.post("/api/battito", json={"servizio": "relay", "backup_ore": 5},
               headers=giusto)
    prova("il battito buono: 200 {ok}", (200, {"ok": True}),
          (r.status_code, r.json()))
    prova("...e non si cacha", "no-store", r.headers.get("cache-control"))

    print("\n[il quadro, solo per gli admin]")
    come(111)
    r = c.get("/api/admin/servizi")
    prova("chi non e' admin: 403", 403, r.status_code)
    SRV._servizi_giro(time.time())          # il giro dell'orologio
    come(999, admin=True)
    r = c.get("/api/admin/servizi")
    d = r.json()
    q = {v["chiave"]: v for v in d.get("servizi", [])}
    prova("l'admin: 200, i nove servizi", (200, 9), (r.status_code, len(q)))
    prova("il relay ha battuto: su, col suo backup e uptime",
          ("su", 5, True),
          (q["relay"]["stato"], q["relay"]["backup_ore"],
           q["relay"]["uptime"] is not None))
    prova("il VPS l'ha battuto il giro dell'orologio, da solo", "su",
          q["vps"]["stato"])
    prova("chi non ha mai battuto: «mai»", "mai", q["nodo"]["stato"])
    prova("la porta e' detta aperta, e il segreto non esce", (True, False),
          (d.get("battiti_aperti"), segreto in r.text))
    prova("i certificati: tre, non ancora letti in collaudo",
          (3, [False, False, False]),
          (len(d.get("certificati", [])),
           [x["letto"] for x in d.get("certificati", [])]))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
