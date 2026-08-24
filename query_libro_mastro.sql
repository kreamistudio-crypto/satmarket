-- =====================================================================
-- IL LIBRO MASTRO — i controlli a mano (ago 2026)
--
-- Gli stessi invarianti che l'orologio sorveglia da solo una volta al
-- giorno (`CONTROLLI_LIBRO_MASTRO` in server.py, che TACE quando tutto
-- torna e manda il 🧊 ai moderatori quando no). Questo file resta lo
-- strumento MANUALE: si lancia quando è arrivato un avviso e si
-- vogliono vedere le righe per intero, o quando si vuole guardare il
-- polso della funzione — che l'orologio non racconta, perché non è un
-- allarme.
--
--   sqlite3 ~/satmarket/satmarket.db < query_libro_mastro.sql
--
-- TUTTO IN SOLA LETTURA. Nessuna correzione automatica esiste, né qui
-- né nell'orologio: un libro mastro sbagliato lo guarda una persona.
-- I controlli da 1 a 16 DEVONO stampare «(nessuna riga)».
-- =====================================================================

.mode column
.headers on

-- --- IL CONTO DEGLI ORDINI: qui una violazione costa sats ------------

SELECT '1) ARITMETICA DELLA TESTATA (deve essere vuoto)' AS controllo;
-- prezzo_sats = Σ(unitario × quantità) − sconto + spedizione + protezione
SELECT o.id, o.prezzo_sats, SUM(r.unitario_sats*r.quantita) AS lordo,
       o.sconto_sats, o.spedizione_sats, o.protezione_sats,
       SUM(r.unitario_sats*r.quantita) - o.sconto_sats
         + o.spedizione_sats + o.protezione_sats AS atteso
  FROM ordini o JOIN ordine_righe r ON r.ordine_id = o.id
 GROUP BY o.id
HAVING o.prezzo_sats <> SUM(r.unitario_sats*r.quantita) - o.sconto_sats
                        + o.spedizione_sats + o.protezione_sats;

SELECT '2) ARITMETICA DEL MONO (deve essere vuoto)' AS controllo;
-- dall'ago 2026 il mono sconta («2) MONO SCONTATI» è morto qui: sarebbe
-- un falso allarme su ogni ordine legittimo). L'invariante vero è la
-- divisione a ritroso di _righe_ordine, che riaggiunge sconto_sats:
-- (prezzo − spedizione − protezione + sconto) si divide esatta per i pezzi
SELECT id, quantita, sconto_sats, prezzo_sats FROM ordini
 WHERE annuncio_id <> 0 AND quantita > 1
   AND (prezzo_sats - spedizione_sats - protezione_sats + sconto_sats)
       % quantita <> 0;

SELECT '3) SCONTI FUORI SCALA (deve essere vuoto)' AS controllo;
SELECT o.id, o.sconto_sats, SUM(r.unitario_sats*r.quantita) AS lordo
  FROM ordini o JOIN ordine_righe r ON r.ordine_id = o.id
 GROUP BY o.id
HAVING o.sconto_sats < 0 OR o.sconto_sats >= SUM(r.unitario_sats*r.quantita);

SELECT '3b) SCONTI FUORI SCALA SUL MONO (deve essere vuoto)' AS controllo;
-- il gemello per la testata (il JOIN qui sopra non vede mai i mono):
-- sconto >= lordo equivale a prezzo <= spedizione + protezione
SELECT id, sconto_sats, prezzo_sats - spedizione_sats - protezione_sats
         + sconto_sats AS lordo
  FROM ordini
 WHERE annuncio_id <> 0 AND (sconto_sats < 0
    OR (sconto_sats > 0
        AND prezzo_sats - spedizione_sats - protezione_sats <= 0));

SELECT '4) SCONTO E PERCENTUALE SCORDATI (deve essere vuoto)' AS controllo;
SELECT id, sconto_sats, sconto_percento FROM ordini
 WHERE (sconto_percento > 0) <> (sconto_sats > 0);

SELECT '5) PEZZI DELLA TESTATA (deve essere vuoto)' AS controllo;
SELECT o.id, o.quantita, SUM(r.quantita) AS somma_righe
  FROM ordini o JOIN ordine_righe r ON r.ordine_id = o.id
 GROUP BY o.id HAVING o.quantita <> SUM(r.quantita);

-- --- LA FORMA DI ordini / ordine_righe -------------------------------

