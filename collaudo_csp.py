# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE CINTURE HTTP, DELLA CSP IN PROVA E DEL LOGIN A REDIRECT
(1 ott 2026, cantiere «CSP e le voci aperte degli audit»).

`prove.py` fa girare i giudici puri e tiene le sentinelle sul testo; qui
risponde il SERVER VERO (fastapi c'e' solo nei collaudi): le intestazioni
sulla pagina, su un file js e sul widget; il cestino `/api/csp-report`
coi suoi argini e la guardia CSRF che lo lascia passare; il login web a
redirect, firmato col BOT_TOKEN di cartone del banco — entrata, cookie,
`/api/me` che riconosce, uscita, rientro — e la Mini App che entra con
l'initData esattamente come prima.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete.

USO:  python collaudo_csp.py
"""

import base64
import contextlib
import hashlib
import hmac
import io
import json
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def firma_widget(token, dati):
    """La firma del Login Widget: HMAC-SHA256 con chiave SHA256(token)
    sui campi in ordine, come la calcola Telegram."""
    controllo = "\n".join(f"{k}={dati[k]}" for k in sorted(dati))
    chiave = hashlib.sha256(token.encode()).digest()
    return hmac.new(chiave, controllo.encode(), hashlib.sha256).hexdigest()


def main():
    print("=" * 58)
    print("  LE CINTURE HTTP, LA CSP IN PROVA, IL LOGIN A REDIRECT")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    c = TestClient(banco.SRV.app)

    print("\n[le intestazioni della pagina]")
    g = c.get("/")
    csp = g.headers.get("content-security-policy-report-only", "")
    prova("la pagina risponde 200", 200, g.status_code)
    prova("...con la CSP in PROVA (report-only)", True, csp.startswith("default-src 'self'"))
    prova("...che nomina il cestino", True, "report-uri /api/csp-report" in csp)
    prova("...in collaudo con ws: per il relay morto", True,
          "connect-src 'self' wss: ws:" in csp)
    prova("...e senza unsafe-eval", False, "'unsafe-eval'" in csp)
    prova("nessuna CSP vera: la leva dell'iframe e' spenta", None,
          g.headers.get("content-security-policy"))
    prova("nosniff, referrer e permissions ci sono",
          ["nosniff", "strict-origin-when-cross-origin", "microphone=(), payment=(), usb=(), midi=()"],
          [g.headers.get("x-content-type-options"), g.headers.get("referrer-policy"),
           g.headers.get("permissions-policy")])
    prova("niente HSTS in collaudo (la pagina gira su http)", None,
          g.headers.get("strict-transport-security"))
    prova("...e il no-cache di sempre e' rimasto", "no-cache, no-store, must-revalidate",
          g.headers.get("cache-control"))

    print("\n[un file js e il widget]")
    v = c.get("/vendor/qrcode.js")
    prova("il js risponde 200", 200, v.status_code)
    prova("...SENZA la CSP delle pagine (non e' HTML)", None,
          v.headers.get("content-security-policy-report-only"))
    prova("...ma con le cinture", "nosniff", v.headers.get("x-content-type-options"))
    w = c.get("/widget/annuncio/1")
    cw = w.headers.get("content-security-policy-report-only", "")
    prova("il widget risponde 200 anche senza annuncio", 200, w.status_code)
    prova("...con la SUA CSP in prova, piu' stretta", True, cw.startswith("default-src 'none'"))
    prova("...senza frame-ancestors: deve stare nell'iframe di chiunque", False,
          "frame-ancestors" in cw)
    corpo = w.text
    dentro = corpo[corpo.index("<script>") + 8:corpo.index("</script>")]
    atteso = "sha256-" + base64.b64encode(hashlib.sha256(dentro.encode("utf-8")).digest()).decode()
    prova("...e l'impronta e' quella del corpo SERVITO, byte per byte", True,
          f"script-src '{atteso}'" in cw)

    print("\n[il cestino delle violazioni]")
    report = {"csp-report": {"effective-directive": "script-src",
                             "blocked-uri": "https://evil.example/x.js",
                             "source-file": "https://barattolo.store/",
                             "line-number": 7,
                             "document-uri": "https://barattolo.store/"}}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        r1 = c.post("/api/csp-report", content=json.dumps(report),
                    headers={"Content-Type": "application/csp-report"})
        r2 = c.post("/api/csp-report", content=json.dumps(report),
                    headers={"Content-Type": "application/csp-report"})
    righe = [l for l in out.getvalue().splitlines() if "CSP:" in l]
    prova("il report risponde 204", [204, 204], [r1.status_code, r2.status_code])
    prova("...e scrive UNA riga nel journal, non due", 1, len(righe))
    prova("...che dice cosa e dove", True,
          righe and "script-src" in righe[0] and "https://evil.example/x.js" in righe[0]
          and "https://barattolo.store/:7" in righe[0])
    grosso = json.dumps({"csp-report": {"blocked-uri": "x" * 20000}})
    prova("un corpo oltre 16 KB e' un 413", 413,
          c.post("/api/csp-report", content=grosso,
                 headers={"Content-Type": "application/csp-report"}).status_code)
    prova("...e il JSON storto un 204 muto", 204,
          c.post("/api/csp-report", content="{{{",
                 headers={"Content-Type": "application/csp-report"}).status_code)
    # la guardia CSRF: il cestino passa, il resto no
    prova("col cookie e un Origin estraneo il cestino passa lo stesso", 204,
          c.post("/api/csp-report", content="{}",
                 headers={"Origin": "https://evil.example",
                          "Cookie": "barattolo_sessione=x"}).status_code)
    prova("...mentre la guardia CSRF ferma ancora le altre rotte", 403,
          c.post("/api/logout", headers={"Origin": "https://evil.example",
                                         "Cookie": "barattolo_sessione=x"}).status_code)

    print("\n[il login web a redirect: entrata, sessione, uscita, rientro]")
    token = "0:collaudo"
    dati = {"id": "111", "first_name": "Tester", "username": "tester",
            "auth_date": str(int(time.time()))}
    dati["hash"] = firma_widget(token, dati)
    r = c.get("/api/login/telegram/ritorno", params={**dati, "da": "/negozio/ab12cd34"},
              follow_redirects=False)
    prova("un login firmato: 303 alla pagina di partenza",
          (303, "/negozio/ab12cd34"), (r.status_code, r.headers.get("location")))
    biscotti = r.headers.get_list("set-cookie")
    sess = [b for b in biscotti if b.startswith("barattolo_sessione=")]
    prova("...col cookie di sessione, HttpOnly e SameSite=lax", True,
          len(sess) == 1 and "HttpOnly" in sess[0] and "samesite=lax" in sess[0].lower())
    prova("...e il portachiavi", 1,
          len([b for b in biscotti if b.startswith("barattolo_portachiavi=")]))
    me = c.get("/api/me")
    prova("da li' in poi /api/me riconosce dal cookie", (200, 111),
          (me.status_code, (me.json().get("tg_id") if me.status_code == 200 else None)))
    r = c.post("/api/logout")
    prova("l'uscita risponde", 200, r.status_code)
    prova("...e /api/me non riconosce piu'", 401, c.get("/api/me").status_code)
    dati["auth_date"] = str(int(time.time()))
    dati["hash"] = firma_widget(token, {k: v for k, v in dati.items() if k != "hash"})
    r = c.get("/api/login/telegram/ritorno", params={**dati, "da": "/"},
              follow_redirects=False)
    prova("il rientro riapre la sessione", (303, 200),
          (r.status_code, c.get("/api/me").status_code))
    c.post("/api/logout")

    print("\n[il login web a redirect: i no]")
    storto = dict(dati, hash="0" * 64)
    r = c.get("/api/login/telegram/ritorno", params={**storto, "da": "/negozio/ab12cd34"},
              follow_redirects=False)
    prova("firma storta: si torna con ?accesso=no, senza cookie",
          (303, "/negozio/ab12cd34?accesso=no", []),
          (r.status_code, r.headers.get("location"),
           [b for b in r.headers.get_list("set-cookie") if b.startswith("barattolo_sessione=")]))
    prova("...e /api/me resta fuori", 401, c.get("/api/me").status_code)
    vecchio = {k: v for k, v in dati.items() if k != "hash"}
    vecchio["auth_date"] = str(int(time.time()) - 600)
    vecchio["hash"] = firma_widget(token, vecchio)
    r = c.get("/api/login/telegram/ritorno", params=vecchio, follow_redirects=False)
    prova("un login di dieci minuti fa non vale (i cinque minuti di sempre)",
          "/?accesso=no", r.headers.get("location"))
    buono = {k: v for k, v in dati.items() if k != "hash"}
    buono["auth_date"] = str(int(time.time()))
    buono["hash"] = firma_widget(token, buono)
    r = c.get("/api/login/telegram/ritorno", params={**buono, "da": "//evil.example"},
              follow_redirects=False)
    prova("`da` fuori casa: si torna alla radice", "/", r.headers.get("location"))
    c.post("/api/logout")

    print("\n[la Mini App non cambia: entra con l'initData]")
    me = c.get("/api/me", headers={"X-Tg-Init-Data": "collaudo:111:Tester"})
    prova("l'initData di collaudo apre come sempre", (200, 111),
          (me.status_code, me.json().get("tg_id") if me.status_code == 200 else None))
    prova("...e la vecchia POST del collaudo risponde ancora", 200,
          c.post("/api/login/telegram",
                 json={"collaudo": True, "id": 111, "first_name": "Tester"}).status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
