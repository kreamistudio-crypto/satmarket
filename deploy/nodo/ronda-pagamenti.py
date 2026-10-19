#!/usr/bin/env python3
# ronda-pagamenti.py — il giudice dei PAGAMENTI usciti dal nodo, ogni ora.
# Nato il 28 set 2026, quando il nodo ha cominciato a pagare tutti i
# giorni (payout del mercatino dalla cassaforte nodo, payout P2P di
# mostrod) e la ronda di prima chiamava «SCONOSCIUTO» ogni pagamento non
# imparato con --impara: 63 allarmi falsi in una settimana, e un furto
# vero si sarebbe letto in mezzo a loro — una volta a settimana.
#
# UN PAGAMENTO E' CONOSCIUTO SE UNA FONTE LO SPIEGA, e le fonti sono
# quattro, chieste in quest'ordine (prima quelle della macchina, poi
# quella che costa un giro su Tor):
#   1) mostro.db, in SOLA LETTURA: l'hash della fattura del compratore
#      (buyer_invoice decodificata qui), della dev fee, di un payout in
#      volo (payout_payment_hash);
#   2) i log di mostrod: le righe «Invoice with hash: … paid!», quelle
#      della dev fee e quelle del payout andato in timeout («keeping
#      payout claim for hash …») — la sola strada per i payout a un
#      Lightning address, di cui il database non tiene l'hash;
#   3) un FAILED seguito da un SUCCEEDED dello stesso importo verso la
#      stessa destinazione: un ritentativo, che non ha mosso niente;
#   4) il VPS di Barattolo, POST /api/nodo/pagamenti-noti via Tor, che
#      risponde solo si'/no per ogni hash (payout_tentati e i payout_hash
#      delle tre tabelle che pagano).
# Quello che nessuna fonte spiega ALLARMA SUBITO, una volta, con cifra,
# destinazione, descrizione e cosa fare. Quello che non si e' potuto
# VERIFICARE (VPS muto, mostro.db illeggibile) aspetta: allarma solo se
# resta non verificato per piu' di tre ore.
#
# NON SCRIVE NIENTE FUORI DA /var/lib/ronda: lncli listpayments,
# listchannels, getinfo e decodepayreq sono letture, mostro.db si apre
# in mode=ro, i log si leggono e basta. Il segreto del VPS sta in
# /etc/ronda/barattolo.env (root, 600) e non passa MAI da una riga di
# comando: curl lo legge da stdin (-K -), cosi' `ps` non lo vede.
#
# Vive in /usr/local/bin sul nodo e lo chiama ronda-nodo.sh; questa e'
# la COPIA nel repo (deploy/nodo/), con la regola del relay: chi tocca
# il file di la' lo riporta qui nello stesso giro. Le prove stanno in
# prove.py, «prove_ronda_nodo».
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

LND = "nodo-lnd-1"
MOSTRO = "nodo-mostro-1"
DB_MOSTRO = "/home/debian/nodo/mostro/mostro.db"
SEGRETI = "/etc/ronda/barattolo.env"
TOR_SOCKS = "172.28.1.3:9050"    # il tor del compose, lo stesso di ronda.sh
AVVISA = "/usr/local/bin/ronda-avvisa.sh"
CARTELLA = "/var/lib/ronda"
# «hash fonte», una riga per pagamento spiegato. Le righe di prima
# (solo l'hash, scritte da --impara fino al 28 set 2026) valgono come
# «imparato»: il file vecchio si legge senza migrazioni.
NOTI = "pagamenti_noti"
# «hash primo_tentativo motivo»: i non verificati, col QUANDO della
# prima volta che non si e' potuto. Il conto delle tre ore parte da li'
# e non dalla nascita del pagamento: una ronda rimasta spenta un giorno
# non deve allarmare al primo giro su un VPS che ha solo un singhiozzo.
ATTESA = "pagamenti_in_attesa"
# «hash quando»: gli allarmi gia' partiti. Un pagamento sconosciuto si
# grida UNA volta; poi lo ripete il riassunto di ogni giorno finche'
# qualcuno non lo riconosce o non lo impara.
ALLARMATI = "pagamenti_allarmati"
# «chiave primo ultimo_avviso»: i guasti che durano (lncli muto, nessun
# canale, HTLC vicino alla scadenza). Un guasto che resta vero non si
# grida ogni ora: la prima volta, e poi una volta al giorno.
GUASTI = "guasti"
# «giorno»: il riassunto di quel giorno e' partito. Un giro lungo
# rifatto dopo un Telegram caduto non lo manda due volte.
RIASSUNTI = "riassunti"