SELECT '6) MONO CON RIGHE (deve essere vuoto)' AS controllo;
SELECT DISTINCT o.id, o.annuncio_id FROM ordini o
  JOIN ordine_righe r ON r.ordine_id = o.id WHERE o.annuncio_id <> 0;

SELECT '7) RIGHE ORFANE (deve essere vuoto)' AS controllo;
SELECT r.id, r.ordine_id, r.annuncio_id, r.titolo FROM ordine_righe r
 WHERE NOT EXISTS (SELECT 1 FROM ordini o WHERE o.id = r.ordine_id);

SELECT '8) CARRELLI SENZA MERCE (deve essere vuoto)' AS controllo;
SELECT o.id, o.stato, o.prezzo_sats FROM ordini o
 WHERE o.annuncio_id = 0
   AND NOT EXISTS (SELECT 1 FROM ordine_righe r WHERE r.ordine_id = o.id);

-- --- L'ASTA: la cassa deve tornare -----------------------------------

SELECT '9) CASSA DELL''ASTA CHIUSA (deve essere vuoto)' AS controllo;
-- Σ delta saldati = esposto della vincitrice + Σ registro.
-- Ancorata a stato='vincitrice': le aste VIVE, le deserte e quelle
-- annullate dall'admin non hanno una vincitrice e restano fuori — è
-- ciò che tiene la query silenziosa sui casi legittimi. I saldi
-- 'tardivo' sono comunque sats entrati e stanno a sinistra.
SELECT p.annuncio_id,
       (SELECT COALESCE(SUM(r.delta_sats),0) FROM rilanci r
         WHERE r.annuncio_id = p.annuncio_id
           AND r.stato IN ('saldato','tardivo'))          AS entrati,
       p.offerto_sats                                     AS esposto,
       (SELECT COALESCE(SUM(x.importo_sats),0) FROM rimborsi_asta x
         WHERE x.annuncio_id = p.annuncio_id)             AS registro
  FROM puntate p WHERE p.stato = 'vincitrice'
   AND (SELECT COALESCE(SUM(r.delta_sats),0) FROM rilanci r
         WHERE r.annuncio_id = p.annuncio_id
           AND r.stato IN ('saldato','tardivo'))
       <> p.offerto_sats + (SELECT COALESCE(SUM(x.importo_sats),0)
                              FROM rimborsi_asta x
                             WHERE x.annuncio_id = p.annuncio_id);

SELECT '10) PUNTATE CHIUSE SENZA RIMBORSO (deve essere vuoto)' AS controllo;
-- sats versati e mai messi in coda al registro: fermi e invisibili.
-- Il versato_sats > 0 è obbligatorio: una puntata mai salda e poi
-- chiusa non ha niente da rimborsare, legittimamente.
SELECT p.id, p.annuncio_id, p.tg_id, p.versato_sats FROM puntate p
 WHERE p.stato = 'chiusa' AND p.versato_sats > 0
   AND NOT EXISTS (SELECT 1 FROM rimborsi_asta x WHERE x.puntata_id = p.id);

SELECT '11) ESPOSTO SENZA COPERTURA (deve essere vuoto)' AS controllo;
-- versato >= offerto SEMPRE (uguali quando proxy=0). La forma con «<»
-- è quella che non ha stati transitori: una puntata non può gareggiare
-- con più sats di quanti ne siano stati versati.
SELECT id, annuncio_id, tg_id, stato, proxy, versato_sats, offerto_sats
  FROM puntate WHERE versato_sats < offerto_sats;

SELECT '12) DOPPI RIMBORSI DA RITIRO (deve essere vuoto)' AS controllo;
-- 'ritiro' è l'unico motivo senza indice UNIQUE: lo tiene solo il CAS
SELECT puntata_id, COUNT(*) AS quanti FROM rimborsi_asta
 WHERE motivo = 'ritiro' GROUP BY puntata_id HAVING COUNT(*) > 1;

SELECT '13) CINTURE D''IDEMPOTENZA CADUTE (deve essere vuoto)' AS controllo;
-- gli indici UNIQUE parziali di rimborsi_asta: se ne manca uno, il
-- prossimo crash a metà chiusura paga due volte
SELECT nome FROM (
  SELECT 'idx_rimborso_chiusura'  AS nome UNION ALL
  SELECT 'idx_rimborso_tardivo'         UNION ALL
  SELECT 'idx_rimborso_ecc_ritiro'      UNION ALL
  SELECT 'idx_rimborso_eccedenza')
 WHERE nome NOT IN (SELECT name FROM sqlite_master WHERE type='index');

