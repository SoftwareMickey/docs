#!/usr/bin/env python3
"""features/cli-experience V93/V99 — the generated error-code reference and exit-status table.

  gen_errors.py            write reference/errors/*.mdx and snippets/exit-status-table.mdx
  gen_errors.py --check    fail if any is out of date, or a registered code has no page
  gen_errors.py --sync SERVER_REPO CLI_REPO
                           refresh the inventory snapshots from vhb-server's problem/testdata/codes.golden.json
                           and beaver-cli's problem/testdata/exitstatus.golden.json, then regenerate

Sources (features/docs-experience/inventory/): problem-codes.json (a snapshot of the server's registry, the same list GET /api/problem/codes
serves), exit-status.json (the CLI's exit-status table, `beaver help exit-status`), problem-examples.json (recorded example documents).
A code added to the registry without regenerating leaves a code with no page, which `--check` (and check-docs.py) reports.
"""
import json, os, shutil, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV = f"{ROOT}/features/docs-experience/inventory"
HEAD = "{/* GENERATED FILE — do not edit. Regenerate with `python3 scripts/gen_errors.py`; sources: features/docs-experience/inventory/%s. */}\n\n"

CLASS_TITLE = {
    "authentication": "Sign-in", "authorization": "Permission", "not_found": "Not found", "conflict": "Conflict", "eligibility": "Eligibility",
    "invalid_input": "Invalid input", "rate_limit": "Rate limit", "unavailable": "Availability", "internal": "Internal", "quota": "Plan and quota",
    "state": "Resource state", "dependency": "Dependency",
}
# What a reader finds in a failure of each class: the generic guidance every code of the class shares.
CLASS_NEXT = {
    "authentication": "Sign in again with `beaver login`. In CI, set `BEAVER_TOKEN` and run `beaver login` once.",
    "authorization": "Ask an Owner or Admin of the workspace to do this or to change your role. If another workspace of yours has access, switch with `beaver workspace use`.",
    "not_found": "Check the name or id, and that you are acting in the right workspace (`beaver workspace list`). A resource you cannot see looks the same as one that does not exist.",
    "conflict": "The response names the resource it conflicts with. Resolve that, or choose a different name, then run the command again.",
    "eligibility": "Every requirement is listed with its status. Fix the failed ones — each has its own repair — then run the command again, or use `--check` to see the verdict without changing anything.",
    "invalid_input": "The response names the flag or argument and shows an accepted value. Run `beaver help <command>` for the command's flags.",
    "rate_limit": "Wait the number of seconds the response gives, then run the command again. Reads are retried for you; changes never are.",
    "unavailable": "This is temporary. The response says whether anything changed; if it says nothing changed, run the command again later.",
    "internal": "Beaver could not complete the operation. Quote the request id when you contact support: it identifies the exact failure.",
    "quota": "Your plan or the workspace limit stopped the operation. The response shows the limit and what you asked for.",
    "state": "The resource is not in a state this operation accepts. The response shows its current state and what it must be.",
    "dependency": "Something the operation depends on is not ready. The response names it.",
}


# Guidance specific to one code, where the class-wide sentence would be too vague to act on. Codes of
# features/services-durability point at the page that explains the whole situation (its anchors are checked).
CODE_NEXT = {
    "ATTACHMENTS_ACTIVE": "The response lists every attached application and the commands that follow. Detach them one by one, or run `beaver service delete NAME --detach-apps` to detach them all and delete in one step. See [A service's container went missing](/operate/service-container-missing#applications-are-still-attached).",
    "SERVICE_CONTAINER_ABSENT": "Run `beaver service check NAME`, then `beaver service recover NAME` to recreate the container from its data volume. Nothing was dispatched or changed. See [A service's container went missing](/operate/service-container-missing#the-container-is-missing).",
    "SERVICE_MACHINE_UNREACHABLE": "Wait until the machine is online and run the command again. For a detach you cannot wait for, `--revoke-later` records it now — the application's credential may still work until the machine is back. See [A service's container went missing](/operate/service-container-missing#the-machine-is-not-connected).",
    "SERVICE_MACHINE_REMOVED": "The machine is no longer enrolled, so its data can no longer be reached. `beaver service delete NAME --abandon` removes the service from Beaver and asks you to type its name. See [A service's container went missing](/operate/service-container-missing#the-machine-was-removed).",
    "SERVICE_VOLUME_MISSING": "Recover never creates an empty volume. List backups with `beaver service backup list NAME` and restore one with `beaver service restore NAME --backup ID`. See [A service's container went missing](/operate/service-container-missing#the-data-volume-is-missing).",
    "RECOVER_REFUSED": "The response carries a `refusal_code` and the next command. See [A service's container went missing](/operate/service-container-missing#recover-was-refused).",
}


