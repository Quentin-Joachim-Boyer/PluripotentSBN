/*
 * mcsbn.c — Generateur Monte-Carlo de SBN (version rapide en C).
 *
 * Replique a l'identique la logique validee de la version Python (sbf.py,
 * decompose.py, mcsbn.py) : meme table SBF, memes statistiques, meme
 * decomposition "sous controle" (inegalites exactes sur la matrice de poids
 * echantillonnee). La sortie CSV est byte-pour-byte comparable.
 *
 * Compilation (depuis la racine MCSBN) :
 *   make            # -> ./bin/mcsbn
 *   gcc -O3 -march=native -fopenmp -o bin/mcsbn src/c/mcsbn.c -lm -lz
 *
 * Voir le README et `./bin/mcsbn --help`.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <immintrin.h>
#include <omp.h>
#include <zlib.h>
#ifdef _WIN32
  #include <io.h>
  #define MCSBN_ISATTY(fp) _isatty(_fileno(fp))
#else
  #include <unistd.h>
  #define MCSBN_ISATTY(fp) isatty(fileno(fp))
#endif

typedef uint64_t u64;
typedef uint32_t u32;
typedef unsigned __int128 u128;

/* ------------------------------------------------------------------ RNG --- */
static u64 rng_s[4];
static inline u64 rotl(u64 x, int k) { return (x << k) | (x >> (64 - k)); }
static u64 splitmix64(u64 *x) {
    u64 z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static void rng_seed(u64 seed) {
    u64 sm = seed;
    for (int i = 0; i < 4; i++) rng_s[i] = splitmix64(&sm);
}
static inline u64 rng_next(void) {
    u64 r = rotl(rng_s[1] * 5, 7) * 9;
    u64 t = rng_s[1] << 17;
    rng_s[2] ^= rng_s[0]; rng_s[3] ^= rng_s[1];
    rng_s[1] ^= rng_s[2]; rng_s[0] ^= rng_s[3];
    rng_s[2] ^= t; rng_s[3] = rotl(rng_s[3], 45);
    return r;
}
/* entier uniforme dans [0, bound) (Lemire, biais negligeable) */
static inline u32 rng_below(u32 bound) {
    u32 r = (u32)(rng_next() >> 32);
    return (u32)(((u64)r * bound) >> 32);
}

/* ------------------------------------------------------- parametres globaux */
static int n, N, wb, domain_size, M;
static u64 *sbf_tt;      /* [M] table de verite de chaque SBF distincte */
static int *repr_col;    /* [M*n] colonne de poids representative */
static u64 *csize;       /* [M] taille de ColumnSet */
static double *nmean;    /* [M] moyenne du compte de voisins neutres */
static double *nvar;     /* [M] variance */
static int *evol;        /* [M] nb de phenotypes voisins distincts */
static double Knorm;     /* constante de normalisation Wagner */

static int wbound(int d) {
    if (d == 1) return 1;
    if (d == 2) return 1;
    if (d == 3) return 2;
    if (d == 4) return 3;
    return d;
}

static inline u64 threshold_tt(const int *col, int k) {
    u64 tt = 0;
    int ns = 1 << k;
    for (int s = 0; s < ns; s++) {
        int sum = 0, ss = s, i = 0;
        while (ss) { if (ss & 1) sum += col[i]; ss >>= 1; i++; }
        if (sum > 0) tt |= (u64)1 << s;
    }
    return tt;
}

/* ----------------------------------------- ensemble de u64 (open addressing)
 * Sentinelle EMPTY = UINT64_MAX : bit 0 de toute table de verite seuil vaut 0
 * (f(0)=0), donc UINT64_MAX n'est jamais une valeur valide. */
#define U64SET_EMPTY (~(u64)0)
typedef struct { u64 *slot; u32 cap, mask, size; } U64Set;
static void u64set_init(U64Set *s, u32 cap_pow2) {
    s->cap = cap_pow2; s->mask = cap_pow2 - 1; s->size = 0;
    s->slot = malloc(sizeof(u64) * cap_pow2);
    memset(s->slot, 0xFF, sizeof(u64) * cap_pow2);
}
static void u64set_grow(U64Set *s);
static inline int u64set_add(U64Set *s, u64 v) { /* retourne 1 si nouveau */
    if ((s->size + 1) * 4 >= s->cap * 3) u64set_grow(s);
    u64 h = (v * 0x9E3779B97F4A7C15ULL) & s->mask;
    while (s->slot[h] != U64SET_EMPTY) {
        if (s->slot[h] == v) return 0;
        h = (h + 1) & s->mask;
    }
    s->slot[h] = v; s->size++; return 1;
}
static inline int u64set_has(const U64Set *s, u64 v) {
    u64 h = (v * 0x9E3779B97F4A7C15ULL) & s->mask;
    while (s->slot[h] != U64SET_EMPTY) {
        if (s->slot[h] == v) return 1;
        h = (h + 1) & s->mask;
    }
    return 0;
}
static void u64set_grow(U64Set *s) {
    u32 oc = s->cap; u64 *os = s->slot;
    u64set_init(s, oc * 2);
    for (u32 i = 0; i < oc; i++) if (os[i] != U64SET_EMPTY) u64set_add(s, os[i]);
    free(os);
}

/* --------------------------------------------------------- table SBF dim n */
/* map tt -> index, et accumulateurs par SBF */
typedef struct { u64 *key; int *val; u32 cap, mask, size; } TtMap;
static void ttmap_init(TtMap *m, u32 cap_pow2) {
    m->cap = cap_pow2; m->mask = cap_pow2 - 1; m->size = 0;
    m->key = malloc(sizeof(u64) * cap_pow2);
    m->val = malloc(sizeof(int) * cap_pow2);
    memset(m->key, 0xFF, sizeof(u64) * cap_pow2);
}
static void ttmap_grow(TtMap *m) {
    u32 oc = m->cap; u64 *ok = m->key; int *ov = m->val;
    ttmap_init(m, oc * 2);
    for (u32 i = 0; i < oc; i++) {
        if (ok[i] == U64SET_EMPTY) continue;
        u64 h = (ok[i] * 0x9E3779B97F4A7C15ULL) & m->mask;
        while (m->key[h] != U64SET_EMPTY) h = (h + 1) & m->mask;
        m->key[h] = ok[i]; m->val[h] = ov[i]; m->size++;
    }
    free(ok); free(ov);
}
static int ttmap_get_or_add(TtMap *m, u64 k, int next_index) {
    if ((m->size + 1) * 4 >= m->cap * 3) ttmap_grow(m);
    u64 h = (k * 0x9E3779B97F4A7C15ULL) & m->mask;
    while (m->key[h] != U64SET_EMPTY) {
        if (m->key[h] == k) return m->val[h];
        h = (h + 1) & m->mask;
    }
    m->key[h] = k; m->val[h] = next_index; m->size++;
    return next_index;
}

static void build_table(void) {
    wb = wbound(n);
    domain_size = 2 * wb + 1;
    Knorm = (double)n * n * (domain_size - 1);

    u64 ncols = 1;
    for (int i = 0; i < n; i++) ncols *= domain_size;

    /* --- Phase A (parallele) : table de verite de base de chaque colonne --- */
    u64 *coltt = malloc(sizeof(u64) * ncols);
    #pragma omp parallel
    {
        int *col = malloc(sizeof(int) * n);
        #pragma omp for schedule(static)
        for (u64 idx = 0; idx < ncols; idx++) {
            u64 rest = idx;
            for (int i = 0; i < n; i++) { col[i] = (int)(rest % domain_size) - wb; rest /= domain_size; }
            u64 tt = 0;
            for (int s = 0; s < N; s++) {
                int v = 0;
                for (int i = 0; i < n; i++) if ((s >> i) & 1) v += col[i];
                if (v > 0) tt |= (u64)1 << s;
            }
            coltt[idx] = tt;
        }
        free(col);
    }

    /* --- Phase B (serie) : indexation des SBF + representant canonique +
     * |ColumnSet| + l'index de SBF de chaque colonne (si_of_col). */
    TtMap map; ttmap_init(&map, 1 << 16);
    u32 cap = 1024;
    sbf_tt = malloc(sizeof(u64) * cap);
    repr_col = malloc(sizeof(int) * cap * n);
    csize = calloc(cap, sizeof(u64));
    u32 *si_of_col = malloc(sizeof(u32) * ncols);
    M = 0;
    int *col = malloc(sizeof(int) * n);
    for (u64 idx = 0; idx < ncols; idx++) {
        u64 tt = coltt[idx];
        u64 rest = idx;
        for (int i = 0; i < n; i++) { col[i] = (int)(rest % domain_size) - wb; rest /= domain_size; }
        int si = ttmap_get_or_add(&map, tt, M);
        if (si == M) {
            if (M >= (int)cap) {
                u32 nc = cap * 2;
                sbf_tt = realloc(sbf_tt, sizeof(u64) * nc);
                repr_col = realloc(repr_col, sizeof(int) * nc * n);
                csize = realloc(csize, sizeof(u64) * nc); memset(csize + cap, 0, sizeof(u64) * (nc - cap));
                cap = nc;
            }
            sbf_tt[M] = tt;
            for (int i = 0; i < n; i++) repr_col[M * n + i] = col[i];
            M++;
        } else {
            int *rc = repr_col + si * n, smaller = 0;
            for (int i = 0; i < n; i++) { if (col[i] != rc[i]) { smaller = col[i] < rc[i]; break; } }
            if (smaller) for (int i = 0; i < n; i++) rc[i] = col[i];
        }
        si_of_col[idx] = si;
        csize[si]++;
    }
    free(col);

    /* Regroupe les indices de colonnes par SBF (tri par comptage), pour que la
     * phase C attribue chaque SBF a UN seul thread : aucun verrou ni atomique. */
    u64 *off = malloc(sizeof(u64) * (M + 1));
    off[0] = 0;
    for (int f = 0; f < M; f++) off[f + 1] = off[f] + csize[f];
    u32 *col_of_sbf = malloc(sizeof(u32) * ncols);
    u64 *cur = malloc(sizeof(u64) * M);
    memcpy(cur, off, sizeof(u64) * M);
    for (u64 idx = 0; idx < ncols; idx++) col_of_sbf[cur[si_of_col[idx]]++] = (u32)idx;
    free(cur); free(si_of_col); free(map.key); free(map.val);

    /* --- Phase C (parallele, partitionnee par SBF) : voisins neutres +
     * phenotypes voisins. Chaque SBF est traitee par un seul thread, donc son
     * ensemble de voisins et ses accumulateurs sont prives : pas de contention. */
    double *nsum = calloc(M, sizeof(double));
    double *nsq = calloc(M, sizeof(double));
    nmean = malloc(sizeof(double) * M);
    nvar = malloc(sizeof(double) * M);
    evol = malloc(sizeof(int) * M);

    #pragma omp parallel
    {
        int *colb = malloc(sizeof(int) * n);
        int *ssum = malloc(sizeof(int) * N);
        U64Set neigh; u64set_init(&neigh, 64);
        #pragma omp for schedule(dynamic, 64)
        for (int f = 0; f < M; f++) {
            neigh.size = 0; memset(neigh.slot, 0xFF, sizeof(u64) * neigh.cap);
            u64 tt = sbf_tt[f];
            double sums = 0, sqs = 0;
            for (u64 p = off[f]; p < off[f + 1]; p++) {
                u64 idx = col_of_sbf[p], rest = idx;
                for (int i = 0; i < n; i++) { colb[i] = (int)(rest % domain_size) - wb; rest /= domain_size; }
                for (int s = 0; s < N; s++) {
                    int v = 0;
                    for (int i = 0; i < n; i++) if ((s >> i) & 1) v += colb[i];
                    ssum[s] = v;
                }
                int neutral = 0;
                for (int i = 0; i < n; i++) {
                    int old = colb[i];
                    for (int cand = -wb; cand <= wb; cand++) {
                        if (cand == old) continue;
                        int delta = cand - old;
                        u64 tt2 = 0;
                        for (int s = 0; s < N; s++) {
                            int v = ((s >> i) & 1) ? ssum[s] + delta : ssum[s];
                            if (v > 0) tt2 |= (u64)1 << s;
                        }
                        if (tt2 == tt) neutral++;
                        else u64set_add(&neigh, tt2);
                    }
                }
                sums += neutral; sqs += (double)neutral * neutral;
            }
            nsum[f] = sums; nsq[f] = sqs;
            double mean = sums / (double)csize[f];
            nmean[f] = mean;
            double var = sqs / (double)csize[f] - mean * mean;
            nvar[f] = var < 0 ? 0 : var;
            evol[f] = neigh.size;
        }
        free(neigh.slot); free(colb); free(ssum);
    }

    free(nsum); free(nsq); free(off); free(col_of_sbf); free(coltt);
}

/* --------------------------------------- cache binaire de la table sur disque */
static int table_load(const char *path) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return 0;
    int fn, magicok = 0; u32 magic;
    if (fread(&magic, 4, 1, fp) == 1 && magic == 0x4D435342u) magicok = 1;
    if (!magicok) { fclose(fp); return 0; }
    fread(&fn, sizeof(int), 1, fp);
    if (fn != n) { fclose(fp); return 0; }
    fread(&wb, sizeof(int), 1, fp);
    fread(&M, sizeof(int), 1, fp);
    domain_size = 2 * wb + 1;
    Knorm = (double)n * n * (domain_size - 1);
    sbf_tt = malloc(sizeof(u64) * M);
    repr_col = malloc(sizeof(int) * M * n);
    csize = malloc(sizeof(u64) * M);
    nmean = malloc(sizeof(double) * M);
    nvar = malloc(sizeof(double) * M);
    evol = malloc(sizeof(int) * M);
    fread(sbf_tt, sizeof(u64), M, fp);
    fread(repr_col, sizeof(int), M * n, fp);
    fread(csize, sizeof(u64), M, fp);
    fread(nmean, sizeof(double), M, fp);
    fread(nvar, sizeof(double), M, fp);
    fread(evol, sizeof(int), M, fp);
    fclose(fp);
    return 1;
}
static void table_save(const char *path) {
    FILE *fp = fopen(path, "wb");
    if (!fp) return;
    u32 magic = 0x4D435342u;
    fwrite(&magic, 4, 1, fp);
    fwrite(&n, sizeof(int), 1, fp);
    fwrite(&wb, sizeof(int), 1, fp);
    fwrite(&M, sizeof(int), 1, fp);
    fwrite(sbf_tt, sizeof(u64), M, fp);
    fwrite(repr_col, sizeof(int), M * n, fp);
    fwrite(csize, sizeof(u64), M, fp);
    fwrite(nmean, sizeof(double), M, fp);
    fwrite(nvar, sizeof(double), M, fp);
    fwrite(evol, sizeof(int), M, fp);
    fclose(fp);
}

