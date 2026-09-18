#!/usr/bin/env python3
"""
Era 1 V1 — full command/flag extraction for the CLI Documentation Closure roadmap.

Walks beaver-cli/commands/**/*.go, finds every `<varName>[:]= &cobra.Command{...}`
literal, extracts Use/Short/Hidden/Deprecated from the literal body, then finds
every `<varName>.Flags()/<varName>.PersistentFlags().<Kind>Var(...)` call in the
same file and attributes it to the command whose Go variable name matches the
call's receiver — this is the actual pattern beaver-cli uses (flags registered
in an `init()` at the bottom of the file, keyed by the command's variable name,
not lexically nested inside the command literal). A small nearest-preceding
fallback handles the rare case where a flag call's receiver can't be resolved to
a named command variable in the same file.

Output: commands.csv, one row per (command, flag) pair, plus one row per
command with an empty flag for commands with zero flags — so every command is
represented at least once.

Read-only. Never writes to beaver-cli.
"""
import csv
import re
import sys
from pathlib import Path

CLI_ROOT = Path.home() / "Desktop/vhb/beaver-cli/commands"
OUT_CSV = Path(__file__).parent / "commands.csv"

# Two files register real, invocable top-level commands *outside* `commands/`
# entirely (confirmed by a full-repo `&cobra.Command{` sweep, 2026-09-17):
# `root/root.go`'s `shell` (no `commands/shell/` directory exists — it's a
# true root-level command) and `main.go`'s `destroy` (a short-form alias for
# `container <name> delete`, registered directly in `func main()`, not inside
# any package under `commands/`). CLI_ROOT.iterdir() alone never sees either
# file, so they were completely absent from every version of this inventory
# until this fix — `destroy` is a destructive command with zero documentation
# coverage found as a result. Scanned as a synthetic group, `root`, with the
# program's own root command (`Use: "beaver"`) filtered out afterward since
# it isn't an invocable subcommand.
EXTRA_ROOT_FILES = [
    Path.home() / "Desktop/vhb/beaver-cli/root/root.go",
    Path.home() / "Desktop/vhb/beaver-cli/main.go",
]

# var fooCmd = &cobra.Command{   OR   fooCmd := &cobra.Command{   OR   fooCmd = &cobra.Command{
CMD_ASSIGN_RE = re.compile(
    r"(?:^|\n)\s*(?:var\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?::?=)\s*&cobra\.Command\{"
)

# func fooCmd(args...) *cobra.Command {   ... return &cobra.Command{...} ...
FACTORY_DEF_RE = re.compile(
    r"(?:^|\n)func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\*cobra\.Command\s*\{"
)
# a call site assigning a factory's return value to a var:
#   fooVar = someFactory(arg1, arg2, ...)   OR   fooVar := someFactory(...)
FACTORY_CALL_RE = re.compile(
    r"(?:^|\n)\s*(?:var\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?::?=)\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\(([^\n]*?)\)\s*(?=,|\n|$)",
    re.MULTILINE,
)
STRING_LITERAL_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
USE_SUFFIX_RE = re.compile(r'Use:\s*\w+\s*\+\s*"((?:[^"\\]|\\.)*)"')
FIELD_RES = {
    "use": re.compile(r'Use:\s*"((?:[^"\\]|\\.)*)"'),
    "short": re.compile(r'Short:\s*"((?:[^"\\]|\\.)*)"'),
    "aliases": re.compile(r"Aliases:\s*\[\]string\{([^}]*)\}"),
    "hidden": re.compile(r"Hidden:\s*(true|false)"),
    "deprecated": re.compile(r'Deprecated:\s*"((?:[^"\\]|\\.)*)"'),
}

# <recv>.Flags().StringVarP(&x, "name", "s", "default", "usage")
# <recv>.Flags().Bool("name", false, "usage")
# <recv>.PersistentFlags().IntVar(&x, "name", 0, "usage")
FLAG_RE = re.compile(
    r"(?P<recv>[A-Za-z_][A-Za-z0-9_]*)\.(?:Flags|PersistentFlags)\(\)\."
    r"(?P<kind>[A-Za-z0-9]+?)(?P<varp>VarP?)?\(\s*"
    r"(?:&[A-Za-z0-9_.\[\]]+\s*,\s*)?"              # optional &var,
    r'"(?P<name>[a-zA-Z0-9][a-zA-Z0-9-]*)"\s*,\s*'  # "flag-name",
    r'(?:"(?P<short>[a-zA-Z0-9])"\s*,\s*)?'          # optional "x", (shorthand, VarP forms)
    r"(?P<default>[^,]*?)\s*,\s*"                    # default value (up to next comma)
    r'"(?P<usage>(?:[^"\\]|\\.)*)"',                 # "usage text"
    re.DOTALL,
)


