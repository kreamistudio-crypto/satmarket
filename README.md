# SatMarket ⚡

**Il mercatino in sats con escrow** — una Mini App Telegram tipo
Subito.it, ma con pagamenti solo in satoshi (Bitcoin Lightning) e una
cassaforte escrow che protegge acquirente e venditore.

## Come funziona l'escrow

1. 🔒 L'acquirente compra → i sats finiscono **bloccati** nel wallet
   della piattaforma (LNbits)
2. 📦 Il venditore spedisce, con corriere e **tracciamento** visibili
   all'acquirente
3. 📬 Alla consegna l'acquirente ha **72 ore** per controllare
   l'oggetto: conferma, oppure apre disputa
4. 🔓 Alla conferma (o allo scadere del tempo) i sats vengono
   **sbloccati automaticamente** al venditore — sul suo Lightning
   address, meno l'1% di commissione
5. ⚖️ In caso di disputa decide un moderatore: rimborso immediato,
   rimborso **previa restituzione** dell'oggetto (con tracking del
   reso), o pagamento al venditore
6. ⏰ Protezioni automatiche: sblocco d'ufficio a 10 giorni se
   l'acquirente sparisce; ordini mai pagati che si autodistruggono

In piu': foto degli annunci, ricerca AI in linguaggio naturale
("tastiera sotto i 100k vicino Milano"), import di annunci da
**Nostr** (NIP-99 e NIP-15) con foto e contatto del venditore,
incassi automatici via Lightning address.

## I file

| File                  | Cosa fa                                        |
|-----------------------|------------------------------------------------|
| `server.py`           | Backend: FastAPI + SQLite + LNbits + Telegram  |
| `miniapp.html`        | La Mini App (frontend, un solo file)           |
| `config_esempio.py`   | Modello di configurazione → copialo in `config.py` |
| `importa_nostr.py`    | Importa gli annunci di un venditore da Nostr   |
| `censimento_nostr.py` | Strumento: conta gli annunci sui relay Nostr   |
| `AVVIA_SATMARKET.bat` | Avvio con doppio click (Windows)               |
| `CHECKLIST_LANCIO.md` | Da spuntare prima di andare online             |

## Partire in 5 minuti (collaudo locale)

```bash
pip install fastapi uvicorn httpx anthropic websocket-client
```

1. Copia `config_esempio.py` → `config.py` e compila le chiavi
   (servono un wallet LNbits dedicato e le sue due chiavi)
2. Avvia: `python -m uvicorn server:app --host 0.0.0.0 --port 8080`
   (o doppio click su `AVVIA_SATMARKET.bat` su Windows)
3. Apri `miniapp.html` nel browser: in **modalità collaudo** hai tre
   identità (Compratore / Venditore / Admin) per provare tutto il
   flusso, sats veri compresi
4. Dal telefono (stesso WiFi): `http://IP-DEL-PC:8080/miniapp.html`

Senza backend attivo, `miniapp.html` gira in **modalità demo** con
dati finti: utile per lavorare sulla UX.

## ⚠️ Avvertenze

- **`config.py` non va MAI committato**: contiene la admin key di
  LNbits, cioè la cassaforte. Il `.gitignore` lo esclude già.
- Modello **custodial**: i sats passano dal wallet della piattaforma.
  Per test in community con importi piccoli ok; per volumi reali
  serve un parere legale (normativa MiCA).
- `MODALITA_COLLAUDO = False` è obbligatorio prima di andare online
  (vedi `CHECKLIST_LANCIO.md`).

## Roadmap

- Etichette di spedizione prestampate + consegna rilevata dal
  tracking del corriere (Sendcloud/Packlink + webhook)
- Feedback e stelle post-affare, sezione Profilo, modifica annunci
- Pubblicazione degli annunci **verso** Nostr (+ "sold" automatico),
  login Nostr (bunker), feed dei contatti seguiti
- Escrow on-chain multisig 2-di-3 per gli oggetti di valore
- Pagamento in un tap via NWC (Nostr Wallet Connect)
