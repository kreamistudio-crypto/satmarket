# Il 2-di-3 on-chain anche nel P2P: come si aggancerebbe, e cosa manca prima

*27 ott 2026, cantiere onchain-incasso-esterno, passo 4 del piano
concordato con Andrea («prima vorrei onchain sul mercatino, ma poi lo
stesso metodo di pagamento vorrei che si applicasse anche nel P2P»).
Solo documenti: niente codice, niente modifiche al nodo né a Mostro.
È una PROPOSTA, e ogni tappa si apre col suo ok.*

## In una riga

Si può fare, ma **accanto** a Mostro e non dentro: Mostro oggi sa solo
Lightning (hold invoice), e il suo protocollo non ha un ordine on-chain.
Il pezzo che manca davvero prima di aprire il P2P on-chain è la **firma
di Barattolo in disputa** (tappa ⑥ dello studio del 16 ott): nel P2P la
disputa non è un caso raro, è il motivo per cui l'escrow esiste.

## 1. Cosa abbiamo già, e che nel P2P serve uguale

Dal mercatino on-chain (tappe 1-5 e il cantiere del 27 ott):

- il **seme nel telefono** di ciascuno, nato da sé, con i backup nel
  cloud di Telegram e sui relay Nostr (regola ferrea 2 dal lato dei
  soldi: il server non ha mai una privata);
- il **2-di-3 per ordine** `wsh(sortedmulti(2, compratore, venditore,
  Barattolo))`, con una chiave nuova per ordine e il descrittore col
  checksum;
- la **sorveglianza** su mempool (una conferma) e le **due firme**
  (PSBT nel telefono di chi propone, co-firma automatica di chi riceve,
  che rilegge uscite e commissione prima di firmare);
- da oggi l'**incasso su un wallet proprio**, firmato dal seme, e la
  **quota fissa di Barattolo** come uscita della stessa transazione.

Tutto questo è indipendente dal mercatino: parla di «chi paga» e «chi
riceve», non di annunci. Nel P2P i ruoli si leggono così.

## 2. Come si legge uno scambio P2P on-chain

