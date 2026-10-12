#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0012 del fork — LA DISPUTA CHE IL COORDINATORE APRE DA SOLO.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/v0.19.0,
SOPRA la 0011 (pretende `src/barattolo_tempo.rs`, e si ferma se manca):
    python3 /percorso/patch-0012-disputa-automatica.py --secco  # prova e basta
    python3 /percorso/patch-0012-disputa-automatica.py          # applica
Ogni ancora deve comparire UNA volta: se anche una manca o e' doppia si
ferma SENZA SCRIVERE NIENTE. Poi si committa e si esporta con
`git format-patch -1 --start-number 12`.

IL DISEGNO (12 ott 2026, cantiere tempo-di-chi-pubblica, richiesta di
Andrea dalla nota del cantiere dispute-nel-cruscotto). Il guardiano della
garanzia (`enforce_escrow_deadline_pass`, upstream 0.19.0) gira ogni
cinque minuti: quando l'HTLC della garanzia e' a `escrow_deadline_margin_blocks`
dalla sua scadenza, uno scambio `active` lo ANNULLA (e la 0007 lo dice gia':
`expired` / `escrow-deadline`), e uno scambio `fiat-sent` lo manda IN
DISPUTA da solo — chi compra ha detto di aver pagato, e solo una persona
puo' decidere finche' la garanzia esiste. Quella disputa la 0007 non la
raccontava a nessuno: il server di Barattolo non ne sapeva niente, i
moderatori non ricevevano l'avviso proprio nel caso che ha meno tempo, e
il cruscotto delle dispute non la contava.

