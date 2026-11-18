# -*- coding: utf-8 -*-
"""
IL LUCCHETTO DELLA PROVA ON-CHAIN (18 nov 2026, produzione ferma dalle
14:46 alle 14:49 UTC; la sentinella ha scritto la pila e ha riavviato).

La pila del filo principale diceva: `/api/onchain/prova` →
`onchain_ammesso` → `leva_scrivibile` → `_leve_pannello_tabella`, ferma
su sqlite. La rotta chiedeva `onchain_ammesso` per OGNI riga di
`onchain_xpub` (120 in produzione) MENTRE il cursore di quella SELECT
era ancora aperto. Col journal «delete» un cursore aperto tiene il
lucchetto di lettura (SHARED); uno scrittore di un altro filo prende il
PENDING e aspetta che quel lucchetto cada — e non cade, perche' chi lo
tiene e' fermo ad aspettare lui: ogni connessione nuova di
`leva_scrivibile` aspetta fino a DB_BUSY_TIMEOUT (15 s), riga dopo riga,
e intanto il ciclo principale non serve nessuno.

LA PROVA DIPENDE DALL'ORDINE, NON DALL'OROLOGIO: dentro ogni chiamata a
`onchain_ammesso` della rotta una connessione SENZA pazienza (timeout 0)
chiede `BEGIN EXCLUSIVE`, che riesce solo se nessuno tiene un lucchetto
di lettura. Col cursore aperto muore subito («database is locked»), con
la lista letta tutta prima passa sempre. Nessun sonno, nessun tempo.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti, PRIMA dell'import del server.

USO:  python collaudo_onchain_prova_lucchetto.py
"""
import sqlite3
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  IL LUCCHETTO DELLA PROVA ON-CHAIN — il giro vero")
    print("=" * 58)
    db = banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)

    SRV.ONCHAIN_ATTIVO = True
    SRV.ADMIN_IDS = [999]
    # una prima lettura fa nascere le tabelle (onchain_* e leve_pannello)
    banco.come(999, admin=True)
    prova("la prova risponde all'admin", 200,
          c.get("/api/onchain/prova").status_code)

    con = SRV.db()
    altri = list(range(5001, 5013))
    for tg in [999] + altri:
        con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome) VALUES (?,?)",
                    (tg, f"U{tg}"))
        con.execute("INSERT OR REPLACE INTO onchain_xpub(tg_id, xpub, creato,"
                    " aggiornato) VALUES (?,?,1,?)", (tg, f"tpub{tg}", tg))
    con.commit()
    con.close()

    vero = SRV.onchain_ammesso
    esiti = []

    def ammesso_che_sonda(tg_id):
        # la sonda: uno scrittore che non aspetta nessuno
        s = sqlite3.connect(db, timeout=0)
        try:
            s.execute("BEGIN EXCLUSIVE")
            s.execute("ROLLBACK")
            esiti.append("libero")
        except sqlite3.OperationalError as e:
            esiti.append(str(e))
        finally:
            s.close()
        return vero(tg_id)

    SRV.onchain_ammesso = ammesso_che_sonda
    try:
        print("\n[mentre la rotta chiede chi e' ammesso, il database e' libero]")
        banco.come(999, admin=True)
        r = c.get("/api/onchain/prova")
    finally:
        SRV.onchain_ammesso = vero
    d = r.json()
    prova("la rotta risponde, e le controparti sono le 12 (solo admin: "
          "nessuna ammessa)", (200, []), (r.status_code, d["controparti"]))
    # +1: il cancello della rotta chiede prima di chi legge
    prova("onchain_ammesso chiesto una volta per riga (piu' il cancello)",
          len(altri) + 1, len(esiti))
    prova("...e ogni volta nessun lucchetto di lettura era tenuto",
          ["libero"] * (len(altri) + 1), esiti)

    print("\n[aperta a tutti: le controparti tornano, coi nomi]")
    SRV.ONCHAIN_SOLO_ADMIN = False
    con = SRV.db()
    SRV._leve_pannello_tabella(con)
    con.execute("DELETE FROM leve_pannello WHERE chiave='ONCHAIN_SOLO_ADMIN'")
    con.commit()
    con.close()
    banco.come(999, admin=True)
    d = c.get("/api/onchain/prova").json()
    prova("12 controparti, la piu' recente prima, col suo nome",
          (12, {"id": 5012, "nome": "U5012"}),
          (len(d["controparti"]), d["controparti"][0]))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
