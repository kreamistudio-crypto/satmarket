# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Dove sta il resto

Tre file in `docs/`, e NON sono import: si aprono quando servono.
- `ARCHITETTURA.md` — com'è fatto: le parti, le rotte pubbliche, i
  giudici unici, e il perché di ogni pezzo.
- `CANTIERI.md` — perché è fatto così: un paragrafo per cantiere, in
  ordine di tempo, con le decisioni, le strade scartate e le lezioni.
- `PRODUZIONE.md` — la macchina, la catena del deploy, le procedure.

Non c'è un indice e non deve nascerne uno: si cerca per NOME.
`grep -n "sconto carrello" docs/*.md` — ogni voce porta il suo nome
nella prima riga, e i rimandi già scritti dappertutto nel codice e in
questi file («vedi Architettura, "IL SUPPLEMENTO PER PEZZO"») sono
indirizzi che dopo il trasloco funzionano identici.
PRIMA di toccare qualcosa, cercalo lì: se un cantiere l'ha già deciso,
la decisione ha un perché scritto, e rovesciarla senza saperlo è il
modo in cui si rifà un errore già pagato.

## Produzione

- VPS Hetzner Helsinki `46.62.162.103`, Ubuntu 26.04, servizio systemd
  `barattolo` (uvicorn su 127.0.0.1:8080 dietro Caddy con HTTPS).
- Dominio: https://barattolo.store — Bot: @ilbarattolobot (BotFather URL
  con `?v=2`, innocuo). Header anti-cache già attivi su `/` e
  `/miniapp.html`: non rimuoverli.
- Il tetto del barattolo (`MAX_PREFERITI`) ha il default 10 nel CODICE
  dall'ago 2026, ma una riga esplicita nel config del VPS vince su di
  lui — e finché c'è, il tetto nuovo non entra in vigore. Si guarda
  PRIMA del deploy, in sola lettura:
  `grep -n "MAX_PREFERITI" ~/satmarket/config.py` — nessuna riga = vale
  il default e non c'è niente da fare; una riga con 20 = va cambiata a
  mano (o cancellata) e poi riavviato.
- DEPLOY AUTOMATICO (ago 2026): commit+push su main, e basta. Entro un
  minuto è online — se la CI è verde. Config e database NON viaggiano
  mai (restano fuori dalla repo, e `git reset` non li tocca).
  IL VPS TIRA, NON VIENE SPINTO, ed è una decisione di SICUREZZA e non
  di comodità: nessuna chiave di quella macchina sta nei secret di
  GitHub, quindi chi compromette GitHub — o una action di terzi — non
  arriva al nodo Lightning. Per la stessa ragione «la CI è verde» non
  è una domanda da fare a un'API con un token in mano: è il fatto
  stesso che il ref si sia mosso. Un commit rosso resta su main e in
  produzione non ci arriva mai.
  IL FRENO È LA RIGA CHE SI DIMENTICA: dopo un rollback il ref `pronto`
  resta AVANTI, quindi al giro dopo — fra un minuto — si riproverebbe
  lo STESSO commit rotto, e poi ancora, riavviando il mercatino ogni
  sessanta secondi per sempre. Il commit bocciato si timbra in
  `.deploy-bocciato` e non si riprova da solo: per riprovarlo si
  spinge un commit nuovo (che è anche quel che si dovrebbe fare)
  oppure si lancia `./deploy.sh --forza` a mano, guardando.
  La catena per intero — i tre pezzi, `/api/salute` che tocca il
  database apposta, la copia in /tmp, il backup pre-deploy e i comandi
  a mano — sta in `docs/PRODUZIONE.md`, con le procedure (le leve del
  P2P, l'import Nostr, l'anello, la ricategorizzazione, `/setdomain`) e
  le dipendenze pip.
- Webhook del bot: `TELEGRAM_WEBHOOK_SEGRETO` nel config del server
  (stringa casuale) e al riavvio si registra da solo (riga «🔔 Webhook
  Telegram» nel journal). ATTENZIONE: mai avviare MODALITA_COLLAUDO=False
  col BOT_TOKEN vero fuori dal VPS — ruberebbe il webhook (e quindi i
  /start) alla produzione.

## Il nodo Mostro (un'ALTRA macchina)

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
chiaro; chiusa con `iptables -A FORWARD -s 172.28.1.5 -j DROP` **dentro
il compose, riga 48** — a mano sparirebbe al primo `up -d` e il buco si
riaprirebbe in silenzio — provata con `--force-recreate`. Nessuno dei
due era un errore di configurazione nostro: il primo era nel codice, il
secondo era il residuo che le tre regole di redirect non coprivano.

