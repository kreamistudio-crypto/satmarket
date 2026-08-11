# -*- coding: utf-8 -*-
"""
SATMARKET — CONFIGURAZIONE D'ESEMPIO

QUESTO FILE NON CONTIENE SEGRETI: e' il modello da copiare.

PRIMA VOLTA:
  1. Copia questo file e rinominalo in  config.py
  2. Compila i campi qui sotto con le TUE chiavi
  3. config.py NON verra' mai caricato su GitHub (vedi .gitignore):
     le chiavi restano solo sul tuo computer/server.
"""

# --- Telegram -------------------------------------------------------
BOT_TOKEN = "INCOLLA_QUI_IL_TOKEN_DEL_BOT"      # da @BotFather
ADMIN_IDS = [123456789]      # il TUO user id Telegram (da @userinfobot):
                             # decide le dispute e riceve gli avvisi.
                             # Piu' moderatori? Elenca gli id separati da
                             # virgola: [123456789, 987654321]. Sono tutti
                             # pari grado (nessun super-admin) e la lista
                             # si cambia SOLO qui, sul server: nessun
                             # comando dell'app o del bot la tocca.

# Chi ha FONDATO Barattolo (id Telegram, come sopra). Portano il
# titolo «🏛 Fondatore» sotto il nome, messo da solo alla prima
# apertura. Non e' un traguardo che si raggiunge e nessun altro
# potra' mai ottenerlo: e' un fatto, e per questo sta qui e non fra i
# criteri. Vuoto = nessuno, che e' il default del codice.
FONDATORI = []               # es. [123456789, 987654321]

# --- Bot Telegram in ricezione (doppia cittadinanza) -----------------
# Il segreto che Telegram ci rimanda in ogni update (header
# X-Telegram-Bot-Api-Secret-Token), cosi' il webhook sa che a suonare
# e' davvero Telegram. Genera una stringa casuale (1-256 caratteri,
# solo A-Za-z0-9_-) e incollala SOLO nel config.py del server.
# Finche' resta il segnaposto, il bot resta solo-invio come prima.
TELEGRAM_WEBHOOK_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_CASUALE"

# --- Anthropic (ricerca AI in linguaggio naturale) -------------------
ANTHROPIC_API_KEY = "INCOLLA_QUI_LA_API_KEY"
MODELLO_RICERCA = "claude-haiku-4-5"

# --- LNbits: la "cassaforte" escrow ----------------------------------
# Usa un wallet DEDICATO a SatMarket, non quello personale!
LNBITS_URL = "https://TUA-ISTANZA-LNBITS.com"
LNBITS_INVOICE_KEY = "INCOLLA_QUI_LA_INVOICE_KEY"   # per incassare
LNBITS_ADMIN_KEY = "INCOLLA_QUI_LA_ADMIN_KEY"       # per pagare (SEGRETA!)

# --- Regole del mercatino --------------------------------------------
COMMISSIONE_PERCENTO = 0     # trattenuta a vendita conclusa (0 = sospesa: cifra da decidere)
PROTEZIONE_PERCENTO = 0      # protezione acquisti a carico del COMPRATORE
                             # (modello Vinted): % sul solo prezzo articolo,
                             # si aggiunge al conto e resta alla piattaforma.
                             # 0 = spenta
GIORNI_DATA_ANNUNCIO = 60    # «pubblicato N giorni fa» nel dettaglio:
                             # oltre questi giorni la riga non si mostra
AUTO_SBLOCCO_ATTIVO = False  # IL DISARMO (ago 2026): False = i sats non
                             # si muovono MAI senza un gesto umano. Gatea
                             # i soli rami FISICI dell'orologio; le due
                             # finestre del DIGITALE qui sotto restano
                             # armate comunque. True = si torna allo
                             # sblocco d'ufficio di ieri, e allora vanno
                             # rimessi i testi (l'elenco dei posti e'
                             # nella voce sua in CLAUDE.md)
ORE_CONFERMA = 72            # finestra dell'acquirente dopo la consegna:
                             # a leva spenta e' quando parte il PRIMO
                             # promemoria, non piu' quando partono i sats
GIORNI_AUTO_SBLOCCO = 10     # silenzio dopo la spedizione: idem, a leva
                             # spenta e' il primo promemoria
