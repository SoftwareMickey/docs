#!/usr/bin/env python3
"""features/docs-experience V113 — typo gate. Prose only (fenced and inline code are exempt). A curated list of common misspellings
(features/docs-experience/inventory/typos.txt: `wrong<TAB>right`); the product vocabulary is never flagged because only listed typos fail.
  check-spelling.py            scan published pages
  check-spelling.py --fixture  prove the gate fires on a seeded typo
"""
import os, re, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ("blog/", "changelog/", "features/", "snippets/data/", "node_modules/", "recipes/", ".git/")
TYPOS = f"{ROOT}/features/docs-experience/inventory/typos.txt"


def typos():
    out = {}
    for line in open(TYPOS):
        if line.strip() and not line.startswith("#"):
            a, _, b = line.rstrip("\n").partition("\t"); out[a.lower()] = b
    return out


def prose(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"\{/\*.*?\*/\}", "", text, flags=re.S)


def scan(root=ROOT):
    t = typos(); rx = re.compile(r"\b(" + "|".join(map(re.escape, t)) + r")\b", re.I); hits = []
    for dp, dn, fs in os.walk(root):
        rel = os.path.relpath(dp, root) + "/"
        if rel.startswith(SKIP) or ".git/" in rel or "node_modules/" in rel: dn[:] = []; continue
        for f in fs:
            if not f.endswith(".mdx"): continue
            path = os.path.normpath(os.path.join(rel, f))
            for n, line in enumerate(prose(open(f"{root}/{path}", errors="replace").read()).splitlines(), 1):
                for m in rx.finditer(line): hits.append(f"{path}: {m.group(0)!r} -> {t[m.group(0).lower()]!r}")
    return hits


def main():
    if "--fixture" in sys.argv:
        import tempfile
        d = tempfile.mkdtemp(); os.makedirs(f"{d}/features/docs-experience/inventory"); os.makedirs(f"{d}/deploy")
        open(f"{d}/features/docs-experience/inventory/typos.txt", "w").write("recieve\treceive\n")
        open(f"{d}/deploy/a.mdx", "w").write("---\ntitle: x\n---\nYou will recieve it. `recieve` in code is fine.\n")
        h = scan(d)
        ok = len(h) == 1
        print(("PASS" if ok else "FAIL") + "  a seeded typo is caught exactly once"); return 0 if ok else 1
    hits = scan()
    for h in hits: print("TYPO  " + h)
    print(f"spelling: {len(hits)} typo(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
