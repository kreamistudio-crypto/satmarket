"""Ripubblica su Nostr gli annunci attivi firmati dalla PIATTAFORMA
col tag `client` di Barattolo (NIP-89), e pubblica l'evento handler
kind 31990 della piattaforma. Una tantum, dopo il deploy del tag.

COSA FA
- Pubblica (o sostituisce: e' addressable, d="barattolo") l'evento
  handler kind 31990 di Barattolo, firmato dalla chiave di piattaforma.
- Rilegge gli annunci ATTIVI nativi con un evento in piazza firmato da
  NOI (contatto_nostr='' AND nostr_event_id<>'' AND nostr_autore='')
  e per ognuno ricompone l'evento con la fabbrica VERA del server
  (evento_annuncio: zero copie, o divergerebbero al primo campo nuovo)
  e lo rispedisce ai relay con lo stesso tag `d` — la sostituzione
  NIP-99, niente doppioni. Con almeno un relay OK aggiorna
  annunci.nostr_event_id, con commit PER RIGA.

COSA NON FA
- Non tocca gli eventi firmati dai VENDITORI (il BIVIO,
  nostr_autore<>''): la chiave e' loro e non si accoda niente —
  decisione di Andrea, quegli eventi si rifanno da soli alla prima
  modifica, vendita o rimborso. Lo script li CONTA e basta.
- Non tocca gli annunci importati dai relay (contatto_nostr<>'').
- Non manda mai una raffica: lotti da LOTTO_NOSTR con PAUSA_NOSTR di
  respiro, i valori del server.

USO
    python ripubblica_tag_client.py [percorso.db]            # anteprima
    python ripubblica_tag_client.py [percorso.db] --scrivi   # fa davvero
    python ripubblica_tag_client.py --scrivi --relay wss://localhost:7777
                                        # collaudo contro un relay locale

Gira SUL VPS (servono la nsec vera e il database vero). In locale si
prova col config di collaudo: senza --relay e con MODALITA_COLLAUDO
accesa gli eventi si stampano e basta; con --relay si spediscono al
relay indicato (la prova generale). Prima del giro vero: una passata
su una COPIA del database, il pattern di ripulisci_anello_nostr.py.

NOTA DICHIARATA: `import server` fa girare init_db() sul database del
CONFIG — le stesse migrazioni idempotenti di ogni riavvio. Il percorso
posizionale governa solo le letture/scritture di QUESTO script; per la
prova sulla copia conviene un config di collaudo che punti alla copia.
Idempotente: un secondo giro ricompone e sostituisce gli stessi eventi.
"""

import json
import sqlite3
import sys
import time


