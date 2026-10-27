# Le leve dal pannello: quali si aprono, quali mai, quali decidi tu

*27 ott 2026, cantiere onchain-incasso-esterno, passo 5 del piano
concordato con Andrea («il config tra l'altro deve anche poter essere
modificato dal pannello amministrazione da un admin, di modo di non
dover entrare nella vps per forza»; sul biglietto delle scelte:
«Entrambe le cose», cioè subito la quota on-chain e poi le altre leve
**decise una per una**). Il meccanismo c'è già, da oggi; qui c'è il
censimento delle 231 leve del cassetto «⚙️ Stato delle leve», con la mia
proposta per ognuna. Non è aperta nessuna leva oltre alla quota e a «Solo gli admin» dell'on-chain: ogni
riga diventa scrivibile col suo sì.*

> **Aggiornamento, stesso giorno (cantiere leve-tutte).** Andrea: «tutto
> devo poter configurare da lì, però suddividilo bene in sezioni, ogni
> configurazione richieda una conferma e che possa esistere un backup»;
> sul biglietto: «No, le "mai" restano sul VPS». Quindi le «✅ si può» e
> le «⚖️ decidi tu» sono APERTE tutte insieme, col giudice del loro tipo
> (Architettura, «TUTTE LE LEVE DAL PANNELLO»); le «🔒 mai» restano
> chiuse. Le due ragioni qui sotto restano vere e hanno la loro
> risposta: la prima è la lettura del sorgente che dice «subito» o «dal
> riavvio», più i valori posati sul config all'avvio; la seconda è la
> conferma «Adesso / Dopo», la storia con «Annulla» e il backup.

## Come funziona già (e perché una alla volta)

Una leva scrivibile è una riga in `LEVE_SCRIVIBILI` (server.py) con il
suo **giudice**: il tipo (un intero, una lista, un sì/no), il pavimento e
il tetto. Il valore scritto dal pannello sta nel database
(`leve_pannello`), **vince sul config** del VPS, sopravvive ai riavvii e
ai deploy, e lascia una riga nel registro della moderazione con chi e da
quanto a quanto. «Torna al config» lo cancella. Il cassetto mostra ✏️
accanto alle sole leve aperte, con «Salva» e poi «Conferma».

Non si possono aprire tutte con un colpo solo, per due ragioni:

1. **Il codice legge la leva in un punto preciso, spesso all'avvio.**
   Molte leve finiscono in strutture costruite una volta sola (i tetti
   dei freni, i testi, gli orologi). Aprirne una vuol dire trovare OGNI
   punto che la legge e farlo passare da `leva_scrivibile`, e provarlo:
   è lavoro per leva, piccolo ma vero.
2. **La regola di agosto resta vera** per le leve che aprono porte o
   muovono soldi: «una leva che si accende da un telefono è una leva che
   si accende per sbaglio», e un admin con il telefono rubato non deve
   poter alzare una commissione o spegnere una guardia.

## Le tre classi

- **🔒 mai** (59): sicurezza, segreti, indirizzi, chiavi, relay, il
  coordinator, le guardie dei soldi. Stanno sul VPS e basta, anche
  perché molte vogliono un riavvio vero o toccano un'altra macchina.
- **✅ si può** (110): numeri di servizio — giorni dei promemoria,
  durate, ritmi dei post, tetti di quantità, percentuali di sconto che
  decide il venditore. Sbagliarne uno dà fastidio, non costa soldi a
  nessuno. Proposta: aprirle **a gruppi** (un gruppo per cantiere), con
  pavimento e tetto ciascuna.
- **⚖️ decidi tu** (61): le porte (le leve «…_ATTIVO» che accendono una
  funzione) e i numeri che muovono soldi o tetti (commissioni, tetti del
  P2P, limiti dello swap, prezzi dei banner). Qui la mia proposta è
  «no», salvo quelle che tu indichi una per una.
- **✏️ fatte** (2): la quota fissa on-chain e, lo stesso giorno, «Solo gli
  admin» dell'on-chain (Andrea non ha accesso alla VM).

## La proposta, se vuoi partire

