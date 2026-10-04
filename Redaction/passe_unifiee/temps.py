"""
Mesures de la fiche O1 (Redaction/plan_figures.md), sur la machine de la passe.

  O1a  contraintes sur la structure (PSBN_distinct_faces_HS.lp, qui retrouve les
       189 dynamiques de Laurent) contre contraintes sur les poids, sur ⟨0,2,0,0⟩
       en d = 3 ; le temps de Laurent vient de sa sortie et n'est pas remesuré ;
  O1b  les trois formulations successives de PSBN_undercontrol_taggedtree.lp ;
  O1c  clingcon --parallel 1, 2, 4, 8 contre JPP, sur l'énumération globale PSBN
       taggedtree en d = 3.

Chaque appel à clingcon est borné en mémoire (ulimit -v) et en durée (timeout),
car la version 88ccf0e sature la mémoire. Une mesure complète de moins de 10 s
est répétée, et l'on garde la médiane.
"""

import re
import shlex
import shutil
import statistics
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASP = REPO / "JPPipeline" / "src" / "asp"
INTERMEDIAIRE = REPO / "Redaction/sources/PSBN_undercontrol_taggedtree_intermediaire_2026-07-03.lp"
DISTINCT_FACES = REPO / "SBN_pluripotent/PSBN_distinct_faces_HS.lp"

MEMOIRE_KO = 4_000_000
# Symptômes de la borne mémoire : selon le moment, clingcon ou la glibc échoue.
MEMOIRE_SATUREE = r"bad_alloc|out of memory|Cannot allocate memory"
DUREE_MAX = 300
COURTE = 10.0
V0200 = ["-c", "d=3", "-c", "v3=0", "-c", "v2=2", "-c", "v1=0", "-c", "v0=0"]
# Sortie de Laurent : « Pluripot-decomp.189-sol.d=3._0, 2, 0, 0_ .lp », clingcon 5.2.1,
# 15-07-2024, sa machine (hors du dépôt, transmise par Quentin le 2026-10-04).
LAURENT = {"programme": "Laurent (15-07-2024, sa machine)", "modeles": 189, "temps_clingcon_s": 2.517}


def appel_clingcon(args, cwd, env, journal):
    cmd = f"ulimit -v {MEMOIRE_KO}; exec timeout {DUREE_MAX} clingcon " + " ".join(map(shlex.quote, args))
    t0 = time.perf_counter()
    with open(journal, "w") as j:
        rc = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, stdout=j, stderr=subprocess.STDOUT).returncode
    mur = time.perf_counter() - t0
    texte = journal.read_text(errors="replace")
    m = re.search(r"^Models\s*:\s*(\d+)(\+?)", texte, re.M)
    tc = re.search(r"^Time\s*:\s*([\d.]+)s", texte, re.M)
    return {"code": rc, "modeles": int(m.group(1)) if m else None, "complet": bool(m) and not m.group(2),
            "temps_clingcon_s": float(tc.group(1)) if tc else None, "mur_s": round(mur, 3),
            "memoire_saturee": bool(re.search(MEMOIRE_SATUREE, texte))}


def appel_jpp(sortie, env, journal):
    dossier = sortie / "tmp" / "temps" / "jpp"
    shutil.rmtree(dossier, ignore_errors=True)
    dossier.mkdir(parents=True)
    cmd = ["java", "-cp", f"{sortie / 'bin' / 'jpp'}:{REPO / 'JPPipeline/lib/jpp.jar'}", "PSBN.Main", "3",
           str(ASP / "PSBN_undercontrol_taggedtree.lp"), str(ASP), "0", str(dossier), "1"]
    t0 = time.perf_counter()
    with open(journal, "w") as j:
        rc = subprocess.run(cmd, cwd=REPO, env=env, stdout=j, stderr=subprocess.STDOUT).returncode
    mur = time.perf_counter() - t0
    lignes = (dossier / "3d_PSBN_undercontrol_taggedtree_output.csv").read_text().count("\n") - 1
    return {"code": rc, "modeles": lignes, "complet": rc == 0, "temps_clingcon_s": None,
            "mur_s": round(mur, 3), "memoire_saturee": False}


def mesurer(nom, appel, repetitions, attendu=None):
    """Lance appel() une fois, puis jusqu'à `repetitions` fois si la mesure est courte."""
    essais = [appel()]
    if essais[0]["complet"] and essais[0]["mur_s"] < COURTE:
        essais += [appel() for _ in range(repetitions - 1)]
    r = dict(essais[-1])
    r["mur_s"] = round(statistics.median(e["mur_s"] for e in essais), 3)
    if r["temps_clingcon_s"] is not None:
        r["temps_clingcon_s"] = round(statistics.median(e["temps_clingcon_s"] for e in essais), 3)
    r.update(nom=nom, attendu=attendu, essais=len(essais),
             tous_mur_s=[e["mur_s"] for e in essais])
    etat = "mémoire saturée" if r["memoire_saturee"] else f"{r['modeles']}{'' if r['complet'] else '+'} modèles"
    print(f"    {nom} : {etat}, {r['mur_s']} s (médiane de {len(essais)})")
    return r