def find_matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def collect_factory_defs(text: str) -> dict:
    """fname -> {"use": literal-or-None, "use_suffix": literal-or-None, "short": str}
    for every `func fname(...) *cobra.Command { ... return &cobra.Command{...} }`
    in this file. Package-scoped in Go, so callers merge this across every file
    in a command group directory before resolving call sites (Pass B/C)."""
    defs = {}
    for m in FACTORY_DEF_RE.finditer(text):
        fname = m.group(1)
        open_brace = text.index("{", m.end() - 1)
        close_brace = find_matching_brace(text, open_brace)
        if close_brace == -1:
            continue
        body = text[open_brace:close_brace]
        cmd_lit = re.search(r"&cobra\.Command\{", body)
        if not cmd_lit:
            continue
        cb_open = body.index("{", cmd_lit.start())
        cb_close = find_matching_brace(body, cb_open)
        cmd_body = body[cb_open:cb_close] if cb_close != -1 else body
        use_m = FIELD_RES["use"].search(cmd_body)
        short_m = FIELD_RES["short"].search(cmd_body)
        suffix_m = USE_SUFFIX_RE.search(cmd_body)
        defs[fname] = {
            "use": use_m.group(1) if use_m else None,
            "use_suffix": suffix_m.group(1) if suffix_m else None,
            "short": short_m.group(1) if short_m else "",
        }
    return defs


def resolve_factory_use(fdef: dict, fname: str, argstr: str):
    """Best-effort Use string for one call site, given its factory's definition
    and the literal call arguments. Returns None if not resolvable."""
    arg_literals = STRING_LITERAL_RE.findall(argstr)
    if fname == "monitoringPut" and not arg_literals:
        arg_literals = ["enable" if argstr.strip() == "true" else "disable"]
    if fdef["use"]:
        return fdef["use"]
    if fdef["use_suffix"] is not None and arg_literals:
        return arg_literals[0] + fdef["use_suffix"]
    if arg_literals:
        return arg_literals[0]
    return None


