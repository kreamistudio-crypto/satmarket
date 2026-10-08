#!/usr/bin/env node
// nwc-wdk.mjs — il wallet WDK dell'utente che parla NIP-47 (Nostr Wallet
// Connect), per l'hackathon di Torino. E' la BASE preparata prima
// dell'evento e dichiarata: evento info, `get_info`, `get_balance`, la
// connection string per il Profilo di Barattolo. I metodi `rgb_*` della
// bozza di estensione (rgb_list_assets, rgb_make_invoice, rgb_pay_invoice,
// rgb_lookup_transfer) si scrivono a Torino, in commit datati: qui c'e'
// il posto dove entrano (`METODI`), e basta.
//
// Scritto a mano con nostr-tools e non con NWCWalletService di @getalby/sdk,
// che ha gli handler tipizzati (getInfo, payInvoice…) e non fa passare un
// metodo fuori lista: i nostri lo sono per definizione.
//
// Casa: ~/wdk-prova/nwc/
//   servizio.txt              la chiave privata del servizio (hex, 0600): nasce al primo uso
//   connessioni.json          le chiavi PUBBLICHE dei client autorizzati {pub: {nome, creato}}
//   connessione-<nome>.txt    la connection string da incollare nel Profilo (0600): c'e' il secret
//
// Uso:  node nwc-wdk.mjs <comando> [argomenti]
//   info                       la chiave pubblica del servizio e il relay (niente di segreto)
//   connetti <nome>            autorizza un client nuovo e scrive la sua connection string su file
//   serve                      resta in ascolto sul relay e risponde (Ctrl-C per fermare)
//   prova <nome>               un client di prova: manda get_info e get_balance e stampa le risposte
//
// Il relay: NWC_RELAY (default ws://127.0.0.1:7777, il `nak serve` locale).
// Mai un relay pubblico in questo giro. Il wallet WDK (punti.mjs) si apre
// SOLO quando serve `get_balance`, e resta aperto finche' il servizio gira:
// in quel tempo non si lancia `node punti.mjs …` (rgb-lib: «never
// instantiate a wallet in multiple places»).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { finalizeEvent, generateSecretKey, getPublicKey, verifyEvent, nip04, nip44 } from 'nostr-tools'
import { Relay } from 'nostr-tools/relay'

const CASA = process.env.NWC_CASA || path.join(os.homedir(), 'wdk-prova', 'nwc')
const RELAY = process.env.NWC_RELAY || 'ws://127.0.0.1:7777'
const FILE_SERVIZIO = path.join(CASA, 'servizio.txt')
const FILE_CONNESSIONI = path.join(CASA, 'connessioni.json')
const ALIAS = 'WDK Barattolo (prova, signet)'
const RETE = 'signet'
const KIND_INFO = 13194, KIND_RICHIESTA = 23194, KIND_RISPOSTA = 23195

const hex = (b) => Buffer.from(b).toString('hex')   // SOLO per le chiavi private (Uint8Array): getPublicKey torna gia' hex
const daHex = (h) => Uint8Array.from(Buffer.from(h, 'hex'))
const muori = (msg) => { console.error('✗', msg); process.exit(1) }
const adesso = () => Math.floor(Date.now() / 1000)

if (/^wss?:\/\/(?!127\.0\.0\.1|localhost)/i.test(RELAY) && !process.env.NWC_RELAY_PUBBLICO_OK) {
  muori(`il relay ${RELAY} non e' locale: in questo giro niente relay pubblici (NWC_RELAY_PUBBLICO_OK=1 per forzare)`)
}

// ----------------------------------------------------------------- chiavi
function chiaveServizio (crea = false) {
  if (fs.existsSync(FILE_SERVIZIO)) return daHex(fs.readFileSync(FILE_SERVIZIO, 'utf8').trim())
  if (!crea) muori('il servizio non ha ancora una chiave: prima `node nwc-wdk.mjs connetti <nome>`')
  fs.mkdirSync(CASA, { recursive: true, mode: 0o700 })
  const sk = generateSecretKey()
  fs.writeFileSync(FILE_SERVIZIO, hex(sk) + '\n', { mode: 0o600 })
  console.log(`✓ chiave del servizio creata in ${FILE_SERVIZIO} (non si stampa, non si incolla)`)
  return sk
}

function connessioni () {
  return fs.existsSync(FILE_CONNESSIONI) ? JSON.parse(fs.readFileSync(FILE_CONNESSIONI, 'utf8')) : {}
}

