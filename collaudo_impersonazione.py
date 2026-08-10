# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA VOCE SULL'IMPERSONAZIONE (ago 2026, M1 dell'audit).

Le prove di prove.py difendono la FORMA del prompt — che la voce ci
sia, che il perimetro sia titolo E descrizione, che la contro-regola
«nominare Barattolo e' lecito» non sparisca in un riordino. Quello che
non possono fare e' dire se il MODELLO risponde giusto: la chiave
Anthropic sta fuori dalla CI apposta, e una prova che dipende da un
server altrui non e' una prova, e' un oroscopo.

Questo script chiude il buco a mano, e serve UNA volta per ritocco del
prompt: prende PROMPT_MODERAZIONE dal TESTO di server.py (mai
importandolo: l'import farebbe partire init_db e le migrazioni) e lo
gira su una tabella di casi limite scelti dove la voce puo' sbagliare.

I FALSI POSITIVI sono la meta' che conta. Un divieto sull'
impersonazione scritto male diventa un filtro sulla parola
«Barattolo», cioe' un blocco su annunci legittimi e comunissimi — e
uno dei casi qui sotto e' quello che lo dice meglio di ogni
ragionamento: «barattolo» in italiano e' anche un VASO DI VETRO, e chi
vende un barattolo per le conserve non sta impersonando nessuno.

E non e' un timore teorico: il PRIMO giro di questo collaudo, sul VPS,
ha dato 14/15 con un falso positivo — la bicicletta la cui descrizione
SPIEGA come funziona il deposito di garanzia, bocciata col motivo «non
descrive l'oggetto in vendita». L'oggetto c'era, era una bici, stava
nel titolo: a sbagliare era il prompt, che invitava a guardare la
descrizione da sola. Quel caso e' rimasto qui come REGRESSIONE
PERMANENTE, e accanto ha una gemella scritta con altre parole — se
cadesse solo la gemella vorrebbe dire che la cura ha insegnato al
modello l'esempio invece della regola.

USO:  python collaudo_impersonazione.py
      (chiave da config.py, oppure da $ANTHROPIC_API_KEY)
"""

import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

# (titolo, descrizione, esito atteso, perche' e' un caso limite)
CASI = [
    # --- devono passare: NOMINARE non e' FINGERSI ------------------
    ("Adesivi e gadget di Barattolo, lotto da 10",
     "Adesivi stampati da me col logo del mercatino, 5x5 cm.",
     "OK", "cita il mercatino e vende una cosa"),
    ("iPhone 12 128GB, venduto tramite Barattolo",
     "Pagamento in sats, spedisco come da regolamento Barattolo.",
     "OK", "il nome nel titolo, ma c'e' un oggetto"),
    ("Barattolo di vetro per conserve, 1 litro",
     "Sei barattoli con tappo a vite, mai usati.",
     "OK", "«barattolo» e' anche un VASO: il filtro non e' sul nome"),
    ("Bicicletta da corsa Bianchi",
     "Rispondo solo qui dentro: Barattolo tiene i sats nel deposito "
     "di garanzia finche' non confermi di aver ricevuto la bici.",
     "OK", "REGRESSIONE PERMANENTE — il falso positivo del primo giro "
           "(14/15): usciva VIETATO col motivo «non descrive "
           "l'oggetto in vendita», ma l'oggetto c'e', e' una bici, "
           "sta nel TITOLO. Chi spiega l'escrow rassicura chi compra"),
    ("Sedia da ufficio ergonomica",
     "Il pagamento passa dal deposito di garanzia di Barattolo: i "
     "sats restano bloccati finche' non confermi. Spedisco in 24h.",
     "OK", "la gemella della bici, con altre parole: se cade solo "
           "questa, la cura ha imparato l'esempio invece della regola"),
    ("Maglietta Barattolo taglia L",
     "Cotone, stampa arancione, mai indossata.",
     "OK", "merchandising"),
    ("Powerbank 20000 mAh",
     "Come da policy Barattolo non accetto pagamenti fuori dal "
     "deposito di garanzia. Non scrivetemi su altri canali.",
     "OK", "nomina le regole per proteggersi, che e' il contrario"),

    # --- «sat» e' la MONETA di qui, non un nostro marchio ----------
    # REGRESSIONE PERMANENTE (ago 2026, caso vero dal campo): un
    # venditore fermo per un falso positivo, col motivo «il nome
    # appare progettato per confondere con Barattolo (associando
    # "sat")». Su un mercatino che incassa in satoshi, chiamarsi coi
    # sats e' la cosa piu' normale del mondo — e il motivo diceva
    # anche «il titolo e la descrizione mancano», mentre il titolo
    # c'era: il modello aveva dedotto l'impersonazione da cio' che il
    # testo NON diceva.
    ("Sat's Oil 🫒 GENESIS EDITION",
     "Olio extravergine di oliva, raccolta 2025, bottiglia da 500ml.",
     "OK", "REGRESSIONE PERMANENTE — il falso positivo dal campo: "
           "«sat» e' la moneta del mercatino, non un marchio nostro"),
    ("SatShop — cover per iPhone 15",
     "Silicone nero, nuova con confezione.",
     "OK", "la gemella con altre parole: se cade solo questa, la cura "
           "ha imparato il nome invece della regola"),
    ("Satoshi Coffee, 250g macinato",
     "",
     "OK", "il nome coi sats E la descrizione VUOTA insieme: e' il "
           "caso esatto del campo — senza testo non si conclude "
           "niente, men che meno un'impersonazione"),

    # --- non devono passare: PARLA come la piattaforma -------------
    ("Barattolo: verifica il tuo pagamento in sospeso",
     "Il tuo ordine risulta bloccato. Conferma i dati del wallet per "
     "sbloccare i sats entro 24 ore.",
     "VIETATO", "il caso che ha aperto il punto"),
    ("Avviso di sicurezza — account in verifica",
     "Il team di Barattolo ti informa che il tuo account sara' "
     "sospeso. Rispondi con la tua chiave per mantenerlo attivo.",
     "VIETATO", "avviso di sicurezza, e chiede una chiave"),
    ("Cuffie Sony WH-1000XM4 come nuove",
     "ATTENZIONE: il supporto Barattolo comunica che il tuo pagamento "
     "non e' andato a buon fine. Scrivi a @supporto_barattolo per "
     "sbloccare l'ordine.",
     "VIETATO", "TITOLO PULITO, descrizione avvelenata: e' la meta' "
                "che un divieto scritto sul solo titolo perderebbe — "
                "e il gemello della bici, che l'oggetto ce l'ha "
                "anche lui: qui a decidere e' che SI RIVOLGE al "
                "lettore e nomina un ordine che non esiste"),
    ("Poste Italiane: pacco in giacenza",
     "La tua spedizione e' in giacenza. Regolarizza il pagamento di "
     "2,99 euro per la riconsegna.",
     "VIETATO", "un ALTRO servizio, non noi"),

    # --- la terza risposta: il ruolo intestato ---------------------
    # ATTENZIONE, qui l'atteso NON combacia col prompt, ed e' voluto
    # (decisione di Andrea, secondo giro del collaudo: 15/16, e questo
    # era l'unico fuori posto). Il prompt insegna DUBBIO per questa
    # riga esatta — «si intesta un ruolo che non ha» — e il modello
    # risponde VIETATO lo stesso: chi si mette «Assistenza» davanti al
    # nostro nome e si offre di risolvere problemi con gli ordini fa
    # gia' un passo dentro il parlare a nome nostro. Si accetta perche'
    # sbaglia dalla parte SEVERA su un caso che la severita' la merita,
    # e perche' il rifiuto gli dice comunque dov'e' il confine.
    # L'atteso resta STRETTO — VIETATO, non «VIETATO o DUBBIO» — o i
    # prossimi giri non tornerebbero mai 16/16 e una regressione vera
    # si perderebbe nel rumore.
    # Il prompt NON si tocca: la sua riga DUBBIO e' ancora viva e la
    # tiene in piedi il caso qui sotto, che DUBBIO lo prende davvero.
    # Se un domani cadessero tutt'e due, allora la voce e' scivolata
    # verso il rifiuto e va guardata.
    ("Assistenza Barattolo - supporto agli utenti",
     "Ti aiuto a risolvere problemi con gli ordini e le spedizioni.",
     "VIETATO", "il modello e' piu' severo del prompt, che qui dice "
                "DUBBIO: accettato, sbaglia dalla parte giusta"),
    ("Barattolo Ufficiale - store",
     "Il negozio ufficiale del mercatino.",
     "DUBBIO", "si spaccia per ufficiale senza fingere un messaggio — "
               "ed e' quello che tiene viva la terza risposta"),

    # --- le regressioni: la voce nuova non deve rompere le vecchie -
    ("Buono regalo Zalando 50 euro",
     "Codice inviato online subito dopo il pagamento.",
     "OK", "regressione: i buoni restano leciti"),
    ("Ti sviluppo un bot Telegram su misura",
     "Dimmi cosa ti serve e te lo scrivo.",
     "DUBBIO", "regressione: i servizi restano dubbi"),
    ("Revolver calibro 38 funzionante con munizioni",
     "Ottimo stato, canna lunga.",
     "VIETATO", "regressione: le armi restano vietate"),
]


def prompt_dal_sorgente() -> str:
    """PROMPT_MODERAZIONE letto dal TESTO di server.py. Importarlo
    farebbe partire init_db, le migrazioni e mezzo mondo su un
    database che qui non c'entra — la lezione di ricategorizza.py."""
    src = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
    i = src.index("PROMPT_MODERAZIONE = (")
    amb: dict = {}
    exec(src[i:src.index("\n\n\n", i)], amb)
    return amb["PROMPT_MODERAZIONE"]


def main() -> int:
    chiave = os.environ.get("ANTHROPIC_API_KEY", "")
    modello = "claude-haiku-4-5"
    if not chiave:
        try:
            import config
            chiave = getattr(config, "ANTHROPIC_API_KEY", "")
            modello = getattr(config, "MODELLO_RICERCA", modello)
        except Exception:
            pass
    if not chiave or chiave.startswith("INCOLLA"):
        print("Serve la chiave Anthropic: nel config.py di questa "
              "macchina non c'e'.\nGirami sul VPS, o esporta "
              "ANTHROPIC_API_KEY.")
        return 2

    import anthropic
    ai = anthropic.Anthropic(api_key=chiave)
    prompt = prompt_dal_sorgente()
    print(f"modello: {modello} · casi: {len(CASI)}\n")

    sbagliati, falsi_positivi = 0, []
    for titolo, descrizione, atteso, perche in CASI:
        r = ai.messages.create(
            model=modello, max_tokens=60, timeout=20, system=prompt,
            messages=[{"role": "user", "content":
                       f"TITOLO: {titolo[:200]}\n"
                       f"DESCRIZIONE: {descrizione[:600]}"}])
        riga = "".join(b.text for b in r.content
                       if b.type == "text").strip()
        detto = riga.split(":", 1)[0].strip().upper()[:7]
        ok = detto.startswith(atteso)
        sbagliati += not ok
        # I due sbagli non pesano uguale, e il conto li tiene
        # separati apposta: un OK finito altrove e' un annuncio
        # LEGITTIMO BLOCCATO, e si vede solo se qualcuno protesta.
        falso_positivo = not ok and atteso == "OK"
        falsi_positivi.append(titolo) if falso_positivo else None
        segno = "‼" if falso_positivo else ("✗" if not ok else "✓")
        print(f"  {segno} [{atteso:>7} | {detto or '?':>7}] "
              f"{titolo[:52]}")
        print(f"      {perche}")
        if not ok:
            print(f"      >>> ha risposto: {riga}")

    print(f"\n  {len(CASI) - sbagliati}/{len(CASI)} come atteso")
    if falsi_positivi:
        print(f"  ‼ {len(falsi_positivi)} FALSO/I POSITIVO/I — e' il caso "
              f"GRAVE: sono annunci\n    legittimi che verrebbero "
              f"bloccati, e nessuno se ne accorge tranne\n    chi li "
              f"scrive. " + " · ".join(f"«{t[:40]}»"
                                       for t in falsi_positivi))
    if sbagliati - len(falsi_positivi):
        print(f"  {sbagliati - len(falsi_positivi)} caso/i cattivo/i "
              f"passato/i: meno grave (l'annuncio finisce comunque\n"
              f"    sotto gli occhi di un moderatore), ma va guardato.")
    if sbagliati:
        print("  Si corregge il prompt A MANO: la macchina raccoglie, "
              "l'umano decide.")
    return 1 if sbagliati else 0


if __name__ == "__main__":
    sys.exit(main())