ATTESA_MAX_S = 3 * 3600          # la regola: non verificato da piu' di 3 ore
GUASTO_TOLLERATO_S = 3 * 3600    # lncli muto: un riavvio non e' un allarme
RIPETI_GUASTO_S = 24 * 3600
MAX_PAGAMENTI = 500              # i piu' recenti: listpayments impagina al contrario
MAX_HASH_PER_DOMANDA = 50        # il tetto della rotta del VPS
LOG_ORE = 72                     # quanto indietro si leggono i log di mostrod
# HTLC: mostrod molla la hold invoice a escrow_deadline_margin_blocks
# (24) dalla scadenza, e LND chiude il canale on-chain a 10 per salvare
# un HTLC in entrata. Sotto 20 vuol dire che mostrod NON l'ha mollata:
# e' il solo caso che vale un allarme. Un HTLC in volo non lo e' piu' —
# ogni scambio P2P ne tiene uno per ore (la hold invoice), e la ronda
# di prima («HTLC in volo, con zero trade attesi») avrebbe gridato a
# ogni scambio, ogni ora.
SOGLIA_HTLC_BLOCCHI = 20

FONTI = {"barattolo": "Barattolo", "mostro": "mostrod",
         "mostro-log": "mostrod (log)", "ritentato": "ritentativi",
         "imparato": "imparati a mano"}

HEX64 = re.compile(r"^[0-9a-f]{64}$")
# Le righe di mostrod che nominano l'hash di un pagamento FATTO DA LUI:
# il payout («Order Id …: Invoice with hash: H paid!» / «has failed!»,
# src/app/release.rs) e la dev fee («Amount: N sats, Hash: H»,
# «Payment hash: H», src/app/dev_fee.rs).
# E IL PAYOUT ANDATO IN TIMEOUT («Order Id …: keeping payout claim for
# hash H: …», 19 ott 2026): dalla 0.19.0, se LND non dice ne' si' ne' no
# entro 75 secondi, mostrod lascia andare l'invio e scrive SOLO questa
# riga — niente «has failed!». Poi la riconciliazione legge il FAILED da
# LND, cancella l'hash da mostro.db e riparte con una fattura nuova (un
# Lightning address ne fa una a ogni giro): di quel tentativo resta
# soltanto questa riga. Senza, la ronda ha gridato SCONOSCIUTO al primo
# dei quattro tentativi dell'ordine f285e973. La riga «re-arming retry
# for hash H» invece NON entra: li' l'hash viene dopo un testo variabile.
# ⚠️ LA RIGA DEV'ESSERE DI MOSTROD, NON SOLO CONTENERE LE PAROLE, ed e'
# la riga da non ammorbidire: mostrod stampa anche eventi interi
# ({:#?}), e dentro un evento c'e' testo scritto da chiunque — un
# metodo di pagamento che dicesse «Hash: <il mio>» spiegherebbe un
# furto. Quindi si pretende l'inizio di una riga di tracing (ora,
# livello), il MODULO che paga SUBITO DOPO il livello (mostrod non usa
# span: niente fra i due) e il messaggio esatto subito dopo. Il testo
# degli eventi arriva scappato ({:?} non lascia andare a capo) e sta
# dopo il modulo di chi lo stampa: una riga cosi' non la puo'
# fabbricare nemmeno scrivendola per intero dentro un evento. I colori
# ANSI si tolgono prima.
RIGA_HASH_MOSTRO = re.compile(
    r"^\S+\s+(?:INFO|WARN|ERROR)\s+mostrod?::app::(?:release|dev_fee):\s+"
    r"(?:Order Id [0-9a-f-]+: (?:Invoice with hash: |keeping payout claim "
    r"for hash )|Amount: \d+ sats, Hash: |Payment hash: )([0-9a-f]{64})\b",
    re.M)
ANSI = re.compile(r"\x1b\[[0-9;]*m")
_ALF = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_GEN = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)


# --------------------------------------------------------------------
# I PEZZI PURI: niente rete, niente file. Sono quelli che provano.py
# fa girare, con pagamenti e fonti di cartone.
# --------------------------------------------------------------------

