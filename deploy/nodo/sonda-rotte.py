#!/usr/bin/env python3
# sonda-rotte.py — «Phoenix ci paga SOLO dal canale ACINQ?» (11 ott 2026,
# cantiere allarme-liquidita). SOLA LETTURA: chiede a LND, non paga, non
# apre, non scrive niente (nemmeno un file).
#
# La domanda: partendo dal nodo di ACINQ — che e' chi instrada per conto
# di Phoenix — esiste una strada fino a noi che NON passi dal canale
# diretto? E costa meno di quel che Phoenix lascia spendere (4 sat +
# 0,4 %)? `lncli queryroutes` non sa partire da un altro nodo (non ha
# l'opzione), la REST di LND si' (`source_pub_key`): per questo si passa
# di li', col macaroon di SOLA LETTURA che LND ha gia' (non sa pagare).
# Il macaroon non si stampa mai.
#
# LND da qui NON conosce i saldi degli altri: dice se la strada esiste
# sulla carta (canali, capienze, tariffe, tetti). L'ultimo salto pero'
# e' un canale NOSTRO, e di quello l'entrata vera si sa: la sonda la
# mette accanto.
#
# Uso, sul nodo:  python3 /tmp/sonda-rotte.py
# (o con l'indirizzo della REST a mano:  python3 /tmp/sonda-rotte.py IP:PORTA)
import base64, collections, datetime, json, os, re, ssl, subprocess, sys
import urllib.error, urllib.request

NODO = os.path.expanduser("~/nodo")
PREFISSO_ACINQ = "03864ef025fde8fb"      # come la ronda: il prefisso basta
IMPORTI = [100_000, 300_000, 500_000, 1_000_000]
TLS = ssl._create_unverified_context()   # si parla col LND di casa, in locale


def tetto_phoenix(sats):
    return 4 + sats * 4 // 1000


def dentro(*comando):
    """Un comando DENTRO il container di LND; None se non riesce."""
    r = subprocess.run(["docker", "compose", "exec", "-T", "lnd", *comando],
                       cwd=NODO, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def macaroon_trovati():
    """[(percorso, esadecimale)]: TUTTI i readonly.macaroon del container,
    quello di mainnet per primo. Il primo giro (11 ott) prendeva il primo
    che `find` incontrava: una copia vecchia in un'altra cartella avrebbe
    fatto dire «permission denied» a un LND che rispondeva benissimo."""
    elenco = dentro("sh", "-c", 'find / -name readonly.macaroon '
                                '-not -path "/proc/*" 2>/dev/null; true') or ""
    percorsi = sorted((p.strip() for p in elenco.split("\n") if p.strip()),
                      key=lambda p: ("/mainnet/" not in p, p))
    trovati = []
    for p in percorsi:
        esa = re.sub(r"\s", "", dentro("od", "-An", "-tx1", "-v", p) or "")
        if re.fullmatch(r"[0-9a-f]{100,}", esa):
            trovati.append((p, esa))
    if not trovati:
        sys.exit("FERMO: non trovo readonly.macaroon nel container di LND "
                 "(o docker compose non risponde da ~/nodo)")
    return trovati


def ip_del_container():
    """Gli IP del container di LND; se la rete e' prestata da un altro
    container (`container:...`), gli IP di quello."""
    def ispeziona(chi):
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.HostConfig.NetworkMode}}|"
             "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}", chi],
            capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    r = subprocess.run(["docker", "compose", "ps", "-q", "lnd"], cwd=NODO,
                       capture_output=True, text=True)
    chi = (r.stdout.strip().split("\n") or [""])[0] if r.returncode == 0 else ""
    if not chi:
        return []
    modo, _, ips = ispeziona(chi).partition("|")
    if modo.startswith("container:"):
        _, _, ips = ispeziona(modo.split(":", 1)[1]).partition("|")
    return ips.split()


def indirizzi_rest(a_mano=None):
    """Dove puo' rispondere la REST di LND: l'indirizzo dato a mano, quello
    che usa il socat del ponte, gli IP del container, l'IP del tunnel."""
    c = [a_mano] if a_mano else []
    try:
        for riga in open("/etc/default/lnd-rest-wg"):
            m = re.match(r"\s*LND_REST=(\S+)", riga)
            if m:
                c.append(m.group(1))
    except OSError:
        pass
    ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True)
    m = re.search(r"socat TCP4-LISTEN:18080\S* TCP4:([0-9.]+:\d+)", ps.stdout)
    if m:
        c.append(m.group(1))
    c += [ip + ":8080" for ip in ip_del_container()]
    c += ["10.77.0.1:18080", "127.0.0.1:8080"]
    return list(dict.fromkeys(c))


