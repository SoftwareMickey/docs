#!/usr/bin/env python3
"""features/docs-experience V114 — disclosure sweep. Fails when a published page names something a user never sees
(internal packages, private paths, secret names, detection logic). Prose AND code blocks are scanned.

  check-disclosure.py            scan the docs (DOCS_ROOT overrides the root)
  check-disclosure.py --fixture  prove the gate works: seed a deliberate leak into a scratch copy and require a failure

Patterns: features/docs-experience/inventory/disclosure-patterns.txt. Exceptions: disclosure-allowlist.txt (owner-reviewed).
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = "features/docs-experience/inventory"
SKIP = ("blog/", "changelog/", "features/", "snippets/data/", "node_modules/", "recipes/", ".git/")


def rules(name):
    out = []
    p = f"{ROOT}/{INV}/{name}"
    if os.path.exists(p):
        for line in open(p):
            if line.strip() and not line.startswith("#"): out.append(line.rstrip("\n").split("\t"))
    return out


def scan():
    pats = [(re.compile(r[0]), r[1] if len(r) > 1 else "") for r in rules("disclosure-patterns.txt")]
    allow = [(r[0], r[1]) for r in rules("disclosure-allowlist.txt") if len(r) >= 2]
    hits = []
    for dp, dn, fs in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT) + "/"
        if rel.startswith(SKIP) or any(s in rel for s in (".git/", "node_modules/")): dn[:] = []; continue
        for f in fs:
            if not f.endswith((".mdx", ".md")): continue
            path = os.path.normpath(os.path.join(rel, f))
            if path.startswith(SKIP) or path in ("README.md", "CLAUDE.md"): continue
            for n, line in enumerate(open(f"{ROOT}/{path}", errors="replace"), 1):
                line = re.sub(r"\{/\*.*?\*/\}", "", line)  # JSX comments are not rendered
                for rx, why in pats:
                    m = rx.search(line)
                    if m and not any(path == a and s in line for a, s in allow):
                        hits.append(f"{path}:{n}: {m.group(0)!r} — {why}")
    return hits


def fixture():
    d = tempfile.mkdtemp()
    for item in os.listdir(ROOT):
        if item in (".git", "node_modules"): continue
        s = f"{ROOT}/{item}"
        (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, f"{d}/{item}")
    os.makedirs(f"{d}/deploy", exist_ok=True)
    open(f"{d}/deploy/zz-leak.mdx", "w").write("---\ntitle: x\n---\nThe agenthub relays this over /internal/relay.\n")
    r = subprocess.run([sys.executable, __file__], env={**os.environ, "DOCS_ROOT": d}, capture_output=True, text=True)
    shutil.rmtree(d, ignore_errors=True)
    if r.returncode == 0 or "agenthub" not in r.stdout:
        print("FAIL  the seeded leak was not caught"); return 1
    print("PASS  a seeded leak fails the sweep"); return 0


def main():
    if "--fixture" in sys.argv: return fixture()
    hits = scan()
    for h in hits: print("LEAK  " + h)
    print(f"disclosure sweep: {len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
