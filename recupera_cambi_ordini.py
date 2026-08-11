"""Recupera il cambio del giorno degli ordini di prima (ago 2026).

Dall'agosto 2026 ogni ordine si porta dietro il cambio del giorno in
cui e' nato: quanto valeva in euro quell'affare e' un FATTO
dell'affare, come il prezzo, e non deve cambiare piu'. Prima invece
`ordini.cambio_ordine` si riempiva SOLO dove serviva a convertire
qualcosa (listino in euro, tariffa ancorata), quindi di un ordine
tutto-sats non resta scritto niente — e l'unico modo di raccontarlo
sarebbe il cambio di OGGI, cioe' un numero che cambia ogni giorno su
un fatto che non cambia piu'.

Questo script chiede a CoinGecko il prezzo del GIORNO di ogni ordine
scoperto e riempie la colonna. UNA volta, a mano, guardando.

    python recupera_cambi_ordini.py                # anteprima, ZERO chiamate
    python recupera_cambi_ordini.py --scrivi       # la passata vera
    python recupera_cambi_ordini.py --pausa 20     # piu' lento (429)
    python recupera_cambi_ordini.py copia.db --scrivi   # su un altro db

UNA CHIAMATA PER GIORNO, non per ordine: dieci ordini dello stesso
giorno valgono lo stesso cambio. E L'ANTEPRIMA NON NE SPENDE NESSUNA —
legge i giorni dal database e dice quante ne serviranno: e' quello il
numero da guardare prima di dire di si', visto che dall'altra parte
c'e' un servizio a consumo.

TRE COSE MISURATE SU COINGECKO prima di scegliere questa strada, e
vanno rimisurate se un domani smettesse di funzionare:
 - l'endpoint storico e' PUBBLICO e senza chiave (`/coins/bitcoin/
   history`), risponde `market_data.current_price.eur`;
 - arriva indietro 365 GIORNI e non oltre: piu' in la' e' un 401 con
   «Public API users are limited to querying historical data within
   the past 365 days». Oggi copre tutto (Barattolo incassa da luglio
   2026); fra un anno non piu', e allora lo script lo dira' invece di
   lasciare un buco in silenzio;
 - il rate limit e' STRETTO: quattro chiamate di fila e arriva un 429.
   Da qui la pausa generosa e il ritentativo.

IL PREZZO E' QUELLO DEL GIORNO, NON DELL'ISTANTE (imperfezione
dichiarata): su una giornata mossa il valore recuperato puo'
scostarsi da quanto valeva davvero al minuto dell'ordine. Resta un
fatto vero e fermo, riguarda solo gli ordini di prima — i nuovi hanno
l'istante — e in vetrina quella cifra porta comunque il «≈».

SI SCRIVE SOLO `cambio_ordine`, e SOLO dove e' a zero: nessun'altra
colonna di `ordini` viene toccata, mai (c'e' una sentinella in
prove.py che lo verifica sul corpo di questo file). Quindi rilanciarlo
non fa niente, e si puo' interrompere a meta' — ogni giorno si scrive
e si committa per conto suo, e al rilancio riparte da dove era.
"""
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request

URL = ("https://api.coingecko.com/api/v3/coins/bitcoin/history"
       "?date={}&localization=false")

# La cintura contro una risposta malformata, non un giudizio sul
# mercato: un BTC non e' mai valso 12 euro ne' dieci milioni, e un
# numero cosi' dentro la tabella dei soldi non ci deve entrare
# nemmeno per sbaglio. Fuori scala = si dice e si salta il giorno.
MIN_PLAUSIBILE = 1_000
MAX_PLAUSIBILE = 10_000_000

PAUSA = 15          # secondi fra una chiamata e l'altra (il 429 e' vero)
TENTATIVI = 3       # per giorno, con l'attesa che si allunga


def plur(n, uno, molti):
    """«1 ordine» e non «1 ordini»: qui i numeri piccoli sono la
    norma — un solo giorno scoperto e' il caso tipico dopo la prima
    passata — e una riga sgrammaticata su uno strumento dei soldi si
    legge come una cosa scritta di fretta."""
    return f"{n} {uno if n == 1 else molti}"


def giorni_scoperti(con):
    """I giorni (in UTC, come lo snapshot di CoinGecko) degli ordini
    che il cambio non ce l'hanno, dal piu' vecchio. Il formato e'
    gia' quello che vuole l'endpoint: dd-mm-yyyy."""
    return con.execute(
        "SELECT strftime('%d-%m-%Y', creato, 'unixepoch') AS giorno, "
        "       COUNT(*) AS quanti, MIN(creato) AS primo "
        "FROM ordini WHERE cambio_ordine = 0 AND creato > 0 "
        "GROUP BY giorno ORDER BY primo").fetchall()


