#!/usr/bin/env python3
"""
Era 1 V3 + V4 — maturity classification and final consolidated summary.

Merges commands.csv (V1) with doc_status.csv (V2), applies the maturity rule
(Hidden:true -> needs-classification; a small set of known partial-limitation
commands -> available-but-limited; everything else -> implemented-usable,
pending each family era's own deeper verification at writing time), and
writes 00-summary.docs — the single top-of-file number the roadmap's
acceptance gate (criterion 1) checks against zero `unresolved`.
"""
import csv
import re
from pathlib import Path
from collections import defaultdict, Counter

HERE = Path(__file__).parent
CMDS_CSV = HERE / "commands.csv"
DOC_STATUS_CSV = HERE / "doc_status.csv"
OUT_DOCS = HERE / "00-summary.docs"
BEAVER_CLI_COMMANDS = Path.home() / "Desktop/vhb/beaver-cli/commands"

LOOP_RE = re.compile(
    r"for\s+_,\s*(\w+)\s*:?=\s*range\s*\[\]\*cobra\.Command\{([^}]*)\}\s*\{([^}]*)\}",
    re.DOTALL,
)


def count_register_flags_commands():
    """Distinct commands that get --json/--output/--quiet/--yes/--wait/--timeout
    via output.RegisterFlags(cmd), direct or via a `for _, c := range
    []*cobra.Command{...}` loop — computed live against source rather than
    hardcoded, after the 2026-09-17 re-verification found the previous
    hardcoded "69" was stale (a raw call-site grep gives 145, since some
    call sites are direct 1-command calls and some are loops covering 20+
    commands each; the true distinct-command count is neither)."""
    seen = set()
    if not BEAVER_CLI_COMMANDS.exists():
        return None
    for f in BEAVER_CLI_COMMANDS.rglob("*.go"):
        if f.name.endswith("_test.go"):
            continue
        text = f.read_text(errors="replace")
        for m in re.finditer(r"output\.RegisterFlags\(([A-Za-z_][A-Za-z0-9_]*)\)", text):
            seen.add((str(f), m.group(1)))
        for lm in LOOP_RE.finditer(text):
            loopvar, items, body = lm.groups()
            if f"output.RegisterFlags({loopvar})" in body.replace(" ", ""):
                for name in (x.strip() for x in items.split(",")):
                    if name:
                        seen.add((str(f), name))
    return len(seen)

# Commands confirmed by source read (Era 1 V3) to have a real, documentable
# partial limitation — not a stub, not fully unavailable. Extend this table as
# family eras find more during their own deeper verification.
KNOWN_LIMITED = {
    ("ai", "connect"): "API-key authentication is not implemented by the local daemon; falls back to subscription sign-in (commands/ai/connect.go:112).",
}

# Directories confirmed (Era 1 V2) to contain zero cobra.Command definitions —
# support/library packages, not CLI surface. Excluded from the command
# inventory entirely; not a documentation gap.
NON_COMMAND_DIRS = {
    "deployui": "support code for deploy's terminal UI rendering, not a command group",
    "envbanner": "support code (env var banner rendering), not a command group",
    "internal": "internal/shared library code — confirmed zero cobra.Command definitions",
    "projectconfig": "support library, likely backing `config`/`projectcontract` — confirmed zero commands",
    "projectcontext": "support library — confirmed zero commands",
    "state": "support library backing `statecmd` — confirmed zero commands",
    "ui": "shared UI rendering helpers — confirmed zero commands",
}


def load_commands():
    """All rows (one per command, or one per command-flag pair), grouped by
    command group. Distinct-command counting is done separately by callers via
    the (group, file, cmd_line) key — do not dedupe here, it would drop every
    flag row after the first for a multi-flag command."""
    by_group = defaultdict(list)
    with CMDS_CSV.open() as f:
        for row in csv.DictReader(f):
            by_group[row["group"]].append(row)
    return by_group


def distinct_commands(rows):
    # (file, cmd_line, use) — line number alone collides when two commands are
    # built on the same source line (e.g. `AddCommand(f(true), f(false))`).
    seen = {}
    for r in rows:
        key = (r["file"], r["cmd_line"], r["use"])
        if key not in seen:
            seen[key] = r
    return list(seen.values())


def load_doc_status():
    status = {}
    with DOC_STATUS_CSV.open() as f:
        for row in csv.DictReader(f):
            status[row["group"]] = row["doc_status"]
    return status


def classify(group, use, hidden):
    if hidden == "true":
        return "needs-classification"
    if (group, use.split()[0] if use else "") in KNOWN_LIMITED:
        return "available-but-limited"
    return "implemented-usable"


