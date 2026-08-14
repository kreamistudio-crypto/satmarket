# I font di Barattolo

I tre font del progetto, serviti da casa nostra e mai da un CDN — stesso patto
di `vendor/nostr.bundle.js` e `vendor/qrcode.js`, ma qui la ragione è un'altra:
finché la pagina li chiedeva a `fonts.googleapis.com`, l'indirizzo IP e lo
user-agent di **ogni** visitatore — anche di chi passa e non compra —
arrivavano a un terzo, a ogni apertura. Ora non arrivano a nessuno.

## I file

Sei `.woff2`, scaricati da Google Fonts il **14 agosto 2026**:

| file | famiglia | versione Google | byte |
|---|---|---|---|
| `baloo2-latin.woff2` | Baloo 2 | v23 | 33.188 |
| `baloo2-latin-ext.woff2` | Baloo 2 | v23 | 27.384 |
| `nunito-latin.woff2` | Nunito | v32 | 39.128 |
| `nunito-latin-ext.woff2` | Nunito | v32 | 35.588 |
| `jetbrains-mono-latin.woff2` | JetBrains Mono | v24 | 31.432 |
| `jetbrains-mono-latin-ext.woff2` | JetBrains Mono | v24 | 11.624 |

**Sono font VARIABILI**: un file solo porta tutti i pesi della famiglia, ed è
il motivo per cui bastano sei file per gli otto pesi che il foglio usa (Baloo 2
700 e 800 leggono lo stesso file; Nunito 400, 600, 700 e 800 pure). I
`@font-face` in `miniapp.html` dichiarano i pesi **uno per uno**, esattamente
come faceva il CSS di Google: con un intervallo (`font-weight: 400 800`) il
browser istanzierebbe il peso esatto richiesto, e una regola come
`.sicu p{font-weight:500}` — che oggi ricade sul 400 — cambierebbe aspetto.
Qui si è spostato *da dove* arrivano i byte, non come si vede l'app.

Sottoinsiemi tenuti: `latin` e `latin-ext`. Fuori restano cirillico, greco,
vietnamita e devanagari, che Google serviva e noi no — **imperfezione
dichiarata**: un nome scritto in quegli alfabeti (può capitare da Nostr) cade
sul font di sistema invece che sul nostro. Resta leggibile, e non riguarda
nessun testo dell'app. Chi volesse chiuderla scarichi anche quei
sottoinsiemi dalla stessa fonte e aggiunga i loro `@font-face`.

## Come si aggiornano

Non si aggiornano da soli, ed è voluto. Per rifarlo: si chiede a Google il CSS
con uno user-agent moderno —

```
https://fonts.googleapis.com/css2?family=Baloo+2:wght@700;800&family=JetBrains+Mono:wght@500;700&family=Nunito:wght@400;600;700;800&display=swap
```

— si prendono gli URL `latin` e `latin-ext` che ne escono, si scaricano al
posto di questi sei, si ricopiano gli `unicode-range` nei `@font-face` di
`miniapp.html` e **si alza `VERSIONE` in `sw.js`** (i file stanno in dispensa).

## Licenza

Tutte e tre le famiglie sono sotto **SIL Open Font License 1.1**, che permette
la ridistribuzione a patto di portarsi dietro questo avviso.

Copyright 2019 The Baloo 2 Project Authors (https://github.com/EkType/Baloo2)
Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)
Copyright 2014 The Nunito Project Authors (https://github.com/googlefonts/nunito)

Il testo integrale della licenza è in `OFL.txt`, accanto a questo file.
