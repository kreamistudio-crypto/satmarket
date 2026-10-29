"""Il server VERO di Barattolo in locale, col nodo muto del banco e una
rete Bitcoin FINTA in memoria (mempool.space non e' raggiungibile da qui).
Tutto il resto e' il codice di produzione: login Nostr, cassa, 2-di-3,
firme, disputa. Le porte /_giro/* sono solo per il copione."""
import json
import os
import sys
import time

QUI = sys.argv[1]
PORTA = int(sys.argv[2]) if len(sys.argv) > 2 else 8099
sys.path.insert(0, QUI)
os.chdir(QUI)
import collaudo_lnbits_muto as banco  # noqa: E402

banco.avvio()
SRV = banco.SRV
from embit import bip32, bip39, script  # noqa: E402
from embit.finalizer import finalize_psbt  # noqa: E402
from embit.networks import NETWORKS  # noqa: E402
from embit.psbt import PSBT  # noqa: E402
from embit.transaction import Transaction, TransactionInput, TransactionOutput  # noqa: E402
from fastapi import Request  # noqa: E402

N = NETWORKS["signet"]
SRV.ONCHAIN_ATTIVO = True
# mai relay veri: tutto al relay morto
for nome in ("RELAYS_VERIFICA", "RELAY_NOSTR", "RELAY_NOSTR_IMPORT",
             "MOSTRO_RELAY", "MOSTRO_RELAY_SPECCHIO", "AVVISO_DM_NOSTR_RELAY"):
    if hasattr(SRV, nome):
        setattr(SRV, nome, ["ws://127.0.0.1:9"])

# ---------------- la rete finta: txid -> uscite -----------------------
CATENA = {}          # txid -> [{"addr", "value", "speso"}]
TX_HEX = {}          # txid -> hex
GIORNALE = []        # cosa e' successo, in ordine


def _utxo(addr):
    out = []
    for txid, uscite in CATENA.items():
        for i, u in enumerate(uscite):
            if u["addr"] == addr and not u["speso"]:
                out.append({"txid": txid, "vout": i, "value": u["value"],
                            "status": {"confirmed": True, "block_height": 100}})
    return out


async def utxo_finte(indirizzo):
    return _utxo(indirizzo)


async def scheda_finta(indirizzo):
    n = sum(1 for us in CATENA.values() for u in us if u["addr"] == indirizzo)
    return {"chain_stats": {"tx_count": n}, "mempool_stats": {"tx_count": 0}}


async def tariffa_finta():
    return 1.0


