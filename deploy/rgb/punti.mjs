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

const CASA = process.env.PUNTI_CASA || path.join(os.homedir(), 'wdk-prova', 'utente')
const SEME = path.join(CASA, 'seme.txt')
const DATI = path.join(CASA, 'wallet')
const BACKUP = path.join(path.dirname(CASA), 'backup')
const INDEXER = process.env.RGB_INDEXER || 'tcp://127.0.0.1:50001'
const PROXY = process.env.RGB_PROXY || 'rpc://127.0.0.1:3000/json-rpc'
const FEE = Number(process.env.RGB_FEE || 2)
const SCADENZA = 24 * 3600
const ESPLORA = 'https://mempool.space/signet/tx/'

const mostra = (x) => JSON.stringify(x, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2)
const muori = (msg) => { console.error('✗', msg); process.exit(1) }

function nuovo () {
  if (fs.existsSync(SEME)) muori(`${SEME} esiste gia': non si rigenera una frase sopra un wallet vivo`)
  fs.mkdirSync(DATI, { recursive: true, mode: 0o700 })
  const frase = bip39.generateMnemonic(128)
  fs.writeFileSync(SEME, frase + '\n', { mode: 0o600 })
  console.log(`✓ wallet utente creato in ${CASA}; la frase sta SOLO in seme.txt`)
}

async function apri () {
  if (!fs.existsSync(SEME)) muori('prima `node punti.mjs nuovo`')
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
    console.log(`✓ creati ${mostra(n)} UTXO colorabili (una transazione signet)`)
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