Il primo gruppo da aprire, perché è quello che oggi ti fa entrare più
spesso nel VPS e non tocca soldi: **⏱ Tempi e promemoria** (tranne
`GIORNI_AUTO_SBLOCCO`, che è dell'auto-sblocco). Poi **🟣 i ritmi del
canale** e **🏷️ la vetrina**. Dimmi quali gruppi o quali righe, e li apro.

## Il censimento

### 🚦 Sicurezza

| leva | chiave | proposta |
|---|---|---|
| Modalità collaudo | `MODALITA_COLLAUDO` | 🔒 mai |
| Indirizzo del sito | `URL_PUBBLICO` | 🔒 mai |
| Bot dei link e del login | `LINK_BOT` | 🔒 mai |
| Istanza di prova: id ammessi | `PROVA_SOLO_IDS` | 🔒 mai |
| Istanza di prova: aperta a tutti | `PROVA_APERTA` | 🔒 mai |
| Scadenza dell'initData (ore) | `ORE_INITDATA` | 🔒 mai |
| Stemmer della ricerca | `pip install snowballstemmer` | 🔒 mai |
| Porta dell'iframe chiusa | `PROTEGGI_IFRAME` | 🔒 mai |
| CSP accesa (Content-Security-Policy) | `CSP_ATTIVA` | 🔒 mai |
| Servizio nascosto Tor | `ONION_HOST` | 🔒 mai |
| Cookie senza Secure sul tunnel Tor | `ONION_SEGNALE` | 🔒 mai |
| Negozi collegati (Shopify e WooCommerce) | `CONNETTORI_NEGOZIO_APERTI` | 🔒 mai |
| Negozi collegati: la porta per tutti | `CONNETTORI_NEGOZIO_PER_TUTTI` | 🔒 mai |
| Bot in ascolto (webhook) | `TELEGRAM_WEBHOOK_SEGRETO` | 🔒 mai |
| Whitelist del relay | `RELAY_CHIAVI_TOKEN` | 🔒 mai |
| Moderatori | `ADMIN_IDS` | 🔒 mai |
| Gruppo degli admin | `ADMIN_CANALE_ID` | 🔒 mai |
| Coda del gruppo degli admin | `GRUPPO_ADMIN_CODA` | 🔒 mai |

### 🔒 Escrow e denaro

| leva | chiave | proposta |
|---|---|---|
| Cassaforte del denaro nuovo: LNbits sul nodo | `CASSAFORTE_NUOVA` | 🔒 mai |
| Guardia della liquidità del nodo | `GUARDIA_LIQUIDITA` | 🔒 mai |
| Margine delle casseforti: percentuale (%) | `LIQUIDITA_MARGINE_PERCENTO` | ⚖️ decidi tu |
| Margine delle casseforti: sats fissi | `LIQUIDITA_MARGINE_MIN_SATS` | ⚖️ decidi tu |
| Guardiano del ponte verso LND | `GUARDIANO_PONTE` | 🔒 mai |
| Auto-sblocco dei sats | `AUTO_SBLOCCO_ATTIVO` | ⚖️ decidi tu |
| Commissione (%) | `COMMISSIONE_PERCENTO` | ⚖️ decidi tu |
| Protezione acquisti (%) | `PROTEZIONE_PERCENTO` | ⚖️ decidi tu |
| Fee dinamica: totale da spartire (%) | `FEE_DINAMICA_TOTALE_PERCENTO` | ⚖️ decidi tu |
| Fee dinamica: split di base oggi | `db: fee_dinamica_stato` | 🔒 mai |
| Tetto di prezzo per annuncio (sats) | `TETTO_SATS_ANNUNCIO` | ⚖️ decidi tu |
| Cifratura dei codici digitali | `CHIAVE_CONTENUTI_DIGITALI` | 🔒 mai |
| Il cambio vale al massimo (ore) | `ORE_CAMBIO_VALIDO` | ⚖️ decidi tu |
| Si rilegge il cambio ogni (secondi) | `CAMBIO_RINFRESCO_S` | ⚖️ decidi tu |
| La ronda del libro mastro | `CONTROLLO_LIBRO_MASTRO` | 🔒 mai |
| La ronda dei payout | `RICONCILIA_PAYOUT` | 🔒 mai |

### ⏱ Tempi e promemoria

| leva | chiave | proposta |
|---|---|---|
| Conferma dopo la consegna (ore) | `ORE_CONFERMA` | ✅ si può |
| Silenzio dopo la spedizione (giorni) | `GIORNI_AUTO_SBLOCCO` | ⚖️ decidi tu |
| Digitale: dopo la rivelazione (ore) | `ORE_CONFERMA_DIGITALE` | ✅ si può |
| Digitale: consegnato e mai letto (ore) | `ORE_SILENZIO_DIGITALE` | ✅ si può |
| Ogni quanto si ribussa (giorni) | `PROMEMORIA_CONFERMA_GIORNI` | ✅ si può |
| Promemoria ignorati prima dei moderatori | `PROMEMORIA_CONFERMA_MAX` | ✅ si può |
| Merce mai partita: primo squillo (giorni) | `PROMEMORIA_SPEDIZIONE_GIORNI` | ✅ si può |
| Codice mai consegnato: primo squillo (ore) | `PROMEMORIA_DIGITALE_ORE` | ✅ si può |
| Promemoria a comando: da quando (ore) | `SOLLECITO_MANUALE_ORE` | ✅ si può |
| Promemoria a comando sul codice: da quando (ore) | `SOLLECITO_MANUALE_DIGITALE_ORE` | ✅ si può |
| Promemoria a comando: pausa fra uno e l'altro (ore) | `SOLLECITO_MANUALE_PAUSA_ORE` | ✅ si può |
| Promemoria a comando: quanti in tutto | `SOLLECITO_MANUALE_MAX` | ✅ si può |
| Busta di ritiro mai depositata: primo squillo (giorni) | `PROMEMORIA_BUSTA_GIORNI` | ✅ si può |
| Punto contestato: primo squillo a chi compra (giorni) | `PROMEMORIA_OBIEZIONE_GIORNI` | ✅ si può |
| Ritiro al punto: primo squillo e passo (giorni) | `PROMEMORIA_RITIRO_GIORNI` | ✅ si può |
| Sollecito degli incassi fermi (giorni) | `SOLLECITO_INCASSO_GIORNI` | ✅ si può |
| Solleciti prima dei moderatori | `SOLLECITO_INCASSO_MAX` | ✅ si può |
| Indirizzo di casa: cancellato dopo la chiusura (giorni) | `GIORNI_INDIRIZZO` | ✅ si può |
| Ordini fermi: da quanti giorni (coda admin) | `CODA_FERMI_GIORNI` | 🔒 mai |

### 🔨 Aste

| leva | chiave | proposta |
|---|---|---|
| Aste | `ASTA_ABILITATA` | ⚖️ decidi tu |
| Rilancio automatico (proxy) | `ASTA_PROXY_ATTIVO` | ⚖️ decidi tu |
| Durate offerte (giorni) | `ASTA_DURATE_GIORNI` | ✅ si può |
| Rilancio minimo (%) | `ASTA_INCREMENTO_PERCENTO` | ✅ si può |
| Proroga anti-cecchino (minuti) | `ASTA_PROROGA_MINUTI` | ✅ si può |
| Aste vive per venditore | `ASTA_MAX_ATTIVE_VENDITORE` | ✅ si può |

### 🔄 Swap

| leva | chiave | proposta |
|---|---|---|
| Swap degli incassi (on-chain) | `SWAP_ATTIVO` | ⚖️ decidi tu |
| Chiavi per leggere la quota (SATS Routing) | `SWAP_REFERRAL_API_SECRET` | 🔒 mai |
| Swap: solo i moderatori | `SWAP_SOLO_MODERATORI` | ⚖️ decidi tu |
| Swap: minimo per swap (sats) | `SWAP_MIN_SATS` | ⚖️ decidi tu |
| Swap: massimo per swap (sats) | `SWAP_MAX_SATS` | ⚖️ decidi tu |
| Swap: pagati per venditore in 24 ore (sats) | `SWAP_MAX_SATS_UTENTE_GIORNO` | ⚖️ decidi tu |
| Swap: pagati in tutto in 24 ore (sats) | `SWAP_MAX_SATS_GIORNO` | ⚖️ decidi tu |
| Swap: la nostra fee (%) | `SWAP_FEE_PERCENTO` | ⚖️ decidi tu |
| Swap: dove si leggono le tariffe | `SWAP_API_BASE` | 🔒 mai |
| Swap: la rete | `SWAP_RETE` | 🔒 mai |
| Swap: dove si legge il lockup | `SWAP_MEMPOOL_API` | 🔒 mai |
| Swap: gli altri fornitori | `SWAP_FORNITORI_IN_PIU` | 🔒 mai |
| Codice partner di SATS Routing | `SWAP_REFERRAL_ID` | 🔒 mai |

### 📅 Servizi

| leva | chiave | proposta |
|---|---|---|
| Servizi | `SERVIZI_ATTIVI` | ⚖️ decidi tu |
| Appuntamento entro (giorni) | `SERVIZIO_MAX_GIORNI` | ✅ si può |
| Ordini aperti insieme, chi non ha vendite | `SERVIZIO_MAX_APERTI` | ✅ si può |

### ⚡ Offerta lampo

| leva | chiave | proposta |
|---|---|---|
| Offerte lampo | `LAMPO_ATTIVE` | ⚖️ decidi tu |
| Sconti proposti (%) | `LAMPO_SCONTI` | ✅ si può |
| Sconto minimo (%) | `LAMPO_MIN_PERCENTO` | ✅ si può |
| Sconto massimo (%) | `LAMPO_MAX_PERCENTO` | ✅ si può |
| Durate proposte (ore) | `ORE_LAMPO_OPZIONI` | ✅ si può |
| Lanci per annuncio in 7 giorni | `MAX_LAMPO_SETTIMANA` | ✅ si può |
| Cooldown «ha fatto colpo» (giorni) | `GIORNI_COLPO` | ✅ si può |

### 🎁 Sconto sugli articoli

| leva | chiave | proposta |
|---|---|---|
| Sconto sugli articoli | `SCONTO_PACCO_ATTIVO` | ⚖️ decidi tu |
| Criteri della soglia | `SCONTO_PACCO_CRITERI` | ✅ si può |
| Soglie proposte (articoli) | `SCONTO_PACCO_SOGLIE` | ✅ si può |
| Valute della soglia a valore | `VALUTE_SOGLIA` | ✅ si può |
| Soglie proposte a valore (€) | `SCONTO_PACCO_VALORI_EUR` | ✅ si può |
| Soglie proposte a valore (sats) | `SCONTO_PACCO_VALORI_SATS` | ✅ si può |
| Sconti proposti (%) | `SCONTO_PACCO_SCONTI` | ✅ si può |
| Soglia minima (articoli) | `SCONTO_PACCO_MIN_SOGLIA` | ✅ si può |
| Soglia minima a valore (€) | `SCONTO_PACCO_MIN_VALORE_EUR` | ✅ si può |
| Soglia minima a valore (sats) | `SCONTO_PACCO_MIN_VALORE_SATS` | ✅ si può |
| Sconto minimo (%) | `SCONTO_PACCO_MIN_PERCENTO` | ✅ si può |
| Sconto massimo (%) | `SCONTO_PACCO_MAX_PERCENTO` | ✅ si può |

### 🚚 Spedizione gratis sopra soglia

| leva | chiave | proposta |
|---|---|---|
| Spedizione gratis | `SPED_GRATIS_ATTIVO` | ⚖️ decidi tu |
| Soglie proposte (€) | `SPED_GRATIS_SOGLIE_EUR` | ✅ si può |
| Soglie proposte (sats) | `SPED_GRATIS_SOGLIE_SATS` | ✅ si può |
| Soglia minima (€) | `SPED_GRATIS_MIN_EUR` | ✅ si può |
| Soglia minima (sats) | `SPED_GRATIS_MIN_SATS` | ✅ si può |

### 🎟 Codici sconto del venditore

| leva | chiave | proposta |
|---|---|---|
| Codici sconto | `CODICI_SCONTO_ATTIVI` | ⚖️ decidi tu |
| Sconto minimo (%) | `CODICI_SCONTO_MIN_PERCENTO` | ✅ si può |
| Sconto massimo (%) | `CODICI_SCONTO_MAX_PERCENTO` | ✅ si può |
| Sconti proposti (%) | `CODICI_SCONTO_PERCENTI` | ✅ si può |
| Sconti proposti a valore (€) | `CODICI_SCONTO_VALORI_EUR` | ✅ si può |
| Sconti proposti a valore (sats) | `CODICI_SCONTO_VALORI_SATS` | ✅ si può |
| Sconto massimo a valore (€) | `CODICI_SCONTO_MAX_VALORE_EUR` | ✅ si può |
| Sconto massimo a valore (sats) | `CODICI_SCONTO_MAX_VALORE_SATS` | ✅ si può |
| Durate proposte (giorni) | `CODICI_SCONTO_DURATE_GIORNI` | ✅ si può |
| Codici per venditore | `CODICI_SCONTO_MAX_PER_VENDITORE` | ✅ si può |
| Usi massimi per codice | `CODICI_SCONTO_MAX_USI` | ✅ si può |
| Tentativi sbagliati all'ora | `CODICI_SCONTO_TENTATIVI_ORA` | ✅ si può |

### 💰 Offerte e 🌴 ferie

| leva | chiave | proposta |
|---|---|---|
| Offerta minima (% del listino) | `OFFERTA_MINIMA_PERCENTO` | ✅ si può |
| Tempo per rispondere (ore) | `ORE_RISPOSTA_OFFERTA` | ✅ si può |
| Tempo per pagare (ore) | `ORE_PAGAMENTO_OFFERTA` | ✅ si può |
| Tentativi per annuncio | `MAX_OFFERTE_ANNUNCIO` | ✅ si può |
| Rilanci per trattativa | `MAX_RILANCI_OFFERTA` | ✅ si può |
| Negozio in ferie | `FERIE_ATTIVE` | ⚖️ decidi tu |
| Ferie: quanto in là (giorni) | `FERIE_MAX_GIORNI` | ✅ si può |
| Ferie: preavviso di rientro (ore) | `FERIE_PREAVVISO_ORE` | ✅ si può |
| Banner del negozio | `BANNER_NEGOZIO_ATTIVO` | ⚖️ decidi tu |
| Banner: sconto fedeltà per livello (mai il 100%) | `BANNER_SCONTI_LIVELLO` | ⚖️ decidi tu |
| Banner: prezzo della porta (sats, prima dello sconto) | `BANNER_PREZZO_SATS` | ⚖️ decidi tu |
| Banner: prezzo pieno barrato (sats) | `BANNER_PREZZO_PIENO_SATS` | ⚖️ decidi tu |
| Banner: domini vietati | `BANNER_LINK_VIETATI` | 🔒 mai |
| Link del negozio: livello che lo sblocca | `SLUG_NEGOZIO_LIVELLO` | ✅ si può |
| Link del negozio: prezzo per ogni cambio (sats) | `SLUG_NEGOZIO_PREZZO_SATS` | ⚖️ decidi tu |
| Link toccabili in descrizione | `LINK_DESCRIZIONE_AMMESSI` | 🔒 mai |

### 💾 Consegna digitale

| leva | chiave | proposta |
|---|---|---|
| Tetto per compratori nuovi (sats) | `TETTO_DIGITALE_NUOVI` | ⚖️ decidi tu |
| Vendite minime per vendere digitale | `DIGITALE_MIN_VENDITE` | ⚖️ decidi tu |

### 🛡 Moderazione

| leva | chiave | proposta |
|---|---|---|
| Terza via (il dubbio va in revisione) | `MODERAZIONE_REVISIONE` | ⚖️ decidi tu |
| Attesa dichiarata al venditore (ore) | `REVISIONE_ATTESA_ORE` | ✅ si può |
| Sollecito ai moderatori (giorni) | `REVISIONE_SOLLECITO_GIORNI` | ✅ si può |
| Categorie proposte dopo ogni import | `RICATEGORIZZA_AUTO` | ✅ si può |

### 🟣 Nostr e canali

| leva | chiave | proposta |
|---|---|---|
| Relay Nostr | `RELAY_NOSTR` | 🔒 mai |
| Relay in più per l'import | `RELAY_NOSTR_IMPORT` | 🔒 mai |
| Import aperto da Nostr | `IMPORT_NOSTR_APERTO` | ⚖️ decidi tu |
| Barattolo pubblica su Nostr | `NOSTR_NSEC_PIATTAFORMA` | 🔒 mai |
| Post automatici | `POST_AUTOMATICI` | ⚖️ decidi tu |
| Canale Telegram | `TELEGRAM_CANALE_ID` | 🔒 mai |
| Ritmo della vetrina | `/vetrina` | 🔒 mai |
| Post singoli all'ora | `POST_MAX_ORA` | ✅ si può |
| Un post per venditore ogni (giorni) | `PROMO_GIORNI_VENDITORE` | ✅ si può |
| Da quanti annunci esce un post solo | `SOGLIA_AGGREGA` | ✅ si può |
| Sconti lampo nel canale | `POST_LAMPO_CANALE` | ✅ si può |
| Riepilogo settimanale | `RIEPILOGO_SETTIMANALE` | ⚖️ decidi tu |
| Annunci minimi per il riepilogo | `RIEPILOGO_MINIMO` | ✅ si può |
| Negozi raccontati per raffica | `MAX_NEGOZI_RAFFICA` | ✅ si può |
| Link nella didascalia del negozio | `MAX_LINK_NEGOZIO` | 🔒 mai |
| Podio nel riepilogo | `RIEPILOGO_IMMAGINE` | ✅ si può |

### 🏪 Negozi collegati

| leva | chiave | proposta |
|---|---|---|
| Prodotti letti per giro | `MAX_PRODOTTI_CONNETTORE` | ✅ si può |
| Annunci nuovi per giro | `MAX_NUOVI_CONNETTORE_GIRO` | ✅ si può |
| Annunci nuovi all'ora nel rodaggio | `MAX_NUOVI_CONNETTORE_RODAGGIO` | ✅ si può |
| Ore di rodaggio di un negozio nuovo | `ORE_RODAGGIO_CONNETTORE` | ✅ si può |
| Giri falliti prima dell'avviso | `CONNETTORI_ERRORI_MAX` | ✅ si può |
| Negozi per venditore | `MAX_CONNETTORI_VENDITORE` | ⚖️ decidi tu |
| Freno dell'«🔄 Aggiorna ora» (secondi) | `CONNETTORI_SYNC_MANUALE_S` | ✅ si può |
| Tetto delle tariffe dichiarate (€) | `MAX_TARIFFA_CONNETTORE` | ✅ si può |
| Tetto delle tariffe dichiarate (sats) | `MAX_TARIFFA_CONNETTORE_SATS` | ✅ si può |

### 🏷️ Vetrina e limiti

| leva | chiave | proposta |
|---|---|---|
| Mercato e Lavoro in vetrina | `MERCATO_LAVORO` | ⚖️ decidi tu |
| Modifica di più annunci insieme | `MODIFICA_MASSIVA_ATTIVA` | ⚖️ decidi tu |
| Cartello «fase di test» | `BANNER_TEST` | ✅ si può |
| Bottone del canale nel cartello | `BANNER_TEST_LINK` | 🔒 mai |
| Contatore degli utenti | `CONTATORE_UTENTI` | ✅ si può |
| «Pubblicato N giorni fa» fino a (giorni) | `GIORNI_DATA_ANNUNCIO` | ✅ si può |
| Annunci per venditore in ogni finestra della vetrina | `VETRINA_PER_VENDITORE` | ✅ si può |
| Larghezza della finestra (card consecutive) | `VETRINA_FINESTRA` | ✅ si può |
| Annunci nel barattolo | `MAX_PREFERITI` | ✅ si può |
| Pezzi per annuncio | `MAX_QUANTITA_ANNUNCIO` | ✅ si può |
| Annunci diversi in un carrello | `MAX_RIGHE_SET` | ✅ si può |

### 👥 Più account

| leva | chiave | proposta |
|---|---|---|
| Più account ovunque | `PIU_ACCOUNT_OVUNQUE` | ⚖️ decidi tu |
| Account insieme sullo stesso dispositivo | `MAX_ACCOUNT_BROWSER` | ⚖️ decidi tu |
| Entra dal bot | `LOGIN_DAL_BOT` | ⚖️ decidi tu |

### 🏆 Classifica

| leva | chiave | proposta |
|---|---|---|
| La classifica del mercatino | `CLASSIFICA_ATTIVA` | ⚖️ decidi tu |
| Nomi in pubblico | `CLASSIFICA_TOP` | ✅ si può |
| Peso della media del mercatino | `CLASSIFICA_K` | ✅ si può |
| XP-ordine per il bonus pieno | `CLASSIFICA_XP_RIF` | ✅ si può |
| Quanto può contare il commercio | `CLASSIFICA_PESO_XP` | ✅ si può |
| Persone per il bonus pieno del commercio | `CLASSIFICA_KD` | ✅ si può |

### 🔁 Scambio P2P (Mostro)

| leva | chiave | proposta |
|---|---|---|
| Scambio P2P | `P2P_ATTIVO` | ⚖️ decidi tu |
| Coordinator (npub) | `MOSTRO_NPUB` | 🔒 mai |
| Fase di prova P2P | `P2P_PROVA_IDS` | 🔒 mai |
| Statistiche P2P: amministratori | `P2P_STATISTICHE_IDS` | 🔒 mai |
| Soglia delle dispute P2P (%) | `P2P_DISPUTE_SOGLIA_PERCENTO` | ⚖️ decidi tu |
| Dispute P2P escluse dal conto | `P2P_DISPUTE_ESCLUSE` | ✅ si può |
| Relay del coordinator | `MOSTRO_RELAY` | 🔒 mai |
| Commissione P2P — listino (%) | `P2P_COMMISSIONE_PERCENTO` | ⚖️ decidi tu |
| Link dentro Telegram → Mini App | `TELEGRAM_MINIAPP_LINK` | 🔒 mai |
| Card P2P in vetrina | `P2P_IN_VETRINA` | ⚖️ decidi tu |
| Campagna P2P a tutti | `P2P_CAMPAGNA_TUTTI` | ⚖️ decidi tu |
| Card «P2P in arrivo», data | `P2P_IN_ARRIVO_FINO` | ✅ si può |
| Prese P2P dalle (ora italiana) | `P2P_PRESE_DA` | ✅ si può |
| Tetto ordini P2P dal collaudo (sats) | `P2P_MAX_SATS_PROVA` | ⚖️ decidi tu |
| Tetto ordini P2P (€) | `P2P_MAX_EURO` | ⚖️ decidi tu |
| Minimo PayCode Barattozon (€) | `BARATTOZON_MIN_EURO` | ⚖️ decidi tu |
| Tetto contanti di persona (€) | `P2P_CONTANTI_MAX_EURO` | ⚖️ decidi tu |
| Cauzione nel contanti di persona | `P2P_CAUZIONE` | ⚖️ decidi tu |
| Cauzione sul metodo scelto (nodo alla -bar7) | `P2P_CAUZIONE_SUL_METODO` | ⚖️ decidi tu |
| Tempo di chi pubblica: pausa, badge, penalità | `P2P_TEMPO_DI_CHI_PUBBLICA` | ⚖️ decidi tu |
| Paracadute degli ordini P2P | `P2P_PARACADUTE` | ⚖️ decidi tu |
| Chat nello scambio P2P | `P2P_CHAT_SCAMBIO` | ⚖️ decidi tu |
| Avvisi dei nuovi ordini P2P | `P2P_AVVISI_NUOVI_ORDINI` | ✅ si può |
| Avvisi nuovi ordini — finestra (minuti) | `P2P_AVVISI_NUOVI_MINUTI` | ✅ si può |
| Sconto fedeltà P2P (punti % per parte) | `P2P_SCONTO_FEDELTA_PERCENTO` | ⚖️ decidi tu |
| Sconto fedeltà P2P — porta del coordinatore | `P2P_SCONTO_SEGRETO` | 🔒 mai |
| Ronda del nodo — porta dei pagamenti | `RONDA_NODO_SEGRETO` | 🔒 mai |
| Avvisi P2P — porta del coordinatore | `P2P_EVENTI_SEGRETO` | 🔒 mai |
| Profilo legato all'account | `SEGRETI_PROFILO_P2P` | 🔒 mai |
| Versione del profilo | `SEGRETO_PROFILO_P2P_VIVA` | 🔒 mai |
| Specchi del libro | `MOSTRO_RELAY_SPECCHIO` | 🔒 mai |
| Relay che confermano | `MOSTRO_RELAY_CONFERMA` | 🔒 mai |

### ⛓️ Pagamento on-chain

| leva | chiave | proposta |
|---|---|---|
| Pagamento on-chain | `ONCHAIN_ATTIVO` | ⚖️ decidi tu |
| Solo gli admin | `ONCHAIN_SOLO_ADMIN` | ✏️ fatta (27 ott, richiesta di Andrea) |
| Libreria del 2-di-3 (embit) | `pip install embit` | 🔒 mai |
| Terza chiave (Barattolo) | `ONCHAIN_XPUB` | 🔒 mai |
| Quota fissa di Barattolo (sats) | `ONCHAIN_QUOTA_FISSA_SATS` | ✏️ fatta |

### 🪙 Punti e dollari su RGB (hackathon)

| leva | chiave | proposta |
|---|---|---|
| Punti e dollari su RGB | `RGB_ATTIVO` | ⚖️ decidi tu |
| Fase di prova RGB | `RGB_PROVA_IDS` | 🔒 mai |
| Nomi NIP-05 di casa | `NIP05_NOMI` | 🔒 mai |

### 🔔 Avvisi ai moderatori

| leva | chiave | proposta |
|---|---|---|
| Campanello dei nuovi iscritti | `AVVISI_ISCRITTI` | ✅ si può |
| Avvisi singoli all'ora | `AVVISI_ISCRITTI_MAX_ORA` | ✅ si può |
| Polso degli ordini | `AVVISI_ORDINI_ADMIN` | 🔒 mai |
| Termometro delle sottocategorie | `TERMOMETRO_SOTTOCATEGORIE` | ✅ si può |
| Termometro: sotto questi vuoti tace | `TERMOMETRO_SOTTOCATEGORIE_MINIMO` | ✅ si può |

### 💬 Chat negli ordini del mercatino

| leva | chiave | proposta |
|---|---|---|
| Chat negli ordini del mercatino | `MERCATINO_CHAT_ORDINI` | ⚖️ decidi tu |

### 🆕 Avvisi del mercatino

| leva | chiave | proposta |
|---|---|---|
| Avvisi dei nuovi annunci e dei venditori seguiti | `MERCATINO_AVVISI_NUOVI` | ✅ si può |
| Nuovi annunci — finestra (minuti) | `MERCATINO_AVVISI_NUOVI_MINUTI` | ✅ si può |
| Venditore seguito — finestra (minuti) | `MERCATINO_AVVISI_SEGUI_MINUTI` | ✅ si può |

### 💡 Suggerimenti ai venditori

| leva | chiave | proposta |
|---|---|---|
| Accesi di serie | `SUGGERIMENTI_DI_SERIE` | ✅ si può |
| Ritmo: uno ogni (giorni) | `SUGGERIMENTI_OGNI_GIORNI` | ✅ si può |
| Invito ai corrieri: quante volte | `INVITO_CORRIERI_MAX` | ✅ si può |
| Avviso «indica i tuoi corrieri» | `AVVISO_CORRIERI_PUNTI` | ✅ si può |
