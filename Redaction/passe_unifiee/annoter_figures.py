#!/usr/bin/env python3
"""Annotations des figures P4, OL2a et OL2b (Redaction/figures/).

Les zones sont dessinées derrière le graphe : on teinte l'image, puis on recolle par-dessus les
pixels qui ne sont pas du fond, si bien que nœuds, arêtes et points restent intacts. Les
originaux non annotés sont gardés dans figures/non_annotees/ ; le script repart toujours d'eux.

Usage : python3 Redaction/passe_unifiee/annoter_figures.py
"""
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

FIG = Path(__file__).resolve().parents[1] / "figures"
ORIG = FIG / "non_annotees"
POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ORANGE, VERT = (235, 104, 52), (27, 175, 122)
ORANGE_TEXTE, VERT_TEXTE = (170, 62, 22), (14, 110, 76)   # plus foncés, lisibles en texte


def original(nom):
    """Copie l'original la première fois, puis repart toujours de lui."""
    ORIG.mkdir(exist_ok=True)
    if not (ORIG / nom).exists():
        shutil.copy2(FIG / nom, ORIG / nom)
    return Image.open(ORIG / nom).convert("RGB")


def derriere(im, calque):
    """Compose le calque (RGBA) sous le dessin : le fond est teinté, le reste recollé."""
    fond = Image.new("RGB", im.size, im.getpixel((0, 0)))
    masque = ImageChops.difference(im, fond).convert("L").point(lambda v: 255 if v > 18 else 0)
    teinte = Image.alpha_composite(im.convert("RGBA"), calque).convert("RGB")
    teinte.paste(im, mask=masque)
    return teinte


def etiquette(d, xy, texte, couleur, taille, fond=(247, 248, 251)):
    """Texte posé sur un cartouche du fond de la figure, lisible par-dessus les arcs."""
    police = ImageFont.truetype(POLICE, taille)
    x0, y0, x1, y1 = d.textbbox(xy, texte, font=police)
    m = taille // 4
    d.rounded_rectangle([x0 - m, y0 - m, x1 + m, y1 + m], radius=m, fill=fond + (230,))
    d.text(xy, texte, font=police, fill=couleur + (255,))


def p4():
    nom = "3d_P4_PSBN_undercontrol_taggedtree_hypercube.png"
    im = original(nom)
    # centres des sommets (pixels de l'image rognée, relevés sur la figure) ; rayon d'un sommet ~46
    s = {"000": (152, 1132), "001": (1122, 1158), "100": (674, 1472), "101": (1560, 1518),
         "110": (860, 598), "111": (1712, 582)}
    calque = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    # Pas d'aplat : en projection, 001 tombe dans le quadrilatère de la face x3 = 1. On souligne
    # donc les arêtes du sous-cube et l'on cercle ses sommets.
    for a, b in [("100", "110"), ("110", "111"), ("111", "101"), ("101", "100")]:
        d.line([s[a], s[b]], fill=ORANGE + (90,), width=44)
    d.line([s["000"], s["001"]], fill=VERT + (110,), width=44)
    for sommets, c in [(("100", "110", "111", "101"), ORANGE), (("000", "001"), VERT)]:
        for k in sommets:
            x, y = s[k]
            d.ellipse([x - 78, y - 78, x + 78, y + 78], fill=c + (110,))
    im = derriere(im, calque)
    d = ImageDraw.Draw(im, "RGBA")
    etiquette(d, (1020, 440), "face x₃ = 1", ORANGE_TEXTE, 60)
    etiquette(d, (330, 1225), "arête {000, 001}", VERT_TEXTE, 60)
    im.save(FIG / nom)
    print("P4 annotée :", nom)


# --- Nuages de sbn_scatter (export ×3) : pad = 52 px d'écran, vue initiale = étendue des données.
ENCRE = (60, 60, 60)
CSV3 = Path(__file__).resolve().parent / "sortie" / "csv" / "3d_PSBN_undercontrol_taggedtree_output.csv.gz"


def dynamiques_plus_fines():
    """Une ligne par dynamique, avec son vecteur le plus fin et la dimension de sa plus grande
    hyper-face non décomposable (position du premier coefficient non nul)."""
    import pandas as pd
    t = pd.read_csv(CSV3, dtype={f"f_{j}": str for j in (1, 2, 3)})
    v = ["v_3", "v_2", "v_1", "v_0"]
    t["somme"] = t[v].sum(axis=1)
    t["vec"] = t[v].astype(str).agg(",".join, axis=1)
    fin = t.sort_values(["somme", "vec"], ascending=False).drop_duplicates(["f_1", "f_2", "f_3"])
    fin["dim"] = fin[v].apply(lambda r: 3 - next(i for i, x in enumerate(r) if x > 0), axis=1)
    return fin, t


def vers_pixels(im, xmin, xmax, ymin, ymax, echelle=3, pad=52):
    W, H = im.size
    p = pad * echelle
    return (lambda x: p + (x - xmin) / (xmax - xmin) * (W - 2 * p),
            lambda y: H - p - (y - ymin) / (ymax - ymin) * (H - 2 * p))