/* --------------------------------------------------- keysets de sous-dimension
 * Pour la realisabilite des faces : fonctions seuil de dimension k realisables
 * avec le bound du sommet wb(n). keyset[n] = l'ensemble des sbf_tt. */
static U64Set keyset[8];
static void build_keysets(void) {
    for (int k = 1; k <= n; k++) {
        u64set_init(&keyset[k], 1 << 12);
        if (k == n) { for (int f = 0; f < M; f++) u64set_add(&keyset[k], sbf_tt[f]); continue; }
        int *col = malloc(sizeof(int) * k);
        u64 nc = 1; for (int i = 0; i < k; i++) nc *= (2 * wb + 1);
        for (u64 idx = 0; idx < nc; idx++) {
            u64 rest = idx;
            for (int i = 0; i < k; i++) { col[i] = (int)(rest % (2 * wb + 1)) - wb; rest /= (2 * wb + 1); }
            u64set_add(&keyset[k], threshold_tt(col, k));
        }
        free(col);
    }
}

/* --------------------------------------------------------- decomposition (W) */
static int curW[8][8];     /* W[i][j] poids i->j */
static u64 curf[8];        /* dynamique f[j] */
static signed char memo_status[1 << 12]; /* index = fn*N+fv ; 0 inconnu,1 valide,2 invalide */
static int memo_counts[1 << 12][9];
static int decomp_tbn;   /* 0 = SBN (avec garde de realisabilite), 1 = TBN (sans) */

