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
-- prezzo_sats = Σ(unitario × quantità) − sconto − accordo
--             + spedizione + protezione
-- (l'accordo sul carrello, ago 2026: la seconda voce sottrattiva di
-- testata — le righe restano LORDE)
SELECT o.id, o.prezzo_sats, SUM(r.unitario_sats*r.quantita) AS lordo,
       o.sconto_sats, o.accordo_sats, o.spedizione_sats, o.protezione_sats,
       SUM(r.unitario_sats*r.quantita) - o.sconto_sats - o.accordo_sats
         + o.spedizione_sats + o.protezione_sats AS atteso
  FROM ordini o JOIN ordine_righe r ON r.ordine_id = o.id
 GROUP BY o.id
HAVING o.prezzo_sats <> SUM(r.unitario_sats*r.quantita) - o.sconto_sats
                        - o.accordo_sats
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

-- --- L'ACCORDO SUL CARRELLO (ago 2026) -------------------------------

SELECT '8b) ACCORDO SU UN MONO (deve essere vuoto)' AS controllo;
-- è solo-SET per costruzione: la divisione a ritroso del mono non lo
-- sottrae, e un accordo lì sbaglierebbe l'unitario in silenzio
SELECT id, accordo_sats, prezzo_sats FROM ordini
 WHERE annuncio_id <> 0 AND accordo_sats > 0;

SELECT '8c) ACCORDO FUORI SCALA (deve essere vuoto)' AS controllo;
SELECT o.id, o.accordo_sats, SUM(r.unitario_sats*r.quantita) AS lordo
  FROM ordini o JOIN ordine_righe r ON r.ordine_id = o.id
 WHERE o.accordo_sats <> 0
 GROUP BY o.id
HAVING o.accordo_sats < 0
    OR o.accordo_sats > SUM(r.unitario_sats*r.quantita);

SELECT '8d) OFFERTE DI CARRELLO SENZA RIGHE (deve essere vuoto)' AS controllo;
SELECT o.id, o.stato FROM offerte o
 WHERE o.annuncio_id = 0
   AND NOT EXISTS (SELECT 1 FROM offerte_righe r WHERE r.offerta_id = o.id);

SELECT '8e) RIGHE D''OFFERTA ORFANE (deve essere vuoto)' AS controllo;
-- niente r.id: la tabella non ha quella colonna (il rowid c'e', ma
-- l'offerta mancante e' il dato che si cerca)
SELECT r.offerta_id, r.annuncio_id, r.titolo FROM offerte_righe r
 WHERE NOT EXISTS (SELECT 1 FROM offerte o WHERE o.id = r.offerta_id);

SELECT '8f) OFFERTE MONO CON RIGHE FIGLIE (deve essere vuoto)' AS controllo;
SELECT DISTINCT o.id, o.annuncio_id FROM offerte o
  JOIN offerte_righe r ON r.offerta_id = o.id WHERE o.annuncio_id <> 0;

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
-- 'in_volo' (dal 19 set 2026) è un pagamento in viaggio: stato
-- transitorio legittimo quanto 'incerto', e fino al 22 set questa
-- query lo segnalava come anomalia
SELECT id, payout_stato FROM ordini
 WHERE payout_stato NOT IN ('', 'incerto', 'uscito', 'da_riprovare',
                           'in_volo')
 UNION ALL
SELECT id, payout_stato FROM rimborsi_asta
 WHERE payout_stato NOT IN ('', 'incerto', 'uscito', 'da_riprovare',
                           'in_volo')
 UNION ALL
SELECT id, payout_stato FROM pagamenti
 WHERE payout_stato NOT IN ('', 'incerto', 'uscito', 'da_riprovare',
                           'in_volo');

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

