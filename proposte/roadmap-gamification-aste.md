# Roadmap — gamification completa, poi aste con escrow

Documento di lavoro (lug/ago 2026). Decisioni prese con Andrea, coi
motivi — comprese quelle scartate, che fra sei mesi sono la parte che
serve davvero.

Punto di partenza: la gamification è a **parte 1 (feedback e stelle)** e
**parte 2 (distintivi 🏅)**, entrambe fatte. Le aste sono terreno nuovo,
ma il motore delle **offerte** e l'**escrow** esistono già e sono i due
mattoni su cui poggiano — un'asta non è un cantiere da zero, è la
macchina a stati delle offerte con un vincitore automatico al posto
della stretta di mano.

---

# PARTE A — Gamification

## A0. La differenza che governa tutto

Distintivi e rating sono **auto-riparanti**: si RICALCOLANO dai dati veri
(`controlla_distintivi`, `_ricalcola_rating`), quindi una passata
retroattiva all'avvio rimette tutto in pari e un bug non lascia
cicatrici.

**Gli XP no.** Una visita giornaliera è un evento: se non lo scrivi
quando succede, è perso per sempre. Quindi gli XP hanno bisogno di un
REGISTRO, e il registro ha bisogno di essere idempotente per
costruzione — non per attenzione di chi scrive i ganci.

È la prima cosa da fare bene, ed è la sola parte di questa roadmap che
non perdona.

---

## A1. XP — schema

```sql
xp_eventi(
  id INTEGER PRIMARY KEY,
  tg_id INTEGER,
  tipo TEXT,            -- 'ordine', 'visita', 'feedback', 'distintivo'…
  punti INTEGER,
  riferimento TEXT,     -- 'ordine:42:venditore', 'giorno:2026-08-04'
  creato INTEGER,
  UNIQUE(tg_id, tipo, riferimento)
)

utenti.xp                INTEGER DEFAULT 0   -- somma (cache)
utenti.xp_ultimo_giorno  TEXT DEFAULT ''     -- data locale ultima visita
```

**Il registro è la verità, `utenti.xp` è la cache.** Ricalcolabile con
una `SUM()`, esattamente come `_ricalcola_rating` rifà i conti dalla
tabella `feedback`. Conseguenze gratis:

- `esegui_fusione` somma i due registri e ricalcola: nessun caso speciale
- un bug nei ganci si ripara con un ricalcolo, non con una migrazione
- gli XP di un ordine annullato a mano si tolgono cancellando la riga

La **`UNIQUE(tg_id, tipo, riferimento)` è il giudice dell'idempotenza**, e
questo è il punto: non si chiede a chi scrive un gancio di ricordarsi
«l'ho già dato?». Un retry, un doppio gancio, un riavvio a metà, un
moderatore che rilancia una funzione — tutti sbattono contro il vincolo
e non pagano due volte. `INSERT OR IGNORE`, il modo dei distintivi.

Gancio unico, fail-open, **sempre dopo il commit**:

```python
def assegna_xp(tg_id, tipo, punti, riferimento) -> bool
```

Vive accanto a `premia_distintivi`, e come lui non deve MAI poter far
fallire ciò che l'ha chiamato: un errore negli XP non tocca uno sblocco
di sats.

---

## A2. XP dagli ordini — la formula

**Decisa con Andrea, ago 2026:**

```python
FISSO_XP_ORDINE = 10        # ogni affare concluso conta, anche quello da 3 €
XP_PER_EURO     = 1         # un euro, un punto
XP_RUOLO        = {'venditore': 1.0, 'compratore': 0.6}

XP = (FISSO_XP_ORDINE + euro_ordine * XP_PER_EURO) * XP_RUOLO[ruolo]
```

**NESSUN TETTO**, ed è una decisione esplicita. Un acquisto da 4.000 €
su un mercatino appena nato non è un'anomalia da limare: è qualcuno che
ha affidato quella cifra al nostro deposito di garanzia. Gli XP
ripagano la fiducia, e la fiducia grossa vale di più.

Il venditore prende più del compratore perché **vendere è il lato
scarso**: un mercatino muore per mancanza di merce, mai di curiosi.

### Frequenza e importo valgono ENTRAMBI

Dodici libri da 10 € e un solo oggetto da 900 € sono due meriti diversi
e tutti e due veri: sul volume ci guadagniamo le fee a ogni
transazione, sull'importo grosso ci guadagniamo la fiducia. La formula
li premia entrambi senza doverli pesare l'uno contro l'altro — il fisso
paga la frequenza, il variabile paga l'importo.

