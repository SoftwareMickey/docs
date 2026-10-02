#!/usr/bin/env python3
"""features/docs-experience V88/V93 — every Dashboard route and every Desktop section / settings page has a guide section or an explicit
exclusion with a reason.

  scripts/check-interface-coverage.py                    # sources found next to this repo (or via env), else only the data checks
  VHB_CLIENT=~/Desktop/works/vhb-client VHB_DESKTOP=~/Desktop/vhb/beaver-desktop scripts/check-interface-coverage.py --require-sources

Checks (E = fails):
  E  inventory/route-coverage.csv: a `guide` row names a page that exists and contains its `term`; an `excluded` row has a reason
  E  inventory/surfaces-source.csv: every public Dashboard/Desktop capability's doc_target exists and contains one of its keywords
  E  with the product repos present: every route in vhb-client src/App.tsx, every InfraSectionId and every SettingsSectionId in beaver-desktop
     appears in route-coverage.csv, and no row names a route that no longer exists (stale)
The product-repo half is not run in CI (the repos are not checked out there); it is part of the monthly cross-repo audit (Era 22 V116).
"""
import csv, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"
CLIENT = os.path.expanduser(os.environ.get("VHB_CLIENT", "~/Desktop/works/vhb-client"))
DESKTOP = os.path.expanduser(os.environ.get("VHB_DESKTOP", "~/Desktop/vhb/beaver-desktop"))
errors = []
E = errors.append

def page_text(slug):
    f = f"{ROOT}/{slug}.mdx"
    return open(f).read().lower() if os.path.exists(f) else None

def source_routes():
    out = {"dashboard": set(), "desktop": set()}
    app = f"{CLIENT}/src/App.tsx"
    if os.path.exists(app):
        for m in re.finditer(r'(?<![/\w])path(?:=|: ?)"([^"]*)"', open(app).read()): out["dashboard"].add(m.group(1))
    nav = f"{DESKTOP}/apps/desktop/src/infra/nav/store.ts"
    if os.path.exists(nav):
        t = open(nav).read(); block = re.search(r"export type InfraSectionId =(.*?);", t, re.S)
        if block: out["desktop"] |= {"section:" + s for s in re.findall(r'"([a-z-]+)"', block.group(1))}
    sn = f"{DESKTOP}/apps/desktop/src/settings/nav.ts"
    if os.path.exists(sn):
        t = open(sn).read(); block = re.search(r"export type SettingsSectionId =(.*?);", t, re.S)
        if block: out["desktop"] |= {"settings:" + s for s in re.findall(r'"([a-z-]+)"', block.group(1))}
    return out

def main():
    rows = list(csv.DictReader(open(f"{INV}/route-coverage.csv")))
    ids = {(r["surface"], r["id"]) for r in rows}
    for r in rows:
        if r["disposition"] == "excluded":
            if not r["reason"].strip(): E(f"route-coverage: {r['surface']} {r['id']} is excluded without a reason")
        else:
            t = page_text(r["guide"])
            if t is None: E(f"route-coverage: {r['surface']} {r['id']} -> '{r['guide']}' does not exist")
            elif r["term"].lower() not in t: E(f"route-coverage: {r['surface']} {r['id']} -> '{r['guide']}' never mentions '{r['term']}'")
    for r in csv.DictReader(open(f"{INV}/surfaces-source.csv")):
        if r["surface"] not in ("dashboard", "desktop") or r["disposition"] != "public": continue
        t = page_text(r["doc_target"])
        if t is None: E(f"surfaces: '{r['capability']}' -> '{r['doc_target']}' does not exist"); continue
        kws = [k.strip().lower() for k in r["keywords"].split("|") if k.strip()]
        if kws and not any(k in t for k in kws): E(f"surfaces: '{r['capability']}' -> '{r['doc_target']}' mentions none of {kws}")
    src = source_routes(); have = any(src.values())
    if "--require-sources" in sys.argv and not (src["dashboard"] and src["desktop"]): E("product repos not found (set VHB_CLIENT / VHB_DESKTOP)")
    for surface, found in src.items():
        for rid in sorted(found):
            if (surface, rid) not in ids: E(f"{surface}: '{rid}' exists in the product but has no row in route-coverage.csv — document it or exclude it with a reason")
        for s, rid in sorted(ids):
            if s == surface and found and rid not in found: E(f"route-coverage: {surface} '{rid}' is no longer in the product — remove the row")
    for e in errors: print("ERROR  ", e)
    n = sum(len(v) for v in src.values())
    print(f"\n{len(rows)} coverage rows · {n} product routes/sections read" + ("" if have else " (product repos not present — data checks only)") + f" · {len(errors)} errors")
    sys.exit(1 if errors else 0)

main()
