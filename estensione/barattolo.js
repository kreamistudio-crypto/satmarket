/* ═══ BARATTOZON DENTRO BARATTOLO (20 nov 2026, cantiere bz-integrata) ═══
   Gira SOLO su https://barattolo.store/*, e solo nella scheda aperta dal
   ponte (`#barattozon-estensione`). Chiede al ponte i dati dell'ordine
   Amazon e li consegna alla pagina di Barattolo con un evento
   `barattozon:ordine` (il dettaglio e' testo JSON): la pagina li passa
   dalla sua dogana e, con la sessione gia' aperta in questo browser,
   pubblica l'ordine da sola. La pagina dice quando e' pronta ad
   ascoltare con `barattozon:pronto`: l'evento parte quando ci sono
   tutt'e due le cose, i dati e la pagina. Nient'altro: niente rete,
   niente cookie, niente chiavi, niente lettura della pagina. */
(function(){
  if (location.hash !== '#barattozon-estensione') return;
  const API = (typeof browser !== 'undefined' && browser.runtime) ? browser : chrome;
  let dati = null, pronta = false, consegnato = false;

  function consegna(){
    if (consegnato || !dati || !pronta) return;
    consegnato = true;
    window.dispatchEvent(new CustomEvent('barattozon:ordine', {detail: JSON.stringify(dati)}));
  }

  window.addEventListener('barattozon:pronto', () => { pronta = true; consegna(); });
  API.runtime.sendMessage({tipo: 'prendi'}).then(r => {
    if (r && r.d) { dati = r.d; consegna(); }
  }, () => {});
})();