static int popcnt(int x) { return __builtin_popcount(x); }

/* renvoie 1 si la face (fn,fv) se decompose (remplit out[0..n]), 0 sinon */
static int decompose(int fn, int fv, int *out) {
    int key = fn * N + fv;
    if (memo_status[key] == 1) { memcpy(out, memo_counts[key], sizeof(int) * (n + 1)); return 1; }
    if (memo_status[key] == 2) return 0;

    int free_mask = (~fn) & (N - 1);
    int k = popcnt(free_mask);

    if (k == 0) {
        memset(out, 0, sizeof(int) * (n + 1)); out[0] = 1;
        memo_status[key] = 1; memcpy(memo_counts[key], out, sizeof(int) * (n + 1));
        return 1;
    }

    /* realisabilite : fonction restreinte de chaque noeud libre = SBF dim k.
     * Garde du mode SBN uniquement ; en TBN (PTBN) toute face est une feuille
     * valide (le contexte n'ajoute qu'un biais a une fonction qui reste seuil). */
    if (!decomp_tbn) {
        int ns = 1 << k;   /* etats de la face, indexes par la config libre */
        for (int Nn = 0; Nn < n; Nn++) {
            if (!((free_mask >> Nn) & 1)) continue;
            u64 rtt = 0;
            u64 fN = curf[Nn];
            for (int c = 0; c < ns; c++) {
                int s = fv | (int)_pdep_u64((u64)c, (u64)free_mask);
                if ((fN >> s) & 1) rtt |= (u64)1 << c;
            }
            if (!u64set_has(&keyset[k], rtt)) { memo_status[key] = 2; return 0; }
        }
    }

    /* feuille valide de dimension k */
    int best[9];
    memset(best, 0, sizeof(int) * (n + 1));
    best[k] = 1;

    /* noeuds de controle : inegalites exactes sur W */
    for (int c = 0; c < n; c++) {
        if (!((free_mask >> c) & 1)) continue;
        int offset = 0, sum_pos = 0, sum_neg = 0;
        for (int on = 0; on < n; on++)
            if (((fn >> on) & 1) && ((fv >> on) & 1)) offset += curW[on][c];
        for (int i = 0; i < n; i++) {
            if (!((free_mask >> i) & 1) || i == c) continue;
            int w = curW[i][c];
            if (w > 0) sum_pos += w; else sum_neg += w;
        }
        if (offset + sum_pos > 0) continue;            /* activable de l'exterieur */
        if (offset + sum_neg + curW[c][c] <= 0) continue; /* desactivable */

        int d0[9], d1[9];
        if (!decompose(fn | (1 << c), fv, d0)) continue;
        if (!decompose(fn | (1 << c), fv | (1 << c), d1)) continue;
        int comb[9];
        for (int t = 0; t <= n; t++) comb[t] = d0[t] + d1[t];
        /* plus fin = plus de feuilles, puis davantage de feuilles de basse dim */
        int sc = 0, sb = 0;
        for (int t = 0; t <= n; t++) { sc += comb[t]; sb += best[t]; }
        int finer = 0;
        if (sc != sb) finer = (sc > sb);
        else { for (int t = 0; t <= n; t++) if (comb[t] != best[t]) { finer = comb[t] > best[t]; break; } }
        if (finer) memcpy(best, comb, sizeof(int) * (n + 1));
    }

    memo_status[key] = 1;
    memcpy(memo_counts[key], best, sizeof(int) * (n + 1));
    memcpy(out, best, sizeof(int) * (n + 1));
    return 1;
}

