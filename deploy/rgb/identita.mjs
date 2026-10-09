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
//   profilo <nome> [https://…/logo.webp]        firma e pubblica il kind 0 (name, about, nip05, e la picture se data) sul relay LOCALE
//   annuncio <nome> <asset_id>                  firma e pubblica l'ANNUNCIO dell'asset (docs/spec/NIP-RGB-ASSETS.md,
//                                               kind segnaposto) sul relay LOCALE: la riga «16 ott» di HACKATHON-SETUP §10
//   annuncio --prova <nome> <asset_id>          lo stesso evento, firmato e stampato in JSON, NON pubblicato
//                                               (nessun relay toccato: serve alle prove e a guardarlo prima)
//
// Il relay: NWC_RELAY (default ws://127.0.0.1:7777, il `nak serve` locale).
// Niente relay pubblici in questo giro (NWC_RELAY_PUBBLICO_OK=1 per forzare).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { finalizeEvent, generateSecretKey, getPublicKey, nip19, verifyEvent } from 'nostr-tools'
import { Relay } from 'nostr-tools/relay'

const CASA = process.env.IDENTITA_CASA || path.join(os.homedir(), 'wdk-prova', 'identita')
const RELAY = process.env.NWC_RELAY || 'ws://127.0.0.1:7777'
const hex = (b) => Buffer.from(b).toString('hex')
const muori = (msg) => { console.error('✗', msg); process.exit(1) }

// L'ANNUNCIO DELL'ASSET (docs/spec/NIP-RGB-ASSETS.md): un evento
// ADDRESSABLE (kind 3xxxx) firmato dalla chiave dell'emittente, con `d` =
// ContractId. Il numero e' un SEGNAPOSTO, lo assegnano i maintainer dei
// NIP: 38172/38173 sono di NIP-87 (Cashu/Fedimint), questo sta subito
// dopo e non e' registrato da nessuno. L'evento «raccomandazione»
// (3xxxx+1, lo pubblica chiunque) NON si fa qui: la riga del 16 ott
// prevede i due annunci e basta.
const KIND_ANNUNCIO = 38180
// Il tag `n` resta 'signet' su TUTT'E DUE le catene: Mutinynet E' un
// signet (stesso blocco 0, stessa etichetta per rgb-lib), la bozza non
// distingue i signet fra loro, e il ContractId identifica gia' il
// contratto e con lui la catena su cui vive.
const RETE = 'signet'

// LA CATENA (9 ott 2026, studio Mutinynet): RGB_CATENA = signet (default) |
// mutinynet, come in punti.mjs. Gli asset esistono UNA volta per catena
// (riemessi su Mutinynet domenica 11 ott: id nuovi), e la tabella sotto
// e' una per catena. Le stesse identita' (stesse chiavi, stesso NIP-05)
// firmano gli annunci su tutt'e due.
const CATENA = process.env.RGB_CATENA || 'signet'
const RETE_NOME = { signet: 'signet', mutinynet: 'Mutinynet, il signet dell\'hackathon' }
if (!RETE_NOME[CATENA]) muori(`RGB_CATENA=${CATENA}: conosco ${Object.keys(RETE_NOME).join(', ')}`)

