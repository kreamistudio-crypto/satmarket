"""Schnorr BIP-340 in Python puro, SOLO per i banchi di prova.

Il server firma e verifica con `coincurve` (libsecp256k1), e senza quel
pacchetto NON crede a niente (fail-closed, vedi `verifica_firma_nostr`).
In CI pero' coincurve non c'e' — `prove.py` importa solo quel che il suo
passo installa, e i collaudi nemmeno — quindi una prova che volesse
verificare una firma VERA, prodotta dal client con nostr-tools, non
aveva con cosa farlo. Questo modulo e' quel «con cosa»: la ricetta di
riferimento del BIP-340, lenta (aritmetica affine, un'inversione per
passo) ma di sola libreria standard, che i banchi montano al posto di
`ChiavePubblicaNostr` del server per far girare il giudice VERO sui
byte veri. Verificato contro coincurve nei due versi dove coincurve c'e'
(`prove_contanti_a_mano`).

⚠️ NON SI USA NEL SERVER: la' vale la libreria compilata, e la scelta di
non credere a una firma senza di lei e' scritta e provata.
"""
import hashlib

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _hash_etichettato(etichetta: str, dati: bytes) -> bytes:
    t = hashlib.sha256(etichetta.encode()).digest()
    return hashlib.sha256(t + t + dati).digest()


def _somma(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    if p1[0] == p2[0] and p1[1] != p2[1]:
        return None
    if p1 == p2:
        lam = (3 * p1[0] * p1[0] * pow(2 * p1[1], P - 2, P)) % P
    else:
        lam = ((p2[1] - p1[1]) * pow(p2[0] - p1[0], P - 2, P)) % P
    x3 = (lam * lam - p1[0] - p2[0]) % P
    return (x3, (lam * (p1[0] - x3) - p1[1]) % P)


def _moltiplica(punto, k: int):
    r = None
    for i in range(256):
        if (k >> i) & 1:
            r = _somma(r, punto)
        punto = _somma(punto, punto)
    return r


def _alza_x(x: int):
    if x >= P:
        return None
    y2 = (pow(x, 3, P) + 7) % P
    y = pow(y2, (P + 1) // 4, P)
    if pow(y, 2, P) != y2:
        return None
    return (x, y if y % 2 == 0 else P - y)


def _byte_x(punto) -> bytes:
    return punto[0].to_bytes(32, "big")


def pubblica(sk: bytes) -> bytes:
    """La chiave pubblica x-only (32 byte) di una privata (32 byte)."""
    d = int.from_bytes(sk, "big")
    if not 1 <= d < N:
        raise ValueError("chiave privata fuori misura")
    return _byte_x(_moltiplica(G, d))


def firma(sk: bytes, msg: bytes, aux: bytes = b"\x00" * 32) -> bytes:
    """La firma BIP-340 (64 byte) di `msg` (32 byte) con `sk` (32 byte)."""
    if len(msg) != 32:
        raise ValueError("il messaggio e' un hash di 32 byte")
    d0 = int.from_bytes(sk, "big")
    if not 1 <= d0 < N:
        raise ValueError("chiave privata fuori misura")
    pt = _moltiplica(G, d0)
    d = d0 if pt[1] % 2 == 0 else N - d0
    t = bytes(a ^ b for a, b in zip(d.to_bytes(32, "big"), _hash_etichettato("BIP0340/aux", aux)))
    k0 = int.from_bytes(_hash_etichettato("BIP0340/nonce", t + _byte_x(pt) + msg), "big") % N
    if k0 == 0:
        raise ValueError("nonce nullo")
    r = _moltiplica(G, k0)
    k = k0 if r[1] % 2 == 0 else N - k0
    e = int.from_bytes(_hash_etichettato("BIP0340/challenge", _byte_x(r) + _byte_x(pt) + msg), "big") % N
    return _byte_x(r) + ((k + e * d) % N).to_bytes(32, "big")


def verifica(pub: bytes, msg: bytes, sig: bytes) -> bool:
    """Vero se `sig` (64 byte) e' la firma di `msg` (32 byte) con `pub` (32 byte)."""
    try:
        if len(pub) != 32 or len(msg) != 32 or len(sig) != 64:
            return False
        pt = _alza_x(int.from_bytes(pub, "big"))
        r = int.from_bytes(sig[:32], "big")
        s = int.from_bytes(sig[32:], "big")
        if pt is None or r >= P or s >= N:
            return False
        e = int.from_bytes(_hash_etichettato("BIP0340/challenge", sig[:32] + pub + msg), "big") % N
        rr = _somma(_moltiplica(G, s), _moltiplica(pt, N - e))
        return rr is not None and rr[1] % 2 == 0 and rr[0] == r
    except Exception:
        return False


class ChiaveXOnly:
    """Il calco di `coincurve.PublicKeyXOnly` che serve al server:
    `ChiaveXOnly(pub_bytes).verify(sig, msg)`. I banchi lo montano al
    posto di `ChiavePubblicaNostr` dove coincurve non c'e'."""

    def __init__(self, pub: bytes):
        if len(pub) != 32 or _alza_x(int.from_bytes(pub, "big")) is None:
            raise ValueError("chiave pubblica non valida")
        self.pub = bytes(pub)

    def verify(self, sig: bytes, msg: bytes) -> bool:
        return verifica(self.pub, msg, sig)


if __name__ == "__main__":
    import os
    sk = os.urandom(32)
    pub = pubblica(sk)
    m = hashlib.sha256(b"prova").digest()
    s = firma(sk, m, os.urandom(32))
    assert verifica(pub, m, s)
    assert not verifica(pub, hashlib.sha256(b"altro").digest(), s)
    print("ok", pub.hex()[:16])
