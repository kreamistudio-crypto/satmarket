# -*- coding: utf-8 -*-
"""
GLI ALLEGATI DELLA CHAT, SUL SERVER VERO (16 ott 2026, cantiere
barcode-paycode, parte C, richiesta di Andrea).

Nella chat dello scambio si mandano foto e PDF CIFRATI SUL TELEFONO: al
server arriva solo `iv || cifrato`, la chiave viaggia dentro il
messaggio della chat. `prove.py` (`prove_allegati_chat`) fa girare la
cifratura vera e i due telefoni in node; qui girano le ROTTE VERE —
`/api/p2p/chat/allegato`, `/api/p2p/chat/allegato/leggi`,
`/api/p2p/moderazione/chat/allegato` — su un database usa-e-getta, con
l'autenticazione VERA:

   1. chi manda e chi riceve: il file entra (il corpo letto a pezzi,
      lo scambio nell'intestazione), torna IDENTICO a tutte e due le
      parti, e mai a un estraneo o a un altro scambio;
   2. i tetti: troppo piccolo, troppo grande, dieci per parte, il
      cassetto pieno, un id storto;
   3. il journal: una riga col solo peso, niente id, niente byte;
   4. il moderatore: solo dopo aver preso la disputa, e solo i file di
      quello scambio;
   5. la fine: a scambio finito il file sparisce DAL FILE del cassetto,
      non solo dall'elenco, e chi lo chiede sente «non c'e' piu'»;
   6. la leva della chat spenta: niente file nuovi;
   7. (16 ott 2026, cantiere pdf-allegati) i tetti di Andrea — il PDF fino
      a 20 MB, 40 MB per persona in ogni scambio —, l'avviso nel gruppo
      degli admin quando il cassetto passa l'80 % (una volta, riarmato
      sotto il 60 %), e lo spazio dei file cancellati che torna DAVVERO
      al disco (auto_vacuum incrementale).

NON TOCCA NIENTE DI VERO: il config di cartone di
`collaudo_pagamento_p2p`, niente Telegram, niente relay, niente
coordinatore. I «file» qui sono byte a caso: il server non li apre.

USO:  python collaudo_allegati_chat.py
"""

import asyncio
import contextlib
import io
import json
import os
import sys

import collaudo_pagamento_p2p as banco
import collaudo_chat_scambio as cs

prova = banco.prova


class Corpo(banco.Busta):
    """Una richiesta finta coi byte nudi nel corpo, letti a pezzi come
    li legge Starlette."""

    def __init__(self, dati, pezzo=65536):
        super().__init__({})
        self.grezzo, self.pezzo = dati, pezzo

    async def stream(self):
        for i in range(0, len(self.grezzo), self.pezzo):
            yield self.grezzo[i:i + self.pezzo]


async def manda(chi, ordine, dati, pezzo=65536):
    try:
        r = await banco.SRV.chat_allegato_p2p(Corpo(dati, pezzo), x_chat_ordine=ordine, **cs.ACCESSO[chi])
    except banco.SRV.HTTPException as e:
        return cs.Rifiuto((e.status_code, str(e.detail)))
    return json.loads(r.body)


async def ritira(chi, ordine, ident, mod=False):
    fn = banco.SRV.moderazione_chat_allegato_p2p if mod else banco.SRV.chat_allegato_leggi_p2p
    try:
        r = await fn(banco.Busta({"ordine": ordine, "id": ident}), **cs.ACCESSO[chi])
    except banco.SRV.HTTPException as e:
        return cs.Rifiuto((e.status_code, str(e.detail)))
    return r.body if r.media_type == "application/octet-stream" else json.loads(r.body)


