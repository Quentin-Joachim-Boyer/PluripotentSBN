"""
Rédige <sortie>/resume.md à partir du manifeste, de fiches/fiches.json et de
temps/temps.json : ce que la passe a produit, les nombres des fiches (attendu /
obtenu), les lignes à capturer et les mesures de la fiche O1.
"""

import json


def nombre(x):
    if isinstance(x, bool):
        return "oui" if x else "non"
    if isinstance(x, float):
        return f"{x:.4g}".replace(".", ",")
    if isinstance(x, int):
        return f"{x:,}".replace(",", " ")
    if isinstance(x, (list, dict)):
        return json.dumps(x, ensure_ascii=False)
    return "" if x is None else str(x)


def marque(ok):
    return {True: "✓", False: "**ÉCART**", None: ""}[ok]


def rediger(sortie, man):
    L = ["# Passe unifiée : résumé", ""]
    env = man.get("env", {})
    L.append(f"- Date : {env.get('date')} ; commit `{env.get('commit', '')[:7]}`.")
    if not env.get("sources_propres", True):
        L.append("- **Sources non commitées** (passe en brouillon) : "
                 + ", ".join(f"`{s.strip()}`" for s in env.get("sources_modifiees", [])) + ".")
    m = env.get("machine", {})
    L.append(f"- Machine : {m.get('cpu')}, {m.get('coeurs')} cœurs, {nombre(m.get('memoire_Go'))} Go, "
             f"noyau {m.get('noyau')}.")
    v = env.get("versions", {})
    L.append(f"- Versions : {v.get('clingcon')} ; {v.get('java')} ; {v.get('gcc')} ; Python {v.get('python')}.")
    commits = {s.get("commit") for k, s in man.items() if isinstance(s, dict) and "commit" in s and k != "env"}
    for groupe in ("jpp", "mcsbn"):
        commits |= {s.get("commit") for s in man.get(groupe, {}).values()}
    commits.discard(None)
    if len(commits) > 1:
        L.append(f"- **Étapes faites à des commits différents** : {', '.join(c[:7] for c in sorted(commits))} "
                 "(relancer avec --refaire).")
    L.append("")

    L += ["## Générations", "", "| Fichier (`csv/`) | Lignes | Durée (s) |", "|---|---:|---:|"]
    for groupe in ("jpp", "mcsbn"):
        for nom, s in man.get(groupe, {}).items():
            L.append(f"| `{nom}` | {nombre(s['lignes'])} | {nombre(s['duree_s'])} |")
    mg = man.get("metagraphe")
    if mg:
        L += ["", f"Métagraphe (M2, OL4) : `csv/{mg['fichier']}`, options `{mg['options']}`, {mg['graphe']}. "
                  f"Deux placements identiques : {nombre(mg['reproductible'])}."]
    L.append("")

    fichier_fiches = sortie / "fiches" / "fiches.json"
    ecarts = []
    if fichier_fiches.exists():
        L += ["## Fiches", "",
              "Les fichiers à capturer sont dans `fiches/` ; « n° » est le rang de la ligne dans le CSV "
              "complet de `csv/`, trié (T1).", ""]
        for F in json.loads(fichier_fiches.read_text()):
            L += [f"### {F['fiche']}. {F['titre']}", "", "| Compte | Attendu | Obtenu | |", "|---|---:|---:|---|"]
            for c in F["comptes"]:
                L.append(f"| {c['quoi']} | {nombre(c['attendu'])} | {nombre(c['obtenu'])} | {marque(c['ok'])} |")
                if c["ok"] is False:
                    ecarts.append(f"{F['fiche']} : {c['quoi']} (attendu {nombre(c['attendu'])}, "
                                  f"obtenu {nombre(c['obtenu'])})")
            L.append("")
            for fi in F["fichiers"]:
                L.append(f"Fichier `fiches/{fi['fichier']}`, tiré de `csv/{fi['source']}`"
                         + (f" ({fi['legende']})" if fi["legende"] else "") + " :")
                for l in fi["lignes"]:
                    arbre = f", arbre `{l['arbre']}`" if l["arbre"] else ""
                    alerte = "" if l["poids_realisent_f"] else " **les poids ne réalisent pas f**"
                    L.append(f"- n° {nombre(l['n'])} : {l['vecteur']}{arbre}, poids {l['poids']}{alerte}")
                L.append("")
            for n in F["notes"]:
                L += [f"> {n}", ""]

    fichier_temps = sortie / "temps" / "temps.json"
    if fichier_temps.exists():
        T = json.loads(fichier_temps.read_text())
        L += ["## Mesures de temps (O1)", "",
              f"Médiane de {T['repetitions']} essais pour les mesures complètes de moins de 10 s, un essai "
              f"sinon ; mémoire bornée à {nombre(T['memoire_max_ko'] // 1000)} Mo. « clingcon » : temps "
              "affiché par clingcon ; « mur » : durée de l'appel, lancement compris.", "",
              "### O1a. Structure contre poids, ⟨0,2,0,0⟩, d = 3", "",
              "| Programme | Dynamiques | clingcon (s) | mur (s) |", "|---|---:|---:|---:|",
              f"| {T['laurent']['programme']} | {T['laurent']['modeles']} | "
              f"{nombre(T['laurent']['temps_clingcon_s'])} | |"]
        for r in T["O1a"]:
            L.append(f"| `{r['nom']}` | {etat(r)} | {nombre(r['temps_clingcon_s'])} | {nombre(r['mur_s'])} |")
        L += ["", "### O1b. Formulations de `PSBN_undercontrol_taggedtree.lp`", "",
              "| Mesure | Résultat | clingcon (s) | mur (s) |", "|---|---:|---:|---:|"]
        for r in T["O1b"]:
            L.append(f"| {r['nom']} | {etat(r)} | {nombre(r['temps_clingcon_s'])} | {nombre(r['mur_s'])} |")
        L += ["", "### O1c. Parallélisme, énumération globale PSBN taggedtree, d = 3", "",
              "| Moteur | Dynamiques | mur (s) | Accélération |", "|---|---:|---:|---:|"]
        base = next((r["mur_s"] for r in T["O1c"] if r["parallel"] == 1), None)
        for r in T["O1c"]:
            acc = nombre(round(base / r["mur_s"], 2)) if base and r["mur_s"] else ""
            L.append(f"| {r['nom']} | {etat(r)} | {nombre(r['mur_s'])} | ×{acc} |")
        for r in T["O1a"] + T["O1b"] + T["O1c"]:
            if r["attendu"] is not None and r["modeles"] != r["attendu"] and not r["memoire_saturee"]:
                ecarts.append(f"O1 : {r['nom']} (attendu {nombre(r['attendu'])}, obtenu {etat(r)})")
        L.append("")

    L += ["## Écarts", ""] + ([f"- {e}" for e in ecarts] or ["Aucun."]) + [""]
    return "\n".join(L)


def etat(r):
    if r["memoire_saturee"]:
        return "mémoire saturée"
    if r["modeles"] is None:
        return f"échec (code {r['code']})"
    return nombre(r["modeles"]) + ("" if r["complet"] else "+")
