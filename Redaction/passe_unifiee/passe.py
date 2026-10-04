#!/usr/bin/env python3
"""
Passe unifiée : régénère toutes les données décidées dans Redaction/plan_figures.md.

Lancement, depuis n'importe où, avec l'environnement conda du projet activé
(conda activate ./.conda, pour numpy, scipy et matplotlib) :

    python3 Redaction/passe_unifiee/passe.py [--sortie <dossier>] [--etapes <e1,e2,...>]
                                             [--refaire] [--repetitions <k>] [--brouillon]

Étapes, dans l'ordre :
  env          versions, machine et commit (toujours exécutée) ;
  compilation  JPP (javac, dans <sortie>/bin) et MCSBN (make -B, make drgraph) ;
  jpp          énumérations exhaustives, CSV triés (T1) puis compressés ;
  mcsbn        tirages uniformes en d = 4 et 5 (OL1) ;
  metagraphe   positions du métagraphe d = 3 (M2, OL4), lancées deux fois pour
               vérifier qu'elles sont identiques ;
  fiches       nombres des fiches recalculés, lignes à capturer (fiches.py) ;
  temps        mesures de la fiche O1 (temps.py), à lancer sur une machine au repos ;
  resume       <sortie>/resume.md.

Une étape dont la sortie existe déjà est sautée, sauf avec --refaire. La passe
refuse de tourner si les sources qu'elle exécute ont des modifications non
commitées ; --brouillon passe outre, et le manifeste comme le résumé le signalent.
"""

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Pas de __pycache__ : il salirait l'arbre de travail, que la passe veut propre.
sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[2]
ICI = Path(__file__).resolve().parent
CONDA_BIN = REPO / ".conda" / "bin"
ASP = REPO / "JPPipeline" / "src" / "asp"
JPP_JAR = REPO / "JPPipeline" / "lib" / "jpp.jar"

# Sources exécutées par la passe : elles doivent être commitées.
SOURCES = [
    "JPPipeline/src", "JPPipeline/lib", "MCSBN/src", "MCSBN/tools", "MCSBN/Makefile",
    "SBN_pluripotent/PSBN_distinct_faces_HS.lp", "Redaction/passe_unifiee",
    "Redaction/sources/PSBN_undercontrol_taggedtree_intermediaire_2026-07-03.lp",
]

# Énumérations JPP exhaustives (programme, dimension) et fiches qu'elles servent.
JPP_RUNS = [
    ("PSBN_undercontrol", 3),               # C1, C2, C3, C7
    ("PTBN_undercontrol", 3),               # C2, C6
    ("PSBNI_undercontrol", 3),              # P3
    ("PSBN_undercontrol_taggedtree", 2),    # O2, OL1
    ("PSBN_undercontrol_taggedtree", 3),    # C4, C5, C7, P1, P2, P4, O2, O3, OL1, OL2
    ("PTBN_undercontrol_taggedtree", 3),    # C6, C8, P2, P4, M2, O3, OL4
    ("PSBN_undercontrol_treeinsolver", 3),  # C6, C7, P0/P5
    ("PTBN_undercontrol_treeinsolver", 3),  # C6
]
# Tirages MCSBN : mesure variety (dynamiques équiprobables), graine par défaut.
MCSBN_DIMS = [4, 5]
MCSBN_N = 100000
# Métagraphe : un seul fil et une graine fixe rendent DRGraph reproductible.
METAGRAPHE_CSV = "3d_PTBN_undercontrol_taggedtree_output.csv.gz"
METAGRAPHE_OPTS = ["--threads", "1", "--seed", "1"]

ETAPES = ["env", "compilation", "jpp", "mcsbn", "metagraphe", "fiches", "temps", "resume"]


# ---------------------------------------------------------------------------
# Outils

def env_conda():
    """Environnement des sous-processus : clingcon de .conda en tête du PATH."""
    env = os.environ.copy()
    env["PATH"] = str(CONDA_BIN) + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # MCSBN/src/python/__pycache__ est versionné
    return env


