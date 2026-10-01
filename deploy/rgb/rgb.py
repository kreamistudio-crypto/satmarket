#!/usr/bin/env python3
"""rgb.py — il banco di prova RGB di Barattolo su signet (hackathon di Torino).

Un wallet per NOME, in ~/rgb/dati/<nome>/:
  chiavi.json   la frase segreta, gli xpub e la password del backup (0600)
  wallet/       la cartella dati di rgb-lib (lo "stash": senza, i punti
                non si provano e non si spendono — la seed da sola NON basta)

Regola d'oro di rgb-lib: «never instantiate a wallet in multiple places».
Qui ogni comando apre UN wallet, fa la sua cosa e chiude; mai due processi
sulla stessa cartella.

Uso:  rgb.py <comando> <nome> [argomenti]
  nuovo         <nome>                          crea le chiavi (una volta sola)
  indirizzo     <nome>                          un indirizzo signet per il faucet
  saldo         <nome>                          sats, UTXO colorabili, asset
  utxo          <nome> [quanti]                 crea UTXO colorabili (default 5)
  emetti        <nome> <TICKER> <Nome> <quantita> [precisione]   emette un NIA
  fattura       <nome> [asset_id|-] [witness]   una fattura RGB per ricevere
  invia         <nome> <asset_id> <quantita> <fattura>           manda punti
  aggiorna      <nome>                          refresh: ACK, broadcast, conferme
  trasferimenti <nome> [asset_id]               la storia dei trasferimenti
  btc           <nome> <indirizzo> <sats>       manda sats (per fondare un altro wallet)
  backup        <nome>                          backup cifrato di rgb-lib in ~/rgb/backup
  ripristina    <nome> <file.backup>            ripristina lo stash (chiavi.json gia' al suo posto)

Variabili d'ambiente (facoltative): RGB_INDEXER, RGB_PROXY, RGB_FEE, RGB_BASE.
"""
import json
import os
import re
import secrets
import sys
import time

import rgb_lib

BASE = os.path.expanduser(os.environ.get("RGB_BASE", "~/rgb/dati"))
BACKUP = os.path.join(os.path.dirname(BASE), "backup")
RETE = rgb_lib.BitcoinNetwork.SIGNET
INDEXER = os.environ.get("RGB_INDEXER", "tcp://127.0.0.1:50001")
PROXY = os.environ.get("RGB_PROXY", "rpc://127.0.0.1:3000/json-rpc")
FEE = int(os.environ.get("RGB_FEE", "2"))          # sat/vB: su signet basta
SCHEMI = [rgb_lib.AssetSchema.NIA]
SCADENZA = 24 * 3600                                # le fatture valgono un giorno
CONFERME = 1
SATS_WITNESS = 1000                                 # l'uscita che paga chi manda
ESPLORA = "https://mempool.space/signet/tx/"


def _die(msg):
    print("✗", msg, file=sys.stderr)
    sys.exit(1)


def _cartella(nome):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,30}", nome):
        _die("il nome del wallet: minuscole, cifre e trattini (es. barattolo, caffe-luca)")
    return os.path.join(BASE, nome)


def _chiavi(nome):
    percorso = os.path.join(_cartella(nome), "chiavi.json")
    if not os.path.exists(percorso):
        _die(f"il wallet «{nome}» non esiste: prima `rgb.py nuovo {nome}`")
    with open(percorso) as f:
        return json.load(f)


def _wallet(nome, online=True):
    """Apre il wallet e, se serve, lo mette in rete (sync con electrs)."""
    c = _chiavi(nome)
    dati = rgb_lib.WalletData(
        data_dir=os.path.join(_cartella(nome), "wallet"),
        bitcoin_network=RETE,
        database_type=rgb_lib.DatabaseType.SQLITE,
        max_allocations_per_utxo=1,
        supported_schemas=SCHEMI,
    )
    chiavi = rgb_lib.SinglesigKeys(
        account_xpub_vanilla=c["account_xpub_vanilla"],
        account_xpub_colored=c["account_xpub_colored"],
        vanilla_keychain=None,
        master_fingerprint=c["master_fingerprint"],
        mnemonic=c["mnemonic"],
        witness_version=rgb_lib.WitnessVersion.TAPROOT,
    )
    w = rgb_lib.Wallet(dati, chiavi)
    if not online:
        return w, None
    opzioni = rgb_lib.OnlineOptions(
        indexer_url=INDEXER, skip_consistency_check=False, vanilla_sync_lookback=20)
    return w, w.go_online(opzioni)


