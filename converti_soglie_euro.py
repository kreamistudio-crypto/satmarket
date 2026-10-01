"""Converte in EURO le soglie delle due promesse di negozio (ago 2026).

Lo sconto carrello a valore e la spedizione gratis sopra soglia sono
nati con la soglia in SATS. Il problema di quella scelta e' che una
soglia in sats DERIVA COL CAMBIO: chi ha scritto 100.000 pensando
«circa 90 €» si ritrova, sei mesi dopo, una promessa da 180 € senza
aver toccato niente. Dall'agosto 2026 le soglie sono in euro, in
colonne NUOVE — le vecchie restano intatte e inerti, che una colonna
non cambia mai significato.

Questo script fa il travaso, UNA volta. A conversione fatta le vecchie
colonne non le legge piu' nessuno, ma restano dove sono: sono anche
l'unico posto dove ritrovare cosa il venditore aveva scritto.

PERCHE' NON LO FA init_db DA SOLA, ed e' la ragione per cui esiste
questo file: la migrazione d'avvio e' sincrona e senza rete, mentre qui
serve il cambio. Una migrazione che dipende da CoinGecko puo' restare a
meta' — e non su una riga che decide del denaro. Meglio un gesto, con
un umano che guarda le cifre prima di dire di si'.

    python converti_soglie_euro.py                 # anteprima, non scrive
    python converti_soglie_euro.py --scrivi        # fa la conversione
    python converti_soglie_euro.py --cambio 92000  # cambio a mano
    python converti_soglie_euro.py copia.db --scrivi   # su un altro db

Anteprima di serie e `--scrivi` per farla davvero: il pattern di
assegna_sottocategorie.py e ripulisci_anello_nostr.py. Idempotente —
tocca solo le righe che hanno la vecchia soglia piena e la nuova a
zero, quindi rilanciarlo non fa niente.
"""
import json
import sqlite3
import sys
import urllib.request

# Le cinture del server, ripetute qui perche' lo script gira da solo e
# non importa server.py (che vorrebbe config.py, anthropic e mezzo
# mondo). Sono minimi, non tarature: se il config del VPS li alza, una
# soglia convertita sotto il minimo verra' semplicemente ignorata dal
# giudice — e lo script lo dice.
MIN_EUR = 1

COLONNE = (
    # (in sats, in euro, la colonna della valuta, come si chiama per un
    # umano)
    ("sconto_pacco_valore", "sconto_pacco_valore_eur",
     "sconto_pacco_valore_valuta", "sconto carrello a valore"),
    ("sped_gratis_soglia", "sped_gratis_soglia_eur",
     "sped_gratis_valuta", "spedizione gratis"),
)


def cambio_da_coingecko():
    """EUR per BTC. Nessuna cache e nessun ripiego: se non risponde lo
    script si ferma e lo dice — una conversione col cambio sbagliato e'
    peggio di una conversione non fatta, e qui non c'e' fretta."""
    url = ("https://api.coingecko.com/api/v3/simple/price"
           "?ids=bitcoin&vs_currencies=eur")
    with urllib.request.urlopen(url, timeout=15) as r:
        return float(json.load(r)["bitcoin"]["eur"])


def in_euro(sats, cambio):
    """La conversione, e l'arrotondamento e' all'euro PIU' VICINO —
    non per difetto come _eur_interi. La ragione e' che li' si misura
    un carrello (e sbagliare per difetto vuol dire «non scatta», il
    verso prudente), qui invece si traduce una PROMESSA: 92.000 sats
    devono diventare «85 €» e non «84 €», o si sposterebbe di un euro
    quello che il venditore aveva deciso."""
    return max(MIN_EUR, round(sats * cambio / 100_000_000))


def main():
    argv = sys.argv[1:]
    scrivi = "--scrivi" in argv
    argv = [a for a in argv if a != "--scrivi"]
    cambio = 0.0
    if "--cambio" in argv:
        i = argv.index("--cambio")
        try:
            cambio = float(argv[i + 1].replace(",", "."))
        except (IndexError, ValueError):
            print("⚠️  --cambio vuole un numero, es. --cambio 92000")
            return 1
        del argv[i:i + 2]
    percorso = argv[0] if argv else None
    if percorso is None:
        try:
            from config import DB as percorso
        except ImportError:
            percorso = "satmarket.db"

    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(percorso, timeout=15)
    con.row_factory = sqlite3.Row
    # Chi ha una soglia vecchia piena e la nuova ancora a zero: e'
    # esattamente la popolazione che in questo momento ha una promessa
    # in vetrina che NON scatta piu'.
    # LA VALUTA E' NELLA WHERE (ago 2026, il cantiere della scelta), e
    # senza sarebbe un danno vero: «soglia in sats piena e soglia in
    # euro a zero» adesso e' la firma di chi ha SCELTO i sats, e questo
    # script gli sovrascriverebbe la cifra in euro — cioe' gli
    # cancellerebbe in silenzio quello che aveva scritto nell'altra
    # unita', proprio la cifra che il toggle serve a ritrovare. Si
    # tocca solo chi la promessa ce l'ha dichiarata in EURO.
    da_fare = []
    for vecchia, nuova, valuta, _ in COLONNE:
        try:
            righe = con.execute(
                f"SELECT tg_id, nome, {vecchia} AS sats FROM utenti "
                f"WHERE {vecchia} > 0 AND {nuova} = 0 "
                f"AND {valuta} = 'eur'").fetchall()
        except sqlite3.OperationalError as e:
            print(f"⚠️  Colonna assente ({e}): il database non ha ancora "
                  f"fatto la migrazione — avvia il server una volta.")
            return 1
        for r in righe:
            da_fare.append((vecchia, nuova, r["tg_id"], r["nome"], r["sats"]))

    if not da_fare:
        print("✅ Nessuna soglia da convertire: tutte le promesse "
              "parlano già euro.")
        con.close()
        return 0

    if cambio <= 0:
        try:
            cambio = cambio_da_coingecko()
        except Exception as e:
            print(f"⚠️  Il cambio non risponde ({e}). Riprova più tardi, "
                  f"oppure passalo a mano: --cambio 92000")
            con.close()
            return 1
    print(f"💶 Cambio usato: 1 BTC = {cambio:,.0f} €".replace(",", "."))
    print(f"   {len(da_fare)} soglie da convertire "
          f"{'(SCRIVO)' if scrivi else '(anteprima: non scrivo niente)'}\n")

    per_colonna = {}
    for vecchia, nuova, tg_id, nome, sats in da_fare:
        eur = in_euro(sats, cambio)
        etichetta = next(e for v, _, _c, e in COLONNE if v == vecchia)
        limato = "  ← limato al minimo" if eur == MIN_EUR and sats else ""
        print(f"  {etichetta:26} {(nome or '')[:20]:20} "
              f"{sats:>10,} sats → {eur:>5} €{limato}".replace(",", "."))
        if scrivi:
            con.execute(f"UPDATE utenti SET {nuova}=? WHERE tg_id=?",
                        (eur, tg_id))
        per_colonna[nuova] = per_colonna.get(nuova, 0) + 1

    if scrivi:
        con.commit()
        print(f"\n✅ Fatto: {len(da_fare)} soglie convertite. Le colonne "
              f"in sats restano dov'erano, inerti.")
    else:
        print(f"\n👀 Anteprima soltanto. Per farla davvero: "
              f"python converti_soglie_euro.py --scrivi")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