-- --- LE COLONNE CHE NON DEVONO STARE INSIEME -------------------------

SELECT '14) ANNUNCI A DUE TESTE (deve essere vuoto)' AS controllo;
-- contatto_nostr (importato) e nostr_event_id (l'evento di questa riga,
-- firmato da noi O da lui col BIVIO) non stanno mai sulla stessa riga:
-- se ci stanno, la riga è nata qui e l'import se l'è presa — il
-- venditore non può più modificarla né rifornirla, e la coppia
-- sparisce dalla deduplica invece di comparirci
SELECT id, venditore_id, stato, contatto_nostr, nostr_event_id
  FROM annunci WHERE contatto_nostr <> '' AND nostr_event_id <> '';

SELECT '15) PAYOUT FUORI CONTRATTO (deve essere vuoto)' AS controllo;
SELECT id, payout_stato FROM ordini
 WHERE payout_stato NOT IN ('', 'incerto', 'uscito')
 UNION ALL
SELECT id, payout_stato FROM rimborsi_asta
 WHERE payout_stato NOT IN ('', 'incerto', 'uscito');

SELECT '16) PROMESSE DI SCONTO CHE NON POSSONO SCATTARE (vuoto)' AS controllo;
-- Qui non si perdono sats: si perde una vendita, e in silenzio. Un
-- criterio che nessun ramo sa applicare, o una soglia sotto il minimo
-- STRUTTURALE (2 pezzi, 1 €) — non le leve SCONTO_PACCO_MIN_*, che
-- cambiando farebbero suonare l'allarme senza che sia rotto niente.
-- Dal passaggio all'euro (ago 2026) questo controllo pesca ANCHE la
-- migrazione dimenticata: un negozio a criterio valore DICHIARATO IN
-- EURO con la colonna in euro ancora a zero promette e non scatta. Il
-- rimedio è converti_soglie_euro.py.
-- E dalla scelta della valuta il ramo a valore guarda l'unità
-- dichiarata: senza, suonerebbe su OGNI negozio in sats, che ha
-- legittimamente soglia_eur a zero.
-- Col criterio 'entrambi' (ago 2026) devono essere serie TUTTE E DUE le
-- gambe: chi ne accende due e ne ha una sola valida promette metà di
-- quel che crede.
SELECT tg_id, nome, sconto_pacco_criterio AS criterio,
       sconto_pacco_valore_valuta AS valuta,
       sconto_pacco_soglia AS soglia_pezzi,
       sconto_pacco_valore AS soglia_sats,
       sconto_pacco_valore_eur AS soglia_eur, sconto_pacco_percento AS pct
  FROM utenti WHERE sconto_pacco_percento > 0 AND (
       sconto_pacco_criterio NOT IN ('pezzi','valore','entrambi')
    OR (sconto_pacco_criterio IN ('pezzi','entrambi')
        AND sconto_pacco_soglia < 2)
    OR (sconto_pacco_criterio IN ('valore','entrambi') AND (
           sconto_pacco_valore_valuta NOT IN ('eur','sats')
        OR (sconto_pacco_valore_valuta = 'eur'  AND sconto_pacco_valore_eur < 1)
        OR (sconto_pacco_valore_valuta = 'sats' AND sconto_pacco_valore < 1))));

SELECT '15c) PROMESSA DI SPEDIZIONE GRATIS CHE NON PUÒ SCATTARE (vuoto)' AS controllo;
-- Il gemello, che fino alla scelta della valuta non aveva ragione di
-- esistere: allora c'era un intero >= 0 dove 0 significa «spenta», e
-- non c'era un valore rotto da trovare. Adesso una valuta fuori
-- catalogo è una promessa accesa che non scatta mai, in silenzio.
SELECT tg_id, nome, sped_gratis_valuta AS valuta,
       sped_gratis_soglia AS soglia_sats,
       sped_gratis_soglia_eur AS soglia_eur
  FROM utenti WHERE sped_gratis_valuta NOT IN ('eur','sats')
   AND (sped_gratis_soglia > 0 OR sped_gratis_soglia_eur > 0);