def hash_da_bolt11(bolt11) -> str:
    """Il payment hash di una bolt11 (il campo `p`), letto qui senza
    chiedere a LND: cosi' le fatture dei compratori si decodificano
    tutte a ogni giro senza un `docker exec` per ciascuna. Gemello di
    `leggi_bolt11(…, con_hash=True)` di server.py, e c'e' una prova che
    li fa leggere le stesse fatture. Il checksum si verifica; '' = non
    si legge, e allora non si afferma niente."""
    s = str(bolt11 or "").strip().lower()
    sep = s.rfind("1")
    if not s.startswith("ln") or sep < 2:
        return ""
    hrp, corpo = s[:sep], s[sep + 1:]
    try:
        v = [_ALF.index(c) for c in corpo]
    except ValueError:
        return ""
    chk = 1
    for x in ([ord(c) >> 5 for c in hrp] + [0]
              + [ord(c) & 31 for c in hrp] + v):
        alto = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ x
        for i, g in enumerate(_GEN):
            if (alto >> i) & 1:
                chk ^= g
    if chk != 1:
        return ""
    d = v[:-6]
    if len(d) < 7 + 104:
        return ""
    fine, i = len(d) - 104, 7
    while i + 3 <= fine:
        tipo, lung = d[i], d[i + 1] * 32 + d[i + 2]
        if i + 3 + lung > fine:
            break
        if tipo == 1 and lung == 52:
            n = 0
            for g in d[i + 3:i + 3 + lung]:
                n = n * 32 + g
            return f"{n >> 4:064x}"
        i += 3 + lung
    return ""


def hash_dai_log(testo: str) -> set:
    """Gli hash dei pagamenti che mostrod dice di aver fatto, dai suoi
    log (vedi RIGA_HASH_MOSTRO per quali righe contano)."""
    return set(RIGA_HASH_MOSTRO.findall(ANSI.sub("", testo or "")))


def hash_da_mostro(con) -> set:
    """Gli hash dei pagamenti che mostrod ha fatto o sta facendo, da
    mostro.db. Le colonne si CHIEDONO al database invece di darle per
    scontate: `dev_fee_payment_hash` e `payout_payment_hash` sono nate
    con due migrazioni diverse, e un nodo piu' vecchio o piu' nuovo non
    deve far esplodere la ronda — una colonna che manca e' una fonte in
    meno, non un guasto."""
    trovati = set()
    col = {r[1] for r in con.execute("PRAGMA table_info(orders)")}
    if "buyer_invoice" in col:
        for (inv,) in con.execute("SELECT buyer_invoice FROM orders "
                                  "WHERE buyer_invoice IS NOT NULL"):
            h = hash_da_bolt11(inv)
            if h:
                trovati.add(h)
    for c in ("dev_fee_payment_hash", "payout_payment_hash"):
        if c in col:
            for (h,) in con.execute(f"SELECT {c} FROM orders WHERE {c} IS NOT NULL"):
                h = str(h).strip().lower()
                if HEX64.match(h):
                    trovati.add(h)
    bond = {r[1] for r in con.execute("PRAGMA table_info(bonds)")}
    if "payout_payment_hash" in bond:
        for (h,) in con.execute("SELECT payout_payment_hash FROM bonds "
                                "WHERE payout_payment_hash IS NOT NULL"):
            h = str(h).strip().lower()
            if HEX64.match(h):
                trovati.add(h)
    return trovati


def interpreta_risposta(codice: str, corpo: str, chiesti: list):
    """(risposte, motivo): la risposta del VPS letta con sospetto.
    `risposte` e' {hash: bool} solo se il VPS ha risposto 200, in JSON,
    con un booleano per OGNI hash chiesto; altrimenti None, e `motivo`
    dice perche' in parole — finisce nel journal e, dopo tre ore,
    nell'allarme. Un hash chiesto e non risposto NON e' un «no»: e' un
    «non so», e un «non so» non si grida come un furto."""
    codice = str(codice or "").strip()
    if codice == "000" or not codice:
        return None, "il VPS non risponde (Tor lento o VPS giu')"
    if codice == "404":
        return None, ("il VPS dice 404: la porta e' chiusa "
                      "(RONDA_NODO_SEGRETO manca nel config del VPS?)")
    if codice == "403":
        return None, ("il VPS dice 403: il segreto non combacia "
                      "(/etc/ronda/barattolo.env contro il config del VPS)")
    if codice != "200":
        return None, f"il VPS ha risposto {codice}"
    try:
        d = json.loads(corpo)
        noti = d["noti"] if d.get("ok") is True else None
    except (ValueError, TypeError, KeyError, AttributeError):
        return None, "il VPS ha risposto qualcosa che non si legge"
    if not isinstance(noti, dict) or not all(
            isinstance(noti.get(h), bool) for h in chiesti):
        return None, "il VPS non ha risposto per tutti gli hash chiesti"
    return {h: noti[h] for h in chiesti}, ""


