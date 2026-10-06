# Nome e foto del profilo a scelta, per 20.000 sats (6 ott 2026)

Studio, nessuna modifica al codice. Letto su `origin/main` (eea8d6e).
Domanda di Andrea: «Personalizza nome e foto profilo con 20.000 sats».
Com'è oggi il profilo (da dove vengono nome e foto), dove compaiono, e
il disegno a partire dalle sue idee: sblocco una tantum pagato con
fattura Lightning alla cassa di Barattolo (incasso, non deposito), nome
visualizzato e foto caricata dall'utente, regole contro l'imitazione e
contro le foto offensive, controllo dei moderatori prima della
pubblicazione finché la moderazione AI è spenta (credito Anthropic a
zero), rimborso o nuovo tentativo se rifiutato, cambi successivi gratis
una volta al mese. In più: il badge, il P2P, la fiducia, la privacy, il
pubblico non Telegram. Le decisioni di Andrea, date lo stesso giorno,
stanno al §7. **Il cantiere si apre dal 19 ottobre 2026**, dopo il
lancio del P2P (10 ott) e l'hackathon di Torino (17-18 ott).

## In breve

- Oggi Barattolo non ha un nome suo per l'utente: fa la FOTOCOPIA di
  un documento che sta altrove — Telegram o il kind-0 Nostr.
- Il rischio d'imitazione esiste GIÀ, gratis: chiunque può chiamarsi
  «Barattolo Assistenza» su Telegram o nel suo kind-0, e noi lo
  mostriamo. Nessun filtro guarda i nomi, nessuno guarda le foto
  profilo.
- Esiste già una strada gratuita alla personalizzazione: npub provata
  più la scelta «Nostr» nel cassetto Identità. Il prodotto a pagamento
  vende COMODITÀ e un CONTROLLO UMANO, non un potere nuovo.
- Il disegno: una quarta scelta nel selettore («✏️ Mio»), un
  «cartellino» timbrato da un moderatore, la porta comprata col calco
  ESATTO dello sblocco del banner (pagamenti, ripresa, lapide, libro
  mastro, rimborso per motivo). L'80 % è riuso.
- Fiducia salva per costruzione: recensioni, XP, livello, distintivi
  sono appesi al `tg_id`, non al nome.

## 1. Com'è oggi

**Il nome** (`utenti.nome`):
- Telegram: il `first_name`, riscritto a OGNI richiesta della Mini App
  e al login web (`_upsert_da_telegram`, la sola porta). Lo username è
  un campo a parte e si aggiorna sempre.
- Nativo Nostr (`tg_id` negativo): nasce come npub abbreviata
  (`crea_utente_nostr`), poi il `display_name`/`name` del kind-0, al
  massimo 40 caratteri (`nome_da_profilo`, `MAX_NOME_NOSTR`),
  rinfrescato ogni `GIORNI_AVATAR` (7) da `aggiorna_profilo_social` e
  dal giro `rinfresca_profili_nostr`.
- Telegram con npub provata e scelta esplicita «Nostr»
  (`avatar_scelta='nostr'`, set 2026): il nome viene dal kind-0 e
  `_upsert_da_telegram` non lo riscrive più.

**La foto** (`utenti.avatar`): un francobollo di `AVATAR_LATO` (128
px), ricompresso JPEG in `foto/` (`_salva_avatar`) — la ricompressione
toglie già EXIF e GPS. Il selettore «📷 La tua foto» del cassetto
Identità (`avatar_scelta`): `''` automatico (Telegram → Nostr →
iniziale), `'telegram'`, `'nostr'`, `'nessuna'`. Un'identità sola, non
due preferenze: lo stesso selettore governa anche il nome quando vale
`'nostr'`.

**Il sito**: il login web passa dal Login Widget di Telegram (stesso
nome di Telegram) o da Nostr (nome del kind-0). Nessuno scrive il suo
nome a mano, da nessuna parte.

**I filtri**: `PAROLE_VIETATE` e `moderazione_ai` guardano titolo e
descrizione degli annunci, mai i nomi. Le foto profilo non passano da
nessun controllo: ci si fida del social di provenienza.

**Due precedenti in casa**, entrambi incassi per sé:
- lo sblocco del banner (`sblocca_banner`, `_incassa_sblocco`,
  `BANNER_PREZZO_SATS` 20.000 con lo sconto di livello da
  `_prezzo_banner_utente`, pieno 40.000): si compra LA PORTA, il banner
  nasce sempre in revisione e il vivo resta acceso finché il nuovo non
  è approvato; rimborso mai dovuto ma sempre possibile come gesto di un
  moderatore (`_rimborsa_sblocco`, `_rimborso_del_motivo`);
