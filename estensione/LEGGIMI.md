# Barattolo per Amazon — l'estensione del browser di Barattozon

Cantiere «estensione-bz», 16 nov 2026. Il perché di ogni scelta sta in
`docs/CANTIERI.md`, «L'estensione del browser per Barattozon»; la porta
dentro Barattolo in `docs/ARCHITETTURA.md`, «BARATTOZON DA UN LINK».

## Cosa fa

1. Fai un ordine su **www.amazon.it** e scegli «paga in contanti».
2. Sulla pagina dove Amazon ti dà il PayCode compare, in basso a
   destra, il bottone **«🫙 Pubblica su Barattozon»**.
3. Il bottone apre barattolo.store in una scheda nuova, su «Vendi BTC»,
   col percorso Barattozon già compilato: PayCode, importo, scadenza e
   codice a barre, quando la pagina li ha.
4. Rileggi e premi «Pubblica» dentro Barattolo. L'ordine lo firma
   Barattolo sul tuo dispositivo: l'estensione non sa chi sei.

Se non sei entrato su barattolo.store, prima ti chiede di entrare con
Telegram; i campi aspettano mezz'ora nella memoria di quella scheda.

## Compra con Barattozon (dal 17 nov 2026)

Il percorso si vede fin dall'inizio, col marchio Barattozon:

- **Pagina del prodotto**: sotto «Aggiungi al carrello» c'è
  **«Compra con Barattozon»**. Al tocco preme «Aggiungi al carrello» di
  Amazon, e basta.
- **Carrello**: sotto «Procedi all'ordine» lo stesso bottone. Al tocco
  preme «Procedi all'ordine».
- **Cassa**: un cartello in basso a destra coi tre passi, e la riga
  «Paga in Contanti nel Punto Vendita più vicino» contornata d'arancio.
  Qui l'estensione non clicca niente: il pagamento lo scegli tu.
- Poi, sulla pagina del PayCode, «Pubblica su Barattozon» come sopra.

Non preme MAI «Acquista ora» (con l'1-Click ordinerebbe da solo) né il
bottone che invia l'ordine.

## Cosa NON fa (e non deve mai fare)

- Non parla con nessun server: niente rete, niente cookie, niente
  memoria. Nessun permesso oltre a www.amazon.it.
- Non mette link affiliati (Amazon li vieta nelle estensioni).
- Non manda il PayCode al server di Barattolo: viaggia dopo il «#»
  dell'indirizzo, che il browser non spedisce.
- Non inventa dati: quel che non trova lo chiede il foglio di Barattolo.

## Provarla sul computer (senza store)

Chrome, Brave, Edge, Opera:
1. `chrome://extensions` (o `brave://`, `edge://`, `opera://`).
2. Accendi «Modalità sviluppatore».
3. «Carica estensione non pacchettizzata» → la cartella `estensione/`.

Firefox (140 o più nuovo):
1. `about:debugging#/runtime/this-firefox`.
2. «Carica componente aggiuntivo temporaneo…» → il file
   `estensione/manifest.json`. Resta finché non chiudi Firefox.

## Lo zip per gli store

Dalla cartella del repo:

    cd estensione && zip -r ../barattolo-per-amazon-0.1.0.zip manifest.json amazon.js icone

Lo stesso zip va bene per il Chrome Web Store e per Firefox Add-ons
(Chrome ignora `browser_specific_settings`). Prima di ogni invio si
alza `version` nel manifest.

## Da fare prima della pubblicazione

- Vedere una pagina Amazon vera con un PayCode (ordine di prova): oggi
  il codice cerca il link del PDF del PayCode e, in mancanza, il
  PayCode accanto alla parola «PayCode». Quella pagina non è ancora
  stata vista.
- La pagina privacy dell'estensione su barattolo.store.
- Account sviluppatore a nome di Barattolo, con la verifica in due passi.