**LA 0.18.7 (4 set 2026) NON C'ENTRA COL NOSTRO GIRO**, e va scritto
perche' la domanda torna: il changelog e' pagamenti, timelock, dev-fee,
annullamenti e contatori di drain — **niente sulla verifica della
firma, niente sul trasporto, e mostro-core resta 0.14.6**, cioe' la
ricetta che il nostro client ricalca non si e' mossa. L'aggiornamento
resta una cosa a parte e non un pezzo di diagnosi.
⚠️ UNA SOLA VOCE MERITA UNO SGUARDO IL GIORNO CHE SI SALE: `c6efb2d`
(#952) rinomina il campo con cui l'evento `info` annuncia la finestra
della hold invoice (`invoice_expiration_window`). Il client lo legge
(`mostroInfoP2P`), quindi si guarda quel nome PRIMA di aggiornare, o la
finestra torna a essere quella di riserva senza che niente fallisca.

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
senza IP lock (oggi il file non esce dalla macchina); LLMNR sulla 5355
(superficie che non paga affitto); il pull non è sorvegliato (il
server sa che l'archivio esiste, non che il PC l'abbia preso); il DROP
del FORWARD è solo in `iptables` e **non in `ip6tables`**, e va messo
DENTRO il compose accanto alla riga 48 o evapora al primo `up -d`; la
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
(verificata sul `settings.tpl.toml` del tag v0.18.6, la versione del
nodo): è in BLOCCHI, 144 ≈ 24h — il numero che hanno detto — e 3
giorni fanno 432. Il margine `escrow_deadline_margin_blocks` (24)
resta com'è, quindi la finestra UTILE è sempre ~4 ore più corta
dell'orizzonte: mostrod molla la presa PRIMA che LND sia costretto a
chiudere il canale per salvare l'HTLC. GIRATA A 432 il 6 set 2026, a
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
168, `expiration_seconds` 900, `hold_invoice_cltv_delta` 432 — le tre
leve girate il 6 set 2026 si leggono **DAL LIBRO PUBBLICO** e non piu'
dal solo `settings.toml`, cioe' sono verificate dal lato di chi legge e
non da quello di chi le ha scritte. Piu' `bond_enabled` false (coerente
con `[anti_abuse_bond]` commentata), `maintenance_mode` false,
`max_order_amount` 100000 e **`fee` 0.01** — l'1% del coordinatore, che
e' un numero che il cantiere dovra' mostrare a chi scambia.
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
codice: attribuisce il mestiere a una voce inerte e lo nega a quella
viva.
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
• `hold_invoice_expiration_window` (300) **non la legge NESSUNO: è
configurazione morta in v0.18.6.** Dichiarata nella struct, scritta
dal wizard, presente in una fixture di test, e in nessun altro posto
— censite tutte e 25 le `.rs` che potrebbero nominarla. Toccarla non
fa niente, e il suo commento nel template descrive il mestiere di
`expiration_seconds`.
• `hold_invoice_cltv_delta` (432) alimenta SOLO il `cltv_expiry` della
hold invoice (`create_hold_invoice` in `src/lightning/mod.rs`, che
l'`expiry` della fattura non lo tocca proprio): è quanto l'HTLC resta
appeso DOPO il pagamento, e la finestra utile la dà
`escrow_guard_window_secs` — `(432−24)×600 = 68 ore`.
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
la riconsegna al libro di `job_cancel_orders` e i 432 blocchi del
`cltv_delta`, che l'HTLC non è mai andato vicino a spirare. Si provano
solo lasciando scadere un ordine APPOSTA, e si agganciano alla tappa 8
del cantiere client P2P.
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

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI chiedere o gestire nsec (chiave privata Nostr) degli utenti.
   Decisione permanente: mai custodia di segreti altrui, mai firme che
   richiedano di consegnare chiavi al server. La scala di quel che è
   APPROVATO — badge npub auto-dichiarato, verifica con nota pubblica,
   login con firma di sfida, wallet NWC solo-nel-browser, DM NIP-17,
   sessione bunker NIP-46 conservata — col perché di ognuna e quel che
   è stato RESPINTO (il secret NWC salvato sul server, anche cifrato)
   sta in `docs/ARCHITETTURA.md`, alla voce «LA SCALA NOSTR APPROVATA».
3. Il server pubblico non monta MAI StaticFiles su una directory
   (config e .git diventerebbero pubblici — falla già successa e
   chiusa): ogni file servito ha la sua rotta esplicita, e i nomi che
   arrivano dal client passano da una whitelist. Dall'ago 2026 non c'è
   più NESSUN mount: anche `/foto/*`, l'ultimo, è una rotta con la sua
   whitelist di FORME (`NOME_FOTO`). L'elenco completo sta in
   `docs/ARCHITETTURA.md`, alla voce «LE ROTTE PUBBLICHE». La regola è
   verificabile e non solo raccomandata: una sentinella di `prove.py`
   fallisce se in server.py ricompare `app.mount(` o l'import di
   StaticFiles, e una seconda conta le rotte-pagina contro l'elenco
   scritto a mano di `prove_anteprime`, perché una rotta pubblica nuova
   non resti senza sorveglianza.
4. Stati ordine: creato | locked | shipped | delivered | confirmed |
   released | dispute | return_pending | return_shipped | refund |
   refunded | annullato. Non inventarne di nuovi senza aggiornare
   frontend (STATES, stepper cassaforte) e notifiche.
5. Solo l'ACQUIRENTE può segnare "consegnato" (anti-frode venditore).
   Dall'ago 2026 A MANO non la scrive più NESSUNO: il bottone «È
   arrivato» del compratore è stato tolto perché puniva chi lo premeva
   (voce sua sopra). LA REGOLA RESTA, ed è quella che il giorno del
   tracking verificato impedirà al VENDITORE di scriverla: quella data
   la scriverà il corriere, cioè un fatto, mai la parte che ci rimette.
   Sul digitale la scrive la rivelazione del codice, che è un gesto del
   compratore. Il venditore è protetto dall'auto-sblocco a 10 giorni
   (oggi disarmato: al suo posto il promemoria) e dal sollecito
   (max 1 ogni 24h).
6. Testare sempre in locale (MODALITA_COLLAUDO=True, tre identità finte:
   Compratore 111, Venditore 222, Admin 999) prima del deploy.
   In produzione MODALITA_COLLAUDO deve restare False.
7. Stile del codice esistente: commenti e nomi in italiano, tono caldo,
   niente refactoring di massa non richiesti, diff piccoli e verificabili.
8. A fine cantiere, PRIMA del commit finale: la voce del cantiere —
   cosa si è deciso, i perché, le strade scartate, cosa è stato provato
   e cosa resta da guardare — va in fondo a `docs/CANTIERI.md`.
   L'architettura va in `docs/ARCHITETTURA.md`, le procedure di
   produzione in `docs/PRODUZIONE.md`. Questo file si tocca SOLO se è
   cambiata una REGOLA di qui: è la ragione per cui era arrivato a
   28.593 righe, e rientra intero a ogni /compact di ogni sessione.
   Proponilo come commit separato, senza aspettare che Andrea lo
   chieda. Ritocchi minori (testi, tarature, fix) non lo richiedono.
9. Lessico dell'escrow (lug 2026): nei testi per gli utenti si dice
   sempre «deposito di garanzia» — «(escrow)» solo nella prima
   spiegazione lunga di ogni contesto; azione = «🔒 Compra in
   sicurezza» (era «Compra protetto», cambiata lug 2026);
   MAI «assicurato». «Escrow» resta solo dove il pubblico è bitcoiner:
   memo della invoice LNbits e testi verso Nostr (footer NIP-99,
   presenta_release). Il barattolo 🫙 è dei preferiti, mai metafora
   dell'escrow.

## Adesso

Lanciando in rodaggio su community italiana, senza limiti di prezzo
attivi (la leva `TETTO_SATS_ANNUNCIO` esiste ma è spenta).
Quel che è stato fatto, cantiere per cantiere coi suoi perché, sta in
`docs/CANTIERI.md`. Quali leve sono ACCESE lo dice il pannello
«⚙️ Stato delle leve» dell'admin, che chiede al valore VIVO e non alla
costante nel codice — che è la trappola in cui una riga esplicita nel
config del VPS fa cadere.

Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri (che porterà la MAPPA dei punti nel
varco-mappa della pagina), escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.

Da riprendere quando i cantieri in corso saranno chiusi (ago 2026,
segnati da Andrea — non sono ancora decisi, sono da riprendere):
- il LUOGO DEL RITIRO A MANO salvato e richiamato a ogni annuncio: il
  gemello dei punti di ritiro salvati, per chi consegna in zona sempre
  nello stesso posto;
- «I MIEI ANNUNCI» resa più fruibile;
- i PRIVILEGI DEI PIONIERI (la coorte esiste già, non dà ancora niente);
- il LOCKER DI RISERVA: un secondo punto se il primo non va.