- il link del negozio a scelta (`negozio_slug`,
  `SLUG_NEGOZIO_PREZZO_SATS` 5.000, `SLUG_NEGOZIO_RISERVATI`,
  `_slug_negozio_libero`): la forma giudicata prima della fattura, la
  disponibilità ricontrollata all'incasso.

## 2. Dove compaiono nome e foto

Tutto legge `nome` e `avatar` da `utenti` AL MOMENTO, per join sul
`tg_id`: ordini e recensioni non tengono una copia del nome. Cambiata
la riga, cambia ovunque — circa 70 letture nel server, una decina di
punti nel client (`voltoHTML`, `avatarImg`).

Dove compaiono:
- card degli annunci e dettaglio (`venditore_nome`,
  `venditore_avatar`), pagina del negozio, anteprime Open Graph,
  widget incorporabili, pagine SEO;
- Ordini (`compratore_nome`, `venditore_nome`) e le notifiche del bot;
- recensioni (`da_nome`, `da_avatar`);
- P2P: i volti del libro (chi pubblica), la controparte nella pagina
  dello scambio (`_controparti_p2p`, «LE PARTI SI VEDONO»), le frasi
  degli avvisi (`_nome_altro_p2p`);
- classifica (con «nascondimi», `classifica_nascosta`);
- pannello admin.

Dove NON compaiono:
- dentro Mostro: il protocollo conosce solo le chiavi di scambio;
- negli eventi Nostr: il NIP-99 non porta il nome, e i client Nostr
  mostrano il kind-0 dell'utente;
- nella chat: in app non ce n'è una, ci si scrive su Telegram (dove si
  vede il nome Telegram) o in DM Nostr.

## 3. Il disegno

La metafora: oggi Barattolo fotocopia il documento; con lo sblocco
l'utente appende alla bancarella un CARTELLINO scritto da lui e
timbrato da un moderatore.

### 3.1 La quarta scelta del selettore

`avatar_scelta` prende un quarto valore, `'mia'` (nel client «✏️
Mio»), che governa nome E foto insieme come oggi fa `'nostr'`.
- Il cartellino vive in colonne sue: nome e foto approvati, nome e
  foto in attesa, stato, motivo del rifiuto, date (chiesto, approvato,
  porta aperta).
- All'approvazione si scrive in `utenti.nome` e `utenti.avatar`: le
  letture di tutto il resto non si toccano.
- Le due porte che riscrivono — `_upsert_da_telegram` e
  `aggiorna_profilo_social` (anche per i `tg_id` negativi, che oggi il
  nome lo riscrivono SEMPRE) — rispettano `'mia'` come già rispettano
  `'nostr'`.
- Tornare a Telegram, Nostr o Nessuna è sempre gratis e immediato
  (togliere non è mai un problema: il patto del banner). Rientrare su
  «Mio» rimette il cartellino già approvato, senza nuova revisione.

### 3.2 Il pagamento: il calco dello sblocco banner

- Si compra LA PORTA (il diritto di avere un cartellino, per sempre),
  non un nome preciso. Detto PRIMA di pagare, nel foglio della
  conferma.
- `pagamenti` con un motivo nuovo, `'profilo'`: guardie tutte prima
  della fattura, ripresa entro 30 minuti, annullo a lapide, incasso e
  porta aperta nella stessa transazione, avviso agli admin, il suo
  controllo nel libro mastro, la riga in `_rimborso_del_motivo` (la
  sentinella che lo tiene uguale allo smistatore degli incassi la
  vorrà).
- È un INCASSO nella cassaforte di Barattolo, non un deposito.
- Leve: `PROFILO_ATTIVO`, `PROFILO_PREZZO_SATS` (20.000; 0 = spento),
  col prezzo per utente dello stesso sconto di livello del banner.