### La base è il TOTALE, spedizione compresa

`euro_ordine` si calcola su **`ordini.prezzo_sats` intero**: articolo +
spedizione + protezione. Chi paga 300 € di spedizione ha speso 300 €, e
si premia quello che è stato speso.

```python
def euro_ordine(prezzo_sats: int, cambio_eur: float) -> float:
    if cambio_eur <= 0:          # cambio mai arrivato
        return 0.0
    return prezzo_sats / 100_000_000 * cambio_eur
```

Il cambio **c'è già e non costa niente**: `ordini.cambio_eur` lo scrive
`_sblocca_sats` alla chiusura per l'export contabile, ed è esattamente
il momento in cui gli XP si assegnano. Zero colonne nuove, zero
chiamate a CoinGecko nel percorso caldo.

Cambio a 0 (ordine storico, CoinGecko muto) → **resta il solo fisso**.
Onesto: meglio 10 XP invece di 310, che un numero inventato. È la stessa
regola per cui un avviso di ricerca in EUR non scatta senza cambio.

### Il gancio

Uno solo, in `_sblocca_sats`, dopo il `con.commit()` e accanto a
`premia_distintivi` — dove il cambio è appena stato scritto e le due
parti sono note:

```
riferimento = f"ordine:{id}:venditore"   e   f"ordine:{id}:compratore"
```

**Solo `released`.** Mai su `refunded`: rimborsato vuol dire che la
merce è tornata indietro e lo scambio non c'è stato.

### Set e ordini multipli

Il totale sta sulla **testata**, quindi set e mono passano dallo stesso
identico percorso: nessun ramo, nessun `_righe_ordine`, una riga di
registro per ordine e per ruolo. Un set da tre oggetti vale i suoi tre
oggetti perché il totale li comprende, e resta **1 vendita** per
distintivi e contatori, com'è già.

*(Una versione precedente calcolava gli XP per RIGA sul solo articolo,
per non far pagare la spedizione. Scartata: metà del codice in più, e
premiava meno chi ha speso di più.)*

---

## A3. Il resto del tariffario — `AZIONI_XP`

| Azione | XP | Note |
|---|---|---|
| Visita giornaliera | 1 | `riferimento='giorno:AAAA-MM-GG'` (giorno LOCALE) |
| Primo annuncio del giorno | 5 | tetto giornaliero, o si pubblica spazzatura |
| Feedback lasciato | 10 | uno per ordine, la `UNIQUE` di `feedback` fa da specchio |
| Profilo completato | 20 | una volta sola |
| npub verificata / Telegram collegato | 15 | |
| Distintivo ottenuto | 25 | in `premia_distintivi`, che ha già il ciclo |

**REGOLA DEL TARIFFARIO, da non rovesciare:** nessuna azione ripetibile
a costo zero deve valere quanto una che muove sats. Pubblicare, salvare
nel barattolo, fare un'offerta — tutte a tetto giornaliero o a zero.
Altrimenti la scala premia chi fa rumore, non chi commercia, e a quel
punto non descrive più il mercatino.

**La visita giornaliera** si timbra in `/api/me`, che già scrive su GET
(rinfresco avatar, catch-all distintivi): il precedente c'è, ed è
idempotente per costruzione grazie al riferimento del giorno.

**Niente streak con la fiammella che si spegne** (deciso). In un
mercatino non c'è nulla da fare ogni giorno, e una serie che si rompe
punisce chi ha lavorato invece di aprire l'app. Se si vuole premiare la
costanza, si premiano i **giorni totali**, che salgono e basta.

---

## A4. Ordini fasulli — la posizione presa, e quando regge

**Decisione di Andrea:** chi crea ordini finti per salire di livello
**va bene lo stesso**, perché a ogni transazione paga la commissione. Si
sta comprando la fama, e chi si compra la fama è un cliente. Niente
regola della coppia, niente limiti fra due utenti che commerciano
spesso: uno può essere fidelizzato a un negozio e usare Barattolo
proprio perché si fida dell'escrow — che, per giunta, paga.

Il ragionamento è corretto **a commissione accesa**. Due cose vanno
tenute presenti perché oggi non è così.

### 1. Oggi la commissione è SOSPESA
`COMMISSIONE_PERCENTO = 0`, protezione spenta. Un ordine fasullo fra due
account costa in questo momento solo le fee Lightning. Il freno
economico su cui poggia la decisione **esiste, ma non è ancora acceso**.