async def invia_finta(tx_hex):
    tx = Transaction.from_string(tx_hex)
    txid = tx.txid().hex()
    for vin in tx.vin:
        t = vin.txid.hex()
        if t not in CATENA or vin.vout >= len(CATENA[t]) or CATENA[t][vin.vout]["speso"]:
            raise ValueError("bad-txns-inputs-missingorspent")
    entrate = sum(CATENA[v.txid.hex()][v.vout]["value"] for v in tx.vin)
    uscite = sum(o.value for o in tx.vout)
    if uscite > entrate:
        raise ValueError("bad-txns-in-belowout")
    for vin in tx.vin:
        CATENA[vin.txid.hex()][vin.vout]["speso"] = True
    CATENA[txid] = [{"addr": o.script_pubkey.address(N), "value": o.value, "speso": False}
                    for o in tx.vout]
    TX_HEX[txid] = tx_hex
    GIORNALE.append({"tx": txid, "entrate": entrate, "uscite": [(u["addr"], u["value"]) for u in CATENA[txid]],
                     "fee": entrate - uscite, "vbytes": len(bytes.fromhex(tx_hex)) // 4 + 20})
    return txid


SRV.onchain_mempool_utxo = utxo_finte
SRV.onchain_mempool_indirizzo = scheda_finta
SRV.onchain_mempool_tariffa = tariffa_finta
SRV.onchain_mempool_invia = invia_finta

# ---------------- il wallet esterno di chi compra (come Sparrow) -------
SEME = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
RADICE = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(SEME))


def chiave_ext(i):
    return RADICE.derive(f"m/84h/1h/0h/0/{i}")


def addr_ext(i):
    return script.p2wpkh(chiave_ext(i).key.get_public_key()).address(N)


app = SRV.app


@app.post("/_giro/faucet")
async def giro_faucet(req: Request):
    d = await req.json()
    addr = d.get("indirizzo") or addr_ext(0)
    txid = ("f" * 60 + f"{len(CATENA):04x}")
    CATENA[txid] = [{"addr": addr, "value": int(d.get("sats", 100_000)), "speso": False}]
    GIORNALE.append({"faucet": addr, "sats": int(d.get("sats", 100_000)), "tx": txid})
    return {"ok": True, "txid": txid, "indirizzo": addr}


@app.post("/_giro/paga")
async def giro_paga(req: Request):
    """Il wallet esterno paga `sats` a `a` dalle sue monete, con 1 sat/vB."""
    d = await req.json()
    a, sats = d["a"], int(d["sats"])
    mie = _utxo(addr_ext(0))
    tot = sum(u["value"] for u in mie)
    fee = 150
    if tot < sats + fee:
        return {"ok": False, "motivo": f"nel wallet esterno ci sono {tot} sats"}
    tx = Transaction(vin=[TransactionInput(bytes.fromhex(u["txid"]), u["vout"]) for u in mie],
                     vout=[TransactionOutput(sats, script.address_to_scriptpubkey(a))])
    resto = tot - sats - fee
    if resto >= 546:
        tx.vout.append(TransactionOutput(resto, script.address_to_scriptpubkey(addr_ext(0))))
    p = PSBT(tx)
    for i, u in zip(p.inputs, mie):
        i.witness_utxo = TransactionOutput(u["value"], script.p2wpkh(chiave_ext(0).key.get_public_key()))
    p.sign_with(chiave_ext(0).key)
    txid = await invia_finta(finalize_psbt(p).serialize().hex())
    return {"ok": True, "txid": txid}


@app.get("/_giro/utenti")
def giro_utenti():
    con = SRV.db()
    righe = [{"tg_id": str(r["tg_id"]), "nome": r["nome"]}
             for r in con.execute("SELECT tg_id, nome FROM utenti").fetchall()]
    con.close()
    return {"utenti": righe}


@app.get("/_giro/catena")
def giro_catena():
    return {"catena": CATENA, "giornale": GIORNALE}


@app.get("/_giro/detto")
def giro_detto():
    return {"detto": banco.DETTO, "avvisi": banco.AVVISI}


@app.post("/_giro/annuncio")
async def giro_annuncio(req: Request):
    d = await req.json()
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(?,?,?,?,'Altro','Pavia (PV)','attivo',?,'ritiro',1,'sats','nuovo')",
        (int(str(d["venditore"])), d["titolo"], d.get("descrizione", "una cosa"),
         int(d["prezzo"]), int(time.time())))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return {"id": aid}


@app.get("/_giro/ordine/{oid}")
def giro_ordine(oid: int):
    con = SRV._onchain_db_ordini()
    try:
        o = con.execute("SELECT * FROM onchain_ordini WHERE id=?", (oid,)).fetchone()
        o = dict(o) if o else None
        if o:
            o.pop("utxo", None)
    finally:
        con.close()
    return {"onchain": o}


@app.get("/_giro/ordini-veri")
def giro_ordini_veri():
    con = SRV.db()
    righe = [{k: v for k, v in dict(r).items() if k in (
        "id", "stato", "compratore_id", "venditore_id", "cassaforte",
        "prezzo_sats", "totale_sats", "metodo", "annuncio_id")}
        for r in con.execute("SELECT * FROM ordini").fetchall()]
    con.close()
    return {"ordini": righe}


print("GIRO PRONTO", flush=True)
import uvicorn  # noqa: E402
uvicorn.run(app, host="127.0.0.1", port=PORTA, log_level="warning")