# niente proxy presi dall'ambiente: si parla con un indirizzo di casa
APRI = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                   urllib.request.HTTPSHandler(context=TLS))


def chiedi(base, mac, percorso, corpo=None, attesa=60):
    """GET (o POST col corpo) alla REST. Torna il JSON; un «no» di LND
    torna come {"errore": ...}; una REST muta come {"muto": ...}."""
    req = urllib.request.Request(
        f"https://{base}{percorso}",
        data=None if corpo is None else json.dumps(corpo).encode(),
        headers={"Grpc-Metadata-macaroon": mac} if mac else {},
        method="GET" if corpo is None else "POST")
    try:
        with APRI.open(req, timeout=attesa) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return {"errore": json.loads(e.read()).get("message") or f"http {e.code}"}
        except Exception:
            return {"errore": f"http {e.code}"}
    except Exception as e:
        return {"muto": f"{type(e).__name__}: {str(e)[:120]}"}


def b64(esa):
    return base64.b64encode(bytes.fromhex(esa)).decode()


def punti(n):
    return f"{int(n):,}".replace(",", ".")


def utile(saldo, canale, lato):
    riserva = int((canale.get(lato + "_constraints") or {}).get("chan_reserve_sat") or 0)
    return max(0, int(saldo) - riserva)


