#!/usr/bin/env python3
"""features/docs-experience V11 — write docs.json `redirects` from the migration map.

Every old path that moved or merged redirects to its new home (Invariant 9). Re-run after any change to
inventory/migration-map.csv, inventory/redirects-extra.csv, or inventory/redirects-later.csv (pages that a
later era merged/renamed: old,new). Existing manual redirects in docs.json are not preserved on purpose —
those three CSVs are the source of truth.
"""
import csv, glob, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"

def rows():
    out = {}
    for r in csv.DictReader(open(f"{INV}/migration-map.csv")):
        if r["new_path"] and r["old_path"] != r["new_path"]: out["/" + r["old_path"]] = "/" + r["new_path"]
    for name in ("redirects-extra.csv", "redirects-later.csv"):
        p = f"{INV}/{name}"
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                out[r.get("source") or r.get("old")] = r.get("destination") or r.get("new")
    return out

def main():
    cfg = json.load(open(f"{ROOT}/docs.json"))
    red = rows()
    # collapse chains (a -> b -> c) so every redirect is one hop
    for s in list(red):
        seen = 0
        while red[s] in red and seen < 5: red[s] = red[red[s]]; seen += 1
    cfg["redirects"] = [{"source": s, "destination": d} for s, d in sorted(red.items()) if s != d]
    json.dump(cfg, open(f"{ROOT}/docs.json", "w"), indent=2, ensure_ascii=False); open(f"{ROOT}/docs.json", "a").write("\n")
    print(len(cfg["redirects"]), "redirects")
main()
