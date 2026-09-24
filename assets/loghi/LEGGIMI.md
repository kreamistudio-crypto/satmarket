# I loghi dei tondi (24 set 2026)

I tondi del riquadro del venditore — negozio, Profilo e card della
controparte nello scambio P2P — usano i loghi VERI, mai ridisegnati né
ricolorati. In pagina viaggiano come `data:` URI dentro `miniapp.html`,
BYTE PER BYTE uguali a questi file: lo controlla `prove.py`
(`prove_loghi_tondi`), quindi chi li cambia cambia questi file e rifà
il `data:` URI, mai uno dei due da solo.

- `telegram.webp` — il logo ufficiale di Telegram (il cerchio azzurro
  con l'aeroplano bianco), dalla pagina dei loghi di Telegram.
  Originale: `logo-telegram.png`, 1000×1000, 197.144 byte, sha256
  `f91e9d7c30894cb0f00196581d4cc8867dd1139b2b1455de2c58071103475ca8`.
  È un marchio di Telegram: qui dice soltanto «questo bottone ti porta
  su Telegram», che è l'uso per cui la pagina dei loghi lo offre.
- `nostr.webp` — il logo di Nostr (la «n» viola con lo struzzo), dal
  pacchetto di github.com/mbarulli/nostr-logo, rilasciato CC0 1.0
  (pubblico dominio). Originale: `logo-nostr.png`, 256×256, 3.189 byte,
  sha256 `85d68c69723600993cbe18fe1c28324570b25fafde9ca4fefc62acb5ec2e155c`.
- L'icona «link» di Lucide (i due anelli intrecciati) non ha un file
  qui: è un SVG di due tracciati, e sta dentro `miniapp.html` con i
  tracciati dell'originale (`icons/link.svg` del repository di Lucide),
  che la prova confronta a uno a uno. È una delle icone che Lucide ha
  ereditato da Feather, quindi vale la licenza MIT di Feather oltre
  alla ISC di Lucide: i due testi sono qui sotto, come chiedono.

LA RICETTA (Pillow): alfa PREMOLTIPLICATO (`RGBa`), riduzione LANCZOS,
WebP senza perdita (`method=6`). Telegram a 120×120 — il tondo è largo
40px, e a densità 3 ne servono 120. Nostr ritagliato sul riquadro
opaco dell'originale, (52,47)-(212,207), e ridotto a 72×72 — nel tondo
è largo 24px (a 26 gli spigoli della «n» sfioravano il bordo). Senza il
premoltiplicato il bordo sfumato del cerchio si mescolava col nero dei
pixel trasparenti, e nasceva un alone scuro.

## Licenza MIT (Feather, per l'icona «link»)

The MIT License (MIT)

Copyright (c) 2013-present Cole Bemis

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

## Licenza ISC (Lucide)

ISC License

Copyright (c) 2026 Lucide Icons and Contributors

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
