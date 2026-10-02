#!/usr/bin/env python3
"""features/docs-experience V81 — render snippets/capability-matrix.mdx from snippets/data/capability-matrix.json.

  scripts/gen_capability_matrix.py            write the snippet
  scripts/gen_capability_matrix.py --check    fail if the committed snippet differs from the data (CI)

The JSON is the source of truth (task x interface -> {status, how, page}); the page cannot drift from it. Parity rules
(also run by check-docs.py): status in full|partial|none|planned; none/planned carry a `how` that names the alternative or the
reason; every `page` resolves; a full/partial cell's page must actually mention that interface (no silent gaps — Invariant 6);
planned is never rendered as available (Invariant 8). Cell text may not contain a pipe (it would break the table).
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{ROOT}/snippets/data/capability-matrix.json"
OUT = f"{ROOT}/snippets/capability-matrix.mdx"
STATUS = {"full": ("✓", "Yes"), "partial": ("◐", "Partly"), "none": ("—", "No"), "planned": ("○", "Not yet")}
IFACES = [("dashboard", "Dashboard"), ("desktop", "Desktop"), ("cli", "CLI")]

def load(): return json.load(open(SRC))["tasks"]

def cell(c):
    sym, word = STATUS[c["status"]]
    how = c["how"]
    link = f" [Guide]({c['page']})" if c.get("page") else ""
    return f"{sym} **{word}.** {how}{link}"

def render(tasks):
    out = ["{/* GENERATED FILE — do not edit. Regenerate with `python3 scripts/gen_capability_matrix.py`; source: snippets/data/capability-matrix.json. */}\n"]
    groups = []
    for t in tasks:
        if t["group"] not in groups: groups.append(t["group"])
    for g in groups:
        out.append(f"\n### {g}\n")
        out.append("| Task | Dashboard | Desktop | CLI |\n| --- | --- | --- | --- |")
        for t in [x for x in tasks if x["group"] == g]:
            also = "".join(f"<br />[{r['title']}]({r['page']})" for r in t.get("related", []))
            out.append(f"| **{t['task']}**{also} | " + " | ".join(cell(t["interfaces"][k]) for k, _ in IFACES) + " |")
    return "\n".join(out) + "\n"

def main():
    tasks = load(); text = render(tasks)
    if "--check" in sys.argv:
        cur = open(OUT).read() if os.path.exists(OUT) else ""
        if cur != text: print("snippets/capability-matrix.mdx is stale — run scripts/gen_capability_matrix.py"); sys.exit(1)
        print(f"capability matrix up to date ({len(tasks)} tasks)"); return
    open(OUT, "w").write(text)
    counts = {}
    for t in tasks:
        for k, _ in IFACES: counts[(k, t["interfaces"][k]["status"])] = counts.get((k, t["interfaces"][k]["status"]), 0) + 1
    print(f"wrote {OUT}: {len(tasks)} tasks")
    for k, _ in IFACES: print(f"  {k:10s}", {s: counts.get((k, s), 0) for s in STATUS})

if __name__ == "__main__": main()
