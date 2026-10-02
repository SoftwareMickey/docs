#!/usr/bin/env python3
"""features/docs-experience V116 — lastVerified freshness report.

Lists published pages whose `lastVerified` is older than the SLA (default 90 days) or that declare `verified` without a date.
  freshness.py                 report; exit 0
  freshness.py --strict        exit 1 when any page is past SLA (the nightly CI job)
  freshness.py --days 60       a different SLA
  freshness.py --today 2027-01-15   evaluate as of a date (tests)
"""
import datetime, os, re, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ("blog/", "changelog/", "features/", "snippets/", "node_modules/", "recipes/", ".git/")


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    days = int(arg("--days", 90))
    today = datetime.date.fromisoformat(arg("--today", datetime.date.today().isoformat()))
    stale, undated, total = [], [], 0
    for dp, dn, fs in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT) + "/"
        if rel.startswith(SKIP) or ".git/" in rel or "node_modules/" in rel: dn[:] = []; continue
        for f in fs:
            if not f.endswith(".mdx"): continue
            path = os.path.normpath(os.path.join(rel, f))
            if path.startswith(SKIP): continue
            fm = re.match(r"---\n(.*?)\n---", open(f"{ROOT}/{path}", errors="replace").read(), re.S)
            if not fm: continue
            verified = re.search(r"^verified:\s*(\S+)", fm.group(1), re.M)
            last = re.search(r"^lastVerified:\s*(\d{4}-\d{2}-\d{2})", fm.group(1), re.M)
            if not verified: continue
            total += 1
            if not last: undated.append(path); continue
            age = (today - datetime.date.fromisoformat(last.group(1))).days
            if age > days: stale.append((age, path))
    for age, p in sorted(stale, reverse=True): print(f"STALE   {age:>4}d  {p[:-4]}")
    for p in undated: print(f"UNDATED        {p[:-4]}")
    print(f"{total} verified pages · {len(stale)} past the {days}-day SLA · {len(undated)} without lastVerified (as of {today})")
    return 1 if ("--strict" in sys.argv and (stale or undated)) else 0


if __name__ == "__main__":
    sys.exit(main())