// ----------------------------------------------------------------- cifratura
// Il client dice come cifra col tag `encryption` della richiesta
// (`nip44_v2`); assente = nip04, come scrive il NIP. Si risponde con lo
// stesso schema con cui si e' stati interrogati.
function schemaDi (evento) {
  const tag = (evento.tags || []).find(t => t[0] === 'encryption')
  return tag && /nip44/.test(tag[1] || '') ? 'nip44_v2' : 'nip04'
}

async function decifra (schema, sk, pubAltro, testo) {
  if (schema === 'nip44_v2') return nip44.v2.decrypt(testo, nip44.v2.utils.getConversationKey(sk, pubAltro))
  return nip04.decrypt(sk, pubAltro, testo)
}

async function cifra (schema, sk, pubAltro, testo) {
  if (schema === 'nip44_v2') return nip44.v2.encrypt(testo, nip44.v2.utils.getConversationKey(sk, pubAltro))
  return nip04.encrypt(sk, pubAltro, testo)
}

// ----------------------------------------------------------------- il wallet
let wdk = null
async function wallet () {
  if (wdk) return wdk
  const { default: WalletManagerRgb } = await import('@utexo/wdk-wallet-rgb')
  const casaUtente = process.env.PUNTI_CASA || path.join(os.homedir(), 'wdk-prova', 'utente')
  const seme = path.join(casaUtente, 'seme.txt')
  if (!fs.existsSync(seme)) throw new Error('il wallet utente non esiste (punti.mjs nuovo)')
  const manager = new WalletManagerRgb(fs.readFileSync(seme, 'utf8').trim(), {
    network: RETE,
    indexerUrl: process.env.RGB_INDEXER || 'tcp://127.0.0.1:50001',
    transportEndpoint: process.env.RGB_PROXY || 'rpc://127.0.0.1:3000/json-rpc',
    dataDir: path.join(casaUtente, 'wallet')
  })
  const account = await manager.getAccount()
  wdk = { manager, account }
  console.log('🟪 wallet WDK aperto (resta aperto finche\' il servizio gira)')
  return wdk
}

// I sats «vanilla» confermati, in msat: e' il saldo che NIP-47 intende.
// La forma di btcBalance e' quella di rgb-lib ({vanilla:{settled,future},
// colored:{…}}); se un giorno cambiasse, si legge quel che c'e' e si dice.
function msatDa (btcBalance) {
  const v = btcBalance?.vanilla ?? btcBalance
  const settled = Number(v?.settled ?? v ?? 0)
  return Math.round(settled * 1000)
}

// ----------------------------------------------------------------- i metodi
// Qui entreranno i quattro `rgb_*` a Torino. Ogni handler riceve `params`
// e torna `result`, o lancia {code, message}.
const METODI = {
  async get_info () {
    return {
      alias: ALIAS, color: '#f5a623', pubkey: getPublicKey(chiaveServizio()),
      network: RETE, block_height: 0, block_hash: '',
      methods: Object.keys(METODI), notifications: []
    }
  },
  async get_balance () {
    const { account } = await wallet()
    const reg = await account.registerWallet()
    return { balance: msatDa(reg.btcBalance) }
  }
}

async function rispondi (relay, sk, evento) {
  const miaPub = getPublicKey(sk)
  const autore = evento.pubkey
  const autorizzati = connessioni()
  if (!autorizzati[autore]) { console.log(`· richiesta da un client non autorizzato (${autore.slice(0, 8)}…): ignorata`); return }
  const scad = (evento.tags || []).find(t => t[0] === 'expiration')
  if (scad && Number(scad[1]) < adesso()) { console.log('· richiesta scaduta: ignorata'); return }
  const schema = schemaDi(evento)
  let richiesta
  try { richiesta = JSON.parse(await decifra(schema, sk, autore, evento.content)) } catch (e) { console.log('· richiesta che non si decifra:', e.message); return }
  const metodo = String(richiesta.method || '')
  let risposta
  if (!METODI[metodo]) {
    risposta = { result_type: metodo, error: { code: 'NOT_IMPLEMENTED', message: `metodo sconosciuto: ${metodo}` }, result: null }
  } else {
    try {
      risposta = { result_type: metodo, error: null, result: await METODI[metodo](richiesta.params || {}) }
    } catch (e) {
      risposta = { result_type: metodo, error: { code: e.code || 'INTERNAL', message: e.message || String(e) }, result: null }
    }
  }
  const ev = finalizeEvent({
    kind: KIND_RISPOSTA, created_at: adesso(),
    tags: [['p', autore], ['e', evento.id]],
    content: await cifra(schema, sk, autore, JSON.stringify(risposta))
  }, sk)
  await relay.publish(ev)
  console.log(`✓ ${autorizzati[autore].nome}: ${metodo} → ${risposta.error ? risposta.error.code : 'ok'} (${schema})`)
}

