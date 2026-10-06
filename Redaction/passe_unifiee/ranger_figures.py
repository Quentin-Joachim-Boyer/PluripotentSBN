#!/usr/bin/env python3
"""Range les exports des pages HTML sous les noms que rapport_stage.tex attend.

Les pages téléchargent leurs exports dans ~/Téléchargements sous un nom tiré du CSV :
  sbn_viz     <csv>_sbn<k>_{reseau,hypercube}.png
  sbn_scatter <csv>_<x>_vs_<y>.png
  metagraphe  <csv>_metagraphe.png
Ce script copie chacun dans Redaction/figures/ sous le nom des emplacements du rapport
(commentaires « Fichier(s) attendu(s) »), puis liste ce qui manque. Il ne supprime rien.

Usage : python3 Redaction/passe_unifiee/ranger_figures.py [dossier des téléchargements]
"""
import shutil
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Téléchargements"
FIGURES = Path(__file__).resolve().parents[1] / "figures"

# nom exporté -> nom attendu dans le rapport
CORRESPONDANCES = {}
for fiche, prog, k in [("X2", "PSBN_undercontrol_taggedtree", 1), ("C1", "PSBN_undercontrol", 1),
                       ("C2", "PTBN_undercontrol", 1), ("C3", "PSBN_undercontrol", 1),
                       ("C6", "PTBN_undercontrol_taggedtree", 1), ("C7", "PSBN_undercontrol_taggedtree", 1),
                       ("C8", "PTBN_undercontrol_taggedtree", 2), ("P0", "PSBN_undercontrol_treeinsolver", 1),
                       ("P3", "PSBNI_undercontrol", 1), ("P4", "PSBN_undercontrol_taggedtree", 1)]:
    for partie in ("reseau", "hypercube"):
        CORRESPONDANCES[f"3d_{fiche}_{prog}_sbn{k}_{partie}.png"] = f"3d_{fiche}_{prog}_{partie}.png"
CORRESPONDANCES["3d_C5_PSBN_undercontrol_taggedtree_sbn1_hypercube.png"] = "3d_C5_PSBN_undercontrol_taggedtree_0200.png"
CORRESPONDANCES["3d_C5_PSBN_undercontrol_taggedtree_sbn2_hypercube.png"] = "3d_C5_PSBN_undercontrol_taggedtree_0040.png"
# OL1 (vecteur trivial seul en d = 2 et 3) ; en d = 3, OL2a a le même nom d'export : exporter OL1
# d'abord, OL2a ensuite (le navigateur nomme alors la seconde « … (1).png »).
CORRESPONDANCES["2d_PSBN_undercontrol_taggedtree_Robustness_mean_vs_Evolvability.png"] = "2d_OL1_PSBN_undercontrol_taggedtree.png"
CORRESPONDANCES["3d_PSBN_undercontrol_taggedtree_Robustness_mean_vs_Evolvability.png"] = "3d_OL1_PSBN_undercontrol_taggedtree.png"
CORRESPONDANCES["3d_PSBN_undercontrol_taggedtree_Robustness_mean_vs_Evolvability (1).png"] = "3d_OL2a_PSBN_undercontrol_taggedtree.png"
# Firefox écrit « …(1).png » sans espace
CORRESPONDANCES["3d_PSBN_undercontrol_taggedtree_Robustness_mean_vs_Evolvability(1).png"] = "3d_OL2a_PSBN_undercontrol_taggedtree.png"
CORRESPONDANCES["4d_MCSBN_variety_100000_Robustness_mean_vs_Evolvability.png"] = "4d_OL1_MCSBN_variety.png"
CORRESPONDANCES["5d_MCSBN_variety_100000_Robustness_mean_vs_Evolvability.png"] = "5d_OL1_MCSBN_variety.png"
CORRESPONDANCES["3d_PSBN_undercontrol_taggedtree_Robustness_mean_vs_Robustness_std.png"] = "3d_OL2b_PSBN_undercontrol_taggedtree.png"
CORRESPONDANCES["3d_PTBN_undercontrol_taggedtree_output_metagraph_metagraphe.png"] = "3d_M2_PTBN_undercontrol_taggedtree_metagraphe.png"

# captures de page entière : à copier à la main (nom libre de l'outil de capture)
PAGES = ["3d_V1_sbn_viz_page.png", "3d_V2_sbn_scatter_page.png", "3d_V3_metagraphe_page.png"]

def rogner(path, marge=0.04):
    """Retire le fond uniforme autour du dessin (couleur du coin), puis remet une marge égale."""
    from PIL import Image, ImageChops
    im = Image.open(path).convert("RGB")
    fond = Image.new("RGB", im.size, im.getpixel((0, 0)))
    boite = ImageChops.difference(im, fond).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    if not boite:
        return
    m = int(marge * max(boite[2] - boite[0], boite[3] - boite[1]))
    rogne = im.crop(boite)
    sortie = Image.new("RGB", (rogne.width + 2 * m, rogne.height + 2 * m), im.getpixel((0, 0)))
    sortie.paste(rogne, (m, m))
    sortie.save(path)


copies = 0
for exporte, attendu in CORRESPONDANCES.items():
    src = SOURCE / exporte
    if src.exists():
        dest = FIGURES / attendu
        if dest.exists():
            print(f"existe déjà, non écrasé : {attendu}")
            continue
        shutil.copy2(src, dest)
        if attendu.endswith(("_hypercube.png", "_0200.png", "_0040.png")):
            rogner(dest)  # le panneau de l'hypercube est souvent bien plus haut que le dessin
        copies += 1
        print(f"{exporte}  ->  figures/{attendu}")
manquants = [a for a in CORRESPONDANCES.values() if not (FIGURES / a).exists()]
manquants += [p for p in PAGES if not (FIGURES / p).exists()]
print(f"\n{copies} copiés ; {len(manquants)} encore manquants :")
for m in manquants:
    print("  " + m)
