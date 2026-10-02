#!/usr/bin/env python3
"""features/docs-experience — retire a page that a later era merged into another.

  scripts/merge_page.py OLD NEW      # slugs without leading slash or .mdx

Does, in one step: git rm OLD.mdx; rewrite every internal link /OLD -> /NEW (blog/ and changelog/ are left alone; their old links
keep working through the redirect); append "/OLD,/NEW" to inventory/redirects-later.csv; remove OLD from docs.json navigation;
regenerate docs.json `redirects`. The merged content must already be in NEW — this tool never edits NEW's body.
"""
import glob, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/scripts")
import docsnav

def main():
    old, new = sys.argv[1].strip("/"), sys.argv[2].strip("/")
    if not os.path.exists(f"{ROOT}/{new}.mdx"): sys.exit(f"{new}.mdx does not exist — write the merged page first")
    pat = re.compile(r"(\]\(|href=[\"'])/" + re.escape(old) + r"(?=[#)\"'?])")
    n = 0
    for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(("features/", "node_modules/", "blog/", "changelog/")): continue
        t = open(f).read(); t2, c = pat.subn(lambda m: f"{m.group(1)}/{new}", t)
        if c: open(f, "w").write(t2); n += c
    if os.path.exists(f"{ROOT}/{old}.mdx"):
        subprocess.run(["git", "rm", "-q", "-f", f"{old}.mdx"], check=True, cwd=ROOT)
    cfg = docsnav.load(); docsnav.remove(cfg, old); docsnav.save(cfg)
    csv = f"{ROOT}/features/docs-experience/inventory/redirects-later.csv"
    lines = open(csv).read().splitlines()
    if f"/{old},/{new}" not in lines: open(csv, "a").write(f"/{old},/{new}\n")
    subprocess.run([sys.executable, f"{ROOT}/scripts/gen_redirects.py"], check=True, cwd=ROOT)
    print(f"merged {old} -> {new}; {n} links rewritten")

main()