SELECT '16g) BUSTA FUORI CONTRATTO (vuoto)' AS controllo;
-- la busta di consegna: flag, nome e codice si scrivono nello stesso
-- UPDATE e solo sulla via punto. Gli ultimi due bracci sono la BUSTA
-- DIRETTA (ago 2026, cantiere 45): la dichiarazione «il codice arriva
-- direttamente al compratore» vive solo sulla via punto, e il deposito
-- della busta la azzera nello STESSO UPDATE — «depositata E dichiarata»
-- non ha nessuno stato transitorio legittimo.
-- Il braccio del codice guarda la COLONNA e non il contenuto: dal
-- cantiere del documento una busta col solo QR non ha un codice
-- scritto, ed e' normale — non suona perche' _cifra_contenuto
-- prefissa anche il vuoto, quindi dopo un deposito la colonna non
-- e' mai ''. Quel che prende e' la colonna mai scritta col timbro.
SELECT id, stato, via_punto, busta_il, busta_diretta_il
  FROM ordini
 WHERE (busta_il > 0) <> (busta_nome <> '')
    OR (busta_il > 0) <> (busta_codice <> '')
    OR (busta_il > 0 AND via_punto = 0)
    OR (busta_corretta_il > 0 AND busta_il = 0)
    OR (busta_diretta_il > 0 AND via_punto = 0)
    OR (busta_diretta_il > 0 AND busta_il > 0);

SELECT '16h) PRESA IN CARICO FUORI CONTRATTO (vuoto)' AS controllo;
-- la rete di punti di casa (ago 2026): il timbro e il codice negozio
-- del punto si scrivono nello STESSO UPDATE, e solo su un ordine che
-- passa di lì. Il secondo braccio è quello che morde: una presa in
-- carico su una strada che non è la nostra vorrebbe dire che la
-- guardia della rotta è caduta — e quella riga avrebbe una busta
-- scritta da noi dove il codice lo deposita il venditore, cioè due
-- sorgenti per lo stesso dato.
SELECT id, stato, via_punto, punto_barattolo, punto_preso_il
  FROM ordini
 WHERE (punto_preso_il > 0) <> (punto_preso_da <> '')
    OR (punto_preso_il > 0 AND (via_punto = 0 OR punto_barattolo = ''));

SELECT '16i) PUNTO DI CASA FUORI CONTRATTO (vuoto)' AS controllo;
-- l'id del punto lo fissa compra() insieme alla via, e nessuna rotta
-- lo riscrive dopo: una riga con un punto di casa ma senza la via
-- punto la vedrebbe il titolare mentre per le due parti quella strada
-- non esiste.
-- ⚠️ NON si guarda se l'id è nel catalogo: togliere una voce è un
-- gesto LEGITTIMO — è la sola sanzione che abbiamo verso un punto — e
-- gli ordini già nati continuano a nominarlo apposta.
SELECT id, stato, via_punto, punto_barattolo
  FROM ordini
 WHERE punto_barattolo <> '' AND via_punto = 0;

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