def extract_file(path: Path, group: str, rows: list, group_factory_defs: dict):
    text = path.read_text(errors="replace")
    rel = path.relative_to(CLI_ROOT.parent)

    commands = {}       # var_name -> dict(meta)
    span_order = []      # list of var_name in source order, for fallback

    for m in CMD_ASSIGN_RE.finditer(text):
        var_name = m.group(1)
        open_brace = text.index("{", m.end() - 1)
        close_brace = find_matching_brace(text, open_brace)
        if close_brace == -1:
            continue
        body = text[open_brace:close_brace]
        use_m = FIELD_RES["use"].search(body)
        if not use_m:
            continue
        short_m = FIELD_RES["short"].search(body)
        hidden_m = FIELD_RES["hidden"].search(body)
        dep_m = FIELD_RES["deprecated"].search(body)
        alias_m = FIELD_RES["aliases"].search(body)
        commands[var_name] = {
            "var": var_name,
            "start": open_brace,
            "end": close_brace,
            "use": use_m.group(1),
            "short": (short_m.group(1) if short_m else ""),
            "hidden": (hidden_m.group(1) if hidden_m else "false"),
            "deprecated": (dep_m.group(1) if dep_m else ""),
            "aliases": (alias_m.group(1) if alias_m else ""),
            # m.start(1) (the var-name group), not m.start() — the regex's
            # leading `(?:^|\n)\s*` can swallow blank/comment lines before the
            # actual `var Foo = ...` line, anchoring m.start() to the *previous*
            # line and under-reporting the source location. Found during the
            # 2026-09-17 V1 re-verification pass.
            "line": line_of(text, m.start(1)),
            "flags": [],
        }
        span_order.append(var_name)

    # --- Pass B: commands built via a factory function (`return &cobra.Command{...}`)
    # and assigned at a call site (`fooVar = someFactory("use-string", ...)`), rather
    # than a literal `&cobra.Command{}` assigned directly to a var (Pass A above).
    # `group_factory_defs` is resolved package-wide by main() since Go files in the
    # same command-group directory share a package and can call each other's
    # factory functions. Bounded, deliberate handling — see gaps/00-index.docs.
    if group_factory_defs:
        for m in FACTORY_CALL_RE.finditer(text):
            var_name, fname, argstr = m.group(1), m.group(2), m.group(3)
            if fname not in group_factory_defs or var_name in commands:
                continue
            use_val = resolve_factory_use(group_factory_defs[fname], fname, argstr)
            if use_val is None:
                continue
            open_brace_pos = m.end()
            commands[var_name] = {
                "var": var_name,
                "start": open_brace_pos,
                "end": open_brace_pos,
                "use": use_val,
                "short": group_factory_defs[fname]["short"] or "",
                "hidden": "false",
                "deprecated": "",
                "aliases": "",
                "line": line_of(text, m.start(1)),  # same fix as Pass A, see note above
                "flags": [],
                "dynamic": True,
            }

        # --- Pass C: inline factory calls with no variable at all, passed straight
        # into AddCommand(...) — e.g. `AddCommand(monitoringPut(true), monitoringPut(false))`.
        # No receiver var exists, so these can never carry attributed flags (there is
        # nothing for a later `.Flags()` call to be written against); recorded as
        # zero-flag commands under a synthetic var name so they aren't silently lost.
        inline_idx = 0
        for fname, fdef in group_factory_defs.items():
            for cm in re.finditer(re.escape(fname) + r"\(([^()\n]*)\)", text):
                argstr = cm.group(1)
                # Skip call sites already captured as a `var = factory(...)` assignment.
                line_start = text.rfind("\n", 0, cm.start()) + 1
                prefix = text[line_start:cm.start()]
                if re.search(r"[A-Za-z0-9_]\s*(?::?=)\s*$", prefix):
                    continue  # `var = factory(...)` — already captured above
                if re.search(r"func\s*$", prefix):
                    continue  # the factory's own `func fname(...) *cobra.Command {` definition
                use_val = resolve_factory_use(fdef, fname, argstr)
                if use_val is None:
                    continue
                synthetic_var = f"__inline_{fname}_{inline_idx}"
                inline_idx += 1
                pos = cm.end()
                commands[synthetic_var] = {
                    "var": synthetic_var, "start": pos, "end": pos,
                    "use": use_val, "short": fdef["short"] or "",
                    "hidden": "false", "deprecated": "", "aliases": "",
                    "line": line_of(text, cm.start()), "flags": [], "dynamic": True,
                }

    # --- Pass D: anonymous `&cobra.Command{Use: "...", ...}` literals passed
    # directly as call arguments (e.g. `parent.AddCommand(&cobra.Command{Use:
    # "init", ...}, &cobra.Command{Use: "sync", ...})`) — no var assignment
    # (Pass A misses these) and not inside a factory function body (Pass B/C
    # already resolves those via their call sites). Found by a fresh 2026-09-17
    # audit spot-check (commands/config/wizard.go) that Pass A/B/C together
    # still left 2 real commands (`config init`, `config sync`) completely
    # absent from the inventory. Recorded as zero-flag commands under a
    # synthetic var name, same convention as Pass C, since there is no var for
    # a later `.Flags()` call to attribute against.
    consumed_open_braces = {c["start"] for c in commands.values() if not c.get("dynamic")}
    factory_def_body_spans = []
    for fm in FACTORY_DEF_RE.finditer(text):
        fb_open = text.index("{", fm.end() - 1)
        fb_close = find_matching_brace(text, fb_open)
        if fb_close != -1:
            factory_def_body_spans.append((fb_open, fb_close))

    inline_idx = 0
    for lit_m in re.finditer(r"&cobra\.Command\{", text):
        open_brace = lit_m.end() - 1  # position of the literal's opening `{`
        if open_brace in consumed_open_braces:
            continue  # Pass A already has this one
        if any(span_open <= open_brace <= span_close for span_open, span_close in factory_def_body_spans):
            continue  # this is a factory function's own `return &cobra.Command{...}` — Pass B/C handle its call sites
        close_brace = find_matching_brace(text, open_brace)
        if close_brace == -1:
            continue
        body = text[open_brace:close_brace]
        use_m = FIELD_RES["use"].search(body)
        if not use_m:
            continue
        short_m = FIELD_RES["short"].search(body)
        hidden_m = FIELD_RES["hidden"].search(body)
        dep_m = FIELD_RES["deprecated"].search(body)
        alias_m = FIELD_RES["aliases"].search(body)
        synthetic_var = f"__inline_literal_{inline_idx}"
        inline_idx += 1
        commands[synthetic_var] = {
            "var": synthetic_var,
            "start": open_brace,
            "end": close_brace,
            "use": use_m.group(1),
            "short": (short_m.group(1) if short_m else ""),
            "hidden": (hidden_m.group(1) if hidden_m else "false"),
            "deprecated": (dep_m.group(1) if dep_m else ""),
            "aliases": (alias_m.group(1) if alias_m else ""),
            "line": line_of(text, lit_m.start()),
            "flags": [],
        }

    if not commands:
        return

    ordered_cmds = sorted(commands.values(), key=lambda c: c["start"])
    unattributed = []

    for fm in FLAG_RE.finditer(text):
        recv = fm.group("recv")
        entry = {
            "name": fm.group("name"),
            "short": fm.group("short") or "",
            "kind": fm.group("kind"),
            "default": fm.group("default").strip(),
            "usage": fm.group("usage"),
            "line": line_of(text, fm.start()),
            "idx": fm.start(),
        }
        if recv in commands:
            commands[recv]["flags"].append(entry)
        else:
            unattributed.append(entry)

    # Fallback for flags whose receiver isn't a known command var in this file
    # (e.g. a local `cmd` parameter inside a RunE closure, or a shared helper).
    # Attribute to the nearest command literal that lexically contains the call,
    # else the nearest preceding one.
    for entry in unattributed:
        containing = [c for c in ordered_cmds if c["start"] <= entry["idx"] <= c["end"]]
        target = None
        if containing:
            target = min(containing, key=lambda c: entry["idx"] - c["start"])
        else:
            preceding = [c for c in ordered_cmds if c["end"] < entry["idx"]]
            if preceding:
                target = max(preceding, key=lambda c: c["end"])
        if target:
            target["flags"].append(entry)

    for cmd in ordered_cmds:
        source_kind = "factory" if cmd.get("dynamic") else "literal"
        if not cmd["flags"]:
            rows.append({
                "group": group, "file": str(rel), "cmd_line": cmd["line"],
                "use": cmd["use"], "short_desc": cmd["short"], "aliases": cmd["aliases"],
                "hidden": cmd["hidden"], "deprecated": cmd["deprecated"],
                "source_kind": source_kind,
                "flag_name": "", "flag_shorthand": "", "flag_kind": "",
                "flag_default": "", "flag_usage": "", "flag_line": "",
            })
            continue
        for f in cmd["flags"]:
            rows.append({
                "group": group, "file": str(rel), "cmd_line": cmd["line"],
                "use": cmd["use"], "short_desc": cmd["short"], "aliases": cmd["aliases"],
                "hidden": cmd["hidden"], "deprecated": cmd["deprecated"],
                "source_kind": source_kind,
                "flag_name": f["name"], "flag_shorthand": f["short"],
                "flag_kind": f["kind"], "flag_default": f["default"],
                "flag_usage": f["usage"], "flag_line": f["line"],
            })