def slug(code):
    return code.lower().replace("_", "-")


def load(name):
    return json.load(open(f"{INV}/{name}"))


def fm(title, desc, kw):
    return ["---", f'title: "{title}"', f'sidebarTitle: "{title}"', f'description: "{desc}"', 'icon: "triangle-alert"', "type: reference",
            "audience: [developer, operator]", f"keywords: {json.dumps(kw)}", "---", ""]


def example_for(code, entry, examples):
    ex = examples.get(code)
    if ex is None:
        ex = {"ok": False, "error": {"code": code, "message": entry["message"], "changed": False, "conditions": [], "repairs": [], "request_id": "req_…", "error": entry["message"]}}
    return json.dumps(ex, indent=2, ensure_ascii=False)


def exit_for(code, rows):
    for r in rows:
        if code in (r.get("codes") or []):
            return r["status"]
    return 1


def code_page(entry, examples, rows):
    c = entry["name"]
    cls = CLASS_TITLE.get(entry["class"], entry["class"].replace("_", " ").title())
    desc = f"What the {c} failure means, what the response contains, and how to fix it."
    out = fm(c, desc, [c, entry["message"], "error", "failure", "beaver help " + c])
    out += [HEAD.rstrip("\n") % "problem-codes.json", "",
            f"**{entry['message']}**", "", entry["doc"], "",
            "| | |", "| --- | --- |", f"| Code | `{c}` |", f"| Kind | {cls} |", f"| HTTP status | `{entry['http']}` |", f"| CLI exit status | `{exit_for(c, rows)}` |", "",
            "## What to do", "", CODE_NEXT.get(c) or CLASS_NEXT.get(entry["class"], "Read the conditions in the response: each says what was checked and how to fix it."), "",
            "## What the response contains", "",
            "Every failure — in the table output, `--json`, `--yaml` and the API — carries the same fields: `code`, `message`, `changed` (whether anything was altered), "
            "`conditions` (each requirement checked, with `status`, `detail` and a `repair`), `repairs`, a `retry` command and a `request_id`. "
            "Branch on `error.code`, never on the message text.", "",
            "```json", example_for(c, entry, examples), "```", "",
            f"Look it up offline with `beaver help {c}`. See [Exit codes and output formats](/reference/exit-codes-and-output) for what a script can rely on.", ""]
    return "\n".join(out)


def index_page(codes):
    by_class = {}
    for e in codes:
        by_class.setdefault(e["class"], []).append(e)
    out = fm("Error codes", "Every failure code Beaver can return, what it means and how to fix it, in one searchable reference.",
             ["error code", "failure", "beaver help", "error.code", "troubleshooting", "request id"])
    out += [HEAD.rstrip("\n") % "problem-codes.json", "",
            "Every refusal from the CLI, the API and the Dashboard carries a stable **code**. Scripts branch on `error.code` in `--json` output; people read the conditions and repairs under it. "
            "`beaver help CODE` prints the same entry offline. For the status a command exits with, see [Exit codes and output formats](/reference/exit-codes-and-output).", ""]
    for cls in sorted(by_class, key=lambda k: CLASS_TITLE.get(k, k)):
        out += [f"## {CLASS_TITLE.get(cls, cls.replace('_', ' ').title())}", "", "| Code | Meaning | HTTP |", "| --- | --- | --- |"]
        for e in sorted(by_class[cls], key=lambda e: e["name"]):
            out.append(f"| [`{e['name']}`](/reference/errors/{slug(e['name'])}) | {e['message']} | `{e['http']}` |")
        out.append("")
    return "\n".join(out)


def exit_table(rows):
    out = [HEAD % "exit-status.json" + "| Status | Where | Meaning |", "| --- | --- | --- |"]
    for r in rows:
        out.append(f"| `{r['status']}` | {r['scope']} | {r['meaning']} |")
    return "\n".join(out) + "\n"


def build():
    codes = load("problem-codes.json")
    examples = {k: v for k, v in load("problem-examples.json").items() if not k.startswith("_")}
    rows = load("exit-status.json")
    files = {"reference/errors/index.mdx": index_page(codes), "snippets/exit-status-table.mdx": exit_table(rows)}
    for e in codes:
        files[f"reference/errors/{slug(e['name'])}.mdx"] = code_page(e, examples, rows)
    return files, codes, examples


