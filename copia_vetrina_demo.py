# -*- coding: utf-8 -*-
"""
🪟 LA VETRINA COPIATA NEL COLLAUDO (16 ott 2026, hackathon di Torino,
richiesta di Andrea): il Barattolo in collaudo del portatile della demo
nasce con una vetrina vuota — un negozio seminato (`semina_demo.py`) e
basta. Questo file la riempie con quel che barattolo.store mostra a
CHIUNQUE la apra: la vetrina pubblica, letta come la legge un visitatore
(`GET /api/listings`, paginata), e le foto delle rotte pubbliche `/foto/`.

COSA COPIA, e perche' cosi':
  - GLI ANNUNCI ATTIVI della vetrina pubblica, coi loro id di
    produzione (le foto si chiamano `a<id>_<n>.jpg`: tenere l'id vuol
    dire non rinominare niente). Le colonne sono quelle che la vetrina
    espone E che il database locale ha (l'incrocio con PRAGMA
    table_info): un campo calcolato dal server non diventa mai una
    colonna inventata qui.
  - I VENDITORI, coi dati che la vetrina gia' mostra a tutti (nome,
    username, npub dichiarata, codice negozio, titolo, avatar, rating,
    vendite): decisione di Andrea del 16 ott, «nomi veri». Il loro
    tg_id NON e' pubblico e non si copia: ogni venditore riceve un id
    finto locale, da ID_BASE in su, sempre lo stesso a ogni giro.
  - LE FOTO degli annunci (con le miniature `_min`, se ci sono) e gli
    avatar, nella cartella `foto/` accanto al codice, come le scrive il
    server. Una foto gia' scaricata non si riscarica.
  - Le famiglie arrivano col solo capofila, come in vetrina: le
    varianti sorelle non sono nella risposta pubblica.

COSA NON FA: niente ordini, chat, indirizzi, saldi, feedback, utenti
che non vendono — non sono pubblici e non servono a una vetrina. Niente
VPS, niente database di produzione, niente chiavi: solo HTTPS verso le
rotte pubbliche, con un User-Agent che si dichiara.

FAIL-CLOSED, come la semina: senza `MODALITA_COLLAUDO = True` nel config
non scrive un byte; vuole il database che il server ha gia' creato, e
controlla le tabelle prima di scrivere. Niente `import server`.
Rilanciarlo aggiorna (gli annunci copiati prima si riscrivono, quelli
spariti dalla vetrina vera restano finche' non si usa `--rifai`).

USO (dalla cartella del repo, col server acceso o spento):
  .venv/bin/python copia_vetrina_demo.py            # copia tutto
  .venv/bin/python copia_vetrina_demo.py --rifai    # toglie prima i copiati di ieri
  .venv/bin/python copia_vetrina_demo.py stato      # quanti ce ne sono, senza scrivere
Opzioni: --db PERCORSO (default: `DB` del config), --sorgente URL
(default https://barattolo.store), --max N (solo i primi N, per provare).
Per prove: COPIA_CARTELLA_FOTO sposta la cartella delle foto.
"""
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

QUI = os.path.dirname(os.path.abspath(__file__))
SORGENTE = "https://barattolo.store"
ID_BASE = 7_000_000            # i venditori copiati: 7000001, 7000002, …
PAGINA = 100                   # LIMITE_PAGINA_MAX del server
AGENTE = "barattolo-copia-vetrina-demo/1 (collaudo locale, hackathon Torino)"
PARALLELE = 4                  # scaricamenti insieme: gentili col server vero
# Un nome di file come quelli che `foto/` ammette: lettere, cifre, _ . -
# e niente barre. Un URL (le foto degli annunci importati da Nostr) non
# si scarica: resta un URL, e la pagina lo mostra da li'.
NOME_SICURO = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,120}$")