def main():
    if not CLI_ROOT.exists():
        print(f"ERROR: {CLI_ROOT} not found", file=sys.stderr)
        sys.exit(1)

    rows = []
    for group_dir in sorted(CLI_ROOT.iterdir()):
        if group_dir.is_file() and group_dir.suffix == ".go":
            text = group_dir.read_text(errors="replace")
            extract_file(group_dir, group_dir.stem, rows, collect_factory_defs(text))
            continue
        if not group_dir.is_dir():
            continue
        group = group_dir.name
        go_files = [p for p in sorted(group_dir.rglob("*.go")) if not p.name.endswith("_test.go")]
        # Factory functions are package-scoped (one Go package per command-group
        # directory) — resolve them once across every file in the group before
        # attributing any file's call sites (fixes cross-file factory calls, e.g.
        # machine/predictive.go calling genericGet() defined in machine/observe.go).
        group_factory_defs = {}
        for go_file in go_files:
            group_factory_defs.update(collect_factory_defs(go_file.read_text(errors="replace")))
        for go_file in go_files:
            extract_file(go_file, group, rows, group_factory_defs)

    for extra in EXTRA_ROOT_FILES:
        if extra.exists():
            text = extra.read_text(errors="replace")
            extract_file(extra, "root", rows, collect_factory_defs(text))
    # Drop the program's own root command (`Use: "beaver"`) — not an invocable
    # subcommand, just the entry point every other command hangs off.
    rows = [r for r in rows if not (r["group"] == "root" and r["use"] == "beaver")]

    fieldnames = [
        "group", "file", "cmd_line", "use", "short_desc", "aliases",
        "hidden", "deprecated", "source_kind", "flag_name", "flag_shorthand",
        "flag_kind", "flag_default", "flag_usage", "flag_line",
    ]
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n_cmds = len({(r["group"], r["file"], r["cmd_line"]) for r in rows})
    n_flags = sum(1 for r in rows if r["flag_name"])
    print(f"Wrote {len(rows)} rows to {OUT_CSV}")
    print(f"Distinct commands: {n_cmds}")
    print(f"Flag rows: {n_flags}")


if __name__ == "__main__":
    main()
