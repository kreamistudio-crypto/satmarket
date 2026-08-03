# NIP-99, metadati di commercio — note per Barattolo

Appunti in italiano che accompagnano la bozza inglese
(`nip99-commerce-metadata.md`, il testo destinato al repo `nostr-protocol/nips`).
Qui si spiega perché quel disegno e cosa costa a noi implementarlo.

## Da dove nasce

Verificato sulla spec ufficiale (lug 2026): NIP-99 standardizza solo
`d`, `title`, `summary`, `published_at`, `location`, `g`, `price`,
`status`, `t`, `image`. **Nessun tag per spedizione, condizione,
quantità, peso.** La spec però chiude con «other tags may be added as
necessary»: aggiungerne non viola nulla, è previsto.

Noi oggi (`evento_annuncio` in server.py) mettiamo nei tag solo lo
standard e scriviamo tutto il resto **in prosa dentro il content**:
consegna, costo spedizione, condizione, quantità. La taglia del pacco
non la pubblichiamo affatto. E il buco è nei due sensi:
`estrai_annuncio` in importa_nostr.py legge solo title, summary,
location, price, image, d — se un venditore ci manda condizione e
quantità nei tag, le buttiamo via.

## Le due scoperte che hanno guidato il disegno

1. **Lo standard di fatto esiste già.** Shopstr pubblica e legge
   `shipping`, `condition`, `quantity`, `pickup_location`, `size`,
   `volume`, `weight`, `bulk`, `valid_until`, `restrictions`,
   `required`. Nessuno di questi è in un NIP. Il loro `shipping` è a
   4 elementi `["shipping", tipo, costo, valuta]` con allowlist chiusa
   (`N/A`, `Free`, `Pickup`, `Free/Pickup`, `Added Cost`), e il loro
   parser rifiuta in silenzio i formati vecchi e i tipi fuori lista.

2. **C'è già una collisione sul nome `weight`.** Per Shopstr è una
   *variante di prodotto col suo prezzo* (`["weight", "500g", "12.00"]`),
   non il peso del pacco (`["weight", "1200", "g"]`). Stessa arità,
   significato opposto: chi legge l'uno sbriciola l'altro. È l'argomento
   più forte che abbiamo per standardizzare, ed è al centro della
   proposta — che infatti non chiede di cambiare il tag altrui, ma
   detta una **regola di discriminazione**: se l'ultimo elemento è
   un'unità di misura (`g`/`kg`/`oz`/`lb`) è un peso, altrimenti è la
   variante legacy.

## Perché non abbiamo semplicemente copiato Shopstr

Scelta di Andrea (lug 2026): tag nostri, disegnati meglio. Le tre
differenze che contano:

- **`delivery` ripetibile invece di `shipping` a enum.** Il loro enum
  ha già dovuto inventare il valore `Free/Pickup` per dire due cose
  insieme; aggiungere un terzo metodo (la nostra consegna digitale)
  vorrebbe dire enumerare tutti i sottoinsiemi. Un tag per ogni
  metodo accettato non esplode mai — e il nostro `entrambe` diventa
  banalmente due tag, `anche_digitale` un tag in più.
- **Costo assente ≠ costo zero.** Distinzione che il loro enum fa a
  metà e che a noi serve davvero: `["delivery","shipping","0","EUR"]`
  è spedizione gratuita, `["delivery","shipping"]` è «spedisco, il
  costo lo concordiamo».
- **`stock` invece di `quantity`.** «Quantity» non dice se è la
  quantità disponibile o quella venduta. E l'assenza del tag vale 1,
  così il pezzo singolo — cioè quasi tutti i nostri annunci — resta
  pulito com'è oggi.

## Mappatura sui nostri campi

| Campo Barattolo | Tag proposto |
|---|---|
| `consegna = spedizione` + `spedizione_sats/eur` | `["delivery","shipping",costo,valuta]` |
| `consegna = ritiro` | `["delivery","pickup"]` |
| `consegna = entrambe` | i due tag sopra insieme |
| `consegna = digitale` / `anche_digitale` | `["delivery","digital"]` |
| `condizione` (5 valori) | `["condition", …]` — mappa 1:1 |
| `quantita` | `["stock", n]` — da omettere se 1 |
| `taglia_pacco` | **niente**, vedi sotto |

La condizione mappa esattamente perché il vocabolario inglese è stato
scelto sulle nostre cinque voci:

    nuovo → new · come_nuovo → like-new · buono → good
    accettabile → fair · da_sistemare → poor

**La taglia del pacco resta fuori** ed è una rinuncia consapevole:
`busta/piccolo/medio/grande/ingombrante` sono categorie di corriere
italiane, non un fatto oggettivo — in una proposta internazionale
sarebbero indifendibili. La proposta chiede invece `weight` e `dim`,
che sono misure vere e da cui una taglia si ricava in casa. Per noi
significa che, quando implementeremo, la taglia continua a vivere solo
nel nostro DB e nell'evento non ci va: **non dobbiamo inventare un peso
plausibile a partire dalla taglia**, sarebbe un dato falso su un
protocollo pubblico. Se vorremo pubblicare il peso, andrà chiesto al
venditore nel form (campo nuovo, oggi non c'è).

## Cosa costerebbe implementarlo

Cantiere piccolo, due funzioni:

- `evento_annuncio` (server.py): aggiungere i tag **accanto** alla
  prosa che già c'è, non al posto suo. Finché l'adozione è parziale la
  prosa è ciò che gli umani leggono su njump e Amethyst, e va lasciata.
- `estrai_annuncio` (importa_nostr.py): leggere i tag nuovi **e** il
  dialetto Shopstr (`shipping`, `condition`, `quantity`) — parliamo già
  con chi c'è, senza aspettare che la proposta passi. Nota: le colonne
  `condizione`, `quantita`, `consegna` sugli importati oggi non le
  scriviamo mai, e l'import orario le sovrascriverebbe a ogni giro:
  da decidere caso per caso come per titolo e prezzo.

Da valutare anche `evento_annuncio_importato` (la modifica firmata):
lì i tag li firma il venditore, e in v1 avevamo congelato la superficie
a ciò che l'evento originale portava.

## Prima di aprire la PR

Le proposte di NIP senza implementazioni muoiono. L'ordine giusto è:
implementare (cantiere sopra) → far girare qualche annuncio vero coi
tag nuovi → aprire la PR potendo dire «due implementazioni indipendenti
parlano già questi tag», e citare la collisione `weight` come urgenza.

Verificato lug 2026: sul repo `nostr-protocol/nips` **non c'è nessuna
issue né PR aperta** su spedizione/condizione/quantità per NIP-99. La
sola cosa vicina è la issue #1999 (informazioni di prodotto
distribuite, kind 30401), che è un'altra cosa: parla di anagrafica
prodotto condivisa — ingredienti, filiera, GTIN — non di cosa offre un
singolo annuncio. Il campo è libero.
