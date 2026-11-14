# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA DISPUTA CHE CAMBIA STRADA (14 nov 2026, cantiere
audit-dispute, dal primo audit di sicurezza).

IL CASO: un moderatore decide una disputa, il pagamento non riesce
subito, e lui ci ripensa — e' una strada VOLUTA (vedi «Una disputa
decisa resta in mano al moderatore»). Ma la prima decisione lasciava
sulla riga il suo timbro, e i giri dell'orologio seguono il timbro, non
lo stato. Due strade portavano i sats alla persona sbagliata:
  1. «al venditore» che non paga, poi «reso»: il giro pagava chi vende
     mentre chi compra rispediva l'oggetto;
  2. un rimborso rimasto a meta', poi «al venditore» con la fattura di
     chi vende scaduta: il giro rimborsava chi aveva perso.

`prove.py` (`prove_disputa_cambia_strada`) lo prova coi pezzi estratti;
qui gira la STORIA sul SERVER VERO, con un database usa-e-getta e il
nodo di cartone del banco di casa: la rotta del moderatore, le due
uscite, il giro dei sospesi e il reso fino in fondo sono quelli veri.

Le domande a cui risponde:
  1. dopo «al venditore» fallito e poi «reso», il giro non paga
     nessuno, e il reso arriva in fondo: rimborsato chi compra, UNA
     uscita sola, e fa il deposito;
  2. lo stesso a nodo muto (il timbro nasce dalla 'dispute');
  3. con un pagamento in volo il «reso» e' un 409 e nessuno sente
     parlare di restituzione;
  4. rimborso a meta', poi «al venditore» con la fattura scaduta: il
     giro paga CHI VENDE, mai chi ha perso.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete,
nessuna chiave.

USO:  python collaudo_disputa_cambia_strada.py
"""

import time

import collaudo_lnbits_muto as banco
import collaudo_rimborso_meno_spese as casa
from prove import bolt11_finta

prova = banco.prova
SRV = None


def tre(oid):
    o = casa.ordine(oid)
    return (o["stato"], o["payout_stato"] or "", o["payout_verso"] or "")


def scena_reso_dopo_venditore(aid):
    print("\n── 1. «AL VENDITORE» NON PAGA, POI «RESO» ──")
    oid = casa.disputa(aid)
    casa.ESITO["venditore"] = "failed"
    casa.decidi(oid, "venditore")
    prova("al venditore, e il nodo non consegna: deciso, aspetta il giro",
          ("confirmed", "da_riprovare", "venditore"), tre(oid))
    banco.DETTO.clear()
    r = casa.decidi(oid, "reso")
    prova("il moderatore ci ripensa: «reso»", "return_pending",
          r.get("stato"))
    prova("...e il timbro di prima se ne va con la decisione di prima",
          ("return_pending", "", ""), tre(oid))
    casa.ESITO.clear()
    casa.CHIESTE.clear()
    casa.giro_sospesi()
    prova("il giro dell'orologio non paga NESSUNO a reso deciso",
          ([], "return_pending"), (casa.uscite(), tre(oid)[0]))
    # ...e il reso arriva in fondo, per la strada di sempre
    banco.come(111)
    banco.chiama(SRV.reso_spedito, oid, None, "", "",
                 corpo={"corriere": "BRT", "tracking": "RESO001"})
    banco.come(222)
    banco.chiama(SRV.reso_ricevuto, oid, "", "")
    prova("il reso arriva in fondo: rimborsato chi compra, UNA uscita, "
          "ed e' il deposito",
          ("refunded", [("compratore", casa.TOTALE)]),
          (tre(oid)[0], casa.uscite()))
    prova("...e a chi vende nessuno ha mai detto «a tuo favore» dopo il "
          "reso", False, "a tuo favore" in casa.detti_a(222))


def scena_reso_a_nodo_muto(aid):
    print("\n── 2. NODO MUTO, POI «RESO» ──")
    oid = casa.disputa(aid)
    banco.NODO["codice"] = 520
    casa.decidi(oid, "venditore")
    prova("al venditore a nodo muto: sospeso, la disputa resta aperta",
          ("dispute", "da_riprovare", "venditore"), tre(oid))
    casa.decidi(oid, "reso")
    banco.NODO["codice"] = 200
    casa.CHIESTE.clear()
    casa.giro_sospesi()
    prova("...poi «reso»: a nodo tornato il giro non paga nessuno",
          ([], ("return_pending", "", "")), (casa.uscite(), tre(oid)))


def scena_reso_in_volo(aid):
    print("\n── 3. UN PAGAMENTO IN VOLO: IL RESO ASPETTA ──")
    oid = casa.disputa(aid)
    casa.ESITO["venditore"] = "pending"
    casa.decidi(oid, "venditore")
    prova("al venditore, e il pagamento resta in volo",
          ("dispute", "in_volo", "venditore"), tre(oid))
    banco.DETTO.clear()
    casa.alza("«reso» adesso e' un 409, con le sue parole",
              lambda: casa.decidi(oid, "reso"), 409, "non sappiamo ancora")
    prova("...la riga non si muove", ("dispute", "in_volo", "venditore"),
          tre(oid))
    prova("...e nessuno ha sentito parlare di restituzione", False,
          "restituzione" in casa.detti_a(111)
          or "reso" in casa.detti_a(222).lower())
    casa.ESITO.clear()


def scena_verso_di_ieri(aid):
    print("\n── 4. RIMBORSO A META', POI «AL VENDITORE» CON LA FATTURA "
          "SCADUTA ──")
    oid = casa.disputa(aid)
    casa.ESITO["compratore"] = "failed"
    casa.decidi(oid, "rimborso")
    prova("rimborso deciso, e il nodo non consegna: aspetta il giro",
          ("refund", "da_riprovare", "compratore"), tre(oid))
    # chi vende ha in colonna una fattura di quattro giorni fa: non si
    # tenta nemmeno, quindi nessuno prende la mano e riscrive il verso
    scaduta = bolt11_finta(casa.TOTALE, 3600, int(time.time()) - 4 * 86400,
                           phash=909)
    casa.db_esegui("UPDATE ordini SET invoice_venditore=? WHERE id=?",
                   scaduta, oid)
    casa.ESITO.clear()
    casa.CHIESTE.clear()
    casa.decidi(oid, "venditore")
    prova("il moderatore ci ripensa: «al venditore», la scaduta non si "
          "tenta, e il timbro dice VENDITORE",
          ([], ("confirmed", "da_riprovare", "venditore")),
          (casa.uscite(), tre(oid)))
    casa.giro_sospesi()
    chi = sorted({c for c, _ in casa.uscite()})
    prova("il giro paga CHI VENDE, dal suo address: mai chi ha perso",
          (["venditore"], "released"), (chi, tre(oid)[0]))
    prova("...ed e' UNA uscita sola", 1, len(casa.uscite()))


def main():
    global SRV
    print("=" * 66)
    print("  LA DISPUTA CHE CAMBIA STRADA — il giro vero")
    print("=" * 66)
    casa.avvio()
    SRV = casa.SRV
    aid, _ = casa.semina()
    scena_reso_dopo_venditore(aid)
    scena_reso_a_nodo_muto(aid)
    scena_reso_in_volo(aid)
    scena_verso_di_ieri(aid)
    print("\n" + "=" * 66)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 66)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