async def giro():
    SRV = banco.SRV
    SRV.P2P_EVENTI_SEGRETO = cs.SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}

    async def notifica_finta(chi, testo, bottone=None, *a, **k):
        cs.DETTI.append((chi, testo, bottone))
    SRV.notifica = notifica_finta
    for tg, nome in ((cs.TG_V, "Venditore"), (cs.TG_C, "Compratore"),
                     (cs.ESTRANEO, "Estraneo"), (cs.ADMIN, "Admin")):
        cs.ACCESSO[tg] = {"x_tg_init_data": f"collaudo:{tg}:{nome}", "barattolo_sessione": ""}
    V, C, X, ADMIN = cs.TG_V, cs.TG_C, cs.ESTRANEO, cs.ADMIN
    kv, kc = cs.chiave(0x10), cs.chiave(0x30)
    o = await cs.scambio(41, V, C, kv, kc)
    altro = await cs.scambio(42, V, C, cs.chiave(0x11), cs.chiave(0x31))
    foto = os.urandom(300 * 1024)

    print("\n1) chi manda e chi riceve")
    giornale = io.StringIO()
    with contextlib.redirect_stdout(giornale):
        r = await manda(V, o, foto)
    ident = r.get("id", "")
    prova("il file entra e torna un id a caso di 32 esadecimali", (True, 32),
          (r.get("ok"), len(ident) if all(c in "0123456789abcdef" for c in ident) else 0))
    prova("...chi l'ha mandato lo riprende IDENTICO", True, await ritira(V, o, ident) == foto)
    prova("...l'altra parte lo riprende IDENTICO", True, await ritira(C, o, ident) == foto)
    prova("un estraneo no: 403", 403, cs.no(await ritira(X, o, ident)))
    prova("lo stesso id chiesto da un altro scambio: 404", 404, cs.no(await ritira(C, altro, ident)))
    prova("un id storto: 404", 404, cs.no(await ritira(C, o, "../" + ident)))
    prova("un estraneo non manda: 403", 403, cs.no(await manda(X, o, foto)))
    prova("(un file anche nell'altro scambio, che restera' vivo)", True,
          (await manda(C, altro, os.urandom(128))).get("ok"))
    prova("uno scambio storto nell'intestazione: 400", 400, cs.no(await manda(V, "x' OR 1=1", foto)))

    print("\n3) il journal")
    riga = giornale.getvalue()
    prova("una riga col solo peso: lo scambio, i KB, niente id e niente byte",
          (True, False), (f"📎 Chat P2P: un allegato sullo scambio {o[:8]}, 300 KB" in riga,
                          ident in riga))

    print("\n2) i tetti")
    prova("troppo piccolo (meno di iv e sigillo): 400", 400, cs.no(await manda(V, o, b"x" * 20)))
    prova("troppo grande (20 MB e un byte oltre il sigillo): 413", 413,
          cs.no(await manda(V, o, b"x" * (SRV.P2P_CHAT_ALLEGATO_MAX + 1))))
    prova("...e il tetto vale anche a pezzi piccoli: il corpo si ferma prima", 413,
          cs.no(await manda(V, o, b"x" * (SRV.P2P_CHAT_ALLEGATO_MAX + 1), pezzo=1000)))
    prova("20 MB esatti col sigillo entrano", True,
          (await manda(C, o, b"y" * SRV.P2P_CHAT_ALLEGATO_MAX)).get("ok"))
    prova("...un secondo da 20 MB della stessa persona no: i 40 MB a persona (409)", 409,
          cs.no(await manda(C, o, b"y" * SRV.P2P_CHAT_ALLEGATO_MAX)))
    for _ in range(SRV.P2P_CHAT_ALLEGATI_PARTE - 1):
        await manda(V, o, os.urandom(64))
    prova("al file numero undici della stessa parte: 409", 409, cs.no(await manda(V, o, os.urandom(64))))
    prova("...l'altra parte ne manda ancora", True, (await manda(C, o, os.urandom(64))).get("ok"))
    prima = SRV.P2P_CHAT_ALLEGATI_CASSETTO
    SRV.P2P_CHAT_ALLEGATI_CASSETTO = 1024
    prova("il cassetto pieno: 507", 507, cs.no(await manda(C, altro, os.urandom(2048))))
    SRV.P2P_CHAT_ALLEGATI_CASSETTO = prima
    await asyncio.sleep(0.3)

    print("\n7) l'avviso del cassetto quasi pieno")
    tutto = lambda: int(cs.cassetto("SELECT COALESCE(SUM(peso), 0) FROM allegati")[0][0])
    AVVISATI = []

    async def admin_finto(testo, bottone=None, argomento=""):
        AVVISATI.append((testo, argomento))
    SRV.notifica_admin = admin_finto
    avvisi = lambda: [t for t, a in AVVISATI if a == "errori" and "Il cassetto dei file della chat (scambi e ordini) è quasi pieno" in t]
    SRV._CASSETTO_AVVISATO["su"] = False
    n0 = len(avvisi())
    SRV.P2P_CHAT_ALLEGATI_CASSETTO = tutto() + 10_000          # oltre l'80 % col prossimo file
    await manda(C, altro, os.urandom(500))
    await asyncio.sleep(0.3)
    prova("passato l'80 %: UN avviso agli admin, col testo che dice quanto", 1, len(avvisi()) - n0)
    await manda(C, altro, os.urandom(500))
    await asyncio.sleep(0.3)
    prova("...il file dopo non ne manda un secondo", 1, len(avvisi()) - n0)
    SRV.P2P_CHAT_ALLEGATI_CASSETTO = tutto() * 3               # sotto il 60 %: si riarma
    await manda(C, altro, os.urandom(500))
    await asyncio.sleep(0.3)
    prova("...sceso sotto il 60 % si riarma", False, SRV._CASSETTO_AVVISATO["su"])
    SRV.P2P_CHAT_ALLEGATI_CASSETTO = tutto() + 10_000
    await manda(C, altro, os.urandom(500))
    await asyncio.sleep(0.3)
    prova("...e ripassato l'80 % lo ridice", 2, len(avvisi()) - n0)
    SRV.P2P_CHAT_ALLEGATI_CASSETTO = prima
    SRV._CASSETTO_AVVISATO["su"] = False

    print("\n4) il moderatore")
    await cs.evento(o, "hold-invoice-paid", "seller", "active", kc, kv)
    await cs.evento(o, "dispute-opened", "seller", "", kc, kv)
    for _ in range(50):
        con = banco.con_db()
        c_e = con.execute("SELECT 1 FROM p2p_dispute WHERE ordine=?", (o,)).fetchone()
        con.close()
        if c_e:
            break
        await asyncio.sleep(0.1)
    prova("prima di prendere la disputa il moderatore non lo ritira: 409", 409,
          cs.no(await ritira(ADMIN, o, ident, mod=True)))
    prova("chi non e' moderatore: 403", 403, cs.no(await ritira(V, o, ident, mod=True)))
    con = banco.con_db()
    con.execute("UPDATE p2p_dispute SET stato='presa', presa_da=?, presa_il=? WHERE ordine=?",
                (ADMIN, cs.adesso(), o))
    con.commit()
    con.close()
    prova("presa la disputa, lo ritira IDENTICO (lo apre solo con la chiave della chat)", True,
          await ritira(ADMIN, o, ident, mod=True) == foto)
    prova("...ma non un file di un altro scambio", 404,
          cs.no(await ritira(ADMIN, altro, ident, mod=True)))

    print("\n5) la fine")
    pezzo_foto = foto[1000:1064]
    prova("(prima della fine i byte stanno nel file del cassetto)", True,
          pezzo_foto in open(SRV.DB_CHAT, "rb").read())
    # la misura PRIMA degli eventi: e' l'evento che chiude a far girare la scopa
    peso_prima = os.path.getsize(SRV.DB_CHAT)
    await cs.evento(o, "released", "mostro", "admin", kc, kv)
    await cs.evento(o, "success", "mostro", "", kc, kv)
    await asyncio.sleep(0.3)
    SRV._chat_p2p_spazza(o)
    peso_dopo = os.path.getsize(SRV.DB_CHAT)
    prova("LO SPAZIO TORNA AL DISCO: il cassetto e' incrementale, nessuna pagina libera resta, e il file "
          "si restringe di almeno i 20 MB del PDF cancellato", (2, 0, True),
          (int(cs.cassetto("PRAGMA auto_vacuum")[0][0]), int(cs.cassetto("PRAGMA freelist_count")[0][0]),
           peso_prima - peso_dopo >= 20 * 1024 * 1024))
    prova("a scambio finito: nessuna riga di quello scambio nel cassetto", 0,
          len(cs.cassetto("SELECT id FROM allegati WHERE ordine=?", o)))
    prova("...e i byte non sono piu' nel file (secure_delete)", False,
          pezzo_foto in open(SRV.DB_CHAT, "rb").read())
    prova("...chi lo chiede sente che la chat e' finita", (True, False),
          ((await ritira(C, o, ident)).get("finita"), (await ritira(C, o, ident)).get("aperta")))
    prova("...e non se ne mandano altri: 409", 409, cs.no(await manda(C, o, os.urandom(64))))
    prova("l'altro scambio, ancora vivo, i suoi li tiene", True,
          len(cs.cassetto("SELECT id FROM allegati WHERE ordine=?", altro)) > 0)

    print("\n6) la leva della chat spenta")
    SRV.P2P_CHAT_SCAMBIO = False
    prova("niente file nuovi", 409, cs.no(await manda(C, altro, os.urandom(64))))
    SRV.P2P_CHAT_SCAMBIO = True
    prova("riaccesa, riprende", True, (await manda(C, altro, os.urandom(64))).get("ok"))


def main():
    banco.avvio()
    banco.semina()
    banco.SRV.P2P_RESPIRO_S = 1
    banco.SRV.P2P_RESPIRO_NOME_S = 1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
