# Censimento delle notifiche ai moderatori

Documento di lavoro (ago 2026). Nato dal cantiere che ha tolto la «✏️»
della modifica approvata: Andrea ha chiesto, già che c'era, la mappa
completa di cosa arriva ai moderatori e perché.

**Cosa è stato deciso quel giorno:** si toglie SOLO la ✏️ della
modifica approvata. Tutto il resto resta com'è — i nuovi pionieri
compresi. Il censimento si scrive qui perché rifarlo da capo un domani
sarebbe uno spreco, non perché sia una lista di lavori approvati.

**Quindi: niente qui dentro è deciso.** Le colonne «verdetto» sono la
mia proposta di quel giorno, con i motivi, da riprendere in mano
quando e se si vorrà.

---

## Il criterio

Deciso da Andrea, ed è la riga che governa tutto il resto:

> Si tiene solo quello che richiede un **gesto umano** che **nessun
> altro posto già racconta**.

Due condizioni, e servono entrambe. Una notifica che chiede un gesto ma
lo racconta anche il pannello è un doppione: il gesto resta, lo squillo
no. Una notifica che non chiede nessun gesto è rumore comunque, anche
se l'informazione non c'è altrove.

Il motivo per cui il criterio è severo: il fiume delle notifiche admin
è già pieno, e un fiume pieno si smette di leggere. Le notifiche che
contano davvero — un ⛔ su un importo storto, un 🧊 su sats fermi —
valgono solo se qualcuno le vede quando arrivano.

---

## Come leggere questo documento fra sei mesi

**I riferimenti sono per FUNZIONE e per EMOJI, mai per numero di
riga:** i numeri di riga di `server.py` marciscono in una settimana.
Se un'emoji non si trova più, cercare `notifica_admin(` — è il punto
unico da cui passano tutte tranne `avvisa_revisione` (che usa
`bot_api` diretto, perché deve portare la tastiera) e la disputa (che
usa `notifica()` in un ciclo su `ADMIN_IDS`).

**Le frequenze sono STIME.** Il VPS è fuori dal perimetro di chi ha
scritto questo documento: le stime vengono dalla struttura del codice
e dai numeri noti del rodaggio (~46 annunci, ~60-75 utenti, ~28
ordini). Prima di agire su una voce «per volume», il numero vero si
guarda sul VPS.

---

## TIENI — chiedono un gesto, e nessun altro posto lo racconta (11)

| Notifica | Innesco | Ogni quanto (stima) | Il gesto |
|---|---|---|---|
| ⛔ Pagamento rifiutato | `paga_venditore`, bolt11 ≠ dovuto | mai, si spera | wallet rotto o tentato prelievo: si guarda subito |
| 🧊 Pagamento da verificare | payout INCERTO, il nodo non risponde | rarissima | cercare l'hash su LNbits, poi «è uscito / non è uscito» |
| ⚠️ Disputa aperta | `apri_disputa` | rara | decidere: è il gesto più consequenziale che ci sia |
| ⚠️ Pagamento su ordine annullato | `controlla_annullati`, riacciuffo | rarissima | l'oggetto può essere andato a un altro nel frattempo |
| 🧊 ×6: incasso, conferma, merce mai partita, ritiro, busta, rimborso d'asta | tetto dei solleciti passato | rara per costruzione | sats fermi: da lì in poi solo un umano li smuove |
| 🧊 Libro mastro | ronda, 1×giorno | mai, se i conti tornano | gli invarianti non tornano |
| ⏳ Revisione (tastiera ✅/❌) | verdetto DUBBIO dell'AI | qualcuna a settimana | ✅/❌ **dentro** il messaggio: è il gesto stesso |
| ⏳ Sollecito revisioni | coda ferma da ≥2 giorni | max 1×giorno | la coda si è impantanata |
| 🗂 Termometro sottocategorie | lunedì | 1×settimana | rilanciare `assegna_sottocategorie.py` |
| 📥 Riassunto import CSV | fine job | rara (commercianti) | guardare i bocciati |

Su questi non c'è discussione: passano il criterio con tutt'e due le
gambe.

---

## GATE — il gesto c'è, il ritmo è sbagliato (1)

### 🗂 Proposte di categoria (`ricategorizza_automatico`)

Parte a **ogni giro d'import che produce proposte**, cioè
potenzialmente ogni ora. Ma la coda è **persistente nel pannello**
(«🗂 Categorie da sistemare»), quindi il messaggio non porta
un'informazione che si perde: è un promemoria.

Proposta: gate giornaliero, come `sollecita_revisioni` — che quel
pattern ce l'ha già ed è la funzione da copiare.

Nota trovata strada facendo: il pallino `.off-dot` del tappo conta
**solo** `stato='revisione'`. La coda delle categorie nel pannello non
ha nessun badge, quindi oggi la notifica è l'unico richiamo. Se si
mette il gate, vale la pena aggiungere anche quella al conteggio — o
il gate la renderebbe più facile da dimenticare.

---

## SPOSTA — il pannello lo racconta già (8)

### I sei 🚫 della moderazione

`annuncio bloccato dal filtro` · `annuncio bloccato dall'AI` ·
`modifica bloccata dal filtro` · `modifica bloccata dall'AI` ·
`modifica firmata bloccata dal filtro` · `modifica firmata bloccata
dall'AI`

