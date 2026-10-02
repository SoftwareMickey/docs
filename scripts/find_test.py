#!/usr/bin/env python3
"""features/docs-experience V110 — the 30-task find test, run offline against the pages themselves.

  find_test.py                 print each task's result and the pass rate
  find_test.py --check         exit 1 below the threshold (CI / the launch gate)
  find_test.py --json          machine-readable result
  find_test.py --record        rewrite inventory/find-test-results.md (before/after table); the baseline is inventory/find-test-baseline.json
                               (measured 2026-10-02 on the tree as it stood when Era 21 began, before titles/keywords were tuned)

For every task in inventory/find-test.md:
  * clicks  — the fewest clicks from the home page: one to open the tab that lists the page, one to open the page from the tab's sidebar
              (navigation is at most two levels deep, so every page in the tree is 2 clicks away); a page missing from the tree is a miss
  * search  — a ranked full-text search over title, sidebar title, description, keywords, headings and body, run twice: the task as a user types it,
              then its content words only. The target must rank in the top 3 for either run ("2 searches").
A task passes when the target is in the navigation (clicks <= 3) AND found by search in <= 2 searches. Search is a local BM25-style model of what a
reader's search box does; the real Mintlify index may rank differently, so a task also lists its rank for review.
"""
import glob, json, math, os, re, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ("blog/", "changelog/", "features/", "snippets/", "node_modules/", "recipes/")
STOP = set("a an the to my i of in on is it for and or do does how can what why when where which with from at by be this that your you our we me not no are was were has have app".split())
THRESHOLD, TOP = 0.90, 3
FIELDS = {"title": 6.0, "sidebar": 4.0, "keywords": 5.0, "description": 3.0, "headings": 2.5, "body": 1.0}


def toks(s):
    return [w for w in re.findall(r"[a-z0-9][a-z0-9+#.\-]*", s.lower()) if w not in STOP and len(w) > 1]


def pages():
    out = {}
    for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
        rel = os.path.relpath(f, ROOT)[:-4]
        if rel.startswith(SKIP) or rel.startswith("cli/") and False: continue
        t = open(f).read()
        m = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
        fm, body = (m.group(1), m.group(2)) if m else ("", t)
        g = lambda k: (re.search(rf"^{k}:\s*(.+)$", fm, re.M) or [None, ""])[1].strip().strip('"')
        kw = re.search(r"^keywords:\s*\[(.*)\]", fm, re.M)
        body = re.sub(r"```.*?```", lambda m: m.group(0), body, flags=re.S)
        out[rel] = {"title": g("title"), "sidebar": g("sidebarTitle"), "description": g("description"),
                    "keywords": kw.group(1).replace('"', "") if kw else "",
                    "headings": " ".join(re.findall(r"^#{1,4}\s+(.+)$", body, re.M)),
                    "body": re.sub(r"<[^>]+>|[`*_|>\[\]()]", " ", body)}
    return out


def index(docs):
    n = len(docs); df = {}
    tf = {}
    for p, d in docs.items():
        tf[p] = {}
        for fld in FIELDS:
            c = {}
            for w in toks(d[fld]): c[w] = c.get(w, 0) + 1
            tf[p][fld] = c
        for w in {w for c in tf[p].values() for w in c}: df[w] = df.get(w, 0) + 1
    return tf, df, n