Conseguenza per il calendario, non per il disegno:

- XP, livelli, titoli di PERCORSO (coorti, profilo completo, prima
  vendita) → si accendono subito: non sono comprabili
- **classifica e titoli di PRESTIGIO → si accendono con la commissione**

Non è una diffidenza verso gli utenti: è che finché farmare è gratis,
una classifica misura chi ha tempo, e quando farmare costa il 5% misura
chi commercia. Sono due cose diverse e conviene mostrare la seconda.

### 2. «La gente capirà se è fake» — oggi non può
Sul negozio pubblico i feedback escono **senza nomi**, di proposito:
mostrare chi ha comprato rivelerebbe gli acquisti altrui. Quindi un
venditore con 40 feedback tutti dallo stesso account **si vede identico**
a uno con 40 feedback di 40 persone. L'informazione che smaschera è
esattamente quella che abbiamo nascosto per proteggere i compratori.

Il rimedio è piccolo e non tocca la privacy — **un conteggio, non dei
nomi**:

> ⭐ 4,8 · 40 feedback **da 3 persone**

`COUNT(DISTINCT da_tg_id)` accanto a `n_feedback` nel profilo di
`/api/negozio/{chi}`. Chi ha 40 feedback da 38 persone ha un negozio;
chi ne ha 40 da 1 lo dice da solo, e chi guarda decide — che è
letteralmente il meccanismo su cui la decisione conta. Serve anche a
commissione accesa: uno che si compra la fama resta un cliente, ma il
compratore ha diritto di sapere che quella fama viene da una persona
sola.

**Da fare insieme agli XP degli ordini**, non dopo.

---

## A5. Livelli

Derivati dagli XP, **mai memorizzati** — catalogo `LIVELLI` in
server.py, giudice unico `livello_utente(xp, affari)`.

**Due chiavi, non una** (conseguenza diretta del niente-tetto): senza
tetto una vendita da 4.000 € vale più di trecento piccole, quindi un
livello sui soli XP direbbe «ha venduto una cosa cara», non
«commercia». Le soglie guardano **XP e numero di affari conclusi**
insieme, così il grado dice entrambe le cose — che è la stessa idea per
cui frequenza e importo valgono tutti e due.

Superficie: `venditore_livello` in `CAMPI_VETRINA`, espanso in
`arricchisci_righe_vetrina` (il collo di bottiglia delle sei rotte che
diventano card). In testata negozio e nel foglietto distintivi;
**mai in card** — la riga meta è già satura (comune + tre icone +
«gratis»), e il grado riguarda il venditore, non l'oggetto: è la stessa
ragione per cui il pallino Nostr è uscito dalle card.

Notifica di promozione via `notifica()` (multi-canale e DM NIP-17
gratis), dal gancio che assegna gli XP.

---

## A6. Coorti — Pioniere e i suoi fratelli

`Pioniere` esiste già come distintivo (posizione ≤100 per
`registrato ASC, tg_id`, gli 0 pre-migrazione come i più vecchi). Si
generalizza senza toccare la logica:

```python
COORTI = [(100,   'pioniere',  '🌱 Pioniere'),
          (500,   'fondatore', '🧱 Fondatore'),
          (2000,  'veterano',  '🏺 Dei primi giorni'),
          (10000, 'bottegaio', '🏪 Bottegaio')]
```

Chi entra oltre l'ultima soglia non ha coorte, ed è giusto: la coorte è
un **fatto**, non un premio da distribuire a tutti. Se ce l'hanno tutti
non dice più niente, e chi è arrivato per primo se ne accorge.

**Colonna `utenti.coorte`, congelata al primo calcolo.** La posizione in
una fila non cambia mai più: ricalcolarla a ogni giro è lavoro buttato,
e a 10.000 utenti è una scansione per ogni chiamata. Backfill
idempotente all'avvio, il modo di `deriva_regioni`.

---

## A7. Titoli selezionabili

Il distintivo dice *ho fatto*; il titolo dice *chi sono*, ed è la parte
che si sceglie.

```
utenti.titolo   TEXT DEFAULT ''    -- id del titolo scelto, '' = nessuno
```

Catalogo `TITOLI` accanto a `DISTINTIVI`, ogni voce con `id, nome,
requisito` — dove il requisito è **un distintivo posseduto, una soglia
XP/livello, o una coorte**. Un solo giudice
`titoli_disponibili(con, tg_id)`, e `POST /api/me/titolo` accetta solo
un titolo davvero sbloccato: il pattern esatto di `canale-notifiche` e
`avatar-scelta` — *si accetta solo una sorgente che esiste*.

