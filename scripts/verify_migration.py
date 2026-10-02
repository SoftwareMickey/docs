#!/usr/bin/env python3
"""features/docs-experience V12 — prove a move changed only links.

  scripts/verify_migration.py snapshot   # before: hash every page with internal link targets masked
  scripts/verify_migration.py verify     # after: every moved page has the same hash at its new path

Masking replaces the target of absolute internal links with LINK, so a pass means the diff is renames +
link rewrites only (headings, prose, code and frontmatter byte-identical).
"""
import csv, glob, hashlib, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"
SNAP = f"{INV}/.migration-snapshot.json"
MASK = re.compile(r"(\]\(|href=[\"'])/[^)\"'\s#?]*")

def digest(path):
    t = MASK.sub(r"\1/LINK", open(path).read())
    return hashlib.sha256(t.encode()).hexdigest()

def pages():
    for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(("features/", "node_modules/")): continue
        yield rel[:-4], f

def mapping():
    m = {r["old_path"]: r["new_path"] for r in csv.DictReader(open(f"{INV}/migration-map.csv"))}
    for p in glob.glob(f"{ROOT}/deploy/frameworks/*.mdx"): m[f"frameworks/{os.path.basename(p)[:-4]}"] = f"deploy/frameworks/{os.path.basename(p)[:-4]}"
    return m

if sys.argv[1] == "snapshot":
    json.dump({p: digest(f) for p, f in pages()}, open(SNAP, "w"))
    print("snapshot of", len(list(pages())), "pages")
else:
    snap = json.load(open(SNAP)); m = mapping(); bad = 0; ok = 0
    for old, h in snap.items():
        new = m.get(old, old)
        if not new:
            print("retired:", old); continue
        f = f"{ROOT}/{new}.mdx"
        if not os.path.exists(f): print("MISSING", old, "->", new); bad += 1; continue
        if digest(f) != h: print("CHANGED", old, "->", new); bad += 1
        else: ok += 1
    print(f"{ok} identical, {bad} problems"); sys.exit(1 if bad else 0)
