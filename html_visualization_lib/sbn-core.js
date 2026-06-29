/* Cœur SBN partagé : logique PURE (aucun DOM). Script classique (file://).
   Attention aux variantes documentées :
   - transitionsFromF : dynamique depuis les chaînes f_* (scatter, métagraphe).
   - transitionsFromW : dynamique depuis la matrice de poids W (visualizer).
   - decompTree       : arbre de décomposition dérivé de T (findSplitBit) — scatter & métagraphe.
     (Le visualizer a sa propre décomposition vec-based, non incluse ici.)
*/
window.SBN = window.SBN || {};
SBN.core = (function () {

  const popcount = x => { let c = 0; while (x) { c += x & 1; x >>= 1; } return c; };
  const hexA = (hex, a) => `rgba(${parseInt(hex.slice(1,3),16)},${parseInt(hex.slice(3,5),16)},${parseInt(hex.slice(5,7),16)},${a})`;

  // T(s) depuis les chaînes f_* : bit (j-1) = caractère s de la chaîne f_j. -> Int32Array
  function transitionsFromF(fstr, n) {
    const N = 1 << n, T = new Int32Array(N);
    for (let s = 0; s < N; s++) { let t = 0; for (let j = 0; j < n; j++) if (fstr[j].charCodeAt(s) === 49) t |= (1 << j); T[s] = t; }
    return T;
  }

  // T(s) depuis la matrice de poids W{ "i,j" }. Convention : w_i,j = arc i->j ;
  // le nœud j s'active ssi somme_i W[i,j]*x_i > 0. -> objet { s: succ }
  function transitionsFromW(W, n) {
    const T = {};
    for (let s = 0; s < (1 << n); s++) {
      const bits = Array.from({ length: n }, (_, i) => (s >> i) & 1);
      const nb = Array.from({ length: n }, (_, j) => {
        const sum = bits.reduce((a, xi, i) => a + (W[`${i+1},${j+1}`] || 0) * xi, 0);
        return sum > 0 ? 1 : 0;
      });
      T[s] = nb.reduce((a, b, i) => a | (b << i), 0);
    }
    return T;
  }

  // Bassins + états dans un cycle. Superset : { inCycle:Uint8Array, basin:Int32Array, numBasins }.
  function basins(T, n) {
    const N = 1 << n;
    const inCycle = new Uint8Array(N), cycleId = new Int32Array(N).fill(-1);
    let cid = 0;
    for (let start = 0; start < N; start++) {
      const path = [], seen = {}; let cur = start;
      while (seen[cur] === undefined) { seen[cur] = path.length; path.push(cur); cur = T[cur]; }
      if (cycleId[cur] === -1) { for (let k = seen[cur]; k < path.length; k++) { inCycle[path[k]] = 1; cycleId[path[k]] = cid; } cid++; }
    }
    const basin = new Int32Array(N).fill(-1);
    for (let start = 0; start < N; start++) {
      let cur = start; const path = [];
      while (!inCycle[cur]) { path.push(cur); cur = T[cur]; }
      const b = cycleId[cur];
      for (const x of path) basin[x] = b;
      basin[cur] = b;
    }
    return { inCycle, basin, numBasins: cid };
  }

  // Arbre de décomposition dérivé de T : on cherche récursivement les bits qui
  // partitionnent l'ensemble en deux sous-faces bit-closes. -> liste de feuilles ou null.
  function decompTree(T, n) {
    let colorIdx = 0; const leaves = [];
    function findSplitBit(states, fixed) {
      for (let b = n - 1; b >= 0; b--) {
        if (fixed.has(b)) continue;
        const L = new Set(), R = new Set();
        for (const s of states) ((s >> b) & 1) ? R.add(s) : L.add(s);
        if (L.size > 0 && R.size > 0 && [...L].every(s => L.has(T[s])) && [...R].every(s => R.has(T[s]))) return b;
      }
      return -1;
    }
    function build(states, fixed) {
      if (!states.length) return;
      const sb = findSplitBit(states, fixed);
      if (sb === -1) { leaves.push({ groupKey: String(colorIdx++), states, dim: Math.round(Math.log2(states.length)) }); return; }
      const nf = new Set(fixed); nf.add(sb);
      const L = [], R = []; for (const s of states) ((s >> sb) & 1) ? R.push(s) : L.push(s);
      build(L, nf); build(R, nf);
    }
    build(Array.from({ length: 1 << n }, (_, i) => i), new Set());
    return leaves.length > 0 ? leaves : null;
  }

  // Géométrie de l'hypercube projeté (versions scatter/métagraphe).
  function hcPositions(n) {
    const N = 1 << n, p = [];
    for (let s = 0; s < N; s++) {
      const x = (s & 1), y = (s >> 1) & 1, z = (s >> 2) & 1;
      if (n <= 3) p.push([x*2-1, y*2-1, z*2-1]);
      else if (n === 4) { const w = (s >> 3) & 1, sc = w ? 1 : 0.5; p.push([(x*2-1)*sc, (y*2-1)*sc, (z*2-1)*sc]); }
      else { const sc = 1 - (s >> 3) * 0.15; p.push([(x*2-1)*sc, (y*2-1)*sc, (z*2-1)*sc]); }
    }
    return p;
  }
  function hcEdges(n) {
    const N = 1 << n, e = [];
    for (let s = 0; s < N; s++) for (let b = 0; b < n; b++) if (!((s >> b) & 1)) e.push([s, s | (1 << b)]);
    return e;
  }
  function rot3(p, rx, ry) {
    let [x, y, z] = p;
    const y2 = y*Math.cos(rx) - z*Math.sin(rx), z2 = y*Math.sin(rx) + z*Math.cos(rx);
    y = y2; z = z2;
    return [x*Math.cos(ry) + z*Math.sin(ry), y, -x*Math.sin(ry) + z*Math.cos(ry)];
  }

  return { popcount, hexA, transitionsFromF, transitionsFromW, basins, decompTree, hcPositions, hcEdges, rot3 };
})();
