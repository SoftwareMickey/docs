#!/usr/bin/env python3
"""Managed-services removal tripwire for the docs (services-removal V9).

After V17 the removed pages are gone and every old URL redirects to the notice. This fails when a page body links to a
removed page (/cli/service or one of the deleted /data/** pages), so a deleted page cannot creep back in via a link.
scripts/services-freeze-allowlist.txt is kept (empty) so an exception, if ever needed, is explicit and reviewed.
Redirect targets in docs.json are ignored; this scans page bodies only.

    python3 scripts/check-services-freeze.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOW = ROOT / "scripts" / "services-freeze-allowlist.txt"
REMOVED = (r"/cli/service\b", r"/data/services\b", r"/data/(?:create-a-service|resize-and-upgrade|high-availability|connect-locally"
           r"|credentials-and-connection-strings|backups-and-restore|services-and-persistence)\b", r"/start/first-service\b")
LINK = re.compile(r"""[("'](?:""" + "|".join(REMOVED) + r""")[^)"' ]*""")
SKIP_DIRS = {"node_modules", ".git", "scripts", "features", "images"}


def pages():
    for p in ROOT.rglob("*"):
        if p.suffix not in (".mdx", ".md") or SKIP_DIRS & set(p.relative_to(ROOT).parts):
            continue
        yield p


def main() -> int:
    allow = {
        l.strip() for l in ALLOW.read_text().splitlines() if l.strip() and not l.startswith("#")
    }
    got = {
        str(p.relative_to(ROOT))
        for p in pages()
        if LINK.search(p.read_text(errors="ignore"))
    }
    added, stale = sorted(got - allow), sorted(allow - got)
    if added:
        print("managed services were removed; these pages link to a removed page:")
        print("  " + "\n  ".join(added))
    if stale:
        print("good news: these pages no longer link there; delete them from the allowlist:")
        print("  " + "\n  ".join(stale))
    if not (added or stale):
        print(f"services freeze: {len(got)} pages link to a removed page")
    return 1 if (added or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