PROMEMORIA_CONFERMA_GIORNI = 3  # ogni quanto si ribussa al compratore
                             # dopo il primo squillo (0 = promemoria
                             # spenti: i sats restano fermi in silenzio)
PROMEMORIA_CONFERMA_MAX = 3  # promemoria ignorati prima che il caso
                             # venga segnalato ai moderatori, poi silenzio
                             # (la cadenza e il tetto qui sopra valgono
                             # anche per i due promemoria al VENDITORE)
PROMEMORIA_SPEDIZIONE_GIORNI = 5  # ordine 'locked' col pacco mai partito:
                             # dopo quanti giorni dal pagamento parte il
                             # primo squillo al venditore (0 = spento)
PROMEMORIA_DIGITALE_ORE = 48 # idem per il codice online mai consegnato:
                             # ore, non giorni — un codice si manda subito
SOLLECITO_INCASSO_GIORNI = 7 # ordine «Da incassare» fermo: ogni tot
                             # giorni un promemoria al venditore
                             # (0 = solleciti spenti)
SOLLECITO_INCASSO_MAX = 4    # solleciti ignorati prima che il caso
                             # venga segnalato ai moderatori
TERMOMETRO_SOTTOCATEGORIE = True  # il lunedi' UNA notifica agli admin
                                  # con gli annunci senza sottocategoria
                                  # (False = mai; tace comunque sotto il
                                  # minimo e a vetrina piena)
TERMOMETRO_SOTTOCATEGORIE_MINIMO = 5  # sotto questi vuoti non si disturba
TETTO_SATS_ANNUNCIO = 0      # prezzo massimo per annuncio: 0 = nessun
                             # limite (default). Mettici es. 100_000 per
                             # accendere il tetto; per gli annunci in EUR
                             # vale l'equivalente al cambio corrente
MAX_QUANTITA_ANNUNCIO = 999999  # pezzi massimi per annuncio (quantita'
                             # in stock). Alto apposta: quanti pezzi ha
                             # in magazzino lo sa il venditore, non noi.
                             # E' un guardrail contro il numero incollato
                             # per sbaglio, non un giudizio sul negozio
MAX_RIGHE_SET = 8            # annunci DIVERSI massimi in un set
                             # («Riempi il barattolo»): un pacco vero,
                             # non un camion
MAX_PREFERITI = 10           # quanti annunci ATTIVI stanno «nel tuo
                             # barattolo». Piccolo apposta: e' una
                             # selezione, non una lista dei desideri
                             # infinita. Contano solo gli attivi —
                             # comprare qualcosa che c'e' dentro
                             # libera spazio da solo

# --- Consegna digitale (buoni regalo, codici, licenze) ---------------
# Il codice passa DENTRO Barattolo: il venditore lo consegna in un
# campo dedicato dell'ordine, il compratore lo rivela con un tocco
# che fa da ricevuta di lettura. Finestre piu' corte del fisico:
# un codice si prova subito.
ORE_CONFERMA_DIGITALE = 24   # dopo la rivelazione: poi sblocco automatico
ORE_SILENZIO_DIGITALE = 48   # consegnato ma mai rivelato: poi sblocco
# Cifratura a riposo dei codici nel database: una stringa segreta
# qualsiasi (generane una casuale e incollala SOLO nel config.py del
# server). Vuota = i codici restano in chiaro nel DB: tutto funziona
# uguale, protegge meno un backup rubato — e il server lo dice con una
# riga all'avvio, cosi' non e' un silenzio.
# DUE COSE DA SAPERE PRIMA DI METTERLA: se la perdi, i contenuti gia'
# cifrati non si leggono piu' (nessuno puo' recuperarli, nemmeno noi);
# e accenderla non ricifra il passato — le righe gia' scritte in
# chiaro restano in chiaro, e vanno bene cosi' finche' esistono.
CHIAVE_CONTENUTI_DIGITALI = ""
# Leve anti-frode, SPENTE di serie (0 = nessun limite):
TETTO_DIGITALE_NUOVI = 0     # es. 50_000: un compratore senza acquisti
                             # conclusi non compra digitale sopra questa
                             # cifra (sats, sul solo articolo)
DIGITALE_MIN_VENDITE = 0     # es. 1: per pubblicare annunci digitali
                             # servono almeno N vendite concluse

