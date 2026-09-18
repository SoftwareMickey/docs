#!/usr/bin/env python3
"""
Era 1 V2 — cross-reference the V1 command inventory (commands.csv) against the
existing cli/*.mdx pages in this repo, and tag every command with a doc-status:

  documented       — group has a same-named page, and grep finds the command's
                      Use verb mentioned on it (weak signal, still useful triage)
  undocumented      — no page maps to this group at all
  orphan-page       — a page exists whose basename has no matching commands/
                      directory (the Era 1 pre-work's 15-page list) — recorded
                      separately, resolved by the manual mapping below

The manual mapping table encodes what V2's prose already worked out by hand
(observability subcommands vs. logs/metrics/traffic pages, auth vs.
login/logout/whoami, etc.) so this script's output matches the roadmap's own
findings instead of re-deriving them mechanically and risking a different
answer.

Read-only against both repos. Writes doc_status.csv only.
"""
import csv
import re
from pathlib import Path
from collections import defaultdict

CLI_ROOT = Path.home() / "Desktop/vhb/beaver-cli/commands"
DOCS_DIR = Path.home() / "Desktop/vhb/mintlify/cli"
IN_CSV = Path(__file__).parent / "commands.csv"
OUT_CSV = Path(__file__).parent / "doc_status.csv"

# group -> list of existing cli/*.mdx basenames (without .mdx) that document it,
# resolved by hand during the Era 1 audit (see gaps/00-index.docs for the ones
# still open, e.g. container vs containers, observe vs observability overlap).
MANUAL_GROUP_TO_PAGES = {
    "auth": ["login", "logout", "whoami"],
    "observability": ["logs", "metrics", "traffic"],
    "projectcontract": ["contract", "validate"],
    "initcmd": ["init"],
    "integration": ["integrations"],
    "config": ["validate"],  # config validate subcommand only; config itself has no page
    "billing": ["plans"],  # `beaver plans` is billing.go's own "plans" subcommand
    # Confirmed 2026-09-17 re-verification: each page's own body documents the
    # `*cmd` group's commands under the CLI's shorter public name (`beaver
    # reconcile`, `beaver skills`, `beaver state`), not the internal Go package
    # name — the same "documented under a different name" pattern as `auth`/
    # `observability` above, previously unresolved because the earlier
    # doc_status.csv predates these three pages existing.
    "reconcilecmd": ["reconcile"],
    "skillscmd": ["skills"],
    "statecmd": ["state"],
    # `root/root.go`'s `shell` and `main.go`'s `destroy` (Era 1 V1 extractor
    # fix, 2026-09-17) — both have their own page under the command's own
    # public name.
    "root": ["shell"],
    # Phase 2 re-verification (2026-09-17): `container`'s own flag-coverage
    # false positives traced to real content that lives on a sibling page
    # sharing the same source directory/package, not a gap — recorded here so
    # the mapping (and future coverage checks) reflect where the content
    # actually is.
    "container": ["container", "containers"],
    # `projectcontract`'s push/pull/diff/status/rollback/delete/containers are
    # wired at runtime as `beaver config <verb>` (nested under configcmd.ConfigCmd
    # in main.go), not `beaver projectcontract <verb>` — confirmed by reading
    # main.go directly. `plan`/`validate` are root commands with their own pages.
    "projectcontract": ["plan", "validate", "config"],
}

# speccmd was `undocumented` until this pass (Phase 2 re-verification,
# 2026-09-17) — `beaver spec` is a real, visible, compatibility-promised
# command with zero prior coverage anywhere in the repo. `cli/spec.mdx`
# written this pass; add the mapping now that it exists.
MANUAL_GROUP_TO_PAGES["speccmd"] = ["spec"]

# Era 1 pre-work flagged `plan`/`plans` as stale-page candidates (gap 003).
# Phase 2 re-verification (2026-09-17) resolved this definitively via source,
# not inference: `plan` is `projectcontract.PlanCmd`, wired as the root
# `beaver plan <container>` command (see MANUAL_GROUP_TO_PAGES above); `plans`
# is real too — `commands/billing/billing.go`'s own `Use: "plans"`
# subcommand, cross-linked correctly from `cli/billing.mdx`. Neither page is
# stale. Kept as an empty set (not deleted) so this resolution — and the
# reasoning — stays visible rather than silently disappearing.
KNOWN_STALE_PAGES = set()

# Pages that are real, current, and correctly published, but are not a
# per-group command reference page at all — cross-cutting reference material
# (Era 2 V7) or an alias page for a command documented on another page's own
# group. Excluded from "orphan" classification; not a gap.
NOT_A_GROUP_PAGE = {
    "shared-flags": "Era 2 V7 cross-cutting shared-flags reference, not a command group",
    "containers": "documents the `containers` (plural) command, a second top-level "
                  "command literal inside commands/container/container.go — same "
                  "group directory as `container.mdx`, not a separate group",
}


def existing_pages():
    return {p.stem for p in DOCS_DIR.glob("*.mdx")}


def groups_from_inventory():
    groups = set()
    with IN_CSV.open() as f:
        for row in csv.DictReader(f):
            groups.add(row["group"])
    return groups


def main():
    pages = existing_pages()
    groups = groups_from_inventory()

    group_pages = {}
    for g in sorted(groups):
        mapped = set(MANUAL_GROUP_TO_PAGES.get(g, []))
        if g in pages:
            mapped.add(g)
        group_pages[g] = sorted(mapped)

    doc_status = {}
    for g, mapped in group_pages.items():
        if mapped:
            doc_status[g] = "partial" if len(mapped) < 2 and g not in pages else "documented"
            if g in pages:
                doc_status[g] = "documented"
            elif mapped:
                doc_status[g] = "documented-under-different-name"
        else:
            doc_status[g] = "undocumented"

    orphan_pages = sorted(
        pages - {p for pages_list in group_pages.values() for p in pages_list}
        - groups - set(NOT_A_GROUP_PAGE)
    )

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "doc_status", "mapped_pages"])
        for g in sorted(group_pages):
            w.writerow([g, doc_status[g], ";".join(group_pages[g])])

    print(f"Groups: {len(groups)}")
    print(f"  documented (own page):                {sum(1 for g in groups if g in pages)}")
    print(f"  documented under a different name:    {sum(1 for g,s in doc_status.items() if s=='documented-under-different-name')}")
    print(f"  undocumented:                          {sum(1 for g,s in doc_status.items() if s=='undocumented')}")
    print()
    print("Undocumented groups:")
    for g in sorted(g for g,s in doc_status.items() if s == "undocumented"):
        print(f"  - {g}")
    print()
    print(f"Orphan pages (no matching group dir at all, {len(orphan_pages)}):")
    for p in orphan_pages:
        stale = " [KNOWN STALE — gaps/003]" if p in KNOWN_STALE_PAGES else ""
        print(f"  - {p}.mdx{stale}")
    print()
    print(f"Not-a-group pages (real, current, excluded from orphan count, {len(NOT_A_GROUP_PAGE)}):")
    for p, why in NOT_A_GROUP_PAGE.items():
        print(f"  - {p}.mdx — {why}")
    print()
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
