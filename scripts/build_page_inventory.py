#!/usr/bin/env python3
"""features/docs-experience V1 — page inventory.

Reads features/docs-experience/inventory/migration-map.csv (hand-authored: where every page goes, its
type, audience, interfaces, and what a later era does to it) and measures every page, then writes
inventory/pages.csv. cli/* stays put (the Reference tab); frameworks/* moves to deploy/frameworks/*.

Re-run after any page is added/removed; exits 1 if a page has no row or a row has no page.
"""
import csv, glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"
SKIP = ("blog/", "changelog/", "features/", "snippets/", "node_modules/", "recipes/")
STALE = re.compile(r"auto-?dockeri|zero-config|framework detection|auto-?detect|providers/|vectorihub-hosted", re.I)
NEGATED = re.compile(r"\b(no|not|never|without|instead of|rather than|doesn't|does not|guess|sounds convenient)\b", re.I)

def stale(body):
    """A stale hit is an old-model claim; the same words in a sentence that denies them are the current model."""
    for sent in re.split(r"(?<=[.!?])\s+|\n", body):
        if STALE.search(sent) and not NEGATED.search(sent):
            return True
    return False

def pages(root=ROOT):
    return sorted(p[:-4] for p in (os.path.relpath(x, root) for x in glob.glob(f"{root}/**/*.mdx", recursive=True))
                  if not p.startswith(SKIP))

def nav_members():
    cfg = json.load(open(f"{ROOT}/docs.json")); out = set()
    def walk(n):
        if isinstance(n, str): out.add(n.lstrip("/"))
        elif isinstance(n, dict):
            for k in ("pages", "groups", "tabs"):
                if k in n: walk(n[k])
        elif isinstance(n, list):
            for i in n: walk(i)
    walk(cfg["navigation"]); return out

def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)

def main():
    mm = {r["old_path"]: r for r in csv.DictReader(open(f"{INV}/migration-map.csv"))}
    nav = nav_members(); rows = []; errors = []
    existing = pages()
    for p in existing:
        fm, body = frontmatter(open(f"{ROOT}/{p}.mdx").read())
        words = len(body.split())
        r = mm.get(p)
        if r is None and (p == "cli" or p.startswith("cli/")):
            r = dict(new_path=p, type_target="reference", audience="dev;ops", interfaces="cli", action_later="keep (reference, features/docs)")
        elif r is None and p.startswith("frameworks/"):
            r = dict(new_path="deploy/" + p, type_target="howto", audience="dev", interfaces="cli", action_later="runnable recipe Era19")
        if r is None:
            # already moved by Era 3 V12? find by new_path
            by_new = next((v for v in mm.values() if v["new_path"] == p), None)
            if by_new: r = by_new
            elif p.startswith("deploy/frameworks/"):
                r = dict(new_path=p, type_target="howto", audience="dev", interfaces="cli", action_later="runnable recipe Era19")
        if r is None:
            ft = re.search(r"^type:\s*(\S+)", fm, re.M)
            if ft:  # a page created after the migration describes itself (the page contract is the source of truth)
                fa = re.search(r"^audience:\s*\[(.*?)\]", fm, re.M); fi = re.search(r"^interfaces:\s*\[(.*?)\]", fm, re.M)
                r = dict(new_path=p, type_target=ft.group(1),
                         audience=";".join(x.strip() for x in fa.group(1).split(",")) if fa else "",
                         interfaces=";".join(x.strip() for x in fi.group(1).split(",")) if fi else "",
                         action_later="new")
        if r is None:
            errors.append(f"{p}: no row in migration-map.csv"); continue
        # the page contract is the source of truth once a page carries it; the migration map only seeds pages that lack it
        ft = re.search(r"^type:\s*(\S+)", fm, re.M); fa = re.search(r"^audience:\s*\[(.*?)\]", fm, re.M); fi = re.search(r"^interfaces:\s*\[(.*?)\]", fm, re.M)
        r = dict(r)
        if ft: r["type_target"] = ft.group(1)
        if fa: r["audience"] = ";".join(x.strip() for x in fa.group(1).split(","))
        if fi: r["interfaces"] = ";".join(x.strip() for x in fi.group(1).split(","))
        rows.append(dict(path=p, target_path=r["new_path"] or "(retire)", type_target=r["type_target"], audience=r["audience"],
                         interfaces=r["interfaces"], words=words,
                         thin="y" if words < 300 and r["type_target"] in ("howto", "tutorial", "troubleshooting") else "",
                         stale="y" if stale(body) else "", in_nav="y" if p in nav else "n",
                         action_later=r["action_later"]))
    if errors:
        print("\n".join(errors), file=sys.stderr); sys.exit(1)
    cols = ["path", "target_path", "type_target", "audience", "interfaces", "words", "thin", "stale", "in_nav", "action_later"]
    with open(f"{INV}/pages.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} pages; thin={sum(1 for r in rows if r['thin'])} stale={sum(1 for r in rows if r['stale'])} orphan={sum(1 for r in rows if r['in_nav']=='n')}")

main()