# --- Offerte (contrattazione sul prezzo) -----------------------------
# Il compratore propone una cifra, il venditore accetta, rifiuta o fa
# UNA controproposta. Accettare = diritto di comprare a quel prezzo
# entro la scadenza; l'annuncio resta in vetrina e vince chi paga.
OFFERTA_MINIMA_PERCENTO = 50 # sotto questa % del listino l'offerta
                             # non parte proprio (anti-offerte-insulto)
ORE_RISPOSTA_OFFERTA = 48    # senza risposta l'offerta scade da sola
ORE_PAGAMENTO_OFFERTA = 24   # tempo per pagare dopo l'accettazione
MAX_OFFERTE_ANNUNCIO = 3     # tentativi totali per compratore per
                             # annuncio (una offerta attiva alla volta)

# --- Negozio in ferie ------------------------------------------------
# Il venditore che parte chiude la bottega con la data di rientro. Gli
# annunci RESTANO in vetrina, col prezzo in grigio e la data scritta
# sopra: si guardano, non si comprano — niente acquisti, offerte,
# carrello, lampo ne' aste nuove. Non si chiude con affari da spedire,
# aste vive, accordi da pagare o pagamenti in corso.
# Il rientro e' AUTOMATICO alla data: il controllo e' in lettura, quindi
# il negozio riapre da solo anche se il server e' stato spento.
FERIE_ATTIVE = True          # interruttore generale (False = spento)
FERIE_MAX_GIORNI = 90        # quanto in la' puo' stare la data di rientro
FERIE_PREAVVISO_ORE = 24     # «domani riapri» (0 = nessun promemoria)

# --- La ronda del libro mastro ---------------------------------------
# Una volta al giorno l'orologio ripassa gli INVARIANTI del database
# (l'aritmetica degli ordini, la cassa delle aste chiuse, la forma di
# ordine_righe...). Se torna tutto TACE — nemmeno una riga nel journal;
# se qualcosa non torna manda il 🧊 ai moderatori con la query che ha
# fallito e gli id. LEGGE E BASTA: non corregge mai niente.
# Gli stessi controlli si lanciano a mano con query_libro_mastro.sql.
CONTROLLO_LIBRO_MASTRO = True   # False = ronda spenta

# --- Sconto carrello (chi prende piu' cose paga meno) ----------------
# Il venditore premia chi compra piu' articoli in un ordine solo: UNA
# regola per tutto il suo negozio — «da N articoli, −X%» — senza
# scaglioni. Vale SOLO sul prezzo degli articoli, MAI sulla spedizione.
# Non vale su un annuncio comprato da solo, per quante copie se ne
# prendano: lo sconto e' del carrello.
# IL CRITERIO della soglia lo sceglie il venditore: a PEZZI («da 3
# articoli») o a VALORE degli articoli («da 100.000 sats nel
# carrello»), che e' il modo di dare lo sconto da due pezzi su un
# computer e da venti su una scatola di cianfrusaglie, con una regola
# sola. E la VALUTA della soglia a valore la sceglie sempre lui, in
# EURO o in SATS (ago 2026): in euro non deriva col cambio — chi scrive
# 100.000 sats pensando «una cinquantina di euro» si ritrova una
# promessa del doppio senza aver toccato niente — mentre in sats non ha
# bisogno del cambio, e scatta anche quando il cambio non risponde. Il
# cassetto lo dice, e sceglie il venditore. L'incasso resta sempre in
# sats.
# ATTENZIONE se questo file lo copi su un config gia' esistente: le
# leve si chiamano *_EUR e *_SATS apposta, cosi' una riga vecchia dal
# nome nudo resta INERTE invece di essere letta nell'unita' sbagliata
# (che sarebbe una promessa spenta in silenzio).
# Si cumula con la lampo e con le offerte accettate: e' una promessa di
# negozio, e un pezzo che non la mantenesse non avrebbe un posto onesto
# dove dirlo. Il tetto qui sotto e' il guardrail della cascata — e
# attenzione, a criterio valore la soglia guarda il carrello DOPO
# lampo e accordo: una lampo generosa puo' farlo scendere sotto soglia.
SCONTO_PACCO_ATTIVO = True      # interruttore generale (False = spento)
SCONTO_PACCO_CRITERI = ("pezzi", "valore")   # togliere un criterio da
                                # qui lo spegne per chi l'aveva scelto
