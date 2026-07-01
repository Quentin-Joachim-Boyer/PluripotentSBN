/* Export de figures pour rapport (SBN viz / scatter / métagraphe). Script classique (file://).

   UI : un seul bouton « Export » ouvre un widget (SBN.export.dialog) où l'on choisit
   la PARTIE de la visu, le FORMAT (SVG/PNG) et l'ÉCHELLE (PNG).

   API bas niveau :
     SBN.export.svg(svgEl, name, opts)         -> .svg vectoriel
     SBN.export.svgToPNG(svgEl, name, opts)     -> .png rastérisé depuis un <svg>
     SBN.export.canvasPNG(canvas, name, opts)   -> .png d'un canvas
     SBN.export.compositePNG(canvases, name)    -> .png empilant plusieurs canvases
   opts : { background, scale }. background déf. = variable --bg courante (null = transparent).

   API widget :
     SBN.export.dialog(figures)
       figures : [{ id, label, formats:['svg','png'], scalable:true, run(format, scale) }]
*/
window.SBN = window.SBN || {};
SBN.export = (function () {

  function bgColor(opts) {
    if (opts && 'background' in opts) return opts.background;
    return getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#ffffff';
  }
  function stamp() {
    const d = new Date(), p = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
  }
  function name(prefix, ext) { return `${prefix}_${stamp()}.${ext}`; }

  // Base « significative » d'un nom de CSV : sans dossier, sans extension
  // (.csv/.csv.gz/.gz) ni suffixe _output ; caractères invalides remplacés par _.
  function baseName(filename) {
    let b = (filename || 'figure').split(/[\\/]/).pop();
    b = b.replace(/\.csv\.gz$/i, '').replace(/\.(csv|gz)$/i, '').replace(/_output$/i, '');
    return b.replace(/[<>:"/\\|?*]+/g, '_').replace(/_+$/,'') || 'figure';
  }

  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function _resolveVars(str) {
    const cs = getComputedStyle(document.documentElement);
    return str.replace(/var\(\s*(--[a-z0-9-]+)\s*\)/gi, (m, v) => cs.getPropertyValue(v).trim() || m);
  }

  // Dimensions d'un <svg> (attributs width/height, sinon viewBox, sinon bbox écran).
  function _dims(svgEl) {
    let w = parseFloat(svgEl.getAttribute('width')), h = parseFloat(svgEl.getAttribute('height'));
    if (!w || !h) {
      const vb = (svgEl.getAttribute('viewBox') || '').split(/\s+/).map(Number);
      const r = svgEl.getBoundingClientRect();
      if (!w) w = vb.length === 4 ? vb[2] : Math.round(r.width);
      if (!h) h = vb.length === 4 ? vb[3] : Math.round(r.height);
    }
    return { w, h };
  }

  // Sérialise un <svg> vivant en chaîne autonome (vars résolues, fond, dimensions).
  function _serialize(svgEl, opts) {
    const clone = svgEl.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
    const { w, h } = _dims(svgEl);
    clone.setAttribute('width', w);
    clone.setAttribute('height', h);
    const bg = bgColor(opts);
    if (bg) {
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', 0); rect.setAttribute('y', 0);
      rect.setAttribute('width', '100%'); rect.setAttribute('height', '100%');
      rect.setAttribute('fill', bg);
      clone.insertBefore(rect, clone.firstChild);
    }
    let str = new XMLSerializer().serializeToString(clone);
    str = _resolveVars(str);
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + str;
  }

  function svg(svgEl, filename, opts) {
    const str = _serialize(svgEl, opts);
    download(new Blob([str], { type: 'image/svg+xml;charset=utf-8' }), filename || name('figure', 'svg'));
  }

  // Rastérise un <svg> en PNG (échelle ≥1 pour la résolution).
  function svgToPNG(svgEl, filename, opts) {
    const str = _serialize(svgEl, opts);
    const scale = (opts && opts.scale) || 1;
    const { w, h } = _dims(svgEl);
    const url = URL.createObjectURL(new Blob([str], { type: 'image/svg+xml;charset=utf-8' }));
    const img = new Image();
    img.onload = () => {
      const cv = document.createElement('canvas');
      cv.width = Math.round(w * scale); cv.height = Math.round(h * scale);
      const ctx = cv.getContext('2d');
      const bg = bgColor(opts);
      if (bg) { ctx.fillStyle = bg; ctx.fillRect(0, 0, cv.width, cv.height); }
      ctx.drawImage(img, 0, 0, cv.width, cv.height);
      URL.revokeObjectURL(url);
      cv.toBlob(b => b && download(b, filename || name('figure', 'png')), 'image/png');
    };
    img.onerror = () => { URL.revokeObjectURL(url); alert('Échec du rendu SVG → PNG.'); };
    img.src = url;
  }

  function canvasPNG(canvas, filename, opts) {
    const bg = bgColor(opts);
    const fn = filename || name('figure', 'png');
    if (!bg) { canvas.toBlob(b => b && download(b, fn), 'image/png'); return; }
    const off = document.createElement('canvas');
    off.width = canvas.width; off.height = canvas.height;
    const ctx = off.getContext('2d');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, off.width, off.height);
    ctx.drawImage(canvas, 0, 0);
    off.toBlob(b => b && download(b, fn), 'image/png');
  }

  function compositePNG(canvases, filename, opts) {
    const cs = canvases.filter(Boolean);
    if (!cs.length) return;
    const w = cs[0].width, h = cs[0].height;
    const off = document.createElement('canvas');
    off.width = w; off.height = h;
    const ctx = off.getContext('2d');
    const bg = bgColor(opts);
    if (bg) { ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h); }
    for (const c of cs) { try { ctx.drawImage(c, 0, 0, w, h); } catch (_) {} }
    off.toBlob(b => b && download(b, filename || name('figure', 'png')), 'image/png');
  }

  // ── Widget de configuration d'export ─────────────────────────────────────────
  const FMT_LABEL = { svg: 'SVG (vectoriel)', png: 'PNG (image)' };

  function closeDialog() {
    const ex = document.getElementById('sbn-export-overlay');
    if (ex) ex.remove();
  }

  function dialog(figures) {
    if (!figures || !figures.length) return;
    closeDialog();
    const ov = document.createElement('div');
    ov.id = 'sbn-export-overlay';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:99999;display:flex;align-items:center;justify-content:center';
    const btnCss = 'border:none;border-radius:6px;padding:6px 12px;font-size:12px;cursor:pointer;font-family:inherit';
    ov.innerHTML = `
      <div style="background:var(--panel);color:var(--text);border:1px solid var(--border);border-radius:10px;
                  padding:16px 18px;min-width:300px;max-width:92vw;font-family:'DM Sans',sans-serif;box-shadow:0 10px 40px #0008">
        <div style="font-size:14px;font-weight:600;margin-bottom:12px">Exporter une figure</div>
        <div id="sbn-exp-figrow" style="margin-bottom:10px">
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px">Partie</label>
          <select id="sbn-exp-fig" style="width:100%;padding:5px 8px;font-size:12px"></select>
        </div>
        <div style="margin-bottom:10px">
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px">Format</label>
          <select id="sbn-exp-fmt" style="width:100%;padding:5px 8px;font-size:12px"></select>
        </div>
        <div id="sbn-exp-scalerow" style="margin-bottom:12px">
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px">Résolution (PNG)</label>
          <select id="sbn-exp-scale" style="width:100%;padding:5px 8px;font-size:12px">
            <option value="1">×1</option><option value="2">×2</option>
            <option value="3" selected>×3</option><option value="4">×4</option>
          </select>
        </div>
        <div style="font-size:10px;color:var(--muted);font-style:italic;margin-bottom:12px">
          Astuce : passe en thème clair (☀️) avant d'exporter pour un fond imprimable.
        </div>
        <div style="display:flex;justify-content:flex-end;gap:8px">
          <button id="sbn-exp-cancel" style="${btnCss};background:var(--border);color:var(--text)">Fermer</button>
          <button id="sbn-exp-go" style="${btnCss};background:var(--accent);color:#fff;font-weight:600">Exporter</button>
        </div>
      </div>`;
    document.body.appendChild(ov);

    const figSel = ov.querySelector('#sbn-exp-fig');
    const figRow = ov.querySelector('#sbn-exp-figrow');
    const fmtSel = ov.querySelector('#sbn-exp-fmt');
    const scaleRow = ov.querySelector('#sbn-exp-scalerow');
    const scaleSel = ov.querySelector('#sbn-exp-scale');

    figSel.innerHTML = figures.map((f, i) => `<option value="${i}">${f.label}</option>`).join('');
    if (figures.length === 1) figRow.style.display = 'none';

    function curFig() { return figures[+figSel.value]; }
    function refreshFmt() {
      const f = curFig();
      fmtSel.innerHTML = f.formats.map(x => `<option value="${x}">${FMT_LABEL[x] || x}</option>`).join('');
      refreshScale();
    }
    function refreshScale() {
      const f = curFig();
      const isPng = fmtSel.value === 'png';
      scaleRow.style.display = (isPng && f.scalable !== false) ? '' : 'none';
    }
    figSel.addEventListener('change', refreshFmt);
    fmtSel.addEventListener('change', refreshScale);
    refreshFmt();

    ov.querySelector('#sbn-exp-cancel').addEventListener('click', closeDialog);
    ov.addEventListener('click', e => { if (e.target === ov) closeDialog(); });
    ov.querySelector('#sbn-exp-go').addEventListener('click', () => {
      const f = curFig();
      const fmt = fmtSel.value;
      const scale = parseInt(scaleSel.value) || 3;
      closeDialog();
      try { f.run(fmt, scale); } catch (err) { console.error(err); alert('Export échoué : ' + (err && err.message || err)); }
    });
  }

  return { download, name, baseName, svg, svgToPNG, canvasPNG, compositePNG, dialog, closeDialog };
})();
