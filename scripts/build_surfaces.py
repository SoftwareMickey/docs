#!/usr/bin/env python3
"""features/docs-experience V2 — product-surface inventory (the missing-page inventory).

Reads inventory/surfaces-source.csv (hand-authored capability list from the product repos) plus the CLI
groups in features/docs/inventory/doc_status.csv, probes the published docs for evidence, and writes
inventory/surfaces.csv with a coverage status per capability.

Evidence = number of public docs pages (not cli/, blog/, changelog/, features/) that match one of the
capability's keywords AND name the interface (Dashboard rows must say "dashboard", Desktop rows
"desktop"). status: 0 pages = missing, 1 = thin, >=2 = covered. This is a *floor* measure meant to show
movement between eras; the launch gate (Era 22 V117) is a human review, not this script.
Dispositions internal/unreleased pass through unchanged — they are decisions, not omissions.
"""
import csv, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"
SKIP = ("cli/", "blog/", "changelog/", "features/", "snippets/", "node_modules/", "recipes/")

# Decided in features/docs Era 10/11: operator and MCP-transport commands are excluded from public docs.
CLI_EXCLUDED = {"admin": "operator command group, excluded (features/docs Era 10)", "mcpcmd": "MCP wiring, excluded (features/docs Era 11)"}

def corpus():
    out = {}
    for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(SKIP) or rel == "cli.mdx": continue
        out[rel[:-4]] = open(f, errors="ignore").read().lower()
    return out

def main():
    docs = corpus(); rows = []
    for r in csv.DictReader(open(f"{INV}/surfaces-source.csv")):
        evid = []
        if r["disposition"] == "public" and r["keywords"]:
            kws = [k.strip().lower() for k in r["keywords"].split("|") if k.strip()]
            iface = r["surface"] if r["surface"] in ("dashboard", "desktop") else ""
            for p, t in docs.items():
                if iface and iface not in t: continue
                if any(k in t for k in kws): evid.append(p)
        if r["disposition"] != "public": status = r["disposition"]
        else: status = "missing" if not evid else "thin" if len(evid) == 1 else "covered"
        rows.append(dict(surface=r["surface"], area=r["area"], capability=r["capability"], source_ref=r["source_ref"],
                         interfaces=r["interfaces"], doc_target=r["doc_target"], status=status,
                         evidence=";".join(sorted(evid)[:4]), note=r["note"]))
    cli_status = f"{ROOT}/features/docs/inventory/doc_status.csv"
    if os.path.exists(cli_status):
        for r in csv.DictReader(open(cli_status)):
            if r["group"] in CLI_EXCLUDED:
                rows.append(dict(surface="cli", area="command group", capability=f"beaver {r['group']}", source_ref="beaver-cli/commands",
                                 interfaces="cli", doc_target="", status="internal", evidence="", note=CLI_EXCLUDED[r["group"]])); continue
            st = {"documented": "covered", "documented-under-different-name": "covered", "undocumented": "missing"}.get(r["doc_status"], "thin")
            rows.append(dict(surface="cli", area="command group", capability=f"beaver {r['group']}", source_ref="beaver-cli/commands",
                             interfaces="cli", doc_target=r["mapped_pages"] or "", status=st, evidence=r["mapped_pages"], note=r["doc_status"]))
    cols = ["surface", "area", "capability", "source_ref", "interfaces", "doc_target", "status", "evidence", "note"]
    with open(f"{INV}/surfaces.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    from collections import Counter
    by = Counter((r["surface"], r["status"]) for r in rows)
    for s in ("dashboard", "desktop", "backend", "admin", "cli"):
        print(f"{s:10s}", {st: n for (sf, st), n in sorted(by.items()) if sf == s})
    print("total", len(rows))

main()