# ----------------------------------------------------------------- comandi

def nuovo(nome):
    cartella = _cartella(nome)
    if os.path.exists(os.path.join(cartella, "chiavi.json")):
        _die(f"«{nome}» esiste gia': non si rigenerano chiavi sopra un wallet vivo")
    k = rgb_lib.generate_keys(RETE, rgb_lib.WitnessVersion.TAPROOT)
    os.makedirs(os.path.join(cartella, "wallet"), mode=0o700, exist_ok=True)
    percorso = os.path.join(cartella, "chiavi.json")
    with open(os.open(percorso, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
        json.dump({
            "rete": "signet",
            "mnemonic": k.mnemonic,
            "xpub": k.xpub,
            "account_xpub_vanilla": k.account_xpub_vanilla,
            "account_xpub_colored": k.account_xpub_colored,
            "master_fingerprint": k.master_fingerprint,
            "password_backup": secrets.token_urlsafe(24),
            "creato": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)
    print(f"✓ wallet «{nome}» creato in {cartella}")
    print(f"  impronta {k.master_fingerprint}, xpub colorato {k.account_xpub_colored[:16]}…")
    print("  la frase segreta sta SOLO in chiavi.json: non incollarla da nessuna parte")


def indirizzo(nome):
    w, _ = _wallet(nome)
    print(w.get_address())


def saldo(nome):
    w, on = _wallet(nome)
    b = w.get_btc_balance(on, False)
    print(f"sats vanilla: {b.vanilla.settled} (in arrivo {b.vanilla.future})  "
          f"sats colorati: {b.colored.settled} (in arrivo {b.colored.future})")
    print("UTXO:")
    for u in w.list_unspents(on, False, True):
        o = u.utxo.outpoint
        col = "colorabile" if u.utxo.colorable else "vanilla"
        print(f"  {o.txid[:12]}…:{o.vout}  {u.utxo.btc_amount} sats  {col}")
        for a in u.rgb_allocations:
            stato = "settled" if a.settled else "in attesa"
            print(f"      ↳ {a.asset_id}  {a.assignment}  ({stato})")
    print("asset NIA:")
    for a in w.list_assets([]).nia:
        print(f"  {a.ticker:8} {a.name:32} emessi {a.issued_supply}  "
              f"saldo {a.balance.settled} (spendibili {a.balance.spendable}, futuri {a.balance.future})")
        print(f"           {a.asset_id}")


def utxo(nome, quanti="5"):
    w, on = _wallet(nome)
    n = w.create_utxos(on, True, int(quanti), None, FEE, False)
    print(f"✓ creati {n} UTXO colorabili (una transazione signet, aspetta una conferma)")


def emetti(nome, ticker, nome_asset, quantita, precisione="0"):
    if not re.fullmatch(r"[A-Z0-9]{1,8}", ticker):
        _die("il ticker: solo MAIUSCOLE e cifre, da 1 a 8 caratteri (niente trattini)")
    w, on = _wallet(nome)
    a = w.issue_asset_nia(ticker, nome_asset, int(precisione), [int(quantita)])
    print(f"✓ emesso {a.ticker} «{a.name}», {a.issued_supply} unita'")
    print(f"  asset_id: {a.asset_id}")
    print("  (vive su un UTXO colorabile: niente transazione finche' non lo mandi)")


def fattura(nome, asset_id="-", modo="blind"):
    w, _ = _wallet(nome)
    aid = None if asset_id in ("-", "") else asset_id
    scade = int(time.time()) + SCADENZA
    if modo == "witness":
        r = w.witness_receive(aid, rgb_lib.Assignment.ANY(), scade, [PROXY], CONFERME)
    else:
        r = w.blind_receive(aid, rgb_lib.Assignment.ANY(), scade, [PROXY], CONFERME)
    print(r.invoice)
    print(f"# {modo}, recipient {r.recipient_id[:20]}…, scade {time.strftime('%Y-%m-%d %H:%M', time.localtime(r.expiration_timestamp))}", file=sys.stderr)


def invia(nome, asset_id, quantita, fattura_str):
    dati = rgb_lib.Invoice(fattura_str).invoice_data()
    if dati.asset_id and dati.asset_id != asset_id:
        _die(f"la fattura e' per un altro asset ({dati.asset_id})")
    if dati.network != RETE:
        _die(f"la fattura e' per un'altra rete ({dati.network})")
    tipo = rgb_lib.RecipientInfo(dati.recipient_id).recipient_type()
    witness = rgb_lib.WitnessData(amount_sat=SATS_WITNESS, blinding=None) \
        if tipo == rgb_lib.RecipientType.WITNESS else None
    endpoint = list(dati.transport_endpoints) or [PROXY]
    w, on = _wallet(nome)
    destinatario = rgb_lib.Recipient(
        recipient_id=dati.recipient_id, witness_data=witness,
        assignment=rgb_lib.Assignment.FUNGIBLE(int(quantita)),
        transport_endpoints=endpoint)
    esito = w.send(on, {asset_id: [destinatario]}, False, FEE, CONFERME,
                   int(time.time()) + SCADENZA)
    print(f"✓ consignment depositato sul proxy ({tipo}), txid {esito.txid}")
    print(f"  {ESPLORA}{esito.txid}")
    print("  la transazione parte quando chi riceve fa ACK: `aggiorna` da tutti e due i lati")


def aggiorna(nome):
    w, on = _wallet(nome)
    esito = w.refresh(on, None, [], False)
    if not esito:
        print("nessun trasferimento da aggiornare")
    for idx, r in esito.items():
        print(f"  trasferimento {idx}: {r.updated_status or 'invariato'}"
              + (f"  ✗ {r.failure}" if r.failure else ""))


def trasferimenti(nome, asset_id=None):
    w, _ = _wallet(nome, online=False)
    for t in w.list_transfers(asset_id):
        quando = time.strftime("%Y-%m-%d %H:%M", time.localtime(t.updated_at))
        print(f"  #{t.idx} {quando} {t.kind} {t.status}  {t.assignments}  "
              f"tx {(t.txid or '-')[:16]}")


def btc(nome, indirizzo_dest, sats):
    w, on = _wallet(nome)
    txid = w.send_btc(on, indirizzo_dest, int(sats), FEE, False)
    print(f"✓ mandati {sats} sats, txid {txid}\n  {ESPLORA}{txid}")


def backup(nome):
    c = _chiavi(nome)
    w, _ = _wallet(nome, online=False)
    os.makedirs(BACKUP, mode=0o700, exist_ok=True)
    percorso = os.path.join(BACKUP, f"{nome}-{time.strftime('%Y%m%d-%H%M')}.rgb-backup")
    w.backup(percorso, c["password_backup"])
    os.chmod(percorso, 0o600)   # rgb-lib lo scrive con l'umask: qui dentro c'e' lo stash
    print(f"✓ backup di «{nome}»: {percorso} ({os.path.getsize(percorso)} byte)")
    print("  si apre solo con la password_backup di chiavi.json: i due file viaggiano insieme")


def ripristina(nome, percorso):
    c = _chiavi(nome)
    dest = os.path.join(_cartella(nome), "wallet")
    if os.path.exists(dest) and os.listdir(dest):
        _die(f"{dest} non e' vuota: un ripristino sopra uno stash vivo perde asset")
    rgb_lib.restore_backup(percorso, c["password_backup"], dest)
    print(f"✓ stash di «{nome}» ripristinato in {dest}")


COMANDI = {f.__name__: f for f in (
    nuovo, indirizzo, saldo, utxo, emetti, fattura, invia, aggiorna,
    trasferimenti, btc, backup, ripristina)}

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in COMANDI:
        print(__doc__)
        sys.exit(2)
    try:
        COMANDI[sys.argv[1]](*sys.argv[2:])
    except TypeError as e:
        _die(f"argomenti sbagliati per «{sys.argv[1]}»: {e}")
    except rgb_lib.RgbLibError as e:
        _die(f"rgb-lib dice: {e}")
