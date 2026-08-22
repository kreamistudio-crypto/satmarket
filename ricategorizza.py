# -*- coding: utf-8 -*-
"""
RICATEGORIZZA — l'AI PROPONE, l'admin decide (lug 2026).

IL PROBLEMA: il catalogo delle categorie e' passato da 9 voci a 25, ma
gli annunci di ieri sono rimasti nelle caselle di ieri — un portatile
in «Elettronica» invece che in «Informatica», una Jade in «Elettronica»
invece che in «Bitcoin», un paio di scarpe in «Abbigliamento» invece
che in «Scarpe e accessori» — e gli annunci che arrivano da Nostr
nascono TUTTI in «Altro», che e' la casella dove non li cerca nessuno.

COSA FA QUESTO SCRIPT: legge titolo e descrizione degli annunci attivi,
li manda all'AI a lotti da 20 e scrive le proposte nella tabella
`categoria_proposta`. Basta.

COSA NON FA, ed e' il punto: NON tocca `annunci.categoria`. Mai. A
spostare un annuncio e' un moderatore, dalla coda «🗂 Categorie da
sistemare» del Profilo, dove le proposte arrivano raggruppate per
spostamento e si approvano a gruppi coi titoli sotto gli occhi.
Nessun annuncio cambia casella senza che un umano l'abbia visto.

L'AI puo' anche dire NON SO, ed e' importante che possa: un annuncio
lasciato dov'e' non fa danno a nessuno, uno spostato male si'.

USO (dalla cartella del progetto):
    python ricategorizza.py                # dice solo cosa proporrebbe
    python ricategorizza.py --scrivi       # riempie la coda dei moderatori
    python ricategorizza.py --scrivi --limite 100   # una fetta per volta
    python ricategorizza.py --scrivi --rifai        # richiede anche i gia' visti

Si puo' passare un percorso di database diverso da quello del config:
    python ricategorizza.py /tmp/prova.db

Idempotente: di serie non richiede all'AI ne' gli annunci su cui un
moderatore si e' gia' pronunciato (approvando o rifiutando: quella e'
una decisione umana e la macchina non ci torna sopra), ne' quelli che
hanno gia' una proposta in attesa sulla categoria che hanno adesso.
Cosi' un rilancio dopo un'ondata di import costa solo i nuovi.
Con --rifai si riconsidera tutto, decisioni comprese: e' il modo di
chiederlo esplicitamente.

COSTO INDICATIVO: ~0,005 $ a lotto di 20 annunci con Haiku, cioe'
circa 20 centesimi per un catalogo di 800. Lo script lo stampa alla
fine, contando i token veri.
"""

import ast
import os
import re
import sqlite3
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# Il config si chiede dentro main(), non qui: `catalogo()`, `PROMPT` e
# `RIGA` sono roba pura che il server e le prove importano da questo
# file, e chi importa un modulo per una costante non deve ritrovarsi il
# processo chiuso in faccia perche' manca una chiave che non gli serve.
# (E' successo: la CI e' rimasta rossa per 13 push, e siccome il
# controllo dei segreti gira dopo le prove, non girava piu' nemmeno
# quello.) Stesso modo di sposta_a_mano.py, che il config lo chiede
# con un ripiego.
try:
    from config import MODELLO_RICERCA
except ImportError:
    MODELLO_RICERCA = "claude-haiku-4-5"

# Quanti annunci per chiamata. Venti e' la misura gia' collaudata
# dalla moderazione a lotti dell'import: sta comodo nel contesto e la
# risposta resta corta e leggibile.
LOTTO = 20


def catalogo() -> list:
    """Le categorie le legge da server.py, che e' la fonte unica.
    Si prende il TESTO e non si importa il modulo: importarlo
    farebbe partire init_db(), le migrazioni e il caricamento dei
    comuni — cioe' scritture su un database che magari non e' quello
    che gli stiamo passando dalla riga di comando."""
    src = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
    i = src.index("CATEGORIE = (")
    return list(ast.literal_eval(src[src.index("(", i):src.index(")", i) + 1]))


