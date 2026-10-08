#!/usr/bin/env node
// identita.mjs — le identita' Nostr DI PROVA degli emittenti degli asset
// dell'hackathon (gli «emittenti» di USDB e di MOON). Chiavi NUOVE, mai
// quella della piattaforma; la privata vive SOLO nel file (0600) e non si
// stampa mai; si stampa la PUBBLICA, che va nel config del VPS
// (`NIP05_NOMI = {"usdb": "<hex>", …}`) e negli annunci di domani.
//
// Casa: ~/wdk-prova/identita/<nome>.json  {nome, nip05, display, sk (hex)}
//
// Uso:  node identita.mjs <comando> [argomenti]
//   nuova <nome> "<Nome mostrato>" <nip05>     crea la coppia di chiavi e il file; stampa la pubblica
//   pubblica <nome>                             la chiave pubblica (hex e npub), senza toccare niente
//   profilo <nome>                              firma e pubblica il kind 0 (name, about, nip05) sul relay LOCALE
//
// Il relay: NWC_RELAY (default ws://127.0.0.1:7777, il `nak serve` locale).
// Niente relay pubblici in questo giro (NWC_RELAY_PUBBLICO_OK=1 per forzare).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { finalizeEvent, generateSecretKey, getPublicKey, nip19 } from 'nostr-tools'
import { Relay } from 'nostr-tools/relay'

const CASA = process.env.IDENTITA_CASA || path.join(os.homedir(), 'wdk-prova', 'identita')
const RELAY = process.env.NWC_RELAY || 'ws://127.0.0.1:7777'
const hex = (b) => Buffer.from(b).toString('hex')
const muori = (msg) => { console.error('✗', msg); process.exit(1) }

if (/^wss?:\/\/(?!127\.0\.0\.1|localhost)/i.test(RELAY) && !process.env.NWC_RELAY_PUBBLICO_OK) {
  muori(`il relay ${RELAY} non e' locale: in questo giro niente relay pubblici`)
}

function file (nome) {
  if (!/^[a-z0-9._-]{1,30}$/.test(nome || '')) muori('il nome: minuscole, cifre, punto, trattino, trattino basso (l\'alfabeto del NIP-05)')
  return path.join(CASA, `${nome}.json`)
}
function leggi (nome) {
  const f = file(nome)
  if (!fs.existsSync(f)) muori(`${f} non esiste: prima \`nuova ${nome} …\``)
  return JSON.parse(fs.readFileSync(f, 'utf8'))
}
function stampaPubblica (nome, pub) {
  console.log(`${nome}: hex ${pub}`)
  console.log(`${' '.repeat(nome.length)}  npub ${nip19.npubEncode(pub)}`)
}

const COMANDI = {
  nuova (nome, display, nip05) {
    const f = file(nome)
    if (!display || !nip05) muori('nuova <nome> "<Nome mostrato>" <nip05>')
    if (!/^[a-z0-9._-]+@[a-z0-9.-]+\.[a-z]{2,}$/i.test(nip05)) muori('il nip05 ha la forma nome@dominio')
    if (fs.existsSync(f)) muori(`${f} esiste gia': non si rigenera una chiave sopra un\'identita' viva`)
    fs.mkdirSync(CASA, { recursive: true, mode: 0o700 })
    const sk = generateSecretKey()
    fs.writeFileSync(f, JSON.stringify({ nome, display, nip05, sk: hex(sk), creato: new Date().toISOString() }, null, 2) + '\n', { mode: 0o600 })
    console.log(`✓ identita' «${nome}» creata in ${f} (la privata sta SOLO li')`)
    stampaPubblica(nome, getPublicKey(sk))
  },

  pubblica (nome) {
    const i = leggi(nome)
    stampaPubblica(nome, getPublicKey(Uint8Array.from(Buffer.from(i.sk, 'hex'))))
  },

  async profilo (nome) {
    const i = leggi(nome)
    const sk = Uint8Array.from(Buffer.from(i.sk, 'hex'))
    const ev = finalizeEvent({
      kind: 0, created_at: Math.floor(Date.now() / 1000), tags: [],
      content: JSON.stringify({
        name: i.display, display_name: i.display, nip05: i.nip05,
        about: `Identita' di PROVA dell'hackathon RGB di Torino (17-18 ott 2026): l'emittente dichiarato di un asset su signet. Nessun valore reale.`
      })
    }, sk)
    const relay = await Relay.connect(RELAY)
    await relay.publish(ev)
    relay.close()
    console.log(`✓ kind 0 di «${nome}» (${i.nip05}) pubblicato su ${RELAY}, id ${ev.id.slice(0, 12)}…`)
  }
}

const [cmd, ...args] = process.argv.slice(2)
if (!cmd || !COMANDI[cmd]) {
  console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').filter(l => l.startsWith('//')).map(l => l.slice(3)).join('\n'))
  process.exit(2)
}
try {
  await COMANDI[cmd](...args)
} catch (e) {
  muori(e?.message || e)
}
