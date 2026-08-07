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
     "OK", "spiega come funziona la piattaforma, non parla per lei"),
    ("Maglietta Barattolo taglia L",
     "Cotone, stampa arancione, mai indossata.",
     "OK", "merchandising"),
    ("Powerbank 20000 mAh",
     "Come da policy Barattolo non accetto pagamenti fuori dal "
     "deposito di garanzia. Non scrivetemi su altri canali.",
     "OK", "nomina le regole per proteggersi, che e' il contrario"),

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
                "che un divieto scritto sul solo titolo perderebbe"),
    ("Poste Italiane: pacco in giacenza",
     "La tua spedizione e' in giacenza. Regolarizza il pagamento di "
     "2,99 euro per la riconsegna.",
     "VIETATO", "un ALTRO servizio, non noi"),

    # --- la terza risposta: il ruolo intestato ---------------------
    ("Assistenza Barattolo - supporto agli utenti",
     "Ti aiuto a risolvere problemi con gli ordini e le spedizioni.",
     "DUBBIO", "si intesta un ruolo che non ha (ed e' anche un "
               "servizio: qualunque dei due motivi va bene)"),
    ("Barattolo Ufficiale - store",
     "Il negozio ufficiale del mercatino.",
     "DUBBIO", "si spaccia per ufficiale senza fingere un messaggio"),

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

    sbagliati = 0
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
        print(f"  {'✓' if ok else '✗'} [{atteso:>7} | {detto or '?':>7}] "
              f"{titolo[:52]}")
        print(f"      {perche}")
        if not ok:
            print(f"      >>> ha risposto: {riga}")

    print(f"\n  {len(CASI) - sbagliati}/{len(CASI)} come atteso")
    if sbagliati:
        print("  Un FALSO POSITIVO (un OK atteso finito in VIETATO) e' "
              "il caso grave:\n  blocca annunci legittimi. Si corregge "
              "il prompt A MANO — la macchina\n  raccoglie, l'umano "
              "decide.")
    return 1 if sbagliati else 0


if __name__ == "__main__":
    sys.exit(main())