PROMPT = (
    "Sei il magazziniere di un mercatino italiano. Ti do una "
    "lista di annunci e per ciascuno devi dire in quale categoria del "
    "catalogo starebbe meglio.\n\n"
    "CATEGORIE AMMESSE (usa il nome ESATTO, nessun altro):\n{cat}\n\n"
    "REGOLE:\n"
    "- Rispondi con UNA riga per annuncio, nel formato esatto:\n"
    "  <numero>: <nome esatto della categoria>\n"
    "  oppure\n"
    "  <numero>: NON SO\n"
    "- «NON SO» quando il titolo e la descrizione non bastano a "
    "decidere, o quando due categorie sono ugualmente plausibili. Non "
    "tirare a indovinare: un annuncio lasciato dov'e' non fa danno, uno "
    "spostato male si'.\n"
    "- «Altro» e' l'ultima spiaggia: se una categoria vera esiste, usa "
    "quella.\n"
    # La regola «Bitcoin» e' stata riscritta ad ago 2026 da un caso
    # vero: 19 proposte in produzione, e UNDICI erano annunci da
    # tirare fuori da «Bitcoin» — sacche, poster cypherpunk,
    # magliette. Non era il modello a disobbedire: la regola vecchia
    # insegnava «hardware e nodi» con quattro esempi tutti apparecchi
    # (Jade, BitBox, SeedSigner, NerdMiner), mentre l'albero delle
    # sottocategorie ha «merch» e «poster-stampe» sotto Bitcoin da
    # quando e' stato disegnato: quel reparto e' TEMATICO. Qui si e'
    # corretta una premessa parziale, mai inseguito il modello — e a
    # dire se il modello ha capito c'e' collaudo_ricategorizza.py,
    # da rilanciare a OGNI ritocco di questo prompt.
    # E IL SECONDO GIRO HA TROVATO L'EFFETTO OPPOSTO (ago 2026, dal
    # campo): le undici sparite, ma tre «Sat's Oil» proposti da
    # Alimenti a Bitcoin per il «Sat» nel NOME, e il «Manifesto
    # Hacker» spinto verso Arte perche' e' una stampa. Da qui la
    # contro-regola (decisione di Andrea): il tema dev'essere
    # L'OGGETTO, non il nome del prodotto — la stessa lezione gia'
    # pagata dal prompt della moderazione, dove «sat» e' la MONETA e
    # una somiglianza di nome non e' mai un motivo.
    "- «Bitcoin» e' un reparto TEMATICO, non un reparto di hardware: "
    "ci sta tutto cio' che parla di bitcoin e di cultura cypherpunk "
    "— portafogli hardware, miner, nodi, libri, poster, magliette, "
    "sacche, adesivi. A decidere e' il TEMA, non il tipo di oggetto: "
    "una maglietta col logo bitcoin e' «Bitcoin», una maglietta "
    "qualunque e' «Abbigliamento», e un poster cypherpunk resta "
    "«Bitcoin» anche se e' una stampa d'arte. MA il tema dev'essere "
    "L'OGGETTO, non il nome del prodotto: un olio o una birra in "
    "edizione bitcoin restano «Alimenti e bevande» — «sat» o "
    "«bitcoin» nel NOME non bastano mai a spostare un prodotto "
    "d'uso. Non ci sta l'elettronica generica.\n"
    # IL TERZO GIRO (ago 2026, dal campo): una consulenza sui wallet
    # restava in «Bitcoin» — lo stesso pendolo del Sat's Oil ma
    # sull'altro asse: il modello guardava il TEMA e ignorava che
    # l'oggetto e' una PRESTAZIONE. La regola sta da sola perche' non
    # e' un caso di Bitcoin: vale per ogni argomento — un corso di
    # cucina non e' «Alimenti e bevande».
    "- Le PRESTAZIONI battono il tema: se quello che si vende e' una "
    "prestazione — una lezione, un corso, una consulenza, un lavoro "
    "su commissione — la categoria e' «Lezioni e corsi» o «Lavoro e "
    "servizi», qualunque sia l'argomento. Una consulenza su bitcoin "
    "e' «Lezioni e corsi», un hardware wallet e' «Bitcoin».\n"
    "- «Informatica» e' per computer, portatili, componenti e "
    "periferiche; «Telefonia» per telefoni e accessori; «Elettronica» "
    "resta per il resto.\n"
    "- Guarda l'oggetto, non il contorno: «spedisco in tutta Italia» "
    "non e' una categoria.\n"
    "Nessun altro testo prima o dopo le righe.")