def secondi(p) -> int:
    return int(int(p.get("creation_time_ns") or 0) // 1_000_000_000)


def giudica(pagamenti, noti, locali, fonti_mute, chiedi_vps, dest_di,
            attesa, ora):
    """IL VERDETTO, pagamento per pagamento. Puro: le fonti entrano gia'
    lette o come funzioni, cosi' la prova le sostituisce tutte.

    pagamenti  — la lista di `lncli listpayments`
    noti       — {hash: fonte} gia' spiegati (e gli imparati a mano)
    locali     — {hash: fonte} da mostro.db e dai log di mostrod
    fonti_mute — [motivo, …] delle fonti locali che non si sono lette:
                 se ce n'e' una, un «nessuno lo spiega» non e' certo
    chiedi_vps — f(lista di hash) -> (dict|None, motivo)
    dest_di    — f(pagamento) -> destinazione ('' se non si sa)
    attesa     — {hash: (primo_tentativo, motivo)} dal giro prima
    ora        — adesso, in secondi

    Torna un dict: `riconosciuti` {hash: fonte}, `sconosciuti` [p],
    `in_attesa` {hash: (primo, motivo)} (i non verificati che possono
    ancora aspettare) e `non_verificati` [(p, primo, motivo)] (quelli
    oltre le tre ore, che allarmano)."""
    nuovi = [p for p in pagamenti if p.get("payment_hash") not in noti]
    riconosciuti = {}
    for p in nuovi:
        h = p["payment_hash"]
        if h in locali:
            riconosciuti[h] = locali[h]
    # IL RITENTATIVO: un FAILED non ha mosso un sat. Se dopo di lui un
    # SUCCEEDED ha pagato la stessa cifra alla stessa destinazione, e'
    # lo stesso pagamento riuscito al secondo giro (un wallet che ha
    # rifatto la fattura, una strada trovata dopo): non si grida. Il
    # SUCCEEDED invece si giudica da solo, come tutti.
    riusciti = [q for q in pagamenti if q.get("status") == "SUCCEEDED"]
    for p in nuovi:
        h = p["payment_hash"]
        if h in riconosciuti or p.get("status") != "FAILED":
            continue
        dest = dest_di(p)
        if not dest:
            continue
        for q in riusciti:
            if (q["payment_hash"] != h
                    and str(q.get("value_sat")) == str(p.get("value_sat"))
                    and secondi(q) >= secondi(p) and dest_di(q) == dest):
                riconosciuti[h] = "ritentato"
                break
    resto = [p["payment_hash"] for p in nuovi
             if p["payment_hash"] not in riconosciuti]
    # Le risposte del VPS valgono pezzo per pezzo: se il secondo pezzo
    # non torna, i si' del primo restano si', e i suoi no restano no.
    # Non chiesto o non risposto = «non so», mai «no».
    risposte, motivo_vps = {}, ""
    for i in range(0, len(resto), MAX_HASH_PER_DOMANDA):
        pezzo, motivo = chiedi_vps(resto[i:i + MAX_HASH_PER_DOMANDA])
        if pezzo is None:
            motivo_vps = motivo or "il VPS non ha risposto"
            break
        risposte.update(pezzo)
    for h in resto:
        if risposte.get(h) is True:
            riconosciuti[h] = "barattolo"
    sconosciuti, in_attesa, non_verificati = [], {}, []
    for p in nuovi:
        h = p["payment_hash"]
        if h in riconosciuti:
            continue
        muti = list(fonti_mute) + ([] if h in risposte else [motivo_vps])
        if not muti:
            sconosciuti.append(p)
            continue
        primo = attesa.get(h, (ora, ""))[0]
        motivo = "; ".join(muti)
        if ora - primo > ATTESA_MAX_S:
            non_verificati.append((p, primo, motivo))
        else:
            in_attesa[h] = (primo, motivo)
    return {"riconosciuti": riconosciuti, "sconosciuti": sconosciuti,
            "in_attesa": in_attesa, "non_verificati": non_verificati,
            "vps": motivo_vps}


def giudica_htlc(canali, altezza: int) -> list:
    """Gli HTLC a meno di SOGLIA_HTLC_BLOCCHI dalla scadenza: [(chiave,
    testo)]. La chiave e' l'hash_lock, cosi' lo stesso HTLC si grida una
    volta sola."""
    vicini = []
    for c in canali:
        for x in c.get("pending_htlcs") or []:
            resta = int(x.get("expiration_height") or 0) - altezza
            if altezza and resta < SOGLIA_HTLC_BLOCCHI:
                verso = "in entrata" if x.get("incoming") else "in uscita"
                vicini.append((
                    "htlc:" + str(x.get("hash_lock") or "?"),
                    f"HTLC {verso} da {sats(x.get('amount'))} sats a "
                    f"{resta} blocchi dalla scadenza (canale con "
                    f"{str(c.get('remote_pubkey', ''))[:16]}…): se mostrod "
                    "non lo molla, LND chiude il canale on-chain per "
                    "salvarlo"))
    return vicini


def sats(n) -> str:
    """12345 -> «12.345», all'italiana."""
    return f"{int(n or 0):,}".replace(",", ".")


def quando(sec: int) -> str:
    return dt.datetime.fromtimestamp(sec, dt.timezone.utc).strftime("%d/%m %H:%M UTC")


def testo_allarme(p, dest: str, descrizione: str, motivo: str = "") -> str:
    """L'allarme di UN pagamento: cifra, destinazione, descrizione, e
    cosa fare. `motivo` pieno = non VERIFICATO (una fonte muta da tre
    ore), vuoto = SCONOSCIUTO (tutte le fonti hanno risposto di no)."""
    h = p["payment_hash"]
    testa = ("⚠️ PAGAMENTO NON VERIFICATO da piu' di tre ore" if motivo
             else "🚨 PAGAMENTO SCONOSCIUTO uscito dal nodo")
    righe = [testa,
             f"{sats(p.get('value_sat'))} sats (fee {sats(p.get('fee_sat'))}) — "
             f"{p.get('status')} — {quando(secondi(p))}",
             f"verso: {dest or 'destinazione non leggibile'}",
             f"descrizione: «{(descrizione or '')[:120]}»",
             f"hash: {h[:16]}…"]
    if motivo:
        righe.append(f"Perche' non si e' potuto verificare: {motivo}.")
    else:
        righe.append("Nessuna fonte lo spiega: non e' un payout di Barattolo "
                     "(il VPS ha detto no), non e' di mostrod (ne' nel suo "
                     "database ne' nei suoi log), non e' un nuovo tentativo "
                     "di un pagamento riuscito.")
    righe += [
        "Cosa fare:",
        "1) VERIFICA. Se e' tuo (Zeus, uno swap, un lease) riconoscilo: "
        f"sudo /usr/local/bin/ronda-nodo.sh --impara {h[:16]}",
        "   Se dovrebbe essere di Barattolo, sul VPS: sudo -u barattolo "
        "sqlite3 -readonly /srv/barattolo/dati/satmarket.db \"SELECT "
        "tabella,riga_id,esito,cassaforte "
        f"FROM payout_tentati WHERE hash LIKE '{h[:16]}%'\"",
        "2) SOLO SE NON E' DI NESSUNO: revoca il macaroon di LNbits "
        "(ferma anche i payout del mercatino): sudo docker exec "
        f"{LND} lncli deletemacaroonid 1 — poi scrivi a Claude."]
    return "\n".join(righe)


def testo_riassunto(pagamenti, noti, aperti, giorno: dt.date,
                    in_attesa, htlc_in_volo: int) -> str:
    """Il riassunto di un giorno (UTC), breve: quante volte il nodo ha
    pagato e chi lo spiega. Parte anche a zero pagamenti — e' anche la
    prova quotidiana che la ronda gira e che il tubo verso Telegram
    regge."""
    di_ieri = [p for p in pagamenti
               if dt.datetime.fromtimestamp(secondi(p), dt.timezone.utc).date() == giorno]
    pagati = [p for p in di_ieri if p.get("status") == "SUCCEEDED"]
    falliti = [p for p in di_ieri if p.get("status") == "FAILED"]
    volo = [p for p in di_ieri if p.get("status") == "IN_FLIGHT"]
    etichetta = giorno.strftime("%d/%m")
    righe = [f"🧾 Pagamenti del nodo, ieri {etichetta} (UTC)"]
    if not pagati:
        righe.append("Ieri il nodo non ha pagato niente.")
    else:
        conta = {}
        for p in pagati:
            f = noti.get(p["payment_hash"])
            conta[f] = conta.get(f, 0) + 1
        spiegati = sum(n for f, n in conta.items() if f)
        chi = ", ".join(f"{FONTI.get(f, f)} {n}" for f, n in
                        sorted(conta.items(), key=lambda x: -x[1]) if f)
        totale = sum(int(p.get("value_sat") or 0) for p in pagati)
        volte = "una volta" if len(pagati) == 1 else f"{len(pagati)} volte"
        if spiegati == len(pagati):
            tutte = "riconosciuta" if len(pagati) == 1 else "tutte riconosciute"
            righe.append(f"Ieri il nodo ha pagato {volte}, per {sats(totale)} "
                         f"sats: {tutte} ({chi}).")
        else:
            righe.append(f"Ieri il nodo ha pagato {volte}, per {sats(totale)} "
                         f"sats: {spiegati} riconosciute ({chi or 'nessuna'}), "
                         f"⚠️ {len(pagati) - spiegati} NO.")
    if falliti:
        ok = sum(1 for p in falliti if noti.get(p["payment_hash"]))
        righe.append(f"Tentativi falliti: {len(falliti)}"
                     + (", tutti spiegati." if ok == len(falliti)
                        else f", {len(falliti) - ok} non spiegati."))
    if volo:
        righe.append(f"Ancora in volo: {len(volo)}.")
    if in_attesa:
        righe.append(f"In attesa di verifica (VPS o mostro.db muti): {len(in_attesa)}.")
    if aperti:
        righe.append(f"⚠️ Allarmi ancora aperti: {len(aperti)} — "
                     + ", ".join(h[:12] + "…" for h in sorted(aperti))
                     + ". Se sono tuoi: sudo /usr/local/bin/ronda-nodo.sh "
                       "--impara <hash>")
    if htlc_in_volo:
        righe.append(f"HTLC in volo adesso: {htlc_in_volo} (gli scambi P2P "
                     "in corso ne tengono uno a testa).")
    righe.append("--- fine riassunto")
    return "\n".join(righe)


# --------------------------------------------------------------------
# I PEZZI CHE TOCCANO IL MONDO: lncli, mostro.db, i log, il VPS, i file.
# --------------------------------------------------------------------

def lncli(*a):
    r = subprocess.run(["docker", "exec", LND, "lncli", *a],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "lncli muto").strip()[:200])
    return json.loads(r.stdout)


