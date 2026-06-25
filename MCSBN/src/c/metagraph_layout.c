/*
 * metagraph_layout.c — port C des passes Python de add_metagraph_layout.py.
 *
 * Prend un CSV (ou .csv.gz) genere par mcsbn et lui ajoute les colonnes
 * metagraph_x, metagraph_y : la position 2D de chaque dynamique dans le
 * metagraphe (cf. metagraphe.html / add_metagraph_layout.py).
 *
 *   - noeud  = dynamique distincte (signature f_1..f_n) ;
 *   - arete  = deux dynamiques ne differant que sur une colonne f_k, vers un
 *              SBF voisin (mutation d'un poids ; relation symetrique).
 *
 * Le layout 2D est delegue au binaire DRGraph (Vis). On rapporte aussi la
 * structure en composantes connexes (union-find) : c'est l'info clef pour
 * juger si une couverture donnee fait emerger une composante geante.
 *
 * Limite : n <= 4 (signature empaquetee sur 64 bits = n * 2^n bits ; pour
 * n=4 c'est 4*16=64). Au-dela le metagraphe est de toute facon trop creux
 * pour etre instructif.
 *
 * Compilation : voir la cible `metalayout` du Makefile.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <zlib.h>

typedef uint32_t u32;
typedef uint64_t u64;

#define EMPTY_ID 0xFFFFFFFFu

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static int wbound(int n) {
    if (n <= 2) return 1;
    if (n == 3) return 2;
    if (n == 4) return 3;
    return n;
}

/* Table de verite (bit s = f(s)) de la SBF de colonne `col` en dimension k. */
static u64 threshold_tt(const int *col, int k) {
    u64 tt = 0;
    for (int s = 0; s < (1 << k); s++) {
        int sum = 0;
        for (int i = 0; i < k; i++) if (s & (1 << i)) sum += col[i];
        if (sum > 0) tt |= (u64)1 << s;
    }
    return tt;
}

static u64 splitmix(u64 x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31);
}

/* ─────────────────────────────────────────────────────────────────────────
 * Carte des voisins SBF (n <= 4 -> tt < 2^16). nbr[tt] = liste des tt voisins.
 * ───────────────────────────────────────────────────────────────────────── */
static u32 *nbr_buf;        /* concatenation des listes de voisins */
static u32  nbr_off[65537]; /* offsets : voisins de tt = nbr_buf[off[tt]..off[tt+1]) */

static int cmp_u32(const void *a, const void *b) {
    u32 x = *(const u32 *)a, y = *(const u32 *)b;
    return (x > y) - (x < y);
}

static void build_neighbor_map(int n) {
    int wb = wbound(n);
    int ds = 2 * wb + 1;
    long ncols = 1; for (int i = 0; i < n; i++) ncols *= ds;

    /* 1ere passe : compter les voisins (avec doublons) par tt */
    static u32 cnt[65536];
    memset(cnt, 0, sizeof(cnt));
    int col[8];
    /* on stocke temporairement toutes les paires puis on trie/dedoublonne */
    /* borne : ncols * n * (ds-1) */
    long maxpairs = ncols * n * (ds - 1);
    u32 *src = malloc(sizeof(u32) * maxpairs);
    u32 *dst = malloc(sizeof(u32) * maxpairs);
    long np = 0;

    for (long idx = 0; idx < ncols; idx++) {
        long r = idx;
        for (int i = 0; i < n; i++) { col[i] = (int)(r % ds) - wb; r /= ds; }
        u64 f = threshold_tt(col, n);
        for (int i = 0; i < n; i++) {
            int old = col[i];
            for (int c = -wb; c <= wb; c++) {
                if (c == old) continue;
                col[i] = c;
                u64 f2 = threshold_tt(col, n);
                if (f2 != f) { src[np] = (u32)f; dst[np] = (u32)f2; np++; }
            }
            col[i] = old;
        }
    }
    /* compte par source */
    for (long p = 0; p < np; p++) cnt[src[p]]++;
    /* offsets */
    u32 acc = 0;
    for (int t = 0; t < 65536; t++) { nbr_off[t] = acc; acc += cnt[t]; }
    nbr_off[65536] = acc;
    nbr_buf = malloc(sizeof(u32) * acc);
    /* remplissage */
    static u32 cur[65536];
    memcpy(cur, nbr_off, sizeof(cur));
    for (long p = 0; p < np; p++) nbr_buf[cur[src[p]]++] = dst[p];
    /* tri + dedoublonnage par source, on compacte en place */
    u32 w = 0;
    for (int t = 0; t < 65536; t++) {
        u32 a = nbr_off[t], b = nbr_off[t + 1];
        nbr_off[t] = w;
        if (b > a) {
            qsort(nbr_buf + a, b - a, sizeof(u32), cmp_u32);
            u32 last = nbr_buf[a]; nbr_buf[w++] = last;
            for (u32 j = a + 1; j < b; j++)
                if (nbr_buf[j] != last) { last = nbr_buf[j]; nbr_buf[w++] = last; }
        }
    }
    nbr_off[65536] = w;
    free(src); free(dst);
}

