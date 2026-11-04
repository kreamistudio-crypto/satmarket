---
name: cerca-nei-docs
description: Come trovare una sezione nei file giganti di Barattolo (docs/CANTIERI.md, ARCHITETTURA, PRODUZIONE, server.py, miniapp.html, prove.py) leggendone solo il pezzo che serve. Usala prima di aprire uno di quei file, o quando un commento rimanda a una voce («vedi Architettura, ...»).
---

# Cercare nei file giganti senza leggerli interi

I file grandi del repo pesano milioni di caratteri: `docs/CANTIERI.md`
(~4,5 MB), `docs/ARCHITETTURA.md` (~2,3 MB), `docs/PRODUZIONE.md`,
`server.py` (~5 MB), `miniapp.html` (~5,5 MB), `prove.py` (~11 MB).
Una lettura intera costa più di tutto il cantiere, e le righe di
`miniapp.html` arrivano a 40.000 caratteri: anche un grep nudo può
riempire il contesto. Si legge SOLO la sezione che serve.

## Nei documenti (`docs/*.md`)

Ogni voce porta il suo nome nella prima riga, che comincia con `## `.
Non c'è un indice e non deve nascerne uno.

1. Trova il titolo, solo le righe-titolo:
   `grep -n "^## .*sconto carrello" docs/*.md`
   Se il titolo non lo sai, cerca la parola chiave e tieni corto:
   `grep -n -i "sconto carrello" docs/*.md | cut -c1-200 | head -20`
2. Trova dove finisce la voce (il `## ` successivo):
   `awk 'NR>INIZIO && /^## /{print NR; exit}' docs/CANTIERI.md`
3. Leggi solo quell'intervallo: `sed -n 'INIZIO,FINEp' docs/CANTIERI.md`
   (o Read con `offset` e `limit`). Se la voce è lunga, prima le prime
   60 righe: spesso il perché sta in cima.

I rimandi scritti nel codice («vedi Architettura, "IL SUPPLEMENTO PER
PEZZO"», «Cantieri, «Il doppio wallet»») sono indirizzi: si cercano
così, col titolo fra virgolette.

Le voci di luglio e agosto 2026 (e via via quelle più vecchie di 30
giorni) stanno in `docs/CANTIERI-ARCHIVIO-2026.md`: il grep su
`docs/*.md` le prende già.

## Nel codice (`server.py`, `miniapp.html`, `prove.py`)

- Cerca la definizione, non ogni uso:
  `grep -n "^def nome_funzione\|^async def nome_funzione" server.py`,
  `grep -n "function nomeFunzione" miniapp.html`,
  `grep -n "^def prove_nome" prove.py`.
- Taglia SEMPRE le righe e limita i risultati:
  `grep -n "parola" miniapp.html | cut -c1-200 | head -30`.
  Prima di un grep largo, conta: `grep -c "parola" server.py`.
- Poi leggi un intervallo stretto intorno alla riga trovata
  (`sed -n 'N,Mp'`, o Read con `offset`/`limit`), mai il file intero.
- Per sapere dove finisce una funzione Python:
  `awk 'NR>N && /^(async )?def |^class /{print NR; exit}' server.py`.

## Cosa non fare

- `cat` o Read senza `limit` su uno di questi file.
- Un grep senza `head` e senza `cut` su `miniapp.html` o `prove.py`.
- Scrivere un indice dei documenti: la ricerca per titolo è l'indice.
