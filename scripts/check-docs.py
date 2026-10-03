#!/usr/bin/env python3
"""features/docs-experience V15 — the docs lint. Run in CI next to `mint validate` and `mint broken-links`.

  scripts/check-docs.py              errors fail (exit 1); warnings are listed
  scripts/check-docs.py --strict     warnings fail too (the launch-gate setting)

Rules (E = error, W = warning; --strict promotes W):
  E  every docs.json page exists; every public MDX page is in the navigation (no orphans)
  E  frontmatter contract: title, description, type (hub|tutorial|howto|concept|reference|troubleshooting|interface);
     audience on every non-cli page; titles unique outside cli/
  E  navigation budget: <= 12 page entries per group/subgroup; nesting depth <= 2; each tab's first page is a hub
  E  redirects: destination exists, source is not a live page, no chains
  E  terminology: inventory/forbidden-terms.txt patterns in prose
  E  generated snippets keep their GENERATED header
  W  concept pages contain no `beaver ...` command blocks (explain, never instruct) — becomes E at the Era 14 gate
  W  pages that declare `interfaces:` and are verified (have lastVerified) have a Tab per declared interface
  W  images/`<img>` without alt text
  E  screenshots (V94-V95): every <Shot name=... alt=.../> has alt text that says what is shown, and a light and a dark image listed in
     images/ui/manifest.json; every Dashboard/Desktop interface guide (except the workflow maps) shows at least one
  E  capability matrix (V81): schema, every page resolves, a full/partial cell's page mentions that interface, the generated
     snippet is current; multi-interface task pages are referenced by a matrix row (parity)
  E  findability (V109): title <= 60 characters, description 30-200 and unique across pages; troubleshooting and tutorial pages carry `keywords`
  W  howto pages without `keywords` (the synonyms a reader types: "502", "roll back", "env")
  E  generated reference (V107/V108): the glossary and the service tables are current and every terminology.csv term has a glossary entry
  E  help-link registry (V97): inventory/help-links.json keys are well formed and every path/#anchor resolves to a page
     (`--products` also fails when a sibling product checkout's generated mirror is out of date)
"""
import glob, json, os, re, subprocess, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ("blog/", "changelog/", "features/", "snippets/", "node_modules/", "recipes/")
TYPES = {"hub", "tutorial", "howto", "concept", "reference", "troubleshooting", "interface"}
errors, warns = [], []
E = errors.append; W = warns.append

def mdx_pages():
    return {os.path.relpath(f, ROOT)[:-4]: f for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True)
            if not os.path.relpath(f, ROOT).startswith(SKIP)}

def fm_body(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)

def strip_code(body):
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", body)

def nav_walk(cfg):
    pages = []
    def node(n, depth, where):
        direct = [i for i in n["pages"] if isinstance(i, str)]
        if len(direct) > 12: E(f"nav: '{where}' has {len(direct)} pages (max 12) — add a subgroup")
        if depth > 2: E(f"nav: '{where}' is nested {depth} deep (max 2)")
        for i in n["pages"]:
            if isinstance(i, str): pages.append(i.lstrip("/"))
            else: node(i, depth + 1, f"{where} > {i['group']}")
    first_pages = {}
    for t in cfg["navigation"]["tabs"]:
        for k, g in enumerate(t.get("groups", [])):
            before = len(pages); node(g, 1, f"{t['tab']} > {g['group']}")
            if k == 0 and len(pages) > before: first_pages[t["tab"]] = pages[before]
    return pages, first_pages

IFACE_WORDS = {"dashboard": "dashboard", "desktop": "desktop", "cli": "beaver"}

