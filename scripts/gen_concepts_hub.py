#!/usr/bin/env python3
"""features/docs-experience V79 — regenerate start/concepts.mdx (the Concepts hub) from every page with `type: concept`.
Concepts live in the tab where they are used; this hub is the one place that lists them all, grouped by area, with the page's own
description. Re-run after adding, moving or retyping a concept. Order inside an area follows docs.json navigation order."""
import glob, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREAS = [("start", "Start here", "book-open"), ("deploy", "Deploy", "rocket"), ("infrastructure", "Infrastructure", "server"), ("data", "Services and data", "database"),
         ("network", "Networking and security", "shield"), ("operate", "Operate", "activity"), ("teams", "Teams and governance", "users"), ("alie", "Alie", "bot")]
def nav_order():
    cfg = json.load(open(f"{ROOT}/docs.json")); out = []
    def walk(n):
        if isinstance(n, str): out.append(n.lstrip("/"))
        elif isinstance(n, dict):
            for k in ("pages", "groups", "tabs"):
                if k in n: walk(n[k])
        elif isinstance(n, list):
            for i in n: walk(i)
    walk(cfg["navigation"]); return {p: i for i, p in enumerate(out)}
def meta(p):
    t = open(f"{ROOT}/{p}.mdx").read(); fm = re.match(r"---\n(.*?)\n---\n", t, re.S).group(1)
    g = lambda k: (re.search(rf"^{k}:\s*(.*)$", fm, re.M) or [None, ""])[1].strip().strip("\"'")
    return g("type"), g("title"), g("description")
order = nav_order(); items = {}
for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
    p = os.path.relpath(f, ROOT)[:-4]
    if p.startswith(("features/", "blog/", "changelog/", "cli/", "snippets/", "node_modules/")) or p not in order: continue
    ty, title, desc = meta(p)
    if ty == "concept": items.setdefault(p.split("/")[0], []).append((order[p], p, title, desc))
body = ""
for key, label, icon in AREAS:
    if key not in items: continue
    body += f"\n## {label}\n\n<CardGroup cols={{2}}>\n"
    for _, p, title, desc in sorted(items[key]):
        d = desc.replace('"', "'")
        body += f'  <Card title="{title}" icon="{icon}" href="/{p}">{d}</Card>\n'
    body += "</CardGroup>\n"
head = '''---
title: "Concepts"
sidebarTitle: "Concepts"
description: "The ideas behind Beaver, in one place — what each thing is and why it behaves as it does. Each concept also sits beside the how-tos that use it."
icon: "book-open"
type: hub
audience: [evaluator, developer, team-lead, operator, security]
---

A **concept** page explains *why*; it never tells you which button to press or command to run. Each one lives in the section where you need it — under **Deploy**, **Infrastructure**,
**Data**, **Networking & security**, **Operate**, **Teams** or **Alie** — and every how-to links to its concept. Read these first if you are new:

1. [How Beaver fits together](/start/how-beaver-fits-together) — workspaces, projects, environments, machines, clouds, deployments and services in one picture.
2. [What is Beaver?](/start/what-is-vectorihub) — what it handles for you, and what it does not.
'''
open(f"{ROOT}/start/concepts.mdx", "w").write(head + body)
print("concepts hub:", sum(len(v) for v in items.values()), "concept pages")
