# Ripristino da zero — Barattolo

Data: 20 ott 2026 · Versione: 1.0 · Scenario: Il VPS è perso, rebuild completo

Questo documento copre la procedura passo-passo per **ricostruire Barattolo da zero** su una macchina nuova Ubuntu 26.04 LTS, partendo da un backup decriptato e da GitHub.

**Tempo stimato:** 4-6 ore (a seconda di scarichi e approvazioni).  
**Prerequisiti:**

- Una macchina Ubuntu 26.04 LTS nuova (AWS, Hetzner, qualunque provider)
- Accesso root SSH alla macchina
- Un backup decriptato (da Telegram o dal PC di Andrea)
- Il dominio `barattolo.store` gestito (DNS A record punto a nuovo IP)
- Il token GitHub (o un token nuovo da generare)
- 30 GB di spazio su disco

---

## Fasi

### Fase 1: Setup della macchina

**Sul nuovo server (root):**

```bash
# 1) Update del sistema
apt update && apt upgrade -y

# 2) Timezone
timedatectl set-timezone UTC

# 3) Hostname
hostnamectl set-hostname barattolo

# 4) Dipendenze base
apt install -y \
  curl wget git htop screen \
  python3 python3-pip python3-venv \
  build-essential libssl-dev libffi-dev \
  sqlite3 age tor \
  caddy

# 5) Docker (per LNbits e coordinatore P2P)
apt install -y docker.io docker-compose
systemctl enable docker
usermod -aG docker root

# 6) Prova che tutto sia installato
python3 --version  # 3.11 o superiore
git --version
sqlite3 --version
age --version
caddy version
docker --version
```

### Fase 2: Preparazione del codice

```bash
# 1) Crea la cartella di lavoro
mkdir -p /srv/barattolo
cd /srv/barattolo

# 2) Clone di Barattolo
git clone https://github.com/alanbimbati/satmarket.git .
# Oppure se il repo è privato:
# git clone https://<UTENTE>:<TOKEN>@github.com/alanbimbati/satmarket.git .

# 3) Checkout all'ultima versione stabile (su main)
git fetch origin main
git checkout origin/main
# Verifica che il codice sia il giusto:
git log -1 --oneline

# 4) Crea la virtualenv e installa le dipendenze
python3 -m venv venv
source venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt

# 5) Verifica che il codice compili
python3 -m compileall -q server.py
echo "✅ Codice compilato"
```

### Fase 3: Posa del backup

**Prima, prepara il backup decriptato:**

Sul PC di Andrea (o dove hai decriptato il backup):

```bash
# Estrai il tar.gz decriptato
tar -tzf barattolo-20261020-2200.tar.gz | head -10
# Deve mostrare: satmarket.db, config.py, lnbits/, sistema/, buste/, etc

# Trasferisci il backup sul server
# (o copiacollalo se è via scp)
scp barattolo-20261020-2200.tar.gz root@<nuovo-ip>:/root/backup-ripristino.tar.gz
```

**Sul nuovo server:**

```bash
cd /srv/barattolo

# 1) Estrai il backup
tar -xzf /root/backup-ripristino.tar.gz -C /tmp

# 2) Copia il database
cp /tmp/satmarket.db ./satmarket.db

# 3) Copia il config (contiene i segreti)
cp /tmp/config.py ./config.py

# 4) Verifica che il database sia valido
sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"
# Deve rispondere con un numero (es: 150), non un errore

# 5) Copia le directory di dati
mkdir -p dati/
[ -d /tmp/buste ]     && cp -r /tmp/buste ./
[ -d /tmp/contenuti ] && cp -r /tmp/contenuti ./

# 6) Copia le foto (se il backup le contiene; solitamente no)
# mkdir -p foto/
# [ -d /tmp/foto ] && cp -r /tmp/foto ./

# 7) Permessi
chmod 600 satmarket.db config.py

# 8) Pulisci
rm -rf /tmp/satmarket.db /tmp/config.py /tmp/buste /tmp/contenuti /tmp/lnbits /tmp/sistema
```

### Fase 4: Setup del servizio Barattolo