/* ─────────────────────────────────────────────────────────────────────────
 * Table de hachage signature(u64) -> node id (open addressing).
 * ───────────────────────────────────────────────────────────────────────── */
static u64 *h_key;
static u32 *h_id;
static u32  h_cap, h_mask;
static u64 *node_sig;   /* signature par node id */
static u32  n_nodes, node_cap;

static void hash_init(u32 cap_pow2) {
    h_cap = cap_pow2; h_mask = cap_pow2 - 1;
    h_key = malloc(sizeof(u64) * h_cap);
    h_id  = malloc(sizeof(u32) * h_cap);
    for (u32 i = 0; i < h_cap; i++) h_id[i] = EMPTY_ID;
    node_cap = 1 << 20;
    node_sig = malloc(sizeof(u64) * node_cap);
    n_nodes = 0;
}

static void hash_grow(void);

/* Insere sig si absent, retourne son node id. */
static u32 hash_intern(u64 sig) {
    if ((n_nodes + 1) * 4 >= h_cap * 3) hash_grow();
    u32 i = (u32)splitmix(sig) & h_mask;
    while (h_id[i] != EMPTY_ID) {
        if (h_key[i] == sig) return h_id[i];
        i = (i + 1) & h_mask;
    }
    if (n_nodes == node_cap) {
        node_cap *= 2; node_sig = realloc(node_sig, sizeof(u64) * node_cap);
    }
    u32 id = n_nodes++;
    node_sig[id] = sig;
    h_key[i] = sig; h_id[i] = id;
    return id;
}

/* Recherche seule, EMPTY_ID si absent. */
static u32 hash_find(u64 sig) {
    u32 i = (u32)splitmix(sig) & h_mask;
    while (h_id[i] != EMPTY_ID) {
        if (h_key[i] == sig) return h_id[i];
        i = (i + 1) & h_mask;
    }
    return EMPTY_ID;
}

static void hash_grow(void) {
    u32 old_cap = h_cap;
    u64 *ok = h_key; u32 *oi = h_id;
    h_cap *= 2; h_mask = h_cap - 1;
    h_key = malloc(sizeof(u64) * h_cap);
    h_id  = malloc(sizeof(u32) * h_cap);
    for (u32 i = 0; i < h_cap; i++) h_id[i] = EMPTY_ID;
    for (u32 j = 0; j < old_cap; j++) {
        if (oi[j] == EMPTY_ID) continue;
        u32 i = (u32)splitmix(ok[j]) & h_mask;
        while (h_id[i] != EMPTY_ID) i = (i + 1) & h_mask;
        h_key[i] = ok[j]; h_id[i] = oi[j];
    }
    free(ok); free(oi);
}

/* ─────────────────────────────────────────────────────────────────────────
 * Lecture CSV : entete (quote-aware) + extraction des champs f_k par index.
 * ───────────────────────────────────────────────────────────────────────── */
static int f_field[8];   /* index de colonne de f_1..f_n */
static int n_f;          /* = n */
static int bits;         /* = 2^n */

