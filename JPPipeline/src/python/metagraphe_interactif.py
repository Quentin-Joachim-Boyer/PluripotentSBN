"""
Métagraphe mutationnel interactif.

Génère un fichier HTML autonome (données JSON embarquées) depuis le CSV
de la pipeline. Même style que sbn_scatter.

Usage:
  python metagraphe_interactif.py sbnps.csv [--out metagraphe.html]
"""

import argparse
import itertools
import json
import math
import pandas as pd
import networkx as nx


# ── Mutation graph (copié de metagraphe_mutation.py) ─────────────────────────

def w_bound(n):
    if n <= 2: return 1
    if n == 3: return 2
    if n == 4: return 3
    return n

def threshold(v):
    n = len(v)
    return tuple(1 if sum(v[i] for i in range(n) if s & (1 << i)) > 0 else 0
                 for s in range(1 << n))

def sbf_neighbors(n):
    wb = w_bound(n)
    domain = range(-wb, wb + 1)
    neighbors = {}
    for v in itertools.product(domain, repeat=n):
        v = list(v)
        f = threshold(v)
        if f not in neighbors:
            neighbors[f] = set()
        for i in range(n):
            old = v[i]
            for c in domain:
                if c == old: continue
                v[i] = c
                f2 = threshold(v)
                if f2 != f:
                    neighbors[f].add(f2)
            v[i] = old
    return neighbors

def build_mutation_graph(df):
    f_cols = [c for c in df.columns if c.startswith("f_")]
    n = len(f_cols)
    sbf_len = 1 << n

    def sbf_str(val): return str(int(val)).zfill(sbf_len)
    def to_tuple(s): return tuple(int(c) for c in s)
    def to_str(t): return "".join(str(b) for b in t)

    print(f"Précalcul voisinage SBF pour n={n}...", flush=True)
    neighbors = sbf_neighbors(n)

    lookup = {}
    sbf_vecs = []
    for i, row in df.iterrows():
        vec = tuple(sbf_str(row[c]) for c in f_cols)
        sbf_vecs.append(vec)
        lookup[vec] = i

    decomp_cols = sorted((c for c in df.columns if c.startswith("v_")), reverse=True)
    G = nx.Graph()
    for i in range(len(df)):
        G.add_node(i, decomp=tuple(int(x) for x in df[decomp_cols].iloc[i]))

    print("Construction du graphe de mutation...", flush=True)
    for i in range(len(df)):
        vec = sbf_vecs[i]
        for k in range(n):
            fk = to_tuple(vec[k])
            for nbr in neighbors.get(fk, ()):
                query = vec[:k] + (to_str(nbr),) + vec[k+1:]
                j = lookup.get(query)
                if j is not None and j > i:
                    G.add_edge(i, j)

    print(f"Graphe : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes.", flush=True)
    return G, decomp_cols


# ── Layout ────────────────────────────────────────────────────────────────────

def compute_layout(G):
    print("Calcul du layout...", flush=True)
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="sfdp")
    except Exception:
        print("  pygraphviz absent — spring_layout.", flush=True)
        pos = nx.spring_layout(G, seed=42, k=1.5)

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    span = max(xmax - xmin, ymax - ymin) or 1
    margin = 0.04 * span

    return {i: (round((pos[i][0] - xmin + margin) / (span + 2*margin), 5),
                round((pos[i][1] - ymin + margin) / (span + 2*margin), 5))
            for i in G.nodes()}


# ── HTML generation ───────────────────────────────────────────────────────────