```bash
cd /srv/barattolo

# 1) Copia le unit systemd (dal backup)
cp /tmp/sistema/barattolo*.service /etc/systemd/system/
cp /tmp/sistema/barattolo*.timer /etc/systemd/system/

# 2) Aggiorna i percorsi dentro le unit (controllia che siano corretti per /srv/barattolo)
cat /etc/systemd/system/barattolo.service
# Deve avere: WorkingDirectory=/srv/barattolo, ExecStart=/srv/barattolo/venv/bin/python3 ...

# 3) Reload systemd
systemctl daemon-reload

# 4) Crea l'utente barattolo (se non esiste)
id barattolo &>/dev/null || useradd -r -s /usr/sbin/nologin barattolo

# 5) Permessi: root possiede il codice, barattolo possiede i dati
chown -R root:root /srv/barattolo
chown -R barattolo:barattolo /srv/barattolo/dati /srv/barattolo/foto /srv/barattolo/buste /srv/barattolo/contenuti

# 6) Test del servizio
systemctl start barattolo
sleep 3
systemctl status barattolo
# Deve dire "active (running)"

# 7) Test dell'API
curl http://127.0.0.1:8080/api/salute
# Deve rispondere con JSON, status 200
```

### Fase 5: Setup Caddy (reverse proxy HTTPS)

```bash
# 1) Copia la configurazione dal backup
cp /tmp/sistema/Caddyfile /etc/caddy/Caddyfile

# 2) Edita il Caddyfile per puntare al nuovo dominio (se è cambiato)
nano /etc/caddy/Caddyfile
# Cambia "barattolo.store" se il dominio è diverso

# 3) Valida la configurazione
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

# 4) Ricarica Caddy
systemctl reload caddy

# 5) Test HTTPS (aspetta 10 secondi che Let's Encrypt generi il cert)
sleep 10
curl -I https://barattolo.store/
# Deve rispondere 200 su /, non 502
```

### Fase 6: Setup Tor (servizio nascosto .onion)

Se il backup contiene la chiave Tor (irrecuperabile se persa):

```bash
# 1) Copia la chiave del servizio nascosto dal backup
# (è la cartella tor-hidden-service dentro /tmp/sistema/)
cp -a /tmp/sistema/tor-hidden-service /var/lib/tor/hidden-barattolo

# 2) Permessi (Tor è rigido su questo)
chown -R debian-tor:debian-tor /var/lib/tor/hidden-barattolo
chmod 700 /var/lib/tor/hidden-barattolo
chmod 600 /var/lib/tor/hidden-barattolo/*

# 3) Aggiungi il servizio al torrc
cat >> /etc/tor/torrc <<EOF
# Barattolo hidden service
HiddenServiceDir /var/lib/tor/hidden-barattolo
HiddenServicePort 80 127.0.0.1:8080
HiddenServiceVersion 3
EOF

# 4) Valida il torrc
tor --verify-config

# 5) Riavvia Tor
systemctl restart tor

# 6) Leggi l'indirizzo .onion (deve essere lo stesso di prima)
cat /var/lib/tor/hidden-barattolo/hostname
# Deve finire con .onion
```

Se il backup NON contiene la chiave Tor (disastro): una nuova chiave verrà generata, ma l'indirizzo .onion cambierà (tutte le persone con link salvati dovranno aggiornare).

### Fase 7: LNbits (cassaforte del nodo)

Se il backup contiene la configurazione di LNbits:

```bash
# 1) Copia la directory dal backup
mkdir -p /opt/lnbits
cp -r /tmp/lnbits/* /opt/lnbits/
cp /tmp/lnbits/.env /opt/lnbits/.env

# 2) Avvia il container (dal compose)
cd /opt/lnbits
docker-compose up -d

# 3) Aspetta che sia pronto (30 secondi)
sleep 30
curl http://127.0.0.1:5000/

# 4) Verifica che il database sia integro
docker-compose exec lnbits sqlite3 data/database.sqlite3 "SELECT COUNT(*) FROM accounts LIMIT 1"
```

Se il backup NON contiene LNbits (disastro): bisognerà riconfigurare il node, il che significa lost satoshis. Scenario da evitare a tutti i costi.