def check_matrix(docs):
    """features/docs-experience V81 — the interface-parity test over snippets/data/capability-matrix.json."""
    path = f"{ROOT}/snippets/data/capability-matrix.json"
    if not os.path.exists(path): return
    tasks = json.load(open(path))["tasks"]
    ids = set(); referenced = set()
    for t in tasks:
        tid = t.get("id", "?")
        if tid in ids: E(f"matrix: duplicate task id '{tid}'")
        ids.add(tid)
        for k in ("dashboard", "desktop", "cli"):
            c = (t.get("interfaces") or {}).get(k)
            if not c: E(f"matrix: '{tid}' has no {k} cell"); continue
            st, how, page = c.get("status"), (c.get("how") or "").strip(), (c.get("page") or "").lstrip("/")
            if st not in ("full", "partial", "none", "planned"): E(f"matrix: '{tid}'/{k} status {st!r}"); continue
            if not how: E(f"matrix: '{tid}'/{k} has no `how`")
            if "|" in how: E(f"matrix: '{tid}'/{k} `how` contains a pipe")
            if st == "none" and not re.search(r"\b(Use|Start|Not applicable|already|Read-only|Nothing to|Shows)\b|^The ", how):
                E(f"matrix: '{tid}'/{k} is 'none' but does not name the alternative or the reason: {how!r}")
            if page:
                referenced.add(page)
                if page not in docs: E(f"matrix: '{tid}'/{k} page '/{page}' does not exist"); continue
                if st in ("full", "partial"):
                    body = open(docs[page]).read().lower()
                    if IFACE_WORDS[k] not in body: E(f"matrix: '{tid}'/{k} is {st} but '/{page}' never mentions the {k}")
            elif st in ("full", "partial"): E(f"matrix: '{tid}'/{k} is {st} with no page")
    for t in tasks:
        for rel in t.get("related", []):
            referenced.add(rel["page"].lstrip("/"))
            if rel["page"].lstrip("/") not in docs: E(f"matrix: '{t['id']}' related page '{rel['page']}' does not exist")
    r = subprocess.run([sys.executable, f"{ROOT}/scripts/gen_capability_matrix.py", "--check"], capture_output=True, text=True)
    if r.returncode: E("matrix: " + r.stdout.strip())
    for p, f in docs.items():
        fm, _ = fm_body(open(f).read())
        ty = re.search(r"^type:\s*(\w+)", fm, re.M); itf = re.search(r"^interfaces:\s*\[(.*)\]", fm, re.M)
        if ty and ty.group(1) in ("howto", "tutorial") and itf and len([x for x in itf.group(1).split(",") if x.strip()]) >= 2 and p not in referenced:
            W(f"parity: '{p}' declares several interfaces but no capability-matrix row points at it")