# Le colonne di `utenti` e la voce della vetrina da cui si leggono.
VENDITORE = {
    "nome": "venditore", "username": "venditore_username",
    "npub": "venditore_npub", "npub_verificata": "venditore_npub_verificata",
    "negozio": "venditore_negozio", "titolo": "venditore_titolo",
    "ferie_fino": "venditore_ferie", "avatar": "venditore_avatar",
    "rating": "rating", "vendite_ok": "vendite_ok",
    "sconto_pacco_criterio": "venditore_sconto_criterio",
    "sconto_pacco_valore_valuta": "venditore_sconto_valuta",
    "sconto_pacco_soglia": "venditore_sconto_soglia",
    "sconto_pacco_valore": "venditore_sconto_valore",
    "sconto_pacco_valore_eur": "venditore_sconto_valore_eur",
    "sconto_pacco_percento": "venditore_sconto_percento",
    "sped_gratis_valuta": "venditore_sped_gratis_valuta",
    "sped_gratis_soglia": "venditore_sped_gratis",
    "sped_gratis_soglia_eur": "venditore_sped_gratis_eur",
}


class CopiaFerma(Exception):
    """Un motivo per non scrivere niente, detto in chiaro."""


def _config():
    try:
        import config
    except ImportError:
        raise CopiaFerma("manca config.py: la copia legge MODALITA_COLLAUDO e "
                         "DB da li' (copia config_esempio.py e metti "
                         "MODALITA_COLLAUDO = True)")
    if getattr(config, "MODALITA_COLLAUDO", False) is not True:
        raise CopiaFerma("MODALITA_COLLAUDO non e' True nel config: la copia "
                         "scrive SOLO su un database di collaudo")
    return config


def colonne(con, tabella: str) -> set:
    return {r[1] for r in con.execute(f"PRAGMA table_info({tabella})")}


def controlla_schema(con) -> None:
    for tabella, servono in (("annunci", {"id", "venditore_id", "titolo",
                                          "prezzo_sats", "foto", "stato"}),
                             ("utenti", {"tg_id", "nome", "username"})):
        mancano = servono - colonne(con, tabella)
        if mancano:
            raise CopiaFerma(f"la tabella {tabella} non ha {sorted(mancano)}: "
                             "il database non e' quello del server (avvialo "
                             "una volta e rilancia)")


def leggi_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def leggi_vetrina(sorgente: str, massimo: int = 0) -> list:
    """Tutti gli annunci della vetrina pubblica, pagina per pagina."""
    annunci, cursore = [], ""
    while True:
        url = f"{sorgente}/api/listings?limit={PAGINA}"
        if cursore:
            url += "&cursore=" + urllib.request.quote(cursore, safe="")
        pagina = leggi_json(url)
        annunci += pagina.get("annunci") or []
        cursore = pagina.get("cursore") or ""
        print(f"  … {len(annunci)} di {pagina.get('totale', '?')} annunci letti")
        if not cursore or (massimo and len(annunci) >= massimo):
            break
    return annunci[:massimo] if massimo else annunci


def _testo(v):
    """Un valore della vetrina come lo vuole una colonna TEXT: le liste e
    gli oggetti (foto, opzioni) tornano nel JSON da cui il server li ha
    letti."""
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v


def nomi_foto(annuncio: dict) -> list:
    foto = annuncio.get("foto") or []
    if isinstance(foto, str):
        try:
            foto = json.loads(foto) if foto.strip().startswith("[") else [foto]
        except ValueError:
            foto = [foto]
    return [f for f in foto if isinstance(f, str) and NOME_SICURO.match(f)]


def scarica(sorgente: str, cartella: str, nome: str, facoltativa=False) -> str:
    """'nuova', 'c-era', 'manca' (404 di una facoltativa) o 'errore …'."""
    dest = os.path.join(cartella, nome)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "c-era"
    req = urllib.request.Request(f"{sorgente}/foto/{nome}",
                                 headers={"User-Agent": AGENTE})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            dati = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404 and facoltativa:
            return "manca"
        return f"errore {e.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return f"errore {e}"
    temporaneo = dest + ".parziale"
    with open(temporaneo, "wb") as f:
        f.write(dati)
    os.replace(temporaneo, dest)
    return "nuova"