Superficie: `venditore_titolo` in `CAMPI_VETRINA`, **sotto il nome** in
dettaglio e testata negozio; mai in card. Selettore a pillole nel
cassetto «🏅 Distintivi» del Profilo, accanto alla griglia.

**IL CATALOGO RESTA CHIUSO.** Un titolo scritto a mano dall'utente è
una superficie di abuso — «Moderatore», «Barattolo ufficiale» — che
nessun `esc()` risolve, perché il problema non è l'HTML ma il
significato. Se un giorno serviranno titoli liberi, quella è una
funzione con la sua moderazione, non un campo di testo.

---

## A8. «Il barattolo pieno» — lo strumento d'incentivo

Obiettivo dichiarato: incentivare l'utilizzo. **Con un'avvertenza presa
sul serio:** uno strumento che massimizza l'*utilizzo* non massimizza il
*commercio*. Barattolo ha successo quando qualcuno vende un oggetto e
riceve i sats, non quando apre l'app venti volte; e una classifica
visibile in un mercatino piccolo dice a 55 persone su 60 che stanno
perdendo.

Quindi lo strumento non è una classifica ma una **checklist estesa del
venditore**, gemella di quella che esiste già nel Profilo
(`renderChecklist`):

- le voci sono le azioni che **servono davvero a vendere**, e ognuna
  dice *a cosa serve*, non *quanto vale*: una foto per ogni annuncio ·
  consegna e condizione dichiarate · Lightning address impostato ·
  offerte in attesa a cui rispondere · un avviso di ricerca attivo
- **contestuali**: compaiono solo se mancano davvero, il modo degli
  hint; a lista piena il blocco sparisce del tutto
- premiano in XP e sbloccano titoli, quindi si agganciano al resto
- riusano la voce «💡 Suggerimenti» **opt-in** del cassetto Avvisi, e
  la regola del benvenuto vale anche qui: un messaggio non richiesto è
  spam anche quando è un complimento

**Se poi si vorrà la classifica** (e ha senso a commissione accesa, vedi
A4): mensile — che azzera i vantaggi accumulati —, **solo i primi 10** —
chi è 47° non lo scopre —, e opt-in.

---

# PARTE B — Aste con escrow

Non un cantiere da zero: la macchina a stati delle **offerte** con un
vincitore automatico al posto della stretta di mano. Riusa `offerte`,
`compra()`, l'escrow, l'orologio asyncio, la decadenza e le notifiche.

## B1. Asta base a scadenza

Colonne su `annunci`: `asta_fine`, `asta_base_sats`, `asta_rilancio_min`.
Attiva = `asta_fine` futura, **col pattern di `lampo_*`: ogni lettura
gatea sulla scadenza**, e la scopa nell'orologio azzera solo i numeri
morti. Mai fidarsi di un flag che qualcuno deve spegnere.

```sql
rilanci(annuncio_id, tg_id, importo_sats, creato)   -- append-only
```
È insieme lo storico e il giudice: il migliore è una `MAX`, non un
contatore da tenere allineato.

`POST /api/listings/{id}/rilancio`: maggiore del precedente più
l'incremento minimo, count-guard **senza `await`** fra controllo e
INSERT (il patto anti-doppione), 400 sul proprio annuncio.

**Incompatibilità dichiarate**, con un giudice unico `in_asta(a)` da cui
passano tutti: un annuncio in asta non ha offerte, non ha lampo, non
entra nei set, `quantita` è 1.

Chiusura in `controlla_scadenze`: vincitore = ultimo rilancio valido →
nasce un ordine `creato` con `ORE_PAGAMENTO_ASTA` per pagare, **esatta-
mente come un'offerta accettata**. L'escrow da lì in poi è quello di
sempre, e questo è tutto il punto del disegno.

## B2. Il vincitore che non paga

È l'unico punto in cui l'asta diverge davvero dalle offerte, e va deciso
prima di scrivere codice.

| Strada | Come | Costo |
|---|---|---|
| **Fiducia** (consigliata per la v1) | non paga → passa al secondo, contatore di inadempienza, sospensione dal rilancio | zero infrastruttura |
| Cauzione escrow | ogni rilancio deposita, restituito ai perdenti | N invoice e N rimborsi per asta |
| Impegno wallet NWC | rilancio solo con wallet collegato | esclude quasi tutti |