def main():
    by_group = load_commands()
    doc_status = load_doc_status()
    register_flags_count = count_register_flags_commands()

    maturity_counts = Counter()
    doc_counts = Counter()
    group_rows = []

    for group in sorted(by_group):
        rows = by_group[group]
        cmds = distinct_commands(rows)
        n_cmds = len(cmds)
        n_flags = sum(1 for r in rows if r["flag_name"])
        n_dynamic = sum(1 for r in cmds if r.get("source_kind") == "factory")
        n_hidden = sum(1 for r in cmds if r["hidden"] == "true")
        status = doc_status.get(group, "undocumented")
        doc_counts[status] += 1
        for r in cmds:
            m = classify(group, r["use"], r["hidden"])
            maturity_counts[m] += 1
        group_rows.append((group, n_cmds, n_flags, n_dynamic, n_hidden, status))

    total_cmds = sum(r[1] for r in group_rows)
    total_flags = sum(r[2] for r in group_rows)
    total_dynamic = sum(r[3] for r in group_rows)
    total_hidden = sum(r[4] for r in group_rows)

    lines = []
    lines.append("# CLI Documentation Closure — Inventory Summary (Era 1 V4)")
    lines.append("")
    lines.append("Generated by extract_commands.py -> cross_reference.py -> build_summary.py")
    lines.append("against beaver-cli @ commands/ (2026-09-17 audit). Source of truth for every")
    lines.append("later era's \"my family's rows\" filter and for the roadmap's acceptance gate")
    lines.append("criterion 1 (zero rows in `unresolved` status).")
    lines.append("")
    lines.append("## Headline numbers")
    lines.append("")
    lines.append(f"- **{len(group_rows)} real command groups** (directories with at least one")
    lines.append("  `cobra.Command` definition), **{} total distinct commands**, **{} flags**.".format(total_cmds, total_flags))
    lines.append(f"- {total_dynamic} commands are built via a factory function (parameterized,")
    lines.append("  e.g. `service database <verb>`-style generators) rather than a literal")
    lines.append("  `&cobra.Command{}` — resolved by the extractor's Pass B/C, see")
    lines.append("  `extract_commands.py`'s module docstring for method.")
    lines.append(f"- {total_hidden} commands are `Hidden: true` in source (not shown in `--help`)")
    lines.append("  — all in `admin` (3) and `mcpcmd` (1) — flagged `needs-classification`,")
    lines.append("  not assumed excluded or assumed public.")
    lines.append(f"- **{len(NON_COMMAND_DIRS)} directories excluded entirely**: confirmed zero")
    lines.append("  `cobra.Command` definitions anywhere in their source — support/library code,")
    lines.append("  not CLI surface. Not a documentation gap. Listed below.")
    lines.append("")
    lines.append("## Doc-status breakdown (Era 1 V2)")
    lines.append("")
    for status, n in sorted(doc_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{status}**: {n} groups")
    lines.append("")
    lines.append("## Maturity breakdown (Era 1 V3, command-level)")
    lines.append("")
    for m, n in sorted(maturity_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{m}**: {n} command{'' if n == 1 else 's'}")
    lines.append("")
    lines.append("`unresolved` (the acceptance-gate criterion): **0** — every command has")
    lines.append("exactly one doc-status and one maturity tag by construction of this script.")
    lines.append("(\"Resolved\" here means *classified*, not yet *documented* — Phase 2 still")
    lines.append("has to write the pages. Zero-unresolved is Era 1's own done-when, not the")
    lines.append("whole roadmap's.)")
    lines.append("")
    lines.append("## Per-group table")
    lines.append("")
    lines.append("| Group | Commands | Flags | Dynamic | Hidden | Doc status |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for group, n_cmds, n_flags, n_dynamic, n_hidden, status in group_rows:
        lines.append(f"| `{group}` | {n_cmds} | {n_flags} | {n_dynamic} | {n_hidden} | {status} |")
    lines.append("")
    lines.append("## Excluded directories (confirmed zero commands, not a gap)")
    lines.append("")
    lines.append("| Directory | Why |")
    lines.append("| --- | --- |")
    for d, why in NON_COMMAND_DIRS.items():
        lines.append(f"| `{d}` | {why} |")
    lines.append("")
    lines.append("## Known partial-limitation commands (Era 1 V3, available-but-limited)")
    lines.append("")
    if KNOWN_LIMITED:
        for (group, verb), note in KNOWN_LIMITED.items():
            lines.append(f"- `{group} {verb}`: {note}")
    else:
        lines.append("- none found yet")
    lines.append("")
    lines.append("## Commands needing an explicit public-vs-internal classification")
    lines.append("")
    lines.append("(`Hidden: true` in source — Era 10 V34 / Era 11 V39 own the decision)")
    lines.append("")
    for group in sorted(by_group):
        for r in distinct_commands(by_group[group]):
            if r["hidden"] == "true":
                lines.append(f"- `{group}`: `{r['use']}` ({r['file']}:{r['cmd_line']})")
    lines.append("")
    lines.append("## Known extraction gap: `output.RegisterFlags()` shared flags (Era 2 V7)")
    lines.append("")
    rfc = register_flags_count if register_flags_count is not None else "an unknown number of"
    lines.append("The flag counts above come from literal `Flags().Kind(\"name\", ...)` call sites")
    lines.append("inside `commands/`. They do **not** include `--json`, `--output`, `--quiet`,")
    lines.append(f"`--yes`, `--wait`, `--timeout` on the **{rfc} commands** that attach them via one")
    lines.append("indirect call, `output.RegisterFlags(cmd)` (`beaver-cli/output/output.go`,")
    lines.append("outside `commands/` — confirmed by a live source scan (direct calls and the")
    lines.append("`for _, c := range []*cobra.Command{...}` loop form both counted; re-run by this")
    lines.append("script every regeneration, not a hardcoded figure — see `gaps/00-index.docs`")
    lines.append(f"entry 009). Every one of those {rfc} commands has 6 more flags than this file's")
    lines.append("per-group table shows. Documented authoritatively in `cli/shared-flags.mdx`.")
    lines.append("Phase 2 family eras should check `grep -rn output.RegisterFlags commands/<group>/`")
    lines.append("before assuming a command has no `--wait`/`--json`/etc. just because it's absent")
    lines.append("from `commands.csv`.")
    lines.append("")

    OUT_DOCS.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_DOCS}")
    print(f"Total command groups: {len(group_rows)}")
    print(f"Total commands: {total_cmds}, flags: {total_flags}")
    print(f"Excluded non-command directories: {len(NON_COMMAND_DIRS)}")


if __name__ == "__main__":
    main()
