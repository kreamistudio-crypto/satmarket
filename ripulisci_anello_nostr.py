# -*- coding: utf-8 -*-
"""
RIPULISCI L'ANELLO — la pulizia una-tantum dopo il bug dell'import
aperto che importava Barattolo dentro Barattolo (lug 2026).

COS'ERA SUCCESSO: la scoperta setaccia i relay senza filtro d'autore,
e fra gli annunci NIP-99 italiani con firma valida ci sono anche i
NOSTRI — quelli che la piattaforma firma per conto di chi pubblica da
qui. Nessuno la escludeva, cosi' e' nato un account intestato alla
nostra stessa chiave e l'import ha ricominciato a scaricare in casa
cio' che avevamo appena pubblicato: copie doppie in vetrina,
intestate a un venditore che non esiste, e il negozio di quel
venditore pieno di roba di persone diverse.

Il TAPPO e' gia' nel codice (chiave_di_casa in server.py e il
controllo dell'autore in importa_nostr.py): da li' in poi non se ne
creano di nuove. Questo script si occupa di quelle gia' nate.

COSA FA:
  - spegne le copie (stato='rimosso'): sono righe che non dovevano
    esistere, e l'originale e' vivo e vegeto al suo posto;
  - annulla gli ordini mai pagati che le riguardassero;
  - neutralizza l'account fantasma, cioe' gli toglie le chiavi Nostr
    cosi' esce da venditori_nostr_attivi() e non torna a importare.
    NON lo cancella: una riga di utenti cancellata lascerebbe
    riferimenti ciechi in annunci, ordini e registro — e un account
    inerte non fa danno a nessuno.

COSA NON FA, di proposito:
  - nessuna cancellazione NIP-09 verso i relay. Gli eventi la' fuori
    sono i NOSTRI, quelli degli annunci VERI: ritirarli
    cancellerebbe dalla piazza la merce buona. Qui si tocca solo il
    database di casa.
  - non tocca una copia su cui esiste un affare in corso: con dei
    sats in cassaforte prima si chiude l'ordine, poi si sistema
    l'annuncio. E' la stessa guardia della rimozione admin.

USO (dalla cartella del progetto, a server SPENTO o con l'import
gia' disattivato):
    python ripulisci_anello_nostr.py             # dice solo cosa farebbe
    python ripulisci_anello_nostr.py --conferma  # esegue

Si puo' passare anche un percorso di database diverso da quello del
config, e vale la pena farlo almeno una volta:
    cp satmarket.db /tmp/prova.db
    python ripulisci_anello_nostr.py --conferma /tmp/prova.db
cosi' la prova generale si fa su una copia, e sul database vero ci si
va sapendo gia' cosa succede.

Idempotente: rilanciarlo a lavoro fatto non trova piu' niente.
"""

import sqlite3
import sys
import time

try:
    from config import DB
except ImportError:
    DB = "satmarket.db"

# Il marchio degli eventi firmati da NOI: il tag `d` che scrive
# evento_annuncio() e' sempre 'barattolo-{id}', e l'id la' dentro e'
# l'annuncio VERO da cui la copia discende.
MARCHIO = "barattolo-%"

# Stati che vogliono dire «ci sono dei sats in ballo»: la stessa
# tupla della rimozione admin.
ORDINI_VIVI = ("locked", "shipped", "confirmed", "dispute",
               "return_pending", "return_shipped", "refund")


def ordini_vivi(con, annuncio_id):
    """Quanti ordini non terminali toccano l'annuncio, come testata
    mono o come riga di un set (gemello di _ordini_vivi_annuncio)."""
    seg = ",".join("?" * len(ORDINI_VIVI))
    try:
        return con.execute(
            f"SELECT COUNT(*) AS n FROM ordini WHERE stato IN ({seg}) "
            f"AND (annuncio_id=? OR id IN (SELECT ordine_id FROM "
            f"ordine_righe WHERE annuncio_id=?))",
            (*ORDINI_VIVI, annuncio_id, annuncio_id)).fetchone()[0]
    except sqlite3.OperationalError:
        # database senza ordine_righe (Barattolo piu' vecchio)
        return con.execute(
            f"SELECT COUNT(*) AS n FROM ordini WHERE stato IN ({seg}) "
            f"AND annuncio_id=?", (*ORDINI_VIVI, annuncio_id)).fetchone()[0]