def leggi_segreti(percorso=SEGRETI) -> dict:
    """KEY=VALORE, una per riga; # e righe vuote si saltano. Non si fa
    `source` da bash: il segreto resta dentro Python e dentro curl."""
    out = {}
    try:
        for riga in open(percorso, encoding="utf-8"):
            riga = riga.strip()
            if not riga or riga.startswith("#") or "=" not in riga:
                continue
            k, v = riga.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def _per_curl(valore) -> str:
    """Un valore dentro le virgolette della configurazione di curl: li'
    la barra rovescia e' un carattere di escape, quindi un percorso o
    un segreto che ne contenesse una arriverebbe storpiato (il banco su
    Windows l'ha visto sul percorso del corpo: «C:UsersAndrea…»)."""
    return str(valore).replace("\\", "\\\\").replace('"', '\\"')


def chiedi_al_vps(hashes, segreti) -> tuple:
    """(risposte, motivo) per un pezzo di hash. curl e non urllib: urllib
    non parla SOCKS, e il nodo esce solo da Tor. Il segreto viaggia nella
    configurazione letta da stdin, il corpo in un file che solo root
    legge e che sparisce subito."""
    url = segreti.get("RONDA_URL", "")
    segreto = segreti.get("RONDA_SEGRETO", "")
    if not url or not segreto or segreto.startswith("INCOLLA"):
        return None, f"segreto del VPS non configurato ({SEGRETI})"
    fd, corpo = tempfile.mkstemp(prefix="ronda-domanda-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump({"hashes": list(hashes)}, f)
        cfg = (f'url = "{_per_curl(url)}"\n'
               f'header = "Authorization: Bearer {_per_curl(segreto)}"\n'
               'header = "Content-Type: application/json"\n'
               f'data = "@{_per_curl(corpo)}"\n')
        cmd = ["curl", "-sS", "--max-time", "90", "-o", "-",
               "-w", "\n%{http_code}", "-K", "-"]
        # DA TOR PER DEFAULT, come la porta dello sconto: il nodo non
        # esce in chiaro. «nessuno» va scritto apposta, e serve al banco.
        socks = segreti.get("TOR_SOCKS", TOR_SOCKS)
        if socks and socks != "nessuno":
            cmd[1:1] = ["--socks5-hostname", socks]
        r = subprocess.run(cmd, input=cfg, capture_output=True, text=True,
                           timeout=120)
        testo, _, codice = r.stdout.rpartition("\n")
        risposte, motivo = interpreta_risposta(codice, testo, list(hashes))
        if risposte is None and r.stderr.strip():
            motivo += f" — {r.stderr.strip().splitlines()[-1][:140]}"
        return risposte, motivo
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"curl verso il VPS non e' partito ({e})"
    finally:
        try:
            os.unlink(corpo)
        except OSError:
            pass


def fonti_locali(db_mostro=DB_MOSTRO, contenitore=MOSTRO) -> tuple:
    """({hash: fonte}, [motivi delle fonti mute])."""
    locali, mute = {}, []
    try:
        con = sqlite3.connect(f"file:{db_mostro}?mode=ro", uri=True, timeout=10)
        try:
            for h in hash_da_mostro(con):
                locali[h] = "mostro"
        finally:
            con.close()
    except sqlite3.Error as e:
        mute.append(f"mostro.db non si legge ({e})")
    try:
        r = subprocess.run(["docker", "logs", "--since", f"{LOG_ORE}h", contenitore],
                           capture_output=True, text=True, errors="replace",
                           timeout=120)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "").strip()[:120])
        for h in hash_dai_log(r.stdout + "\n" + r.stderr):
            locali.setdefault(h, "mostro-log")
    except (OSError, subprocess.SubprocessError, RuntimeError) as e:
        mute.append(f"i log di mostrod non si leggono ({e})")
    return locali, mute


