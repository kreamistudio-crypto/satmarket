# -*- coding: utf-8 -*-
"""
CENSIMENTO SPEDIZIONE — quali annunci storici dicevano «spedisco»
a parole, senza mai dichiararlo nel campo consegna?

Nati prima che la consegna esistesse, quegli annunci scrivevano la
spedizione nel testo libero — spesso nel campo ZONA. Da quando la
vetrina mostra il solo comune, quella scritta non si vede piu' e
l'annuncio non dice come arriva la roba: questo censimento serve a
decidere quali recuperare, e come.

NON SCRIVE NIENTE. Apre il database in mode=ro, quindi anche un
errore di battitura verrebbe rifiutato da SQLite prima di toccare i
dati; e non importa server.py di proposito, perche' quel modulo
all'avvio scrive (migrazioni e backfill).

I due gruppi, decisi con Andrea (lug 2026):
  A) la spedizione e' scritta nella ZONA  -> indizio FORTE: scrittura
     automatica (consegna='spedizione', costo 0) + notifica. Le righe
     che nominano una CIFRA o negano la spedizione escono pero'
     dall'automatico: il costo 0 sarebbe una promessa che paga il
     venditore, e vanno guardate a mano.
  B) solo nella DESCRIZIONE               -> indizio DEBOLE (la stessa
     frase spesso nomina anche il ritiro): NESSUNA scrittura, solo la
     notifica-domanda. Decide il venditore, modalita' e costo.
Gli importati da Nostr si saltano sempre: li' comandano i relay.

USO:  cd satmarket && python3 censimento_spedizione.py
      cd satmarket && python3 censimento_spedizione.py > censimento.txt
Nessuna dipendenza: solo la libreria standard.
"""
import sqlite3, re, sys, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SPED = re.compile(r"spedisc|spedizione|spedito|spedire", re.I)
RIT = re.compile(r"ritir|a mano|di persona|in zona", re.I)
# Frasi che potrebbero ROVESCIARE il senso: negano la spedizione, o la
# fanno pagare a qualcuno. Non decidono nulla da sole, alzano la mano.
SOSPETTE = re.compile(
    r"non spedisc|niente spedizione|no spedizione|solo ritiro|"
    r"spedizione a carico|spese di spedizione|piu' spedizione|"
    r"\+ *spedizione|spedizione esclusa|escluse spese|a tue spese|"
    r"costo spedizione|spedizione \d|\d+ *(?:eur|euro|sat)", re.I)