SELECT '23) IL CONTO DI CASSA — UN POLSO, NON UN ALLARME (set 2026)' AS polso;
-- QUANTO DOVREBBE ESSERCI nel wallet LNbits della piattaforma, adesso.
-- Nasce dal 14 set 2026: un payout fallito era stato scritto come
-- riuscito, e per sapere se i sats fossero ancora in cassa non c'era
-- nessun numero da guardare — solo un elenco di pagamenti paginato di
-- cui non conoscevamo nemmeno l'ordine. Questo e' quel numero.
--
-- COME SI USA, in due gesti:
--   1. qui si legge `saldo_atteso_sats`, UNA RIGA PER CASSAFORTE;
--   2. si chiede a OGNI LNbits il suo saldo vero
--      (GET /api/v1/wallet -> `balance`, in MILLIsatoshi: si divide per 1000)
-- e si confrontano riga per riga. Dal doppio wallet (set 2026) il conto
-- e'' per cassaforte perche'' un numero solo non combacerebbe con NESSUN
-- wallet: ogni tabella porta la colonna `cassaforte`, e i rimborsi
-- d''asta con la colonna vuota la ereditano dalla puntata, come fa
-- `_cassaforte_riga` nel server.
--
-- ⚠️ IL WALLET NON E'' NATO VUOTO, ed e'' la voce senza la quale questo
-- controllo dava un FALSO POSITIVO GARANTITO (trovata da Andrea il 14
-- set 2026, il giorno stesso in cui e'' nato): dei sats nostri erano
-- gia'' li'' prima del primo ordine, e senza contarli lo scarto si
-- legge come «sats dati per pagati e ancora in cassa» — cioe''
-- esattamente l''allarme che deve restare raro. Il capitale si
-- DICHIARA, in `impostazioni`, UNA CHIAVE PER CASSAFORTE —
-- `capitale_saas_sats` e `capitale_nodo_sats` — e i numeri li da''
-- `capitale_cassa.py`, che legge i due registri:
--
--   INSERT OR REPLACE INTO impostazioni(chiave, valore)
--        VALUES('capitale_saas_sats', '123456');
--   INSERT OR REPLACE INTO impostazioni(chiave, valore)
--        VALUES('capitale_nodo_sats', '0');
--
-- (`capitale_nostro_sats`, la chiave di prima del doppio wallet, vale
-- ancora come RIPIEGO per il solo SaaS: era l''unico wallet che c''era,
-- e un numero gia'' dichiarato non si perde per un nome nuovo.)
--
-- E'' il NETTO di quel che ci abbiamo messo NOI — il capitale iniziale
-- piu'' i versamenti successivi, meno i prelievi per noi — e si aggiorna
-- a mano ogni volta che quel denaro si muove. Si chiama «nostro» e non
-- «iniziale» perche'' un nome che invecchia male costa piu'' di un nome
-- diverso di una parola: il giorno del secondo versamento, «iniziale»
-- diventerebbe una bugia e nessuno lo verrebbe a sapere.
--
-- ⚠️⚠️ E NON SI RICAVA DAL SALDO DI OGGI. La scorciatoia che viene in
-- mente — «capitale = saldo vero meno (entrate - uscite)» — e'' circolare:
-- farebbe leggere ZERO a questo controllo per sempre, e ci murerebbe
-- dentro qualunque buco ci sia adesso. Il capitale si legge dal registro
-- LNbits: sono gli incassi che NON hanno un memo di Barattolo (i nostri
-- memo sono «Barattolo escrow #», «Barattolo escrow set:», «Barattolo
-- asta #», «Barattolo sblocco banner #»), meno i prelievi che abbiamo
-- fatto per noi.
--
-- SE IL CAPITALE NON E'' DICHIARATO, `saldo_atteso_sats` viene VUOTO
-- invece che sbagliato: un numero che manca non si sostituisce con zero.
-- E'' la stessa regola del lettore degli esiti — nel dubbio si dice «non
-- lo so», mai un si''.
--
-- ⚠️⚠️ NON E'' UN ALLARME, E NON DIVENTERA'' MAI TALE SU QUESTO WALLET
-- (decisione di Andrea, 15 set 2026, il giorno dopo averlo scritto).
-- LA RAGIONE E'' STRUTTURALE e non si cura con piu'' voci: la cassaforte
-- e'' un wallet MISTO — ci stanno gli escrow degli ordini e sats suoi,
-- che entrano ed escono per ragioni che il database non vede e non deve
-- vedere. Quindi il confronto col saldo vero NON deve tornare, e un
-- rilevatore che non torna mai e'' peggio di nessun rilevatore: insegna
-- a ignorare la riga, e il giorno che avesse ragione nessuno gli
-- crederebbe. Si guarda per CURIOSITA'' contabile, mai per decidere.
--
-- QUEL CHE VALE DAVVERO STA ALTROVE, ed e'' la lezione del cantiere: la
-- protezione e'' PER ORDINE, non di cassa. Ogni payout ha il suo
-- payment_hash scritto nella riga, il suo esito chiesto per hash, il suo
-- ritentativo e il suo avviso ai moderatori quando fallisce. Una prova
-- per riga batte una quadratura globale su un conto misto, sempre: la
-- prima nomina il caso, la seconda da'' un numero che non si sa leggere.
--
-- L'UNICA RIGA CHE PARLA DA SOLA e'' `movimento_mercatino`, che non
-- dipende dal capitale: se e'' NEGATIVO sono usciti piu'' sats di quanti
-- ne siano entrati dagli utenti, e li'' non serve nessun confronto con
-- niente. Quello si guarda.
--
-- (Le commissioni di routing, per memoria: escono davvero dal wallet e
-- non sono registrate da nessuna parte — misurate, 179 sats su 67.672,
-- cioe'' lo 0,26%.)
--
-- TRE COSE CHE QUESTO CONTO NON SA, dichiarate perche'' chi legge non
-- ci inciampi:
--   a) LA COMMISSIONE NON E'' FOTOGRAFATA sull'ordine. Il netto del
--      venditore si ricalcola con la leva di OGGI, quindi il giorno che
--      COMMISSIONE_PERCENTO cambia, le righe vecchie vengono ricontate
--      con l'aliquota nuova e questo numero sbanda. Oggi la leva e'' 0 e
--      il netto e'' prezzo - protezione: la riga sotto lo scrive cosi'',
--      e chi accende la commissione deve tornare qui.
--   b) GLI ORDINI NATI DA UN'ASTA non hanno pagato una fattura loro: i
--      sats erano gia'' in cassa dai `rilanci`. Contarli due volte
--      gonfierebbe l'atteso, quindi si escludono guardando l'annuncio
--      (`asta_base_sats > 0`).
--   c) LE FATTURE IN ENTRATA CREATE E NON PAGATE non c'entrano: non e''
--      mai arrivato niente. Gli stati 'creato' e 'annullato' sono fuori.
WITH
  casseforti(nome) AS (SELECT 'saas' UNION ALL SELECT 'nodo'),
  -- IL CAPITALE NOSTRO, dichiarato, uno per cassaforte. Il CAST che
  -- torna su se stesso non e'' pignoleria: `CAST('' AS INTEGER)` fa
  -- ZERO, quindi una riga scritta male — vuota, con uno spazio, con
  -- «123 sats» dentro — passerebbe per un capitale nullo e il conto
  -- tornerebbe a mentire in silenzio. Se il valore non e'' un intero
  -- pulito, qui resta NULL e il saldo atteso resta vuoto.
  dichiarato AS (
    SELECT 'saas' AS cf, COALESCE(
        (SELECT valore FROM impostazioni WHERE chiave = 'capitale_saas_sats'),
        (SELECT valore FROM impostazioni WHERE chiave = 'capitale_nostro_sats'))
        AS valore
    UNION ALL
    SELECT 'nodo', (SELECT valore FROM impostazioni
                     WHERE chiave = 'capitale_nodo_sats')),
  capitale AS (
    SELECT cf, CASE WHEN CAST(CAST(TRIM(valore) AS INTEGER) AS TEXT)
                         = TRIM(valore)
                    THEN CAST(TRIM(valore) AS INTEGER) END AS sats
      FROM dichiarato),
  -- ENTRATE: gli escrow degli ordini NON nati da un'asta
  dentro_ordini AS (
    SELECT o.cassaforte AS cf, SUM(o.prezzo_sats) AS sats
      FROM ordini o LEFT JOIN annunci a ON a.id = o.annuncio_id
     WHERE o.stato NOT IN ('creato', 'annullato')
       AND COALESCE(a.asta_base_sats, 0) = 0
     GROUP BY o.cassaforte),
  -- ENTRATE: i versamenti d'asta saldati (anche i tardivi: quei sats
  -- sono in cassa, e ne escono come rimborso)
  dentro_aste AS (
    SELECT cassaforte AS cf, SUM(delta_sats) AS sats
      FROM rilanci WHERE stato IN ('saldato', 'tardivo')
     GROUP BY cassaforte),
  -- ENTRATE: i nostri incassi (lo sblocco del banner)
  dentro_nostri AS (
    SELECT cassaforte AS cf, SUM(importo_sats) AS sats
      FROM pagamenti WHERE stato IN ('pagato', 'rimborsato')
     GROUP BY cassaforte),
  -- USCITE: il netto ai venditori sugli ordini chiusi
  fuori_venditori AS (
    SELECT cassaforte AS cf, SUM(prezzo_sats - protezione_sats) AS sats
      FROM ordini WHERE stato = 'released' GROUP BY cassaforte),
  -- USCITE: i rimborsi integrali ai compratori
  fuori_compratori AS (
    SELECT cassaforte AS cf, SUM(prezzo_sats) AS sats
      FROM ordini WHERE stato = 'refunded' GROUP BY cassaforte),
  -- USCITE: i rimborsi d'asta riscossi (la cassaforte vuota si
  -- eredita dalla puntata, e nel dubbio e'' il SaaS: la colonna e''
  -- nata col doppio wallet, e quel che c''era prima stava tutto la'')
  fuori_aste AS (
    SELECT COALESCE(NULLIF(r.cassaforte, ''),
                    (SELECT cassaforte FROM rilanci
                      WHERE puntata_id = r.puntata_id
                        AND stato IN ('saldato', 'tardivo')
                      ORDER BY id LIMIT 1),
                    'saas') AS cf,
           SUM(r.importo_sats) AS sats
      FROM rimborsi_asta r WHERE r.stato = 'riscosso' GROUP BY 1),
  -- USCITE: gli sblocchi restituiti da un moderatore
  fuori_nostri AS (
    SELECT cassaforte AS cf, SUM(importo_sats) AS sats
      FROM pagamenti WHERE stato = 'rimborsato' GROUP BY cassaforte),
  conto AS (
    SELECT c.nome AS cassaforte,
      (SELECT sats FROM capitale WHERE cf = c.nome)         AS capitale_nostro,
      COALESCE((SELECT sats FROM dentro_ordini    WHERE cf = c.nome), 0)
                                                            AS in_escrow_ordini,
      COALESCE((SELECT sats FROM dentro_aste      WHERE cf = c.nome), 0)
                                                            AS in_versamenti_asta,
      COALESCE((SELECT sats FROM dentro_nostri    WHERE cf = c.nome), 0)
                                                            AS in_incassi_nostri,
      COALESCE((SELECT sats FROM fuori_venditori  WHERE cf = c.nome), 0)
                                                            AS out_ai_venditori,
      COALESCE((SELECT sats FROM fuori_compratori WHERE cf = c.nome), 0)
                                                            AS out_ai_compratori,
      COALESCE((SELECT sats FROM fuori_aste       WHERE cf = c.nome), 0)
                                                            AS out_rimborsi_asta,
      COALESCE((SELECT sats FROM fuori_nostri     WHERE cf = c.nome), 0)
                                                            AS out_sblocchi_resi
      FROM casseforti c)