def main() -> int:
    scrivi = "--scrivi" in sys.argv
    argv = [x for x in sys.argv[1:] if x != "--scrivi"]
    relays_forzati = []
    while "--relay" in argv:
        i = argv.index("--relay")
        if i + 1 >= len(argv):
            print("--relay vuole un indirizzo wss://…")
            return 2
        relays_forzati.append(argv[i + 1])
        del argv[i:i + 2]

    # Config e server DENTRO main(): la CI fa solo compileall, e uno
    # script non deve chiudere il processo per una chiave che non ha
    # (la regola degli script «puri», v. ricategorizza.py).
    try:
        from config import DB, MODALITA_COLLAUDO
    except ImportError:
        print("config.py non trovato: questo script gira dove vive il "
              "config (VPS, o locale di collaudo)")
        return 2
    import server

    if server._NOSTR is None:
        print("Nostr e' spento (NOSTR_NSEC_PIATTAFORMA mancante o "
              "pacchetti assenti): niente da firmare.")
        return 2

    db = argv[0] if argv else DB
    relays = relays_forzati or list(server.RELAYS_VERIFICA)
    # In collaudo senza un relay esplicito non si spedisce niente: si
    # stampa, il patto di presenta_release.py.
    solo_stampa = MODALITA_COLLAUDO and not relays_forzati

    def spedisci(evento: dict) -> int:
        """Quanti relay hanno detto OK (in solo-stampa: tutti, finto)."""
        if solo_stampa:
            print(f"   🟣 [nostr simulato] kind {evento['kind']} "
                  f"id {evento['id'][:16]}…")
            return len(relays)
        ok = 0
        for r in relays:
            if server.invia_evento_relay(r, evento):
                ok += 1
            else:
                print(f"   ❌ {r}")
        return ok

    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(db, timeout=15)
    con.row_factory = sqlite3.Row

    # Il perimetro: i soli eventi che possiamo rifirmare NOI.
    nostri = con.execute(
        "SELECT * FROM annunci WHERE stato='attivo' AND contatto_nostr=''"
        "  AND nostr_event_id<>'' AND nostr_autore='' ORDER BY id").fetchall()
    bivio = con.execute(
        "SELECT COUNT(*) FROM annunci WHERE stato='attivo'"
        "  AND contatto_nostr='' AND nostr_event_id<>''"
        "  AND nostr_autore<>''").fetchone()[0]

    print(f"Database: {db}")
    print(f"Da ripubblicare (firma piattaforma): {len(nostri)}")
    print(f"Firmati dai venditori (BIVIO): {bivio} — non si toccano, "
          f"si rifanno da soli al primo evento naturale")
    print(f"Relay: {', '.join(relays)}"
          + ("  [SOLO STAMPA: collaudo senza --relay]" if solo_stampa else ""))
    if nostri:
        esempio = server.evento_annuncio(dict(nostri[0]), "active")
        tag = next(t for t in esempio["tags"] if t[0] == "client")
        print(f"Il tag che parte: {tag}")
        for r in nostri[:5]:
            print(f"   #{r['id']}  {r['titolo'][:60]}")
        if len(nostri) > 5:
            print(f"   … e altri {len(nostri) - 5}")

    if not scrivi:
        print("\nAnteprima: non e' partito niente. Rilancia con --scrivi.")
        con.close()
        return 0

    # L'handler NIP-89 della piattaforma: kind 31990, addressable su
    # d="barattolo" (nessuna collisione coi "barattolo-{id}": altro
    # kind). Niente template web per-evento: i nostri URL vogliono
    # l'id numerico e il bech32 non si traduce — handler minimo.
    profilo = json.dumps({
        "name": server.NOME_CLIENT_NOSTR,
        "about": "Barattolo — il mercatino in sats, con escrow Lightning",
        "picture": f"{server.URL_PUBBLICO}/assets/icona-512.png",
        "website": server.URL_PUBBLICO,
    }, ensure_ascii=False)
    handler = server.firma_evento(31990, [["d", "barattolo"],
                                          ["k", "30402"]], profilo)
    ok = spedisci(handler)
    print(f"Handler 31990: {ok}/{len(relays)} relay OK")

    fatti = saltati = 0
    for n, r in enumerate(nostri, 1):
        ev = server.evento_annuncio(dict(r), "active")
        ok = spedisci(ev)
        if ok:
            # Solo con almeno un relay OK: mai la testa di un evento
            # mai partito. Commit per riga: un crash a meta' lascia
            # solo righe complete (il patto dell'import CSV).
            con.execute("UPDATE annunci SET nostr_event_id=? WHERE id=?",
                        (ev["id"], r["id"]))
            con.commit()
            fatti += 1
            print(f"✅ #{r['id']} {r['titolo'][:50]} ({ok}/{len(relays)})")
        else:
            saltati += 1
            print(f"⛔ #{r['id']} {r['titolo'][:50]} — nessun relay OK, "
                  f"riga NON toccata (si riprova al prossimo giro)")
        if n % server.LOTTO_NOSTR == 0 and n < len(nostri):
            time.sleep(server.PAUSA_NOSTR)

    con.close()
    print(f"\nFatto: {fatti} ripubblicati, {saltati} saltati.")
    return 0 if not saltati else 1


if __name__ == "__main__":
    sys.exit(main())
