#!/usr/bin/env python3
"""Managed-services removal V16/V21 — every page that existed at the archive tag and is gone now must redirect, in one hop, to a page that exists.

    python3 scripts/check-removed-redirects.py [TAG]     (default services-final-2026-10)

Walks `git ls-tree` at the tag, so a page deleted without a redirect (a 404 for an old link) fails here, as does a redirect chain or a
redirect to a missing page. Pages that merely moved before the tag are covered by check-docs.py's redirect rules.
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG = sys.argv[1] if len(sys.argv) > 1 else "services-final-2026-10"


def exists(url: str) -> bool:
    p = url.split("#")[0].strip("/")
    return p == "" or (ROOT / f"{p}.mdx").exists() or (ROOT / p / "index.mdx").exists()


def main() -> int:
    tree = subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", TAG], text=True).split()
    red = {r["source"]: r["destination"] for r in json.loads((ROOT / "docs.json").read_text())["redirects"]}
    gone = [f[:-4] for f in tree if f.endswith(".mdx") and not f.startswith(("blog/", "changelog/", "features/", "snippets/", "scripts/"))
            and not (ROOT / f).exists()]
    bad = []
    for page in sorted(gone):
        url = "/" + page
        dest = red.get(url) or red.get(url.removesuffix("/index"))
        if dest is None:
            bad.append(f"{url}: removed with no redirect")
        elif dest in red:
            bad.append(f"{url} -> {dest}: redirect chain ({dest} redirects again)")
        elif not exists(dest):
            bad.append(f"{url} -> {dest}: destination does not exist")
    print("\n".join(bad) if bad else f"removed-page redirects: {len(gone)} pages, all single-hop to an existing page")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