SELECT
  cassaforte,
  CASE WHEN capitale_nostro IS NULL
       THEN 'NO — dichiaralo, o il confronto non si puo'' fare'
       ELSE 'si' END                  AS capitale_dichiarato,
  capitale_nostro, in_escrow_ordini, in_versamenti_asta, in_incassi_nostri,
  out_ai_venditori, out_ai_compratori, out_rimborsi_asta, out_sblocchi_resi,
  -- il movimento del solo mercatino, che vale anche senza il capitale:
  -- se questo numero e'' negativo sono usciti piu'' sats di quanti ne
  -- siano entrati dagli utenti, e li'' non serve nessun confronto
  in_escrow_ordini + in_versamenti_asta + in_incassi_nostri
    - out_ai_venditori - out_ai_compratori - out_rimborsi_asta
    - out_sblocchi_resi                 AS movimento_mercatino,
  -- e l''atteso vero, che senza il capitale resta VUOTO invece che
  -- sbagliato (NULL si propaga da solo in tutta la somma)
  capitale_nostro
    + in_escrow_ordini + in_versamenti_asta + in_incassi_nostri
    - out_ai_venditori - out_ai_compratori - out_rimborsi_asta
    - out_sblocchi_resi                 AS saldo_atteso_sats
  FROM conto;

