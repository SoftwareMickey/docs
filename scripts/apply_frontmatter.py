#!/usr/bin/env python3
"""features/docs-experience V15 — backfill the page-contract frontmatter (type, audience, interfaces) from
inventory/pages.csv onto pages that lack it. Metadata only: the body is never touched. Idempotent.

cli/* gets `type: reference` only (audience/interfaces are implied by the Reference tab).
"""
import csv, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = {r["path"]: r for r in csv.DictReader(open(f"{ROOT}/features/docs-experience/inventory/pages.csv"))}
LONG = {"ev": "evaluator", "dev": "developer", "lead": "team-lead", "ops": "operator", "sec": "security"}
n = 0
for path, r in rows.items():
    f = f"{ROOT}/{path}.mdx"; t = open(f).read()
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    if not m: continue
    fm = m.group(1); add = []
    if not re.search(r"^type:", fm, re.M): add.append(f"type: {r['type_target']}")
    if not path.startswith("cli") or path == "cli":
        if not re.search(r"^audience:", fm, re.M) and r["audience"]:
            add.append("audience: [" + ", ".join(LONG.get(a, a) for a in r["audience"].split(";")) + "]")
        if not re.search(r"^interfaces:", fm, re.M) and r["interfaces"]:
            add.append("interfaces: [" + ", ".join(r["interfaces"].split(";")) + "]")
    if add:
        open(f, "w").write("---\n" + fm + "\n" + "\n".join(add) + "\n---\n" + t[m.end():]); n += 1
print(n, "pages updated")