RIGA = re.compile(r"^\s*(?:ANNUNCIO\s+)?(\d+)\s*[:.\)\-]\s*(.+?)\s*$")


def chiedi(ai, cat: list, voci: list):
    """voci = [(id, titolo, descrizione, categoria_ora)]; ritorna
    ({id: categoria_nuova} SOLO per gli spostamenti veri, (token in,
    token out)). Una riga storta, un «NON SO», un nome di categoria
    inventato o un id che non appartiene al lotto: quella voce resta
    dov'e'. Fail-open per lotto: se la chiamata esplode, si tira
    avanti col prossimo."""
    corpo = "\n\n".join(
        f"ANNUNCIO {i}\nTITOLO: {(t or '')[:160]}\n"
        f"DESCRIZIONE: {(d or '')[:400]}\nORA STA IN: {c}"
        for i, t, d, c in voci)
    try:
        r = ai.messages.create(
            model=MODELLO_RICERCA, max_tokens=700, timeout=40,
            system=PROMPT.format(cat="\n".join(f"- {c}" for c in cat)),
            messages=[{"role": "user", "content": corpo}])
    except Exception as e:
        print(f"  ⚠️ lotto saltato ({type(e).__name__}: {e})")
        return {}, (0, 0)
    testo = "".join(b.text for b in r.content if b.type == "text")
    nel_lotto = {i: c for i, _, _, c in voci}
    fuori = {}
    for riga in testo.splitlines():
        m = RIGA.match(riga)
        if not m:
            continue
        ident, nuova = int(m.group(1)), m.group(2).strip().strip(".")
        if ident not in nel_lotto or nuova not in cat:
            continue                      # NON SO, o categoria inventata
        if nuova != nel_lotto[ident]:
            fuori[ident] = nuova
    return fuori, (r.usage.input_tokens, r.usage.output_tokens)