def main():
    # CHI RISPONDE, E PERCHE' NO (11 ott 2026): il primo giro diceva solo
    # «non risponde», e non si capiva se era l'indirizzo o il macaroon.
    # Adesso ogni indirizzo dice la sua: muto (col motivo), o vivo; e
    # ogni macaroon, su un indirizzo vivo, dice accettato o rifiutato.
    a_mano = sys.argv[1] if len(sys.argv) > 1 else None
    macaroon = macaroon_trovati()
    mac = base = info = None
    for b in indirizzi_rest(a_mano):
        r = chiedi(b, "", "/v1/state", attesa=10)
        if "muto" in r:
            print(f"REST {b}: muta ({r['muto']})")
            continue
        print(f"REST {b}: risponde ({r.get('state') or r.get('errore') or '?'})")
        for percorso, esa in macaroon:
            r = chiedi(b, esa, "/v1/getinfo", attesa=20)
            if r.get("identity_pubkey"):
                print(f"  macaroon {percorso}: accettato")
                mac, base, info = esa, b, r
                break
            print(f"  macaroon {percorso}: rifiutato "
                  f"({r.get('errore') or r.get('muto') or 'risposta senza chiave'})")
        if base:
            break
    if not base:
        sys.exit("FERMO: nessun indirizzo ha risposto col macaroon di sola "
                 "lettura (le righe qui sopra dicono dove si ferma)")
    noi = info["identity_pubkey"]
    print(f"LND {info.get('version', '?')[:24]}  REST su {base}  noi {noi[:16]}")

    canali = chiedi(base, mac, "/v1/channels?peer_alias_lookup=true").get("channels") or []
    acinq = next((c["remote_pubkey"] for c in canali
                  if c["remote_pubkey"].startswith(PREFISSO_ACINQ)), None)
    if not acinq:
        sys.exit("FERMO: nessun canale con ACINQ fra i nostri")
    nostri = {str(c.get("chan_id")): c for c in canali}
    nomi = {noi: "NOI"}

    def nome(pk):
        if pk not in nomi:
            n = chiedi(base, mac, f"/v1/graph/node/{pk}", attesa=20)
            nomi[pk] = ((n.get("node") or {}).get("alias") or pk[:16]).strip()
        return nomi[pk]

    print("\n== I NOSTRI CANALI (sats; «utile» = tolta la riserva) ==")
    for c in canali:
        h = c.get("pending_htlcs") or []
        print(f"- {c.get('peer_alias') or nome(c['remote_pubkey'])} | "
              f"{'in linea' if c.get('active') else 'FUORI LINEA'} | "
              f"capienza {punti(c['capacity'])} | "
              f"uscita utile {punti(utile(c['local_balance'], c, 'local'))} | "
              f"entrata utile {punti(utile(c['remote_balance'], c, 'remote'))} | "
              f"HTLC in sospeso {len(h)} ({punti(sum(int(x.get('amount') or 0) for x in h))}) | "
              f"scid {c.get('chan_id')} | {'privato' if c.get('private') else 'pubblico'}")

    def strada(sats, evita_diretto, tetto):
        corpo = {"source_pub_key": acinq, "use_mission_control": False}
        if evita_diretto:
            corpo["ignored_pairs"] = [{"from": b64(acinq), "to": b64(noi)}]
        if tetto is not None:
            corpo["fee_limit"] = {"fixed": str(tetto)}
        r = chiedi(base, mac, f"/v1/graph/routes/{noi}/{sats}", corpo)
        vie = r.get("routes") or []
        if not vie:
            return None, r.get("errore") or r.get("muto") or "nessuna strada"
        return vie[0], ""

    def racconta(via):
        salti = via.get("hops") or []
        costo = (int(via.get("total_fees_msat") or 0) + 999) // 1000
        giro = " -> ".join(["ACINQ"] + [nome(s["pub_key"]) for s in salti])
        tariffe = ", ".join(f"{nome(s['pub_key'])} {(int(s.get('fee_msat') or 0) + 999) // 1000}"
                            for s in salti[:-1]) or "nessun intermediario"
        ultimo = nostri.get(str(salti[-1].get("chan_id"))) if salti else None
        return giro, costo, tariffe, ultimo

    print("\n== DA ACINQ A NOI ==")
    for sats in IMPORTI:
        tetto = tetto_phoenix(sats)
        print(f"\n{punti(sats)} sat (Phoenix lascia spendere {punti(tetto)} di rete)")
        via, perche = strada(sats, False, None)
        if via:
            giro, costo, _, _ = racconta(via)
            print(f"  controllo, strada libera: {giro} | costo {punti(costo)}")
        else:
            print(f"  controllo, strada libera: NESSUNA ({perche})")
        via, perche = strada(sats, True, tetto)
        if not via:
            print(f"  SENZA il canale diretto, nel tetto di Phoenix: NESSUNA ({perche})")
            via, perche = strada(sats, True, None)
            if not via:
                print(f"  SENZA il canale diretto, a qualunque prezzo: NESSUNA ({perche})")
                continue
            etichetta = "SENZA il canale diretto, FUORI dal tetto"
        else:
            etichetta = "SENZA il canale diretto, nel tetto di Phoenix"
        giro, costo, tariffe, ultimo = racconta(via)
        print(f"  {etichetta}: {giro} | costo {punti(costo)} ({tariffe})")
        if ultimo is None:
            print("  ultimo salto: NON e' un canale nostro (strano: riportalo)")
        else:
            entra = utile(ultimo["remote_balance"], ultimo, "remote")
            print(f"  ultimo salto: canale con {ultimo.get('peer_alias') or '?'}, "
                  f"entrata utile VERA {punti(entra)} -> "
                  + ("ci sta" if entra >= sats else "NON ci sta"))

    # Da dove sono entrati i pagamenti veri: per ogni fattura incassata,
    # il canale di ogni pezzo arrivato. Non dice che wallet pagava, ma
    # dice se dagli altri canali entra qualcosa davvero.
    print("\n== DA DOVE SONO ENTRATI GLI INCASSI (ultime fatture incassate) ==")
    r = chiedi(base, mac, "/v1/invoices?num_max_invoices=5000&reversed=true", attesa=120)
    fatture = [f for f in (r.get("invoices") or []) if f.get("state") == "SETTLED"]
    if not fatture:
        print("  nessuna fattura incassata letta"
              + (f" ({r.get('errore') or r.get('muto')})" if r.get("errore") or r.get("muto") else ""))
    else:
        conto = collections.defaultdict(lambda: [0, 0, 0])
        for f in fatture:
            for h in f.get("htlcs") or []:
                if h.get("state") != "SETTLED":
                    continue
                v = conto[str(h.get("chan_id"))]
                sats = int(h.get("amt_msat") or 0) // 1000
                v[0] += 1
                v[1] += sats
                v[2] = max(v[2], sats)
        date = sorted(int(f.get("settle_date") or 0) for f in fatture)
        giorno = lambda t: datetime.datetime.fromtimestamp(t).strftime("%d/%m")
        print(f"  {len(fatture)} fatture incassate, dal {giorno(date[0])} al {giorno(date[-1])}")
        for scid, (n, tot, grosso) in sorted(conto.items(), key=lambda x: -x[1][1]):
            c = nostri.get(scid)
            chi = (c.get("peer_alias") or "?") if c else f"canale chiuso {scid}"
            print(f"  - da {chi} ({scid}): {n} pezzi, {punti(tot)} sat in tutto, "
                  f"il pezzo piu' grosso {punti(grosso)}")
    print("\n--- fine sonda")


if __name__ == "__main__":
    main()
