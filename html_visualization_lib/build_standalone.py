#!/usr/bin/env python3
"""
Génère des HTML AUTONOMES (toutes les ressources locales inlinées) à la RACINE DU GIT,
à partir des fichiers de développement de ce dossier (html_visualization_lib/).

Le dev travaille sur les HTML d'ici (qui référencent les libs externes sbn-*.js/css et
metagraph_lib/) ; ce script produit, à la racine, des copies portables (un seul fichier,
ouvrable et partageable tel quel, sans le dossier html_visualization_lib).

Sont inlinés :
  - <link rel="stylesheet" href="local.css">      -> <style>…</style>
  - <script src="local.js"></script>              -> <script>…</script>
Les URL http(s) (ex. la police Google via @import) et les ressources introuvables
sont laissées telles quelles.

Usage : python build_standalone.py
"""
import re
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent      # html_visualization_lib/
ROOT    = LIB_DIR.parent                        # racine du dépôt git
DEV_HTMLS = ["metagraphe.html", "sbn_scatter.html", "sbn_viz.html"]

_EXTERNAL = ("http://", "https://", "//", "data:")


def _read_local(ref: str):
    """Lit la ressource locale `ref` relative au dossier des libs. None si externe/introuvable."""
    if ref.startswith(_EXTERNAL):
        return None
    p = (LIB_DIR / ref).resolve()
    if not p.is_file():
        print(f"  ⚠ ressource introuvable, laissée en lien : {ref}")
        return None
    return p.read_text(encoding="utf-8")


def _guard_script(content: str) -> str:
    """Neutralise un éventuel </script> dans du JS inliné (ne casse pas le parseur HTML)."""
    return re.sub(r"</(script)", r"<\\/\1", content, flags=re.IGNORECASE)


def inline(html: str) -> str:
    # 1) <link rel="stylesheet" href="…">  (rel avant href OU href avant rel)
    def css_repl(m):
        ref = m.group("href")
        css = _read_local(ref)
        if css is None:
            return m.group(0)
        return f"<style>\n/* inliné depuis {ref} */\n{css}\n</style>"

    link_rel_href = re.compile(
        r'<link\b[^>]*\brel=["\']stylesheet["\'][^>]*\bhref=["\'](?P<href>[^"\']+)["\'][^>]*>',
        re.IGNORECASE)
    link_href_rel = re.compile(
        r'<link\b[^>]*\bhref=["\'](?P<href>[^"\']+)["\'][^>]*\brel=["\']stylesheet["\'][^>]*>',
        re.IGNORECASE)
    html = link_rel_href.sub(css_repl, html)
    html = link_href_rel.sub(css_repl, html)

    # 2) <script src="…"></script>
    def js_repl(m):
        ref = m.group("src")
        js = _read_local(ref)
        if js is None:
            return m.group(0)
        return f"<script>\n/* inliné depuis {ref} */\n{_guard_script(js)}\n</script>"

    script_src = re.compile(
        r'<script\b[^>]*\bsrc=["\'](?P<src>[^"\']+)["\'][^>]*>\s*</script>',
        re.IGNORECASE)
    html = script_src.sub(js_repl, html)
    return html


def main():
    ok = 0
    for name in DEV_HTMLS:
        src = LIB_DIR / name
        if not src.is_file():
            print(f"⚠ source de dev manquante : {src}")
            continue
        print(f"• {name}")
        out_html = inline(src.read_text(encoding="utf-8"))
        # garde-fou : il ne doit plus rester de <script src=…> ou <link …stylesheet…> LOCAL
        leftover = re.findall(r'<(?:script\b[^>]*\bsrc|link\b[^>]*\bhref)=["\']([^"\']+)["\']', out_html)
        local_left = [r for r in leftover if not r.startswith(_EXTERNAL)]
        if local_left:
            print(f"  ⚠ liens locaux NON inlinés : {local_left}")
        dst = ROOT / name
        dst.write_text(out_html, encoding="utf-8")
        print(f"  → {dst}")
        ok += 1
    print(f"\nTerminé : {ok}/{len(DEV_HTMLS)} HTML autonomes générés à la racine ({ROOT}).")
    return 0 if ok == len(DEV_HTMLS) else 1


if __name__ == "__main__":
    sys.exit(main())