def _righe(nome) -> list:
    try:
        return [l.split() for l in open(os.path.join(CARTELLA, nome),
                                        encoding="utf-8") if l.strip()]
    except OSError:
        return []


def _scrivi(nome, righe) -> None:
    """Atomico: file temporaneo nella stessa cartella e rename, cosi' un
    giro interrotto a meta' non lascia un elenco monco — e un elenco
    monco dei noti vorrebbe dire allarmi falsi al giro dopo."""
    os.makedirs(CARTELLA, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=CARTELLA, prefix="." + nome)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for r in righe:
            f.write(" ".join(str(x) for x in r) + "\n")
    os.replace(tmp, os.path.join(CARTELLA, nome))


def leggi_noti() -> dict:
    return {r[0]: (r[1] if len(r) > 1 else "imparato") for r in _righe(NOTI)}


def avvisa(testo: str) -> bool:
    try:
        return subprocess.run([AVVISA], input=testo, text=True,
                              timeout=120).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


class Decodifiche:
    """La destinazione e la descrizione di un pagamento, chieste a LND
    una volta sola per giro. La destinazione vera e' quella della
    fattura; se manca (keysend) si ripiega sull'ultimo salto della
    strada."""

    def __init__(self):
        self.memo = {}

    def __call__(self, p) -> tuple:
        h = p["payment_hash"]
        if h not in self.memo:
            dest, descr = "", ""
            if p.get("payment_request"):
                try:
                    d = lncli("decodepayreq", p["payment_request"])
                    dest, descr = d.get("destination", ""), d.get("description", "")
                except (RuntimeError, ValueError, OSError,
                        subprocess.SubprocessError):
                    pass
            if not dest:
                for x in p.get("htlcs") or []:
                    hops = (x.get("route") or {}).get("hops") or []
                    if hops:
                        dest = hops[-1].get("pub_key", "")
            self.memo[h] = (dest, descr)
        return self.memo[h]


