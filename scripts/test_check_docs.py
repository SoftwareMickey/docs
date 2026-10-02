#!/usr/bin/env python3
"""features/docs-experience V15 — seed every check-docs.py rule with a deliberate violation; each must fail on exactly
that rule. Runs against a scratch copy of the docs (DOCS_ROOT), never the working tree."""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = f"{ROOT}/scripts/check-docs.py"

def fresh():
    d = tempfile.mkdtemp()
    for item in os.listdir(ROOT):
        if item in (".git", "node_modules"): continue
        s = f"{ROOT}/{item}"
        (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, f"{d}/{item}")
    return d

def run(d):
    r = subprocess.run([sys.executable, CHECK, "--strict"], env={**os.environ, "DOCS_ROOT": d}, capture_output=True, text=True)
    return r.returncode, r.stdout

def write(d, path, text): os.makedirs(os.path.dirname(f"{d}/{path}"), exist_ok=True); open(f"{d}/{path}", "w").write(text)
def edit_nav(d, fn):
    c = json.load(open(f"{d}/docs.json")); fn(c); json.dump(c, open(f"{d}/docs.json", "w"))
def edit_reg(d, fn):
    p = f"{d}/features/docs-experience/inventory/help-links.json"; r = json.load(open(p)); fn(r); json.dump(r, open(p, "w"))
def edit_inv(d, name, fn):
    p = f"{d}/features/docs-experience/inventory/{name}"; r = json.load(open(p)); fn(r); json.dump(r, open(p, "w"))
PAGE = '---\ntitle: "Seeded"\ndescription: "x"\ntype: howto\naudience: [developer]\n---\nbody\n'

cases = [
    ("orphan", lambda d: write(d, "deploy/zzz.mdx", PAGE), "orphan: 'deploy/zzz'"),
    ("missing page", lambda d: edit_nav(d, lambda c: c["navigation"]["tabs"][1]["groups"][0]["pages"].append("deploy/nope")), "no page"),
    ("missing type", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("type: howto\n", "")), "type must be one of"),
    ("bad type", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("howto", "essay")), "type must be one of"),
    ("missing audience", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("audience: [developer]\n", "")), "missing audience"),
    ("duplicate title", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("Seeded", "Deploy overview" if False else "Projects")), "duplicates"),
    ("group over budget", lambda d: edit_nav(d, lambda c: c["navigation"]["tabs"][0]["groups"][0]["pages"].extend([f"x/{i}" for i in range(13)])), "max 12"),
    ("tab first page not hub", lambda d: edit_nav(d, lambda c: c["navigation"]["tabs"][1]["groups"][0]["pages"].reverse()), "must be a hub"),
    ("redirect to nowhere", lambda d: edit_nav(d, lambda c: c.setdefault("redirects", []).append({"source": "/old-x", "destination": "/nowhere"})), "does not exist"),
    ("redirect from live page", lambda d: edit_nav(d, lambda c: c["redirects"].append({"source": "/deploy/scale", "destination": "/deploy/overview"})), "is a live page"),
    ("forbidden term", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("body", "Ask ALIE about it.")), "write \"Alie\""),
    ("concept command block", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("howto", "concept").replace("body", "```bash\nbeaver deploy\n```")), "deploy/zzz: concept page contains"),
    ("verified page missing a tab", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("audience", "interfaces: [dashboard, cli]\nlastVerified: 2026-10-01\naudience")), "has no <Tab"),
    ("image without alt", lambda d: write(d, "deploy/zzz.mdx", PAGE.replace("body", "![](/images/x.png)")), "alt text"),
    ("help-link to a missing page", lambda d: edit_reg(d, lambda r: r["keys"].__setitem__("dashboard.zzz", {"path": "/deploy/nowhere", "surface": "dashboard", "where": "x"})), "dashboard.zzz: no page at /deploy/nowhere"),
    ("help-link to a missing anchor", lambda d: edit_reg(d, lambda r: r["keys"].__setitem__("dashboard.zzy", {"path": "/deploy/overview#no-such-heading", "surface": "dashboard", "where": "x"})), "no heading #no-such-heading"),
    ("help-link malformed key", lambda d: edit_reg(d, lambda r: r["keys"].__setitem__("Bad Key", {"path": "/deploy/overview", "surface": "dashboard", "where": "x"})), "key must look like"),
    ("registered code without a page", lambda d: edit_inv(d, "problem-codes.json", lambda r: r.append({"name": "ZZZ_NEW_CODE", "http": 409, "class": "conflict", "message": "New", "doc": "A code added to the registry."})), "reference/errors/zzz-new-code.mdx is missing"),
    ("exit-status table drift", lambda d: edit_inv(d, "exit-status.json", lambda r: r.append({"status": 9, "scope": "beaver zzz", "meaning": "New status"})), "snippets/exit-status-table.mdx is out of date"),
    ("error page for a retired code", lambda d: write(d, "reference/errors/retired-code.mdx", PAGE), "no longer registered"),
    ("snippet header", lambda d: write(d, "snippets/plan-ladder.mdx", "no header\n"), "GENERATED"),
]
failed = 0
base = fresh()
r0 = subprocess.run([sys.executable, CHECK], env={**os.environ, "DOCS_ROOT": base}, capture_output=True, text=True)
baseline_out = r0.stdout
print(("PASS" if r0.returncode == 0 else "FAIL") + "  baseline has zero errors" + ("" if r0.returncode == 0 else "\n" + baseline_out[-600:])); failed += r0.returncode != 0
shutil.rmtree(base)
for name, seed, expect in cases:
    d = fresh(); seed(d)
    # pages seeded into the nav are not needed for most rules; orphan/metadata rules fire on the page itself
    rc, out = run(d); shutil.rmtree(d)
    ok = rc != 0 and expect in out and expect not in baseline_out
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  (expected {expect!r})\n{out[-400:]}"))
    failed += not ok
sys.exit(1 if failed else 0)