SELECT '23b) DI CHE COSA E'' FATTO L''ATTESO (le voci che restano a noi)' AS polso;
-- Le due leve che NON escono mai dalla cassaforte: servono a capire
-- quanta parte dell'atteso e'' denaro NOSTRO e quanta e'' deposito di
-- garanzia di qualcun altro. Non entrano nel conto qui sopra — sono
-- gia'' dentro `prezzo_sats` — ma dicono dove guardare quando il numero
-- non torna.
SELECT
  (SELECT COALESCE(SUM(protezione_sats), 0) FROM ordini
    WHERE stato = 'released')                       AS protezioni_trattenute,
  (SELECT COALESCE(SUM(prezzo_sats - protezione_sats), 0) FROM ordini
    WHERE stato = 'released')                       AS netti_gia_usciti,
  (SELECT COALESCE(SUM(prezzo_sats), 0) FROM ordini
    WHERE stato NOT IN ('creato','annullato','released','refunded'))
                                                    AS escrow_ancora_aperti,
  (SELECT COUNT(*) FROM ordini
    WHERE stato NOT IN ('creato','annullato','released','refunded'))
                                                    AS ordini_aperti;

SELECT '24) LE DUE CASSAFORTI: cosa resta aperto, e dove (set 2026)' AS polso;
-- Il doppio wallet: ogni riga di denaro porta la sua cassaforte
-- ('saas' = il LNbits ospitato di ieri, 'nodo' = il LNbits nostro sul
-- VPS). E'' IL NUMERO DELLA FASE 4: il SaaS si puo'' svuotare e disdire
-- solo quando le righe APERTE con cassaforte 'saas' sono ZERO su tutt''e
-- quattro i registri — un rimborso di un ordine del SaaS esce dal SaaS,
-- e un wallet chiuso con una riga aperta e'' un rimborso che non parte.
-- I rimborsi d''asta con cassaforte '' non sono un errore: la colonna
-- si compila dalla puntata la prima volta che il rimborso si paga.
SELECT 'ordini' AS registro, cassaforte, COUNT(*) AS aperte,
       SUM(prezzo_sats) AS sats
  FROM ordini
 WHERE stato NOT IN ('creato','annullato','released','refunded')
 GROUP BY cassaforte
