# -*- coding: utf-8 -*-
"""LA PROVA DELLA NOTIFICA (17 set 2026): manda un messaggio di prova a
UN chat id col bot di Barattolo e stampa la risposta VERA di Telegram.

Nato il giorno che il journal diceva «avvisati 2» e sui telefoni non
arrivava niente: prima di cercare il guasto nel P2P va tolto di mezzo
il trasporto, e il trasporto si prova cosi' — la stessa chiamata
`sendMessage` di `_manda_telegram`, con lo stesso token e lo stesso
`parse_mode`, guardando cosa risponde Telegram invece di dedurlo.

    cd ~/satmarket && python3 prova_notifica.py 123456789

NON importa server.py (che all'import fa l'avvio): legge il solo
BOT_TOKEN dal config, e NON lo stampa mai — nemmeno nell'errore.
Dice anche CHI e' quel chat id (`getChat`: nome e username), che e' il
modo di risalire da un numero del journal a un account: risponde solo
se quella persona ha avviato il bot almeno una volta.
"""
import json
import sys
import urllib.error
import urllib.request


def chiama(token, metodo, corpo):
    """(status, testo) — il token sta nell'URL e qui non esce mai."""
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{metodo}",
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:                       # rete, DNS, timeout
        return 0, f"{type(e).__name__}: {str(e).replace(token, '<token>')}"


def main(argv):
    if len(argv) != 2 or not argv[1].lstrip("-").isdigit():
        print("uso: python3 prova_notifica.py <chat_id>")
        return 2
    try:
        from config import BOT_TOKEN
    except ImportError:
        print("manca config.py (o il token del bot): si lancia dalla cartella del server")
        return 2
    chat = int(argv[1])
    st, testo = chiama(BOT_TOKEN, "getChat", {"chat_id": chat})
    print(f"getChat -> {st}")
    try:
        d = json.loads(testo).get("result") or {}
        print(f"   chi e': {d.get('first_name', '')} {d.get('last_name', '')} "
              f"@{d.get('username', '')} (tipo {d.get('type', '?')})")
    except Exception:
        print(f"   {testo[:300]}")
    st, testo = chiama(BOT_TOKEN, "sendMessage", {
        "chat_id": chat, "parse_mode": "HTML",
        "text": "⚡ <b>Prova delle notifiche P2P.</b> Se leggi questo, "
                "il bot ti raggiunge: il trasporto funziona."})
    print(f"sendMessage -> {st}")
    print(f"   {testo[:400]}")
    if st == 200:
        print("   ✅ Telegram l'ha PRESO IN CONSEGNA: il messaggio e' nella "
              "chat del bot di quell'account.")
    elif st == 403:
        print("   🔕 quell'account non ha avviato il bot, o l'ha bloccato.")
    elif st == 400:
        print("   ⚠️ chat id sconosciuto al bot (mai avviato), o testo rifiutato.")
    return 0 if st == 200 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
