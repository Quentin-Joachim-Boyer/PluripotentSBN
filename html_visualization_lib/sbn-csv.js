/* Parsing CSV partagé (SBN viz / scatter / métagraphe). Script classique (file://).
   - parseLine : parseur CSV gérant les champs entre guillemets ("w_1,1").
   - parseName : extrait dimension + vecteur depuis un nom de fichier.
   - parse     : CSV complet en mémoire -> tableau d'objets {colonne: valeur} (petits fichiers, viz).
   - parseStream : streaming COLUMNAR + .gz, retour superset consommé par scatter & métagraphe.
*/
window.SBN = window.SBN || {};
SBN.csv = (function () {

  function parseLine(line) {
    const fields = []; let cur = '', inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') inQ = !inQ;
      else if (c === ',' && !inQ) { fields.push(cur.trim()); cur = ''; }
      else cur += c;
    }
    fields.push(cur.trim());
    return fields;
  }

  // La colonne `tree` (ex. "2[3[*,*],3[*,*]]") contient des virgules mais est écrite
  // NON quotée par le pipeline : elle déborde sur plusieurs champs. Comme c'est la seule
  // colonne à virgules non quotées, on recolle les champs excédentaires à sa position
  // (déduite du schéma d'en-tête). Sans-effet si elle est un jour quotée correctement.
  function realignTree(vals, ncol, treeIdx) {
    const extra = vals.length - ncol;
    return vals.slice(0, treeIdx)
      .concat([vals.slice(treeIdx, treeIdx + extra + 1).join(',')])
      .concat(vals.slice(treeIdx + extra + 1));
  }

  function parse(text) {
    const lines = text.trim().split(/\r?\n/);
    const header = parseLine(lines[0]);
    const treeIdx = header.indexOf('tree');
    return lines.slice(1).filter(l => l.trim()).map(line => {
      let vals = parseLine(line);
      if (treeIdx >= 0 && vals.length > header.length) vals = realignTree(vals, header.length, treeIdx);
      const obj = {};
      header.forEach((h, i) => obj[h] = vals[i] ?? '');
      return obj;
    });
  }

  function parseName(name) {
    const mDim = name.match(/^(\d+)d/);
    if (!mDim) return { dim: null, vec: [] };
    const dim = parseInt(mDim[1]);
    const mAngle = name.match(/<([0-9,]+)>/);
    if (mAngle) return { dim, vec: mAngle[1].split(',').map(Number) };
    const rest = name.slice(mDim[0].length).replace(/^_+/, '');
    const mVec = rest.match(/^([0-9][0-9_]*)/);
    if (!mVec) return { dim, vec: [] };
    return { dim, vec: mVec[1].split('_').filter(s => s !== '').map(Number) };
  }

  // Streaming columnar : ne matérialise jamais un objet par ligne. Colonnes gardées
  // (hors f_*/w_*) en tableaux parallèles (Float32Array croissant si numérique) ;
  // f_*/w_* dédupliqués par signature (référence partagée). onProgress(frac) = octets lus.
  async function parseStream(file, onProgress) {
    const gz = file.name.endsWith('.gz');
    const total = file.size || 0;
    let bytesRead = 0, lastPct = -1;
    const counter = new TransformStream({
      transform(chunk, controller) {
        bytesRead += chunk.byteLength; controller.enqueue(chunk);
        if (onProgress && total) {
          const pct = Math.floor(bytesRead / total * 100);
          if (pct !== lastPct) { lastPct = pct; onProgress(bytesRead / total); }
        }
      }
    });
    let stream = file.stream().pipeThrough(counter);
    if (gz) stream = stream.pipeThrough(new DecompressionStream('gzip'));
    const reader = stream.pipeThrough(new TextDecoderStream()).getReader();

    let header = null, leftover = '', treeIdx = -1;
    let keptIndices = null, colNames = null, numericCols = null, colData = null;
    let fIndices = [], wIndices = [], fcols = [];
    const fdataRows = [], wdataRows = [];
    const fdataDedup = new Map(), wdataDedup = new Map();

    function pushRow(fields) {
      if (!colData) {
        numericCols = keptIndices.map(i => {
          const v = fields[i];
          return v !== '' && v != null && Number.isFinite(parseFloat(v));
        });
        colData = keptIndices.map((_, j) => numericCols[j] ? { buf: new Float32Array(4096), len: 0 } : []);
      }
      for (let j = 0; j < keptIndices.length; j++) {
        const v = fields[keptIndices[j]] ?? '';
        if (numericCols[j]) {
          const c = colData[j];
          if (c.len === c.buf.length) { const nb = new Float32Array(c.buf.length * 2); nb.set(c.buf); c.buf = nb; }
          c.buf[c.len++] = parseFloat(v);
        } else colData[j].push(v);
      }
    }
    function captureRow(fields) {
      if (!fIndices.length) fdataRows.push(null);
      else { const arr = fIndices.map(i => fields[i] ?? ''); const sig = arr.join('\x00');
        if (!fdataDedup.has(sig)) fdataDedup.set(sig, arr); fdataRows.push(fdataDedup.get(sig)); }
      if (!wIndices.length) wdataRows.push(null);
      else { const arr = wIndices.map(i => fields[i] ?? ''); const sig = arr.join('\x00');
        if (!wdataDedup.has(sig)) wdataDedup.set(sig, arr); wdataRows.push(wdataDedup.get(sig)); }
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = (leftover + value).split(/\r?\n/);
      leftover = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let fields = parseLine(line);
        if (!header) {
          header = fields;
          treeIdx = header.indexOf('tree');
          keptIndices = header.map((h, i) => i).filter(i => !/^f_\d+$/.test(header[i]) && !/^w_\d+,\d+$/.test(header[i]));
          colNames = keptIndices.map(i => header[i]);
          fIndices = header.map((h, i) => i).filter(i => /^f_\d+$/.test(header[i])).sort((a, b) => +header[a].slice(2) - +header[b].slice(2));
          wIndices = header.map((h, i) => i).filter(i => /^w_\d+,\d+$/.test(header[i])).sort((a, b) => {
            const [ra, ca] = header[a].slice(2).split(',').map(Number), [rb, cb] = header[b].slice(2).split(',').map(Number);
            return ra !== rb ? ra - rb : ca - cb;
          });
          fcols = fIndices.map(i => header[i]);
          continue;
        }
        if (treeIdx >= 0 && fields.length > header.length) fields = realignTree(fields, header.length, treeIdx);
        if (fields.length < header.length) continue;
        pushRow(fields); captureRow(fields);
      }
    }
    if (leftover.trim() && header) {
      let fields = parseLine(leftover);
      if (treeIdx >= 0 && fields.length > header.length) fields = realignTree(fields, header.length, treeIdx);
      if (fields.length >= header.length) { pushRow(fields); captureRow(fields); }
    }

    const wN = wIndices.length ? Math.round(Math.sqrt(wIndices.length)) : 0;
    const nRows = (colData && colData.length) ? (numericCols[0] ? colData[0].len : colData[0].length) : 0;
    const cols = {};
    if (colData) for (let j = 0; j < colNames.length; j++) {
      if (numericCols[j]) { const c = colData[j]; cols[colNames[j]] = c.len === c.buf.length ? c.buf : c.buf.slice(0, c.len); }
      else cols[colNames[j]] = colData[j];
      colData[j] = null;
    }
    const vKeys = (colNames || []).filter(k => /^v_[0-9]+$/.test(k)).sort((a, b) => parseInt(b.slice(2)) - parseInt(a.slice(2)));
    return { name: file.name, nRows, nDataRows: fdataRows.length, colNames: colNames || [], cols,
             fcols, fdataRows, wdataRows, wN, vKeys, header: header || [] };
  }

  return { parseLine, parse, parseName, parseStream };
})();
