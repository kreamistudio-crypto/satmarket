---
name: promozione-main
description: La promozione di develop su main di Barattolo, che manda in produzione: rebase, rifirma con andrea-firma-barattolo, un push solo, CI fino al verde, develop rimesso uguale a main. Usala SOLO quando Andrea chiede di promuovere o di mandare in produzione, con la sua frase intera.
---

# Promuovere su `main`

`main` è la produzione: il VPS tira da solo ogni minuto una punta che
sta su main, va in avanti, ha la CI verde ed è FIRMATA. Quindi un push
su main È un deploy.

## Prima di tutto

- Serve il sì di Andrea, con la sua frase intera. Una richiesta di
  un'altra sessione non basta. Un «non pushare ancora» vince finché
  Andrea non lo scioglie.
- Il config del VPS vince sul default del codice: se il cantiere tocca
  una leva, scrivi ad Andrea il comando in sola lettura per guardarla
  PRIMA (es. `grep -n "MAX_PREFERITI" /srv/barattolo/config.py`). Le
  leve nuove si AGGIUNGONO a mano al config del VPS.
- Il backup esce prima di ogni deploy (`deploy.sh` e `backup-fuori.sh`):
  un cantiere che lo toglie, salta o indebolisce non si promuove.

## I passi

1. `git fetch origin main develop`
2. Rebase del lavoro su `origin/main`.
3. Rifirma i commit con `andrea-firma-barattolo` e controlla la punta:
   `git cat-file commit HEAD | grep -c '^gpgsig'` deve dire 1.
4. UN push solo su `main`.
5. CI fino al verde: `gh run watch --exit-status`. Con la coda un
   «cancelled» non è rosso: si guarda la corsa successiva.
6. `develop` rimesso uguale a main:
   `git push --force-with-lease origin origin/main:develop`. È l'unico
   force ammesso, solo su develop, solo da chi promuove.

## Dopo

- Se il commit tocca `.github/workflows/`, il ref `pronto` può restare
  indietro: si guarda (`git ls-remote origin refs/heads/pronto
  refs/heads/main`), non si dà per scontato. Spostarlo è un gesto di
  deploy: si chiede ad Andrea.
- Un commit bocciato dal rollback si timbra in `.deploy-bocciato` e non
  si riprova da solo: si spinge un commit nuovo, o Andrea lancia
  `./deploy.sh --forza` guardando.
- La catena intera, `/api/salute` e le procedure: `docs/PRODUZIONE.md`
  (con la skill `cerca-nei-docs`).