SELECT '16b) SPEDIZIONE RISPARMIATA E PAGATA INSIEME (vuoto)' AS controllo;
-- sped_gratis_sats è la tariffa OFFERTA, spedizione_sats quella
-- INCASSATA: le due si scrivono nello stesso INSERT e si escludono per
-- costruzione, quindi una riga qui vuol dire che una delle due cifre è
-- falsa — e una delle due è la ricevuta di qualcuno.
SELECT id, stato, consegna_scelta, spedizione_sats, sped_gratis_sats
  FROM ordini WHERE sped_gratis_sats > 0 AND spedizione_sats > 0;

SELECT '16c) SPEDIZIONE RISPARMIATA DOVE NON SI SPEDIVA (vuoto)' AS controllo;
-- un ritiro o un codice online non hanno una tariffa da regalare
SELECT id, stato, consegna_scelta, sped_gratis_sats
  FROM ordini WHERE sped_gratis_sats > 0
   AND consegna_scelta IN ('ritiro','digitale','servizio');

SELECT '16d) ORDINE NASCOSTO SU UNO STATO NON FINALE (vuoto)' AS controllo;
-- il nascondere (ago 2026) è ammesso solo su released/refunded, gli
-- stati assorbenti: un flag altrove è una guardia caduta — e un ordine
-- vivo che una parte non vede più
SELECT id, stato, nascosto_compratore, nascosto_venditore
  FROM ordini WHERE (nascosto_compratore = 1 OR nascosto_venditore = 1)
   AND stato NOT IN ('released', 'refunded');

SELECT '16e) INDIRIZZO FUORI CONTRATTO (vuoto)' AS controllo;
-- l'indirizzo di casa (ago 2026) si scrive col suo timbro e solo sulla
-- spedizione a casa. L'ultimo ramo è quello che conta davvero: se la
-- scopa ha timbrato la cancellazione ma il testo è ancora lì, la
-- promessa scritta nella pagina pubblica è falsa.
SELECT id, stato, via_punto, indirizzo_il, indirizzo_purgato_il,
       CASE WHEN indirizzo = '' THEN 'cancellato' ELSE 'presente' END AS testo
  FROM ordini
 WHERE (indirizzo <> '' AND indirizzo_il = 0)
    OR (indirizzo = '' AND indirizzo_il > 0 AND indirizzo_purgato_il = 0)
    OR (indirizzo <> '' AND via_punto = 1)
    OR (indirizzo_purgato_il > 0 AND indirizzo <> '');

SELECT '16f) OBIEZIONE SUL PUNTO FUORI CONTRATTO (vuoto)' AS controllo;
-- il venditore che segnala un punto sbagliato (ago 2026): timbro e
-- motivo si scrivono nello stesso UPDATE e solo sulla via punto. Il
-- secondo ramo è quello che morde: un'obiezione aperta fuori dalla via
-- punto zittisce `sollecita_venditori_fermi` senza che nessun altro
-- promemoria raccolga quell'ordine — la sua WHERE esige via_punto=1 —
-- cioè un ordine coi sats in cassaforte che non squilla più da nessuna
-- parte.
SELECT id, stato, via_punto, punto_obiettato_il, punto_obiezioni,
       CASE WHEN punto_obiezione = '' THEN 'nessun motivo'
            ELSE punto_obiezione END AS motivo
  FROM ordini
 WHERE (punto_obiettato_il > 0) <> (punto_obiezione <> '')
    OR (punto_obiettato_il > 0 AND via_punto = 0)
    OR (punto_obiezioni = 0 AND punto_obiettato_il > 0);

-- =====================================================================
-- Da qui in giù NON sono controlli: sono il polso, che l'orologio non
-- racconta perché non è un allarme.
-- =====================================================================

SELECT '17) I NEGOZI CHE SCONTANO' AS polso;
-- il CASE non è una comodità: senza, la colonna «soglia» mescola pezzi,
-- euro e sats ed è il primo posto dove un umano si sbaglia leggendo. Per
-- la stessa ragione accanto c'è l'UNITÀ, che dalla scelta della valuta
-- non si deduce più dal solo criterio.
SELECT tg_id, nome, sconto_pacco_criterio AS criterio,
       CASE WHEN sconto_pacco_criterio <> 'valore' THEN 'pezzi'
            ELSE sconto_pacco_valore_valuta END AS unita,
       CASE WHEN sconto_pacco_criterio <> 'valore'
              THEN sconto_pacco_soglia
            WHEN sconto_pacco_valore_valuta = 'sats'
              THEN sconto_pacco_valore
            ELSE sconto_pacco_valore_eur END AS soglia,
       sconto_pacco_percento AS sconto
  FROM utenti WHERE sconto_pacco_percento > 0
 ORDER BY sconto_pacco_percento DESC;