# --- «la zona contiene un comune?», in piccolo -----------------------
# Serve solo a dire se, dopo il fix, la card mostrera' ancora un luogo.
# Non importa server.py apposta: quel modulo all'avvio scrive sul
# database, e questo script non deve poterlo fare.
def carica_nomi():
    nomi = set()
    try:
        import csv, unicodedata
        with open(os.path.join("dati", "comuni.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=";"):
                n = unicodedata.normalize("NFKD", r["nome"].lower())
                n = "".join(c for c in n if not unicodedata.combining(c))
                nomi.add(re.sub(r"[^a-z0-9]+", " ", n).strip())
    except Exception as e:
        print("(dati/comuni.csv non letto: %s — salto il controllo comune)\n" % e)
    return nomi


NOMI = carica_nomi()


def ha_comune(zona):
    if not NOMI:
        return None
    import unicodedata
    t = unicodedata.normalize("NFKD", (zona or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    tok = re.sub(r"[^a-z0-9]+", " ", t).split()
    for lung in range(min(6, len(tok)), 0, -1):
        for i in range(len(tok) - lung + 1):
            if " ".join(tok[i:i + lung]) in NOMI:
                return " ".join(tok[i:i + lung])
    return ""


# --- raggiungibilita', con la stessa regola di notifica() ------------
def avvisabile(u):
    if not u:
        return False, "utente non trovato"
    dest = u["npub_accesso"] or (u["npub"] if u["npub_verificata"] else "")
    canale = (u["canale_notifiche"] or "") or ("nostr" if u["tg_id"] < 0 else "telegram")
    via_nostr = canale in ("nostr", "entrambi") and bool(dest)
    via_tg = canale in ("telegram", "entrambi") and u["tg_id"] > 0
    if canale == "nostr" and not via_nostr and u["tg_id"] > 0:
        via_tg = True
    if via_tg and via_nostr:
        return True, "Telegram + Nostr"
    if via_tg:
        return True, "Telegram"
    if via_nostr:
        return True, "DM Nostr"
    return False, "NESSUN CANALE: la notifica non arriverebbe"


if not os.path.exists("satmarket.db"):
    print("Non trovo satmarket.db qui dentro.\n"
          "Lancialo dalla cartella del progetto:  cd satmarket && "
          "python3 censimento_spedizione.py")
    sys.exit(1)
# il database e' quello VIVO, e il server ci scrive mentre giriamo:
# quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
con = sqlite3.connect("file:satmarket.db?mode=ro", uri=True, timeout=15)
con.row_factory = sqlite3.Row

tot = con.execute("SELECT COUNT(*) c FROM annunci WHERE stato='attivo'").fetchone()["c"]
righe = con.execute(
    "SELECT * FROM annunci WHERE stato='attivo' AND consegna='' ORDER BY id").fetchall()

A, B, nostr = [], [], []
for x in righe:
    if x["contatto_nostr"]:
        if SPED.search((x["zona"] or "") + " " + (x["descrizione"] or "")):
            nostr.append(x)
        continue
    if SPED.search(x["zona"] or ""):
        A.append(x)
    elif SPED.search(x["descrizione"] or ""):
        B.append(x)

print("=" * 72)
print("CENSIMENTO SPEDIZIONE — sola lettura, nessuna modifica")
print("=" * 72)
print("annunci ATTIVI in tutto ...................... %d" % tot)
print("  di cui con consegna VUOTA ................. %d" % len(righe))
print("    A) spedizione nella ZONA ................ %d" % len(A))
print("    B) solo nella DESCRIZIONE (solo avviso) . %d" % len(B))
print("    importati da Nostr (saltati) ............ %d" % len(nostr))
print("(il dettaglio del gruppo A e' piu' sotto: qualche riga puo'")
print(" uscire dall'automatico se nomina una cifra — vedi il riepilogo)")


def dubbio(x):
    """Il gruppo A si scrive in automatico col costo 0 — ma se il testo
    nomina una CIFRA o nega la spedizione, quello zero sarebbe una
    promessa falsa che il venditore paga di tasca sua. Quelle righe
    escono dall'automatico e le si guarda a mano."""
    return bool(SOSPETTE.search((x["zona"] or "") + " " + (x["descrizione"] or "")))


def scheda(x, campo, azione):
    u = con.execute(
        "SELECT tg_id, nome, username, npub, npub_verificata, npub_accesso, "
        "canale_notifiche FROM utenti WHERE tg_id=?", (x["venditore_id"],)).fetchone()
    ok, via = avvisabile(u)
    chi = (u["nome"] if u else "?") or "?"
    if u and u["username"]:
        chi += " (@%s)" % u["username"]
    print("\n" + "-" * 72)
    print("#%d  %s" % (x["id"], x["titolo"]))
    print("  venditore : %s  [tg_id %s]" % (chi, x["venditore_id"]))
    print("  avviso    : %s%s" % (via, "" if ok else "   <-- ATTENZIONE"))
    print("  zona      : %r" % (x["zona"],))
    com = ha_comune(x["zona"])
    if com is not None:
        print("  comune in zona: %s" % (
            ("si, «%s» — la card continuera' a mostrarlo" % com) if com
            else "NO — dopo il fix la card mostrera' solo l'icona 🚚"))
    print("  descrizione: %s" % " ".join((x["descrizione"] or "").split())[:400])
    testo = (x["zona"] or "") + " " + (x["descrizione"] or "")
    if RIT.search(testo):
        print("  !! nomina anche il RITIRO -> semmai 'entrambe', da leggere")
    for m in set(m.group(0).strip() for m in SOSPETTE.finditer(testo)):
        print("  !! frase da leggere: «%s»" % m)
    print("  AZIONE    : %s" % azione)


A_auto = [x for x in A if not dubbio(x)]
A_mano = [x for x in A if dubbio(x)]

print("\n\n" + "#" * 72)
print("# GRUPPO A — spedizione scritta nella ZONA")
print("# consegna='spedizione', spedizione_sats=0, + notifica")
print("#" * 72)
for x in A_auto:
    scheda(x, "zona", "consegna='spedizione', costo 0  +  notifica")
if not A_auto:
    print("\n  (nessuno)")

if A_mano:
    print("\n\n" + "#" * 72)
    print("# GRUPPO A ma DA GUARDARE A MANO — il testo nomina una cifra")
    print("# o nega la spedizione: il costo 0 sarebbe una promessa falsa,")
    print("# e a pagarla sarebbe il venditore. Fuori dall'automatico.")
    print("#" * 72)
    for x in A_mano:
        scheda(x, "zona", "NIENTE in automatico — decidiamo insieme")

print("\n\n" + "#" * 72)
print("# GRUPPO B — spedizione solo nella DESCRIZIONE")
print("# NESSUNA scrittura: solo la notifica-domanda al venditore")
print("#" * 72)
for x in B:
    scheda(x, "descrizione", "solo notifica — decide il venditore")
if not B:
    print("\n  (nessuno)")

if nostr:
    print("\n\n" + "#" * 72)
    print("# IMPORTATI DA NOSTR — si saltano (comandano i relay)")
    print("#" * 72)
    for x in nostr:
        print("  #%d  %s" % (x["id"], x["titolo"][:56]))

print("\n" + "=" * 72)
print("RIEPILOGO")
print("  da scrivere in automatico (A) ........ %d" % len(A_auto))
print("  gruppo A da guardare a mano .......... %d" % len(A_mano))
print("  da avvisare soltanto (B) ............. %d" % len(B))
print("  importati da Nostr, saltati .......... %d" % len(nostr))
senza = [x for x in A_auto + A_mano + B
         if not avvisabile(con.execute(
             "SELECT tg_id, npub, npub_verificata, npub_accesso, "
             "canale_notifiche FROM utenti WHERE tg_id=?",
             (x["venditore_id"],)).fetchone())[0]]
if senza:
    print("  ATTENZIONE: %d venditori senza canale — la notifica non "
          "arriverebbe (id: %s)" % (len(senza), ", ".join(str(x["id"]) for x in senza)))
print("\nNessun dato e' stato modificato.")
print("=" * 72)
con.close()