def lancer(cmd, journal, cwd=REPO, codes_ok=(0,)):
    """Lance cmd, écrit sa sortie dans journal, renvoie la durée (s)."""
    journal.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    with open(journal, "w") as j:
        rc = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env_conda(),
                            stdout=j, stderr=subprocess.STDOUT).returncode
    duree = time.perf_counter() - t0
    if rc not in codes_ok:
        sys.exit(f"Échec (code {rc}) de : {' '.join(map(str, cmd))}\nJournal : {journal}")
    return duree


def sortie_de(cmd, cwd=REPO):
    p = subprocess.run(cmd, cwd=cwd, env=env_conda(), capture_output=True, text=True)
    return (p.stdout + p.stderr).strip()


def lire_texte(path):
    """Contenu d'un CSV, compressé ou non."""
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", newline="") as f:
            return f.read()
    return path.read_text(newline="")


def ecrire_gzip(path, texte):
    """gzip sans date ni nom dans l'en-tête : même contenu, mêmes octets."""
    with open(path, "wb") as brut, gzip.GzipFile(filename="", mode="wb", fileobj=brut, mtime=0) as gz:
        gz.write(texte.encode())


def sha256(texte):
    return hashlib.sha256(texte.encode()).hexdigest()


def trier_csv(texte):
    """Trie les lignes (T1) : vecteur du plus grossier au plus fin, arbre,
    dynamique, poids, puis la ligne elle-même. Les lignes sont recopiées telles
    quelles, seul leur ordre change."""
    import csv
    lignes = texte.splitlines()
    tete = next(csv.reader([lignes[0]]))
    iv = [i for i, c in enumerate(tete) if c.startswith("v_")]
    it = tete.index("tree") if "tree" in tete else None
    jf = [i for i, c in enumerate(tete) if c.startswith("f_")]
    iw = [i for i, c in enumerate(tete) if c.startswith("w_")]

    def cle(ligne):
        r = next(csv.reader([ligne]))
        return (tuple(-int(r[i]) for i in iv), r[it] if it is not None else "",
                tuple(r[i] for i in jf), tuple(int(r[i]) for i in iw), ligne)

    corps = sorted((l for l in lignes[1:] if l), key=cle)
    return "\n".join([lignes[0]] + corps) + "\n", len(corps)


class Manifeste:
    """<sortie>/manifeste.json : ce qu'a fait chaque étape, et à quel commit."""

    def __init__(self, sortie):
        self.path = sortie / "manifeste.json"
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}

    def __getitem__(self, cle):
        return self.data.setdefault(cle, {})

    def __setitem__(self, cle, val):
        self.data[cle] = val

    def sauver(self):
        self.path.write_text(json.dumps(self.data, indent=1, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Étapes

def etape_env(sortie, man, args):
    commit = sortie_de(["git", "rev-parse", "HEAD"])
    sales = sortie_de(["git", "status", "--porcelain", "--"] + SOURCES)
    if sales and not args.brouillon:
        sys.exit("Sources non commitées (commiter, ou --brouillon) :\n" + sales)
    clingcon = shutil.which("clingcon", path=str(CONDA_BIN))
    if not clingcon:
        sys.exit("clingcon introuvable dans .conda/bin : créer l'environnement (annexe A).")
    v_clingcon = sortie_de([clingcon, "--version"]).splitlines()[0]
    if "5.2.1" not in v_clingcon:
        print(f"Attention : {v_clingcon} (5.2.1 attendu)", file=sys.stderr)
    import numpy, scipy, pandas, matplotlib
    cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo")
                if l.startswith("model name")), platform.processor())
    mem = next((l.split()[1] for l in open("/proc/meminfo") if l.startswith("MemTotal")), "?")
    man["env"] = {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "commit": commit,
        "sources_propres": not sales,
        "sources_modifiees": sales.splitlines(),
        "machine": {"cpu": cpu, "coeurs": os.cpu_count(), "memoire_Go": round(int(mem) / 2**20, 1),
                    "noyau": platform.release()},
        "versions": {
            "clingcon": v_clingcon,
            "java": sortie_de(["java", "-version"]).splitlines()[0],
            "javac": sortie_de(["javac", "-version"]),
            "gcc": sortie_de(["gcc", "--version"]).splitlines()[0],
            "python": platform.python_version(),
            "numpy": numpy.__version__, "scipy": scipy.__version__,
            "pandas": pandas.__version__, "matplotlib": matplotlib.__version__,
        },
    }