UNA RIGA, nel ramo `Status::FiatSent`, DOPO che lo stato `dispute` e'
stato scritto nel database: `dispute-opened` con attore `mostro` (non l'ha
aperta nessuna delle due parti) e dettaglio `escrow-deadline` (la stessa
parola dell'annullo gemello). Li' e non prima: finche' la scrittura non e'
riuscita il giro «riprova al prossimo tick», e l'evento partirebbe piu'
volte; dopo, l'ordine non e' piu' `fiat-sent` e il guardiano non ci torna.
`emit_detail` non blocca e non fallisce (0007): se il server e' giu' la
disputa nasce lo stesso, esattamente come upstream.

Piu' la riga del vocabolario dei dettagli in `barattolo_eventi.rs` e una
prova PURA del corpo che parte (`dispute-opened` / `mostro` /
`escrow-deadline`, senza importi).

IL SERVER DI BARATTOLO: `dispute-opened` lo conosce dalla 0007, e l'attore
`mostro` lo accettava gia' (riga in `p2p_dispute` con `aperta_da` vuoto,
avviso ai moderatori). Il commit che porta questa patch gli da' le DUE
frasi giuste per questo caso — alle parti «lo scambio e' passato ai
moderatori» invece di «<l'altro> ha aperto una disputa», ai moderatori
«l'ha aperta il coordinatore da solo… va decisa adesso». PRIMA IL SERVER,
POI IL NODO, come per la 0011: col server di ieri le due parti
leggerebbero che la disputa l'ha aperta l'altro.

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo): la firma di `emit_detail` e
il ramo sono stati LETTI sul clone del tag v0.19.0 con le dieci patch
applicate, e il patcher e' stato fatto girare li' a secco e per davvero —
il primo `cargo build` e il primo `cargo test` sono quelli sul nodo.
"""
import io
import os
import sys

SECCO = "--secco" in sys.argv


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


AZIONE, ATTORE, DETTAGLIO = "dispute-opened", "mostro", "escrow-deadline"

# (file, ancora, testo nuovo, "dopo" | "prima")
AGGANCI = [
    # ── l'evento, nel ramo fiat-sent del guardiano ───────────────────
    ("src/scheduler.rs",
     "                info!(\n"
     "                    \"escrow_deadline: order {} moved to dispute — fiat claimed sent and the escrow is near its CLTV horizon\",\n"
     "                    order.id\n"
     "                );\n",
     "                // Barattolo fork (patch 0012): tell the marketplace server.\n"
     "                // Patch 0007 reports the disputes the USERS open; this one is\n"
     "                // opened by the daemon itself, so the actor is \"mostro\" and\n"
     "                // the detail names the guardian. Sent only here, once the\n"
     "                // status flip is persisted: the order is no longer\n"
     "                // `fiat-sent`, so no later tick comes back to this branch.\n"
     "                crate::barattolo_eventi::emit_detail(\n"
     "                    \"%s\",\n"
     "                    &order,\n"
     "                    \"%s\",\n"
     "                    \"%s\",\n"
     "                );\n" % (AZIONE, ATTORE, DETTAGLIO), "dopo"),

    # ── il vocabolario dei dettagli ──────────────────────────────────
    ("src/barattolo_eventi.rs",
     "//   released                admin (a moderator settled a dispute)\n",
     "//   dispute-opened          escrow-deadline (patch 0012: the escrow guardian of\n"
     "//                           this daemon opened it, actor `mostro`; a dispute a\n"
     "//                           user opens carries no detail)\n", "dopo"),

    # ── la prova pura del corpo che parte ────────────────────────────
    ("src/barattolo_eventi.rs",
     "    #[test]\n"
     "    fn lnd_failure_reasons_by_code() {\n",
     "    #[test]\n"
     "    fn a_dispute_the_daemon_opens_is_mostros_and_says_why() {\n"
     "        // patch 0012: the escrow guardian files it, no user did\n"
     "        let event =\n"
     "            event_of(\"%s\", &order(), \"%s\", Some(\"%s\")).unwrap();\n"
     "        assert_eq!(event.actor, \"mostro\");\n"
     "        assert_eq!(event.detail.as_deref(), Some(\"escrow-deadline\"));\n"
     "        let body = payload(&event);\n"
     "        assert_eq!(body[\"action\"], \"dispute-opened\");\n"
     "        assert_eq!(body[\"detail\"], \"escrow-deadline\");\n"
     "        // a dispute never carries amounts\n"
     "        assert!(body.get(\"sats\").is_none());\n"
     "    }\n"
     "\n" % (AZIONE, ATTORE, DETTAGLIO), "prima"),
]

if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
if not os.path.isfile("src/barattolo_eventi.rs"):
    sys.exit("FERMO: manca src/barattolo_eventi.rs — la 0012 sta SOPRA la 0007, che qui non c'e'")
if not os.path.isfile("src/barattolo_tempo.rs"):
    sys.exit("FERMO: manca src/barattolo_tempo.rs — la 0012 sta SOPRA la 0011, che qui non c'e'")

# LE PAROLE AL SERVER: l'azione deve stare nell'elenco chiuso della 0007 (o
# `event_of` la butta via con una riga nel log e basta), e il dettaglio deve
# essere una parola a macchina, o `clean_detail` la taglierebbe in silenzio.
eventi = leggi("src/barattolo_eventi.rs")
elenco = eventi[eventi.find("pub const ACTIONS"):eventi.find("];", eventi.find("pub const ACTIONS"))]
if '"%s"' % AZIONE not in elenco:
    sys.exit("FERMO: «%s» non e' fra le ACTIONS della 0007 — niente scritto" % AZIONE)
if not all(c.isalnum() or c in "-_" for c in DETTAGLIO) or len(DETTAGLIO) > 40:
    sys.exit("FERMO: «%s» non e' una parola a macchina — niente scritto" % DETTAGLIO)

testi = {}
for percorso, ancora, nuovo, dove in AGGANCI:
    t = testi.get(percorso)
    if t is None:
        if not os.path.isfile(percorso):
            sys.exit("FERMO: manca %s — niente scritto" % percorso)
        t = leggi(percorso)
    if "\r\n" in t:
        ancora = ancora.replace("\n", "\r\n")
        nuovo = nuovo.replace("\n", "\r\n")
    if nuovo in t:
        sys.exit("FERMO: %s porta gia' questo aggancio — la patch e' gia' applicata?" % percorso)
    n = t.count(ancora)
    if n != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto:\n%s"
                 % (percorso, n, ancora))
    testi[percorso] = t.replace(ancora, ancora + nuovo if dove == "dopo" else nuovo + ancora)


def taglio_dei_test(t):
    for capo in ("#[cfg(test)]\nmod ", "#[cfg(test)]\r\nmod "):
        if capo in t:
            return t.find(capo)
    return len(t)


# L'EVENTO STA NEL CODICE VERO, la prova nei test: al contrario l'uno
# compilerebbe e in servizio non farebbe niente, l'altra finirebbe nel
# binario.
guardiano = testi["src/scheduler.rs"]
chiamata = '"%s",\n                    &order,\n                    "%s",' % (AZIONE, ATTORE)
if "\r\n" in guardiano:
    chiamata = chiamata.replace("\n", "\r\n")
if not 0 <= guardiano.find(chiamata) < taglio_dei_test(guardiano):
    sys.exit("FERMO: in src/scheduler.rs l'evento non e' nel codice vero — niente scritto")
modulo = testi["src/barattolo_eventi.rs"]
if not modulo.find("fn a_dispute_the_daemon_opens_is_mostros_and_says_why") > taglio_dei_test(modulo):
    sys.exit("FERMO: in src/barattolo_eventi.rs la prova e' finita FUORI dai test — niente scritto")
# E UNA VOLTA SOLA: il guardiano ha un ramo solo che apre la disputa.
if guardiano.count(chiamata) != 1:
    sys.exit("FERMO: in src/scheduler.rs l'evento compare piu' di una volta — niente scritto")

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore uniche. Niente scritto."
          % (len(AGGANCI), len(testi)))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
print("FATTO: %d agganci in %d file" % (len(AGGANCI), len(testi)))
print("Adesso: i test, il commit, git format-patch -1 --start-number 12")