def guasto(guasti: dict, chiave: str, vero: bool, ora: int,
           tollera: int) -> bool:
    """Registra lo stato di un guasto e dice se va gridato ADESSO: la
    prima volta dopo `tollera` secondi, poi una volta ogni 24 ore.
    Un guasto che torna falso esce dalla memoria."""
    if not vero:
        guasti.pop(chiave, None)
        return False
    primo, ultimo = guasti.get(chiave, (ora, 0))
    grida = ora - primo >= tollera and (not ultimo or ora - ultimo >= RIPETI_GUASTO_S)
    guasti[chiave] = (primo, ora if grida else ultimo)
    return grida


def impara(pagamenti, noti, prefisso: str) -> str:
    """--impara: senza argomento, TUTTI i pagamenti di adesso diventano
    noti (il gesto di sempre); con un prefisso di almeno 8 caratteri,
    solo QUEL pagamento — quello che l'allarme ha nominato, e nessun
    altro sconosciuto insieme a lui."""
    if prefisso:
        prefisso = prefisso.lower()
        if len(prefisso) < 8 or not re.fullmatch(r"[0-9a-f]+", prefisso):
            return "--impara vuole almeno 8 caratteri esadecimali dell'hash"
        presi = [p for p in pagamenti if p["payment_hash"].startswith(prefisso)]
        if len(presi) != 1:
            return f"--impara {prefisso}: {len(presi)} pagamenti con quell'inizio, ne serve UNO"
    else:
        presi = pagamenti
    for p in presi:
        noti.setdefault(p["payment_hash"], "imparato")
    _scrivi(NOTI, sorted(noti.items()))
    tolti = {p["payment_hash"] for p in presi}
    _scrivi(ALLARMATI, [r for r in _righe(ALLARMATI) if r[0] not in tolti])
    _scrivi(ATTESA, [r for r in _righe(ATTESA) if r[0] not in tolti])
    return f"imparati {len(presi)} pagamenti: {len(noti)} ora noti"


