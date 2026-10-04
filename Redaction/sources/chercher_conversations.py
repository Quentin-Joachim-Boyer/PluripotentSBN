"""
Recherche dans les conversations Claude Code du projet (fichiers .jsonl).

Ne garde que le dialogue (messages de Quentin et réponses texte de Claude),
sans les appels d'outils ni leurs résultats, qui font l'essentiel du volume.

Usage :
    python3 chercher_conversations.py "motif" [--session a589] [--role user]
                                              [--contexte 1] [--max 20] [--largeur 600]

Le motif est une expression régulière, insensible à la casse.
"""

import argparse
import glob
import json
import os
import re

DOSSIER = os.path.expanduser("~/.claude/projects/-home-quentin-boyer-Bureau-asp-PSBN")
BALISES = re.compile(
    r"<(ide_opened_file|ide_selection|system-reminder|command-[a-z]+|local-command-[a-z]+)>.*?</\1>",
    re.S)


def texte(message):
    contenu = message.get("content")
    if isinstance(contenu, str):
        return contenu
    return "\n".join(p.get("text", "") for p in contenu or []
                     if isinstance(p, dict) and p.get("type") == "text")


def dialogue(chemin):
    with open(chemin, errors="replace") as f:
        for ligne in f:
            try:
                e = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            if e.get("type") not in ("user", "assistant") or not isinstance(e.get("message"), dict):
                continue
            t = BALISES.sub("", texte(e["message"])).strip()
            if t:
                yield e.get("timestamp", "")[:16].replace("T", " "), e["type"], t


def extrait(t, motif, largeur):
    t = " ".join(t.split())
    if len(t) <= largeur:
        return t
    m = motif.search(t)
    debut = max(0, (m.start() if m else 0) - largeur // 3)
    fin = debut + largeur
    return ("…" if debut else "") + t[debut:fin] + ("…" if fin < len(t) else "")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("motif")
    p.add_argument("--session", default="", help="préfixe de l'identifiant de session (ex. a589)")
    p.add_argument("--role", choices=["user", "assistant"], help="ne chercher que chez Quentin (user) ou Claude (assistant)")
    p.add_argument("--contexte", type=int, default=0, help="nombre de messages affichés avant et après chaque résultat")
    p.add_argument("--max", type=int, default=20, help="nombre maximal de résultats")
    p.add_argument("--largeur", type=int, default=600, help="caractères affichés par message")
    p.add_argument("--dossier", default=DOSSIER)
    a = p.parse_args()

    motif = re.compile(a.motif, re.I)
    trouves = 0
    for chemin in sorted(glob.glob(os.path.join(a.dossier, a.session + "*.jsonl"))):
        sid = os.path.basename(chemin)[:8]
        msgs = list(dialogue(chemin))
        for i, (ts, role, t) in enumerate(msgs):
            if (a.role and role != a.role) or not motif.search(t):
                continue
            print(f"===== {sid}  {ts}")
            for j in range(max(0, i - a.contexte), min(len(msgs), i + a.contexte + 1)):
                qui = "Quentin" if msgs[j][1] == "user" else "Claude"
                print(f"[{qui}] {extrait(msgs[j][2], motif, a.largeur)}")
            trouves += 1
            if trouves >= a.max:
                print(f"... arrêt à {a.max} résultats (--max)")
                return
    print(f"{trouves} résultat(s)")


if __name__ == "__main__":
    main()