SCONTO_PACCO_SOGLIE = (2, 3, 4, 5)      # le soglie proposte al venditore
# LA VALUTA DELLA SOGLIA A VALORE LA SCEGLIE IL VENDITORE (ago 2026,
# chiesto dalla comunita'). Vale per TUTTE E DUE le promesse, e ognuna
# ha la sua: sono indipendenti. Togliere una valuta da qui la spegne per
# chi l'aveva scelta — freno d'emergenza, non una taratura.
VALUTE_SOGLIA = ("eur", "sats")
SCONTO_PACCO_VALORI_EUR = (10, 25, 50, 100)  # a valore, in euro: basse
                                # apposta, che il carrello di un
                                # mercatino dell'usato e' piccolo
SCONTO_PACCO_VALORI_SATS = (10_000, 25_000, 50_000, 100_000)  # le
                                # gemelle in sats: numeri TONDI, non la
                                # conversione delle sorelle in euro
SCONTO_PACCO_SCONTI = (5, 10, 15, 20)   # le percentuali proposte
SCONTO_PACCO_MIN_SOGLIA = 2     # sotto non e' uno sconto carrello: e'
                                # un ribasso di listino, e quello si fa
                                # sul prezzo
SCONTO_PACCO_MIN_VALORE_EUR = 1  # la gemella a valore: una cintura
                                # contro lo zero travestito, non un
                                # giudizio su quanto debba valere un
                                # carrello
SCONTO_PACCO_MIN_VALORE_SATS = 1  # idem, in sats
SCONTO_PACCO_MAX_PERCENTO = 30  # sconto massimo consentito

# --- Spedizione gratis sopra soglia ----------------------------------
# La seconda promessa di negozio: «da N di articoli la spedizione la
# offro io». Anche qui la VALUTA la sceglie il venditore, e ne ha una
# SUA: le due promesse restano indipendenti, e un venditore puo'
# dichiarare lo sconto in euro e la spedizione gratis in sats.
# A DIFFERENZA DELLO SCONTO vale anche su un oggetto solo: azzerare una
# tariffa scrive spedizione_sats=0, cioe' lo stato che gli annunci con
# spedizione gratuita dichiarata hanno da sempre — mentre uno sconto di
# testata romperebbe il conto dell'unitario di un ordine a un annuncio
# solo. Il venditore incassa meno, che e' cosa vuol dire offrirla.
# Le due promesse guardano lo STESSO numero, il prezzo degli articoli
# prima dello sconto carrello: sono indipendenti, e nessuna delle due
# puo' spegnere l'altra. Attenzione, come per lo sconto: la soglia
# guarda il carrello DOPO lampo e accordi.
SPED_GRATIS_ATTIVO = True       # interruttore generale (False = spento)
SPED_GRATIS_SOGLIE_EUR = (10, 25, 50, 100)  # le soglie proposte al
                                # venditore, in euro
SPED_GRATIS_SOGLIE_SATS = (10_000, 25_000, 50_000, 100_000)  # e in sats,
                                # per chi dichiara la soglia cosi'
SPED_GRATIS_MIN_EUR = 1         # una cintura contro lo zero travestito:
                                # sotto, la spedizione sarebbe gratis
                                # sempre — e quella si dichiara nel
                                # prezzo dell'annuncio (costo 0)
SPED_GRATIS_MIN_SATS = 1        # idem, in sats

# --- Suggerimenti dal bot --------------------------------------------
# I consigli che il bot manda al venditore: cosa manca a un annuncio, e
# le leve del negozio che non ha ancora acceso. ACCESI di serie
# dall'ago 2026 (prima erano opt-in, e non li accendeva quasi nessuno).
# IL RITMO E' LA META' CHE CONTA, e va tenuto anche se un giorno il
# default tornasse spento: chi si stufa BLOCCA IL BOT, e col bot
# bloccato non riceve piu' le notifiche degli ordini, che sono
# portanti. Su Nostr il danno e' identico e meno visibile: smette
# semplicemente di leggere i DM, e non se ne accorge nessuno.
# Chi ha SCELTO — in un verso o nell'altro — non viene mai scavalcato
# dal default: lo garantisce la colonna utenti.suggerimenti_scelti.
SUGGERIMENTI_DI_SERIE = True    # False = tornano opt-in (chi ha gia'
                                # scelto resta com'e', in entrambi i sensi)