SELECT '17b) I NEGOZI CHE OFFRONO LA SPEDIZIONE' AS polso;
-- la seconda promessa di negozio, e le due si guardano insieme: sono
-- indipendenti (misurano lo stesso lordo, senza vedersi), ma un
-- venditore che le tiene tutte e due va letto in una riga sola
SELECT tg_id, nome, sped_gratis_valuta AS unita,
       CASE WHEN sped_gratis_valuta = 'sats' THEN sped_gratis_soglia
            ELSE sped_gratis_soglia_eur END AS gratis_da,
       sconto_pacco_percento AS sconto_carrello
  FROM utenti
 WHERE (sped_gratis_valuta = 'sats' AND sped_gratis_soglia > 0)
    OR (sped_gratis_valuta <> 'sats' AND sped_gratis_soglia_eur > 0)
 ORDER BY gratis_da;

SELECT '17d) SOGLIE ANCORA IN SATS DA CONVERTIRE (dovrebbe essere vuoto)' AS polso;
-- Il travaso del passaggio all'euro (ago 2026). NON è un controllo del
-- libro mastro, ed è deliberato: finché lo script non è girato questo
-- è uno stato transitorio LEGITTIMO, e un allarme che suona su uno
-- stato legittimo insegna a ignorarlo. Qui invece è il posto giusto:
-- lo si guarda quando si guarda il resto. Rimedio:
-- python converti_soglie_euro.py --scrivi
-- La VALUTA è nella WHERE: dalla scelta (ago 2026) «soglia in sats
-- piena, soglia in euro a zero» è la firma di chi ha SCELTO i sats, non
-- di una migrazione dimenticata. Senza quel filtro questa riga
-- elencherebbe per sempre negozi che stanno benissimo.
SELECT tg_id, nome, sconto_pacco_valore AS vecchia_sconto_sats,
       sped_gratis_soglia AS vecchia_sped_sats
  FROM utenti
 WHERE (sconto_pacco_valore > 0 AND sconto_pacco_valore_eur = 0
        AND sconto_pacco_valore_valuta = 'eur')
    OR (sped_gratis_soglia  > 0 AND sped_gratis_soglia_eur  = 0
        AND sped_gratis_valuta = 'eur');

SELECT '17c) GLI ORDINI CON LA SPEDIZIONE OFFERTA' AS polso;
SELECT COUNT(*) AS ordini, SUM(sped_gratis_sats) AS sats_di_spedizione,
       SUM(prezzo_sats) AS incassato
  FROM ordini WHERE sped_gratis_sats > 0;

SELECT '18) GLI ORDINI SCONTATI' AS polso;
SELECT COUNT(*) AS ordini, SUM(sconto_sats) AS sats_scontati,
       ROUND(AVG(sconto_percento), 1) AS percento_medio,
       SUM(prezzo_sats) AS incassato
  FROM ordini WHERE sconto_sats > 0;

SELECT '19) GLI ULTIMI DIECI SCONTATI' AS polso;
-- il lordo accanto ai pezzi: a criterio valore è LUI il numero che ha
-- fatto scattare la soglia, e senza non si capisce perché quell'ordine
-- ha scontato e quello sopra no. Il COALESCE è per i MONO (ago 2026,
-- il mono sconta): il LEFT JOIN a vuoto darebbe lordo NULL proprio
-- sui casi nuovi, e il lordo della testata è netto + sconto
SELECT o.id, o.stato, o.quantita AS pezzi,
       COALESCE(SUM(r.unitario_sats*r.quantita),
                o.prezzo_sats - o.spedizione_sats - o.protezione_sats
                  + o.sconto_sats) AS lordo,
       o.sconto_percento AS pct, o.sconto_sats, o.prezzo_sats,
       datetime(o.creato, 'unixepoch', 'localtime') AS quando
  FROM ordini o LEFT JOIN ordine_righe r ON r.ordine_id = o.id
 WHERE o.sconto_sats > 0 GROUP BY o.id ORDER BY o.id DESC LIMIT 10;

SELECT '20) I PAGAMENTI CONGELATI (non è un guasto: è la coda)' AS polso;
-- payout_stato='incerto' NON è un allarme — è una riga che aspetta un
-- moderatore, cioè il funzionamento previsto. Qui si guarda da quanto.
SELECT id, stato, payout_stato, payout_verso, payout_hash,
       datetime(aggiornato, 'unixepoch', 'localtime') AS da_quando
  FROM ordini WHERE payout_stato = 'incerto' ORDER BY aggiornato;