def etape_compilation(sortie, man, args):
    bin_jpp = sortie / "bin" / "jpp"
    if (bin_jpp / "PSBN" / "Main.class").exists() and not args.refaire:
        print("  compilation : déjà faite")
        return
    shutil.rmtree(bin_jpp, ignore_errors=True)
    bin_jpp.mkdir(parents=True)
    sources = sorted(str(p) for p in (REPO / "JPPipeline/src/java_src/PSBN").rglob("*.java"))
    logs = sortie / "logs"
    lancer(["javac", "-cp", JPP_JAR, "-d", bin_jpp] + sources, logs / "javac.log")
    lancer(["make", "-B"], logs / "make_mcsbn.log", cwd=REPO / "MCSBN")
    lancer(["make", "drgraph"], logs / "make_drgraph.log", cwd=REPO / "MCSBN")
    man["compilation"] = {"commit": man["env"]["commit"], "date": time.strftime("%Y-%m-%d %H:%M:%S")}


def lancer_jpp(sortie, prog, d, dossier, journal):
    """Une exécution de JPP ; renvoie (chemin du CSV brut, durée)."""
    shutil.rmtree(dossier, ignore_errors=True)
    dossier.mkdir(parents=True)
    cmd = ["java", "-cp", f"{sortie / 'bin' / 'jpp'}{os.pathsep}{JPP_JAR}", "PSBN.Main",
           str(d), ASP / f"{prog}.lp", ASP, "0", dossier, "1"]
    duree = lancer(cmd, journal)
    if "Exception" in journal.read_text(errors="replace"):
        sys.exit(f"JPP a levé une exception, voir {journal}")
    return dossier / f"{d}d_{prog}_output.csv", duree


def etape_jpp(sortie, man, args):
    csvdir = sortie / "csv"
    csvdir.mkdir(parents=True, exist_ok=True)
    for prog, d in JPP_RUNS:
        nom = f"{d}d_{prog}_output.csv.gz"
        if (csvdir / nom).exists() and not args.refaire:
            print(f"  {nom} : déjà généré")
            continue
        brut, duree = lancer_jpp(sortie, prog, d, sortie / "tmp" / "jpp",
                                 sortie / "logs" / f"jpp_{d}d_{prog}.log")
        texte, n = trier_csv(lire_texte(brut))
        ecrire_gzip(csvdir / nom, texte)
        man["jpp"][nom] = {"commit": man["env"]["commit"], "lignes": n,
                           "duree_s": round(duree, 2), "sha256": sha256(texte)}
        man.sauver()
        print(f"  {nom} : {n} lignes en {duree:.1f} s")
    shutil.rmtree(sortie / "tmp" / "jpp", ignore_errors=True)


def etape_mcsbn(sortie, man, args):
    csvdir = sortie / "csv"
    csvdir.mkdir(parents=True, exist_ok=True)
    for d in MCSBN_DIMS:
        nom = f"{d}d_MCSBN_variety_{MCSBN_N}.csv.gz"
        if (csvdir / nom).exists() and not args.refaire:
            print(f"  {nom} : déjà généré")
            continue
        cmd = [REPO / "MCSBN/bin/mcsbn", "-d", d, "-n", MCSBN_N, "--measure", "variety",
               "--no-progress", "-o", csvdir / nom]
        duree = lancer(cmd, sortie / "logs" / f"mcsbn_{d}d.log")
        texte = lire_texte(csvdir / nom)
        man["mcsbn"][nom] = {"commit": man["env"]["commit"], "lignes": texte.count("\n") - 1,
                             "duree_s": round(duree, 2), "sha256": sha256(texte)}
        man.sauver()
        print(f"  {nom} : {duree:.1f} s")