SUGGERIMENTI_OGNI_GIORNI = 7    # al massimo uno ogni N giorni PER
                                # PERSONA, qualunque sia la coda.
                                # 0 = nessun ritmo: e' la raffica di
                                # ieri, un freno d'emergenza e non una
                                # taratura

# --- Offerta lampo (sconto a tempo su tutto l'annuncio) --------------
# Modello Vinted «sconto ai follower»: quando qualcuno mette l'annuncio
# nel suo barattolo il venditore riceve un avviso anonimo e puo' lanciare
# uno sconto a tempo. E' PUBBLICO (chiunque compra nella finestra paga
# scontato) e a PERCENTUALE (non tocca mai il prezzo del listino).
LAMPO_ATTIVE = True          # interruttore generale (False = spento)
LAMPO_SCONTI = [10, 20, 30]  # le percentuali proposte come chip
LAMPO_MIN_PERCENTO = 5       # sconto minimo consentito
LAMPO_MAX_PERCENTO = 70      # sconto massimo consentito (anti-svendita)
ORE_LAMPO_OPZIONI = [6, 24, 48]  # le durate proposte
MAX_LAMPO_SETTIMANA = 2      # lanci per annuncio in 7 giorni
GIORNI_COLPO = 7             # cooldown dell'avviso «ha fatto colpo»

# --- Asta a tempo (vendita al miglior offerente) ---------------------
# Chi vuole comprare punta versando sats nel deposito di garanzia; per
# superare chi e' in testa si versa solo la differenza; alla scadenza
# la puntata piu' alta diventa un ordine gia' pagato e i perdenti
# vengono rimborsati nel loro «Da riscuotere». L'interruttore nasce
# SPENTO: le aste muovono denaro vero in uscita, si accende qui con un
# gesto consapevole guardando il primo giro (come l'import Nostr).
ASTA_ABILITATA = False       # interruttore generale (False = spento)
ASTA_DURATE_GIORNI = [1, 3, 7, 14, 30]  # le durate offerte al venditore
                             # (nel form: 7 giorni preselezionato)
ASTA_INCREMENTO_PERCENTO = 5 # rilancio minimo sopra la puntata in testa
ASTA_PROROGA_MINUTI = 10     # anti-cecchino: saldo negli ultimi N
                             # minuti = scadenza spostata a saldo + N
ASTA_MAX_ATTIVE_VENDITORE = 3  # aste vive per venditore (prudenza)
# Il proxy a budget depositato: chi punta deposita il suo MASSIMO e il
# sistema espone per lui il minimo necessario (il massimo resta
# segreto). Nasce SPENTO e resta spento anche quando ASTA_ABILITATA si
# accendera': il proxy parte solo a gara manuale rodata. Spegnerlo
# blocca le sole puntate proxy nuove, mai il motore dei proxy vivi.
ASTA_PROXY_ATTIVO = False    # rilancio automatico (False = spento)

DB = "satmarket.db"

# --- Import da Nostr (usato da importa_nostr.py) ---------------------
NPUB_VENDITORE = "INCOLLA_QUI_LA_NPUB_DEL_VENDITORE"  # npub1… oppure hex
VENDITORE_ID = 222   # a chi intestare gli annunci importati:
                     #  - collaudo: 222 (l'utente finto "Venditore")
                     #  - lancio: il VERO user id Telegram del venditore
                     #    (da @userinfobot); rilanciando lo script gli
                     #    annunci vengono re-intestati automaticamente

# --- Barattolo su Nostr (pubblicazione degli annunci) ----------------
# La chiave DELLA PIATTAFORMA (mai di utenti!) con cui il server firma
# gli annunci come eventi NIP-99. Generane una nuova con un client
# Nostr e incollala SOLO nel config.py del server: mai in chat, mai
# su GitHub. Finche' resta il segnaposto, la funzione e' spenta.
NOSTR_NSEC_PIATTAFORMA = "INCOLLA_QUI_LA_NSEC_DELLA_PIATTAFORMA"