/* --------------------------------------------------------------- attracteurs */
static int *succ_buf, *state_attr;
static int cycle_lengths(int *lengths) {
    for (int i = 0; i < N; i++) state_attr[i] = -1;
    int nl = 0;
    int *path = succ_buf + N; /* reutilise un tampon */
    for (int start = 0; start < N; start++) {
        if (state_attr[start] != -1) continue;
        int plen = 0, cur = start;
        /* suit la trajectoire ; pos via marquage temporaire dans state_attr=-2-plen ? */
        /* on memorise les positions dans un petit tableau path + recherche lineaire courte */
        while (state_attr[cur] == -1) {
            int found = -1;
            for (int p = 0; p < plen; p++) if (path[p] == cur) { found = p; break; }
            if (found >= 0) { /* nouveau cycle */
                lengths[nl] = plen - found;
                int aid = nl; nl++;
                for (int p = 0; p < plen; p++) state_attr[path[p]] = aid;
                cur = -1; break;
            }
            path[plen++] = cur;
            cur = succ_buf[cur];
        }
        if (cur >= 0) { /* rejoint un bassin connu */
            int a = state_attr[cur];
            for (int p = 0; p < plen; p++) state_attr[path[p]] = a;
        }
    }
    return nl;
}

/* ------------------------------------------------------------ impression u128 */
/* format flottant round-trip (%.17g), avec point decimal garanti pour les
 * valeurs finies non exponentielles (style 1.0). Un seul snprintf : rapide. */
static int fmt_double(double v, char *buf) {
    int l = snprintf(buf, 32, "%.17g", v);
    int has_dot = 0;
    for (int i = 0; i < l; i++) {
        char c = buf[i];
        if (c == '.' || c == 'e' || c == 'E' || c == 'n' || c == 'i') { has_dot = 1; break; }
    }
    if (!has_dot) { buf[l++] = '.'; buf[l++] = '0'; buf[l] = 0; }
    return l;
}

