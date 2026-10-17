#!/usr/bin/env python3
"""features/docs-experience V107/V108 — generated reference.

  gen_reference.py            write reference/glossary.mdx
  gen_reference.py --check    fail if it is out of date, or a terminology.csv term is missing from the glossary

Source: inventory/terminology.csv (the terminology registry the lint reads). The glossary is generated, so a new registry row cannot be forgotten.
"""
import csv, json, os, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"

# term -> the page that explains it best (every target must exist; the lint resolves links)
SEE = {
    "Beaver CLI": "/cli", "Beaver Desktop": "/interfaces/desktop/shell-tour", "Dashboard": "/interfaces/dashboard/tour", "Beaver Cloud": "/infrastructure/beaver-cloud",
    "Beaver Edge": "/network/beaver-edge", "Alie": "/alie/what-is-alie", "machine": "/infrastructure/machines-and-roles", "node": "/infrastructure/machines-and-roles",
    "workspace": "/teams/accounts-workspaces-teams", "team workspace": "/teams/create-a-team", "project": "/deploy/projects", "deployment": "/deploy/deployment-lifecycle",
    "environment": "/deploy/environments", "Composer": "/deploy/compose-applications", "compose application": "/deploy/compose-applications",
    "container": "/deploy/containers-and-replicas", "replica": "/deploy/containers-and-replicas", "approval": "/teams/production-approvals", "role": "/teams/roles-and-permissions",
    "activity": "/operate/activity-and-following", "template": "/deploy/publishing-a-template", "2-step verification": "/teams/two-step-verification", "passkey": "/teams/two-step-verification",
    "sign-in method": "/teams/sign-in-methods", "repository access": "/teams/signing-in-and-repository-access", "device authorization": "/cli/login", "Builder": "/infrastructure/machines-and-roles",
    "Host": "/infrastructure/machines-and-roles", "gateway": "/infrastructure/beaver-cloud", "drift": "/operate/state-and-drift", "reconcile": "/operate/drift-and-reconcile",
    "firewall": "/network/firewall", "incident": "/operate/incidents", "plan": "/teams/plans-and-billing",
}
HEAD = "{/* GENERATED FILE — do not edit. Regenerate with `python3 scripts/gen_reference.py`; sources: features/docs-experience/inventory/%s. */}\n\n"


def title_of(path):
    import re
    p = path.strip("/")
    for c in (f"{ROOT}/{p}.mdx", f"{ROOT}/{p}/index.mdx"):
        if os.path.exists(c):
            m = re.search(r'^title:\s*"(.+)"', open(c).read(), re.M)
            if m: return m.group(1)
    return p


def glossary():
    rows = list(csv.DictReader(open(f"{INV}/terminology.csv")))
    out = ["---", 'title: "Glossary"', 'sidebarTitle: "Glossary"',
           'description: "Every term Beaver\'s Dashboard, Desktop and CLI use — what it means, where you see it and where to read more."',
           'icon: "book-open"', "type: reference", "audience: [evaluator, developer, operator, team-lead]",
           'keywords: ["glossary", "terms", "definitions", "what is a node", "workspace vs project"]', "---", "",
           HEAD.rstrip("\n") % "terminology.csv", "",
           "Terms are spelled the way the product spells them. Where two surfaces use different words for one thing (the Dashboard's **node** is Desktop's and the CLI's **machine**), both are listed.", ""]
    for r in sorted(rows, key=lambda r: r["term"].lower()):
        t = r["term"]
        where = r["where_in_product"].strip()
        see = SEE.get(t)
        out += [f"### {t}", "", r["short_definition"].strip().rstrip(".") + ".", ""]
        if where: out += [f"**Where you see it:** {where}.", ""]
        if see: out += [f"Read more: [{title_of(see)}]({see})", ""]
    return "\n".join(out)


def main():
    outputs = {"reference/glossary.mdx": glossary()}
    bad = 0
    for rel, text in outputs.items():
        p = f"{ROOT}/{rel}"
        have = open(p).read() if os.path.exists(p) else None
        if have != text:
            if "--check" in sys.argv:
                print(f"ERROR  reference: {rel} is out of date — run python3 scripts/gen_reference.py"); bad += 1
            else:
                os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(text); print("wrote", rel)
    if "--check" in sys.argv:
        terms = [r["term"] for r in csv.DictReader(open(f"{INV}/terminology.csv"))]
        g = outputs["reference/glossary.mdx"]
        for t in terms:
            if f"### {t}\n" not in g: print(f"ERROR  reference: glossary lacks '{t}'"); bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
