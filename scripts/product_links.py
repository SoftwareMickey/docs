#!/usr/bin/env python3
"""features/docs-experience V11/V98 — every docs URL the product repos emit.

  scripts/product_links.py            # print path -> where it is emitted
  scripts/product_links.py --check    # exit 1 if a path resolves to no page and no redirect

Scans vhb-client (DOCS_URL + "/path", ${DOCS_URL}/path, docs-host literals, *_PATH constants that
feed DOCS_URL), vhb-server and beaver-desktop (docs-host literals), beaver-cli. A path "resolves"
if a page exists for it (docs.json navigation or file) or docs.json `redirects` maps it.
"""
import argparse, json, os, re, sys

HOME = os.path.expanduser("~/Desktop")
REPOS = {
    "vhb-client": f"{HOME}/works/vhb-client/src",
    "vhb-server": f"{HOME}/works/vhb-server",
    "beaver-desktop": f"{HOME}/vhb/beaver-desktop/apps",
    "beaver-desktop-pkg": f"{HOME}/vhb/beaver-desktop/packages",
    "beaver-cli": f"{HOME}/vhb/beaver-cli",
    "admin-dashboard": f"{HOME}/vhb/admin-dashboard/src",
}
SKIP = {"node_modules", ".git", "dist", "features", "vendor", "build", "target"}
EXT = (".ts", ".tsx", ".js", ".jsx", ".go", ".yml", ".yaml")
PATTERNS = [
    re.compile(r"DOCS_URL\s*\+\s*[\"'`](/[A-Za-z0-9_\-./#]*)"),
    re.compile(r"\$\{DOCS_URL\}(/[A-Za-z0-9_\-./#]*)"),
    re.compile(r"docs\.vectorihub\.[a-z]+(/[A-Za-z0-9_\-./#]*)"),
    re.compile(r"(?:_PATH|Path)\s*=\s*[\"'`](/(?:guides|concepts|cli|services|deploying|infrastructure-setup|frameworks|languages|runtimes)[A-Za-z0-9_\-./#]*)[\"'`]"),
]

def scan():
    found = {}
    for name, root in REPOS.items():
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP]
            for f in files:
                if not f.endswith(EXT) or f.endswith(("_test.go", ".test.ts", ".test.tsx")):
                    continue
                p = os.path.join(d, f)
                try:
                    txt = open(p, errors="ignore").read()
                except OSError:
                    continue
                for pat in PATTERNS:
                    for m in pat.finditer(txt):
                        path = m.group(1).split("#")[0].rstrip("/") or "/"
                        if "${" in path:
                            continue
                        found.setdefault(path, set()).add(f"{name}:{os.path.relpath(p, root)}")
    return found

def nav_pages(cfg):
    out = set()
    def walk(n):
        if isinstance(n, str): out.add("/" + n.lstrip("/"))
        elif isinstance(n, dict):
            for k in ("pages", "groups", "tabs", "anchors", "dropdowns", "products", "versions", "menu"):
                if k in n: walk(n[k])
        elif isinstance(n, list):
            for i in n: walk(i)
    walk(cfg["navigation"])
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true")
    ap.add_argument("--docs", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    cfg = json.load(open(f"{a.docs}/docs.json"))
    pages = nav_pages(cfg)
    redirects = {r["source"].rstrip("/") or "/": r["destination"] for r in cfg.get("redirects") or []}
    found = scan()
    bad = []
    for path in sorted(found):
        ok = (path in pages or path in redirects or path in ("/", "/changelog", "/blog")
              or os.path.exists(f"{a.docs}{path}.mdx") and False)
        # a path is also valid if it is a blog/changelog entry
        if not ok and (path.startswith(("/blog", "/changelog"))): ok = True
        print(("ok   " if ok else "MISS ") + path + "   <- " + ", ".join(sorted(found[path]))[:110])
        if not ok: bad.append(path)
    if a.check and bad:
        print(f"\n{len(bad)} product-emitted docs path(s) resolve to nothing", file=sys.stderr); sys.exit(1)

main()