def generate_html(G, df, pos, decomp_cols):
    extra_cols = [c for c in ['AtrSize', 'R_P_mean', 'R_P_std', 'E_P', 'GenotypeCount']
                  if c in df.columns]

    nodes_data = []
    for i in range(len(df)):
        row = df.iloc[i]
        nd = {'x': pos[i][0], 'y': pos[i][1],
              'dc': list(G.nodes[i]['decomp']),
              'dg': G.degree(i)}
        for c in extra_cols:
            try:
                nd[c] = round(float(row[c]), 4)
            except (ValueError, TypeError):
                nd[c] = 0
        nodes_data.append(nd)

    adj_data = [sorted(G.neighbors(i)) for i in range(len(df))]

    unique_decomps = sorted(
        set(G.nodes[i]['decomp'] for i in G.nodes()),
        key=lambda d: (sum(d), d)
    )

    data_js = (
        f"const NODES={json.dumps(nodes_data, separators=(',',':'))};\n"
        f"const ADJ={json.dumps(adj_data, separators=(',',':'))};\n"
        f"const DECOMPS={json.dumps([list(d) for d in unique_decomps])};\n"
        f"const XCOLS={json.dumps(extra_cols)};\n"
    )

    return HTML_TEMPLATE.replace("/*__DATA__*/", data_js)