SELECT '17e) LO SBLOCCO PAGATO DEL BANNER' AS controllo;
-- I QUATTRO MODI in cui il primo incasso nostro puo' rompersi senza
-- che niente alzi la voce. Devono stampare "(nessuna riga)".
-- 1) ha pagato e la porta non si e' aperta
SELECT p.id, p.tg_id, p.importo_sats,
       datetime(p.pagato_il, 'unixepoch', 'localtime') AS pagato
  FROM pagamenti p JOIN utenti u ON u.tg_id = p.tg_id
 WHERE p.motivo = 'banner' AND p.stato = 'pagato'
   AND COALESCE(u.banner_sbloccato_il, 0) = 0;
-- 2) la porta si e' aperta senza che nessuno abbia pagato
SELECT u.tg_id, u.negozio,
       datetime(u.banner_sbloccato_il, 'unixepoch', 'localtime') AS aperta
  FROM utenti u WHERE COALESCE(u.banner_sbloccato_il, 0) > 0
   AND NOT EXISTS (SELECT 1 FROM pagamenti p WHERE p.tg_id = u.tg_id
     AND p.motivo = 'banner' AND p.stato IN ('pagato','rimborsato'));
-- 3) pagato due volte la stessa porta
SELECT tg_id, motivo, COUNT(*) AS quanti, SUM(importo_sats) AS sats
  FROM pagamenti WHERE stato = 'pagato'
 GROUP BY tg_id, motivo, riferimento HAVING COUNT(*) > 1;
-- 4) rimborsato ma la porta e' rimasta aperta
SELECT p.id, p.tg_id FROM pagamenti p JOIN utenti u ON u.tg_id = p.tg_id
 WHERE p.motivo = 'banner' AND p.stato = 'rimborsato'
   AND COALESCE(u.banner_sbloccato_il, 0) > 0
   AND NOT EXISTS (SELECT 1 FROM pagamenti q WHERE q.tg_id = p.tg_id
     AND q.motivo = 'banner' AND q.stato = 'pagato');

SELECT '21) IL POLSO DEGLI INCASSI NOSTRI (non e'' un allarme)' AS polso;
-- Quanto ha incassato Barattolo per se', e in che stato sono le righe.
-- E' anche la lista da incrociare col registro LNbits: il memo dice
-- «Barattolo sblocco banner #tg_id», e ogni incasso di quel tipo
-- DEVE avere una riga qui — altrimenti e' un orfano.
SELECT motivo, stato, COUNT(*) AS quanti, SUM(importo_sats) AS sats
  FROM pagamenti GROUP BY motivo, stato ORDER BY motivo, stato;
-- le ultime dieci, per guardarle una per una
SELECT id, tg_id, motivo, importo_sats, stato, payment_hash,
       datetime(creato, 'unixepoch', 'localtime') AS quando
  FROM pagamenti ORDER BY id DESC LIMIT 10;
-- e i congelati di questa tabella (il gemello della 20)
SELECT id, tg_id, stato, payout_stato, payout_hash,
       datetime(aggiornato, 'unixepoch', 'localtime') AS da_quando
  FROM pagamenti WHERE payout_stato = 'incerto' ORDER BY aggiornato;

SELECT '22) LA FORBICE DELLE TRATTATIVE (col rilancio, ago 2026)' AS forbice;
-- `importo_*` e' il pavimento (l'offerta di chi compra), `contro_*` il
-- soffitto (la richiesta di chi vende): ogni mossa stringe da un lato,
-- e i due non devono MAI incrociarsi. Se succede, da li' in poi
-- `_importo_accordo` puo' dire la cifra sbagliata — e nessun
-- confronto preventivo/invoice se ne accorge, perche' leggono la
-- stessa funzione.
SELECT id, stato, giri, importo_sats, contro_sats, importo_eur, contro_eur
  FROM offerte
 WHERE (contro_sats > 0 AND importo_sats >= contro_sats)
    OR (contro_eur > 0 AND importo_eur >= contro_eur);
-- e il contatore dei giri fuori scala: e' la sola cintura del
-- ping-pong, visto che il rilancio non consuma i tentativi per
-- annuncio.
SELECT id, stato, giri FROM offerte WHERE giri < 0 OR giri > 9;