static int u128_to_str(u128 v, char *buf) {
    char tmp[40]; int p = 0;
    if (v == 0) { buf[0] = '0'; buf[1] = 0; return 1; }
    while (v > 0) { tmp[p++] = '0' + (int)(v % 10); v /= 10; }
    for (int i = 0; i < p; i++) buf[i] = tmp[p - 1 - i];
    buf[p] = 0; return p;
}

/* --------------------------------------------------------- dedup des dynamiques
 * cle = n indices de SBF (u32). open addressing, comparaison exacte. */
static u32 *dd_keys; static u64 dd_cap, dd_mask, dd_size;
static void dd_init(u64 cap_pow2) {
    dd_cap = cap_pow2; dd_mask = cap_pow2 - 1; dd_size = 0;
    dd_keys = malloc(sizeof(u32) * cap_pow2 * n);
    memset(dd_keys, 0xFF, sizeof(u32) * cap_pow2 * n);
}
static int dd_add(const u32 *idx) { /* 1 si nouveau */
    u64 h = 1469598103934665603ULL;
    for (int i = 0; i < n; i++) { h ^= idx[i]; h *= 1099511628211ULL; }
    h &= dd_mask;
    while (1) {
        u32 *slot = dd_keys + h * n;
        if (slot[0] == 0xFFFFFFFFu) {
            memcpy(slot, idx, sizeof(u32) * n); dd_size++;
            if ((dd_size + 1) * 4 >= dd_cap * 3) { /* grow */
                u32 *ok = dd_keys; u64 oc = dd_cap;
                dd_init(dd_cap * 2);
                for (u64 i = 0; i < oc; i++) if (ok[i * n] != 0xFFFFFFFFu) dd_add(ok + i * n);
                free(ok);
            }
            return 1;
        }
        int eq = 1;
        for (int i = 0; i < n; i++) if (slot[i] != idx[i]) { eq = 0; break; }
        if (eq) return 0;
        h = (h + 1) & dd_mask;
    }
}

/* ------------------------------------------------------------------- sortie */
static char *obuf; static size_t opos, ocap;
static FILE *out_fp;        /* sortie texte/binaire brute (NULL si gz) */
static gzFile out_gz;       /* sortie compressee zlib si -o *.gz, sinon NULL */
static void oflush(void) {
    if (opos == 0) return;
    if (out_gz) gzwrite(out_gz, obuf, (unsigned)opos);
    else        fwrite(obuf, 1, opos, out_fp);
    opos = 0;
}
static inline void oput(const char *s, int len) {
    if (opos + len >= ocap) oflush();
    memcpy(obuf + opos, s, len); opos += len;
}
static inline void oputs(const char *s) { oput(s, (int)strlen(s)); }
static inline void oint(long v) { char t[24]; int l = snprintf(t, sizeof t, "%ld", v); oput(t, l); }

static int include_weights = 1;

static void emit_header(void) {
    char t[64];
    for (int i = 0; i <= n; i++) { int l = snprintf(t, sizeof t, "v_%d,", n - i); oput(t, l); }
    if (include_weights) {
        for (int j = 1; j <= n; j++) { int l = snprintf(t, sizeof t, "f_%d,", j); oput(t, l); }
        for (int i = 1; i <= n; i++) for (int j = 1; j <= n; j++) {
            int l = snprintf(t, sizeof t, "\"w_%d,%d\",", i, j); oput(t, l);
        }
    }
    oputs("CycleLenMSQ,NumAttractors,GenotypeCount,Robustness_std,Robustness_mean,Evolvability\n");
}

static int lengths_buf[1 << 12];

static void emit_row(const u32 *idx) {
    /* dynamique + matrice */
    for (int j = 0; j < n; j++) curf[j] = sbf_tt[idx[j]];
    for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) curW[i][j] = repr_col[idx[j] * n + i];

    /* successeurs */
    for (int s = 0; s < N; s++) {
        int nx = 0;
        for (int j = 0; j < n; j++) if ((curf[j] >> s) & 1) nx |= (1 << j);
        succ_buf[s] = nx;
    }
    int na = cycle_lengths(lengths_buf);
    long long sumsq = 0; for (int i = 0; i < na; i++) sumsq += (long long)lengths_buf[i] * lengths_buf[i];
    double cyclemsq = (double)sumsq / na;

    /* stats par colonne */
    u128 gcount = 1; int overflow = 0;
    double rmean = 0, rvar = 0; int ev = 0;
    for (int j = 0; j < n; j++) {
        int f = idx[j];
        u128 ng = gcount * (u128)csize[f];
        if (csize[f] != 0 && ng / (u128)csize[f] != gcount) overflow = 1;
        gcount = ng;
        rmean += nmean[f]; rvar += nvar[f]; ev += evol[f];
    }
    double r_std = sqrt(rvar) / Knorm;
    double r_mean = rmean / Knorm;

    /* decomposition "sous controle" en mode TBN (PTBN) : on relache la garde de
     * realisabilite SBF des faces (cf. decompose / decomp_tbn). */
    int vec[9];
    decomp_tbn = 1;
    memset(memo_status, 0, sizeof(signed char) * (size_t)N * N);
    decompose(0, 0, vec);

    char t[64];
    /* v_n..v_0 */
    for (int i = 0; i <= n; i++) { oint(vec[n - i]); oput(",", 1); }
    if (include_weights) {
        char fs[(1 << 6) + 1];
        for (int j = 0; j < n; j++) {
            for (int s = 0; s < N; s++) fs[s] = ((curf[j] >> s) & 1) ? '1' : '0';
            oput(fs, N); oput(",", 1);
        }
        for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) { oint(curW[i][j]); oput(",", 1); }
    }
    int l = fmt_double(cyclemsq, t); oput(t, l); oput(",", 1);
    oint(na); oput(",", 1);
    if (overflow) { l = fmt_double((double)gcount, t); oput(t, l); }
    else { char gb[40]; int gl = u128_to_str(gcount, gb); oput(gb, gl); }
    oput(",", 1);
    l = fmt_double(r_std, t); oput(t, l); oput(",", 1);
    l = fmt_double(r_mean, t); oput(t, l); oput(",", 1);
    oint(ev); oput("\n", 1);
}