# ── HTML template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Métagraphe mutationnel SBNP</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap');
  :root{--bg:#0f1117;--panel:#161b27;--border:#252d3d;--accent:#4f8ef7;--text:#e2e8f0;--muted:#64748b}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
  header{display:flex;align-items:center;gap:12px;padding:8px 16px;border-bottom:1px solid var(--border);background:var(--panel);flex-shrink:0}
  header h1{font-size:15px;font-weight:500}
  .btn{background:#2d3748;color:var(--text);border:1px solid var(--border);padding:4px 10px;border-radius:6px;font-size:12px;cursor:pointer;font-family:inherit}
  .btn:hover{background:#3d4a5c}
  .btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
  .wrap{flex:1;position:relative;overflow:hidden;cursor:grab}
  .wrap.drag{cursor:grabbing}
  canvas{width:100%;height:100%;display:block}
  .tip{position:absolute;background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:11px;pointer-events:none;display:none;min-width:190px;z-index:10;font-family:'JetBrains Mono',monospace;line-height:1.75;box-shadow:0 4px 20px #0008}
  .tip-row{display:flex;justify-content:space-between;gap:16px}
  .tip-k{color:var(--muted)}
  .tip-v{color:var(--text);font-weight:600}
  .scatter-legend{display:flex;flex-wrap:wrap;gap:5px 16px;padding:5px 16px;background:var(--panel);border-top:1px solid var(--border);flex-shrink:0;font-size:11px;max-height:60px;overflow-y:auto}
  .scatter-legend-item{display:flex;align-items:center;gap:5px;cursor:pointer;user-select:none;transition:opacity .15s}
  .scatter-legend-item:hover{opacity:.75!important}
  .scatter-legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;display:inline-block}
  @keyframes spin{to{transform:rotate(360deg)}}
  .spinning{display:inline-block;animation:spin 1s linear infinite}
</style>
</head>
<body>
<header>
  <h1>Métagraphe mutationnel SBNP</h1>
  <span id="inf" style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted)"></span>
  <span id="loading-indicator" style="font-size:13px;font-weight:600;color:var(--accent);letter-spacing:.05em"></span>
  <div style="margin-left:auto;display:flex;gap:8px">
    <button class="btn active" id="ebtn" onclick="toggleEdges()">Arêtes ✓</button>
    <button class="btn" onclick="resetView()">↺ Vue</button>
  </div>
</header>
<div class="wrap" id="wrap">
  <canvas id="c"></canvas>
  <div class="tip" id="tip"></div>
</div>
<div class="scatter-legend" id="scatter-legend"></div>

<script>
/*__DATA__*/

// ── Couleurs (même logique que sbn_scatter) ───────────────────────────────────
const dcKey = d => d.join(',');
const dcStr = d => '<'+d.join(',')+'>';

function hslToHex(h,s,l){
  const c=(1-Math.abs(2*l-1))*s, x=c*(1-Math.abs((h/60)%2-1)), m=l-c/2;
  let r,g,b;
  if(h<60){r=c;g=x;b=0;}else if(h<120){r=x;g=c;b=0;}else if(h<180){r=0;g=c;b=x;}
  else if(h<240){r=0;g=x;b=c;}else if(h<300){r=x;g=0;b=c;}else{r=c;g=0;b=x;}
  return '#'+[r+m,g+m,b+m].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');
}

// DECOMPS est trié par (sum, lex) côté Python; on assigne les couleurs par rang.
const dcColorMap = new Map();
(function(){
  const total = DECOMPS.length;
  DECOMPS.forEach((d,i)=>{
    const t = total>1 ? Math.pow(i/(total-1), 0.3) : 0;
    const hue = (220 + t*300 + 360) % 360;
    const light = 0.38 + (i%5)*0.04;
    dcColorMap.set(dcKey(d), hslToHex(hue, 0.75, light));
  });
})();

const dcColor = d => dcColorMap.get(dcKey(d)) ?? '#888';
const hidden = new Set();

// Draw order: most common group first (bottom layer), rarest last (top layer).
const _gCnt = new Map(DECOMPS.map(d=>[dcKey(d),0]));
NODES.forEach(n=>{ const k=dcKey(n.dc); _gCnt.set(k,(_gCnt.get(k)||0)+1); });
const DRAW_ORDER = [...DECOMPS].sort((a,b)=>(_gCnt.get(dcKey(b))||0)-(_gCnt.get(dcKey(a))||0));

// ── Canvas ───────────────────────────────────────────────────────────────────
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let W, H;
function resize(){
  const r = document.getElementById('wrap');
  W = canvas.width = r.clientWidth;
  H = canvas.height = r.clientHeight;
}
window.addEventListener('resize', ()=>{resize(); buildEdgeBitmap(); render();});
resize();

// ── State ────────────────────────────────────────────────────────────────────
let panX=0, panY=0, zoom=1;
let drag=false, dx0=0, dy0=0, px0=0, py0=0;
let hov=-1, sel=-1, showEdges=true;
const N = NODES.length;

// ── Coordinate helpers ───────────────────────────────────────────────────────
// World coords are [0,1]x[0,1]; Y is flipped (world y=1 → top of canvas).
const wx = x => panX + x * zoom;
const wy = y => panY + (1-y) * zoom;
const sx = px => (px - panX) / zoom;
const sy = py => 1 - (py - panY) / zoom;

function nodeR(n){ return 2.5 + Math.sqrt(Math.min(n.dg, 60)) * 0.55; }

// ── Edge bitmap ───────────────────────────────────────────────────────────────
// Pre-render all edges once at high resolution; use drawImage for pan/zoom.
const BS = 3000;
let edgeBitmap = null;

function buildEdgeBitmap(){
  const oc = new OffscreenCanvas(BS, BS);
  const bc = oc.getContext('2d');
  bc.strokeStyle = '#5a7fa8';
  bc.globalAlpha = 0.18;
  bc.lineWidth = 0.7;
  bc.beginPath();
  for(let i=0;i<N;i++){
    if(hidden.has(dcKey(NODES[i].dc))) continue;
    const ni=NODES[i];
    for(const j of ADJ[i]){
      if(j<=i) continue;
      if(hidden.has(dcKey(NODES[j].dc))) continue;
      bc.moveTo(ni.x*BS, (1-ni.y)*BS);
      bc.lineTo(NODES[j].x*BS, (1-NODES[j].y)*BS);
    }
  }
  bc.stroke();
  edgeBitmap = oc;
}

// ── Render ────────────────────────────────────────────────────────────────────
function render(){
  ctx.clearRect(0,0,W,H);

  // Edge bitmap (fast drawImage)
  if(showEdges && edgeBitmap){
    ctx.drawImage(edgeBitmap, 0,0,BS,BS, panX,panY,zoom,zoom);
  }

  // Nodes: most-common group first (bottom layer), rarest last (top layer).
  for(const dc of DRAW_ORDER){
    const key = dcKey(dc);
    if(hidden.has(key)) continue;
    const col = dcColor(dc);
    ctx.fillStyle = col;
    ctx.globalAlpha = 0.88;
    for(let i=0;i<N;i++){
      if(dcKey(NODES[i].dc)!==key || i===hov || i===sel) continue;
      const r=nodeR(NODES[i]);
      ctx.beginPath();
      ctx.arc(wx(NODES[i].x), wy(NODES[i].y), r, 0, 6.283);
      ctx.fill();
    }
  }
  ctx.globalAlpha = 1;

  // Focus node (hov or sel)
  const focus = sel!==-1 ? sel : hov;
  if(focus!==-1){
    // Highlighted edges
    if(showEdges){
      ctx.save();
      ctx.strokeStyle='#4f8ef7';
      ctx.globalAlpha=0.65;
      ctx.lineWidth=1.3;
      ctx.beginPath();
      const fn=NODES[focus];
      for(const j of ADJ[focus]){
        ctx.moveTo(wx(fn.x),wy(fn.y));
        ctx.lineTo(wx(NODES[j].x),wy(NODES[j].y));
      }
      ctx.stroke();
      ctx.restore();
    }
    // Neighbors slightly enlarged
    for(const j of ADJ[focus]){
      const nj=NODES[j];
      ctx.fillStyle=dcColor(nj.dc);
      ctx.globalAlpha=1;
      const r=nodeR(nj)+2;
      ctx.beginPath(); ctx.arc(wx(nj.x),wy(nj.y),r,0,6.283); ctx.fill();
    }
    // Focused node: white ring + color fill
    const fn=NODES[focus];
    ctx.fillStyle='#fff'; ctx.globalAlpha=1;
    ctx.beginPath(); ctx.arc(wx(fn.x),wy(fn.y),nodeR(fn)+3,0,6.283); ctx.fill();
    ctx.fillStyle=dcColor(fn.dc);
    ctx.beginPath(); ctx.arc(wx(fn.x),wy(fn.y),nodeR(fn),0,6.283); ctx.fill();
  }
  ctx.globalAlpha=1;
}

// ── Spatial grid for hover ────────────────────────────────────────────────────
const GS=60;
const grid=new Map();
for(let i=0;i<N;i++){
  const gx=Math.floor(NODES[i].x*GS), gy=Math.floor(NODES[i].y*GS);
  const k=`${gx},${gy}`;
  if(!grid.has(k)) grid.set(k,[]);
  grid.get(k).push(i);
}

function nearest(px,py){
  const wx_=sx(px), wy_=sy(py);
  const r=Math.min(18/zoom, 0.4);  // cap: don't scan the whole world when zoomed out
  let best=-1, bd2=r*r;
  const gx0=Math.floor((wx_-r)*GS), gx1=Math.floor((wx_+r)*GS);
  const gy0=Math.floor((wy_-r)*GS), gy1=Math.floor((wy_+r)*GS);
  for(let gx=gx0;gx<=gx1;gx++) for(let gy=gy0;gy<=gy1;gy++){
    const c=grid.get(`${gx},${gy}`);
    if(!c) continue;
    for(const i of c){
      if(hidden.has(dcKey(NODES[i].dc))) continue;
      const ddx=NODES[i].x-wx_, ddy=NODES[i].y-wy_, d2=ddx*ddx+ddy*ddy;
      if(d2<bd2){bd2=d2;best=i;}
    }
  }
  return best;
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
function row(k,v){return `<div class="tip-row"><span class="tip-k">${k}</span><span class="tip-v">${v}</span></div>`;}
function showTip(i,ex,ey){
  const n=NODES[i];
  let h=row('id',i)+row('decomp','('+n.dc.join(', ')+')')+row('degré',n.dg);
  for(const c of XCOLS) if(n[c]!==undefined) h+=row(c,n[c]);
  const tip=document.getElementById('tip');
  tip.innerHTML=h; tip.style.display='block';
  const wr=document.getElementById('wrap').getBoundingClientRect();
  tip.style.left=Math.min(ex+16, wr.width-200)+'px';
  tip.style.top=Math.min(ey+16, wr.height-160)+'px';
}
function hideTip(){document.getElementById('tip').style.display='none';}

// ── Events ────────────────────────────────────────────────────────────────────
const wrap=document.getElementById('wrap');
wrap.addEventListener('mousedown',e=>{
  drag=true; dx0=e.clientX; dy0=e.clientY; px0=panX; py0=panY;
  wrap.classList.add('drag');
});
window.addEventListener('mouseup',()=>{drag=false;wrap.classList.remove('drag');});
window.addEventListener('mousemove',e=>{
  const rect=canvas.getBoundingClientRect();
  const pr=canvas.width/rect.width;
  const cpx=(e.clientX-rect.left)*pr, cpy=(e.clientY-rect.top)*pr;
  if(drag){
    panX=px0+(e.clientX-dx0)*pr; panY=py0+(e.clientY-dy0)*pr;
    render(); return;
  }
  const n=nearest(cpx,cpy);
  if(n!==hov){
    hov=n; render();
    if(n!==-1) showTip(n, e.clientX-rect.left, e.clientY-rect.top);
    else hideTip();
  }
});
wrap.addEventListener('click',e=>{
  const rect=canvas.getBoundingClientRect();
  const pr=canvas.width/rect.width;
  const cpx=(e.clientX-rect.left)*pr, cpy=(e.clientY-rect.top)*pr;
  const n=nearest(cpx,cpy);
  sel=(n===sel)?-1:n; render();
});
wrap.addEventListener('wheel',e=>{
  e.preventDefault();
  const rect=canvas.getBoundingClientRect();
  const pr=canvas.width/rect.width;
  const cpx=(e.clientX-rect.left)*pr, cpy=(e.clientY-rect.top)*pr;
  const f=e.deltaY<0?1.15:1/1.15;
  panX=cpx-(cpx-panX)*f; panY=cpy-(cpy-panY)*f; zoom*=f;
  render();
},{passive:false});

// ── Controls ──────────────────────────────────────────────────────────────────
function toggleEdges(){
  showEdges=!showEdges;
  const b=document.getElementById('ebtn');
  b.textContent=showEdges?'Arêtes ✓':'Arêtes ✗';
  b.classList.toggle('active',showEdges);
  render();
}
function resetView(){
  zoom=Math.min(W,H)*0.92; panX=(W-zoom)/2; panY=(H-zoom)/2;
  render();
}

// ── Legend ────────────────────────────────────────────────────────────────────
function buildLegend(){
  const bar=document.getElementById('scatter-legend');
  bar.innerHTML = DECOMPS.map(d=>{
    const key=dcKey(d), col=dcColor(d);
    const cnt=_gCnt.get(key)||0;
    const active=!hidden.has(key);
    return `<span class="scatter-legend-item" onclick="toggleVec('${key}')"
             data-vec="${key}" style="opacity:${active?1:0.3}">
      <span class="scatter-legend-dot" style="background:${col}"></span>
      <span style="color:var(--text)">${dcStr(d)}</span>
    </span>`;
  }).join('');
}
function toggleVec(key){
  if(hidden.has(key)){hidden.delete(key);}else{hidden.add(key);}
  document.querySelectorAll('.scatter-legend-item[data-vec]').forEach(el=>{
    const v=el.getAttribute('data-vec');
    el.style.opacity=hidden.has(v)?'0.3':'1';
  });
  buildEdgeBitmap(); render();
}

// ── Info ──────────────────────────────────────────────────────────────────────
const nEdges=ADJ.reduce((s,a)=>s+a.length,0)>>1;
document.getElementById('inf').textContent=`${N} nœuds · ${nEdges} arêtes`;

// ── Init ──────────────────────────────────────────────────────────────────────
buildLegend();
document.getElementById('loading-indicator').innerHTML='<span class="spinning">⟳</span> building edges…';
setTimeout(()=>{
  buildEdgeBitmap();
  document.getElementById('loading-indicator').textContent='';
  resetView();
},0);
</script>
</body>
</html>
"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sbnps_csv", help="CSV de la pipeline (colonnes f_*, v_*)")
    parser.add_argument("--out", default="metagraphe_interactif.html")
    args = parser.parse_args()

    print(f"Lecture de {args.sbnps_csv} ...", flush=True)
    df = pd.read_csv(args.sbnps_csv)
    print(f"{len(df)} SBNPs chargés.", flush=True)

    G, decomp_cols = build_mutation_graph(df)
    pos = compute_layout(G)
    html = generate_html(G, df, pos, decomp_cols)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML généré : {args.out}", flush=True)


if __name__ == "__main__":
    main()
