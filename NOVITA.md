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