/* ------------------------------------------------------ progression runtime
 * Ligne reecrite sur stderr (\r) pour ne pas polluer le CSV (stdout).
 * Throttlee dans la boucle pour un cout negligeable. */
static double t_start;   /* debut de la generation (omp_get_wtime) */

static void progress_sampling(long written, long target, long draws) {
    double el = omp_get_wtime() - t_start;
    double rate = el > 0 ? written / el : 0;
    double nov  = draws > 0 ? 100.0 * written / draws : 0;
    double eta  = rate > 0 ? (target - written) / rate : 0;
    fprintf(stderr, "\r[d=%d] %ld/%ld %5.1f%% | %.0fk dyn/s | nouveaute %5.2f%% | ETA %.0fs   ",
            n, written, target, 100.0 * written / target, rate / 1000.0, nov, eta);
    fflush(stderr);
}

static void progress_exhaustive(u64 done, u64 space) {
    double el = omp_get_wtime() - t_start;
    double rate = el > 0 ? done / el : 0;
    double eta  = rate > 0 ? (double)(space - done) / rate : 0;
    fprintf(stderr, "\r[d=%d] %llu/%llu %5.1f%% | %.0fk dyn/s | ETA %.0fs   ",
            n, (unsigned long long)done, (unsigned long long)space,
            100.0 * done / space, rate / 1000.0, eta);
    fflush(stderr);
}

/* ===================================================================== *
 *  Mode --core-trees : port C de core_tree_enum.py. Enumere les ARBRES DE
 *  CONTROLE (un noeud de controle force invariant SUR SA FACE), ce qui couvre
 *  le coeur COMPLET des plus decomposees, classes "en epine"/asymetriques
 *  incluses (que le forcage de projections globales manquait). On garde les M
 *  a plus grand decompSum.
 * ===================================================================== */

/* decompSum (somme des feuilles) d'un idx-tuple, mode TBN. */
static int decompsum_of(const u32 *idx) {
    for (int j = 0; j < n; j++) curf[j] = sbf_tt[idx[j]];
    for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) curW[i][j] = repr_col[idx[j] * n + i];
    int vec[9];
    decomp_tbn = 1;
    memset(memo_status, 0, sizeof(signed char) * (size_t)N * N);
    decompose(0, 0, vec);
    int s = 0; for (int t = 0; t <= n; t++) s += vec[t];
    return s;
}

/* invariant_set(fn,fv,c) : indices SBF dont la restriction a la face vaut
 * proj_c (c invariant sur la face). Trie croissant. Cache lazy. */
#define INVKEY(fn, fv, c) (((fn) * N + (fv)) * n + (c))
static int  **inv_set;   /* [N*N*n] */
static int   *inv_cnt;
static char  *inv_done;
static int *invariant_set(int fn, int fv, int c, int *cnt) {
    int key = INVKEY(fn, fv, c);
    if (!inv_done[key]) {
        int free_mask = (~fn) & (N - 1);
        int ns = 1 << __builtin_popcount(free_mask);
        int *buf = malloc(sizeof(int) * M), m = 0;
        for (int i = 0; i < M; i++) {
            u64 tt = sbf_tt[i];
            int ok = 1;
            for (int cc = 0; cc < ns; cc++) {
                int s = fv | (int)_pdep_u64((u64)cc, (u64)free_mask);
                if (((tt >> s) & 1) != ((s >> c) & 1)) { ok = 0; break; }
            }
            if (ok) buf[m++] = i;
        }
        inv_set[key] = buf; inv_cnt[key] = m; inv_done[key] = 1;
    }
    *cnt = inv_cnt[key];
    return inv_set[key];
}

typedef struct { int node, fn, fv; } Split;
static Split tree_buf[70];
static int   tree_len;
static int   open_fn[70], open_fv[70];

typedef struct { int dsum; u32 idx[8]; } Cand;
static Cand *cands; static long ncand, cap_cand;
static int  g_min_leaves, g_max_free;
static int *ct_scratch[8];   /* intersections par noeud */

static void emit_candidate(const u32 *idx) {
    if (!dd_add(idx)) return;                 /* deja vu (toutes arbres confondus) */
    int d = decompsum_of(idx);
    if (d < 2) return;
    if (ncand == cap_cand) {
        cap_cand = cap_cand ? cap_cand * 2 : (1 << 16);
        cands = realloc(cands, sizeof(Cand) * cap_cand);
    }
    cands[ncand].dsum = d;
    for (int j = 0; j < n; j++) cands[ncand].idx[j] = idx[j];
    ncand++;
}

