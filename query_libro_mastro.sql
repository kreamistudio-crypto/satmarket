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

SELECT '2) MONO SCONTATI (deve essere vuoto)' AS controllo;
-- lo sconto carrello è del CARRELLO: su un ordine a un annuncio solo
-- romperebbe la divisione a ritroso dell'unitario di _righe_ordine
SELECT id, annuncio_id, sconto_sats, sconto_percento FROM ordini
 WHERE annuncio_id <> 0 AND (sconto_sats <> 0 OR sconto_percento <> 0);

SELECT '3) SCONTI FUORI SCALA (deve essere vuoto)' AS controllo;
SELECT o.id, o.sconto_sats, SUM(r.unitario_sats*r.quantita) AS lordo
  FROM ordini o JOIN ordine_righe r ON r.ordine_id = o.id
 GROUP BY o.id
HAVING o.sconto_sats < 0 OR o.sconto_sats >= SUM(r.unitario_sats*r.quantita);

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
-- contatto_nostr (importato) e nostr_event_id (nativo, firmato da noi)
-- non stanno mai sulla stessa riga: la deduplica confronterebbe un
-- annuncio con sé stesso
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
-- STRUTTURALE (2 pezzi, 1 sat) — non le leve SCONTO_PACCO_MIN_*, che
-- cambiando farebbero suonare l'allarme senza che sia rotto niente.
SELECT tg_id, nome, sconto_pacco_criterio AS criterio,
       sconto_pacco_soglia AS soglia_pezzi,
       sconto_pacco_valore AS soglia_sats, sconto_pacco_percento AS pct
  FROM utenti WHERE sconto_pacco_percento > 0 AND (
       sconto_pacco_criterio NOT IN ('pezzi','valore')
    OR (sconto_pacco_criterio = 'pezzi'  AND sconto_pacco_soglia < 2)
    OR (sconto_pacco_criterio = 'valore' AND sconto_pacco_valore < 1));

-- =====================================================================
-- Da qui in giù NON sono controlli: sono il polso, che l'orologio non
-- racconta perché non è un allarme.
-- =====================================================================

SELECT '17) I NEGOZI CHE SCONTANO' AS polso;
-- il CASE non è una comodità: senza, la colonna «soglia» mescola pezzi
-- e sats ed è il primo posto dove un umano si sbaglia leggendo
SELECT tg_id, nome, sconto_pacco_criterio AS criterio,
       CASE sconto_pacco_criterio WHEN 'valore' THEN sconto_pacco_valore
            ELSE sconto_pacco_soglia END AS soglia,
       sconto_pacco_percento AS sconto
  FROM utenti WHERE sconto_pacco_percento > 0
 ORDER BY sconto_pacco_percento DESC;

SELECT '18) GLI ORDINI SCONTATI' AS polso;
SELECT COUNT(*) AS ordini, SUM(sconto_sats) AS sats_scontati,
       ROUND(AVG(sconto_percento), 1) AS percento_medio,
       SUM(prezzo_sats) AS incassato
  FROM ordini WHERE sconto_sats > 0;

SELECT '19) GLI ULTIMI DIECI SCONTATI' AS polso;
-- il lordo accanto ai pezzi: a criterio valore è LUI il numero che ha
-- fatto scattare la soglia, e senza non si capisce perché quell'ordine
-- ha scontato e quello sopra no
SELECT o.id, o.stato, o.quantita AS pezzi,
       SUM(r.unitario_sats*r.quantita) AS lordo,
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
