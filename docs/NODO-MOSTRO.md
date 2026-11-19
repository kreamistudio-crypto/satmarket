## Il nodo Mostro (un'ALTRA macchina)

Questo documento e' la sezione «Il nodo Mostro» che fino al 30 set 2026
viveva in `CLAUDE.md` (392 righe), spostata qui INTERA e senza ritocchi:
le decisioni coi loro perche', l'audit, i timer letti sul sorgente, la
sonda del coordinator, la dev fee sul circuito freddo. In `CLAUDE.md`
restano le regole in forma corta, con il rimando a questo file. Si cerca
per NOME come negli altri documenti (`grep -n "TRE TIMER" docs/*.md`),
e non si legge intero.


⚠️ Non è il VPS di Barattolo. È il coordinator Mostro P2P su LNVPS
(Dublino), Debian 13, tutto in container — bitcoind pruned, LND, tor,
mostrod — con un canale da 400.000 sat verso ACINQ. IPv4 pubblico
`185.18.221.96`. Sta qui perché la tappa 8 del cantiere client P2P
(il primo ordine vero, due identità e mille sats) si chiude LÌ.

**L'AUDIT DI SICUREZZA È GIÀ STATO FATTO — 2 settembre 2026.** Non
riproporre le sue sei domande come «da fare»: superficie esposta,
ampiezza del macaroon di mostrod, cosa può chi entra nella macchina,
buchi nel proxy trasparente Tor, la nsec in chiaro in `settings.toml`,
e cosa può fare un attaccante che arriva dai relay. Tutti e sei chiusi,
in modalità **guarda-e-riferisci** (i comandi li scrivo io, li esegue
Andrea — vedi la regola del VPS fuori dal perimetro).

**IL DOCUMENTO STA NEL CANALE TELEGRAM DEL NODO**, quello degli avvisi
della ronda, col nome `auditnodomostro202609`. Si chiede quello invece
di riscriverlo a memoria: contiene le decisioni **coi loro perché**, che
è la parte che non si ricostruisce.
⚠️ Da quando quel canale è anche un archivio vale la regola: **i canali
Telegram non sono cifrati end-to-end**, quindi lì dentro vanno documenti
SENZA segreti — mai `settings.toml`, mai la nsec, mai un macaroon. Per i
segreti la strada è l'archivio cifrato con age.

I DUE DIFETTI VERI che ha trovato, perché sono la lezione: 1) in mostrod
0.18.5 lo **spam gate girava PRIMA della verifica della firma** —
chiunque dai relay poteva bruciare il budget di un utente vero
dichiarandone la trade key, cioè censura per identità a costo zero;
chiuso salendo a **0.18.6** (rollback taggato `mostro:v0.18.5`). 2) Una
**fuga di traffico fuori da Tor**: `ip_forward=1` con la tabella filter
tutta ACCEPT, quindi UDP≠53 (QUIC/HTTP-3 sulla 443) e ICMP uscivano in
chiaro; chiusa con `iptables -A FORWARD -s 172.28.1.5 -j DROP`, che dal
15 set 2026 sta in `tor-entrypoint.sh` e si riapplica a ogni avvio di
tor (prima nel comando del sidecar, riga 48 del compose). Nessuno dei
due era un errore di configurazione nostro: il primo era nel codice, il
secondo era il residuo che le tre regole di redirect non coprivano.
⚠️ IL NAMESPACE PRESTATO (15 set 2026, tre ore di P2P muto): il sidecar
`tor-redirect` viveva nel namespace di rete di `tor`, e un `restart tor`
lo lasciava in quello VECCHIO — regole visibili a `docker exec`, mostro
«000» su ogni host. Dalla sera stessa il sidecar NON C'E' PIU' (regole
nell'entrypoint di tor, uid inchiodato nel Dockerfile); `mostro` vive
ancora in `mostro-net`: dopo `restart mostro-net` sempre `up -d --force-recreate mostro`. Vedi PRODUZIONE («IL NAMESPACE PRESTATO»).