# --- Import aperto da Nostr -------------------------------------------
# Barattolo mostra gli annunci NIP-99 che stanno su Nostr: chiunque
# pubblichi in italiano si ritrova in vetrina, e chi non ci vuole
# stare manda una cancellazione (kind 5) dal suo client, che qui
# viene rispettata per sempre. I filtri sono due: la lingua e la
# legge (parole vietate + AI, la stessa moderazione di chi pubblica
# da qui). NON serve elencare nessuna npub: i venditori si deducono
# dal database e la scoperta trova i nuovi da sola.
#
# Nasce SPENTA, ed e' voluto: acceso, il server apre account per
# venditori che non ci conoscono e manda loro un DM di benvenuto. Una
# cosa cosi' si accende di proposito, mai per il solo fatto di aver
# aggiornato il codice sul VPS. Questa riga e' anche l'interruttore
# d'emergenza: rimettila False e riavvia.
# False = nessun relay viene toccato e il mercatino vive come prima
# (l'import dell'unico venditore di ieri si lancia comunque a mano con
# `python importa_nostr.py`, che usa NPUB_VENDITORE / VENDITORE_ID).
IMPORT_NOSTR_APERTO = False

# --- Categorie proposte da sola (la coda dei moderatori) --------------
# Dopo ogni giro d'import l'AI guarda gli annunci arrivati dai relay (e
# chiunque sia rimasto in "Altro") e propone dove starebbero meglio: le
# proposte finiscono nella coda "Categorie da sistemare" del Profilo, e
# un moderatore le approva a gruppi. In vetrina non cambia niente
# finche' non le approvi tu.
# Costa pochi centesimi al giorno perche' chiede solo per gli annunci
# NUOVI o cambiati, e non ripropone mai uno spostamento gia' rifiutato.
# False = coda ferma (restano ricategorizza.py e sposta_a_mano.py, che
# si lanciano quando vuoi).
RICATEGORIZZA_AUTO = True

# --- Post automatici (la piattaforma racconta i fatti) ----------------
# Ogni nuovo annuncio in vetrina viene annunciato dai canali di
# Barattolo: una nota Nostr (con la chiave piattaforma qui sopra) e un
# post nel canale Telegram. Attivo di default; False per spegnere tutto.
POST_AUTOMATICI = True
# Il canale Telegram di Barattolo: "@nomecanale" oppure l'id numerico
# (-100...). Il bot deve esserne AMMINISTRATORE. Vuoto = niente post
# sul canale (la nota Nostr vive comunque).
TELEGRAM_CANALE_ID = ""
# Anti-spam: quanti post SINGOLI al massimo in un'ora. Oltre (o per le
# raffiche, es. un import CSV) esce un solo post aggregato
# ("N nuovi annunci nel barattolo").
POST_MAX_ORA = 6

# --- Avviso "fase di test" (il cartello all'apertura) ----------------
# Il cartello che accoglie chi apre l'app durante il rodaggio: si
# mostra UNA VOLTA AL GIORNO per dispositivo, a tutti (anche a chi
# guarda la vetrina da anonimo), mai nella demo coi dati finti.
# A rodaggio finito basta rimettere False: nessun cantiere.
BANNER_TEST = False
# La PRIMA riga diventa il titolo del cartello, il resto il messaggio.
BANNER_TEST_TESTO = """🚧 Barattolo è in fase di test.
Nei prossimi giorni integriamo il fornitore per le spedizioni (nel rispetto della privacy di ognuno) e sveleremo tutte le meccaniche d'acquisto.
Per ora esplora liberamente e contribuisci allo sviluppo: un feedback, un'opinione, una funzione che vorresti.
🎁 Un vantaggio dedicato ai primi 100 pionieri che ci aiuteranno a migliorarlo.
👉 Entra nel canale: dentro trovi il post fissato 📋 dove lasciare i tuoi feedback."""
# Dove porta il bottone "Entra nel canale". Vuoto = niente bottone.
BANNER_TEST_LINK = ""

# --- Contatore dei pionieri (in vetrina, sotto gli oggetti) ----------
# "👥 54 pionieri": quante persone sono già entrate nel mercatino.
# In rodaggio è un invito ad esserci; False lo spegne, e la riga
# sparisce dalla vetrina senza altro da toccare.
CONTATORE_UTENTI = True

