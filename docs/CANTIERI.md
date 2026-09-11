## Cantieri

Un paragrafo per cantiere, in ordine di tempo: cosa si è deciso, i
PERCHÉ, le strade scartate, cosa è stato provato e cosa resta da
guardare. È la memoria del progetto, e i perché valgono più dei fatti:
prima di rovesciare una decisione, si cerca se qualcuno l'ha già presa
e perché.

Non c'è un indice e non deve nascerne uno: ogni voce porta il suo nome
nella prima riga, e si cerca per nome —
`grep -n "sconto carrello" docs/*.md`.

Fatti (lug 2026): banner sulla demo browser; vetrina pubblica in sola
lettura (annunci veri dal browser, azioni → invito al bot); moderazione
contenuti a tre strati (parole + AI + admin); badge npub auto-dichiarato
nel profilo e sugli annunci; verifica della npub via nota pubblica
(badge 🟣, dal lug 2026 pubblico SOLO da verificata e senza ✓, vedi
Architettura); pubblicazione degli annunci verso
Nostr con la chiave della piattaforma (NIP-99 + NIP-09, vedi
Architettura); pagina negozio del venditore, interna e pubblica
(`/negozio/{username|codice}`, vedi Architettura); login web col
Telegram Login Widget (sessioni cookie, app completa dal browser,
vedi Architettura — ricordarsi `/setdomain` su BotFather); login web
con Nostr (estensione NIP-07, bunker NIP-46, nsec solo-in-pagina;
tg_id negativi e npub_accesso, vedi Architettura — gli utenti Nostr
per ora restano senza notifiche: le vedono nei loro Affari); scudo
anti-XSS `esc()` su tutti i template; Compra subito col wallet NWC
(NIP-47 lato client, secret solo in localStorage, vedi Architettura
— il percorso felice va collaudato con un wallet vero a budget
minuscolo: in locale è verificato il ripiego, non il pagamento);
doppia cittadinanza completa (righe identità nel cassetto
«🆔 Identità» del Profilo,
badge verificato promuovibile a chiave d'accesso, webhook /start del
bot e fusione atomica Nostr→Telegram, vedi Architettura — in
produzione va provata una fusione vera con un account di test);
notifiche via DM Nostr NIP-17 con scelta del canale (i nativi Nostr
finalmente ricevono gli avvisi, cassetto «🔔 Avvisi» nel Profilo, vedi
Architettura — la cifratura è verificata contro nostr-tools, ma in
produzione va provato un DM vero verso la propria npub su 0xchat o
Amethyst; sul VPS serve `pip install cryptography`); modifica annuncio
del venditore (form di Vendi riusato, moderazione completa,
ripubblicazione Nostr, vedi Architettura); foto HEIC/HEIF e WebP
accettate e convertite in JPEG (client via canvas quando può, server
con Pillow altrimenti — sul VPS serve `pip install pillow
pillow-heif`); scheda Profilo 👤 (tutto ciò che
riguarda l'utente trasloca lì da Vendi, che torna solo form di
pubblicazione; Lightning address impostabile anche da lì; canale
avvisi sempre in chiaro; dal lug 2026 riorganizzata a cassetti
richiudibili stile Vinted, testata sempre visibile e npub+verifica
riuniti nel cassetto identità; vedi Architettura); feedback e stelle
(voto 1-5 + commento a affare concluso, rating per ricalcolo,
ultimi feedback anonimi nel negozio, rimozione admin, vedi
Architettura — parte 1 della gamification); distintivi 🏅 (parte 2:
11 badge auto-assegnati per ricalcolo dai dati veri, cassetto con
griglia e conteggio «N di M» nel Profilo, chip di fiducia nel negozio
pubblico, retroattivi a ogni
avvio, vedi Architettura); badge 🟣 pubblico semplificato (solo da
npub verificata, senza ✓; il non verificato lo vede solo il
proprietario col suo invito a verificare); export CSV contabile
degli affari conclusi (bottone nel Profilo, controvalore EUR
valorizzato alla chiusura da ora in poi, vedi Architettura);
doppia valuta (lug 2026: listino in sats o in EUR a scelta del
venditore, toggle ₿/€ per chi guarda, pagamento sempre in sats col
cambio bloccato dalla vita della invoice, e la leva del tetto per
annuncio con tolleranza +20% sul drift, vedi
Architettura — collaudato in locale da cima a fondo; la riga EUR
nella ricerca AI va provata in produzione, dove la chiave Anthropic
è vera; la leva del tetto `TETTO_SATS_ANNUNCIO` esiste nel codice
ma è SPENTA di default: nessun annuncio viene limitato finché non
la si accende dal config); onboarding contestuale (lug 2026:
suggerimenti discreti al momento del bisogno — wallet NWC nel
paySheet, Lightning address e verifica npub dopo la pubblicazione —
più la checklist «Completa il profilo (N di M)» nel Profilo; «Non
ora» memorizzato in localStorage, mai in demo/vetrina, vedi
Architettura); redesign «mercatino di paese» (lug 2026: palette crema/
arancio/verde sigillo, Baloo 2+Nunito, card «Etichetta», bottoni con
ombra piena, recinto escrow tratteggiato, festa dei sats, mascotte e
barattolo con route /assets, favicon e hero desktop, vedi
Architettura — collaudato in locale su tutte le viste e i tre
viewport; da rivedere dal vivo dentro Telegram dopo il deploy);
dark mode «mercatino di sera» (lug 2026: token scuri su fondo bruno
caldo, toggle Auto/Chiaro/Scuro nel cassetto «🌗 Aspetto» del Profilo,
tg.colorScheme dentro Telegram, vedi Architettura — collaudata in
locale con contrasti AA misurati; da provare dal vivo dentro Telegram
col tema scuro e il cambio tema a app aperta); tre completamenti del
redesign (lug 2026: etichetta prezzo sempre di carta chiara anche in
dark, medagliette di fiducia del venditore nella scheda annuncio via
`venditore_distintivi`, pillola-contatore «🏅 N/M» accanto al lockup
per gli autenticati, vedi Architettura); cinque ritocchi dal feedback
dei tester (lug 2026: via la pillola-contatore, al suo posto il
tasto-tappo del Profilo in testata e nav a 3 voci; searchbar che
cerca con Invio senza bottone; ✕ «ho capito» sul banner web; il
cassetto «🆔 Identità» perde il «e Nostr» — vedi Architettura,
redesign — collaudati in locale su mobile e desktop, chiaro e scuro,
web/vetrina/demo); categorie nuove a 9 voci con pillole ordinate per
contenuto (lug 2026: catalogo `CATEGORIE`, migrazione idempotente,
vuote nascoste, vedi Architettura — collaudate in locale con
migrazione sui dati veri; la ricerca AI col set nuovo va provata in
produzione, dove la chiave Anthropic è vera); tenuta al volume
(lug 2026: paginazione keyset su vetrina/negozio/miei con scroll
infinito, indici su annunci, miniature `_min` per le card con
backfill all'avvio, cache di un giorno su /foto, shortlist a 300
della ricerca AI, ricerca semplice anonima lato server e GET del
singolo annuncio per i link condivisi, vedi Architettura — misurato
in locale con 814 annunci seminati: pagina 25× più leggera di prima
[17KB vs 436KB], query tutte sugli indici, card da ~8-25KB invece
del JPEG pieno; da rivedere dal vivo dentro Telegram dopo il deploy,
e la shortlist AI va provata in produzione con la chiave vera);
modifica firmata degli annunci importati (lug 2026: il doppio
cittadino aggiorna i suoi eventi NIP-99 da Barattolo — due fasi con
moderazione prima della firma, firma nel browser col firmatario del
login, pubblicazione sui relay dal client e copia locale allineata
subito; l'import impara il match per tag `d` e le colonne origine,
vedi Architettura — collaudato in locale da cima a fondo, casi
negativi compresi; in produzione va provata una modifica vera con la
chiave del venditore consenziente, verificando su njump che l'evento
sostituisca il vecchio anche sul suo relay personale); deduplica dei
doppioni su Nostr (lug 2026: era nel backlog, sbloccata dal match a
impronta stretta — cassetto «🔁 Doppioni su Nostr» nel Profilo con le
coppie sospette, ritiro NIP-09 solo della copia della piattaforma con
conferma esplicita, «non è un doppione» persistente in
`doppioni_ignorati`, messaggio mirato del bot dopo la fusione, vedi
Architettura — collaudata in locale da cima a fondo, casi negativi e
soglie comprese; in produzione va provato un ritiro vero verificando
su njump che sparisca SOLO l'evento della piattaforma e che
l'originale del venditore resti); import in blocco da CSV (lug 2026:
cassetto nel Profilo per i commercianti — 70 negozi in arrivo al
lancio — con modello scaricabile, foto da URL o ZIP, moderazione
COMPLETA con AI a lotti, anteprima e conferma esplicita, job
asincrono con avanzamento e report, Nostr a lotti lenti con opt-out,
vedi Architettura — collaudato in locale da cima a fondo, TestClient
e browser; in produzione va provato un import vero con la chiave AI
e un catalogo reale, e il download del modello da dentro Telegram);
post automatici dei fatti (lug 2026: nota Nostr kind-1 + post nel
canale Telegram per ogni nuovo annuncio, anti-spam a drenatore con
aggregato per le raffiche, ciclo di vita ✅ Venduto/cancellazione,
vedi Architettura — collaudato in locale con 13 verifiche simulate;
in produzione serve creare il canale, mettere il bot come admin e
`TELEGRAM_CANALE_ID` nel config del VPS, poi verificare un post vero
su canale e relay); avvisi di ricerca personalizzati (lug 2026:
criteri salvati nel cassetto «🔎» del Profilo — categorie, comune con
raggio km sul dataset comuni committato, prezzo max, parole chiave —
matching alla pubblicazione col gemello della coda promo,
anti-molestia a tre strati (dedup persistente, aggregato per le
raffiche, tetto giornaliero) e CTA «Avvisami se arriva» dopo la
ricerca a vuoto, vedi Architettura — collaudato in locale da cima a
fondo: matching positivo e negativi per ogni criterio, distanze
Milano/Monza/Pavia/Napoli, dedup sulla modifica, aggregato da
raffica, tetto col messaggio onesto, form/pausa/elimina/precompila
nel browser; in produzione va provato un avviso vero con notifica
Telegram reale); gestione completa della npub nel Profilo (lug 2026:
bottone «Rimuovi la npub dal profilo» con conferma, guardia per il
nativo Nostr che ne sarebbe chiuso fuori, canale avvisi riportato
all'automatico quando la destinazione Nostr sparisce, sottotesti che
distinguono le due leve Disabilita/Rimuovi, vedi Architettura, badge
Nostr — collaudato in locale con TestClient [31 verifiche] e nel
browser su tutti gli stati della riga Nostr); dettaglio annuncio
immersivo e preferiti col barattolino (lug 2026: foto a filo con
ritorno flottante, lightbox a tutto schermo con pinch/rotella/swipe
in vanilla JS, cassetto «🫙 Nel tuo barattolo» primo nel Profilo con
gli stati onesti dei non più disponibili, vedi Architettura —
collaudato in locale su mobile e desktop, chiaro e scuro, con
venduto nel mezzo e DEMO/vetrina senza barattolino; il pinch va
riprovato dal vivo su un telefono vero dentro Telegram); PWA
installabile — Fase 1 (lug 2026: manifest con le icone del barattolo
su tessera arancio, service worker prudente con pagina offline e
mascotte, banner «installa» discreto solo su web mobile, dentro
Telegram tutto identico per costruzione, vedi Architettura —
collaudato in locale: dispensa completa senza /api, offline vero a
server spento, guardie del banner esercitate una a una, demo file://
pulita; in produzione vanno provate l'installazione vera su Android
e iPhone e la verifica del widget Telegram in standalone, il cui
esito decide l'eventuale piano di riserva redirect); APK distribuito
sui due canali pubblici (lug 2026, Fase 3: release v1.3 su
github.com/kreamistudio-crypto/barattolo-releases per Obtainium e
download diretto, e su Zapstore con chiave Nostr dedicata fredda e
certificato legato via NIP-C1 — eventi verificati sul relay, hash e
certificato coincidenti; vedi «Distribuzione dell'APK» — restano da
fare: screenshot nella scheda Zapstore, profilo kind-0 dell'identità
release, e la prova d'installazione dallo store sul telefono); avatar
dal social di provenienza (lug 2026, richiesta di Alan: la foto
profilo Telegram o la picture del kind-0 Nostr come francobollo 128px
servito da foto/, catena Telegram→Nostr→iniziale per i doppi
cittadini, selettore «La tua foto» nel cassetto Identità —
Telegram / Nostr / Nessuna, voci solo per le sorgenti vere, default
la catena automatica — vedi Architettura — collaudato in locale: 12
verifiche server comprese la gamba Nostr sui relay veri, rendering e
ripieghi nel browser, selettore avanti e indietro con la validazione
delle sorgenti; in produzione va vista una foto Telegram vera, che
in collaudo il bot simulato non può dare); cartello «fase di test»
all'apertura (lug 2026: modale col velo sfocato, testo e link del
canale scritti nel config, una volta al giorno per dispositivo,
precedenza sul tour di benvenuto, vedi Architettura — collaudato in
locale in tutti gli stati [acceso, spento, link vuoto o storto,
server muto, stesso giorno, giorno nuovo], chiaro e scuro, mobile e
desktop, demo e vetrina; a rodaggio finito si spegne con
`BANNER_TEST = False` nel config del VPS e un riavvio); spedizione e
protezione acquisti modello Vinted (lug 2026: modalità di consegna,
costo spedizione nella valuta del listino e taglia del pacco
sull'annuncio, conto scomposto a carico del compratore col totale in
cassaforte, ritiro in zona senza stati nuovi, filtro «solo con
spedizione», leva `PROTEZIONE_PERCENTO` SPENTA di serie, vedi
Architettura — collaudato in locale: 72 verifiche TestClient sui
quattro strati compreso il giro completo a tre identità con
spedizione EUR, ritiro con auto-sblocco a 72h/10gg e annuncio
storico, più il giro visivo in Chrome headless su chiaro e scuro; in
produzione va rivisto dal vivo dentro Telegram, e quando la
protezione si accenderà dal config vanno decisi i testi con la
cifra); offerte e contrattazione sul prezzo (lug 2026, modello
Vinted: foglio con chip −10%/−20% e stima live, una sola
controproposta, accettazione = 24h per pagare col flusso di sempre
alla cifra pattuita, l'annuncio non si blocca mai e vince chi paga,
sezione «💰 Offerte» in testa alla scheda Ordini col pallino sul nav,
leve config 50%/48h/24h/3, vedi Architettura — collaudato in locale
con 51 verifiche TestClient sui quattro strati: giro pieno sats con
controproposta, giro EUR con virgola e cambio_ordine, anti-abuso
completo, decadenza per vendita, sweep delle scadenze, reaper con
ripagamento, modifica prezzo, regressione dell'acquisto normale; in
produzione va provato un giro vero dentro Telegram con le notifiche
reali); offerta lampo ai barattoli (lug 2026, modello Vinted «sconto
ai follower»: avviso anonimo «ha fatto colpo» al venditore quando
qualcuno salva, sconto pubblico a percentuale e a tempo lanciato dal
foglio del dettaglio, avviso mirato a chi ha l'annuncio nel barattolo,
badge col countdown e prezzo barrato in vetrina e dettaglio, filtro e
ordinamento «⚡ In offerta», minimo con l'accordo individuale in
compra(), scadenza che ripristina tutto da sola anche a pagina
aperta, leve nel config, vedi Architettura — collaudato in locale da
cima a fondo: valvola e cooldown in console, guardie del lancio una a
una, acquisto scontato sats ed EUR, min nei due versi, superficie
pubblica con cursore, e il giro visivo nel browser vero via CDP da
venditore e in demo; in produzione va provato un giro vero dentro
Telegram con le notifiche reali); lampo e offerte anche sugli annunci
importati da Nostr (lug 2026, decisione di prodotto: il catalogo e' uno
solo, la differenza tra nato-qui e nato-su-Nostr e' SOLO chi firma
l'evento NIP-99 — via le guardie contatto_nostr da fai_offerta,
lancia_lampo e _drena_colpo e i due l.nostr dal dettaglio; porta
«🟣 …o entra con Nostr» nel foglio invito della vetrina per il
percorso DM → link → login npub → azione; la guardia di modifica_annuncio
resta: il contenuto degli importati si cambia sui relay, la lampo e'
un'altra strada che non lo tocca; vedi Architettura, offerte e lampo —
collaudato in locale con 16 verifiche TestClient su DB usa-e-getta:
giro offerta completo sull'importato con cifra pattuita nell'ordine,
lampo lanciata/comprata scontata/annullata, «ha fatto colpo» arrivato
al venditore dell'importato, regressioni su nativo e guardie
sopravvissute; in produzione va provato il giro vero: DM NIP-17 con
link a un venditore solo-Nostr, login npub dal foglio invito e
risposta all'offerta); consegna digitale 💾 (lug 2026: quarta modalità
per buoni regalo, codici e licenze — il contenuto passa dentro
Barattolo con consegna tracciata e rivelazione-ricevuta, cifratura a
riposo fail-open, finestre corte 24/48h, regola asimmetrica dichiarata
e leve anti-frode spente di serie, servizi esclusi dalla moderazione
col messaggio gentile e prodotti digitali leciti in whitelist, vedi
Architettura — collaudato in locale con 58 verifiche TestClient su DB
usa-e-getta: giro completo consegna→rivela→sblocco 24h, silenzio 48h,
regressione dei rami fisici, cifratura nei due formati, disputa con
nota admin, leve accese e spente, import CSV e NIP-99; in produzione
va provato un giro vero dentro Telegram, la voce «buono
regalo/servizio» della moderazione AI con la chiave vera, e sul VPS va
scelta CHIAVE_CONTENUTI_DIGITALI nel config — senza, i codici restano
in chiaro nel DB, dichiarato; dal lug 2026 anche in COMBO con una
modalità fisica via `anche_digitale`: il compratore sceglie la strada
con le pillole e le tutele seguono la sua scelta, vedi Architettura —
collaudata con 32 verifiche TestClient: tutele digitali sul ramo
digitale e fisiche sul ramo fisico dello STESSO annuncio, default
fisico per i client vecchi, guardie, NIP-99 e CSV col «+»); regione
derivata e cercabile (lug 2026: nessun campo nuovo nel form — la
regione si ricava dalla sigla della provincia con una mappa fissa,
colonna sua scritta accanto alle coordinate e backfill all'avvio, voce
«Regione» nel pannello Filtri con le sole regioni che hanno annunci e
il loro numero, vedi Architettura — collaudata in locale con 42
verifiche TestClient su DB usa-e-getta [mappa, pubblicazione, modifica,
import CSV, filtro combinato e paginato, risposta legacy, backfill
idempotente] e il giro nel browser vero su chiaro e scuro, coi dati
veri e in demo; in produzione basta il riavvio: la migrazione e il
backfill girano da soli); barra d'acquisto al posto della tab bar nel
dettaglio (lug 2026, modello Vinted: aperto un annuncio comprabile la
tab bar lascia il posto a «Compra in sicurezza» col totale e
«Offerta», stessa altezza e stessa carta — niente salto di layout —
con i gemelli in pagina spenti su mobile e il recinto escrow lasciato
alle spiegazioni; guardie e cifre riusate tal quali, da desktop non
esiste, vedi Architettura — collaudata in locale a 360/375/1280px e nei
due temi: altezza allineata, lampo −20% e cambio consegna sulla cifra,
invito in vetrina, annuncio proprio con la tab bar intatta, fogli e
lightbox che le passano sopra; in produzione va rivista dal vivo dentro
Telegram, dove contano la gesture bar del telefono e il tema del
client); il varco della barra (lug 2026, subito dopo: la barra si
raggiunge senza scorrere e comprava con la consegna decisa in silenzio
— ora la barra dice sempre la strada quando ce n'è più d'una, e il
primo tocco a scelta implicita apre il foglio «Come vuoi riceverlo?»
coi totali per strada, che scegliendo chiude e procede in un gesto
solo, vedi Architettura — collaudato in locale col giro vero a 360px:
foglio, scelta, paySheet coerente, secondo tocco diretto, Escape senza
ordine, combo digitale, vetrina e regressione dei picker); quantità in
stock per annuncio (lug 2026: campo quantità nel form Vendi, stepper e
conto × N all'acquisto con spedizione una volta sola, esaurito = stato
venduto con «Rimetti in vendita» dai tuoi annunci, prenotazione
derivata dagli ordini 'creato' che chiude anche il buco storico del
doppio acquisto — deployata per prima, da sola —, offerte a prezzo
unitario, riga «disponibili» nel NIP-99 e colonna CSV, vedi
Architettura — collaudata in locale con 60 verifiche TestClient su
quattro script [prenotazione con rivale nell'await, parziale/
esaurimento/decadenze, rimborso e ricarica, superficie e import] più
il giro nel browser vero a 375px con invoice LNbits reale; è il
mattone del futuro cantiere «set»); il set «Riempi il barattolo»
(lug 2026: più annunci diversi dello stesso venditore in un ordine
solo — sezione «Altri oggetti di questo venditore» nel dettaglio,
foglio di composizione con spunte e stepper, UNA spedizione al MAX
dei costi dichiarati con la stima della taglia del pacco solo
informativa, un escrow e una conferma con disputa/rimborso
tutto-o-niente dichiarati, modello testata+ordine_righe coi mono
intonsi byte per byte, vedi Architettura — collaudato in locale con
97 verifiche TestClient su quattro script [fondamenta e guardie,
compra a righe con EUR/offerte/lampo e 409 col nome del pezzo,
ciclo di vita completo con rimborso che riattiva tutto, tabella dei
casi della stima taglia] più il giro nel browser vero con invoice
LNbits reale, vista compratore e venditore e il rivale che soffia
il pezzo a metà composizione; in produzione va provato un set vero
dentro Telegram con le notifiche reali; gli SCONTI SET alla Vinted
sono il cantierino successivo, deciso: la preparazione è
l'invariante articolo = Σ unitario×qta, lo sconto sarà una voce di
testata); card più stretta e dettaglio spogliato (lug 2026: in card
le icone si raggruppano a destra e la zona si mostra solo se è un
LUOGO vero; nel dettaglio restano luogo, consegna, condizione,
disponibilità e Nostr, mentre escono categoria, taglia del pacco,
«protezione acquisti inclusa» e il costo dalla pillola della
spedizione, che vive già nel foglio della consegna e nel conto
scomposto; collaudato a 360/375/390 e 1280px, chiaro e scuro);
il luogo si fa pulito, dentro e fuori (lug 2026, subito dopo: il
pallino Nostr esce dalle card — riguarda il venditore, non
l'oggetto, e in griglia lo spazio è poco; si mostra il solo COMUNE
estratto dal dizionario invece del testo intero — in card, e dal
giorno dopo anche nella pillola del dettaglio e nelle righe-elenco
del Profilo: una regola sola ovunque, vedi in Architettura perché
tenere il testo intero nel dettaglio non era tenibile; e in INGRESSO
la zona, pur restando facoltativa senza
ritiro, dev'essere un comune vero — l'avviso morbido del form e
dell'import CSV è diventato bloccante, con un messaggio unico e il
«forse Pavia (PV)?»: chi spedisce e basta lascia il campo vuoto,
niente più «spedisco in tutta Italia» nel campo Zona. Superficie
API: `zona_comune` in CAMPI_VETRINA, che ASSORBE il
`zona_riconosciuta` del giorno prima — il nome è anche il flag —
calcolato nel collo di bottiglia `arricchisci_righe_vetrina`; zero
colonne nuove, in produzione basta il riavvio. Conseguenza
dichiarata: gli annunci storici con la zona storta si mettono in
regola alla prima modifica, come per la condizione. Vedi
Architettura per il vincolo del cuore unico `_chiave_comune`, che
serve al prossimo cantiere. Collaudato con 16 casi mirati più
l'invariante su tutto il dataset [7.904 comuni × 3 forme], 9 casi
TestClient sulla guardia, l'anteprima CSV, i 6 stati della riga di
hint e il gate end-to-end contando le POST); riordino del dettaglio
annuncio stile Subito.it (lug 2026: data relativa sotto la foto con la
colonna `annunci.modificato` e la leva GIORNI_DATA_ANNUNCIO, titolo
con la condizione accanto, luogo come testo nudo, badge azzurro
«Spedizione disponibile» accanto al prezzo con le altre strade
discrete, titolino «Descrizione», e il 🟣 dentro il riquadro
venditore, vedi Architettura — collaudato in locale via CDP a
360/375/390 e 1280px nei due temi e con reduced-motion, sui casi
senza luogo / senza spedizione / solo digitale / lampo attiva /
annuncio storico; in produzione basta il riavvio, la migrazione gira
da sola; più le quattro rifiniture del giorno dopo: badge spedizione
sulla stessa riga del prezzo, 🟣 solo icona in fila coi badge, via i
ponti di contatto dal riquadro venditore; e le correzioni del giorno
dopo ancora: «Acquista» arancio ₿ NUDO senza prezzo — solo lui e
centrato dentro il recinto escrow, «Fai un'offerta» fuori sotto — e
nella barra fissa i due tasti gemelli piatti (offerta a sinistra)
col richiamo tratteggiato verde e il lucchettino, via le
pillole di scelta consegna dal dettaglio (la strada si sceglie nel
foglio del varco, che diventerà la pagina dedicata del prossimo
cantiere), forme rettangolari col raggio del riquadro su TUTTI i
bottoni del dettaglio — riverificate a 360/375/390 nei due temi,
col varco esercitato dal vivo); il recinto parla poco e la spedizione
si vede (lug 2026: «Acquista» un gradino più grande e i due tasti
della barra finalmente gemelli — il tratteggio diventa un outline che
non occupa layout e le basi flex vanno al 50%, la stessa lezione dei
bottoni del pannello Filtri; la spedizione a due gradi dello stesso
azzurro nel solo chip «Spedizione gratuita» sopra il prezzo — le altre
strade restano pillole normali, perché il colore veste solo ciò che è
un vantaggio — con «🚚 gratis» scritto in vetrina; il gemello col costo sotto
Acquista è nato e morto nello stesso cantiere: il recinto è il posto
della fiducia, non del listino; il recinto ridotto a una riga,
via la riga sulla invoice, e tutto il resto nella pagina nuova «Il
pagamento protetto» raggiungibile da tre porte; i tempi dell'escrow
raccolti nella costante `TEMPI` con la tabella delle leve accanto —
erano sparsi in dodici stringhe; più «Riempi il pacco» col nuovo
accento cartone e lo «Scopri di più» in inchiostro. Vedi Architettura
— collaudato in locale via CDP a 360/375/390 e 1280px nei due temi,
sui casi spedizione a pagamento / gratuita / ritiro / digitale /
storico / lampo / multi-pezzo, in vetrina anonima, in DEMO e col
wallet NWC collegato, con le tre porte e i loro ritorni, il tour
ancora intero e zero errori JS; contrasti misurati AA su tutti i
token nuovi. In produzione basta il deploy: nessuna colonna, nessuna
leva nuova. RESTA DA DECIDERE A RODAGGIO: i testi della pagina sono
scritti oggi con la commissione sospesa e la protezione spenta —
quando si accenderanno vanno riletti, in particolare «Se qualcosa va
storto» e «Dove stanno i sats»); il gesto indietro torna indietro
(lug 2026: dentro Telegram, nella PWA e nel browser il tasto/gesto
indietro non chiude più l'app — prima chiude i fogli, poi smonta le
viste, e si esce solo dalla radice; freccia ← e tab bar restano tutte
e ora dicono la stessa cosa del gesto, che è come sono spariti
`sicurezzaRitorno` e l'euristica di `tornaDalNegozio`. Vedi
Architettura per le tre scelte da non rovesciare: URL mai toccato,
ascoltatore dichiarativo, pila derivata dal DOM con un
MutationObserver — che è come i 18 siti dei fogli, `closeSheet` e le
tre chiusure mirate sono rimasti intonsi — collaudato in locale nel
browser vero a 375px: catena viste con salti multipli e AVANTI del
browser, dieci giri di tab senza far crescere la cronologia, deep link
che atterra sulla vetrina, lightbox, tour, cartello e foglio-invito,
nessun gradino morto dopo ✕/velo/Escape, e il caso a cui teneva
Andrea — picker aperto SOPRA il paySheet con invoice LNbits vera: il
primo indietro chiude solo il picker e il pollTimer resta VIVO, il
secondo chiude il foglio e lo ferma. In produzione basta il deploy:
nessuna rotta, nessuna colonna. Da provare dal vivo dentro Telegram,
dove contano la freccia di sistema e il gesto del client); Barattolo
diventa una vetrina di Nostr (lug 2026, cantiere di Alan — PR #5 —
merged con sette correzioni decise da Andrea: si importa chiunque
pubblichi NIP-99 in italiano, con scoperta ogni 6h, firme verificate
davvero, moderazione completa prima che un evento diventi una riga,
metadati di commercio nei tag, catalogo a 25 categorie e la rete di
prove in CI. Le correzioni, che sono la parte da ricordare:
l'interruttore nasce SPENTO perché il salto non sia l'effetto di un
deploy; le categorie SI AGGIUNGONO e non si rinominano, quindi zero
migrazioni e nessun annuncio spostato; la moderazione si paga una
volta sola e si rifà solo quando cambia il TESTO; dubbi E bocciature
dell'AI vanno in una coda visibile agli admin invece di sparire, e la
decisione è REVERSIBILE («↩︎ Ripensaci»); lo stock dai relay si lima
al tetto e la consegna digitale dai relay non passa; i suggerimenti su
cosa manca a un annuncio sono OPT-IN e spenti di serie — il benvenuto
resta l'unico messaggio che mandiamo senza permesso. Più i tre
ritocchi del giorno dopo: quattro icone di categoria che dicevano un
prodotto invece del reparto, il tetto della quantità a 999999 (con
tutte le quantità che passano da `fmt()`), e i due testi definitivi.
Vedi Architettura —
collaudato in locale con 48 prove pure in `prove.py` [che ora coprono
anche il modello CSV, il testo condiviso degli eventi e le due
guardie] più 26 verifiche su DB usa-e-getta [`_da_giudicare` nei sei
casi, il marchio che fa nascere in revisione, il registro legato
all'annuncio e la sua idempotenza, il giro completo
rifiuta→riapri→pubblica→riapri, la guardia degli affari in corso, la
coda «decisi», e i suggerimenti nei loro cinque casi — spenti che non
scrivono e NON timbrano, accesi che scrivono una volta sola e mai nel
giro dell'apparizione], più il foglio delle 25 categorie e
l'interruttore nei due stati guardati nel browser. IN PRODUZIONE: il
deploy da solo non cambia NIENTE — girano le migrazioni delle due
colonne (`completamento_avvisato`, `suggerimenti_annunci`) e basta;
l'import aperto si accende scrivendo la riga nel config del VPS, e
quello è il momento da guardare col journal aperto. Se il config del
VPS ha una riga `MAX_QUANTITA_ANNUNCIO` esplicita, va alzata anche lì.
RESTA DA FARE: decidere se anche lo scarto per PAROLE VIETATE debba
finire in coda come quelli dell'AI — oggi non ci va, resta uno scarto
secco visibile solo nel registro);
il primo giro vero, e l'anello che si chiudeva (lug 2026: acceso
l'import in produzione sono comparsi 40 annunci doppi, articoli
intestati al venditore sbagliato e «Altri oggetti di questo venditore»
pieno di roba d'altri — TRE sintomi di UN bug solo, la scoperta che
adottava la chiave della piattaforma come se fosse un venditore
qualsiasi. Diagnosi fatta sui dati veri con query in sola lettura
PRIMA di toccare qualunque cosa, import spento subito, e zero denaro
coinvolto: nessun ordine aperto su annunci importati. Cura in due
tempi — il TAPPO (`chiave_di_casa` + il confronto dell'autore
nell'import, che è il buco vero: non ci si fida del filtro `authors`
del relay) e la PULIZIA (`ripulisci_anello_nostr.py`), più la cintura
sull'origine nella guardia del set. Vedi Architettura, «L'ANELLO CHE
SI CHIUDEVA» — collaudato con 57 prove pure [9 nuove, compresa la
sentinella sul confronto dell'autore] e 22 verifiche su DB
usa-e-getta che RICOSTRUISCONO il bug daccapo: il negozio del fantasma
con roba di due persone, il relay che risponde con eventi di un terzo,
l'anteprima che non scrive, la copia con l'ordine aperto lasciata
stare, il secondo giro che finisce il lavoro, il rilancio a vuoto.
LEZIONE da non perdere: un cantiere che legge da una fonte pubblica
deve chiedersi per prima cosa se in quella fonte c'è anche la propria
voce).
ritocchi ai filtri e al recinto (lug 2026: le due spunte di consegna
che mancavano — «🤝 Ritiro in zona» e «💾 Codice online», col digitale
che guarda il SET delle strade per prendere anche la combo — e le
etichette senza «Solo con…», che dentro un pannello che si chiama
Filtri il «solo» lo dice il posto; e lo «Scopri di più» che passa in
coda alla frase del recinto, nel verde del testo di fiducia, legato
all'ultima parola perché sotto i 390px scendano insieme. Collaudato
coi dati veri: conteggi dei filtri incrociati con le query sul
database, composizione con condizione e regione, paginazione, risposta
legacy senza `limit` ancora un array, e il ritorno a capo del link
misurato a 360/375/390/1280 nei due temi coi contrasti AA. In
produzione basta il deploy).
E in mezzo, «📍 Vicino a me»: nato, deployato e TOLTO nel giro di due
giorni perché si sovrapponeva al filtro per regione — la storia, il
motivo e cosa è rimasto in piedi stanno in Architettura, alla voce
omonima. Con lui se n'è andata la precompilazione della Zona in Vendi:
il campo nasce vuoto e lo scrive l'utente. Resta INERTE la colonna
`utenti.comune`, che nessuno scrive e nessuno legge.
Due migliorie prima di aprire la pagina «Sfoglia» (lug 2026, decisioni
di Andrea): LA RICATEGORIZZAZIONE — l'AI propone leggendo titolo e
descrizione, i moderatori confermano dalla coda «🗂 Categorie da
sistemare» raggruppata per spostamento, e nessun annuncio cambia
casella senza che un umano l'abbia visto (~0,20 $ per 800 annunci);
più il fix all'invito opt-in, che la voce «la categoria giusta» non la
faceva partire mai. E LA CONDIZIONE CHE NON SI CHIEDE dove non vuol
dire niente: «Alimenti e bevande» e i codici online consegnati dentro
Barattolo — il campo sparisce dal form, la pillola dal dettaglio, la
riga dal pannello Filtri, e gli alimentari di ieri non si migrano ma
smettono di mostrarla. Vedi Architettura per i due giudici unici
(`senza_condizione`, `_sposta_categoria`) — collaudate in locale con
20 prove pure nuove in `prove.py` (parità dei due elenchi
server↔client compresa) e 26 verifiche TestClient su DB usa-e-getta
(guardia nei quattro casi, alimentare storico fuori dal filtro ma in
vetrina, modifica che torna a chiedere la condizione cambiando
categoria, coda con spostamento parziale, proposta stantia, 409 e
scarto), più il giro nel browser vero a 375px: campo che compare e
sparisce sui quattro passaggi, filtro che dorme e si risveglia, coda
admin con «mostra tutti» che non perde le spunte tolte a mano. In
produzione basta il deploy — la tabella `categoria_proposta` la crea
init_db —, e la coda resta vuota finché non si lancia
`python ricategorizza.py --scrivi` sul VPS.
La pagina «Sfoglia» (lug 2026): le 26 categorie diventano una vetrina —
quarta radice della nav, griglia a due colonne di piastrelle
illustrate, dieci in una schermata come nel riferimento. Il tondo del
Vendi resta al centro esatto grazie al quinto posto vuoto, e l'indietro
da una categoria torna a Sfoglia (l'unica eccezione al patto delle
radici, con la sua bandierina). Vedi Architettura — collaudata in
locale a 360/375/390 e 1280px nei due temi: nav misurata (Vendi a
180.0 su 180.0, altezza invariata, nessuna etichetta troncata), catena
del gesto indietro compresi i cinque cambi di tab che non lasciano
gradini, categoria vuota che atterra sul suo «Avvisami se arriva», la
rotta che serve solo le 26 vere (404 su nomi inventati e su
`../../config.py`), il ripiego a emoji, e 77 prove verdi con le tre
nuove sulle illustrazioni. Due problemi veri trovati e chiusi
strada facendo: i nomi di una parola sola che sbordavano dove il
browser non ha il dizionario di sillabazione, e la guardia di
`renderChips` che rimangiava la categoria scelta quando era vuota.
In produzione basta il deploy: nessuna colonna, nessuna leva —
solo i 26 file in `assets/categorie/`, che viaggiano col commit.
L'avvertimento che stava qui — cache di un giorno su nomi NON
versionati, «una rifatta resta vecchia nei browser per 24 ore» — si è
incassato per davvero (ago 2026): la PWA di Andrea mostrava DUE
generazioni vecchie insieme (il biglietto della 27ª con l'alone
«attaccato al titolo», Animali senza il pareggio) mentre la Mini App,
che ha la SUA cache WebView, era giusta — e sembrava in tutto un
render diverso nei due contesti. Ed era STRUTTURALE, non un caso: ogni
illustrazione nuova sposta la mediana dell'inchiostro e il pareggio
riscrive delle sorelle, quindi i file cambiano a ogni categoria
aggiunta. La cura, per tutte e 27: la rotta risponde
`Cache-Control: public, no-cache` — il browser tiene la copia ma la
RICONTROLLA a ogni uso, e l'ETag che FileResponse già manda fa 304
finché il file non cambia — più il timbro una-tantum `?b=2` sugli URL
del client (renderSfoglia e icoCategoria), che ha ripulito le cache
scritte col regime vecchio e NON va più toccato. Il «nome col timbro»
delle foto resta la strada se un giorno servisse rimettere il max-age.
Tre lavori sulla nav, in un cantiere solo (lug 2026): la nav non mente
più entrando da Sfoglia — si accendeva «Esplora» su una vetrina
filtrata, e chi guardava credeva fosse il mercatino intero e lo
trovava vuoto (rimedio: `ramoVetrina`, una variabile e non una vetrina
duplicata, letta dal giudice unico `voceNav()` e spenta da
`setCat('Tutto')`, cioè dal filtro che la giustifica); gli Ordini
passano all'ESTREMA destra col posto vuoto in mezzo, che è solo uno
scambio nel markup perché i cinque slot sono tutti `flex:1`; e le tre
emoji della barra diventano SVG di casa — lente, piastrelle, pacco di
tre quarti — che si ACCENDONO invece di accendere una pillola sotto di
sé. Più le icone della consegna in Vendi, che crescono a 20px e in cui
la spedizione passa dal 📦 al 🚚, cioè al disegno che la spedizione ha
in tutto il resto dell'app. Vedi Architettura, alla voce Sfoglia, per
la taratura delle icone (26px come tetto, viewBox ritagliato a
`2 2 20 20`) e soprattutto per le TRE STRADE SCARTATE col loro perché
— pacco piatto, barattolo del logo, illustrazioni a 24px — che è la
parte che serve fra sei mesi. Collaudato nel browser vero a 360px nei
due temi: nav 61,2px invariata e Vendi a 180,0 su 180,0 dopo ogni
ritocco, giro completo del ramo Sfoglia (piastrella → dettaglio →
negozio → i due indietro → tab Esplora che rimette 837 oggetti con una
richiesta senza `cat`), caselle di consegna che aprono ancora costo e
taglia, e 78 prove verdi. In produzione basta il deploy: nessuna
colonna, nessuna leva, nessun asset nuovo. Resta da vedere dal vivo
dentro Telegram, dove contano la gesture bar del telefono e il tema
del client.
Tre difetti di navigazione nati con quei due cantieri (lug 2026, tutti
e tre visti da Andrea sull'app vera). 1) I DOPPIONI entrando in una
categoria da Sfoglia: non un doppio render ma la pagina-dopo che
arriva in ritardo col cursore della vetrina di prima — rimedio
`vetrinaGiro`, vedi «Tenuta al volume». 2) IL GESTO DI AGGIORNAMENTO,
che non era di nessuno e dentro Telegram portava via la Mini App: ora
`disableVerticalSwipes` vale anche alla radice e la tirata è nostra,
coi tre recinti che tengono fuori la galleria a scroll-snap. 3) LO
SWIPE INDIETRO che da Sfoglia non faceva niente: `history.back()` alla
cieca su una sessione che ha una entry sola — ora il gradino lo dice
`d` nello state e l'ultimo passo è esplicito. E l'ultimo passo è che
ESPLORA È LA RADICE MADRE: dalle altre radici l'indietro ci passa, e
solo da Esplora si esce. Deciso in due tempi, ed è la parte da
ricordare: per un giorno la regola è stata «ogni radice esce per conto
suo» (le radici sono sorelle, non parenti), poi Andrea l'ha rovesciata
perché su Subito e Vinted la home È la radice madre — la convenzione
che gli utenti hanno già nelle dita vale più della simmetria del nostro
modello. Tutte e due le ragioni stanno in Architettura, con la
conseguenza accettata (chi apre l'app dritto su un'altra radice
all'indietro finisce in Esplora senza esserci mai passato).
Vedi Architettura, «il gesto indietro» — riprodotti tutti e tre in
locale prima di toccare niente (i doppioni misurati: 60 card di cui 14
doppie, poi 30 su 30 uniche) e ricollaudati dopo: scroll infinito su
tre pagine, due tocchi svelti su due categorie, le sei guardie del
gesto di aggiornamento, `d` che conta giusto lungo tab → piastrella →
dettaglio → i due indietro, e 78 prove verdi. In produzione basta il
deploy: nessuna colonna, nessuna leva.
E POI IL SECONDO GIRO, dalla PWA installata di Andrea (lug 2026), che
è la lezione grossa del cantiere: i primi rimedi funzionavano dentro
Telegram e NON nella PWA, che è il contesto in cui lui prova davvero.
Tre correzioni. 1) La tirata non aggiornava: ricaricava la pagina, cioè
riportava a Esplora — `overscroll-behavior` stava solo sul body e alla
viewport arriva quello dell'HTML, quindi il pull-to-refresh nativo non
era mai stato spento; e i nostri ascoltatori passivi non potevano
chiamare `preventDefault`, ora il touchmove è non-passivo mentre la
tirata è armata. 2) Da Sfoglia la PWA si chiudeva senza passare da
Esplora: lì il gesto è di SISTEMA e non passa da `navIndietro`, quindi
il passaggio dalla madre non si può intercettare — va PREPARATO, e ora
il primo passo via da Esplora spinge una entry. 3) Gli annunci a foto
SINGOLA scorrevano di lato trascinando la pagina: la striscia restava
scorrevole senza niente da scorrere e l'incatenamento arrivava alla
viewport (stessa causa del punto 1, sull'asse X). Vedi Architettura
per la distinzione fra i due contesti, che è la cosa da non
dimenticare: nella PWA non c'è niente da intercettare.
Verificato in locale nel contesto PWA (senza `initData`, col gesto
simulato come `history.back()` diretto): la catena piastrella →
dettaglio risale a categoria, Sfoglia, Esplora-intera in tre gesti; i
tab costano un indietro solo; la tirata in categoria annulla il gesto
nativo, fa una chiamata e non si muove; la galleria a una foto non
scorre e la pagina non sborda. E POI PROVATO DA ANDREA SUL TELEFONO,
nei DUE contesti: tirata, galleria, radice madre e chiusura funzionano
in entrambi, `tg.close()` compreso.
Restava un terzo caso, che si presentava UGUALE nei due contesti — ed
è il modo in cui si è capito che era contenuto e non contesto: due
annunci importati si trascinavano di lato col dito sul corpo della
scheda, per una parola lunga senza spazi che allargava il documento.
Vedi «il testo dell'utente non può allargare la pagina» nel dettaglio
annuncio, e in particolare il `min-width:0` sul figlio flex, che è la
metà del rimedio che non viene in mente.
La 27ª categoria e l'albero dormiente (ago 2026, due cantierini in un
giorno): «Buoni ed esperienze» accesa subito — la merce vera che
moriva in «Altro» (pacchetto B&B, buoni Zalando) ha una casa, coi
sette posti, i gemelli SENZA_CONDIZIONE e le righe-voucher del
modello CSV traslocate — e l'albero delle SOTTOCATEGORIE definito ma
mostrato mai: 86 sottovoci su 26 categorie (l'86esima, «Mare e
piscina», nata dal Telo d'Amare vero), disegnate sui 46 annunci
veri di produzione, colonna e payload silenzioso già vivi, UI zero
(vedi Architettura per il patto, le regole di confine e la decisione
su Elettronica, che resta col contenuto suo invece di chiudere).
Collaudato: 38 prove pure nuove/aggiornate in prove.py, 16 verifiche
TestClient su DB usa-e-getta (giudici in pubblica/modifica, conserva/
azzera, la 27ª senza condizione, la vetrina che non mostra la
colonna) più il filo del CSV. IN PRODUZIONE basta il deploy (la
migrazione della colonna gira da sola); dopo il deploy gli
spostamenti veri — B&B e Zalando verso la voce nuova (il casco moto
citato nei primi appunti era merce del db di COLLAUDO, non di
produzione) — si mettono in coda con `sposta_a_mano.py` sul VPS e si
approvano dalla coda admin, che aggiorna anche il NIP-99.
Il GIUDICE SILENZIOSO (ago 2026, il giorno dopo): la colonna si
riempie da sola a parole chiave dentro la categoria scelta — misurato
prima di accenderlo (45/46 in produzione, 12/15 fuori campione, zero
sbagliati: si astiene, non sbaglia), agganciato a pubblica/modifica/
CSV/dopo-import Nostr, con `assegna_sottocategorie.py` per la passata
sul pregresso e il termometro `--conta` che dice dove arricchire il
dizionario coi dati veri. Collaudato: 11 prove pure nuove (dizionario
allineato all'albero voce per voce + il giudice nei suoi casi), 6
verifiche TestClient dei ganci su DB usa-e-getta, e lo script nei tre
modi su una copia del db locale (300 assegnate, idempotente al terzo
giro). IN PRODUZIONE: deploy, poi `python assegna_sottocategorie.py`
sul VPS per l'anteprima e `--scrivi` per la passata una tantum.
L'ACCENSIONE dell'albero è un cantiere futuro, solo frontend + param.
L'asta 🔨 (ago 2026, cantiere in sette passi con revisione di Andrea
sui passi dei soldi): vendita al miglior offerente con escrow
incrementale — puntare è pagare, si versa solo la differenza, il
vincitore diventa un ordine già pagato e i perdenti riscuotono dal
binario degli incassi. Vedi Architettura per schema, motore, chiusura,
regola della lapide e strade scartate. Collaudata in locale su DB
usa-e-getta lungo tutti i passi (partita a tre offerenti con la corsa
risolta al saldo, proroga anti-cecchino, tardivi nel registro, ritiro
definitivo con la cintura del saldo postumo, chiusura idempotente con
l'invariante dei totali, fusione con collisione e lapide, giro visivo
della demo) e con 19 prove pure in prove.py (127 totali). IN
PRODUZIONE: il deploy da solo non cambia niente (migrazioni additive);
le aste si accendono SOLO scrivendo `ASTA_ABILITATA = True` nel config
del VPS e riavviando — da fare guardando il primo giro col journal
aperto, e il primo giro vero dentro Telegram (puntata, sorpasso,
chiusura, riscossione con wallet reale a cifre minuscole) è il
collaudo che manca. RESTA DA DECIDERE a rodaggio: se e quando dare
alle aste la radice «🔨 Aste» nello slot vuoto della nav.
Il disarmo dell'auto-sblocco (ago 2026, decisione di Andrea presa
guardando un ordine vero): i sats non si muovono più senza un gesto
umano — leva `AUTO_SBLOCCO_ATTIVO` che nasce False, i due rami fisici
dell'orologio spenti, e al loro posto il promemoria al compratore coi
suoi due bottoni, poi il 🧊 ai moderatori. Le finestre del digitale e
i timer che RESTITUISCONO (chiusura d'asta, rimborsi, riacciuffo)
restano armati, ed è la regola precisa: nessun timer sposta sats da
una parte a un'altra. Vedi Architettura per il censimento completo,
le eccezioni motivate e il piano di rientro. Collaudato con 22
sentinelle nuove in prove.py (188 totali, una per riga del censimento
— quelle che devono tacere e quelle che devono restare accese) più un
collaudo eseguibile su DB usa-e-getta, 40 verdi: fisico/asta/set che
non si sbloccano, i due digitali che si sbloccano ancora, la cadenza
fino al tetto e poi il silenzio, il caso normale in cui il compratore
conferma e il promemoria smette da solo, e la regressione a leva
accesa. IN PRODUZIONE basta il deploy (le due colonne nascono da
sole) — fatto, e verificato sul caso che ha aperto il cantiere:
l'ordine #28, a 6,44 giorni su 10, è rimasto `shipped` con zero
squilli invece di sbloccarsi tre giorni e mezzo dopo.
Il venditore che non fa partire la merce (ago 2026, il giorno dopo, dopo
una verifica indipendente del disarmo che ha confermato tutte e cinque
le righe del censimento): chiuso il buco 1 — un ordine `locked` non
aveva nessun timer e nessuna parola, e il compratore non sapeva di poter
aprire una disputa — e con lui il gemello digitale che non era nemmeno
dichiarato. `sollecita_venditori_fermi` è una FUNZIONE SORELLA di
`sollecita_conferme_ferme` e non una sua popolazione, perché il buco è
preesistente al disarmo e quindi non deve stare dietro
`AUTO_SBLOCCO_ATTIVO`: così il diff sul codice dei soldi è ZERO, solo
aggiunte. Vedi Architettura per le due finestre (5 giorni / 48 ore) coi
loro perché, per le colonne che dicono CHI aspettiamo, e soprattutto per
la trappola di `aggiornato` — che `deposita_invoice` scrive proprio su
`locked`, cioè il venditore avrebbe potuto rimandare il proprio
promemoria ri-salvando la sua invoice d'incasso. Collaudato con 9
sentinelle nuove in prove.py (197 verdi) e un collaudo eseguibile su DB
usa-e-getta, 27 verdi: le due finestre al giorno e all'ora giusti, la
trappola dell'invoice ri-salvata provata sul serio, il set col titolo
sintetizzato, la cadenza fino al 🧊 e poi il silenzio, il venditore che
spedisce e il contatore del compratore che riparte da zero, le strade
che non ci riguardano, e la regressione a leva riaccesa. IN PRODUZIONE
basta il deploy (le due colonne nascono da sole, le due leve hanno un
default nel codice): il primo giro da guardare è un ordine `locked` con
più di 5 giorni sulle spalle — al primo battito dell'orologio arriva UNO
squillo al venditore e UNO al compratore.

L'importo di ogni bolt11 in uscita si controlla contro il dovuto (ago
2026, C-1 dell'audit di sicurezza — la prima voce chiusa, e l'unica
critica). Nel LNURL-pay la fattura la scrive il wallet del
beneficiario: il `ln_address` è auto-dichiarato, quindi un dominio
proprio poteva rispondere con qualunque cifra e usciva quella scritta
dentro la bolt11. Il controllo esisteva già sul ramo dell'invoice
incollata a mano — mancava solo su quello automatico. Ora il giudice è
uno (`importo_invoice`) e la cintura sta su `paga_venditore`, con
`atteso_sats` obbligatorio senza default così ogni strada d'uscita
futura la eredita. Vedi Architettura per il perché per esteso. Provato
in due sensi: 212 prove verdi (erano 197), dove le sei della cintura
asseriscono che la POST verso l'admin key **non è mai partita** — non
che una funzione «torna False» — più cinque sentinelle anti-refactor;
e un collaudo end-to-end su DB usa-e-getta sui tre chiamanti con
eccesso/difetto/onesto, che tiene ferma anche la regressione (wallet
onesto = tutto come prima). La falla è stata riprodotta sul codice di
HEAD prima di toccarla: 1 sat dovuto, 100 milioni usciti. IN
PRODUZIONE basta il deploy: nessuna colonna, nessuna leva, nessuna
rotta, nessuna migrazione.
DA RICORDARE QUANDO SI DECIDERÀ LA COMMISSIONE CON ALAN, ed è qui e
non solo in Architettura perché è lì che ci si inciamperà: la cintura
è RETROATTIVA sulle invoice già depositate. Oggi con
COMMISSIONE_PERCENTO e PROTEZIONE_PERCENTO a 0 non cambia niente, ma
il giorno che la percentuale si accende una invoice depositata col
vecchio netto e pagata col nuovo non combacia più e viene rifiutata:
il venditore riceve l'avviso e ne incolla una nuova, i sats restano in
cassaforte, nessuno perde niente. È il comportamento corretto — non si
paga la cifra sbagliata — ma va guardata la coda degli ordini
`confirmed` con una invoice già depositata prima di girare la leva, o
si scambieranno dei rifiuti giusti per un guasto.
Il secondo giro dell'audit (ago 2026) ha chiuso le due voci ALTE
rimaste, più il buco della CI che le prove stesse non vedevano.
1) L'INITDATA SCADE (24 ore, leva `ORE_INITDATA`): la firma dice CHI,
non QUANDO, e uno catturato apriva quell'account per sempre — vedi
Architettura, sotto il login web, per il perché delle 24 ore e non
dei 5 minuti del widget. 2) `/foto` NON È PIÙ MONTATA: rotta
esplicita con la whitelist delle forme, e la regola ferrea 3 diventa
verificabile invece che raccomandata. 3) LA CI INSTALLA PILLOW, e una
prova saltata si conta invece di sparire. 4) `MODALITA_COLLAUDO` nasce
`False` in `config_esempio.py` (in produzione era già False,
verificato: cambia da dove si parte, non cosa gira). Provate: 253
verdi (erano 212), il buco dell'initData riprodotto sul codice di
prima, il giro degli header fatto su un server vero — foto 200 e 304,
illustrazioni invariate, 404 a `..%2Fconfig.py`, `%00` e `%0A`. In
produzione basta il deploy: nessuna colonna, nessuna migrazione.
DA GUARDARE al primo deploy: il cartello «Sessione scaduta» dentro
Telegram vero — in locale si è verificato che il banner si disegna e
sta su una riga, ma il ramo che lo accende ha bisogno di un initData
vero, che solo Telegram conia.
Il terzo giro (ago 2026) ha chiuso le sette voci MEDIE, e la lista
dell'audit adesso è vuota. In ordine di gravità: 1) il timeout di
`paga_venditore`, che poteva far uscire i sats DUE volte — il caso
riprodotto sul codice di prima: due giri, due fatture diverse, due
richieste di pagamento per lo stesso ordine; 2) la disputa che
usciva dalla coda dei moderatori quando il pagamento falliva;
3) l'IDOR su `verifica-pagamento`, che era un oracolo sullo stato di
ogni ordine del mercatino; 4) lo scanner della CI cieco sulla
cronologia e su tre forme di segreto; 5) Fernet senza KDF e col
fail-open muto; 6) il guardiano anti-SSRF aggirabile con un `302`, e
l'import Nostr senza guardie affatto; 7) nessun freno su
`/api/search`. Più i timeout espliciti sui due tubi LNbits in
entrata. Tutte in Architettura, alle voci loro.
Provate: 320 verdi (erano 253), e i tre difetti dei soldi riprodotti
sul codice di prima prima di ripararli. Le prove nuove asseriscono
il NON FATTO: nessun secondo pagamento, nessuna fattura nuova
coniata, nessuno stato riscritto, zero domande a LNbits per conto
d'altri.
IN PRODUZIONE il deploy fa girare tre migrazioni additive
(`payout_stato`, `payout_hash`, `payout_verso` su `ordini` e su
`rimborsi_asta`) e niente altro. `TETTO_RICERCHE_AI_ORA` ha un
default nel codice; se in rodaggio 30 ricerche l'ora stanno strette
a qualcuno, è una riga nel config. DA GUARDARE al primo deploy: la
riga d'avvio sui contenuti digitali — se dice che si scrivono IN
CHIARO, sul VPS `CHIAVE_CONTENUTI_DIGITALI` è vuota.
IMPERFEZIONI DICHIARATE che restano: il DNS-rebinding fra controllo
e download (era già accettato), i commit di MERGE fuori dalla
scansione della cronologia, e il fatto che uno sconosciuto possa
ancora far bussare il nostro LNbits chiedendo la verifica dei PROPRI
ordini.

Giro di interfaccia (ago 2026, undici punti dal campo e dal feedback di
Andrea). La ✕ della pagina del pacco svuota davvero, con la conferma
davanti — il gesto indietro no, e il perché sta nella voce sua: nella
PWA è di sistema e non si può intercettare. IL TRACCIAMENTO su tre
gambe (prevenzione, forma euristica che non blocca mai, correzione solo
da moderatore con traccia visibile a tutt'e due le parti), col buco
trovato provandolo dal vivo: il moderatore non poteva nemmeno APRIRE un
ordine spedito fra estranei, e senza il parametro `ordine` il pannello
sarebbe rimasto irraggiungibile. Colori coerenti in vetrina (lampo
rossa anche nella cornice e nel prezzo, asta petrolio). Tetto del
barattolo da 20 a 10 ed è una LEVA; conteggio pubblico e anonimo dei
salvataggi accanto all'icona (da 2 in su, dichiarato); il barattolino
scende in basso a destra sulla foto, il liquido sale arancio invece di
rovesciare lo sfondo, e il bottone grande sotto Acquista è sparito.
«Altri oggetti» da striscia a griglia col bottone sticky. Il 🔨 in nav
c'è sempre e a leva spenta dice che le aste stanno arrivando (con la
leva nella busta di prima pagina, che chiude l'imperfezione degli
anonimi). Il logo torna al mercatino. E la forma di «Acquista» è la
forma di TUTTI: era una deroga scritta a mano in quattro punti con due
valori diversi, ora è la base con un token solo — vedi la voce per
l'elenco di cosa è passato al rettangolo e di cosa resta tondo di
proposito. Collaudato: 389 prove verdi (erano 320, con le tre famiglie
nuove — la correzione del tracciamento, il barattolo su tre tetti
diversi, le forme dei codici sui casi veri) più il giro visivo via CDP
a 375 e 1280px nei due temi, zero errori JS, e la catena del pacco
esercitata dal vivo (conferma, indietro che NON svuota, svuota che
azzera davvero). IN PRODUZIONE il deploy fa girare due migrazioni
additive (`tracking_corretto_il`, `tracking_reso_corretto_il`) e crea
`idx_preferiti_annuncio`; nient'altro. ATTENZIONE al tetto del
barattolo: il default 10 vive nel CODICE, e una riga `MAX_PREFERITI`
esplicita nel config del VPS vincerebbe su di lui — si verifica prima
del deploy (vedi Produzione).

La pagina d'acquisto (ago 2026, il cantiere annunciato qui sotto come
«prossimo», ora FATTO): il foglio del varco è morto e Acquista porta
sempre a `view-acquisto` — articoli, le vie col solo costo di
spedizione per pillola (ritiro / casa / punto di ritiro / codice
online; il totale lo dice il conto), il campo del punto col
varco-mappa, il conto DEL SERVER prima della invoice; il venditore
dichiara DUE costi di spedizione e lo spedizioniere del negozio, il
compratore scrive il punto che il venditore ritrova nell'ordine. Le
decisioni di Andrea: costo unico come fallback su entrambe le strade,
la via punto SEMPRE offerta (dal secondo giro: senza spedizioniere
dichiarato vale l'accordo in chat, detto in pagina — supera il gate
del primo giro), e il conto di «Controlla il
pacco» dallo stesso preventivo (mai due conti che divergono, anteprima
sulla più economica dichiarandolo). Vedi Architettura, «LA PAGINA
D'ACQUISTO», per il modello dati (punto in colonna, MAI un valore
nuovo di consegna_scelta; il flag della tariffa; le quattro pure del
conto) e i perché. Collaudato: 450 prove verdi in CI (61 nuove, con le
sentinelle sul preventivo-che-non-crea e sul patto del ricontrollo
senza await), 50 verifiche TestClient su DB usa-e-getta — LA PROVA
REGINA: preventivo == compra a parità di via, al sat, mono e set — coi
caratteri strani nel punto lungo tutta la filiera, e il giro visivo
CDP chiaro/scuro a 375/1280 con zero errori JS (che ha anche trovato
dal vivo il 409 dello stock con la sua pagina d'errore, e l'edit di
setValuta finito su rinfrescaViste). Col SECONDO GIRO (feedback di
Andrea sul primo): il bottone finale dice «Paga», le pillole della
consegna il solo costo di spedizione, e la via punto si offre SEMPRE
(la decisione che supera il gate del primo giro). Col TERZO GIRO il
punto si fissava quando il corriere era noto: con la rete dichiarata
si scriveva al pagamento, senza si sceglieva la sola strada e il
punto arrivava dal campo dentro l'ordine (`via_punto`,
`POST /api/orders/{id}/punto-ritiro`, spedito bloccato finché manca
— dove spedirebbe?). E col QUARTO GIRO (ago 2026) la scelta del punto
è tornata SEMPRE prima di «Paga», come su Subito e Vinted: il campo
c'è anche senza rete — due mappe e la riga onesta — la regola vive
nel client (il 400 del server resta sul solo ramo con rete,
tolleranza per il client di ieri), il campo dell'ordine è diventato
la rete di sicurezza della correzione e il gate di segna_spedito
resta per il residuo; vedi Architettura, «E LA SCELTA DEL PUNTO
TORNA SEMPRE PRIMA DI "PAGA"», coi perché di tutti e due i giri.
Collaudato il quarto giro dal vivo sul server locale: campo e mappe
nei due casi, guardia a punto vuoto (zero POST), ordine nato col
punto scritto anche senza rete, 1443 prove verdi (4 nuove, 1
rovesciata). IN PRODUZIONE il deploy fa girare le migrazioni
additive (tre colonne punto su annunci, punto_ritiro + via_punto su
ordini, spedizioniere + avvisato_spedizioniere su utenti) e al primo
battito dell'orologio parte la notifica UNA-TANTUM ai venditori che
spediscono senza spedizioniere — col timbro, mai due volte. DA
GUARDARE dal vivo dentro Telegram: il giro completo su un telefono
vero (pagina, punto, paySheet sopra la pagina), il primo ordine al
punto visto dal venditore — nei due flussi, rete e non — e il testo
della campagna nel journal del primo giro.
Il negozio in ferie 🌴 (ago 2026): il venditore che parte chiude la
bottega con la data di rientro, e gli annunci RESTANO in vetrina col
prezzo in grigio — si guardano, non si comprano. Le decisioni di
Andrea: cosa BLOCCA la chiusura (locked non spediti, aste vive,
accordi già stretti, pagamenti in viaggio, lampo in corso — gli
ordini già spediti no), le offerte pendenti che DECADONO col 🕊, il
rientro AUTOMATICO alla data col promemoria il giorno prima, e su
Nostr NIENTE. Il modello è una colonna sola col gate in LETTURA, lo
stesso patto di lampo e asta: il negozio riapre da solo, senza
orologio. Vedi Architettura per le cinque cose che trattengono coi
loro perché, per il LEFT JOIN dei set (la lezione alla terza volta) e
per le due strade scartate sul badge in card, misurate in pixel.
Collaudato: 47 prove nuove in `prove.py` (640 verdi, erano 593) — fra
cui gli impegni uno per uno su sqlite in memoria, il caso SET con
`annuncio_id=0`, e le sentinelle che la guardia stia PRIMA della
invoice in tutti e dieci i varchi — più un collaudo TestClient su DB
usa-e-getta (31 verdi) che verifica le due cose che contano davvero:
che a negozio chiuso non nasca NESSUNA invoice, e che il rientro sia
IMMEDIATO senza che la scopa sia mai girata. Più il giro visivo via
CDP a 320/360/750px nei due temi (badge che non tocca il barattolino,
prezzo grigio misurato contro la carta, cassetto e elenco degli
impegni che va a capo). IN PRODUZIONE basta il deploy: le due colonne
(`ferie_fino`, `ferie_avvisato`) nascono da sole e le tre leve hanno
il default nel codice — `FERIE_ATTIVE` è ACCESA, che qui non esce
niente verso nessuno. DA GUARDARE al primo giro: il journal del
promemoria di rientro, e il primo venditore vero che chiude (che
l'elenco degli impegni gli dica cose sensate).
Lo sconto carrello 🎁 (ago 2026): il venditore premia chi compra più
cose in un ordine solo — UNA regola per negozio, «da N articoli −X%»,
sul SOLO prezzo degli articoli e mai sulla spedizione. Le quattro
decisioni di Andrea: il MONO non sconta mai (e c'è anche la ragione
tecnica — la divisione a ritroso di `_righe_ordine` si romperebbe in
silenzio), si CUMULA con lampo e accordo, si dice in pubblico in due
posti soli (negozio e «Altri oggetti»), la soglia conta i PEZZI. Il
modello è la voce di TESTATA che questo file dichiarava già preparata:
`ordine_righe` resta intatta e gli unitari LORDI. Vedi Architettura,
«LO SCONTO CARRELLO», per il perché di ognuna, per la colonna
TESTIMONE (che è la riga da leggere prima di toccare una strada del
denaro) e per la clausola dell'euro nativo, che è l'unico punto dove
la modifica poteva produrre una cifra precisa e falsa.
Collaudato: 99 prove nuove in `prove.py` (738 verdi, erano 640) — le
pure del conto una per una (soglia esatta e soglia−1, arrotondamenti
col resto a chi paga, i limiti, l'invariante, la cascata col FONDO
detto ad alta voce) più 38 sentinelle di forma, fra cui quelle che
tengono lo sconto fuori dal mono, fuori dal payload del compratore e
fuori da ogni strada del denaro in uscita. Più un collaudo TestClient
su DB usa-e-getta (71 verdi) con in testa LA PROVA REGINA aggiornata:
preventivo == compra al sat su quattro combinazioni, e `prezzo_sats`
== l'importo della bolt11 CONIATA — il confronto che lega il libro
mastro al denaro vero — con l'identità di bilancio riletta dal
database a ogni ordine; e i casi chiesti da Andrea: sconto cambiato
fra preventivo e acquisto (nei due versi), cambiato a invoice viva
(il prezzo non si ricalcola), il mono a ×5 che non sconta, il netto
del venditore sul totale scontato, l'euro nativo che resta ESATTO, e
la leva spenta che non lascia niente in piedi. Più il giro visivo via
CDP a 320/375/750px nei due temi: il conto che quadra a mano nelle due
valute, l'invito che conta e si trasforma alla soglia, il paySheet che
dice la stessa cifra della pagina, la scheda ordine che torna, e il
cassetto avanti e indietro (dove il giro dal vivo ha trovato un bug
vero: la bozza si fissava prima che la regola arrivasse). IN
PRODUZIONE basta il deploy — le quattro colonne nascono a 0, cioè
regola spenta per tutti, e le leve hanno il default nel codice
(`SCONTO_PACCO_ATTIVO` è ACCESA: qui non esce niente verso nessuno).
DA GUARDARE al primo giro: il controllo del libro mastro in SQL (le
query sono pronte, le lancia Andrea), il primo acquisto scontato vero
dentro Telegram con la bolt11 su LNbits, e il primo payout di un
ordine scontato — se `paga_venditore` avvisa i moderatori, ci si ferma.
La ronda del libro mastro (ago 2026, il giorno dopo): le query che
sorvegliano gli invarianti non si lanciano più a mano — le gira
l'orologio una volta al giorno. 15 controlli, tutti già dichiarati in
questo file: l'aritmetica degli ordini col suo sconto, la forma di
`ordine_righe`, la cassa delle aste chiuse, le cinture d'idempotenza
dei rimborsi, l'annuncio a due teste. A libro mastro sano TACE — un
«tutto bene» quotidiano è rumore; quando qualcosa non torna manda il
🧊 coi nomi e gli id, una volta al giorno finché il problema esiste.
LEGGE E BASTA: nessuna correzione automatica. Vedi Architettura, «LA
RONDA DEL LIBRO MASTRO», soprattutto per quali invarianti sono stati
lasciati FUORI e perché (hanno stati transitori legittimi: suonerebbero
su casi normali, che è il modo in cui si impara a ignorare un allarme).
Collaudato: 164 prove nuove in `prove.py` (902 verdi, erano 738) — le
query girano DAVVERO su un database gemello in memoria, prima sano
(nessuno deve fiatare) e poi con una riga rotta piantata per OGNI
controllo, che deve trovarla col suo id: una query di controllo
sbagliata non fallisce, TACE, ed è il peggior modo di fallire. Più 15
verifiche dal vivo sul giro completo (silenzio a db sano, l'avviso
all'id giusto, il gate che non ripete a ogni battito ma ribussa il
giorno dopo, la riga rotta ancora rotta dopo la ronda, la leva che
spegne) e le 15 query lanciate in sola lettura sul database vero.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione, e
la leva ha il default nel codice. DA GUARDARE al primo giro: che nel
journal non compaia NIENTE — se arriva un 🧊 il primo giorno, quello è
il momento di guardare, non di sistemare la ronda.
Il criterio dello sconto carrello (ago 2026, il giorno dopo, da un
venditore vero): «se vendo un computer lo sconto lo do già da 2 pezzi,
se vendo cianfrusaglie ne servono tante». Lui chiedeva una soglia per
PRODOTTO — scartata, non sarebbe spiegabile su un carrello misto e
romperebbe la divisione a ritroso dell'unitario. La soglia resta UNA
per negozio e a cambiare è il CRITERIO: a pezzi come sempre, o a
VALORE degli articoli. Le decisioni di Andrea: la soglia a valore è in
SATS (l'euro è un aiuto per SCEGLIERE nel cassetto, mai l'unità della
soglia), colonne separate perché `sconto_pacco_soglia` non cambi mai
significato, e il valore si confronta col LORDO — cioè col carrello
DOPO lampo e accordo, quindi una lampo generosa può far scendere sotto
soglia un carrello che a listino ci arrivava: è voluto, ha la sua
prova e il cassetto lo dice al venditore. Vedi Architettura, «IL
CRITERIO LO SCEGLIE IL VENDITORE», per il perché dei sats e per la
regola d'oro della retrocompatibilità (`_sconto_pubblico`: la soglia
in pezzi esce >0 solo a criterio pezzi, ed è il lucchetto del client
vecchio in cache).
Collaudato: 118 prove nuove in `prove.py` (1020 verdi, erano 902) —
fra cui gli shim che fanno girare IDENTICHE le ~35 asserzioni di ieri
(la regressione dei negozi esistenti, gratis), il caso misto nei due
versi, la lampo che spegne lo sconto, il criterio ignoto che NON
ripiega sui pezzi, e le prime prove funzionali di `_regola_sconto`,
che la sua docstring prometteva dal giorno in cui è nata e non aveva
mai avuto. Più un collaudo eseguibile su DB usa-e-getta (58 verdi) con
in testa LA PROVA REGINA aggiornata — preventivo == compra AL SAT su
entrambi i criteri e al filo della soglia — l'identità di bilancio
riletta dal database, le due soglie che si conservano a vicenda anche
da un client vecchio, e la ronda che tace. Più il giro visivo via CDP
a 320 e 375px nei due temi, che ha trovato dal vivo l'unico difetto
del cantiere: sulla pillola accesa l'≈€ spariva, perché era una
`.unit`. IN PRODUZIONE basta il deploy — le due colonne nascono col
loro default (`'pezzi'`, 0), cioè tutti i negozi che scontano oggi
continuano identici, e le tre leve nuove hanno il default nel codice.
DA GUARDARE al primo giro: il primo venditore che passa a valore (che
il cassetto e la riga pubblica dicano la stessa cifra) e il polso SQL
17, che adesso dice anche il criterio.
La spedizione gratis sopra soglia (ago 2026, il giorno dopo, richiesta
dal campo): «da N sats di articoli la spedizione la offro io», la
seconda promessa di negozio. La cosa da sapere prima di tutte è che
VALE ANCHE SULL'ACQUISTO SINGOLO, e non per scelta ma per FORMA:
azzerare una tariffa scrive `spedizione_sats=0` — lo stato che ogni
annuncio con tariffa gratis dichiarata ha da sempre — mentre lo sconto
sottrae dal totale e romperebbe la divisione a ritroso dell'unitario,
che è il motivo per cui il mono non sconta. Le decisioni di Andrea: la
soglia in sats, le due promesse che guardano lo STESSO numero (l'
articolo lordo) e quindi non possono spegnersi a vicenda, la riga
pubblica in TRE posti — negozio, «Altri oggetti» e la scheda
dell'annuncio, che lo sconto non ha —, la colonna testimone
`ordini.sped_gratis_sats`, e la decisione TARDI sul cambio con la sua
imperfezione dichiarata. Più le due righe nel form Vendi, ognuna
attaccata al campo di cui parla (unirle è stato valutato e scartato:
il perché sta in Architettura, ed è la parte che vale). Vedi
Architettura, «LA SPEDIZIONE GRATIS SOPRA SOGLIA».
Collaudata: 100 prove nuove in `prove.py` (1120 verdi, erano 1020) —
le pure al filo della soglia, i quattro quadranti dell'indipendenza
col caso che smaschera una dipendenza (netto sotto soglia, lordo
sopra), la lampo che fa scendere sotto, e le sentinelle che tengono la
tariffa offerta fuori da ogni strada d'uscita del denaro e la
decisione nello stesso punto nei quattro percorsi. Più un collaudo
eseguibile su DB usa-e-getta (80 verdi) con in testa LA PROVA REGINA:
preventivo == compra AL SAT su mono e set, sopra e sotto soglia, in
sats e in EUR, e `prezzo_sats` == l'importo della bolt11 CONIATA — più
l'euro nativo che resta esatto, la soglia cambiata fra preventivo e
acquisto nei due versi, la leva spenta che spegne tutte le vetrine
insieme, e la ronda che tace. Più il giro visivo via CDP a 375px nei
due temi e nelle due valute, zero errori JS, che ha trovato dal vivo
tre cose: «gratuita» che usciva in monospazio (contro la regola di
casa per quella parola), il titolo del cassetto che andava a capo, e
la punteggiatura della riga dello sconto nel form. IN PRODUZIONE basta
il deploy — le due colonne nascono a 0, cioè promessa spenta per
tutti, e le tre leve hanno il default nel codice
(`SPED_GRATIS_ATTIVO` è ACCESA: non esce niente verso nessuno). DA
GUARDARE al primo giro: il primo venditore che l'accende, e il primo
ordine con spedizione offerta vero dentro Telegram con la bolt11 su
LNbits — se `paga_venditore` avvisa i moderatori, ci si ferma.
I suggerimenti dal bot diventano attivi di serie, ma col RITMO (ago
2026, decisione di Andrea): «💡 Suggerimenti sui miei annunci» nasce
acceso — l'opt-in non lo accendeva quasi nessuno — e a tenerli gentili
è il tetto di uno ogni 7 giorni per PERSONA, qualunque sia la coda
(prima era per annuncio, e chi ne pubblicava cinque in un pomeriggio
ne riceveva cinque). Il perché è la parte da non ammorbidire: chi si
stufa BLOCCA IL BOT, e col bot bloccato non riceve più le notifiche
degli ordini, che sono portanti; su Nostr il danno è identico e meno
visibile, perché smette di leggere i DM. Più due suggerimenti nuovi —
lo sconto carrello e la spedizione gratis a chi non li ha accesi —
una volta sola per funzione e mai insieme, che è una proprietà del
timbro del ritmo e non una regola scritta.
COME SI DISTINGUE «mai toccato» da «spento da lui» (la domanda di
Andrea): una colonna del GESTO, `utenti.suggerimenti_scelti`, e non un
terzo stato dentro il valore — con «2 = spento» il primo `if` scritto
distrattamente leggerebbe 2 come acceso, cioè fallirebbe nel verso di
scrivere a chi ha detto no. Del PREGRESSO però il gesto NON ESISTE, e
si dichiara: l'endpoint di ieri scriveva solo il valore, quindi chi è
a 0 può essere chi non l'ha mai guardato o chi l'ha spento. La
migrazione fa l'unica cosa dimostrabile (chi è acceso l'ha acceso lui)
e per gli altri sceglie «mai toccato»; il prezzo è UN messaggio a chi
l'aveva spento, con dentro il modo di rispegnerlo. Vedi Architettura,
«I SUGGERIMENTI SUGLI ANNUNCI».
Collaudati: 37 prove nuove in `prove.py` (1162 verdi, erano 1125) — i
quattro casi del giudice per entrambi i default, la prova che
rovesciare il default non tocca chi ha scelto, il ritmo su un database
di cartone (al sesto giorno chiuso, al settimo esatto riapre), la
whitelist dei timbri che rifiuta un nome fuori catalogo, e le
sentinelle sul timbro-prima-dell'invio e sul gate prima di
`completamento_avvisato`. Più un collaudo eseguibile su DB usa-e-getta
(28 verdi) che gira le funzioni VERE dell'orologio: la migrazione e la
sua idempotenza, chi riceve e chi no, un solo messaggio per giro, il
secondo che arriva solo dopo N giorni ed è l'ALTRA funzione, «una
volta per funzione per sempre», il bersaglio (un annuncio solo →
niente sconto; solo ritiro → niente spedizione gratis), le due leve
nei due stati, e `/api/me` che dice lo stato effettivo. Più il giro
visivo sul cassetto «🔔 Avvisi» nei due temi. IN PRODUZIONE il deploy
fa girare le quattro colonne nuove e la migrazione dei gesti (che
stampa quanti utenti ha registrato); le due leve hanno il default nel
codice. DA GUARDARE al primo giro: il journal della prima passata di
`suggerisci_funzioni` — quanti ne partono — e che nessuno riceva due
messaggi.
Le due soglie a valore passano all'EURO (ago 2026, cambio di rotta
deciso da Andrea il giorno dopo averle fatte in sats): una soglia in
sats DERIVA COL CAMBIO — chi scrive 100.000 pensando «una cinquantina
di euro» si ritrova, sei mesi dopo, una promessa del doppio senza aver
toccato niente. Vale per TUTTE E DUE le promesse, o avremmo due promesse
identiche in due valute diverse. Non cambia niente di sostanziale: si
paga sempre in sats, l'escrow è in sats, il conto è del server, e
`ordini` non si tocca di una riga.
Le tre cose da sapere. 1) LE PURE RESTANO PURE: guadagnano un
argomento (`articolo_eur`), non una chiamata — nasce `_eur_interi`,
che si invoca UNA volta per conto e serve tutte e due le promesse,
così «guardano lo stesso numero» diventa una proprietà della
struttura invece di un patto da ricordare. 2) A CAMBIO MUTO la
promessa NON scatta e lo si dice (fail-closed dentro il giudice,
`promesse_sospese` nel preventivo, riga onesta in pagina), MAI un 503
nuovo: senza cambio un listino in euro non si sa convertire e
l'ordine non nasce, una promessa non si sa solo valutare. E «muto»
vuol dire pochissimo — `cambio_btc_eur` è fail-open e tiene l'ultimo
valore noto, quindi lo 0 esce solo dopo un riavvio dentro
un'interruzione. 3) COLONNE E LEVE NUOVE col suffisso, le vecchie
inerti: una riga `SPED_GRATIS_SOGLIE = (50_000, …)` già scritta in un
config verrebbe letta come euro e spegnerebbe la promessa in silenzio.
Vedi Architettura, «LA SOGLIA A VALORE È IN EURO».
Collaudato: 1198 prove verdi in `prove.py` (erano 1162) — fra cui il
filo esatto nelle due unità, il floor che decide, il cambio muto sui
due giudici, il criterio a PEZZI che a cambio muto scatta lo stesso, e
le sentinelle nuove sulla purezza di `_eur_interi`, sui due 503 che
restano due, e su `cambio_ordine` che non si sporca con la misura. Più
un collaudo eseguibile su DB usa-e-getta (57 verdi) con in testa LA
PROVA REGINA aggiornata — preventivo == compra AL SAT su set e mono,
sotto/al filo/sopra soglia, in sats e in EUR, **e a cambio muto** — col
confronto fra `prezzo_sats` e l'importo della bolt11 coniata, e la
ronda del libro mastro che tace. Più il giro visivo via CDP a 375px nei
due temi (cassetti, tre righe pubbliche, invito del carrello nei suoi
quattro casi compreso il floor a 49 €), zero errori JS. Due difetti
trovati e chiusi strada facendo, tutti e due nelle PROVE e non nel
codice: una sentinella che non poteva fallire, e una finestra a
lunghezza fissa che aveva smesso di provare quel che diceva.
IN PRODUZIONE: il deploy fa nascere le due colonne `*_eur` a zero,
cioè **promesse spente per chi le aveva a valore** — ed è il momento
da guardare. Il rimedio è una riga: `python converti_soglie_euro.py`
in anteprima e poi `--scrivi`. Se non l'ha impostata nessuno (molto
probabile: le due funzioni sono nate ieri) stampa «nessuno» e si
chiude; a ricordarlo c'è la riga d'avvio e il polso SQL 17d. ⚠️ Se il
config del VPS ha righe esplicite `SCONTO_PACCO_VALORI`,
`SCONTO_PACCO_MIN_VALORE`, `SPED_GRATIS_SOGLIE` o `SPED_GRATIS_MIN`,
diventano INERTI: vanno riscritte coi nomi `*_EUR` e con cifre in
euro, o valgono i default del codice (10·25·50·100 €).
DA GUARDARE al primo giro: il primo venditore che rimette la soglia in
euro, e il primo ordine scontato vero con la bolt11 su LNbits.

...e due giorni dopo LA VALUTA TORNA AL VENDITORE (ago 2026, chiesto
dalla comunità): la soglia a valore si dichiara in EURO o in SATS, con
un toggle nel cassetto, e ogni promessa ha la SUA valuta. Non è un
ritorno indietro — si AGGIUNGE la scelta, e accanto al toggle si dice
cosa comporta in tutte e due le direzioni invece di deciderlo al posto
del venditore. Il perché di venerdì (la deriva col cambio) resta vero e
diventa l'avvertimento; il perché che lo supera è che quel difetto ce
l'ha già il prezzo di ogni annuncio in sats, e la valuta in cui uno
ragiona è una scelta sua. IL GUADAGNO che l'euro non poteva dare: in
sats la promessa NON HA BISOGNO DEL CAMBIO — scatta a CoinGecko muto,
l'invito del carrello smette di convertire (era l'unica conversione che
il client fa su una promessa) e un negozio tutto-sats non paga più un
giro di rete. Vedi Architettura, «LA VALUTA DELLA SOGLIA A VALORE LA
SCEGLIE IL VENDITORE», per il modello (le colonne in sats che tornano
vive col significato di sempre, il `DEFAULT 'eur'` che È la migrazione),
per il toggle che CONSERVA e non converte, e per la LEZIONE
STRUTTURALE — «soglia euro a zero» ha smesso di voler dire «promessa
spenta», e tre posti lo codificavano.
E UN DIFETTO PREESISTENTE CHIUSO QUI, dalla domanda di Andrea «cosa
succede in pratica a un venditore col client in cache che tocca
Salva?»: le risposte erano due e tutte e due cattive — sullo sconto un
400 col messaggio SBAGLIATO, sulla spedizione gratis uno SPEGNIMENTO
SILENZIOSO (la chiave assente valeva 0, che lì è lo spegnimento).
Adesso la chiave del valore nell'unità dichiarata dev'essere PRESENTE:
assente = 400 che dice di riaprire l'app, mai un salvataggio muto.
Collaudato: 2393 prove verdi in `prove.py` (erano 2220) — le due pure
sui quattro quadranti valuta × cambio muto, i due lettori con la loro
leva, la regola d'oro torturata su tutte le combinazioni, e una
famiglia NUOVA di prove ESEGUIBILI sui due endpoint (sqlite in memoria)
che asserisce il NON FATTO: body vecchio → 400 **e la colonna riletta
dal database ancora quella di prima**, su tutti e tre i casi, con le
due regressioni dello spegnimento esplicito. Più **DICIASSETTE
MUTAZIONI**, una riga alla volta, ognuna rossa da sola — e sono state
loro a trovare tre difetti veri nelle sentinelle: due fette di sorgente
troppo larghe (una guardia tolta al set passava perché quella del
preventivo era ancora nella stessa fetta) e una prova mancante sul
COALESCE dello sconto, che il client di casa nascondeva mandando sempre
tutte le chiavi. Più la migrazione provata su una COPIA del database
locale (24 righe, tutte a 'eur', promesse identiche prima e dopo) e il
giro dal vivo sul server locale: cassetto col toggle avanti e indietro
che ritrova i 50.000 sats scritti prima di venerdì (non una
conversione), salvataggio in sats end-to-end, le tre righe pubbliche e
la pagina Paga che dicono «sats», zero errori JS — e lì è saltato fuori
l'ultimo difetto, una frase sgrammaticata nella riga del form Vendi.
IN PRODUZIONE basta il deploy: le due colonne nascono con `DEFAULT
'eur'`, cioè **nessuna promessa cambia di un centesimo**, e le quattro
leve nuove (`VALUTE_SOGLIA`, `SCONTO_PACCO_VALORI_SATS`,
`SCONTO_PACCO_MIN_VALORE_SATS`, `SPED_GRATIS_SOGLIE_SATS`,
`SPED_GRATIS_MIN_SATS`) hanno il default nel codice. `converti_soglie_
euro.py` e il suo avviso d'avvio RESTANO e sono ancora giusti — lo
stato che descrivono esiste ancora — ma adesso quel negozio ha un
secondo rimedio: passare la sua soglia a sats, e ritrova il numero che
aveva scritto. DA GUARDARE al primo giro: il primo venditore che sceglie
i sats, e che il libro mastro continui a tacere.

Il supplemento di spedizione per pezzo (ago 2026, caso dal campo: il
riso da 4 kg venduto a sacchi con la spedizione di UNO dichiarata —
chi ne comprava dieci pagava la spedizione di uno). Un campo
facoltativo accanto al costo base, «ogni pezzo in più: +N», PER
ANNUNCIO e non per negozio: il supplemento dipende dall'oggetto, un
sacco di riso non è una collanina. La regola sta in una riga — la
spedizione più cara fa da base, e ogni altro pezzo aggiunge il suo
supplemento — e il mono con quantità ne è un caso particolare, non un
ramo. Le decisioni di Andrea: un supplemento SOLO (vale casa e punto),
la colonna nel CSV, e il fix del bug preesistente qui sotto nel suo
commit. Vedi Architettura, «IL SUPPLEMENTO PER PEZZO», per il MAX che
non è il minimo, l'euro nativo e la ragione per cui qui la divisione a
ritroso dell'unitario regge mentre lo sconto sul mono no.
DUE BUCHI TROVATI mentre si costruiva, tutti e due nel codice di ieri:
`preventivo_ordine` passava a `_strade_preventivo` l'annuncio SENZA la
quantità (col supplemento il preventivo mono avrebbe detto la
spedizione di un pezzo e la invoice quella di dieci — la prima
divergenza preventivo↔compra), e il `None` di una tariffa ancorata col
cambio muto sarebbe diventato un 500 (`max(sped, None)`) invece di un
503. Più la bugia chiusa in vetrina: con base 0 e supplemento, la card
avrebbe scritto «🚚 gratis» e la pagina Paga avrebbe chiesto 27.000
sats per dieci pezzi.
Collaudato: 1296 prove verdi in `prove.py` (erano 1267 — 31 pure sulla
formula, fra cui il fuzz a seme fisso sulle due proprietà strutturali,
il pareggio nelle due permutazioni e l'arrotondamento che si smaschera
solo a cambio non tondo, più le sentinelle di forma, quattro delle
quali torturate rompendole a una a una), e un collaudo eseguibile su
DB usa-e-getta (59 verdi) con in testa LA PROVA REGINA — preventivo ==
compra AL SAT su mono 1/10 pezzi, listino sats e EUR, via casa e
punto, carrello a quantità diverse, spedizione offerta — col confronto
fra `prezzo_sats` e l'importo della bolt11 CONIATA, la divisione a
ritroso verificata anche sul ramo della ripresa, il 503 che resta un
503, e la ronda del libro mastro che tace. Più il giro visivo via CDP
a 375px nei due temi.
IN PRODUZIONE basta il deploy: le due colonne nascono a 0, cioè
supplemento spento per tutti — nessuna migrazione, nessun ordine
esistente cambia di un sat. DA GUARDARE al primo giro: il primo
venditore che lo scrive, e il primo ordine con q≥2 e supplemento vero
dentro Telegram, con la bolt11 confrontata su LNbits.

La promessa della spedizione gratis si leggeva sulla cifra, non sulla
strada (ago 2026, commit suo, trovato col cantiere qui sopra): su un
listino in SATS con la tariffa ancorata all'EURO i sats in colonna
sono 0, quindi il gate `if sped:` non leggeva nemmeno la soglia del
venditore e la spedizione si pagava — mentre `preventivo_ordine` la
legge senza quel gate e la pagina Paga scriveva «gratuita».
Riprodotto su DB usa-e-getta prima di toccare: preventivo 100.000,
invoice 105.000. Ora la guardia è la STRADA. Va nel verso di chi
compra: dopo il deploy quelle spedizioni diventano gratis davvero.

L'import non adotta più gli annunci nati qui (ago 2026): un evento che
abbiamo composto noi e fatto firmare al venditore — il BIVIO — è il
RIFLESSO di una riga locale, non una sua fonte, e l'import lo salta.
Senza il tappo il match per TITOLO gli scriveva addosso
`contatto_nostr`: da lì niente più modifica dal form (e chi ha solo il
badge 🟣 restava senza nessuna strada, che `modifica-firmata` esige
`npub_accesso`), la descrizione si prendeva il footer promozionale, e
una sua NIP-09 da un client qualunque spegneva l'annuncio su Barattolo.
Vedi Architettura, «IL RIFLESSO NON È UNA FONTE», per le tre condizioni
del riconoscimento, la perdita dichiarata (una modifica fatta da un
altro client non arriva più) e la strada scartata del kind 5.
Riprodotto su DB usa-e-getta prima di toccare — adozione, NIP-09 che
spegne, footer nella descrizione e foto riscaricate da noi stessi —
poi verificato che la correzione chiuda tutti e quattro senza spegnere
l'import vero (un annuncio davvero importato entra e si aggiorna come
sempre). 1314 prove verdi, di cui 15 nuove: i due giudici puri sui loro
casi e due sentinelle di forma, TORTURATE con cinque mutazioni del
codice — chiamata tolta, filtro spostato dopo il vaglio, ognuna delle
tre condizioni rotta — e ognuna diventa rossa da sola. IN PRODUZIONE
basta il deploy: nessuna colonna nuova sul server, nessuna migrazione,
nessuna leva (la colonna `nostr_autore` è solo entrata nella lista di
`importa_nostr.py`, per lo script lanciato a mano su un database
vecchio). Il conto prima del cantiere: zero annunci già adottati, uno
esposto al giro dopo. L'ORDINE DEI LAVORI ERA VINCOLANTE e vale per
chiunque ripulisca a mano i doppioni dell'anello: prima il tappo, poi
la rimozione della copia — vedi il caso dell'annuncio 173, che faceva
da parafulmine all'89.

La busta di consegna nell'ordine (ago 2026, dal campo): sugli ordini
verso un punto di ritiro il venditore deposita nome del destinatario e
codice di ritiro DENTRO l'ordine, cifrati, e il compratore li legge da
lì — sostituisce la chat privata, non il corriere (niente mappa,
niente API, niente tracking). La decisione che governa il cantiere:
NIENTE gate su segna_spedito — il codice arriva quando il pacco è GIÀ
al punto, e i due momenti restano separati come nella realtà; al posto
del gate lo stato d'attesa visibile e il promemoria al venditore. La
riga da non ammorbidire: aprire la busta NON è una ricevuta — il GET è
puro, l'escrow si muove solo coi bottoni di sempre, e il moderatore la
busta non la legge mai (in disputa vede solo SE e QUANDO, correzioni
contate comprese). Vedi Architettura, «LA BUSTA DI CONSEGNA», per la
dedup del segnale d'arrivo e il controllo del libro mastro (col suo
gemello da NON fare). Collaudata: 1375 prove verdi (61 nuove, fra cui
la prova regina «la lettura non scrive niente» e la sentinella
rovesciata sul gate che non esiste), collaudo TestClient su DB
usa-e-getta (40 verdi: escrow immobile al deposito, admin respinto,
correzione fino in disputa, nota al moderatore senza mai il contenuto,
ronda che tace sul sano) e giro visivo CDP a 375px nei due temi, con
la verifica dal vivo che dopo l'apertura l'ordine resta `shipped`.
IN PRODUZIONE basta il deploy: sette colonne additive nascono da sole
e la leva ha il default nel codice. DA GUARDARE al primo giro vero: il
primo ordine al punto con la busta depositata dentro Telegram (i due
messaggi a giorni di distanza, mai il doppione) e il journal di
`sollecita_buste_ferme` al primo battito con un ordine oltre i 3
giorni.

La pagina Ordini ristrutturata (ago 2026): filtro «Solo attivi» e
pillole Tutti/Acquisti/Vendite (due assi indipendenti, stato di
sessione, tutto client-side — la WHERE di /api/orders non si tocca),
la foto vera dell'articolo al posto del 📦 (foto0 dal server, per i
set il primo pezzo, ripiego a catena fino al 📦), e il NASCONDERE
degli affari conclusi — mai cancellare: due colonne per-parte, gate
sui soli stati assorbenti released/refunded, ✕ sulla riga col toast
che dice dove ritrovarlo, «N nascosti — mostrali» col ↩ per
rimetterli in vista, controllo nuovo nella ronda del libro mastro.
Vedi Architettura, «LA PAGINA ORDINI RISTRUTTURATA», per le
definizioni dichiarate (cosa è attivo, perché confirmed/refund e
annullato NON si nascondono) e per il LIMITE NOTO: la lista scarica
anche i nascosti, nascondere alleggerisce la vista e non la risposta.
Collaudata: 1440 prove verdi (65 nuove — il gate su TUTTI i dieci
stati non assorbenti, il per-parte, l'anti-oracolo estraneo ==
inesistente, il dump prima/dopo che dimostra che nascondere non muove
niente, il GET vero con foto0 nei quattro casi e il flag che non esce
mai all'altra parte, la parità NASCONDIBILI server↔client, la riga
rotta della ronda trovata col suo id) più il giro visivo CDP a 375px
nei due temi, con e senza foto, zero errori JS: nascondi → toast →
mostrali → rimetti in vista esercitati dal vivo sul server locale.
IN PRODUZIONE basta il deploy: le due colonne nascono da sole a 0,
nessuna leva, nessun backfill; il client vecchio in cache ignora
foto0 e nascosto e vive come oggi.
Tornando indietro la vetrina riparte da dove si era (ago 2026): si apre
un annuncio, si torna, e ci si ritrova sulla stessa riga di card invece
che in cima. LA DIAGNOSI PRIMA DI TUTTO, perché ha deciso il cantiere e
rovescia l'istinto: la griglia non si perde MAI — 90 card prima, 90
durante, 90 dopo, misurate — quindi non c'era niente da ricaricare e la
cura è stata la più semplice delle due (salvare la posizione lasciando
la vetrina, rileggerla tornando). Il giudice del «ritorno» è
`navApplicando`, la bandierina che il motore alza già oggi mentre
ri-applica una entry: da lì escono gratis il pull-to-refresh e il
cambio filtro che ripartono dalla cima, i percorsi che entrano da fuori
che partono normalmente, e la convenzione dei tab. Vedi Architettura,
«TORNANDO INDIETRO LA VETRINA RIPARTE DA DOVE SI ERA», per i due denti
del lucchetto (il conto delle card e l'azzeramento in `loadListings`) e
per cosa NON si copre e perché.
Collaudato: 14 prove nuove in `prove.py` (1457 verdi, erano 1443) —
sentinelle di forma TORTURATE con nove mutazioni del codice, una per
riga sorvegliata (salvataggio spostato dopo il `display:none`, guardia
del ritorno tolta, cintura del conto card tolta, `scrollTo(0,0)`
rimesso, azzeramento spostato dopo il fetch…): ognuna diventa rossa da
sola, nessuna sopravvive. Più il giro dal vivo sul server locale con le
misure a mano — 90 card e 4200px ritrovati identici da dettaglio,
negozio, carrello e pagina d'acquisto, salto multiplo compreso; e i
casi che NON devono ripristinare, verificati uno per uno: vetrina
ricaricata mentre si è via (→ cima, mai il clamp in fondo), ricerca,
cambio categoria, tab Esplora su Esplora, deep link `/annuncio/{id}`.
Più due screenshot CDP prima/dopo identici pixel per pixel, e zero
errori JS. Un difetto PREESISTENTE trovato di striscia e chiuso qui: il
focus che torna al campo alla chiusura del picker trascinava la pagina
in cima (`preventScroll`). IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna leva, nessuna rotta — e lo stato vive per la sessione,
niente localStorage. DA GUARDARE dal vivo: il giro su un telefono vero
nei DUE contesti — Mini App (il tasto di Telegram) e PWA installata (lo
swipe di sistema) — che è dove i due cammini si sono già divisi in
passato.
Il cambio non muore a un riavvio (ago 2026, caso vero: due deploy alle
13:34 e alle 13:48, CoinGecko muto in tutti e due, e un compratore
davanti alla pagina d'acquisto bloccata). La cache era già fail-open e
teneva l'ultimo valore noto: il buco era che NASCEVA VUOTA. Ora
l'ultimo cambio letto vive nella tabella `cambio_noto` e torna in cache
nello startup, prima che il server risponda a chiunque; ha un'età oltre
la quale smette di valere (`ORE_CAMBIO_VALIDO`, 24 — fino a ieri non
scadeva mai, quindi qualunque soglia finita è una stretta); si tiene
fresco nell'orologio invece che nel percorso caldo, con la riprova a
pause crescenti al boot e il raffreddamento di un minuto dopo un buco;
e il client non chiama più CoinGecko per conto suo — il cambio viaggia
nella busta di prima pagina di `/api/listings`, una fonte sola, così il
«≈» della vetrina e il conto del server non possono più divergere. Vedi
Architettura, «IL CAMBIO NON MUORE A UN RIAVVIO», per le tre età e per
il perché delle 24 ore.
Poi la fonte unica è costata freschezza, e si è stretta la finestra
(ago 2026, il giorno dopo): il rinfresco ha un giro suo da 60 secondi
(`orologio_cambio`, leva `CAMBIO_RINFRESCO_S`) invece di stare
nell'orologio da dieci minuti — perché da quando la fonte è una sola,
la cadenza del server è la freschezza che vede chiunque guardi un
prezzo. La soglia si DERIVA dalla cadenza (due giri di slack, minimo
120s) invece di essere un secondo numero da tenere in pari, e al
momento della fattura non si forza nessuna lettura: nel percorso caldo
la rete resta la rete di sicurezza dietro il raffreddamento. Misurato
dal vivo: il valore sul disco non ha mai più di 60 secondi, e nell'arco
di due minuti si vede muovere (56.324 → 56.329 → 56.340 €/BTC).
E poi l'ultima verità doppia, trovata nel journal dopo il deploy (ago
2026): alle 14:52:33 il server legge il cambio, alle 14:52:57 l'import
Nostr dice che non è disponibile. `importa_nostr.cambio_btc()` era una
seconda lettura — e stava DENTRO `importa_venditore`, cioè una chiamata
PER VENDITORE a ogni giro orario, dallo stesso IP da cui bussa già il
nostro rinfresco. Ora il server legge il cambio una volta per giro e lo
passa a tutti (`cambio_per_import()`, il patto del `vaglio`), la stessa
GET porta anche il dollaro che all'import serve, e lo script a mano
resta identico. Vedi Architettura, «L'IMPORT DA NOSTR BEVE ALLA STESSA
FONTE».
Collaudato: 21 prove nuove/aggiornate (1512 verdi, erano 1499) più
cinque mutazioni del codice — import che torna a leggersi il cambio da
solo, cambio vuoto che passa in silenzio, lettura spostata dentro il
giro dei venditori, dollaro scaduto che esce lo stesso, euro che smette
di comandare — ognuna rossa da sola. E un collaudo eseguibile che gira
`importa_venditore` VERA su database usa-e-getta coi relay di cartone,
12 verdi: col cambio iniettato l'annuncio in EUR entra convertito al
cambio del server e CoinGecko non viene toccato; col cambio vuoto si
salta e lo si dice; con `cambio=None` la strada di ieri è intatta; e
l'annuncio in USD entra col dollaro del server e si salta senza. IN
PRODUZIONE basta il deploy: la riga 'usd' nasce da sola al primo
rinfresco.
Collaudato: 29 prove nuove in `prove.py` (1486 verdi, erano 1457) — il
giudice puro al filo esatto e un secondo dopo, l'andata e ritorno dal
disco, e il caso del cantiere provato per davvero (cache vuota + rete
muta = vale l'ultimo noto, e un buco non azzera niente) — con le
sentinelle di forma TORTURATE, cinque mutazioni del codice una per
riga sorvegliata, ognuna rossa da sola. Più il giro dal vivo sul
server locale con CoinGecko puntato su un host irraggiungibile: al
riavvio la riga «ripreso dal database», la vetrina che serve il cambio
lo stesso, e un preventivo su un listino da 38,50 € che esce a 68.455
sats invece del 503 di ieri; poi la stessa prova con la riga sul disco
invecchiata a 30 ore, che torna al 503 onesto invece di convertire con
un numero vecchio. E in browser: zero chiamate a CoinGecko, prezzi col
«≈» e nessun errore JS. IN PRODUZIONE basta il deploy: la tabella
nasce da sola (vuota, quindi il primo avvio dice «nessun valore
salvato» e lo chiede subito) e la leva ha il default nel codice. DA
GUARDARE al primo deploy: le due righe 💱 nel journal — al secondo
riavvio deve comparire «ripreso dal database».
Lo stock raccontato bene (ago 2026): l'annuncio esaurito non si butta
più — resta nel negozio in fondo, spento, e il venditore lo rifornisce
con un gesto invece di rifare la scheda da capo. La DIAGNOSI ha ridotto
il cantiere prima di scrivere una riga: il riassortimento esisteva già
(`ricarica_quantita` accettava lo stato 'venduto'), e il guasto vero
era che il deep-link `/annuncio/{id}` rispondeva 404 — un link mandato
a un amico moriva insieme alle scorte. Più il badge «Ne resta 1», che
parla SOLO dove la scarsità è una notizia: la colonna `quantita_max`
esiste per quella domanda sola, e la sua scopa è anche il backfill
onesto («ne ha almeno tanti quanti ne ha adesso» è un limite inferiore
vero, non un passato fabbricato). E il `prompt()` del sistema
operativo se n'è andato: un foglio di casa che sull'errore resta aperto
col numero da correggere. Vedi Architettura, «LO SCAFFALE VUOTO», per
le decisioni di Andrea (dove si vede l'esaurito, dove compare il badge,
il foglio al posto del prompt) e per le tre strade scartate sul colore.
QUATTRO CORREZIONI al piano approvato, tutte trovate costruendo:
1) il RIMBORSO alza il massimo — avevo dichiarato il caso impossibile,
e non lo è (3 pezzi, venduti tutti, ricarica a 1, una disputa ne
rimborsa 3 = 4, sopra il massimo di ieri); 2) l'ASTA non è mai
«esaurita», ed è la stessa riga che il server ha sempre avuto in
`ricarica_quantita`; 3) il badge non prende un colore ma la CARTA, e
dice «Ne resta 1» perché a 320px «Ultimo pezzo» tocca il barattolino
(misurato); 4) Esc NON arriva gratis ai fogli — solo picker, lightbox
e tour lo ascoltano, e aggiungerlo sarebbe un cantiere per tutti e
dodici o per nessuno. Più la correzione di un numero SBAGLIATO in
questo file da mesi: il prezzo arancio del cartellino rende 3,01 e non
3,59 (la conclusione regge e anzi si rafforza — vedi la voce ferie).
Collaudato: 1552 prove verdi (40 nuove, fra cui la scopa girata
DAVVERO su un database di cartone e il giudice puro sui sette casi che
decidono), 11 MUTAZIONI del codice una riga alla volta — massimo
assegnato secco, scopa che abbassa, pop tolto, guardie del bottone,
lampo che torna a parlare su un esaurito — e ognuna diventa rossa da
sola; 23 prove funzionali su DB usa-e-getta (il link condiviso che non
muore, lo scaffale che non entra nel totale, «ricaricare a UNO non
cancella la memoria dei quattro», la ronda che tace); giro visivo via
CDP a 375/360/320px nei due temi col rifornimento esercitato dal vivo.
IN PRODUZIONE basta il deploy: la colonna nasce da sola e la scopa la
riempie al primo avvio (misurato su 888 annunci veri in locale), nessuna
leva, nessuna rotta nuova, nessuno stato nuovo. DA GUARDARE al primo
giro: che il badge sia spento ovunque — è giusto così, si accende solo
su chi rifornisce da qui in avanti — e il primo venditore vero che
rifornisce (che il post di canale perda la ✅ e l'evento Nostr torni
`active`).

Le anteprime dei link (ago 2026): un link di Barattolo su Telegram,
WhatsApp o in un DM Nostr arrivava come una card vuota col titolo
generico — i crawler non eseguono JavaScript, e qui titolo, prezzo e
foto nascono tutti da fetch. Adesso le cinque rotte che servono
miniapp.html ci infilano in testa i loro meta Open Graph. La regola che
ha aperto il cantiere, e la sola da non ammorbidire: RIMOSSO E
REVISIONE non raccontano niente di sé — un rimosso in un'anteprima
cachata e inoltrata è lo scudo anti-resurrezione bucato da un'altra
parte. Il VENDUTO invece ha la sua card vera (decisione di Andrea: è
uno scaffale vuoto, non un annuncio che non c'è — il link non muore con
le scorte), col «✅ Venduto» in testa alla descrizione perché non
menta, e col confine tenuto allineato a quello di `/api/listings/{id}`
da una prova apposta. Vedi Architettura, «LE ANTEPRIME DEI LINK», per
le altre due cose da non rovesciare (i meta in cima a 900 KB di pagina,
l'escaping in attributo) e per la scelta dell'immagine coi suoi tre
ripieghi.
Col cantiere è arrivato `_fmt_eur` e la regola che un euro si scrive in
un modo solo in tutta l'app (il client lo faceva già: il server era
l'unico fuori riga) — coi tag NIP-99 fuori apposta, che lì il punto
decimale è la specifica. La sentinella che lo sorveglia ha preso tre
casi che il censimento a mano aveva mancato, perché scrivevano «EUR» a
parole invece del simbolo. Poi la stessa medicina ai SATS, che di
formati ne avevano quattro: 33 cifre riportate su `_fmt_sats`, e
soprattutto `_fmt_sats` che NON SOLLEVA PIÙ — un formattatore che alza
le mani dentro il `try/except` di una notifica non fa un errore, fa
sparire l'allarme, ed era successo davvero sull'avviso di pagamento
rifiutato (`importo_invoice` torna `None` sulla bolt11 illeggibile).
Collaudate: 78 prove nuove (1629 verdi), e quella sul rimosso è
ESEGUIBILE e non una sentinella sulla forma — passa da un database vero
e il titolo si cerca nell'HTML che esce. TORTURATE con ventuno mutazioni
del codice, una per riga sorvegliata (stato tolto dalla WHERE, rimosso
rimesso dentro, venduto tolto fuori, «✅ Venduto» che sparisce, euro
tornato al punto in tre modi diversi, `_fmt_sats` che torna a sollevare
sul `None`, sats scritti a mano — anche nascosti nella piega di una
stringa spezzata —, virgola inglese rimessa, escaping a quote=False,
rotta tornata al file nudo, francobollo scambiato col pieno, conto del
negozio senza stato, tg_id nell'anteprima, meta prima del charset,
cintura che rilancia, ripiego che appende in fondo, ritorno alla
modalità testo):
ognuna diventa rossa da sola, e la prima ne fa rosse cinque insieme. Più
il giro dal vivo sul server locale simulando gli User-Agent veri di
Telegram, WhatsApp, Facebook, Slack e dei client Nostr con la loro
lettura parziale — tutti vedono la stessa card, l'ultimo meta cade al
byte ~1300, e l'og:image sta dentro i limiti di tutti e tre —, la
verifica che la pagina esca IDENTICA al file byte per byte, e
l'escaping provato end-to-end con una riga usa-e-getta dal titolo
cattivo (virgolette, `<script>`, apostrofi: 13 meta interi, nessun tag
spezzato, e la riga poi cancellata), più il venduto vero e un listino
in euro guardati dal vivo («✅ Venduto · 50 sats (≈ 0,03 €)»,
«40,00 € (≈ 70.764 sats)»).
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta nuova. DA FARE AL PRIMO DEPLOY, ed è il
pezzo che in locale non si può fare: `python anteprime.py
https://barattolo.store /annuncio/N` e poi le card vere in chat, con
URL USA-E-GETTA — un annuncio di prova da rimuovere subito dopo —
perché Telegram e WhatsApp cachano a lungo e dal nostro lato non si
bustano; e verificare col rimosso VERO che la sua card sia quella
generica e col venduto VERO che porti il suo «✅ Venduto».
Tre correzioni dall'audit (ago 2026), tutte e tre sulla stessa idea:
un annuncio può raccontare cose a gente che Barattolo non l'ha mai
aperto. M1, CHI SI FINGE BARATTOLO — la card brandizzata è un link
autentico sul nostro dominio dove i testi li sceglie chi pubblica:
voce nuova nel prompt, VIETATO a chi SI RIVOLGE al lettore a nome
della piattaforma e DUBBIO a chi si intesta solo un ruolo, con le due
contro-regole («nominare è lecito», «raccontare come funziona pure»)
che sono la metà delicata, e il rifiuto che ora dice cosa si è
sbagliato invece dell'elenco di armi e droghe. M2, L'OG:IMAGE VERSO
HOST DI TERZI — l'URL remoto di chi pubblica su Nostr non ci finisce
più: diventava la campana di chiunque veda un'anteprima, ed è
sostituibile a card già in giro. B6, L'AVVISO CHE SPARIVA IN SILENZIO —
corriere e tracciamento scappati in `segna_spedito` e `reso_spedito`.
Vedi le voci loro in Architettura per i perché.
Collaudate: 53 prove nuove (1683 verdi, erano 1630) — quelle di B6
ESEGUIBILI sulle funzioni vere, quelle di M1 sulla forma del prompt
più la sentinella che il lotto non se ne sdoppi uno suo — e
QUATTORDICI mutazioni del codice, una per riga sorvegliata: ognuna
diventa rossa da sola. Due difetti trovati dalle prove e non dalla
lettura del codice: «finto» non è una declinazione di «finge» (la
lista dei motivi non lo prendeva, e «finto servizio clienti» cadeva
nel ramo dei servizi), e l'ordine dei due rami di `messaggio_rifiuto`,
che scambiato manderebbe a un impostore il messaggio di garbo.
E IL COLLAUDO COL MODELLO VERO HA PAGATO SUBITO (ago 2026, secondo
giro): 14/15, con un FALSO POSITIVO — la bici la cui descrizione
spiega l'escrow, bocciata perché «non descrive l'oggetto in vendita».
La causa era la formulazione, non il modello, e la storia con la cura
a tre gambe sta nella voce sua in Architettura; il caso è rimasto nel
collaudo come regressione permanente, con una gemella accanto. È
esattamente il motivo per cui quel collaudo esiste: nessuna prova di
CI l'avrebbe visto, e in vetrina si sarebbe visto solo quando un
venditore onesto avesse protestato.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva. DA FARE PRIMA DEL DEPLOY, ed è il pezzo che in locale
non si può fare perché vuole la chiave vera: `python
collaudo_impersonazione.py` sul VPS — se un OK atteso finisce in
VIETATO è un falso positivo, cioè annunci legittimi bloccati, e il
prompt si corregge A MANO. IMPERFEZIONE DICHIARATA che resta:
l'immagine remota la scarica comunque il browser di chi APRE la
scheda (è la regola della vetrina, dichiarata). Il titolo nudo dei
solleciti è invece chiuso — vedi più sotto, ed erano quindici siti.
Nessuna riga si cancella senza aver chiesto a LNbits (ago 2026,
trovato di striscia rispondendo a un'altra domanda — «al pagamento il
compratore riceve una notifica?» — e portato avanti prima di tutto il
resto): il reaper buttava via gli ordini 'creato' scaduti con un
DELETE secco, e con loro il `payment_hash`, cioè l'unico filo verso un
pagamento che nessuno aveva mai verificato. LA DIAGNOSI HA CAMBIATO LA
DOMANDA, ed è la parte da tenere: la fattura NON sopravvive alla riga
(muore a 900s, la riga a 1800s) — quindi il pericolo non era «paga
dopo la cancellazione» ma «paga prima, nessuno guarda, la riga sparisce
coi sats dentro». MAI SUCCESSO in produzione, verificato prima di
toccare qualunque cosa incrociando gli incassi di LNbits coi
payment_hash noti (zero orfani; il metodo è nella voce in
Architettura, e da SQL non si può fare). La cura è la regola delle
lapidi arrivata fino in fondo: il reaper i 'creato' non li tocca più e
a guardarli — solo a fattura morta — c'è `controlla_abbandonati`
nell'orologio, che è async e a LNbits ci può parlare. Vedi
Architettura, «E NESSUNA RIGA SI CANCELLA SENZA AVER CHIESTO A
LNBITS», per il fail-open nel verso giusto, il rilancio pagato che non
entra in gara e le due conseguenze — collaudata con 14 prove nuove
(1707 verdi), una sentinella ROVESCIATA e nove mutazioni del codice
una per riga sorvegliata, di cui la nona ha smascherato una sentinella
che non poteva fallire. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna migrazione, nessuna leva. DA GUARDARE al primo giro:
nel journal non deve comparire niente — un «⚠️ Ordine #N pagato e mai
verificato» vuol dire che il caso è appena successo per davvero, e
quello è il momento di guardare l'ordine, non la funzione.
La ricevuta del compratore (ago 2026, il giorno dopo — chiude
l'imperfezione che quel cantiere aveva dichiarato): chi paga riceve una
notifica appena i sats sono in cassaforte, e la riceve SEMPRE, non solo
quando l'accredito arriva dall'orologio. Il toast in-app se n'è andato:
durava tre secondi e non lasciava niente da ritrovare. La decisione che
governa il resto è «sempre» invece di «un ramo per l'orologio»: costa un
messaggio in più nel caso normale e in cambio la ricevuta vive nel
FUNNEL (`_incassa_ordine`), quindi tutte e tre le strade dell'accredito
la ereditano — e anche quelle di domani. La coda segue la STRADA SCELTA
o si dice il falso a metà degli ordini, e sul digitale non si promette
mai la conferma, che lì le finestre corte scattano da sole. Vedi
Architettura, «LA RICEVUTA DEL COMPRATORE».
Collaudata: 42 prove nuove (1748 verdi, erano 1706) — il giudice puro
strada per strada più `_incassa_ordine` chiamata DAVVERO su un database
vero, col titolo cattivo e i grassetti che restano pari — e DODICI
mutazioni del codice una per riga sorvegliata (ricevuta tolta, titolo
nudo, escape prima del troncamento, digitale che promette la conferma,
i tre rami della coda tolti a uno a uno, punto passato come testo,
toast rimesso, destinatario sbagliato, coda scritta a mano, e la
ricevuta traslocata sul poll — la regressione che rimetterebbe muto
l'orologio): ognuna diventa rossa da sola. Più il giro DAL VIVO sulle
sette strade con un database usa-e-getta — le cinque code, il titolo
con un «<» dentro, `controlla_abbandonati` e il riacciuffo di
`controlla_annullati`, che sono i due casi per cui il cantiere esiste —
e il controllo nel browser vero che il toast non si accenda più e
l'ordine si apra lo stesso. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna migrazione, nessuna leva, nessuna rotta. DA GUARDARE
al primo giro: la prima ricevuta vera dentro Telegram — e soprattutto
che chi compra un CODICE non si veda promettere un pacco.
Il titolo nudo nelle notifiche (ago 2026, subito dopo: la stessa
famiglia di B6, chiusa). Il conto vero era **quindici siti** e non i
«quattro solleciti fratelli» che questo file dichiarava — il polso 🛒
ai moderatori, quattro solleciti su sei, e altri otto che solo un
censimento ha tirato fuori; il più grave è il 🧊 di un pagamento
INCERTO, cioè l'avviso che dice che dei sats possono essere usciti
davvero. La lezione è quella: l'elenco a memoria di un buco dichiarato
rimpicciolisce, e a contare dev'essere una prova che guarda il file.
Una regola sola — si scappa all'assegnazione — più l'ultima rete in
fondo al tubo, che è la parte che risponde al danno vero: la risposta
di Telegram non la guardava nessuno, quindi il 400 «can't parse
entities» finiva nel nulla; ora il messaggio si rimanda SPOGLIO e la
cosa si STAMPA. Vedi Architettura, «IL TITOLO NUDO NELLE NOTIFICHE»,
per la strada scartata (l'escape dentro il polso, che avrebbe fatto
vivere la stessa variabile in due regimi) e per il rovescio — il 404
del carrello, dove scappare sarebbe stato il bug.
Collaudato: 36 prove nuove (1784 verdi, erano 1748) — in testa il
CENSIMENTO, che non è un elenco ma una passata su tutte le funzioni
del file, così il sollecito nuovo di domani entra nel conto da solo —
e NOVE mutazioni una per riga sorvegliata, di cui una ha smascherato
una sentinella che non poteva fallire (il `print` del collaudo la
teneva verde). Più il giro DAL VIVO con un titolo ostile
(`Cuffie <b>AKG</b> & "K371" <script>`) su ricevuta, polso e tre
solleciti: tutti scappati, `<b>` pari, e l'evento NIP-99 che tiene
giustamente il titolo grezzo. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna leva, nessuna rotta. DA GUARDARE al primo giro: nel
journal non deve comparire nessun «⚠️ HTML rifiutato da Telegram» — se
compare, quella riga dice il sito da scappare alla fonte.

I timbri degli avvisi periodici (ago 2026, caso dal campo: il
termometro delle sottocategorie arrivato TRE volte in cinquanta minuti,
agli orari dei tre deploy di quel lunedì). Il timbro viveva in un
globale: un globale muore col processo, quindi non era un gate ma una
deduplica valida quanto il processo — e questo file prometteva «al più
due volte quel lunedì», che non era garantito da niente. Ora sta nella
tabella `timbri`. Erano TRE le funzioni con lo stesso ancoraggio, e la
peggiore non è quella che si è vista: `sollecita_revisioni` contava
24 ore da un globale SENZA nemmeno il gate del calendario — due deploy
a un minuto di distanza e suonava due volte. Più la riga nel journal su
tutti e tre, che era il secondo difetto: l'invio non si trovava da
nessuna parte, quindi un avviso che parte troppo non si poteva neanche
diagnosticare. Vedi Architettura, «I TIMBRI DEGLI AVVISI PERIODICI»,
per il fail-open nel verso del parlare e per i quattro gate in RAM che
RESTANO col loro perché.
Collaudato: 29 prove nuove (1814 verdi, erano 1785) — in testa quella
ESEGUIBILE che simula tre deploy (tre ambienti diversi, un database
solo) e chiede una notifica sola — più NOVE mutazioni una per riga
sorvegliata, ognuna rossa da sola. Più il giro DAL VIVO con tre
subprocess veri sullo stesso file di database: una notifica, la riga di
journal sul primo giro, e la tabella con dentro il suo timbro. E la
migrazione provata su una COPIA del database esistente: una tabella in
più, nessuna persa, `timbri` vuota.
IN PRODUZIONE basta il deploy (la tabella nasce da sola). ⚠️ DA SAPERE:
oggi è lunedì e la tabella nasce vuota, quindi il primo riavvio dopo il
deploy manda UN'ULTIMA notifica del termometro — dal secondo in poi
silenzio. Non si semina il timbro apposta: sarebbe un trucco una-tantum
dentro una migrazione, e su un'installazione nuova salterebbe il primo
lunedì per davvero.

Farsi trovare (ago 2026): Barattolo diventa indicizzabile. Indirizzi
parlanti `/annuncio/{id}-{slug}` e `/negozio/{chi}-{slug}` (i vecchi non
muoiono e non redirigono: rispondono 200 col canonical), un `<title>`
per pagina — che ROVESCIA una regola scritta in CLAUDE.md —, le card e
le piastrelle diventate collegamenti VERI, 27 pagine `/categoria/{slug}`,
il contenuto pre-renderizzato nel corpo dentro il «cartello», più
`robots.txt`, `sitemap.xml` (~900 URL) e il JSON-LD Product/Offer col
prezzo in BTC, che è una conversione esatta e non un cambio inventato.
Vedi Architettura, «FARSI TROVARE», per i tre regimi di escape, la
regola robots-vs-noindex e le imperfezioni dichiarate.
Collaudato: 1995 prove verdi (211 nuove) e — la parte che conta —
QUINDICI MUTAZIONI del codice, una per sentinella, che diventano rosse
tutte e quindici: card senza `position:relative`, bottoni rimessi dentro
l'`<a>`, `preventDefault` dopo `openDetail`, `navSpingi` all'atterraggio,
la chiamata tolta da `avviaVetrina`, la regex ancorata col `$`, lo spacco
del negozio tolto, `html.escape` dentro `_ld`, INNER JOIN al posto del
LEFT, un rimosso rimesso nella WHERE, «Disallow: /», `int(aid)`, il
titolo crudo, la lampo nella query, il canonical su una pagina
deindicizzata. Più il confronto PIXEL prima/dopo su cinque viste
(vetrina chiara e scura, negozio, Sfoglia chiara e scura) con un
worktree al commit precedente: **identiche byte per byte**, che è la
prova vera del «zero pixel di differenza» sulla card ristrutturata. E
`anteprime.py`: le anteprime social non cambiano, tutti e cinque i
crawler vedono la stessa cosa e l'ultimo meta sta al byte 1868.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva. `sw.js` passa a v4 perché `offline.html` (in dispensa) ha
guadagnato il suo noindex. DA FARE DOPO IL DEPLOY, ed è il pezzo che in
locale non si può fare: inviare la sitemap a Search Console, e tenere
d'occhio la BANDA la prima settimana (~820 MB per passata completa: vedi
la voce del costo). DA GUARDARE: che `/robots.txt` risponda 200 sul
dominio vero, e che la prima card social condivisa dopo il deploy sia
identica a prima.

L'offerta si porta dietro i pezzi (ago 2026): il venditore accettava un
prezzo unitario a quantita' INDETERMINATA e poteva ritrovarsi a vendere
tutto lo stock alla cifra scontata, scoprendolo con l'ordine — e il
compratore che aveva scelto tre pezzi li perdeva per strada. Ora la
quantita' scelta accanto ad «Acquista» viaggia con l'offerta e comanda
nei quattro percorsi del conto. La cifra resta l'UNITARIO (si confronta
col listino, e un totale romperebbe la divisione a ritroso di
`_righe_ordine`) e le due facce si dicono INSIEME ovunque i pezzi siano
piu' di uno. Nello stesso giro il foglio si rifa': tre pillole senza
controvalore, toggle €/₿ che governa la lettura, la riga «Offri 120.000
sats per 3 pezzi (40.000 sats al pezzo)» al posto del totale incompleto
di prima — col TOTALE davanti, che e' quello che si vuole sapere per
primo —, lo stepper della quantita' dentro il foglio (che scrive nella
STESSA variabile del gemello: due numeri divergenti sono il difetto che
il cantiere toglie), la ✕ al posto di
«Annulla», e il tasto offerta che porta la quantita' come il suo
gemello. Vedi Architettura, «L'OFFERTA SI PORTA DIETRO I PEZZI», per la
decisione unitario-vs-totale coi suoi tre perche', per l'ordine delle
guardie che NON si tocca (spostare il blocco dell'offerta sopra la
ripresa e' una regressione, non una pulizia) e per il corner dichiarato
del client che chiede piu' pezzi dell'accordo. Collaudata: 2095 prove
verdi (56 nuove — il giudice puro, l'aritmetica con la divisione a
ritroso esatta, i quattro percorsi, l'ordine delle guardie, il gemello
client, il foglio, lo stepper e le due superfici del tasto) piu' SEDICI
mutazioni del codice una per riga sorvegliata, ognuna rossa da sola —
e due sentinelle sono state riscritte proprio perche' la tortura le ha
trovate VACUE (cercavano una stringa che vive anche altrove); e il giro
vero su database usa-e-getta col server acceso: offerta per 3 pezzi →
accordo → il client che chiede 5 e ottiene 3, preventivo == compra al
sat (215.000), unitario esatto a ritroso, stock sceso a 2 col 400
onesto e l'offerta ancora viva, offerta «di ieri» che si comporta come
allora, 99 pezzi limati a 2. Piu' gli screenshot a 320 e 375px nei due
temi (testata del foglio senza collisioni, barra coi due tasti a 3
pezzi, pannello del venditore, pagina d'acquisto). IN PRODUZIONE basta
il deploy: la colonna nasce a 0 — cioe' quantita' non dichiarata per
tutte le offerte gia' aperte — e non c'e' nessuna leva. DA GUARDARE al
primo giro: la prima offerta vera con piu' di un pezzo dentro Telegram,
e che il venditore legga nella notifica del bot sia il totale sia il
fatto che accettare non blocca niente.

L'AI segnala, non decide (ago 2026, giro urgente dal campo: un
venditore vero fermo). «Sat's Oil 🫒 GENESIS EDITION» bloccato per
impersonazione col motivo «il nome appare progettato per confondere
con Barattolo (associando "sat")» — su un mercatino che incassa in
satoshi. Due difetti e un cambio di rotta: la voce del prompt ora dice
che i sats sono la MONETA e che una somiglianza di NOME non è mai un
motivo; dice anche cosa fare quando il testo non c'è (lo stesso motivo
sosteneva che titolo e descrizione mancassero, mentre il titolo
c'era: il modello deduceva dal non detto); e la lista
`PAROLE_IMPERSONAZIONE` aveva un buco separato, «confondere», per cui
al venditore era arrivata pure la lista delle armi e delle droghe.
IL CAMBIO DI ROTTA (decisione di Andrea): un VIETATO dell'AI non basta
più a bloccare — ferma solo su QUATTRO famiglie (armi, droghe, sesso a
pagamento e sfruttamento, documenti e credenziali), tutto il resto va
in REVISIONE, dove non è pubblico e decide un umano. Vedi Architettura,
«L'AI SEGNALA, NON DECIDE», per l'elenco completo, per cosa ne è FUORI
e perché (refurtiva, contraffazione, farmaci, animali protetti: hanno
tutti una lettura innocente che il modello può aver frainteso), e per
la ragione che rende la scelta poco rischiosa — in revisione
l'annuncio non è pubblico, quindi il costo è la coda e non il rischio.
MISURATO, non stimato: il collaudo col modello vero dà **18/19 con
ZERO falsi positivi** (i tre casi nuovi sui sats passano tutti; l'unico
fuori posto era «Assistenza Barattolo — supporto agli utenti», atteso
VIETATO e risposta DUBBIO — un «caso cattivo passato», il tipo meno
grave, che ora finisce comunque in coda. L'atteso è stato rimesso a
DUBBIO, che è quello che il prompt insegna: col prossimo giro il conto
torna 19/19 — ed è tornato, **25/25** il 23 ago 2026 coi sei casi dei
servizi), e `stima_coda_moderazione.py` sui rifiuti
veri di 30 giorni dice che la coda passa da **7 a 14, cioè 0,2 annunci
in più al giorno**. 2171 prove verdi, nove mutazioni tutte rosse, e UNA
prova che ha cambiato lato: chiedeva che «VIETATO: impersonazione»
fosse un rifiuto secco, cioè certificava il comportamento che ha
fermato il venditore. IN PRODUZIONE basta il deploy: nessuna colonna,
nessuna migrazione, nessuna leva nuova — e `MODERAZIONE_REVISIONE`
spenta resta il freno d'emergenza che rimette il binario di ieri.
DA RIFARE quando il volume cresce: la stima della coda, che è il solo
numero su cui questa scelta poggia.

Il foglio dell'offerta, rifinito dal campo (ago 2026, tre giri): il
campo del prezzo è sempre visibile e modificabile — le pillole lo
riempiono, non lo nascondono — e la pillola accesa si DEDUCE dalla
cifra invece di ricordarsi, o dopo un ritocco direbbe il falso; il
campo dice «al pezzo» mentre si digita (solo coi pezzi >1: chi ne
vuole tre ragiona sul totale e rischia di scrivere 120 intendendo il
totale mentre ne offre 360); il minimo non è più un cartello
permanente ma un avviso che compare solo sotto soglia, e lì sparisce
anche la riga del totale — due righe dove ne serve una sola. Più la
tastiera, che non copre più quel che si scrive: vedi Architettura, «LA
TASTIERA NON COPRE PIÙ QUEL CHE SI SCRIVE», per il perché non basta
`100dvh`, per il difetto introdotto e visto sullo screenshot (i fogli
CHIUSI che rientravano in vista) e per l'ONESTÀ SULLA VERIFICA — in
headless lo scatto non si riproduce né si esclude, quindi invece di
scommettere su una causa sola si sono tolte tutte quelle plausibili.
IN PRODUZIONE basta il deploy. DA GUARDARE dal telefono: che lo scatto
sia sparito nella PWA — se sopravvive, il sospetto successivo è la
`max-height` che cambia durante l'animazione.
Il compratore ritira un'offerta (ago 2026, caso vero dal campo): chi ne
manda una per sbaglio non doveva più aspettare 48 ore o chiedere al
venditore di rifiutarla — e intanto non poteva nemmeno rifarla giusta,
che la guardia `attive` glielo impediva. Rotta sua
(`POST /api/offerte/{id}/ritira`), stato `ritirata` che è una lapide,
da 'proposta' e da 'accettata' ma mai da 'controproposta' (lì c'è già
«Rifiuta»). Le decisioni di Andrea: il venditore lo sa SEMPRE, e il
tetto dei 3 tentativi conta anche le ritirate — non contarle aprirebbe
uno spam illimitato, e il ritiro non toglie niente perché oggi chi
sbaglia brucia comunque il tentativo e in più aspetta due giorni. Vedi
Architettura, «IL COMPRATORE RITIRA», per il perché non è un'azione di
`rispondi_offerta` e per la correzione che il cantiere ha fatto al
proprio piano: a bloccare è l'ordine VIVO e non l'esistenza del numero,
o si apre un vicolo cieco da cui nessuna azione dell'utente esce.
Collaudato: 54 prove nuove (2246 verdi, erano 2192) e — la parte che
conta — DODICI MUTAZIONI del codice, una per riga sorvegliata (il CAS
tolto, la guardia di proprietà fuori dalla WHERE, il 404 rimesso, la
guardia dell'ordine riportata alla forma secca, il gate della scadenza
tolto, la controproposta ammessa, `'ritirata'` in un secondo posto, un
`UPDATE ordini` infilato nel ritiro, la scadenza non azzerata, il
titolo nudo, il bottone tolto dal client, il tetto hardcodato): ognuna
diventa rossa da sola. Più il giro dal vivo sul server locale — il
venditore respinto, l'anti-oracolo verificato sul database vero
(altrui e inesistente rispondono identico), il ritiro che libera
`attive` e permette di riprovare SUBITO, l'ordine vivo che blocca e la
lapide che non blocca, e gli ordini immobili prima e dopo — e il gesto
nel browser coi due confirm e zero errori JS. IN PRODUZIONE basta il
deploy: nessuna colonna, nessuna migrazione, nessuna leva.

Gli ordini si leggono meglio (ago 2026, due giri): gli ANNULLATI
spariscono dalla lista — la lapide resta nel database, dove serve alla
macchina — e i VERBI seguono il tempo dell'affare, con la cifra che
ognuno ha davvero mosso (totale a chi paga, netto a chi incassa) e
nessuna cifra sul rimborso, dove nessuno ha comprato e nessuno ha
venduto. Nel DETTAGLIO: via la modalità, che era già scritta due righe
sotto; la spedizione torna un inciso accanto alla cifra (muto quando la
promessa del negozio l'ha resa gratis, che «di cui 0» non dice niente);
e i testi parlano a chi legge — il compratore non si sente più chiamare
«l'acquirente» a casa sua. Vedi Architettura, «LE LAPIDI NON SI VEDONO»
e «IL DETTAGLIO PARLA A CHI LEGGE», per le decisioni di Andrea (dove
finiscono gli annullati, quale cifra per quale lato, la strada scartata
del verbo nel dettaglio) e per le terze persone che RESTANO tali.
Collaudati: 2433 prove verdi (37 nuove) e DICIASSETTE mutazioni del
codice, una per riga sorvegliata — annullati rimessi in lista, `orders`
riletto in una delle tre righe, verbo che scavalca il giudice, netto
ricopiato a mano, inciso che parla a spedizione gratis, terze persone
girate a tutti e due i lati —, ognuna rossa da sola. Più il giro dal
vivo via CDP a 390px nei due temi e dai due lati, con i casi che lo
screenshot non copre verificati a parte (spedizione gratis, rimborso,
sola spedizione su una riga). IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna rotta, nessuna leva — solo client.

Chi ha pagato può bussare, e la disputa si vede (ago 2026): il bottone
«🔔 Ricorda al venditore di spedire» sull'ordine pagato e non ancora
partito — 48 ore dal pagamento (24 sul codice online), uno al giorno,
tre in tutto, poi resta la disputa — col testo che è un promemoria e
non un rimprovero, perché chi non ha spedito ha quasi sempre solo
avuto una giornata storta. I contatori dell'automatico non si toccano:
colonne sue e ancora `creato`, o chi bussa spesso allontanerebbe il 🧊
ai moderatori. E «⚠️ C'è un problema — apri disputa» prende la forma
di tutti gli altri col rosso velato dei ponti: era un testuale
sottolineato e in fila coi due blocchi colorati spariva. Vedi
Architettura, «E CHI HA PAGATO PUÒ BUSSARE PRIMA» e «E L'USCITA DI
SICUREZZA HA LA STESSA RICETTA». Più la prima riga del riquadro verde,
che ora dice un GESTO e lo gira a chi legge («Hai depositato i sats» /
«Hai il pagamento in garanzia»). Collaudati: 2485 prove verdi (52
nuove — l'endpoint girato DAVVERO su sqlite in memoria, con l'ambiente
POVERO che esplode con NameError se un domani imparasse a toccare i
sats) e DICIOTTO mutazioni del codice, una per riga sorvegliata,
ognuna rossa da sola; più il giro dal vivo sul server locale (le tre
finestre, la pausa, il tetto, l'anti-oracolo verificato sul database
vero) e gli screenshot dei quattro bottoni in fila nei due temi.
IN PRODUZIONE basta il deploy: le due colonne nascono a 0 e le quattro
leve hanno il default nel codice. DA GUARDARE al primo giro: il primo
promemoria vero dentro Telegram — che al venditore arrivi UN messaggio
e che si legga come un promemoria.

La coda degli ordini fermi, e la riga per chi ha pagato (ago 2026): il
🧊 ai moderatori era un messaggio Telegram e basta — dopo, un ordine
coi sats in cassaforte non compariva in nessuna lista e si raggiungeva
solo sapendone il numero; e il compratore veniva avvisato UNA volta
sola, al primo squillo. Adesso c'è la sezione «⏸ Ordini fermi» nel
pannello admin (regola in una frase: «i sats sono in cassaforte e
nessuno si muove da 10 giorni», il complemento dei terminali) e una
riga permanente nell'ordine di chi ha pagato. Nessun automatismo
nuovo: la coda LEGGE e basta, la riga racconta, e i sats continuano a
muoverli solo le persone. Vedi Architettura, «E DOPO IL 🧊 C'È UNA
CODA», per l'invariante della soglia, la regola dello zero sulle
ancore e le due popolazioni scoperte trovate costruendola (il `locked`
con `consegna_scelta=''` e lo `shipped` con `spedito_il=0`, che non
ricevono nessun promemoria e nessun 🧊). Incluso, su decisione di
Andrea, il buco latente che la coda avrebbe reso un vicolo cieco: il
pannello del moderatore sul caso incagliato.
Collaudato: 2674 prove verdi (73 nuove — l'endpoint girato DAVVERO su
un database gemello, col dump di `ordini` identico prima e dopo) e
VENTUNO MUTAZIONI del codice una per riga sorvegliata, ognuna rossa da
sola; la tortura ha trovato due sentinelle mie che non potevano
fallire, riscritte. Più il giro dal vivo sul server locale, che ha
mostrato la coda coi due `locked` veri fermi da 24 e 22 giorni,
entrambi «🔕 mai sollecitato» — cioè la popolazione scoperta si è
presentata al primo giro — il 403 al non-moderatore, la riga nell'ordine
del compratore nei due temi e il pannello del caso incagliato, con zero
errori JS e il database di collaudo intatto.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuno stato nuovo, e la leva ha il default nel codice. DA GUARDARE
al primo giro: chi c'è già dentro la coda — se compare un ordine che
nessuno ha mai sollecitato, quello è il caso per cui il cantiere
esiste.

Il mono sconta, punto (12 ago 2026, decisione di Andrea che ROVESCIA
PER INTERO il «il mono non sconta mai» del 6 ago): lo sconto carrello
vale su ogni acquisto — tre copie dello stesso articolo dalla scheda
sono tre pezzi, una soglia a valore superata è superata anche con un
oggetto solo, tutti e due i criteri e tutte e due le valute. Il motivo:
è quello che la gente si aspetta (Andrea ci si è stupito due volte in
due giorni), e l'invito del carrello diceva già «✅ Sconto nel conto»
su un carrello a una riga che poi non scontava — la mezza regola era
una bugia in vetrina, e la mezza via «carrello sì, scheda no» è quella
SCARTATA: le due porte sono lo stesso endpoint, e costruire la
differenza farebbe dipendere un prezzo da quale JSON manda il client.
Vedi Architettura, «IL MONO SCONTA, PUNTO», per il censimento completo:
i quattro chiamanti di `_sconto_pacco`, la divisione a ritroso che
riaggiunge `sconto_sats` nelle sue TRE copie (`_righe_ordine`, la
ripresa, la riga client) sorvegliate dal CENSIMENTO
`prove_divisione_a_ritroso`, `articolo_sats` diventato NETTO anche sul
mono, il controllo «mono scontato» della ronda sostituito da due
invarianti veri (i controlli salgono a 16), i quattro testi-antidoto
riscritti con le sentinelle rovesciate, e la campagna una-tantum
`avvisa_sconto_su_mono` ai venditori con la regola già accesa (timbro
globale in `timbri`, il testo dice la LORO regola e come spegnerla).
Collaudato: 2830 prove verdi in CI (erano 2793 prima del cantiere, con
le rovesciate e le estese 2→4 percorsi), DODICI MUTAZIONI una per riga
sorvegliata — ognuna rossa da sola, e una ha smascherato una mutazione
che sbagliava bersaglio (il replace prendeva la SELECT identica di
`_compra_set`: la tortura va mirata quanto le sentinelle) — più il
collaudo eseguibile su DB usa-e-getta (117 verdi, con LNbits VERO e le
bolt11 decodificate al sat): LA PROVA REGINA preventivo == compra sul
mono scontato al filo della soglia nei due criteri e nelle due valute,
l'identità di bilancio riletta dal database, la divisione a ritroso
esatta anche sul ramo della RIPRESA, il digitale che sconta, la lampo
che fa scendere sotto soglia, il cambio muto senza 503 nuovi, la
regola cambiata fra preventivo e acquisto nei due versi, la ronda che
tace e la regressione del venditore senza regola. Più il giro visivo
via CDP a 375px: pagina Paga e paySheet con la riga «Sconto carrello»
e i totali che quadrano a mano (30.000 → −3.000 → 27.000), il cassetto
e la riga del negozio coi testi nuovi.
IN PRODUZIONE basta il deploy: ZERO colonne, ZERO migrazioni, ZERO
leve nuove (`sconto_sats`/`sconto_percento` esistevano già su `ordini`
a DEFAULT 0). Al primo battito dell'orologio parte la campagna — una
volta sola, il journal nomina i destinatari — e DA GUARDARE sono: quel
journal (i ~5 negozi con la regola accesa), il primo mono scontato
vero dentro Telegram con la bolt11 confrontata su LNbits, e che la
ronda TACCIA — se «aritmetica del mono» suona, si guarda l'ordine
prima della funzione.
E lo stesso giorno L'INVITO DELLE DUE PROMESSE nella pagina Paga
(chiesto da Andrea in due tempi: prima lo sconto — nel carrello c'era,
lì no — poi la spedizione gratis, che deve parlargli uguale): pillole
affiancate in una fila, ognuna col suo stato — «Ancora N → …» sotto
soglia, il verde «nel conto» quando scatta — coi numeri del SERVER, la
cifra a valore da `cifraSoglia`, il cambio muto detto invece che
taciuto e gated sulla valuta di OGNUNA (chiuso il bug preesistente del
flag combinato che sospendeva una spedizione in sats per colpa di uno
sconto in euro). Il verde della spedizione convive con la riga
«gratuita» del conto: il perché e il cosa, deciso a schermo. Più i
badge di «Altri oggetti» a cifra nuda («di articoli» resta dov'è una
misura), e la posizione dei badge sopra il bottone RICONFERMATA
MISURANDO dopo un tentativo vero di rovesciarla (il difetto dello
sticky torna, fotogramma agli atti — vedi la voce). Verificato con 9
sentinelle nuove (2838 verdi) e gli screenshot 320/375 × chiaro/scuro,
sotto/sopra soglia e stato misto.
E il ritocco del CARRELLO (12 ago 2026, sempre quel giorno): il
sottotitolo dice il perimetro («articoli dello stesso venditore»)
invece del modello, e testata+badge restano appiccicati in cima
mentre si scorre — misurato PRIMA di lasciarlo, com'era chiesto:
137px a 375 (17%) e 158px a 320 (19%) collo stato più alto, sotto i
178 (23%) del precedente scartato in «Altri oggetti». 5 sentinelle
nuove (2843 verdi), screenshot chiaro/scuro in cima e a metà scroll.
E LO STEPPER NELLA PAGINA PAGA (12 ago 2026, a chiudere la giornata):
il ± accanto al titolo dell'articolo — l'invito dice «ancora 1 pezzo»
e il pezzo si aggiunge lì. Ogni tocco rifà il preventivo; l'anti-race
è la riassegnazione di `acqDati` sulla guardia che c'era già (mai un
debounce), il velo d'attesa è RITARDATO di ~180ms (secco lampeggiava:
la riserva di Andrea, guardata a schermo con 800ms di latenza
artificiale), l'errore su un ± ripiega sull'ultimo conto buono invece
di buttare la pagina, e `setQta(0)` sincronizza la scheda al ritorno
(il difetto trovato dal vivo: l'indietro non ri-renderizza). 12
sentinelle nuove (2855 verdi), la raffica da 5 tocchi provata dal
vivo — vince l'ultima chiesta — e il limite dello stock in silenzio,
come nella scheda. Vedi «LO STEPPER NELLA PAGINA» nella voce della
pagina d'acquisto.

Il punto di ritiro diventa il default, e il campo diventa un bottone
(ago 2026, cambio di rotta di Andrea in due tempi: prima «il default
è il punto — default e "Consigliato" devono dire la stessa cosa», poi,
davanti all'argomento-contro trovato in sola lettura PRIMA di toccare
— col campo sempre aperto la pagina diventava un modulo da compilare —
il bottone che rende il default sostenibile). Tre pezzi: la precedenza
di `viaDefault` passa a punto → casa → ritiro → digitale (la
selezionata su «entrambe» diventa la TERZA della lista); il campo a
testo libero esce dalla pagina e lo espande «📍 Indica il punto di
ritiro» — riga espansa e non foglio, stato in `acqDati.puntoAperto`,
col punto scritto la riga compatta lo mostra col «Cambia» e il campo
riapre PRECOMPILATO, e le due guardie di «Paga»/⚡ a punto vuoto
APRONO il cassetto prima del fuoco; e la pillola 🚚 della spedizione
gratis tace sulla via ritiro/codice online — rovescia il 12 ago, ed è
legato al default: chi ci sta ci è arrivato toccando, la 🎁 resta su
ogni via. Il campo dentro l'ordine non cambia di una riga, e il VARCO
MAPPA resta vero parola per parola. Vedi Architettura: «IL DEFAULT
DELLA VIA È IL PUNTO DI RITIRO», «E DAL QUINTO GIRO IL CAMPO STA
DIETRO UN BOTTONE», e il gate nella voce dell'invito delle due
promesse. Collaudato: 2875 prove verdi (13 nuove, più la sentinella
della precedenza riscritta), SETTE mutazioni una per riga sorvegliata
— precedenza rigirata, gate tolto, gate copiato sulla 🎁, apertura
dopo il toast, esc() tolto dalla riga compatta, flag perso da un
costruttore, campo non più precompilato — ognuna rossa da sola; e il
giro dal vivo via CDP sul server locale, 71 verifiche su 320/360/375 ×
chiaro/scuro: default punto con la radio terza della lista, campo
chiuso senza autofocus e senza overflow, bottone→campo→riga
compatta→«Cambia» con l'indirizzo da 120 caratteri che cede coi
puntini e il «Cambia» in vista anche a 320, «Paga» a vuoto che apre il
cassetto senza NESSUN POST, gate 🚚 nei quattro stati delle vie, zero
errori JS e zero ordini nati dal giro. La guardia NWC a punto vuoto è
coperta dalle sentinelle ma non provata dal vivo (nessun wallet nel
collaudo), dichiarato. IN PRODUZIONE basta il deploy: nessuna colonna,
nessuna leva, nessuna rotta — solo client. DA GUARDARE dal vivo dentro
Telegram: che all'apertura della pagina la tastiera NON si alzi, e il
primo ordine al punto nato passando dal bottone.

La fila delle promesse parla una lingua sola (13 ago 2026, chiesto da
Andrea in tre punti): la veste di Paga — righe a tutta larghezza —
arriva su «Altri oggetti» e sul carrello; il carrello corre la STESSA
barra di Paga (riempimento, viraggio, scattata piena e accesa: tre
«solo di Paga» rovesciati in un giro solo); e il totale della barra
del carrello mostra lo SCONTATO col lordo barrato, come l'unitario in
Paga. Le tre cose da tenere: 1) la MISURA resta al LORDO — al giudice
`statoScontoPacco` (nuovo, unico: lo chiamano badge e totale) va il
totale così com'è, o lo sconto si spegnerebbe da solo — e il netto è
solo RESA con la formula del server; con lui è morta la coda «nel
conto» (diceva di aspettare il conto perché il totale restava al
lordo, e ora scende da solo: la sentinella conta ZERO code). 2) La
barra del carrello corre coi numeri del CLIENT — gli stessi del testo
«Ancora N», nessuna pretesa nuova, la fascia del cambio dichiarata sul
giudice — sui FERRI CONDIVISI `barraPromessa`/`barreCattura`/
`barreCorri`, estratti da renderAcquisto: una seconda stesura della
corsa è il posto dove il prossimo «si anima solo la spedizione»
tornerebbe a nascondersi. 3) In «Altri oggetti» cambia SOLO la veste
(classe `.fila-promesse` sui tre contenitori, un posto solo): niente
barra e niente verde — lì la promessa è una regola, non un verdetto
sul carrello corrente — e il costo dichiarato è la coppia sempre in
colonna, ~30px in più col negozio che promette due cose.
Collaudato: 2928 prove verdi (erano 2923 prima del cantiere, con le
rovesciate — «nel conto» a zero, la tenue che non veste più nessuno,
le OTTO pillole con la chiave della corsa) e NOVE mutazioni una per
riga sorvegliata, ognuna rossa da sola — la tortura ha trovato una
sentinella che non poteva fallire (il conteggio dei chiamanti dei
ferri contava anche la chiamata COMMENTATA: riscritta sulla riga
intera, la lezione del reaper, terza volta). Più il giro CDP a
320/375 nei due temi: fill 33%/10% misurati sulle pillole vere,
scattata accesa, totale 14,89 € col 16,54 barrato (−10% al floor),
doppio verde a carrello pieno, Paga byte-per-byte uguale e zero
errori JS. IN PRODUZIONE basta il deploy: nessuna colonna, nessuna
leva, nessuna rotta — solo client. E LA VIA DEL LOCKER RESTA SENZA
SPAZI (13 ago 2026, decisione di Andrea presa sui numeri): la barra
spaziata («Spedizione a locker / punto di ritiro») era stata chiesta,
MISURATA prima di applicarla — sta su una riga a 360/375, ma a 320 va
a capo (21→43px: la colonna lì è tappata a 258px e il testo spaziato
ne chiede ~264) — e RITIRATA davanti alla misura: due righe a 320 per
due spazi non le valgono, e uniformare gli altri otto siti di prosa
della formula costerebbe più di quanto renda. Chi la riproponesse
rimisuri prima a 320, che è la larghezza dove la via si gioca la riga.

L'invito che non si può accettare, e il verde in vetrina (ago 2026, due
difetti opposti sulla stessa famiglia di badge). Nella pagina PAGA
l'invito «Ancora 2 pezzi → −10%» compariva anche su un annuncio che ne
ha uno solo: adesso la pillola sotto soglia sparisce quando nessuna
quantità acquistabile arriva alla soglia, e quella SCATTATA non si
tocca — un fatto non è un invito. In VETRINA il contrario: un articolo
che da solo fa scattare lo sconto carrello non lo diceva da nessuna
parte, e adesso il prezzo parla verde col contorno. Le due decisioni di
Andrea: «🚚 gratis» dice il FATTO in tutti e due i casi (gratuità
dichiarata o soglia raggiunta) e resta NERA — chi sfoglia vuole sapere
se paga la spedizione, non perché — e il verde è dello SCONTO e basta,
l'unica promessa che in card non aveva voce. Vedi Architettura, «IL
VERDE DELLO SCONTO IN CARD» per la precedenza e la coppia da tenere
d'occhio, e «L'INVITO CHE NON SI PUÒ ACCETTARE» per la formula che
risponde con i giudici del denaro invece che con un terzo giudice.
Collaudato: 2967 prove verdi (30 nuove) e QUATTORDICI mutazioni una per
riga sorvegliata — ognuna rossa da sola, e la tortura ha smascherato
una sentinella MIA che non poteva fallire (guardava la riga della
pillola mentre una guardia di troppo si aggiunge a quella della
condizione: adesso è un censimento, e conta la FORMA della guardia e
non la parola, che vive anche nei commenti). Più un collaudo eseguibile
su DB usa-e-getta col server VERO via TestClient (23 verdi): stock 1
sotto e sopra soglia, 3 contro 5 pezzi, l'accordo che abbassa il tetto,
il set che non afferma niente, e la regressione che il conto non si
sposta di un sat. E il giro visivo via CDP a 320/360/375 nei due temi —
le quattro card in fila, i tre segni ingranditi, e la pagina Paga dal
vivo nei tre casi — con zero errori JS.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta, e il client vecchio in cache non vede le
due chiavi nuove e si comporta come oggi. DA GUARDARE al primo giro: le
card che il supplemento faceva mentire — quelle con base 0 e
supplemento pieno perdono il «🚚 gratis», ed è la correzione — e il
primo annuncio che da solo fa scattare lo sconto, guardato accanto a
un'asta.

Lo sconto carrello si vede in vetrina (ago 2026, quattro cose chieste da
Andrea in un colpo): la card in sconto mostra il prezzo SCONTATO col
listino barrato e un badge verde in alto a sinistra — lo stesso
meccanismo della lampo, senza il fulmine, perché ⚡ vuol dire «a tempo»
e questo non scade — e lo stesso vale nella scheda; nei Filtri nascono
«🚚 Spedizione gratis» e «🎁 In sconto», e «In offerta» diventa
«Offerta a tempo» (con due sconti in elenco quella parola da sola non
distingueva più niente). LA REGOLA, nella forma più semplice trovata
(Andrea): è il CRITERIO a dire dove vale lo sconto — a VALORE conta la
cifra, quindi vale anche su un articolo solo; a PEZZI conta il numero,
quindi serve arrivare a più pezzi. Nessuna eccezione da ricordare. Il
prezzo mostrato ha un giudice solo (`prezzoMostrato`) e la lampo vince,
che è la regola del conto; «Ne resta 1» adesso si spegne per lo sconto,
e quella riga ROVESCIA il giro prima — era vera finché il verde era
solo un colore, ha smesso di esserlo quando ha preso un badge. Vedi
Architettura, «LO SCONTO CARRELLO SI VEDE IN VETRINA», anche per i due
filtri, che promettono quello che la card mostra e per questo rifanno
il verdetto lato SERVER — l'aritmetica in due funzioni sole, incrociata
in CI col giudice Python, perché un filtro che sbaglia non fallisce:
mostra la card sbagliata.
Collaudato: 3003 prove verdi (36 nuove) e DICIOTTO mutazioni una per
riga sorvegliata, tutte rosse — la tortura ha trovato l'ennesima
sentinella cieca (contava il NOME `_no_lampo` invece del suo contenuto,
quindi un `_no_lampo = ""` la lasciava verde). Più il giro dal vivo a
320/360/375 nei due temi con le quattro card in fila, la scheda, e i
due filtri chiesti al server vero — ed è lì che è saltato fuori il caso
che leggendo il codice non si vedeva: il filtro «Spedizione gratis»
pescava un'ASTA il cui prezzo di base superava la soglia. Da lì la
guardia dell'asta è entrata anche in `spedGratisQui`.
E il giorno dopo il BUG DELLE COMBINAZIONI (segnalato da Andrea):
spuntandone due la vetrina restava vuota. La causa non era aritmetica
ma STRUTTURALE — lampo, asta e sconto sono stati mutuamente esclusivi
per costruzione, quindi in AND l'intersezione è vuota per definizione
— e adesso le OCCASIONI si uniscono in «o», mentre la spedizione
gratis resta un asse ortogonale in AND. Riproducendo è saltato fuori
un secondo difetto che leggendo non si vedeva: il filtro «Spedizione
gratis» escludeva le LAMPO, e sbagliava due volte, perché quella
parola convive con la lampo e sulla card la soglia si misura sul
prezzo SCONTATO — quindi saltava proprio gli annunci su cui il segno
c'era. Più lo spostamento della spunta accanto a «Spedizione», che
è la sua famiglia. La composizione della WHERE vive ora in due
funzioni pure, e la prova gira le 16 combinazioni dei quattro filtri
su un database gemello: UN FILTRO SOLO CHE FUNZIONA NON GARANTISCE CHE
DUE INSIEME FUNZIONINO, ed è esattamente quello che era successo — le
prove del giro prima ne guardavano uno alla volta e passavano tutte.
3015 verdi, sette mutazioni su sette rosse (l'ultima ha fatto nascere
la sentinella sull'ORDINE delle spunte, che non c'era), e la
coerenza card↔filtro verificata dal vivo: le card che scrivono
«🚚 gratis» sono esattamente quelle che il filtro pesca.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva nuova. DA GUARDARE al primo giro: un negozio con lo sconto
a VALORE acceso — le sue card sopra soglia cambiano prezzo in vetrina,
ed è la cosa più visibile del cantiere.

Il conteggio dei barattoli torna al proprietario (ago 2026): sui propri
annunci il barattolino non nasceva, e col bottone se ne andava il numero
— cioè proprio il dato che al venditore interessa. Adesso c'è in tre
posti: la riga di «📋 I tuoi annunci», la scheda del proprio annuncio (la
frase intera, che insegna cosa vuol dire il numero) e la CARD, dentro la
pastiglia del barattolino. Soglia UNO (decisione di Andrea: al
proprietario «1 persona» è un dato vero) e lo zero non scrive niente. IL
DATO ERA GIÀ IN MANO AL CLIENT — il server lo conta su tutte le righe
senza guardare il venditore — quindi zero query, zero campi, zero
server: il cantiere è solo client.
IN DUE GIRI, e il secondo va letto col primo. Nato col numero vestito da
DATO e il barattolino ancora assente (un cerchietto che non fa niente si
legge come rotto), è stato ROVESCIATO da Andrea: **il bottone c'è, e il
tocco SPIEGA** — stessa resa degli annunci altrui, e il foglio di casa in
modo AVVISO dice «non puoi mettere un tuo annuncio nel barattolo». Col
bottone il numero è tornato nella sua pastiglia e la riga meta della card
è quella di sempre, comune compreso: lo scambio col comune del primo giro
non serve più, e con lui è sparito il residuo di 1,3px oltre il bordo.
Restano la riga di «I tuoi annunci» e la frase nella scheda. Vedi
Architettura, «E IL PROPRIETARIO LO VEDE», anche per l'angolo della card
che sui propri esauriti resta del rifornimento. E la regola vale ANCHE
DALL'API (decisione di Andrea: una regola che vale solo nel client è
mezza regola) — `toggle_preferito` rifiuta il proprio annuncio, ma nel
ramo dell'INSERT, così una riga nata da un client di ieri si può ancora
togliere.
Collaudato: 3064 prove verdi (34 nuove) e mutazioni una per riga
sorvegliata; più il giro dal vivo via CDP a 320/360/375 nei due temi e
dai due lati — col compratore la vetrina è quella di ieri, e sul proprio
il tocco apre il foglio con **zero POST** partite e i preferiti
invariati. Nel primo giro è saltato fuori il difetto che ha insegnato di
più: un commento CSS aperto con «\*» invece di «/*» si era mangiato la
regola dopo, `.nota-punto` compresa — da lì è nata `prove_commenti_css`.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta.

E l'ORDINA torna a TRE VOCI (ago 2026, decisione di Andrea): più
recenti e i due prezzi. «Offerta a tempo» e «All'asta» erano
ordinamenti VERI — per scadenza, chi finisce prima in testa — ma
implicavano il filtro, che c'è già fra le spunte: la stessa cosa in due
posti. L'urgenza non si perde, la EREDITA il filtro quando l'occasione
spuntata è UNA sola, e il campo dice l'ordine effettivo invece di
mentire. Il server non cambia di una riga. Due difetti trovati DAL VIVO
e non leggendo: il campo non si ridisegnava al cambio delle spunte, e
la radice 🔨 Aste si faceva scavalcare da una scelta esplicita rimasta
in memoria — la pagina della gara finiva ordinata per prezzo. Otto
mutazioni su otto rosse, e lo stato dell'ordinamento vive per la
SESSIONE: al deploy si riparte da «Più recenti», nessuno resta bloccato
su una voce che non esiste più.

La riga dello sconto nel form diventa viva (ago 2026, chiesto da
Andrea): chi pubblica un articolo che da solo supera la soglia del suo
sconto carrello lo legge mentre scrive il prezzo, con le due cifre,
invece di scoprirlo da una vendita. Non un blocco, un avviso. Il caso è
nato col mono che sconta — prima un articolo solo non scattava mai. Il
verdetto NON si ricalcola nel form: `scontoScatta` è il cuore estratto
da `scontoQui`, così la riga e la card non possono dire due cose
diverse sullo stesso prezzo. Vedi Architettura, «E QUELLA DELLO SCONTO
È VIVA», per il momento di quiete coi suoi numeri, per la riga che tace
sull'asta e per la risposta alla domanda sulla modifica (parla uguale,
ed è lì che serve di più).
Collaudato: 3097 prove verdi (25 nuove) e **DICIASSETTE MUTAZIONI** una
per riga sorvegliata, ognuna rossa da sola — e sono state loro a
trovare due sentinelle MIE ingannabili da una copia morta, riscritte.
Più il giro DAL VIVO col server locale, che è la parte che il testo non
poteva dire: digitando davvero, carattere per carattere, la riga si
riscrive UNA volta sola a 425ms dall'ultimo tasto, e resta una sola
anche a un tasto ogni mezzo secondo, correggendosi all'indietro e
esitando sul filo — dove senza quiete sarebbero state cinque. Più il
listino in euro (79,20 € invece di 99,00), il cambio muto nei due versi,
l'asta che la fa tacere, e il giro pubblica → riapri in modifica, che è
il caso della domanda. Screenshot a 320/360/375 nei due temi: tre righe,
nessun overflow. UNA LEZIONE DI METODO: il primo giro di sonde diceva
che la riga non scattava MAI — era rotta la sonda, che non normalizzava
gli spazi mentre il testo va a capo a metà frase. Una verifica che
fallisce va guardata prima di crederle.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client. DA GUARDARE al primo giro:
il primo venditore con lo sconto a VALORE acceso che pubblica sopra
soglia.
L'avvio non mostra più roba che non c'entra (ago 2026, segnalato da
Andrea: «aprendo l'app si vede per un istante una vetrina con oggetti
che non c'entrano»). Due difetti nello stesso mezzo secondo, tutti e
due REGISTRATI prima di toccare qualcosa — Chrome headless via CDP,
screencast fotogramma per fotogramma più un diario in pagina che a
ogni rAF dice cosa c'è nel DOM: 1) il primo fotogramma della home ERA
IL CARTELLO (5 giri su 6 a 8 Mbps, ~110 ms, l'elenco puntato dei 24
annunci coi prezzi di listino); 2) le pillole delle categorie
nascevano dal SEME DELLA DEMO e duravano ~280 ms, cioè più a lungo.
La griglia invece era pulita — passa da 0 a 30 in un colpo coi dati
veri — quindi il secondo sospetto («la vetrina del giro precedente»)
è stato ESCLUSO, non curato a caso. Vedi le voci loro per le due cure
(`#cartello{display:none}` con la distinzione dal testo nascosto, e
il giudice unico `contaCategorie`) e per la VIA D'USCITA DICHIARATA
CHE ERA SBAGLIATA — «legare la rimozione al primo `go()`»: provata, e
`go()` sulla home non viene chiamato mai.
Collaudato: 3114 prove verdi (11 nuove, una ROVESCIATA — quella sul
`#cartello:empty`, che il display:none copre a maggior ragione) e
CINQUE MUTAZIONI del codice una per riga sorvegliata — cartello che
torna a dipingersi, guardia della conta tolta, le due superfici che
si ricontano il seme per conto loro, rimozione al parse sparita —
ognuna rossa da sola. Più i fotogrammi rifatti dopo la cura: nessun
frame con l'elenco (3 giri su 3), e le pillole che vanno da «Tutto»
a quelle vere senza passare dalle finte. IN PRODUZIONE basta il
deploy: nessuna colonna, nessuna leva, nessuna rotta, e sw.js non si
tocca (nessun HTML sta in dispensa). DA GUARDARE dal telefono, che è
l'unico posto dove il difetto si vedeva: l'apertura dentro Telegram e
in PWA installata.
E IL SECONDO GIRO, dal telefono di Andrea («lo scatto c'è ancora,
identico a prima»): rifatti i fotogrammi sul codice nuovo, IN
PRODUZIONE — il cartello era morto davvero (altezza 0 a ogni giro),
e a dipingersi era un'altra coppia: la FASCIA del rodaggio che si
infilava sopra la griglia a card già dipinte (~56px di salto, 170 ms
dopo le card) e le card che nascevano SENZA foto per poi riempirsi —
due ricambi nello stesso quinto di secondo, ed erano lì da prima del
cartello: due difetti sovrapposti, se n'era tolto uno. Le due cure
(decisione di Andrea: queste due, e NIENTE sagome-fantasma alla
Vinted finché l'attesa non torna a dare fastidio): la fascia si
disegna PRIMA delle card col fetch partito in testa all'avvio (vedi
la voce sua, con la trappola della cache-promessa), e `renderGrid`
parte SUBITO dopo `loadListings` invece che dopo anche ordini,
preferiti, offerte e puntate — quattro giri di rete sequenziali che
alla vetrina non servivano a disegnare, misurati −271 ms in locale a
40 ms di RTT (su un telefono ~0,5-1,5 s). Chi arriva dopo riallinea
IN PLACE (il pattern dichiarato dei barattolini); l'unico dato
tardivo che cambia una card intera è un ACCORDO accettato su un
annuncio in vetrina, e lì — e solo lì — la griglia si ridisegna.
Il pop-in delle foto resta e non ha una cura da questo lato: la
`.ph` ha già la sua altezza (zero shift, solo il contenuto che
arriva) e dalla seconda apertura la cache HTTP di un giorno lo rende
istantaneo — con la fascia ferma smette di leggersi come un
ricambio. Collaudato: 3121 prove verdi (7 nuove) e SEI mutazioni una
per riga sorvegliata, tutte rosse; fotogrammi rifatti sui DUE avvii
(autenticato, e anonimo forzando un 401 su /api/me via CDP): il
primo fotogramma con la griglia ha già la fascia sopra, e dopo le
card non si muove più niente (`#grid` sparito dalle sorgenti di
layout-shift). IN PRODUZIONE basta il deploy: solo client. DA
GUARDARE dal telefono: se la griglia vuota che resta (~1-1,5 s) dà
ancora fastidio, il passo dichiarato sono le sagome-fantasma
(~40-60 righe, stimate e non fatte apposta).
Il documento di ritiro nella busta (ago 2026, dal campo): al locker il
corriere manda un PDF o un QR, e un PIN si trascrive mentre un QR no —
il venditore lo carica dentro l'ordine. È l'ALTRA strada per dare il
codice e non un'aggiunta (decisione di Andrea): il nome del
destinatario serve sempre, poi basta uno dei due. La riga che governa
tutto il resto: **chi ha quel file ritira il pacco**, quindi non è una
foto ma una credenziale — niente `foto/`, niente URL pubblico, byte
cifrati in `buste/` e una rotta autenticata che decifra al volo, con le
regole della busta riga per riga (solo le due parti, il moderatore mai,
GET puro, `no-store`). Vedi Architettura, «IL DOCUMENTO DI RITIRO»,
per la whitelist di FORME (il tipo lo dicono i byte, e qui quel tipo
torna indietro come Content-Type) e per la limitazione dichiarata sul
PDF, che si scarica invece di aprirsi in una scheda.
Collaudato: 2892 prove verdi (33 nuove, erano 2859 — le stesse 3
rosse di prima e di dopo, che sono `websocket` non installato qui) e
soprattutto DODICI MUTAZIONI del codice, una per riga sorvegliata:
cache rimessa, documento scritto in `foto/`, byte nudi sul disco,
guardia allentata sulla rotta dei byte, whitelist tolta, «si conserva»
tolto, vecchio file non cancellato, busta vuota ammessa, ripulitura del
nome tolta, byte serviti ancora cifrati, 503 tolto, tipo sbagliato —
ognuna diventa rossa da sola. La rotta dei byte GIRA per davvero nel
banco di prova (Response di cartone, il resto è il pezzo vero): byte
identici a quelli caricati, estraneo e inesistente indistinguibili, e
il dump del database uguale prima e dopo due letture. UNA PROVA ERA
VACUA e l'ha detto la tortura, non la rilettura: il caso della
ripulitura del nome usava un percorso, che lo toglie già `basename` —
ora porta una virgoletta e un a-capo, che solo la regex leva.
NON COLLAUDATO QUI, e va detto: su questa macchina non ci sono
`fastapi` né `anthropic`, quindi il giro end-to-end col server acceso e
la prova in browser NON sono stati fatti. DA FARE al primo deploy: un
ordine vero al punto con un QR caricato dentro Telegram — che
l'immagine si veda in pagina sul telefono del compratore, e che il PDF
finisca fra i suoi file.
Il canale diventa la vetrina (ago 2026, chiesto da Andrea insieme al
canale «Barattolo Vetrina»): tutti gli annunci nuovi nel canale invece
di uno per venditore a settimana, gli sconti lampo raccontati lì, e il
riepilogo del lunedì con annunci, ordini e i tre più venduti. Le
quattro decisioni: UN canale solo (non un secondo posto da tenere
allineato), freno spento ma col ritmo che si stringe **dal bot** e non
dal config (`/vetrina tutto | giorno | settimana`), riepilogo pubblico
che tace se la settimana è magra, e NIENTE link al canale dentro l'app
— lì dentro per ora c'è solo Andrea, e prima vuole guardarlo. Vedi
Architettura, «IL RITMO LO DECIDE IL BOT», per il nome-non-i-numeri nel
database, per il freno che si RICEVE invece di rileggerlo a metà
drenaggio, e per le due imperfezioni dichiarate (il post della lampo
senza ✅ se l'annuncio si vende, e il turno del riepilogo che si consuma
anche quando tace — che è il contrario del termometro).
Collaudato: 2961 prove verdi in `prove.py` (erano 2794 — le pure dei
giudici, il recinto delle impostazioni diventato un CENSIMENTO delle
chiavi, l'elenco di chi parla col canale che ora si NOMINA invece di
contarsi, `_conta_settimana` su un database di cartone coi mono **e** i
set insieme, e il riepilogo girato DAVVERO tre volte su tre ambienti
diversi con lo stesso database sotto — tre deploy, un post solo) più
**VENTUNO MUTAZIONI**, una per riga sorvegliata, ognuna rossa da sola.
LA TORTURA HA TROVATO TRE BUCHI VERI, ed è la parte da tenere: la
soglia dell'aggregato che non era verificata da nessuna prova, la UNION
dei set che si poteva togliere in silenzio, e — la peggiore — il
pannello delle leve, dove il commento dello stub PROMETTEVA il
controllo del ritmo effettivo e nessuna asserzione lo faceva. Più un
collaudo eseguibile su DB usa-e-getta (27 verdi) che fa girare il
drenatore VERO e `promo_lampo` VERA: due venditori a «settimana» → due
post, tre a «tutto» → tre, quattro in una finestra → l'aggregato che
non nomina nessuno, il negozio in ferie e l'importato che restano
fuori, e il titolo cattivo che esce scappato coi grassetti pari.
NON COLLAUDATO QUI: manca `fastapi`, quindi il giro col server acceso
non si è fatto (il comando `/vetrina` è stato però eseguito sul pezzo
vero, coi quattro casi e l'estraneo che non cambia niente).
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione — la
tabella `impostazioni` e quella dei `timbri` esistono già, e le tre
leve nuove hanno il default nel codice. POI, NELL'ORDINE: il bot
amministratore del canale, `/canale -1003975076313` (deve arrivare il
messaggio di prova), `/vetrina` per vedere dov'è, `/vetrina tutto`, e
un annuncio vero da guardare. DA GUARDARE il primo lunedì: il
riepilogo, **una volta sola** anche con un deploy in mezzo.

L'indirizzo di casa dentro l'ordine (ago 2026): chi sceglie la
spedizione a casa scrive l'indirizzo al momento dell'acquisto, viaggia
cifrato come il codice della busta, lo legge solo il venditore e una
scopa lo cancella: SUBITO alla conferma di ricezione (garantiamo la
transazione, non la consegna), e dopo dieci giorni per gli ordini che
si chiudono senza quella conferma. Prima passava in chat
privata — e chi non ha username Telegram né npub non poteva darlo a
NESSUNO: lo stesso caso vero che ha fatto nascere la busta, sull'altra
strada. Le quattro decisioni di Andrea (campi separati per il
riempimento automatico, finestra di grazia, il moderatore che non
legge mai, la voce nella pagina pubblica) e le sei righe da non
ammorbidire stanno in Architettura, «L'INDIRIZZO DI CASA» — con la
lezione che vale oltre il cantiere: **la pagina «Il pagamento
protetto» non diceva quello che sembrava**, le parole *recapito,
indirizzo, dati personali* non ci comparivano MAI, e la frase «noi non
raccogliamo dati veri» viveva solo in un commento del codice. Nessuna
promessa è stata smentita; ne è stata scritta una che non c'era.
Collaudato: 3468 sentinelle (56 nuove) e DODICI mutazioni una per riga
sorvegliata, ognuna rossa da sola; gli endpoint girati per davvero su
sqlite in memoria (il GET non scrive niente, estraneo e ordine
inesistente rispondono identico, la scopa è idempotente e non tocca né
`aggiornato` né gli ordini vivi); `collaudo_conto.py` resta 55/55 e le
funzioni del conto e delle tre uscite del denaro sono INTATTE byte per
byte; più il giro dal vivo in Chrome headless dai due lati, che ha
trovato quel che la lettura non vedeva — il pannello che diceva «il
pacco è partito» su un ordine nemmeno pagato, e le label dei campi
nate inline dentro `.payout`.
E UNA PROVA NUOVA CHE MANCAVA, `prove_avvio_client`: scrivendo questo
cantiere ho ucciso l'app intera con un ReferenceError da temporal dead
zone — 3400 sentinelle verdi e `node --check` pulito, perché la
sintassi era perfetta ed era l'esecuzione a morire. La prima stesura
della prova passava anche col guasto dentro, e l'ha detto la tortura.
IN PRODUZIONE basta il deploy: le sei colonne nascono da sole
(additive, tutte a 0) e la leva ha il default nel codice. DA GUARDARE
al primo giro: il primo ordine vero a casa dentro Telegram — che il
venditore trovi l'indirizzo nel suo pannello — e, al primo affare
confermato, la riga «🏠 Indirizzi cancellati: 1 alla conferma» nel
journal entro dieci minuti.
DA PROVARE SUL TELEFONO, che qui non si può: se il riempimento
automatico degli indirizzi funziona dentro la WebView di Telegram.

Il codice di ritiro dentro il bottone (ago 2026, tre cose dal campo):
la pagina non salta più toccando «Mostra», il codice nasce dove stava
il dito invece che altrove, e toccandolo si copia. Le due prime sono
la stessa cura — il salto era `openOrder` (verificato con una spia su
`window.scrollTo`: lo stack diceva mostraBusta → openOrder → go →
scrollTo(0,0), da y=578 a y=0, e di `focus()` NESSUNA, quindi il
sospetto del `preventScroll` non c'entrava), e non passare più da lì è
ciò che permette al piatto di nascere nello slot del bottone. Il
gesto cambia mestiere e lo dice in una parola: 👁 → 📋, «Tocca per
copiare», `aria-label` nuovo. Vedi Architettura, «IL CODICE COMPARE
DENTRO IL BOTTONE», anche per l'anello della rivelazione (mezzo
secondo, una volta sola, spento da reduced-motion) e per il piatto del
venditore in rilettura, che chiude un tocco che prima non faceva
niente. Collaudato: 3633 prove verdi (16 nuove, fra cui `piattoCodice`
fatta GIRARE con node sui quattro casi) e SEDICI MUTAZIONI una per
riga sorvegliata, ognuna rossa da sola — e la tortura ha trovato una
sentinella che ESPLODEVA invece di essere rossa, portandosi dietro le
prove dopo di lei. Più il giro dal vivo via CDP: scrollY 578 → 578 con
zero chiamate a scrollTo, top del bottone e del piatto identici alle
tre larghezze, il tocco che copia col suo toast, l'anello che parte
una volta e non riparte a un ridisegno, e i tre rami (compratore,
venditore che scrive, venditore che rilegge) più il caso del solo
documento. Screenshot a 320/360/375 nei due temi, prima e dopo, più il
codice LUNGO (il link di un QR), che va a capo senza sbordare.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna rotta, nessuna
leva — solo client.

I font in casa e la pagina «I tuoi dati» (ago 2026, due commit): prima
si è chiuso il debito — finché la pagina chiedeva i font a Google,
l'IP e lo user-agent di OGNI visitatore arrivavano a un terzo a ogni
apertura, e una pagina sulla privacy avrebbe dovuto dichiararlo — e
poi si è scritta la pagina. Sei `.woff2` in `vendor/font/` con la loro
rotta a whitelist, i pesi dichiarati uno per uno perché la resa non
cambi di un pixel, il ramo cache-first verso Google tolto dal service
worker (VERSIONE a v5). Poi `/privacy`: cosa raccogliamo, per quanto,
chi legge cosa, cosa NON raccogliamo — e le tre affermazioni scomode
per intero (l'indirizzo che resta se l'ordine non si chiude mai;
«cifrato» che non protegge da noi; il moderatore che sul contenuto
digitale legge). Vedi Architettura, «I FONT VENGONO IN CASA» e «LA
PAGINA "I TUOI DATI"», anche per la trappola del banco (Chrome ignora
`--window-size`) e per l'imperfezione dichiarata del ₿.
Collaudato: 3670 prove verdi, con le sentinelle sulle tre frasi
torturate una per una — addolcendone una qualunque diventa rossa la
sua e nessun'altra — e il confronto pixel alle larghezze VERE (la
pagina di solo testo identica in tutti e sei i confronti). Più il giro
dal vivo col server vero su un database usa-e-getta: a 320/360/375 il
documento è largo quanto il viewport, zero elementi oltre il bordo,
zero segnaposto vuoti, i numeri tutti dal server.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva nuova. Il service worker si aggiorna alla visita
successiva, come sempre. DA GUARDARE dopo il deploy: che nella pagina
vera non parta NESSUNA richiesta verso Google, e la prima anteprima di
`/privacy` condivisa in chat.
DA DECIDERE, ed è la ragione per cui la pagina si dichiara ancora in
costruzione: il titolare del trattamento (con Alan e col
commercialista), e se dare un bottone alla cancellazione
dell'account. Il CONTATTO per i diritti invece c'è dall'ago 2026 — la
chat diretta su Telegram, vedi «IL CONTATTO PER I DIRITTI È SUO» — e
diventerà il recapito formale il giorno che il titolare avrà un nome.

La porta del timer (ago 2026, dal caso limite trovato guardando i due
timer del digitale): quando un timer chiudeva un affare e il venditore
non aveva un metodo d'incasso, l'ordine finiva in `confirmed` con
`disputata` a 0 — i sats ancora in cassaforte e **nessuna rotta per
renderli, nemmeno a un moderatore**. La query in produzione tornava
vuota, quindi nessun pregresso da decidere a mano: il cantiere chiude
solo il futuro. La cura registra COME ci si è arrivati e apre la porta
al SOLO moderatore su quel ramo — chi ha confermato di persona resta
chiuso — più i tre testi che dicevano il falso e la notifica che al
compratore non arrivava affatto. Vedi Architettura, «E LA GEMELLA È LA
PORTA DEL TIMER», per la finestra che si chiude da sola, per il prezzo
dichiarato di `disputata=1` e per le due strade scartate.
Collaudato: 3969 prove verdi (32 nuove, più due che hanno CAMBIATO
LATO — certificavano l'espressione di ieri) e **16 mutazioni, una per
riga sorvegliata, zero sopravvissute**; `collaudo_conto.py` resta 55/55
con tutte le pure del conto INTATTE byte per byte, e il nuovo
`collaudo_porta_timer.py` cammina il giro vero su database
usa-e-getta (20 verdi): codice consegnato, rivelato, timer, porta,
rimborso — più la regressione di chi ha confermato a mano, che resta
chiuso e non si muove di un byte.
IN PRODUZIONE basta il deploy: colonna additiva a 0, nessuna leva,
nessuna rotta nuova, nessun backfill; un client vecchio in cache non
vede il campo e si comporta come oggi. DA GUARDARE al primo giro: che
la colonna cominci a timbrarsi — è anche il censimento dei timer, cioè
la risposta a «sono mai scattati?» che oggi si può dare solo dal
journal — e il primo ordine che entra nella coda «⏸ Ordini fermi» col
badge «⚖️ decidibile» acceso.
Il tappo delle «due teste» (ago 2026, dalla ronda del libro mastro: gli
annunci 208 e 209). Non un sanguinamento ma un EPISODIO — la ronda
suona dal 16, sempre 1 controllo, nessun caso prima né dopo — e la
diagnosi si è fatta tutta sul CODICE, in sola lettura, prima di toccare
qualunque cosa: gli scrittori di quelle due colonne sono pochissimi e
si contano, quindi la direzione («la riga era nativa e l'import se l'è
presa») era certa senza guardare il database. Il tappo è una clausola
sul solo match per titolo, la cintura sul POST della firma, la coda che
si svuota da sola, e il «perché» dell'allarme corretto in due posti,
che diceva il falso e mandava a cercare dalla parte sbagliata. Vedi
Architettura, «L'ANNUNCIO A DUE TESTE», per la riga da non ammorbidire
(mai sul match per `d`) e per le due cose viste e non toccate.
Collaudato: 4090 prove verdi (13 nuove, eseguibili dove conta — la
query estratta dal sorgente e girata, l'endpoint della firma fatto
girare per davvero) più `collaudo_due_teste.py`, che ricostruisce il 15
agosto con l'import VERO (12 verdi), e SEI mutazioni, una per riga
sorvegliata, ognuna rossa da sola — quella che allenta la clausola fa
rosse anche sei righe del collaudo, che è il punto: mostra il difetto
invece di descriverlo.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta. **IL TAPPO NON SPEGNE L'ALLARME**: 208 e
209 continuano a matchare per `d` e la ronda continua a suonare finché
le righe non si toccano.
Il giro dopo (ago 2026) ha chiuso le due cose che restavano e ha curato
le righe. IL CODICE: il ramo `sold`, il cassetto doppioni riportato
all'era del BIVIO (etichetta condizionata a chi ha firmato, il 502 che
diventa un'attesa dichiarata, l'intro che dice anche cosa il bottone
non fa) e il 🟣 dell'importato in «I tuoi annunci». Vedi Architettura,
in coda a «L'ANNUNCIO A DUE TESTE».
LA CURA È UN UPDATE, e la sua WHERE **è la query del libro mastro
parola per parola** — «cura tutte le righe che l'allarme segnala» —
quindi è idempotente per costruzione: `SET contatto_nostr='',
nostr_origine_d='', nostr_origine_id='', nostr_origine_foto=''`.
Perché ognuna: `contatto_nostr` è la testa di troppo (e ridà Modifica,
rifornimento e il posto fra i «nativi» della deduplica);
`nostr_origine_d` o il match per `d` la ri-adotta entro l'ora (accetta
`venditore_id`); **`nostr_origine_id` perché è l'aggancio delle
NIP-09** — lasciandolo, una cancellazione del suo evento su un altro
client spegnerebbe la riga nata QUI; `nostr_origine_foto` per coerenza.
NON si toccano `nostr_event_id` e `nostr_autore` (la testa è sua e
legittima) né `modificato`, che è una data vera — l'import l'ha
modificata davvero, e inventarne un'altra sarebbe peggio.
L'ORDINE ERA VINCOLANTE: prima il deploy, poi l'UPDATE. Oggi il difetto
`sold` non toccava quelle righe (importate, il match per `d` vinceva ed
era quello giusto): diventa raggiungibile nell'istante in cui tornano
native. È la regola dell'annuncio 173.
COSA VEDE IL VENDITORE, ed è la parte che il messaggio deve dire: entro
un'ora l'import crea DUE righe importate nuove — attive e senza
ripassare dall'AI, perché `_da_giudicare` ripiega sul titolo e trova la
riga curata col testo identico all'evento (l'ha scritto lui) — e la
coppia arriva nel cassetto. Ma quel bottone NON toglie una riga: per
averne una sola deve togliere l'altra dai suoi annunci, e lo scudo
anti-resurrezione la tiene spenta per sempre. Effetto collaterale
dichiarato: `accoda_match` conta anche gli importati, quindi chi ha un
avviso di ricerca su quegli oggetti riceve un secondo avviso.
E LE FOTO NATIVE ERANO SOVRASCRITTE, non orfanate — la correzione a una
mia affermazione sbagliata, verificata sui file: `pubblica()` salva
`a{id}_{i}.jpg` SENZA versione e `scarica_foto` dell'import scrive lo
STESSO nome, quindi con un evento che porta immagini JPEG i file
spariscono (e la `_min` gemella l'import la cancella apposta).
Sopravvivono solo se l'estensione differisce o se l'annuncio era già
stato modificato una volta, dove i nomi sono versionati. Non si
recuperano che da un backup: lo dice il messaggio.
IL VENDITORE VA AVVISATO — il precedente della correzione a mano della
via di consegna — con «💬 Scrivi a un utente», che registra l'invio nel
registro moderazione e attacca da sé la strada per risponderci.
Collaudato: 4129 prove verdi (19 nuove) e 28 nel collaudo (16 nuove),
con SEI mutazioni una per riga sorvegliata, ognuna rossa da sola; più
il giro dal vivo sui DUE rami del ritiro (200 con la firma in coda, 502
dove è vero) e le etichette misurate a 320px.
LA COSA CHE RENDE SICURA L'OPERAZIONE è che
`collaudo_due_teste.py` **esegue l'UPDATE di produzione VERBATIM** su
un database di cartone e verifica tutto il seguito — la ronda che tace,
l'idempotenza, il venditore che torna a rifornire, l'import che non
ri-adotta, la coppia che arriva col flag, la NIP-09 che non spegne più
la riga nata qui. La SQL è una costante di quel file: un collaudo che
prova una query DIVERSA da quella che si lancia non prova niente.

Il punto salvato che qui non vale, detto a voce (ago 2026, da una
domanda in sola lettura di Andrea): chi si è tenuto un locker InPost e
apre la cassa su un venditore che spedisce solo con Poste trovava il
campo vuoto ESATTAMENTE come chi non ha mai salvato niente — il server
manda `punti_salvati` già filtrato, e una lista vuota non sa dire quale
dei due casi sia. Una riga sotto le pillole del tipo, nella lingua di
quella del Profilo, che però NOMINA le reti dei due lati: «Hai un punto
salvato per InPost, ma questo venditore spedisce solo con Poste
Italiane». Perimetro deciso da Andrea: solo col venditore che le reti le
ha dichiarate — a zero reti la frase è contorta e il caso è raro, meglio
tacere. Vedi Architettura, «I PUNTI SALVATI, E LA RIGA CHE SPIEGA UN
VUOTO», per le reti morte che non si nominano e per il gate che NON si
mette sul campo già scritto.
Collaudata: 4141 prove verdi (11 nuove, di cui una ESEGUIBILE — il
giudice fatto girare con node sui dieci casi, perché le altre dicono che
esiste ed è uno, mai che risponda giusto, e il caso che solo
l'esecuzione prende è la rete morta in mezzo alle vive) e DODICI
MUTAZIONI una per riga sorvegliata, zero sopravvissute. Più il giro dal
vivo col server su un database usa-e-getta a 320/360/375 nei due temi
(riga su due righe, nessuno sbordo, zero errori JS) e la contro-verifica
che il caso normale non cambia: col punto della rete giusta il campo si
apre precompilato e la riga non c'è. Lì è saltata fuori l'unica
correzione del giro, e solo MISURANDO: la riga toccava la label del
campo (10px sopra, ZERO sotto).
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client.

Il widget da incorporare (ago 2026): un annuncio o la vetrina di un
negozio dentro il sito di qualcun altro, in un `<iframe>` — due rotte
esplicite, una pagina sua di due kilobyte col CSS in linea, e il
codice da copiare in un foglio del Profilo (o dal dettaglio del
proprio annuncio). L'IFRAME E NON UNO SCRIPT: uno script nostro sulla
pagina di un estraneo mescolerebbe i due CSS e ci prenderebbe il
diritto di eseguire codice su un dominio che non è nostro — una
fiducia che non ci serve. Vedi Architettura, «IL WIDGET DA
INCORPORARE», per il venduto che si serve, per il 404 che non si dà
mai dentro l'iframe di qualcun altro, e per il rovescio.
IL ROVESCIO C'È MA NASCE SPENTO (decisione di Andrea: «non si deve
rompere nulla»): non c'era NESSUN header sul frame, quindi
barattolo.store era incorniciabile da chiunque — non l'avevamo deciso,
era il default — e adesso `frame-ancestors` vale su tutto tranne
`/widget/`, ma solo a leva `PROTEGGI_IFRAME` accesa. Spenta, il
comportamento è identico a oggi BYTE PER BYTE (verificato: zero header
nuovi su home e API), e il widget funziona uguale: la stretta non gli
serve. È l'unico pezzo dei tre cantieri che possa rompere qualcosa, e
si accende con un gesto dopo aver guardato la sola strada che tocca.
E NIENTE `X-Frame-Options`, che è la riga che verrebbe voglia di
aggiungere «per sicurezza»: è binario, e su Telegram Web la Mini App
gira dentro un iframe di web.telegram.org — un SAMEORIGIN lì è
Barattolo che smette di aprirsi per chi usa Telegram dal browser, e
non se ne accorge nessuno finché non lo prova. Stavo per metterlo:
l'ha fermato il controllo di come Telegram Web apre le mini app.
Collaudato: **27 prove nuove** in modalità severa — il DELTA misurato
contro il main del giorno, che è il numero che si può difendere: il
totale dipende dal ramo su cui il cantiere atterra, e questo è nato
dentro un commit più grosso poi spezzato in tre — e OTTO
MUTAZIONI del codice, una per riga sorvegliata (CSP sovrascritta al
posto di setdefault, CSP tolta a tutti, Telegram fuori dalla lista,
rimossi serviti dal widget, tetto delle card sparito, slug non più
digerito, `a.*` al posto della whitelist, iframe diventato script):
ognuna diventa rossa da sola. Più il giro dal vivo col server acceso
su una copia del database di collaudo — le due rotte, il negozio per
codice e con lo slug appresso, `n` limato al tetto, il venduto col suo
badge, l'annuncio e il negozio inesistenti che rispondono col riquadro
e non con un 404, e gli header verificati uno per uno (la CSP c'è su
home e API, non c'è sul widget).
NON COLLAUDATO QUI: il widget non è stato GUARDATO A SCHERMO — su
questa macchina non c'è un browser connesso — quindi l'aspetto, il
tema scuro che segue il sito ospite e il comportamento dentro un
iframe vero vanno visti dal vivo. E il `postMessage` dell'altezza non
è stato esercitato da nessun ospite.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione, e
`PROTEGGI_IFRAME` nasce spenta — quindi il deploy non cambia NIENTE di
quel che c'è, aggiunge solo due rotte e un foglio. DA GUARDARE al
primo giro: il primo widget incollato su un sito vero. E se un giorno
si vorrà accendere la leva, PRIMA si apre Barattolo da Telegram Web
(il browser, non l'app): è la sola strada che può chiudere.

Il prezzo dell'accordo si vede subito (ago 2026, decisione di Andrea):
chi ha un'offerta accettata vedeva il listino pieno dappertutto — e
nelle celle del carrello la barra sotto diceva già la cifra pattuita,
cioè due numeri nella stessa schermata. Adesso il prezzo mostrato è
quello dell'accordo col listino barrato accanto, in tutte e cinque le
superfici che passano dal giudice unico. Niente badge e niente colore
(i colori del prezzo in card restano quattro), niente CSS nuovo,
niente server: il dato era già in memoria dall'avvio e la decisione
«accordo o lampo, col MIN» viveva già dentro `artStima`, che adesso è
una riga derivata dal giudice. Vedi Architettura, «IL PREZZO
DELL'ACCORDO SI VEDE SUBITO», per la trappola della valuta riscritta,
per il gate della scadenza coi cinque POST che lo scavalcano, e per il
battito che senza il ricalcolo esplicito ridisegnerebbe la griglia una
volta al secondo per sempre.
DUE DIFETTI TROVATI DAL VIVO e non leggendo: il rinfresco si accendeva
quando un accordo NASCE e taceva quando SPARISCE — cioè proprio al
ritiro, dove la scheda tornava al listino e la card restava a dire la
cifra di un accordo che non c'era più (adesso guarda il CAMBIAMENTO,
col pattern della firma); e la riapertura della scheda nel battito
guardava `.lampo-was`, che è il vestito condiviso, quindi una lampo
scaduta su un'altra card riapriva una scheda che non aveva niente da
rimettere a posto. E una LEZIONE DI METODO: la prima prova della
scadenza diceva «il battito non scatta», ed era la SONDA a essere
rotta — ricalcolavo io la prossima scadenza subito dopo averla messa
nel passato, togliendo al battito la cosa che doveva vedere.
Collaudato: 4242 prove verdi (+94, fra cui DUE eseguibili — i giudici
del prezzo su 13 casi con l'atteso scritto a mano, che è anche la
prova che `artStima` risponde gli stessi numeri di prima, e il
rinfresco che si accende nei due versi), sette sentinelle rovesciate
col motivo, e **15 mutazioni, 0 sopravvissute**. Più il giro dal vivo
col server vero su un database usa-e-getta: offerta per 3 pezzi →
accettazione → card, scheda, toggle valuta nei due versi, carrello
(dove cella e barra dicono finalmente la stessa cosa), la scadenza
sotto il battito vero (UN ridisegno, e non si ripete) e il ritiro dal
foglio di conferma. Screenshot a 320/360/375 nei due temi.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — e in DEMO e in vetrina non cambia un
pixel, che lì `offertaAccettataPer` torna sempre null. DA GUARDARE al
primo giro: il primo accordo vero dentro Telegram, e che alla scadenza
la card torni al listino da sola.


Via il bottone «📬 È arrivato — lo controllo» (ago 2026): il passo
intermedio fra 'shipped' e 'delivered' se n'è andato col suo endpoint,
perché quel gesto lavorava contro chi lo premeva — vedi «IL PASSO
INTERMEDIO NON C'È PIÙ» in Architettura per il conto dei tre giorni
contro dieci, per la maniglia che il venditore riguadagna e per il
testo del ritiro che sarebbe diventato falso. Non si tocca niente di
ciò che LEGGE 'delivered': la porta si chiude, la stanza resta, e sul
digitale quello stato è vivissimo (là lo scrive la rivelazione del
codice). Collaudato: 4155 prove verdi con 12 sentinelle nuove — fra
cui il censimento che CONTA gli scrittori di `consegnato` invece di
elencarli — e OTTO mutazioni, una per riga sorvegliata, ognuna rossa
da sola, compresa quella che toglie 'delivered' dalle due porte
d'uscita; più una falsa sicurezza STRETTA in `prove_ritiro`, che
cercava «L'ho ritirato» in tutto il file e restava verde per il
gemello. `collaudo_porta_timer.py` resta 20/0 ed è la prova eseguibile
che da 'delivered' si esce ancora. E dal vivo, server vero su database
usa-e-getta e Chrome via CDP (15/15, zero errori JS): a 320 e 375 il
bottone non c'è, «libera i sats» e la disputa ci sono, un 'delivered'
seminato a mano arriva in fondo, il pannello del ritiro sta su una
riga e il venditore tiene il suo sollecito. IN PRODUZIONE basta il
deploy: nessuna colonna, nessuna migrazione, nessuna leva, nessuno
stato nuovo — e la query in sola lettura prima del cantiere diceva
ZERO ordini in 'delivered', quindi non c'è nessun residuo da
accompagnare. DA GUARDARE al primo giro: che la coda «⏸ Ordini fermi»
non cambi popolazione, e il primo ordine fisico che arriva a dieci
giorni — deve ricevere il promemoria dal ramo 'shipped'.
DA SEGNALARE, visto e NON toccato: il tasto «🔔 Sollecita l'acquirente»
è gated su `s==='shipped'` mentre il server accetta anche 'delivered',
quindi sul DIGITALE il venditore non può sollecitare dal client anche
se il server glielo permetterebbe. Buco preesistente, che il cantiere
chiude per il fisico e lascia intatto per il digitale.

La consegna si dichiara dalla modifica firmata (ago 2026, dal campo: un
venditore da Nostr che non può dichiarare la spedizione). I numeri
misurati in produzione dicevano che non era un caso isolato — 6 righe
senza consegna su 8 importati attivi, cioè NESSUN importato fisico
l'aveva mai dichiarata, e in crescita (4 in quattro giorni contro 2 in
tutto luglio) — e che la strada era già aperta per tutti e sei
(`npub_accesso`): mancava solo il campo, che il form nascondeva su una
premessa invecchiata. Insieme, la cura del difetto che spogliava
l'evento del venditore dei suoi tag di commercio: la stessa riga. Vedi
Architettura, «LA CONSEGNA SI DICHIARA DALLA MODIFICA FIRMATA», per la
regola in una frase, per «chiave assente = conserva» (che protegge i
due digitali corretti a mano dal client rimasto in cache) e per la zona
che può essere fuori dall'Italia.
DUE COSE TROVATE MISURANDO, e sono la parte da ricordare: le quattro
zone dei sei erano «tutte compilate» ma **«baixllobregat» e «maresme»
non sono comuni italiani**, quindi con la guardia intera due venditori
su sei non avrebbero dichiarato niente (da lì `esigi_luogo`); e il
sottotitolo del form firmato prometteva «la consegna compresa» anche
sui digitali, dove il blocco non c'è — visto a schermo, non leggendo.
Collaudato: 4242 prove verdi (+87, fra cui il giro chiuso ESEGUIBILE
`estrai_commercio(evento_annuncio_importato(riga))` e il nome di
quell'evento entrato in tutte e cinque le tuple della cecità), il nuovo
`collaudo_consegna_firmata.py` (27 verdi: i due endpoint veri con una
firma Schnorr vera su database usa-e-getta — il giro completo, le
colonne che non si toccano, il 400 sul digitale, la zona catalana, e il
client di ieri che NON azzera niente), e **21 mutazioni, 0
sopravvissute**. La tortura ha fatto il suo mestiere: tre sentinelle
mie erano deboli o vacue — una guardava solo che un id esistesse — e
una mutazione era mirata male (colpiva `modifica_annuncio` invece della
fase 1, che quella stringa vive in due posti). In più ha scoperto un
caso che nessun collaudo esercitava, «chiave presente ma VUOTA», che
adesso c'è. IN PRODUZIONE basta il deploy: nessuna colonna, nessuna
migrazione, nessuna leva. DA GUARDARE al primo giro: il primo dei sei
che dichiara la spedizione, e che il suo evento su njump porti il tag
`delivery` — è l'unica prova che il cerchio si chiude davvero.

Il feedback si apre alla conferma, non all'incasso (ago 2026, decisione
di Andrea da un caso vero): chi ha comprato vota appena dichiara di aver
ricevuto l'oggetto, anche se il venditore non ha ancora un wallet e
l'ordine è fermo in `confirmed` — quella è una leva sua, non di chi
compra. Si apre SOLO sul confirmed non riapribile (`disputata=0 AND
sbloccato_auto_il=0`), che è il complemento esatto delle due porte di
`risolvi_disputa`: così l'invariante di sempre resta intatto — il
feedback si lascia solo dove lo stato non può più cambiare — e la
domanda «e se dopo finisce in disputa?» non si pone. Votano entrambe le
parti; `refund` resta fuori dichiarato. Vedi Architettura, «IL FEEDBACK
RIGUARDA L'AFFARE, NON L'INCASSO», anche per la trust-note del
compratore che si è allineata (diceva «hai confermato» a chi aveva
PERSO una disputa) e per l'ancora del feedback automatico, dichiarata e
NON piantata. Collaudato: 4271 prove verdi (28 nuove, fra cui LA PROVA
REGINA — la WHERE della porta estratta dal sorgente e fatta GIRARE su
48 combinazioni, perché giudice e porta non possano mai essere veri
insieme — e la parità client↔server girata con node) più OTTO
MUTAZIONI, una per riga sorvegliata, ognuna rossa da sola; e
`collaudo_feedback_confermato.py`, 22 verdi, che cammina il giro vero
su un database usa-e-getta. IL BANCO HA MENTITO UNA VOLTA, ed è la
lezione del giro: al passo del wallet il venditore ne guadagnava uno,
quindi gli ordini dei rifiuti volavano a `released` e passavano PER LA
RAGIONE SBAGLIATA dicendo verde — adesso `ordine_confermato` alza se lo
stato non è quello promesso. IN PRODUZIONE basta il deploy: zero
colonne, zero migrazioni, zero leve, zero campi nuovi nel payload. DA
GUARDARE al primo giro: il primo compratore che vota da `confirmed`, e
che il suo voto sia ancora lì quando il venditore incassa.

Il pacchetto UX acquisto e spedizione (ago 2026, sei punti di Andrea in
un giro): le foto degli ordini a 56/64 (erano francobolli da 38/48 —
solo CSS, la fabbrica ha il raggio inherit apposta); il cassetto «Hai
un codice sconto?» gated sul sì/no del preventivo (`codici_esistono`,
l'oracolo parziale accettato: mai un dato del codice — giudice
`_codici_vivi` che riusa `_codice_vale`, fail-open nel client);
la nota al venditore discreta ovunque («+ Aggiungi una nota») e GIÀ
aperta nelle 4 categorie con varianti, senza tastiera; il cassetto del
punto che dice la RETE per casistica coi trova-punto promossi a
bottoncini (`.btn.mini`, la variante piccola del ghost nata qui, presa
anche da «Ricorda questo punto»); l'invito corrieri SENZA tetto (si
richiede a ogni pubblicazione finché non dichiara, «Pubblica lo
stesso» resta — il mai-bloccante non si è rovesciato, il tetto sì);
e la pagina «I tuoi dati» che dichiara il codice sconto rimasto
nell'ordine (la lacuna trovata esplorando). Vedi le voci loro in
Architettura. Collaudato: 4393 prove verdi (da 4383: nuove più tre
rovesciate col perché — i due costruttori della nota, il tetto
dell'invito), collaudo_conto 99/99 intatto, e il giro dal vivo sul
server locale con la copia del db: il flag dei codici nei tre stati
(senza/con/in pausa) su mono E set, la nota nei due comportamenti,
il foglio corrieri col contatore a 99 e il riarmo al secondo
annuncio, le misure delle foto a tre larghezze. IN PRODUZIONE basta
il deploy: nessuna colonna, nessuna migrazione, nessuna leva nuova —
`codici_esistono` è una chiave in più nel preventivo e il client
vecchio non la legge. DA GUARDARE al primo giro: il primo venditore
vero davanti al foglio senza tetto (che non lo senta come un muro), e
il cassetto dei codici che compare solo dai negozi giusti.

Le categorie in home diventano card a scorrimento (ago 2026,
decisione di Andrea): sotto l'header di Esplora una fila di card
quadrate illustrate — le stesse 27 figure di Sfoglia, nello stesso
ordine — e il tab «Sfoglia» esce dalla barra, lasciando il suo posto
alla voce che verrà. In cima i nomi in pillola non esistono più:
compaiono appiccicati sotto l'header appena le card escono di vista
scorrendo, così il reparto si cambia in qualsiasi momento senza
tornare su — e le due file non si vedono mai insieme. Sfoglia
resta, dietro l'ultima card («Tutte le categorie»), e diventa una
vista interna come /privacy: la nav accende Esplora e l'indietro
riporta in home. Vedi Architettura, «LE CATEGORIE IN HOME», per il
riquadro non-quadrato dentro la card quadrata (il pareggio
dell'inchiostro è tarato su quello di Sfoglia), per le misure
verificate a schermo e per la regola che si rovescia — «MA LA NAV
MENTIVA» era vera finché il reparto si apriva da un ALTRO tab.
IL DIFETTO TROVATO DAL VIVO, ed è la parte che leggendo non si vedeva:
dalla home il tocco su una card NON creava il gradino — la vista non
cambia, quindi l'osservatore del motore non scatta e la entry veniva
SOSTITUITA: il reparto si mangiava la home e l'indietro usciva
dall'app. Da lì `restiamoQui`, che decide se la bandierina si alza
prima o dopo `setCat`, con le prove che ne tengono l'ordine.
Collaudato: 4418 prove verdi (25 nuove) e **21 MUTAZIONI, 21 uccise,
zero sopravvissute** — fra cui una che conferma la tenuta di una
regola vecchia (se la striscia si contasse le categorie da sé, a
diventare rossa è la sentinella storica dei due chiamanti di
`contaCategorie`). Due prove nuove sono state riscritte con `find()`
invece di `index()` perché la tortura le ha viste ESPLODERE invece che
diventare rosse, portandosi dietro tutte quelle dopo. Più il giro dal
vivo via CDP a 320/360/375 nei due temi: il ＋ della nav al centro
esatto (160,0 · 180,0 · 187,5), tre card intere col taglio della
quarta, la catena dell'indietro dalle DUE porte, il barattolo, la
ricerca, il desktop e la DEMO col ripiego a emoji, zero errori JS.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta, nessun file nuovo — e `scaldaSfoglia`
non si tocca, ma smette di essere uno spreco perché adesso quelle
figure servono la home. DA GUARDARE dal telefono, che è dove non si
può provare da qui: l'apertura dentro Telegram e nella PWA
installata, e il gesto indietro di sistema dopo essere entrati in un
reparto dalla card.

Tre difetti della striscia, chiusi (ago 2026, segnalati da Andrea):
1) L'ORDINE si vedeva sbagliato all'avvio — la fila si disegnava
prima che i conteggi arrivassero, quindi in ordine di CATALOGO, e si
riordinava sotto gli occhi ~300 ms dopo: adesso non si disegna finche'
i numeri non sono veri, con lo spazio riservato per non far saltare la
pagina (misurato: 157px dal primo fotogramma). 2) LE EMOJI di ripiego
restavano SOPRA le illustrazioni — 27 su 27 in produzione — perche' il
selettore che le spegne vuole immagine ed emoji FRATELLI, e l'immagine
era chiusa dentro un altro span. 3) LA CARD DEL REPARTO ORA RESTA
ACCESA (rovescia la scelta del primo giro, dove la sezione spariva):
anello arancione, card portata in vista, e sotto gli articoli di
quella categoria; l'indietro riporta alla home intera prima di uscire
dall'app. Vedi Architettura, «LE CATEGORIE IN HOME».
Collaudato: 4436 prove verdi (8 nuove, 2 che hanno CAMBIATO LATO col
perche' scritto) e 9 mutazioni, 9 uccise — una era sopravvissuta e ha
fatto rinforzare la sua sentinella, che diceva «la riga c'e'» invece
di «la riga viene eseguita». Piu' il giro dal vivo via CDP: l'ordine
per numero, zero emoji sopra le figure arrivate, la card accesa anche
quando sta in fondo alla fila, il barattolo, il tema scuro e la catena
dell'indietro. IN PRODUZIONE basta il deploy.
Quattro difetti della striscia, chiusi (ago 2026, dal campo):
1) LA CRONOLOGIA NON ANDAVA A RITROSO passando da un reparto
all'altro — ma solo dalle PILLOLE, che chiamavano `setCat` diretto:
su una radice quello SOSTITUISCE, quindi tre reparti di fila
lasciavano zero gradini e al secondo indietro si usciva dall'app.
Dalle card funzionava gia' (misurato prima di toccare: 0→1→2→3).
Adesso le pillole passano da `apriCategoria` come le card.
(La cronologia A RITROSO e' stata ROVESCIATA il giorno dopo — vedi
«IL REPARTO E' UN GRADINO SOLO» qui sotto: le pillole passano ancora
da apriCategoria, ma il gradino e' uno e l'indietro torna alla home.)
2) LA BARRA COMPARIVA DI COLPO: si spegneva col `display`, da cui non
si transiziona niente. Ora e' un velo con la sua scivolata, spenta da
reduced-motion. 3) IL BUCO DI 6px sotto l'header tornando da un
annuncio: il `top` era scritto a mano e veniva letto in un istante in
cui l'header dichiarava 154px invece di 148 (sonda sulle scritture).
La barra e' ora APPESA all'header in CSS: nessun numero da rincorrere,
e sparisce con la vista — l'altra meta' dello stesso difetto, che la
lasciava accesa sopra il dettaglio. 4) IL LAMPO DI EMOJI all'apertura:
il selettore guardava il `data-ok` invece dell'esistenza
dell'immagine, ora il quadrato aspetta come il fondo delle card degli
annunci. Piu' il RITOCCO sulla card accesa che torna a «Tutto», il
gesto del barattolino (decisione di Andrea).
Collaudato: 4443 prove verdi (13 nuove, 6 che hanno CAMBIATO LATO e 3
MORTE col codice che sorvegliavano) e 10 mutazioni, 10 uccise — una
esplodeva invece di essere rossa e si portava dietro le prove dopo di
lei, riscritta con find(): e' la terza volta, ed e' sempre la stessa
lezione. Piu' il giro dal vivo: i tre reparti dalle pillole con
l'indietro a ritroso, il velo che a 150 ms sta a 0,96 di opacita', il
buco che passa da 6px a -1 (il bordo dell'header), zero emoji in dieci
campioni dall'avvio, il ritocco, il desktop e i due temi.
IN PRODUZIONE basta il deploy.
Il reparto e' un gradino solo, e la ricerca lo spegne (ago 2026, tre
punti di Andrea in un giro, il primo ROVESCIA quello di ieri):
l'indietro dopo una o piu' categorie riporta SUBITO alla home — dalla
home si spinge una volta, i cambi reparto→reparto sostituiscono — e
chi torna a «Tutto» (ritocco, pillola, tab) CONSUMA il gradino con un
vero passo indietro, o resterebbero due entry identiche impilate: un
indietro morto, e quello dopo che butta fuori dall'app. Il push resta
obbligatorio per la PWA, dove il gesto e' di sistema e l'entry deve
esistere prima. Piu' la ricerca che guarda TUTTI gli articoli e
spegne l'anello del reparto (l'AI non ha mai filtrato per categoria:
a filtrare erano DEMO e vetrina anonima). Vedi «IL REPARTO E' UN
GRADINO SOLO» in Architettura per la profondita' registrata, il
history.back() diretto e la ragione per cui spegniReparto non passa
MAI da setCat. Collaudato: 4456 prove verdi (+13, quattro che
CAMBIANO LATO col perche') e la tortura a 16 mutazioni — compresa
quella che rimette la bandierina incondizionata di ieri — tutte
uccise; giro dal vivo sul server locale con la catena dei tre
reparti, il pop alla profondita' giusta dopo un dettaglio, Sfoglia
intatta e la ricerca «Vasetti» da dentro Elettronica che trova gli
Alimenti con l'anello spento. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna leva, nessuna rotta — solo client. DA GUARDARE dal
telefono, nei DUE contesti (Mini App e PWA): entrare in tre reparti e
uscire con UN gesto, e il ritocco della card accesa seguito da un
solo indietro per chiudere l'app.
La card «Tutto» apre la fila, e Sfoglia non esiste più (ago 2026, due
decisioni di Andrea in un giro): in testa alla striscia c'è la card
«Tutto» — illustrata come le sorelle, il tocco passa da tornaATutto e
consuma il gradino della home, il ritocco della card accesa resta —
e la card «Tutte le categorie» in coda è morta con la pagina intera:
la fila È la mappa, e la pagina dietro l'ultima card era un doppione
con una porta sola. Verificato quel che la rimozione doveva
garantire: nessuna porta residua (go('sfoglia') a zero in tutto il
client), /categoria/{slug} intatte (pagine del server: cartello,
sitemap, apriCategoriaDaUrl), e le entry vecchie della cronologia che
degradano su Esplora — v:'sfoglia' ha il suo ramo in navRendiVista, o
il go() di default esploderebbe. Vedi Architettura, «LA CARD "TUTTO"
IN TESTA E LA MORTE DI SFOGLIA», per la whitelist SLUG_ILLUSTRAZIONI
(«tutto» non è una categoria) e per cosa resta col nome vecchio.
Collaudato: 4463 prove verdi (le nuove su porta-zero, card in testa
coi suoi quattro comportamenti, degradazione, whitelist) e NOVE
mutazioni una per riga sorvegliata, ognuna rossa da sola — la decima
l'aveva presa il primo giro: la sentinella della card in coda legge
anche i commenti, e ha pescato il nome della classe nella lapide CSS.
Più il giro dal vivo via CDP a 375px: 28 celle, anello che segue il
reparto e card portata in vista, UN gradino (d 0→1→1→0),
reparto→reparto che sostituisce, tocco a vuoto che non fa niente,
pillole appiccicate con «Tutto», zero errori JS. IN PRODUZIONE basta
il deploy: nessuna colonna, nessuna leva, nessuna rotta nuova (la
rotta delle illustrazioni allarga la whitelist di una voce). DA FARE:
tutto.webp non è ancora nel repo — quando Andrea lo mette,
ritaglia_categorie.py --scrivi e la prova d'esistenza in prove.py;
fino ad allora la card mostra l'emoji di ripiego.


Da oggi Barattolo vende anche i SERVIZI (ago 2026): lezioni,
consulenze, prestazioni definite — online o in presenza. Il quadro
dell'escrow è stato deciso PRIMA della categoria, ed è la cosa che
mancava: su una lezione il fatto su cui i sats si sbloccano non esiste
dentro Barattolo. La frase che tiene insieme tutto: **non possiamo
giudicare se la lezione c'è stata, possiamo giudicare se le CONDIZIONI
per farla c'erano** — appuntamento concordato da tutti e due,
collegamento lasciato in tempo, e sono fatti che restano scritti qui.
Le cinque decisioni di Andrea, il modello a zero stati nuovi (si resta
in `locked`, e quello rende IRRAGGIUNGIBILI i due rami fisici
dell'auto-sblocco), il buco del link morto chiuso col RIPETUTO invece
che con una prova che non abbiamo, e le imperfezioni dichiarate stanno
in Architettura, «I SERVIZI».
Provato: 4601 prove verdi (le nuove comprendono la nota al moderatore
girata DAVVERO su un database di cartone — una sentinella dice che le
righe ci sono, solo girandola si vede cosa legge chi decide) più venti
mutazioni una per riga sorvegliata, ognuna rossa da sola; e il giro
visivo via CDP a 320/360/375 nei due temi sui due ruoli — scheda,
form, i quattro pannelli dell'ordine — dove niente sborda.
Nello stesso giro tre testi che il cantiere rendeva falsi: le parole
della NOTA su una prestazione, il messaggio della REVISIONE che adesso
insegna il perimetro invece di dire solo no (decisione di Andrea), e
l'AVVISO DEL RECUPERO WALLET a chi compra — un avviso, mai un blocco a
chi vende, con la distanza fra le parole MISURATA sui casi veri e zero
falsi positivi sugli 860 annunci del collaudo.
IN PRODUZIONE il deploy fa girare le migrazioni additive (due colonne
su `annunci`, undici su `ordini`, tutte a 0/'') e **non cambia
niente**: `SERVIZI_ATTIVI` nasce FALSE nel codice, come
IMPORT_NOSTR_APERTO e per la stessa ragione — la si accende dal config
del VPS con un gesto, guardando il primo giro. `SERVIZIO_MAX_APERTI`
nasce a 0 (spenta) e si alza solo se in rodaggio si vede una raffica.
FATTO PRIMA DI ACCENDERE (23 ago 2026, Andrea sul VPS):
`collaudo_impersonazione.py` con la chiave vera dà **25/25** — i sei
casi nuovi dicono che il modello ha capito il confine definito/su
misura, e l'atteso segue il PROMPT, mai il modello. `SERVIZI_ATTIVI` è
ACCESA nel config del VPS dallo stesso giorno, insieme a
`CONNETTORI_NEGOZIO_APERTI` e `BANNER_NEGOZIO_ATTIVO`.
DA GUARDARE al primo giro vero: la prima lezione comprata dentro
Telegram (proposta → conferma → «c'è stata» → sats sbloccati) e la
prima disputa, dove la nota al moderatore è l'unica cosa su cui
decide.


E le prestazioni hanno i loro due reparti (ago 2026): «Lezioni e corsi»
e «Lavoro e servizi» — DUE e non uno, decisione di Andrea, perché una
lezione e una consulenza si cercano in due modi diversi. Le
illustrazioni c'erano già, arrivate «in attesa» col commit delle tre
figure nuove: erano asset ORFANI, e la rotta rispondeva 404 anche col
file sul disco perché la whitelist si deriva da `CATEGORIE`. Quindi è
stato un cantiere di solo CODICE — per la maggior parte copiare due
voci in dieci elenchi che `prove.py` incrocia fra loro. Il perché di
ognuna delle scelte (in coda prima di «Altro», ortogonali alla strada,
fuori da CATEGORIE_SENZA_CONDIZIONE, l'albero scritto invece che
lasciato piatto) sta in Architettura, «LEZIONI E CORSI E LAVORO E
SERVIZI».
Nello stesso giro lo SCAMBIO DELLE ICONE — 🎓 al reparto, che è
l'emoji della sua illustrazione, e 📅 alla strada «servizio», che era
già l'icona del suo flusso — e i TRE BUCHI di ieri: la card non aveva
nessuna icona per un servizio, la scheda non aveva la pillola, e
soprattutto `servizio_dove` e `durata_min` non uscivano da
`CAMPI_VETRINA`: il venditore li dichiarava e chi compra non li vedeva
mai, mentre la durata è metà del «definito» che il prompt pretende.
Provato: 4617 prove verdi (+16, fra cui il censimento che vieta al 🎓
di tornare a dire due cose — quel glifo non lo sorvegliava nessuno) e
DICIANNOVE MUTAZIONI una per riga sorvegliata, ognuna rossa da sola.
Il giudice silenzioso girato su 18 titoli veri delle due famiglie: 16
giusti, i due generici che SI ASTENGONO, zero sbagliati. Dal vivo, le
rotte che davano 404 danno 200 e la striscia passa a 30 card senza
cambiare altezza — 157px a 320/360/375 nei due temi.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva — e «si aggiunge, non si rinomina», quindi nessun annuncio
cambia casella. ⚠️ `ritaglia_categorie.py` NON va rilanciato: a secco
dice «0 da sistemare», e con `--scrivi` ricomprimerebbe per niente
tutti e trenta i francobolli.
DA GUARDARE al primo giro: la coda «🗂 Categorie da sistemare», che
`ricategorizza_automatico` riempie da sola dopo ogni import guardando
gli importati e chiunque stia in «Altro» — è da lì che i primi annunci
traslocheranno. Per i nativi già decisi in passato serve
`ricategorizza.py --rifai` sul VPS, che è una scelta e non un deploy.

Il tasto P2P nella barra (ago 2026): la voce nuova che il posto vuoto
aspettava — «P2P» con la ₿ a tratto disegnata da zero (non esisteva),
che per ora porta solo al coming soon «Qualcosa di nuovo è in arrivo»
col teaser vago. Radice sorella sul calco di astepresto, zero server,
zero leve; il cantiere vero (scambio euro↔bitcoin fra utenti) è un
altro. Vedi Architettura, «IL TASTO P2P», per le due trappole delle
sentinelle (la regex senza cifre, la fessura di RADICI ancorata alla
chiusura del Set) e per la fascia stretta della topbar — la pillola
riapriva lo sbordo del logo a 768-867, e nella fascia 768-899 il testo
del lockup ora CEDE tenendo la tessera (decisione di Andrea, misurata
prima e dopo). Collaudato: 4722 prove verdi, tortura a 12
mutazioni tutte uccise — comprese le due che con le finestre fisse di
ieri sarebbero rimaste verdi — e il giro dal vivo via CDP: centro del
＋ esatto alle tre larghezze (160,0/180,0/187,5), voce accesa nei due
temi, un gradino solo girando i tab e indietro che passa da Esplora,
ripiego ₿ da file://. IN PRODUZIONE basta il deploy: nessuna colonna,
nessuna leva, nessuna rotta — solo client. DA GUARDARE dal telefono:
il tocco vero dentro Telegram e nella PWA (il gesto indietro di
sistema dal coming soon), e la ₿ accesa sullo schermo vero.

Il banner del negozio 🖼 (ago 2026): il venditore appende la sua insegna
sopra il catalogo — una foto e un link al suo sito — e vive SOLO sulla
pagina del suo negozio (niente in home: quella è pubblicità vera e ha un
cantiere suo). Le decisioni di Andrea: lo sblocco è il LIVELLO
(«avviato», non «pratico», che oggi non ce l'avrebbe quasi nessuno e la
funzione nascerebbe morta), il link può portare a QUALSIASI sito suo con
la sola regola già scritta per l'impersonazione, sta sotto il riquadro
venditore, e in ferie RESTA mentre a vetrina vuota sparisce. **Il
pagamento che anticipa la porta è dichiarato e non costruito**: questa
tappa è il banner e basta, zero righe di denaro.
LA COSA DA SAPERE PRIMA DI TOCCARLO: è la prima volta che l'app apre un
indirizzo scritto da un utente davanti a un ALTRO utente, e il freno non
è il livello — a commissione spenta quello si compra con due account —
ma la REVISIONE UMANA, che è anche l'unica possibile: l'AI di casa legge
testo, e un banner è un'immagine. Vedi Architettura, «IL BANNER DEL
NEGOZIO», per il giudice del link riga per riga (accorciatori, omografi,
punycode, il nostro dominio) e per le due coppie di campi che tengono
acceso il banner vivo mentre una modifica aspetta.
Collaudato: 4826 prove verdi (le nuove: il giudice del link su 22 casi,
la porta col suo fail-closed, `_banner_pubblico` sui suoi, e
`decidi_banner` girata DAVVERO su sqlite in memoria per tutti e quattro
gli esiti più il 409 del secondo moderatore) e **29 MUTAZIONI, 29
uccise, zero sopravvissute** — una per riga sorvegliata, su una copia
del repo. Più il giro dal vivo col server vero su un database
usa-e-getta e Chrome via CDP a 320/360/375 nei due temi: rapporto 3:1
esatto, zero sbordo, il tocco che apre la conferma col dominio in
testata e NON naviga, i tre casi in cui il banner non esce (pagina 2,
revisione, vetrina vuota), il caricamento coi suoi sei rifiuti, la coda
del moderatore, il 409 e il 403. E LÌ È SALTATO FUORI IL DIFETTO che le
prove non vedevano — chiedendo una modifica il banner già approvato
spariva dalla vetrina: le colonne erano giuste, la vetrina no.
IN PRODUZIONE il deploy da solo non cambia niente: le otto colonne
nascono coi loro default e `BANNER_NEGOZIO_ATTIVO` è SPENTA nel codice.
Si accende scrivendo la riga nel config del VPS e riavviando — ed è il
momento da guardare col journal aperto, perché da lì in poi si possono
aprire link fuori da Barattolo. DA GUARDARE al primo giro: il primo
banner in coda (che il moderatore veda la foto e il dominio) e il primo
approvato sulla pagina del negozio.
La ricerca diventa una sola, e l'AI ne esce (ago 2026, decisione di
Andrea: «l'AI nella ricerca eliminala proprio»). Cercando
«collezionismo» ora si trovano gli annunci che dicono «collezione» e
quelli della categoria Collezionismo — che il LIKE di ieri non
guardava nemmeno. Sotto c'è FTS5, che è dentro SQLite da sempre (zero
dipendenze, zero compilazioni), con lo stemmer italiano di Snowball
per le desinenze e i sinonimi delle categorie cotti DENTRO l'indice.
Vive in `/api/listings`, cioè nella vetrina: si compone coi filtri e
pagina come tutto il resto, e `/api/search` resta un guscio per i
client in cache. Vedi Architettura, «LA RICERCA È UNA SOLA», per lo
stemmer misurato (su 28 coppie singolare/plurale ne sbaglia 4 —
tastiera, telefono, cassettiera, caffettiera — e da lì esce il
troncamento a 5), per il trigger che invalida al posto di sette
chiamanti da ricordare, e per la trappola del doppio filtro nel
client, che è il modo più silenzioso in cui questo cantiere poteva
fallire.
Collaudato: **+29 prove** in modalità severa (3926 → 3955 contro il
main del giorno; è il DELTA il numero difendibile, che il totale
dipende dal ramo su cui il cantiere atterra — questo è nato dentro un
commit più grosso poi spezzato in tre), più una famiglia ROVESCIATA —
certificava il freno della ricerca AI e adesso certifica che di quella
strada non resti niente — e un collaudo
ESEGUIBILE, `collaudo_ricerca.py`, col server VERO su un database
usa-e-getta: 32 verdi (NON rilanciato nello split: su quella macchina
manca `fastapi`). Più **UNDICI MUTAZIONI** del codice, una per
riga sorvegliata (categoria fuori dall'indice, via i sinonimi, pesi
di BM25 appiattiti, via il troncamento, ordine di pertinenza perso,
indice che non si ripara sulla strada calda, filtri applicati alla
pagina invece che alla rosa, cursore che non avanza, totale che
mente, giro stretto saltato, trigger che non invalida): ognuna
diventa rossa da sola. LE PRIME DUE erano SOPRAVVISSUTE al primo
giro, ed è la parte da ricordare: il catalogo di prova non aveva né
un annuncio la cui categoria è l'unica cosa che lo fa trovare, né uno
che ripete la parola in descrizione — le due fixture sono nate dalla
tortura e non dal piano. Più il giro dal vivo col server acceso su un
database usa-e-getta (le cinque domande di esempio, coi totali che
tornano) e il parse del client con node.
NON COLLAUDATO QUI, e va detto: su questa macchina non c'è un browser
connesso, quindi il giro VISIVO non è stato fatto — la searchbar, lo
scorrimento infinito su una ricerca e la tirata di aggiornamento
dentro una ricerca vanno guardati dal telefono.
NON SI ROMPE NIENTE SE FTS5 NON C'È: provato per davvero con una
connessione che alza come farebbe un SQLite senza quel modulo — il
server parte, lo dice nel journal, e la ricerca ripiega sul LIKE di
ieri (10 risultati su «poster», gli stessi di prima).
IN PRODUZIONE: il deploy fa nascere la colonna `ricerca_v` (a zero,
cioè tutto da indicizzare), la tabella `annunci_fts` e i due trigger;
al primo avvio la passata indicizza tutti gli annunci e lo dice con
una riga («🔎 Indice di ricerca: N annunci indicizzati»). PRIMA del
riavvio serve `pip install snowballstemmer` nell'ambiente del
servizio: senza, il server parte lo stesso e la ricerca lavora a
troncamento — e la riga d'avvio lo dichiara. DA GUARDARE al primo
giro: quella riga, e le prime ricerche vere in produzione (se
`snowballstemmer` manca, «tastiere» e «tastiera» smettono di
trovarsi fra loro). Se il config del VPS ha una riga
`TETTO_RICERCHE_AI_ORA`, è diventata INERTE e si può togliere.
RESTA DA FARE, il secondo passo di questo cantiere: il completamento
automatico mentre si digita e il «forse intendevi» — i mattoni sono
già in casa (l'indice dei prefissi, `fts5vocab`, `difflib`).

I connettori del negozio, le fondamenta (ago 2026, tappa 1 di 5 della
FASE 1): cinque venditori con un e-commerce vogliono importare il
catalogo invece di ripubblicarlo a mano. Il cantiere è spezzato in due
per decisione di Andrea — sola lettura adesso, il decremento a monte
quando i volumi lo chiederanno (il conto dice 0-1 collisioni l'anno, e
ognuna la copre l'escrow) — e questa tappa non cambia NIENTE di
visibile: `fonte` nasce vuota per tutti. Ci sono lo schema (le due
tabelle, cinque colonne additive, due indici fra cui quello che
mancava a `contatto_nostr`), il giudice unico dell'origine col suo
censimento delle guardie, e la fusione che migra i negozi collegati —
il pezzo che il piano non aveva previsto e che ha trovato il
censimento delle tabelle figlie. Vedi «I CONNETTORI DEL NEGOZIO» in
Architettura per le decisioni, il conto della sovravendita e la lista
di cosa non c'è ancora.
Collaudata: 4960 prove verdi (le nuove girano il giudice invece di
guardarlo soltanto — una sentinella direbbe che esiste ed è uno, mai
che risponda giusto), due sentinelle che hanno CAMBIATO LATO col
perché scritto (certificavano la guardia stretta di ieri, cioè un
catalogo Woo con lo stock ricaricabile da qui), la migrazione girata
su una COPIA del database vero (900 annunci intatti, idempotente al
secondo giro) e **18 mutazioni, 18 uccise**. La prima stesura ne
lasciava viva una, ed è la lezione del giro: il censimento generico
cerca il NOME della tabella dentro la fusione, e i DELETE lo nominano
lo stesso — quindi restava verde anche togliendo la migrazione. Una
sentinella sul nome certifica che qualcuno l'ha scritto, mai che il
GESTO ci sia.
IN PRODUZIONE il deploy non cambia niente: le migrazioni sono additive
e non esiste ancora nessuna strada che scriva `fonte`.

E la TAPPA 2 (ago 2026): `importa_negozio.py` col traduttore Shopify,
il trasporto con le sue guardie e il giro orario — a leva
`CONNETTORI_NEGOZIO_APERTI` SPENTA nel codice, quindi anche qui il
deploy non fa succedere niente. Vedi la voce in Architettura per il
modulo puro che non gira da solo, la correzione dello stock in due
pezzi e le righe da non ammorbidire.
Collaudata: 5009 prove verdi, `collaudo_connettori.py` (35 verdi: il
giro VERO su database usa-e-getta con un negozio Shopify di cartone —
primo giro, moderazione pagata una volta sola, prezzo che cambia, la
prova regina dello stock, sparizioni, scudo, rete che cade,
collegamento che si dichiara rotto) e **30 mutazioni, 30 uccise**.
QUATTRO ERANO SOPRAVVISSUTE al primo giro, tutte sentinelle mie
scritte male, e sono la lezione da tenere: una cadeva sulla PROSA di
una docstring (`codice()` toglie i commenti `#`, non le docstring),
una contava le occorrenze senza guardare la POSIZIONE (il cambio
spostato dentro il ciclo restava «una volta»), una non distingueva
due cure che si coprivano a vicenda (serviva il tag inline DENTRO una
parola), e una certificava una guardia che il codice rendeva
irraggiungibile.
E IL DIFETTO PIÙ GROSSO L'HA TROVATO IL COLLAUDO, non la rilettura:
senza `rifletti_pendenti` la correzione dello stock si sarebbe
mangiata un pezzo a ogni riallineamento del venditore, fino a zero.
Le tappe che seguono: Woo, il registro agganciato in
`_incassa_ordine` con la notifica di vendita, endpoint + cassetto, e
il rodaggio con uno store di prova prima dell'accensione dal VPS.

E la TAPPA 3 (ago 2026): il dialetto WOOCOMMERCE — il traduttore coi
suoi tre tipi che non sappiamo trattare, la trappola di
`manage_stock: 'parent'`, le due facce dell'esaurito — più le due cose
che Shopify non ha: l'indirizzo che LO SCRIVE L'UTENTE (guardiano nel
trasporto, URL costruiti e mai seguiti, Basic auth) e soprattutto
L'IVA, che Woo non dichiara nel prodotto. Vedi la voce in
Architettura, «IL DIALETTO WOOCOMMERCE», per il perché
`prezzi_finiti_woo` ALZA invece di saltare le righe (una riga saltata
verrebbe spenta dalla riconciliazione: saltare tutto = spegnere la
vetrina in un colpo) e per la porta che manca, dichiarata e non
costruita (l'aliquota nel cassetto, tappa 5).
Collaudata: 5054 prove verdi (le nuove girano i pezzi invece di
guardarli — il traduttore sui suoi casi, `prezzi_finiti_woo` su un
negozio di cartone nei cinque, il lettore sul tetto) più
`collaudo_connettori.py` a 54 verdi (era 35) col SECONDO negozio
finto, dove la prova che conta è che coi prezzi al netto **nessun
annuncio si spegne**; e **20 MUTAZIONI, 20 uccise**, una per riga
sorvegliata. Il primo giro ne ha lasciate vive due — tutte e due
sentinelle mie, la prosa della docstring e il `.index()` che ESPLODE
invece di diventare rossa — e ha trovato DUE DIFETTI VERI che
leggendo non si vedevano: il catalogo troncato in silenzio a
duecento prodotti esatti, e l'invariante `venduto <=> quantita = 0`
che non valeva alla NASCITA (su Woo un prodotto già esaurito nasceva
'attivo' con zero pezzi: comprabile all'occhio, rifiutato alla cassa).
IN PRODUZIONE il deploy non cambia niente: nessuna colonna, nessuna
migrazione, e `CONNETTORI_NEGOZIO_APERTI` è ancora SPENTA nel codice.
DA GUARDARE al rodaggio, ed è il pezzo che in locale non si può fare:
un WooCommerce vero — i certificati di un self-hosted, i permessi
veri di una chiave (le impostazioni le legge una chiave «Read»), e
soprattutto un negozio configurato coi prezzi al netto, che è il caso
su cui questa tappa dice di no.

E la TAPPA 4 (ago 2026): il registro delle uscite, finalmente
SCRITTO. Dalla tappa 2 le pendenti si leggevano e si spegnevano, ma a
metterci una riga non c'era nessuno — quindi ogni vendita fatta qui
sarebbe stata rialzata dal sync entro l'ora, e sul pezzo unico il
'venduto' sarebbe risorto. Adesso `registra_uscita_negozio` scrive
nella stessa transazione dello stock, coi ganci in `_incassa_ordine`
(il funnel di tutte e tre le strade dell'accredito) e in
`_rimborsa_compratore`; il venditore legge in fondo alla notifica la
riga operativa «📦 Aggiorna il magazzino sul tuo negozio: −2 «Miele»»,
col PERCHÉ, che è la metà che conta. Vedi la voce in Architettura,
«IL REGISTRO SCRITTO», per il rimborso — la metà che si dimentica, e
senza la quale la tappa 4 introdurrebbe un difetto peggiore di quello
che cura — e per il SALDO COL SEGNO, il cambio di contratto che ne
discende (`- abs(...)` avrebbe nascosto due volte dei pezzi che ci
sono). Nello stesso giro i due fix Shopify che erano in coda alla
tappa 3: l'host della pagina successiva legato al collegamento, e il
tetto che non tronca più in silenzio.
Collaudata: 5105 prove verdi (le nuove GIRANO il registro su un
database di cartone — il giro chiuso vendita → rimborso → saldo — e i
due lettori Shopify sulle loro due strade) più
`collaudo_connettori.py` a 69 verdi (era 54), dove `_incassa_ordine`
e `_rimborsa_compratore` VERE scrivono il registro e il sync poi non
rialza niente; e 18 mutazioni, una per riga sorvegliata.
IN PRODUZIONE il deploy non cambia niente: nessuna colonna, nessuna
migrazione — `connettori_uscite` e i suoi stati esistevano già — e
`CONNETTORI_NEGOZIO_APERTI` è ancora SPENTA nel codice, quindi finché
nessuno collega un negozio il registro resta vuoto e i due ganci non
scrivono una riga.
DA GUARDARE al rodaggio: la PRIMA vendita vera su un annuncio
importato — che il venditore legga la riga del magazzino e che il
giro d'ora dopo non gli rialzi la giacenza — e il primo reso, che è
il caso in cui il registro deve tornare in pari da solo.

E la TAPPA 5 (ago 2026), che chiude la FASE 1: «🏪 Il tuo negozio»
nel Profilo e i suoi cinque endpoint — collega, pausa, aggiorna ora,
scollega, e la lista. Fin qui il collegamento si scriveva a mano nel
database (il collaudo lo faceva, e lo dichiarava). Vedi la voce in
Architettura, «IL CASSETTO E I SUOI ENDPOINT», per le due righe che
rendono questa tappa diversa dalle sorelle — la credenziale su un
sistema di un altro (whitelist in uscita, 503 senza chiave) e il «si
prova prima di crederci» — e per la dichiarazione che scende anche
sul pregresso, senza la quale un errore alla prima riga sarebbe per
sempre su duecento annunci.
Nello stesso giro le tre code rimaste: i cinque `.index()` di
`prove_connettori_sync` diventati `find()` (la forma che è già
esplosa due volte mangiandosi le sorelle), `PAUSA_PAGINE_SHOPIFY`
tolta perché prometteva una pausa che nessuno prendeva, e le
credenziali dei negozi entrate nello scanner dei segreti — le chiavi
WooCommerce (`ck_`/`cs_` più 40 esadecimali) e i token Shopify
(`shpat_` e i suoi tre fratelli): sono i primi segreti del progetto
che non passano da config_esempio.py, quindi si riconoscono dalla
FORMA come la nsec, e le lunghezze sono LARGHE in coda come per il
token del bot.
Collaudata: 5206 prove verdi (99 nuove, e una che ha CAMBIATO LATO
col perché scritto) più `collaudo_connettori.py` a 94 verdi (era 69),
dove gli endpoint girano PER DAVVERO — il token sbagliato che non
lascia una riga scritta, il JSON in cui le chiavi non compaiono né
come campo né come valore, la dichiarazione che scende sul pregresso,
la pausa, i due freni del bottone, l'estraneo che riceve la stessa
risposta di un id inesistente, e lo scollegamento che non lascia il
registro orfano. Più 23 mutazioni, una per riga sorvegliata.
E UN DIFETTO TROVATO DALLE PROVE E NON DALLA RILETTURA, che vale più
della cura: il cassetto era nato con un `_url_negozio` suo e quel nome
ESISTEVA GIÀ nel file (gli indirizzi parlanti) — Python non fiata,
l'ultimo `def` vince, e l'endpoint avrebbe chiamato in silenzio la
funzione del cantiere SEO. Da lì il censimento dei `def` duplicati.
IN PRODUZIONE il deploy non cambia niente: nessuna colonna, nessuna
migrazione, e `CONNETTORI_NEGOZIO_APERTI` è ancora SPENTA nel codice
— quindi il cassetto non compare a nessuno finché la riga non entra
nel config del VPS.
E LE SEI LEVE SONO IN `config_esempio.py`, col loro perché: cinque
erano costanti nel codice e sono diventate leve vere prima di
dichiararle, che una riga da copiare la quale non cambia niente è
peggio di una riga che manca. A tenere chiuso il punto c'è
`prove_config_esempio`, che censisce le due direzioni fra il codice e
il file da cui si copia — vedi la voce in Architettura. Il giorno dopo
(ago 2026, decisione di Andrea) si sono chiusi anche i SEI DEBITI di
altri cantieri che quel censimento aveva trovato: la revisione, la
busta di consegna e i solleciti delle firme Nostr sono dichiarati
ognuno nella sua famiglia, e l'elenco delle eccezioni è VUOTO — che è
l'affermazione più forte. E il pannello «⚙️ Stato delle leve» ha
imparato i connettori: la porta nel primo gruppo, i cinque numeri in
un gruppo loro. Sei mutazioni in più, una per riga sorvegliata, ognuna
rossa da sola.
DA GUARDARE quando si accenderà, ed è il pezzo che in locale non si
può fare: il primo collegamento vero a uno store di sviluppo — che il
401 di un token sbagliato arrivi come un 400 leggibile, che il
WooCommerce coi prezzi al netto si rifiuti dicendo perché, e che il
primo giro dopo il collegamento entri da solo senza aspettare l'ora.

La barra delle pillole si legge (ago 2026, due cose dal campo): la
pillola del reparto scelto si porta al CENTRO della fila invece di
restare a sinistra — un giudice solo per lei e per la card della
striscia, coi rect e non con `offsetLeft`, che chiude di striscia un
centro sbagliato della striscia sopra i 520px — e il fondo della
testata e della barra diventa OPACO, che a `.92` col blur la vetrina si
vedeva passare dietro. Col fondo pieno se n'è andato anche il
`backdrop-filter`, che sopra una carta opaca non può cambiare un pixel.
Vedi Architettura, «LE CATEGORIE IN HOME», per la trappola
dell'offsetParent e per la risposta all'ultima pillola: il clamp del
browser la ferma a filo del bordo destro, intera.
Collaudato: 5067 prove verdi (14 nuove, una ROVESCIATA col perché — la
formula non vive più dentro la striscia) e UNDICI MUTAZIONI, una per
riga sorvegliata, ognuna rossa da sola, di cui due prese SOLO dal banco
che fa girare il giudice (il centro che diventa un quarto, il verso del
conto rovesciato: la forma resta giusta e a dirlo può essere solo
l'esecuzione). Più il giro dal vivo col server locale su una COPIA del
database, a 320/360/375 nei due temi: centro esatto alle tre larghezze,
l'ultima pillola intera coi suoi 16px d'aria, il fondo `rgb()` pieno
senza blur e la vetrina che non passa più (chiesto a
`elementsFromPoint`, non all'occhio), zero errori JS.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna leva, nessuna
rotta — solo client.

Il like sulle funzioni in arrivo (ago 2026): sulle due pagine «in
arrivo» si preme «🔔 Avvisami» e il totale si vede a tutti — serve a
sapere quale cantiere aprire per primo. Il bottone è l'UNICO di quelle
pagine: l'uscita se n'è andata, che la nav ha già Esplora. Le quattro decisioni di
Andrea: il like è ANCHE un'iscrizione (il testo promette l'avviso, e
il debito è scritto sulla tabella perché il cantiere che accenderà la
funzione lo mantenga), l'anonimo in vetrina vede il numero e col tocco
viene invitato a entrare, a zero si dice «Sii il primo» invece di uno
zero, e le righe restano per sempre. Il punto che decide è una TABELLA
e non due colonne: «un like per persona» è la PK, e la funzione in
arrivo di domani costa zero migrazioni. Vedi Architettura, «LO
ASPETTO», per la whitelist del nome, per il segnaposto che tiene vera
la sentinella del markup fisso, e per il nome `interesse` che NON è
`attesa` (nel client quella parola significa già il velo che blocca).
Collaudato: 5256 prove verdi (46 nuove, fra cui due famiglie
ESEGUIBILI — il toggle e la fusione su sqlite in memoria, e
`renderInteresse` girata con node sui suoi sei stati: le sentinelle
dicono che i pezzi esistono, mai che rispondano giusto) e **DICIOTTO
MUTAZIONI, diciotto uccise**, una per riga sorvegliata — whitelist
tolta e spostata dopo l'INSERT, PK tolta, UPDATE secco al posto della
liturgia, migrazione tolta, `tg_id` rimesso nel conteggio, identità
resa facoltativa, totali spostati fuori dalla busta, ±1 ottimistico
nel client, DEMO che disegna, «Sii il primo» sostituito da uno zero,
promessa tolta dal testo, render tolto dal ramo di `go()`, innerHTML
al posto di textContent, ghost tornato pieno, guardia della vetrina
tolta, bandierina sostituita dal velo dei sats, debito cancellato.
Più il giro col server VERO su un database usa-e-getta (15 verifiche:
metti/togli, i due canali, la whitelist che risponde 400 e NON scrive,
il 401 senza identità, e l'anonimo che vede il numero ma non chi ha
votato) e il giro visivo via CDP a 320/360/375 nei due temi — zero
sbordo, zero scorrimento laterale, zero errori JS — coi casi che il
testo non può dire: il tocco che vota, il ritorno DALLA CRONOLOGIA
(che non passa da `vaiP2P` ed è la ragione per cui il render sta nel
ramo di `go()`), la vetrina che apre l'invito e la DEMO che non
disegna niente.
IN PRODUZIONE basta il deploy: la tabella nasce vuota, nessuna leva,
nessuna migrazione di dati, nessuna rotta pubblica nuova — e finché
nessuno tocca il bottone non cambia niente di quel che si vede.
DA GUARDARE al primo giro: i primi like veri, e soprattutto che i
numeri delle due pagine siano DIVERSI — è quella la domanda per cui
il cantiere esiste.

La porta del banner si anticipa pagando (ago 2026, tappa 2): 10.000
sats e la porta si apre subito — ed è il PRIMO INCASSO che Barattolo
fa per sé, perché finora ogni fattura in entrata era escrow per conto
di terzi. Le decisioni di Andrea: una tantum ora ma la colonna è una
DATA (il giorno dell'abbonamento non serve migrare niente), due strade
per la stessa porta (chi arriva al livello ce l'ha gratis: il giudice
diventa un OR), il rimborso mai automatico ma possibile al moderatore,
e il paySheet coi due testi — «a garanzia … finché non confermi di aver
ricevuto l'oggetto» su una tassa sono due frasi false. Vedi
Architettura, «LA PORTA SI ANTICIPA PAGANDO», per la tabella
`pagamenti` (che è il vero contenuto del cantiere: senza, il metodo di
riconciliazione con LNbits diventava falso il giorno stesso e ogni
banner pagato sembrava un orfano), per l'endpoint che NON ha un 400
dopo la fattura, e per la PURGA che non si fa.
TRE COSE TROVATE COSTRUENDO E NON LEGGENDO, ed è la parte da
ricordare: 1) LA FUSIONE — il nativo Nostr che paga e poi collega
Telegram perdeva i suoi 10.000 sats, e a dirlo è stato il censimento
delle tabelle figlie; 2) IL VESTITO DEL paySHEET — nessuno rimetteva
il testo dell'escrow, quindi dopo una tassa l'ordine successivo
prometteva «questi sats non sono un deposito» su un deposito, e la
cura non è stata una chiamata in tre posti ma una regia sola dentro
`mostraQr`; 3) LA CONFERMA DEL RIMBORSO che non faceva NIENTE — la
chiave sbagliata (`azione:` invece di `poi:`), un foglio che si apre,
si legge e chiude senza agire: da lì la sentinella che chiede a tutti
e dodici i chiamanti di portare la loro azione.
Collaudato: 5358 prove verdi (erano 5251) e VENTICINQUE MUTAZIONI, una
per riga sorvegliata, ognuna rossa da sola — e la tortura ha fatto il
suo mestiere due volte: ha trovato tre sentinelle che guardavano se una
cosa ESISTE invece che se è USATA, e soprattutto IL BANCO STESSO
MENTIVA (torturava una copia mai rinfrescata, quindi le mutazioni
giravano su un codice di ore prima: adesso ricopia sempre e si ferma se
il conto della baseline non combacia con la repo). Più
`collaudo_sblocco_banner.py`, 54 verdi con LNbits simulato: il giro
vero su database usa-e-getta, i due rami dell'orologio, la lapide col
riacciuffo, il rimborso nei suoi quattro casi (non parte → la porta
resta APERTA; riesce → porta chiusa e insegna spenta; il secondo giro
non paga due volte; chi ha il livello tiene la porta), la ronda che
tace e la regressione di chi ha il livello. E il giro dal vivo via CDP
a 320/360/375 nei due temi.
IN PRODUZIONE il deploy fa girare due migrazioni additive (la tabella
`pagamenti` e la colonna, a 0/'') e NON cambia niente: la funzione resta
dietro `BANNER_NEGOZIO_ATTIVO`, che nasce spenta. Il prezzo si spegne
da solo con `BANNER_PREZZO_SATS = 0`, e allora resta la sola strada del
livello. DA GUARDARE al primo giro vero: il primo sblocco pagato dentro
Telegram — che l'avviso «💰 Sblocco banner pagato» arrivi ai moderatori
col numero del pagamento, e che la ronda TACCIA; e la riconciliazione
su LNbits, dove il memo «Barattolo sblocco banner #tg_id» dev'essere
l'unico incasso nuovo senza una riga in `ordini`/`rilanci` — e averla
invece in `pagamenti`.

La foto del contenuto digitale, e la finestra per correggerlo (ago
2026, terzo punto del giro dal campo, ora costruito): un buono
cartaceo si riscatta col codice a barre, e trascriverlo a mano non
basta — il venditore allega la foto, e il testo resta obbligatorio,
quindi il percorso della RIVELAZIONE non cambia di una riga. La foto
vive cifrata in una cartella sua e non esce da nessuna parte tranne
la sua rotta; il compratore la vede solo DOPO aver rivelato, perché
quel codice a barre È il bene comprato.
E IL CONTENUTO SI CORREGGE FINCHÉ NESSUNO L'HA GUARDATO — decisione
di Andrea che ROVESCIA il limite che il quadro aveva dichiarato
(«nessuna correzione dopo la consegna»), e aveva ragione lui: il
principio era giusto e il confine sbagliato. La prova in disputa
nasce con la RICEVUTA, quindi fra la consegna e la rivelazione c'è
una finestra vera in cui correggere non tocca niente — **il confine è
`consegnato = 0`, non lo stato.** Vedi Architettura, «IL CONTENUTO SI
LEGGE DOVE COMPARE», per le righe da non ammorbidire: l'ancora della
finestra che non si muove, la chiave assente che conserva il testo, e
soprattutto il 'delivered' che sta nella SELECT APPOSTA.
IL GIRO DAL VIVO HA TROVATO QUEL CHE LA LETTURA NON VEDEVA, ed è la
parte da ricordare: la guardia della ricevuta NON POTEVA SCATTARE —
la rivelazione scrive `consegnato` e `stato='delivered'` nello stesso
UPDATE, quindi l'ordine rivelato usciva già dalla SELECT e chi
correggeva tardi si sentiva dire «Operazione non permessa», muto
proprio dove serve un perché. Era una guardia che prometteva d'essere
esercitata e non lo era mai. E il TESTO APPENA SCRITTO si perdeva
allegando la foto, perché il ridisegno rifà la textarea.
Collaudato: **5448 prove verdi** e **25 MUTAZIONI, 25 uccise**, una
per riga sorvegliata — ed è stata la tortura a trovare il difetto
peggiore, il gate scritto `== "shipped"` che avrebbe fatto cadere un
ordine 'delivered' nel ramo della CONSEGNA, cioè riscritto stato e
contenuto dopo la rivelazione. Più DUE banchi eseguibili col server
acceso: le rotte vere su un database usa-e-getta (49 verdi — il testo
cifrato `f2:`, i byte cifrati sul disco, il compratore che non
sbircia, l'estraneo indistinguibile dall'ordine inesistente, le
quattro correzioni col testo che si conserva, l'ancora ferma, il file
vecchio che se ne va, la porta che si chiude dopo la rivelazione, il
moderatore in disputa) e il giro nel BROWSER via CDP (29 verdi, zero
errori JS: il file scelto col chip, la consegna, la correzione con la
pagina che non salta, l'immagine aperta in pagina, e nessuno sbordo a
320/360/375 nei due temi).
IN PRODUZIONE il deploy fa girare cinque migrazioni additive su
`ordini` (tutte a 0/'') e crea la cartella `contenuti/`; nessuna leva
nuova, nessuno stato nuovo, e il client vecchio in cache non conosce
le due chiavi in più e si comporta come oggi. ⚠️ Sul VPS
`CHIAVE_CONTENUTI_DIGITALI` dev'esserci, o le foto si scrivono in
chiaro come già fa il testo — la riga d'avvio lo dichiara. DA
GUARDARE al primo giro: il primo buono cartaceo vero consegnato con
la foto dentro Telegram, e che il compratore la veda solo dopo aver
rivelato.
LA RIGA DEL CAMPO FILE, PER TUTTI E DUE (ago 2026, il giro dopo,
chiesto da Andrea): il chip col nome e il «togli» andavano a capo
sotto il bottone e il «togli» finiva centrato a tutta larghezza,
sembrando un secondo bottone principale. MISURATO prima di toccare —
**tre righe e 152px**, col bottone e il link larghi 254px per un chip
che ne chiede 155 — e la causa è che `.btn` nasce `width:100%`, che
dentro un flex si prende la riga intera.
UNA CLASSE E NON DUE `style=` GEMELLI (`.campo-file`): i due campi —
la busta e la foto del contenuto — sono lo stesso mestiere, e copiati
a mano divergono al primo ritocco (la lezione di `.fila-promesse`).
Il bottone passa a `.btn.mini`, che esiste già ed è nato per questo:
«la ricetta del ghost in formato da riga».
DUE COSE LE HA CORRETTE IL GIRO A SCHERMO, e nessuna delle due si
vedeva leggendo il foglio. 1) SENZA IL WRAP il nome si riduceva a
«🖼 …» — **31px MISURATI a 320** — che è peggio del difetto di
partenza: lì almeno si leggeva. Col wrap il chip non ci sta alla sua
base e scende INTERO. 2) IL NOME E IL «TOGLI» SONO UN ITEM SOLO
(`.cf-chip`): a 375 il chip restava accanto al bottone e il «togli»
scendeva DA SOLO — il gesto lontano dalla cosa su cui agisce.
E I PUNTINI SONO DEL NOME, NON DELLA PROSA: il ramo del «togli in
attesa» ci mette una FRASE, e «…verrà tolta al salvatag…» è peggio di
una frase a capo. La regola vive su `.hint.mono`, che è il vestito del
nome file; la frase resta libera di andare a capo.
Risultato: **87px invece di 152**, uguale a 320, 360 e 375 — bottone
compatto sopra, «nome — togli» accanto sotto.
Provato: 5481 verdi (7 sentinelle nuove, fra cui il CENSIMENTO che i
campi file sono DUE — il terzo di domani viene a leggere questa riga
invece di ricopiarsi uno stile) e CINQUE MUTAZIONI, cinque uccise;
più il giro dal vivo a 320/360/375 nei due temi su tutti gli stati dei
DUE campi (senza file, file scelto, file già caricato, «togli» in
attesa), zero errori JS e nessuno sbordo. ⚠️ L'ancora della mutazione
del chip è AMBIGUA apposta — la coda del template è identica nei due
gemelli, che è il punto del cantiere: se ne muta UNA e la sentinella
che ne conta DUE diventa rossa.

Il reparto si condivide col tocco lungo, e l'anteprima è la sua (ago
2026, due decisioni di Andrea in un giro): via il bottone «Condividi la
categoria» — costava una riga verticale dentro OGNI reparto, ~37px
tolti alla griglia — e al suo posto il tocco lungo sulla card della
striscia, che non costa un pixel (misurato: la sezione resta 157px
esatti a 320/360/375). Il costo della scopribilità è accettato, e a
pagarlo il meno possibile c'è un TOAST una-tantum al primo ingresso in
un reparto: l'unica forma a zero pixel di layout, con la guardia su
`DEMO` e non su `hintAttivi()` perché in vetrina il gesto funziona e
chi arriva dal web è precisamente chi condivide. La convivenza coi due
gesti che la card aveva già è la bandierina `premutaFatta`, azzerata a
ogni `pointerdown`: al rilascio il browser manda comunque un click, e
senza quella riga chi condivide si ritroverebbe anche dentro il reparto
— o fuori, se la card premuta era quella accesa. E l'anteprima del link
adesso porta la FIGURA del reparto invece dell'icona generica: 29 JPEG
opachi 1200×630 composti una volta sola da `og_categorie.py` e
committati, con la rotta a whitelist derivata e il ripiego sul brand
quando il file non c'è. Vedi Architettura, «IL REPARTO SI CONDIVIDE»,
per le due righe da non ammorbidire (il `preventDefault` prima della
bandierina, l'esistenza chiesta al disco) e per le tre lezioni di
metodo del banco che mentiva a giri alterni.
Collaudato: 5791 prove verdi sull'ALBERO ISOLATO — HEAD più i soli
hunk di questo cantiere, che è la sola cosa che risponde a «questo
commit, da solo, sta in piedi?» visto che la copia di lavoro è
condivisa con un'altra sessione — e **VENTI MUTAZIONI, venti uccise**,
una per riga sorvegliata. Più due giri dal vivo via CDP con eventi
TOUCH veri (`Input.dispatchTouchEvent`, così il click dopo il rilascio
lo genera il BROWSER, che è precisamente la cosa da verificare): 17/17
sul gesto — il tocco corto che filtra, il lungo che condivide LA CARD
PREMUTA senza far scattare il filtro, il tocco dopo che torna a
filtrare, lo scorrimento che annulla, «Tutto» che resta fuori,
l'accenno che arriva una volta sola — e 17/17 sui bordi (DEMO inerte,
tasto destro del mouse conservato, le misure a tre larghezze nei due
temi). Più `anteprime.py`, che simula gli User-Agent di Telegram,
WhatsApp, Facebook, Slack e dei client Nostr con la loro lettura
parziale: tutti e cinque vedono la stessa cosa, tutti e tre i limiti
dicono «card grande», e l'ultimo meta cade al byte 1401.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva — i 29 JPEG viaggiano col commit.
VERIFICATO DAL VIVO (ago 2026, Andrea su Telegram e WhatsApp): un link
di reparto incollato in chat mostra la FIGURA del suo reparto in tutte
e due le app. Non è più da guardare — era il pezzo che da qui non si
poteva fare, perché l'anteprima si vede solo dal vivo e le due app la
trattano diversamente.
LA NOTA SUL CACHING RESTA, e vale per ogni anteprima futura: Telegram e
WhatsApp tengono la card per giorni e dal nostro lato non si bustano,
quindi si prova UNA VOLTA SOLA per slug — se qualcosa non va si
ricontrolla su un ALTRO reparto invece di riprovare sullo stesso.

E IL GESTO NON SCATTAVA SUL TELEFONO (set 2026, difetto dal campo:
Andrea su Telegram Android, «tenendo premuto non succede niente»). La
condivisione era scagionata dalla prova incrociata — il bottone
«condividi» dell'annuncio, che è la STESSA scala, funzionava — quindi
il colpevole era il gesto: `PREMUTA_MS` a 500 pareggiava i 500ms del
riconoscitore di lungo di Android, la WebView si prendeva il tocco e
il suo `pointercancel` spegneva il timer un attimo prima che sparasse.
Dentro Telegram il `contextmenu` non arriva nemmeno, quindi la riga
che lo ferma non aveva modo di girare. La correzione sono TRE righe e
non una: il timer a 350ms (prima del fondo di sistema), lo scarto a
8px (la soglia oltre cui il browser scorre, che rende leggibile il
cancel: se il gesto è ancora armato non è uno scorrimento, è il
sistema che ruba — e allora lo si onora, con un fondo di 250ms) e il
`contextmenu` col dito che scatta invece di limitarsi a spegnere il
menu. Lo scatto è finito in un posto solo (`premutaScatta`) coi suoi
tre chiamanti, e col mouse il tasto destro ora SPEGNE il gesto invece
di rischiare una condivisione a sorpresa. La lezione di metodo è la
riga «da guardare dal telefono», rimasta da guardare un mese: il CDP
con `Input.dispatchTouchEvent` non sveglia il riconoscitore nativo, e
un tocco lungo si collauda sul TELEFONO VERO. Vedi Architettura, «IL
REPARTO SI CONDIVIDE», «IL FONDO DI SISTEMA».
Collaudato: 8582 prove verdi e DIECI MUTAZIONI, dieci uccise — una per
riga sorvegliata (il timer che torna a 500, lo scarto che torna a 10,
il fondo azzerato, il cancel che torna a spegnere e basta, il cancel
che non guarda più il mouse, il tasto destro che non spegne, lo scatto
che condivide prima di spegnersi, la bandierina non alzata, la guardia
d'ingresso tolta, il contextmenu che non scatta). Più un GIRO DAL VIVO
su un banco col markup vero e il gesto vero, guidato via CDP con eventi
TOUCH (`Input.dispatchTouchEvent`): 12/12 — il tocco corto che filtra,
il lungo che condivide la card premuta senza far scattare il filtro, il
tocco dopo che torna a filtrare, il `touchCancel` a dito fermo che
condivide lo stesso (è la WebView di Telegram), quello troppo presto
che non è un gesto, lo scorrimento che annulla, «Tutto» che resta
fuori. E LA CONTROPROVA, che è la parte che conta: lo STESSO banco col
codice di ieri, col cancel a 470, 440, 400 e 360ms — quattro volte
silenzio, e quattro volte la condivisione col codice di oggi. Il
difetto si riproduce e la correzione lo toglie.
⚠️ IL BANCO È UN MODELLO, non il telefono: il cancel lo manda il
collaudo, non il riconoscitore nativo, e la distanza fra i due
traguardi la scegliamo noi. Dice che il gesto ARRIVA PRIMA e che la
strada del cancel funziona, NON che sul telefono di Andrea sia andata
esattamente così — quello lo dice solo il telefono.
DA GUARDARE dal telefono, ed è l'unico posto dove si può: il tocco
lungo che ora condivide dentro Telegram Android, e che sul web copia
il link negli appunti (l'ultimo gradino della scala).

Il punto di ritiro si concorda (ago 2026, caso vero dal campo): il
venditore che trova un punto sbagliato — un locker che non esiste, o di
una rete che non serve — ora può dirlo e proporne fino a tre; chi compra
ne accetta uno con un tocco, che è il gesto che ha già, e quel gesto
CHIUDE l'obiezione. Zero costo sugli ordini che vanno bene, zero stati
nuovi, zero rotte per accettare. E le due righe che rendono vera la
promessa: mentre la palla è del compratore il venditore non viene più
rimproverato per la merce mai partita, e a bussare è un promemoria coi
destinatari invertiti. Vedi Architettura, «IL PUNTO SI CONCORDA», per la
forma presa dall'appuntamento e non dalle offerte (col perché), per il
🧊 che cade al giorno 11 — dopo la coda dei fermi — e per quel che NON
si chiude: il compratore che sparisce, dove al tetto si tace e l'unica
uscita resta la sua disputa.
Provato: 5891 prove verdi (le nuove) e **30 MUTAZIONI, 30 uccise** — la
sola sopravvissuta al primo giro era una sentinella mia che cercava il
NOME della funzione nell'orologio invece della riga, cioè la lezione del
reaper ripagata alla lettera. Più `collaudo_punto_concordato.py` (46
verdi: il giro vero sul server VERO su un database usa-e-getta, i
rifiuti e l'anti-oracolo sul database vero, i due promemoria e la ronda
che tace), TORTURATO a sua volta su sei mutazioni; e il giro dal vivo a
320/360/375 nei due temi (96 verifiche, zero sbordo, zero errori JS),
che ha trovato quel che le misure non vedevano — le proposte
incolonnate strette a destra del testo, perché `.trust-note` è un flex
ROW: non sbordava, quindi le sonde erano verdi.
IN PRODUZIONE basta il deploy: sette colonne additive nascono coi loro
default (obiezione spenta per tutti), una leva sola col default nel
codice, nessuna migrazione di dati, nessuno stato nuovo — e un client
vecchio in cache non conosce i campi e si comporta come oggi. DA
GUARDARE al primo giro: la prima obiezione vera dentro Telegram — che
il compratore riceva la notifica, e soprattutto che il venditore
SMETTA di ricevere il promemoria della merce mai partita.

  LA CLASSIFICA DEL MERCATINO 🏆 (ago 2026): i migliori in una pagina
  raggiungibile dal PODIO in testata (dall'ago 2026 — nacque in fondo
  al Profilo, vedi la voce della card del barattolo per il trasloco),
  ordinati per reputazione — non la sola
  media dei feedback, ma pesata col commercio. ROVESCIA una decisione
  scritta (`proposte/roadmap-gamification-aste.md`: «classifica fuori
  dalla v1, farmare oggi è gratis: misurerebbe il tempo libero, non il
  commercio»), e il modo in cui la rovescia È la sostanza del cantiere:
  non «facciamola lo stesso» ma CAMBIARE COSA SI MISURA, così che
  farmare non paghi più.
  LA FORMULA vive in un giudice PURO, `_classifica_utenti` — prende
  righe e ritorna la lista ordinata, niente database dentro: è quel che
  la fa girare in CI e la fa riusare allo script della tappa 0.
    punteggio = F × (1 + PESO · C · S)
    F = (persone · media + K · M) / (persone + K)      la FIDUCIA
    C = log10(1 + xp_ordini) / log10(1 + RIF)          il COMMERCIO
    S = persone / (persone + KD)                       lo SMORZAMENTO
  `F` È UNA MEDIA BAYESIANA e risponde alla frase che ha aperto il
  cantiere: uno con 5,0 su due recensioni non vale uno con 4,8 su
  cinquanta. Una media con pochi voti si tira verso quella del
  mercatino, e più persone ti votano più la tua media conta come tua.
  Si spiega in una riga — «una media vale di più quando la dicono più
  persone» — ed è la formula del Top 250 di IMDb, non un'invenzione di
  casa.
  `persone` E NON `n_feedback`, ed è metà del freno: quaranta voti da un
  account solo pesano come UNO. La colonna `utenti.n_recensori` esiste
  dall'ago 2026 proprio per questa domanda, ma la classifica NON la
  legge — la ricalcola coi soli recensori reali, dalla tabella
  `feedback`, che è la fonte: quella colonna è una cache arrotondata a
  un decimale e può restare indietro.
  MOLTIPLICATIVO E NON ADDITIVO: il commercio AMPLIFICA la fiducia
  invece di sostituirla, quindi chi ha una media bassa non risale
  comprando volume. È la riga che tiene fuori dalla cima «la persona
  sbagliata» — nel confronto la formula additiva metteva PRIMO chi ha
  4,2 di media e 120 affari.
  IL LOGARITMO COMPRIME il commercio: senza, un affare da 4.000 €
  varrebbe più di trecento piccoli. Con: da 100 a 1.000 XP il bonus
  passa da +16% a +25%, da 1.000 a 10.000 arriva a +33% — raddoppiare
  il volume non raddoppia niente.
  LO SMORZAMENTO DELLA FIDUCIA LARGA (ago 2026, `CLASSIFICA_KD`): il
  bonus del commercio vale quanto è LARGA la fiducia che amplifica —
  con `KD=2` chi ha un recensore solo se ne prende un terzo, chi ne ha
  cinque cinque settimi, chi ne ha venti quasi tutto. La fiducia di uno
  solo è un'opinione, non un curriculum.
  SI SMORZA IL BONUS E NON LA FIDUCIA, ed è la riga da non ammorbidire:
  la media resta la media, e chi non commercia non viene punito due
  volte. Applicato a tutto il punteggio (o alla sola fiducia) chi ha un
  recensore scenderebbe SOTTO la media del mercatino pur avendola presa
  identica, che è un'altra cosa da quella che si vuole dire.
  E `persone` E NON `voti`, per la ragione della bayesiana un gradino
  più su: quaranta voti da un account solo devono pesare come UNO.
  NASCE A ZERO, e a zero `persone/(persone + 0)` fa **1 esatto per
  chiunque**: i punteggi restano IDENTICI BIT PER BIT a quelli di prima
  dello smorzamento — verificato, il `5.260264460129354` inchiodato in
  `prove.py` non si muove di un decimale. È voluto e non timidezza: il
  valore si SCEGLIE guardando i numeri veri (`python
  classifica_prova.py`, sezione 3, che affianca le tarature), che è il
  patto con cui fu misurato K. Quindi il deploy non sposta un solo
  punteggio, la misura passa dal GIUDICE VERO invece che da una
  simulazione, e la scelta dopo la misura è una riga nel config del VPS
  — zero codice.
  E LA MISURA È STATA FATTA: **KD = 2** (ago 2026, decisione di Andrea
  sui numeri veri del VPS) — chi ha un recensore solo si prende un
  TERZO del bonus, «che si sente senza azzerare». LE TRE TARATURE
  DAVANO LO STESSO ORDINE, e questo è il fatto da tenere: con quasi
  tutte le medie a 5,00 a ordinare è già il commercio, quindi a
  decidere non è stato l'ordine ma la SEVERITÀ — **11 persone su 16
  hanno un recensore solo**, e con KD=3 quella severità toccherebbe
  quasi tutti in un mercatino ancora giovane. È esattamente la domanda
  per cui esiste la §3b, ed è anche il segnale per rivedere il numero:
  si ritara quando quel rapporto cambia, non a calendario.
  ⚠️ E IL VALORE VIVE NEL CONFIG DEL VPS, non nel codice: nel codice il
  default resta 0. Chi legge `CLASSIFICA_KD = 0` in `server.py` e ne
  conclude che lo smorzamento è spento sta guardando il posto sbagliato
  — lo dice il pannello «⚙️ Stato delle leve», che chiede al valore
  VIVO e non alla costante (la trappola che quella pagina esiste per
  non far ricadere). Stessa famiglia di `MAX_PREFERITI`: una riga
  esplicita nel config del VPS vince sempre sul default.
  ⚠️ IL DEFAULT NON SI SCRIVE NEL COMMENTO che lo spiega:
  `classifica_prova._leggi_giudice` risolve le leve con una `re.search`
  sul TESTO di server.py e prende la PRIMA occorrenza, quindi un
  `CLASSIFICA_KD = 3` dentro una frase gli ruberebbe il numero in
  silenzio. Si dice «a zero» in prosa, e la cintura è la regex ancorata
  all'ASSEGNAZIONE (`^[ 	]*NOME\s*=`, con `re.M`): il rischio non è
  teorico — nel file c'è già un `CLASSIFICA_PESO_XP = 0` dentro un
  commento, innocuo solo perché sta DOPO la sua assegnazione.
  ⚠️ E `kd is None` E MAI `kd or CLASSIFICA_KD`: qui lo zero pesa il
  doppio delle sorelle, perché è proprio il DEFAULT — con l'`or` un
  `kd=0` passato a mano ricadrebbe sulla costante, e la leva spenta
  smetterebbe di essere spegnibile dal chiamante. Più il `max(…, 0)`,
  che non è cosmesi: un KD negativo nel config azzera il denominatore e
  fa cadere con un 500 una pagina PUBBLICA, che non è avvolta in nessun
  fail-open.
  E SOLO GLI XP DEGLI ORDINI (`tipo='ordine'`, gli altri sei tipi
  restano fuori): sono gli unici che costano un pagamento Lightning
  vero. Visita giornaliera, pubblicazione, profilo completo e distintivi
  misurano PRESENZA e non commercio — e sono precisamente quelli che si
  farmano con un tocco. Il registro `xp_eventi` ha già la colonna: è una
  WHERE, non un cantiere.
  K = 5 E NON 3, ed è MISURATO e non scelto a orecchio: a K=3 la frase
  che ha aperto il cantiere è FALSA — 5,0 da due persone rende 4,7966 e
  4,8 da cinquanta rende 4,7921, cioè il primo passa davanti. Da 4 in su
  regge. Il numero sta nel config col conto accanto.
  ⚠️ E C'È UN LIMITE DELLA BAYESIANA da sapere PRIMA di tarare K, che è
  la scoperta del cantiere: quando le due medie stanno una SOPRA e una
  SOTTO la media del mercatino, NESSUN K le inverte — K decide solo
  quanto chi ha pochi voti viene tirato verso M. Due casi del banco
  fallivano proprio per questo (la media globale, calcolata sui soli due
  utenti di prova, stava in mezzo), e da lì è nato il `fondo()` che
  semina utenti di sfondo. C'è la prova che tortura il limite su K = 1,
  5, 50, 500.
  IL PAREGGIO NON LO SCIOGLIE LO SMORZAMENTO, e non poteva: quando la
  media è uguale a quella del mercatino la fiducia vale ESATTAMENTE M
  per qualunque `persone` (è il limite qui sopra visto dall'altro lato),
  e senza XP d'ordine il bonus è zero — quindi lo smorzamento
  moltiplica uno zero. È il mercatino di oggi, dove hanno tutti 5,00 e
  parecchi hanno zero XP: lì due righe hanno gli stessi punti BIT PER
  BIT, ed è il caso che ha aperto il cantiere (Libertoshi con un
  recensore e Luca con due, a decidere l'id).
  LA CHIAVE È `persone → affari → id` (decisione di Andrea): prima le
  PERSONE, che è la stessa cosa che dice lo smorzamento un gradino più
  su — la regola del cantiere applicata al pareggio, non una regola
  nuova da spiegare — e senza XP è l'unica che separa.
  E VA DETTO COSA SI STA SCEGLIENDO col secondo criterio: **LA
  FREQUENZA BATTE IL VALORE** — due affari da 15 € vanno davanti a uno
  da 40, che danno gli stessi XP. Non è ovvio, ed è meglio di un id, che
  non significa niente.
  LA MEDIA È STATA PROVATA IN QUELLA CHIAVE E TOLTA, ed è una misura e
  non un gusto: a pari persone due medie diverse danno GIÀ punti diversi
  (senza XP il punteggio È esattamente la fiducia), quindi in terza
  posizione sarebbe codice morto — una guardia che promette d'essere
  esercitata e non lo è mai, la famiglia dell'`except` irraggiungibile
  di `_npub_venditore`. Il fatto è stato portato ad Andrea invece di
  implementarlo in silenzio, e la decisione è cambiata di conseguenza.
  L'ID RESTA IN CODA E NON È UN MERITO: è il determinismo — due righe
  identiche non devono scambiarsi di posto a ogni richiesta.
  ⚠️ E LA PROVA DEL PAREGGIO DI IERI ERA UNA TAUTOLOGIA, la sesta della
  famiglia che questo repo ha già smascherato: chiamava tre volte lo
  stesso giudice sugli stessi dati e restava VERDE anche togliendo
  `r["id"]` dalla chiave, perché `sort` è stabile e i dizionari sono
  ordinati. Al suo posto si cambia l'ORDINE D'ARRIVO DEI VOTI, che è
  l'unica cosa che l'id deve neutralizzare — e la mutazione che toglie
  l'id adesso la fa rossa.
  IL FRENO È IL RECENSORE REALE (scelta di Andrea): conta come PERSONA
  solo chi ha a sua volta concluso almeno un affare con QUALCUN ALTRO
  che non sia me. Va più lontano di quanto sembri — il farmer che si
  fabbrica venti identità e se le fa votare NON ENTRA AFFATTO: nessuna
  di quelle venti ha un affare con un terzo, quindi i suoi recensori
  reali sono zero, e a zero non si passa il gate d'ingresso.
  ALZA IL COSTO, NON LO CHIUDE, E VA DICHIARATO: il farmer può far
  commerciare le sue identità FRA LORO prima di votarsi — due ordini in
  più a testa e diventano tutte «reali». Il costo cresce (più pagamenti,
  più fee, più tempo), la cosa non diventa impossibile. A chiuderla
  davvero sarebbe la transitività da un seme fidato — un web-of-trust
  vero, che è un cantiere suo — oppure la COMMISSIONE, che è il freno
  che il roadmap aspettava e che oggi è a 0.
  ⚠️ IL FRENO ECONOMICO ASPETTA UN EVENTO, NON UN CANTIERE (ago 2026,
  decisione di Andrea di metterlo a verbale): il giorno che si accende
  `COMMISSIONE_PERCENTO` questa riga diventa vera DA SOLA — farmare
  comincia a costare una percentuale su ogni ordine finto, senza che
  nessuno tocchi la classifica. Chi rilegge fra sei mesi non deve
  cercare qui un lavoro da fare: deve solo sapere che la leva è quella.
  GLI ALTRI TRE FRENI erano già in casa: i soli XP d'ordine, la
  bayesiana che pesa le persone, e la riga «da N persone» accanto al
  nome, che fa autodenunciare chi farma — la stessa informazione già
  decisa per il conteggio dei recensori.
  IL GATE D'INGRESSO è ≥1 affare concluso e ≥1 voto da un recensore
  reale. I COMPRATORI CI SONO, non solo i venditori: gli affari contano
  da tutte e due le parti, e il nome di chi compra è già pubblico da
  quando i feedback del negozio dicono chi li ha scritti. Da guardare al
  primo giro: se dà fastidio, il gate diventa `vendite_ok >= 1`.
  COSA NON ESCE MAI, ed è la parte da non allentare: il `tg_id` (che in
  vetrina non compare da nessuna parte), gli XP — `/api/negozio` li
  toglie apposta dal pubblico, «gli XP sono roba di chi li ha, e un
  numero altrui non aiuta nessuno a decidere se fidarsi», e USARLI per
  ordinare non rovescia quella riga mentre PUBBLICARLI sì — e il
  PUNTEGGIO, che sarebbe un numero opaco da spiegare e non lo sarebbe
  mai abbastanza. Si mostrano la POSIZIONE e i FATTI su cui poggia:
  media, da quante persone, quanti affari. Sono anche quel che permette
  a chi guarda di giudicare da sé, che è il meccanismo su cui la
  tolleranza agli ordini fasulli conta.
  I CAMPI SI ELENCANO uno per uno invece di togliere quelli di troppo da
  un dict: la regola di `CAMPI_VETRINA`, e la differenza si vede il
  giorno che il giudice ritorna una chiave nuova.
  LA TUA RIGA esce solo a te e solo se NON sei nei primi
  `CLASSIFICA_TOP`: chi sta in fondo non compare mai in una lista che
  vedono gli altri, e chi è nei primi la vede già.
  LA RIGA CHE SPIEGA UN'APPARENZA (chiesta da Andrea guardando il conto
  vero): con tutte le medie uguali l'ordine lo decide il commercio, e
  senza dirlo uno legge sette nomi con «5,00» accanto e non capisce
  perché è settimo. È DERIVATA DAI DATI e non un testo fisso — si
  accende finché è vero e sparisce da sola il giorno che arriva il primo
  voto diverso: il patto degli hint contestuali («sparisce da solo
  quando smette di essere vero») e della riga «nessun venditore usa più
  questa rete». Nessuna soglia da tarare.
  ⚠️ E GUARDA LE RIGHE CHE SI VEDONO, non tutta la classifica — è il
  difetto che il giro DAL VIVO ha trovato e la rilettura no: col conto
  su TUTTE le righe, il giorno che il venticinquesimo prende un 4 la
  riga sparisce mentre i primi venti mostrano ancora una colonna di
  «5,00» identici, cioè si spegne esattamente nel caso per cui esiste.
  Guardando la fetta visibile la frase è anche VERA su quel che c'è a
  schermo. Nel collaudo la prova ha CAMBIATO LATO col perché scritto, e
  ha guadagnato il rovescio (con la fetta più larga la riga si spegne).
  LE PILLOLE DEL FILTRO (Tutti · ⭐4+ · ⭐4,5+) compaiono SOLO se
  filtrano davvero: se nessuno sta sotto la soglia, quella pillola
  darebbe la stessa lista con un tocco in più — la regola di
  `condFiltrabile` (il filtro condizione DORME dove non vuol dire
  niente) e della card che sparisce quando la sua occasione non esiste.
  Oggi, con tutte le medie a 5,00, non ne compare nessuna. Filtrano la
  media VERA e non il punteggio, lato client sulla lista già in memoria
  (zero rete per un tocco); stato di SESSIONE, mai localStorage.
  IL COSTO È MISURATO e non stimato: 0,1 ms oggi · 2,5 ms a 1.000 utenti
  e 3.000 feedback · 26,5 ms a 10.000 e 30.000, più le quattro letture.
  Il calcolo sta IN RAM e non in SQL perché non esiste un indice su
  `ordini(venditore_id/compratore_id)` e un EXISTS per riga di feedback
  degenererebbe — ed è il pattern di casa (`arricchisci_righe_vetrina`
  calcola in Python, il dizionario dei comuni vive in RAM). Cache di 60
  s in memoria, il calco di `conta_pionieri`. NIENTE COLONNA
  MATERIALIZZATA: il progetto ha già la regola «derivato, mai in
  colonna» per livelli e distintivi, e una colonna invecchierebbe a ogni
  feedback. Il segnale per cambiare idea è la LATENZA dell'endpoint, non
  un numero di utenti.
  `GET /api/classifica` è PUBBLICA come `/api/listings` e l'identità è
  FACOLTATIVA (`utente_se_autenticato`): serve a una cosa sola, la
  propria riga. LEGGE E BASTA, come `controlla_libro_mastro` — c'è la
  prova che nella strada intera non compaia un INSERT, un UPDATE o un
  DELETE, e il collaudo confronta il dump di `utenti`, `feedback` e
  `xp_eventi` prima e dopo.
  LA VISTA È INTERNA, il patto di `/sicurezza` e `/privacy`: fuori da
  `RADICI` — quindi si SPINGE e il gesto indietro riporta a Esplora —
  `voceNav` la mappa su 'esplora', nessun ramo in `navRendiVista` (il
  contenuto si ridisegna dal `go(b.v)` finale) e fuori da `VISTE_PTR`.
  In DEMO e in VETRINA NON ESISTE: là non c'è un server che la calcoli e
  un numero inventato sarebbe peggio del niente (il patto del cassetto
  wallet), quindi il podio non compare e `apriClassifica` ha la
  cintura per ogni altra strada.
  LA PORTA È UNA ED È IL PODIO IN TESTATA (ago 2026, decisione di
  Andrea): il bottone in fondo al Profilo è MORTO — due porte per la
  stessa pagina sono un bivio, e il podio si vede da ogni vetrina
  invece che in fondo a un'altra scheda. Il podio è un SVG statico
  inline (tre gradini, la grammatica delle icone di casa: viewBox
  «2 2 20 20», tratto 1.5 currentColor, velo 12% inline perché
  `.velo` è scoped a `.nav-ico` — il precedente di ICO_LOCKER), due
  istanze gemelle fra la levetta del tema e il tappo, gate
  `myClassifica && !DEMO && !VETRINA` in `renderPodioTesta` (chiamata
  DOPO il /me, dove `myClassifica` è appena arrivata, più i tre rami
  anonimi/demo), anello `.attivo` da `go()` quando la vista è la
  classifica (il registro del tappo). CONSEGUENZA DICHIARATA: su
  mobile la testata vive solo in Esplora, quindi dal Profilo la
  classifica non si raggiunge più — da desktop la topbar c'è ovunque.
  IL VESTITO È QUELLO DI CASA e non una classe nuova da tarare:
  `.seller` per la riga (lo stesso blocco avatar+nome+reputazione del
  negozio e del Profilo) e `.tema-pill` per il filtro — la riga si legge
  uguale alle sue sorelle. Negli onclick viaggia SOLO il codice negozio
  passato dal filtro-alfabeto, il patto di `renderNegozio`; senza codice
  la riga non è toccabile, meglio ferma che rotta.
  LA SESTA LEVA è `CLASSIFICA_KD` (0 = spenta), col suo `spento` nel
  pannello — che scatta proprio sul default, ed è ciò che permette a un
  moderatore che legge «0» di distinguere «spenta» da «tarata bassa».
  ⚠️ Chi la aggiunge la metta ANCHE nella tupla del censimento leve di
  `prove.py` e nello stub di `_amb_classifica`: senza la prima
  `_ConfigFinto.__missing__` le dà 7 in tutti e due gli stati e la voce
  esce «accesa» perfino nel censimento spento, senza il secondo l'`exec`
  del giudice cerca una costante che lì non esiste e TUTTE le prove
  della classifica esplodono con NameError invece di fallire.
  LEVE: `CLASSIFICA_ATTIVA` nasce SPENTA nel codice, il patto di
  `ASTA_ABILITATA` e `BANNER_NEGOZIO_ATTIVO` — non perché muova denaro,
  ma perché nessuno sa ancora quante righe escono: si accende dal config
  del VPS dopo aver guardato il conto. Più `CLASSIFICA_TOP` (20),
  `CLASSIFICA_K` (5), `CLASSIFICA_XP_RIF` (1000), `CLASSIFICA_PESO_XP`
  (0,25). ⚠️ Tutte e cinque vanno anche nell'ambiente di `_censimento`
  in `prove.py`, o quella prova non diventa rossa: ESPLODE con
  NameError.
  ⚠️ E `peso=0` DEVE ESSERE UN VALORE, non un «non passato»: la prima
  stesura scriveva `peso or CLASSIFICA_PESO_XP` e uno zero ricadeva sul
  default, cioè rendeva FALSA la promessa scritta nel config («0 = la
  classifica torna la sola media»). L'ha trovato una PROVA e non la
  rilettura, ed è il motivo per cui i tre parametri si leggono con
  `is None`.
  LA MISURA VIENE PRIMA (tappa 0): i dati locali sono finti e non ci si
  tara niente, quindi `classifica_prova.py` — che LEGGE E BASTA, il
  calco di `stima_coda_moderazione.py`, e legge il giudice dal TESTO di
  `server.py` invece di importarlo (la lezione di `ricategorizza.py`) —
  l'ha lanciato Andrea sul VPS. IL CONTO: **14 entrano, il freno ne
  tiene fuori 3**, e hanno TUTTI media 5,00 — quindi oggi la classifica
  ordina di fatto per VOLUME, ed è anche la ragione per cui la riga che
  spiega esiste.
  RESTA FUORI, dichiarato: nessuna rotta `/classifica` condivisibile (la
  porta è il podio in testata; aggiungerla è il calco di `/sicurezza` ed è una
  decisione a parte, con SEO, anteprima e sitemap); niente classifica
  mensile né opt-in; e NESSUNA NOTIFICA — nessuno viene avvisato che è
  salito o sceso, che una classifica che scrive in chat è la famiglia di
  messaggi che fa bloccare il bot.
  GLI ORDINI DI PROVA E IL PREGRESSO DEGLI XP (ago 2026, dal campo:
  Andrea primo in classifica coi suoi collaudi di luglio). Due fatti
  scoperti insieme guardando i numeri veri: «affari» e XP contano da
  fonti DIVERSE — gli affari si ricalcolano da `ordini`, gli XP sono
  un registro append-only nato ad ago 2026, quindi il commercio
  pre-deploy non alzava il punteggio (asimmetria che non era
  dichiarata da nessuna parte) — e i collaudi fatti in produzione
  facevano curriculum e rendevano «reali» dei recensori.
  LA COLONNA È `ordini.prova` (DEFAULT 0 = la migrazione), scritta
  SOLO da `marca_prove.py` a mano e IN LISTA ESPLICITA: a decidere
  cos'è una prova è Andrea, mai un'euristica sui titoli. NON SI
  CANCELLA, ed è la riga che regge tutto: la riconciliazione LNbits
  incrocia gli incassi coi `payment_hash` di quelle righe, e un
  DELETE fabbricherebbe proprio gli orfani che quel metodo esiste per
  trovare. Il CSV contabile li TIENE, deliberato: sono sats mossi
  davvero.
  I LETTORI che imparano `prova=0` sono i due del COMMERCIO:
  `_dati_classifica` (affari, controparti, e i voti con la cintura
  NOT IN — i feedback sulle prove si tolgono con la valvola admin,
  ma la classifica non deve dipendere da una pulizia a mano) e
  `_dati_distintivi` (quattro conteggi). `classifica_prova.py` è
  allineata con la stessa WHERE più il ripiego per un database di
  prima della colonna. Restano fuori, dichiarato: `_conta_settimana`
  (guarda la settimana corrente, le prove sono di luglio) e il CSV.
  `marca_prove.py`: timbra, toglie gli eventi XP e rifà la cache dal
  registro, decrementa `vendite_ok`/`acquisti_ok` (incrementali:
  nessun ricalcolo li rimette in pari da solo) SOLO nel giro in cui
  il timbro passa 0→1 — il secondo lancio è un no-op — e mai sotto
  zero; ELENCA i feedback per la valvola e i distintivi coi conteggi
  rifatti (sono append-only: toglierli è una decisione a mano). Su
  un id inesistente o non-released si ferma dicendolo, senza aver
  scritto niente.
  `recupera_xp_ordini.py`: il pregresso VERO — due eventi per ordine
  con la formula viva, le cui costanti si estraggono dal TESTO di
  server.py (fail-closed: senza, ci si ferma, mai punti a memoria).
  IL CAMBIO in ordine di onestà: `cambio_eur` (chiusura, lo stesso
  del gancio vivo) → `cambio_ordine` (creazione, un fatto REGISTRATO)
  → soli punti fissi, MAI il cambio di oggi. La data dell'evento è
  `aggiornato` (lo sblocco). IL PERIMETRO È DERIVATO CON LA LISTA
  COME GUARDIA: «released, prova=0, zero eventi» deve dare
  esattamente gli id passati, o si ferma senza scrivere. L'ORDINE È
  VINCOLANTE: prima marca_prove, POI il recupero — al contrario
  regalerebbe XP proprio ai collaudi.
  Provato: 27 prove nuove col banco che fa GIRARE i due script su un
  database di cartone (il pavimento a zero dei contatori e la
  precedenza chiusura-su-creazione hanno i loro casi apposta: senza,
  due mutazioni non potevano fallire) e 14 MUTAZIONI una per riga
  sorvegliata, tutte uccise — cinque non si APPLICAVANO nemmeno al
  primo giro, le ancore multi-riga coi CRLF: la trappola già a
  verbale, ripagata.
  IN PRODUZIONE, nell'ordine: deploy → `python marca_prove.py 4 6 7 8
  9 10 11 12 18 29 82 --scrivi` (anteprima prima, senza flag) → la
  valvola admin sui feedback che lo script elenca →
  `python recupera_xp_ordini.py 28 31 33 36 37 --scrivi` →
  `classifica_prova.py` per il prima/dopo. DA GUARDARE: le
  controparti-collaudo che escono dal gate della classifica (è
  l'effetto voluto), e i badge che lo script elenca come non più
  meritati, da decidere riga per riga.

La card del barattolo nella striscia, e il podio in testata (ago 2026,
i due cambi in home chiesti da Andrea): il barattolino di testata è
diventato una card grande come le altre, accanto a «Tutto», col vetro
che si riempie in place; al suo posto il PODIO della classifica (icona
scelta da Andrea fra otto candidate guardate a schermo), e il bottone
in fondo al Profilo è morto — una porta sola. Col filtro acceso la
striscia RESTA (c'è la card da illuminare) e la pillola del barattolo
sta accesa in testa fra le altre nella barra appiccicata. Vedi
Architettura, «LA CARD DEL BARATTOLO NELLA STRISCIA», per la firma
J/B, il niente-data-cat e la regia unica. Collaudato: 6016 prove verdi
(rovesciate col perché: jar-testa a zero, la striscia che non si
nasconde più, profiloClassifica a zero) e 7 mutazioni una per riga
sorvegliata, tutte uccise; giro dal vivo via CDP a 320/360/375 nei due
temi col server vero. IN PRODUZIONE basta il deploy: nessuna colonna,
nessuna leva, nessuna rotta — solo client. `CLASSIFICA_ATTIVA` è GIÀ
accesa sul VPS (Andrea, 24 ago), quindi il podio compare al deploy per
tutti gli autenticati. GUARDATO dal telefono (set 2026): la card del
barattolo resta fuori dal gesto, il podio dentro Telegram vero sta in
piedi — e il tocco lungo di condivisione NON scattava affatto, che è
il difetto poi corretto (vedi Architettura, «IL REPARTO SI CONDIVIDE»,
«IL FONDO DI SISTEMA»: il timer pareggiava i 500ms del riconoscitore
di Android e vinceva il sistema).

E la riga di quanto manca al prossimo grado dice tre cose giuste (ago
2026, dal campo: «mancano 0 XP e 1 affari conclusi» — lo zero scritto,
nessun singolare, il verbo sempre plurale). Erano TRE difetti nella
stessa frase, quindi si sistemano insieme: giudice unico `fraseManca`,
zero server, zero colonne, zero leve. Vedi Architettura, in coda a «DA
CHE LATO VENGONO GLI XP», per la regola del verbo (guarda quanti pezzi
restano, non i numeri) e per la lezione dell'ordine fra due funzioni,
che non conta per il browser e conta per `pezzo_js`.
Collaudata: 6 prove nuove — il DELTA misurato sull'albero isolato
(6481 → 6487), che il totale dipende dal ramo su cui si atterra — e
**TREDICI MUTAZIONI, tredici uccise**, una per riga sorvegliata. Fra
queste, quella che lascia il nome del gradino NUDO: senza il caso col
nome cattivo sarebbe sopravvissuta, e l'ha chiesta la tortura. Più il
giro DAL VIVO col server su un database usa-e-getta, col caso vero di
Andrea seminato (76 XP e zero affari): «manca 1 affare concluso» letto
a schermo, più il plurale, i due pezzi insieme e la cima della scala,
a 320/360/375 nei due temi — zero scorrimento laterale, zero errori JS.
IN PRODUZIONE basta il deploy: solo client.

Il barattolo si condivide col suo link (ago 2026, il punto 3 del giro
della card): fotografia e non vista viva, token casuale opt-in e
revocabile, pagina anonima col noindex, venduti spenti e rimossi mai,
l'avvertimento PRIMA del tocco e la voce in «I tuoi dati» coi limiti
della revoca. Vedi Architettura, «IL BARATTOLO SI CONDIVIDE COL SUO
LINK». Collaudato: 6098 prove verdi (le eseguibili girano gli
endpoint VERI su sqlite in memoria: crea idempotente senza
rifotografare, aggiorna che tiene il token, revoca che rende il link
morto, il token nuovo dopo, la pagina fresca col venduto e senza il
rimosso, l'anti-oracolo) e **18 MUTAZIONI, 18 uccise**, una per riga
sorvegliata — token derivato dal tg_id, SELECT col tg_id, guardia
della forma tolta, fotografia coi rimossi, pagina che non rifiltra,
crea che rifotografa di soppiatto, aggiorna che rigenera il token,
revoca che non cancella, fusione senza DELETE, pagina che legge il
db, noindex sparito, spegniOspite tolto, avvertimento spostato,
disabled, deep-link via da avviaVetrina, regex ancorata, link
nell'onclick, revoca senza domanda. Più il collaudo vivo col server
del worktree su DB usa-e-getta: **24/24 sull'API** (il giro completo
crea→apri→aggiorna→revoca→ricrea, l'ordine della fotografia, il
venduto dichiarato, l'anti-oracolo sul database vero) e **25/26 nel
browser** via CDP a 320/375 nei due temi — l'unico NO era il
SELETTORE DEL BANCO e non un bug (le card sono `<div>` col gestore
sull'`<a>` interno: cliccando l'`<a>` la scheda dell'esaurito si
apre, verificato a mano), con zero errori JS e zero sbordo.
IN PRODUZIONE basta il deploy: una tabella additiva che nasce vuota,
zero leve, zero migrazioni di dati — e finché nessuno tocca
«Condividi il barattolo» non cambia niente di visibile. DA GUARDARE
al primo giro: il primo link vero condiviso in chat — l'anteprima
DEVE restare la card generica del brand, che è la garanzia della
revoca vista dal vivo — e la prima revoca, col link che muore subito.

La maniglia del codice di ritiro (ago 2026, cantiere 44): il bottone
«🔔 Ricorda al venditore» si apre anche sugli ordini 'shipped' verso un
punto di ritiro senza busta depositata — la cura mirata del buco messo
a verbale il giorno prima: chi sa dell'arrivo è il compratore, con
l'avviso del corriere in mano, e non aveva nessuna maniglia mentre la
giacenza (~3 giorni) correva. Finestra sua a 24 ore dalla spedizione
(leva nuova `SOLLECITO_MANUALE_BUSTA_ORE`), pausa e tetto di famiglia
(24h × 3), contatori SUOI (la fase 'locked' può aver consumato i tre
squilli), e il testo che dice il fatto che sappiamo davvero — mai un
arrivo che non possiamo verificare. `PROMEMORIA_BUSTA_GIORNI` resta a
3, deciso: abbassarlo bussa a chi ha spedito ieri con un pacco ancora
in viaggio. Vedi Architettura, «E LA SECONDA FASE È LA BUSTA», anche
per la traccia del cantiere 45 (l'email del compratore
sull'etichetta). Collaudato: 6057 prove verdi (34 nuove — l'endpoint
girato DAVVERO sul mondo di cartone esteso con la fase busta:
finestra, pausa, tetto, lo storico con `spedito_il=0` che ha la
maniglia, l'anti-oracolo sulla strada nuova, il titolo cattivo
scappato, e la fase locked esaurita che NON blocca, che è il punto del
cantiere) e DIECI MUTAZIONI una per riga sorvegliata, ognuna rossa da
sola. IN PRODUZIONE basta il deploy: le due colonne nascono a 0, la
leva ha il default nel codice, nessuna rotta nuova — e un client
vecchio in cache non vede il bottone e vive come oggi. DA GUARDARE al
primo giro: il primo promemoria vero della busta dentro Telegram, e
che al venditore arrivi il testo del codice e non quello della
spedizione.

L'offerta sul carrello, e il totale in superficie (ago 2026, decisioni
di Andrea): «Fai un'offerta» in fondo alla cassa del set apriva un
coming soon, e adesso apre il suo foglio — UNA cifra per tutto il
carrello, la trattativa di sempre sopra (contro, rilancio, accetta), e
al pagamento la voce di TESTATA `accordo_sats` che non spalma niente
sugli unitari. E nello stesso giro l'unità si è unificata IN
SUPERFICIE: anche sull'offerta del singolo con più pezzi i campi dove
si digita parlano il TOTALE, mentre la sostanza resta unitaria —
sennò la stessa app avrebbe chiesto due unità diverse a due dita di
distanza. Vedi Architettura, «L'OFFERTA SUL CARRELLO» e «IL TOTALE IN
SUPERFICIE», per l'atterraggio, le decadenze una per una e la trappola
dei JOIN.
COLLAUDATO: 6238 prove verdi (il blocco nuovo delle sentinelle
strutturali) più `collaudo_offerta_carrello.py` — 55 verdi, il server
VERO su un database usa-e-getta con LNbits finto: il giro completo
proposta→contro→rilancio→accetta→paga con la bolt11 confrontata AL
SAT, preventivo == compra, gli sconti spenti provati GIRANDO il conto
nei due mondi, le decadenze della tabella una per una, la fusione
senza figlie orfane, la ronda che tace. Più **26 MUTAZIONI, 26
uccise**, una per riga sorvegliata.
E LA TORTURA HA FATTO IL SUO MESTIERE, che è la parte da ricordare:
ha trovato due mutazioni MIRATE MALE (colpivano `fai_offerta` invece
del gemello carrello: le due funzioni hanno righe identiche, e la
prima occorrenza nel file è quella singola), una INERTE (`[] or X`
vale X), e soprattutto **un buco vero del collaudo** — il body
mandava le quantità GIUSTE, quindi «il client si ignora» non era
provato da niente; adesso le manda storte apposta. Nel giro delle
sentinelle ne ha trovate altre quattro che non potevano fallire, per
la ragione di sempre: la fetta di `pezzo()` era così larga da
contenere anche le funzioni vicine col loro LEFT JOIN.
DUE BUG DELLA STESSA FAMIGLIA IN DUE GIORNI, e li ha presi solo il
codice che GIRA: `offerte_righe` non ha una colonna `id` — la ronda le
chiedeva `r.id` (segnalato dalla sessione accanto) e la lettura delle
figlie faceva `ORDER BY id`. Le prove erano verdi tutte e due le
volte, perché i cartoni davano alla tabella un id che il DDL non ha.
IN PRODUZIONE: due migrazioni additive (`offerte_righe`,
`ordini.accordo_sats` a 0), nessuna leva nuova, nessuna rotta di
pagina — e un client vecchio in cache non conosce le chiavi e vive
come oggi. DA GUARDARE al primo giro: la prima offerta di carrello
vera dentro Telegram (che al venditore arrivi UNA notifica con
l'elenco, mai N), e il primo accordo pagato con la bolt11 confrontata
su LNbits — se `paga_venditore` avvisa i moderatori, ci si ferma.

Da che lato vengono gli XP (ago 2026): nel Profilo «76 XP» non diceva
che sono pochi perché si è comprato invece di venduto. Il dato c'era
già nel registro — il ruolo sta DENTRO il riferimento, e il perimetro è
un tipo solo — quindi zero colonne, zero migrazioni, zero leve: una
chiave in più in `/api/me` e la hint del cassetto «🎖 Livello e titolo»
che si sdoppia in tre casi. Le tre righe da non ammorbidire — lo zero
che non si scrive, i numeri che li dà il server, la scomposizione solo
se i due lati fanno il totale — stanno in Architettura, «DA CHE LATO
VENGONO GLI XP», col perché di ognuna.
Collaudato: 23 prove nuove — fra cui LA PROVA REGINA, che estrae la
f-string dal GANCIO e la dà in pasto al parser (una sentinella direbbe
che il parser esiste, mai che combaci con chi scrive), e il banco node
che fa GIRARE `fraseXp` sui suoi sei casi con undici asserzioni — più
TREDICI MUTAZIONI, una per riga sorvegliata, tutte uccise al primo
giro. E il giro DAL
VIVO col server su una copia usa-e-getta: le quattro popolazioni lette
A SCHERMO, dal registro fino al DOM (46 e 30 sui due lati, i due casi a
un lato solo, e la riga muta che fa tacere la scomposizione), con le
misure a 320/360/375 nei due temi — zero scorrimento laterale, la riga
a 15px dal bordo del cassetto.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — e un client rimasto in cache non legge la
chiave nuova e vede la riga di sempre.

E il foglio dell'offerta sul carrello si legge nelle due valute (ago
2026, chiesto da Andrea in due domande: «se tutti gli articoli sono in
euro posso offrire in sats?» e «vorrei vedere la conversione mentre
scrivo»). La risposta alla prima è che la valuta la forza il SERVER,
che la deduce dalle righe — quindi si è aperto quel che si poteva
aprire senza toccare il denaro: il campo si legge e si scrive
nell'altra valuta, la cifra che parte resta quella dell'offerta. La
seconda viene quasi in omaggio, ed è lo stesso meccanismo: la coda
della riga viva dice l'altra faccia col ≈. Vedi Architettura, «IL
FOGLIO SI LEGGE NELLE DUE VALUTE», per la strada scartata (l'accordo
che ESISTE in sats su un carrello tutto-EUR, che farebbe ballare lo
sconto col cambio) e per le tre regole del gemello ricalcate una per
una. Zero server, zero colonne, zero leve: il cantiere è solo client.
Collaudato: 6353 prove verdi in modalità severa sull'albero pulito (18
nuove, più due censimenti che hanno CAMBIATO LATO col perché scritto)
e **14 MUTAZIONI, 14 uccise** — la sola sopravvissuta al primo giro
chiedeva DOVE la pillola pianta l'ancora, e il conteggio delle due
scritture restava verde spostandone una: l'ha detto la tortura, non la
rilettura. Più il banco node che FA GIRARE l'ancora sul caso che
smaschera la deriva (66661 sats non tornano a sé passando per gli
euro, quindi un render che riscrivesse l'ancora perderebbe un sat al
primo toggle), e il giro DAL VIVO col server vero su un database
usa-e-getta — **40 verifiche verdi** a 320/360/375 nei due temi: i due
carrelli (misto e tutto-EUR), i dieci toggle che non spostano l'ancora
di un sat, il minimo detto nella lingua del campo, e il cambio muto
che spegne coda e toggle insieme. IN PRODUZIONE basta il deploy.

L'email per il codice del locker (ago 2026, tappa B, dalla richiesta di
un venditore vero in chat): chi compra può lasciare la sua email
nell'ordine, così il codice del locker glielo manda direttamente il
corriere invece del venditore. È la QUARTA volta che lo stesso buco
morde — chi non ha né username Telegram né npub in chat non ci arriva —
e la risposta è la terza strada: **passa, ma non resta**. Le cinque
decisioni di Andrea (una sola email e **mai il telefono, vincolo
permanente**; facoltativa; dentro l'ordine dopo il pagamento; su ogni
ordine via punto senza gate sul venditore; il moderatore vede CHE c'era
e mai QUALE) e la premessa da correggere — «cifrato nell'ordine» non
vuol dire «non passa da noi» — stanno in Architettura, «L'EMAIL PER IL
CORRIERE».
Collaudata: **6580 prove verdi sull'albero ISOLATO** (HEAD più i soli
hunk di questo cantiere: la copia di lavoro è condivisa con un'altra
sessione, e la sua baseline era rossa per un cantiere che non è
questo — è l'unica cosa che risponde a «questo commit, da solo, sta in
piedi?»), con la famiglia nuova `prove_email_corriere` che fa GIRARE i
due endpoint su un database di cartone; più
`collaudo_email_corriere.py`, **39 verdi**, che cammina il giro intero
col server VERO su un database usa-e-getta — l'email che in colonna
arriva CIFRATA (`f2:`, con la chiave nel config finto: senza, il caso
che conta non si potrebbe provare), il venditore che la legge e
spedisce, il campo che si chiude dopo la spedizione, il moderatore che
riceve il FATTO e non il valore, l'anti-oracolo verificato sul database
vero, la scopa nelle due velocità, il caso normale che non cambia di un
byte e la ronda che tace. Più la TORTURA: **21 mutazioni, 21
uccise**, una per riga sorvegliata — il telefono che torna nel
giudice, il tetto che tronca, l'email in chiaro, il confronto sui blob,
il valore che esce da `/api/orders`, il moderatore che legge, le due
corsie della scopa, i due rami del libro mastro, il campo che resta
aperto sullo spedito, la guardia di proprietà fuori dalla WHERE, la
lettura aperta all'admin. E il GIRO DAL VIVO via CDP a 320/360/375 nei
due temi e dai TRE ruoli: **65 verifiche verdi e ZERO errori JS** —
il link chiuso alto una riga, il campo aperto col tipo e l'autofill, la
riga compatta che NON porta il valore (che in `/api/orders` non c'è) e
lo precompila al tocco, i due rami dello spedito, il venditore che
rivela e il moderatore che non ha nemmeno il pannello.
QUATTRO LEZIONI DI METODO, e sono la parte che serve fra sei mesi.
1) LA PROSA, per la quarta volta in un giro solo: tre sentinelle sono
nate rosse per colpa di un COMMENTO — la docstring che dichiara il
vincolo del telefono, quella della scopa che nomina `'annullato'`
apposta per dire che non c'è, e un commento del client che nominava il
velo d'attesa proprio per spiegare perché NON si chiama. Si stringono
con `_senza_prosa`, o si toglie il nome dal commento.
2) LA PROVA CHE NON PUÒ FALLIRE: «il valore non c'è nella nota» era
verde anche con la nota VUOTA — passava per la ragione sbagliata.
Adesso è in coppia con «la nota esiste».
3) IL VELO D'ATTESA RESTA ALLE LETTURE: la scrittura dell'email non lo
prende, perché le due scritture sorelle dell'ordine (`salvaNota`,
`salvaPuntoRitiro`) non ce l'hanno, e quell'elenco vale finché resta di
sole letture — è lui ad accorgersi del gesto che un domani muovesse
sats.
4) IL GIRO DAL VIVO HA TROVATO QUEL CHE LE MISURE NON DICEVANO, ed è
la lezione più cara del cantiere: due righe facevano il CONTRARIO di
quel che il loro commento prometteva, con tutte le sentinelle verdi —
il cursore che alzava su `type="email"`, e il testo dello spedito che
dava per scontata la busta diretta. La terza è di registro e si vede
solo GUARDANDO: la via d'uscita scritta due volte a due dita di
distanza. Stanno in Architettura, in coda alla voce.
5) E IL BANCO CREDEVA DI ESSERE UN ALTRO: il login di collaudo vuole
`id` e non `tg_id`, quindi il POST falliva in silenzio e la sessione
restava quella di prima — tre righe rosse «del venditore» erano il
COMPRATORE guardato due volte. Adesso il banco CHIEDE chi è (`myTgId`)
e si ferma se non è chi crede, che è la stessa rete del marcatore sul
server.
6) IL FILTRO DEGLI HUNK SI RIFÀ AL MOMENTO DEL COMMIT: gli hunk
dell'altra sessione sono cresciuti mentre lavoravo (quattro nuovi in
`prove.py`), e un censimento di un'ora prima avrebbe portato via metà
del suo lavoro.
IN PRODUZIONE basta il deploy: cinque colonne additive che nascono
vuote, nessuna leva nuova, nessuna migrazione di dati, nessuno stato
nuovo — e un client rimasto in cache non conosce il campo e si comporta
come oggi. ⚠️ Sul VPS `CHIAVE_CONTENUTI_DIGITALI` deve esserci, o il
giudice risponde **503** e l'email non si salva dicendolo: qui il 503
non blocca l'acquisto (l'ordine esiste già), ma un recapito in chiaro
non si scrive — a differenza del PIN della busta, che è una
degradazione accettabile e dichiarata.
DA GUARDARE al primo giro: la prima email vera lasciata dentro Telegram
— che il venditore la trovi nel suo riquadro al momento di comprare
l'etichetta — e, al primo affare confermato, che sparisca con
l'indirizzo entro dieci minuti (la riga 🏠 nel journal li conta
insieme).

L'email si lascia già alla cassa (ago 2026, il giro dopo, e ROVESCIA la
decisione 3 del cantiere qui sopra): il punto di ritiro si sceglie PRIMA
di pagare e l'email si lasciava DOPO — la stessa decisione in due
momenti, con in mezzo la finestra in cui **un venditore veloce compra
l'etichetta prima che l'email esista**. Il campo si AGGIUNGE in cassa,
dentro il cassetto del punto; l'ordine resta la seconda porta e il suo
endpoint non cambia di una riga. Le tre decisioni di Andrea (nel
cassetto del punto e non in uno suo, senza chiave non si salva e lo si
dice ma l'ordine nasce, il venditore lo sa da una riga in coda a «Hai
venduto») e le righe da non ammorbidire — il permesso di degradare che
si deve SCRIVERE, `mail_persa` che è una congiunzione, il gate della
coda sul TIMBRO e mai sulla colonna cifrata — stanno in Architettura,
«L'EMAIL SI LASCIA GIÀ ALLA CASSA».
Collaudata: **+48 prove** in modalità severa (6589 → 6637 contro HEAD
del giorno, che era verde; è il DELTA il numero difendibile, che la
cartella è condivisa con altre sessioni) più
`collaudo_email_corriere.py` a **67 verdi** (era 39: il giro dalla cassa
end-to-end con la colonna cifrata `f2:`, la riga in coda a «Hai
venduto», la doppia scrittura nei suoi tre casi, la ripresa che non
riconia, il degrado che fa nascere l'ordine e la ronda che tace), e
**20 MUTAZIONI, 20 uccise**, una per riga sorvegliata.
E IL GIRO DAL VIVO via CDP a 320/360/375 nei due temi, col server
vero su un database usa-e-getta: **49 verifiche verdi e ZERO errori
JS** — la cascata rete → tipo → dove → email nell'ordine giusto (il
campo non c'è finché le scelte mancano), il venditore senza reti che
lo vede subito, le altre vie che non lo offrono, l'email scritta che
arriva CIFRATA `f2:` in colonna col suo timbro, il venditore che la
legge e il moderatore che no, la RIPRESA che non conia un ordine
nuovo e aggiorna il valore senza muovere il timbro, e la correzione
dall'ordine che conta 1. È lì che l'imperfezione 1 si è rivelata più
mite del previsto (vedi la voce).
⚠️ E IL BANCO HA MENTITO QUATTRO VOLTE, tutte nello stesso modo: id
sbagliato del campo, cassetto non aperto, punti salvati cancellati da
un giro precedente, e un annuncio che era un'ASTA. Otto righe rosse
che non erano del codice — **una verifica che fallisce si guarda
prima di crederle**, ed è la seconda volta in questo cantiere.
E DUE SENTINELLE DI ALTRI CANTIERI hanno dovuto imparare qualcosa, che è
la parte da ricordare: quella del gate del campo elencava cosa c'è SOTTO
il gate («? campoDove : ''») e tornava rossa per un'aggiunta legittima
invece che per un gate caduto — adesso si ferma al GATE; e il cartone di
`prove_ricevuta_compratore` non aveva la colonna del timbro, quindi la
riga nuova in `_incassa_ordine` non faceva una prova rossa ma ESPLODERE
la famiglia con un IndexError — la classe di guasto già pagata dalla
colonna mancante di `offerte_righe`.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — e un client rimasto in cache non manda la
chiave e si comporta come oggi. DA GUARDARE al primo giro: la prima
email lasciata alla CASSA dentro Telegram — che al venditore arrivi la
riga in coda a «Hai venduto», e che il compratore la ritrovi
nell'ordine, col «Cambia» che la riapre precompilata.

Più account sullo stesso browser (ago 2026, chiesto da Andrea: «il mio
account e quello del negozio entrambi loggati, senza fare logout e
login ogni volta»). Il cookie di sessione resta quello di sempre — il
token ATTIVO — e accanto nasce il PORTACHIAVI: così `verifica_utente` e
i ~50 endpoint che la chiamano non cambiano di una riga, e lo switch è
solo il cookie attivo che si riscrive. Le tre decisioni di Andrea: solo
web e PWA (dentro Telegram l'identità la impone il client, e lo switch
vorrebbe dire rovesciare una regola di sicurezza scritta), si passa
LIBERAMENTE anche con un affare aperto, e il logout esce da UN account
alla volta. IL GESTO È IL DOPPIO TOCCO SUL TAPPO (decisione di Andrea,
il giro dopo): il primo porta al Profilo come sempre, il secondo apre
il menu — quello di Gmail — e la lista è TRASLOCATA dalla pagina al
foglio, che due elenchi della stessa cosa sono il difetto che il gesto
esiste per togliere. Vedi Architettura, «PIÙ ACCOUNT SULLO STESSO
BROWSER», per il token che non esce mai da `/api/sessioni`, per
l'anti-oracolo, per la fusione — che non ha voluto una riga perché la
dedup vive in lettura — e per l'accenno one-shot, senza il quale un
gesto nascosto non lo scopre nessuno.
Provato: **+41 prove** in `prove.py` (6472 → 6513 contro `origin/main`
del giorno, che ha le stesse 6 fallite preesistenti — `websocket` non
installato qui; è il DELTA il numero difendibile) con i ferri VERI
girati su un database di cartone, e **13 MUTAZIONI, 13 uccise**, una
per riga sorvegliata: dedup tolta, tetto rovesciato, scadenza non
guardata, token che esce, switch che apre una sessione, anti-oracolo
che distingue, logout che chiude tutti, HttpOnly perso, login che si
riapre la sessione da solo, selettore in DEMO, switch che non ricarica.
Più `collaudo_account.py` (32 verdi), che è il pezzo che le sentinelle
non possono dare: un browser vero che tiene i cookie, e la domanda su
cui il cantiere si regge — **dopo lo switch `/api/me` cambia persona
davvero?** — con l'anti-oracolo provato sul database vero, dove
l'account estraneo ESISTE. Torturato a sua volta: 5 mutazioni, 5
uccise, e la quinta ha fatto irrobustire la prova dell'anti-oracolo
(confrontava le parole e non il codice di stato). E il giro DAL VIVO
col server vero su un database usa-e-getta a 320/360/375 nei due temi,
zero sbordo e zero errori JS: il primo tocco che porta al Profilo, il
secondo che apre il menu, il tocco sull'altra riga che porta da 222 a
111 col nome che cambia e tutti e due ancora aperti, l'accenno che
compare una volta sola, il caso a UN account solo, e — la prova che il
gesto non è cambiato per nessun altro — `accountVivi()` falsa, dove i
due tocchi fanno esattamente quel che facevano ieri.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuno stato nuovo, e la leva ha il default nel codice — un browser
con un account solo fa login e logout esattamente come oggi, e chi è
dentro Telegram non vede niente di diverso. DA GUARDARE al primo giro:
il widget di Telegram dentro il menu, che qui non si può esercitare
(vuole il dominio registrato su BotFather: in locale disegna un
riquadro «Bot domain invalid») — e che dopo lo switch gli ORDINI
mostrino quelli dell'altro account.

Barattolo si raggiunge anche su Tor (ago 2026): un indirizzo `.onion`
accanto al dominio di sempre, con l'app COMPLETA e non la sola vetrina
(decisione di Andrea con Alan: chi arriva da Tor sa cosa fa e userà
Nostr). Il quadro è arrivato prima del codice, e il punto che decideva
era il quinto — «se metà delle cose porta comunque fuori, l'onion
promette una riservatezza che non mantiene». Il censimento ha detto che
il client è già tutto relativo e che a uscire restava UNA riga: lo
script di telegram.org, che su Tor era la prima richiesta a partire col
tuo IP vero. Si toglie SOLO di là, con una quarta fessura fail-open nel
meccanismo che c'era già. Vedi Architettura, «BARATTOLO SU TOR», per il
giudice che legge l'Host (e per l'header di Caddy scartato), per i TRE
`location.origin` che NON si toccano — in testa il tag `relay` del
login Nostr, che romperebbe il login proprio sull'unica porta che di là
funziona — e per il registro dei tre testi, che è una mappa e non un
avvertimento.
Collaudato: 6852 prove verdi in modalità severa (le nuove: la famiglia
`prove_onion`, la quarta fessura in `prove_anteprime`, e il banco node
che fa GIRARE `condividiAnnuncio` dai due mondi) e **27 MUTAZIONI, 27
uccise**, una per riga sorvegliata — e sono state loro a trovare i due
buchi veri: la sentinella del middleware che restava verde davanti a un
`pass  # _HOST_RICHIESTA.set(...)` (`codice()` toglie le righe che
COMINCIANO per «#», non un commento in coda: vale la cura del reaper,
si chiede la RIGA INTERA) e il fatto che nessuno guardasse se
`renderFasciaOnion()` fosse CHIAMATA. Più IL GIRO DAL VIVO col server
VERO su una copia usa-e-getta, **12/12**: dall'onion nessuno
`<script src>` punta più a telegram.org, dal clearnet c'è ancora, la
differenza fra le due pagine è ESATTAMENTE la lunghezza del segno, un
altro `.onion` non apre la porta e la porta appresso non la chiude.
IN PRODUZIONE il deploy non cambia NIENTE: `ONION_HOST` nasce vuota nel
codice, e senza quella riga nel config del VPS ogni pagina esce
esattamente com'è sempre stata. Si accende scrivendo l'indirizzo (senza
schema e senza porta) e riavviando.
VERIFICATO DAL VIVO (ago 2026, Andrea in Tor Browser col pannello di
rete aperto): filtrando «telegram» **non compare nessuna richiesta**, e
`ONION_HOST` è nel config del VPS. Era il pezzo che da qui non si
poteva fare, ed è il solo che dica se la fessura scatta davvero: non è
più da guardare.

Le quattro porte verso Telegram che su onion non si aprono (ago 2026,
dal campo: Andrea ha toccato «Apri @ilbarattolobot» da Tor Browser e
la richiesta si è fermata con un errore — non una fuga silenziosa, ma
un bottone ROTTO). Erano QUATTRO e non una, e il censimento è la parte
che vale: il foglio invito col suo bottone arancio (dieci chiamanti),
il CTA del banner della vetrina, il link inline di `barraWeb` e
`collegaTelegram` — che Andrea non aveva visto ed è il peggiore, perché
quando il link fallisce il codice monouso è già stato emesso. Vedi
Architettura, «E LE QUATTRO PORTE VERSO TELEGRAM», per la decisione che
ha dato forma al cantiere (togliere il bottone non bastava: il foglio
si gira, e Nostr prende il pieno) e per il catalogo che tiene il SENSO
dei dieci testi senza nominare il mezzo.
Collaudato: **6886 prove verdi** (34 nuove, di cui una ESEGUIBILE che
fa GIRARE `invitoTelegram` sui suoi casi) e **16 MUTAZIONI, 16
uccise** — e una di quelle ha trovato un buco vero: la chiave che il
censimento accettava senza controllare che fosse DICHIARATA, cioè un
refuso che su onion perdeva il testo del gesto in silenzio. Più il giro
DAL VIVO nel DOM vero col server acceso su un database usa-e-getta
(**16/16, zero errori JS**): le quattro porte nei due mondi, il doppio
cittadino col `tg_id` positivo, e la regressione del clearnet, che non
cambia di un byte. Più gli screenshot a 320/375 nei due temi.
⚠️ E IL BANCO HA MENTITO PASSANDO, che è il modo peggiore: un apostrofo
scappato male rendeva la chiamata un errore di sintassi e il primo
controllo usciva verde leggendo il markup fisso. Una verifica che passa
per la ragione sbagliata è peggio di una rossa.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client, e senza `ONION_HOST` nel
config del VPS non cambia niente per nessuno. DA GUARDARE al primo
giro in Tor Browser: il foglio girato al primo tocco su «Acquista», e
che «Collega Telegram» non compaia nel cassetto Identità.

E su onion la porta Nostr era DOPPIA (ago 2026, il giorno dopo, dal
campo: «due bottoni Nostr affiancati, tutti e due pieni»). Il difetto
era mio e nasceva dal non aver guardato CHI ALTRO scrive in quel
banner: il giro prima aveva dato la porta Nostr al CTA di
`mostraBanner`, e `bottoneLoginNostr()` la sua la **appende** allo
stesso nodo. La cura non e' cambiargli porta un'altra volta — su onion
il CTA non si disegna proprio, perche' il suo mestiere e' portare alla
Mini App dentro Telegram. Piu' il «…o» del bottone, che di la' nomina
un'alternativa che non c'e'. Vedi Architettura, «IL CTA DEL BANNER NON
CAMBIA PORTA: SPARISCE».
Collaudato: 6903 verdi e **6 MUTAZIONI, 6 uccise** — e la tortura ha
trovato che **il banco nuovo contava le PAROLE invece delle PORTE**:
con un secondo bottone verso Nostr dal testo diverso il conteggio
restava UNO, cioe' la prova nata apposta per questo difetto non lo
prendeva. Piu' il giro DAL VIVO nel DOM vero (**6/6, zero errori JS**):
su onion UNA porta sola, e il clearnet invariato al pixel — stessi
testi, stesse quote, stesse larghezze.
⚠️ LA LEZIONE E' LA STESSA DI DUE GIORNI FA, da un'altra porta: una
prova che guarda **un pezzo alla volta** puo' essere onesta su ognuno e
cieca su quel che fanno INSIEME. Il banco del giro prima leggeva il
banner subito dopo `mostraBanner`, quando la seconda mano non ci aveva
ancora scritto.
IN PRODUZIONE basta il deploy: solo client, e sul clearnet non cambia
un byte.
VERIFICATO DAL VIVO (ago 2026, Andrea su Tor Browser): «un bottone
solo, 🟣 Entra con Nostr». La doppia porta e' chiusa in produzione e il
testo senza il «…o» e' quello che si legge — non e' piu' da guardare.
E CON LUI IL CANTIERE TOR E' CHIUSO: `ONION_HOST` e' nel config del
VPS e il pannello di rete non mostra nessuna richiesta a telegram.org,
cioe' anche la FESSURA del server e' verificata (le due cose andavano
guardate separate: `suOnion()` nel client giudica `location.hostname` e
non passa da quella leva, quindi il bottone giusto da solo non avrebbe
detto niente sullo script).

Un posto sul mio piano non e' un account rubato (ago 2026, dal campo:
il divieto «dati personali o account» prendeva anche i posti sui piani
famiglia — Spotify, DAZN, Netflix — che sono un mercato vero, e
Together Price fa solo quello). LA DIAGNOSI ROVESCIA LA DOMANDA, ed e'
la cosa da leggere per prima: l'esito di ieri non era «bloccato», era
ALEATORIO — `credenzial` stava fra le parole del declassamento e
«account» no, quindi lo stesso annuncio finiva in coda o veniva
rifiutato secco secondo la parola che il modello sceglieva. Da li' la
cura in due pezzi, che la voce nel prompt da sola non basta. Le tre
decisioni di Andrea (il perimetro e' il POSTO sul piano di cui il
venditore resta titolare, l'esito e' OK, `credenzial` scende in coda) e
le tre contro-regole stanno in Architettura, «UN POSTO SUL MIO PIANO
NON E' UN ACCOUNT RUBATO» — con l'ETICHETTA, che e' la parte sottile:
e' la stringa che il venditore legge, e con solo `clonat` dentro
prometteva due famiglie che la voce non blocca piu'.
Piu' la voce in «Dove il deposito non puo' proteggerti»: un posto puo'
sparire dopo, ed e' PEGGIO del codice riscattato perche' il bene
funzionava e poi ha smesso.
E `stima_coda_moderazione.py` ERA ROTTA DA AGOSTO, trovata di striscio:
lo strumento che misura quanto cresce la coda — il numero su cui poggia
la decisione del declassamento — moriva di NameError. Adesso c'e' una
prova che lo fa GIRARE, ed e' quella che ha preso anche la seconda
meta' della cura (`_vietato_bloccante` chiama `divieto_bloccante`, che
la prima stesura lasciava fuori: un patch puo' applicarsi pulito ed
essere incompleto).
Collaudato: **6951 prove verdi** (una famiglia nuova che GIRA i giudici
e il filtro parole invece di guardarli, piu' quattro asserzioni che
hanno CAMBIATO LATO col perche' scritto) e **16 MUTAZIONI, 16 uccise**,
una per riga sorvegliata. La sola sopravvissuta al primo giro non era
di questo cantiere — togliere una `prove_*` dalla tupla di `main()`,
che fa sparire una prova dal giro senza far diventare rossa NIENTE — e
da li' il censimento delle prove orfane, che copre anche il cantiere di
domani.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — il prompt vale per i giudizi nuovi e gli
annunci gia' in coda restano dove sono.
IL COLLAUDO COL MODELLO VERO È **30/30 AL PRIMO GIRO** (28 ago 2026,
Andrea sul VPS, era 25/25): i cinque casi nuovi passano tutti, e
nessuno dei vecchi è caduto. È la cosa che dice se il modello ha
capito, e in locale non si può fare — vuole la chiave.
⚠️ VA RILANCIATO A OGNI RITOCCO DEL PROMPT, e questa è la lettura
delle cadute per il prossimo giro: se cade la GEMELLA del DAZN la cura
ha imparato l'esempio invece della regola; se cade il Netflix la parola
«condiviso» è diventata un lasciapassare; se cadono il Disney+ rubato o
la carta clonata il muro si è allentato. Il conto si scrive COL NOME di
quel che cade, che un «29/30» senza nome è un numero su cui fra sei
mesi nessuno può agire.
DA GUARDARE al primo giro: il primo annuncio vero di piano condiviso, e
il registro `moderazione_log` — se i «credenziali» cominciano a
comparire fra i dubbi invece che fra i rifiuti, il declassamento
accorciato sta funzionando.

La card P2P resta in vista (ago 2026, decisione di Andrea): «Da
scoprire» non toglie piu' la card a chi ha gia' premuto «Avvisami».
LA DOMANDA CHE ANDREA HA FATTO — «cosa mostra a chi ha gia' votato?
non puo' dire ancora Avvisami» — HA UNA RISPOSTA CHE ROVESCIA LA
PREMESSA, ed e' la parte da tenere: la card «Avvisami» non l'ha mai
detto. Mostra il disegno e il titolo «P2P», cioe' il NOME della
sezione, e l'aria-label dice lo stesso; l'invito vive DENTRO la
pagina, dove il bottone diventa «✓ Ti avviseremo» da solo. Quindi a
chi ha votato non si mostra niente di diverso, e non c'era nessun
invito da correggere.
E LA PROPOSTA «✓ Ti avviseremo» SUL TITOLO NON ENTRA, ed e' MISURATO
e non un'opinione: la fascia del contrasto finisce a 282 sui 318 dove
comincia la scia dorata, quindi il capolinea sono i TRE caratteri di
«P2P» — il quarto porta la fascia a 342 e la CI diventa rossa, quella
frase va a capo in una scatola da 96px e arriva a 390. Vedi
Architettura, «RESTA SEMPRE, ANCHE A CHI HA GIA' VOTATO», per i due
prezzi dichiarati (la sezione che non puo' piu' sparire e la spinta al
P2P che diventa permanente) e per `interessiNoti`, che se n'e' andato
col lampo che era nato a curare.
Collaudata: **6972 prove verdi sull'albero ISOLATO** (HEAD piu' i soli
hunk di questo cantiere: la copia di lavoro e' condivisa con altre due
sessioni — e' il DELTA il numero difendibile, −3 sulle 6975 di HEAD,
che il cantiere TOGLIE uno stato e i suoi casi), con la sentinella
della sparizione e i due casi del banco che CAMBIANO LATO col perche'
scritto, e **5 MUTAZIONI, 5 uccise** — la sparizione rimessa, il voto
che torna a ridisegnare la fila, il flag che rinasce, la card che
sparisce col barattolo, il tocco che smette di navigare. La prova che
conta e' quella che GIRA: `interessiMiei` si muove sul catalogo VERO e
la fila deve restare la stessa — una sentinella sulla forma non puo'
dirlo, perche' il catalogo quella lista non la nomina piu'.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client. DA GUARDARE al primo giro:
che la sezione «Da scoprire» sia in vista anche nei giorni senza
occasioni, e la crescita ASSOLUTA dei like sul P2P, che da oggi non
si ferma piu' col voto.

Le due strisce sono più grandi sul web (ago 2026, dal campo: «sul sito
le card di Da scoprire e le icone delle categorie sono troppo
piccole»). Da 768px in su e FUORI da Telegram le card dei banner
passano a 400×191 e le celle delle categorie a 120, col titolo che
cresce dello stesso fattore; dentro la Mini App non cambia un byte. Il
difetto era misurato — su desktop una card di banner era larga quanto
una card di annuncio, e la fila non scorreva affatto lasciando ~600px
di vuoto — e le due misure vengono dai FILE e non dal gusto (i banner
816×390 reggono 408 a 2x, le illustrazioni 120 senza scalarsi su
nemmeno a 3x). Vedi Architettura, «LE DUE STRISCE SONO PIÙ GRANDI SUL
WEB», per il giudice `initData` e mai `WEB` (che sarebbe falso per
l'anonimo, in DEMO e in collaudo: mezzo web resterebbe piccolo senza
che niente fallisca), per il gate DOPPIO e per il contrasto, che resta
identico PER COSTRUZIONE quando titolo e card scalano insieme.
Collaudato: **+28 prove** in modalità severa sull'albero ISOLATO — HEAD
più i soli hunk di questo cantiere, che la cartella è condivisa con
un'altra sessione che lavora proprio su «Da scoprire» — con la baseline
di HEAD a 6975/0 e il cantiere a **7003/0**. La prova del contrasto ora
gira su TUTTE E DUE le misure (12,34 / 12,57 / 15,40, identici) e il
fattore file/card si legge dal file invece di essere il 3 fisso, che
l'avrebbe resa cieca proprio sulla variante nuova.
E IL GIRO DAL VIVO NEI DUE POSTI, col codice VERO servito dal server e
non con CSS iniettato: 767 e 768 (il filo esatto: prima le misure di
ieri, dopo quelle nuove), 960, 1280 chiaro e scuro, 375 — e la Mini App
simulata mettendo `initData` PRIMA del documento, dove **a 1280 le
misure sono quelle del telefono, identiche**. Zero scorrimento
laterale, zero errori JS.
⚠️ E IL BANCO HA MENTITO UN GIRO INTERO: lo stub di Telegram da solo non
basta — lo script di telegram.org rimpiazza `window.Telegram`, quindi
la classe compariva lo stesso e il caso Mini App usciva «rotto» mentre
era rotto il banco. Si blocca quella richiesta.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client, e sul telefono (in Telegram
o in browser) non cambia un pixel.

E su desktop le due strisce si scorrono (ago 2026, il giorno dopo, dal
campo: «col dito sul telefono funziona, col mouse no»). Crescere le card
aveva reso VISIBILE un difetto che c'era da sempre: le file scorrono di
lato, la barra è nascosta apposta, e col mouse non c'era nessun
appiglio — le card fuori schermo erano irraggiungibili. Due strade e non
una (decisione di Andrea): le frecce che si vedono e la rotellina che è
il gesto istintivo. Nello stesso giro le card sono cresciute ancora —
**520×248** i banner (rigenerati dagli originali a 1040×498: il loro
tetto non è un muro ma un lavoro) e **160** le celle delle categorie,
dove il muro invece c'è ed è ~190 perché l'illustrazione più piccola è
335×240 — e la prova dei file si scrive col CRITERIO invece che col
numero, che «≥ 3x del mobile e ≥ 2x del web» non invecchia mentre
816×390 sì. Vedi Architettura, «E SU DESKTOP LE DUE STRISCE SI
SCORRONO», per le tre righe del listener da non ammorbidire e per il
fatto che decide tutto: **Blink non dirotta la rotella verticale su una
fila orizzontale**, nemmeno con `overflow-y:hidden`.
Collaudato: **+20 prove** in modalità severa sull'albero ISOLATO (7044 →
7064; la cartella è condivisa con un'altra sessione, quindi è il DELTA
il numero difendibile) e **19 MUTAZIONI, 19 uccise**, una per riga
sorvegliata. Tre erano sopravvissute al primo giro, e sono tutte e tre
buchi delle mie sentinelle e non del codice: il `position:relative` del
guscio, che il commento prometteva e nessuno guardava; il chevron che
tornava a un'entità tipografica; e la prova del file riportata al
numero, che **passa lo stesso** finché i file sono grandi abbastanza —
la classe di guasto che questo repo ha già visto sei volte, la prova
onesta e insufficiente insieme.
E il giro DAL VIVO col server dell'albero isolato: il filo esatto
767/768, la Mini App a 1280 che tiene le misure del telefono e non arma
la rotellina, la rotellina che scorre la fila con la pagina ferma e la
lascia passare a fine corsa, e le frecce che si accendono e si spengono
ai due estremi — provate su una fila che SCORRE DAVVERO, che il primo
giro le aveva guardate sui due banner che su 1160px non scorrono e il
click non provava niente.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna leva, nessuna
rotta — solo client e tre file. DA GUARDARE dal computer di Andrea: le
due file scorse col mouse e con le frecce, che è il gesto per cui il
cantiere esiste.

I relay Nostr diventano una leva (ago 2026, primo passo del cantiere
del relay nostro): dove Barattolo scrive e legge su Nostr si cambia
dal config del VPS invece che con un commit. Erano CINQUE elenchi
scritti a mano che già divergevano fra loro, e la leva ripaga tre
cose vere — puntare a un relay NOSTRO il giorno che ci sarà, togliere
di mezzo in un riavvio un relay che si comporta male, e il debito già
scritto in questo file sui relay che rifiutano gli exit node di Tor,
dove «cambiare relay» era finora un deploy. Vedi Architettura, «I
RELAY SONO UNA LEVA», per le DUE leve e il perché non si uniscono,
e per il FAIL-SAFE, che è l'unico modo in cui il cantiere può fallire
in silenzio.
IL RELAY IN SÉ NON È QUESTO CANTIERE: il quadro completo — dove vive,
quale programma, chi ci scrive — sta nel piano, e le due decisioni
prese sono **4a** (lettura aperta a tutti, scrittura riservata alla
piattaforma e ai venditori con la chiave dimostrata) e la leva
subito. **Resta aperta** la scelta di dove vive, in attesa che LNVPS
risponda su dominio proprio e NIP-11 personalizzabile: senza quelle
due cose il relay gestito esce dal tavolo e resta una macchina
piccola nostra. La macchina del NODO è sconsigliata, e le due ragioni
stanno nel piano — un record DNS che punta all'IP dei canali, e una
porta aperta a chiunque su una macchina dove un guasto costa sats.
Collaudato: **+18 prove** sull'albero ISOLATO (HEAD più i soli hunk di
questo cantiere: la cartella è condivisa con altre due sessioni, e
7306 → 7324 è il DELTA difendibile; le 4 rosse sono preesistenti a
HEAD e sono il mojibake del meno tipografico su una console cp1252,
non del cantiere) e **12 MUTAZIONI, 12 uccise**, una per riga
sorvegliata — la leva che non comanda, il fail-safe che non scatta,
quello che scatta e TACE, le stringhe vuote, il pannello che torna
alla costante, gli extra che saltano il giudice, il doppione che
resta, l'ordine rovesciato, il relay del venditore sparito dal
default, la leva tolta dal file da cui si copia, lo script che si
riscrive la lista invece di ereditarla.
LA PROVA HA TROVATO UN DIFETTO, ed era nella PROVA e non nel codice:
il taglio del blocco si chiudeva sull'ultima assegnazione, che nel
server compare DUE volte — nell'`except` e nel fail-safe — quindi
tagliava alla prima e si portava via proprio il fail-safe, cioè la
riga per cui la prova esiste. Diceva «il fail-safe non scatta» mentre
a non scattare era il taglio. Da lì `_blocco` chiude su una marca
ESCLUSA, che è la prima cosa DOPO il blocco.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna rotta — e **senza le due righe nel config del VPS non cambia
NIENTE**, che è la regressione provata per prima (i quattro di ieri
nel server e i cinque nell'import, nello stesso ordine). Le due righe
si aggiungono al config solo quando ci sarà un relay da aggiungere.

Il rifiuto dice quale divieto è scattato, e cosa fare (ago 2026,
decisione di Andrea da un caso vero: un annuncio bloccato dall'AI e
nessuna strada per protestare). Il messaggio adesso porta le tre cose
che gli mancavano — QUALE dei nove divieti l'ha fermato, che si può
riscrivere e ripubblicare, e dove scrivere se l'errore è nostro — col
modello di `MSG_RIFIUTO_SERVIZI`, che la strada la diceva già. Le
quattro famiglie diventano la FONTE (`DIVIETI_BLOCCANTI`) e le due
liste si derivano da lei, così la domanda «quale?» ha una risposta
invece di essere un `any()` su un elenco piatto. Vedi Architettura,
«E IL RIFIUTO DICE QUALE DIVIETO È SCATTATO», per le parole NOSTRE e
mai quelle del modello, per il ramo dei servizi che NON prende il
«riscrivi» (la strada la dice già), e soprattutto per QUEL CHE NON SI
È FATTO: nessuna valvola per sbloccare i «vietato», perché lì non
manca il bottone — manca l'oggetto, e far nascere in revisione anche
armi e droghe vorrebbe dire tenerle SCRITTE nel database.
LA DIAGNOSI VALE PIÙ DELLA CURA, ed è la parte da ricordare: non
esiste un solo «blocco dell'AI». Se il motivo nomina una delle quattro
famiglie il rifiuto è secco e non lascia NIENTE — la riga non nasce,
l'`HTTPException` alza prima del `db()` — mentre tutto il resto era
già in coda dal cantiere «l'AI segnala, non decide». A distinguerli
nel registro è `esito`: 'vietato' è il secco, 'dubbio' è la coda.
Collaudato: 6760 prove verdi (le nuove: la derivazione identica a
ieri coi prefissi nell'ordine, il giudice girato sui suoi dieci casi,
il censimento dei sei siti, e le tre cose guardate una per una sul
testo che il venditore legge) più DIECI prove che hanno CAMBIATO LATO
col perché scritto — certificavano il messaggio SENZA la strada, cioè
il muro — e **15 MUTAZIONI, 15 uccise**, una per riga sorvegliata.
LA TORTURA HA TROVATO IL BUCO CHE LA RILETTURA NON VEDEVA: il ramo del
FILTRO PAROLE — quello che serve i tre quarti dei rifiuti, perché
viene prima dell'AI — non aveva NESSUNA prova sul testo che compone,
e la sua coda si poteva togliere senza far diventare rossa una riga.
Tutte le prove passavano dal ramo dell'AI. Adesso ha le sue due.
E IL BANCO HA MENTITO DUE VOLTE, tutte e due lezioni già a verbale:
la tortura girata sui file VERI ha lasciato una mutazione su
`server.py` quando il timeout ha ucciso il processo prima del
`finally` (si tortura su una COPIA nello scratchpad, sempre), e nella
copia lo script di tortura messo nella radice faceva scattare
`prove_script_nel_workflow` — «1 rossa a codice intatto», cioè un
banco che non si può credere.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — e un client rimasto in cache riceve
comunque il testo nuovo (viene dal server), solo col tempo di lettura
di ieri. DA GUARDARE al primo giro: il primo rifiuto vero dentro
Telegram — che dica la famiglia giusta e che il canale sia quello del
config — e il registro, per vedere se i falsi positivi cominciano ad
arrivare adesso che si possono segnalare.

Il Profilo a sezioni, e l'indirizzo Tor (ago 2026, decisione di Andrea):
i diciannove cassetti in fila diventano CINQUE sezioni richiudibili —
catalogo, negozio, quando compri, privacy, account — tutte chiuse
entrando; e il ventesimo cassetto porta l'indirizzo `.onion`, che il
servizio nascosto aveva da mesi senza che nessuno potesse saperlo. Il
Profilo passa da ~1660 a **1113px** misurati a 375px (il 1115 della
prima stesura era misurato con un cassetto in meno visibile: il numero
assoluto dipende dalle leve di quell'utente, e a valere è la
differenza misurata prima e dopo nella stessa sessione). Vedi
Architettura, «IL PROFILO A SEZIONI, E L'INDIRIZZO TOR», per la forma
della sezione — una TERZA forma, né etichetta né cassetto, rifatta dal
campo il giorno dopo perché i titoli non sembravano toccabili — per
la riga che il cantiere paga — `apriCassettoProfilo` che apre anche la
sezione, o il cassetto si aprirebbe invisibile — e per le due
decisioni che si leggono male da sole: «Incassi e pagamenti» sta in
PRIVACY perché è il dato più longevo del profilo, e niente si nasconde
a chi non vende.
IL LAMPO DICHIARATO NEL PIANO NON ESISTE, misurato e non supposto: 124
campioni con la vista a schermo, e in tutti la sezione vuota era già
spenta — il Profilo non è la vista d'ingresso, quindi quando ci si
arriva i render sono già girati.
Collaudato: 39 prove nuove (**7067 verdi** in modalità severa, col
censimento che nessun cassetto resti fuori da una sezione e il banco
node che fa GIRARE i quattro pezzi su un DOM di cartone) e **15 + 8 +
12 MUTAZIONI, tutte uccise**, una per riga sorvegliata — fra cui la
sola che dice se la cintura del tetto serve a qualcosa: chi cresce il
corpo E AGGIORNA I LETTERALI delle prove, che è quel che si fa
naturalmente (l'ho fatto io passando da 17 a 18) — lì le prove
letterali seguono il codice e a fermare resta solo il tetto. Più il
giro DAL VIVO col server vero su un database usa-e-getta a
320/360/375 nei due temi — 38 + 108 verifiche verdi e poi le tre
differenze rimisurate una per una, zero errori JS: l'atterraggio sul
cassetto profondo, il cassetto Tor nelle due facce, il caso SENZA
indirizzo, la DEMO dove una sezione sparisce, e la regressione del
ritorno da un annuncio (y=700 → y=700).
⚠️ E UNA SONDA HA MENTITO, la lezione del giro: la differenza della
CARTA misurava «trasparente» per TUTTI E DUE i livelli — perché la
carta è del contenitore `.acc` e io guardavo il suo header `.acc-h`,
che di fondo non ne ha. Il codice era giusto e la misura no: una
verifica che dice quel che non ti aspetti si guarda prima di crederle.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna rotta, nessuna leva nuova — e se `ONION_HOST` sul VPS è vuoto
il cassetto semplicemente non compare. DA GUARDARE dal VPS, ed è il
pezzo che da qui non si può fare: l'indirizzo vero sul dominio `.onion`
col Tor Browser, che la fascia 🧅 e il cassetto dicano la stessa cosa.

I buoni sconto scontano quanto vuoi, e anche a cifra fissa (ago 2026,
decisione di Andrea: «devo poter decidere arbitrariamente quando
scontare, anche 100% se voglio, oppure ancora meglio a valore»). Due
cose in un giro: il tetto della percentuale passa da 30 a **100** e il
pavimento da 5 a **1** — le due leve si slegano da quelle dello sconto
carrello, che è una promessa PUBBLICA mentre un codice è un segreto
mirato — e nasce il secondo TIPO di codice, la cifra fissa: «−10 €» o
«−5.000 sats». Vedi Architettura, «LA PERCENTUALE È LIBERA, E LA CIFRA
FISSA È UN TIPO», per il FONDO della cascata che non si muove (fra
codice e regola vince il maggiore, e un `max()` non è una somma), per
il DEFAULT che È la migrazione, e per la percentuale in ricevuta che
su una cifra fissa è ZERO e non si deduce — con la conseguenza che il
libro mastro ha dovuto imparare.
IL BUG CHE HA TROVATO IL COLLAUDO E NON LA RILETTURA, ed è la parte
che vale più della funzione: il cambio si prendeva solo quando lo
chiedeva una promessa del NEGOZIO, e un codice non è una promessa del
negozio — quindi **ogni buono in EURO scontava ZERO**, in silenzio e
su una strada sola (in sats funzionava). Nessuna sentinella poteva
vederlo: il conto era coerente con sé stesso.
Collaudato: **7023 prove verdi** (le nuove: i due giudici girati sui
loro casi, il banco node della cifra, l'ordine SANO del libro mastro
che spende un codice a valore) più `collaudo_conto.py` a **136 verdi**
(era 99: la PROVA REGINA — preventivo == compra al sat con la bolt11
confrontata — sui due tipi, il 100% che lascia un sat, il buono più
grande del carrello, la divisione a ritroso esatta, e la ronda che
tace) e **21 MUTAZIONI, 21 uccise**. Il primo giro ne lasciava vive
DIECI: nove buchi veri delle mie sentinelle e una mutazione inerte —
l'elenco sta nella voce, perché è il genere di cecità che ritorna.
IN PRODUZIONE basta il deploy: quattro colonne additive che nascono
coi loro default (nessun codice esistente cambia), nessuna migrazione
di dati, nessuna rotta nuova, e le leve hanno il default nel codice.
⚠️ Se il config del VPS ha righe esplicite `CODICI_SCONTO_MAX_PERCENTO`
o `CODICI_SCONTO_MIN_PERCENTO`, vincono sul default e il tetto nuovo
non entra in vigore: si guarda PRIMA del deploy, come per
`MAX_PREFERITI`. DA GUARDARE al primo giro: il primo buono a cifra
fissa speso dentro Telegram, con la bolt11 confrontata su LNbits.

Duplicare un annuncio (ago 2026, chiesto da Andrea: «crea un duplicato
dove posso modificare alcune info — però la chiave è titolo, prezzo e
foto»): «📄 Duplica questo annuncio» nella scheda del proprio annuncio
riempie il form di Vendi con tutto e ne fa nascere uno NUOVO. Titolo,
prezzo e foto arrivano PIENI e non svuotati, ed è la decisione che
governa il resto: sono le tre cose che quasi sempre cambiano, e averle
lì vuol dire correggerle invece che riscriverle — chi ha venti prodotti
simili cambia una parola nel titolo e poche cifre nel prezzo. Vedi
Architettura, «DUPLICARE UN ANNUNCIO», per il fatto che NON è una
modifica (il pezzo che si può capire male, e a dirlo sono testata,
banner e il bottone che resta «Pubblica»), per le foto copiate dal
SERVER coi byte del pieno — il patto della filiera a una sola
compressione — e per gli importati esclusi, che duplicati darebbero
proprio il doppione che la deduplica esiste per togliere.
ZERO ROTTE NUOVE: è `pubblica()` con una chiave in più nel payload,
quindi guardie, scudo anti-doppione, moderazione, Nostr, promo e match
si ereditano per costruzione.
Collaudato: **+38 prove** in modalità severa (7023 → 7061 contro HEAD
del giorno; è il DELTA il numero difendibile, che la cartella è
condivisa con un'altra sessione) più `collaudo_duplicato.py` — 18
verdi, la rotta VERA su un database e una cartella foto usa-e-getta:
il duplicato che nasce, l'originale che non si muove di un byte, i
byte del pieno confrontati, le foto nuove che vincono sull'eredità, la
guardia di proprietà, e il mondo di ieri intatto. Più **15 MUTAZIONI,
15 uccise**, una per riga sorvegliata.
DUE ERANO SOPRAVVISSUTE AL PRIMO GIRO, e sono buchi delle mie
sentinelle e non del codice — la classe di cecità che questo repo ha
già smascherato sette volte: una guardava se una riga ESISTE
(«editandoId = null» c'era ancora, e una seconda assegnazione due
righe più giù passava liscia rimettendo il duplicato in modalità
modifica: adesso si contano TUTTE le scritture di quella variabile nel
corpo), e il ramo del file sparito dal disco scartava in SILENZIO
senza che nessuna prova lo dicesse, contro la regola di casa «nessuna
foto sparisce in silenzio».
E il giro DAL VIVO col server locale su un database usa-e-getta a
320/360/375: il bottone presente sul nativo e assente sull'importato,
il form ereditato coi suoi campi, la pubblicazione che fa nascere
l'annuncio con le foto copiate — `cmp` dice byte IDENTICI — l'originale
intatto, il duplicato che si spegne dopo, e l'uscita con la sua
domanda. È lì che si è visto quel che il foglio non diceva: la nota
«restano com'erano» parlava di foto che nel duplicato non sono ancora
di nessuno, e la riga sotto le miniature lo diceva già meglio.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — e un client rimasto in cache non manda
la chiave nuova e pubblica come oggi. DA GUARDARE al primo giro: il
primo duplicato vero dentro Telegram, e che le foto ereditate si
vedano in vetrina (sono file nuovi con nomi nuovi: se una card resta
col segnaposto, il posto da guardare è `copia_foto`).

Si entra col telefono inquadrando un codice, e la chiave si crea da
qui (ago 2026, chiesto da Andrea in un messaggio solo): «📱 Col
telefono (Amber)» nel foglio del login mostra un QR `nostrconnect://`
— il bunker ROVESCIATO, dove la URI la scriviamo noi e a richiamare è
il firmatario — e accanto c'è la guida «Crea il tuo profilo», che
spiega le due strade (Amber dal telefono, nstart.me dal browser) e
soprattutto COME TORNARE INDIETRO a entrare. Vedi Architettura, «IL
LOGIN COL TELEFONO», per il segreto che è la porta (verso la nostra
chiave effimera può cifrare chiunque veda il codice), per il relay
UNICO nella URI — la riga che impedisce il fallimento silenzioso «il
telefono dice fatto e qui non arriva niente» — e per la delega a
`firmatarioBunker`, che tiene UNO il motore NIP-46 e lascia intatta la
forma della sessione conservata, quindi coda delle firme e modifica
firmata non sanno nemmeno che questa strada esiste.
Collaudato: **+32 prove** in modalità severa (7072 → 7104 contro HEAD
del giorno; è il DELTA il numero difendibile, che la cartella è
condivisa con altre sessioni e le 5 rosse sono le preesistenti —
`websocket` non installato qui) e **19 MUTAZIONI, 19 uccise**, una per
riga sorvegliata. La prova che conta è il BANCO NODE, che fa GIRARE
`firmatarioNostrConnect` su un NostrTools di cartone: tre relay di cui
solo il terzo risponde (e nel QR finisce solo quello), il messaggio
col segreto sbagliato che NON apre, quello giusto che delega al bunker
con la chiave del mittente e senza il secret, e la lista vuota che non
disegna niente — cose che una sentinella sulla forma non può dire.
E IL GIRO DAL VIVO ha trovato quel che le prove non vedevano, per la
solita ragione: due difetti di RESA e un fatto del mondo. Il bottone
andava a capo (130px di altezza) e la URI stampava cinque righe di
gibberish — curati con la misura e col vestito che il progetto ha già
(`.invoice`, tre righe e testo intero per la copia) — e
soprattutto **`relay.nsec.app` non risponde nemmeno a una GET**, cioè
il relay dedicato al NIP-46 faceva aspettare quindici secondi prima
che il codice comparisse. Riordinata la lista (damus in testa), il QR
compare in ~1 s: il fatto è misurato e scritto accanto alla costante.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — il bottone compare da sé appena
`relay_nip46` arriva al client, e chi resta su un client in cache non
lo vede e continua a entrare come oggi.
DA GUARDARE al primo giro, ed è il pezzo che da qui non si può fare:
**una scansione vera con Amber su un telefono** — che l'approvazione
faccia comparire l'utente qui, e che la sessione conservata regga al
riavvio (una firma chiesta il giorno dopo non deve rimandare al QR).

La pagina del Consigliato, cinque ritocchi su sette (ago 2026, dal
campo). Via l'occhiello (diceva in anticipo quel che la prima riga
della storia dice meglio), il bottone **Acquista** accanto a «Leggi la
storia» — che non compra: scorre alla merce, ed è la metà che spiega
perché il racconto vive dentro il negozio — l'**hero dentro il
cassetto** (chiudendo la storia si chiude tutto: fuori restava
l'oggetto più grande della pagina senza niente attorno), e la riga in
fondo accorciata a una frase. Vedi Architettura, «NIENTE COPERTINA» e
le voci sotto, per il prezzo dichiarato dell'hero (il nome del
progetto vive solo lì dentro, quindi a cassetto chiuso non si legge —
la leva è il nome nell'h3, non l'hero fuori) e per quel che resta
scoperto sulla riga.
IL PUNTO 4 NON SI È ESEGUITO ALLA LETTERA, ed è stato riportato ad
Andrea invece di applicarlo in silenzio: la sezione se n'è andata per
metà. Quel che RACCONTA la funzione è sparito, quel che GARANTISCE
resta — «le tutele sull'acquisto sono le stesse di ogni altro
negozio» — perché è l'unica frase che impedisca di leggere
«Consigliato» come un endorsement nostro, cioè ciò che il
`PROMPT_MODERAZIONE` vieta agli altri. Il costo è dichiarato: da oggi
nessuna superficie dice più che quello spazio si compra.
I PUNTI 6 E 7 NON SI SONO TOCCATI, ed è la risposta alla domanda di
Andrea: quella riga è del **NEGOZIO** e non del racconto —
`spedGratisNegozioRiga` si disegna per qualunque venditore con la
spedizione gratis accesa. Toccarla cambierebbe la pagina di tutti, e
in tre modi diversi secondo cosa si tocca: il TESTO si divide fra
l'involucro locale e `frasePromessaSpedGratis`, che è giudice unico di
due superfici in prosa più l'etichetta di «Altri oggetti»; la
POSIZIONE rovescerebbe l'ordine 🚚-prima-di-🎁, che ha la sua prova su
quattro superfici; e il simbolo € viene da `cifraSoglia`, usato
ovunque. È una decisione di prodotto, non un ritocco.
Collaudato: **DELTA +10 prove** sull'albero ISOLATO — la cartella è
condivisa con altre due sessioni, quindi è il DELTA il numero
difendibile — e **15 MUTAZIONI, 15 uccise**, una per riga
sorvegliata — due erano sopravvissute al primo giro ed erano MIRATE
MALE, non buchi del codice: `tourRidotto()` vive in sei posti, e la
mutazione dell'hero aggiungeva spazi invece di spostarlo. Più il giro
DAL VIVO col server vero su un database usa-e-getta a 320/360/375 nei
due temi (**113 verdi, zero errori JS, zero scorrimento laterale**):
l'hero che si vede a cassetto aperto e sparisce a chiuso, «Acquista»
che scorre davvero (l'etichetta atterra a 1px dalla cima) e che resta
visibile a cassetto chiuso.
⚠️ E LE QUATTRO ROSSE DEL BANCO NON SONO UN DIFETTO, ed è la
trappola che ha fatto concludere male per un'ora: sono **mojibake** —
`âˆ'` al posto di `−` — di un banco node lanciato senza
`encoding="utf-8"` (le altre tre chiamate a node del file ce l'hanno).
Falliscono su Windows e passano in CI, che infatti è VERDE sullo
stesso albero. È la lezione già a verbale in memoria, e il modo di
smascherarla è quello: **se la CI è verde su un commit che in locale
è rosso, il difetto è del banco** — si guarda il valore avuto, non il
nome della prova.
E IL NUMERO SI MISURA PRIMA E DOPO, ed è la lezione del giro: il 748
di oggi sembrava una crescita contro il 639 scritto in CLAUDE.md, e
non lo era — quel numero veniva da un altro banco con un altro
catalogo. Rimisurato sullo stesso seme: **897 → 748, cioè −149px** a
cassetto chiuso.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client.

E il giorno dopo, tre ritocchi che si leggono insieme (ago 2026, dal
campo): via il banner delle tutele in fondo al racconto, le due
promesse del negozio SOTTO «In vetrina in questo negozio» — corte e
su fondo neutro, **per tutti i venditori** — e la prosa del racconto
a 15px/1.6, che è `.sicu p`, il corpo delle due pagine di testo lungo
del progetto.
DUE COSE DA DIRE AD ANDREA, e sono le decisioni che il giro ha preso
per lui invece di applicarle in silenzio. 1) SI È SPOSTATA LA COPPIA
e non la sola 🚚 che aveva nominato: le due promesse sono lo stesso
mestiere e il loro ordine è una regola con la sua prova su quattro
superfici — spostandone una sola l'ordine si rovescerebbe leggendo
dall'alto, e le due gemelle avrebbero due vesti nella stessa
schermata. 2) LA CIFRA LA FA `cifraSoglia`, quindi la riga dice
«10 €» e non «10 euro»: quel giudice è unico, e scrivere la parola a
mano vorrebbe dire mentire al venditore che la soglia l'ha messa in
sats.
IL COSTO È MISURATO NEI QUATTRO STATI (i numeri per esteso stanno
nella voce «IL RACCONTO SI LEGGE»), e la riga che conta è che per chi
arriva al negozio da un annuncio — dove il cassetto nasce chiuso — la
merce **non scende: sale di 4px**, perché il racconto cresciuto si
riprende quel che il banner e la testata hanno lasciato.
Collaudato: **DELTA +9 prove**, e a dirlo è la CI: **7352 → 7361,
zero fallite**. ⚠️ IL CONTO CHE VALE È QUELLO DELLA CI e non quello
del portatile, ed è questo giro ad averlo insegnato: in locale la
suite dava **4 rosse su tutt'e due gli alberi** — baseline compresa,
quindi il delta era giusto lo stesso — e a caldo le avevo attribuite
a un'altra sessione. Non erano di nessuna sessione: sono della
MACCHINA (Python 3.14 qui, più vecchio in CI, e l'encoding di
Windows), e sulla baseline la CI le dà verdi. Un numero assoluto
misurato sul portatile non si scrive qui: si scrive il delta, e il
totale lo dice il log della CI. Più **16
MUTAZIONI, 16 uccise**, una per riga sorvegliata. Tre erano
sopravvissute al primo giro: due MIRATE MALE (un'ancora storta, e un
contenitore aggiunto con un NOME DIVERSO invece di spostare quello
vero) e una che ha trovato un buco VERO — la prova chiedeva che la
riga del montaggio ESISTESSE e restava verde con un `if` davanti,
cioè non garantiva l'INCONDIZIONATA. Più il giro DAL VIVO col server
vero su un database usa-e-getta a 320/360/375 nei due temi (**113
verdi, zero errori JS**), dove una prova del banco ha CAMBIATO LATO
col perché scritto: chiedeva la dichiarazione DUE volte, cioè
certificava proprio la riga che Andrea ha tolto.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client.

Le immagini del racconto respirano (ago 2026, chiesto da Andrea:
«come le card in home — quel movimento lento che gia' c'e'»): lo zoom
lentissimo della card degli sconti, piu' lento e piu' timido perche'
qui le foto sono grandi e a colonna piena, sfalsate a coppie e dentro
un guscio che le ritaglia — il fondo non si scopre mai, ed e'
aritmetica e non fortuna. Vedi Architettura, «LE IMMAGINI RESPIRANO».
E CON LORO C'ERA UN RAZZO, tolto due giorni dopo (decisione di Andrea:
«non mi piace come viene»). Partiva dalla card del venditore quando si
tornava a scorrere verso l'alto e si portava dietro una nuvola di fumo
col logo del progetto; se n'e' andato tutto — CSS, markup,
l'osservatore, il file del logo e le sue prove — e la pagina e'
tornata quella di prima. **Quel che NON se n'e' andato e' la regola**,
ed e' la parte che serve fra sei mesi: sopra la merce di uno spazio
pagato non si mette un velo, e le tre condizioni (non spinge, non
copre, con le animazioni ridotte non esiste) restano la specifica di
qualunque ornamento futuro di quella pagina. Sta in Architettura,
«NIENTE RAZZO E NIENTE VELO SOPRA LA MERCE».
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva — il server torna alla whitelist di forma di prima
(`cop` e le cifre, senza `logo`) e il file esce dal repo.
La rete di punti di ritiro di Barattolo 📍 (ago 2026, da un ristoratore
di Milano che si è offerto): per la prima volta un punto di ritiro è
un'entità che proponiamo NOI e non una rete di terzi — «Barattolo»
diventa una voce di `SPEDIZIONIERI`, chi compra sceglie da un elenco
invece di scrivere un indirizzo a mano, il punto SEGNA che il pacco è
arrivato e il codice di ritiro lo conia il server. Le tre decisioni di
Andrea (presa in carico, incentivi non-monetari, ingresso su invito) e
il vincolo che le governa — «il livello dell'incentivo fissa il livello
della responsabilità» — stanno in Architettura, «LA RETE DI PUNTI DI
BARATTOLO», insieme a quel che quelle tre decisioni permettono di NON
costruire: nessuna candidatura, nessuna coda di moderazione, nessuna
mappa, nessuna uscita di sats nuova.
IN CINQUE COMMIT, e il primo non tocca la rete: **la cintura del
ritiro**, cioè il difetto vivo che il quadro ha trovato prima di
scrivere una riga — i due rami fisici di `controlla_scadenze` non
escludevano `'ritiro'`, quindi il giorno del rientro
dell'auto-sblocco un ritiro segnato dal venditore si sarebbe sbloccato
sulla SUA parola, e un punto che segna «ricevuto» farebbe la stessa
cosa. Poi il catalogo col comando del bot, la presa in carico col
codice coniato, e i testi pubblici col distintivo.
LA RIGA CHE COMPRA TUTTO IL RESTO: «se il punto ha segnato, per noi chi
ha spedito ha consegnato». È una DECISIONE dichiarata prima
dell'acquisto — il gemello della regola del codice digitale — e senza
di lei la presa in carico non sposterebbe il peso di nessuna prova. E
la sanzione è quella che abbiamo: **toglierlo dalla mappa**, perché con
un punto non c'è nessun contratto da fargli valere.
Provato: il DELTA sull'albero ISOLATO a ogni commit (+62, +71, +24, +5
prove; la cartella è condivisa con altre sessioni, quindi il totale non
dice niente su nessuno), `collaudo_punti_barattolo.py` da 33 a **121
verdi** col server VERO su un database usa-e-getta, e **sei torture** —
25 + 33 + 13 + 16 + 5 + 5 mutazioni, tutte uccise. Hanno fatto il loro
mestiere: hanno trovato un'esenzione che nessuna prova guardava, tre
prove che non potevano fallire, che **in tutto `prove.py` non esisteva
una prova che chiamasse il criterio di un distintivo**, e infine un
buco del BANCO — una sezione esplosa si portava via il conto finale,
quindi la tortura si autopromuoveva.
E IL GIRO DAL VIVO HA TROVATO QUEL CHE NESSUNA DELLE QUATTRO TORTURE
POTEVA: dopo la presa in carico il venditore LEGGEVA il codice che non
ha coniato, col pannello che gli diceva pure «ciò che hai depositato».
La cura è nel SERVER e non solo nel client — vedi la voce sua in
Architettura — e al suo posto adesso c'è la PROVA con la data.
IN PRODUZIONE il deploy fa girare le migrazioni additive (due colonne
su `ordini`, tutte a 0/'') e **non cambia niente**, per una ragione più
netta di quanto il piano prevedesse: `PUNTI_BARATTOLO` nasce **VUOTO**
— c'è il solo commento che ne dice la forma — quindi non c'è nemmeno
un id da accendere. Il ristoratore ci si scrive il giorno che si sa il
suo **codice negozio**, e da lì si accende con `/punti` sul bot, uno
alla volta. Finché nessuno è acceso «Barattolo» non compare in nessun
elenco. DA GUARDARE al primo giro vero: il primo ordine
verso il punto dentro Telegram — che il venditore veda il nome DEL
PUNTO da scrivere sull'etichetta, che il titolare trovi il pacco nella
sua coda, e che il codice arrivi a chi compra solo DOPO la presa in
carico.

Il libro P2P diventa una vetrina (ago 2026, chiesto da Andrea sullo
screenshot dell'app di Mostro: «mi piace come struttura la pagina, e la
voglio così — ma in stile Barattolo, non copiata»). Cantiere di FORMA:
il motore non si tocca. Le differenze vere erano TRE — la card al posto
della riga, il conteggio, e la reputazione, che ci arriva già dal tag
`rating` del NOSTRO coordinator e che scaricavamo e buttavamo via.
LA CARD È A BLOCCHI e non a righe (la richiesta letterale di Andrea a
metà cantiere, «con questa struttura»): prezzo e scadenza ai due bordi,
la stima in sats sulla riga sua, i metodi in una scatola, chi c'è
dall'altra parte in un'altra. La cifra prima, la persona ultima — ed è
la sola cosa in cui NON si segue il riferimento. Più il conteggio nella
forma di casa, la riga degli esclusi (gli ordini a intervallo sparivano
in silenzio) e il commutatore che passa alle `consegna-pill`. Vedi
Architettura, «IL LIBRO È UNA VETRINA, NON UNA PAGINA DI TESTO», per le
tre righe da non ammorbidire della reputazione, per il selettore
DISCENDENTE che tiene ferme le altre due case di `.p2p-sats`, e per
`min-width:0` che non c'è più — la garanzia non si è allentata, è
diventata strutturale.
I DUE DIFETTI TROVATI LÌ erano preesistenti e MISURATI: la testa senza
`flex-wrap` spezzava il prezzo su 2 card su 7 a 320px col ripiego a
cambio muto, e i metodi allargavano la pagina.
Provato: **+34 prove** sul ramo (7990 → 8024 in modalità severa; le 4
rosse sono le preesistenti — il mojibake della console cp1252: **in CI
il ramo è 8028/0**, e su questo l'autorità è lei) con quattro che hanno CAMBIATO LATO col perché
scritto, e **25 MUTAZIONI, 25 uccise**, una per riga sorvegliata. La
tortura ha trovato una sentinella che guardava se la riga ESISTE invece
di cosa DICE: restava verde con la stima tornata in fila col prezzo,
cioè col difetto appena misurato. Più il giro a schermo a 320/360/375
nei due temi, prima e dopo, coi casi che contano — cambio muto, cinque
metodi di pagamento, reputazione a zero voti, libro vuoto, e un
`total_rating` fuori scala: testa su una riga sempre, zero scorrimento
laterale, i puntini che mordono solo a 320, e le altre due case di
`.p2p-testa` identiche al pixel.
IL PREZZO È DICHIARATO, e la prima stesura di questa riga lo diceva
SBAGLIATO — «436 contro ~360» erano i due cappelli e non le due
altezze. Misurato con la stessa sonda sui due alberi: card **158,9**
contro **99,8** a 320 e **77,7** a 360/375, quindi le offerte intere
passano da **2 a 1** a 320 e da **3 a 1** a 360/375. Il margine dentro
la card è ~12px (l'aria delle due scatole), e non basta: la sola leva
che ne recupera una è la DISCLOSURE, 108,8px a 320, che è una
decisione di prodotto e non un ritocco. Vedi Architettura.
⚠️ E QUELLA DECISIONE È STATA PRESA, nello stesso merge e il giorno
dopo: la disclosure si richiude dalla prima lettura in poi, e la card
in più è tornata a tutte e tre le larghezze — vedi la voce «La riga che
dice chi tiene i sats si richiude dopo la prima lettura», in fondo a
questo file. Fino a oggi questa riga diceva il contrario del codice.
IN PRODUZIONE non cambia niente: è solo client — nessuna colonna,
nessuna migrazione, nessuna leva, nessuna rotta — e il P2P resta dietro
`P2P_ATTIVO`. DA GUARDARE al primo giro vero: un libro con offerte VERE
sul telefono, dove la reputazione arriva dal coordinator e non dal
banco — e in particolare un'offerta senza il tag `rating`, che è il caso
che il collaudo copre e che in produzione decide se la card si legge
lo stesso.

E POI IL COORDINATORE HA RISPOSTO, ma la firma non era l'ultimo strato
(set 2026, il giorno dopo): col client nuovo confermato in pagina il
tocco su «pubblica» non faceva NIENTE — nessun ordine, nessuna riga nel
journal del nodo, console muta. La causa era un BUNDLE VECCHIO servito
dal service worker: `/vendor/nostr.js` sta in dispensa e va
cache-first, `miniapp.html` è una navigazione e va sempre in rete —
quindi le due metà erano di due giorni diversi, e `NT.hmac` non
esisteva. Vedi Architettura, «UN BUNDLE VECCHIO NON FALLISCE DOVE LO
CARICHI», per l'asimmetria per esteso, per il fatto che dentro Telegram
il difetto non si presentava affatto (là il service worker non si
registra) e per le due cure — la guardia che alza al caricamento
dicendo la strada, e il catch che parla quando l'ordine non è mai
comparso a schermo.
⚠️ E LA DIAGNOSI L'HA DATA UNA DOMANDA AL DATABASE DEL CLIENT, non la
lettura del codice: l'errore vero era già scritto, con la sua causa
dentro, in una riga che nessuna vista poteva mostrare — id vuoto,
perché `chiaveScambio` gira prima che l'ordine prenda il suo nome. È la
lezione del giro, e vale oltre il P2P: quando un gesto «non fa niente»,
la prima cosa da chiedere è se qualcuno abbia già scritto il perché
dove nessuno lo guarda.
FATTO (6 set 2026, Andrea sul coordinator vero): dopo unregister del
service worker e clear site data, l'ordine è passato — `new-order`
accettato, 25 EUR Satispay — e anche il RITIRO ha risposto. Quindi
pubblicazione e cancellazione sono provate sulla macchina vera; resta
lo scambio completo con due identità.
Provato: DELTA **+13 prove** (7950 → 7963 sul ramo isolato; le 4 rosse
sono le preesistenti — il mojibake su console Windows, verde in CI, e
la CI su questo commit è verde) e **9 MUTAZIONI, 9 uccise**, una per
riga sorvegliata: la guardia tolta da ognuno dei due rami, la guardia
che torna un booleano invece di alzare, il bundle incompleto che resta
in cache come promessa, un pezzo che esce dall'elenco, il messaggio che
perde la strada, la bandierina che non si alza, il catch che torna
muto, l'ordine senza nome che torna a scriversi.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client. ⚠️ E chi ha l'app aperta da
prima **non prende la cura al primo giro**, che è esattamente il
difetto che cura: `sw.js` non è cambiato, quindi la dispensa resta
quella finché il service worker in attesa non si attiva. Da lì in poi
un bundle disallineato lo dice invece di far sparire un gesto.

Il mazzo viaggia davvero fra i dispositivi (set 2026, dal campo: «Mini
App sul telefono e Mini App su Telegram Desktop hanno mazzi diversi, un
ordine pubblicato dal telefono non si vede sul desktop»). La prima gamba
del mazzo — la copia nel CloudStorage di Telegram — c'era e non
funzionava: si scriveva SOLO alla nascita, quindi un mazzo già in
localStorage non ci finiva mai e una migrazione non esisteva; e
`cloudScrivi` è fail-open MUTA, quindi un fallimento non lasciava
traccia e nessuno riprovava. Più la terza faccia, che il foglio
prometteva sulla base sbagliata: guardava se l'API del cloud ESISTE,
mai se la copia ci fosse. Adesso c'è un giudice solo,
`sincronizzaMazzo()`, con cinque esiti — e la riga del profilo li
legge invece di indovinare. Vedi Architettura, «IL MAZZO VIAGGIA
DAVVERO FRA I DISPOSITIVI», per il fail-closed che costa di più (un
testo che c'è e non si legge NON è un cloud vuoto: sovrascriverlo
butterebbe via una chiave) e per il conflitto, che non si risolve da
solo — due mazzi diversi sono due identità, e il foglio mostra le due
date con due bottoni invece di scegliere.
⚠️ E LA SINCRONIZZAZIONE DAL NOSTRO SERVER RESTA SCARTATA (decisione
di Andrea, ribadita qui): le tre gambe non passano da noi, e
`chiavi_p2p` non ha una colonna dove la metà privata potrebbe finire.
Provato: DELTA **+27 prove** (7963 → 7990 sul ramo isolato; le 4 rosse
sono le preesistenti — il mojibake su console Windows, verde in CI) e
**15 MUTAZIONI, 15 uccise**, una per riga sorvegliata: il cloud
illeggibile sovrascritto, il bundle caricato prima di guardare se c'è
del testo, due mazzi diversi sovrascritti in silenzio o tenuti senza
dire quale, il ramo veloce che non migra o che fa aspettare,
`if (!nuvola)` al posto di `if (!grezzo)`, la scrittura fallita
raccontata come riuscita, il cloud spento raccontato come copia, i due
giri che fanno due letture, il foglio che non rilegge, la riga di stato
che torna a guardare l'API, e le due uscite del conflitto che non
chiedono più niente. La prova che conta non è una sentinella: un banco
node fa GIRARE `sincronizzaMazzo` su sette scenari — le sentinelle
dicono che le righe ci sono, mai che il fail-closed scatti.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client. ⚠️ E AL PRIMO GIRO DOPO IL
DEPLOY qualcuno vedrà il conflitto: il telefono non aveva mai scritto
nel cloud, quindi il desktop ci ha messo il SUO mazzo, ed è il telefono
a doversi scegliere quale tenere. DA GUARDARE: quel foglio (che le due
date siano sensate) e, sui dispositivi allineati, la riga «Ne esiste una
copia nel tuo Telegram» — che da oggi è un fatto verificato e non una
promessa.


Il coordinatore Mostro rifiutava ogni ordine, e la firma era il perché
(set 2026, dal campo — il difetto che ha fermato la tappa 8 prima ancora
che cominciasse). Il client parlava correttamente NIP-44 e il messaggio
arrivava: a non tornare era la FIRMA, perché mostrod la verifica sul
JSON che ri-serializza lui, e noi omettevamo tre campi che serde scrive
a null. Vedi Architettura, «IL JSON CHE SI FIRMA È QUELLO DI SERDE», per
la regola, per il presidio che la difende dal giorno che mostro-core
aggiunge un campo, e per le due righe che il difetto poteva rimettere in
piedi.
⚠️ E LA DIAGNOSI DELL'ALTRO ERRORE ERA SBAGLIATA, ed è la parte da
ricordare: l'«Error serializing message» delle 10:00 l'avevo attribuito
al nome provvisorio `nuovo:N` che usciva come `id`. Tre verifiche
l'hanno smontata — il ramo che lo produrrebbe è già bloccato a monte,
tutte e nove le azioni esistono nell'enum, e i campi sospetti sono
guardati prima. Poi la MISURA l'ha chiusa: col padding NIP-44 un
`content` da 688 caratteri vuol dire plaintext ≤446 byte, e le sole due
firme ne occupano ~330 — dentro ci sta un messaggio SENZA `id` e senza
payload, quindi `nuovo:N` non è mai uscito. Il gate dell'id è entrato
come CINTURA e non come cura. **La causa di quell'errore resta ignota**,
e curare la firma è anche ciò che la rende diagnosticabile: da adesso un
messaggio malformato tira una risposta `cant-do` invece del silenzio.
⚠️ E VA DETTO CHE NEMMENO L'ALTRO CLIENT è riuscito a creare un ordine
(zero eventi 38383 dal nostro coordinator), quindi dopo questa cura può
affiorare un terzo strato.
Provato: DELTA **+17 prove** sul ramo isolato (7933 → 7950; le 4 rosse
sono preesistenti e IDENTICHE sulla baseline — il mojibake del meno
tipografico su console Windows, che in CI è verde) e **9 MUTAZIONI, 9
uccise**, una per riga sorvegliata: la tabella riordinata, un campo che
smette di scriversi a null, un campo sparito dalla tabella, le due
canonizzazioni tolte una per una, il giudice dell'id che accetta tutto,
il provvisorio che torna a uscire, la seconda serializzazione, il gate
che se ne va. Una era MIRATA MALE al primo giro — l'ancora attraversava
un a-capo su un file CRLF, la trappola già a verbale.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta — solo client.
DA GUARDARE alla tappa 8, ed è il pezzo che da qui non si può fare: il
primo new-order vero verso il coordinator — nel journal del nodo non
deve comparire nessun «trade signature does not verify», e l'ordine deve
uscire come 38383 col suo `d`.

CLAUDE.md scende a 518 righe, e la bussola diventa il grep (set 2026).
Il file rientra INTERO a ogni /compact di ogni sessione, quindi ogni
riga che sta lì si paga per sempre: da 28.593 righe è sceso a 518, in
cinque commit. Il criterio l'ha dato Andrea, ed è quello che ha deciso
ogni taglio: cosa una sessione deve sapere SEMPRE, prima di sapere su
cosa sta lavorando.
DUE VINCOLI TROVATI NEL CODICE E NON NEL FILE, ed è la parte che serve
a chi vorrà tagliare ancora. 1) LE REGOLE FERREE SONO INDIRIZZATE PER
NUMERO: ~15 siti fra server.py, prove.py e miniapp.html dicono «regola
ferrea 1/2/3», quindi non si rinumerano e non se ne toglie nessuna —
ed è anche il motivo per cui quella sezione non può traslocare, che una
regola da aprire non è una regola ferrea. 2) TREDICI PUNTATORI NEL
CODICE DICEVANO «in CLAUDE.md» per contenuto traslocato, fra cui una
STRINGA CHE UN MODERATORE LEGGE nel pannello ⚙️ Stato delle leve — e
tre di loro mentivano già prima di questo cantiere. Nessuna prova se
n'era accorta, perché nessuna guardava.
COSA RESTA, e perché: l'intestazione; la bussola; di Produzione solo
ciò che cambia il GESTO invece del contenuto (push su main = online, il
config del VPS che vince sul default del CODICE, il freno del deploy, e
MODALITA_COLLAUDO col BOT_TOKEN vero fuori dal VPS — l'unica riga del
file che permette di rompere la produzione da un portatile); le nove
regole; e «Adesso», cioè cosa c'è da fare, mai cosa è stato fatto.
NON RESTA L'ELENCO DELLE LEVE ACCESE, e ha un'autorità migliore: il
pannello chiede al valore VIVO e non alla costante.
LE DUE REGOLE DIMAGRITE sono l'unica riscrittura del cantiere, perché
lì regola e catalogo erano la stessa frase: nella 3 restano il divieto
(mai StaticFiles su una directory) e le sue due sentinelle, e l'elenco
delle rotte va in ARCHITETTURA — dove peraltro era già sorvegliato da
quelle prove, quindi non serviva stare in CLAUDE.md per essere
rispettato; nella 2 i sei gradini della scala restano NOMINATI (chi
propone qualcosa sa subito se è già in scala) e traslocano i perché.
LA BUSSOLA NON È UN INDICE, ed è la decisione che regge il resto: tre
nomi e il gesto del grep. Un indice di ottantasei cantieri sarebbe un
elenco scritto a mano, e qui un elenco scritto a mano rimpicciolisce —
la lezione del titolo nudo nelle notifiche. Funziona già così:
ARCHITETTURA.md ha UN solo titolo in 23.593 righe e si legge per nome.
IL FRENO È LA REGOLA 8, che era il MOTORE della crescita («a fine
cantiere proponi l'aggiornamento di CLAUDE.md»): adesso dice DOVE va la
voce — in fondo a questo file — e che CLAUDE.md si tocca solo se cambia
una regola. Più le due sentinelle, perché una regola raccomandata e non
verificabile è quella che si scorda: `prove_bussola` guarda le DUE
direzioni (ogni nome punta a un file che c'è, e nessun documento resta
orfano — è la seconda che guiderà il trasloco del nodo Mostro) e i
rimandi dei sorgenti; `prove_tetto_claude_md` tiene il file sotto 538
righe, misurate e non scelte a orecchio (518 + 20: venti bastano a una
regola nuova, non a una voce di cantiere, che ne pesa 40-60).
PROVATO: +5 asserzioni e SEI MUTAZIONI, cinque uccise. La sopravvissuta
è dichiarata e irriducibile: chi alza il tetto INSIEME alla crescita
passa, che sopra l'ultimo tetto non c'è nessun altro strato — ma quel
numero cambia in una riga di diff che si legge. E LA SENTINELLA HA
BOCCIATO IL SUO AUTORE al primo giro: la docstring nominava
`docs/NODO-MOSTRO.md`, che non esiste ancora. La cura non è escludere
la prosa dal censimento — un rimando dentro una docstring è un rimando
— ma non scrivere l'indirizzo di un file che non c'è.
IL CONTROLLO CHE RISPONDE A «SPOSTA, NON RIASSUMERE» non è un
conteggio: uno script prende CLAUDE.md com'era e verifica che OGNI RIGA
TOLTA si ritrovi IDENTICA in uno dei file nuovi, col pool stretto ai
soli file nuovi più le righe APPESE ad ARCHITETTURA. Le righe di
raccordo (le regole 2, 3, 8, il titolo della sezione e il puntatore
vecchio) sono dichiarate a mano, e quel che non si riconosce ALZA
invece di tirare avanti. Torturato anche lui: tolta una riga a caso dal
diario, diventa rosso e la nomina. E NON È UNA FORMALITÀ: al secondo
giro ha trovato un difetto vero che la rilettura non vedeva — lo split
della Produzione mangiava il newline e i bullet uscivano INCOLLATI
(«…con HTTPS).- Dominio: …»), col conto delle righe che tornava, anzi
scendeva, cioè col segno che per un taglio sembra quello giusto.
⚠️ E IL PRIMO GIRO ERA SU UNA BASE VECCHIA, che è la lezione più cara
del cantiere. Il trasloco era stato fatto sopra il main LOCALE, indietro
di 930 righe già pubblicate su origin/main — 686 delle quali proprio
dentro l'Architettura, cioè dentro il file già traslocato. Committato
così, `docs/ARCHITETTURA.md` sarebbe nato monco, e alla riconciliazione
quelle righe sarebbero cadute in una zona rimossa dal commit: sparite
risolvendo il conflitto, senza che niente protestasse. Il rifacimento è
stato fatto in un worktree su origin/main — che non è né un fetch né un
reset, e non tocca la working copy — riancorando ogni taglio al TESTO
invece che ai numeri di riga. Verificato dopo: il nuovo ARCHITETTURA
contiene TUTTE le righe di quello vecchio, zero perse.
E LA BASE NUOVA HA CAMBIATO TRE TAGLI SU QUATTRO, che è la prova che
riancorare non era formalità: lo Stato aveva i cantieri in TRE tronconi
invece di due, la Produzione un bullet in più (le leve del P2P), e il
blocco «Da riprendere» non è separato da una riga vuota dalla voce che
lo segue — presa per paragrafo, se la sarebbe portata dentro CLAUDE.md.
E LA RICONCILIAZIONE HA CAMBIATO ANCORA LA BASE, ed è il seguito di
quella lezione: quando i quattro cantieri aperti hanno chiuso, il
trasloco è stato rifatto una TERZA volta sopra il ramo che li porta
tutti — relay, p2p-altrove, ordini-p2p — invece di essere rebasato. Un
rebase di questi cinque commit chiederebbe a git di riapplicare «togli
23.593 righe e mettile in un file nuovo» su un testo cambiato, cioè un
conflitto da entrambi i lati; rifarlo con gli script ancorati al testo
costa dieci minuti ed è verificabile.
E IL TRASLOCO VA PER ULTIMO, mai per primo: se andasse prima, ogni ramo
dopo di lui produrrebbe un conflitto della forma «riga aggiunta» contro
«zona cancellata» — la più insidiosa che ci sia, perché la risoluzione
istintiva («tengo la mia») cancella il lavoro dell'altro senza che
niente protesti.
E LA FUSIONE DEL NODO L'HA MOSTRATO SUL SERIO: i tre conflitti NON si
risolvevano tutti allo stesso modo. Due erano revisioni dichiarate (il
7 set che dice «Cade quindi la riga che stava qui»), il terzo erano DUE
AGGIUNTE nello stesso punto — il macaroon e la voce della sonda — e
lì tenere un lato solo avrebbe buttato 97 righe committate un'ora
prima. A fermare il `--ours` è stata la cintura dello script, non la
rilettura: un risolutore automatico vale per UNA forma di conflitto, e
va fermato appena la forma cambia.
IL NODO MOSTRO NON SI È SPOSTATO, per decisione di Andrea: quella
sezione aveva lavoro in volo. Resta in CLAUDE.md e la bussola nomina
tre file, non quattro — un puntatore a un file che non c'è è
esattamente ciò che questo cantiere toglie. Quando si sposterà,
`prove_bussola` lo dirà da sola.

Il relay nostro entra nella lista dove Barattolo pubblica (set 2026,
l'ultimo passo del cantiere del relay). Da oggi ogni annuncio esce
anche su `wss://relay.barattolo.store`, e la macchina che serve il
nostro relay smette di essere un posto dove non arriva niente.
LA DOMANDA È NATA DA UN SOSPETTO SBAGLIATO, e la lezione vale più
della cura: aperta la sezione P2P dal sito, nei log dello strfry non
compariva NESSUNA connessione — solo il check di salute al minuto.
L'ipotesi era «il relay nostro non è in `RELAY_NOSTR`», ed era vera;
ma non era la spiegazione, perché il P2P `RELAY_NOSTR` non la legge
proprio. Un'ipotesi vera può spiegare la cosa sbagliata, e allora la
si conferma per il motivo che non c'entra.
SONO DUE LISTE E NON UNA: `RELAY_NOSTR` (→ `RELAYS_VERIFICA`) è dove
il SERVER pubblica e legge gli annunci, e arriva al browser solo
quando un venditore firma il suo annuncio con NIP-07; il P2P legge
`MOSTRO_RELAY`, che viaggia in `/api/me` dentro `p2p_leve` e dice
dove pubblica IL COORDINATOR. Il silenzio era il comportamento
giusto.
LA STRADA SCARTATA, e non si riproponga: mettere il nostro relay in
`MOSTRO_RELAY`. Sarebbe stato un PEGGIORAMENTO, per due ragioni
indipendenti. Il coordinator da noi non può scrivere — la policy è
una whitelist fail-closed che ammette la piattaforma e i venditori
con la chiave dimostrata, e la chiave di Mostro lì non c'è né ci deve
entrare — quindi il nostro relay risponderebbe con zero eventi; e il
client legge il libro da UN RELAY SOLO, il primo della lista che
risponde. Un relay vuoto in testa non è un relay in più: è il libro
ordini che diventa vuoto.
I QUATTRO DI SEMPRE SI RIPETONO NELLA RIGA, ed è la trappola di
questa leva: la variabile ASSENTE vale i quattro di serie, ma
DICHIARATA comanda lei e basta. Vuota è protetta (il fail-safe
rimette i quattro e lo stampa); CORTA no — quella è una scelta, e
viene rispettata. Scriverci il solo relay nostro avrebbe tolto damus,
nos.lol, primal e nostr.mom, cioè avrebbe fatto sparire gli annunci
da dove la gente li legge, senza che niente protestasse.
E VA IN CODA, NON IN TESTA, per una ragione precisa e non per
prudenza: `RELAYS_VERIFICA[0]` è il relay hint dentro il tag `client`
di ogni 30402 (`tag_client`). In testa avrebbe riscritto quel
suggerimento su tutti gli annunci, mandando le classifiche dei
marketplace a interrogare un relay nato ieri invece di damus.
`RELAY_NOSTR_IMPORT` NON SI TOCCA: `importa_nostr` compone `RELAYS`
da `RELAY_NOSTR + RELAY_NOSTR_IMPORT`, quindi il relay nostro entra
anche nell'import PER COSTRUZIONE — che era il patto delle due leve
il giorno che sono nate.
PROVATO SUL VIVO: pannello admin «⚙️ Stato delle leve» → cinque
relay, che è il valore VIVO e non la costante; riavvio pulito, e
serviva — la lista si legge all'import del modulo, quindi senza
riavvio non sarebbe cambiato niente; e il primo 30402 nel database
dello strfry, l'annuncio `barattolo-193`, verificato con `strfry
scan` e non dai soli log.
DA GUARDARE, E NON È UN DIFETTO: dal VPS si vedono connessioni che si
aprono e si chiudono ogni 2-3 secondi. Il sospettato è
`rinfresca_profili_nostr` — al più una volta l'ora, venti utenti per
giro, UNO ALLA VOLTA, e ognuno fa una REQ kind-0 a TUTTI i relay,
ognuna con la sua websocket aperta e chiusa. Combacia col ritmo, e
non è nuovo: il nostro relay è solo diventato la quinta destinazione
di un ventaglio che c'era già. LA VERIFICA CHE LO FALSIFICA È LA
FORMA, e va scritta perché è quel che rende il sospetto una diagnosi:
dev'essere una RAFFICA CHE FINISCE — venti utenti, poi silenzio — e
che torna a distanza d'ora. Se invece è continua giorno e notte la
diagnosi è sbagliata e il sospettato è un altro.
E IL NOSTRO RELAY RISPONDERÀ SEMPRE VUOTO A QUELLE DOMANDE, che i
kind-0 lì non li pubblica nessuno: innocuo, perché `_profilo_nostr`
tiene la prima risposta NON vuota e non la prima che arriva.
⚠️ E DUE COMMENTI ADESSO MENTONO DI UNO: `_profilo_nostr` dice «il
kind-0 dai 4 relay» e `rinfresca_profili_nostr` «sono quattro relay a
testa». Erano già stantii dal giorno della leva — il numero non vive
più nel codice — e si correggono al primo giro che passa di lì.
IL DIFETTO LATENTE CHE RESTA SCRITTO: il plugin del relay ha la
chiave della piattaforma CABLATA, una copia scritta a mano il giorno
del montaggio. Finché combacia con la nsec viva tutto passa; il
giorno che la nsec cambia il relay rifiuterebbe i NOSTRI annunci
dicendo «restricted: solo Barattolo e i suoi venditori». La cura non
è toccare il plugin ma `RELAY_CHIAVI_TOKEN`, che accende
`/api/relay/chiavi` — quella rotta mette in testa alla whitelist la
chiave con cui il server sta firmando ADESSO, e la lista resta giusta
da sé.
IN PRODUZIONE non c'era niente da deployare: nessuna colonna, nessuna
rotta, nessuna riga di codice — solo cinque righe nel config del VPS
e un riavvio. Che è esattamente ciò per cui la leva era nata.

La riga che dice chi tiene i sats si richiude dopo la prima lettura
(set 2026, la seconda metà del merge della vetrina — e la voce arriva
oggi, col ritardo dichiarato in fondo). Aperta la prima volta che si
apre il P2P, poi dietro «Scopri di più ›»: chi l'ha letta una volta non
deve rileggerla a ogni giro.
LA DECISIONE È DI ANDREA ED EMENDA PER METÀ la riga «la disclosure non
si tocca» scritta il giorno prima, che è la parte da leggere: «Non la
chiudo del tutto: quella riga dice chi tiene i sats, e nasconderla per
guadagnare spazio è la cosa che non facciamo. Ma aperta la PRIMA volta,
e da lì in poi richiusa.»
A SPARIRE È LA RIPETIZIONE, MAI IL FATTO, ed è la condizione che rende
ammissibile tutta la variante: la riga CHIUSA continua a nominare il
custode — «I sats li custodisce il coordinatore (Mostro), non
Barattolo» — quindi chi torna al libro il giorno dopo legge comunque
chi tiene i suoi soldi.
LA FORMULA PIÙ CORTA È SCARTATA, e la ragione è di Andrea: «non cambia
il conto delle offerte, quindi accorciarla è rischio senza guadagno».
Misurato: la riga chiusa sta su DUE righe a tutte e tre le larghezze
(43,5px), e una formula da una riga sola ne toglierebbe 21,8 — che non
fa comparire nessuna card in più e costa la parola «coordinatore».
IL GUADAGNO, misurato sul DOM vero PRIMA di costruire: la riga aperta
pesa 108,8px a 320 (cinque righe) e 87,0 a 360/375 (quattro), chiusa
43,5 dappertutto; il cappello scende da 436,5 a 371,2, e le offerte
INTERE passano da 1 a 2 a tutte e tre le larghezze — cioè proprio la
card che la voce qui sopra dava per irrecuperabile.
Vedi Architettura, «LA DISCLOSURE SI RICHIUDE DOPO LA PRIMA VOLTA», per
il perché il CSS nasconde e il markup resta fisso (le tre sentinelle che
leggono quelle parole nel SORGENTE restano verdi E restano vere: scritte
da un render sarebbero diventate VACUE senza che nessuna fallisse), per
il fail-soft che la fa nascere aperta, per il timbro alla COMPARSA e non
al tocco, per la bandierina `p2pChiDeciso` senza la quale la riga si
richiuderebbe sotto le dita di chi l'ha appena riaperta, e per l'aggancio
in `renderP2P` invece che in `vaiP2P`.
IL RICORDO È DEL DISPOSITIVO E MAI UNA COLONNA, ed era la condizione di
Andrea alla lettera: timbro `p2pchi` in `barattolo_hint`, con la prova
che quel nome in `server.py` non compaia.
LE TRE TRAPPOLE PAGATE COSTRUENDOLA sono di CASA e non di questo
cantiere, e per questo valgono oltre. 1) `pezzo_js` TAGLIA ALLA PRIMA
RIGA VUOTA e non alla graffa a colonna zero: le funzioni nuove, nate
attaccate, si sono mangiate le sorelle e le sentinelle che le affettano
erano diventate VACUE senza che niente fallisse — le funzioni JS di
`miniapp.html` vanno separate da una riga vuota. 2) La sentinella che
vieta le interpolazioni legge la fetta GREZZA, commenti compresi: il
commento che nominava il segno vietato per spiegarlo l'ha fatta
diventare rossa, la trappola della prosa presa mentre la si scriveva.
3) `main()` conta una famiglia esplosa come UNA sola fallita e si mangia
in silenzio ogni `prova()` dopo il raise, quindi la TORTURA legge
«uccisa» per la ragione sbagliata — `find()` col suo guardiano, la
regola di casa pagata qui per la quinta volta.
Provato: DELTA +9 prove sull'albero isolato (8210 → 8219, le quattro
rosse sono le preesistenti) e 13 MUTAZIONI, 13 uccise, una per riga
sorvegliata — e la prima ne fa rosse DUE, che togliendo lo span cadono
insieme «le due forme» e «il custode»: è la prova visibile che la
famiglia non esplode più al primo rosso. Più il giro del timbro dal
vivo: prima apertura aperta e timbrata, ricarica chiusa senza aver
premuto niente, il tocco riapre, e un `renderP2P` non la richiude.
IN PRODUZIONE basta il deploy: solo client — nessuna colonna, nessuna
migrazione, nessuna leva, nessuna rotta.
⚠️ E LA VOCE DELLA VETRINA DICEVA IL CONTRARIO DEL CODICE fino a oggi,
che è la ragione per cui questa voce nasce con un mese di ritardo: là la
disclosure è nominata come «una decisione di prodotto e non un ritocco»,
cioè come la leva NON presa, mentre era stata presa nello stesso merge.
La frase è corretta adesso, e la lezione è quella della regola 8: un
cantiere che atterra dentro il merge di un altro è esattamente quello
che resta senza voce, perché il merge sembra già raccontato.


L'avviso che il profilo c'è già, e sta su un altro dispositivo (set
2026, tappa 7b del client P2P). Chi apre il P2P da dove il mazzo non c'è
— il sito, la PWA, l'APK — ne farebbe nascere uno nuovo in silenzio,
lasciando indietro identità e reputazione. Adesso il foglio glielo dice
prima.
IL SEGNALE SONO DUE FATTI INSIEME, e nessuno dei due basta da solo: qui
il mazzo non c'è e il cloud di Telegram non l'ha dato, ma il SERVER sa
che questo account una chiave l'ha registrata ALTROVE. Allora «nasce da
solo al primo scambio» è falso — è già nato, e sta su un altro telefono
— e chi si fida di quella riga fa nascere una seconda identità.
LA RIGA STA NEL FOGLIO DEL PROFILO e non in testa alla vista: è il ramo
senza mazzo di `renderProfiloP2P`, cioè lo stesso posto dove prima si
leggeva la frase rassicurante, con accanto l'importazione da codice
segreto che è la via d'uscita vera.
SI CHIEDE, NON SI GENERA: qui non nasce niente — a generare è solo
`assicuraMazzo`, che parte da un gesto.
ESCE UN CONTO E MAI UNA PUBKEY, ed è la riga da non ammorbidire.
L'elenco sembrerebbe più utile e sarebbe il difetto peggiore di questa
strada: metterebbe per iscritto, in una risposta sola, il legame fra un
account Telegram e TUTTE le sue identità di scambio — proprio la
correlazione per non fare la quale il mazzo esiste. Nessun parametro, in
nessuna forma: non si può chiedere DI UN ALTRO, e non esiste nemmeno la
sintassi per provarci.
`dal` È UN PAVIMENTO E NON UNA NASCITA: è `MIN(creato)`, cioè la prima
volta che il server ha visto una chiave tua, e una chiave registrata
tardi non dice quando il profilo è nato. A schermo diventa «almeno da» e
mai «creato il».
FAIL-OPEN, che è il verso giusto qui: se non si sa, non si avvisa —
meglio nessun avviso che un avviso su un conto che non abbiamo. E il
conto ha TRE stati e non due: `null` è «non lo sappiamo», che è un'altra
cosa da «nessuna».
LA CACHE È LA PROMESSA E NON IL CONTO CHE NE ESCE: col gate booleano il
secondo chiamante arrivato mentre la risposta è in volo prenderebbe un
vuoto. E il foglio non aspetta — si disegna quel che si sa e si
ridisegna quando il conto arriva, solo se è ancora aperto.
IL NUMERO NON VA MAI A SCHERMO, ed è una scelta di esattezza prima che
di riserbo: la tabella non distingue l'identità del mazzo dalle trade
key, quindi risponde bene a «almeno una?» e MALE a «quante?».
DIMENTICARE BUTTA ANCHE IL CONTO, e non è un dettaglio: la chiave appena
cancellata era una di quelle contate, quindi un conto letto prima
direbbe «ce l'hai altrove» di una chiave che era PROPRIO QUESTA.
LA GET STA DOPO LA DELETE E NON FRA LE DUE, con la sua sentinella: le
fette di `prove.py` tagliano la POST fino a `@app.delete`, quindi una
GET messa in mezzo finirebbe dentro quella fetta e farebbe rossa la
sentinella del vicino. In coda non disturba nessuno.
LE DUE MANI, dichiarate: i pezzi 1 e 2 vengono dalla sessione
precedente, esauritasi mentre scriveva le sentinelle mancanti; le tre
sentinelle sono di quella dopo.
Provato: 8231 → 8234 (+3, con PYTHONUTF8=1). La tortura del pezzo 2
aveva lasciato vive DUE mutazioni su 14, e le sentinelle nuove le
uccidono: 1) la guardia sul CONTO invece che sul GIRO — due chiamanti
nello stesso istante fanno due fetch, e col server muto il conto resta
`null` per sempre, quindi si richiederebbe a ogni giro, cioè proprio nel
caso in cui non si sa niente e chiedere ancora non aiuta; 2) la guardia
su `dal` che cade — con `dal` a zero la coda diventerebbe «(almeno da
gen 1970)», una data precisa e falsa, che è peggio del silenzio.
Rimesse a mano una per volta, file ripristinato prima di committare.
Adesso 14 su 14.
IL DEBITO È PAGATO: LA TORTURA DEL PEZZO 1 È STATA FATTA (set 2026),
e qui c'era scritto che finché non lo era questa riga restava. Sedici
mutazioni, una per riga sorvegliata dell'endpoint, rimesse a mano una
per volta su un worktree pulito da `origin/main` — mai sui file veri —
con la base misurata prima (8336 passate, 0 fallite, `PYTHONUTF8=1`) e
il file confrontato col suo `.bak` alla fine. QUINDICI UCCISE: via
l'identità, via il gate, il gate che guarda la leva GLOBALE invece
della persona, il 409 che diventa 403, un parametro nella firma, un
parametro nel path, la GET rimessa FRA la POST e la DELETE, la DELETE
che si mette a contare, `MIN` che diventa `MAX`, il `WHERE tg_id=?` che
perde l'uguale, le pubkey che escono dal giudice, il pavimento di `dal`
che cade, una scrittura dentro la lettura, la fusione che non porta più
le chiavi, e le pubkey aggiunte alla risposta della rotta.
UNA SOLA È SOPRAVVISSUTA, ed è la ragione per cui la tortura si fa: LA
GET CHE SCAVALCA IL GIUDICE e si rifà la query in casa. Tutto restava
verde — 8336 su 8336 — perché il banco sqlite continuava a esercitare
`_conta_chiavi_p2p`, che intanto non chiamava più nessuno: le sue
sentinelle parlavano di CODICE MORTO, e la rotta vera non la guardava
nessuno. È la stessa forma della cecità già a verbale sulla sonda del
coordinatore: la prudenza scritta in un posto e mancante in quello
accanto — la POST aveva la sua «il conto lo fa il giudice puro» dal
primo giorno, la GET no.
LA SENTINELLA NUOVA è la gemella di quella della POST, e la mutazione
rimessa dopo averla scritta muore su di lei sola. Provato: 8336 → 8337.
IN PRODUZIONE basta il deploy, ma NON è solo client: c'è una rotta nuova
(`GET /api/p2p/chiavi`) — nessuna colonna, nessuna migrazione, e a leva
`P2P_ATTIVO` spenta risponde 409 come le sue sorelle. DA GUARDARE al
primo giro vero: qualcuno che apre il profilo dal sito avendo il mazzo
sul telefono, e legge l'avviso invece della frase di prima.


Gli scambi P2P finiti si tolgono, e a decidere è un giudice solo (set
2026). Fin qui la lista degli scambi non aveva modo di accorciarsi: le
righe finite restavano lì per sempre, e in fondo il tetto ne mostrava
dodici mentre le altre si accumulavano invisibili.
UN GIUDICE SOLO — `p2pTogliibile` — E LO CHIEDONO IN DUE: la ✕ della
riga e la scopa che gira in testa a `scambiP2P()`. Due letture della
stessa domanda un giorno direbbero due cose diverse, e qui la differenza
sta fra una riga che sparisce e dei sats che restano senza padrone. Il
giudice nuovo è la funzione, non l'elenco: `P2P_FINALI` (concluso,
annullato, rifiutato) era già di casa e non si tocca.
LA RAGIONE DELLA GUARDIA, che è quel che va capito prima di
ammorbidirla: togliere una riga APERTA cancella la sua chiave di trade,
e i sats bloccati restano senza nessuno che li muova. Non è una riga che
se ne va, è un pagamento che non ha più padrone. Su Barattolo la riga
vive nel database e «nascondi» la lascia dov'è; qui il telefono È
l'archivio, quindi togliere è per sempre.
«senza_risposta» È IL CASO SOTTILE e non è finale: il coordinatore non
ha risposto in tempo, ma l'ordine può essere vivo lo stesso e la sua
chiave serve a riprenderlo. Si toglie solo dopo l'ORIZZONTE del
coordinatore — `expiration_hours` = 168 ore, la leva girata il 6 set —
oltre il quale nel libro non c'è più niente da riprendere. E senza
un'ancora si TIENE: fail-closed nel verso giusto, che una riga di troppo
costa una riga e una chiave buttata costa i sats di qualcuno.
E LA RIGA LO DICE invece di tacere: «Resta qui ancora N giorni», con la
RAGIONE e non col solo fatto — un bottone che non c'è senza un perché si
legge come un guasto — e cade da sola quando smette di essere vera.
LA SCOPA CI METTE DUE CONDIZIONI SUE: trenta giorni senza cambi di
STATO, e mai un «concluso» col voto ancora da dare, che è finale per i
sats e non per la reputazione — e sul coordinatore la reputazione è
l'unica cosa che chi scambia si porta dietro. Gira alla lista perché la
lista è l'unico posto che li mostra: nessun timer da ricordare.
«aggiornato» È L'ULTIMO CAMBIO DI STATO E NON L'ULTIMO TOCCO, ed è la
riga da leggere prima di tarare i giorni: sbaglia nel verso di togliere
PRIMA, e l'unico caso in cui conterebbe — il voto — lo copre la guardia
qui sopra.
L'ID ARRIVA DAL DOM, E IL DOM NON È LA VERITÀ: il giudice si RICHIEDE
dentro `togliScambioP2P`, che è la stessa ragione per cui sul server la
guardia di proprietà sta dentro la WHERE e non nel client.
LA MISURA DELLA ✕ HA CORRETTO UN COMMENTO che prometteva più del fatto:
il wrap della riga meta è vero, ma col contenuto reale non si presenta
mai, perché il caso peggiore sono DUE span e non tre — «tocca a te» esce
da `azioniDisponibili()`, che tace proprio sugli stati finali, cioè
quelli su cui la ✕ compare, e le due cose non possono coesistere.
Misurato a 320, 360 e 375px: la ✕ resta IN RIGA a 31px dal bordo destro,
e il suo costo sono +3,8px di card perché il bottone è più alto del
testo, non perché scenda. Col numero da rimisurare scritto accanto, se
un domani si aggiunge uno span.
NELLO STESSO GIRO SONO CADUTE DUE PROMESSE più larghe del fatto: il
commento di «aggiornato», e quello del tetto che diceva «i vecchi non
spariscono» — vero prima della scopa, falso dopo.
A QUATTRO MANI, e va a verbale perché il cantiere è passato di sessione
in sessione: il giudice, la scopa, la ✕, la riga che spiega l'attesa e
il commento del tetto sono della sessione b6f014b5, esaurita il 7 set
alle 11:20; di lì in poi le sentinelle, la tortura e la misura.
Provato: 57 verdi fra commenti CSS, parse del client e le sentinelle
nuove — `prove_scambi_p2p_vecchi`, che fa GIRARE il giudice su 21 casi
in un banco node, perché una sentinella dice che il giudice esiste e mai
che risponda — più DIECI MUTAZIONI, dieci uccise, zero sopravvissute.
IL DEBITO CHE ARRIVA COL LAVORO, e si è pagato dopo: il gesto nuovo
passa da `chiediConferma`, quindi il conteggio della domanda unica
restava a 54 — prova già rossa sul SUO ramo, e non un effetto della
riconciliazione. Pagato in `d65d3e9`: 55, col registro sopra la prova
che dice QUALE gesto è e perché passa di lì, che è quel che fra sei mesi
permette di sapere se un gesto nuovo ci deve stare. Il numero da solo
non basta, e i conteggi si RIMISURANO invece di sommarli a mente.
IN PRODUZIONE basta il deploy: solo client — nessuna colonna, nessuna
migrazione, nessuna leva, nessuna rotta — e il ricordo degli scambi vive
nel localStorage del dispositivo, quindi non c'è niente da migrare a
nessuno. DA GUARDARE: la prima riga «Resta qui ancora N giorni» su un
ordine vero rimasto senza risposta, e la scopa, che non ha ancora potuto
togliere niente — perché lo faccia serve uno scambio fermo da trenta
giorni, e il più vecchio è del 6 set 2026.

Gli ordini P2P si vedono anche sul relay nostro, e il lettore ha
smesso di scommettere (set 2026). Il libro di Mostro viveva solo sui
relay del coordinator: se cadevano loro, cadeva il libro. Adesso
`relay.barattolo.store` ne tiene una copia, e il client legge da tutti
insieme.
QUESTA VOCE ROVESCIA UNA DECISIONE SCRITTA, e va detto in testa perche'
chi la ritrova deve sapere che non e' una svista: la voce «Il relay
nostro entra nella lista dove Barattolo pubblica» (`c7802e7`) aveva
SCARTATO l'idea, con due ragioni. Erano giuste tutt'e due, e il
cantiere non le ha ignorate — le ha tolte di mezzo una per una. «Il
coordinator da noi non puo' scrivere»: infatti non gli si chiede, lo
specchio siamo NOI che andiamo a prenderci i suoi eventi. «Il client
legge da UN RELAY SOLO, e un relay vuoto in testa e' il libro che
diventa vuoto»: infatti il lettore non e' piu' quello.
IL DIFETTO ERA STRUTTURALE E NON DI CONFIGURAZIONE: `leggiLibroMostro`
prendeva il primo relay che rispondeva, e «risponde» comprende
«risponde con zero eventi» — un EOSE vuoto e una risposta piena si
servono uguali. E' la stessa cecita' di Q3 della sonda del
coordinator, dove «non ti riconosco» si serve COME una lista vuota. La
cura non e' indovinare l'ordine giusto della lista: e' la lezione gia'
a verbale — si rende ROBUSTO IL LETTORE invece di scommettere sul
campo. Ventaglio con `Promise.allSettled`, unione per `d` (il dedup
c'era gia', e il suo commento era scritto proprio per questo giorno).
E IL TEMPO PEGGIORE MIGLIORA: tre relay muti in fila costavano 24
secondi, insieme ne costano 8.
LE DUE LISTE NON SI FONDONO, ed e' l'invariante che regge tutto.
`MOSTRO_RELAY` e' dove il coordinator ASCOLTA — e il client la scorre
anche per PUBBLICARE le richieste di scambio — mentre
`MOSTRO_RELAY_SPECCHIO` sono relay da cui si LEGGE soltanto. Uno
specchio finito nella prima si prenderebbe una richiesta di scambio
che nessuno leggera' mai: nessun errore, nessuna riga nel log, solo un
coordinatore che «non risponde». Lo sorvegliano tre sentinelle —
`mostroConnetti` e `mostroChiama` non nominano gli specchi, e
`leggiLibroMostro` invece li LEGGE dalla leva (il verso opposto vale
quanto gli altri due: se il lettore smettesse di usarla, la leva
sarebbe morta e il libro continuerebbe ad arrivare, cioe' il cantiere
sarebbe disfatto senza che niente diventasse rosso).
LA TORTURA HA TROVATO UNA SENTINELLA CIECA, ed e' la lezione del giro:
la terza cercava la parola nel TESTO della funzione e la trovava nei
COMMENTI, quindi svuotare la lista degli specchi la lasciava verde.
Quattro mutazioni provate, tre uccise e quella sopravvissuta. La cura
e' un `solo_codice` per il JS, gemello di `codice()`, e l'ancora
spostata sulla RIGA che legge la leva. Una guardia che si accontenta
della prosa e' peggio di nessuna guardia: da' l'impressione di
sorvegliare.
LO SPECCHIO E' UN `strfry router`, NON UN `sync` A TIMER: tiene una
sottoscrizione viva, quindi il ritardo e' di secondi. Su questo libro
il ritardo si paga caro — un ordine che passa da `pending` a preso e'
una SOSTITUZIONE, non una cancellazione, quindi uno specchio indietro
lo mostra ancora disponibile e chi prova a prenderlo si becca un
errore che non sa spiegarsi. Per questo il libro dice anche se e'
COMPLETO (ha risposto almeno un relay del coordinator): se ha parlato
solo lo specchio, la pagina scrive «elenco parziale» invece di
«nessun ordine aperto».
LA WHITELIST NON SI E' TOCCATA, e non per fortuna: il plugin
`chi-scrive.py` lo invoca l'ingester del processo `strfry relay`,
mentre il router e' un ALTRO processo che apre l'LMDB e ci scrive
dentro. Confermato sul binario di strfry 1.1.3, che porta sia
`pluginDown` sia `pluginUp` — se il writePolicy coprisse gia' quella
strada, quelle opzioni sarebbero ridondanti. La chiave del coordinator
NON entra in `chiavi.txt` e non deve entrarci: quella lista e' di chi
ci scrive DA FUORI. Il ramo di riserva (`MOSTRO_HEX` in testa a
`/api/relay/chiavi`) e' decaduto prima di essere scritto.
IL PERIMETRO, a verbale perche' la domanda torna: `authors =
MOSTRO_HEX` vuol dire «del NOSTRO coordinator», NON «nato in
Barattolo». Il nostro mostrod e' un coordinator PUBBLICO per
costruzione — chiunque conosca la npub e un relay che ascoltiamo puo'
mandargli un `new-order`, e non c'e' cancello (pow 0, bond
commentati); la npub e' gia' scopribile, perche' ogni nostro 38383
sui relay pubblici la porta come `author`. E NESSUN CAMPO DISTINGUE I
DUE CASI: i tag del 38383 li scrive mostrod, non chi pubblica
l'ordine — la stessa lezione gia' scritta per `rating` — e l'elenco
verificato su `nip33.rs` non contiene niente che dica chi e' il
client. Quindi il criterio in piu' non si puo' mettere ne' nello
specchio ne' nel lettore: non c'e' nulla su cui filtrare. Oggi le due
frasi coincidono per OSCURITA', non per costruzione, e l'oscurita' si
consuma da sola man mano che il libro cresce.
E IL RISCHIO VERO NON E' QUELLO TEMUTO: un ordine creato da un client
esterno col nostro coordinator e' operativamente NOSTRO — lo
garantiamo noi, la hold invoice sta sul nostro nodo, l'1% lo
incassiamo noi. Non e' inquinamento, e' lavoro. Il rischio e' l'altro
lato, che creare ordini junk oggi non costa niente, e la cura e' gia'
scritta: i BOND, non un filtro. Il registro degli ordini «nati in
Barattolo» resta un cantiere suo, e ha un costo di privacy da pesare
(legare un conto Barattolo a un id di ordine Mostro) che non si
decide di sfuggita.
DUE TRAPPOLE PAGATE SULLA MACCHINA. L'entrypoint dell'immagine non
inoltra: `--entrypoint strfry` risponde «executable not found», ci
vuole `/app/strfry` — e si scavalca `strfry.sh` invece di passargli
argomenti, perche' quello script e' fatto per il relay (si copia il
template della config, e da non-root fallisce). E LO SCANNER DEI
SEGRETI SAREBBE DIVENTATO ROSSO bloccando il deploy: `router.conf`
porta 64 esadecimali nudi — la chiave PUBBLICA del coordinator, che i
filtri Nostr vogliono cosi' perche' non parlano bech32 — e la CI non
sa distinguerla da una privata. Provato prima di correggere (senza
l'eccezione il file esce nell'elenco, con l'eccezione e' pulito), ed
e' entrato come QUARTO FILE PER NOME e mai la cartella, in tutt'e due
i posti. Il commento li' aveva gia' previsto il giorno: «un quarto
file messo li' domani torna sotto la regola da solo».
PROVATO DAL VIVO, e in due modi che rispondono a due domande diverse.
Con relay finti in Node, otto casi sul solo lettore. E contro i relay
VERI dentro la pagina: coordinator morto → il libro arriva dallo
specchio con «elenco parziale»; specchio morto → il libro arriva
intero; tutti morti → alza come prima; leva vuota → il mondo di ieri.
Piu' una REQ mandata a mano da fuori ai quattro relay, che e' l'unica
domanda a cui `strfry scan` non sa rispondere («quel che c'e' nel db,
il relay lo SERVE a un client qualunque?»): lo specchio dice le stesse
cose dei tre del coordinator, non gli manca niente e non ha niente di
suo.
⚠️ IL LIMITE DELLA PROVA SI DICHIARA: quel giorno il libro aveva ZERO
ordini pending — c'era il solo 38385 — quindi l'unione di piu' eventi
veri non e' stata esercitata, e a coprirla ci sono solo i relay finti.
Si guarda il primo giorno che un ordine vero sta nel libro.
IN PRODUZIONE SU TUTT'E TRE LE MACCHINE (set 2026), e le tre verifiche
non sono la stessa domanda fatta tre volte. Sul relay: lo specchio e'
un servizio del compose e il NIP-11 servito dice la pagina della
privacy — chiesto al relay, non al file. Sul VPS: la leva e'
`MOSTRO_RELAY_SPECCHIO` nel config, e `/api/listings` mostra `relay` e
`specchio` come chiavi SEPARATE — che e' l'invariante guardato dal
lato di chi lo consuma, e non dal lato di chi lo scrive. E il riavvio
del relay si e' dato col NOME del servizio, cosi' lo specchio non si e'
nemmeno interrotto.
DA GUARDARE: che lo specchio non resti indietro in silenzio (il conto
per relay finisce in console a ogni lettura, ed e' il modo in cui uno
specchio fermo si scopre in un giorno invece che in un mese), e il
peso del db, che oggi e' 196K su 6,3 G liberi.
E LA COSA CHE MANCAVA DA UN'ALTRA PARTE, trovata chiudendo: il foglio
del panico del relay non diceva DI QUALE MACCHINA parlasse. Ora ha le
tre in tabella con nome e indirizzo — il relay, il VPS e il nodo — che
e' un'informazione da un rigo e si cercava sotto panico.

L'indice del mazzo converge, e si scrive nei due versi (set 2026,
`716f8d1`). VOCE RECUPERATA IN RITARDO, e si dice: quel cantiere ando'
in commit senza la sua riga in questo file — i suoi perche' vivevano
solo nel messaggio del commit e in CLAUDE.md — contro la regola 8. Sta
qui adesso perche' la fase 2 del cantiere del profilo legato all'account
ci e' passata sopra e ne ha esteso la regola al server: senza questa
voce, quella si leggerebbe come una decisione nata dal nulla.
IL DIFETTO: lo stesso mazzo su due dispositivi tornava `copia` e
l'indice non lo toccava nessuno — lo raccoglieva solo l'ADOZIONE.
Quindi due dispositivi che scambiano entrambi RIUSANO una trade key
gia' viva: `ordiniAscoltoP2P` indicizza per `pubTrade` e l'ultimo
vince, i messaggi di uno scambio finiscono sull'altro, e il
coordinatore risponde `invalid-trade-index` — che a schermo diventa
«prova a riaprire l'app», mentre riaprire non ripara niente.
VINCE IL PIU' ALTO E MAI IL PIU' RECENTE, ed e' la regola che regge
tutto il resto: l'indice conta le chiavi BRUCIATE, quindi tornare
indietro le riusa, e chi e' avanti non ha niente da imparare da chi e'
indietro. Non e' una sincronizzazione, e' un PAVIMENTO.
E SI SCRIVE NEI DUE VERSI, che e' la meta' che si dimentica: col cloud
avanti si allinea il locale, col LOCALE avanti si riscrive il cloud —
ed e' la riprova della scrittura persa, l'unico modo in cui i due
possono divergere (ogni incremento scrive il cloud, e quella scrittura
e' fail-open MUTA). Senza il secondo verso la convergenza resta a
meta': il dispositivo arretrato prenderebbe il massimo fra il suo e un
cloud vecchio, cioe' si allineerebbe a un numero gia' superato.
E IL SEGUITO STA PIU' IN BASSO: la fase 2 del cantiere del profilo
legato all'account ha aggiunto il TERZO posto in cui l'indice converge
— il server, con `p2p_indice` — perche' i due di qui bastano solo a chi
passa dal cloud di Telegram, e col profilo che si ricava dall'account un
browser mai visto diventa il caso normale invece dell'eccezione.

Il profilo di scambio si lega all'account, e le tre strade piu' ovvie
sono tutte sbagliate (set 2026, CANTIERE IN CORSO — questa voce cresce
a ogni fase, e si chiude con l'ultima). Il mazzo Mostro nasceva casuale
nel browser e viveva per DISPOSITIVO: chi apriva Barattolo da un altro
telefono si ritrovava un'altra identita', con altre recensioni. Adesso
chi entra da Telegram ha la chiave d'identita' RICAVATA dal suo
account, cosi' gli stessi scambi si vedono dal bot, dal sito e
dall'app.
IL PATTO E' A TRE LIVELLI E SI DICHIARA, che e' la parte che non si
puo' rimandare: Telegram = comodita', e il server SA RICAVARE quella
chiave; chiave Nostr propria incollata = sovranita' piena, e non la
ricava nessuno; estensione, bunker o Amber = sovranita' piena ma
profilo per dispositivo, spostabile col codice segreto. Il terzo caso
non e' una pigrizia: `firmaMostro` firma BYTES GREZZI, e NIP-07 e
NIP-46 firmano solo EVENTI — non c'e' modo deterministico ne' di
derivare ne' di firmare, quindi promettere di piu' sarebbe mentire.
⚠️ E' L'ECCEZIONE DICHIARATA ALLA REGOLA FERREA 2, la prima da quando
il progetto esiste, e va letta per quel che e': il server non
CUSTODISCE la chiave di nessuno — non c'e' una colonna dove potrebbe
finire — ma la sa RICAVARE, cioe' POTREBBE firmare uno scambio al posto
di chi entra da Telegram. Non lo fa e non c'e' niente che lo faccia; e
«potrebbe» e' scritto in «I tuoi dati» con le parole di chi legge,
perche' un potere che non si dichiara e' un potere che si scopre male.
Vedi Architettura, «LA SCALA NOSTR APPROVATA», dove il gradino nuovo
sta accanto a quello RESPINTO.

LE TRE STRADE SCARTATE, e sono le tre piu' ovvie — questa e' la parte
che serve fra sei mesi, quando qualcuno le riproporra' perche' sono
piu' semplici. Nessuna e' un'idea di qualcun altro da correggere: sono
il primo disegno che viene in mente, ed e' giusto che venga in mente.

1. UN SEGRETO SOLO, COME STRINGA. E' la forma naturale — una riga nel
   config, come il segreto del webhook — e rende la ROTAZIONE
   IMPOSSIBILE. Non «scomoda»: impossibile. Cambiando quella stringa
   cambiano insieme le chiavi di TUTTI, cioe' si cancella in silenzio
   l'identita' e la reputazione di chiunque non abbia salvato il suo
   codice — e se il cambio arriva mentre uno scambio e' aperto, i sats
   fermi sulla hold invoice restano senza nessuno che possa muoverli.
   Da qui il DIZIONARIO `{versione: segreto}` e la colonna `versione`
   in `p2p_semi`: la versione entra nell'etichetta di derivazione,
   quindi due versioni sono due chiavi per COSTRUZIONE, e ruotare vuol
   dire AGGIUNGERE una riga mentre i vecchi restano sulla loro finche'
   non passano con un GESTO. Va deciso il primo giorno o non si puo'
   piu' aggiungere: e' il senso di questa riga.
   ⚠️ E LA ROTAZIONE NON RITIRA UN SEGRETO TRAPELATO, che va scritto
   accanto o si crede il contrario: chi l'ha preso, col sale, ricava le
   chiavi passate per sempre — quelle identita' sono BRUCIATE. La
   rotazione serve a due cose sole, ed e' gia' molto: che nessun
   profilo NUOVO nasca dal segreto bruciato, e che chi c'era sia
   avvisato e traghettato con un gesto invece che in silenzio.

2. IL SEGRETO DA SOLO, SENZA UN SALE PER PERSONA. Sembra sufficiente —
   il segreto e' segreto — e regala il difetto peggiore: chi si porta
   via il SOLO config.py deriva le chiavi di tutti. E il config letto
   da solo e' il caso PROBABILE, non quello raro: un `cat` incollato in
   una chat, una riga in un log, un messaggio d'errore, un backup
   guardato di fretta. Col sale in `p2p_semi` servono DUE pezzi da DUE
   posti, e il config rubato da solo e' inerte.
   ⚠️ QUEL CHE IL SALE NON COPRE SI DICHIARA: chi apre l'archivio
   cifrato del backup ha tutti e due (`backup-fuori.sh` mette database
   e config nello STESSO archivio age), e chi entra nella macchina viva
   pure. Il sale alza il costo del furto piu' probabile, non di tutti —
   e la separazione vera (il segreto FUORI dall'archivio, solo carta e
   Bitwarden) ha il suo prezzo, che un ripristino non rigenera i
   profili finche' non lo si rimette a mano. Resta una cosa APERTA in
   PRODUZIONE.md, non una cosa fatta.
   E il sale NASCE AL PRIMO GESTO e mai alla registrazione, l'abitudine
   di casa: una riga che esiste dice qualcosa, e un sale scritto
   all'iscrizione direbbe «questa persona ha un profilo di scambio» di
   chiunque si sia iscritto.

3. LA DERIVAZIONE SENZA IL RAMO DEL RIPROVA. Un HMAC-SHA256 sono 256
   bit uniformi, e sembra una chiave: non lo e'. Puo' uscire zero, o
   maggiore-uguale all'ordine della curva, e allora NON E' UNO SCALARE
   VALIDO — firmarci darebbe una firma che il coordinatore butta via
   senza che niente lo dica, cioe' il guasto muto di sempre. Si
   incrementa un contatore DENTRO il messaggio e si riprova, che e' il
   ramo di BIP-32. La probabilita' e' una su 2^128, e il ramo esiste lo
   stesso: le cose che capitano una volta ogni mai sono quelle che
   nessuno sa diagnosticare il giorno che capitano.

E LA TORTURA HA CORRETTO DUE VOLTE IL BANCO E MAI IL CODICE, che e' la
lezione del giro. Primo: per esercitare il riprova avevo passato un
ordine finto di 2, e con 2 la condizione diventa «n == 1 esatto» — in
256 giri non capita mai, quindi la funzione ESAURISCE invece di
riprovare con successo, e la prova avrebbe certificato il ramo
opposto a quello che voleva guardare. Con 2^252 il giro 0 cade fuori e
ne servono 37, deterministici perche' l'ingresso e' fisso.
⚠️ SECONDO, E VALE DI PIU': sostituendo il riprova con un `n % ordine`
le due prove restavano VERDI, perche' quel numero e' valido lo stesso.
La domanda giusta non era «e' valido?» ma «e' USCITO dalla serie?» —
ed e' la stessa cecita' della sentinella dello specchio, che cercava la
parola nel testo e la trovava nei commenti. Una guardia che si
accontenta di una CONSEGUENZA del fatto non guarda il fatto. Adesso si
controlla che il seme sia uno degli HMAC della serie: nove mutazioni,
nove uccise.

FAIL-OPEN E NON FAIL-CLOSED, e qui il verso non e' ovvio: leva assente
o storta vuol dire che la strada derivata non si offre e il profilo
resta per dispositivo — il mondo di ieri byte per byte — perche'
spegnere uno scambio per una riga mancante nel config punirebbe chi sta
scambiando per un errore d'amministrazione. A dirlo e' il journal
all'avvio, il gemello della riga di `MOSTRO_HEX`: il config del VPS non
eredita niente da `config_esempio.py`, quindi senza quella riga il
giorno dell'accensione resterebbero tutti per dispositivo e nessuno
saprebbe perche'.

E UN RAMO CHE NON C'ENTRA, a verbale perche' il nome torna: `p2p-pulito`
(worktree in una cartella temporanea di un'altra sessione) NON contiene
un tentativo precedente di questo cantiere. E' un ANTENATO di
`origin/main` — zero commit avanti, cinquantanove indietro — e quel che
porta e' gia' tutto in main: le tappe 3-7b del client P2P (il mazzo nel
browser, il motore, l'ordine, la chat, il campanello, l'avviso «ce
l'hai altrove»). Cercandoci `SEGRETI_PROFILO_P2P`, `p2p_semi` o un
seme: nulla, e il suo albero e' pulito. Resta dov'e' e non si riusa;
letto solo via `git show`, senza entrare nella sua cartella. Le tre
strade qui sopra sono scelte di progetto e non vengono da li'.

L'ordine appeso in «settled-hold-invoice» si chiude a mano, e
l'admin-cancel non c'entra (set 2026). Una prova con Alan sul
coordinator — ordine `5eca1bc6`, nessun fiat mai arrivato — si è
impantanata a metà: il venditore (Andrea) aveva rilasciato, la hold
invoice era stata INCASSATA (7.439 sats = `amount` 7402 + `fee` 37) e
il payout verso il compratore era fallito tre volte con
`MalformedAPIRes`. Andrea chiedeva la via ufficiale per annullare da
admin e farsi tornare i sats. Non esiste, e il perché vale più della
procedura.
UNA HOLD INVOICE SETTLED NON TORNA INDIETRO, ed è la lezione che regge
tutte le altre: `cancel` agisce solo su una invoice ACCEPTED, cioè con
l'HTLC ancora appeso. Dopo il settle il preimage è stato rivelato, i
sats sono saldo del canale, e ANNULLARE UN ORDINE NON È RIMBORSARLO.
Verificato sui byte di tutt'e due i lati e non a memoria: in LND
`cancelInvoiceImpl` (`invoices/invoiceregistry.go`) su una invoice
settled non è un no-op — `shouldCancel` torna `true`, l'update arriva a
channeldb e channeldb rifiuta con `ErrInvoiceAlreadySettled`, la
stringa «invoice already settled» (`invoices/errors.go`); in mostro
`classify_cancel_error` (`src/app/bond/flow.rs`) conosce sei modelli di
«già fatto» e quella stringa non è fra loro, quindi l'esito è
`Transient` e l'admin-cancel ABORTISCE.
E NON CI SAREBBE MAI ARRIVATO COMUNQUE, per due porte chiuse prima:
`dispute.rs` apre una disputa solo da `Active` o `FiatSent` — da
`settled-hold-invoice` non se ne apre più — e `admin_cancel.rs` vuole
un solver assegnato più `check_status(Dispute)`. Idem `admin_settle`.
Anche la via gRPC passa dallo stesso `admin_cancel_action`, e con
`pretrade_only` viene rifiutata ancora prima (`rpc/service.rs`). Il
commento «Funds returned to seller» che si legge in `admin_cancel.rs`
vale solo per l'escrow ancora APPESO: leggerlo come una promessa di
rimborso è l'errore che questo giro ha evitato.
LA RIGA NON ERA FERMA, ERA ARMATA, ed è la ragione vera per cui si è
scritto nel database. Il job dei retry aveva già smesso da solo
(`payment_attempts` 3 contro la leva `payment_attempts` = 3, quindi
`3 < 3` è falso) e la dev fee non c'entrava (`dev_fee` 0, col tappo
`dev_fee_percentage = 0.0` acceso). Ma la richiesta di add-invoice
mandata al compratore era ancora valida: il giorno che il suo client
gliela avesse mostrata, `pay_new_invoice` avrebbe riazzerato
`payment_attempts`, e al giro dopo il nodo gli avrebbe pagato 7.365
sats per un fiat mai arrivato.
LA CURA È UNA SOLA SCRITTURA, e funziona perché TRE code filtrano sullo
stesso campo: `find_failed_payment` e `find_unpaid_dev_fees` (`db.rs`)
e `add_invoice_action`. Portato lo stato a `canceled-by-admin` — la
stringa esatta dell'enum di mostro-core — nessuno dei tre lo vede più,
e a un'eventuale invoice di Alan il nodo risponde `NotAllowedByStatus`
invece di pagare. `UPDATE` con la guardia `AND status =
'settled-hold-invoice'` e commit solo a `rowcount == 1`: se qualcosa
avesse mosso la riga nel frattempo la scrittura non parte invece di
sovrascrivere. Copia del database PRIMA, con l'API `backup` di sqlite e
non con un `cp` a caldo, che su un WAL può uscire incoerente.
`failed_payment` LASCIATO A 1 APPOSTA: quel pagamento è davvero
fallito, e la storia si tiene: il cancello è lo stato.
I SATS RESTANO SUL NODO, E NON È RINUNCIA: il nodo è nostro, quindi
erano già tornati nel momento in cui la hold è stata incassata — solo
nel saldo del canale invece che nel portafoglio. Farli uscire verso una
nostra invoice e rientrare costerebbe routing e sposterebbe liquidità
per niente.
QUEL CHE LA SCRITTURA NON FA, e va saputo: non ripubblica l'evento
Nostr dell'ordine. Nel libro e nel client del compratore resta l'ultimo
stato pubblicato, perché a ripubblicare è un'AZIONE di mostrod e non
una riga nel database.
IL DIFETTO CHE HA CAUSATO TUTTO È DEL CLIENT, E RESTA DA CURARE: a
retry esauriti mostrod manda al compratore un `Action::AddInvoice` —
«rimandami una invoice» — e il nostro client non la mostra. Da fuori
l'ordine sembra semplicemente fermo, e l'unica persona che potrebbe
sbloccarlo non sa di doverlo fare. È il cantiere del client P2P, e
questa prova è il suo caso reale.
E LA SECONDA LEZIONE È SULLA DESTINAZIONE DEL PAYOUT: mai un lightning
address. `is_valid_invoice` accetta indirizzo e LNURL, e `do_payment`
li RI-RISOLVE a ogni tentativo, quindi un server che risponde male
rende il fallimento deterministico — nessun retry lo aggiusterà mai.
`MalformedAPIRes` nasce solo da uno stato HTTP non-2xx (`lnurl.rs`),
cioè la risposta è arrivata ed era un errore: NON è il circuito Tor
freddo della dev fee, che dà `NoAPIResponse`. Due sintomi diversi per
due malattie diverse, e confonderli manda a curare la cosa sbagliata.
IL FORK È INNOCENTE, e conviene averlo scritto: `bar1` tocca solo
`dev_fee.rs`, `config/util.rs` e `lnurl.rs`, quindi tutti i gate letti
qui sopra sono upstream puri e le conclusioni valgono per la macchina
che gira, non per quella di GitHub.
Il tentativo più vecchio (`8448dd70`, hold da 7.425 mai pagata) non
c'entra e non si tocca: nessun HTLC, nessun sat in gioco, scade da
solo. DA GUARDARE: che il client mostri quella richiesta, e che nessun
pagamento fantasma raggiunga mai Alan.

Il loop della restore-session e la domanda mai fatta (9 set 2026, cura
d'urgenza a `d52dac1`, commit `63f623d`). Dal campo, la notte stessa
del deploy: aprendo il P2P la pagina si inchiodava — 184.000 ripetizioni
della stessa riga `[p2p]` in console — e su ogni dispositivo i propri
ordini tornavano «di un estraneo». Confinato per costruzione a chi ha
un mazzo con indice ≥ 1 dietro il gate di prova: il pubblico non ci
passava, e per questo la cura ha battuto il rollback.
IL LOOP ERA UNA FAME DI MICROTASK, ed è la specie da riconoscere:
`chiaveScambio` girava PRIMA di `mostroConnetti()`, cioè prima che il
bundle NostrTools fosse caricato, e l'errore sincrono
(`undefined.utils`) cadeva nel catch fail-open → il `finally` riapriva
il gate → il `.then(() => renderP2P())` rientrava nella condizione
ancora vera. Tutto in microtask e codice sincrono, senza mai cedere il
passo all'event loop: l'`onload` dello script che avrebbe CURATO
l'errore non girava mai. **Un retry immediato su un errore sincrono non
è un retry: è un loop che affama il proprio antidoto.** Due cinture,
perché nessuna basta da sola: l'ordine giusto (la connessione, che
carica il bundle, prima della derivazione) e la bandierina
`p2pMieiChiesto` — si alza PRIMA di chiedere, non si riabbassa da sola,
la riabbassa il gesto «Riprova». Un tentativo per sessione.
E LA DOMANDA NON PARTIVA MAI, la metà muta: la funzione apriva la
sottoscrizione alle risposte e non PUBBLICAVA la richiesta — il
coordinatore taceva su una domanda mai fatta, il timeout scadeva e il
vuoto veniva scritto come «non ne hai». È il difetto che il fail-open
dichiarato nel commit padre prometteva di evitare, tradito da un'altra
porta: **il timeout muto contava come risposta**. Ora la richiesta
parte (busta `restore`, prova d'identità del mazzo — è per IDENTITÀ che
il coordinatore risponde, il fatto della sonda — orecchio aperto prima
di parlare, nonce minato se la soglia non è zero) e il silenzio lascia
`null`, «non si sa»: solo un vuoto arrivato DENTRO una risposta si
scrive, che per Q3 è legittimo.
LA LEZIONE SULLE SENTINELLE, ed è la parte che vale oltre il giro: le
prove di `d52dac1` guardavano la sottoscrizione, l'aggancio, il
fail-open del catch — tutte vere — e nessuna chiedeva «ma la domanda
PARTE?» né «e se l'errore è sincrono, chi ferma il rientro?». Una
suite che certifica i pezzi non certifica il giro: il difetto stava
nei due punti che nessuna prova nominava. Le cinque sentinelle nuove
nominano esattamente quelli (l'ordine bundle→chiave, il tentativo
unico, il gesto che riprova, il publish con identità, il timeout che
non conclude).
DA GUARDARE: se dopo la cura la lista torna ancora vuota coi propri
ordini vivi, il sospetto non è più questo difetto ma l'IDENTITÀ — la
leva `SEGRETO_PROFILO_P2P_VIVA` accesa l'8 set può aver dato al client
un mazzo diverso da quello che ha creato gli ordini, e allora il
coordinatore risponde, giusto, «questa identità non ha niente».

L'annuncio orfano si annulla nel database, e l'evento stantio non ha
denti (9 set 2026). Nel libro del coordinator restava un buy da 5 EUR
(Satispay), ordine `c430cbad`, pubblicato l'8 set da un profilo client
che non esiste piu': nessun client poteva ritirarlo. Solo un annuncio
— `pending`, nessuna hold invoice, zero sats in gioco — e la liturgia
e' quella di `5eca1bc6` (voce qui sopra): lettura in `mode=ro` per
trovarlo (era l'UNICO buy pending rimasto, e combaciava tutto, compresa
la `expires_at` a 168 ore ESATTE dalla creazione — il marchio della
leva del 6 set), copia con l'API `backup` di sqlite e mai `cp` a caldo
su un WAL, poi UPDATE con guardia doppia (`hex(id)` esatto AND
`status = 'pending'`) e commit solo a `rowcount == 1`. Fatto: 1 riga,
rilettura `canceled`.
LO STATO DI ARRIVO E' `canceled` E NON `canceled-by-admin`, ed e' la
differenza da stanotte che merita il perche': `-by-admin` serviva a
zittire tre code che filtravano su `settled-hold-invoice`, e qui non
c'e' NIENTE in ascolto su un pending; `canceled` e' invece il
vocabolario che il libro ha gia' mostrato dopo il ritiro della sonda
(Q1), cioe' quello che ogni client sa leggere.
L'EVENTO 38383 SUL RELAY RESTA STANTIO, E VA BENE COSI' (decisione di
Andrea): la scrittura nel db non ripubblica — ripubblicare e' un'AZIONE
di mostrod — quindi nel libro l'annuncio si legge ancora `pending`. Ma
e' senza denti: chi lo prendesse sbatte sul coordinator, che guarda il
DATABASE e non il relay (stato non piu' `pending` -> rifiuto pulito), e
il job che a scadenza porta i pending a `expired` filtra anche lui su
`status = 'pending'`, quindi salta la riga senza toccarla. Muore da
solo alla `expires_at` (15 set) col tag `expiration` NIP-40, e non e'
piu' una deduzione: VERIFICATO il 9 set stesso, leggendo l'evento
`e0f3ca93…` dai tre relay del coordinator E dallo specchio — quattro
copie concordi, un id solo, e il tag c'e' (1789509744 = 15 set
22:02:24).
LA STRADA SCARTATA E' STATA CAMMINATA A META', APPOSTA, E POI CHIUSA:
Andrea aveva prima chiesto il sostitutivo subito — un 38383 gemello
con `s` a `canceled`, firmato con la chiave del coordinator, che i
relay sostituiscono per protocollo base (NIP-01) senza dipendere dal
NIP-09 opzionale. Il giro era spezzato in tre perche' la nsec non
lasciasse MAI la macchina: lettura dell'evento dal PC (fatta), firma
sul nodo con uno script a zero dipendenze e quattro guardie (scritto
e torturato in locale), pubblicazione dal PC. Poi il ripensamento,
PRIMA che la chiave fosse toccata: non si maneggia la nsec per un
problema cosmetico che muore da solo in sei giorni. Lo script non e'
mai girato sul nodo, e se una copia ci fosse arrivata va tolta
(`rm ~/firma_38383.py`): un attrezzo che legge la nsec non resta
armato accanto a lei.
DUE COSE VERE restano dalla meta' camminata, e valgono oltre il giro:
la serializzazione NIP-01 di casa (json compatto, ensure_ascii
spento) produce BYTE PER BYTE l'id che mostrod ha firmato, provato
sul suo evento vero; e il vettore di prova giusto per Schnorr non e'
quello ricordato a memoria — il primo banco ne aveva uno sbagliato,
ed era il BANCO a mentire — ma una firma di PRODUZIONE: quella di
mostrod, gia' accettata da quattro relay che le firme le verificano.
DA GUARDARE, senza impegno: dopo il 15 set l'annuncio non deve piu'
stare nel libro — ora e' il controllo di un fatto letto, non di una
deduzione.

Il seme senza commit, e ogni chiamata coniava un'identita' (9 set
2026). Il «DA GUARDARE» della voce del loop qui sopra si e' avverato
il giorno stesso, ma il colpevole non era la leva: era la ROTTA. La
restore funzionava sul PC e taceva su app e miniapp, e il controllo
dei codici segreti ha detto la cosa che nessuna ipotesi prevedeva —
TRE superfici dello stesso account, TRE profili «del conto» diversi,
ognuno col foglio che prometteva «torna da solo ogni volta che entri».
IL DIFETTO ERA UNA RIGA MANCANTE: `/api/p2p/seme` faceva
`con = db()` → `_sale_profilo_p2p` → `con.close()`, senza commit. E
`db()` non e' in autocommit: l'INSERT del sale viveva nella
transazione, la SELECT — sulla STESSA connessione — lo vedeva, la
rotta rispondeva un seme in tutto valido, e la close faceva rollback.
`p2p_semi` in produzione era VUOTA con quattordici identita' passate
da `p2p_indice` in una sera: un generatore di identita' casuali con
la faccia di una derivazione stabile. La diagnosi e' stata tutta in
sola lettura, e l'ha chiusa il database: tabella presente, zero
righe — rollback, non assenza.
PERCHE' LE PROVE ERANO VERDI, ed e' la meta' che vale piu' del fix:
`_sale_profilo_p2p` si provava su UNA connessione mai chiusa — che i
propri INSERT non committati li vede sempre — e la rotta si provava
solo sul TESTO. La transazionalita' vive nella CUCITURA fra la
funzione pura e la rotta, e li' non guardava nessuno. E' la lezione
delle sentinelle della voce del loop, un gradino piu' su: una suite
che certifica i pezzi non certifica il giro, e stavolta il giro era
«il sale sopravvive a chi l'ha coniato?».
LA CURA: `con.commit()` prima della close, la prova a DUE connessioni
su un database su FILE (`:memory:` muore con la connessione e non puo'
fare questa domanda) col CONTROESEMPIO che dimostra il rollback — se
mai diventasse rossa, e' cambiato il default di `isolation_level` e il
commit va riguardato, non dato per inutile — e il chiodo testuale che
la rotta committi PRIMA di chiudere. Torturato: senza il commit la
suite si accende, col commit e' verde.
LE IDENTITA' GIA' NATE SONO ORFANE PER SEMPRE: i loro sali non sono
mai stati scritti, il server non le ridera' mai piu'. Vivono solo nel
localStorage dei rispettivi dispositivi, e quella del PC (`d5e641…`)
tiene l'ordine da 5 EUR aperto sul coordinator: si chiude o si ritira
CON QUELLA CHIAVE prima di far ripassare i dispositivi al profilo del
conto — che dopo il fix nasce alla prima richiesta, stavolta per
davvero e per sempre.
DUE COSE RESTANO APERTE, dichiarate qui perche' non si perdano:
1) IL PROFILO «DEL CONTO» NON SI RIVERIFICA MAI — adottato una volta,
nessuno lo confronta piu' col server (`sincronizzaMazzo` guarda solo
locale↔cloud). E' esattamente il buco che ha lasciato tre identita'
dire «torna da solo» per ore: la sentinella naturale e' richiedere il
seme a ogni ingresso quando `origine === 'conto'` e DIRLO se diverge,
invece di tacere. Cantiere suo: la divergenza non si risolve da sola
(due identita' sono due storie), quindi prima serve decidere il
foglio di quel conflitto.
2) LA CORSA DELL'INDICE A ZERO ammutolisce la restore sul dispositivo
fresco: `chiediMieiOrdiniP2P` a indice 0 si auto-risponde «nessuno»
senza chiedere, ma il pavimento che direbbe l'indice vero viaggia con
`registraChiaviP2P`, lanciata senza await tre righe prima — la corsa
la vince sempre il gate. E una volta scritto `{}`, nemmeno «Riprova»
richiede: `ricaricaP2P` riabbassa `p2pMieiChiesto` ma il gate vuole
`p2pMieiOrdini === null`. Si cura da solo alla sessione DOPO (il
pavimento bumpa e persiste), che e' un ritardo di una sessione intera
spacciato per «non ne hai»: o il gate aspetta il pavimento, o
«Riprova» riarma anche la marcatura. Tutte e due costano poco; quel
che non costa niente e' dimenticarsele, ed e' il motivo di questa
voce.

La corsa dell'indice curata, e la striscia che nasce ovunque (set
2026, il giro dopo la prova finale). I due aperti della voce qui sopra
si chiudono insieme, perche' sono le due meta' della stessa promessa —
«i tuoi ordini ovunque» — e la prova sul campo li aveva mostrati tutti
e due: la marcatura arrivava solo alla SECONDA apertura fredda, e
anche allora la striscia «I tuoi scambi» restava vuota sul dispositivo
che non aveva pubblicato.
LA CORSA SI CURA TENENDO LA PROMESSA: renderP2P adesso conserva in
`p2pPavimento` la promessa di `registraChiaviP2P` — quella che porta
indietro il pavimento dell'indice — e `chiediMieiOrdiniP2P`, quando
l'indice locale e' zero, la ASPETTA e rilegge il mazzo prima di
giudicare. Fail-open nel verso giusto: un pavimento che cade non
blocca niente, si conclude come prima. E il giudizio sull'indice e'
SCESO dentro il giro asincrono: prima viveva fuori, dove non poteva
aspettare nessuno.
E «RIPROVA» ADESSO RIARMA: il gate della marcatura esigeva
`p2pMieiOrdini === null`, quindi il `{}` scritto dal giro a indice
zero era definitivo — il gesto riabbassava la bandierina e il gate
restava chiuso lo stesso. Ora la bandierina e' l'UNICO gate: una
risposta fresca sostituisce la vecchia, un giro caduto lascia quel che
si sapeva, e il ritentativo continua a costare un gesto.
LA STRISCIA NASCE ANCHE SUL DISPOSITIVO FRESCO: `righeAltroveP2P`
prende gli ordini riconosciuti dalla restore che NON hanno una riga
locale e che il LIBRO sa ancora descrivere, e `scambiP2P` li accoda
alla striscia con una riga loro — cifra e lato dal 38383, il lato
letto da MAKER (un `sell` nella striscia e' «vendi», perche' li'
l'ordine e' tuo), e il tocco che passa dalla porta del gesto, il
giudice che gia' distingue «mio ma non in lista» e risponde con la
frase onesta invece di aprire uno scambio che su quel dispositivo non
c'e'.
IL LIMITE E' DICHIARATO, non nascosto: di un ordine preso o in corso
la restore da' solo l'id e uno stato nel vocabolario del coordinatore,
che non si traduce a memoria (la lezione di Q4: gli stati si scrivono
quando si VEDONO) — quegli ordini nella striscia non compaiono ancora.
Li aprira' la RIPRESA vera, col `trade_index` che la risposta della
restore gia' porta: e' il mattone delle fasi 5-6-7, che partono da
qui.
LA TORTURA HA MORSO ANCHE LA PROVA, ed e' la riga da tenere: il banco
simulava il pavimento con un'async IIFE che bumpava l'indice PRIMA del
primo await, cioe' in modo sincrono — e cosi' il caso «si aspetta la
promessa» passava anche a cura tolta. Il corpo di un'async IIFE gira
sincrono fino al primo await: un banco che deve provare un'attesa deve
mettere il fatto DOPO un await vero. Stessa famiglia del rovescio
trovato al primo giro: la sentinella «niente piu' `=== null` nel gate»
lo ritrovava nel COMMENTO che raccontava il vecchio gate — si guarda
`solo_codice`, mai la prosa. Tre mutazioni provate, tutte uccise:
senza l'attesa del pavimento (4 rosse), col vecchio gate (2), senza le
righe della restore nella striscia (3).
DA GUARDARE: resta aperto — dalla voce qui sopra — il profilo 'conto'
che non si riverifica mai dopo l'adozione; e alla prossima apertura
fredda su un dispositivo che non ha pubblicato, la marcatura E la
striscia devono arrivare alla PRIMA, non piu' alla seconda.

La restore beveva la storia del relay, e la chiave della domanda
diventa usa-e-getta (set 2026, dal campo: il controllo della voce qui
sopra e' andato ROSSO). Prima apertura fredda dopo la cura della
corsa: ordine fresco dal PC, app riaperta una volta — non marcato,
niente striscia; alla seconda tutto giusto. Il «DA GUARDARE» ha fatto
il suo mestiere, e il colpevole non era piu' la corsa.
IL FATTO ERA DETERMINISTICO, ed e' la briciola che ha guidato: prima
no e seconda si', sempre, e' STATO che cambia — non rete fredda (la
cache HTTP sopravvive alla chiusura, la WSS e' fredda uguale in tutti
e due i giri). Lo stato che cambia fra le due aperture e' l'INDICE,
che il pavimento alza a fine primo giro: quindi la domanda partiva da
DUE CHIAVI DIVERSE nei due giri, e la risposta cambiava con la chiave.
IL MECCANISMO: la domanda partiva dalla trade key dell'ultimo indice
bruciato, e la sottoscrizione (`#p` sulla chiave, SENZA `since`)
riceve per prima la STORIA del relay — dove c'era la risposta di IERI
alla stessa chiave, fatta quando l'ordine fresco non esisteva. Una
restore-session vera, decifrabile, con l'action giusta: il lettore
chiudeva li', su una lista vecchia. Alla seconda apertura l'indice
era salito, la chiave era nuova, nessuna storia — e «funzionava»,
travestendo il difetto da timing. E' l'ignoto DICHIARATO dalla sonda
(«l'aggancio per sola chiave prende il primo che arriva») nella forma
che nessuno aspettava: non un messaggio spontaneo del coordinatore —
la NOSTRA risposta del giro prima.
LA CURA E' QUELLA CHE LA SONDA AVEVA GIA' VALIDATO: la domanda parte
da una chiave USA-E-GETTA appena nata (Q2: il coordinatore accetta
una chiave mai vista, con la busta restore e la prova d'identita' —
risponde per IDENTITA'). Una chiave senza storia non puo' ricevere
repliche vecchie per costruzione: niente `since` da tarare, niente
margini d'orologio, e cade pure la regola «una restore alla volta per
chiave» — ogni domanda ha la sua chiave. E siccome una chiave nuova
e' SEMPRE un primo contatto, il nonce si mina sulla soglia piu' alta
fra `pow` e `pow_first_contact` (oggi tutt'e due a zero, Q7).
LE STRADE SCARTATE, coi perche': il filtro `since` o il confronto su
`created_at` vogliono un margine d'orologio fra noi e il coordinatore
— un margine largo lascia rientrare il replay recente, uno stretto
butta la risposta vera di un nodo con l'ora storta; il `request_id`
non c'e' (su restore-session torna null, fatto della sonda). La
chiave nuova non ha nessuna delle due debolezze.
IL BANCO HA IMPARATO A RIGIOCARE: il relay finto del motore ora
consegna la `storia` a chi si sottoscrive — com'e' il relay vero — e
il caso 9 mette sul relay la risposta di ieri e nel coordinatore
quella di oggi: con la chiave derivata vince ieri (torturato: 2 rosse
esatte), con la usa-e-getta arriva oggi, intera. E la tortura ha
morso anche una sentinella: l'`index()` su una stringa assente
ESPLODEVA portandosi via il resto della sezione — una sentinella che
muore non e' una sentinella, e ora usa `find`.
DA GUARDARE: la verifica sul campo che chiude — ordine fresco da un
dispositivo, PRIMA apertura fredda su un altro: marcatura e striscia
devono esserci. E resta il solo aperto di sempre: il profilo 'conto'
che non si riverifica dopo l'adozione.

La striscia si veste uguale, e l'etichetta dice solo il fatto che sa
(set 2026, la coda del cantiere). LA VERIFICA SUL CAMPO E' PASSATA —
marcatura e striscia alla PRIMA apertura fredda, contorni del libro
perfetti su ogni dispositivo — e proprio lo screenshot della prova ha
mostrato gli ultimi due difetti, tutti e due nella striscia e tutti e
due miei del giro precedente.
IL PRIMO ERA UN VESTITO DISUGUALE: la riga locale della striscia e'
sempre stata nuda (`p2p-ord`), e a quelle della restore avevo messo
`p2p-mio` — fianco a fianco si leggevano come un guasto del giudice,
che era innocente (la diagnosi e' passata da un `querySelectorAll`
che pescava le righe della striscia credendole card del libro: la
card del libro dell'ordine fresco non era MAI nel DOM, il libro si
carica una volta per sessione). Il bordo e' del LIBRO — distingue il
tuo in mezzo a quelli degli sconosciuti — mentre nella striscia e'
tutto tuo per definizione: ora nessuna riga della striscia lo porta.
IL SECONDO ERA UN'ETICHETTA BUGIARDA, ed e' la lezione: «pubblicato
da un altro tuo dispositivo» e' un'affermazione che il client NON
puo' fare — l'assenza della riga locale non prova dove l'ordine e'
nato, dice solo che QUI non ci sono le sue carte. Il campo l'ha colta
a mentire: tre ordini pubblicati dallo stesso PC, la lista locale ne
ricordava uno, e gli altri due portavano l'«altrove». Ora riga e
toast dicono il fatto che regge in tutti i casi: «da qui si guarda
soltanto» — e ad aprirli davvero sara' la ripresa delle fasi 5-6-7.
SI AFFERMA SOLO CIO' CHE SI SA: e' la regola della sonda (un NO su un
fatto vero e' peggio di un «non lo so») portata nei testi a schermo.
DA GUARDARE, ed e' un mistero VERO non ancora spiegato: sul PC le
righe locali di due ordini pubblicati li' sono SPARITE dalla lista
(`barattolo_mostro_ordini`). Nessun codice le toglie («Dimentica il
profilo» non tocca gli ordini, la scopa vuole 30 giorni e stati
finali, la ✕ non compare su un 'pubblicato'). Il sospettato e' la
CARTELLA CONDIVISA in miniatura: due schede dello stesso browser che
si sovrascrivono la lista — ogni scrittura e' una fotografia INTERA
del JSON, e una scheda vecchia che salva dopo cancella quel che
l'altra aveva aggiunto. Se si ripresenta e' un cantiere suo (versione
nella lista, o l'evento `storage` che riallinea); per ora e' a
verbale, e la striscia della restore fa da rete: gli ordini persi
localmente restano visibili e marcati.

La riga si adotta, e l'ordine riconosciuto torna governabile (set
2026, un'ora dopo la voce qui sopra). La conseguenza pratica del
mistero e' arrivata subito, da Andrea: «NON POSSO PIU' ANNULLARE il
4 e il 5 euro» — il PC li vedeva «da un altro dispositivo» e non
offriva il ritiro, ma nessun altro dispositivo li governava. Ogni
ordine fuori dalla lista locale era un ORFANO INGOVERNABILE.
LA CURA HA CAMBIATO IL DISEGNO invece di rattoppare l'etichetta: per
un ordine PENDING la restore e il libro insieme dicono TUTTO quel che
una riga locale contiene — l'id, il `trade_index` da cui la trade key
si rideriva (l'identita' e' condivisa), cifra, lato e metodi dal
38383. Quindi `adottaOrdiniAltroveP2P` RICOSTRUISCE la riga vera, e
l'ordine torna un cittadino normale: pagina apribile, «Ritira» col
giro di sempre (`cancel` firmato con la chiave riderivata, aggancio
per request_id — che su cancel TORNA, fatto della sonda, Q5),
ascolto del campanello sulla sua chiave. Le righe «altrove» nate il
giorno prima muoiono dopo un giorno, e va bene cosi': erano una riga
di seconda classe, e la classe giusta esisteva gia'.
IL PROVVISORIO SI RINOMINA invece di raddoppiare: una riga `nuovo:N`
con lo stesso indice E' quell'ordine — la conferma che non e' mai
arrivata, la restore gliela porta adesso. E' anche la rete
dell'orfano in generale: la riga persa (una scheda che sovrascrive
l'altra, una memoria svuotata) torna governabile OVUNQUE.
I CONFINI, dichiarati: si adotta solo con l'INDICE in mano (senza,
la chiave non si rideriva) e solo quel che il libro descrive come
pending — di un ordine preso o in corso la restore da' uno stato nel
vocabolario del coordinatore che non si traduce a memoria (Q4), e lo
aprira' la ripresa piena delle fasi 5-6-7, che da qui eredita il
mattone. L'adozione e' sincrona e senza rete: se il bundle manca si
salta il giro, ma la restore che riempie la lista l'ha gia' caricato.
PROVATO NEI DUE BANCHI: quello della striscia (stub dichiarati)
guarda i confini — adotta/non adotta, il rinome, il doppione, il
senza-indice — e quello del motore fa il giro INTERO col bundle vero:
adozione con la chiave vera, `cancel` firmato con la chiave
riderivata e la prova d'identita' verificata dal coordinatore di
cartone, ordine che finisce `annullato`. Tortura: adozione tolta,
sei rosse su due banchi.
DA GUARDARE: il ritiro vero dei due ordini orfani di Andrea (4 e 5
euro) — al prossimo giro sul PC devono comparire come righe normali
con «Ritira», ed e' la verifica sul campo di questa voce.

La scopa lampo, e la ✕ che «si sincronizza» derivando dallo stato
(set 2026, dopo il ritiro verificato sul campo). La richiesta era la
✕ sincronizzata: chiusa una card su un dispositivo, sparisca ovunque.
LE TRE STRADE VALUTATE, coi perche' — e due sono scartate:
1) IL CLOUD DI TELEGRAM sincronizzerebbe solo miniapp↔miniapp:
`cloudTelegram()` e' null sul PC (browser) e sull'app di Zapstore,
cioe' proprio la coppia di superfici del caso reale. Non e' una
strada, e' un vicolo.
2) UNA LISTA SUL SERVER romperebbe un pezzo di disegno: il motore
P2P ha la sentinella «zero fetch» apposta, e il server oggi sa SOLO
quali pubkey guardare sui relay — mandargli gli id degli ordini
nascosti gli insegnerebbe QUALI ordini del libro sono di chi. Una
comodita' pagata in privacy, contro la voce «le chiavi pubbliche
dello scambio».
3) IL QUADERNO CIFRATO SUI RELAY — un kind 30078 cifrato a se stessi,
pubblicato da una chiave derivata dal mazzo con un'etichetta sua
(quindi non collegabile ne' all'identita' ne' alle trade key), con un
`d` derivato per non marchiare il client — e' la strada GIUSTA per la
sincronizzazione istantanea, e servira' comunque alla ripresa piena:
ma e' un pilastro nuovo (storage personale sui relay), e si disegna
DENTRO la fase 6, non in coda a questo giro. Registrata qui perche'
il giorno che l'istantaneo servira' davvero, la via e' gia' scritta.
LA STRADA COSTRUITA E' LA DERIVAZIONE DALLO STATO, che era anche
nella richiesta: lo stato E' gia' sincronizzato dal coordinatore —
ogni dispositivo vede l'annullato da solo — e quel che mancava era
che la card, detta la notizia, se ne andasse. LA SCOPA LAMPO: un
`annullato` o `rifiutato` che non ha MAI tenuto sats (niente hold,
niente satsNetti) e' una notizia e non una ricevuta — 24 ore dopo il
cambio di stato si toglie da sola, su ogni dispositivo, senza nessun
canale nuovo. La ✕ resta per il subito. I CONFINI: il «concluso» non
si tocca (porta il voto e finisce nell'export CSV degli affari — e'
una ricevuta), e un annullato che i sats li ha tenuti (cooperative
cancel con hold) resta ricevuta a 30 giorni.
LA PROVA REGINA HA CAMBIATO VESTITO SENZA CAMBIARE MESTIERE: il caso
«chiuso ieri dal coordinatore resta» difendeva la catena dei timbri
(`quando` prima di `aggiornato`) con la soglia a un mese; col lampo a
24 ore lo stesso caso e' passato a «chiuso stamattina» (12 ore) — chi
pulisse `quando` dalla catena spazzerebbe una riga chiusa poche ore
fa, e la riga diventa rossa uguale. Torturato nei due versi: senza la
guardia della hold la ricevuta se ne va (rosso), senza il lampo la
notizia resta (rosso).
DA GUARDARE: se il rodaggio dira' che 24 ore sono troppe o poche, e'
UNA costante (`P2P_SCOPA_LAMPO_S`); e se l'istantaneo tornera' a
mancare, la strada 3 aspetta nella fase 6.

Il ritirato non si vede piu' (set 2026, un'ora dopo: Andrea
semplifica il lampo). La regola nuova, sua: ritirato = SPARITO,
subito e ovunque — niente ✕, niente attesa, niente card «annullato»
che resta in giro. La derivazione dallo stato resta la stessa della
voce qui sopra, cambia la soglia: per l'annullato che non ha mai
tenuto sats, zero.
IL GIUDICE E' UNO (`p2pRitirato`: annullato, niente hold, niente
satsNetti) E LO CHIAMANO I TRE POSTI dove l'annullato arriva o
riposa: `applicaMessaggioP2P` (il kind 14 — toglie la riga, dice
«Ordine ritirato ✓», e chi stava guardando proprio quella pagina
torna al libro), `statoPubblicoOrdini` (la via di riserva
all'apertura — in silenzio: la card di un ordine morto non deve
nemmeno comparire, e qui passa anche lo SCADUTO senza sats), e la
scopa (la rete per le righe rimaste da prima del cambio).
⚠️ IL RIMOTORE PULISCE ANCHE LE DUE CACHE DI SESSIONE, ed e' la meta'
che non si vede: la restore e il libro in cache dicono «pending» per
tutta la sessione, e una riga tolta con quei due ancora caldi
RINASCEREBBE «pubblicato» al render dopo, per mano dell'adozione — la
tortura l'ha mostrato (rimotore senza pulizia: rosso il banco del
motore, l'ordine risorto). Lo stesso rischio, in forma piu' rara,
vale per la ✕ su una riga finita con le cache calde: dichiarato, non
curato — se si vede sul campo, la pulizia si sposta in un posto solo.
IL LAMPO DELLE 24 ORE RESTA AL SOLO `rifiutato` (porta un motivo da
leggere), le RICEVUTE — annullato con hold o satsNetti — ai 30
giorni, il concluso com'era. La prova regina della catena dei timbri
cambia portatore un'altra volta (dal «chiuso stamattina» al «rifiuto
di stamattina») senza cambiare mestiere. Torturato: rimotore senza
pulizia delle cache, rosse sentinella e banco del motore.


FASE 6 DEL CLIENT P2P, PRIMA TAPPA: le parole e il libro che si
aggiorna da solo (9 set 2026). La decisione di prodotto, di Andrea,
a verbale: IL P2P E' BARATTOLO, PUNTO — l'identita' e' l'account con
cui si e' entrati, e la UI non nomina nessun terzo. Questa tappa fa
la meta' delle parole; il profilo invisibile e i campi cifrati al
posto della chat sono le tappe dopo.
DUE EMENDAMENTI A PRINCIPI GIA' A VERBALE, coi perche' — e si
scrivono come emendamenti proprio perche' rovesciano una riga che
qualcuno un giorno vorrebbe «correggere» all'indietro:
1) LA RIGA CHIUSA NON NOMINA PIU' IL CUSTODE. Il principio di ago
2026 («nascondere chi tiene i sats e' la cosa che questo progetto
non fa») resta vero nella sua meta' che conta: il FATTO non si
nasconde — ogni testo dice «custoditi in garanzia» e che Barattolo
non li tiene e non li vede. A sparire e' il NOME («Mostro», «il
coordinatore»): per chi entra da Telegram era un attore in piu' da
capire senza poterci fare niente, e il nome intero con la spiegazione
vive UNA volta, nella pagina «I tuoi dati», dove gia' stava. La
sentinella 4c ora sorveglia il fatto (in garanzia + Barattolo) e che
il nome non rientri; una seconda passa al setaccio TUTTE le stringhe
a schermo del motore (sui letterali estratti, non su cod intero:
la' «Mostro» vive negli identificatori tipo mazzoMostro).
2) LA COMMISSIONE RESTA COL NUMERO E SENZA IL CHI (decisione 3 di
Andrea): «commissione 1% - fino a 100.000 sats», niente
«Coordinatore Mostro X.Y.Z»; senza numeri dal 38385 la riga non
nasce affatto, che una riga vuota non dice niente.
«AGGIORNA IL LIBRO» NON C'E' PIU', e al suo posto non c'e' un gesto:
renderP2P rilegge da solo, in sottofondo, un libro piu' vecchio di
P2P_LIBRO_FRESCO_MS (60 s), TENENDO a schermo quel che si vede — mai
il lampo di «Leggo il libro...» sotto le dita, quindi niente
ricaricaP2P (che azzera il libro) ma caricaLibroP2P diretto. I FRENI
SONO DUE piu' la guardia di sempre: l'eta' del libro, l'eta'
dell'ultimo TENTATIVO (p2pRiletto — o un giro caduto coi relay giu'
riproverebbe a ogni render), e la lettura in volo che gia' evita i
doppi. «Riprova» del ramo rotto resta: li' un libro non c'e' proprio.
LA MARCATURA «E' MIO» NON SI RIARMA dalla rilettura silenziosa, ed
e' voluto: e' una restore-session verso il coordinator — una alla
volta per chiave, il vincolo della sonda — e resta a una per
sessione (il gesto «Riprova» del ramo rotto la riarma come prima).
LA TRAPPOLA DEL GIRO, per la prossima volta: la sentinella nuova
(«niente Mostro nelle stringhe») scritta su cod intero era rossa sul
codice giusto, e quella sul bottone sparito si beccava il proprio
commento — il setaccio giusto guarda i letterali a schermo, e il
segno di un markup si cerca col suo attributo (>...), non a parole.
E pezzo_js ritaglia LUNGO (oltre la funzione chiesta): una prova
NEGATIVA su quel ritaglio morde anche il vicino di sotto — la si
restringe al ramo che si vuole guardare.
RESTANO FUORI APPOSTA da questa tappa: i testi del foglio del
profilo (muore intero nella tappa B) e la chat (tappa C); la pagina
«I tuoi dati» tiene nome e spiegazione del coordinatore, ed e'
l'unico posto. Prove: 8562 verdi, con le emendate una per una.

FASE 6, SECONDA TAPPA: IL PROFILO INVISIBILE (9 set 2026). La
decisione di Andrea, eseguita: l'identita' e' l'account con cui sei
entrato, e non si gestisce. Dalla vista P2P sparisce il bottone del
profilo, dal foglio spariscono l'import, l'offerta «lega al mio
account» col suo ritorno indietro, le due uscite del conflitto fra
mazzi, la strada sovrana della nsec incollata e l'adozione manuale
del conto. Il MOTORE non si e' mosso di una riga: assicuraMazzo
(cloud, poi seme del conto, poi il caso), la sincronizzazione,
l'adozione silenziosa di renderP2P e la registrazione delle chiavi
fanno gia' tutto da sole — il foglio era la faccia, e la faccia
non serviva.
IL FOGLIETTO RIDOTTO vive SOLO in «I tuoi dati» (decisione 2 di
Andrea: mai nella vista P2P): mostra/copia il codice segreto,
«dimentica», la riga di stato del cloud, e per chi non ha un mazzo
l'avviso «ne hai gia' uno altrove» — L'AVVISO RESTA, IL RIMEDIO NO,
che l'import e' uscito ma la sorpresa va detta lo stesso.
SECONDO EMENDAMENTO A VERBALE: la pagina «I tuoi dati» prometteva
«lo vedi, lo copi, lo CAMBI o lo dimentichi» — il «cambi» non e' piu'
vero e la pagina adesso dice quel che c'e' (vedi, copi, dimentichi),
col bottone che rende vera la promessa nel posto dove e' scritta.
La strada sovrana resta NEL PATTO come riga della stessa pagina
(«resta nel patto anche se oggi non ha piu' un gesto dentro l'app»):
chi ha origine 'mia' continua identico, nessuno di nuovo puo'
imboccarla da UI — scelta reversibile, la ricetta sta nella voce
della fase 4 e in git.
LA CINTURA DEGLI SCAMBI APERTI HA CAMBIATO CASA, ed e' l'unica
aggiunta oltre il taglio: viveva in applicaImportMazzo (tutte le
sostituzioni), e con le sostituzioni morte l'unico gesto che puo'
orfanare dei sats e' il «dimentica» — che pero' avvisava solo a
parole. Adesso scordaMazzo si ferma con uno scambio aperto, e un
pagamento che perderebbe il padrone non passa da un avviso.
COSA NON SI E' FATTO, coi perche': nessuna migrazione forzata dei
profili di dispositivo (decisione 1 — sostituire un'identita' in
silenzio e' distruggerla, e in rodaggio quei mazzi sono due);
MAZZO_PRIMA orfano nel localStorage NON si spazza (potrebbe essere
l'unica copia di un'identita'); il conflitto «diverso» del cloud
resta un'informazione senza bivio (per i profili del conto non puo'
piu' nascere, per i legacy si legge e non si decide al posto di chi
guarda); l'autoapertura del foglio a scambio concluso e il nag
«Mettilo al sicuro» sono usciti (il debito di backup del conto non
esiste, quello dei legacy sta scritto in «I tuoi dati»).
LE PROVE: cinque conferme in meno (57 diventa 52, registro emendato),
i sei gesti del mazzo diventano uno, i chiamanti di registraChiaviP2P
da sei a cinque, il banco node del mazzo perde i casi dei gesti morti
e guadagna il foglietto-senza-gesti e la guardia nel dimentica; le
sezioni sovrana/adozione diventano sentinelle NEGATIVE (la porta e'
chiusa e sorvegliata). Verificato dal vivo: pagina «I tuoi dati» col
bottone, foglietto ridotto che risponde, zero errori console nuovi.
Prove: 8535 verdi.

FASE 6, TERZA TAPPA: I DUE RECAPITI CIFRATI AL POSTO DELLA CHAT
(9 set 2026). La decisione di Andrea, eseguita: niente piu' chat
libera — due CAMPI tipizzati, «dove ricevere gli euro» (per chi
vende: senza, chi compra non puo' pagare) e «un tuo contatto»
(facoltativo, per tutt'e due, con l'avvertenza a schermo che rivela
l'identita' alla controparte).
IL CANALE E' QUELLO DELLA CHAT, BUSTA PER BUSTA, ed e' la scelta che
regge la tappa: cambiare anche il trasporto avrebbe buttato la
crittografia gia' provata coi test vector di mostro-core (ECDH
x-only, HKDF senza sale, le due chiavi conv/firma — chi ha solo conv
LEGGE e non scrive, quindi la lettura per chi risolve una disputa
resta possibile). Cambia il CONTENUTO: dentro la busta un kind 1 col
tag `t` che porta il tipo — nell'evento INTERNO, firmato dalla trade
key, mai sulla busta dove lo leggerebbe il relay. Il vocabolario e'
CHIUSO (euro, contatto): un tipo ignoto o un kind 1 senza `t` — la
chat di ieri — si lascia cadere.
PER OGNI TIPO VINCE IL PIU' RECENTE, ed e' il disegno che risolve
due problemi con una regola: l'IBAN sbagliato si corregge
re-inviando (l'ultimo vale), e i PROPRI campi mandati da un altro
dispositivo tornano dall'eco della stessa sottoscrizione — la chiave
di firma e' condivisa fra le parti — e i dispositivi convergono da
soli. Il replay della stessa busta non muove niente (l'id di
dentro), e il vecchio rimesso in giro non torna (la data di dentro).
LA CONSEGNA SI APPOGGIA ALLA STORIA DEL RELAY: la sub riparte dal
piu' vecchio scambio aperto (ultimoVistoP2P), quindi un recapito
mandato ad app chiusa si ritrova alla riapertura. LIMITE DICHIARATO:
se il relay non tiene la storia, il recapito si ri-manda a mano
(«Aggiorna il recapito») — nessun rinvio automatico, che con l'eco
multi-dispositivo rischierebbe di far vincere una copia vecchia.
«OBBLIGATORIO PER CHI VENDE» E' UNA RIGA CHE INSISTE, non un gate:
nella pagina dello scambio, appena la controparte si conosce, chi
vende senza recapito inviato legge «di' a chi compra dove mandarti
gli euro: senza, non puo' pagarti» — ma il bottone della hold non si
blocca, che i 900 secondi di expiration_seconds sono un timer vero e
un campo di testo non deve mangiarselo. Chi compra vede il recapito
arrivato in un riquadro, nella pagina e nel foglio.
LA UI: un foglio solo («I vostri recapiti», p2pCampiSheet al posto di
p2pChatSheet), coi pezzi di casa — via il CSS delle bolle. I testi
della disputa si adeguano (decisione 5): «dai tempo all'altra
persona... se vi siete mandati un contatto, provate a sentirvi» al
posto di «prova a scrivere».
LE PROVE: prove_p2p_chat diventa la suite dei recapiti — le
sentinelle della catena di validazione restano IDENTICHE (autore
prima di tutto, raffica prima di decifrare, doppia firma), il banco
node col bundle vero guadagna aggiornamento-che-vince, il vecchio
che non torna, l'eco nei propri, il vocabolario chiuso; e i rifiuti
RIPARTONO DA RECAPITI VUOTI, che e' la trappola del giro: coi campi
gia' pieni il «vince il piu' recente» rifiuterebbe da solo una busta
vecchia, e le guardie sembrerebbero verdi anche da spente.
RESTA DA PROVARE SUL CAMPO (tappa 8, con Alan): il giro vero a due
identita' — recapito che arriva, aggiornamento, contatto — e la
scadenza dei timer mai vista (il verbale del nodo la aggancia gia'
alla tappa 8). Prove: 8542 verdi.

IL MORTO CHE RISORGE (9 set 2026, dal campo — il rischio gemello
della scopa lampo, maturato in una forma peggiore). Al refresh il
proprio ritirato RICOMPARIVA nel libro, non marcato come mio, cioe'
prendibile da me stesso: la riga locale il rimotore l'aveva tolta
(giusto), la restore i canceled non li elenca (giusto, Q6), e il
libro serviva ancora la copia pending. LA CAUSA NON ERA LA DEDUP MA
LA FAME: la REQ del libro filtrava `#s: pending`, quindi la
sostituzione a `canceled` — che la sonda Q1 aveva gia' visto
esistere nel 38383 — non veniva nemmeno RICHIESTA. Un relay rimasto
indietro (o uno che non rimpiazza gli addressable) serviva la copia
stantia senza rivali, e la dedup per `d`, che c'era gia' e avrebbe
deciso giusto, non riceveva mai il rivale.
LA CURA E' A DUE CINTURE, perche' i due guasti sono due:
1) LA REQ CHIEDE LA FINESTRA INTERA — niente `#s`, e cade anche `#f`
per la stessa prudenza (una sostituzione che perdesse il tag valuta
resterebbe fuori): stato e valuta li giudica il client. La finestra
e' `since` a 16 giorni (`max_expiration_days` 15 + 1): oltre, un
pending non puo' esistere, quindi il libro resta leggero anche con
un anno di annullati alle spalle. E la dedup e' diventata ROBUSTA
ALLE SAGOME ROTTE con la mappa dei MORTI: un 38383 con `s` non
pending uccide la copia pending piu' vecchia del suo stesso `d`
anche quando il parser non saprebbe leggerlo (bastano d, s e la
data). Il verso legittimo resta aperto: un pending PIU' FRESCO del
suo morto e' l'ordine tornato nel libro (il taker che ha lasciato
scadere) e si mostra. Anche il conteggio degli intervalli muore col
suo morto.
2) LE LAPIDI, per il relay che non si aggiorna MAI: quando il
rimotore toglie un ritirato MIO da maker (`o.mio` — le righe
pubblicate e adottate lo portano, quelle prese no), l'id si timbra
in `barattolo_mostro_lapidi` con la scadenza dell'ordine (o creato +
finestra), e `caricaLibroP2P` filtra le lapidate. SOLO i miei da
maker, ed e' il confine che conta: un take andato a vuoto riporta
nel libro l'ordine di un ALTRO, vivo, e lapidarlo sarebbe una bugia
del libro. La lapide scade con l'ordine: potata, non puo' nascondere
niente che il parser non scarterebbe comunque.
IL LETTORE DEL LIBRO E' DIVENTATO PURO (`libroDaEventi`: da eventi a
ordini/intervalli/info, zero rete e zero stato) apposta perche' il
banco lo facesse GIRARE sui casi della resurrezione invece di
guardare le righe — le lapidi restano fuori dal lettore, in
`caricaLibroP2P`, perche' sono stato del dispositivo.
LA TRAPPOLA DEL GIRO, gia' pagata e riscritta qui: una costante
condivisa fra due blocchi (`P2P_LIBRO_FINESTRA_S`, usata dal filtro
nel blocco del libro e dalle lapidi nel blocco del motore) viveva
nel blocco sbagliato, e nel banco del motore il rimotore esplodeva
in ReferenceError INGHIOTTITO dal catch della pipeline — tre prove
rosse che sembravano della cura ed erano del banco. La costante ora
vive accanto alle lapidi, dentro il blocco che i banchi affettano.
TORTURATO, cinque mutazioni e cinque uccise (baseline 0): il filtro
`#s` rimesso, la mappa dei morti spenta, il rimotore senza lapide,
il libro che ignora le lapidi, lapidataP2P sempre falsa. La seconda
ha insegnato la stratificazione: col rivale LEGGIBILE la dedup
semplice basta gia', ed e' la mappa dei morti a morire solo sul
rivale rotto — le due cinture non sono ridondanti, coprono guasti
diversi. Prove: 8557 verdi.
RESTA VERO il gemello dichiarato della scopa lampo (la X su riga
finita a cache calde), che e' un altro caso e resta a verbale la'.

L'IDENTITA' DI PAGAMENTO: IL RECAPITO CONOSCE IL SUO METODO E SI
RICORDA (9 set 2026, miglioria della terza tappa). «Dove ricevere gli
euro» non e' piu' un campo di testo unico: il METODO dell'ordine
sceglie il form — SEPA vuole intestatario e IBAN in due campi,
Revolut un RevTag, Satispay un numero di telefono, PayPal un conto,
i contanti un luogo di ritrovo proposto, e il metodo libero (che per
il coordinatore resta testo libero, vedi P2P_METODI) il suo campo
generico. Con piu' metodi sull'ordine, le pillole scelgono quale
compilare.
LA DOMANDA DEL CANTIERE ERA SE ESTENDERE IL VOCABOLARIO DEL TAG `t`,
e la risposta e' NO, per due ragioni che vanno ricordate insieme:
1) «per ogni tipo vince il piu' recente» e' il meccanismo di
correzione — con un tipo per metodo (`euro:sepa`, `euro:revolut`),
chi corregge passando da SEPA a Revolut lascerebbe DUE recapiti vivi
e chi compra non saprebbe quale vale; il recapito degli euro e' UNO
per scambio, quindi il tipo e' uno. 2) Il vocabolario e' chiuso
apposta: un tipo nuovo, per un client di ieri, e' una busta lasciata
cadere in silenzio. E SUL FILO VIAGGIA TESTO COMPOSTO, mai una
struttura: chi riceve mostra quel che legge con qualunque versione
(niente parser dall'altra parte, niente JSON mostrato grezzo da una
versione vecchia). La tipizzazione vive nel client che scrive: form,
validazione leggera (l'IBAN si ripulisce e si guarda nella sagoma,
due lettere due cifre e una lunghezza da IBAN — mai nel contenuto),
composizione canonica. La strada scartata — JSON nel content con
fallback — non si riproponga senza un motivo nuovo: comprava un
«copia campo» dall'altra parte al prezzo di un formato da mantenere
in due versioni.
IL RICORDO sta in localStorage (`barattolo_p2p_recapiti`), per FORMA
di metodo ('sepa', 'revolut', …, 'altro:<nome>'), coi campi
strutturati e il testo composto: si scrive a ogni invio riuscito —
l'invio E' il salvataggio, vince l'ultimo per data come sul filo — e
precompila il form. Mai sul server, come tutto il P2P.
L'INVIO AUTOMATICO: quando la controparte si conosce (il passaggio di
`peer` da vuoto a pieno in applicaMessaggioP2P), chi vende col
ricordo giusto non riscrive niente: parte da solo. TRE prudenze:
si aspetta qualche secondo e si RICONTROLLA allo sparo (l'eco
multi-dispositivo fa in tempo ad arrivare, e un recapito gia' mandato
da un altro dispositivo non viene scavalcato da una copia stantia);
parte solo con UNA forma pronta fra i metodi dell'ordine (con due
sceglie il venditore nel foglio — la riga che insiste c'e' apposta);
e se non parte NON si riprova da solo, che e' la stessa regola della
consegna dei campi (nessun rinvio automatico, vedi la voce della
terza tappa). Il caso residuo dichiarato: chi corregge a mano il
recapito per UNO scambio su un dispositivo e apre l'altro proprio
nella finestra della presa in carico puo' vedersi scavalcare dalla
copia ricordata — l'attesa con ricontrollo lo copre nei giri visti,
e la cura e' sempre la stessa: re-inviare, l'ultimo vale.
LE PROVE: il banco node guadagna storage finto e stati finali fra gli
stub, e fa girare forme, composizione, ricordo che vince, auto-invio
che parte una volta sola, il no con due ricordi, il no di chi compra
e dello scambio finito; sentinelle su vocabolario fermo a due, ricordo
scritto DOPO l'invio riuscito, localStorage e mai server, aggancio in
applicaMessaggioP2P, e gli a-capo del recapito composto mostrati a chi
compra. Prove: 8578 verdi. RESTA DA GUARDARE dal vivo col giro a due
identita' della tappa 8 (il foglio nuovo, le pillole, l'auto-invio
vero via coordinatore); e un editor del ricordo in «I tuoi dati»,
fuori dallo scambio, e' possibile ma non deciso.


LA TESTATA DEL P2P: IL LOGO E I DUE TAB GRANDI (9 set 2026,
restyling — decisione di Andrea). La vista del libro apriva con tre
righe di servizio: il titolo «🔁 Scambio P2P», la riga che diceva chi
tiene i sats (aperta/richiusa dietro «Scopri di più», con la sua
regia: decidiChiP2P, il timbro p2pchi, le due forme nel markup fisso)
e la riga commissione/tetto sotto le pillole. Ora apre col MARCHIO:
la tessera del barattolo e il lockup centrati, e sotto DUE TAB GRANDI
sul modello dei libri P2P veri — «Compra sats» e «Vendi sats»,
Baloo 2 grosso, colore SOLO sull'attivo: compra parla il verde della
protezione (--trust), vendi il rosso di casa (--danger), il non
attivo resta neutro. I token hanno già la loro sera, quindi il tema
scuro è gratis. Gli id e il giro non si sono mossi: renderP2P accende
`attiva` sugli stessi due bottoni di ieri, è cambiato solo il vestito
(da consegna-pill a .p2p-lati/.p2p-lato) e il verbo delle etichette
(da «Compro/Vendo», il mio lato in prima persona, a «Compra/Vendi»,
il gesto — come nel riferimento).
QUEL CHE È USCITO NON È SPARITO DAL PRODOTTO, ed è la mappa da
tenere: il FATTO della garanzia («custoditi in garanzia, Barattolo
non li tiene e non li vede») resta detto dalla vista dello scambio e,
col nome del coordinatore, da «I tuoi dati» — la prova del motore
«...e il fatto resta detto» lo sorveglia lì. I numeri del 38385
(commissione e tetto) restano nel foglio del nuovo ordine
(renderNuovoOrdineP2P), letti e mai cablati come prima. Con la riga è
morta infoRigaP2P e tutta la regia della riga chi-tiene-i-sats
(vestiChiP2P/toggleChiP2P/decidiChiP2P, la bandierina p2pChiDeciso):
niente codice morto, e una sentinella nuova vieta che ne resti.
⚠️ A VERBALE, LA RIGA CHE NON SI DIMENTICA: la commissione (oggi l'1%
del coordinatore) ora si vede SOLO pubblicando un ordine — chi PRENDE
un ordine dal libro non la incontra mai. PRIMA DEL PUBBLICO deve
ricomparire anche per chi prende (nel foglio della presa in carico, o
sulla card): richiesta esplicita di Andrea il giorno del restyling.
LE PROVE: il blocco 4c (la famiglia della riga chi-tiene-i-sats) è
caduto con la riga, sostituito dalla sentinella sul codice morto; il
blocco 4 sorveglia il logo (.p2p-testata con tessera e lockup), i due
tab coi loro colori e che né la vecchia riga né le pillole risorgano;
la prova della riga-impostazioni ora guarda il foglio del nuovo
ordine («tace su quel che non sa» vale identico lì). Guardata dal
vivo in chiaro, scuro e mobile: i tab compongono, l'attivo cambia col
gesto. Prove: 8569 verdi.


LA NAV CHE SI TRASFORMA NEL P2P (9 set 2026, chiesto da Andrea). Entrando
nello scambio la barra cambia mestiere CON ANIMAZIONE: P2P, Aste e Ordini
scendono fuori dal bordo e dal basso salgono «Libro ordini» (icona libro
aperto, apre il libro di tutti) e «I miei scambi» (le due frecce, apre gli
ordini miei); al posto di Ordini NIENTE — lo slot resta vuoto, deciso da
Andrea, in attesa della voce che verra'. Il + di Vendi cambia pelle: la
scritta scende con le sorelle e il tondo sale di un soffio, si fa CERCHIO
e veste il colore del lato — verde protezione su «Compra sats», rosso di
casa su «Vendi sats» (body.p2p-vendo, scritto da setLatoP2P; token nuovo
--danger-deep per l'ombra piena, nei due temi). Esplora non si muove: e'
la via del ritorno, e uscendo l'animazione si rovescia da sola. Lo sfondo
della barra si INCASSA (--nav-bg-p2p nei due temi + ombra interna, dal
basso sulla topbar desktop): un contesto diverso deve vedersi, non solo
leggersi.
IL TRUCCO E' LA CELLA A DUE STRATI, ed e' quel che tiene ferma la
geometria: le tre voci che si trasformano vivono in una .nav-cella (grid,
i due bottoni nella STESSA cella di griglia, overflow:hidden), quindi le
celle di primo livello restano CINQUE ed equilarghe e il + resta la terza
— l'invariante del centro esatto non si e' mosso, e il censimento della
barra in prove.py conta appiattendo le celle prima. `nav button` resta il
selettore delle voci perche' e' un discendente: CSS e spazzata di go()
prendono anche gli strati senza una riga nuova. Si muovono SOLO
transform e opacity (visibility col delay per non troncare l'uscita,
~.28s cubic-bezier morbida, scala di .06s fra uscita e ingresso), con la
gemella reduced-motion. Da desktop niente levitazione: la pillola del +
cambia colore e la scritta fa il crossfade «Vendi» → «Pubblica» dentro
una pila a griglia larga quanto la parola piu' lunga — mai uno
spostamento.
LA CLASSE LA SCRIVE go() DERIVANDOLA DALLA VISTA (VISTE_NAV_P2P: p2p,
p2pmiei, p2pordine — MAI p2ppresto, che a leva spenta e' l'unica cosa
che si vede), non i vai*: cosi' indietro e cronologia la rimettono
giusta da soli, la lezione di renderInteresse. Il + ha due mestieri e
li decide toccaPiu() chiedendo alla classe sul body — la stessa verita'
che l'utente ha davanti: se il tondo e' verde, pubblica.
IL LIBRO E LA STRISCIA SI SONO SEPARATI: view-p2pmiei e' la vista nuova
(markup fisso, la testata di casa, #p2pMieiCorpo), «I tuoi scambi» esce
dal corpo del libro e il bottone «Pubblica il tuo ordine» in fondo alla
pagina MUORE — il gesto e' solo il + (decisione di Andrea). MA IL
RENDERER RESTA UNO: renderP2P dipinge ENTRAMBI i corpi a ogni giro,
quindi i quattro freni per sessione (p2pRegistrato, p2pAdozione,
p2pMieiChiesto, p2pRiletto) non si sdoppiano e ogni `.then(renderP2P)`
gia' scritto rinfresca la vista giusta qualunque sia. Prima del libro
l'attesa sta in TUTT'E DUE le viste, ed e' sostanza e non pigrizia:
l'adozione ricostruisce solo cio' che il libro sa descrivere, quindi
una striscia disegnata senza libro mentirebbe. p2pordine accende «I
miei scambi» (uno scambio aperto e' MIO) e tutti i ripieghi go('p2p')
del ritiro e della cronologia sono diventati go('p2pmiei'): si torna
ai propri scambi, non al libro degli altri. p2pmiei e' radice sorella
e sta in VISTE_PTR: la tirata riarma anche la marcatura «e' mio»
(p2pMieiChiesto = false), che li' e' la risposta che si sta guardando.
LE STRADE SCARTATE, coi perche': otto bottoni piatti in position:
absolute (fragile da desktop, dove le pillole hanno larghezze sue);
riusare gli stessi bottoni rietichettandoli a runtime (niente
scorrimento, e il markup statico della barra e' un patto vecchio);
rimappare i miei sulla voce Aste senza vista nuova (semantica storta
in cronologia e nel censimento).
LE PROVE: il censimento delle cinque celle EMENDATO (appiattisce le
.nav-cella e chiede l'ordine dentro ognuna), le quattro sentinelle dei
go('p2p') girate sui nuovi approdi, e la prova nuova prove_nav_p2p —
forma della vista, un renderer per due corpi, la classe scritta solo
da go(), CSS che muove solo transform/opacity col reduced-motion, e il
banco node che fa GIRARE voceNav (libro→p2plibro, miei e scambio→
p2pmiei, presto→p2p) e toccaPiu nei due stati. Prove: 8605 verdi.
Guardata dal vivo (leve P2P accese nel config locale, poi tolte):
mobile chiaro e scuro, desktop, il lato che colora il +, il foglio dal
+, il ritorno da Esplora via navIndietro. RESTA DA GUARDARE: la
commissione per chi PRENDE un ordine (a verbale dal restyling della
testata) e il giro a due identita' della tappa 8.
IL GIRO DELLE RIFINITURE (stesso giorno, guardata dal vivo da Andrea):
1) il RITORNO e' simmetrico — lo stato di quiete dei bottoni base porta
il transition-delay dell'ingresso (.1s), che a riposo non fa nulla e al
ritorno e' la scala che mancava: prima escono gli strati, poi salgono i
normali, come all'andata; 2) lo SFONDO e' la BANDA SCURA (scelta di
Andrea fra due varianti guardate a schermo: l'oro incassato #E3D0A6 e'
la strada scartata) — bruna anche di giorno (#2B2214, di sera #0F0A04),
incasso piu' profondo, e sulla banda le voci parlano la lingua della
sera nei DUE temi con valori fissi (qui il tema non c'entra piu'):
etichette #B5AA90, attiva #FFB25C, il lockup della topbar schiarito
(#F1E8D5) o affogherebbe, la pillola attiva desktop e' un velo caldo
rgba(255,178,92,.16) perche' il crema di --sats-soft renderebbe
l'arancio illeggibile; 3) il + tondo sale a -15px (era -8); 4) i tempi
rallentati per godersi la corsa: .4s il transform, .3s l'opacity, .4s
il cambio della banda, scala .1s; 5) LA TESTATA HA IL SUO LOGO — il
PNG dedicato del P2P (barattolo, lucchetto, le due frecce verde/rossa)
scelto da Andrea, 98px scontornato con drop-shadow, al posto di
tessera+lockup di casa: rotta esplicita /assets/p2p-logo.png (regola 3,
mai un mount), sentinella della testata emendata sul logo nuovo.
Prove: 8605 verdi anche qui.
E IL TERZO GIRO DELLA TESTATA (stesso giorno): logo a 56px servito a
2x (il PNG ridimensionato a 112px, da 278 a 21 KB), tutto compatto in
cima (via i margini della testata, padding del contenitore a 2px per
le sole due viste dello scambio), i tab rinominati «Compra BTC» e
«Vendi BTC» (nessuna sentinella guardava le etichette; gli importi
restano in sats). E il QUARTO RITOCCO, visto dal vivo da Andrea: al
ritorno la scritta «Vendi» compariva DI COLPO — lo stato di quiete
teneva il delay di visibility dell'uscita (.4s), quindi la scritta si
mostrava a corsa finita. Ora la quiete porta il delay dell'ingresso
(.1s, come i bottoni base) e lo stato P2P rimette quello dell'uscita;
il selettore ESCLUDE «Pubblica», che porta anche lei la classe eti ma
ha la quiete rovesciata (nascosta), o le si mangiava la dissolvenza
d'uscita desktop.
E LA RIGA SOLA (stesso giorno, ritocco di Andrea): nel libro il logo
sta IN MEZZO ai due tab — Compra BTC, marchio, Vendi BTC — dentro
.p2p-lati coi tab ancorati in basso (flex-end), la .p2p-testata resta
solo ai MIEI che tab non hanno. Logo a 68px, PNG rifatto dal sorgente
480 recuperato dalla storia git (136px, ~30 KB, sempre 2x); la
sentinella della testata chiede ora l'ORDINE tab-logo-tab. Conteggio
e importi restano in sats, deciso da Andrea.
E IL GEMELLO ROVESCIO (stesso giorno, visto da Andrea): il ritorno di
«Vendi» era guarito ma l'ANDATA si era rotta — spariva di colpo. La
regola di quiete (quattro classi) batteva anche lo stato P2P (tre), e
la visibility spegneva a delay zero pure uscendo. Cura: lo stato P2P
ricalca la STESSA catena lunga della quiete piu' body.nav-p2p (cinque
classi), e cosi' anche l'override desktop del transform, o non lo
batterebbe. Verificata la cascata dal vivo coi delay calcolati:
quiete .1/.1/0, P2P 0/0/.4 — fluida nei due versi. La lezione: due
stati della stessa proprieta' su catene di specificita' DIVERSE non
sono due stati, sono uno stato e un'eccezione — le catene si tengono
uguali.
E IL LOGO CHE REAGISCE AL TAB (stesso giorno, ritocco di Andrea, coi
suoi due PNG): il marchio fra i tab e' una PILA di due gemelli —
freccia verde accesa a comprare, rossa a vendere, stesso barattolo
nelle stesse posizioni — col crossfade (.3s, sola opacity, spento in
reduced-motion) guidato da body.p2p-vendo: lo stesso giudice del +
della nav, quindi la reazione vale nel libro E nei miei senza una
riga di JS nuova. Logo a 76px, seduto SULLA linea dei tab (margine
negativo -8px: stava troppo alto), PNG a 2x della resa (152px, ~34 KB
l'uno) ritagliati dai sorgenti di Andrea. Il PNG singolo di ieri e'
morto con la sua rotta; al suo posto due rotte esplicite gemelle. Le
sentinelle: l'ordine tab-logo-tab ora chiede il gemello compra, e il
blocco nuovo di prove_nav_p2p conta le due pile, i quattro strati, il
giudice del crossfade e che del singolo non resti niente.
E TRE RIFINITURE DEL LOGO REATTIVO (stesso giorno, viste da Andrea):
1) il barattolo «si trasformava» — sfumando ENTRAMBI i gemelli, a
meta' corsa l'immagine calava al 75% e il barattolo respirava. Cura
senza asset nuovi: sfuma SOLO il gemello sopra (vendi), il compra
sotto resta pieno — i barattoli sono identici, quindi coprendosi non
cambiano e a muoversi si vedono solo le FRECCE. Sentinella: la regola
che sfumava il compra non deve risorgere. 2) LA SCOSSA: al tocco di un
tab la pila dondola una volta (.35s, keyframes logoScossa, spenta in
reduced-motion), riavviata dal togli-e-rimetti col reflow in mezzo
(scuotiLogoP2P), e parte anche sul tab GIA' attivo — e' la risposta
al dito, non al cambio, percio' sta PRIMA dell'early return di
setLatoP2P. 3) NIENTE STRISCIA CONTINUA: la linea vive sotto ogni tab
(grigia sul quieto, colorata sull'attivo, border del bottone) e sotto
il logo non passa niente — il contenitore ha perso il border-bottom e
i tab il margine negativo che lo scavalcava.
E IL COLORE DEL LATO SI PROPAGA (stesso giorno, ritocco di Andrea):
la voce ATTIVA della nav trasformata (icona e scritta, e da desktop
il velo della pillola) e la CIFRA delle card del libro (sats +
«prezzo di mercato», che vivono in un solo span) vestono il verde a
comprare e il rosso a vendere — sempre body.p2p-vendo, lo stesso
giudice del + e del logo, con la dissolvenza morbida (.4s la nav, .3s
le cifre, spenta in reduced-motion). Sulla banda scura i toni sono i
chiari della sera FISSI (#34B47A / #F07A47: i pieni del giorno sul
bruno affogano); nelle card sono i token, che la sera ce l'hanno
gia'. SOLO le card del libro (.p2p-ord > .p2p-sats): nelle altre case
della classe — scambio e striscia — la cifra resta arancio, perche'
li' il lato e' della RIGA e non del tab, e una riga «vendo» tinta dal
tab «compro» direbbe una bugia.
E LA CARD DICE CHI FA COSA (stesso giorno, richiesta di Andrea): riga
grande col VERBO e i sats — «Vende ≈ 12 000 sats» verde, «Compra …»
rosso — e sotto «in cambio di 8,00 € · prezzo di mercato» in prosa;
il premio, quando c'e', resta dov'era (la coda dopo il ·), e a cambio
muto la coda dice «al mercato» senza inventare numeri. IL VERBO E' UN
FATTO DELLA RIGA (o.lato), mai del tab: dice quel che fa chi ha
pubblicato, e resterebbe giusto anche fuori dall'elenco filtrato. Le
classi base (.p2p-euro/.p2p-sats) restano — le usano il colore del
lato, l'ordine con la reputazione e le ALTRE due case di .p2p-testa
(scambio e ordine preso), che non si muovono — e il vestito nuovo sta
nelle sorelle .p2p-cifra/.p2p-cambio, solo del libro. Il selettore
del colore diventa discendente (la cifra ora sta DENTRO la testa). Il
banco delle card gira sui casi veri e le sentinelle della vecchia
«stima che scende» sono diventate quelle del «chi fa cosa».


IL RIDISEGNO DELLE CARD DEL LIBRO (9 set 2026, chiesto da Andrea:
«capite in un secondo, piu' semplici di Mostro»). Quattro righe:
1) il verbo e i sats, grandi e col colore del lato, con la SCADENZA a
destra (scelta nostra fra scadenza ed eta': quanto RESTA fa decidere,
quanto e' vecchio no); 2) la frase UNICA dell'euro — «in cambio di
8,00 € al prezzo di mercato» a premio zero, «, +4% sopra il mercato»
in tinta d'avviso o «, −2% sotto il mercato» in tinta buona col
premio (token --danger/--trust, la sera ce l'hanno), niente coda a
importo fisso; 3) il metodo come prima; 4) la reputazione in UNA
frase umana — «⭐ 4,8 · 37 scambi · da 232 giorni», «🆕 Senza voti ·
da oggi» — via la fila di stelle e i due pezzi ai bordi («scambi» e
non «voti»: su Mostro ogni voto e' uno scambio concluso). L'etichetta
VENDENDO/COMPRANDO separata non e' mai esistita da noi: il verbo
della riga 1 fa quel mestiere. «E' il tuo ordine» resta.
E LA PARTE GROSSA E' SOTTO IL VESTITO: gli ordini A INTERVALLO
ENTRANO NEL LIBRO. Il parser accetta due importi crescenti
(euro/euroMax; invertito o triplo restano ordini rotti), la card dice
i due capi e chiude con «, scegli tu», la stima in sats stima
ENTRAMBI i capi collo stesso metro, e la dedup e' quella di tutti gli
ordini — la macchina degli «esclusi» (il giudice, la mappa, la riga
fissa «N offerte a intervallo») e' morta con la sua ragione, nome
compreso: una sentinella vieta che risorga, il precedente dello
spaziatore. PRENDERLI ANCORA NO: il take vuole la scelta dell'importo
e quel foglio non c'e' — lo dice il TOCCO sulla card, una volta
(«si sceglie l'importo, e da qui non si puo' ancora»), mai una riga
fissa sopra il libro. E' il prossimo mattone naturale del cantiere.
LE PROVE: i casi del range girano nel banco del parser (i due capi,
i rotti, la dedup fra copie, le card coi tre premi), la reputazione
umana ha i suoi (singolare compreso, e il clamp DENTRO la frase), la
sezione degli «esclusi» e' diventata la sentinella che niente ne
resti, e la prova del cambio muto e' stata riscritta sul fatto:
nessun ≈ e nessun numero inventato, la frase dell'euro intera.
Guardato dal vivo col renderer vero su card sintetiche (range, +4%,
−2%, reputazioni) sopra il libro vero dei relay.
E IL VERSO DEL PREMIO (stesso giorno, chiesto da Andrea: «dal punto
di vista di chi legge»). VERIFICATO SUI BYTE, non dedotto: in mostro
v0.18.6 `get_market_quote` (src/util.rs) fa `sats -= premium/100 *
sats`, sottrazione UNIFORME sui due versi — quindi su un SELL il
premio positivo lo paga chi legge (compra sats: avviso), su un BUY lo
paga la controparte (chi legge vende e incassa di piu': affare). Il
TESTO resta un fatto del prezzo («sopra/sotto il mercato»), la TINTA
porta il giudizio per chi legge: classi p2p-affare/p2p-avviso decise
da `(lato==='buy') === (premium>0)`. E GIA' CHE I BYTE ERANO APERTI,
la stima si e' allineata alla formula vera: satsMercatoP2P faceva
/(1+p/100) e a +2% stimava 98039 dove il coordinatore consegna 98000
— ora e' la sottrazione sua, e il ≈ dice il numero che il taker
riceve davvero. Verificato dal vivo nel tab Vendi: +5% verde, −3%
rosso, stime che scendono col premio come dal coordinatore.


IL TIMBRO DEGLI ASSET (9 set 2026, dal campo: i loghi del P2P
sostituiti tre volte in un giorno NON arrivavano ai client — l'app
Android mostrava la prima versione, la miniapp la penultima, anche a
cache «svuotata»). Due mani sulla stessa ferita: le rotte servono gli
asset con cache 24h, e fuori da Telegram c'e' la dispensa del service
worker. La cura e' STRUTTURALE, come chiesto da Andrea: ogni URL
/assets/... e /vendor/... LETTERALE nella pagina esce timbrato
?v=<sha1 corto del file> — il timbro E' il contenuto, quindi ogni
sostituzione invalida da sola ogni cache di ogni client, senza numeri
da alzare a mano. Il timbro vive in _timbra_asset_pagina e si applica
nella RILETTURA di _pagina_con_meta, prima delle fessure: si paga una
volta per riavvio (che il deploy fa sempre) e ogni rotta-pagina lo
eredita per costruzione, il pregio della quarta fessura. NON si
timbrano: chi ha gia' una query sua (il ?b=2 delle famiglie, il ?v
manuale del bundle Nostr — il gruppo-query della regex li salta), i
path costruiti in JS (il ${} non matcha, ed e' giusto: le famiglie
dinamiche hanno il loro giro), e offline.html — la sua mascotte deve
combaciare colla chiave in dispensa, o l'offline si romperebbe
proprio senza rete.
E IL BUCO VERO ERA NEL SERVICE WORKER: la dispensa matchava per
PATHNAME (`caches.match(url.pathname)`), quindi anche col timbro
nuovo un asset in dispensa serviva la copia vecchia — il ?v ignorato
per costruzione. Ora il match e' sull'URL INTERO (v8): una versione
nuova e' una chiave nuova, manca, si scarica e si mette via
(`c.put`). Il gate resta sul pathname (il precache non porta query),
e la REGOLA OPERATIVA di sw.js e' emendata: gli asset timbrati si
aggiornano da soli, VERSIONE resta per offline.html e l'elenco.
LE PROVE (prove_timbro_asset): il banco esegue le funzioni vere —
hash che e' davvero lo sha1 del file, 404 mai timbrato, query
esistente rispettata, ${} intoccato, idempotenza, /vendor/ come
/assets/ — poi la pagina VERA timbrata (i due loghi P2P + almeno una
decina di asset), la pipeline (il timbro prima delle fessure,
offline.html fuori), e il service worker (URL intero, put, v8+, i
patti di API e navigazioni fermi). Verificato dal vivo: la pagina
servita porta 13 asset timbrati, l'URL col timbro risponde 200, il
SW v8 installa la dispensa nuova accanto alla vecchia che cade alla
visita dopo (niente skipWaiting, com'era).
E IL TERZO DELLA FAMIGLIA (9 set 2026, PNG di Andrea): il logo
COMPLETO — entrambe le frecce accese — veste i posti dove un lato
attivo NON c'e'. Nella testata dei propri scambi al posto della pila
reattiva, ed e' il motivo: li' gli ordini sono i miei, di tutt'e due i
versi, e un crossfade risponderebbe a un tab che quella vista non ha
(la coppia gemella resta al libro, dove il tab c'e'). E al posto del
🔁 dove l'emoji faceva da SIMBOLO dello scambio: la riga «Lo scambio»
e i due stati vuoti. NON si e' toccato dove quell'emoji ha un altro
mestiere — «Doppioni su Nostr» nell'admin dice ripetizione, non P2P —
ne' i prefissi dei console.log ne' i tre toast, che sono testo e non
possono portare un'immagine.
⚠️ E DUE POSTI SONO RIMASTI SENZA SEGNO, misurando a schermo invece di
dedurre: sul BOTTONE arancio che pubblica il marchio a 1,3em diventava
una macchia (i suoi colori e quelli del fondo sono la stessa
famiglia), e in riga con una section-label da 11px l'em dava 14px —
a quella taglia un'emoji regge, un'illustrazione no: e' un puntino
colorato. Cura: la misura in riga e' 20px FISSI (li' il marchio si
riconosce, guardato), e sotto quella soglia meglio nessun segno —
l'emoji non torna, che ha smesso di essere il nostro segno.
E L'ICONA DELLA NAV RESTA IL DISEGNO (decisione di Andrea, chiesta
guardando il conflitto): «I miei scambi» in nav non era un'emoji ma
un SVG monocromatico a due frecce che eredita currentColor — cioe' e'
quello che si accende verde o rosso col lato, come chiesto due giri
prima. Un PNG a colori li' spegnerebbe la propagazione e metterebbe
una figurina fra icone di linea.
IL FILE: ridimensionato a 152px come i gemelli (~33 KB), barattolo
verificato identico agli altri due alla resa (zero pixel oltre la
soglia percettiva contro il vendi, due marginali contro il compra, e
non conta: il completo non fa crossfade con nessuno). Rotta esplicita
sua, e il TIMBRO se l'e' preso da solo — la prova che il cache-buster
del giro prima vale anche per gli asset che nasceranno. Prove: 8662
verdi.
LA TRAPPOLA DEL GIRO, che vale oltre il cantiere: la sentinella delle
parole del foglio del nuovo ordine (niente «nostr», «nsec», «npub»,
«relay» a chi entra da Telegram) e' CIECA AI COMMENTI apposta — cosi'
prende anche chi la parola la infilasse in una stringa — e cerca
minuscolo dentro tutto il corpo. Un commento con «il segno nostro»
l'ha fatta rossa, perche' quel possessivo contiene per intero il nome
della rete; e la riscrittura che SPIEGAVA la trappola nominandola l'ha
fatta rossa una seconda volta. Da qui la formula «il segno di casa» e
la nota nel commento che non nomina niente. Chi scrive li' dentro se
lo ricordi: la parola non si puo' nemmeno spiegare sul posto.
E LA TESTATA DEI MIEI E' USCITA DEL TUTTO (stesso giorno, correzione
di Andrea): niente logo in cima a «I miei scambi» — la vista si apre
sugli scambi e basta —, e col blocco se n'e' andata la regola CSS
.p2p-testata, che non aveva piu' nessuno: era l'ultima superstite del
restyling della testata, e un CSS orfano fa credere a chi legge che
qualcosa lo usi (il precedente di .sped-badge). Il marchio resta dove
DICE qualcosa — la riga «Lo scambio» e i due stati vuoti — e li' e'
GRANDE: 76px, una misura sola per tutt'e due i posti, che a 20 era un
puntino colorato e a 14 peggio. La regola sotto e' quella misurata
tre volte in un giorno: un'emoji regge a taglie piccole perche' e'
disegnata per quello, un'illustrazione no — o le si da' lo spazio di
essere un marchio, o non si mette. Nella section-label il
vertical-align non serve piu': quella riga e' un flex e la centra
`align-items:center`.


LA CARD PARLA A CHI LEGGE (9 set 2026, ridisegno chiesto da Andrea).
Tre righe in SECONDA PERSONA, e le prime due si scambiano il posto col
lato: nel tab «Compra BTC» (ordini k=sell) «Paghi 8,00 €» grande e
«ricevi ≈ 11 828 sats» sotto; nel tab «Vendi BTC» (k=buy) «Invia ≈
11 828 sats» grande e «ricevi 8,00 €» sotto. La terza riga e' il
prezzo rispetto al mercato — «al prezzo di mercato», «+4% sopra», «−4%
sotto» — e a importo fisso non c'e', che quel prezzo il mercato non lo
guarda. Il verbo VENDE/COMPRA della controparte e' morto: la seconda
persona lo rende inutile. Il range chiude la riga dell'euro con
«, scegli tu», che e' li' che la scelta si fa. Metodo e reputazione
restano, «È il tuo ordine» pure.
LE CLASSI DICONO LA TAGLIA (.p2p-grande/.p2p-piccola) e non il
contenuto, ed e' la conseguenza del disegno: quale cifra occupi quale
riga lo decide il LATO, quindi le classi dei numeri (.p2p-euro coi
suoi caratteri, .p2p-sats col mono) viaggiano con lei. La cifra in
SATS porta il colore del lato in qualunque riga finisca: e' quella che
cambia col tab, e la sua tinta lo dice.
IL VERSO DEL PREMIO, RIVERIFICATO SUI BYTE (mostro v0.18.6,
get_market_quote in src/util.rs, seconda lettura in due giorni):
`sats -= premium/100 * sats`, sottrazione UNIFORME — il kind non tocca
ne' formula ne' segno. Quindi un premio positivo ASSOTTIGLIA sempre i
sats, e chi ci guadagna dipende da che parte dei sats si sta: su un
SELL chi legge ne riceve meno per i suoi euro (paga di piu': AVVISO),
su un BUY ne invia meno per gli stessi euro (incassa di piu':
AFFARE). ⚠️ La premessa «il premium e' il guadagno di chi pubblica»
regge solo meta': sui BUY il premio positivo e' un guadagno di chi
PRENDE. Il testo resta un fatto del prezzo, la tinta un giudizio per
chi legge, e il segno del giudizio si rovescia col lato.
L'ANELLO AL POSTO DELLA SCADENZA: il testo «⏳ scade fra 7 g» esce
dalla card e diventa un cerchio di progresso in alto a destra, pieno
appena pubblicato e vuoto alla scadenza, ultimi 10% in rosso — in un
elenco che si scorre col pollice la fretta e' una FORMA prima che una
parola. La soglia del rosso sta nel JS e non nel CSS, che e' un
giudizio e non un vestito. Il giudice e' PURO (frazioneVitaP2P prende
l'orologio) e torna -1 sui due casi che non si sanno — niente
scadenza, o una finestra rovescia (un `expires_at` piu' vecchio della
nascita, roba che arriva da relay di sconosciuti): li' non si disegna
niente, mai un anello su una finestra storta. IL TESTO NON SI PERDE:
vive nell'aria dell'anello (title + aria-label), quindi il dito e lo
screen reader ce l'hanno ancora — la sua casa nel dettaglio dello
scambio la decide Andrea.
⚠️ E L'ANELLO E' ANCORATO IN ASSOLUTO, non in fila: dentro il flex
della testa una cifra lunga («≈ 74 029–148 058 sats») prendeva tutta
la riga e lo faceva scendere a meta' card — visto dal vivo, curato
con position:absolute e il padding della riga grande. Cosi' la cifra
va a capo nella SUA scatola e l'anello non entra nel giro del wrap;
e la .p2p-testa condivisa torna al suo align-items:baseline, che le
altre due case (scambio e ordine preso) non si muovono di un pixel.
CANTIERE FUTURO, a verbale: il PREMIUM impostabile dal foglio
«Pubblica il tuo ordine» — oggi si pubblica sempre al prezzo di
mercato, e il campo non c'e'.
LE PROVE: la seconda persona e lo scambio di posto sui due lati, le
tinte rovesciate, il range che sceglie, e l'anello col suo giudice
puro (pieno, mezzo, vuoto, oltre la scadenza, i due «non si sa», il
mezzo giro del dasharray, l'aria che porta il testo, gli sgoccioli).
Guardato dal vivo sui due tab con card sintetiche dal renderer vero.
E CINQUE RITOCCHI ALLE CARD E AL LIBRO (stesso giorno, Andrea):
1) LA TERZA RIGA E' NUDA: «prezzo di mercato» senza «al», e col premio
«prezzo di mercato +4%» — in tinta ci va SOLO il segno con la
percentuale, che le parole sono un fatto e il giudizio sta nel numero.
Via «sopra/sotto il mercato»: il segno e il colore lo dicono gia', e
due modi di dire la stessa cosa sono uno di troppo.
2) I SATS SONO SEMPRE AL NETTO DEL PREMIO, regola resa esplicita: la
cifra mostrata e' quella che passera' di mano, e la terza riga SPIEGA
perche' e' diversa dal cambio puro — mai un conto da fare a mente.
Era gia' cosi' (satsMercatoP2P applica il premio), e ora c'e' la
sentinella che lo protegge: due ordini identici tranne il premio, e il
4% deve vedersi nella cifra della card.
3) L'ANELLO SBIADISCE E POI SI ALLARMA: pieno e' l'ARANCIO di casa e
scendendo scivola verso il grigio (color-mix in uno stile inline,
perche' la percentuale cambia a ogni card; dove color-mix non c'e' lo
stile cade e resta il grigio della regola CSS — un ripiego che si
legge). NELL'ULTIMO GIORNO passa al rosso e PULSA (1,5 s, ferma con
reduced-motion): li' non e' piu' un'informazione ma un avviso. LA
SOGLIA E' IL TEMPO CHE RESTA E NON UNA FRAZIONE — su un ordine di
sette giorni l'ultimo giorno e' il 14%, su uno di quindici il 7% — e
vive nel JS, che e' un giudizio e non un vestito. Nell'ultimo giorno
lo stile inline NON si scrive, o vincerebbe sul rosso.
4) L'EURO E' SEMPRE LA RIGA GRANDE, anche nel tab Vendi («Ricevi 7,00
€» in cima, «invia ≈ X sats» sotto): fra i due tab cambiano i VERBI,
non le taglie, e si leggono collo stesso movimento dell'occhio. E'
il rovescio del giro prima, deciso guardandolo: la coerenza fra i tab
vale piu' del mettere in cima «quel che dai». La regola per l'euro in
seconda riga e' morta con lui, niente CSS orfano.
5) IL LIBRO SI ORDINA PER CONVENIENZA DI CHI LEGGE e non piu' per
data: il metro e' il PREMIO e il verso si rovescia col tab — a
comprare sats conviene il piu' BASSO (piu' sats per i propri euro), a
venderli il piu' ALTO (meno sats da consegnare per gli stessi euro) —
e a parita' vince il piu' recente, che fra due offerte uguali quella
fresca ha piu' probabilita' di trovare ancora chi l'ha scritta. Il
giudice e' puro e lavora su una COPIA: la lista in memoria serve a
tutt'e due i tab e non si riordina sul posto.
Verificato dal vivo sui due tab: ordine s−3 > s0 > s+4 a comprare e
b+5 > b0 > b−2 a vendere, tinte rovesciate, e le cifre nette che
mostrano il premio (a +5% si inviano 9857 sats invece di 10 376).


I VOLTI SUL LIBRO (9 set 2026, decisione di prodotto di Andrea, e
ROVESCIA UNA STRADA SCARTATA — si scrive per intero perche' la
prossima volta si sappia cosa si e' scelto).
LA PREMESSA ANDAVA CORRETTA: la richiesta diceva «la strada 3 gia' a
verbale», ma la strada 3 e' il QUADERNO CIFRATO sui relay, disegnato
apposta per NON essere collegabile all'identita'. Quel che serve ai
volti e' la STRADA 2 — la lista sul server — scartata nel cantiere
della scopa lampo con questa motivazione: «mandargli gli id degli
ordini nascosti gli insegnerebbe QUALI ordini del libro sono di chi.
Una comodita' pagata in privacy». Detto ad Andrea prima di
costruire; la decisione, presa con gli occhi aperti, e' di
rovesciarla.
IL PATTO, con le sue parole: la card mostra CIO' CHE L'UTENTE GIA'
MOSTRA NEL MERCATINO — foto Telegram per chi entra da Telegram,
foto o iniziale Nostr per chi entra da Nostr — e chi vuole
l'anonimato lo ottiene come nel resto di Barattolo, entrando da
Nostr. Il P2P EREDITA la visibilita' del mercatino, non ne aggiunge:
chi toglie la foto dalle impostazioni la toglie anche dalle card,
resta l'iniziale, e nessuna impostazione nuova nasce.
LA FORMA, scelta da Andrea fra tre: endpoint CON SESSIONE. Gli utenti
Barattolo vedono volto, nome e stelline sul libro; la vetrina anonima
vede le card senza volto. Il libro sui relay resta leggibile da
chiunque, ma la corrispondenza col nostro account no — un
raccoglitore anonimo che incrocia il libro pubblico non incrocia
niente. Le altre due strade guardate: pubblico per tutti (piu'
fiducia, ma il collegamento ordine→persona diventava un dato aperto)
e volto solo dopo la presa in carico (nessuna esposizione, ma sul
libro spariva il segnale di fiducia).
COSA COSTA, scritto perche' non si dimentichi: il server IMPARA quali
ordini del libro pubblico sono di chi, e chi ha una sessione puo'
chiedere il volto dietro un ordine (gli account sono gratis, quindi
la barriera e' una frizione, non un muro). Il dato che si espone e'
finanziario — chi compra o vende bitcoin, per quanto, con che metodo
— e questa e' la differenza rispetto al vendere una bicicletta. Sta
qui perche' il giorno del parere legale MiCA sia una riga da leggere
e non una cosa da riscoprire.
COME E' FATTO. Server: tabella `p2p_ordini(ordine, tg_id, creato)`,
`POST /api/p2p/ordini` (il client dice «questi sono miei», gate per
persona come le chiavi) e `POST /api/p2p/facce` (chiede la SESSIONE,
POST e non GET perche' gli id in una query finirebbero nei log del
web server, e un log e' un posto dove le cose restano). Esce solo
roba gia' pubblica nel mercatino — nome, avatar, media, conteggio —
mai il tg_id ne' la npub. UN ORDINE GIA' DI UN ALTRO NON SI RUBA
(INSERT OR IGNORE): l'id si legge dal libro pubblico, quindi chiunque
potrebbe provare a intestarsi l'ordine altrui per metterci la propria
faccia; chi arriva primo e' chi l'ha pubblicato, che l'id vero lo sa
prima di tutti. «Dimentica il profilo» porta via ANCHE i volti, o
resterebbe in piedi il collegamento che quel gesto esiste per
rompere; e la fusione degli account se li porta dietro (il censimento
delle tabelle figlie l'ha trovato da solo — la prova ha fatto il suo
mestiere).
CLIENT: gli id si registrano nel `.then` della restore, dove sono
quelli VERI del coordinatore e arrivano tutti insieme; i volti si
chiedono per gli ordini che si stanno per disegnare, in sottofondo,
mai due volte per lo stesso id. ⚠️ E IL BLOCCO STA FUORI DAI TRE del
P2P: libro, mazzo e motore hanno sentinelle «zero fetch» e «una busta
sola» che sono la forma scritta della privacy di ieri — infilarci
dentro due chiamate nuove le avrebbe fatte mentire. I volti hanno il
loro blocco, coi loro marcatori e la loro sentinella: due fetch, e
nel corpo SOLO la lista degli ordini.
LA CARD: il volto sta DENTRO l'anello, che cresce a 44px e diventa la
sua cornice — un segno solo per due cose, nell'angolo che era gia'
suo — e sotto il metodo compaiono le stelline del mercatino, «⭐ 4,8 ·
💬 12», l'icona al posto della parola. Senza voti la riga non c'e'
proprio; senza volto (vetrina anonima, o un ordine di chi Barattolo
non ce l'ha) restano l'anello e la card di ieri, che il volto e' un
di piu' e non un pezzo di struttura.
⚠️ E LA REPUTAZIONE DEL COORDINATORE E' USCITA DALLA CARD: due
reputazioni nello stesso posto, con la stessa faccia di stella,
direbbero cose diverse sembrando la stessa. `repTestoP2P` e' stata
TOLTA invece di restare senza chiamanti (niente codice morto); il
dato resta letto dal 38383 in `o.rep`, che e' un fatto del libro, e
il giorno che il dettaglio dello scambio vorra' dire «su quel
coordinatore ha 7 scambi» si riscrive in tre righe.
VERIFICATO DAL VIVO col giro intero: un ordine VERO del libro
(89500454-…) registrato all'account di collaudo, il volto tornato
dalla rotta con le stelline vere del mercatino (⭐ 3,0 · 💬 2 dalla
tabella feedback), e la card che se lo mette dentro l'anello.
⚠️ UN DIFETTO MISURATO E CURATO: il disco della faccia a `inset:6px`
copriva la meta' interna del tratto — a 44px l'anello va dal raggio
13,75 al 19,25, e un disco piu' largo se lo mangia — quindi i due
scuri si impastavano. A 9px il disco sta nel buco e fra i due resta
la carta.
E LE DUE TRAPPOLE DELLE SENTINELLE, che sono le stesse di sempre: una
prova su «color-mix» in tutto il file era rossa per la BARRA DEGLI XP,
che quel colore lo usa da mesi; e una su «npub» dentro il giudice era
rossa per la DOCSTRING che dice cosa NON esce — `codice()` toglie i
commenti, non le stringhe. Le due domande si fanno DOVE contano: nel
disegno dell'anello, e nel corpo della funzione senza la sua docstring.


IL PROFILO CHE RINASCE, LA RIGA DELL'ALTRA PIAZZA E IL VOLTO-PORTA
(set 2026). Tre punti di Andrea in un giro solo, e il primo dei tre
era un DIFETTO DAL CAMPO: sull'app Android (Zapstore) i propri ordini
non erano piu' marcati come «miei» — prendibili — mentre miniapp e
sito li riconoscevano, con la stessa identita' su tutte e tre.
LA DIAGNOSI, coi tre sospetti di Andrea sfilati uno a uno. Il service
worker v8 era innocente: le navigazioni sono rete-prima e le pagine
non entrano mai in dispensa. Il blocco dei volti era innocente: il
callback della restore fa le stesse cose di prima piu' la
registrazione, che e' async e ingoiata dal catch. La restore invece
NON PARTIVA DAVVERO, ma piu' a monte di quanto si pensasse: sull'app
non c'era piu' IL MAZZO. La catena: ieri sera i codici segreti erano
uguali su PC, app e miniapp (la prova finale del seme); oggi
pomeriggio, durante la caccia ai loghi stantii, la cache dell'app e'
stata svuotata — e col localStorage se n'e' andato il mazzo; e la
tappa B del profilo invisibile (stesso giorno, mattina) aveva tolto
il bottone «Usa il profilo del mio account» con la premessa che «il
motore facesse gia' tutto da solo». LA PREMESSA ERA FALSA FUORI DA
TELEGRAM: l'adozione silenziosa dal seme viveva SOLO in
`assicuraMazzo`, cioe' nel primo GESTO, e il cloud e' una gamba che
sull'app e sul sito non esiste (`cloudTelegram()` nullo). Un
dispositivo svuotato restava senza profilo per sempre, guardando i
propri ordini da estraneo. La fase 4d aveva gia' trovato questo
identico buco e l'aveva chiuso col bottone: il bottone e' uscito, il
buco e' tornato.
LA CURA E' LA GAMBA CHE MANCAVA: `adottaProfiloContoP2P`, chiamata
dal render del P2P quando ne' il locale ne' il cloud danno un mazzo.
Deriva dal seme del conto — che non e' un'identita' nuova: e' il nome
di scambio dell'account, deterministico e uguale ovunque — e NON
riusa `assicuraMazzo`, che a mani vuote genera a caso (l'invariante:
guardare il libro non fa nascere identita'). Il 409 resta silenzio;
una nuvola illeggibile ferma anche qui (la regola delle lapidi); il
profilo rinato si registra subito e si fa dare il pavimento
dell'indice, che e' cio' che rende la restore possibile appena nati.
DUE GUARDIE DI CONTORNO trovate per strada: il gate dell'adozione
fuori da Telegram ASPETTA l'identita' (`myTgId`) — senza, il seme
risponderebbe 409 e la bandierina bruciata chiuderebbe la porta per
la sessione — e il giro dei miei a indice zero parte solo col
pavimento IN VOLO, o un giro concluderebbe «non ne hai» su un fatto
mai chiesto e la bandierina lo renderebbe definitivo.
IL SECONDO PUNTO e' la promessa mantenuta del giro scorso: la
reputazione del circuito e' RINATA come `repRigaP2P`, nel DETTAGLIO
della presa — il foglio che si legge prima di dire si', che e' il
momento in cui serve — e non sulla card, dove le stelline sono del
mercatino. Il ⚡ e la parola «P2P» la tengono distinta. La forma
chiesta da Andrea («100% positivi») NON e' ricavabile dal tag rating
del 38383, che porta total_reviews, total_rating e days: si dice quel
che si sa — «⚡ 7 scambi P2P · ⭐ 4,6 · da 23 giorni», e senza voti
«⚡ Nuovo sul P2P · da oggi» — mai un numero ricavato per sembrare
piu' netto.
IL TERZO PUNTO e' il volto che diventa una PORTA: il tocco sulla
faccia apre il NEGOZIO del mercatino di chi ha pubblicato (lo stesso
`apriNegozio` del dettaglio annuncio, col codice pubblico prima e lo
username poi), mentre il resto della card resta l'ordine. Lo
stopPropagation vive in `apriNegozioP2P`; senza un negozio da aprire
il volto resta un volto, senza onclick ne' cursore. La rotta delle
facce esce col campo `negozio` in piu' — roba gia' pubblica, e' lo
stesso indirizzo che ogni annuncio porta — e nel passaggio si e'
chiuso un buco del giro di ieri: l'avatar ora rispetta
`avatar_scelta='nessuna'` con lo stesso CASE della pagina negozio,
che al primo giro dei volti non era stato ricopiato.
VERIFICATO DAL VIVO sul dispositivo «svuotato» simulato
(localStorage.clear + ingresso nel P2P): mazzo rinato con origine
'conto', pavimento partito, restore partita e conclusa su un fatto;
la riga ⚡ dentro il foglio della presa su un ordine VERO del libro;
il tocco sul volto che apre il negozio del Venditore di collaudo
senza far scattare la presa. E il banco node fa girare la gamba vera
con un coordinatore di cartone: nasce dal seme, non tocca un mazzo
che c'e', tace sul 409, porta a casa il pavimento.
RESTA A VERBALE il gemello non curato: un giudice lato server («e'
tuo» dalla tabella p2p_ordini) marcherebbe anche a restore muta, ma
saprebbe dire «e' tuo» senza saper APRIRE lo scambio — un tocco
monco. Se un giorno servira', si costruira' insieme alla ripresa vera.
LA PORTA DELLO SCAMBIO NELLA FILA DELLE CATEGORIE (set 2026,
decisione di Andrea). Il P2P aveva due ingressi e nessuno dei due si
incontra guardando la home: il tab in fondo alla nav — un glifo, che
si trova solo se lo si cerca — e la card in «Da scoprire», che è una
fila di occasioni e non una mappa. La fila delle CATEGORIE invece è
il posto dove si guarda «cosa c'è qui dentro», e lì adesso c'è la
card dello scambio: dopo il barattolo, col logo completo al posto
dell'illustrazione, «Scambio P2P» scritto sotto.
IL GATE NON SI RISCRIVE, si CHIAMA: il tocco è `vaiP2P()`, la stessa
funzione del tab. Chi ha la leva accesa atterra sulla vista vera con
la nav trasformata, tutti gli altri sul coming soon che c'era già.
Una `go('p2p')` scritta a mano sulla card sarebbe stata più corta di
mezza riga e avrebbe creato una seconda verità: due porte con due
giudici restano allineate finché nessuno ne tocca uno.
TRE STRADE SCARTATE, coi loro perché. 1) La card PRIMA del
barattolo: quel posto è del vetro dall'ago 2026 e chi usa l'app
l'ha già imparato — un ingresso nuovo non sposta uno vecchio.
2) Una classe CSS sua per «pareggiare» il logo con le illustrazioni:
misurato a schermo, non serve — il quadrato 152×152 dentro il
riquadro a ~1,15 rende 125×125, che è l'altezza piena delle sorelle
(«Casa e giardino» ne rende 114 di larghezza, meno di lui). Una
taratura in più sarebbe stata una taratura da mantenere per niente.
3) Togliere la card da «Da scoprire» adesso che c'è questa: non è
una decisione di questo cantiere, e la sua voce dice perché resta —
si guarda a rodaggio se due porte per lo stesso posto sono una di
troppo.
LA CARD C'È PER TUTTI e non porta la guardia del barattolo: quella
serve perché una card che filtra il nulla è un bottone verso un muro,
mentre qui il muro non c'è — a leva spenta si atterra sul coming
soon, che è markup fisso. E non entra nella `firma` della striscia,
che è sempre uguale a sé stessa: la fila si rifà quando cambia
l'ordine, il reparto o lo stato del barattolo, e in nessun altro
caso.
UNA PROVA HA CAMBIATO FETTA, non lato: `prove_barattolo_in_striscia`
ritagliava la card del vetro da «cella-barattolo» fino a
«voci.map(», e con la card P2P in mezzo si sarebbe mangiata anche
lei — il taglio adesso finisce dove quella comincia, col perché
scritto accanto.
COLLAUDATA: **8759 prove verdi, 0 rosse** (+11 sulle 8748 di HEAD,
misurate su una copia pulita dell'albero), e **5 mutazioni, 5
uccise** — il `go` scritto a mano, il `data-cat` che farebbe cadere
la card nel tocco lungo, il gesto da tastiera tolto, la card che si
accende come un reparto, la card che scavalca il barattolo. Giro dal
vivo col server vero a 375 e a 1100 nei due rami del giudice: a leva
SPENTA il tocco porta a `view-p2ppresto` senza nav trasformata, a
leva ACCESA a `view-p2p` con `body.nav-p2p`; e da anonimo (senza
`myTgId`) la fila apre con «Tutto» e la card dello scambio subito
dopo, che il vetro là non nasce.
I TRE RITOCCHI ALLA CARD DELLO SCAMBIO (set 2026, chiesti da Andrea
guardando la home). Il logo più grosso, il tocco lungo che condivide,
le frecce che virano. Tre cose piccole, e due di loro ROVESCIANO una
riga scritta il giorno prima — che è il motivo per cui questa voce
esiste: le prove che le certificavano hanno cambiato lato col perché,
nessuna si è allentata.
1) PIÙ GROSSO, E LA RAGIONE NON È «PERCHÉ SÌ»: le 27 illustrazioni
sono pareggiate d'inchiostro FRA LORO, questo è un marchio — tratto
sottile, due frecce attorno al vuoto — quindi alla stessa misura pesa
meno. `inset:5%` sulla sola `.cat-fig` porta il lato reso da 125 a 144
(su card da 160) senza toccare il quadrato: la fila resta allineata al
pixel, si allarga la figura dentro. Il primo giro aveva MISURATO
giusto e concluso «nessuna regola CSS dedicata»; la misura resta vera,
la conclusione cade perché è cambiato quel che si vuole.
2) IL TOCCO LUNGO CONDIVIDE, e per farlo è servita una PAGINA.
`/p2p` è una rotta vera del server, la terza sorella di `/sicurezza` e
`/privacy`: stessa liturgia — stessa Mini App, il client legge il
percorso e apre la vista. Quindi cade il «niente href, niente
data-cat» del primo giro, che si reggeva su «una vista dell'app un URL
da condividere non ce l'ha».
IL data-cat È LA STESSA CHIAVE DELLE SORELLE, e il nome è `p2p`
MINUSCOLO: i reparti sono nomi italiani con la maiuscola, quindi in
`CATS` non può entrare nemmeno per sbaglio. Così il gesto resta UNO —
il delegato guarda `.cat-cella[data-cat]`, e un secondo selettore
sarebbe un secondo posto dove ricordarsi delle bandierine — senza che
la card diventi un reparto da nessun'altra parte. `condividiCategoria`
lo riconosce PRIMA della guardia su `CATS`: quella guardia resta, ed è
ciò che impedisce a qualunque altro nome di finire lì.
LA PAGINA NON SI INDICIZZA, ed è una decisione: finché la leva è una
fase di prova, chi ci arrivasse da un motore troverebbe quasi sempre
il «coming soon» — un risultato che promette una cosa e ne dà
un'altra. I meta però sono suoi: l'indirizzo si MANDA, e l'anteprima
deve dire di cosa si tratta. Fuori dalla sitemap per la stessa
ragione — deindicizzata e annunciata sarebbe un segnale contro
l'altro. Il giorno che la leva si apre a tutti si toglie
`indicizza=False` e si aggiunge la riga.
E CHI ATTERRA SU /p2p PASSA DAL GIUDICE, `vaiP2P()`, non da un `go`
scritto lì: il gate resta in un posto solo, come per le due porte.
Sta in coda al boot e NON fra le viste anticipate con /sicurezza e
/privacy — quelle sono markup fisso, questa ha bisogno delle leve, e
anticiparla vorrebbe dire rispondere «spenta» a tutti.
3) LE FRECCE VIRANO, e la strada scelta è il CROSSFADE fra i due
gemelli già in casa (compra, freccia di sopra verde; vendi, freccia di
sotto rossa). Scartato l'hue-rotate: girerebbe anche il barattolo, e
mascherarne le sole frecce vorrebbe dire un file nuovo. Si anima la
sola `opacity` — la proprietà che il compositore muove senza
ridisegnare — a `2.5s ease-in-out infinite alternate`, cinque secondi
di ciclo, con la curva che indugia sui due estremi e passa svelta per
il mezzo scolorito.
IL BARATTOLO FERMO NON È UNA SPERANZA, È UNA MISURA, e la ricetta era
già pagata (i gemelli si giudicano ALLA RESA, nella pancia, soglia
percettiva 24 — il confronto esatto scatta anche a disegno identico):
fra i due PNG a 152 zero pixel sopra soglia, e sui due fotogrammi VERI
a 480 — l'animazione fermata ai due estremi con la Web Animations API,
così il confronto è deterministico invece di una gara col cronometro —
di nuovo zero, massimo 22. Sulla tessera intera 35.760 pixel cambiano:
si muove quel che deve.
A MOVIMENTO SPENTO IL MARCHIO RESTA INTERO: sotto
`prefers-reduced-motion:reduce` la coppia si spegne tutt'e due e
prende il posto il terzo gemello, il logo completo. Il solo verde
sarebbe un logo a metà. I tre file non costano niente in più: stanno
già nel markup fisso della vista scambio e degli stati vuoti, quindi
il browser li scarica comunque a ogni avvio.
⚠️ E IL VIRAGGIO NON SI PROVA NEL BROWSER PANE, che emula
`prefers-reduced-motion:reduce`: lì l'animazione non parte proprio — il
che ha provato GRATIS la via ridotta (verde 0, rosso 0, completo 1,
`animation:none`), ma dell'altra non diceva niente. E LA STESSA
TRAPPOLA STA IN HEADLESS: anche Chrome headless parte a «reduce», e il
primo giro ha risposto «nessuna animazione» su un'animazione sana.
Serve `Emulation.setEmulatedMedia` con `prefers-reduced-motion:
no-preference` — senza, si conclude che il viraggio non c'è.
COLLAUDATI: **8772 prove verdi, 0 rosse** (+13 sulle 8759 di HEAD,
misurate su una copia pulita dell'albero), con **sei prove che cambiano
lato** — l'href, il data-cat, la regola CSS, il gesto da tastiera, il
conto della card (adesso conta l'ancora e non la parola, che la parola
sta anche nel CSS) e il tocco, che ora passa da `vaiP2PDaTocco` — e
**10 MUTAZIONI, 10 UCCISE**: il logo che torna alla misura delle
sorelle, il viraggio senza `alternate`, il ridotto che si ferma su un
logo a metà, il completo che scivola in testa e copre i gemelli,
l'href tolto, il solo data-cat tolto, il ramo della condivisione
spostato DOPO la guardia su `CATS`, l'atterraggio che scavalca il
giudice, la rotta che si mette a farsi indicizzare, la rotta che
sparisce.
GIRO DAL VIVO col server vero: `/p2p` risponde 200 coi suoi meta e col
`noindex` (nessun canonical, che sulla deindicizzata non ci va);
atterrando lì la vista è `p2ppresto` a leva spenta e `p2p` con la nav
trasformata a leva accesa; il tocco sulla card fa lo stesso nei due
rami; la condivisione produce `…/p2p` col suo testo; il delegato del
tocco lungo vede la card (`.cat-cella[data-cat]` la trova, e le celle
con quell'attributo salgono a 30); la figura misura 144 su un quadrato
da 160, cioè la fila non si è mossa.
I DUE RITOCCHI DEL GIORNO DOPO (set 2026, Andrea guardando la home e
il libro). Il viraggio delle frecce se ne va, e nel tab «Vendi BTC» la
riga in sats cambia verbo.
1) VIA IL VIRAGGIO, E NON PERCHÉ ERA ROTTO. Il crossfade fra i gemelli
compra e vendi funzionava, e il barattolo restava fermo per
costruzione — misurato alla resa, zero pixel sopra soglia. La ragione
è un'altra, ed è quella che vale: LA FILA DELLE CATEGORIE È UNA MAPPA
DA LEGGERE, e l'unica cosa che si muove in quella riga tira l'occhio
via da tutte le altre. Una card che si agita pesa più di quanto vale.
Resta il logo COMPLETO e fermo, e resta il logo più grosso — quello
del giro prima non si tocca.
COL VIRAGGIO SE NE VANNO ANCHE LE SUE CONSEGUENZE, che è la parte che
in un «togli» si dimentica: la regola del movimento ridotto (non ha
più niente da fermare) e le due immagini in più. Della card resta UNA
riga di CSS in tutto il foglio — quella dell'`inset` — e a contarla
c'è una sentinella, perché «una regola sola» è la forma più corta di
dire tutte e tre le cose insieme.
LA CARD IN «DA SCOPRIRE» NON SI TOCCA (decisione di Andrea): è
un'altra fila e un altro mestiere — lì si annunciano occasioni, qui si
legge una mappa.
2) «PAGA» E NON «INVIA», e il ritocco è più piccolo di quel che dice.
Nel tab «Vendi BTC» la riga in sats diceva «Invia ≈ X sats», mentre
nel tab «Compra BTC» la riga in euro dice «Paga 8,00 €». IL GESTO NON
CAMBIA FRA I DUE TAB — chi dà, paga — quindi due verbi diversi
facevano sembrare diverse due cose che diverse non sono. Cambia solo
CON COSA si paga: euro di là, sats di qua.
E «PAGA» DICE ANCHE MEGLIO COME VA: chi vende sats non li spedisce a
mano a chi compra — paga una fattura, e quella li tiene in garanzia
finché l'euro non è arrivato. «Invia» lasciava immaginare un bonifico
in bitcoin da mandare a qualcuno.
UNA SENTINELLA NUOVA NON GUARDA LA PAROLA MA IL PATTO: che il verbo di
chi dà sia LO STESSO nei due tab, letto da tutt'e due le righe
renderizzate. Una prova sulla sola parola nuova sarebbe passata anche
il giorno che qualcuno cambia l'altro capo.
⚠️ TRE PROVE NON CAMBIANO LATO MA VERSO, che è una cosa diversa dal
solito: certificavano che il viraggio CI FOSSE, e adesso certificano
che non torni — stessa riga sorvegliata, giudizio opposto. Sono la
memoria della decisione: senza, fra sei mesi il crossfade rientra come
«miglioria» e nessuno si accorge che era già stato tolto apposta.
COLLAUDATI: **8774 prove verdi, 0 rosse** (+2 nette sulle 8772 di HEAD,
misurate su una copia pulita: quattro del viraggio se ne vanno, quattro
sulla card ferma le sostituiscono, due nuove sul verbo), con **quattro
prove che cambiano lato** — le tre del viraggio e quella dei verbi
imperativi — e **7 MUTAZIONI, 7 UCCISE**: il viraggio che rientra dalla
finestra, il fotogramma orfano lasciato indietro, la regola del
movimento ridotto che torna senza niente da fermare, il marchio che
ridiventa un gemello del libro, il logo che torna alla misura delle
sorelle, la riga in sats che torna a «Invia», e i due tab che tornano a
due verbi diversi DALL'ALTRO CAPO — l'euro che diventa «Invia» — che è
la mutazione che una sentinella sulla sola parola nuova non avrebbe
preso.
GIRO DAL VIVO col server vero: sulla card una sola immagine (il
completo), `animationName: none`, 144 px dentro un quadrato da 160 —
il logo grosso è rimasto e la fila non si è mossa. Le due righe del
libro, renderizzate dai loro eventi 38383 veri, dicono «Paga 8,00 € /
ricevi ≈ 13 115 sats» nel tab Compra e «Paga ≈ 13 115 sats / Ricevi
8,00 €» nel tab Vendi. ⚠️ In locale il libro non ha relay, quindi le
card VERE a schermo non si sono viste: a rispondere per loro è la
prova ESEGUIBILE, che fa girare `ordineDaEvento` + `rigaOrdineP2P` sui
due eventi sotto node — che è la stessa strada di sempre per questa
famiglia, e va detto invece di lasciarlo intendere.

L'ordine P2P in vetrina (set 2026, chiesto da Andrea: «ogni nuovo
annuncio della sezione p2p deve essere pubblicato nella vetrina
similmente a come succede con barattolo»). La richiesta ambigua si e'
chiarita per iscritto: non la griglia della home, non il libro P2P —
il CANALE TELEGRAM «Barattolo Vetrina», lo stesso dove escono gli
annunci normali (vedi «Il canale diventa la vetrina», sopra).
UNA ROTTA NUOVA E FERMA LI', `POST /api/p2p/canale`: il client la
chiama subito dopo che `mostroChiama` e' tornato con successo (dentro
`inviaNuovoOrdineP2P`, riga `agg.contattato = true`), il server
costruisce la caption con `_caption_canale_p2p` — gemella di
`_caption_canale` — e la manda con la STESSA fabbrica di sempre,
`_manda_post_canale(canale_id(), ...)`. Stesso gate delle sorelle
P2P (`_p2p_per(user["id"])["attivo"]`, 409 altrimenti), stesso
fail-open della vetrina normale: canale spento o post fallito non
rompono mai il gesto di chi ha appena pubblicato un ordine vero.
NIENTE FIRMA, ed è la riga da non ammorbidire: `_caption_canale_p2p`
non chiama mai `_firma_venditore` né `_npub_venditore` — l'identità
di scambio non si lega MAI all'account Telegram in un posto pubblico,
la stessa regola che tiene `_conta_chiavi_p2p` senza una pubkey nella
risposta. Il corpo che il client manda è `{lato, euro, metodo}` e
basta: mai una chiave, mai la trade key.
⚠️ E QUELLA RIGA È STATA RIBALTATA lo stesso giorno (decisione di
Andrea): «voglio sempre vedere chi l'ha pubblicato, come già in
Barattolo». La firma ora c'è, ed è la STESSA `_firma_venditore` degli
annunci normali — non una sua imitazione — con la riga che la
distingue dal resto del P2P: questa non è l'identità DI SCAMBIO (la
trade key, pseudonima per costruzione — regola ferrea 2, mai toccata),
è l'identità di chi ha premuto «Pubblica», e il server la conosce già
per forza (il gate di `annuncia_ordine_p2p_canale` chiede un utente
autenticato) — qui si SCEGLIE di scriverla, non la si scopre. La rotta
legge la riga di `utenti` per `tg_id` (nome, username, npub,
npub_verificata, npub_accesso, negozio) e costruisce lo stesso dizionario
a sei chiavi che `_firma_venditore` si aspetta dagli annunci.
IL POSTO DOVE VIVE IL CLIENT NON È UN DETTAGLIO: `annunciaCanaleP2P`
sta DOPO il marcatore «fine del motore dello scambio», mai dentro —
quel blocco è sorvegliato da `prove_p2p_motore` a ZERO fetch e ZERO
`body:` («il segreto non esce, il denaro non passa di qui»), e
infilarci una vera chiamata di rete lì dentro l'avrebbe fatta rossa a
ragione. `inviaNuovoOrdineP2P` (che vive dentro il motore) si limita
a CHIAMARE `annunciaCanaleP2P(...)` per nome — un identificatore, non
un `fetch(` — lo stesso schema che la funzione usa già per
`renderOrdineP2P()`. La prima stesura la metteva vicino alle sorelle
del mazzo (`registraChiaviP2P` e c.) e la tortura testuale di TRE
sentinelle diverse l'ha bocciata subito: quel blocco conta le fetch
col corpo e le vuole ESATTAMENTE quattro (registra, dimentica, il
conto, il seme) — la quinta andava nominata altrove, non lì.
NESSUN THROTTLE, a differenza del drenatore degli annunci normali
(anti-spam, un post al giorno per venditore, aggregati sulle
raffiche): quella macchina legge righe di `annunci`/`utenti` che un
ordine P2P non ha, e il volume atteso oggi è zero — la leva
`P2P_ATTIVO` è ancora chiusa a una lista di prova. Se il volume
crescesse, il freno da aggiungere è quello di casa
(`ritmo_vetrina()`), non uno nuovo. Il tetto sull'importo
(`MAX_EURO_P2P_CANALE = 100_000`) ricalca `max_order_amount` di
mostrod letto dal 38385 (vedi sopra, «I PARAMETRI DEL 38385»): un
ordine più grande di così il coordinatore non lo accetterebbe
comunque.
Collaudato: **+19 prove** (`prove_p2p_canale`, nuova) — la caption
FATTA GIRARE per davvero (non solo grep) su entrambi i lati, la
regola del lessico (rule 9: «deposito di garanzia», mai «escrow» né
«assicurato»), l'escape HTML del metodo, il gate e le validazioni
della rotta lette sul sorgente, e le due posizioni sorvegliate lato
client (fuori dal motore; chiamata solo DOPO `agg.contattato = true`).
Il ramo resta a 8427/1 prima di queste prove nuove come dopo — l'unica
riga rossa è preesistente e indipendente da questo cantiere (un file
di scratch di una sessione precedente, non tracciato, fuori
dall'elenco del compileall).
IN PRODUZIONE basta il deploy: nessuna migrazione (la rotta non
scrive niente su nessuna tabella), nessuna leva nuova — il gate è
quello già acceso o spento del P2P. DA GUARDARE al primo ordine vero
con `P2P_ATTIVO` aperto: che il canale riceva davvero il post (serve
`canale_id()` configurato) e che la caption si legga bene accanto
agli annunci normali.

Il foglio «Pubblica» ridisegnato, e l'intervallo che si prende (set
2026, richiesta di Andrea sul modello della «creazione nuovo ordine»
dell'app di riferimento). Il foglio del + della nav trasformata era due
campi in croce — quanti euro, e un metodo scritto a mano — su un ordine
che nasceva sempre uguale: al prezzo di mercato, importo singolo,
premio zero. Il ridisegno lo apre a tutto quello che il coordinatore sa
già fare, e le due cose nuove — il PREMIO e l'INTERVALLO — erano
tutt'e due a verbale come cantieri futuri: si chiudono qui.

STRUTTURA: A PIENO SCHERMO, UNA SEZIONE PER RIQUADRO. Cinque riquadri
con l'icona tonda a sinistra — valuta, importo, metodi, tipo di prezzo,
e la quinta che cambia col tipo (sats fissi o premio) — testata con la
via d'uscita a sinistra e il titolo in mezzo («Vuoi comprare Bitcoin» /
«Vuoi vendere Bitcoin», che è il tab), piede appiccicato con «Annulla»
e «Invia». A pieno schermo perché cinque sezioni in un foglio dal basso
vogliono dire scorrere dentro una finestra dentro una pagina, che è il
modo in cui si perde il fondo — e il piede sempre a vista è dove si
legge che «Invia» è ancora spento, cioè che manca qualcosa.
LA TASTIERA NON LO ALZA, LO ACCORCIA: i fogli normali salgono di
`--tastiera` col transform, ma un foglio alto quanto lo schermo salendo
si porterebbe via la testata. Qui l'altezza si toglie in fondo e il
transform si spegne (`.sheet.pieno.open{transform:none}`). Da 768px in
su non cambia niente: là il foglio è già un modale centrato, e a pieno
schermo su un monitor sarebbe una finestra vuota con cinque riquadri in
mezzo.

I DUE ESCLUSIVI SONO REGOLA DEL PROTOCOLLO, NON GRAFICA, e sono la
scoperta che ha disegnato il foglio più di qualunque screenshot. Letti
sui byte di mostro-core 0.14.6 (`order.rs`) e di mostrod v0.18.7:
• `check_zero_amount_with_premium` RIFIUTA un ordine che porta insieme
  `amount` e `premium`. Quindi la leva «Prezzo fisso / Mercato» *è*
  quella regola: o i sats o il premio, mai tutt'e due — e il premio si
  azzera nel codice, invece di sperare che il foglio l'abbia lasciato a
  zero.
• `check_range_order_limits` vuole `min < max` e `amount` a ZERO: un
  intervallo non può fissare i sats. Quindi col prezzo fisso il secondo
  campo dell'importo SPARISCE, e passando alla leva il massimo scritto
  si svuota davvero — nasconderlo non basta, un numero rimasto in
  memoria finirebbe nel messaggio.
• `create_fiat_amt_array` (`nip33.rs`) scrive il tag `fa` coi due capi
  quando ci sono, e allora `fiat_amount` vale 0.
La tabella canonica NON si tocca: l'ordine dei campi di `SmallOrder` è
ancora quello di `CAMPI_MOSTRO.ordine`, `min_amount` e `max_amount`
c'erano già (a `null`), quindi la firma regge senza toccare niente.

I METODI DIVENTANO UN VOCABOLARIO CHIUSO, e ROVESCIA una decisione
scritta: prima le pillole erano un suggerimento e sotto c'era un campo
di testo libero, col suo commento che lo difendeva («chi paga in un
altro modo lo scrive, e nessuna lista di casa glielo impedisce»).
IL PERCHÉ DEL ROVESCIAMENTO (decisione di Andrea): ogni metodo ha il
SUO form di recapito — `P2P_FORME_RECAPITO`, dove SEPA vuole
intestatario e IBAN, Revolut un RevTag, i contanti un luogo — e un
metodo scritto a mano cade nella forma generica, dove chi deve ricevere
gli euro trova una casella vuota invece delle sue due righe. Il testo
libero restava leggibile dal coordinatore e ILLEGGIBILE da noi. Le sei
voci (SEPA, SEPA Instant, Revolut, Satispay, PayPal, Contanti) hanno
tutte il loro form — «SEPA Instant» cade in quella `sepa`, che
riconosce /sepa|bonific|iban/ — e c'è la prova ESEGUIBILE che lo dice:
`formaRecapito` sui sei nomi non deve mai tornare la generica. Una voce
nuova si aggiunge nel vocabolario e, se vuole un form suo, anche là.
SUL FILO VIAGGIANO SEPARATI DA VIRGOLE, in una stringa sola: è così che
`nip33.rs` li spezza nei valori del tag `pm`, ed è così che il nostro
lettore li ritrova. La selezione multipla non è una comodità nostra: è
una cosa che il coordinatore sa già fare.

IL PREMIO È IMPOSTABILE, e la nota sotto il cursore dice cosa cambia
PER IL LATO IN CUI SI STA — dalla stessa formula letta sui byte
(`sats -= premium/100 * sats`, sottrazione uniforme sui due versi): un
premio positivo assottiglia sempre i sats, quindi chi vende ne consegna
meno per gli stessi euro e chi compra ne riceve meno. La fascia ±10% è
una scelta di casa e non un limite del protocollo (il premio è un i64 e
nessun controllo lo guarda), e si scrive anche a mano — ma con un CAMPO
IN RIGA, mai un `prompt()` di sistema: quelli sono usciti da questa
pagina uno per uno e non rientrano da qui. La pillola col numero
diventa il campo e «Modifica» diventa «Fatto».

L'INTERVALLO SI PUBBLICA **E** SI PRENDE (decisione di Andrea, che ha
scartato la strada «pubblicalo e basta»): un range che i nostri utenti
vedono e non possono prendere è un buco peggiore del cantiere più
largo. Il libro li mostrava già dal ridisegno delle card, e il tocco
diceva «da qui non si può ancora». Adesso il tocco DEVIA su un foglio
piccolo — «Quanto vuoi scambiare?», un campo e la stima in sats — e da
lì si rientra nella STESSA strada: stessa conferma, stesse cinture,
stessa presa. La cifra viaggia come `Payload::Amount`, che mostrod
legge SOLO su take-sell e take-buy (`get_amount` in `message.rs`) e
confronta con min/max (`get_fiat_amount_requested`): fuori fascia
risponde `OutOfRangeSatsAmount`. Il controllo che facciamo qui è
cortesia — a tenere il patto è lui — ma un no che arriva dopo un giro
di rete e una chiave bruciata è un no pagato troppo caro.
L'IMPORTO SCELTO SI RICORDA (`importoScelto`) e non è un doppione di
`euro`: la riga locale porta la cifra, questo porta il FATTO che va
rimandata a ogni tentativo. Senza, un «Riprova» su un intervallo
ripartirebbe senza la scelta e si prenderebbe un `OutOfRangeSatsAmount`
che nessuno collegherebbe al gesto.
E L'INTERVALLO COLLASSA quando il coordinatore fissa la cifra: dal
`fiat_amount` della sua risposta in poi la pagina dello scambio mostra
un numero solo. Senza quella riga continuerebbe a dire «20,00–100,00 €»
su uno scambio che vale 45. Il giudice è UNO (`euroTestoP2P`), che le
due viste dello scambio non possano dire due cose.

⚠️ IL LIMITE DICHIARATO DELL'INTERVALLO, e non è un difetto: si CHIUDE
alla prima presa. Il resto di un range si ripubblica solo se chi ha
creato manda `NextTrade` (chiave e indice del prossimo scambio) insieme
al rilascio, e mostrod senza quel pezzo «salta il resto» invece di dare
errore (`release.rs`: handle_child_order failed → skipping remainder,
resolving maker bond). Mandarlo NON è la strada corta che sembra:
farebbe nascere un ordine FIGLIO con una chiave che questa pagina non
sa ancora governare, cioè rifarebbe il difetto degli «ordini
ingovernabili» chiuso il 9 set. Quindi oggi non si manda, ed è una
scelta: il pezzo mancante è il suo cantiere, e sta accanto alla ripresa
delle fasi 5-6-7 che eredita lo stesso mattone.

⚠️ IL LIGHTNING ADDRESS NON C'È, ed è la sezione che il disegno di
partenza aveva e questo foglio non ha (decisione di Andrea). Due
ragioni, e la seconda è più forte della prima. UNO: il verbale dice già
«mai un lightning address» come destinazione del payout — `do_payment`
li RI-RISOLVE a ogni tentativo, quindi un server che risponde male rende
il fallimento deterministico e nessun retry lo aggiusterà mai
(`MalformedAPIRes`, la prova impantanata con Alan). DUE, e vale per la
CREAZIONE: su new-order mostrod fa girare `validate_invoice`, e
`is_valid_invoice` prova PRIMA il Lightning address e l'LNURL — su un
circuito Tor freddo (10,6 s contro i tre budget compilati da 4s/2s/2s)
l'ordine non nasce proprio, in silenzio. Un campo che può far fallire
la pubblicazione senza dire perché è peggio di un campo che non c'è.
Il Lightning address si chiede DOPO, nel foglio «💸 Dove ricevere i
sats», che c'è già ed è il momento in cui un guasto si può ancora
recuperare.

LA VALUTA È UNA TENDINA CON UNA VOCE SOLA, ed è deliberato: `P2P_VALUTE`
è una lista, quindi aggiungerne una — USDT, il giorno che il
coordinatore l'accetta — è UNA RIGA e non una caccia. Il ▾ va rimesso a
mano (`appearance:none` toglie la freccia insieme al recinto, e un
select senza freccia si legge come testo fermo: nessuno lo tocca), e
sta nel wrapper perché uno pseudo-elemento su un `<select>` non si
disegna.

LE REGOLE VIVONO IN UNA FUNZIONE PURA, `ordineDaCampiP2P`, ed è l'unico
modo di provarle: sbagliando questi campi il coordinatore NON risponde
un errore — TACE (è il precedente del JSON canonico, dove la firma
cadeva e nessuno lo leggeva da nessuna parte). Chi spedisce la CHIAMA
invece di ricopiarne le regole, e la riga locale legge dallo STESSO
ordine, così quel che si vede a schermo e quel che è partito non
possono raccontare due cose diverse.
E IL GIUDIZIO DEL BOTTONE È PURO ANCHE LUI (`valeNuovoOrdineP2P`): dice
se i campi bastano e, se non bastano, DICE COSA MANCA — in rosso, non
nel grigio degli altri suggerimenti, dove non lo leggeva nessuno. Un
bottone spento senza una ragione visibile è il vicolo cieco muto che
questa riga esiste per evitare.

LA SENTINELLA DELLE PAROLE SI ALLARGA, ed era il modo in cui questo
cantiere poteva scivolare: il foglio non è più una funzione sola — le
sezioni nascono da `sezioneNuovoP2P`, la nota del premio da
`premioNotaP2P` — e una parola vietata là dentro sarebbe uscita a
schermo con la sentinella verde. Ora guarda tutt'e quattro i pezzi.

COLLAUDATI: **8792 prove verdi, 0 rosse** (+18 sulle 8774 di HEAD,
misurate su un worktree pulito), e **11 MUTAZIONI, 11 UCCISE**: il
premio che non si azzera a prezzo fisso, l'intervallo che porta anche
l'importo singolo, il capo basso che viaggia senza intervallo, i sats
fissi che non partono, l'intervallo che non collassa alla presa, la
cifra scelta che non viaggia col take, l'intervallo che si prende senza
chiedere quanto, i metodi separati da spazi invece che da virgole, il
tetto dei sats che non si guarda, la fascia dell'intervallo che non si
guarda, e il «Riprova» che dimentica la cifra scelta.
GIRO DAL VIVO col server vero, chiaro e scuro, a 375×812: la testata
con la freccia e il titolo che cambia col tab, le cinque sezioni, la
tendina dei metodi che si apre e spunta due voci, la leva che porta a
prezzo fisso (secondo campo e premio VIA, sezione sats che compare,
«Invia» spento con «Scrivi quanti sats»), il premio a +4% con la nota
del lato giusto, e il foglio «Quanto» su un range 20–100 che stima
«Riceverai circa 88 200 sats» a 45 € col premio al 2%. E le due
deviazioni della presa provate dal vivo: senza cifra si apre «Quanto»,
con la cifra si apre la conferma che dice «45,00 € · al prezzo di
mercato».
⚠️ QUEL CHE IL GIRO DAL VIVO **NON** HA PROVATO, e va detto invece di
lasciarlo intendere: nessun ordine è stato PUBBLICATO davvero. In
locale non c'è coordinatore, quindi a rispondere per il messaggio è la
prova eseguibile che fa girare `ordineDaCampiP2P` sui quattro casi
sotto node. Il primo intervallo vero — e la prima presa a importo
scelto — restano da fare sul campo, e si agganciano alla tappa 8.
E DUE COSE LE HA TROVATE IL GIRO, non il ragionamento. 1) A 320px
niente scorrimento orizzontale (scrollWidth = clientWidth = 320) col
caso peggiore addosso: intervallo scritto, due metodi lunghi («SEPA
Instant, Contanti»), e la riga «20 a 100» che regge. 2) DA 768px IN SU
IL PIEDE NON SI APPICCICA PIÙ: là il foglio è un modale che scorre
dentro sé stesso, e un piede sticky lasciava scorrere il contenuto
NELLA striscia d'aria sotto i bottoni — il padding del foglio. Vale la
regola di tutti gli altri fogli: i bottoni stanno in fondo e ci si
arriva scorrendo. Stessa famiglia il rientro doppio della testata, che
sul modale aggiungeva il proprio padding a quello di `.sheet`.
⚠️ LA TENDINA APERTA È USCITA DALLA RIGA DELL'ICONA, trovato guardando:
dentro la riga, l'icona tonda finiva a mezza altezza di una lista di
sei voci — un cerchio che galleggia in mezzo al nulla. Fuori, la lista
prende tutta la larghezza del riquadro e l'icona resta col campo. Da lì
il `sotto` di `sezioneNuovoP2P`, che serve a questa cosa sola.
⚠️ E L'INCROCIO COL CANALE È IL DIFETTO CHE IL REBASE STAVA PER FAR
PASSARE, ed è la lezione del giro. Mentre questo foglio si ridisegnava,
un'altra sessione ha pubblicato «L'ordine P2P si racconta in vetrina»,
che aggiunge `annunciaCanaleP2P(lato, euro, metodo)` in fondo al try di
`inviaNuovoOrdineP2P` — cioè dentro la funzione che qui è stata
riscritta da capo. Il rebase ha applicato TUTTO SENZA UN CONFLITTO: la
riga di là è finita nella funzione di qua, dove `euro` e `metodo` non
esistevano più (il ridisegno aveva sostituito l'importo unico e il
metodo scritto a mano). Un ReferenceError, che a schermo si legge come
«l'ordine non si pubblica» — e nessuna prova sul TESTO poteva vederlo,
perché tutte e tre le righe erano esattamente quelle attese.
LA CURA È DARE INDIETRO I DUE NOMI, non cambiare la chiamata: la rotta
dell'altra sessione non si tocca. E la sentinella nuova non guarda una
parola ma un LEGAME — che `lato`, `euro` e `metodo` esistano e siano
dichiarati PRIMA di quella riga.
⚠️ SU UN INTERVALLO IL POST NEL CANALE DICE IL MINIMO, dichiarato: la
rotta vuole un intero e «20–100» non ci passa. Il capo basso è il
prezzo d'ingresso, quindi non è una bugia — ma racconta meno
dell'ordine, e chi tocca quella rotta lo sistemi là.

I sei ritocchi al foglio «Pubblica» (set 2026, il giorno dopo, guardati
dal vivo da Andrea). Il ridisegno stava in piedi; questi sono i sei
punti in cui, a schermo, diceva ancora una cosa diversa da quella che
voleva dire.

1) VIA LA RIGA D'APERTURA. «Stai chiedendo di comprare sats pagando in
euro. Chi risponde bloccherà i sats in garanzia» diceva col paragrafo
quel che il titolo dice con tre parole, e su un foglio a pieno schermo
si mangiava la prima sezione. Il fatto che i sats restino in garanzia
resta detto dove serve davvero — la pagina dello scambio, «I tuoi
dati» — e la riga in fondo a questo foglio lo ripete a chi arriva fin
là.

2) LA VALUTA APRE IL FOGLIO DI CASA. La tendina apriva il selettore del
SISTEMA: quello non si può vestire, e dentro una Mini App si vede a
occhio nudo che viene da fuori. Adesso apre `#pickerSheet`, LO STESSO
di Categoria e Taglia — stesse voci, stessa chiusura, stesso ritorno
del fuoco — con le voci fatte di bandierina più sigla («🇪🇺 EUR»),
corte apposta: una valuta si riconosce dalla sigla, e il nome per
esteso in un elenco di tre voci è solo più testo da scartare.
⚠️ E IL CATALOGO SE LO PORTA LEI invece di stare nella mappa `PICKER`,
che è la strada breve e sbagliata: quella mappa il boot la percorre
TUTTA (`Object.keys(PICKER).forEach(aggiornaPicker)`) diciassettemila
righe più su di `P2P_VALUTE`, quindi una voce che la legge è una const
toccata dentro la sua temporal dead zone. NON È UN RAGIONAMENTO: la
strada breve è stata presa, e a bocciarla è stata la prova di casa che
fa girare ogni blocco `<script>` fino in fondo — «Cannot access
'P2P_VALUTE' before initialization». In un browser vero oggi non
scoppierebbe (il campo-bottone nasce col foglio, quindi al boot
`el(...)` è null e la funzione esce prima), ma è un invariante che
nessuno saprebbe di dover rispettare: basterebbe mettere quel bottone
nel markup fisso.
IL <select> NASCOSTO NON C'È PROPRIO, e non è una dimenticanza: il
picker di casa lo usa come deposito del valore perché nasce dai form
del venditore, dove il `<select>` c'era già. Qui il valore vive già in
una variabile del foglio, quindi un elemento in più sarebbe solo un
secondo posto da tenere in pari.

3) UN CAMPO SOLO, ALL'APERTURA. Il secondo campo dell'importo — e la
riga che lo spiega — si fanno vedere quando si TOCCA il primo. Chi
vuole un importo secco non incontra mai una casella in più da capire,
e chi vuole un intervallo la trova nel momento esatto in cui sta
scrivendo la cifra. La nota cambia anche verso: da «Tocca il secondo
campo PER creare un ordine a intervallo» (un invito) a «Tocca il
secondo campo SOLO SE vuoi creare un ordine a intervallo» (un
avvertimento) — con la casella già a schermo, la prima frase invitava
a riempirla.
⚠️ SI SVELA, NON SI RIDISEGNA, ed è la riga da non ammorbidire: il
tocco che fa scattare la cosa è lo stesso che apre la tastiera, e un
render lì porterebbe via il fuoco al campo che si sta per riempire (la
lezione delle pillole). Perciò `style="display:none"` e non
l'attributo `hidden`: `.hint` potrebbe avere un `display` suo e
vincerlo. E tornando a mercato dopo un giro a prezzo fisso il secondo
campo riparte CHIUSO — il massimo se n'è andato col passaggio, e una
casella vuota già aperta direbbe che lì c'era qualcosa.

4) IL PREMIO PERDE DUE DISEGNI E GUADAGNA UN ALLINEAMENTO. Via l'icona
tonda (📈): qui la riga è occupata da una barra che vuole tutta la
larghezza che trova, e il cerchio la accorciava di quaranta pixel per
dire una cosa che il titolo «Premio (%)» dice già. Via la matita
accanto a «Modifica», che su un fondo chiaro era la cosa più scura
della sezione. E la pillola col numero passa A SINISTRA DELLA BARRA, a
metà altezza della linea: prima la pillola e il suo bottone stavano in
una colonna sola, e il centro della colonna non è il centro della
pillola — il numero finiva sopra la linea. Adesso la riga tiene solo
pillola e barra, e sotto ci va «Modifica» in fila coi due capi: sotto
la pillola il suo bottone, sotto la barra i suoi estremi.
L'ICONA È DIVENTATA FACOLTATIVA per costruzione (`sezioneNuovoP2P`):
senza quel ramo restava un cerchio vuoto al posto di quello tolto.

5) LA BARRA DICE CHE VA A SCATTI. Dentro il binario una LINEA
tratteggiata bianca, venti tratti — uno per ogni punto percentuale da
−10 a +10 — così chi la guarda capisce che non è un cursore continuo
prima di provarlo. Il passo è in PERCENTUALE (5% = un punto su venti),
quindi i tratti restano al loro posto qualunque sia la larghezza del
riquadro.
⚠️ È UNA LINEA E NON VENTI BLOCCHI, e la differenza si è vista solo a
schermo: al primo giro il tratteggio era alto quanto tutta la barra, e
il binario sembrava SPEZZATO in segmenti arancioni. Il
`background-size:100% 2px` lo tiene a due pixel, in mezzo.
E QUI SPARISCE `accent-color`: vestire il binario vuol dire
`appearance:none`, e da lì in poi il pollice se lo disegna la pagina —
su tutt'e due i motori, che i due pseudo-elementi non si possono
raggruppare (una regola sconosciuta fa cadere l'intera dichiarazione).

6) LE DUE USCITE SONO GEMELLE, e ci sono volute DUE cose. La prima:
`.btn.ghost` porta un `margin-top:10px` suo e vive PIÙ IN BASSO nel
foglio, quindi a pari specificità vinceva lui — e in una riga flex quei
dieci pixel facevano «Annulla» più basso del gemello. La seconda l'ha
trovata il righello e non l'occhio: col `box-sizing:border-box` di casa
una `flex-basis:0` non parte davvero da zero, parte dai BORDI — e
`.ghost` ne ha due da 2px mentre `.orange` non ne ha. Misurati dal
vivo: **169 contro 165**. Due colonne `1fr` sono esattamente uguali
qualunque bordo abbiano dentro, quindi il piede è una GRIGLIA. Adesso
i due bottoni misurano **166,5 × 54,47 allo stesso `top`** a 375px, e
**139 × 54,47** a 320.
LA LEZIONE OLTRE IL BOTTONE: «stessa grandezza» in flex non si ottiene
con `flex:1` quando i due elementi hanno bordi diversi. Chi mette due
bottoni gemelli in una riga misuri, invece di guardare.

COLLAUDATI: **8841 prove verdi, 0 rosse** (+27 sulle 8814 del giro
prima) e **17 MUTAZIONI, 17 UCCISE** in due giri.
Il primo giro (dieci cadute su tredici): la riga d'apertura che
rientra, la valuta che torna al selettore del sistema, il catalogo che
rientra nella mappa percorsa al boot, il tocco che non sveglia niente,
lo svelare che diventa un render, la nota che torna a invitare invece
di avvertire, l'icona che rientra sul premio, il piede che torna una
riga flessibile, la pillola che torna in cima alla riga, e il catalogo
delle valute che cresce lasciando il payload cablato su EUR.
Il secondo, dopo aver stretto le tre prove molli: la «a» in mezzo ai
campi, il campo del massimo e la nota dell'intervallo che nascono già
visibili (tre mutazioni, una per nascosto), la matita che rientra —
sia come carattere sia scritta `\u270f` —, e i tratti che tornano alti
quanto la barra su webkit e spariscono del tutto su moz.
⚠️ QUELL'ULTIMA È UNA PROVA CHE GUARDA AVANTI, ed è nata da questo
giro: la tendina è «pronta per altre valute» ma `ordineDaCampiP2P`
scrive `fiat_code: 'EUR'` a mano. Finché la scelta è una sola non è
una bugia; il giorno che il catalogo cresce la prova diventa rossa e
dice dove andare, invece di lasciar offrire USDT e spedire EUR.

⚠️ IL PRIMO GIRO DI TORTURA NE LASCIÒ VIVE TRE, e le tre erano PROVE
molli — non codice rotto. Vale scriverle, perché sono tre modi diversi
di sbagliare una sentinella, e tornano.
• GUARDARE UN POSTO SOLO DOVE I POSTI SONO TRE: i nascosti
dell'intervallo sono la «a» in mezzo ai campi, il campo e la nota, e
la prova cercava il ternario «da qualche parte» dentro il render —
scoprirne uno solo la lasciava verde. Adesso i tre si nominano a uno a
uno.
• GUARDARE IL CARATTERE E NON IL SUO CODICE: la matita si scrive anche
`\u270f`, e una sentinella che cerca «✏️» le passa davanti. Adesso
guarda tutt'e due le forme.
• NOMINARE DUE COSE E CERCARLE IN UNA SOLA: il ciclo sui due binari
del cursore (`-webkit-` e `-moz-`) cercava dentro TUTTO il foglio di
stile, quindi togliere i tratti da uno lasciava rispondere l'altro. Il
ciclo c'era, l'isolamento no. Adesso ogni pseudo-elemento si ritaglia
il suo blocco.
LA REGOLA CHE LE UNISCE: una prova che cerca in un contenitore più
grande di quello che sta sorvegliando risponde per il vicino. E a
dirlo non è la lettura — è la mutazione: tutte e tre erano verdi, e
tutte e tre lo restavano col guasto dentro.
GIRO DAL VIVO col server vero, chiaro e scuro, a 375 e a 320: il
foglio si apre sulla valuta senza paragrafo davanti, la tendina apre
il foglio di casa col suo «🇪🇺 EUR» spuntato, l'importo ha un campo
solo finché non lo si tocca, il premio a −6% e a +8% con la nota del
lato giusto, i tratti bianchi dentro la barra, e le due uscite
misurate uguali. Nessuno scorrimento orizzontale a 320.

I cinque ritocchi del secondo giorno (set 2026, guardati dal vivo da
Andrea). Quattro sono vestito; uno era un difetto vero, e non era
quello che sembrava.

1) L'ICONA DELLA VALUTA NON È PIÙ L'EURO. Era la bandierina della
valuta scelta, e sembrava una buona idea — dice il fatto invece di
annunciare la categoria — finché non si guarda avanti: nel catalogo
domani c'è USDT, e un'icona che dice UNA valuta diventa una bugia il
giorno che se ne sceglie un'altra. Adesso è un GLOBO, generico per
costruzione. La bandierina resta dov'è vera: nella voce scelta
(«🇪🇺 EUR») e nelle voci del foglio-picker.
LE ALTRE DUE CANDIDATE SONO CADUTE GUARDANDOLE, e vale scriverlo:
«due monete» a 22px diventa una macchia (i due cerchi si toccano e il
velo li fonde), e «cambio» — due frecce dentro un cerchio — nella nav
dice già «I miei scambi», quindi lo stesso segno avrebbe detto due
cose in due posti.

2) UN CAMPO SOLO ALL'APERTURA: era già così. Andrea l'ha segnalato
come non fatto, ma passando dalla porta vera (il `+` della nav) il
campo del massimo nasce con `display:none` — quel che si vedeva era la
versione prima del deploy, o la cache dell'app. NON SI TOCCA NIENTE, e
si aggiunge la prova che inchioda la garanzia dove sta davvero: non nel
render (che disegna quel che lo stato dice) ma nell'AZZERAMENTO di
`apriNuovoOrdineP2P`, che è l'unico posto da cui il foglio si apre.
Una segnalazione dal campo che si rivela già curata lascia comunque
qualcosa: il punto in cui la garanzia era solo implicita.

3) ⚠️ «LA PAGINA SCENDE A TENDINA» NON ERA UNO SCROLL, ed è la voce
che vale il giro. Al tocco sul campo dell'importo tutto il foglio
scivolava giù. Le tre ipotesi ovvie erano `scrollIntoView`, il fuoco
che sposta il foglio, il secondo campo che spinge il layout — e sono
tutte sbagliate. La causa è geometrica: `.sheet` è
`position:fixed; bottom:0`, e a questo foglio la tastiera toglie
altezza (`height:calc(100dvh - var(--tastiera))`). Con l'ancora in
BASSO, accorciare vuol dire ABBASSARE IL BORDO ALTO: il foglio non
scorre, si accorcia dal lato sbagliato, e testata compresa scende di
quanto la tastiera è alta.
LA CURA È `top:0; bottom:auto` sul solo `.sheet.pieno`: l'altezza se ne
va dal basso, dove la tastiera c'è davvero, e sopra non si muove
niente. MISURATO: con `--tastiera` a 300px il `top` resta 0 e l'altezza
passa da 812 a 512 — prima il top sarebbe finito a 300.
E LA SECONDA MEZZA CAUSA SI CURA LO STESSO: la nota che compare
allunga il riquadro, e l'ancoraggio dello scorrimento del browser può
rispondere spostando il corpo sotto il dito. `svelaSecondoImportoP2P`
si segna dov'era e ce lo rimette — il campo che si sta toccando non ha
cambiato posizione, quindi non c'è niente da inseguire.
LA LEZIONE: quando «la pagina si muove» su un foglio ancorato a un
bordo, prima di cercare uno scroll si guarda DA CHE LATO il foglio
cambia dimensione.

4) LE ICONE SONO LINEE, con la loro tinta leggera. Cinque emoji in
fila erano cinque disegni di cinque mani diverse, ognuna col suo colore
e il suo stile — un'accozzaglia dentro cinque cerchi saturi. Adesso
sono disegnate come quelle della nav: stesso `viewBox` (2 2 20 20),
tratto 1.5, e il «velo» — la stessa forma riempita al 12% — che dà
corpo senza aggiungere una seconda linea. Globo, banconota, carta,
dollaro, fulmine.
LA TINTA RESTA MA LEGGERA, una per sezione (scelta di Andrea contro la
prima proposta, che le voleva tutte neutre): fondo tenue e tratto del
suo «text», il tono fatto apposta per leggersi sui fondi tenui. Con una
linea da un pixel e mezzo il colore si vede e non grida.
⚠️ LE CLASSI STANNO NEL CSS E NON IN RIGA, e non è pulizia: uno di quei
token porta nel nome una parola che la sentinella di questo foglio
vieta, e scritta dentro il render la farebbe rossa. Il colore passa da
`.ico-valuta`, `.ico-importo`, `.ico-metodi`, `.ico-prezzo`,
`.ico-sats` — che è anche il posto dove le cinque coppie si leggono una
sotto l'altra.
E IL DOLLARO È IL GLIFO DEL CARATTERE DI CASA (scelta di Andrea: «il
simbolo del dollaro come c'è adesso ma più elegante»). Il primo giro
l'aveva DISEGNATO a tratto come le altre quattro, e a schermo si vedeva
il perché non va: il «$» è un segno TIPOGRAFICO — ha un'asta, una
larghezza e un peso che il font ha già risolto — e ridisegnarlo
significa rifare peggio una cosa fatta. Le altre quattro restano
disegni per la ragione opposta: un globo, una banconota, una carta e un
fulmine il carattere non li ha.
STA NELLO STESSO TONDO e ne prende il colore, ma non la misura: un
glifo e un tratto da un pixel e mezzo non pesano uguale a parità di
altezza, quindi il «$» si accorda all'occhio con le vicine. Il
`line-height:1` toglie l'interlinea, che dentro un `place-items:center`
lo lascerebbe sotto il centro — misurato a zero su tutt'e due gli
assi.

5) LA BARRA DEL PREMIO SI ACCENDE FINO AL PALLINO. Prima era tutta
arancione e a dire «dove sono» c'era solo il pallino; adesso è accesa
dal capo sinistro fino a lui e spenta oltre. Il tratteggio resta —
sopra tutt'e due i lati, che è il motivo per cui lo spento non può
essere chiaro quanto la carta: i tratti bianchi ci sparirebbero
dentro. Da qui il token `--premio-spento`, coi suoi due valori.
⚠️ IL CONFINE NON È LA PERCENTUALE NUDA, ed è il dettaglio che fa la
differenza proprio dove si guarda: il pallino è largo venti pixel e il
suo centro corre dentro `larghezza − 20`, quindi il conto è
`frazione × (100% − 20px) + 10px`. Con la percentuale nuda il colore e
il pallino si scollano ai due estremi — cioè a −10% e a +10%, che sono
le due posizioni in cui uno prova la barra per capire come funziona.
Il conto vive in `pienoPremioP2P`, PURA, e si fa girare: ai due capi,
al centro, e coi numeri fuori fascia che si tosano invece di uscire dal
binario.

COLLAUDATI: **8861 prove verdi, 0 rosse** (+20 sulle 8841 del giro
prima) e **11 MUTAZIONI, 11 UCCISE**: la valuta che torna una bandiera,
un'icona che torna emoji, la tinta che sparisce dal CSS, le icone che
perdono il tratto della nav, il foglio che torna ancorato in basso, lo
svelare che lascia scivolare la pagina, l'apertura che non richiude più
il secondo campo, il riempimento che non si riscrive al movimento, che
parte muto, che perde la correzione del pallino, e i due strati del
binario rovesciati.
⚠️ QUELL'ULTIMA HA UNA PROVA NATA APPOSTA, e senza sarebbe passata: le
due righe che guardano il tratteggio e il colore restano verdi anche a
strati invertiti, perché ci sono tutt'e due — a cambiare è solo
l'ORDINE, e con `background-size` posizionale le misure finirebbero
sullo strato sbagliato. Si guarda la CUCITURA fra i due, non i due. È
la stessa famiglia delle tre prove molli del giro prima.
GIRO DAL VIVO col server vero, chiaro e scuro: il foglio si apre con
un campo solo, le cinque icone a tratto nelle loro tinte tenui, il
binario che si riempie a −4% e a +6% col pallino esattamente sul
confine, e il foglio che a `--tastiera` 300px resta col bordo alto a
zero.

Il «$», la barra dal centro e la pillola che si tocca (set 2026, tre
ritocchi arrivati in coda ai cinque del giorno, guardati dal vivo da
Andrea). Due EMENDANO decisioni scritte poche ore prima, ed è la parte
da leggere: erano giuste sulla carta e sbagliate a schermo.

1) IL «$» È IL GLIFO DEL CARATTERE DI CASA, non un disegno. Il giro
prima l'aveva disegnato a tratto come le altre quattro icone — coerente
per costruzione — e a schermo si vede il perché non regge: il dollaro è
un segno TIPOGRAFICO, ha un'asta, una larghezza e un peso che il font ha
già risolto, e ridisegnarlo significa rifare peggio una cosa fatta. Le
altre quattro restano disegni per la ragione opposta: un globo, una
banconota, una carta e un fulmine il carattere non li ha.
STA NELLO STESSO TONDO e ne prende il colore, ma NON la misura: un
glifo e un tratto da un pixel e mezzo non pesano uguale a parità di
altezza, quindi il «$» si accorda all'occhio con le vicine. Il
`line-height:1` toglie l'interlinea, che dentro un `place-items:center`
lo lascerebbe sotto il centro — misurato a zero su tutt'e due gli assi.
LA REGOLA CHE NE RESTA: un'icona si disegna quando il carattere non ce
l'ha. Se ce l'ha, il disegno è una copia peggiore.

2) ⚠️ LA BARRA DEL PREMIO SI MISURA DAL CENTRO, e questo EMENDA il giro
prima, dove si accendeva dal capo sinistro fino al pallino. Riempita dal
capo la barra diceva QUANTO ci si era spostati e non DA CHE PARTE — e a
zero, con mezza barra già accesa, sembrava una scelta già fatta invece
del punto di partenza. Adesso a zero è tutta spenta, e da lì si accende
SOLO il tratto fra il centro e il pallino: VERDE a destra, dove il
premio è un sovrapprezzo, ROSSO a sinistra, dove è uno sconto. Il
tratteggio resta su tutt'e due i lati.
IL PALLINO VESTE LA STESSA TINTA (decisione mia, dichiarata): con la
barra che parla verde e rosso, un pallino arancio sarebbe stato il terzo
colore in dieci pixel. A fermo resta il grigio dello spento, che è il
modo giusto di dire «di qui non ci si è ancora mossi».
UN GIUDICE SOLO PER TUTTE E TRE LE COSE che dipendono dal segno —
`fasciaPremioP2P`, pura: i due bordi della fascia, la sua tinta, e la
classe che colora il numero nella pillola. Con due giudici sarebbe
bastato un ritocco a uno per far raccontare due segni diversi sulla
stessa cifra.

3) LA PILLOLA DEL PREMIO SI TOCCA. Prima a scrivere il valore a mano
portava solo il «Modifica» qui sotto, e nessuno tocca una parolina
grigia quando ha una pillola grossa davanti. Adesso la pillola È il
bottone, e a dirlo c'è la MATITA nel tondino bianco agganciata
all'angolo in basso a destra, che SPORGE dal bordo — è lo sporgere che
la fa leggere come un'aggiunta invece che come un disegno stampato
dentro. «Modifica» resta sotto: la stessa porta detta a parole, per chi
la matita non la riconosce.
IL FONDO È NEUTRO E IL COLORE CE L'HA IL NUMERO (richiesta di Andrea):
verde sopra il mercato, rosso sotto, neutro a zero, in pari con la
barra. Un fondo pieno — arancio prima, viola nella proposta — faceva
della pillola la cosa più accesa della sezione, davanti alla barra che è
proprio quella da guardare; e non avrebbe potuto dire il segno, perché
il testo bianco sopra deve restare leggibile su tutt'e due le tinte.
⚠️ LA CLASSE DEL COLORE STA SULLA PILLOLA E LA CIFRA IN UN FIGLIO SUO,
ed è una riga che sembra pignoleria e non lo è: se fossero lo stesso
nodo, riscrivere il numero a ogni movimento del cursore porterebbe via
la matita agganciata all'angolo. C'è la prova che lo inchioda.
IL TONDINO È BIANCO NEI DUE TEMI e la matita scura: un tondino che
seguisse il tema sparirebbe dentro la pillola di giorno, che è bianca
anche lei. A staccarlo dal fondo chiaro c'è l'OMBRA e non un bordo — un
bordo intorno a venti pixel diventa un anello e si vede più della
matita.
E SEI PIXEL D'ARIA IN PIÙ sotto la pillola, trovati guardando: la
matita che sporge toccava la «M» di «Modifica».

4) I DUE TAB DELLA TESTATA PESANO UN GRADINO SOTTO (ritocco di
Andrea): da 800 a 700. Sono la cosa più grande della testata, e a peso
pieno spingevano più del logo che gli sta in mezzo. È un peso VERO e non
un grassetto tirato dal browser — Baloo 2 ha il file del 700 come quello
dell'800 — e c'è la riga che lo sorveglia, insieme alla presenza di quel
`@font-face`: senza il file, «700» diventerebbe una finta.

COLLAUDATI: **8878 prove verdi, 0 rosse** (+17 sulle 8861 del giro
prima) e **13 MUTAZIONI, 13 UCCISE**: il «$» che torna un disegno, il
glifo che perde la sua misura, il ramo del glifo che passa dopo quello
del disegno, la fascia che riparte dal capo, che non si ferma al
centro, la tinta che non guarda più il segno, il numero che non cambia
colore, la cifra che torna sulla pillola portando via la matita, la
pillola che torna un'etichetta che non si tocca, che torna col fondo
pieno, la matita che non sporge, il tondino che segue il tema invece di
restare bianco, e il pallino che torna arancio.
GIRO DAL VIVO col server vero, chiaro e scuro: a 0 la barra è tutta
spenta col pallino grigio, a −6% il tratto fra centro e pallino è rosso
col numero rosso, a +7% è verde col numero verde, e il «$» viola siede
centrato nel suo tondo.

Il filtro del libro (set 2026, richiesta di Andrea sul modello di
quello di Mostro). Sotto i tab c'era una riga di servizio — «3 offerte
di chi vende sats» — che diceva un numero e basta. Al suo posto una
PILLOLA col simbolo dell'imbuto: stesso numero, e in più la porta per
restringere. Il lato non si scrive più: lo dice il tab acceso due
centimetri più su, e ripeterlo era la seconda copia della stessa
verità.

LE QUATTRO LEVE: valute (per ora EUR), metodi (le sei voci del
vocabolario chiuso, a scelta multipla), premio/sconto da −10% a +10% e
reputazione da 0 a 5 stelle. Le prime due sono pillole come nel foglio
«Pubblica»; le altre due sono cursori a DUE pallini.

⚠️ LA REPUTAZIONE È QUELLA DEL COORDINATORE e non le stelline del
mercatino, ed è una decisione presa prima di scrivere una riga
(domanda ad Andrea, risposta sua). Il tag `rating` sta DENTRO ogni
38383, quindi ce l'hanno tutti gli ordini — anche quelli nati sugli
altri client. Le stelline di casa le abbiamo solo per chi si è
registrato da noi, e solo da loggati: un filtro su quelle avrebbe
svuotato il libro al primo mezzo punto, e la colpa sarebbe sembrata del
filtro invece che del dato mancante.
E CHI NON HA ANCORA VOTI passa solo col minimo a ZERO. Media 0 con zero
voti non vuol dire «scarso», vuol dire «non si sa» — ma chi chiede
almeno una stella sta chiedendo una PROVA, e «non si sa» non lo è. È
una scelta e non una conseguenza, quindi ha una riga sua nel foglio:
senza, un libro che si svuota a mezzo punto sembra un guasto.

⚠️ IL METODO SI CONFRONTA PER CONTENIMENTO, non per uguaglianza, ed è
la riga che rende il filtro utile invece che pedante: sul libro
arrivano i metodi scritti dagli ALTRI client, e sono testo libero —
«SEPA Instant», «Bonifico SEPA», «sepa». Chiedere «SEPA» deve prenderli
tutti; chiedere «SEPA Instant» solo chi lo dice. Uguaglianza secca
avrebbe filtrato via mezzo libro senza che si capisse perché. Più
metodi scelti valgono in OR: basta che l'ordine ne offra uno.

IL CONTEGGIO NELLA PILLOLA È QUELLO FILTRATO, sempre. Un numero che
contasse il libro intero mentre a schermo se ne vedono tre sarebbe la
bugia più facile da scrivere e la più difficile da notare. E la pillola
si VESTE del colore del lato quando il filtro restringe davvero: è
l'unico modo di accorgersi che il libro non è tutto il libro.
LO STATO VUOTO DICE QUALE DEI DUE VUOTI È: «non c'è niente» e «il tuo
filtro non lascia passare niente» sono due cose diverse, e la seconda ha
una strada d'uscita da offrire — il bottone che toglie il filtro.

SI FILTRA SOLO IL LIBRO, mai «I miei scambi» (richiesta di Andrea, e
c'è la sentinella): quelli sono roba mia, e nasconderne uno perché il
premio non rientra vorrebbe dire perdere di vista uno scambio IN CORSO.
E LO STATO È UNO SOLO per tutt'e due i tab: chi restringe a «SEPA»
vuole SEPA di qua e di là, e un filtro che si azzera cambiando lato
sarebbe una sorpresa a ogni tocco.

SI LAVORA SU UNA BOZZA e non sul filtro vivo: chi tocca i cursori deve
poter cambiare idea, e «Applica» dev'essere il momento in cui il libro
si muove. Senza la bozza il libro si riscriverebbe sotto le dita a ogni
scatto, e «Cancella» non avrebbe più niente da annullare.
⚠️ E LE DUE LISTE SI COPIANO IN TUTT'E DUE I VERSI (`slice()`): senza,
la bozza e il filtro vivo condividerebbero gli array, e toccare una
pillola nel foglio filtrerebbe il libro PRIMA di «Applica» — cioè
proprio la cosa che la bozza esiste per evitare.
«CANCELLA» AZZERA E APPLICA in un gesto solo: uno che svuotasse i campi
lasciando il libro filtrato chiederebbe un secondo tocco per fare la
cosa già chiesta. È anche il bottone dello stato vuoto, dove è l'unica
strada d'uscita.

IL CURSORE A DUE PALLINI NON ESISTE IN HTML: sono DUE
`input[type=range]` SOVRAPPOSTI sopra un binario disegnato da un div. I
due campi non ricevono il dito (`pointer-events:none`) — lo ricevono i
soli PALLINI — o quello sopra si prenderebbe tutti i tocchi e l'altro
non si muoverebbe mai. I due bordi arrivano da `--da` e `--a`, con la
STESSA correzione del pollice del premio (`bordoPremioP2P`): sarebbe
assurdo che i pallini si scollassero dal colore qui e no là. E i due
non si scavalcano: chi spinge il minimo oltre il massimo lo trova fermo
lì, invece di vedere la fascia rovesciarsi.
IL PEZZO È UNO SOLO per tutt'e due i cursori del foglio — premio e
reputazione — così non possono divergere.

⚠️ E LA TEMPORAL DEAD ZONE HA COLPITO DI NUOVO, alla seconda riga
scritta: `P2P_FILTRO_VUOTO` era una `const` che leggeva
`P2P_PREMIO_MAX`, la quale nasce diciassettemila righe più sotto col
foglio «Pubblica». Stessa trappola del catalogo delle valute di ieri, e
a bocciarla di nuovo è stata la prova che fa girare ogni blocco
`<script>` fino in fondo. È diventata una FUNZIONE, che si issa e legge
a pagina viva — e la cura ha portato con sé un secondo difetto che non
avevo visto: un oggetto costante con dentro due ARRAY è una trappola,
perché `Object.assign({}, VUOTO)` copia i RIFERIMENTI, quindi il primo
`push` su una copia avrebbe scritto dentro la costante e il «vuoto» non
sarebbe più stato vuoto per nessuno. Una funzione ne fa uno nuovo ogni
volta.
IL FILTRO SPENTO È `null` e non un oggetto pieno di valori neutri:
così «non c'è filtro» è una cosa sola da controllare, e il giudice che
decide se un ordine passa lo dice in una riga.

COLLAUDATI: **8899 prove verdi, 0 rosse** (+19 sulle 8880 del giro
prima) e **13 MUTAZIONI**: il conteggio che conta il libro intero, le
card che si mostrano tutte, la pillola che non si veste mai, lo stato
vuoto che non distingue i due vuoti, «I miei scambi» che si filtrano
anche loro, il metodo per uguaglianza secca, chi non ha voti che passa
sempre, la fascia del premio che esclude gli estremi, la bozza che
condivide le liste, «Applica» che non ridisegna, i due pallini che si
scavalcano, il foglio che non si chiude col censimento — più il tondino
della matita, che al giro prima era sopravvissuto.
⚠️ QUEL TONDINO È LA STESSA LEZIONE DI IERI, ed è la terza volta in due
giorni: la prova cercava `border-radius:999px;background:#fff;` in
TUTTO il foglio di stile, e quella riga sta anche nel pomello della
leva del tipo di prezzo, dieci righe più su. Rispondeva per il vicino.
Adesso il blocco `.p2p-premio-matita` si RITAGLIA prima di guardarci
dentro. Stessa cura per il pallino in tinta, che col cursore doppio del
filtro esiste ora in tre posti: si conta dentro il blocco del premio,
non nel foglio intero.
GIRO DAL VIVO col server vero, chiaro e scuro, su un libro di tre
ordini: la pillola dice «3 offerte», «SEPA» la porta a 2 (prende anche
«SEPA Instant») e la veste di verde, e col minimo di reputazione a 4
resta la sola offerta da 4,6 stelle. I due pallini si muovono e le
etichette li seguono.


IL CONTO SUL DISPOSITIVO (10 set 2026, dal campo di Andrea: due account
Telegram sullo stesso telefono, e il P2P che li mischiava).
IL SINTOMO: il secondo account (aggiunto a `P2P_PROVA_IDS`) entra nella
Mini App, la home mostra il SUO profilo — e il P2P mostra quello del
primo: i suoi ordini «miei», la sua foto nel profilo di scambio, e
l'ordine appena pubblicato col secondo esce sulla card col volto del
primo. Cache e dati della Mini App svuotati: resta il primo.
LA DIAGNOSI STA IN TRE RIGHE, e nessuna è nel server. 1) Telegram ha
UNA WebView per tutti gli account che scambia, e il localStorage è per
ORIGINE: `barattolo.store` è lo stesso per tutt'e due. 2) Il mazzo
viveva sotto `barattolo_mostro` senza nessun nome sopra, e
l'invariante di tutto il cantiere — «un profilo che c'è non si tocca»
— faceva il resto: `assicuraMazzo` e `adottaProfiloContoP2P` trovavano
un mazzo e lo restituivano, senza chiedersi di chi fosse. 3) Il volto
è la conseguenza: la restore fatta col mazzo del primo consegna gli
ordini del primo, `registraOrdiniP2P` li intesta alla SESSIONE, e
l'ordine nuovo — pubblicato con le trade key del primo — lo intesta
chi fa la restore per primo (INSERT OR IGNORE: chi arriva primo
tiene). E PERCHÉ SVUOTARE LA CACHE NON BASTAVA: `sincronizzaMazzo`,
nel caso «locale c'è + cloud vuoto = si carica» (la migrazione del
cantiere della nuvola), aveva già scritto il mazzo del primo nel
CloudStorage del SECONDO — che è per utente — e da lì l'adozione lo
riprendeva a ogni ingresso, cache o non cache.
I TRE SOSPETTI DI ANDREA, riletti: il primo era giusto per intero; il
secondo no — `/api/p2p/seme` risponde al tg_id dell'initData corrente,
che Telegram inietta al lancio per l'account attivo, e nessuna sessione
stantia c'entra; il terzo a metà — la registrazione usava la sessione
giusta, ma su chiavi sbagliate, quindi la faccia seguiva le chiavi.
LA CURA HA TRE PEZZI, e servono tutti e tre (il perché di ognuno sta
nel commento «IL CONTO SUL DISPOSITIVO» in miniapp.html). 1) OGNI
CHIAVE DEL P2P PORTA IL tg_id NEL NOME (`chiaveP2P`):
`barattolo_mostro@111` e non `barattolo_mostro`, e così scambi, lapidi
e recapiti. Il cambio di conto è il cambio di un suffisso, e due
account sullo stesso dispositivo non si vedono per costruzione. Le
chiavi di ieri, nude, passano al PRIMO conto che entra e solo su un
posto vuoto (`allineaContoP2P`, chiamata da `avvia` appena `/api/me`
ha detto chi sei): chi le ha scritte non si sa più, e il primo che
entra è la scommessa più onesta — il pezzo 2 corregge il caso in cui
sia sbagliata. 2) IL MAZZO DEL CONTO SA DI CHI È: il profilo derivato
dal seme porta dentro `conto`, il tg_id da cui nasce, e un mazzo
'conto' con un tg_id diverso dal mio è di un altro — giudizio
sincrono, senza rete. Quelli scritti PRIMA di oggi il campo non ce
l'hanno, e si chiede il seme UNA volta (`verificaContoP2P`): uguale,
si timbra e non si richiede più; diverso, si mette da parte; 409 o
rete, «non lo so» per la sessione e non si tocca niente. 3) UN MAZZO
DI UN ALTRO SI METTE DA PARTE, MAI SI BUTTA (`parcheggiaMazzoAltruiP2P`):
le quattro chiavi finiscono sotto `@altrui:<pub>` e nessuno le rilegge
— la regola delle lapidi. La copia nel cloud, se è quella, se ne va:
un profilo 'conto' non è mai l'unica copia (rinasce dal suo account,
l'indice dal pavimento del server), e quel cloud è MIO anche se il
profilo no.
E TRE RIGHE ATTORNO: il gate dell'adozione in `renderP2P` vuole
`myTgId` anche DENTRO Telegram (senza conto non c'è un posto in cui
adottare: si scriverebbe nel nome di ieri, che il conto in arrivo poi
assorbe); un mazzo adottato dal cloud che è ancora da verificare non
si registra al server finché la verifica non ha detto che è mio (o la
chiave dell'altro finirebbe intestata a me in `p2p_indice`); e
`azzeraSessioneP2P` butta bandierine, pavimento, lista dei miei e conto
delle chiavi quando il conto cambia a sessione viva — che in
produzione non succede (Telegram riapre la Mini App), ma nel collaudo
il cambio di identità passa da `setCollaudo` → `avvia`.
L'ORDINE DEL RENDER È LA RIGA CHE COSTA: il mazzo estraneo si mette da
parte in SINCRONO, prima che una restore o una registrazione partano
con le sue chiavi; quello di ieri, finché la verifica non ha risposto,
non si registra e non chiede la restore — direbbero al server «questi
ordini sono miei» su chiavi forse altrui, che è precisamente il volto
sbagliato. E `assicuraMazzo` lo verifica PRIMA di firmarci sopra.
LE STRADE SCARTATE, coi perché. a) Buttare via il mazzo altrui: la
chiave sì è rederivabile, ma scambi in corso, lapidi e recapiti no —
la regola delle lapidi vale anche per lo stato di un altro. b) Un
ripescaggio automatico del parcheggio quando il vero padrone entra
(per pub): venti righe in più per un caso che nasce solo da un
dispositivo contaminato PRIMA di oggi dove entra prima il conto
sbagliato; Andrea ha chiesto «si scarta», e il parcheggio è la lapide
che rispetta tutt'e due. c) Richiedere il seme a OGNI ingresso per
ogni mazzo 'conto' (la sentinella che la voce «Il seme senza commit»
aveva proposto): una POST per sessione per tutti, e soprattutto non
distingue «di un altro» da «mio col sale cambiato» — il timbro `conto`
rende il primo caso sincrono e lascia il secondo al suo cantiere.
d) Dare il suffisso anche a NWC e bunker: sono dell'identità Nostr,
non del P2P, e fuori dal perimetro di questo giro.
IL CASO CHE RESTA AMBIGUO, dichiarato: un mazzo 'conto' di ieri che
diverge dal seme può essere di un altro (questo difetto) o MIO con un
sale cambiato (ripristino da un backup vecchio). Si mette da parte in
tutt'e due i casi — mai distrutto — e il secondo caso resta il
cantiere del foglio del conflitto, che questa voce non apre.
COSA SUCCEDE SUL TELEFONO DI ANDREA al primo ingresso dopo il deploy,
nei due ordini possibili. Se entra PRIMA il primo account: le chiavi
nude diventano sue, tutto giusto; poi il secondo trova il suo nome
vuoto, il suo cloud gli dà il mazzo del primo, la verifica col seme
dice «non tuo», parcheggio, cloud ripulito, e nasce il SUO profilo dal
seme. Se entra PRIMA il secondo: le chiavi nude diventano sue per un
istante, la verifica col seme le smentisce, parcheggio sotto
`@altrui:`, cloud ripulito, profilo suo; poi il primo entra a mani
vuote — il suo cloud ha il suo mazzo e lo adotta, e gli ordini
pendenti tornano dalla restore (le sue righe locali di ieri restano
nel parcheggio: è il limite della strada b). In tutt'e due i casi i
due account non si vedono più.
E QUEL CHE IL SERVER TIENE DI IERI: l'ordine di prova pubblicato col
secondo account porta le trade key del PRIMO, quindi per il
coordinator è del primo — dal secondo non si vede più, e si ritira dal
primo (o si lascia scadere). In `p2p_indice` resta una riga (pub del
primo, tg_id del secondo) inerte, e in `p2p_ordini` quel che la prima
restore ha intestato: righe che non mordono e non si toccano.
COLLAUDATI: **8954 prove verdi, 0 rosse** (+55 sulle 8899 del giro
prima): il banco del mazzo fa girare i sei casi — il cambio di conto
come cambio di suffisso, la migrazione delle chiavi di ieri solo sul
vuoto, i due giudici, il timbro dal seme, il 409 che non tocca, e IL
CASO DEL CAMPO per intero (mazzo del primo in locale E nel cloud del
secondo, seme del secondo: parcheggio, cloud ripulito, gesto che torna
col profilo giusto e nessuna fetch che porti la chiave dell'altro);
la nuvola ha il giro «altrui nel cloud» e quello del da-verificare che
non si registra; e una sezione nuova, «il conto sul dispositivo»,
tiene ferme le righe una per una. **16 MUTAZIONI, 16 uccise**: chiave
letta nuda, cambio che non azzera, render che non parcheggia, gesto
che non verifica, cloud che adotta l'altrui, derivato senza conto,
parcheggio che svuota un cloud non suo, 409 che timbra, bandierina non
alzata, migrazione che sovrascrive o che lascia la chiave nuda,
giudice senza origine, testo che perde il conto, render che registra
il da-verificare, chiaveP2P senza conto, adozione dal cloud che
registra prima di verificare.
LA LEZIONE DEL BANCO: quattro di quelle mutazioni la prima stesura le
«uccideva» con un CRASH — `rp.index(riga)` su una riga tolta alza
ValueError e la sezione muore intera, rosso in CI ma senza dire quale
riga manca. Le catene di posizione si scrivono con `find`, che a riga
assente vale -1 e rende la catena falsa da sola.
DA GUARDARE SUL CAMPO: la sequenza dei due account sul telefono
(quale entra prima, e che il secondo veda solo il suo), e che l'ordine
di ieri sparisca dal secondo e resti governabile dal primo.

IL SECONDO GIRO DAL CAMPO, la sera stessa (10 set 2026): ritirato il
vecchio ordine dal primo account, il secondo ne pubblica uno nuovo — e
NON lo vede come suo: niente marcatura, niente striscia, card senza
volto, nessun ritiro possibile. I sospetti di Andrea erano tre (mazzo
nato e non salvato, registrazione mancata, restore con un'identità
diversa) e la risposta è una riga sola: `8711624959 | 0` fa
`121690367`. I tg_id nuovi di Telegram stanno SOPRA 2^31, e il campo
`conto` passava da un bitwise in quattro punti — i due giudici, la
serializzazione e la rilettura. Il mazzo appena derivato si
serializzava col conto troncato, al render dopo si rileggeva «di un
altro» e finiva nel parcheggio; l'adozione lo riderivava dal seme —
stessa sk, indice 0 — e il render dopo lo parcheggiava di nuovo, per
sempre. In mezzo a un giro Andrea ha pubblicato: il gesto passa da
`assicuraMazzo`, che il mazzo timbrato lo prende al volo, quindi
l'ordine è nato con la sk GIUSTA (quella del seme del secondo) e la
riga locale è finita nel parcheggio `@altrui:<pub>` al render
successivo, dove è rimasta intatta (i giri dopo trovavano il nome vivo
vuoto e non sovrascrivevano). La restore non partiva mai — il
parcheggio è sincrono e sta prima — e `registraOrdiniP2P` nemmeno:
ecco la card senza volto. IL BANCO NON LO VEDEVA perché usava 111 e
222, e la mutazione «tronca il conto» non esisteva: le prove sono
esatte solo sui numeri che qualcuno ha pensato di provare.
LA CURA: `numeroConto` (Number, mai bitwise) nei quattro punti, una
sentinella che non ammette `| 0` sul conto in tutto il blocco del
mazzo, e il banco con il tg_id vero. E LA STRADA b) È RIENTRATA, con
un motivo nuovo: il difetto aveva parcheggiato IL MAZZO GIUSTO col suo
ordine, e la prova che un parcheggio è del conto che entra è la più
forte che esista — la STESSA sk. `riprendiParcheggioP2P`, chiamata dal
render prima della registrazione: il mazzo riprende l'indice più alto
(mai riusare una trade key), scambi, lapidi e recapiti tornano vivi
(su un nome già occupato vince quel che c'è, che è il più recente), e
il parcheggio si svuota. Una sk diversa non si tocca. È così che
l'ordine del secondo account torna: al primo ingresso dopo il deploy
il mazzo troncato di ieri va nel parcheggio ancora una volta, quello
nuovo nasce col conto intero, trova nel parcheggio la sua stessa sk e
si riprende riga e indice; la restore parte, l'ordine è «mio», si
registra il volto, e il ritiro passa dal giro di sempre.
COLLAUDATI: **8964 prove verdi, 0 rosse** (+10) e **20 MUTAZIONI, 20
uccise** (le sedici di stamattina più: il conto che torna a un bitwise
nel testo, il giudice che tronca, il render che non riprende il
parcheggio, la ripresa che prende una sk diversa).
LA LEZIONE, che vale oltre il P2P: un id di Telegram non è un
`int32`, e `| 0` non è «arrotonda»: è «tronca a 32 bit e non dirlo».
Ogni volta che un numero arriva dal server e serve intero, `Number`.

IL TERZO GIRO DAL CAMPO, il volto in ritardo (10 set 2026): la
sequenza primo→secondo→primo funziona, l'ordine pubblicato col secondo
è subito «mio» — ma la card resta SENZA foto, e la foto compare solo
dopo circa tre chiusure e riaperture. È una corsa in due tempi. La
card chiede il volto (`chiediFacceP2P`) appena il libro la mostra; il
server non sa ancora di chi è l'ordine, perché l'intestazione
(`registraOrdiniP2P`) partiva SOLO con la restore, cioè alla sessione
dopo — «chi pubblica adesso ha il suo giro al prossimo ingresso», che
era vero e sbagliato insieme; e `p2pFacceChieste` ricorda «già
chiesto» per tutta la sessione, quindi quel no diventa definitivo.
Alla sessione dopo la restore intesta, ma la domanda dei volti del
render parte PRIMA che l'intestazione sia atterrata: un altro no, e
un'altra sessione. Ecco le tre aperture.
LA CURA È UNA FUNZIONE SOLA, `intestaOrdiniP2P`: registra, aspetta
l'ok del server (e una domanda dei volti eventualmente in volo, che a
giro occupato `chiediFacceP2P` rifiuta), dimentica il «già chiesto»
di quegli id, richiede il volto e ridisegna. Due chiamanti: la
risposta del coordinatore che assegna l'id vero a un ordine appena
pubblicato (in `applicaMessaggioP2P`, subito dopo il rinome — l'id
provvisorio non si intesta, cambierebbe nome), e la restore, che ora
passa dalla stessa strada invece di registrare e basta.
COLLAUDATI: **8976 prove verdi, 0 rosse** (+12) e **24 MUTAZIONI, 24
uccise** (le venti di prima più: l'intestazione che non dimentica il
«già chiesto», l'id vero che non intesta, la restore che torna a
registrare senza richiedere, l'intestazione che richiede senza
aspettare il server). Il banco del volto fa girare la corsa vera:
chiesto prima dell'intestazione è un no che da solo non si richiede,
l'intestazione lo porta con un ridisegno, prima l'ordine al server e
poi la domanda, il provvisorio resta fuori, e col server che dice no
non si chiede niente.

L'EURO È UN INTERO (10 set 2026, dal campo di Andrea: nel foglio
Pubblica «5,5 €» usciva un ordine da 5 €).
È UNA REGOLA DEL PROTOCOLLO e non del foglio — `fiat_amount` viaggia
intero, e nemmeno Mostro prende i decimali — ma il foglio la applicava
TRONCANDO IN SILENZIO, con `Math.floor(Number(...))`, negli stessi tre
posti in cui si scrive una cifra in euro: `valeNuovoOrdineP2P` (il
giudice del bottone), `ordineDaCampiP2P` (quel che si SPEDISCE) e
`quantoValeP2P` (l'importo scelto dentro un intervallo). Chi scrive
5,5 vede partire 5 e lo scopre dal libro, che è il modo più caro di
saperlo.
MISURATO SUI BYTE PRIMA DI SCRIVERE LA CURA, ed è lì che il difetto si
è rivelato più largo di come si presentava. Fatte girare le funzioni
vere: `'5.5'` → `"fiat_amount":5` (il troncamento raccontato), `'0.9'`
→ `0`, e **`'5,5'` → `"fiat_amount":null`** — perché
`Math.floor(Number('5,5'))` non è 5, è **NaN**, e `JSON.stringify`
scrive `null`. Un `null` dove il coordinatore aspetta un i64 è una
busta che non sa leggere, e a una busta storta Mostro non risponde un
errore: TACE. Nel browser quella strada era tappata per caso (vedi
sotto), ma esisteva.
⚠️ LA VIRGOLA ARRIVA VUOTA, ed è il pezzo che leggendo il codice non
si vede: un `<input type="number">` con dentro «5,5» risponde
`value === ''` e alza `validity.badInput`. Quindi «non ho scritto
niente» e «ho scritto una virgola» arrivavano al giudice IDENTICI, e
il foglio rispondeva «Scrivi l'importo in euro» a chi l'importo
l'aveva scritto — un vicolo cieco che manda a indovinare. È anche il
motivo per cui il difetto si vedeva col punto e non con la virgola.
LA CURA NON È ACCETTARE I DECIMALI, È DIRLO. Un giudice PURO e uno
solo per i tre posti (`euroInteroP2P`): solo cifre, e `Number` non
basta come giudice — accetta `'5.5'`, `'5e3'` e `' 5 '`, che qui sono
tutti storti. Un lettore solo per i campi (`testoCampoNumero`) che
traduce il badInput in un sentinella (la virgola, che un campo
numerico non può mai produrre) così il giudice lo legge storto. La
frase «Solo importi interi in euro» vive in una costante, che tre
copie sono tre frasi che un giorno divergono. E i tre campi passano da
`inputmode="numeric"` (era `decimal`, cioè una tastiera che OFFRIVA la
virgola) tenendo `step="1"`: gli altri `decimal` del file sono prezzi
del mercatino, dove i decimali sono legittimi, e per questo la
sentinella guarda i tre id e non il conto del file.
FAIL-CLOSED SUL FILO: a cifra storta l'euro vale ZERO e non «quel che
ci somiglia». Un ordine da 0 il coordinatore lo rifiuta; uno da 5 al
posto di 5,5 lo ESEGUE, ed è quello che nessuno voleva. E
`ordineDaCampiP2P` legge dallo stesso giudice del bottone: quel che si
vede acceso e quel che parte non possono divergere — è esattamente
così che «5,5» diventava 5.
L'ORDINE DEI MESSAGGI È PARTE DELLA CURA: la forma si giudica PRIMA
del vuoto e PRIMA della fascia. A «5,5» dire «scrivi l'importo» (o
«scegli una cifra fra 20 e 100») manda a cercare l'errore dove non c'è.
COLLAUDATI: **8993 prove verdi, 0 rosse** sull'albero che porta anche
la firma del canale arrivata da Alan mentre questo giro era aperto (da
sola questa cura fa +14: 8976 → 8990) e **12 MUTAZIONI, 12
uccise**: quel che si spedisce che torna a troncare, il giudice che
accetta i decimali, il bottone che parla del vuoto prima della forma,
il lettore che ignora il badInput, la presa che torna a troncare, i
tre campi che tornano a offrire la virgola, il foglio e la presa che
leggono col solo `value`, il giudice che si fida di `Number`, e la
frase che si sdoppia.
⚠️ E LA TORTURA HA TROVATO UNA PROVA CHE RISPONDEVA PER IL VICINO, la
terza volta che succede in questo file: la sentinella dei campi
affettava `id="p2pNuovoEuro"` più DUECENTO caratteri, e i due campi
dell'importo distano poche righe — la mutazione sul MASSIMO tingeva di
rosso anche la prova dell'IMPORTO. Adesso la fetta finisce dove
comincia il campo dopo. Una finestra a misura fissa è sempre una fetta
che un giorno sconfina.
RESTA FUORI, e si dice: i SATS a prezzo fisso passano ancora da
`Math.floor(Number(v.sats))` — stessa classe, campo diverso (e la sua
tastiera è già `numeric`, quindi la virgola lì non la offre nessuno).
Non è entrato in questo giro perché la richiesta era sull'euro e il
messaggio dice «in euro»: il giorno che si fa, il giudice è già
scritto e serve solo la sua frase.

⚠️ E QUELLA STRADA È STATA CAMBIATA LA SERA STESSA (decisione di
Andrea): «come Mostro — la virgola e il punto non si scrivono proprio
nel campo; il tasto non produce nulla, solo cifre entrano. Niente
messaggio da mostrare». Ed è meglio, per una ragione che vale oltre
questo campo: un messaggio è un errore da leggere, capire e
correggere, mentre un tasto che non produce niente non è un errore —
è un campo che si comporta come dice di comportarsi. Il messaggio
«Solo importi interi in euro» è uscito con la sua costante e con il
sentinella della virgola.
⚠️ E `type="number"` È USCITO CON LUI, che è la metà che non si vede:
un campo numerico NON SI PUÒ FILTRARE. Con dentro «5,5» risponde
`value === ''` e alza `validity.badInput`, quindi il testo vero non
arriva mai a chi vorrebbe ripulirlo; e `setSelectionRange` — che serve
a non far saltare il cursore in fondo a ogni tasto — su un `number`
ALZA. `type="text"` + `inputmode="numeric"` tiene la tastiera dei
numeri e rende il testo leggibile: è l'unico impianto in cui «solo
cifre entrano» si può davvero garantire. Il CSS non se ne accorge:
`.p2p-sez` stila già `input[type=text]` accanto a `input[type=number]`,
e il campo della presa è stilato per tag.
DUE PEZZI, e servono tutti e due. `soloCifreP2P` su `beforeinput`
arriva PRIMA che il carattere entri e lo ferma; `ripuliCifreP2P` è la
RETE per le strade che `beforeinput` non copre (un browser che non ce
l'ha, una composizione IME, un valore messo da fuori) e lì ripulisce
invece di rifiutare — il carattere è già dentro, e l'alternativa
sarebbe lasciarcelo — tenendo il cursore dov'era meno quel che gli è
stato tolto davanti.
UN INCOLLA STORTO SI RIFIUTA INTERO e non si ripulisce: da «1,5»
incollato uscirebbe «15», cioè dieci volte il numero voluto. Meglio
niente che un altro numero — è la stessa regola del troncamento muto,
letta dall'altro lato.
⚠️ MA BATTUTO A MANO «5,5» DIVENTA «55», e va detto perché è il prezzo
di questa strada: la virgola non entra, e la cifra dopo si attacca
alla prima. Misurato. È il comportamento di ogni campo solo-cifre, ed
è comunque meglio del difetto di partenza — il campo mostra SEMPRE
esattamente quel che partirà, mentre prima mostrava 5,5 e spediva 5.
Sul telefono la tastiera `numeric` non ha nemmeno il tasto della
virgola, quindi ci vuole una tastiera vera per arrivarci. Se un giorno
desse fastidio, la cura non è rimettere il messaggio: è la conferma
prima di pubblicare, che oggi non c'è.
E VALE ANCHE PER I SATS a prezzo fisso (stessa decisione, stesso
giro): stesso filtro sul campo e stesso giudice: `Math.floor` era lì
identico. Per questo il giudice non si chiama più `euroInteroP2P` — di
euro non sa niente, sa di interi — e il campo che restava fuori dalla
cura del mattino è rientrato.
NIENTE TETTO ALL'IMPORTO, chiesto esplicitamente da Andrea: la cifra
enorme resta possibile e resta fuori da questo giro.
COLLAUDATI: **8994 prove verdi, 0 rosse** (+1 netta: la cura toglie il
vecchio impianto mentre aggiunge il filtro) e **18 MUTAZIONI, 18
uccise** — il filtro che lascia passare tutto, che ferma anche le
cifre, che ripulisce l'incolla invece di rifiutarlo, che esplode senza
evento; la rete che non ripulisce e quella che manda il cursore in
fondo; il giudice che accetta i decimali e quello che si fida di
`Number`; il troncamento che torna sul filo, nel giudice, sui sats e
sulla presa; i quattro campi che tornano `number` o perdono il filtro;
il foglio e la presa che leggono senza la rete.

I QUATTRO RITOCCHI AL P2P (10 set 2026, chiesti da Andrea): la pillola
centrata sotto il logo, la testata attaccata in alto, l'aria nel foglio
Filtro col titolo raddrizzato, e i cursori che scorrono.
1) LA LINEA VERTICALE STA SOTTO IL LOGO, e non bastava centrare la
pillola: i due lati hanno larghezze diverse — «Filtro» da una parte, «N
offerte» dall'altra, e il numero cambia — quindi il divisorio cadrebbe
spostato, e di quanto lo deciderebbe il conteggio.
⚠️ E LO FA LA GRIGLIA, NON IL FLEX, che è la riga da non
«semplificare»: la prima stesura dava `flex:1 1 0` ai due lati
convinta che si pareggiassero, e MISURATA DAL VIVO si è rivelata
falsa — `flex` pareggia solo lo spazio AVANZATO, e con
`width:fit-content` non ne avanza: ogni lato prende la sua larghezza
naturale. A «1 offerta» il divisorio se ne andava di 11,45px. Due
colonne `1fr` di griglia, sotto dimensionamento intrinseco, valgono
invece entrambe quanto la più capiente. Rimisurato su 1, 2, 3, 10, 99
e 128 offerte: **scarto 0,00px in tutti e sei**.
2) TAB, LOGO E PILLOLA RESTANO IN ALTO, in UN blocco `sticky` solo e
non due impilati: con due il secondo vorrebbe un `top` pari
all'altezza del primo, cioè un numero da tenere in pari a mano che al
primo ritocco del logo diventa una sovrapposizione. La pillola esce da
`#p2pCorpo` e prende un contenitore suo (`#p2pTesta`) — è l'unica
ragione per cui ce l'ha. GLI AVVISI DEL LIBRO RESTANO COL LIBRO: la
pillola è un comando e vale sempre, «elenco parziale» racconta la
lettura di adesso e appeso in alto mangerebbe schermo per sempre.
⚠️ E IL MARGINE NEGATIVO È USCITO, misurato: con `margin-top:-6px` lo
sticky pinna il MARGINE a `top`, quindi il bordo resta 6px più in
basso e in cima avanza una fessura trasparente da cui si vedono
passare le card. Verificato dal vivo: da fermo il blocco sta a 62,8px,
scorrendo si incolla a **0** e le card gli passano sotto (la prima
card a −310 e a −1089), e a 2px dal tetto c'è il logo, non una card.
3) IL FOGLIO FILTRO: 9px d'aria sotto ogni titolo (solo in questo
foglio — la stessa classe vive in mezza app), e «Premio / Sconto»
diventa «Sconto / Premio», che è l'ordine dei due capi qui sotto —
sconto in rosso a sinistra, premio in verde a destra. Un titolo che
legge al contrario del cursore fa cercare il segno dalla parte
sbagliata.
4) ⚠️ I CURSORI «A SCATTI» NON ERANO IL PASSO, ed è la scoperta del
giro: `muoviDoppioP2P` chiamava `renderFiltroP2P`, che riscrive
`innerHTML` — cioè DISTRUGGE E RICREA i due `input[type=range]` a ogni
`oninput`. Il pallino che il dito sta tenendo sparisce a metà
trascinamento, il browser perde la presa, e per continuare bisogna
riafferrarlo. Cambiare `step` non avrebbe curato niente. È la lezione
del lightbox «a scatti», sullo stesso asse: quel che sembra lentezza è
quasi sempre qualcosa che si rifà da capo. Adesso si tocca solo quel
che cambia — le due variabili CSS della fascia e il testo dei due capi
— e i `min`/`max` si RILEGGONO dal campo invece di ribatterli. I due
capi hanno un giudice solo (`capiDoppioP2P`), usato dal disegno
iniziale E dal trascinamento: due formule direbbero due numeri diversi
mentre il dito si muove. Verificato dal vivo: **11 `input` di fila e
il nodo è sempre lo stesso**, i capi si aggiornano, la fascia si
sposta (0,5 a metà corsa, 0,6 sulla reputazione a 3/5) e i due pallini
continuano a non scavalcarsi.
COLLAUDATI: **9012 prove verdi, 0 rosse** (+18) e **15 MUTAZIONI, 15
uccise**.
⚠️ E IL BANCO DELLA TORTURA HA MENTITO DUE VOLTE, che è la parte da
tenere. PRIMA: la copia isolata non portava `assets/`, quindi
`prove_nav_p2p` esplodeva su un PNG mancante, il giro si FERMAVA lì —
le sezioni dopo non giravano affatto — e il banco usciva 1 su codice
INTATTO. Con la baseline a `exit 1` la mia condizione «rossa o exit
non zero» dichiarava uccise anche mutazioni mai provate: una l'aveva
già timbrata così. Il segno che l'ha smascherato è una riga sola:
**zero righe rosse ma exit 1**. Un banco che non parte non è un banco
che passa. SECONDA: smascherata quella, la sentinella del contenimento
è sopravvissuta davvero — guardava l'ORDINE dei due elementi, e
spostando la pillola FUORI dal blocco l'ordine resta identico. È la
trappola del contenitore sbagliato per la quinta volta in due giorni,
in una veste nuova: non «cerco in un posto troppo grande» ma «guardo
la proprietà sbagliata». La seconda stesura camminava sui tag per
contare le graffe, e nel banco rispondeva diverso da quel che
rispondeva a mano: buttata. Il markup qui è FISSO, e la forma si
guarda per quello che è.
DAL VIVO, e va detto com'è fatta la misura: la leva P2P è spenta in
locale, quindi lo stato del client è stato FORZATO (leva accesa e un
libro finto) per misurare la sola GEOMETRIA — non il comportamento
della leva. ⚠️ E due misure hanno mentito prima di dire la verità: il
centro del logo preso UNA volta e riusato (la barra di scorrimento va
e viene col numero di card e sposta tutto di 7,5px — i due vanno
misurati nello stesso fotogramma), e il Browser pane che emula
`prefers-reduced-motion` e CONGELA a frame 0 l'animazione d'entrata
della vista, lasciando `#view-p2p` con un `translateY(6px)` residuo:
un antenato trasformato sposta lo sticky, e per un giro è sembrato un
difetto del CSS. In un browser vero quell'animazione finisce in 180ms
da sola; portata a termine a mano, lo sticky si incolla a 0.

UNA REPUTAZIONE SOLA (10 set 2026, DECISIONE DI ANDREA, e vale come
regola): **chi è onesto con gli oggetti è onesto anche sul P2P**.
Fino a stamattina ce n'erano due: le stelline del MERCATINO sulla card,
e la reputazione del COORDINATORE — quanti scambi, che media, da quanto
— che il libro pubblico porta nel tag `rating` e che vivevano nella
riga «⚡ scambi P2P» del dettaglio, più il filtro «Reputazione» che
guardava quella. Due reputazioni nello stesso posto, con la stessa
faccia di stella, dicono cose diverse sembrando la stessa, e sceglierne
una a occhio tocca a chi legge.
È USCITA TUTTA, non solo nascosta: la riga (`repRigaP2P`), il suo
lettore (`repDaTag`) e il campo `rep` dell'ordine. Restare senza
chiamanti sarebbe codice che racconta una strada che non si percorre
più — è il precedente di `repTestoP2P`, applicato al suo erede. Il tag
`rating` del 38383 continua ad arrivare: semplicemente non lo legge
più nessuno.
IL FILTRO GUARDA ORA LA MEDIA DI CASA, e la conseguenza tecnica non è
piccola: quella media la sa il VOLTO, che arriva dal nostro server, non
l'ordine che arriva dai relay. Quindi il giudice si è SDOPPIATO —
`passaFiltroP2P` per valute, metodi e premio, `passaRepP2P(f, faccia)`
per la reputazione — e `renderP2P` fa DUE PASSI coi volti in mezzo.
⚠️ UN PASSO SOLO SI MORDEREBBE LA CODA, ed è la ragione vera della
divisione: i volti si chiedono per gli ordini che il filtro lascia
passare, quindi a reputazione filtrata non passerebbe nessuno (i volti
non ci sono ancora), quindi non si chiederebbe nessun volto, quindi non
passerebbe mai nessuno. Muto, e per sempre.
CHI NON HA UN ACCOUNT BARATTOLO — un ordine arrivato da un altro client
Mostro — resta senza stelle e passa solo se la reputazione non è
filtrata. È la stessa regola di chi l'account ce l'ha ma non ha ancora
voti: «non si sa» non è «scarso», ma chi chiede almeno una stella sta
chiedendo una PROVA, e «non si sa» non lo è.
⚠️ E «NON FILTRATA» VUOL DIRE «MINIMO A ZERO», che è la lettura più
stretta della richiesta e va detta: con `repDa` a 0 e `repA` abbassato
i senza-stelle passano lo stesso. Si è tenuta UNA regola per tutt'e due
i modi di non avere stelle, perché la riga del foglio ne dice una sola
(«compare solo col minimo a 0») e due regole diverse per due tipi di
«nessuna stella» non si potrebbero spiegare in una frase.
E QUATTRO RITOCCHI NELLO STESSO GIRO (chiesti da Andrea).
1) ARIA SOTTO LA PILLOLA, dentro il blocco attaccato e non come
margine della prima card: dev'essere fondo DIPINTO, o da attaccati le
card si vedrebbero passare in quello spazio.
2) LA STELLA SI RIEMPIE PER QUANTO VALE: una sola, piena a metà a 2,5 e
quasi tutta a 4,8 — non cinque da contare, e nemmeno una intera che
mente arrotondando. ⚠️ NIENTE `id` NELL'SVG, ed è la riga che decide
la forma: un `linearGradient` o una `clipPath` ne vogliono uno, e in un
libro ci sono N card — id ripetuto, il primo vince per tutte. Il
riempimento è una SCATOLA che taglia: due stelle sovrapposte, quella
piena dentro uno `span` largo il tanto per cento giusto con
`overflow:hidden`. La frazione è pura e sta fuori dal disegno.
Misurato dal vivo su quattro card: 2,5→50%, 4,8→96%, 5→100%, 3,2→64%.
3) L'OMINO al posto del fumetto accanto al conto dei voti, con lo
stesso tratto delle icone della nav (`fill:none`, `stroke:currentColor`,
il velo sotto): è lo stesso alfabeto, e due alfabeti nella stessa card
si notano.
4) LA RIGA DEL PROPRIO ORDINE resta senza icona: la scritta basta.
COLLAUDATI: **9016 prove verdi, 0 rosse** (+4 netti: la cura toglie le
prove di una reputazione che non c'è più mentre aggiunge quelle della
stella e del filtro nuovo) e **16 MUTAZIONI, 16 uccise** — la stella
sempre piena, la frazione fuori scala, il non-numero, la larghezza che
non arriva al disegno, la scatola che non taglia, l'id che torna,
l'omino pieno, le faccine che tornano, l'icona del proprio ordine,
l'aria che sparisce, il giudice che si riprende la reputazione, il
senza-volto che passa sempre e quello che non passa mai, la fascia che
esclude gli estremi, i volti chiesti dopo (il cane e la coda) e il
dettaglio che si riprende la riga dell'altra piazza.
⚠️ E L'HEREDOC HA MANGIATO LE ESCAPE PER LA TERZA VOLTA IN UN GIORNO,
lasciando `prove.py` con una stringa non terminata: il file non
COMPILAVA. Il giro di controllo che avevo fatto subito dopo cercava le
righe rosse e non ne trovava — perché non girava niente. **Cercare «✗»
non prova il verde: lo prova il codice d'uscita**, ed è la stessa
lezione che poche ore prima aveva salvato la tortura (baseline a exit 1
con zero rosse). Da qui la guardia esplicita nel banco della tortura,
che si ferma e lo dice invece di contare uccisioni finte.

TRE TARATURE, E DUE COLLISIONI DI CSS TROVATE MISURANDOLE (10 set
2026). Le tarature erano piccole — meno aria sotto la pillola (8→5px),
la stella della card più grande (14→17px), l'omino più piccolo
(14→12px) — e sono servite a scoprire due difetti che una taratura a
occhio non avrebbe mai mostrato.
⚠️ PRIMA COLLISIONE, ED ERA UN DIFETTO GIÀ IN PRODUZIONE: la stella
della card si chiamava `.p2p-stella`, e QUELLA CLASSE ESISTEVA GIÀ —
sono i cinque bottoni-stella del foglio del voto, trecento righe più
giù. Stessa classe, stessa specificità: le due regole si mescolavano.
La nostra sta PRIMA e fissa `width`/`height`, quindi vinceva su quelle
misure e **i bottoni del voto erano diventati scatole da 16x14 px con
dentro un glifo da 34** (misurato dal vivo, non dedotto). Nell'altro
verso i bottoni passavano alla stella della card il loro `padding`, il
`cursor:pointer` e l'ingrandimento all'hover. Curato col NOME —
`p2p-rep-stella` — e non alzando la specificità: una regola più forte
avrebbe curato un verso solo, lasciando la mescolanza dov'era. Dopo la
cura i bottoni tornano **44x42**. La sentinella adesso è doppia: la
stella della card non usa quella classe, e i bottoni del voto restano
i soli a portarla.
⚠️ SECONDA COLLISIONE, e la taratura non arrivava affatto: l'omino
porta `class="p2p-ico p2p-ico-mini"`, e `.p2p-ico` — che fissa 22px —
sta PIÙ IN BASSO nel foglio. Stessa specificità, vince chi viene dopo:
la riga `.p2p-ico-mini{width:12px}` non faceva NIENTE, e l'omino
restava 22px com'era sempre stato. Scritta `.p2p-ico.p2p-ico-mini`
(due classi battono una) la misura arriva: **12x12** misurato.
LA LEZIONE È UNA SOLA E VALE OLTRE IL CSS: due regole con la stessa
specificità si decidono per POSIZIONE nel file, e la posizione non è
una cosa che si vede leggendo la regola che si sta scrivendo. Una
classe nuova si cerca PRIMA di usarla (`grep`), e una misura scritta
si RILEGGE dal vivo — «l'ho scritta» non è «è arrivata».
E LA SENTINELLA DELL'ARIA NON INCHIODA PIÙ IL NUMERO: guardava
`padding-bottom:8px` e sarebbe diventata rossa a ogni ritocco di
Andrea senza dire niente di vero. Adesso guarda che l'aria ci SIA
dentro il blocco — cioè che sia fondo dipinto e non margine della
prima card — e il quanto resta una taratura. Stessa cura per le due
misure delle icone: la sentinella afferma che la stella è più grande
dell'omino, che è la cosa chiesta, invece di due numeri inchiodati.
MISURATO DAL VIVO su un libro finto a 375px: stella 17x17, omino
12x12, i due sulla stessa riga (centri a 0,5px), aria sotto la pillola
15px in tutto (5 del blocco più 10 del margine della pillola), e i
riempimenti a 50%, 96%, 100%.
COLLAUDATI: **9019 prove verdi, 0 rosse** (+3).

IL DETTAGLIO DI UN ORDINE DEL LIBRO DIVENTA UNA PAGINA (10 set 2026,
ridisegno chiesto da Andrea: «struttura come Dettagli ordine di
Mostro, stile Barattolo»). Toccare una card apriva un foglietto di
conferma alto tre righe — titolo, cifra, una frase, due bottoni — e
quel che si stava per prendere non si vedeva mai per intero: il
metodo di pagamento, chi c'era dall'altra parte e quanto tempo
restava erano rimasti sulla card, sotto il foglietto. Adesso è una
pagina a pieno schermo, e i suoi due bottoni gemelli in fondo SONO
la conferma: un gesto al posto di due, e la spiegazione dell'escrow
sta sopra di loro invece che dentro un secondo foglio.
LE SETTE COSE CHIESTE, e come sono state fatte: titolo che dice il
lato («Dettaglio ordine di acquisto» / «di vendita»); apertura in
seconda persona («Stai comprando sats») con la riga del prezzo («per
6,00 € 🇪🇺 al prezzo di mercato (+4%)», e «per 20,00–100,00 €» su un
intervallo); il riquadro del metodo, che con più d'uno si SCEGLIE;
niente «Creato il» e niente «ID ordine»; il riquadro della
reputazione in tre colonne; l'anello grande segmentato col «Tempo
rimasto» sotto; i due gemelli col piede di «Pubblica».
TRE COSE SONO STATE AGGIUNTE ALLA LETTERA DELLA RICHIESTA, e vanno
dette. 1) LA QUANTITÀ IN SATS resta a vista sotto il prezzo: la card
la porta, e una pagina che chiede di confermare uno scambio senza
dire quanti sats passano di mano direbbe MENO della card che si è
appena toccata. 2) IL BOTTONE DICE «VENDI» dal tab «Vendi BTC»: il
titolo e la riga di apertura cambiano già col lato, e un «Compra»
sotto «Stai vendendo sats» sarebbe l'unica parola in disaccordo con
le altre due. 3) I GLIFI DELLE TRE COLONNE sono quelli di casa — la
stella che si riempie, l'omino, e un calendario disegnato collo
stesso tratto — e non tre emoji: la stella e l'omino sono già
decisioni di Andrea di questo mese (l'omino ha SOSTITUITO il fumetto
💬 apposta), e rimetterci accanto un 📅 colorato da un'altra mano
sarebbe il terzo alfabeto nella stessa riga.
⚠️ E UNA COSA CHIESTA NON SI POTEVA FARE COM'ERA SCRITTA: «la scelta
viaggia con la presa». **Mostro al take il metodo scelto non lo
trasmette**, e non è una deduzione — è letto sui byte di v0.18.6 e
di mostro-core v0.14.6: su `take-sell` e `take-buy` mostrod legge
`Payload::Amount` e (sul solo take-sell) una bolt11, e il metodo lo
ripesca da `order.payment_method`, cioè l'ELENCO INTERO scritto da
chi ha pubblicato; in mostro-core nessuna variante di `Payload`
porta un metodo e non esiste nessun `get_payment_method` (censite
tutte le `get_*` di `src/message.rs`). Senza un posto dove metterlo,
le pillole sarebbero state un gesto che non produce niente — che è
esattamente il difetto che il cantiere «solo cifre» aveva chiuso.
LA STRADA PRESA: la scelta si scrive sulla riga locale al momento
della presa e viaggia sul NOSTRO filo, quello dei recapiti cifrati
fra le due chiavi di scambio, come terzo tipo `metodo`. Parte appena
si sa CON CHI — prima non c'è nessuno a cui mandarla — e PRIMA del
recapito, perché chi vende può avere l'invio automatico armato e
senza la scelta in mano sceglierebbe lui la forma da spedire.
IL VOCABOLARIO DEI CAMPI PASSA DA DUE A TRE, e la regola che lo
vietava non è stata rovesciata: quella vieta un tipo PER METODO
(`euro:sepa`, `euro:revolut`), perché «vince il più recente per
tipo» è il meccanismo di correzione e due recapiti vivi non si
sanno scegliere. `metodo` è UNO per scambio e lo scrive un lato
solo. Un client di ieri lo lascia cadere in silenzio, e lì degrada
a com'era: chi vende sceglie lui.
L'ANELLO GRANDE È SESSANTA TACCHE DISEGNATE UNA A UNA, e la
scorciatoia era a un passo: un `stroke-dasharray` con una maschera.
La maschera vuole un `id`, e un id nell'SVG è la trappola già pagata
con la stella (in un elenco di N card il primo id vince per tutte).
Di anello grande ce n'è uno solo alla volta, ma la regola resta la
stessa e costa sessanta `<line>`.
E IL COLORE HA UN GIUDICE SOLO da questo cantiere: le due soglie
(arancio a tre giorni, rosso nell'ultimo) stavano dentro
`anelloScadenzaP2P`, e ricopiarle nell'anello grande avrebbe fatto
due copie che possono divergere — cioè due colori sullo stesso
ordine, e a scoprirlo sarebbe chi guarda. Adesso tutt'e due chiedono
a `statoAnelloP2P`.
IL CONTO ALLA ROVESCIA BATTE NELL'UNICO INTERVAL DELL'APP, quello
della lampo, che è una regola già scritta lì («UN solo interval per
tutta l'app»): un secondo orologio si sfaserebbe col primo e sarebbe
un secondo orologio da spegnere. Si riscrive IN PLACE — un render al
secondo porterebbe via il fuoco alle pillole mentre uno le sta
toccando (la lezione delle pillole del foglio «Pubblica») — e le
tacche si toccano solo quando CAMBIANO: su sette giorni una tacca
dura due ore, cioè 7199 battiti su 7200 non hanno niente da fare.
I GIORNI SU BARATTOLO SONO UN CAMPO NUOVO del volto pubblico
(`/api/p2p/facce`), ed esce un NUMERO DI GIORNI e mai una data: a
grana di giorno non si incrocia niente, un timestamp al secondo è
un'impronta. ⚠️ E LA CHIAVE MANCA QUANDO NON SI SA: gli account con
`registrato` a zero sono nati prima che il server timbrasse
l'iscrizione — cioè sono i PIÙ VECCHI — e un «0 giorni» direbbe
«iscritto oggi», il contrario esatto del vero. Chiave assente, e il
client ci mette il suo trattino.
LA DEVIAZIONE DELL'INTERVALLO HA CAMBIATO CASA, ed era un difetto
che si vede solo dopo: stava nella porta del gesto, quindi su un
ordine a intervallo il foglio «Quanto» si apriva PRIMA che l'offerta
si fosse vista. Adesso sta nel bottone della pagina, e da «Quanto»
si rientra DRITTI nella presa invece di ripassare dalla porta — che
riaprirebbe la pagina appena chiusa.
GUARDATO DAL VIVO a 375px, sui due lati e sui due temi: titolo e
verbo che cambiano col lato, le tre pillole con nessuna accesa e il
bottone spento con la sua riga rossa, la pillola che si accende e il
bottone con lei, l'anello a 52 tacche su 60 di un ordine di otto
giorni con uno consumato, quello ROSSO a 8 tacche nell'ultimo
giorno, il conto che scorre davvero (23:47:15 → 23:46:20 fra due
fotografie), il riquadro della reputazione che sparisce senza volto,
e il bottone che su un intervallo apre «Quanto» senza prendere
niente. Sul tema chiaro le tacche spente diventano `--line` e le
accese `--ink-soft`: il token gira col tema, ed è la ragione per cui
il neutro non è mai stato «bianco».
COLLAUDATI: **9087 prove verdi, 0 rosse**, di cui **67 nuove** in
`prove_p2p_dettaglio` — sentinelle sulla forma più un banco node che
fa GIRARE la pagina intera su un DOM di cartone (il titolo coi due
lati, la riga del prezzo nei cinque casi, le pillole, il riquadro
coi suoi trattini, le tacche ai capi, il bottone spento che non
prende niente e la presa che parte con l'id, la cifra e il metodo).
⚠️ E IL BANCO DEL MOTORE HA DOVUTO PRESTARSI LA PAGINA, con la sua
lezione: lo stub scritto fra gli altri del prologo NON funzionava —
la pagina nasce DENTRO la fetta di sorgente che quel banco carica, e
una dichiarazione di funzione scritta prima se la vede riscrivere
sopra dalla vera, che poi cerca un DOM che lì non c'è. Va DOPO il
sorgente, e allora vince lei.

## Il conto scorporato del dettaglio, e la commissione del 2%

IL RITOCCO CHIESTO DA ANDREA (set 2026, il giorno dopo la pagina):
sotto il titolo resta il solo «Stai comprando/vendendo sats», e la
riga del prezzo con la quantità scendono in un CONTO SCORPORATO
sotto l'anello — il calco del foglio «Paga» del mercatino, stesso
vestito (`.ctrl-conto`, `.ctrl-riga`, il `promo-tag`): Controvalore,
Commissione Barattolo, Premio al venditore, e le due righe in
evidenza — «Ricevi» in sats e «Totale da pagare» in euro, che nel
tab Vendi si specchiano in «Paghi» (i sats bloccati) e «Ricevi»
(gli euro). `prezzoRigaP2P` è morta con la sua ragione, nome
compreso: quel che diceva lo dicono le righe del conto, ognuna col
suo nome. Della moneta resta `monetaP2P` (la bandierina dove è
vera), e il premio porta la tinta delle card (`.ctrl-riga
.p2p-affare/.p2p-avviso`: la coppia CSS c'era solo sotto
`.p2p-prezzo`, e senza il gemello la classe restava grigia).

LA DECISIONE: la commissione di Barattolo sul P2P è il **2%**. E LA
VERIFICA DI COME SI INCASSA, che era la domanda del cantiere:
l'incasso è la **`fee` del coordinatore** (la voce di
`settings.toml` sul nodo, oggi 0.01), e NON può essere altro — i
sats viaggiano dalla hold invoice al payout DENTRO mostrod, e il
client non ha nessun punto dove tirarne fuori uno. Quindi **il 2% È
quella fee, alzata a 0.02: non si somma** — sommare vorrebbe dire
inventare un secondo escrow per la sola trattenuta, cioè tradire
«Barattolo non tiene e non vede i sats».
LE DUE STRADE SCARTATE, coi perché: (a) una seconda trattenuta
lato client — non esiste il punto dove prelevarla, vedi sopra; (b)
cablare «2%» nel client — mentirebbe ogni volta che il settings
dice un'altra cosa, e la regola delle impostazioni («si leggono
dal 38385, mai cablate») esisteva già. La percentuale si legge
VIVA dal 38385, e la leva nuova `P2P_COMMISSIONE_PERCENTO` (config,
default 2, in busta con le leve P2P e nel pannello admin) è il solo
LISTINO: quando la fee viva sta sotto, il conto mostra «in promo»
col cartello del mercatino — quindi finché Andrea non gira la fee
sul nodo il conto dice «in promo 0,5%», che è vero e in rodaggio è
perfino un argomento.

⚠️ E LA FEE SI SPARTISCE META' A TESTA, ed è il punto che ha
piegato la lettera della richiesta («a destra 2%»): verificato sui
numeri veri del primo scambio (74 sats su un ordine da 7301 — hold
del venditore 7338, payout 7264, 37 per parte; e la hold
dell'impantanato: 7439 = 7402 + 37). Nel conto di chi legge ci va
quindi LA SUA METÀ (1% quando la fee è 2%), o «Controvalore −
premio − commissione» non farebbe «Ricevi» — e un conto che non
somma insegna a non fidarsi di tutti gli altri. Il 2% intero sta
nella spiegazione sotto il conto («si divide metà a testa: nel
conto c'è la tua metà»), scritta senza articolo davanti alla
percentuale perché a fee 1% direbbe «il 1%».

E LA CIFRA È UNA SOLA SU TUTTE LE SUPERFICI: `nettoLatoP2P` è il
giudice nuovo — la metà si toglie a chi compra e si AGGIUNGE a chi
vende, che la blocca insieme all'amount — e lo chiamano la card del
libro, il foglio «Quanto» e il conto: la cifra «Ricevi»/«Paghi» è
al netto di TUTTO (premio + commissione), mai un secondo conto
sulla stessa offerta. A prezzo fisso il netto porta il ≈ che prima
non c'era: l'arrotondamento buono della metà ce l'ha il
coordinatore, e la nostra è una stima. A fee ignota (38385 mai
arrivato) la commissione è un trattino e mai uno zero — «non si sa»
non è «gratis» — e la cifra resta quella del mercato.

COLLAUDATO: **9105 verdi, 0 rosse** — il banco del dettaglio fa
girare il conto negli otto casi (mercato, premio in tinta coi
segni, fisso, intervallo coi due capi, valuta ignota, promo, fee
ignota, cambio muto) e verifica che le righe SOMMINO; il banco
delle card prova il netto sui due lati e il ≈ sul fisso; la busta
`_p2p_leve` porta la quinta chiave. Guardato in vetrina CDP a 375 e
320, due lati e due temi. E IL DIFETTO DICHIARATO È STATO CURATO
IL GIORNO STESSO, su decisione di Andrea: a 320px l'etichetta
«Commissione Barattolo» cedeva coi puntini («Commissione Bar…»), e
nei casi promo e intervallo anche a 375 — il rinome è quello secco
del mercatino, «Commissione», per la stessa misura e con la stessa
domanda («dentro il nostro conto, di chi altri sarebbe?»). La
prova adesso pretende l'etichetta esatta e vieta il ritorno di
quella lunga.

E IL NODO È GIRATO (10 set 2026, guarda-e-riferisci, mano di
Andrea): `fee` a 0.02 in `settings.toml`, riavvio dal compose, e
il 38385 annuncia `fee 0.02` — verificato dallo SPECCHIO, cioè dal
lato di chi legge. Da lì il conto ha smesso da solo di dire «in
promo»: nessun deploy, che è esattamente il disegno. IL CONTO
ECONOMICO DA NON DIMENTICARE: la dev fee di Mostro è il 30% della
NOSTRA fee — oggi il tappo `dev_fee_percentage = 0` (il circuito
Tor freddo) la tiene a zero e il 2% resta intero, ma il giorno che
il tappo si toglie 0,6 punti dei 2 se ne vanno upstream, e il
margine va riguardato allora.

## La card essenziale del libro

IL TERZO RITOCCO DELLO STESSO GIORNO (10 set 2026, Andrea): la card
scende a DUE RIGHE — «Paghi 2,00 €» grande, «Ricevi ≈ 2.940 sats»
sotto (nel tab Vendi specchiate: «Paghi ≈ X sats», «Ricevi 2,00 €»)
— e la riga «prezzo di mercato» muore: la cifra è GIÀ il netto di
tutto (premio + metà commissione, `nettoLatoP2P`), la stessa del
conto nel dettaglio, e il conto per esteso sta là. Metodo,
reputazione e anello restano.
AL POSTO DELLA RIGA UN BADGE, e solo col premio: pillola coi
vestiti di casa (trust-soft/trust il verde; `--warn-bg`/`--danger`
il rosso — il fondo che il rosso aveva già in `.btn.allarme`, mai
un colore nuovo). ⚠️ IL BADGE DICE IL SOLO PREMIO DEL VENDITORE,
MAI LA COMMISSIONE, ed è la riga da tenere: la commissione è uguale
per tutti, il mestiere del badge è CONFRONTARE le offerte. I
quattro testi dicono il gesto di chi legge col valore ASSOLUTO —
a comprare «4% più caro» (rosso) / «Risparmi il 4%» (verde), a
vendere «Incassi il 4% in più» (verde) / «in meno» (rosso) — mai un
segno da interpretare; la tinta è il giudizio affare/avviso di
sempre, dal lato. A premio zero nessun badge, a prezzo fisso
nemmeno.
E «RICEVI» È TORNATO MAIUSCOLO: il minuscolo cuciva le prime due
righe in una frase sola con la terza sotto — senza la terza, la
card è righe autonome e ognuna comincia da capo.
IL BADGE È `display:table` E NON inline-block, ed è la trappola
vista in vetrina: nel tab Vendi la riga sopra è lo span inline
dell'euro, e un inline-block gli si incollava accanto sulla stessa
riga. Il table è un blocco che si stringe sul contenuto: riga sua,
larghezza da pillola, nessun wrapper.
COLLAUDATO: 9106 verdi — i quattro testi del badge coi loro colori,
il premio-zero e il fisso senza badge, il cambio muto che tiene il
badge (non ha bisogno del cambio) e perde solo le cifre, e la
sentinella CSS che pretende le coppie di casa e vieta il ritorno di
`.p2p-prezzo`. Guardato in vetrina CDP: sei card nei due temi.
⚠️ DUE SCELTE DI QUESTA VOCE SONO CADUTE IL GIORNO DOPO — le quattro
frasi del gesto e la pillola col fondo tinto: le racconta, coi
perché, «Il badge del premio, e le sue quattro stesure», qui sotto.

## Il badge del premio, e le sue quattro stesure

IL BADGE È STATO RISCRITTO QUATTRO VOLTE IN DUE GIORNI (10-11 set
2026, tutte di Andrea), e le tre scartate stanno qui perché l'ultima
si capisce solo con loro accanto. Quel che NON è mai cambiato, ed è
la riga da tenere: **il badge mostra il SOLO premio del venditore,
mai la commissione** — quella è uguale per tutti, e il mestiere del
badge è CONFRONTARE le offerte fra loro.
LA PRIMA diceva il GIUDIZIO per chi legge, ma con quattro frasi che
cambiavano col lato: «4% più caro» / «Risparmi il 4%» a comprare,
«Incassi il 4% in più / in meno» a vendere. Scartata perché quattro
frasi per la stessa cosa non si confrontano: due offerte vogliono lo
stesso metro.
LA SECONDA prese il mercato come metro — «4% sopra il mercato» /
«2% sotto il mercato» — ed è durata mezza giornata: giusta nella
logica, lunga da leggere in un elenco che si scorre, e «sopra il
mercato» dice dove sta il prezzo ma non che effetto ti fa.
LA TERZA accorciò senza cambiare strada: «4% più caro» / «2% di
sconto», due parole per verso, uguali nei due tab. Durata poche ore,
e il motivo per cui è caduta è la lezione dell'intero giro:
**diceva il PREZZO, cioè un fatto vero che lascia il lavoro a chi
legge**. Su un ordine di vendita «più caro» è una buona notizia, e
capirlo toccava a lui — con la tinta che diceva già il contrario di
quel che la parola suggeriva (un «più caro» VERDE).
LA QUARTA, quella viva: **«4% più conveniente» (verde) / «4% meno
conveniente» (rosso)**, e a premio zero **«al prezzo di mercato»**.
È la strada della PRIMA — dire l'effetto su chi guarda — con la
disciplina della seconda: DUE frasi sole, che valgono nei due tab
senza cambiare parola. Lo stesso premio cambia giudizio col lato,
e il badge lo dice invece di lasciarlo dedurre: +4% a comprare è
«meno conveniente» (si ricevono meno sats), +4% a vendere è «più
conveniente» (se ne consegnano meno).
⚠️ E ADESSO TESTO E TINTA ESCONO DALLO STESSO GIUDICE, che è il
guadagno vero dell'ultima stesura: fino a stamattina il testo
guardava il prezzo e il colore guardava chi legge — due letture da
tenere insieme a mente — mentre ora un badge verde dice sempre «più»
e uno rosso sempre «meno». Una prova nuova lo tiene fermo: nessuna
card può avere la tinta di un verso e le parole dell'altro. Il
giudice non è mai cambiato in nessuna delle quattro stesure:
`affare = (lato==='buy') === (premium>0)`.
A ZERO LA FRASE C'È LO STESSO, ed è la cosa che nessuna delle quattro
richieste diceva e che è stata aggiunta guardando l'elenco: «nessun
badge» lasciava la card muta proprio sul caso più comune, e chi
scorre non poteva sapere se il premio mancava o se nessuno gliel'aveva
detto. A prezzo fisso resta il nulla: quel prezzo il mercato non lo
guarda.
IL VESTITO: la pillola col fondo tinto è durata un giorno — due
pillole colorate per card, in un elenco che si scorre, gridavano più
delle cifre — e ha lasciato il posto al grigio muto delle card con
la TINTA SUL SOLO NUMERO. Resta `display:block`, perché nel tab
Vendi la riga sopra è lo span inline dell'euro e un inline le si
incollerebbe accanto.
⚠️ E UNA SENTINELLA È STATA ROVESCIATA, col suo perché scritto
accanto: vietava le parole del verso, perché la riga del prezzo di
allora portava già segno e colore e le parole erano un terzo modo di
dire la stessa cosa. Oggi il segno non c'è più (il badge porta il
valore ASSOLUTO) e il colore da solo non dice da che parte pende:
quelle parole sono diventate l'unica cosa che lo dice. **La
decisione di allora non era sbagliata: è cambiato ciò che le stava
accanto** — ed è la ragione per cui una sentinella si rovescia
leggendo il perché invece di cancellarla.
NEL CONTO LA PERCENTUALE STA NELL'ETICHETTA, attaccata al nome della
voce e in tinta: «Premio al venditore +4%», a destra i soli sats.
⚠️ E IL NOME DELLA VOCE CAMBIA COL VERSO — «Sconto del venditore
−2%» — perché un premio negativo non è «un premio di meno», è uno
sconto: col nome giusto non si deve leggere il segno per capire di
cosa si parla, che è proprio il lavoro che un'etichetta risparmia.
Anche qui una stesura intermedia scartata: «(+4% sopra il mercato)»
in corpo piccolo di `.ctrl-nota`, che andava bene finché era una
parentetica esplicativa e non quando è diventata il DATO della voce
— un dato in corpo piccolo si legge come una precisazione
facoltativa.
LE DUE MISURE PAGATE, tutt'e due viste in vetrina e non a occhio:
l'etichetta del premio VA A CAPO invece di cedere coi puntini (è
l'unica riga del conto la cui etichetta porta un dato, e troncarla
mangerebbe proprio quello — a 320 si legge «Premio al venditore» e
«+4%» sotto, che è brutto ma intero); e nella stesura con la
parentesi serviva anche un `nowrap` sulla nota, o la spezzatura
cadeva dentro la frase.
⚠️ E LA COPPIA DI TINTE DEL CONTO HA CAMBIATO POSTO nel CSS: quando
la percentuale viveva dentro `.ctrl-nota`, che è grigia, a parità di
specificità vinceva l'ultima scritta — e le tinte stavano più su,
quindi il grigio avrebbe spento il numero senza che niente fallisse.
Ora stanno dopo la nota e valgono in tutti e due i casi, con una
sentinella sull'ORDINE delle due regole: oggi difende un rischio
rientrato, e costa zero il giorno che la percentuale ci rientrasse.
COLLAUDATO: **9110 verdi**. Guardato in vetrina CDP nei due temi:
sei card e sette conti, a 375 e a 320, col caso sconto che somma
(719.424 − 7.338 + 14.389 = 726.475). E LA FRASE PIÙ LUNGA È STATA
MISURATA, non guardata: «4% meno conveniente» sta su UNA riga a
320px (300px di contenuto), che è la misura di casa — il badge è la
riga più lunga della card, e ogni stesura l'ha allungata.
⚠️ E UN DIFETTO DI QUESTO STESSO FILE È STATO TROVATO SCRIVENDOLO,
perché vale più della voce: la stesura di stamattina era stata
infilata in mezzo alla voce della fee del nodo, che si è ritrovata
TRONCATA a metà frase con la sua coda (il conto economico della dev
fee) attaccata in fondo al badge. Nessuna prova copre la prosa, il
commit era già pushato, e a trovarlo è stata solo la rilettura del
contesto prima di riscrivere. **Una voce nuova si inserisce fra due
voci, mai dentro una**: si guarda che il paragrafo sopra FINISCA
davvero — un punto e una riga vuota — e non che cominci bene.

## «Fee Barattolo» nei due conti, e la misura che l'ha permesso

L'ETICHETTA DELLA COMMISSIONE PRENDE IL NOME DI CASA (11 set 2026,
decisione di Andrea) in TUTT'E DUE i conti — quello del P2P e il
foglio «Paga» del mercatino: si vestivano già uguali (`.ctrl-conto`,
`.ctrl-riga`), adesso dicono anche la stessa parola, e il nome torna
a dire DI CHI è quella riga — la cosa che «Commissione» secca aveva
perso per stare nella larghezza.
LA MISURA È IL CUORE DELLA VOCE, perché questa riga ha già un
precedente: «Commissione Barattolo» fu bocciata DUE volte (ago 2026
nel mercatino, 10 set nel P2P) perché cedeva coi puntini a 320px.
Misurato adesso a 320 veri, col Range sul testo e non a occhio:
**«Fee Barattolo» = 85px, «Commissione» = 86px** — il nome nuovo è
perfino UN PIXEL più corto di quello che sostituisce, e nel
mercatino gliene avanzano 74 (85 su 159), nel P2P 58 (85 su 143).
Quindi non è una deroga alla decisione di allora: è la stessa
decisione: **a restare vietata è la FORMULA LUNGA, non il nome.**
⚠️ E IL BANCO DI MISURA HA MENTITO AL PRIMO GIRO, con la trappola
già scritta in memoria: senza `<meta name="viewport">` la pagina in
emulazione mobile impagina a **980px**, quindi le prime misure erano
di un'altra pagina. Il controllo che l'ha preso è `window.innerWidth`
letto e CONFRONTATO col numero atteso — non guardato: lo script si
ferma se non è 320. Una misura sbagliata qui non fallisce, dà numeri
plausibili.
IL SECONDO STRUMENTO CHE È SERVITO è l'**A/B nella stessa pagina**:
lo stesso conto reso due volte, una col nome nuovo e una col vecchio
(sostituito nell'HTML), e il confronto riga per riga. Senza, i
troncamenti trovati sarebbero sembrati tutti colpa del rinome —
mentre erano **zero regressioni**, come ha detto il confronto.
⚠️ MA I TRONCAMENTI TROVATI SONO VERI, e restano DICHIARATI e NON
curati (fuori dal perimetro chiesto): nel conto P2P, quando il
valore a destra è lungo, a cedere è l'etichetta — «in promo 0,5% ·
≈ −3453 sats» le lascia 55px su 85 richiesti, e su un ordine a
INTERVALLO le cifre a due capi («≈ −11.990–59.952 sats») la
schiacciano a **zero**, portandosi dietro anche «Ricevi» e «Totale
da pagare». Erano identici col nome vecchio: la causa è il valore,
non l'etichetta. Il giorno che si curi, la leva non è la parola —
è far cedere qualcosa a DESTRA (la pillola «in promo» a capo, o la
percentuale fuori dal valore).
COLLAUDATO: 9109 verdi, con la sentinella del mercatino che finora
non c'era — l'etichetta di quella riga non era guardata da nessuno,
e il divieto della formula lunga viveva solo in un commento.
