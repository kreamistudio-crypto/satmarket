# Novità di Barattolo per gli utenti

Questo file è la fonte dei post automatici sul canale (cantiere «novita», 10 nov 2026).
A ogni PROMOZIONE su main con la CI verde, n8n (sul RELAY, bot «Barattolo News») legge
le voci NUOVE di questo file rispetto al main di prima, e per ognuna con
`pubblico: sì` fa scrivere a Claude una BOZZA di post, che arriva in privato ad
Andrea coi tasti Pubblica / Modifica / Scarta. Nel canale non esce niente senza il suo
tocco. Il disegno intero: docs/ARCHITETTURA.md, «LE NOVITÀ PER GLI UTENTI».

CHI LA SCRIVE: il thread del cantiere, a fine lavoro, nello stesso commit della voce
in docs/CANTIERI.md. Solo per quello che un utente può VEDERE o USARE: un ritocco
interno, una prova, un documento non portano voce.

COME SI SCRIVE: una voce per novità, in fondo al file, così (le righe vanno tutte,
in quest'ordine; niente altro fra una voce e l'altra):

    ## 2026-11-10 · nome-del-cantiere
    frase: Cosa cambia per chi usa Barattolo, in una o due frasi semplici.
    dove: La pagina e i bottoni dove si vede (per la registrazione dello schermo).
    leva: NOME_DELLA_LEVA spenta di serie   oppure   leva: nessuna
    pubblico: no

- `frase`: per gli utenti, non per noi. Fatti soli: è la base del post, Claude non
  aggiunge niente che qui non c'è. Lessico di Barattolo («deposito di garanzia»,
  «Ordini»). Al massimo 400 caratteri.
- `dove`: scheda, pagina, bottone, coi nomi che l'utente legge sullo schermo.
- `leva`: il nome della leva che la accende (deve esistere in config_esempio.py) e
  com'è DI SERIE, oppure `nessuna` se la novità c'è per tutti appena arriva su main.
- `pubblico`: `sì` solo se, arrivata su main, la vede CHIUNQUE. Leva spenta, o accesa
  solo per gli admin: `no` (un post la annuncerebbe a tutti). Il config del VPS
  vince sul codice: se non sai com'è là, scrivi `no`.
- Il giorno che Andrea accende una leva per tutti, la novità si annuncia con una
  voce NUOVA (`leva: NOME accesa per tutti dal <data>`, `pubblico: sì`). Le voci
  vecchie non si cambiano: n8n guarda solo le intestazioni nuove.
- L'intestazione (`## data · nome`) non si ripete mai: è la chiave con cui n8n
  riconosce una voce già vista.

La forma la controlla `prove_novita_md` in prove.py.

<!-- LE VOCI COMINCIANO QUI SOTTO -->

## 2026-11-10 · come-ricevi
frase: Nel Profilo c'è una voce nuova, «📥 Come ricevi»: lì scegli in che forma ti arrivano i sats quando ti pagano in Lightning e quando ti pagano on-chain, senza cercarlo dentro la voce «₿ On-chain».
dove: Profilo → «📥 Come ricevi», con le due righe «Quando ti pagano in Lightning, ricevi in» e «Quando ti pagano on-chain, ricevi in».
leva: SWAP_AUTO_ATTIVO spenta di serie
pubblico: no

## 2026-11-10 · onion-location
frase: Se apri barattolo.store con Tor Browser, nella barra degli indirizzi compare «.onion disponibile»: un tocco e sei sul sito .onion di Barattolo, dove il server non vede il tuo indirizzo IP.
dove: Tor Browser, barra degli indirizzi su barattolo.store: la pillola viola «.onion disponibile».
leva: nessuna
pubblico: sì

## 2026-11-11 · cifra-btc
frase: Quando paghi on-chain, accanto ai sats da mandare ora vedi anche la cifra in BTC (per esempio 0,00008128 BTC): la tocchi e la copi, pronta da incollare nel wallet. Nel pagamento di un ordine on-chain c'è anche «₿ Apri nel wallet», che apre il wallet con indirizzo e cifra già scritti.
dove: il foglio «Blocca … sats» del pagamento on-chain, «🔒 Blocca i sats» degli scambi P2P on-chain, la scheda «Cambio» e il riquadro «Caricali in Lightning» del P2P: la riga «In BTC» col bottoncino 📋.
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

## 2026-11-11 · foglio-oc-visto
frase: Quando paghi un ordine on-chain, appena la rete vede i tuoi sats la pagina del pagamento si chiude da sola: in «Ordini» l'ordine dice «Visto in rete, aspetto la conferma» invece di «Da pagare», e dopo una conferma, circa dieci minuti, diventa pagato.
dove: il foglio «Blocca … sats» del pagamento on-chain e la riga dell'ordine in «Ordini» (etichetta «In arrivo»).
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no