/* Repere les colonnes f_k dans la ligne d'entete. Retourne n, ou 0 si absent. */
static int parse_header(const char *line) {
    /* split quote-aware ; un champ "f_3" ou f_3 */
    int field = 0, maxk = 0;
    int fpos[16]; for (int i = 0; i < 16; i++) fpos[i] = -1;
    const char *p = line;
    char buf[64];
    while (*p) {
        int q = 0, bl = 0;
        while (*p && (q || (*p != ',' && *p != '\n' && *p != '\r'))) {
            if (*p == '"') { q = !q; p++; continue; }
            if (bl < 63) buf[bl++] = *p;
            p++;
        }
        buf[bl] = 0;
        int k;
        if (sscanf(buf, "f_%d", &k) == 1 && k >= 1 && k <= 15) {
            fpos[k] = field; if (k > maxk) maxk = k;
        }
        if (*p == ',') { p++; field++; }
        else break;
    }
    if (maxk == 0) return 0;
    for (int k = 1; k <= maxk; k++) if (fpos[k] < 0) return 0; /* non contigu */
    n_f = maxk;
    for (int k = 1; k <= maxk; k++) f_field[k - 1] = fpos[k];
    return maxk;
}

/* Calcule la signature (u64) d'une ligne de donnees a partir des champs f_k.
 * Les lignes de donnees ne contiennent pas de virgule entre guillemets, on
 * marche donc simplement les virgules. Retourne 0 si ok, -1 si ligne courte. */
