/* Thème clair / sombre partagé (SBN viz / scatter / métagraphe).
   Le DOM suit les variables CSS ; le canvas lit ces variables dans SBN.theme.TH
   (rafraîchi à chaque bascule). Chargé en <script src> classique (compatible file://).

   Usage app :
     const TH = SBN.theme.TH;                 // objet stable, muté en place
     SBN.theme.init({ onChange: reRender });   // applique le thème mémorisé
     // bouton : onclick="SBN.theme.toggle()"
*/
window.SBN = window.SBN || {};
SBN.theme = (function () {
  const TH = {};            // objet STABLE (muté en place) -> les alias `const TH=SBN.theme.TH` restent valides
  let onChange = null;

  function read() {
    const s = getComputedStyle(document.documentElement), g = k => s.getPropertyValue(k).trim();
    Object.assign(TH, {
      bg:g('--bg'), panel:g('--panel'), border:g('--border'),
      accent:g('--accent'), accent2:g('--accent2'), text:g('--text'), muted:g('--muted'),
      grid:g('--grid'), axis:g('--axis'), ring:g('--ring'), ringHalo:g('--ring-halo'),
      nodeOff:g('--node-off'), skeleton:g('--skeleton'), edge:g('--edge'),
    });
  }
  function apply(mode) {
    document.documentElement.setAttribute('data-theme', mode);
    try { localStorage.setItem('sbn-theme', mode); } catch (_) {}
    read();
    const b = document.getElementById('theme-btn');
    if (b) b.textContent = mode === 'light' ? '☀️' : '🌙';
    if (onChange) onChange();
  }
  function toggle() {
    apply(document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
  }
  function init(opts) {
    onChange = (opts && opts.onChange) || null;
    let saved = null; try { saved = localStorage.getItem('sbn-theme'); } catch (_) {}
    apply(saved || 'dark');
  }
  return { TH, read, apply, toggle, init };
})();
