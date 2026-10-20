# -*- coding: utf-8 -*-
"""
I CERTIFICATI DEI RELAY SI VERIFICANO, SUL SERVER VERO (20 ott 2026,
cantiere certificati-relay, decisione di Andrea).

Un relay `wss://` DI CARTONE sul loopback, con un certificato fatto in
casa (autofirmato, per il solo nome `localhost`), e le porte vere del
server — `chiedi_relay_dm` e `invia_evento_relay`, che passano da
`create_connection`, cioe' dall'involucro `_apri_websocket`:

  1. IL CERTIFICATO FATTO IN CASA SI RIFIUTA: la lettura torna «nessuna
     risposta» e la scrittura «non presa», come per un relay muto, e nel
     journal c'e' la riga 🔐 — UNA, anche a tre tentativi;
  2. LA CONTROPROVA: con quel certificato fra le CA fidate
     (WEBSOCKET_CLIENT_CA_BUNDLE) la stretta di mano TLS passa — il relay
     di cartone la vede compiuta — e la riga 🔐 non c'e': il rifiuto di
     prima era il certificato, non la porta;
  3. SUL NOME: con la CA fidata ma bussando a `127.0.0.1` (il certificato
     dice solo `localhost`) si rifiuta di nuovo, con la sua riga.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta prima
dell'import del server; il relay e' un thread su 127.0.0.1, la gabbia
dei collaudi lascia passare solo quello.

USO:  python collaudo_certificati_relay.py
"""

import datetime
import os
import socket
import ssl
import sys
import tempfile
import threading
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
RIGHE = []
STRETTE = []      # le strette di mano TLS che il relay di cartone ha visto compiute


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-certificati-")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = os.path.join(tmp, "usa-e-getta.db")
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    def stampa(*a, **k):
        RIGHE.append(" ".join(str(x) for x in a))
        print(*a, **k)
    server.print = stampa
    return tmp


def certificato_fatto_in_casa(cartella):
    """Un certificato autofirmato per il SOLO nome `localhost` (nessun IP
    fra i nomi alternativi): chiave e certificato in due file."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    chiave = ec.generate_private_key(ec.SECP256R1())
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    adesso = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(nome).issuer_name(nome)
            .public_key(chiave.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(adesso - datetime.timedelta(days=1))
            .not_valid_after(adesso + datetime.timedelta(days=30))
            .add_extension(x509.SubjectAlternativeName(
                [x509.DNSName("localhost")]), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                           critical=True)
            .sign(chiave, hashes.SHA256()))
    pem_cert = os.path.join(cartella, "relay-di-cartone.crt")
    pem_chiave = os.path.join(cartella, "relay-di-cartone.key")
    with open(pem_cert, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(pem_chiave, "wb") as f:
        f.write(chiave.private_bytes(serialization.Encoding.PEM,
                                     serialization.PrivateFormat.PKCS8,
                                     serialization.NoEncryption()))
    return pem_cert, pem_chiave


def relay_di_cartone(pem_cert, pem_chiave):
    """Un «relay» che fa solo la stretta di mano TLS e poi chiude: quanto
    basta per vedere se il client l'ha accettata. Ogni connessione nel suo
    thread, chiusa dallo stesso thread."""
    contesto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    contesto.load_cert_chain(pem_cert, pem_chiave)
    ascolto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ascolto.bind(("127.0.0.1", 0))
    ascolto.listen(8)

    def servi(grezza):
        try:
            grezza.settimeout(5)
            tls = contesto.wrap_socket(grezza, server_side=True)
            STRETTE.append("compiuta")
            try:
                tls.recv(4096)
            except Exception:
                pass
            tls.close()
        except Exception:
            grezza.close()

    def accogli():
        while True:
            try:
                c, _ = ascolto.accept()
            except Exception:
                return
            threading.Thread(target=servi, args=(c,), daemon=True).start()
    threading.Thread(target=accogli, daemon=True).start()
    return ascolto.getsockname()[1]


def righe_cert(relay):
    return [r for r in RIGHE if r.startswith(f"🔐 Relay {relay}: certificato non valido")]


def main():
    print("=" * 58)
    print("  I CERTIFICATI DEI RELAY SI VERIFICANO — il giro vero")
    print("=" * 58)
    tmp = avvio()
    pem_cert, pem_chiave = certificato_fatto_in_casa(tmp)
    porta = relay_di_cartone(pem_cert, pem_chiave)
    NOME = f"wss://localhost:{porta}"
    IP = f"wss://127.0.0.1:{porta}"
    CHIAVE = "ab" * 32
    os.environ.pop("WEBSOCKET_CLIENT_CA_BUNDLE", None)
    prova("il server non tiene CERT_NONE: le porte verso i relay usano "
          "SSLOPT_RELAY, cioe' CERT_REQUIRED", ssl.CERT_REQUIRED,
          SRV.SSLOPT_RELAY["cert_reqs"])

    print("\n[1) il certificato fatto in casa si rifiuta]")
    esiti = [SRV.chiedi_relay_dm(NOME, CHIAVE),
             SRV.invia_evento_relay(NOME, {"id": "e" * 64, "kind": 1}),
             SRV.chiedi_relay_dm(NOME, CHIAVE)]
    prova("la lettura dice «nessuna risposta» e la scrittura «non presa», come "
          "un relay muto", [None, False, None], esiti)
    prova("...nessuna stretta di mano compiuta dal relay di cartone", [], STRETTE)
    prova("...e nel journal la riga 🔐, UNA a tre tentativi", 1, len(righe_cert(NOME)))
    prova("...che dice perche'", True,
          any("self-signed" in r or "self signed" in r for r in righe_cert(NOME)))

    print("\n[2) la controprova: con la CA fidata la stretta passa]")
    os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = pem_cert
    try:
        SRV._CERT_RIFIUTATI.clear()
        prima = len(RIGHE)
        SRV.chiedi_relay_dm(NOME, CHIAVE)
        prova("il relay di cartone vede la stretta compiuta, e la riga 🔐 non "
              "c'e': il rifiuto di prima era il certificato",
              [True, []], [len(STRETTE) >= 1,
                           [r for r in RIGHE[prima:] if r.startswith("🔐")]])

        print("\n[3) sul nome: la CA e' fidata, ma il nome non e' quello]")
        compiute = len(STRETTE)
        esito = SRV.chiedi_relay_dm(IP, CHIAVE)
        prova("bussando a 127.0.0.1 (il certificato dice solo localhost): "
              "rifiutato, con la sua riga", [None, 1, compiute],
              [esito, len(righe_cert(IP)), len(STRETTE)])
    finally:
        os.environ.pop("WEBSOCKET_CLIENT_CA_BUNDLE", None)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