### Fase 8: Il ponte verso il nodo (Wireguard o Tor)

```bash
# 1) Copia la configurazione dal backup
# Se usa Wireguard (v3, il piano nuovo):
cp /tmp/sistema/wg0.conf /etc/wireguard/wg0.conf

# Se usa Tor (il piano vecchio):
cp /tmp/sistema/lnd-ponte-tor.service /etc/systemd/system/

# 2) Copia la unit del ponte
cp /tmp/sistema/lnd-ponte.service /etc/systemd/system/

# 3) Reload systemd
systemctl daemon-reload

# 4) Avvia il ponte
systemctl start lnd-ponte
systemctl status lnd-ponte
# Deve dire "active (running)" e "🌉 Guardiano del ponte…" nel log
```

### Fase 9: Configurazione del deploy automatico

```bash
# 1) Copia i file di deploy
cp /srv/barattolo/deploy/barattolo-deploy.service /etc/systemd/system/
cp /srv/barattolo/deploy/barattolo-deploy.timer /etc/systemd/system/
cp /srv/barattolo/deploy/barattolo-backup.service /etc/systemd/system/
cp /srv/barattolo/deploy/barattolo-backup.timer /etc/systemd/system/

# 2) Reload systemd
systemctl daemon-reload

# 3) Configura il backup esterno (se serve)
# (vedi la sezione BACKUP QUI SOTTO)

# 4) Abilita i timer
systemctl enable barattolo-deploy.timer barattolo-backup.timer
systemctl start barattolo-deploy.timer barattolo-backup.timer

# 5) Controlla che il timer sia attivo
systemctl status barattolo-deploy.timer
systemctl list-timers barattolo-deploy.timer
```

### Fase 10: Verifica finale

```bash
# 1) Controlla che il servizio sia attivo
systemctl status barattolo
# Deve dire "active (running)"

# 2) Controlla che HTTPS funzioni (pubblico)
curl -I https://barattolo.store/
# 200 OK

# 3) Controlla che /api/salute risponda
curl https://barattolo.store/api/salute
# Risponde {"status": "ok"} o simile

# 4) Controlla che il bot Telegram funzioni
# (apri il bot e prova /start)
# Deve dire "🫙 Barattolo" con il nome del proprietario

# 5) Controlla i log
journalctl -u barattolo -n 20 --no-pager
# Non deve avere Traceback o errori

# 6) Controlla il deploy timer (entro un minuto dovrebbe girare)
journalctl -u barattolo-deploy --since "10 minutes ago" --no-pager | grep -E "🚀|⛔|✅"

# 7) Test finale: fai un preferito, leggi un annuncio, crea un ordine
# (da app.barattolo.store o bot Telegram)
```

---

## BACKUP: Setup del backup esterno

Il backup giornaliero cifrato deve partire ogni giorno alle 22:00 UTC e andare su Telegram.

```bash
# 1) Copia il file di backup
cp /srv/barattolo/deploy/backup-fuori.sh /etc/barattolo-backup/

# 2) Crea il file di configurazione (contiene segreti, MAI nel repo)
nano /etc/barattolo-backup.env
```

**Dentro `/etc/barattolo-backup.env` (chmod 600):**

```bash
BOT_TOKEN_BACKUP=<token di un bot NUOVO, non quello di Barattolo>
CHAT_ID_BACKUP=<id del canale Telegram privato per i backup>
AGE_PUBBLICA=age1<la chiave PUBBLICA che cifra i backup>
```

```bash
# 3) Permessi
chmod 600 /etc/barattolo-backup.env

# 4) Test manuale
bash /etc/barattolo-backup.env /srv/barattolo/deploy/backup-fuori.sh
# Deve dire "📦 backup inviato:" se succede, oppure un warning se il canale non risponde
# (il backup resta comunque in /srv/barattolo/backup/fuori/)

# 5) Il timer è già partito (Fase 9), quindi il primo backup partirà a mezzanotte UTC
journalctl -u barattolo-backup.timer --since "today"
```

---

## E se qualcosa va storto?

### Il codice non compila