static void process_tree(void) {
    if (tree_len + 1 < g_min_leaves) return;          /* #feuilles = #splits + 1 */
    int is_ctrl[8] = {0};
    for (int t = 0; t < tree_len; t++) is_ctrl[tree_buf[t].node] = 1;
    int nfree = 0; for (int c = 0; c < n; c++) if (!is_ctrl[c]) nfree++;
    if (g_max_free >= 0 && nfree > g_max_free) return;

    int *list[8], lsz[8];
    for (int c = 0; c < n; c++) {
        if (!is_ctrl[c]) { list[c] = NULL; lsz[c] = M; continue; }   /* libre */
        int sz = 0, first = 1;
        for (int t = 0; t < tree_len && (first || sz); t++) {
            if (tree_buf[t].node != c) continue;
            int cnt; int *iv = invariant_set(tree_buf[t].fn, tree_buf[t].fv, c, &cnt);
            if (first) { memcpy(ct_scratch[c], iv, sizeof(int) * cnt); sz = cnt; first = 0; }
            else {  /* intersection de deux listes triees, en place */
                int a = 0, b = 0, w = 0;
                while (a < sz && b < cnt) {
                    if (ct_scratch[c][a] == iv[b]) { ct_scratch[c][w++] = ct_scratch[c][a]; a++; b++; }
                    else if (ct_scratch[c][a] < iv[b]) a++; else b++;
                }
                sz = w;
            }
        }
        if (sz == 0) return;            /* aucun idx valide pour ce controle */
        list[c] = ct_scratch[c]; lsz[c] = sz;
    }
    /* produit cartesien (odometre) */
    u32 idx[8]; int pos[8];
    for (int c = 0; c < n; c++) pos[c] = 0;
    for (;;) {
        for (int c = 0; c < n; c++) idx[c] = list[c] ? (u32)list[c][pos[c]] : (u32)pos[c];
        emit_candidate(idx);
        int c = 0;
        for (; c < n; c++) { if (++pos[c] < lsz[c]) break; pos[c] = 0; }
        if (c == n) break;
    }
}

/* enumere tous les arbres de controle : pile de faces ouvertes. */
static void enum_trees(int n_open) {
    if (n_open == 0) { process_tree(); return; }
    int fn = open_fn[n_open - 1], fv = open_fv[n_open - 1];
    int free_mask = (~fn) & (N - 1);
    enum_trees(n_open - 1);                          /* cette face = feuille */
    for (int c = 0; c < n; c++) if ((free_mask >> c) & 1) {   /* sinon, split sur c */
        tree_buf[tree_len].node = c; tree_buf[tree_len].fn = fn; tree_buf[tree_len].fv = fv;
        tree_len++;
        open_fn[n_open - 1] = fn | (1 << c); open_fv[n_open - 1] = fv;
        open_fn[n_open]     = fn | (1 << c); open_fv[n_open]     = fv | (1 << c);
        enum_trees(n_open + 1);
        tree_len--;
    }
    open_fn[n_open - 1] = fn; open_fv[n_open - 1] = fv;        /* restaure */
}

static int cmp_cand_desc(const void *a, const void *b) {
    return ((const Cand *)b)->dsum - ((const Cand *)a)->dsum;
}

static void run_core_trees(long core_M, int min_leaves, int max_free) {
    g_min_leaves = min_leaves; g_max_free = max_free;
    int nkey = N * N * n;
    inv_set = calloc(nkey, sizeof(int *));
    inv_cnt = calloc(nkey, sizeof(int));
    inv_done = calloc(nkey, 1);
    for (int c = 0; c < n; c++) ct_scratch[c] = malloc(sizeof(int) * M);
    dd_init(1 << 20);

    open_fn[0] = 0; open_fv[0] = 0; tree_len = 0;
    enum_trees(1);

    qsort(cands, ncand, sizeof(Cand), cmp_cand_desc);
    long keep = (core_M > 0 && ncand > core_M) ? core_M : ncand;
    for (long i = 0; i < keep; i++) emit_row(cands[i].idx);
    oflush();
    fprintf(stderr, "[core-trees] min_leaves=%d max_free=%d : %ld decomposables, "
            "coeur garde=%ld (decompSum %d..%d)\n", min_leaves, max_free, ncand, keep,
            keep ? cands[keep - 1].dsum : 0, ncand ? cands[0].dsum : 0);
}

/* ------------------------------------------------------------------- main */
static const char *cache_path(void) {
    static char p[512];
    snprintf(p, sizeof p, "%s/.cache/mcsbn_table_%dd.bin",
             getenv("MCSBN_DIR") ? getenv("MCSBN_DIR") : ".", n);
    return p;
}