static int line_signature(const char *line, u64 *out) {
    /* on parcourt une fois, en capturant les champs voulus */
    int want = 0;                 /* prochain f_field a capturer (tries) */
    /* f_field n'est pas forcement trie ; on capte par balayage complet */
    const char *p = line;
    int field = 0;
    u64 sig = 0;
    int got = 0;
    /* pre-tri des index voulus avec leur rang k */
    while (*p && got < n_f) {
        const char *start = p;
        while (*p && *p != ',' && *p != '\n' && *p != '\r') p++;
        int len = (int)(p - start);
        for (int k = 0; k < n_f; k++) {
            if (f_field[k] == field) {
                if (len != bits) return -1;
                u64 tt = 0;
                for (int s = 0; s < bits; s++)
                    if (start[s] == '1') tt |= (u64)1 << s;
                sig |= tt << (k * bits);
                got++;
                break;
            }
        }
        if (*p == ',') { p++; field++; }
        else break;
    }
    (void)want;
    if (got < n_f) return -1;
    *out = sig;
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Union-find pour les composantes connexes.
 * ───────────────────────────────────────────────────────────────────────── */
static u32 *uf_parent, *uf_rank;
static u32 uf_find(u32 x) {
    while (uf_parent[x] != x) { uf_parent[x] = uf_parent[uf_parent[x]]; x = uf_parent[x]; }
    return x;
}
static void uf_union(u32 a, u32 b) {
    a = uf_find(a); b = uf_find(b);
    if (a == b) return;
    if (uf_rank[a] < uf_rank[b]) { u32 t = a; a = b; b = t; }
    uf_parent[b] = a;
    if (uf_rank[a] == uf_rank[b]) uf_rank[a]++;
}

/* ───────────────────────────────────────────────────────────────────────── */
int main(int argc, char **argv) {
    const char *in_path = NULL, *out_path = NULL, *vis_bin = NULL;
    int neg = 5, samples = 400, mode = 1;
    double gamma = 0.1, A = 2.0, B = 1.0;
    int do_write = 1, verbose = 0;

    for (int i = 1; i < argc; i++) {
        if      (!strcmp(argv[i], "-o"))        out_path = argv[++i];
        else if (!strcmp(argv[i], "--vis"))     vis_bin  = argv[++i];
        else if (!strcmp(argv[i], "--neg"))     neg      = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--samples")) samples  = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--gamma"))   gamma    = atof(argv[++i]);
        else if (!strcmp(argv[i], "--mode"))    mode     = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--A"))       A        = atof(argv[++i]);
        else if (!strcmp(argv[i], "--B"))       B        = atof(argv[++i]);
        else if (!strcmp(argv[i], "--stats-only")) do_write = 0;
        else if (!strcmp(argv[i], "-v"))        verbose  = 1;
        else if (argv[i][0] != '-')             in_path  = argv[i];
    }
    if (!in_path) { fprintf(stderr, "usage: %s in.csv[.gz] [-o out] [--stats-only] [opts DRGraph]\n", argv[0]); return 1; }

    double t0 = now();

    /* --- entete --- */
    gzFile in = gzopen(in_path, "rb");
    if (!in) { fprintf(stderr, "ouverture impossible: %s\n", in_path); return 1; }
    /* grand buffer ligne (bitstrings + poids + stats) */
    int LBUF = 1 << 20;
    char *line = malloc(LBUF);
    if (!gzgets(in, line, LBUF)) { fprintf(stderr, "CSV vide\n"); return 1; }
    int n = parse_header(line);
    if (n == 0) { fprintf(stderr, "CSV sans colonnes f_* (genere sans --no-weights ?)\n"); return 1; }
    if (n > 4) { fprintf(stderr, "n=%d non supporte (signature > 64 bits) ; n<=4.\n", n); return 1; }
    bits = 1 << n;

    fprintf(stderr, "[1/4] lecture + deduplication des dynamiques (n=%d) ...\n", n);
    hash_init(1u << 22);
    long n_rows = 0;
    while (gzgets(in, line, LBUF)) {
        if (line[0] == '\n' || line[0] == 0) continue;
        u64 sig;
        if (line_signature(line, &sig) != 0) { fprintf(stderr, "ligne %ld invalide\n", n_rows + 1); return 1; }
        hash_intern(sig);
        n_rows++;
    }
    gzclose(in);
    fprintf(stderr, "      lignes=%ld  noeuds(distincts)=%u  (%.1fs)\n",
            n_rows, n_nodes, now() - t0);

    /* --- aretes --- */
    fprintf(stderr, "[2/4] construction des aretes ...\n");
    build_neighbor_map(n);
    u64 mask = ((u64)1 << bits) - 1;
    size_t edge_cap = 1 << 20, n_edges = 0;
    u32 *edges = malloc(sizeof(u32) * 2 * edge_cap);
    for (u32 i = 0; i < n_nodes; i++) {
        u64 sig = node_sig[i];
        for (int k = 0; k < n; k++) {
            u32 base = (u32)((sig >> (k * bits)) & mask);
            u64 cleared = sig & ~(mask << (k * bits));
            for (u32 o = nbr_off[base]; o < nbr_off[base + 1]; o++) {
                u64 cand = cleared | ((u64)nbr_buf[o] << (k * bits));
                u32 j = hash_find(cand);
                if (j != EMPTY_ID && j > i) {
                    if (n_edges == edge_cap) {
                        edge_cap *= 2; edges = realloc(edges, sizeof(u32) * 2 * edge_cap);
                    }
                    edges[2 * n_edges] = i; edges[2 * n_edges + 1] = j; n_edges++;
                }
            }
        }
    }
    fprintf(stderr, "      aretes=%zu  (%.1fs)\n", n_edges, now() - t0);

    /* --- composantes connexes --- */
    uf_parent = malloc(sizeof(u32) * n_nodes);
    uf_rank   = calloc(n_nodes, sizeof(u32));
    for (u32 i = 0; i < n_nodes; i++) uf_parent[i] = i;
    for (size_t e = 0; e < n_edges; e++) uf_union(edges[2 * e], edges[2 * e + 1]);
    u32 *csize = calloc(n_nodes, sizeof(u32));
    for (u32 i = 0; i < n_nodes; i++) csize[uf_find(i)]++;
    u32 ncomp = 0, largest = 0, isolated = 0;
    for (u32 i = 0; i < n_nodes; i++) if (csize[i]) {
        ncomp++; if (csize[i] > largest) largest = csize[i];
        if (csize[i] == 1) isolated++;
    }
    fprintf(stderr, "      composantes=%u  plus_grande=%u (%.4f%%)  isoles=%u (%.2f%%)\n",
            ncomp, largest, 100.0 * largest / n_nodes,
            isolated, 100.0 * isolated / n_nodes);
    fprintf(stderr, "      degre_moyen=%.4f\n", 2.0 * n_edges / n_nodes);
    free(uf_rank); free(csize);

    if (!do_write) { fprintf(stderr, "[stats-only] termine (%.1fs)\n", now() - t0); return 0; }

    /* --- layout DRGraph --- */
    fprintf(stderr, "[3/4] layout DRGraph ...\n");
    float *cx = malloc(sizeof(float) * n_nodes);
    float *cy = malloc(sizeof(float) * n_nodes);
    if (n_nodes <= 2 || n_edges == 0) {
        fprintf(stderr, "      graphe trivial/sans arete -> cercle de secours.\n");
        for (u32 i = 0; i < n_nodes; i++) {
            double a = n_nodes > 1 ? 2 * M_PI * i / n_nodes : 0;
            cx[i] = (float)cos(a); cy[i] = (float)sin(a);
        }
    } else {
        char dir[] = "/tmp/mcsbn_meta_XXXXXX";
        if (!mkdtemp(dir)) { perror("mkdtemp"); return 1; }
        char gpath[256], lpath[256];
        snprintf(gpath, sizeof(gpath), "%s/graph.txt", dir);
        snprintf(lpath, sizeof(lpath), "%s/layout.txt", dir);
        FILE *gf = fopen(gpath, "w");
        fprintf(gf, "%u %zu\n", n_nodes, n_edges);
        for (size_t e = 0; e < n_edges; e++)
            fprintf(gf, "%u %u 1\n", edges[2 * e], edges[2 * e + 1]);
        fclose(gf);

        const char *vis = vis_bin ? vis_bin : getenv("MCSBN_VIS");
        char vbuf[512];
        if (!vis) {
            /* defaut : tools/DRGraph/Vis relatif a l'executable courant */
            snprintf(vbuf, sizeof(vbuf), "tools/DRGraph/Vis");
            vis = vbuf;
        }
        char cmd[1200];
        snprintf(cmd, sizeof(cmd),
                 "%s -input %s -output %s -neg %d -samples %d -gamma %g -mode %d -A %g -B %g%s",
                 vis, gpath, lpath, neg, samples, gamma, mode, A, B,
                 verbose ? "" : " >/dev/null 2>&1");
        if (verbose) fprintf(stderr, "      %s\n", cmd);
        int rc = system(cmd);
        FILE *lf = fopen(lpath, "r");
        if (rc != 0 || !lf) { fprintf(stderr, "DRGraph (Vis) a echoue (rc=%d). Vis introuvable ? --vis <chemin>\n", rc); return 1; }
        u32 cnt, dim;
        if (fscanf(lf, "%u %u", &cnt, &dim) != 2) { fprintf(stderr, "layout illisible\n"); return 1; }
        for (u32 i = 0; i < n_nodes; i++) { cx[i] = 0; cy[i] = 0; }
        for (u32 i = 0; i < cnt && i < n_nodes; i++) {
            double x = 0, y = 0; if (fscanf(lf, "%lf %lf", &x, &y) != 2) break;
            cx[i] = (float)x; cy[i] = (float)y;
        }
        fclose(lf);
        unlink(gpath); unlink(lpath); rmdir(dir);
    }
    fprintf(stderr, "      ok (%.1fs)\n", now() - t0);

    /* --- reecriture du CSV (pass 2) --- */
    fprintf(stderr, "[4/4] reecriture -> %s\n", out_path ? out_path : "(stdout)");
    in = gzopen(in_path, "rb");
    gzgets(in, line, LBUF); /* entete */
    int gz_out = out_path && strlen(out_path) > 3 && !strcmp(out_path + strlen(out_path) - 3, ".gz");
    gzFile outz = NULL; FILE *outf = NULL;
    if (!out_path) outf = stdout;
    else if (gz_out) outz = gzopen(out_path, "wb");
    else outf = fopen(out_path, "w");
    if ((gz_out && !outz) || (!gz_out && !outf)) { fprintf(stderr, "sortie impossible\n"); return 1; }

    /* entete + nouvelles colonnes */
    char hdr[1 << 20];
    int hl = (int)strlen(line);
    while (hl > 0 && (line[hl-1] == '\n' || line[hl-1] == '\r')) hl--;
    memcpy(hdr, line, hl); hl += snprintf(hdr + hl, 64, ",metagraph_x,metagraph_y\n");
    if (gz_out) gzwrite(outz, hdr, hl); else fwrite(hdr, 1, hl, outf);

    char tail[64];
    while (gzgets(in, line, LBUF)) {
        if (line[0] == '\n' || line[0] == 0) continue;
        u64 sig; line_signature(line, &sig);
        u32 id = hash_find(sig);
        int ll = (int)strlen(line);
        while (ll > 0 && (line[ll-1] == '\n' || line[ll-1] == '\r')) ll--;
        int tl = snprintf(tail, sizeof(tail), ",%.6g,%.6g\n", cx[id], cy[id]);
        if (gz_out) { gzwrite(outz, line, ll); gzwrite(outz, tail, tl); }
        else { fwrite(line, 1, ll, outf); fwrite(tail, 1, tl, outf); }
    }
    gzclose(in);
    if (gz_out) gzclose(outz); else if (outf != stdout) fclose(outf);
    fprintf(stderr, "OK (%.1fs)\n", now() - t0);
    return 0;
}