// ----------------------------------------------------------------- comandi
const COMANDI = {
  info () {
    console.log('relay:    ', RELAY)
    console.log('servizio: ', fs.existsSync(FILE_SERVIZIO) ? getPublicKey(chiaveServizio()) : '(nessuna chiave ancora)')
    console.log('metodi:   ', Object.keys(METODI).join(' '))
    const c = connessioni()
    console.log('client:   ', Object.keys(c).length ? Object.values(c).map(x => x.nome).join(', ') : '(nessuno)')
  },

  connetti (nome) {
    if (!/^[a-z0-9-]{1,30}$/.test(nome || '')) muori('connetti <nome>: minuscole, cifre e trattini (es. barattolo)')
    const sk = chiaveServizio(true)
    const segreto = generateSecretKey()
    const pubClient = getPublicKey(segreto)
    const c = connessioni()
    c[pubClient] = { nome, creato: new Date().toISOString() }
    fs.writeFileSync(FILE_CONNESSIONI, JSON.stringify(c, null, 2) + '\n', { mode: 0o600 })
    const stringa = `nostr+walletconnect://${getPublicKey(sk)}?relay=${encodeURIComponent(RELAY)}&secret=${hex(segreto)}`
    const dest = path.join(CASA, `connessione-${nome}.txt`)
    fs.writeFileSync(dest, stringa + '\n', { mode: 0o600 })
    console.log(`✓ client «${nome}» autorizzato (pub ${pubClient.slice(0, 8)}…)`)
    console.log(`  la connection string sta in ${dest}: si incolla nel Profilo, non in chat`)
  },

  async serve () {
    const sk = chiaveServizio()
    const miaPub = getPublicKey(sk)
    const relay = await Relay.connect(RELAY)
    const info = finalizeEvent({
      kind: KIND_INFO, created_at: adesso(),
      tags: [['encryption', 'nip44_v2 nip04']],
      content: Object.keys(METODI).join(' ')
    }, sk)
    await relay.publish(info)
    console.log(`🟪 servizio NWC su ${RELAY}, pub ${miaPub.slice(0, 8)}…, metodi: ${info.content}`)
    relay.subscribe([{ kinds: [KIND_RICHIESTA], '#p': [miaPub], since: adesso() - 60 }], {
      onevent (ev) {
        if (!verifyEvent(ev)) return
        rispondi(relay, sk, ev).catch(e => console.log('✗', e.message))
      }
    })
    relay.onclose = () => { console.log('✗ il relay ha chiuso'); process.exit(1) }
    process.on('SIGINT', () => { try { wdk?.account?.dispose(); wdk?.manager?.dispose(); relay.close() } catch {} ; process.exit(0) })
    await new Promise(() => {})
  },

  async prova (nome) {
    const f = path.join(CASA, `connessione-${nome || 'barattolo'}.txt`)
    if (!fs.existsSync(f)) muori(`manca ${f}: prima \`connetti ${nome || 'barattolo'}\``)
    const u = new URL(fs.readFileSync(f, 'utf8').trim())
    const pubServizio = u.hostname || u.pathname.replace(/^\/+/, '')
    const segreto = daHex(u.searchParams.get('secret'))
    const relayUrl = u.searchParams.get('relay')
    const relay = await Relay.connect(relayUrl)
    const miaPub = getPublicKey(segreto)
    const chiedi = (method) => new Promise(async (ok, no) => {
      const t = setTimeout(() => no(new Error(`${method}: nessuna risposta in 10 s`)), 10000)
      const ev = finalizeEvent({
        kind: KIND_RICHIESTA, created_at: adesso(),
        tags: [['p', pubServizio], ['encryption', 'nip44_v2'], ['expiration', String(adesso() + 60)]],
        content: await cifra('nip44_v2', segreto, pubServizio, JSON.stringify({ method, params: {} }))
      }, segreto)
      const sub = relay.subscribe([{ kinds: [KIND_RISPOSTA], '#e': [ev.id], '#p': [miaPub] }], {
        async onevent (r) {
          clearTimeout(t); sub.close()
          ok(JSON.parse(await decifra('nip44_v2', segreto, pubServizio, r.content)))
        }
      })
      await relay.publish(ev)
    })
    for (const m of ['get_info', 'get_balance', 'rgb_list_assets']) {
      try { console.log(m, '→', JSON.stringify(await chiedi(m))) } catch (e) { console.log(m, '✗', e.message) }
    }
    relay.close()
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