def ids_venditori(con, annunci: list) -> dict:
    """Venditore della vetrina → id locale, stabile fra un giro e l'altro:
    se un venditore copiato ieri c'e' gia' (stesso codice negozio, o
    stesso nome e username), riprende il suo id."""
    gia = {}
    for r in con.execute("SELECT tg_id, nome, username, negozio FROM utenti "
                         "WHERE tg_id > ?", (ID_BASE,)):
        gia[r[3] or f"{r[1]}|{r[2]}"] = r[0]
    prossimo = max(gia.values(), default=ID_BASE) + 1
    mappa = {}
    for a in annunci:
        chiave = a.get("venditore_negozio") or f"{a.get('venditore')}|{a.get('venditore_username')}"
        if chiave in mappa:
            continue
        if chiave in gia:
            mappa[chiave] = gia[chiave]
        else:
            mappa[chiave] = prossimo
            prossimo += 1
    return mappa


def scrivi(con, annunci: list, adesso: int, rifai: bool) -> dict:
    col_annunci = colonne(con, "annunci")
    col_utenti = colonne(con, "utenti")
    if rifai:
        tolti = con.execute("DELETE FROM annunci WHERE venditore_id > ?",
                            (ID_BASE,)).rowcount
        print(f"  --rifai: tolti {tolti} annunci copiati prima")
    mappa = ids_venditori(con, annunci)
    venditori = scritti = saltati = 0
    visti = set()
    for a in annunci:
        chiave = a.get("venditore_negozio") or f"{a.get('venditore')}|{a.get('venditore_username')}"
        tg_id = mappa[chiave]
        if tg_id not in visti:
            visti.add(tg_id)
            riga = {"tg_id": tg_id, "registrato": adesso}
            for colonna, voce in VENDITORE.items():
                if colonna in col_utenti and a.get(voce) is not None:
                    riga[colonna] = _testo(a[voce])
            riga = {k: v for k, v in riga.items() if k in col_utenti or k == "tg_id"}
            nomi = ", ".join(riga)
            segni = ", ".join("?" * len(riga))
            aggiorna = ", ".join(f"{k}=excluded.{k}" for k in riga if k != "tg_id")
            con.execute(f"INSERT INTO utenti({nomi}) VALUES({segni}) "
                        f"ON CONFLICT(tg_id) DO UPDATE SET {aggiorna}",
                        list(riga.values()))
            venditori += 1
        # l'annuncio: un id di produzione che localmente e' di qualcun
        # altro (un annuncio seminato o scritto a mano) non si tocca
        r = con.execute("SELECT venditore_id FROM annunci WHERE id=?",
                        (a["id"],)).fetchone()
        if r and r[0] is not None and r[0] <= ID_BASE:
            saltati += 1
            continue
        riga = {k: _testo(v) for k, v in a.items()
                if k in col_annunci and k not in ("venditore_id", "stato")}
        riga["venditore_id"] = tg_id
        riga["stato"] = "attivo"
        riga.setdefault("creato", adesso)
        nomi = ", ".join(riga)
        segni = ", ".join("?" * len(riga))
        con.execute(f"INSERT OR REPLACE INTO annunci({nomi}) VALUES({segni})",
                    list(riga.values()))
        scritti += 1
    return {"venditori": venditori, "annunci": scritti, "saltati": saltati}


