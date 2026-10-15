#!/usr/bin/env node
// relay-di-barattolo.mjs — il kind 10002 di Barattolo (NIP-65): la lista
// dei relay dove Barattolo SCRIVE e dove gli altri lo trovano. Firmato da
// AMBER sul telefono di Andrea, con la chiave di Barattolo che sta solo
// la': qui non entra mai una nsec, lo script non ne sa leggere una.
// (15 ott 2026, cantiere «relay-di-barattolo»; i passi: PRODUZIONE,
// «IL KIND 10002 DI BARATTOLO».)
//
// Uso (dal WSL, in una cartella SOTTO ~/wdk-prova, dove c'e' nostr-tools):
//   node relay-di-barattolo.mjs prova    l'evento NON firmato, in JSON: nessun relay toccato
//   node relay-di-barattolo.mjs guarda   SOLA LETTURA: la 10002 e la 10050 di Barattolo oggi, relay per relay
//   node relay-di-barattolo.mjs firma    il QR nostrconnect per Amber; Amber firma il solo kind 10002;
//                                        il controllo; la domanda «pubblico?»; la pubblicazione
//
// LA LISTA E' QUELLA DEL SERVER (`RELAY_DI_SERIE` in server.py, nello
// stesso ordine): una sentinella di prove.py le tiene uguali. Senza
// etichetta (lettura e scrittura) i relay dei DM, quelli del 10050
// (`AVVISO_DM_NOSTR_RELAY`), dove Barattolo ascolta davvero; gli altri
// «write»: Barattolo ci pubblica, ma da li' non legge chi lo cita — e il
// nostro relay le scritture altrui le rifiuta (whitelist).
// IL 10050 NON SI TOCCA: e' un altro evento, coi suoi passi.
import fs from 'node:fs'
import path from 'node:path'
import readline from 'node:readline/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import { generateSecretKey, getPublicKey, nip19, verifyEvent } from 'nostr-tools'
import { Relay } from 'nostr-tools/relay'
import { BunkerSigner, createNostrConnectURI } from 'nostr-tools/nip46'

// La chiave PUBBLICA di Barattolo (la stessa del 10050).
const NPUB = 'npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy'
const LISTA = [
  'wss://relay.primal.net',
  'wss://relay.nostr.net',
  'wss://nostr.oxtr.dev',
  'wss://nos.lol',
  'wss://relay.mostro.network',
  'wss://relay.barattolo.store',
]
const LEGGE = ['wss://nos.lol', 'wss://relay.primal.net']
// Dove i client CERCANO le 10002 altrui: la pubblicazione va anche qui.
const INDICI = ['wss://purplepag.es']
// La stanza del NIP-46: gli stessi relay del login QR (`RELAYS_NIP46`).
const STANZA = [
  'wss://nrs.primal.net',
  'wss://bucket.coracle.social',
  'wss://relay.nip46.com',
  'wss://nos.lol',
  'wss://relay.powr.build',
]
const KIND = 10002
const ATTESA_FIRMA_MS = 5 * 60 * 1000
const TETTO_RELAY_MS = 10000

const muori = (msg) => { console.error('✗', msg); process.exit(1) }

// IL BANCO DI PROVA (solo per prove.py e per il giro col firmatario di
// cartone): la stanza, la chiave attesa e dove pubblicare si possono
// spostare, ma SOLO su un relay di loopback — cosi' nessuna variabile
// dimenticata nell'ambiente manda la lista di qualcun altro in giro.
function soloLoopback(nome) {
  const v = process.env[nome]
  if (!v) return null
  const lista = v.split(',').map((s) => s.trim()).filter(Boolean)
  if (!lista.length || !lista.every((r) => /^ws:\/\/127\.0\.0\.1:\d+$/.test(r)))
    muori(`${nome}: solo ws://127.0.0.1:<porta>, separati da virgole`)
  return lista
}
const STANZA_VERA = soloLoopback('RELAY10002_PROVA_STANZA') || STANZA
const DOVE = soloLoopback('RELAY10002_PROVA_DOVE') || [...LISTA, ...INDICI]
const HEX = nip19.decode(process.env.RELAY10002_PROVA_NPUB || NPUB).data

function bozza() {
  return {
    kind: KIND,
    created_at: Math.floor(Date.now() / 1000),
    tags: LISTA.map((r) => LEGGE.includes(r) ? ['r', r] : ['r', r, 'write']),
    content: '',
  }
}

// Il controllo prima di pubblicare: e' di Barattolo, e' una 10002, dice
// ESATTAMENTE la lista di qui, e la firma regge.
function controlla(ev, attesa) {
  const male = []
  if (ev.pubkey !== HEX) male.push('NON e\' firmato da Barattolo (account sbagliato in Amber?)')
  if (ev.kind !== KIND) male.push(`kind ${ev.kind} invece di ${KIND}`)
  if (JSON.stringify(ev.tags) !== JSON.stringify(attesa.tags)) male.push('i tag non sono quelli chiesti')
  if (ev.content !== '') male.push('il contenuto non e\' vuoto')
  if (!verifyEvent(ev)) male.push('la firma non regge')
  return male
}

