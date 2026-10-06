# Patch PROPOSTE per il fork di Mostro — non applicate

Qui stanno le patch scritte e provate sul PC ma **non ancora decise**: non
fanno parte della serie (`../000[1-8]-*.patch`), la ricetta di «RICOSTRUIRE
IL FORK DA ZERO» non le prende, e il nodo non le ha. Una patch esce di qui
e va accanto alle altre solo col sì di Andrea, nel giro di build che la
porta (oggi la `-bar7`, con la cura 9 del 1 ott).

## 0009 — la fee per parte letta per coppia di chiavi (6 ott 2026)

`patch-0009-fee-per-chiavi.py` (patcher ad ancore uniche, `--secco`) e
`0009-fee-read-the-seller-s-fee-by-the-pair-of-trade-keys-.patch` (il suo
`git format-patch`). Sta SOPRA le otto: tocca `src/barattolo_fee.rs`, il
blocco B della 0008 in `src/app/bond/flow.rs` e l'aggancio della 0005 in
`show_hold_invoice` (`src/util.rs`).

IL PERCHE', in breve (tutto in CANTIERI, «La cauzione e la fee per parte»):
con la cauzione accesa più prese corrono sullo stesso ordine e la riga
della fee per parte è UNA per ordine. La 0008 la rimette a posto al blocco
della cauzione rifacendo la domanda al server — e quella seconda domanda
può rispondere diverso (server giù, interruttore aperto), mentre una presa
rivale con la domanda ancora in volo può scrivere DOPO. Sbaglia solo la
quota di chi vende, di mezzo punto, nei due versi; chi compra e il flusso
non si toccano.

LA CURA: una riga per tentativo, per coppia di chiavi
(`barattolo_fees_takes`); la quota di chi vende letta per la coppia che
l'ordine porta; al blocco nessuna domanda e nessuna scrittura, solo una
riga di journal (`log_winner`).

PROVATO SUL PC (niente cargo): patcher a secco e per davvero sul clone del
tag v0.19.0 (`d53e41d`, `core.autocrlf=false`) con le otto di origin/main
via `git am`; rilanciato si ferma; `git am` delle nove su un secondo clone
dà lo stesso albero (`d1542f5`). Entra a secco anche sulle otto della
`-bar6`. I tre test nuovi in `barattolo_fee.rs` NON sono stati eseguiti.

PER PORTARLA NEL GIRO `-bar7`, sul nodo dopo le otto:
`python3 patch-0009-fee-per-chiavi.py --secco`, poi senza `--secco`,
`cargo fmt --check`, `cargo test barattolo_fee`, il commit e
`git format-patch -1 --start-number 9`; nel repo i due file passano da qui
a `../` e il README del fork dice «nove».