def main():
    conferma = "--conferma" in sys.argv
    # Un percorso esplicito vince sul config: serve a fare la prova
    # generale su una COPIA prima di toccare il database vero.
    percorso = next((a for a in sys.argv[1:] if not a.startswith("-")), DB)
    print(f"Database: {percorso}"
          f"{'' if conferma else '   (anteprima: non scrivo niente)'}\n")
    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(percorso, timeout=15)
    con.row_factory = sqlite3.Row

    copie = con.execute(
        "SELECT a.id, a.titolo, a.stato, a.venditore_id, a.contatto_nostr, "
        "  CAST(substr(a.nostr_origine_d, 11) AS INTEGER) AS id_originale "
        "FROM annunci a "
        "WHERE a.contatto_nostr != '' AND a.nostr_origine_d LIKE ? "
        "ORDER BY a.id", (MARCHIO,)).fetchall()

    if not copie:
        print("✅ Nessuna copia da ripulire: l'anello e' gia' chiuso.")
        con.close()
        return 0

    print(f"Trovate {len(copie)} copie nate dai nostri stessi eventi.\n")
    da_spegnere, intoccabili = [], []
    for c in copie:
        orig = con.execute("SELECT id, venditore_id, stato FROM annunci "
                           "WHERE id=?", (c["id_originale"],)).fetchone()
        vivi = ordini_vivi(con, c["id"])
        riga = (f"  #{c['id']:<5} «{(c['titolo'] or '')[:44]:<44}» "
                f"stato={c['stato']:<9} venditore={c['venditore_id']}")
        if orig:
            riga += f" ← originale #{orig['id']} di {orig['venditore_id']}"
        else:
            riga += "  ⚠️ originale NON trovato"
        if vivi:
            intoccabili.append((c, vivi))
            print(riga + f"  🔒 {vivi} ordini in corso: NON si tocca")
        elif c["stato"] == "rimosso":
            print(riga + "  (gia' spenta)")
        else:
            da_spegnere.append(c)
            print(riga)

    # I venditori fantasma: le righe di utenti che, tolte le copie,
    # non possiedono NIENTE. Un account che ha anche annunci suoi e'
    # una persona vera che ha per sbaglio raccolto delle copie: si
    # spengono quelle e lui non si tocca.
    # Il conto degli ordini guarda solo quelli VIVI (sats in ballo):
    # un ordine chiuso e' storia, e la storia non impedisce di
    # togliere una chiave — anzi, lasciargliela vorrebbe dire tornare
    # a importare per sempre.
    seg = ",".join("?" * len(ORDINI_VIVI))
    fantasmi = []
    for vid in sorted({c["venditore_id"] for c in copie}):
        totale = con.execute("SELECT COUNT(*) AS n FROM annunci "
                             "WHERE venditore_id=?", (vid,)).fetchone()[0]
        suoi = con.execute(
            "SELECT COUNT(*) AS n FROM annunci WHERE venditore_id=? AND "
            "NOT (contatto_nostr != '' AND nostr_origine_d LIKE ?)",
            (vid, MARCHIO)).fetchone()[0]
        u = con.execute("SELECT tg_id, nome, npub, npub_accesso FROM utenti "
                        "WHERE tg_id=?", (vid,)).fetchone()
        aperti = con.execute(
            f"SELECT COUNT(*) AS n FROM ordini WHERE stato IN ({seg}) "
            f"AND (venditore_id=? OR compratore_id=?)",
            (*ORDINI_VIVI, vid, vid)).fetchone()[0]
        # le copie che resteranno vive anche dopo questo giro
        restano = sum(1 for c, _ in intoccabili if c["venditore_id"] == vid)
        print(f"\n  Venditore {vid}: {totale} annunci, di cui {suoi} suoi "
              f"veri; {aperti} ordini aperti; {restano} copie intoccabili")
        if u is None:
            print("    ⚠️ riga utenti assente: niente da neutralizzare")
        elif suoi:
            print("    ⚠️ ha annunci suoi: e' una persona vera, NON lo tocco")
        elif aperti or restano:
            print("    ⏸️ ha ancora affari o copie vive: lo lascio stare, "
                  "rilancia quando saranno chiusi")
        else:
            fantasmi.append(u)
            print(f"    → fantasma: gli tolgo le chiavi Nostr "
                  f"({(u['npub'] or '')[:24]}…)")

    print(f"\nRiepilogo: {len(da_spegnere)} copie da spegnere, "
          f"{len(intoccabili)} intoccabili, "
          f"{len(fantasmi)} account da neutralizzare.")

    if not conferma:
        print("\nAnteprima soltanto. Per eseguire davvero:\n"
              "    python ripulisci_anello_nostr.py --conferma")
        con.close()
        return 0

    adesso = int(time.time())
    con.execute("BEGIN IMMEDIATE")
    for c in da_spegnere:
        con.execute("UPDATE annunci SET stato='rimosso' WHERE id=? "
                    "AND stato!='rimosso'", (c["id"],))
        con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                    "WHERE stato='creato' AND annuncio_id=?",
                    (adesso, c["id"]))
        try:
            con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                        "WHERE stato='creato' AND id IN (SELECT ordine_id "
                        "FROM ordine_righe WHERE annuncio_id=?)",
                        (adesso, c["id"]))
        except sqlite3.OperationalError:
            pass
    for u in fantasmi:
        # Fuori da venditori_nostr_attivi() per sempre: senza chiavi
        # non e' piu' un venditore Nostr, e senza npub_accesso non ci
        # entra piu' nessuno. La riga resta, inerte.
        con.execute(
            "UPDATE utenti SET npub='', npub_verificata=0, "
            "npub_accesso='', nome=? WHERE tg_id=?",
            ("(account chiuso — anello import)", u["tg_id"]))
    con.commit()
    con.close()
    print(f"\n✅ Fatto: {len(da_spegnere)} copie spente, "
          f"{len(fantasmi)} account neutralizzati.")
    print("   Gli eventi sui relay non sono stati toccati: sono i nostri, "
          "quelli degli annunci veri.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
