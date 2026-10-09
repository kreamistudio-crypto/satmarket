#!/usr/bin/env node
// punti.mjs — il wallet dell'UTENTE per la prova dell'hackathon: WDK di Tether
// col modulo RGB di Utexo (@utexo/wdk-wallet-rgb), su signet, sul portatile.
// Parla con l'indexer e col proxy della VM «rgb-prova» attraverso il tunnel
// SSH (127.0.0.1:50001 e 127.0.0.1:3000), o con quelli pubblici se glieli dai.
//
// Casa: ~/wdk-prova/utente/   seme.txt (la frase, 0600)   wallet/ (lo stash)
//
// Uso:  node punti.mjs <comando> [argomenti]
//   nuovo                              genera la frase (una volta sola)
//   indirizzo                          l'indirizzo signet del wallet
//   saldo                              sats, UTXO e asset
//   utxo [quanti]                      crea UTXO colorabili (vuole sats)
//   fattura <asset_id|-> <quantita> [witness]   una fattura RGB per ricevere
//   riscatta <asset_id> <quantita> <fattura>    manda punti (es. al negozio)
//   aggiorna                           refresh: consignment, ACK, conferme
//   trasferimenti [asset_id]           la storia
//   backup                             backup cifrato in ~/wdk-prova/backup
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import WalletManagerRgb from '@utexo/wdk-wallet-rgb'
import * as bip39 from 'bip39'

// LA CATENA (9 ott 2026, studio Mutinynet): RGB_CATENA = signet (default) |
// mutinynet. Per il modulo RGB sono tutt'e due `network: 'signet'` (stesso
// blocco 0); cambiano indexer, proxy, link e la CASA. Uno stash non deve mai
// vedere due catene: `nuovo` scrive catena.txt nella casa e `apri` si ferma
// se l'ambiente dice un'altra catena. File pronto: deploy/rgb/mutinynet-wsl.env.
const CATENE = {
  signet: { esplora: 'https://mempool.space/signet/tx/', casa: ['wdk-prova', 'utente'] },
  mutinynet: { esplora: 'https://mutinynet.com/tx/', casa: ['wdk-prova', 'mutinynet', 'utente'] }
}
const CATENA = process.env.RGB_CATENA || 'signet'
if (!CATENE[CATENA]) { console.error(`✗ RGB_CATENA=${CATENA}: conosco ${Object.keys(CATENE).join(', ')}`); process.exit(2) }
const CASA = process.env.PUNTI_CASA || path.join(os.homedir(), ...CATENE[CATENA].casa)
const SEME = path.join(CASA, 'seme.txt')
const DATI = path.join(CASA, 'wallet')
const MARCA = path.join(CASA, 'catena.txt')
const BACKUP = path.join(path.dirname(CASA), 'backup')
const INDEXER = process.env.RGB_INDEXER || 'tcp://127.0.0.1:50001'
const PROXY = process.env.RGB_PROXY || 'rpc://127.0.0.1:3000/json-rpc'
const FEE = Number(process.env.RGB_FEE || 2)
const SCADENZA = 24 * 3600
const ESPLORA = CATENE[CATENA].esplora

const mostra = (x) => JSON.stringify(x, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2)
const muori = (msg) => { console.error('✗', msg); process.exit(1) }

// La casa ricorda la catena: senza catena.txt (le case di prima del 9 ott)
// vale «signet», che e' quel che erano. nwc-wdk.mjs fa la stessa lettura.
function catenaDellaCasa (casa) {
  const f = path.join(casa, 'catena.txt')
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim() : 'signet'
}

function nuovo () {
  if (fs.existsSync(SEME)) muori(`${SEME} esiste gia': non si rigenera una frase sopra un wallet vivo`)
  fs.mkdirSync(DATI, { recursive: true, mode: 0o700 })
  const frase = bip39.generateMnemonic(128)
  fs.writeFileSync(SEME, frase + '\n', { mode: 0o600 })
  fs.writeFileSync(MARCA, CATENA + '\n')
  console.log(`✓ wallet utente creato in ${CASA} (catena ${CATENA}); la frase sta SOLO in seme.txt`)
}

