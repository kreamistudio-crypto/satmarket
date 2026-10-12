# -*- coding: utf-8 -*-
"""
CHI ANNULLA LO SENTE ANCHE LUI, SUL SERVER VERO (7 ott 2026).

Il caso di Andrea: prende l'ordine d'acquisto di Alan, blocca i sats in
garanzia, annulla. Ad Alan arriva su Telegram «Andrea ha annullato lo
scambio», a lui niente: la regola «mai a chi ha fatto il gesto» valeva
anche per l'annullo. Adesso chi annulla — chi si ritira dopo aver preso,
chi annulla dopo la presa il suo ordine, chi accetta l'annullo d'accordo
— riceve il suo avviso; e chi vende, se nel giro aveva la garanzia
pagata, legge «I sats che avevi bloccato in garanzia sono tornati a te»,
anche quando a chiudere e' l'altro, il moderatore o una scadenza.

`prove.py` difende i giudici estratti (`prove_avviso_chi_annulla`). Qui
gira la ROTTA VERA, `/api/p2p/evento`, coi suoi task e la sua pausa fra
un invio e l'altro, su un database usa-e-getta, e si guarda cosa parte:

  1. tutti i casi di chiusura della tabella, con e senza sats bloccati;
  2. il ritiro di un ordine mai preso: muto, com'era;
  3. i doppioni: il retry di mostrod, la riserva del libro che scade
     dopo il coordinatore, e il libro che ha parlato prima;
  4. chi ha gli avvisi P2P spenti, e la cauzione di chi si ritira.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram (le notifiche finiscono in
una lista), niente relay, niente coordinatore.

USO:  python collaudo_avviso_chi_annulla.py
"""

import asyncio
import json
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
TORNATI = " I sats che avevi bloccato in garanzia sono tornati a te."
# il 38385 come lo tiene la fotografia del libro: la cauzione accesa per
# chi prende, solo «Contanti», il timeout che non brucia
INFO_38385 = {"kind": 38385, "tags": [["bond_enabled", "true"], ["bond_apply_to", "take"],
                                      ["bond_only_payment_methods", "Contanti"],
                                      ["bond_slash_on_waiting_timeout", "false"]]}
V, C = banco.VENDE, banco.COMPRA
KV, KC = banco.CHIAVE_VENDE, banco.CHIAVE_COMPRA


def ora(base):
    """L'orologio di un ordine: `t0 + base` cade cinque minuti fa, e
    la scadenza a `base + 1000` resta dentro i 900 s che la rotta
    accetta (P2P_EVENTO_OROLOGIO_S): l'ora e' parte della chiave
    dell'idempotenza e la rotta non l'aggiusta."""
    return int(time.time()) - 300 - base


def ordine(n):
    return f"5a1e0000-c1c1-4a2b-9c3d-{n:012d}"


def semina_ordine(o, lato, metodi=("SEPA",)):
    """L'ordine nel libro, in vetrina: un `buy` lo pubblica chi compra,
    un `sell` chi vende — i numeri li ha gia' scritti il libro."""
    con = banco.con_db()
    maker = C if lato == "buy" else V
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "sats,euro,metodi) VALUES(?,?,?,'pending',?,1,15000,'10,00 €',?)",
                (o, maker, int(time.time()), lato, json.dumps(list(metodi))))
    con.commit()
    con.close()