def enveloppe(points):
    """Enveloppe convexe (chaîne monotone)."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts
    def cote(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    bas, haut = [], []
    for q in pts:
        while len(bas) >= 2 and cote(bas[-2], bas[-1], q) <= 0:
            bas.pop()
        bas.append(q)
    for q in reversed(pts):
        while len(haut) >= 2 and cote(haut[-2], haut[-1], q) <= 0:
            haut.pop()
        haut.append(q)
    return bas[:-1] + haut[:-1]


def couleurs_vecteurs(im, t, X, Y, xcol, ycol):
    """Couleur de chaque vecteur, relevée au centre des points où il est visible. La page trie
    les points par rayon décroissant puis par somme du vecteur croissante (sbn_scatter.html,
    allPts.sort) : en un point du nuage, on voit le vecteur qui y a le moins de lignes, et à
    égalité le plus décomposé."""
    from collections import Counter, defaultdict
    compte = Counter(zip(t[xcol], t[ycol], t["vec"]))
    par_pos = defaultdict(list)
    for (x, y, v), n in compte.items():
        par_pos[(x, y)].append((n, -sum(map(int, v.split(","))), v))
    vus = defaultdict(Counter)
    for (x, y), vs in par_pos.items():
        v = min(vs)[2]
        vus[v][im.getpixel((round(X(x)), round(Y(y))))] += 1
    couleurs = {}
    for v, c in vus.items():
        (coul, n), total = c.most_common(1)[0], sum(c.values())
        couleurs[v] = coul
        if n < total:
            print(f"  ⟨{v}⟩ : couleur majoritaire sur {n} des {total} points")
    return couleurs


def legende(im, couleurs, titre="vecteur de décomposition", largeur=560):
    """Ajoute un panneau de légende à droite de l'image."""
    fond = im.getpixel((0, 0))
    out = Image.new("RGB", (im.width + largeur, im.height), fond)
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    police = ImageFont.truetype(POLICE, 44)
    x0, y = im.width + 10, 170
    d.text((x0, y), titre, font=ImageFont.truetype(POLICE, 38), fill=ENCRE)
    y += 80
    ordre = sorted(couleurs, key=lambda v: (-int(v.split(",")[0]), [-int(c) for c in v.split(",")]))
    for v in ordre:
        d.ellipse([x0 + 4, y + 6, x0 + 44, y + 46], fill=couleurs[v])
        d.text((x0 + 70, y), "⟨" + v + "⟩", font=police, fill=ENCRE)
        y += 66
    return out


def ol2a():
    nom = "3d_OL2a_PSBN_undercontrol_taggedtree.png"
    im = original(nom)
    fin, t = dynamiques_plus_fines()
    X, Y = vers_pixels(im, t.Robustness_mean.min(), t.Robustness_mean.max(), t.Evolvability.min(), t.Evolvability.max())
    couleurs = couleurs_vecteurs(im, t, X, Y, "Robustness_mean", "Evolvability")
    dec = fin[fin.dim < 3]
    rmax, emax = dec.Robustness_mean.max(), dec.Evolvability.max()
    d = ImageDraw.Draw(im, "RGBA")
    # rectangle pointillé : toutes les dynamiques décomposables sont dans [0, rmax] x [21, emax]
    coins = [(X(0), Y(emax)), (X(rmax), Y(emax)), (X(rmax), Y(t.Evolvability.min()))]
    for (xa, ya), (xb, yb) in zip(coins, coins[1:]):
        n = int(max(abs(xb - xa), abs(yb - ya)) // 40)
        for k in range(n):
            u0, u1 = k / n, min((k + 0.55) / n, 1)
            d.line([(xa + (xb - xa) * u0, ya + (yb - ya) * u0), (xa + (xb - xa) * u1, ya + (yb - ya) * u1)],
                   fill=ENCRE + (210,), width=6)
    texte = f"les {len(dec)} dynamiques décomposables : robustesse ≤ {rmax:.3f}, évolutivité ≤ {emax:g}"
    etiquette(d, (X(0.005), Y(emax) - 70), texte.replace("0.", "0,"), ENCRE, 38)
    im = legende(im, couleurs)
    im.save(FIG / nom)
    print("OL2a annotée :", nom, "| décomposables", len(dec), "| bornes", rmax, emax, "| couleurs", len(couleurs))


def ol2b():
    nom = "3d_OL2b_PSBN_undercontrol_taggedtree.png"
    im = original(nom)
    fin, t = dynamiques_plus_fines()
    X, Y = vers_pixels(im, t.Robustness_mean.min(), t.Robustness_mean.max(), t.Robustness_std.min(), t.Robustness_std.max())
    couleurs = couleurs_vecteurs(im, t, X, Y, "Robustness_mean", "Robustness_std")
    W, H = im.size
    p = 52 * 3
    d = ImageDraw.Draw(im, "RGBA")
    planchers = {k: g.Robustness_std.min() for k, g in fin.groupby("dim")}
    for k in (2, 1):
        y = Y(planchers[k])
        for x0 in range(p, W - p, 40):  # trait discontinu
            d.line([(x0, y), (min(x0 + 22, W - p), y)], fill=ENCRE + (200,), width=5)
        etiquette(d, (X(0.30), y - 60), f"hyper-face max. de dim. {k} : ≥ " + f"{planchers[k]:.4f}".replace(".", ","), ENCRE, 38)
    ident = fin[fin.dim == 0].iloc[0]
    x, y = X(ident.Robustness_mean), Y(ident.Robustness_std)
    d.ellipse([x - 34, y - 34, x + 34, y + 34], outline=ENCRE + (255,), width=6)
    etiquette(d, (x + 50, y + 8), "identité (dim. 0)", ENCRE, 38)
    etiquette(d, (X(0.21), Y(0.0035)), "non décomposables (dim. 3) : jusqu'à 0", ENCRE, 38)
    im = legende(im, couleurs)
    im.save(FIG / nom)
    print("OL2b annotée :", nom, "| planchers", {k: round(float(v), 4) for k, v in planchers.items()}, "| couleurs", len(couleurs))


if __name__ == "__main__":
    p4()
    ol2a()
    ol2b()
