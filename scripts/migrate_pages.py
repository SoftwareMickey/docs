#!/usr/bin/env python3
"""features/docs-experience V12 — execute the page move described by inventory/migration-map.csv.

  scripts/migrate_pages.py --dry-run     report what would move and how many links change
  scripts/migrate_pages.py               git mv every page, delete retired pages, rewrite every internal link

1:1 moves only (Invariant 1): no page is merged, split or rewritten here. Links are rewritten in every
MDX file and snippet except features/; blog/ and changelog/ are historical records and are NOT edited —
their old links keep working through docs.json `redirects` (scripts/gen_redirects.py).
"""
import csv, glob, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"
HISTORICAL = ("blog/", "changelog/")

def load_map():
    m, retired = {}, []
    for r in csv.DictReader(open(f"{INV}/migration-map.csv")):
        if not r["new_path"]: retired.append(r["old_path"])
        elif r["old_path"] != r["new_path"]: m[r["old_path"]] = r["new_path"]
    for f in glob.glob(f"{ROOT}/frameworks/*.mdx"):
        slug = os.path.basename(f)[:-4]; m[f"frameworks/{slug}"] = f"deploy/frameworks/{slug}"
    return m, retired

def main():
    dry = "--dry-run" in sys.argv
    mapping, retired = load_map()
    olds = sorted(mapping, key=len, reverse=True)
    pat = re.compile(r"(\]\(|href=[\"'])/(" + "|".join(re.escape(o) for o in olds) + r")(?=[#)\"'?])")
    changed_files = n_links = 0
    for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(("features/", "node_modules/") + HISTORICAL): continue
        t = open(f).read()
        new, n = pat.subn(lambda m: f"{m.group(1)}/{mapping[m.group(2)]}", t)
        if n:
            changed_files += 1; n_links += n
            if not dry: open(f, "w").write(new)
    print(f"{len(mapping)} moves, {len(retired)} retired; {n_links} links in {changed_files} files")
    if dry: return
    for old, new in mapping.items():
        src, dst = f"{ROOT}/{old}.mdx", f"{ROOT}/{new}.mdx"
        if not os.path.exists(src): print(f"skip (already moved): {old}"); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(["git", "mv", src, dst], check=True, cwd=ROOT)
    for old in retired:
        if os.path.exists(f"{ROOT}/{old}.mdx"):
            subprocess.run(["git", "rm", "-q", f"{old}.mdx"], check=True, cwd=ROOT)

main()