def cambio_del_giorno(giorno, pausa):
    """EUR per BTC di quel giorno. Torna (valore, motivo): uno dei due
    e' sempre vuoto. Non alza mai — un giorno che non si recupera non
    deve fermare gli altri."""
    for tentativo in range(1, TENTATIVI + 1):
        try:
            req = urllib.request.Request(
                URL.format(giorno), headers={"User-Agent": "barattolo/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                dati = json.load(r)
            eur = (dati.get("market_data", {})
                       .get("current_price", {}).get("eur"))
            if not eur:
                return 0.0, "CoinGecko non ha il prezzo di quel giorno"
            return float(eur), ""
        except urllib.error.HTTPError as e:
            if e.code == 429 and tentativo < TENTATIVI:
                attesa = pausa * (tentativo + 1)
                print(f"      (429: aspetto {attesa}s e riprovo)")
                time.sleep(attesa)
                continue
            if e.code == 401:
                return 0.0, ("oltre i 365 giorni che l'API pubblica "
                             "concede")
            return 0.0, f"HTTP {e.code}"
        except Exception as e:                    # rete, timeout, JSON
            if tentativo < TENTATIVI:
                time.sleep(pausa)
                continue
            return 0.0, str(e)
    return 0.0, "troppi tentativi"


def main():
    argv = sys.argv[1:]
    scrivi = "--scrivi" in argv
    argv = [a for a in argv if a != "--scrivi"]
    pausa = PAUSA
    if "--pausa" in argv:
        i = argv.index("--pausa")
        try:
            pausa = max(0, int(argv[i + 1]))
        except (IndexError, ValueError):
            print("⚠️  --pausa vuole un numero di secondi, es. --pausa 20")
            return 1
        del argv[i:i + 2]
    percorso = argv[0] if argv else None
    if percorso is None:
        try:
            from config import DB as percorso
        except ImportError:
            percorso = "satmarket.db"

    con = sqlite3.connect(percorso)
    con.row_factory = sqlite3.Row
    try:
        giorni = giorni_scoperti(con)
    except sqlite3.OperationalError as e:
        print(f"⚠️  Non riesco a leggere gli ordini ({e}).")
        con.close()
        return 1

    if not giorni:
        print("✅ Nessun ordine scoperto: tutti sanno già quanto valevano.")
        con.close()
        return 0

    ordini = sum(g["quanti"] for g in giorni)
    limite = time.time() - 365 * 86400
    fuori = [g for g in giorni if g["primo"] < limite]
    minuti = len(giorni) * pausa // 60 + 1
    print(f"\n📅 {plur(ordini, 'ordine senza cambio', 'ordini senza cambio')}, "
          f"su {plur(len(giorni), 'giorno', 'giorni distinti')}")
    print(f"   {plur(len(giorni), 'chiamata', 'chiamate')} a CoinGecko, una "
          f"per giorno, ~{pausa}s l'una → circa "
          f"{plur(minuti, 'minuto', 'minuti')}\n")
    for g in giorni:
        nota = "  ⚠️ oltre i 365 giorni: non recuperabile" if g in fuori else ""
        print(f"   {g['giorno']}   {g['quanti']:>3} "
              f"{'ordine ' if g['quanti'] == 1 else 'ordini'}{nota}".rstrip())
    if fuori:
        quanti = plur(len(fuori), "giorno è troppo vecchio",
                      "giorni sono troppo vecchi")
        print(f"\n   {quanti} per l'API pubblica: quegli ordini resteranno\n"
              f"   senza euro, che è la risposta onesta — non si ripiega "
              f"sul cambio di oggi.")

    if not scrivi:
        print(f"\n👀 Anteprima soltanto: nessuna chiamata fatta, niente "
              f"scritto.\n   Per farla davvero: "
              f"python recupera_cambi_ordini.py --scrivi\n")
        con.close()
        return 0

    print(f"\n▶️  Vado. Si può interrompere: ogni giorno si scrive per "
          f"conto suo,\n   e al rilancio riparte da dove era.\n")
    scritti, saltati = 0, 0
    for n, g in enumerate(giorni, 1):
        if n > 1 and pausa:
            time.sleep(pausa)
        giorno = g["giorno"]
        eur, motivo = cambio_del_giorno(giorno, pausa)
        if not eur:
            print(f"   {giorno}  saltato — {motivo}")
            saltati += g["quanti"]
            continue
        if not MIN_PLAUSIBILE <= eur <= MAX_PLAUSIBILE:
            print(f"   {giorno}  saltato — cifra fuori scala ({eur}): "
                  f"non la scrivo")
            saltati += g["quanti"]
            continue
        # SOLO `cambio_ordine`, e SOLO dove e' ancora a zero: la
        # clausola non e' cosmesi, e' cio' che rende la passata
        # ripetibile e innocua se nel frattempo qualcosa l'ha riempita.
        tocchi = con.execute(
            "UPDATE ordini SET cambio_ordine = ? "
            "WHERE cambio_ordine = 0 AND creato > 0 "
            "AND strftime('%d-%m-%Y', creato, 'unixepoch') = ?",
            (eur, giorno)).rowcount
        con.commit()
        scritti += tocchi
        cifra = f"{eur:>12,.2f}".replace(",", "@").replace(".", ",") \
                                .replace("@", ".")
        print(f"   {giorno}  1 BTC = {cifra} €   → "
              f"{plur(tocchi, 'ordine', 'ordini')}")

    print(f"\n✅ Fatto: {plur(scritti, 'ordine sa', 'ordini sanno')} di nuovo "
          f"quanto valeva{'' if scritti == 1 else 'no'}.")
    if saltati:
        print(f"   {plur(saltati, 'resta', 'restano')} senza: in vetrina "
              f"diranno i sats e basta,\n   mai un euro che non abbiamo.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