def main(argv) -> int:
    modo = argv[1] if len(argv) > 1 else ""
    ora = int(time.time())
    guasti = {r[0]: (int(r[1]), int(r[2])) for r in _righe(GUASTI) if len(r) >= 3}
    try:
        pagamenti = lncli("listpayments", "--include_incomplete",
                          "--max_payments", str(MAX_PAGAMENTI)).get("payments", [])
        canali = lncli("listchannels").get("channels", [])
        altezza = int(lncli("getinfo").get("block_height", 0))
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as e:
        print(f"ronda-pagamenti: lncli non risponde ({e})")
        if guasto(guasti, "lncli", True, ora, GUASTO_TOLLERATO_S):
            if not avvisa("ALLARME NODO\n- lncli non risponde da piu' di tre "
                          f"ore: i pagamenti in uscita NON sono sorvegliati ({e})"):
                guasti["lncli"] = (guasti["lncli"][0], 0)
        _scrivi(GUASTI, [(k, *v) for k, v in guasti.items()])
        return 1
    guasto(guasti, "lncli", False, ora, 0)
    noti = leggi_noti()

    if modo == "--impara":
        print(impara(pagamenti, noti, argv[2] if len(argv) > 2 else ""))
        return 0

    locali, mute = fonti_locali()
    segreti = leggi_segreti()
    dec = Decodifiche()
    attesa = {r[0]: (int(r[1]), " ".join(r[2:])) for r in _righe(ATTESA) if len(r) >= 2}
    v = giudica(pagamenti, noti, locali, mute,
                lambda hs: chiedi_al_vps(hs, segreti),
                lambda p: dec(p)[0], attesa, ora)
    noti.update(v["riconosciuti"])
    _scrivi(NOTI, sorted(noti.items()))
    _scrivi(ATTESA, [(h, primo, motivo) for h, (primo, motivo) in v["in_attesa"].items()])

    allarmati = {r[0]: r[1] for r in _righe(ALLARMATI) if len(r) >= 2}
    # chi e' stato riconosciuto dopo l'allarme esce dagli aperti
    allarmati = {h: t for h, t in allarmati.items() if h not in noti}
    gridati = 0
    for p in v["sconosciuti"]:
        h = p["payment_hash"]
        if h in allarmati:
            continue
        dest, descr = dec(p)
        if avvisa(testo_allarme(p, dest, descr)):
            allarmati[h] = ora
            gridati += 1
    for p, _, motivo in v["non_verificati"]:
        h = p["payment_hash"]
        if h in allarmati:
            continue
        dest, descr = dec(p)
        if avvisa(testo_allarme(p, dest, descr, motivo)):
            allarmati[h] = ora
            gridati += 1
    _scrivi(ALLARMATI, sorted(allarmati.items()))

    # I GUASTI CHE DURANO: la prima volta e poi una al giorno. Se
    # Telegram non prende l'avviso, le chiavi gridate adesso tornano «mai
    # avvisate» e il giro dopo ci riprova.
    altri, gridate = [], []
    if guasto(guasti, "canali", not canali, ora, 0):
        altri.append("nessun canale aperto")
        gridate.append("canali")
    vivi = set()
    for chiave, testo in giudica_htlc(canali, altezza):
        vivi.add(chiave)
        if guasto(guasti, chiave, True, ora, 0):
            altri.append(testo)
            gridate.append(chiave)
    for k in [k for k in guasti if k.startswith("htlc:") and k not in vivi]:
        guasti.pop(k)
    if altri and not avvisa("ALLARME NODO\n" + "\n".join("- " + a for a in altri)):
        for k in gridate:
            guasti[k] = (guasti[k][0], 0)
    _scrivi(GUASTI, [(k, *val) for k, val in guasti.items()])

    # LA RIGA NEL JOURNAL C'E' SEMPRE, anche quando tutto tace: e' quella
    # che distingue «gira e non trova niente» da «non gira».
    htlc = sum(len(c.get("pending_htlcs") or []) for c in canali)
    per_fonte = {}
    for f in v["riconosciuti"].values():
        per_fonte[f] = per_fonte.get(f, 0) + 1
    muti = ([v["vps"]] if v["vps"] else []) + mute
    print(f"ronda-pagamenti: {len(pagamenti)} letti, "
          f"{len(v['riconosciuti'])} riconosciuti adesso "
          f"({', '.join(f'{f} {n}' for f, n in sorted(per_fonte.items())) or '-'}), "
          f"{len(v['sconosciuti'])} sconosciuti, {len(v['in_attesa'])} in attesa, "
          f"{len(v['non_verificati'])} non verificati da oltre 3 ore, "
          f"allarmi aperti {len(allarmati)}, fonti locali "
          f"{len(locali)} hash, htlc {htlc}, canali {len(canali)}"
          + (f"; fonti mute: {'; '.join(muti)}" if muti else ""))

    if modo in ("--giorno", "--prova"):
        ieri = (dt.datetime.fromtimestamp(ora, dt.timezone.utc) - dt.timedelta(days=1)).date()
        fatti = {r[0] for r in _righe(RIASSUNTI)}
        if modo == "--prova" or ieri.isoformat() not in fatti:
            testo = testo_riassunto(pagamenti, noti, allarmati, ieri,
                                    v["in_attesa"], htlc)
            if modo == "--prova":
                testo = "(PROVA) " + testo
            if avvisa(testo) and modo == "--giorno":
                _scrivi(RIASSUNTI, [(g,) for g in sorted(fatti | {ieri.isoformat()})][-60:])
    return 9 if gridati or altri else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