- Chi ha già la porta non può pagarla una seconda volta (la guardia
  che protegge l'utente da noi).

### 3.3 Il rifiuto

- Un rifiuto non consuma niente: si ripropone subito, gratis, col
  motivo scritto dal moderatore.
- Il rimborso è un gesto di un moderatore, su richiesta: la porta si
  richiude, il cartellino si spegne e si torna all'automatico.
- Scartata: moderare prima e far pagare dopo l'approvazione. Niente
  rimborsi, ma uno stato nuovo («approvato, da pagare») con la sua
  scadenza, e moderatori al lavoro per chi poi non paga. Il calco del
  banner è già provato in produzione.

### 3.4 La revisione

- Ogni proposta, la prima e le successive, nasce «in revisione».
- Il cartellino vecchio RESTA esposto finché il nuovo non è approvato
  (la riga che regge il banner: niente «faccio approvare il pulito e
  lo cambio il giorno dopo»). Prima della prima approvazione resta il
  nome di prima.
- La coda nel pannello admin accanto a quella dei banner, col
  sollecito che c'è già (`REVISIONE_ATTESA_ORE`).
- Quando la moderazione AI tornerà accesa: il nome nel prompt come oggi
  per i testi; la foto vuole un modello che vede (centesimi a foto).
  Anche allora l'AI segnala e la persona decide sui dubbi.

### 3.5 I cambi successivi

- Un cambio approvato ogni 30 giorni, gratis. Il conto parte
  dall'approvazione.
- Un rifiuto o una proposta ritirata non consumano il mese.
- Nome e foto nella stessa proposta = un cambio solo.
- Prima dei 30 giorni il cambio è VIETATO (decisione 4): la proposta
  non si manda, e il foglio dice da quando si potrà.

### 3.6 Le regole del nome

- Da 3 a 30 caratteri; lettere latine con le accentate italiane,
  cifre, spazio e `. - ' _`. NIENTE EMOJI né altri alfabeti: chiude i
  sosia (la «а» cirillica identica alla «a»).
- Parole vietate in ogni travestimento, sul nome NORMALIZZATO
  (minuscolo, senza accenti, 0→o, 1→i, 3→e, 5→s, senza spazi né
  punteggiatura): barattolo, admin, moderatore, mod, staff, supporto,
  assistenza, ufficiale, official, mostro, team — più `PAROLE_VIETATE`.
  ⚠️ Il collaudo dell'impersonazione insegna che «barattolo» è anche un
  vaso di vetro: sul NOME pero' il divieto vale, perché un nome non
  descrive un oggetto, dichiara chi sei.
- Sosia protetti (decisione 7): confronto normalizzato con lo staff
  (admin e moderatori), i negozi Consigliati e i venditori con almeno
  10 affari chiusi. Chi ha già quel nome resta libero di tenerlo.
- La macchina ferma i casi netti PRIMA della fattura; il moderatore
  giudica il resto.

### 3.7 Le regole della foto

- Si carica come il banner (JPEG, PNG, WebP, HEIC: `_byte_banner`),
  diventa un quadrato di 128 px, la ricompressione toglie il GPS.
- Vietati: nudo, violenza, simboli d'odio; loghi di Barattolo, di
  Mostro o di negozi altrui; testo tipo «admin», «supporto»; QR code e
  indirizzi di pagamento (la truffa del «inquadra per pagarmi»); foto
  riconoscibili di altre persone.

### 3.8 Il badge e il bollino

- ✏️ accanto al nome di chi ha il cartellino (decisione 5). Al tocco:
  «Nome e foto scelti su Barattolo, controllati da un moderatore il …».
  NON fra i Distintivi: quelli si guadagnano usando il mercatino, e uno
  comprato li svaluterebbe (la regola sta sopra `DISTINTIVI`).
- 🛡️ Staff: lo dà solo il server, ad admin e moderatori, e non si
  compra. È il segno positivo che batte qualunque filtro: si impara a
  cercare il bollino, non a diffidare dei nomi. Per decisione 8 nasce
  PRIMA, nel cantiere anti-imitazione dopo il lancio (§6), anche senza
  il profilo a pagamento.

### 3.9 Fiducia e storico

- Recensioni, XP, livello, distintivi, vendite: tutto sul `tg_id`. Un
  nome nuovo non cancella niente, per costruzione (e `_ricalcola_rating`
  ricalcola, non incrementa).
- Il rischio è l'opposto: ripulirsi col nome, o cambiarlo a ordine
  aperto. Le cure:
  - la pagina del negozio dice «Nome scelto dal …»;
  - all'approvazione parte un avviso a chi ha un ordine o uno scambio
    P2P APERTO con lui (decisione 9): «Mario ora si chiama Bottega del
    Riuso»;
  - lo storico dei nomi lo vedono solo i moderatori, per le dispute.

### 3.10 Il P2P e le chiavi Nostr

- Mostro, le chiavi di scambio, la reputazione sul coordinatore: nessun
  tocco. Nessuna nsec, nessuna firma: la regola ferrea 2 è salva.
- Il cartellino si vede solo dentro Barattolo (libro e pagina dello
  scambio). Gli altri client Mostro e Nostr vedono il kind-0 o niente:
  va detto nella spiegazione.
- Il P2P è il posto dove l'imitazione costa di più — contanti a mano,
  moderatori veri che nelle dispute contattano le parti: lì il bollino
  Staff e il divieto di «moderatore» pesano più che altrove.

### 3.11 La privacy

Molti pagheranno per NASCONDERE il nome vero di Telegram. Prima di
pagare va detto cosa il cartellino non nasconde:
- lo @username: sta nel link condiviso del negozio
  (`/negozio/<username>`, `baseCondivisione()` nel client) e lo vede la
  controparte di un ordine per scriverti. Il link del negozio a scelta
  (5.000) lo toglie dal link: vendita abbinata naturale;
- nella chat Telegram la controparte vede il nome Telegram;
- gli admin sanno comunque chi sei.

«Dimentica il profilo» cancella cartellino, foto caricate e storico. La
fusione Telegram + Nostr si porta dietro la porta e il cartellino, come
già fa con `banner_sbloccato_il`.

### 3.12 Il pubblico non Telegram

- Nativi Nostr: nome e foto li hanno già dal kind-0. Lo sblocco serve
  loro solo per un nome diverso su Barattolo che altrove: stesso
  prezzo, stesse regole, e il rinfresco del kind-0 deve rispettare
  `'mia'`.
- Login web: come la Mini App. Fattura Lightning uguale per tutti.

## 4. Il costo

- Lavoro: banner più link del negozio messi insieme, ~1,5–2 giornate di
  sessioni con prove, collaudo col server vero e giro dal vivo. L'80 % è
  riuso: pagamenti, revisione, rimborso, upload, francobollo.
- Costi vivi: nessun servizio nuovo; 5–10 KB a foto; ~1 minuto di
  moderatore a proposta; l'AI, quando tornerà, centesimi.
- Ricavo: piccolo all'inizio (101 pionieri, la strada Nostr gratuita).
  20.000 sats sono ~20 € col bitcoin a 100.000 €: il prezzo del banner.

## 5. I rischi

1. Le regole di Telegram sui beni digitali nelle Mini App (le Stelle):
   riguardano già banner e link. Decisione di Andrea: per ora si lascia
   perdere.
2. Un'imitazione che passa un moderatore stanco: la macchina sui casi
   netti, il bollino Staff.
3. Una promessa di privacy fraintesa: dirlo prima di pagare (§3.11).
4. Le strade gratuite restano senza filtro finché non arriva il
   cantiere del §6: le regole proteggerebbero solo chi paga.
5. La coda di moderazione come collo di bottiglia: chi paga e aspetta.
6. Il calendario: lancio P2P il 10, hackathon il 17-18.

## 6. Il cantiere a parte: anti-imitazione sui nomi gratuiti e bollino Staff

Decisione 8: dopo il lancio, PRIMA del profilo a pagamento e senza
dipendere da lui. Le stesse regole del §3.6 (normalizzazione, parole,
sosia) applicate ai nomi che arrivano da Telegram e dal kind-0, più il
bollino 🛡️ Staff del §3.8. Da decidere in quel cantiere: cosa si
mostra al posto di un nome che non passa (l'iniziale e «utente
Telegram»? il nome con un avviso?) — un nome Telegram non si può
rifiutare come si rifiuta una proposta, lo sceglie l'utente fuori da
qui. Il profilo a pagamento poi riusa il giudice del nome, scritto una
volta sola.

**Il bollino è FATTO il 6 ott 2026** (prima del lancio, richiesta di
Andrea): `e_staff` e `bollinoStaff`, voce in CANTIERI «Il bollino 🛡️
Staff». Del §6 resta da fare il filtro sui nomi gratuiti.

## 7. Le decisioni di Andrea (6 ott 2026)

1. Prezzo 20.000 con lo STESSO sconto di livello del banner; nessun
   privilegio speciale ai pionieri, per ora.
2. Si paga PRIMA: si compra la porta.
3. Rimborso solo a mano, su richiesta.
4. Prima dei 30 giorni il cambio è vietato.
5. Sì al badge ✏️, sì al bollino 🛡️ Staff.
6. Nessuna emoji nel nome.
7. Sosia protetti: staff, Consigliati, venditori con almeno 10 affari.
8. Il filtro anti-imitazione sui nomi gratuiti (Telegram e kind-0) è
   un cantiere a parte, dopo il lancio, insieme al bollino Staff, che
   si anticipa anche senza il profilo a pagamento (§6).
9. Sì all'avviso alle controparti con ordini o scambi aperti.
10. Il cantiere si apre dal 19 ottobre 2026.
11. Le Stelle di Telegram: per ora si lasciano perdere.

## 8. Cosa resta da guardare all'apertura

- `git fetch`, PR aperte e rami: nessuno doveva esserci sopra il 6 ott.
- Il conteggio degli «affari» per i sosia: lo stesso della classifica
  (`ordini` released, `prova=0`, `_dati_classifica`) o `vendite_ok`?
  Il primo è la fonte vera, il secondo un contatore incrementale.
- Lo storico dei nomi: tabella sua o colonna JSON; quanto si tiene.
- Le prove che chiedono la colonna nuova nei loro schemi finti (la
  trappola già pagata col link del negozio: `prove_libro_mastro`,
  `prove_anteprime`, `prove_seo`).