def search(q, docs, ix, k=10):
    tf, df, n = ix
    qs = toks(q); scores = {}
    for p in docs:
        s = 0.0
        for w in qs:
            idf = math.log(1 + (n - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
            for fld, wt in FIELDS.items():
                c = tf[p][fld].get(w, 0)
                if not c: continue
                L = sum(tf[p][fld].values()) or 1
                norm = c * 2.2 / (c + 1.2 * (0.25 + 0.75 * L / (60 if fld == "body" else 8)))
                s += wt * idf * norm
        # a phrase hit in the title is what a reader's eye catches first
        if all(w in toks(docs[p]["title"] + " " + docs[p]["sidebar"]) for w in qs) and qs: s *= 1.5
        if s: scores[p] = s
    return [p for p, _ in sorted(scores.items(), key=lambda x: -x[1])[:k]]


def tasks():
    out = []
    for line in open(f"{ROOT}/features/docs-experience/inventory/find-test.md"):
        m = re.match(r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*\w+\s*\|\s*.+?\s*\|\s*([\w/\-]+)\s*\|\s*$", line)
        if m: out.append((int(m.group(1)), m.group(2), m.group(3)))
    return out


def nav_pages():
    cfg = json.load(open(f"{ROOT}/docs.json")); seen = set()
    def walk(n):
        for i in n["pages"]:
            if isinstance(i, str): seen.add(i.lstrip("/"))
            else: walk(i)
    for t in cfg["navigation"]["tabs"]:
        for g in t.get("groups", []): walk(g)
    return seen


def main():
    docs = pages(); ix = index(docs); nav = nav_pages(); results = []
    for num, task, target in tasks():
        r1 = search(task, docs, ix); r2 = search(" ".join(toks(task)), docs, ix)
        rank = lambda r: (r.index(target) + 1) if target in r else None
        a, b = rank(r1), rank(r2)
        in_nav = target in nav
        found = (a is not None and a <= TOP) or (b is not None and b <= TOP)
        results.append({"n": num, "task": task, "target": target, "in_nav": in_nav, "clicks": 2 if in_nav else None, "rank_full": a, "rank_keywords": b, "pass": bool(in_nav and found and target in docs)})
    ok = sum(r["pass"] for r in results); rate = ok / len(results)
    if "--record" in sys.argv:
        base = json.load(open(f"{ROOT}/features/docs-experience/inventory/find-test-baseline.json")); b = {r["n"]: r for r in base["tasks"]}
        import datetime
        rank = lambda r: min([x for x in (r["rank_full"], r["rank_keywords"]) if x] or [None]) if (r["rank_full"] or r["rank_keywords"]) else None
        lines = ["# Find test results (Era 21 V110)", "",
                 f"Recorded {datetime.date.today().isoformat()} by `python3 scripts/find_test.py --record`. Model: a local BM25-style search over title, sidebar title, keywords,",
                 "description, headings and body, run twice per task (the task as typed, then its content words); a task passes when its target page is in the navigation and ranks in the top 3 for either run.",
                 "The real Mintlify search may rank differently; this is the repeatable proxy, and the live find test with real readers is a launch-gate owner step.", "",
                 f"**Before tuning: {base['passed']}/{base['total']} ({base['rate']:.0%}).  After: {ok}/{len(results)} ({rate:.0%}).  Threshold: {THRESHOLD:.0%}.**", "",
                 "| # | Task | Before (best rank) | After (best rank) | Target |", "| --- | --- | --- | --- | --- |"]
        for r in results:
            lines.append(f"| {r['n']} | {r['task']} | {('top ' + str(rank(b[r['n']]))) if b[r['n']]['pass'] else 'miss'} | {('top ' + str(rank(r))) if r['pass'] else 'miss'} | `{r['target']}` |")
        lines += ["", "What changed: page titles rewritten to the task a reader types (\"Add a custom domain\", \"Roll back a bad release\", \"Back up and restore a service\"), `keywords` added with the",
                  "synonyms people use (\"roll back\", \"connection string\", \"open ports\"), every tutorial, troubleshooting and how-to page now carries keywords, and two benchmark targets that pointed at",
                  "pages renamed during the build (#26, #27) were corrected. `check-docs.py` now enforces title length, description length and uniqueness, and keywords.", ""]
        open(f"{ROOT}/features/docs-experience/inventory/find-test-results.md", "w").write("\n".join(lines)); print("wrote inventory/find-test-results.md")
    if "--json" in sys.argv:
        print(json.dumps({"passed": ok, "total": len(results), "rate": round(rate, 3), "tasks": results}, indent=1))
    else:
        for r in results:
            print(("PASS" if r["pass"] else "MISS") + f"  #{r['n']:<2} {r['task'][:52]:52} nav={'y' if r['in_nav'] else 'N'} search1={r['rank_full'] or '-'} search2={r['rank_keywords'] or '-'}  -> {r['target']}")
        print(f"{ok}/{len(results)} tasks found ({rate:.0%}); threshold {THRESHOLD:.0%}")
    return 1 if "--check" in sys.argv and rate < THRESHOLD else 0


if __name__ == "__main__":
    sys.exit(main())
