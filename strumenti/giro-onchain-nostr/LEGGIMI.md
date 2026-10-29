# Il giro on-chain dal vivo con due account Nostr (29 ott 2026)

Due browser veri (Playwright) contro il server VERO in locale: chi compra
e chi vende entrano con una chiave Nostr (non admin), l'on-chain si
accende da solo, chi vende sceglie dove ricevere, chi compra paga da un
wallet esterno; poi il giro buono (conferma, due firme, sats a chi vende)
e quello con la disputa (un admin decide, Barattolo firma, chi vince
co-firma). Le firme le mette il codice vero della Mini App.

Solo la rete Bitcoin e' finta (in memoria, dentro `giro_server.py`):
da una macchina che raggiunge mempool.space si toglie quella sostituzione
e si paga davvero su signet dalla faucet.

```
cd <cartella del repo>
python strumenti/giro-onchain-nostr/giro_server.py "$PWD" 8099 &
NODE_PATH=$(npm root -g) node strumenti/giro-onchain-nostr/giro.js http://127.0.0.1:8099 /tmp/giro
```

Mai relay veri: il server va al relay morto e il browser chiude ogni
websocket. Non e' un collaudo della CI (vuole Playwright e un server in
piedi): si lancia a mano.