# --- Campanello dei nuovi iscritti (solo ai moderatori) --------------
# «👥 Nuovo pioniere: Marco (@marco_b) — da Telegram. Siamo in 25.»
# Arriva SOLO agli ADMIN_IDS, mai sul canale pubblico. Ogni 10 minuti
# il server guarda chi è entrato: pochi = un messaggio ciascuno, una
# raffica = un solo messaggio col conto, senza nomi. In più un avviso
# ai traguardi (50, 100, 250, 500, 1000 pionieri).
AVVISI_ISCRITTI = True
# Quanti messaggi SINGOLI al massimo in un'ora: oltre questo tetto
# restano solo gli aggregati (che non nominano nessuno).
AVVISI_ISCRITTI_MAX_ORA = 6

# Il polso degli ordini: una riga ai moderatori quando un ordine nasce
# (sats in cassaforte) o si chiude (released/rimborso/disputa), col
# conto di quelli ancora aperti. Solo titolo e importi, mai nomi.
AVVISI_ORDINI_ADMIN = True

# --- Sicurezza degli accessi ------------------------------------------
# Quanto vale un initData di Telegram: e' la credenziale di OGNI
# chiamata dentro la Mini App, quindi senza scadenza uno catturato
# oggi apre quell'account per sempre. Ventiquattro ore e non cinque
# minuti perche' l'initData NON si rinfresca finche' la Mini App resta
# aperta: solo riaprirla ne conia uno nuovo, e una finestra corta
# butterebbe fuori chi la tiene minimizzata.
# 0 = spenta, cioe' si torna a un initData che non scade mai: e' un
# freno d'emergenza, non una scelta.
ORE_INITDATA = 24

# Quante ricerche AI puo' fare un utente in un'ora. E' l'unica rotta
# dove una richiesta qualunque diventa una chiamata ad Anthropic, e il
# prompt e' sempre grande uguale (fino a 300 annunci): senza freno, un
# ciclo banale brucia il credito. Finita la quota si risponde col
# filtro per parole, che non costa niente. 0 = nessun freno.
TETTO_RICERCHE_AI_ORA = 30

# Quanto resta buono un cambio BTC/EUR che non riusciamo a rinfrescare.
# L'ultimo cambio letto vive nel database e torna in cache a ogni
# riavvio (prima la cache nasceva vuota, e un deploy dentro
# un'interruzione di CoinGecko lasciava l'app senza saper convertire:
# pagina d'acquisto bloccata sui listini in euro). Ma un valore che
# sopravvive ai riavvii puo' invecchiare per sempre, quindi oltre
# queste ore torna a essere «non disponibile» — il ripiego onesto di
# sempre — invece di far pagare a qualcuno la cifra di ieri.
# 0 = non scade mai: freno d'emergenza, non una scelta.
ORE_CAMBIO_VALIDO = 24

# Ogni quanti secondi si rilegge il cambio, in un giro di sfondo suo.
# Da quando la fonte e' UNA SOLA (il client non chiama piu' CoinGecko
# per conto suo, il cambio gli arriva dalla vetrina) questa cadenza e'
# la freschezza che vede chiunque guardi un prezzo: un minuto e' il
# ritmo con cui il numero cambia davvero. La soglia oltre la quale il
# percorso caldo va a rileggerlo da se' NON e' un secondo numero: si
# ricava da qui (due giri di slack, minimo 120s).
# Un minuto sono ~1.400 chiamate al giorno da un IP solo: comodamente
# dentro il limite al minuto dell'endpoint pubblico di CoinGecko, ma
# BEN OLTRE le 10.000 al mese di una chiave Demo gratuita — se un
# giorno se ne mette una, questo numero va alzato (300 = ~9.000/mese).
# Si alza anche se CoinGecko comincia a rispondere 429.
# 0 = niente giro di sfondo: una lettura all'avvio e poi se ne occupa
# il percorso caldo, col suo raffreddamento da un minuto.
CAMBIO_RINFRESCO_S = 60

# --- Collaudo ---------------------------------------------------------
# False = com'e' giusto che sia online: nessuna identita' finta.
# True  = test locale con gli utenti finti (Compratore/Venditore/Admin),
#         e si mette A MANO quando si lavora sul portatile.
# Nasce spento come IMPORT_NOSTR_APERTO e ASTA_ABILITATA, e per la
# stessa ragione: acceso, l'header «collaudo:111» apre l'account di
# chiunque senza una firma: chi copia questo modello per il server non
# deve poterselo portare dietro per distrazione. Accenderlo dev'essere
# un gesto, e in locale e' il primo che si fa.
MODALITA_COLLAUDO = False