Ognuna chiama già `registra_moderazione`, e il pannello ha
«🛡 Registro moderazione» con le ultime 20 righe, i motivi e il
riepilogo a 30 giorni. **Togliere lo squillo non perde un byte.**

E c'è un argomento più forte del «non si perde niente»: CLAUDE.md
dichiara che è **da quei dati** che il prompt di moderazione si
corregge a mano — cioè da una **lettura periodica del registro**, non
da una reazione per evento. La notifica per evento invita al gesto
sbagliato.

È la vincita più pulita del censimento: sei notifiche, zero
informazione persa.

> ⚠️ **L'ECCEZIONE, da sistemare PRIMA di toccare la famiglia.** Il 🚫
> del **commento di feedback** (in `lascia_feedback`) **non** chiama
> `registra_moderazione`: è l'unico dei sette senza traccia nel
> registro. Togliergli la notifica lo farebbe sparire del tutto. O gli
> si aggiunge la riga nel registro — ed è probabilmente giusto a
> prescindere, per uniformità — oppure quella notifica resta.

### 👥 Nuovo pioniere (il messaggio SINGOLO)

Nessun gesto, e il nome è **già** nella lista utenti in fondo alle
statistiche admin, con la data in `registrato`.

Proposta di allora: tenere l'**aggregato** e i **🎉 traguardi** — che
sono morale, non moderazione, e costano un messaggio ciascuno — e
togliere i singoli. Tre arrivi diventano un messaggio invece di tre.

**Andrea ha deciso di tenerli tutti** (ago 2026). La voce resta qui
perché se un domani il ritmo degli iscritti cresce, questa è la prima
leva che si guarda — e la meccanica dell'aggregato esiste già in
`avvisa_nuovi_iscritti`, non c'è niente da costruire.

---

## TOGLI — nessun gesto, e nessun posto che li perda (2)

- **🔗 Doppia cittadinanza** (fusione riuscita) — pura curiosità,
  qualche volta l'anno. Costa poco tenerla, ma non passa il criterio.
- **✏️🟣 Modifica firmata di un importato** (`modifica_firmata`) — la
  gemella di quella tolta, ma è un **altro evento**: rarissima, e dice
  che abbiamo rispedito ai relay un evento firmato da un altro. È
  stata lasciata apposta nel cantiere della ✏️, per non allargare lo
  scopo di nascosto.

---

## IL CASO A PARTE — 🆕 Nuovo annuncio

Probabilmente il **volume più grosso** dopo il polso ordini, e per il
criterio non chiede nessun gesto: i tre strati l'hanno appena
promosso, è già in vetrina.

**Ma non è il gemello della ✏️, ed è la cosa da sapere prima di
deciderlo.** Tre differenze, e la terza decide:

1. Quella notifica **è** lo «strato 3» della moderazione a tre strati
   dichiarata in CLAUDE.md. Toglierla cambia un principio scritto, non
   solo una riga.
2. È la **prima volta** che quel contenuto esiste; una modifica è roba
   già vagliata una volta.
3. **La pubblicazione approvata NON scrive in `moderazione_log`.**
   Quindi qui, a differenza dei 🚫, il pannello *non* lo racconta già:
   toglierla nuda lascerebbe un buco vero.

Proposta: non toglierla — **spostarla**. Due strade, la seconda
probabilmente più corta:

- una sezione «ultimi pubblicati» nel pannello admin;
- oppure far scrivere in `moderazione_log` anche l'esito OK, e lasciare
  che sia il registro esistente a raccontarlo.

Cantiere suo: prima il posto dove atterra, poi si spegne lo squillo.

---

## Il polso ordini (5)

`🛒 nuovo ordine` · `✅ ordine concluso` · `⚖️ disputa chiusa a favore
del venditore` · `↩️ ordine rimborsato` · `🔨 asta conclusa`

**Restano** (decisione di Andrea). Una sola osservazione per il
futuro: il 🛒 in senso stretto non chiede un gesto — il polso è il
cruscotto del fondatore, non una coda di moderazione. Ai numeri di
oggi va benissimo così, e CLAUDE.md dichiara già che col volume andrà
aggregato (pattern del drenatore promo).

---

## Se un domani si riprende, l'ordine

1. **I sei 🚫** — zero informazione persa, il registro c'è già. Con la
   riga di registro da aggiungere al commento di feedback, che è il
   pezzo da non dimenticare.
2. **👥 singoli** → solo aggregato + traguardi (meccanica già scritta).
3. **🗂 categorie** → gate giornaliero, più il badge sul tappo.
4. **🔗 fusione** e **✏️🟣** → via.
5. **🆕** → cantiere suo, prima il posto dove atterra.

I primi quattro punti sono ~10 notifiche in meno senza toccare niente
di sostanziale.

---

## Cosa è già stato fatto (ago 2026)

**✏️ Modifica approvata — TOLTA.** Il perché per esteso sta in
CLAUDE.md, alla voce «Modifica annuncio». In breve: la modifica
ripassa dalla moderazione INTERA, quindi il vietato blocca con la sua
notifica e il dubbio manda in `stato='revisione'`, dove restano sia la
tastiera ✅/❌ sia la coda del pannello — che filtra per **stato** e
non per come ci si è arrivati, quindi prende le modifiche senza una
riga dedicata. Il fatto in sé resta scritto in `annunci.modificato`,
che la scheda mostra. A sparire è solo lo squillo.