// Gli asset che un'identita' puo' annunciare: i valori PUBBLICI di
// HACKATHON-SETUP §2 (ticker, nome, precisione e supply sono COPIE del
// genesis, e il wallet li confronta: devono combaciare con `rgb.py saldo`,
// quindi il nome di USDB porta gli underscore del genesis, non quello
// mostrato). Chi lo annuncia e' l'emittente dichiarato in §2: un secondo
// annuncio dello stesso contratto da un'altra chiave e' una feature
// della bozza, ma nella demo si evita (studio, D.3 punto 4). JAR resta
// fuori dalla demo (decisione di Alan) e non ha un'identita'.
// La descrizione la compone `descrizione()` dal ticker, cosi' le due
// tabelle portano solo quel che cambia: gli id.
const SCHEDE = {
  MOON: {
    ticker: 'MOON', name: 'Punti To The Mooon', precision: 0, supply: 1000000, schema: 'nia',
    emittente: 'tothemooon',
    descrizione: (rete) => `MOON sono i punti fedelta' di PROVA del negozio To The Mooon, emessi su RGB (${rete}) per l'hackathon di Torino (17-18 ott 2026): un punto per euro speso, 1 MOON = 1 sat di sconto nel negozio. Nessun valore reale.`
  },
  USDB: {
    ticker: 'USDB', name: 'Dollari_di_prova_Barattolo', precision: 2, supply: 100000000, schema: 'nia',
    emittente: 'usdb',
    descrizione: (rete) => `USDB sono i «Dollari di prova Barattolo», un asset NIA di PROVA su RGB (${rete}) emesso per l'hackathon di Torino (17-18 ott 2026): 1,00 USDB vale 1 $ dichiarato, accettato al checkout di Barattolo in collaudo. Nessun valore reale.`
  }
}
// ContractId (senza `rgb:`) → scheda, per catena. Quelli di Mutinynet si
// incollano domenica 11 ott dopo `rgb.py emetti` (HACKATHON-SETUP §10,
// la lista di domenica): finche' dicono INCOLLA_QUI nessun id li trova,
// e `annuncio` lo dice chiaro.
const ASSET_PER_CATENA = {
  signet: {
    '9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM': SCHEDE.MOON,
    'H1951SnR-7Jq3pjE-bXen9Qd-0AkXlmm-s~NLk5g-qGVUh9A': SCHEDE.USDB
  },
  mutinynet: {
    'INCOLLA_QUI_ID_MOON_MUTINYNET': SCHEDE.MOON,
    'INCOLLA_QUI_ID_USDB_MUTINYNET': SCHEDE.USDB
  }
}
const ASSET = ASSET_PER_CATENA[CATENA]

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
// Il ContractId nudo: `rgb:` davanti si toglie (in §2 gli asset_id lo
// portano, la bozza vuole `d` senza), la forma e' quella di rgb-lib
// (gruppi di base64url con `~` e `-`).
function contractId (assetId) {
  const id = String(assetId || '').replace(/^rgb:/, '')
  if (!/^[A-Za-z0-9_~-]{20,80}$/.test(id)) muori('annuncio <nome> <asset_id>: l\'asset_id e\' quello di `rgb.py saldo` (con o senza `rgb:` davanti)')
  return id
}
async function pubblicaEvento (ev) {
  const relay = await Relay.connect(RELAY)
  try { await relay.publish(ev) } finally { relay.close() }
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

  // `picture` (9 ott 2026, richiesta di Andrea): l'URL https del logo
  // (per tothemooon il file gia' in assets/consigliati/ del sito), che i
  // client mostrano accanto al nome. Solo https: un kind 0 e' pubblico
  // per costruzione, e un'immagine su http la caricherebbero in chiaro.
  // Senza argomento il kind 0 resta quello dell'8 ott, senza picture.
  async profilo (nome, picture) {
    const i = leggi(nome)
    if (picture !== undefined && !/^https:\/\/[^\s/]+\/\S+$/.test(picture)) muori('profilo <nome> [https://…/logo]: la picture e\' un URL https')
    const sk = Uint8Array.from(Buffer.from(i.sk, 'hex'))
    const ev = finalizeEvent({
      kind: 0, created_at: Math.floor(Date.now() / 1000), tags: [],
      content: JSON.stringify({
        name: i.display, display_name: i.display, nip05: i.nip05,
        about: `Identita' di PROVA dell'hackathon RGB di Torino (17-18 ott 2026): l'emittente dichiarato di un asset su signet. Nessun valore reale.`,
        ...(picture ? { picture } : {})
      })
    }, sk)
    await pubblicaEvento(ev)
    console.log(`✓ kind 0 di «${nome}» (${i.nip05}${picture ? ', con picture' : ''}) pubblicato su ${RELAY}, id ${ev.id.slice(0, 12)}…`)
  },

  // Sul calco di `profilo`: legge l'identita', costruisce l'evento della
  // bozza, lo firma. Con --prova lo stampa e si ferma PRIMA del relay.
  // Niente `issuer` (il genesis dei nostri asset porta `ssi:anonymous`:
  // siamo al livello 1, «verificato» via NIP-05, non «impegnato») e
  // niente `u` (il consignment del contratto non e' servito da nessuna
  // parte): si aggiungono il giorno che esistono.
  async annuncio (...args) {
    const prova = args[0] === '--prova'
    if (prova) args.shift()
    const [nome, assetId] = args
    if (!nome || !assetId) muori('annuncio [--prova] <nome> <asset_id>')
    const i = leggi(nome)
    const id = contractId(assetId)
    const a = ASSET[id]
    if (!a) {
      const vuoti = Object.keys(ASSET).filter(k => k.startsWith('INCOLLA_QUI'))
      if (vuoti.length) muori(`asset ${id} sconosciuto: la tabella di ${CATENA} ha ancora ${vuoti.length} segnaposto (${vuoti.join(', ')}): dopo \`rgb.py emetti\` su ${CATENA} si incollano gli id al loro posto (HACKATHON-SETUP §10, domenica 11)`)
      muori(`asset ${id} sconosciuto: la tabella ASSET di questo file per ${CATENA} conosce ${Object.values(ASSET).map(x => x.ticker).join(', ')} (§2); un asset nuovo si aggiunge li' copiando ticker, nome, precisione e supply dal genesis`)
    }
    if (a.emittente !== nome) muori(`${a.ticker} lo annuncia «${a.emittente}», non «${nome}»: due annunci dello stesso contratto da chiavi diverse nella demo si evitano (studio, D.3 punto 4)`)
    const sk = Uint8Array.from(Buffer.from(i.sk, 'hex'))
    const ev = finalizeEvent({
      kind: KIND_ANNUNCIO, created_at: Math.floor(Date.now() / 1000),
      tags: [
        ['d', id],
        ['i', `rgb:contract:${id}`], ['k', 'rgb:contract'],
        ['n', RETE],
        ['schema', a.schema],
        ['ticker', a.ticker],
        ['name', a.name],
        ['precision', String(a.precision)],
        ['supply', String(a.supply)],
        ['alt', `RGB asset announcement: ${a.ticker}`]
      ],
      content: `${a.descrizione(RETE_NOME[CATENA])} Emittente dichiarato: ${i.display} (${i.nip05}).`
    }, sk)
    if (!verifyEvent(ev)) muori('la firma dell\'evento non torna: non si pubblica')
    if (prova) {
      console.log(JSON.stringify(ev, null, 2))
      console.error(`— di PROVA: annuncio di ${a.ticker} (${CATENA}) firmato da «${nome}» (${i.nip05}), kind ${KIND_ANNUNCIO} (segnaposto), d ${id}, firma valida. NON pubblicato, nessun relay toccato.`)
      return
    }
    await pubblicaEvento(ev)
    console.log(`✓ annuncio di ${a.ticker} (${CATENA}) firmato da «${nome}» (${i.nip05}) pubblicato su ${RELAY}: kind ${KIND_ANNUNCIO} (segnaposto), d ${id}, id ${ev.id.slice(0, 12)}…`)
    console.log(`  per rileggerlo: la riga «rilettura» di HACKATHON-SETUP §10 (nostr-tools, kind ${KIND_ANNUNCIO}, autore ${ev.pubkey}); \`nak req\` lanciato da wsl.exe stampa muto`)
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