def busta(o, azione, ts, attore, dettaglio="", buyer=KC, seller=KV, segreto=SEGRETO):
    b = banco.Busta({"v": 1, "order": o, "action": azione, "ts": ts,
                     "buyer": buyer, "seller": seller, "actor": attore,
                     "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {segreto}"} if segreto else {}
    return b


async def posta(b, attesa=0.8):
    """Il POST di mostrod alla rotta vera, poi una pausa che lascia
    finire il task dell'invio (0,2 s fra un avviso e l'altro)."""
    try:
        r = json.loads((await banco.SRV.evento_p2p(b)).body)
    except Exception as e:
        r = getattr(e, "status_code", type(e).__name__)
    await asyncio.sleep(attesa)
    return r


async def fino_a(o, passo, ts):
    """Lo scambio fino al passo che serve, coi POST veri. `passo`:
    'preso' (presa e basta) o 'garanzia' (presa e garanzia pagata). Il
    respiro della presa si aspetta: la frase della presa deve partire,
    o il ritorno in vetrina a chi ha pubblicato tacerebbe (presa mai
    detta), e non e' questo che si prova."""
    r = banco.SRV
    lato = _lato(o)
    if lato == "buy":          # ha pubblicato chi compra: prende chi vende
        await posta(busta(o, "taken", ts, "seller", "hold-next"),
                    attesa=r.P2P_RESPIRO_S + 1.2)
        if passo == "garanzia":
            await posta(busta(o, "hold-invoice-paid", ts + 10, "seller", "invoice-next"))
    else:                      # ha pubblicato chi vende: prende chi compra
        await posta(busta(o, "taken", ts, "buyer", "invoice-next"),
                    attesa=r.P2P_RESPIRO_S + 1.2)
        if passo == "garanzia":
            await posta(busta(o, "hold-invoice-paid", ts + 10, "seller", "active"))
    del banco.DETTO[:]


def _lato(o):
    con = banco.con_db()
    r = con.execute("SELECT lato FROM p2p_ordini WHERE ordine=?", (o,)).fetchone()
    con.close()
    return r["lato"] if r else ""


def detto():
    return sorted(banco.DETTO)


def timbri(o, momento):
    con = banco.con_db()
    r = [x[0] for x in con.execute(
        "SELECT tg_id FROM p2p_avvisi WHERE ordine=? AND momento=? ORDER BY tg_id",
        (o, momento))]
    con.close()
    return r


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    # I NOMI: la frase dice il nome dell'altra parte solo se la pagina
    # dello scambio lo mostra (`_nome_altro_p2p`, «LE PARTI SI VEDONO»).
    # Qui nessuno dichiara la presa dal telefono (`preso_da` resta 0),
    # quindi chi ha PUBBLICATO legge «chi compra» / «chi vende»; chi ha
    # PRESO, dal 12 ott 2026 (chi-e-l-altro), vede chi ha pubblicato
    # appena mostrod nomina le due parti: nelle sue frasi c'e' il NOME
    # che il banco semina («Carlo» per C, «Vera» per V), in quelle di
    # chi ha pubblicato il ruolo generico («chi compra» / «chi vende»)

    print("\n1) IL CASO DI ANDREA: chi vende prende un acquisto, blocca i sats, si ritira")
    o = ordine(1)
    t0 = ora(0)
    semina_ordine(o, "buy")
    await fino_a(o, "garanzia", t0)
    r = await posta(busta(o, "canceled", t0 + 40, "seller", "republished"))
    prova("il ritiro entra: nuovo", {"ok": True, "nuovo": True}, r)
    prova("partono DUE avvisi: a chi ha pubblicato il ritorno in vetrina, a chi "
          "si e' ritirato il suo, coi sats tornati",
          [(V, f"❌ <b>Hai annullato lo scambio con Carlo.</b>{TORNATI}"),
           (C, f"🔄 <b>Chi vende ha annullato lo scambio.</b> Il tuo ordine è "
               "tornato in vetrina: non devi fare niente.")], detto())
    print("   (le due frasi, come arrivano:)")
    for chi, t in detto():
        print(f"     → {chi}: {t}")

    print("\n2) lo stesso ritiro PRIMA di bloccare la garanzia")
    o = ordine(2)
    t0 = ora(100)
    semina_ordine(o, "buy")
    await fino_a(o, "preso", t0 + 100)
    await posta(busta(o, "canceled", t0 + 140, "seller", "republished"))
    prova("a chi si ritira la frase senza sats", f"❌ <b>Hai annullato lo scambio con Carlo.</b>",
          dict(banco.DETTO).get(V))

    print("\n3) chi ha PUBBLICATO (e vende) annulla dopo aver bloccato")
    o = ordine(3)
    t0 = ora(200)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 200)
    await posta(busta(o, "canceled", t0 + 240, "seller", ""))
    prova("lui coi sats tornati, chi compra con la frase di sempre",
          [(V, f"❌ <b>Hai annullato lo scambio con chi compra.</b>{TORNATI}"),
           (C, f"❌ <b>Vera ha annullato lo scambio.</b> I sats eventualmente "
               "in garanzia tornano a chi vende.")], detto())

    print("\n4) chi ha pubblicato (e compra) annulla: 3b, a chi vende «sono tornati a te»")
    o = ordine(4)
    t0 = ora(300)
    semina_ordine(o, "buy")
    await fino_a(o, "garanzia", t0 + 300)
    await posta(busta(o, "canceled", t0 + 340, "buyer", ""))
    prova("chi compra sente il suo annullo, chi vende i sats tornati",
          [(V, f"❌ <b>Carlo ha annullato lo scambio.</b>{TORNATI}"),
           (C, f"❌ <b>Hai annullato lo scambio con chi vende.</b>")],
          detto())

    print("\n5) l'annullo D'ACCORDO, nei due versi")
    o = ordine(5)
    t0 = ora(400)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 400)
    await posta(busta(o, "cancel-requested", t0 + 430, "seller", ""))
    prova("la richiesta di chi vende arriva solo a chi compra", [C],
          [chi for chi, _ in detto()])
    del banco.DETTO[:]
    await posta(busta(o, "canceled", t0 + 440, "buyer", "cooperative"))
    prova("chi compra ACCETTA: lo sente anche lui, con le parole di Andrea",
          [(V, f"❌ <b>Chi compra ha accettato di annullare: lo scambio è annullato.</b>"
               f"{TORNATI}"),
           (C, f"❌ <b>Hai accettato di annullare: lo scambio con "
               f"Vera è annullato.</b>")], detto())
    o = ordine(6)
    t0 = ora(500)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 500)
    await posta(busta(o, "cancel-requested", t0 + 530, "buyer", ""))
    del banco.DETTO[:]
    await posta(busta(o, "canceled", t0 + 540, "seller", "cooperative"))
    prova("chi vende ACCETTA: i sats tornano a lui, nella sua frase",
          [(V, f"❌ <b>Hai accettato di annullare: lo scambio con chi compra è annullato.</b>"
               f"{TORNATI}"),
           (C, f"❌ <b>Vera ha accettato di annullare: lo scambio è annullato.</b> "
               "I sats eventualmente in garanzia tornano a chi vende.")], detto())

    print("\n6) il moderatore e le scadenze: tutti e due, e i sats a chi li aveva")
    o = ordine(7)
    t0 = ora(600)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 600)
    await posta(busta(o, "canceled", t0 + 640, "mostro", "admin"))
    prova("il MODERATORE annulla",
          [(V, f"⚖️ <b>Un moderatore ha annullato lo scambio.</b>{TORNATI}"),
           (C, "⚖️ <b>Un moderatore ha annullato lo scambio.</b> I sats "
               "eventualmente in garanzia tornano a chi vende.")],
          [x for x in detto() if not x[1].startswith("⚖️ <b>Disputa")])
    o = ordine(8)
    t0 = ora(700)
    semina_ordine(o, "buy")
    await fino_a(o, "garanzia", t0 + 700)
    await posta(busta(o, "expired", t0 + 1700, "mostro", "maker-timeout"))
    prova("chi ha pubblicato non prosegue: a chi vende, che aveva bloccato, i sats tornati",
          [(V, "⏰ <b>Chi aveva pubblicato l'ordine non ha proseguito in tempo:</b> "
               f"lo scambio è annullato, non devi fare niente.{TORNATI}"),
           (C, "⏰ <b>Non hai proseguito in tempo:</b> il tuo ordine è stato "
               "annullato. Puoi ripubblicarlo quando vuoi.")], detto())
    o = ordine(9)
    t0 = ora(800)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 800)
    await posta(busta(o, "expired", t0 + 1800, "mostro", "taker-timeout"))
    # EMENDATA (10 ott 2026, reputazione-p2p): a chi ha preso e non ha
    # proseguito arriva anche la riga del conto — e' il suo primo
    prova("chi ha preso non prosegue: a chi vende (ha pubblicato e bloccato) i sats tornati",
          [(V, "🔄 <b>Chi aveva preso il tuo ordine non ha proseguito.</b> È "
               f"tornato in vetrina: non devi fare niente.{TORNATI}"),
           (C, "🔄 <b>Non hai proseguito in tempo:</b> l'ordine è tornato in "
               "vetrina. Se ti interessa ancora, puoi riprenderlo.\n\nQuesto conta "
               "come scambio non completato. Il primo è tollerato; con un secondo "
               "nello stesso mese non potrai prendere gli ordini con filtro (1+, 3+, "
               "5+) per 30 giorni, e da due in 90 giorni comparirà sul tuo profilo.")],
          detto())
    o = ordine(10)
    t0 = ora(900)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 900)
    await posta(busta(o, "expired", t0 + 1900, "mostro", "escrow-deadline"))
    prova("la garanzia al capolinea",
          [(V, "⏰ <b>La garanzia è arrivata a scadenza: lo scambio è "
               f"annullato.</b>{TORNATI}"),
           (C, "⏰ <b>La garanzia è arrivata a scadenza: lo scambio è "
               "annullato.</b> I sats tornano a chi vende.")], detto())

    print("\n7) il ritiro di un ordine MAI PRESO")
    del banco.DETTO[:]
    o = ordine(11)
    t0 = ora(1000)
    semina_ordine(o, "sell")
    r = await posta(busta(o, "canceled", t0 + 1000, "seller", "pending", buyer=None))
    prova("entra, e resta muto come prima", ({"ok": True, "nuovo": True}, []),
          (r, detto()))

    print("\n8) I DOPPIONI")
    o = ordine(12)
    t0 = ora(1100)
    semina_ordine(o, "buy")
    await fino_a(o, "garanzia", t0 + 1100)
    await posta(busta(o, "canceled", t0 + 1140, "seller", "republished"))
    prova("il primo annullo: un avviso a testa", [V, C], sorted(chi for chi, _ in detto()))
    del banco.DETTO[:]
    r = await posta(busta(o, "canceled", t0 + 1140, "seller", "republished"))
    prova("il RETRY di mostrod: gia' registrato, e non parte niente",
          ({"ok": True, "nuovo": False}, []), (r, detto()))
    prova("...un timbro solo a testa", [V, C], timbri(o, "tornato"))
    # LA RISERVA DEL LIBRO: la sua frase dello stesso annullo, in attesa
    # per chi l'ha fatto, scade DOPO che il coordinatore ha parlato
    SRV._p2p_leve = lambda *a, **k: {"attivo": True}
    o = ordine(13)
    t0 = ora(1200)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 1200)
    adesso = int(time.time())
    con = banco.con_db()
    con.execute("INSERT INTO p2p_attese(ordine, momento, giro, tg_id, testo, quando, "
                "scade, fonte) VALUES(?,'annullato',1,?,?,?,?,'libro')",
                (o, V, "❌ <b>Lo scambio è stato annullato.</b>", t0 + 1240, adesso - 1))
    con.commit()
    con.close()
    await posta(busta(o, "canceled", t0 + 1240, "seller", ""))
    prova("il coordinatore: un avviso a testa", [V, C], sorted(chi for chi, _ in detto()))
    del banco.DETTO[:]
    await SRV._giro_attese_p2p()
    prova("...e la riserva del libro, alla sua scadenza, tace", [], detto())
    # ...E SE IL LIBRO HA PARLATO PRIMA: il coordinatore in ritardo oltre
    # la riserva non glielo ripete
    o = ordine(14)
    t0 = ora(1300)
    semina_ordine(o, "sell")
    await fino_a(o, "garanzia", t0 + 1300)
    con = banco.con_db()
    con.execute("INSERT INTO p2p_attese(ordine, momento, giro, tg_id, testo, quando, "
                "scade, fonte) VALUES(?,'annullato',1,?,?,?,?,'libro')",
                (o, V, "❌ <b>Lo scambio è stato annullato.</b>", t0 + 1340,
                 int(time.time()) - 1))
    con.commit()
    con.close()
    await SRV._giro_attese_p2p()
    prova("la riserva parla per prima, a chi ha annullato", [V], [chi for chi, _ in detto()])
    del banco.DETTO[:]
    await posta(busta(o, "canceled", t0 + 1340, "seller", ""))
    prova("...e il coordinatore in ritardo glielo NON ripete: solo all'altro", [C],
          [chi for chi, _ in detto()])

    print("\n9) gli avvisi P2P spenti, e la cauzione di chi si ritira")
    o = ordine(15)
    t0 = ora(1400)
    semina_ordine(o, "buy")
    await fino_a(o, "garanzia", t0 + 1400)
    con = banco.con_db()
    con.execute("UPDATE utenti SET avvisi_p2p=0 WHERE tg_id=?", (V,))
    con.commit()
    con.close()
    await posta(busta(o, "canceled", t0 + 1440, "seller", "republished"))
    prova("chi annulla con gli avvisi spenti non riceve niente; l'altro si'", [C],
          [chi for chi, _ in detto()])
    con = banco.con_db()
    con.execute("UPDATE utenti SET avvisi_p2p=1 WHERE tg_id=?", (V,))
    con.commit()
    con.close()
    SRV.P2P_CAUZIONE = True
    SRV._P2P_FOTO["info"] = INFO_38385
    try:
        o = ordine(16)       # una vendita in contanti: chi compra prende, con la cauzione
        t0 = ora(1500)
        semina_ordine(o, "sell", ("Contanti",))
        await fino_a(o, "preso", t0 + 1500)
        await posta(busta(o, "canceled", t0 + 1540, "buyer", "republished"))
        # «Vera» e' il NOME di V: C ha preso, e dal 12 ott 2026 vede chi
        # ha pubblicato (mostrod ha nominato le due parti)
        prova("chi compra si ritira: il suo avviso, e sotto la cauzione che torna",
              f"❌ <b>Hai annullato lo scambio con Vera."
              "</b>\n\n🔐 La cauzione che avevi bloccato torna nel tuo wallet.",
              dict(banco.DETTO).get(C))
    finally:
        SRV.P2P_CAUZIONE = False
        SRV._P2P_FOTO["info"] = None
    if SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(SRV._TASK_EVENTI_P2P), return_exceptions=True)


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
