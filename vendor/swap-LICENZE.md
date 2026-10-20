# Gli otto pacchetti del bundle dello swap

`vendor/swap.bundle.js` non è scritto a mano: è il risultato di otto
pacchetti npm, **tutti MIT**, uniti in un file solo. Serve al telefono di
chi vende per fare da sé lo swap Lightning → on-chain di SATS Routing: le
dodici parole e le chiavi nascono nel browser, e la verifica, il MuSig2 e
il ritiro li fa `boltz-core`, la libreria che usa il server di SATS
Routing (3.13.0, `^5.0.0`). Qui stanno le versioni esatte, la ricetta per
rifarlo byte per byte e le licenze per esteso.

## Perché la 5.0.0 di npm (20 ott 2026, cantiere swap-bundle-500, decisione di Andrea su consiglio di Massimo)

Il bundle è di nuovo quello della tappa 3: `boltz-core` 5.0.0 com'è
uscito su npm, la ricetta qui sotto. Ricostruito il 20 ott 2026 in una
cartella nuova da npm: lo stesso sha256 di prima,
`46306e34468e1647` `a42507221b40aa05` `a96623ecd28039e0` `0b31ee17ff31ad99`
(a gruppi di sedici: lo scanner dei segreti).

PERCHÉ. Per qualche ora (cantiere swap-lockup) il bundle è stato fatto
dal sorgente di `boltz-core` al commit della PR #196, che non è mai
uscita su npm. Massimo (SATS Routing) ha consigliato la 5.0.0: è il
codice che il loro server usa e che gira da anni, mentre il commit è
una costruzione nostra di un ramo che nessuno pubblica. La #196 rendeva
più severo `detectSwap` (l'uscita del lockup legata a quella attesa);
quella stessa difesa il telefono la fa già DA SÉ in `swapRitiro`
(`swap/boltz.js`): l'uscita trovata deve essere byte per byte lo script
atteso, sennò niente segreto. Restano anche gli altri controlli prima
del segreto (l'importo, il lockup letto dalla rete) e il ritiro senza la
loro API: sono solo rifiuti in più, non cambiano il protocollo. Con la
5.0.0 la difesa sullo script è UNA, la nostra, e le prove lo dicono
(`collaudo_swap_telefono`, il lockup «altro script»).

## La strada provata e lasciata: boltz-core al commit della #196 (20 ott 2026, cantiere swap-lockup)

Tenuta per la storia, se un giorno la #196 esce su npm.

Dopo la chiusura di Boltz (3 ago 2026) `boltz-core` NON viene più dal
pacchetto npm 5.0.0 ma dal SORGENTE del repo al commit
`a932d49c4daaeae3d7940dc1519bf77ef92e6dc1` (24 lug 2026, il merge della
PR #196 «Harden scripts», l'ultimo del ramo `master`): la 5.0.0 è del 22
mag e quella correzione non è mai uscita su npm. Cosa porta: `detectSwap`
lega l'uscita del lockup al tipo o allo script ATTESO (la 5.0.0 ne
accettava quattro forme insieme) e `detectPreimage` riconosce il segreto
dalla sua impronta. Il resto è identico: stesse sette dipendenze, stesse
versioni esatte, stesso esbuild, stesso ingresso tranne la riga di
`boltz-core`.

```
git init boltz-core && cd boltz-core
git fetch --depth 1 https://github.com/BoltzExchange/boltz-core.git a932d49c4daaeae3d7940dc1519bf77ef92e6dc1
git checkout FETCH_HEAD && cd ..
npm install --ignore-scripts @scure/bip39@2.4.0 @scure/bip32@2.4.0 @scure/btc-signer@2.4.1 @noble/curves@2.4.0 @noble/hashes@2.4.0 @scure/base@2.4.0 micro-packed@0.11.1
esbuild ingresso.mjs --bundle --format=iife --global-name=BarattoloSwap --target=es2020 --legal-comments=none --outfile=swap.bundle.js
```

con esbuild 0.28.2, la cartella `boltz-core/` accanto a `ingresso.mjs` e
l'ultimo blocco dell'ingresso qui sotto che finisce con
`} from "./boltz-core/lib/Boltz.ts";` invece di `} from "boltz-core";`
(esbuild impacchetta il TypeScript da sé; nessuno script dei pacchetti
gira, nessuna compilazione Solidity serve). Era RIPRODUCIBILE: costruito due
volte in due cartelle nuove, lo stesso sha256,
`02b4184eff3d8a49` `9ac2597059c9c01a` `d1b107234629e4a3` `39ea83ade8370bd0`
(a gruppi di sedici: lo scanner dei segreti), 378.091 byte; l'impronta
intera stava in `prove.py` (`IMPRONTA_SWAP`).

## La ricetta (20 ott 2026, cantiere swap-telefono; quella in uso)

```
npm install --ignore-scripts boltz-core@5.0.0 @scure/bip39@2.4.0 @scure/bip32@2.4.0 @scure/btc-signer@2.4.1
esbuild ingresso.mjs --bundle --format=iife         --global-name=BarattoloSwap --target=es2020 --legal-comments=none         --outfile=swap.bundle.js
```

con esbuild 0.28.2 e questo `ingresso.mjs`, che esporta SOLO i nomi
elencati in `prove_bundle_swap` (prove.py):

```js
// L'ingresso del bundle dello swap (20 ott 2026, cantiere swap-telefono):
// SOLO i nomi che il telefono usa per uno swap Lightning -> on-chain di
// SATS Routing. L'elenco e' controllato da `prove_bundle_swap` (prove.py).
export { generateMnemonic, validateMnemonic, mnemonicToSeedSync } from "@scure/bip39";
export { wordlist } from "@scure/bip39/wordlists/english.js";
export { HDKey } from "@scure/bip32";
export { Address, OutScript, Transaction, SigHash, NETWORK, TEST_NETWORK } from "@scure/btc-signer";
export { sha256 } from "@noble/hashes/sha2.js";
export { hex } from "@scure/base";
export {
    Musig,
    TaprootUtils,
    SwapTreeSerializer,
    reverseSwapTree,
    compareTrees,
    detectSwap,
    constructClaimTransaction,
    OutputType,
    Scripts,
    targetFee,
} from "boltz-core";
```

Il file NON è minimizzato: si deve poter leggere, come `btc.bundle.js`.
Le due dipendenze facoltative di `boltz-core` per Liquid
(`@vulpemventures/secp256k1-zkp`, che è WASM, e `liquidjs-lib`) NON ci
sono: lo swap è solo bitcoin, e la 5.0.0 le ha rese facoltative.

L'impronta del file è scritta in `prove.py` e la CI la controlla a ogni
commit: se cambia di un byte, diventa rossa.

## Le versioni

| pacchetto | versione | licenza |
|---|---|---|
| `boltz-core` | 5.0.0 | MIT |
| `@scure/bip39` | 2.4.0 | MIT |
| `@scure/bip32` | 2.4.0 | MIT |
| `@scure/btc-signer` | 2.4.1 | MIT |
| `@noble/curves` | 2.4.0 | MIT |
| `@noble/hashes` | 2.4.0 | MIT |
| `@scure/base` | 2.4.0 | MIT |
| `micro-packed` | 0.11.1 | MIT |

## La licenza di boltz-core, chiarita

Il `package.json` di `boltz-core` 5.0.0 dice `"license": "AGPL-3.0"`, ma il
`LICENSE` del pacchetto è MIT, e MIT è la licenza del repo
`BoltzExchange/boltz-core` dal 31 gen 2024 (commit `1be98d54`, «chore:
change license to MIT»). La scritta AGPL era un avanzo: l'hanno corretta
gli autori l'8 giu 2026 (commit `eceaa948`, «fix: license in
package.json»), dopo l'uscita della 5.0.0 (22 mag 2026). Verificato il
20 ott 2026 sul repo.

## Le licenze, per esteso

### boltz-core 5.0.0

```
MIT License

Copyright (c) 2024 Boltz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### @scure/bip39 2.4.0

```
The MIT License (MIT)

Copyright (c) 2022 Patricio Palladino, Paul Miller (paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### @scure/bip32 2.4.0

```
The MIT License (MIT)

Copyright (c) 2022 Patricio Palladino, Paul Miller (paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### @scure/btc-signer 2.4.1

```
The MIT License (MIT)

Copyright (c) 2022 Paul Miller (https://paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### @noble/curves 2.4.0

```
The MIT License (MIT)

Copyright (c) 2022 Paul Miller (https://paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### @noble/hashes 2.4.0

```
The MIT License (MIT)

Copyright (c) 2022 Paul Miller (https://paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### @scure/base 2.4.0

```
The MIT License (MIT)

Copyright (c) 2022 Paul Miller (https://paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### micro-packed 0.11.1

```
The MIT License (MIT)

Copyright (c) 2022 Paul Miller (https://paulmillr.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