def etape_metagraphe(sortie, man, args):
    src = sortie / "csv" / METAGRAPHE_CSV
    dest = sortie / "csv" / METAGRAPHE_CSV.replace(".csv.gz", "_metagraph.csv.gz")
    if dest.exists() and not args.refaire:
        print(f"  {dest.name} : déjà généré")
        return
    script = REPO / "MCSBN/src/python/add_metagraph_layout.py"
    essais = [dest, sortie / "tmp" / "metagraphe_bis.csv.gz"]
    essais[1].parent.mkdir(parents=True, exist_ok=True)
    durees = [lancer([sys.executable, script, src, "-o", out] + METAGRAPHE_OPTS,
                     sortie / "logs" / f"metagraphe_{k}.log") for k, out in enumerate(essais, 1)]
    textes = [lire_texte(p) for p in essais]
    log = (sortie / "logs" / "metagraphe_1.log").read_text()
    graphe = next((l.strip() for l in log.splitlines() if "aretes=" in l), "")
    man["metagraphe"] = {"commit": man["env"]["commit"], "fichier": dest.name,
                         "options": " ".join(METAGRAPHE_OPTS), "graphe": graphe,
                         "reproductible": textes[0] == textes[1],
                         "duree_s": round(durees[0], 1), "sha256": sha256(textes[0])}
    essais[1].unlink()
    print(f"  {dest.name} : {graphe} ; deux placements identiques : {textes[0] == textes[1]}")


def etape_fiches(sortie, man, args):
    dest = sortie / "fiches" / "fiches.json"
    if dest.exists() and not args.refaire:
        print("  fiches : déjà calculées")
        return
    sys.path.insert(0, str(ICI))
    import fiches
    resultats = fiches.toutes(sortie / "csv", sortie / "fiches")
    dest.write_text(json.dumps(resultats, indent=1, ensure_ascii=False) + "\n")
    man["fiches"] = {"commit": man["env"]["commit"], "date": time.strftime("%Y-%m-%d %H:%M:%S")}


def etape_temps(sortie, man, args):
    dest = sortie / "temps" / "temps.json"
    if dest.exists() and not args.refaire:
        print("  temps : déjà mesurés")
        return
    sys.path.insert(0, str(ICI))
    import temps
    resultats = temps.toutes(sortie, args.repetitions, env_conda())
    resultats["machine"] = man["env"]["machine"]
    dest.write_text(json.dumps(resultats, indent=1, ensure_ascii=False) + "\n")
    man["temps"] = {"commit": man["env"]["commit"], "date": time.strftime("%Y-%m-%d %H:%M:%S")}


def etape_resume(sortie, man, args):
    sys.path.insert(0, str(ICI))
    import resume
    (sortie / "resume.md").write_text(resume.rediger(sortie, man.data))
    print(f"  {sortie / 'resume.md'}")


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sortie", type=Path, default=ICI / "sortie", help="dossier de sortie (non versionné)")
    ap.add_argument("--etapes", default=",".join(ETAPES[1:]),
                    help="étapes à exécuter, séparées par des virgules (toutes par défaut)")
    ap.add_argument("--refaire", action="store_true", help="refait les étapes même si leur sortie existe")
    ap.add_argument("--repetitions", type=int, default=5,
                    help="répétitions des mesures courtes de O1, dont on garde la médiane (5)")
    ap.add_argument("--brouillon", action="store_true", help="accepte des sources non commitées")
    args = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)  # progression visible même redirigée

    etapes =[e.strip() for e in args.etapes.split(",") if e.strip()]
    inconnues = set(etapes) - set(ETAPES)
    if inconnues:
        sys.exit(f"Étapes inconnues : {', '.join(sorted(inconnues))} (possibles : {', '.join(ETAPES)})")
    sortie = args.sortie.resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    man = Manifeste(sortie)

    for e in ["env"] + [e for e in ETAPES[1:] if e in etapes]:
        print(f"== {e}")
        globals()[f"etape_{e}"](sortie, man, args)
        man.sauver()


if __name__ == "__main__":
    main()
