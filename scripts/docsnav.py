#!/usr/bin/env python3
"""features/docs-experience — edit docs.json navigation without hand-editing JSON.

  scripts/docsnav.py place PAGE "Tab" "Group" [--sub "Subgroup"] [--after PAGE | --first]
  scripts/docsnav.py remove PAGE
  scripts/docsnav.py tree            # print tabs > groups > pages (counts)

`place` is idempotent: it moves PAGE if it is already in the tree. Tabs and groups are created on demand in
call order, so build a section top-to-bottom. docs.json stays the single source of truth (CLAUDE.md).
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = f"{ROOT}/docs.json"

def load(): return json.load(open(P))
def save(cfg):
    json.dump(cfg, open(P, "w"), indent=2, ensure_ascii=False); open(P, "a").write("\n")

def strip(node, page):
    pages = node["pages"]
    for i in list(pages):
        if isinstance(i, str) and i.lstrip("/") == page: pages.remove(i)
        elif isinstance(i, dict): strip(i, page)

def remove(cfg, page):
    for t in cfg["navigation"]["tabs"]:
        for g in t.get("groups", []): strip(g, page)

def place(cfg, page, tab, group, sub=None, after=None, first=False):
    remove(cfg, page)
    tabs = cfg["navigation"]["tabs"]
    t = next((x for x in tabs if x["tab"] == tab), None)
    if t is None: t = {"tab": tab, "groups": []}; tabs.append(t)
    g = next((x for x in t["groups"] if x["group"] == group), None)
    if g is None: g = {"group": group, "pages": []}; t["groups"].append(g)
    node = g
    if sub:
        node = next((x for x in g["pages"] if isinstance(x, dict) and x.get("group") == sub), None)
        if node is None: node = {"group": sub, "pages": []}; g["pages"].append(node)
    pages = node["pages"]
    if first: pages.insert(0, page)
    elif after:
        idx = next((i for i, x in enumerate(pages) if x == after), None)
        if idx is None: pages.append(page)
        else: pages.insert(idx + 1, page)
    else: pages.append(page)

def count(node): return sum(count(i) if isinstance(i, dict) else 1 for i in node["pages"])

def main():
    cfg = load(); a = sys.argv[1:]
    if a[0] == "tree":
        for t in cfg["navigation"]["tabs"]:
            print(f"{t['tab']}")
            for g in t.get("groups", []): print(f"  {g['group']} ({count(g)})")
        return
    if a[0] == "remove": remove(cfg, a[1]); save(cfg); return
    if a[0] == "place":
        page, tab, group = a[1:4]; rest = a[4:]
        sub = rest[rest.index("--sub") + 1] if "--sub" in rest else None
        after = rest[rest.index("--after") + 1] if "--after" in rest else None
        place(cfg, page, tab, group, sub, after, "--first" in rest); save(cfg); return
    sys.exit(__doc__)

if __name__ == "__main__": main()