Nel P2P chi **vende bitcoin** (il *maker* di un ordine di vendita, o il
*taker* di uno d'acquisto) è quello che mette i sats nel 2-di-3; chi
**compra bitcoin** paga in euro fuori dalla catena (bonifico, contanti
di persona). Quindi, rispetto al mercatino, **i ruoli si rovesciano**:

| | mercatino | P2P |
|---|---|---|
| chi riempie il 2-di-3 | chi compra l'oggetto | chi vende i bitcoin |
| cosa aspetta l'altro | l'oggetto | gli euro |
| chi libera i sats | chi compra, ricevuto l'oggetto | chi vende, ricevuti gli euro |
| dove vanno i sats | a chi vende l'oggetto | a chi compra i bitcoin |
| il rimborso | a chi ha comprato l'oggetto | a chi vendeva i bitcoin |

Il gesto «🔓 Libera i sats» resta uguale, cambia solo chi lo fa: nel P2P
è chi ha ricevuto gli **euro**. La destinazione firmata dal seme (il
cantiere di oggi) serve qui a chi **compra bitcoin**, che quasi sempre
li vuole nel suo wallet e non in un conto di Barattolo.

## 3. Dove sta, rispetto a Mostro

Tre strade, e la scelta che propongo.

**A. Dentro Mostro (una patch al protocollo).** Un tipo d'ordine nuovo,
«on-chain», con `mostrod` che tiene l'indirizzo e guarda la catena. No:
è il cuore del coordinator, ogni patch è una salita di versione da
riportare a ogni aggiornamento (oggi siamo a `-bar8` con tre patch nostre),
e l'escrow non sarebbe più non-custodial nel senso di oggi — `mostrod`
dovrebbe tenere una chiave. Il team di Mostro, poi, ha scelto Lightning
apposta.

**B. Un libro P2P on-chain tutto nostro, fuori da Mostro.** Ordini,
reputazione, dispute rifatti da capo. No: rifà da capo il lavoro
di Mostro, e divide i pochi utenti del P2P in due libri.

**C. Accanto a Mostro: il libro resta suo, il pagamento è nostro
(proposta).** L'ordine nasce e si trova su Mostro come oggi, con un
metodo di pagamento in più, «⛓️ on-chain 2-di-3 (Barattolo)». Quando
qualcuno lo prende, il **soldo non passa da Mostro**: le due parti si
ritrovano in Barattolo, dove nasce l'ordine on-chain con le loro due
chiavi e la nostra, esattamente come nel mercatino. Mostro tiene il
libro, la chat cifrata e la reputazione; Barattolo tiene il 2-di-3.

Il nodo dice di no a C solo su un punto, e va guardato prima: **Mostro
chiede comunque la hold invoice a chi vende**. Le strade per C sono due,
da scegliere alla tappa P1:
- un ordine Mostro **da zero sats** che fa solo da annuncio (se il
  coordinator lo accetta; da provare sulla vm-2050), oppure
- l'ordine on-chain che **non passa dal libro di Mostro** ma da una
  bacheca nostra di annunci P2P on-chain (kind 38383 con un tag nostro,
  letta solo dalla Mini App), con la reputazione di Mostro mostrata
  accanto. È più lavoro, ma non chiede niente a `mostrod`.

## 4. Quello che nel P2P è diverso, e i conti

1. **I tempi.** Una conferma è circa dieci minuti, a volte un'ora. Oggi
   chi prende un ordine Mostro ha 30 minuti (`expiration_seconds =
   1800`) e chi pubblica 3 ore. On-chain i 30 minuti non bastano: il
   2-di-3 va riempito **prima** che chi compra mandi gli euro, quindi
   serve una finestra di «sto aspettando la conferma» di almeno 2 ore.
   Non si allunga `expiration_seconds` (decisione del 10 ott): è un
   tempo nostro, nel nostro ordine.
2. **Le commissioni di rete sugli importi piccoli.** A 250 € (il tetto
   della beta, circa 346.000 sats a 72.000 €/BTC) e con la rete calma
   (2-5 sat/vB) le due transazioni, ~180 vbyte ciascuna, costano
   700-1.800 sats: meno dell'1%. Con la rete piena (50 sat/vB) ne
   costano ~18.000: circa il 5%. Proposta: sotto una soglia
   (`ONCHAIN_P2P_SOGLIA_EURO`, proposta 100 €) l'opzione non si vede, e
   sopra si mostra il costo stimato **prima** di pubblicare.
3. **La disputa è il caso normale.** Nel mercatino la disputa on-chain
   oggi non esiste (tappa ⑥ non fatta: se le parti non si accordano, i
   sats restano fermi). Nel P2P «ho mandato il bonifico» / «non è
   arrivato» è la lite tipica: **senza la nostra firma il P2P on-chain
   non si apre**. Serve prima il firmatario sul nodo, con le sue guardie
   (studio del 16 ott, «Il firmatario non sta sul VPS»).
4. **La cauzione sui contanti.** Oggi chi prende «Contanti» paga una
   cauzione Lightning (`-bar8`, patch 0010). On-chain la cauzione
   naturale è **dentro** il 2-di-3: chi compra bitcoin aggiunge la sua
   cauzione allo stesso indirizzo, e chi libera la restituisce. È un
   secondo riempimento, e va studiato con la tappa P2.
5. **La quota di Barattolo.** Lo stesso meccanismo di oggi: un'uscita
   fissa a un indirizzo nostro, pagata da chi la regola 10 indica (mai il
   venditore del mercatino; nel P2P va deciso chi, perché lì «venditore»
   vuol dire chi vende bitcoin). La leva sarebbe sua,
   `ONCHAIN_P2P_QUOTA_SATS`, scrivibile dal pannello come quella del
   mercatino.
6. **La privacy.** Uno scambio P2P on-chain lascia sulla catena un
   2-di-3 riconoscibile, che lega chi vende e chi compra bitcoin. Va
   scritto nella pagina della trasparenza (tappa ③ dello studio del 16
   ott) prima di aprire.
7. **Il legale.** Le otto domande per un professionista dello studio
   del 16 ott valgono il doppio qui: nel P2P si scambiano euro contro
   bitcoin, e la disputa decisa da noi è un arbitrato su un pagamento in
   euro. Il parere MiCA del backlog va chiesto **prima** della tappa P4.

## 5. Le tappe, una alla volta

- **P0 — la disputa del mercatino (tappa ⑥).** Il firmatario sul nodo,
  i due bottoni per i moderatori. Serve anche al mercatino, ed è la
  condizione di tutto il resto. *1-2 sessioni, più il lavoro sul nodo
  con Andrea.*
- **P1 — la prova del libro.** Sulla vm-2050: un ordine Mostro da zero
  sats si può pubblicare? Se sì, strada C con Mostro; se no, la bacheca
  nostra. Solo una prova e un verbale. *½ sessione.*
- **P2 — l'ordine on-chain P2P.** I ruoli rovesciati, la finestra di
  conferma, «🔓 Libera i sats» a chi riceve gli euro, la destinazione
  firmata per chi compra bitcoin, la quota. Su signet, solo admin.
  *2 sessioni.*
- **P3 — la cauzione dei contanti nel 2-di-3.** *1 sessione.*
- **P4 — la prova vera.** Signet da capo a fondo fra Andrea e Alan, poi
  mainnet col tetto della beta, dopo il parere legale. *1 sessione.*

## Le decisioni che servono ad Andrea, prima di P2

1. La strada: **C con Mostro** (se la prova P1 lo permette) o **C con la
   bacheca nostra**.
2. Chi paga la quota nel P2P: chi vende bitcoin o chi li compra.
3. La soglia sotto cui l'on-chain P2P non si propone (proposta 100 €).