def check_help_links():
    """features/docs-experience V97 — product code holds keys; this proves every key still points at a page."""
    reg = f"{ROOT}/features/docs-experience/inventory/help-links.json"
    if not os.path.exists(reg): return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_help_links
    for e in gen_help_links.validate(json.load(open(reg))): E(f"help-links: {e}")
    if "--products" in sys.argv:
        r = subprocess.run([sys.executable, f"{os.path.dirname(os.path.abspath(__file__))}/gen_help_links.py", "--check"], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if line.startswith("ERROR"): E(line.replace("ERROR  ", "", 1))

def check_findability(docs):
    """features/docs-experience V109 — titles, descriptions and keywords are what the search box and the tab hover read."""
    seen = {}
    for p, f in docs.items():
        fm, _ = fm_body(open(f).read())
        g = lambda k: (re.search(rf"^{k}:\s*(.+)$", fm, re.M) or [None, ""])[1].strip().strip('"')
        title, desc, ty = g("title"), g("description"), g("type")
        if len(title) > 60: E(f"findability: {p}: title is {len(title)} characters (max 60)")
        if desc and not 30 <= len(desc) <= 200: E(f"findability: {p}: description is {len(desc)} characters (30-200)")
        if desc:
            if desc in seen: E(f"findability: {p}: description duplicates {seen[desc]}")
            seen[desc] = p
        if "keywords:" not in fm:
            if ty in ("troubleshooting", "tutorial"): E(f"findability: {p}: {ty} pages need `keywords` (the words a reader types)")
            elif ty == "howto": W(f"findability: {p}: howto page without `keywords`")

def check_reference():
    """features/docs-experience V108 — the glossary and service tables are generated; a new registry term cannot be forgotten."""
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_reference.py")
    if not os.path.exists(f"{ROOT}/features/docs-experience/inventory/terminology.csv"): return
    r = subprocess.run([sys.executable, gen, "--check"], capture_output=True, text=True, env={**os.environ, "DOCS_ROOT": ROOT})
    for line in r.stdout.splitlines():
        if line.startswith("ERROR"): E(line.replace("ERROR  ", "", 1))

def check_errors():
    """features/cli-experience V93/V99 — every registered failure code has a generated page, and the exit-status table is the CLI's."""
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_errors.py")
    if not os.path.exists(f"{ROOT}/features/docs-experience/inventory/problem-codes.json"): return
    r = subprocess.run([sys.executable, gen, "--check"], capture_output=True, text=True, env={**os.environ, "DOCS_ROOT": ROOT})
    for line in r.stdout.splitlines():
        if line.startswith("ERROR"): E(line.replace("ERROR  ", "", 1))

def check_shots(docs):
    man_path = f"{ROOT}/images/ui/manifest.json"
    have = set()
    if os.path.exists(man_path): have = {x["file"] for x in json.load(open(man_path))["shots"]}
    for p, f in docs.items():
        body = fm_body(open(f).read())[1]
        shots = re.findall(r"<Shot\b([^>]*?)/>", body, re.S)
        for attrs in shots:
            name = re.search(r'name="([^"]+)"', attrs); alt = re.search(r'alt="([^"]*)"', attrs)
            if not name: E(f"{p}: <Shot> without a name"); continue
            if not alt or len(alt.group(1).strip()) < 25: E(f"{p}: <Shot name={name.group(1)!r}> needs alt text of at least 25 characters saying what is shown")
            elif re.match(r"(?i)\s*(a |an |the )?(screenshot|image|picture|screen shot)\b", alt.group(1)): E(f"{p}: <Shot name={name.group(1)!r}> alt says 'screenshot' — state what is shown")
            for theme in ("light", "dark"):
                if f"{name.group(1)}-{theme}.png" not in have: E(f"{p}: image '{name.group(1)}-{theme}.png' is not in images/ui/manifest.json — run scripts/screenshots/capture.mjs")
        if re.match(r"interfaces/(dashboard|desktop)/", p) and not p.endswith("/workflows") and not shots:
            E(f"{p}: an interface guide must show at least one <Shot> (V95)")
    for rel in have:
        if not os.path.exists(f"{ROOT}/images/ui/{rel}"): E(f"images/ui/manifest.json lists '{rel}' but the file is missing")

def main():
    strict = "--strict" in sys.argv
    cfg = json.load(open(f"{ROOT}/docs.json"))
    docs = mdx_pages()
    nav, first_pages = nav_walk(cfg)
    check_matrix(docs)
    check_help_links()
    check_reference()
    check_errors()
    check_findability(docs)
    check_shots(docs)
    for p in nav:
        if p not in docs: E(f"nav: '{p}' is listed in docs.json but has no page")
    for p in sorted(set(docs) - set(nav)):
        if p != "index" or True: E(f"orphan: '{p}' is not in the navigation")
    seen_titles = {}
    terms = []
    tf = f"{ROOT}/features/docs-experience/inventory/forbidden-terms.txt"
    if os.path.exists(tf):
        for line in open(tf):
            if line.strip() and not line.startswith("#") and "\t" in line:
                rx, msg = line.rstrip("\n").split("\t", 1); terms.append((re.compile(rx), msg))
    for p, f in docs.items():
        fm, body = fm_body(open(f).read())
        def get(k):
            m = re.search(rf"^{k}:\s*(.*)$", fm, re.M); return m.group(1).strip().strip("\"'") if m else None
        title, desc, typ = get("title"), get("description"), get("type")
        if not title: E(f"{p}: missing title")
        if not desc: E(f"{p}: missing description")
        if typ not in TYPES: E(f"{p}: type must be one of {sorted(TYPES)} (got {typ!r})")
        if not p.startswith("cli") and not get("audience"): E(f"{p}: missing audience")
        if title and not p.startswith("cli/"):
            if title in seen_titles: E(f"{p}: title {title!r} duplicates {seen_titles[title]}")
            seen_titles[title] = p
        prose = strip_code(body)
        for rx, msg in terms:
            m = rx.search(prose)
            if m: E(f"{p}: '{m.group(0)}' — {msg}")
        if typ == "concept" and re.search(r"```(?:bash|sh|shell)\n(?:[^`]*\n)?\s*\$?\s*beaver ", body):
            W(f"{p}: concept page contains a `beaver` command block (explain, never instruct)")
        if typ in ("howto", "tutorial") and get("lastVerified") and get("interfaces"):
            declared = [x.strip() for x in re.sub(r"[\[\]]", "", get("interfaces")).split(",") if x.strip()]
            for itf in (declared if len(declared) > 1 else []):
                if not re.search(rf'<Tab title="{itf}"', body, re.I):
                    W(f"{p}: declares interface '{itf}' but has no <Tab title=\"{itf.title()}\">")
        if re.search(r"<img(?![^>]*\balt=)", body) or re.search(r"!\[\]\(", body):
            W(f"{p}: image without alt text")
    for tab, first in first_pages.items():
        fm, _ = fm_body(open(docs[first]).read()) if first in docs else ("", "")
        if not re.search(r"^type:\s*hub", fm, re.M):
            E(f"nav: first page of tab '{tab}' is '{first}' — it must be a hub")
    red = cfg.get("redirects") or []
    live = set(docs)
    for r in red:
        s, d = r["source"].lstrip("/"), r["destination"]
        if s in live: E(f"redirect: source '/{s}' is a live page")
        dd = d.split("#")[0].lstrip("/")
        if dd and dd not in live: E(f"redirect: '/{s}' -> '{d}' does not exist")
    srcs = {r["source"] for r in red}
    for r in red:
        if r["destination"] in srcs: E(f"redirect: '{r['source']}' chains through '{r['destination']}'")
    for f in glob.glob(f"{ROOT}/snippets/*.mdx"):
        t = open(f).read()
        if os.path.basename(f) in ("plan-ladder.mdx", "team-permission-matrix.mdx", "two-step-tables.mdx", "email-catalogue.mdx") and "GENERATED" not in t[:300]:
            E(f"snippets/{os.path.basename(f)}: lost its GENERATED header")
    for e in errors: print("ERROR  ", e)
    for w in warns: print("WARN   ", w)
    print(f"\n{len(docs)} pages · {len(errors)} errors · {len(warns)} warnings" + (" (strict)" if strict else ""))
    sys.exit(1 if errors or (strict and warns) else 0)

main()