**IL NODO GIRA LA 0.18.7**, e non lo dice il changelog ma il nodo
stesso: il suo evento `info` (38385) si annuncia `mostro_version
0.18.7`, letto il set 2026 dai tre relay pubblici E dal nostro
specchio, cioe' verificato dal lato di chi legge. Il changelog di
quella versione e' pagamenti, timelock, dev-fee, annullamenti e
contatori di drain — **niente sulla verifica della firma, niente sul
trasporto, e mostro-core resta 0.14.6**, cioe' la ricetta che il
nostro client ricalca non si e' mossa.
✅ E L'AVVISO CHE STAVA QUI E' RIENTRATO, verificato invece che
dedotto: `c6efb2d` (#952) rinominava il campo con cui l'`info`
annuncia la finestra della hold invoice, e nel 38385 vero i nomi sono
ANCORA QUELLI VECCHI — `invoice_expiration_window` e
`hold_invoice_expiration_window`. Quindi non morde. Dal 16 set 2026 il
client LEGGE `invoice_expiration_window` (`fattFinestra`, via
`finestraFatturaP2P`) per fermare PRIMA una fattura troppo corta: il
nome e' quello che il 38385 emette davvero; se il tag sparisse, il
client ripiega sui 3600 s del template. La sorella della hold resta morta.

**LA RONDA DICE CINQUE COSE E LA QUINTA VALIDA LE ALTRE:** finestra
blocchi/disco/ram, canale e HTLC, backup (allarme oltre 48h o sotto
1 MB), superficie (baseline di 23 righe che NOMINA cosa è comparso o
sparito, e `--impara` è un gesto), più il **marcatore `--- fine ronda`**.
Se il messaggio non finisce con quella riga, un `exit 0` di metà script
si è mangiato un pezzo — è successo DUE volte, e avvisarne a parole non
era bastato: quel difetto non fallisce, semplicemente non gira, e da
fuori un giro monco si legge come uno completo.

**IL BACKUP** è `backup-nodo.sh` + `nodo-backup.timer` (03:30,
`Persistent=true`): cifra con la sola chiave **pubblica** age — il
server produce copie che lui stesso non sa riaprire — e il PC le tira
giù in **pull** via SSH, così non c'è nessuna credenziale di uscita
sulla macchina. Drill completo fatto. **NON contiene `channel.db`, ed è
voluto**: ripristinare uno stato vecchio di un canale e trasmettere un
commitment obsoleto è il modo classico di perdere i fondi — per i canali
esiste solo l'SCB, che li CHIUDE. Lo script non si fida di `--exclude`:
guarda DENTRO l'archivio e si ferma se lo trova.
⚠️ **IL PULL DAL PC ERA ROTTO DAL 7 SET AL 1 OTT 2026** (`storico.log`
sul PC: ultimo `ok` il 6 set 21:09, poi `nodo=False` ogni giorno con
«permission denied» su `/var/backups/nodo`). Gli archivi nascevano
ogni notte, a `debian:pull` 640, ma la riga 19 di `backup-nodo.sh`
faceva `install -d -m 700 -o debian -g debian` e **richiudeva la
cartella ogni notte** a 700: la correzione a mano del 7 set durava fino
alle 03:30. Curato da Andrea il 1 ott: `install -d -m 750 -o debian -g
pull` (copia dello script in `backup-nodo.sh.prima-pull`), pull dal PC
riuscito fino a `nodo-20261001-0330.tgz.age`. La lezione: un permesso
messo a mano su una cartella che uno script RICREA non è una cura, e
`storico.log` va letto — tre settimane di `FALLITO` non avevano
suonato. Scoperto per caso dal cantiere dell'hackathon RGB
(`docs/HACKATHON-SETUP.md`), aggiungendo la gamba `rgb/` al pull.

`pow_first_contact` resta **SPENTO**, e non per prudenza generica: non
c'è spam in corso (zero utenti), il modo in cui fallisce è silenzioso in
tre direzioni — nessun errore al client, nessun messaggio all'utente,
nessuna riga nei nostri log, perché l'evento scartato non raggiunge mai
un handler — e la guida di migrazione per i client è «Phase 3, pending».
Si riapre quando il termometro degli eventi salta di un ordine di
grandezza SENZA che siano arrivati utenti.

`uris` di LND porta **solo l'onion, nessun IP**: verificato, ed era la
cosa che non si sarebbe potuta disfare.

**LE SETTE COSE APERTE**, dichiarate e non dimenticate: `/config`
scrivibile da mostrod (prima serve sapere dove vive il db); macaroon
senza IP lock (quello di mostrod non esce dalla macchina; dal set 2026
ne esiste un SECONDO, dedicato a LNbits e revocabile da solo —
`root_key_id 1` — che vive sul VPS di Barattolo dietro un hidden
service con client-auth: vedi Cantieri, «Il doppio wallet»); LLMNR sulla 5355
(superficie che non paga affitto); il pull non è sorvegliato (il
server sa che l'archivio esiste, non che il PC l'abbia preso); il DROP
del FORWARD in `ip6tables`, che mancava — **CHIUSO il 15 set 2026**
dall'entrypoint di tor, che lo riapplica a ogni avvio insieme al v4; la
**dev fee bloccata dal circuito freddo**, che è upstream e ha la sua
voce in fondo a questa sezione; e la riconciliazione LND↔Mostro, che
dal 7 set 2026 **si può finalmente fare** — qui c'era scritto
«rimandata al primo trade vero perché un controllo su un caso che non
si produce ancora non prova niente», e adesso quel caso c'è.
⚠️ DUE VOCI SONO CADUTE E NON SI RIMETTONO: «nessuno SCAMBIO mai
portato a termine sul coordinator» e il macaroon ristretto «da
verificare» — il 7 set 2026 lo scambio c'è stato, e il ristretto ha
retto tutto (vedi il punto 4 delle risposte del team, qui sotto).

**LE RISPOSTE DEL TEAM MOSTRO (set 2026), a verbale.** 1) La hold
invoice tiene i sats per 24 ORE e la finestra è CONFIGURABILE —
NostroMostro la tiene a 3 giorni. La leva che combacia è
`hold_invoice_cltv_delta` in `[lightning]` di `settings.toml`
(verificata sul `settings.tpl.toml` del tag v0.18.6; il nodo da
allora e' salito alla 0.18.7, e le letture del sorgente qui sotto
restano quelle fatte al 0.18.6): è in BLOCCHI, 144 ≈ 24h — il numero che hanno detto — e 3
giorni fanno 432. Il margine `escrow_deadline_margin_blocks` (24)
resta com'è, quindi la finestra UTILE è sempre ~4 ore più corta
dell'orizzonte: mostrod molla la presa PRIMA che LND sia costretto a
chiudere il canale per salvare l'HTLC. GIRATA A 432 il 6 set 2026 e a 576 il 15 set 2026 (tabacchino, vedi PRODUZIONE), a
scambi fermi: riavvio pulito («Settings correctly loaded», transport
nip44). ⚠️ IL RIAVVIO SI FA DAL COMPOSE: `docker compose restart
mostro` dalla cartella `~/nodo`. «mostro» è il nome del SERVIZIO,
mentre il CONTAINER si chiama `nodo-mostro-1` — quindi sia
`docker restart mostrod` sia `docker restart mostro` rispondono
«No such container», e la prima stesura di questa riga sbagliava
credendo che bastasse togliere la «d». Verificate tutt'e due il
6 set 2026. 2) I 15 minuti che avevamo visto NON sono la finestra del
deposito: sono `expiration_seconds` (900) in `[mostro]` — ma nemmeno
«il tempo per accettare», che era la nostra lettura di allora: è il
tempo per COMPLETARE la presa in carico DOPO averla accettata, e
riparte a ogni gesto. Vedi «I TRE TIMER», qui sotto. 3) Nessun vincolo
di protocollo sul rilascio: «you need trustworthy moderators». La
garanzia siamo noi — che è la stessa frase su cui poggia l'escrow di
Barattolo. 4) Dicono che serve l'ADMIN macaroon, ma il nostro gira col
RISTRETTO (info/invoices/offchain) e ha già risposto ad altri client:
**VERIFICATO il 7 set 2026** dal primo scambio vero — hold invoice
creata, tenuta e saldata, payout al venditore e dev fee pagata, tutto
col ristretto. La cosa aperta si chiude: l'admin macaroon **non
serve**, e non lo si dà.
**LA SONDA DEL COORDINATOR (set 2026), le otto domande della tappa 1.**
Chieste al nodo VERO con un mazzo usa-e-getta generato dalla sonda —
nessun segreto in gioco — e un ordine di prova nato e poi ritirato.
**TUTT'E OTTO hanno una risposta**, e ci sono voluti DUE giri: il primo
ne diede quattro FALSE, e la cura al lettore le ha rimesse in piedi
tutte (la lezione sta in fondo alla voce).
**Q1 — RISPONDE, e alla chiave che ha chiesto.** L'ordine di prova e'
nato ed e' comparso nel 38383 col suo tag rating (days 0, total_rating
0.0, total_reviews 0); il `cancel` l'ha riportato a `canceled`.
**Q2 — SI: accetta una trade key MAI VISTA con `trade_index: null`**, e
con TUTT'E DUE le buste (`order` e `restore`). Non serve una chiave gia'
bruciata per interrogare, ed e' la risposta che decide quale chiave usa
il cantiere. ⚠️ Agganciata di RIPIEGO, e non e' un dettaglio del
lettore: e' Q5 vista dall'altro lato — senza il ripiego questa sarebbe
ancora un NO su un fatto vero.
**Q3 — col mazzo B, mai visto, risponde `{"orders": [], "disputes":
[]}`.** Quindi «non ti riconosco» si serve COME una lista vuota: i due
casi **non si distinguono**. Per noi va bene — la domanda che facciamo
e' «quali ordini ha questa chiave», e la risposta e' giusta in tutti e
due i casi — ma va scritto, perche' il giorno che servisse sapere se una
chiave e' NOTA, da qui non si sa. Agganciata di RIPIEGO anche lei, per
la stessa ragione di Q2.
**Q4 — `status` sta DENTRO ogni ordine**, e in questo giro vale
`"pending"`. E' l'unica stringa che restore-session abbia detto: il
`canceled` visto dopo il ritiro veniva dal LIBRO (38383), che e'
un'altra fonte e un altro vocabolario. La tabella del giudice si
completa vedendo gli altri stati, e finche' non li si vede il giudice
non si scrive a memoria.
**Q6 — SI: l'elenco include i `pending`** (l'ordine di prova c'era, e i
log del nodo dicono «Background restore session completed with 1 orders,
0 disputes»). Quindi un `pending` nella lista implica maker, e **il lato
e' un fatto** invece di un'inferenza.
**Q5 — IL `request_id` TORNA SU DUE FAMIGLIE SU TRE**, ed e' un FATTO e
non piu' un'inferenza: torna uguale su `new-order` e su `cancel`, e su
`restore-session` vale **`null`** — il campo C'E', il valore no («campi
del messaggio: [version, request_id, trade_index, action, payload],
request_id: null»). Non e' che mostrod non lo capisca: non lo RICOPIA su
quella famiglia.
IL CANTIERE NON SI FERMA, MA IL DISEGNO CAMBIA, ed e' la riga da tenere:
su restore-session l'aggancio non puo' essere il `request_id` e diventa
**LA CHIAVE DI DESTINAZIONE** — la risposta e' un kind 14 cifrato verso
la pubkey che ha chiesto, quindi se si apre con la chiave X e' per X.
E' piu' forte di un aggancio sul contenuto, non piu' debole: a garantire
non e' un campo che il mittente puo' scrivere come gli pare, e' la
crittografia.
LA CONDIZIONE CHE LO RENDE VERO va scritta, perche' e' l'unica cosa che
il cantiere deve rispettare: **una restore-session alla volta per
chiave**. Con due in volo dalla stessa chiave le risposte tornano
indistinguibili — il client non ha nessuna ragione di mandarne due, ma
la regola vale finche' qualcuno non la rompe, e allora si rompe in
silenzio (due liste giuste attribuite alla domanda sbagliata).
⚠️ QUEL CHE RESTA IGNOTO SI DICHIARA: se il coordinatore mandi messaggi
SPONTANEI verso quella chiave con la stessa `action`. Se lo facesse,
l'aggancio per sola chiave prenderebbe il primo che arriva. Il secondo
criterio c'e' gia' nella risposta (`action`), e la prima cosa da
guardare il giorno che una lettura tornasse storta e' quella.
**Q7 — POW SPENTO** (`pow=0`, `pow_first_contact=0` nel 38385): conferma
dal LIBRO la scelta gia' a verbale sul nodo, che si riapre solo se il
termometro degli eventi salta di un ordine di grandezza.
**Q8 — UNA RISPOSTA SOLA PER OGNI RICHIESTA**, ed e' la meta' che rende
praticabile l'aggancio per chiave: non c'e' nessuna raffica da sceverare.
I PARAMETRI DEL 38385 VALGONO PIU' DI UNA CONFERMA: `expiration_hours`
168, `expiration_seconds` 900, `hold_invoice_cltv_delta` 576 (432 fino al 15 set 2026) — le tre
leve girate il 6 set 2026 si leggono **DAL LIBRO PUBBLICO** e non piu'
dal solo `settings.toml`, cioe' sono verificate dal lato di chi legge e
non da quello di chi le ha scritte. Piu' `bond_enabled` false (coerente
con `[anti_abuse_bond]` commentata), `maintenance_mode` false,
`max_order_amount` 500000 (dal 17 set) e **`fee` 0.03** — la commissione di
Barattolo: 0.01, poi 0.02 il 10 set 2026, e 0.03 dal 18 set con lo sconto
fedelta' PER PARTE della patch 0005 (1,5% a testa, 1% a pionieri e
livello 5). Il client la legge viva dal 38385, meta' a testa (vedi
CANTIERI, «Il passo 3 delle commissioni per persona»).
⚠️ E SI CALCOLA DOPO IL PREMIO, verificato sui byte (11 set 2026,
`src/util.rs`): `get_market_amount_and_fee` chiama
`get_fee(new_sats_amount)`, e quel numero esce da `get_market_quote`
col premio GIA' applicato. Quindi la base dell'aliquota non e' il
controvalore a mercato puro ma l'importo scontato o caricato dal
premio — l'ordine in cui il conto del client mostra le righe
(Controvalore, premio, Subtotale, fee) e' quello, e non e' impaginazione.
E LA LEZIONE DEL GIRO VALE OLTRE LA SONDA: il lettore del quadro
agganciava la risposta con UN criterio solo — il `request_id` — e da
quell'aggancio dipendevano a cascata quattro risposte, che sono uscite
**NO CATEGORICI su fatti veri** mentre il grezzo li' sopra diceva il
contrario. **Un NO su un fatto vero e' peggio di un «non lo so»**: il
primo chiude una domanda, il secondo la tiene aperta. La cura non e'
indovinare il campo che manca ma rendere il lettore robusto — l'aggancio
ha un ripiego DICHIARATO (la prima risposta che viene dal coordinatore
verso la chiave interrogata, e chi legge se lo trova scritto accanto), e
le risposte che elencano gli stati si ricavano da TUTTE le risposte del
coordinatore nella finestra invece che dalla sola agganciata, che e' quel
che fa un umano guardando il grezzo. IL SEGNO CHE IL DIFETTO ERA VECCHIO:
Q1 aveva gia' il ramo «ha risposto ma non con quel request_id» e gli
altri tre no — la stessa prudenza scritta in un posto e mancante negli
altri, che e' il modo in cui una cecita' si nasconde in mezzo a del
codice che funziona.
IL SECONDO GIRO HA CHIUSO IL CERCHIO, ed e' quel che rende la lezione
verificata invece che raccontata: Q2 e Q3 sono tornate SI **dal
ripiego**, e il grezzo ha detto perche' — `request_id: null` su
restore-session. Cioe' il criterio che mancava non si sarebbe potuto
indovinare (il campo c'era, era il VALORE a mancare), mentre il ripiego
lo ha reso irrilevante. **Quando non si sa quale sara' il criterio buono,
si rende robusto il lettore invece di scommettere sul campo.**

**I TRE TIMER, letti sul sorgente di `v0.18.6`** (set 2026, prima di
rispondere ad Alan, che proponeva di allungare «i 15 minuti» a un
giorno e la vita dell'ordine a 7). Il commento del `settings.tpl.toml`
su questo punto DICE IL FALSO, ed è la ragione per cui si legge il
codice: attribuisce il mestiere a una voce inerte e lo nega a quella viva.
• `expiration_seconds` (900) è il tempo per COMPLETARE la presa in
carico: `find_order_by_seconds` in `src/db.rs` filtra
`WHERE taken_at < now − expiration_seconds` sui SOLI stati
`waiting-buyer-invoice` e `waiting-payment`. Non è la vita
dell'ordine nel libro, e non è il tempo per accettare.
• **E IL CRONOMETRO RIPARTE A OGNI FASE**, che è la parte che
leggendo il config non si vede: `show_hold_invoice` in `src/util.rs`
ri-timbra `taken_at` entrando in `waiting-payment`, col suo commento
che spiega perché DEVE farlo — la colpa in
`slash_or_release_on_timeout` cade su chi tiene il dovere corrente, e
un compratore che si è attardato mangerebbe la finestra del venditore
facendogli bruciare il bond. Quindi i 900 s sono PER GESTO: chi compra
ha 15 minuti per incollare la invoice, e da lì chi vende ne ha altri
15 per pagare — un umano ha già mezz'ora, in due tranche.
**E VALE ANCHE NELL'ALTRO VERSO** (10 ott 2026, letto sul sorgente della
`-bar6` sul nodo: `sed` di `src/flow.rs` e `src/scheduler.rs`): quando
chi vende ha PRESO e ha pagato la garanzia, `hold_invoice_paid` entrando
in `waiting-buyer-invoice` fa `order.set_timestamp_now()` — il gemello
dichiarato del ri-timbro di `show_hold_invoice` — e
`reconfirm_timeout_eligibility` rilegge la riga prima di annullare,
proprio perché un passaggio di turno può aver spostato `taken_at`.
Quindi OGNI gesto ha la finestra intera da quando viene chiesto, in
tutti e due i versi: è la regola su cui Barattolo conta le scadenze
(`_scadenza_gesto_p2p` nel server, `scadenzaGestoP2P` nel client).
• `hold_invoice_expiration_window` (300) **non la legge NESSUNO: è
configurazione morta in v0.18.6.** Dichiarata nella struct, scritta
dal wizard, presente in una fixture di test, e in nessun altro posto
— censite tutte e 25 le `.rs` che potrebbero nominarla. Toccarla non
fa niente, e il suo commento nel template descrive il mestiere di
`expiration_seconds`.
• `hold_invoice_cltv_delta` (576 dal 15 set 2026, prima 432) alimenta SOLO il `cltv_expiry` della
hold invoice (`create_hold_invoice` in `src/lightning/mod.rs`, che
l'`expiry` della fattura non lo tocca proprio): è quanto l'HTLC resta
appeso DOPO il pagamento, e la finestra utile la dà
`escrow_guard_window_secs` — `(576−24)×600 = 92 ore` (68 a 432); il client la legge dal 38385 (`finestraGaranziaP2P`).
• LA VITA NEL LIBRO È UN'ALTRA LEVA, `expiration_hours`:
`get_expiration_date` in `src/util.rs` scrive `orders.expires_at` a
`now + expiration_hours` quando il client non ne manda una sua, e la
clampa a `max_expiration_days` (15) quando la manda. **GIRATA DA 24 A
168 il 6 set 2026** (riga 56 del `settings.toml`, riavvio pulito): è
la richiesta di Alan letta sulla voce giusta. Fino a 15 giorni si
poteva già chiedere per singolo ordine dal client.
COSA SUCCEDE AL TIMEOUT, che nessuno aveva verificato: `job_cancel_orders`
in `src/scheduler.rs` cancella la hold invoice — **niente HTLC
appeso** — e poi guarda di chi è la colpa: se manca il TAKER l'ordine
TORNA NEL LIBRO (`Status::Pending`, `Action::NewOrder`, stato
azzerato), se manca il MAKER l'ordine MUORE (`Status::Canceled`).
**E I 900 SECONDI RESTANO 900** (decisione di Andrea): il motivo forte
non è il curioso che congela l'ordine altrui — quello è vero e si
paga — ma **l'OPZIONE GRATUITA SUL CAMBIO**. Sugli ordini a prezzo di
mercato il tasso si fissa AL TAKE (`get_market_amount_and_fee` in
`src/app/take_buy.rs`), quindi con una finestra di un giorno chi prende
può aspettare e pagare solo se il BTC/EUR si è mosso a suo favore, e
non pagare se si è mosso contro. A 15 minuti quell'opzione non vale
niente. **E oggi abbandonare non costa NULLA**: `[anti_abuse_bond]` è
opt-in e sul nostro nodo è tutta commentata (verificato, riga 215 in
poi). Quindi **la cura per «15 minuti sono pochi» sono i BOND, non la
finestra**: con quelli accesi `slash_or_release_on_timeout` brucia il
bond di chi teneva il dovere, e allora la finestra si allunga senza
regalare niente. Cantiere suo, e va PRIMA di qualunque ritocco ai 900.
**DAL 10 OTT 2026 SONO 1800** (decisione di Andrea, che rovescia la riga
qui sopra sapendolo). IL CASO: la mattina del lancio un PayCode
Barattozon da 111,80 €; alle 10:04 a chi vendeva arriva «Paga la
garanzia», alle 10:20 il coordinatore annulla, lui legge alle 10:48.
Quindici minuti per un gesto che si fa da un wallet esterno, dopo un
avviso su Telegram, sono pochi per una persona che non ha il telefono in
mano. IL CAMBIO, fatto da Andrea sul nodo: nel `[mostro]` di
`~/nodo/mostro/settings.toml` `expiration_seconds = 1800` (era 900),
`docker compose restart mostro` a libro fermo, ripartito alle 14:04 con
«Settings correctly loaded» (parola di Andrea: da qui il nodo non si
guarda). `hold_invoice_expiration_window` RESTA 900, E NON ACCORCIA
NIENTE — la domanda era legittima (se fosse la scadenza BOLT11 della
garanzia, a 900 contro 1800 chi vende avrebbe in pratica 15 minuti) ed
è stata chiusa sul sorgente che gira, letto da Andrea sul nodo lo stesso
pomeriggio: `create_hold_invoice` (`src/lightning/mod.rs:453`) chiama
`create_hold_invoice_with_expiry` con `None`, quindi la fattura di
garanzia prende la scadenza di default di LND, 86400 secondi: il solo
limite di chi vende è `expiration_seconds`. `hold_invoice_expiration_window`
lo legge soltanto il flusso della cauzione (`src/app/bond/flow.rs:186`,
`223`, `392`, `1875`: la fattura della cauzione e la sua
riconciliazione), lo nomina un commento sulla cauzione in
`scheduler.rs:1392`, e `nip33.rs:599` lo pubblica nel 38385. ⚠️ Il
commento a `nip33.rs:584` lo descrive ancora come «il tempo di chi
prende per pagare o dare la fattura»: è il mestiere di
`expiration_seconds`, e chi legge il tag del 38385 credendo a quel nome
dice 15 minuti dove ce ne sono 30. In Barattolo quel tag (`holdFinestra`)
lo leggono solo i tre punti della cauzione — `cauzioneVivaP2P`,
`renderCauzioneP2P` e `scadenzaFoglioP2P` nel modo `cauzione`, tutti
come ripiego della scadenza scritta nella bolt11 —; «Info P2P», il
foglio «Blocca i sats», il conto alla rovescia e gli avvisi del server
leggono `expiration_seconds` (ricontrollato il 10 ott 2026: niente da
correggere). Alzarlo a 1800 allungherebbe solo la richiesta di cauzione
del contanti, ed è un'altra decisione. IL PREZZO, accettato: la finestra è PER GESTO (il cronometro
riparte a ogni passaggio di turno, vedi sopra), quindi sono 30 + 30
minuti, e sugli ordini a prezzo di mercato l'opzione gratuita sul cambio
vale il doppio di prima — poco, a mezz'ora (a stima il movimento tipico
resta sotto commissione e premio), ma non più niente; e chi prende senza
proseguire tiene fermo l'ordine altrui 30 minuti invece di 15. La
cauzione oggi copre il solo «Contanti» e al timeout NON brucia
(`slash_on_waiting_timeout = false`), quindi quella difesa non c'è.
LA REGOLA, RISCRITTA IL 12 OTT 2026 (decisione di Andrea, cantiere
`tempo-di-chi-pubblica`; fino ad allora diceva «oltre i 1800 non si va
senza la cauzione che brucia al timeout, su tutti i metodi — il
ragionamento di sopra vale intero per 2, 6 e 12 ore»). Il ragionamento
non è caduto: è stato diviso per RUOLO, e ha cambiato contrappeso.
• CHI PRENDE RESTA A 1800. Ha il telefono in mano in quel momento, e per
lui vale tutto quel che è scritto sopra: una finestra lunga a chi prende
è un'opzione gratuita sul cambio e un ordine altrui tenuto fermo, e non
si allunga senza un costo.
• CHI PUBBLICA HA TRE ORE (`maker_expiration_seconds = 10800`, patch
0011, immagine `-bar8`): non sa quando gli prenderanno l'ordine. I casi
veri del lancio sono ordini presi di notte o all'alba e annullati mentre
dormiva, da ripubblicare a mano. E se non risponde l'ordine NON MUORE
PIÙ: torna nel libro, e solo alla seconda mancata risposta di fila si
toglie (`maker_timeout_limit = 2`).
• IL CONTRAPPESO NON È LA CAUZIONE, È LA PENALITÀ. L'opzione sul cambio
in tre ore c'è anche per chi pubblica — su un ordine a mercato il prezzo
si ferma alla presa, e lui può rispondere solo se si è mosso a suo
favore —, e senza un costo sarebbe gratuita. Il costo è su Barattolo:
chi pubblica e non risponde entro le sue ore, o annulla a mano dopo una
presa, prende un «non completato», lo stesso contatore di chi prende con
le stesse soglie (CANTIERI, «Il tempo di chi pubblica»). È per questo
che il server la conta SOLO se il nodo il tempo lungo lo dà davvero
(`_penalita_pubblica_p2p`): tempo lungo e penalità stanno insieme o non
stanno. Una cauzione che brucia resterebbe la difesa più forte, e
varrebbe anche per chi usa un'altra app; la penalità vale dentro
Barattolo — il prezzo accettato, detto.
• PERCHÉ TRE E NON DODICI (la proposta di Alan): il movimento del cambio
cresce col tempo, e a dodici ore vale quanto il premio di un ordine
tipico; a tre resta sotto. E chi ha preso aspetta: sugli acquisti i suoi
sats sono già in garanzia per tutta l'attesa (li riprende quando vuole,
annullando da solo e senza penalità — `cancel.rs`, letto sul fork).
PER CAMBIARE LE ORE: la sola riga del `settings.toml` e un `docker
compose restart mostro` a libro fermo, senza ricompilare. Sopra le venti
ore non si va senza toccare anche la scadenza della fattura di garanzia
(86400 secondi, il default di LND: vedi sopra).
✅ IN SERVIZIO DAL 13 OTT 2026, 11:36 UTC (PRODUZIONE, «LA SALITA ALLA
-bar8», «COM'È ANDATA»; in fondo a questo documento, «LA `-bar8` IN
SERVIZIO»): fino ad allora chi pubblicava aveva i 1800 di tutti, l'ordine
moriva al primo tempo scaduto, e su Barattolo valeva la regola del 10 ott
(«mai a chi ha pubblicato»). BARATTOLO SEGUE DA SOLO: il numero lo leggono dal 38385
l'app (`scadenzaSec`: «Hai circa 30 minuti», il conto alla rovescia) e il
server (`_finestra_gesto_p2p`: «⏳ Hai 30 minuti», il promemoria a metà
tempo), e non c'è niente da girare sul VPS (CANTIERI, «Il promemoria
della garanzia»). PER TORNARE INDIETRO: la stessa riga a 900 e lo stesso
riavvio a libro fermo.
E LA PROVA È FATTA (6 set 2026, il primo ordine vero del coordinator:
25 EUR, Satispay, id `992e288e`): `expires_at` è caduto **168 ore
ESATTE** dopo la creazione — il 13 set alle 09:49:11 contro le 09:49:11
del 6 — quindi non «circa sette giorni» ma il valore del config
applicato al secondo.
E L'ESATTEZZA DICE ANCHE QUALE RAMO È PASSATO, ed è la parte che vale
più del numero: `now + expiration_hours`, cioè quello del client che
NON manda un `expires_at` suo. L'altro finirebbe sotto il clamp di
`max_expiration_days` e non avrebbe nessun motivo di combaciare al
secondo — quindi la leva girata è proprio quella che decide, e non una
che il client scavalca.
Nello stesso giro ha risposto anche il RITIRO: l'ordine è andato a
`canceled`.
⚠️ E IL 7 SET 2026 LO SCAMBIO VERO È ARRIVATO (con Alan, 7301 sats,
Revolut): presa in carico, invoice del compratore, hold invoice creata
e SALDATA, payout al venditore, dev fee calcolata e pagata. Cade
quindi la riga che stava qui — «un ordine creato e ritirato non ha mai
toccato una hold invoice» — e con lei il dubbio sul macaroon ristretto.
⚠️ MA «SCAMBIO RIUSCITO» NON VUOL DIRE «TIMER PROVATI», ed è la
distinzione da non perdere: il cronometro di `expiration_seconds` è
partito davvero (`taken_at` scritto) e si è chiuso col GESTO, mai
scadendo — quindi restano NON provati la SCADENZA di quella finestra,
la riconsegna al libro di `job_cancel_orders` e i 576 blocchi del
`cltv_delta`, che l'HTLC non è mai andato vicino a spirare. Si provano
solo lasciando scadere un ordine APPOSTA, e si agganciano alla tappa 8
del cantiere client P2P.
**LA SCADENZA È SUCCESSA DAL VIVO, il 10 ott 2026** (sulla `-bar6`, con
la finestra ancora a 900): un PayCode Barattozon da 111,80 €, garanzia
chiesta a chi aveva PUBBLICATO alle 10:04, non pagata, scambio annullato
dal coordinatore alle 10:20 — i 900 secondi più il giro dello scheduler —
e niente rimasto appeso. Quindi la SCADENZA di `expiration_seconds` dal
lato di chi ha pubblicato (l'ordine MUORE) è provata. Restano NON
provati l'altro ramo — manca chi ha PRESO, e l'ordine TORNA nel libro —
e i 576 blocchi del `cltv_delta`.
IL CONTO DELLO SCAMBIO, AL SATOSHI: 7338 sats entrati e 7264 usciti al
venditore, cioè **74 di fee** (l'1% del coordinator); il 30% di quei
74 fa 22,2 e la dev fee è **22**; il netto per noi è **+50**, cioè 74
meno i 22 della dev fee meno 2 di routing — il primo guadagno vero del
nodo. Anche il CANALE torna al satoshi: i 660 che sembravano mancare
sono i due anchor output (2 × 330), che una chiusura cooperativa
restituisce interi.

LA DEV FEE SI IMPIANTA SUL CIRCUITO FREDDO (7 set 2026, il difetto che
ha aperto il cantiere, ed è UPSTREAM). Chiuso lo scambio, il journal
si è riempito di `Found 1 orders with unpaid dev fees` +
`NoAPIResponse` **una volta al minuto** — ~4.300 righe al giorno, che
rendono il journal illeggibile e che la ronda NON vede: la sua è una
domanda sulla superficie, non sui log.
LA DEV FEE È IL 30% DELLA NOSTRA FEE e va a un Lightning address
**hardcoded nel codice di Mostro**, non in `settings.toml`: il
venditore non ci perde niente, e infatti quei 22 sats erano già stati
trattenuti da un affare CONCLUSO.
LA DIAGNOSI ROVESCIA I DUE SOSPETTI OVVI, ed è la parte da tenere: non
è il DNS (nella misura fredda pesa `0.138s` su 10,6 secondi) e non è
il nostro DROP del FORWARD — **è il TEMPO**. La risoluzione LNURL è
HTTPS su **DUE domini diversi** (`walletofsatoshi.com` per il
`.well-known`, `livingroomofsatoshi.com` per il callback), e
`src/lnurl.rs` ha tre budget come `const` nel binario: request **4s**,
connect **2s**, DNS **2s**. Un circuito Tor FREDDO misura **10,6
secondi** — `dns=0.138s connect=0.138s tls=10.336s` — e tutto il tempo
se lo mangia il TLS; a caldo gli stessi giri stanno a **0,95s** e
**0,83s**. Quattro operazioni su due domini, ognuna col suo circuito
da scaldare.
⚠️ E `time_connect` MENTE SOTTO IL PROXY TRASPARENTE, che è la
trappola in cui si cade leggendo le misure: col `TransPort` il kernel
chiude la stretta di mano locale appena il SYN tocca il socket in
ascolto, **prima che Tor guardi il pacchetto** — quindi `connect` è
quasi zero e il lavoro vero del circuito compare tutto in
`time_appconnect`, cioè nel TLS. Chi guarda il solo `connect` conclude
che la rete va benissimo.
**NON È CONFIGURABILE**: quei tre numeri non stanno in
`settings.toml`, si cambiano solo ricompilando o convincendo upstream.
E IL 7 SET HA PAGATO PER UN ACCIDENTE: avevo scaldato io il circuito
con `curl` mentre facevamo le misure, e nella finestra calda il
pagamento è passato (LND dice SUCCEEDED, la riga in `orders` ha
`dev_fee_paid 1` e lo stesso hash). **Alla prossima si impianta
uguale**, e non è una previsione: è la stessa strada con gli stessi
budget.
⚠️ E NON È SOLO LA DEV FEE, che è la scoperta più larga del giro:
`is_valid_invoice` prova PRIMA il Lightning address e l'LNURL e solo
dopo ripiega sulla bolt11, quindi un TRADER che dà un indirizzo
Lightning finisce sullo **stesso** `lnurl_get` con gli stessi tre
budget — e a circuito freddo si prende un `InvoiceInvalidError` al
momento della VALIDAZIONE, cioè non riesce nemmeno a consegnare la sua
invoice, senza che niente gli dica perché. La dev fee almeno ritenta
da sola per sempre; lui no.
LA CURA LOCALE È `dev_fee_percentage = 0` e vale per gli scambi
FUTURI: la percentuale si consulta quando la fee si CALCOLA, quindi
non ripulisce una riga che ce l'ha già scritta. È un tappo, non la
cura — quella è l'issue upstream, e il giorno che si rimette il 30% il
difetto torna identico.
⚠️ LA STRADA SCARTATA, e non si riproponga senza un motivo nuovo:
esentare i due domini da Tor. L'indirizzo di destinazione è la
costante hardcoded di Mostro, quindi **un IP che bussa a quel endpoint
si dichiara coordinator Mostro** — cioè si perde esattamente ciò per
cui il nodo esce solo da Tor.
E `docs/DEV_FEE.md` DICE UN'ALTRA COSA dal codice («LNURL: 15s»): vale
il codice, e la discrepanza è nell'issue.

LA CAUZIONE DI CHI PRENDE SI ACCENDE CON LA `-bar6` (1 ott 2026, cantiere
B, decisione di Andrea; il verbale in CANTIERI, «La cauzione di chi
prende», la liturgia in PRODUZIONE, «LA SALITA A MOSTRO 0.19.0», punto
7-bis). Le due righe qui sopra — «`bond_enabled` false (coerente con
`[anti_abuse_bond]` commentata)» e «oggi abbandonare non costa NULLA:
`[anti_abuse_bond]` è opt-in e sul nostro nodo è tutta commentata» —
restano VERE fino a quel riavvio, e da lì DIVENTANO FALSE per il solo
metodo «Contanti» (e DAL 10 OTT 2026, con la `-bar7` e la patch 0010,
solo a chi prende SCEGLIENDO «Contanti»: la scelta viaggia nel take come
`Payload::Order.payment_method`, e un «SEPA, Contanti» preso con SEPA non
chiede niente — PRODUZIONE, «LA SALITA ALLA -bar7»; ✅ LA `-bar7` È IN
SERVIZIO, riferito da Andrea il 12 ott 2026: vedi in fondo, «LA -bar7 IN
SERVIZIO»): la patch 0008 del fork limita l'`anti_abuse_bond` ai
metodi che `only_payment_methods` nomina, e le tarature sono
`amount_pct = 0.03`, `base_amount_sats = 1000`, `apply_to = "take"`,
`slash_on_waiting_timeout = false`, `hold_invoice_expiration_window =
900` (che nella 0.19.0 è SOLO la scadenza della richiesta di cauzione,
#999). Il 38385 le annuncia (`bond_enabled true`, i sette `bond_*`, il
nostro `bond_only_payment_methods Contanti`). Quel che NON cambia: i
900 secondi restano 900 (fino al 10 ott 2026: da allora 1800, vedi «DAL
10 OTT 2026 SONO 1800»), e il timeout che brucia resta SPENTO — la
cauzione si perde solo per la direttiva del moderatore (`bond_resolution`),
quindi «la cura per "15 minuti sono pochi" sono i bond» resta un
cantiere DOPO, quando le cauzioni sono provate. Restano NON provati sul
nodo vero, finché non si fa la prova a due telefoni della liturgia: la
richiesta lasciata scadere (LND la cancella a 900 s, mostrod riporta
l'ordine a `pending` senza dire niente al taker), la corsa fra due
prese (vince chi paga per primo), la bruciatura e il payout della metà
(`add-bond-invoice`, 15 giorni), e il `cargo test` dei due moduli della
0008.

LA `-bar7` IN SERVIZIO (riferito da Andrea il 12 ott 2026; la liturgia in
PRODUZIONE, «LA SALITA ALLA -bar7», il perché in CANTIERI, «La cauzione
sul metodo scelto» e «Le scritte sui contanti solo a «Contanti» scelto»).
Il nodo gira `mostro:v0.19.0-bar7`: le otto patch più la 0010, la
cauzione decisa sul metodo che chi prende DICHIARA nel take. Alla salita
i 17 ordini del database erano intatti e nei log nessun errore. Sul VPS
la leva `P2P_CAUZIONE_SUL_METODO` è ACCESA: il client manda il metodo
scelto (`Payload::Order.payment_method`) e promette la cauzione solo a
chi sceglie «Contanti». Provato da Andrea dal telefono: su un ordine
misto, scegliendo SEPA la cauzione non compare, scegliendo Contanti sì.
`settings.toml` non è cambiato (nessuna settings nuova, nessuna
migrazione), il 38385 nemmeno. RESTA NON PROVATO, finché non c'è uno
scambio vero: un «SEPA, Contanti» preso con SEPA che arriva alla garanzia
SENZA `pay-bond-invoice`; lo stesso preso con Contanti CON la cauzione;
un intervallo preso con la cifra scelta dentro `Payload::Order`
(`fiat_amount`); e quel che già mancava della cauzione (la richiesta
lasciata scadere, la corsa fra due prese, la bruciatura e il payout).
NEI TEST DELLA BUILD è caduta una prova, e non è del fork:
`util::tests::connect_nostr_builds_client_with_configured_relays`, di
upstream, che dipende dall'ordine dei test (le impostazioni globali dei
test sono un `OnceLock`, e cinque moduli di upstream le impostano coi
relay vuoti); da sola passa. La liturgia la lancia in un giro suo, e il
perché sta al suo punto 3. IL ROLLBACK resta quello scritto là: la leva
a `False` sul VPS e riavvio, e se serve la riga dell'immagine a
`mostro:v0.19.0-bar6` con `docker compose up -d mostro` a libro fermo.

LA `-bar8` IN SERVIZIO (13 ott 2026, cantiere `mostro-bar8`; i comandi li
ha lanciati Andrea; la liturgia e il verbale in PRODUZIONE, «LA SALITA
ALLA -bar8», il perché in CANTIERI, «Il tempo di chi pubblica» e «La
-bar8 in servizio»). Il nodo gira `mostro:v0.19.0-bar8`: le otto patch,
la 0010, e sopra la 0011 (il tempo di chi pubblica) e la 0012 (la
disputa che il coordinatore apre da solo). Nel `settings.toml`, sezione
`[mostro]`: `expiration_seconds = 1800` (chi prende, non toccato),
`maker_expiration_seconds = 10800`, `maker_timeout_limit = 2`. Nessuna
migrazione. Libro fermo undici secondi (11:36:00-11:36:11 UTC), a zero
scambi aperti. Provato da Andrea con due account: a chi ha pubblicato
«Hai ancora 2:59:29 per bloccare i sats, poi l'ordine torna nel libro».
DA QUEL MINUTO LA PENALITÀ A CHI PUBBLICA È ACCESA DA SOLA sul VPS (la
leva `P2P_TEMPO_DI_CHI_PUBBLICA` lo era dal 12 sera): il server la conta
perché il 38385 annuncia il tempo lungo.
I RELAY DEL NODO SONO TRE dallo stesso giorno (secondo riavvio,
11:47:43-11:47:53 UTC): `relay.barattolo.store`, `relay.mostro.network`,
`nos.lol`. `relay.damus.io` è uscito dal `settings.toml`.
⚠️ IL SORGENTE SUL NODO (`~/nodo/mostro-src`, undici commit sopra
`v0.19.0`) NON È QUELLO CHE IL REPO RICOSTRUISCE: le 0005 e 0007 del nodo
sono quelle del 30 set-1 ott, senza i tre ritocchi dell'audit scritti nel
repo il 1 ott (M6: il segreto degli eventi senza il ripiego su quello
dello sconto; M4: l'interruttore della domanda dello sconto; B6: il tetto
di 64 KB alla risposta). Il codice della 0011 e della 0012 è identico a
quello del repo; cambiano solo le posizioni dentro `barattolo_eventi.rs`.
Si porta con la build della 0.19.3; per la M6 va guardato prima che sul
nodo ci sia `BARATTOLO_EVENTI_SEGRETO`: se oggi vale il ripiego, senza
quella gli eventi si spengono.
RESTA NON PROVATO: l'ordine che TORNA nel libro alla prima mancata
risposta di chi ha pubblicato e si toglie alla seconda (FASE 5 della
liturgia: la prova del 13 si è fermata al conto alla rovescia, e si è
chiusa con l'annullo di chi aveva preso); la disputa automatica a ~92
ore; il ritorno alla `-bar7` (i due file `.prima-bar8` e `up -d`).

LA 0.20.2 IN SERVIZIO DAL 30 OTT 2026, immagine `mostro:v0.20.2-bar9`
(dal 19 nov la `-bar10`, sotto, «LA 0013»; preparata il 29 ott, cantiere `mostro-0202`; la liturgia in PRODUZIONE,
«LA SALITA ALLA 0.20.2», il perché in CANTIERI, «Mostro 0.20.2»; com'è
andata sul nodo in fondo a questa voce). Upstream ha fatto sei versioni
dalla nostra 0.19.0 (la `v0.20.2` è del 28 ott). Il fork è stato
RIFATTO DA CAPO sul tag nuovo coi patcher del repo — quindi porta anche
i tre ritocchi dell'audit del 1 ott (M6, M4, B6) che il nodo non ha mai
avuto — e, per la prima volta, compilato e provato nel cloud prima del
nodo. Tre ancore su undici patch erano cambiate (0007, 0008, 0011); una
riga di un test della 0007 nel repo (`endpoint_from` a tre argomenti,
avanzo della M6) non compilava e nessuno l'aveva mai visto: corretta.
COSA PRETENDE DAL NODO: la riga `bond_cltv_delta` in `[anti_abuse_bond]`
(fra 721 e 864 col nostro `hold_invoice_cltv_delta = 576`; proposta
744; senza la riga `mostrod` NON PARTE, #1085); undici migrazioni al
database, quindi il ritorno alla `-bar8` vuole la copia di prima; e
`BARATTOLO_EVENTI_SEGRETO` nel compose (M6: senza, gli eventi al server
si spengono). COSA PORTA AGLI UTENTI: la cura #910 (il venditore che
paga la garanzia e annulla subito dopo non si riprende più i sats
mentre al compratore arriva «pagato»), le dispute scritte tutte insieme
(#923), i limiti in sats contati col premio (#1095), l'arrotondamento
al sat più vicino (#1090), la manutenzione DA SOLA dopo 10 minuti di
LND non sincronizzato e i pagamenti rimandati senza bruciare i
tentativi del compratore (#1065), l'evento di salute kind 38389 ogni
60 s sui relay (`[health]`, di serie acceso; coi tag grossolani
pubblici e i numeri cifrati solo per un `watchdog_pubkey`, che non
mettiamo). Il protocollo resta la versione 2, il 38385 tiene gli stessi
tag (più `escrow_mode`, `escrow_deadline_margin_blocks`). GLI USDT e il
bitcoin on-chain come valuta dell'ordine (`[price.providers.pegged]`,
#1083 e #1091) restano SPENTI: `fiat_currencies_accepted = ['EUR']`
chiude anche gli ordini a prezzo fisso; si accendono solo con una
decisione di Andrea e il cantiere dell'app (p2p-usdt).

COM'È ANDATA SUL NODO (30 ott 2026, 07:37 UTC, cantiere `mostro-bar9`):
la liturgia intera un comando alla volta, tutta incollata da Andrea; il
29 sera il comando del cambio si è fermato da solo su uno scambio
PayPal `active` preso cinque minuti prima (il freno conta prima di
toccare), e la mattina dopo, a libro fermo e con la copia del database
rifatta, il cambio ha tenuto il libro fermo dodici secondi. Undici
migrazioni entrate, `bond_cltv_delta = 744` in fondo al `settings.toml`,
`mostrod --version` → `mostro p2p 0.20.2`, eventi al server accesi,
primo evento di salute 38389 pubblicato, journal del VPS pulito; alle
07:44 la prova di Andrea con due account, uno scambio intero: «funziona
tutto». Notato:
`blockchain.info` risponde 403 all'uscita Tor (uno dei quattro fornitori
del prezzo; gli altri tre rispondono). Le impronte del segreto degli
eventi sono uguali sul nodo e sul VPS (`12b649c7`): la prima lettura
diversa era il `\x27` nel `tr` del comando, corretto in PRODUZIONE. I
numeri e il registro: PRODUZIONE, «LA SALITA ALLA 0.20.2», «COM'È
ANDATA SUL NODO».

LA 0013, IL TEMPO PER PAGARE (preparata il 18 nov 2026, cantiere
`tempo-pagamento`; SUL NODO DAL 19 NOV 2026, 08:28 UTC, immagine
`mostro:v0.20.2-bar10`, le dodici patch). Il problema: uno scambio `active` lo chiude solo il guardiano della
garanzia, a ~92 ore, e chi prende e sparisce tiene fermi i sats di chi
vende per quattro giorni. Ora chi pubblica su Barattolo sceglie il tempo
su un orologio, da 15 minuti a 24 ore, e il nodo lo CHIEDE al server ogni minuto (`BARATTOLO_FINESTRA_URL`
→ `/api/p2p/finestre`, bearer `BARATTOLO_FINESTRA_SEGRETO`, un segreto
suo come vuole la M6): allo scadere, con l'ordine ancora `active`, annulla
la hold invoice come il ramo `Active` del guardiano e lo dice al server
(`expired` / `payment-window`). Il tempo parte quando il NODO vede lo
scambio attivo, quindi mai prima di quel che legge chi compra. Quel che
un server compromesso ottiene: annullare uno scambio attivo dopo almeno
un quarto d'ora, coi sats che tornano a chi vende; mai un `fiat-sent`, mai una
disputa. Senza le due variabili è inerte, e un server muto vale «nessun
tempo». Nessuna migrazione: la tabella sua la crea il modulo, e il
ritorno alla `-bar9` è il solo cambio d'immagine. Compilata e provata
nel cloud: albero `bdad9c34`, 2001 prove `cargo` verdi (PRODUZIONE, «LA
`-bar10`»).

COM'È ANDATA SUL NODO (19 nov 2026, 08:28 UTC, cantiere `tempo-pagamento`):
la build il 18 sera, un comando alla volta e tutto incollato da Andrea —
lo stesso albero del cloud (`bdad9c34`), 740/0/1 e 90/0, il compose con
le due righe FINESTRA e l'impronta del segreto uguale al VPS. Il cambio
si è fermato da solo il 18 su due scambi aperti; il 19, chiuso il
pagamento da 296.399 sats, ne restava uno `active` abbandonato da 21 ore
(362.235 sats, SEPA Instant), e Andrea ha scelto di cambiare con lui nel
libro: undici secondi di libro fermo. Col riavvio è entrata anche la riga
del contante per posta nel `settings.toml` (`only_payment_methods =
["Contanti", "Contante per posta"]`). Log pulito, il cursore «Tempo per
pagare» compare su Lightning. RESTA DA GUARDARE: lo scambio rimasto lo
chiude il guardiano della garanzia verso domenica 22 (nessun tempo per
pagare: è nato prima). NON PROVATI: l'annullo allo scadere (la prova da
15 minuti fra due account) e la cauzione col contante per posta (leva
`P2P_POSTA_ATTIVO` spenta in produzione). I numeri: PRODUZIONE, «LA
`-bar10`», «COM'È ANDATA SUL NODO».

LA 0014, L'ORDINE CHE TORNA NEL LIBRO (preparata il 19 nov 2026, cantiere
`ritorno-nel-libro`; NON ANCORA SUL NODO: `docs/DA-FARE-ANDREA.md`, voce
26, immagine `-bar11`). Andrea: «No, perché sparisce, scusa? Non dovrebbe
tornare nel libro». Allo scadere del tempo per pagare senza «Ho inviato»
il nodo non chiude più lo scambio: fa il ramo che mostrod fa già per chi
prende e non manda la fattura (taker-timeout) — annulla la hold invoice,
rimette l'ordine `pending` nel libro col suo 38383, libera la cauzione di
chi aveva preso e lo dice al server con `expired` /
`payment-window-republished` (per il server è `tornato`). E il tempo parte
DAL RECAPITO: il server risponde `null` finché chi vende non ha toccato
«Indica dove ricevere gli euro», e il nodo conta da quando riceve il
numero (`started_at`, colonna nuova della sua tabella), al più un minuto
dopo. Quel che un server compromesso ottiene in più rispetto alla 0013:
niente — rimettere nel libro è più mite che annullare, e i sats tornano
comunque a chi vende. Nessuna migrazione di mostrod: la colonna la
aggiunge il modulo, e il ritorno alla `-bar10` è il solo cambio
d'immagine (la colonna la ignora). Compilata e provata nel cloud: albero
`b45281d5`, 2005 prove `cargo` verdi, 4 ignorate.