async function apri () {
  if (!fs.existsSync(SEME)) muori('prima `node punti.mjs nuovo`')
  const nato = catenaDellaCasa(CASA)
  if (nato !== CATENA) muori(`il wallet in ${CASA} e' nato su ${nato}, ma RGB_CATENA dice ${CATENA}: casa o .env sbagliati`)
  const frase = fs.readFileSync(SEME, 'utf8').trim()
  const manager = new WalletManagerRgb(frase, {
    network: 'signet', indexerUrl: INDEXER, transportEndpoint: PROXY, dataDir: DATI
  })
  const account = await manager.getAccount()
  const chiudi = () => { try { account.dispose(); manager.dispose() } catch {} }
  return { account, chiudi }
}

const COMANDI = {
  nuovo,

  async indirizzo () {
    const { account, chiudi } = await apri()
    console.log(account.getAddress()); chiudi()
  },

  async saldo () {
    const { account, chiudi } = await apri()
    const reg = await account.registerWallet()        // sync col chain
    console.log('indirizzo:', reg.address)
    console.log('sats:', mostra(reg.btcBalance))
    console.log('UTXO:', mostra(account.listUnspents()))
    console.log('asset:', mostra(account.listAssets()))
    chiudi()
  },

  async utxo (quanti = '5') {
    const { account, chiudi } = await apri()
    const n = await account.createUtxos({ upTo: true, num: Number(quanti), feeRate: FEE })
    console.log(`✓ creati ${mostra(n)} UTXO colorabili (una transazione ${CATENA})`)
    chiudi()
  },

  async fattura (assetId = '-', quantita, modo = 'blind') {
    if (!quantita) muori('serve la quantita\': fattura <asset_id|-> <quantita> [witness]')
    const { account, chiudi } = await apri()
    const r = account.receiveAsset({
      assetId: assetId === '-' ? undefined : assetId,
      amount: Number(quantita),
      witness: modo === 'witness',
      minConfirmations: 1,
      durationSeconds: SCADENZA
    })
    console.log(r.invoice)
    console.error(`# ${modo}, recipient ${String(r.recipientId).slice(0, 20)}…`)
    chiudi()
  },

  async riscatta (assetId, quantita, fatturaStr) {
    if (!fatturaStr) muori('riscatta <asset_id> <quantita> <fattura>')
    const { account, chiudi } = await apri()
    const esito = await account.transfer({
      recipient: fatturaStr, token: assetId, amount: Number(quantita),
      minConfirmations: 1, feeRate: FEE
    })
    console.log(`✓ consignment depositato, txid ${esito.hash}\n  ${ESPLORA}${esito.hash}`)
    chiudi()
  },

  async aggiorna () {
    const { account, chiudi } = await apri()
    console.log(mostra(account.refreshWallet()))
    chiudi()
  },

  async trasferimenti (assetId) {
    const { account, chiudi } = await apri()
    console.log(mostra(account.listTransfers(assetId)))
    chiudi()
  },

  async backup () {
    const { account, chiudi } = await apri()
    fs.mkdirSync(BACKUP, { recursive: true, mode: 0o700 })
    const pwFile = path.join(CASA, 'password-backup.txt')
    if (!fs.existsSync(pwFile)) {
      fs.writeFileSync(pwFile, Buffer.from(os.hostname() + Date.now() + Math.random()).toString('base64url') + '\n', { mode: 0o600 })
    }
    const password = fs.readFileSync(pwFile, 'utf8').trim()
    const r = account.createBackup({ password, backupPath: BACKUP })
    console.log('✓', mostra(r), '\n  password in', pwFile)
    chiudi()
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