int main(int argc, char **argv) {
    long target = 100000, max_draws = 0, core_M = 20000;
    int seed = 0, exhaustive = 0, genotype = 0, progress = -1;  /* -1 = auto (isatty) */
    int core_trees = 0, min_leaves = -1, max_free = -2;         /* mode --core-trees */
    const char *opath = "-";
    n = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-d")) n = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-n")) target = atol(argv[++i]);
        else if (!strcmp(argv[i], "-o")) opath = argv[++i];
        else if (!strcmp(argv[i], "--seed")) seed = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--max-draws")) max_draws = atol(argv[++i]);
        else if (!strcmp(argv[i], "--core-trees")) core_trees = 1;
        else if (!strcmp(argv[i], "-M")) core_M = atol(argv[++i]);
        else if (!strcmp(argv[i], "--min-leaves")) min_leaves = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--max-free")) max_free = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--exhaustive")) exhaustive = 1;
        else if (!strcmp(argv[i], "--measure")) genotype = !strcmp(argv[++i], "genotype");
        else if (!strcmp(argv[i], "--no-weights")) include_weights = 0;
        else if (!strcmp(argv[i], "--progress")) progress = 1;
        else if (!strcmp(argv[i], "--no-progress")) progress = 0;
        else if (!strcmp(argv[i], "--help")) {
            fprintf(stderr, "usage: mcsbn -d D [-n N] [-o file] [--measure variety|genotype]\n"
                            "             [--seed S] [--max-draws M] [--exhaustive] [--no-weights]\n"
                            "             [--progress|--no-progress]\n"
                            "  progression sur stderr : auto si terminal, sinon silencieuse.\n");
            return 0;
        }
    }
    if (n < 1 || n > 6) { fprintf(stderr, "dimension -d (1..6) requise\n"); return 1; }
    N = 1 << n;

    if (!table_load(cache_path())) {
        fprintf(stderr, "Calcul de la table SBF (d=%d)...\n", n);
        build_table();
        table_save(cache_path());
    }
    build_keysets();

    rng_seed(seed ? (u64)seed : 0x12345678ULL);
    succ_buf = malloc(sizeof(int) * N * 3);
    state_attr = malloc(sizeof(int) * N);

    out_fp = NULL; out_gz = NULL;
    size_t olen = strlen(opath);
    if (!strcmp(opath, "-")) {
        out_fp = stdout;                       /* stdout reste non compresse */
    } else if (olen >= 3 && !strcmp(opath + olen - 3, ".gz")) {
        out_gz = gzopen(opath, "wb");          /* compression zlib native */
    } else {
        out_fp = fopen(opath, "wb");
    }
    if (!out_fp && !out_gz) { fprintf(stderr, "ouverture de %s impossible\n", opath); return 1; }
    ocap = 1 << 22; obuf = malloc(ocap); opos = 0;
    emit_header();

    if (progress < 0) progress = MCSBN_ISATTY(stderr);  /* auto : actif si terminal */
    t_start = omp_get_wtime();
    double t_last = t_start;
    int progress_shown = 0;   /* au moins une ligne ecrite -> il faudra un \n final */

    u32 *idx = malloc(sizeof(u32) * n);

    if (core_trees) {
        if (min_leaves < 0) min_leaves = (n <= 3) ? 2 : 8;
        if (max_free == -2) max_free = (n <= 3) ? -1 : 0;   /* -1 = illimite */
        run_core_trees(core_M, min_leaves, max_free);
    } else if (exhaustive) {
        u64 space = 1; for (int i = 0; i < n; i++) space *= M;
        if (space > 50000000ULL) { fprintf(stderr, "espace exhaustif trop grand (%llu)\n", (unsigned long long)space); return 1; }
        for (int i = 0; i < n; i++) idx[i] = 0;
        for (u64 c = 0; c < space; c++) {
            emit_row(idx);
            int p = 0; while (p < n) { if (++idx[p] < (u32)M) break; idx[p++] = 0; }
            if (progress && (c & 0xFFFF) == 0) {
                double now = omp_get_wtime();
                if (now - t_last >= 0.5) { progress_exhaustive(c, space); t_last = now; progress_shown = 1; }
            }
        }
        oflush();
        if (progress_shown) fputc('\n', stderr);
        fprintf(stderr, "Exhaustif : %llu dynamiques (= %d^%d).\n", (unsigned long long)space, M, n);
    } else {
        /* tirage cumulatif pour le mode genotype */
        u64 *cum = NULL, tot = 0;
        if (genotype) { cum = malloc(sizeof(u64) * M); for (int f = 0; f < M; f++) { tot += csize[f]; cum[f] = tot; } }
        dd_init(1 << 20);
        if (max_draws <= 0) max_draws = target * 50;
        long written = 0, draws = 0, stale = 0;
        while (written < target && draws < max_draws) {
            for (int j = 0; j < n; j++) {
                if (genotype) {
                    u64 r = ((u128)rng_next() * tot) >> 64;
                    /* binary search */
                    int lo = 0, hi = M - 1;
                    while (lo < hi) { int mid = (lo + hi) / 2; if (cum[mid] <= r) lo = mid + 1; else hi = mid; }
                    idx[j] = lo;
                } else idx[j] = rng_below(M);
            }
            draws++;
            if (progress && (draws & 0xFFFF) == 0) {
                double now = omp_get_wtime();
                if (now - t_last >= 0.5) { progress_sampling(written, target, draws); t_last = now; progress_shown = 1; }
            }
            if (!dd_add(idx)) {
                if (++stale > 200000 && stale > 20 * (written + 1)) {
                    if (progress_shown) { fputc('\n', stderr); progress_shown = 0; }
                    fprintf(stderr, "espace probablement epuise (%ld distinctes).\n", written); break;
                }
                continue;
            }
            stale = 0;
            emit_row(idx);
            written++;
        }
        oflush();
        if (progress_shown) fputc('\n', stderr);
        fprintf(stderr, "%ld dynamiques distinctes en %ld tirages (%.1f%% de nouveaute).\n",
                written, draws, 100.0 * written / (draws > 0 ? draws : 1));
    }
    if (out_gz) gzclose(out_gz);
    else if (out_fp != stdout) fclose(out_fp);
    return 0;
}