def preparer(dossier, fichiers):
    """Copie (chemin) ou extrait de git (« commit:chemin ») les programmes dans dossier."""
    shutil.rmtree(dossier, ignore_errors=True)
    dossier.mkdir(parents=True)
    for nom, src in fichiers.items():
        if isinstance(src, Path):
            shutil.copy(src, dossier / nom)
        else:
            (dossier / nom).write_bytes(subprocess.run(["git", "show", src], cwd=REPO, capture_output=True,
                                                       check=True).stdout)
    return dossier


def toutes(sortie, repetitions, env):
    tmp = sortie / "tmp" / "temps"
    logs = sortie / "temps" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    def cc(args, cwd, ident):
        return lambda: appel_clingcon(args, cwd, env, logs / f"{ident}.log")

    print("  O1a : structure contre poids, ⟨0,2,0,0⟩, d = 3")
    ref = preparer(tmp / "reference", {
        "PSBN_distinct_faces_HS.lp": DISTINCT_FACES,
        "PSBN_undercontrol.lp": ASP / "PSBN_undercontrol.lp",
        "PTBN_undercontrol.lp": ASP / "PTBN_undercontrol.lp",
        "setup_btree_3d.lp": ASP / "setup_btree_3d.lp",
        "PSBN_undercontrol_taggedtree.lp": ASP / "PSBN_undercontrol_taggedtree.lp",
        "PTBN_undercontrol_taggedtree.lp": ASP / "PTBN_undercontrol_taggedtree.lp"})
    o1a = [
        mesurer("PSBN_distinct_faces_HS.lp", cc(["0", "--project"] + V0200 +
                ["setup_btree_3d.lp", "PSBN_distinct_faces_HS.lp"], ref, "o1a_distinct_faces"), repetitions, 189),
        mesurer("PSBN_undercontrol.lp", cc(["0", "--project"] + V0200 +
                ["setup_btree_3d.lp", "PSBN_undercontrol.lp"], ref, "o1a_undercontrol"), repetitions, 225),
        mesurer("PSBN_undercontrol_taggedtree.lp", cc(["0", "--project"] + V0200 +
                ["PSBN_undercontrol_taggedtree.lp"], ref, "o1a_taggedtree"), repetitions, 675),
    ]

    print("  O1b : formulations successives de PSBN_undercontrol_taggedtree.lp")
    versions = {
        "88ccf0e": {"PSBN_undercontrol_taggedtree.lp": "88ccf0e:SBN_pluripotent/PSBN_undercontrol_taggedtree.lp",
                    "PTBN_undercontrol_taggedtree.lp": "88ccf0e:SBN_pluripotent/PTBN_undercontrol_taggedtree.lp"},
        "intermédiaire": {"PSBN_undercontrol_taggedtree.lp": INTERMEDIAIRE,
                          "PTBN_undercontrol_taggedtree.lp": "88ccf0e:SBN_pluripotent/PTBN_undercontrol_taggedtree.lp"},
        "7dc415c": {"PSBN_undercontrol_taggedtree.lp": "7dc415c:SBN_pluripotent/PSBN_undercontrol_taggedtree.lp",
                    "PTBN_undercontrol_taggedtree.lp": "7dc415c:SBN_pluripotent/PTBN_undercontrol_taggedtree.lp"},
    }
    q60 = ["0", "--project", "-q", "--time-limit=60"]
    o1b = []
    for version, fichiers in versions.items():
        dossier = preparer(tmp / version.replace("é", "e"), fichiers)
        ident = version.replace("é", "e")
        o1b.append(dict(version=version, **mesurer(
            f"{version}, PSBN ⟨0,2,0,0⟩", cc(q60 + V0200 + ["PSBN_undercontrol_taggedtree.lp"], dossier,
                                             f"o1b_{ident}_psbn_0200"), repetitions, 675)))
        o1b.append(dict(version=version, **mesurer(
            f"{version}, PSBN global (60 s)", cc(q60 + ["-c", "d=3", "PSBN_undercontrol_taggedtree.lp"], dossier,
                                                 f"o1b_{ident}_psbn_global"), 1)))
        if version != "intermédiaire":  # la base PTBN intermédiaire est celle de 88ccf0e
            o1b.append(dict(version=version, **mesurer(
                f"{version}, PTBN global", cc(q60 + ["-c", "d=3", "PTBN_undercontrol_taggedtree.lp"], dossier,
                                              f"o1b_{ident}_ptbn_global"), repetitions, 39020)))

    print("  O1c : clingcon --parallel k contre JPP, PSBN taggedtree global, d = 3")
    o1c = [dict(parallel=k, **mesurer(
        f"clingcon --parallel {k}", cc(["0", "--project", "--parallel", str(k), "-c", "d=3",
                                        "PSBN_undercontrol_taggedtree.lp"], ref, f"o1c_parallel_{k}"),
        repetitions, 34343)) for k in (1, 2, 4, 8)]
    o1c.append(dict(parallel="JPP", **mesurer(
        "JPP", lambda: appel_jpp(sortie, env, logs / "o1c_jpp.log"), repetitions, 34343)))

    # Les journaux d'énumération complète sont gros : on n'en garde que la fin.
    for log in logs.glob("*.log"):
        lignes = log.read_text(errors="replace").splitlines()
        if len(lignes) > 40:
            log.write_text("\n".join(["[...]"] + lignes[-40:]) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    return {"repetitions": repetitions, "memoire_max_ko": MEMOIRE_KO, "laurent": LAURENT,
            "O1a": o1a, "O1b": o1b, "O1c": o1c}
