# SatMarket — CHECKLIST DI LANCIO

Da spuntare IN ORDINE il giorno in cui si va online.
Finché c'è anche una sola casella vuota, NON condividere il link.

## 1. Interruttori in server.py

- [ ] `MODALITA_COLLAUDO = False`  ← IL PIÙ IMPORTANTE.
      Se resta True, chiunque può impersonare chiunque.
- [ ] `BOT_TOKEN` compilato (il token del bot che ospita la Mini App,
      da @BotFather)
- [ ] `ANTHROPIC_API_KEY` compilata (serve per la ricerca AI)
- [ ] `ADMIN_IDS` = il TUO vero user id Telegram
      (scrivi a @userinfobot per scoprirlo). Senza questo non puoi
      decidere le dispute e non ricevi gli avvisi.

## 2. Wallet e sicurezza

- [ ] Wallet LNbits DEDICATO a SatMarket (non quello personale)
- [ ] Sul wallet solo i fondi operativi necessari, non i risparmi
- [ ] Le chiavi LNbits stanno SOLO su il server di produzione
- [ ] Deciso il limite massimo per annuncio del periodo di rodaggio
      (consiglio: 100k sats finché il sistema non è collaudato
      con utenti veri)

## 3. Dati

- [ ] Database del collaudo archiviato: rinomina `satmarket.db` in
      `satmarket_collaudo.db` e riparti pulito (il server ne crea
      uno nuovo da solo). Gli annunci di prova non devono
      inquinare il debutto.
- [ ] Annunci Nostr dell'amico re-importati con il suo VERO id
      Telegram: in `importa_nostr.py` metti `VENDITORE_ID = <suo id>`
      (da @userinfobot) e rilancia lo script
- [ ] L'amico ha AVVIATO il bot almeno una volta (altrimenti
      Telegram non gli consegna le notifiche!)

## 4. Messa online (vedi LEGGIMI.md per i dettagli)

- [ ] VPS attivo con dominio e HTTPS
- [ ] `server.py`, `miniapp.html`, cartella `foto/` e database
      trasferiti sul VPS
- [ ] Mini App registrata su @BotFather (/newapp) con l'URL del VPS
- [ ] Provato il link t.me/tuobot/nomeapp dal telefono:
      la app si apre DENTRO Telegram e il banner collaudo NON c'è
      (se c'è: MODALITA_COLLAUDO è ancora True, torna al punto 1!)

## 5. Il giro di prova finale (con l'app online, prima di condividere)

- [ ] Pubblicato un annuncio di prova con foto
- [ ] Comprato da un secondo account/persona: sats in escrow
- [ ] Segnato spedito, confermato: sats arrivati al venditore
- [ ] Aperta una disputa di prova su un secondo ordine e decisa
      da admin (sia il rimborso che il pagamento al venditore)
- [ ] Notifiche Telegram arrivate a entrambe le parti
- [ ] Annuncio di prova eliminato

## 6. Solo dopo tutto questo

- [ ] Condividere il link alla community, con importi piccoli
      e il messaggio chiaro che è un rodaggio

## Promemoria post-lancio (la lista dei desideri)

- Feedback e stelle dopo ogni affare
- Sezione Profilo completa + modifica annunci
- Pubblicazione degli annunci VERSO Nostr (+ "sold" automatico)
- Sblocco automatico dopo X giorni dalla consegna
- Notifiche "trovato l'oggetto che cercavi"
- Commissione: cifra da decidere (oggi è a 0 nel config); valutare
  un minimo fisso, perché una percentuale piccola sui piccoli
  importi è mangiata dalle fee di rete
- Escrow on-chain multisig 2-di-3 per gli oggetti di valore
- Collegamento wallet via NWC (acquisto in un tap)