def scarica_tutte(sorgente: str, cartella: str, annunci: list) -> dict:
    lavori = []
    for a in annunci:
        for n in nomi_foto(a):
            lavori.append((n, False))
            if re.match(r"^a\d+_\d+(_\d+)?\.(jpg|png|webp|gif)$", n):
                lavori.append((n.rsplit(".", 1)[0] + "_min.jpg", True))
        av = a.get("venditore_avatar")
        if isinstance(av, str) and NOME_SICURO.match(av):
            lavori.append((av, False))
    lavori = list(dict.fromkeys(lavori))
    os.makedirs(cartella, exist_ok=True)
    conto, errori = {}, []
    print(f"  … {len(lavori)} file da guardare in {cartella}")
    with ThreadPoolExecutor(PARALLELE) as pool:
        for (nome, _), esito in zip(lavori, pool.map(
                lambda l: scarica(sorgente, cartella, l[0], l[1]), lavori)):
            tipo = esito.split()[0]
            conto[tipo] = conto.get(tipo, 0) + 1
            if tipo == "errore":
                errori.append(f"{nome}: {esito}")
    return {"conto": conto, "errori": errori}


def stato(con) -> dict:
    return {
        "venditori_copiati": con.execute(
            "SELECT COUNT(*) FROM utenti WHERE tg_id > ?", (ID_BASE,)).fetchone()[0],
        "annunci_copiati": con.execute(
            "SELECT COUNT(*) FROM annunci WHERE venditore_id > ? AND stato='attivo'",
            (ID_BASE,)).fetchone()[0],
        "annunci_attivi_in_tutto": con.execute(
            "SELECT COUNT(*) FROM annunci WHERE stato='attivo'").fetchone()[0],
    }


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    opzioni = {"--db": "", "--sorgente": SORGENTE, "--max": "0"}
    for nome in list(opzioni):
        while nome in argv:
            i = argv.index(nome)
            try:
                opzioni[nome] = argv[i + 1]
            except IndexError:
                print(f"{nome} vuole un valore")
                return 2
            del argv[i:i + 2]
    rifai = "--rifai" in argv
    argv = [x for x in argv if x != "--rifai"]
    comando = argv[0] if argv else "copia"
    if comando not in ("copia", "stato") or len(argv) > 1:
        print(__doc__.split("USO")[1])
        return 2
    try:
        massimo = int(opzioni["--max"])
    except ValueError:
        print("--max vuole un numero")
        return 2
    sorgente = opzioni["--sorgente"].rstrip("/")
    if not sorgente.startswith("https://"):
        print("--sorgente vuole un indirizzo https://")
        return 2
    try:
        cfg = _config()
        percorso = opzioni["--db"] or getattr(cfg, "DB", "satmarket.db")
        if not os.path.isabs(percorso):
            percorso = os.path.join(QUI, percorso)
        if not os.path.exists(percorso):
            raise CopiaFerma(f"il database {percorso} non esiste: avvia "
                             "Barattolo una volta (lo crea lui) e rilancia")
        con = sqlite3.connect(percorso, timeout=15)
        try:
            controlla_schema(con)
            if comando == "stato":
                for k, v in stato(con).items():
                    print(f"{k}: {v}")
                return 0
            print(f"🪟 Leggo la vetrina pubblica di {sorgente} …")
            annunci = leggi_vetrina(sorgente, massimo)
            adesso = int(time.time())
            esito = scrivi(con, annunci, adesso, rifai)
            con.commit()
            print(f"✓ {esito['annunci']} annunci di {esito['venditori']} "
                  f"venditori scritti in {percorso}"
                  + (f" ({esito['saltati']} saltati: il loro id qui e' di "
                     "un annuncio locale)" if esito["saltati"] else ""))
        finally:
            con.close()
        cartella = (os.environ.get("COPIA_CARTELLA_FOTO")
                    or os.path.join(QUI, "foto"))
        print("📷 Le foto …")
        f = scarica_tutte(sorgente, cartella, annunci)
        print("✓ foto: " + ", ".join(f"{k} {v}" for k, v in sorted(f["conto"].items())))
        for riga in f["errori"][:10]:
            print("  ✗", riga)
        if len(f["errori"]) > 10:
            print(f"  … e altri {len(f['errori']) - 10} errori")
        return 0
    except CopiaFerma as e:
        print(f"✋ {e}")
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"✗ la vetrina pubblica non risponde come dovrebbe: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