async function chiedi(url, filtro) {
  let relay
  try {
    relay = await Promise.race([
      Relay.connect(url),
      new Promise((_, no) => setTimeout(() => no(new Error('non si apre')), TETTO_RELAY_MS)),
    ])
  } catch (e) { return { errore: e.message } }
  return await new Promise((ok) => {
    const visti = []
    let finito = false
    // prima la risposta, poi la chiusura: chiudere fa scattare onclose,
    // che altrimenti risponderebbe lui («chiuso») al posto dell'EOSE
    const fine = (x) => {
      if (finito) return
      finito = true
      ok(x)
      try { relay.close() } catch {}
    }
    const t = setTimeout(() => fine({ errore: 'nessun EOSE' }), TETTO_RELAY_MS)
    relay.subscribe([filtro], {
      onevent: (e) => visti.push(e),
      oneose: () => { clearTimeout(t); fine({ eventi: visti }) },
      onclose: (r) => { clearTimeout(t); fine({ errore: `chiuso: ${r}` }) },
    })
  })
}

async function guarda() {
  console.log(`Barattolo ${NPUB.slice(0, 16)}…: la 10002 e la 10050 oggi (sola lettura)\n`)
  for (const url of DOVE) {
    const r = await chiedi(url, { kinds: [KIND, 10050], authors: [HEX] })
    if (r.errore) { console.log(`${url}\n   ✗ ${r.errore}`); continue }
    console.log(url)
    if (!r.eventi.length) console.log('   (niente)')
    for (const e of r.eventi.sort((a, b) => a.kind - b.kind)) {
      const quando = new Date(e.created_at * 1000).toISOString().slice(0, 16).replace('T', ' ')
      const rel = e.tags.filter((t) => t[0] === (e.kind === KIND ? 'r' : 'relay'))
        .map((t) => t[1] + (t[2] ? ` (${t[2]})` : ''))
      console.log(`   ${e.kind} del ${quando} UTC: ${rel.join(', ')}`)
    }
  }
}

function qr(testo) {
  // qrcode-generator 1.5.2, la copia vendorizzata della Mini App
  // (vendor/qrcode.js): accanto allo script, o al suo posto nel repo.
  const qui = path.dirname(fileURLToPath(import.meta.url))
  const dove = [path.join(qui, 'qrcode.js'), path.join(qui, '..', '..', 'vendor', 'qrcode.js')]
    .find((p) => fs.existsSync(p))
  if (!dove) return '(qrcode.js non trovato accanto allo script: incolla il link qui sotto in Amber)'
  const qrcode = createRequire(import.meta.url)(dove)
  const q = qrcode(0, 'L')
  q.addData(testo)
  q.make()
  return q.createASCII(1, 2)
}

async function firma() {
  const attesa = bozza()
  const locale = generateSecretKey()          // la chiave della STANZA, usa-e-getta
  const segreto = Buffer.from(generateSecretKey()).toString('hex').slice(0, 16)
  const uri = createNostrConnectURI({
    clientPubkey: getPublicKey(locale),
    relays: STANZA_VERA,
    secret: segreto,
    perms: [`sign_event:${KIND}`],
    name: 'Barattolo — lista relay (10002)',
    url: 'https://barattolo.store',
  })
  console.log('Inquadra con Amber, account BARATTOLO, approvazione manuale:\n')
  console.log(qr(uri))
  console.log(`\n${uri}\n`)
  console.log('Aspetto Amber (5 minuti)…')
  let signer
  try {
    signer = await BunkerSigner.fromURI(locale, uri, {}, ATTESA_FIRMA_MS)
  } catch (e) { muori(`Amber non si e' collegato: ${e.message}`) }
  console.log('Collegato. In Amber approva la firma del kind 10002, e solo quella.')
  let ev
  try {
    ev = await signer.signEvent(attesa)
  } catch (e) { await signer.close(); muori(`firma rifiutata o scaduta: ${e.message}`) }
  await signer.close()
  const male = controlla(ev, attesa)
  if (male.length) muori('NON PUBBLICO: ' + male.join('; '))
  console.log('\nOK: firmato da Barattolo, kind 10002, la lista e\' quella giusta:')
  for (const t of ev.tags) console.log(`   ${t[1]}${t[2] ? ' (' + t[2] + ')' : ''}`)
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
  const si = (await rl.question(`\nPubblico su ${DOVE.length} relay? (si/no) `)).trim().toLowerCase()
  rl.close()
  if (si !== 'si') { console.log('Niente pubblicato.'); return }
  let presi = 0
  for (const url of DOVE) {
    try {
      const relay = await Relay.connect(url)
      await Promise.race([
        relay.publish(ev),
        new Promise((_, no) => setTimeout(() => no(new Error('nessun OK')), TETTO_RELAY_MS)),
      ])
      relay.close()
      presi++
      console.log(`   ✓ ${url}`)
    } catch (e) { console.log(`   ✗ ${url}: ${e.message}`) }
  }
  console.log(`\nPresa da ${presi} relay su ${DOVE.length}. Controllo: node relay-di-barattolo.mjs guarda`)
}

const [comando] = process.argv.slice(2)
if (comando === 'prova') console.log(JSON.stringify({ ...bozza(), pubkey: HEX }, null, 2))
else if (comando === 'guarda') await guarda()
else if (comando === 'firma') await firma()
else muori('comandi: prova | guarda | firma')
process.exit(0)
