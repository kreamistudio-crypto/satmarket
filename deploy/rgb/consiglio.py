#!/usr/bin/env python3
"""consiglio.py — QVAC in locale dice cosa conviene spendere.

Legge il saldo punti del wallet utente (il JSON di `punti.mjs saldo`, o un
file), il prezzo in sats del carrello e la regola del negozio, e chiede a
QVAC (qvac serve --openai su 127.0.0.1:11434) una proposta in JSON A SCHEMA:
  { "usa_punti": X, "sconto_sats": Y, "asset_id": "...", "motivo": "..." }
Il modello PROPONE, l'utente approva: la regola la applica il programma,
non il modello (il controllo in fondo rifà il conto e boccia se sbaglia).

Uso: python consiglio.py <prezzo_sats> [saldo.json]
     (senza file legge il saldo da stdin)
"""
import json
import sys
import urllib.request

QVAC = "http://127.0.0.1:11434/v1/chat/completions"
MODELLO = "qwen3-600m-inst-q4"
# La regola del negozio di prova: un punto vale un sat di sconto, al massimo
# il 20% del prezzo, e si usano solo punti settled (spendibili davvero).
SAT_PER_PUNTO = 1
TETTO_PERCENTO = 20

SCHEMA = {
    "type": "object",
    "properties": {
        "usa_punti": {"type": "integer", "minimum": 0},
        "sconto_sats": {"type": "integer", "minimum": 0},
        "asset_id": {"type": "string"},
        "motivo": {"type": "string"},
    },
    "required": ["usa_punti", "sconto_sats", "asset_id", "motivo"],
    "additionalProperties": False,
}


def punti_spendibili(saldo):
    """Dal JSON di punti.mjs: gli asset NIA con saldo settled > 0."""
    assets = saldo.get("asset", saldo).get("nia", [])
    return [
        {"asset_id": a["assetId"], "ticker": a["ticker"], "nome": a["name"],
         "punti": int(a["balance"]["settled"])}
        for a in assets if int(a["balance"]["settled"]) > 0
    ]


def chiedi(prezzo, punti):
    tetto = prezzo * TETTO_PERCENTO // 100
    # Il conto lo fa il programma e lo passa al modello gia' fatto: un
    # modello da 0,6 miliardi di parametri sbaglia l'aritmetica, non la scelta.
    for p in punti:
        p["massimo_usabile"] = min(p["punti"], tetto // SAT_PER_PUNTO)
        p["sconto_se_li_usi_tutti"] = p["massimo_usabile"] * SAT_PER_PUNTO
    sistema = (
        "Sei l'assistente di un mercatino in satoshi. Proponi quanti punti "
        "fedelta' usare su questo acquisto. Regola: 1 punto = "
        f"{SAT_PER_PUNTO} sat di sconto; lo sconto non puo' superare "
        f"{TETTO_PERCENTO}% del prezzo ({tetto} sats); non si usano piu' punti "
        "di quelli posseduti. Per ogni asset trovi gia' calcolato "
        "'massimo_usabile': usa_punti deve essere al massimo quello, e "
        f"sconto_sats = usa_punti * {SAT_PER_PUNTO}. Conviene usare il "
        "massimo. Rispondi solo col JSON richiesto, motivo in italiano in "
        "una frase."
    )
    utente = json.dumps({"prezzo_sats": prezzo, "punti": punti}, ensure_ascii=False)
    corpo = {
        "model": MODELLO,
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": utente}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "proposta_sconto",
                                            "schema": SCHEMA, "strict": True}},
        "temperature": 0,
        "max_tokens": 300,
        # Qwen3 ragiona prima di rispondere, e il ragionamento si
        # mangia i token: senza questo una completion nuda torna
        # content null (8 ott sera, dal vivo). Con lo schema la
        # grammatica parte subito e non pensa comunque, ma
        # l'interruttore si manda lo stesso; `enable_thinking` QVAC
        # lo ignora. E' lo stesso di consigliami-prova.html.
        "reasoning_budget": False,
    }
    req = urllib.request.Request(QVAC, data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        risposta = json.load(r)
    testo = risposta["choices"][0]["message"]["content"]
    return json.loads(testo), risposta.get("usage")


def controlla(proposta, prezzo, punti):
    """Il programma rifa' il conto: il modello propone, la regola decide."""
    tetto = prezzo * TETTO_PERCENTO // 100
    disponibili = {p["asset_id"]: p["punti"] for p in punti}
    if proposta["asset_id"] not in disponibili:
        return "asset non posseduto"
    if proposta["usa_punti"] > disponibili[proposta["asset_id"]]:
        return "piu' punti di quelli posseduti"
    if proposta["sconto_sats"] != proposta["usa_punti"] * SAT_PER_PUNTO:
        return "sconto non coerente con i punti"
    if proposta["sconto_sats"] > tetto:
        return f"sconto oltre il tetto di {tetto} sats"
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    prezzo = int(sys.argv[1])
    sorgente = open(sys.argv[2]) if len(sys.argv) > 2 else sys.stdin
    saldo = json.load(sorgente)
    punti = punti_spendibili(saldo)
    if not punti:
        print("nessun punto spendibile: niente da proporre"); sys.exit(0)
    proposta, uso = chiedi(prezzo, punti)
    print("proposta di QVAC:", json.dumps(proposta, ensure_ascii=False, indent=2))
    errore = controlla(proposta, prezzo, punti)
    print("controllo della regola:", "ok" if errore is None else f"BOCCIATA ({errore})")
    if uso:
        print("token:", uso)
