---
name: chiusura-cantiere
description: Come si chiude un cantiere di Barattolo: verbale in docs/CANTIERI.md, prove severe e collaudi, collaudo nuovo nella gabbia, commit firmato, push, pulizia del worktree. Usala quando il lavoro è fatto e si sta per committare o pushare.
---

# Chiudere un cantiere

Un cantiere è CHIUSO quando è committato, provato, collaudato e col
verbale scritto. In quest'ordine:

## 1. Il verbale (regola ferrea 8)

PRIMA del commit finale, in fondo a `docs/CANTIERI.md`, una voce che
comincia con `## <titolo> (<data>, cantiere <nome>, <chi l'ha chiesto>)`:
cosa si è deciso, i perché, le strade scartate, cosa è stato provato e
cosa resta da guardare. L'architettura va in `docs/ARCHITETTURA.md`, le
procedure di produzione in `docs/PRODUZIONE.md`, il nodo in
`docs/NODO-MOSTRO.md`. Quel che resta da fare sul VPS va in
`docs/DA-FARE-ANDREA.md`, coi comandi pronti.

`CLAUDE.md` si tocca SOLO se è cambiata una REGOLA: proponilo come
commit separato. Dopo ogni ritocco, `wc -l CLAUDE.md` sotto
`TETTO_CLAUDE_MD` di `prove.py`, o la CI è rossa e il deploy non parte.

## 2. Le prove

- Nel worktree: `PROVE_SEVERE=1 python prove.py` più i collaudi della
  CI (`python collaudi_ci.py --elenco ci/collaudi.txt`). Se servono `config.py`, la copia nel
  worktree si cancella prima del commit.
- Un collaudo NUOVO: prima nella gabbia (`python collaudi_ci.py
  collaudo_x`), poi una riga in `ci/collaudi.txt` e in `ci/compila.txt`,
  MAI nel workflow.
- Le sessioni cloud non aspettano la CI sul ramo: la loro prova è suite
  e collaudi locali.

## 3. Commit e push

- Si aggiungono i file per nome: mai `git add -A`, mai `git commit -a`,
  mai un `git stash` nudo.
- La punta deve essere firmata: `git cat-file commit HEAD | grep -c
  '^gpgsig'` deve dire 1 (`git commit-tree` firma solo con `-S`).
- Push su `develop` senza chiedere e mai con force. Se il ramo è corso
  nel frattempo: rebase, le sezioni toccate più i collaudi, push. Il
  verbale dice COSA è girato su QUALE albero, il rapporto NOMINA i
  commit non miei. Un «non pushare ancora» di Andrea vince.
- La promozione su `main` NON è qui: è la skill `promozione-main`.

## 4. La pulizia, dopo il push verde

```
cd <la cartella principale del repo>
git worktree remove --force .claude/worktrees/<nome>
git worktree prune
git branch --merged origin/develop --list "cantiere/*"   # poi -d su ognuno
```

Un worktree altrui con modifiche non committate si LASCIA, e si dice
perché.

## 5. Il rapporto

La cosa chiesta, con le sue prove. Quel che si è notato strada facendo
va in fondo come elenco, una riga per voce, e lì si ferma finché non
arriva un sì.
