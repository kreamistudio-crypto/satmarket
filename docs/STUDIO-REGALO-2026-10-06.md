# Studio: il regalo a un altro iscritto (6 ottobre 2026)

Solo lo studio: nessun cantiere, nessuna riga di codice, il VPS, il nodo
e il relay non toccati. Letto su `origin/main` (`eea8d6e`): nessuna PR
aperta né ramo sul tema, e nessun cantiere in CANTIERI, nell'archivio o
in ARCHITETTURA ha mai trattato il regalo. Le decisioni di Andrea, date
lo stesso giorno, stanno in fondo (§ 10) e valgono sopra le
raccomandazioni del corpo.

**La domanda (un'idea di un utente, portata da Andrea).** Comprare un
oggetto su Barattolo e regalarlo a un altro utente iscritto. Chi regala
sceglie l'oggetto, paga, sceglie il destinatario per nick; il
destinatario riceve «🎁 [nick] ti ha fatto un regalo: accetti?»; se
accetta indica (o usa quello salvato) il suo locker o indirizzo, che chi
regala non vede mai; il venditore spedisce al destinatario. Da
considerare: il deposito di garanzia (conferma chi riceve), il rifiuto o
il silenzio (rimborso a chi regala), messaggio e confezione facoltativi,
la privacy dei due, il regalo su Barattozon, lo spam di regali, e il
badge Nostr (NIP-58) da mostrare sul profilo.

**La risposta corta.** Si fa, e si appoggia su un pezzo che esiste già:
l'ordine pagato «in attesa dell'indirizzo», che il venditore non può
spedire finché l'indirizzo manca. Il costo vero non sono le rotte nuove
(quattro o cinque) ma il GIRO DELLE 35 ROTTE dell'ordine, che oggi
conoscono due persone e domani tre: per ognuna si decide chi dei tre può
fare cosa, e un banco lo prova. Il buco di privacy vero non è chi regala
(non vede mai l'indirizzo) ma il VENDITORE, che lo vede per forza: uno
stalker con due account può regalarsi l'indirizzo della vittima. Cura
parziale: regali solo da venditori con vendite confermate, e il locker
spinto nella schermata di accettazione. Lo spam è GRATIS (il rifiuto
rimborsa tutto), quindi servono tetti. Barattozon resta fuori: lì
l'indirizzo vive nell'account Amazon di chi ha fatto l'ordine. Il badge
NIP-58 costa un'ora, perché la macchina dei distintivi → Nostr c'è già.

## 1. Com'è oggi la spedizione

Oggi un ordine è una busta con DUE nomi: `compratore_id` e
`venditore_id`. Tutto il codice ragiona così: 35 rotte
`/api/orders/{ordine_id}/…` e 48 controlli `compratore_id=?` in
`server.py`.

- **Quattro strade** (`consegna_scelta`, `via_punto`): spedizione a
  casa, punto di ritiro (locker o tabaccheria, reti in `SPEDIZIONIERI`:
  Barattolo, InPost, Poste Italiane, Altro), ritiro a mano, codice
  online.
- **A casa.** L'indirizzo lo scrive chi compra DENTRO l'ordine, cifrato
  in un posto solo (`_indirizzo_da_payload`, Fernet con
  `CHIAVE_CONTENUTI_DIGITALI`; senza chiave in produzione è un 503, mai
  il chiaro). Si legge solo da `GET /api/orders/{id}/indirizzo`, solo
  dalle due parti, MAI dal moderatore (in disputa gli arrivano i fatti:
  indicato, quando, quante correzioni). A fine ordine la scopa
  (`pulisci_indirizzi`) lo cancella, e con lui l'email per il corriere.
  Non c'è una rubrica: l'indirizzo di casa non si salva nel profilo.
- **Punto di ritiro.** Chi compra se ne salva uno PER RETE
  (`POST /api/me/punti-ritiro`, «📍 I tuoi punti di ritiro»). Il
  venditore deposita la busta di ritiro (nome del destinatario più
  codice o documento, `deposita_busta_ritiro`), che legge solo chi
  compra; l'email per il corriere è cifrata e spazzata come l'indirizzo.
- **La zona si paga al pagamento e non si cambia più**: in
  `indica_indirizzo` «il paese lo dice l'ordine», perché spostare un
  pacco da Bari a Sydney dopo che i sats sono in cassaforte è il guasto
  già chiuso.
- **L'ordine pagato «in attesa dell'indirizzo» esiste già**
  (`indirizzo_atteso=1` con l'indirizzo vuoto: il vincitore d'asta, i
  client di ieri): il gate di `segna_spedito` non lascia spedire finché
  manca. È il pezzo su cui il regalo si appoggia.
- **Conferma.** Solo chi compra (regola 5). Auto-sblocco disarmato
  (`AUTO_SBLOCCO_ATTIVO = False`), promemoria ogni
  `PROMEMORIA_CONFERMA_GIORNI`; il codice online si sblocca da solo
  `ORE_CONFERMA_DIGITALE` dopo la rivelazione.
- **Rimborso.** `_rimborsa_compratore` paga chi compra: la sua fattura
  di rimborso, o il suo Lightning address; senza nessuno dei due
  l'ordine sta in `refund` e la Mini App gliene chiede uno.
- **Il gemello dell'attesa.** L'offerta ha già il suo «aspetta la
  risposta dell'altro e scade»: `ORE_RISPOSTA_OFFERTA = 48`.

## 2. Il disegno

Il regalo aggiunge un TERZO nome sulla busta, e ogni porta della casa
deve sapere chi dei tre può entrare.

**Il giro.**
1. Sull'annuncio, accanto a «🔒 Compra in sicurezza», compare
   «🎁 Regalalo».
2. Chi regala sceglie chi riceve: lo @username Telegram ESATTO, oppure
   il link «Fammi un regalo» che chi riceve condivide dal suo profilo.
   Niente ricerca per nome, niente autocompletamento. Prima di pagare
   vede foto e nome, per non sbagliare persona.
3. Sceglie la strada — casa o punto — e ne paga la tariffa; facoltativi
   un messaggio e «niente prezzo nel pacco».
4. Paga: i sats entrano nel deposito di garanzia come oggi. L'ordine
   resta `locked` (NESSUNO STATO NUOVO, regola 4) con colonne
   `regalo_*` in più: chi riceve, l'esito (in attesa, accettato,
   non ritirato), la scadenza, il messaggio cifrato. Il venditore
   riceve «🎁 Regalo in attesa di risposta: non spedire ancora».
5. Chi riceve ha una notifica STATICA: «🎁 Hai ricevuto un regalo su
   Barattolo». Il nick e il messaggio si vedono solo dentro l'app — è il
   patto di sempre («il testo del compratore non entra MAI in un tubo
   HTML») e impedisce di usare il proprio nome come pubblicità. Nell'app
   vede chi regala, l'oggetto, il venditore con le sue vendite e il
   messaggio, NON il prezzo.
6. Se accetta, indica il punto (già compilato se ne ha uno salvato su
   una rete del venditore) o l'indirizzo, nella strada scelta da chi ha
   pagato.
7. Il venditore spedisce. La busta di ritiro la legge chi riceve.
8. Chi riceve conferma la ricezione: i sats vanno al venditore, gli XP
   a chi ha regalato (è lui che ha comprato), la recensione la lascia
   chi riceve (è lui che ha avuto l'oggetto in mano).

**Chi vede cosa.**

| | Chi regala | Chi riceve | Venditore | Moderatore |
|---|---|---|---|---|
| Indirizzo, punto, busta, email corriere | **mai** | sì | sì | mai |
| Tracking (rivela la città) | no | sì | sì | solo i fatti |
| Prezzo | sì | **no** | sì | sì |
| Messaggio | sì | sì | no | solo se segnalato |
| Stato dell'ordine | sì | sì | sì | sì |

Il venditore vede chi ha pagato (come oggi) e di chi riceve solo i dati
per spedire, non l'identità su Barattolo.

**Rifiuto o silenzio.**
- Settantadue ore per rispondere, con un promemoria a metà. L'offerta ne
  dà 48; il regalo ne vuole di più, perché arriva anche a chi non apre
  l'app ogni giorno.
- Rifiuto o scadenza: `annullato` e rimborso intero a chi ha pagato,
  dalla stessa `_rimborsa_compratore` (fattura o Lightning address);
  l'annuncio torna in vetrina.
- A chi ha regalato si dice LA STESSA FRASE nei due casi («Il regalo non
  è stato ritirato»): chi riceve può dire di no senza che si sappia.
- Chi regala può ritirare il regalo finché non è accettato.
- I promemoria e i solleciti verso il venditore
  (`PROMEMORIA_SPEDIZIONE_GIORNI` e i fratelli) partono
  dall'ACCETTAZIONE, non dal pagamento: prima non può spedire.

**Il deposito di garanzia.**
- Conferma e disputa le apre chi riceve. La regola 5 regge: protegge
  dal venditore, e chi riceve non è il venditore.
- Qualunque rimborso va SEMPRE a chi ha pagato, anche dopo un reso
  spedito da chi riceve.
- Se chi riceve non conferma mai, chi regala può sollecitarlo ma non
  confermare al suo posto (non sa se il pacco è arrivato). Il venditore
  resta coperto come oggi: promemoria e disputa.
- Lo stepper della cassaforte prende un passo in più, «🎁 In attesa di
  chi riceve», prima di «spedito».

**Messaggio e confezione.**
- Il messaggio: al massimo 200 caratteri (`MAX_NOTA`), una riga, niente
  link; cifrato come l'indirizzo e spazzato dalla stessa scopa a fine
  ordine; mai nella notifica Telegram; «Segnala» accanto.
- La confezione, in fase 1, è una spunta gratuita: «È un regalo: niente
  prezzo nel pacco». Il pacco regalo a pagamento vuole un campo nuovo
  nell'annuncio («Confezione regalo +X sats»): fase 2.

**Fuori dalla fase 1.**
- Il ritiro a mano: farebbe incontrare venditore e destinatario e
  rivelerebbe un luogo.
- Servizi, aste, offerte, annunci importati da Nostr.
- L'estero: chi regala paga la zona prima di sapere dove sta chi
  riceve. Fase 1 solo Italia; chi sta altrove può rifiutare.
- Il codice online invece ENTRA: è il caso più semplice, la rivelazione
  la fa chi riceve.

## 3. Privacy: il buco vero

Chi regala non vede l'indirizzo, ma il VENDITORE sì, per forza. Uno
stalker con due account pubblica un annuncio col secondo, lo regala alla
vittima, lei accetta e scrive l'indirizzo, e lui lo legge. Contro il
doppio account una cura intera non c'è; tre parziali:
- regali solo sugli annunci di venditori con almeno N vendite
  confermate; chi regala, chi vende e chi riceve tre `tg_id` diversi;
- la schermata «Accetti?» mostra le vendite del venditore e spinge il
  LOCKER: «chi vende vede solo il punto e la tua email, non casa tua»,
  e dice chiaro che a casa il venditore legge l'indirizzo;
- se chi riceve ha un punto salvato su una rete del venditore, la
  scelta pronta è quella.

Una riga nella privacy policy: trattiamo l'indirizzo di una persona che
non ha comprato. Lo scrive lei, col suo consenso, cifrato e poi
spazzato — regge, ma va detto.

## 4. Abuso e spam

Il rifiuto restituisce tutto, quindi lo spam di regali NON COSTA NIENTE
a chi lo fa. I tetti proposti:
- al massimo 3 regali in attesa per chi regala, 1 in attesa per coppia;
- dopo un rifiuto o una scadenza, la stessa coppia ferma 30 giorni;
- «Non ricevere più regali da questa persona», silenzioso;
- l'interruttore «🎁 Accetto regali» nel profilo;
- un tetto alle ricerche dello @username (per esempio 20 all'ora), così
  nessuno compila l'elenco degli iscritti;
- la notifica statica (§ 2) toglie il nome come canale pubblicitario.

## 5. Barattozon

Barattozon non è un ordine del mercatino: è uno scambio P2P dove
l'ordine Amazon esiste già, con l'indirizzo dentro l'account Amazon di
chi l'ha creato. Per regalare, chi regala scriverebbe lui l'indirizzo
su Amazon, e la promessa «non lo vedi mai» cade. Amazon ha già la sua
opzione regalo (indirizzo del destinatario, messaggio, ricevuta senza
prezzo), e i buoni regalo Amazon sono esclusi dal PayCode (Cantieri,
«I limiti di Amazon "Paga in contanti" dentro Barattozon»). La variante
«a rovescio» — chi riceve prepara il carrello col suo indirizzo e chi
regala paga il PayCode al tabacchino — non ha bisogno di Barattolo: è
un contante dato a mano. Proposta: Barattozon fuori, con una riga nella
guida.

## 6. Il badge Nostr (NIP-58)

LA MACCHINA C'È GIÀ (Architettura, «IL BADGE NIP-58 DELLE LIVE», e
Cantieri, «IL QUINTO GIRO»): i dodici `DISTINTIVI` interni diventano
badge Nostr da soli, kind 30009 più kind 8, per chi ha la npub
verificata (`premia_distintivi` → `_premia_distintivo` →
`_premia_pubkey`).
- Un distintivo nuovo al PRIMO REGALO CONFERMATO — non pagato: con
  rifiuto e rimborso si raccoglierebbe il badge senza regalare niente.
  Costo: un'ora più le prove.
- Solo a chi regala, mai a chi riceve: sarebbe un «ha ricevuto un
  regalo» pubblico, legato alla sua npub.
- Sul profilo Barattolo i distintivi si vedono già.
- Sul profilo NOSTR serve un kind 30008 (Profile Badges) firmato
  DALL'UTENTE: il server non può (regola 2). Un bottone «Mostra sul tuo
  profilo Nostr» che fa firmare nel browser — estensione o bunker,
  gradini già approvati nella SCALA NOSTR — è un cantierino a parte di
  mezza giornata. ⚠️ Il 30008 è sostituibile per intero: prima si legge
  quello esistente dai relay e poi si aggiunge, o si cancellano gli
  altri badge dell'utente.

## 7. Il costo

- **Server**: le colonne `regalo_*`; quattro o cinque rotte nuove
  (cerca chi riceve, regala, accetta, rifiuta o ritira, preferenze); il
  GIRO DELLE 35 ROTTE dell'ordine con la decisione, per ognuna, di chi
  dei tre può fare cosa; l'orologio (scadenza e promemoria); le
  notifiche a tre; la scopa estesa al messaggio; il gate di
  `segna_spedito` sull'accettazione.
- **Client**: il bottone e il foglio del regalo, la schermata «Hai un
  regalo», l'ordine visto da tre ruoli (nella scheda «Ordini»), il passo
  in più nello stepper, le preferenze, il link «Fammi un regalo».
- **Prove**: un banco che per OGNI rotta d'ordine prova le tre persone
  — il cuore: deve dimostrare che chi regala non legge mai indirizzo,
  busta, email né tracking — più la sentinella che conta le rotte, così
  una rotta nuova non nasce senza la sua decisione. I collaudi vogliono
  una QUARTA identità finta (oggi sono 111, 222, 999): la regola 6 di
  CLAUDE.md cambia, ed è un commit a parte.
- **Stima**: 4-6 sessioni piene (server 2, client 2, prove e giro dal
  vivo 1-2), più mezza per il badge.
- **Calendario**: non prima del 19 ottobre (il P2P il 10, l'hackathon
  il 17-18). Il regalo ha la sua stagione: pronto per metà novembre, in
  tempo per Natale.

## 8. I rischi

1. Una delle 35 rotte dimenticata, e chi regala legge l'indirizzo. Cura:
   il banco a tre e la sentinella che conta le rotte.
2. Il venditore-stalker (§ 3).
3. Lo spam gratis (§ 4).
4. Chi riceve non conferma mai: i sats restano fermi, come oggi con un
   compratore muto.
5. Chi regala non ha un Lightning address: l'ordine resta in `refund`
   finché non dà una fattura. Succede già oggi, si eredita.
6. L'indirizzo di un terzo: la riga nella privacy policy (§ 3).

## 9. Cosa resta da guardare quando si apre il cantiere

- Se la tariffa del punto e quella di casa differiscono per lo stesso
  annuncio (oggi non verificato): la decisione 4 la rende indifferente,
  ma il foglio del regalo deve mostrare la tariffa della strada scelta.
- Il carrello di un venditore (più pezzi in un ordine): se l'ordine è
  l'unità, il regalo lo eredita; da verificare prima di scrivere.
- Chi riceve deve aver avviato il bot perché la notifica arrivi: se non
  l'ha fatto, l'invito resta nell'app e la scadenza fa il resto.

## 10. Le decisioni di Andrea (6 ottobre 2026)

1. Si fa, dopo il 19 ottobre, pronto per metà novembre.
2. Chi riceve si sceglie con lo @username esatto più il link «Fammi un
   regalo»; niente ricerca per nome.
3. Settantadue ore per accettare.
4. Casa o punto lo sceglie chi regala, che ne paga la tariffa.
5. Fase 1 solo Italia.
6. La stessa frase a chi regala per rifiuto e silenzio.
7. Il prezzo nascosto a chi riceve.
8. Regali solo su annunci di venditori con almeno 3 vendite confermate.
9. «Accetto regali» acceso di default, con i tetti (§ 4) e il blocco
   per persona.
10. Sì al messaggio; la confezione a pagamento in fase 2.
11. Il distintivo «🎁 Cuore d'oro» al primo regalo confermato, col suo
    badge Nostr; il bottone per il profilo Nostr dopo.
12. Barattozon fuori, con una riga nella guida sull'opzione regalo di
    Amazon.