```bash
python3 -m compileall -q server.py
# Se fallisce: c'è un errore di sintassi nel codice

# Soluzioni:
# 1) Checkout a una versione più vecchia (tag stabile)
git tag  # vedi le versioni
git checkout v1.5.0  # o simile, una versione che sai che funziona
git reset --hard v1.5.0

# 2) O espandi l'errore di compila:
python3 -m compileall server.py
# Leggi il Traceback, aggiusta il bug, o chiedi a Claude
```

### /api/salute non risponde

```bash
# 1) Controlla il log del servizio
journalctl -u barattolo -n 50 --no-pager | grep -iE "error|traceback|exception"

# 2) Controlla che il database sia valido
sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"
# Se fallisce: il database è corrotto

# 3) Controlla i permessi
ls -ld /srv/barattolo/satmarket.db
# Deve essere leggibile e scrivibile da barattolo

# 4) Controlla la porta 8080
netstat -tlnp | grep 8080
# Deve mostrare il processo di Python in ascolto

# 5) Se la porta è occupata da qualcos'altro:
kill -9 $(lsof -ti :8080)  # uccidi chiunque sia sulla 8080
systemctl restart barattolo
```

### Caddy non serve HTTPS

```bash
# 1) Valida la configurazione
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

# 2) Controlla il log di Caddy
journalctl -u caddy -n 50 --no-pager

# 3) Controlla che il dominio punti al nuovo IP
nslookup barattolo.store
# Deve rispondere con l'IP del nuovo server

# 4) Se il certificato di Let's Encrypt non è stato generato
# (può prendere fino a 30 secondi): aspetta e riprova
sleep 30
curl -I https://barattolo.store/
```

### Il bot Telegram non risponde

```bash
# 1) Controlla che il webhook sia registrato
journalctl -u barattolo -n 50 --no-pager | grep -i "webhook\|🔔"

# 2) Controlla che il config.py abbia il token corretto
grep BOT_TOKEN /srv/barattolo/config.py

# 3) Se il token è sbagliato: aggiornalo a mano
nano /srv/barattolo/config.py
# Cambia BOT_TOKEN
systemctl restart barattolo

# 4) Se il webhook fallisce ancora: il VPS potrebbe non essere raggiungibile da Telegram
# Controlla che il firewall non blocchi la porta 443 (HTTPS)
```

### LNbits non parte

```bash
# 1) Controlla che Docker stia girando
docker ps
systemctl status docker

# 2) Controlla il log del container
docker-compose -f /opt/lnbits/docker-compose.yml logs --tail 50

# 3) Se il container è morto: ricomincia
docker-compose -f /opt/lnbits/docker-compose.yml restart

# 4) Se il database è corrotto:
# Il backup decriptato contiene database.sqlite3 atomico
# Prova a ripristinarlo con la procedura di Scenario 3
```

---

## Checklist finale

Prima di considerare il ripristino completo:

- [ ] `systemctl status barattolo` dice "active (running)"
- [ ] `curl https://barattolo.store/` risponde 200
- [ ] Il bot Telegram risponde a /start
- [ ] La cassaforte LNbits è raggiungibile (se in uso)
- [ ] Il servizio .onion è raggiungibile via Tor Browser
- [ ] Il timer di deploy è attivo e ha girato almeno una volta
- [ ] Il database ha i dati corretti (numero di utenti, ordini, etc)
- [ ] Il journal non ha errori o avvisi in 5 minuti

---

## Tempi di downtime

| Procedura | Downtime | Note |
|-----------|----------|------|
| Rollback (Scenario 1) | ~90 sec | Automatico, il bot lo avvisa |
| Rollback manuale (Scenario 2) | ~90 sec | Manuale, il bot lo avvisa |
| Ripristino da backup (Scenario 3) | ~5 min | Dipende da quant'è grande il backup |
| Rebuild da zero (Scenario 4) | **4-6 ore** | Dipende da scarichi, Let's Encrypt, etc |

---

**Data creazione:** 20 ott 2026  
**Data ultimo aggiornamento:** 20 ott 2026  
**Prossima revisione:** 20 gen 2027