UNION ALL
SELECT 'rilanci (versati su aste ancora vive)', cassaforte, COUNT(*),
       SUM(delta_sats)
  FROM rilanci WHERE stato IN ('saldato','tardivo')
   AND puntata_id IN (SELECT id FROM puntate WHERE stato = 'attiva')
 GROUP BY cassaforte
UNION ALL
SELECT 'rimborsi_asta da riscuotere', cassaforte, COUNT(*), SUM(importo_sats)
  FROM rimborsi_asta WHERE stato = 'da_riscuotere'
 GROUP BY cassaforte
UNION ALL
SELECT 'pagamenti (fattura viva)', cassaforte, COUNT(*), SUM(importo_sats)
  FROM pagamenti WHERE stato = 'creato'
 GROUP BY cassaforte
UNION ALL
SELECT 'payout congelati o in volo', cassaforte, COUNT(*), 0
  FROM ordini WHERE payout_stato IN ('incerto','in_volo','da_riprovare')
 GROUP BY cassaforte;
-- (le puntate 'chiusa' hanno gia'' il loro rimborso nel registro sotto,
-- le 'vincitrice' i loro sats nell''ordine: contarle qui sarebbe
-- contarle due volte, e il conto non scenderebbe mai a zero)
-- e dove nasce il denaro nuovo lo dice il pannello «Stato delle leve»,
-- non questo file: la leva si legge VIVA. Lo stesso conto lo fa
-- l''orologio da solo (`avvisa_saas_senza_doveri`) e avvisa UNA volta,
-- il giorno che scende a zero.
-- ---------------------------------------------------------------------
-- 25) I CREDITI DA RECUPERARE (21 set 2026, «paga da un''altra
-- cassaforte»): i pagamenti rimasti appesi su una cassaforte mentre
-- l''ordine veniva pagato da un''altra. 'aperto' = sats impegnati la';
-- 'doppio' = si e'' saldato lo stesso, chi vende ha ricevuto due volte.
-- Vuoto e'' la risposta sana. La ronda quotidiana lo grida da sola.
SELECT '25) I CREDITI DA RECUPERARE (vuoto = niente di appeso)' AS controllo;
SELECT id, tabella, riga_id, cassaforte, pagato_da, sats, stato,
       datetime(deciso_il, 'unixepoch', 'localtime') AS deciso, deciso_da,
       motivo, nota
  FROM crediti_cassaforte WHERE stato IN ('aperto','doppio');
-- ...e gli ordini che pagano da una cassaforte diversa dalla loro: ognuno
-- deve avere la sua nota (chi, quando, perche'')
SELECT '25b) GLI INCASSI DEVIATI (un polso: ognuno con la sua nota)' AS polso;
SELECT id, stato, payout_stato, cassaforte, cassaforte_payout, payout_nota
  FROM ordini WHERE COALESCE(cassaforte_payout,'') <> '';