def nav_pages(codes):
    return ["reference/errors/index"] + [f"reference/errors/{slug(e['name'])}" for e in sorted(codes, key=lambda e: e["name"])]


def nav_tree(codes):
    """index first, then one subgroup per failure class (the docs lint caps a group at 12 pages)."""
    by = {}
    for e in codes:
        by.setdefault(e["class"], []).append(e["name"])
    groups = []
    for c in sorted(by, key=lambda c: CLASS_TITLE.get(c, c)):
        title = CLASS_TITLE.get(c, c.replace("_", " ").title())
        names = sorted(by[c])
        if len(names) <= 12:
            groups.append({"group": title, "pages": [f"reference/errors/{slug(n)}" for n in names]})
            continue
        # A class over the lint cap is split into sibling groups (the lint also caps nesting at 2):
        # "Invalid input · A–F", "Invalid input · G–P" ...
        for i in range(0, len(names), 10):
            ch = names[i:i + 10]
            span = f"{ch[0][0]}–{ch[-1][0]}" if ch[0][0] != ch[-1][0] else ch[0][0]
            groups.append({"group": f"{title} · {span}", "pages": [f"reference/errors/{slug(n)}" for n in ch]})
    return ["reference/errors/index"] + groups


def main():
    if "--sync" in sys.argv:
        i = sys.argv.index("--sync")
        server, cli = sys.argv[i + 1], sys.argv[i + 2]
        shutil.copy(f"{server}/problem/testdata/codes.golden.json", f"{INV}/problem-codes.json")
        shutil.copy(f"{cli}/problem/testdata/exitstatus.golden.json", f"{INV}/exit-status.json")
    files, codes, examples = build()
    bad = 0
    check = "--check" in sys.argv
    names = {e["name"] for e in codes}
    for k in examples:
        if k not in names:
            print(f"ERROR  errors: problem-examples.json has an example for {k}, which is not a registered code"); bad += 1
    for rel, text in files.items():
        p = f"{ROOT}/{rel}"
        have = open(p).read() if os.path.exists(p) else None
        if have != text:
            if check:
                print(f"ERROR  errors: {rel} is {'missing' if have is None else 'out of date'} — run python3 scripts/gen_errors.py"); bad += 1
            else:
                os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(text); print("wrote", rel)
    # stale pages for codes that no longer exist
    d = f"{ROOT}/reference/errors"
    if os.path.isdir(d):
        want = {os.path.basename(k) for k in files if k.startswith("reference/errors/")}
        for f in sorted(os.listdir(d)):
            if f.endswith(".mdx") and f not in want:
                if check:
                    print(f"ERROR  errors: reference/errors/{f} documents a code that is no longer registered"); bad += 1
                else:
                    os.remove(f"{d}/{f}"); print("removed", f)
    # navigation: every generated page is in docs.json
    nav = open(f"{ROOT}/docs.json").read()
    for page in nav_pages(codes):
        if f'"{page}"' not in nav:
            print(f"ERROR  errors: docs.json navigation lacks {page} — run python3 scripts/gen_errors.py --nav"); bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    if "--nav" in sys.argv:
        files, codes, _ = build()
        docs = json.load(open(f"{ROOT}/docs.json"))
        pages = nav_pages(codes)

        def walk(n):
            if isinstance(n, dict):
                if n.get("group") == "Error codes":
                    n["pages"] = nav_tree(codes); return True
                return any(walk(v) for v in n.values())
            if isinstance(n, list):
                return any(walk(v) for v in n)
            return False

        if not walk(docs):
            def put(n):
                if isinstance(n, dict):
                    if n.get("group") == "Configuration and limits":
                        return n
                    for v in n.values():
                        r = put(v)
                        if r: return r
                if isinstance(n, list):
                    for v in n:
                        r = put(v)
                        if r: return r
            g = put(docs)
            parent = None
            def find_parent(n):
                global parent
                if isinstance(n, dict):
                    for v in n.values(): find_parent(v)
                elif isinstance(n, list):
                    if g in n: parent = n
                    for v in n: find_parent(v)
            find_parent(docs)
            parent.append({"group": "Error codes", "pages": nav_tree(codes)})
        json.dump(docs, open(f"{ROOT}/docs.json", "w"), indent=2, ensure_ascii=False); open(f"{ROOT}/docs.json", "a").write("\n")
        print("docs.json navigation updated"); sys.exit(0)
    sys.exit(main())
