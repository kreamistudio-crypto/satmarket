# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL FILE DEGLI ID TELEGRAM (23 nov 2026, Andrea: gli id
degli utenti di Barattolo da incrociare, sul suo PC, coi membri dei
gruppi Telegram in cui sta) — il giro col SERVER VERO, per HTTP:
- chi non e' admin: 403, e il file non parte;
- l'admin: in collaudo si ferma prima di Telegram e dice quanti sono,
  contando SOLO gli id Telegram (gli utenti solo-Nostr, negativi, no);
- il freno: la sesta richiesta dell'ora risponde 429.

USO:  python collaudo_id_utenti.py
"""
import sys

import collaudo_lnbits_muto as banco
from collaudo_lnbits_muto import come, prova


def main():
    print("=" * 58)
    print("  GLI ID TELEGRAM DEGLI UTENTI — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)

    con = SRV.db()
    for tg_id in (111, 222, -5):
        con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome) VALUES (?, ?)",
                    (tg_id, f"U{tg_id}"))
    con.commit()
    attesi = con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id>0").fetchone()[0]
    tutti = con.execute("SELECT COUNT(*) FROM utenti").fetchone()[0]
    con.close()

    come(111)
    r = c.post("/api/admin/id-utenti/telegram")
    prova("chi non e' admin: 403", 403, r.status_code)

    come(999, admin=True)
    r = c.post("/api/admin/id-utenti/telegram")
    prova("l'admin, in collaudo: si ferma prima di Telegram e conta solo gli id Telegram",
          (200, False, True, attesi),
          (r.status_code, r.json().get("ok"), r.json().get("collaudo"), r.json().get("utenti")))
    prova("...e il solo-Nostr non e' nel conto", tutti - 1, r.json().get("utenti"))
    for _ in range(4):
        c.post("/api/admin/id-utenti/telegram")
    r = c.post("/api/admin/id-utenti/telegram")
    prova("la sesta dell'ora: frenata", 429, r.status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