def main():
    try:
        from config import DB, ANTHROPIC_API_KEY
    except ImportError:
        print("✗ Manca config.py (o le sue chiavi): questo script gira "
              "dalla cartella del progetto.")
        return 1
    scrivi = "--scrivi" in sys.argv
    rifai = "--rifai" in sys.argv
    limite = 0
    if "--limite" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--limite") + 1])
    percorsi = [a for a in sys.argv[1:]
                if not a.startswith("--") and not a.isdigit()]
    db = percorsi[0] if percorsi else DB

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("INCOLLA"):
        print("✗ Senza chiave Anthropic non c'e' niente da chiedere.")
        return 1
    import anthropic
    ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    cat = catalogo()
    print(f"🗂  Ricategorizzazione — {len(cat)} categorie, database {db}")
    print("   " + ("SCRIVO le proposte nella coda dei moderatori"
                   if scrivi else "prova a vuoto: non scrivo niente "
                                  "(--scrivi per riempire la coda)"))

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS categoria_proposta(
        annuncio_id INTEGER PRIMARY KEY, categoria_ora TEXT DEFAULT '',
        categoria_nuova TEXT DEFAULT '', motivo TEXT DEFAULT '',
        creato INTEGER DEFAULT 0, stato TEXT DEFAULT 'proposta',
        deciso_da INTEGER DEFAULT 0, deciso_il INTEGER DEFAULT 0)""")
    dove = "WHERE a.stato='attivo'"
    if not rifai:
        # Due modi di essere «gia' visto», e il primo conta di piu':
        #   - un MODERATORE si e' gia' pronunciato, approvando o
        #     rifiutando. Li' non si torna: rifarlo vorrebbe dire
        #     rimettere in discussione una decisione umana, ed e'
        #     esattamente il bug che l'automatismo ha fatto una volta
        #     (lug 2026). Per riconsiderarlo c'e' --rifai, che e' il
        #     modo di chiederlo ESPLICITAMENTE;
        #   - oppure c'e' gia' una proposta in attesa fatta sulla
        #     categoria che l'annuncio ha ADESSO: e' la stessa domanda
        #     con la stessa risposta, e si pagherebbe due volte.
        dove += (" AND NOT EXISTS(SELECT 1 FROM categoria_proposta p "
                 "WHERE p.annuncio_id=a.id "
                 "AND (p.stato IN ('applicata','scartata') "
                 "     OR p.categoria_ora=a.categoria))")
    righe = con.execute(
        f"SELECT a.id, a.titolo, a.descrizione, a.categoria FROM annunci a "
        f"{dove} ORDER BY a.id" + (f" LIMIT {limite}" if limite else "")
    ).fetchall()
    print(f"   {len(righe)} annunci da guardare\n")
    if not righe:
        con.close()
        return 0

    proposte, tok_in, tok_out = {}, 0, 0
    for i in range(0, len(righe), LOTTO):
        lotto = righe[i:i + LOTTO]
        fuori, (ti, to) = chiedi(ai, cat,
                                 [(r["id"], r["titolo"], r["descrizione"],
                                   r["categoria"]) for r in lotto])
        proposte.update(fuori)
        tok_in += ti
        tok_out += to
        print(f"  · lotto {i // LOTTO + 1}/{-(-len(righe) // LOTTO)}: "
              f"{len(lotto)} annunci, {len(fuori)} da spostare")

    titoli = {r["id"]: (r["titolo"], r["categoria"]) for r in righe}
    gruppi = {}
    for ident, nuova in proposte.items():
        gruppi.setdefault((titoli[ident][1], nuova), []).append(ident)
    print(f"\n📋 {len(proposte)} proposte in {len(gruppi)} spostamenti:")
    for (ora, nuova), ids in sorted(gruppi.items(),
                                    key=lambda g: -len(g[1])):
        print(f"   {ora} → {nuova}: {len(ids)} annunci")
        for ident in ids[:3]:
            print(f"      «{titoli[ident][0][:60]}»")
        if len(ids) > 3:
            print(f"      … e altri {len(ids) - 3}")

    if scrivi and proposte:
        adesso = int(time.time())
        con.executemany(
            "INSERT INTO categoria_proposta(annuncio_id, categoria_ora, "
            "categoria_nuova, motivo, creato, stato, deciso_da, deciso_il) "
            "VALUES(?,?,?,?,?,'proposta',0,0) "
            "ON CONFLICT(annuncio_id) DO UPDATE SET "
            "categoria_ora=excluded.categoria_ora, "
            "categoria_nuova=excluded.categoria_nuova, "
            "creato=excluded.creato, stato='proposta', "
            "deciso_da=0, deciso_il=0",
            [(ident, titoli[ident][1], nuova, "", adesso)
             for ident, nuova in proposte.items()])
        con.commit()
        print(f"\n✅ Coda riempita: {len(proposte)} proposte in attesa di "
              f"un moderatore (Profilo → «🗂 Categorie da sistemare»).")
    elif proposte:
        print("\n(prova a vuoto: non ho scritto niente. --scrivi per "
              "riempire la coda)")
    con.close()

    # Haiku: 1 $ per milione di token in ingresso, 5 in uscita.
    costo = tok_in / 1e6 * 1 + tok_out / 1e6 * 5
    print(f"\n💸 {tok_in} token in, {tok_out} out — circa {costo:.3f} $")
    return 0


if __name__ == "__main__":
    sys.exit(main())