**Raccomandazione: fiducia + reputazione.** La cauzione sembra rigorosa
ma su Lightning significa N pagamenti e N rimborsi per una sola asta:
uccide la partecipazione, che è la cosa di cui un'asta ha più bisogno.

Il contatore di inadempienza del compratore è il pezzo di reputazione
che oggi **non esiste** — ed è il motivo per cui la Parte A viene prima.

## B3. Anti-sniping e superficie

- **Estensione automatica**: un rilancio negli ultimi N minuti sposta
  `asta_fine`. Regola standard, e **va detta prima**, in pagina.
- Filtro `solo_asta`, ordinamento `asta` (keyset su `asta_fine ASC`, chi
  chiude prima in testa — gemello di `lampo`, con il suo indice).
- **Card: badge col tempo che resta, SENZA countdown.** È la lezione già
  pagata con la lampo: allungava il badge e chiedeva un aggiornamento al
  secondo per ogni card disegnata. Il countdown vive solo nella scheda,
  e la griglia torna a posto da sola col trucco di `prossimaLampo`.
- Avvisi ai partecipanti (superato · sta per chiudere · hai vinto) via
  `notifica()`, aggregati col pattern del drenatore promo.

## B4. Nostr

NIP-99 non ha un vocabolario per le aste. Coerente con `tag_commercio`:
tag nostri (`["auction","end","<ts>"]`, `["bid-min",…]`) più il fatto
detto a parole nel `content`, per le persone e per i client che il
nostro vocabolario non lo conoscono.

**Gli importati restano fuori**: un rilancio dev'essere ricevuto e
chiuso da noi, e i relay non possono garantirlo. È la stessa ragione per
cui la consegna digitale non arriva mai dai relay — promettere una cosa
che nessuno può mantenere è una bugia scoperta a sats già in cassaforte.

---

# Ordine di lavoro

1. **XP: registro idempotente + gancio ordini + tariffario** — la
   fondazione, e la sola parte non ricalcolabile
2. **«da N persone» accanto ai feedback** — insieme al punto 1, non dopo
3. **Coorti** (generalizza Pioniere) → i primi titoli quasi gratis
4. **Titoli selezionabili** — richiede 1 e 3
5. **Livelli** a due chiavi (XP + affari)
6. **Il barattolo pieno**
7. *(commissione accesa)* classifica mensile opt-in, titoli di prestigio
8. **Aste**: B1 → B2 → B3, e B4 a rodaggio fatto

Le aste **dopo** la gamification non è un capriccio: senza cauzione,
l'unica cosa che tiene in piedi un'asta è la reputazione — e oggi non
c'è un numero che dica «questo compratore paga».

---

# Decisioni prese, coi motivi

| Decisione | Chi | Perché |
|---|---|---|
| XP dagli ordini: fisso + euro, **nessun tetto** | Andrea | un affare da 4.000 € è fiducia grossa, e va ripagata |
| Base = **totale**, spedizione compresa | Andrea | chi paga 300 € di spedizione ha speso 300 € |
| Frequenza **e** importo valgono entrambi | Andrea | sul volume guadagniamo le fee, sull'importo la fiducia |
| **Nessuna regola della coppia** | Andrea | si può essere fidelizzati a un negozio e usare Barattolo per l'escrow, che è pagato |
| Ordini fasulli tollerati | Andrea | a commissione accesa si comprano la fama pagandola: sono clienti |
| Titoli da catalogo **chiuso** | — | il testo libero è impersonazione, non un problema di `esc()` |
| Niente streak consecutivo | — | in un mercatino non c'è nulla da fare ogni giorno |
| Classifica fuori dalla v1 | — | farmare oggi è gratis: misurerebbe il tempo libero, non il commercio |

## Scartate, e perché (per non ripensarle)

- **Tetto agli XP per importo** — limava proprio la fiducia che si vuole
  premiare
- **XP per riga sul solo articolo** (per non pagare la spedizione) —
  metà codice in più, e premiava meno chi ha speso di più
- **Freno della coppia decrescente** (100/50/25/0) — puniva i clienti
  fidelizzati per colpa dei furbi
- **Cauzione in escrow sui rilanci** — N invoice e N rimborsi per asta:
  uccide la partecipazione
- **Streak giornaliero** — punisce chi lavora invece di aprire l'app

## Aperte

- soglie dei livelli: da tarare **sui dati veri**, o a 60 utenti restano
  tutti al primo grado
- se lo scarto per parole vietate debba finire in coda come i dubbi
  dell'AI (eredità del cantiere import aperto, non di questo)
