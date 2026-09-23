# -*- coding: utf-8 -*-
"""
IN COLLAUDO IL SERVER NON LEGGE DAI RELAY VERI (23 set 2026) — il giro
col SERVER VERO.

La sera del 23 set 2026 l'antivirus ha fermato un python.exe diretto a
nostr.mom: un server di prova, al primo /api/me di un'identita' con la
npub verificata e il francobollo mai rinfrescato, aveva chiesto il suo
kind 0 ai quattro relay di serie. Qui si rifa' ESATTAMENTE quel giro —
config di cartone senza RELAY_NOSTR (cioe' i quattro relay veri di
serie), l'identita' 222 con la npub verificata, la sua /api/me col
rinfresco che parte da solo — e poi si bussa a ogni altra lettura del
server: i relay DM, il libro P2P e le impostazioni del coordinatore, lo
specchio dell'ascolto, l'import orario con la sua scoperta.

DUE RETI, e la prima regge anche fuori dalla CI: le create_connection
del server e di importa_nostr.py sono avvolte da un REGISTRO, quindi una
connessione verso un relay che non e' di casa fa rosso il collaudo
anche sul portatile, dove la rete c'e'. In CI poi la gabbia fa rosso
anche un DNS solo.
L'ALTRA META' DEL PATTO si prova con lo stesso registro: verso il relay
di casa — quello morto dei giri dal vivo, ws://127.0.0.1:9 — il server
BUSSA ancora, e trova la porta chiusa. Una guardia che fermasse tutto
avrebbe tolto di mezzo anche il modo di provare con un relay di cartone.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti, PRIMA dell'import del server.

USO:  python collaudo_letture_relay.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
BUSSATE = []                 # ogni relay a cui si e' aperta (o tentata) una connessione
RIGHE = []                   # quel che il server e lo script hanno stampato
MORTO = "ws://127.0.0.1:9"   # il relay morto dei giri dal vivo
CHIAVE = "cd" * 32           # la chiave di 222: finta, ma una chiave vera per forma
MOSTRO = "e" * 64


def _fuori_casa():
    return [r for r in BUSSATE if not banco.SRV.relay_di_casa(r)]


def _detti(frammento):
    """I relay nominati dalle righe del giudice che contengono `frammento`."""
    return sorted(r.split(" da ", 1)[1].split(": in collaudo")[0]
                  for r in RIGHE if "[nostr simulato] lettura " + frammento in r)


def main():
    print("=" * 58)
    print("  IN COLLAUDO NESSUNA LETTURA DA UN RELAY VERO — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    import importa_nostr as IMP

    # IL REGISTRO, sul server e sullo script, prima di qualunque giro
    vera = SRV.create_connection
    prova("websocket-client c'e': senza, i lettori uscirebbero da soli e "
          "questo collaudo non proverebbe niente", True, vera is not None)

    def registro(relay, *a, **k):
        BUSSATE.append(relay)
        return vera(relay, *a, **k)
    SRV.create_connection = registro
    IMP.create_connection = registro

    def stampa(*a, **k):
        RIGHE.append(" ".join(str(x) for x in a))
        print(*a, **k)
    SRV.print = stampa
    IMP.print = stampa

    # ---- 1) IL 23 SET, RIFATTO ------------------------------------------
    print("\n[il 23 set, rifatto: la /api/me di chi ha la npub verificata]")
    prova("il config di cartone non ha RELAY_NOSTR: valgono i relay di "
          "serie, cioe' quelli veri di quella sera", SRV.RELAY_DI_SERIE,
          SRV.RELAYS_VERIFICA)
    con = SRV.db()
    con.execute("INSERT INTO utenti(tg_id, nome, negozio, registrato, npub, "
                "npub_verificata, avatar_aggiornato) "
                "VALUES(222, 'Venditore', 'neg222', ?, ?, 1, 0)",
                (int(time.time()), SRV.hex_to_npub(CHIAVE)))
    con.commit()
    con.close()
    banco.come(222)

    async def apri_profilo():
        r = await SRV.mio_profilo()
        # il rinfresco del francobollo parte in create_task, e la risposta
        # non lo aspetta: gli si lascia finire il giro, come farebbe il
        # server acceso — finito, il francobollo si timbra
        fine = time.time() + 30
        while time.time() < fine:
            await asyncio.sleep(0.05)
            c = SRV.db()
            t = c.execute("SELECT avatar_aggiornato FROM utenti "
                          "WHERE tg_id=222").fetchone()[0]
            c.close()
            if t:
                return r, t
        return r, 0

    risposta, timbro = asyncio.run(apri_profilo())
    prova("la /api/me risponde, e il rinfresco parte e finisce da solo",
          [True, True], [isinstance(risposta, dict), timbro > 0])
    prova("...senza una sola connessione verso un relay vero", [],
          _fuori_casa())
    prova("...e il server lo dice: una riga per ognuno dei relay di serie",
          sorted(SRV.RELAYS_VERIFICA),
          _detti("del profilo (kind 0) di " + CHIAVE[:16]))

    # ---- 2) LE ALTRE LETTURE --------------------------------------------
    print("\n[le altre letture del server]")
    prima = len(BUSSATE)
    esiti = [SRV.chiedi_relay_dm("wss://nostr.mom", CHIAVE),
             SRV.eventi_libro_da_relay("wss://relay.mostro.network", ["o"],
                                       0, MOSTRO),
             SRV.info_libro_da_relay("wss://relay.mostro.network", MOSTRO)]
    prova("i relay DM, il libro P2P e le impostazioni del coordinatore: "
          "verso un relay vero nessuna bussata, e il ripiego di un relay muto",
          [[None, None, None], []], [esiti, BUSSATE[prima:]])
    dove = asyncio.run(SRV.relay_dm_di(CHIAVE))
    prova("...e chi cerca dove consegnare un DM non esce: gli restano i "
          "relay di serie (e in collaudo il DM poi si stampa soltanto)",
          [SRV.RELAYS_VERIFICA[:4], []], [dove, BUSSATE[prima:]])
    SRV.MOSTRO_RELAY_SPECCHIO = ["wss://specchio.example"]

    async def sguardi():
        SRV._guardia_ascolto_p2p()
        SRV._guardia_ascolto_p2p()
    asyncio.run(sguardi())
    prova("lo specchio che non e' di casa non si ascolta: nessun filo, "
          "nessuna bussata, e la riga dello stato dice perche'",
          [None, [], "spento: in collaudo lo specchio non e' di casa"],
          [SRV._P2P_ASCOLTO["filo"], BUSSATE[prima:],
           SRV._stato_ascolto_p2p()])
    prova("...e il giudice l'ha detto UNA volta, a due sguardi",
          ["wss://specchio.example"], _detti("dell'ascolto P2P (38383)"))
    esito = SRV.eventi_libro_da_relay(MORTO, ["o"], 0, MOSTRO)
    prova("verso il relay di casa invece si bussa ancora — e quello morto "
          "dei giri dal vivo ha la porta chiusa", [None, [MORTO]],
          [esito, BUSSATE[prima:]])

    # ---- 3) L'IMPORT ORARIO E LA SCOPERTA ---------------------------------
    print("\n[l'import orario e la scoperta]")
    prova("lo script, senza righe nel config, legge da relay che non sono "
          "di casa (i quattro di serie e quello di un venditore)", True,
          bool(IMP.RELAYS) and not any(SRV.relay_di_casa(r)
                                       for r in IMP.RELAYS))
    SRV.IMPORT_NOSTR_APERTO = True
    SRV._prossimo_import_nostr = 0.0
    SRV._prossima_scoperta_nostr = 0.0
    prima = len(BUSSATE)
    asyncio.run(SRV.importa_nostr_periodico())
    prova("coi soli relay veri il giro orario non gira: nessuna bussata",
          [], BUSSATE[prima:])
    prova("...e lo dice, una riga per relay", sorted(IMP.RELAYS),
          _detti("dell'import Nostr (annunci e cancellazioni)"))
    # I RELAY MISTI: lo script vero, con un relay vero e quello di casa. A
    # leggere passa 222 (ha la chiave dimostrata): la scoperta setaccia e
    # l'import a testa chiede, e tutt'e due devono bussare al solo MORTO
    IMP.RELAYS = ["wss://nos.lol", MORTO]
    SRV._prossimo_import_nostr = 0.0
    SRV._prossima_scoperta_nostr = 0.0
    prima = len(BUSSATE)
    asyncio.run(SRV.importa_nostr_periodico())
    prova("coi relay misti la scoperta e l'import a testa bussano al SOLO "
          "relay di casa", [True, [MORTO]],
          [len(BUSSATE[prima:]) >= 2, sorted(set(BUSSATE[prima:]))])
    prova("...e il relay vero l'ha detto il giudice, anche per la scoperta",
          ["wss://nos.lol"], _detti("della scoperta Nostr"))

    # ---- IL CONTO --------------------------------------------------------
    print("\n[il conto delle bussate]")
    prova("in tutto il giro, nessuna connessione verso un relay che non e' "
          "di casa", [], _fuori_casa())

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
