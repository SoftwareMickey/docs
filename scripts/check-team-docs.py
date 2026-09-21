#!/usr/bin/env python3
"""features/plans/team V59/V66 — checks that the Team docs cannot drift from the shipped code.

  scripts/check-team-docs.py --server ~/Desktop/works/vhb-server --cli ~/Desktop/vhb/beaver-cli --beaver <built beaver binary>

1. Every subcommand listed by `beaver workspace --help` has a row in cli/workspace.mdx.
2. Every `beaver workspace <sub>` used in an example anywhere in the docs is a real subcommand.
3. Every message and error code quoted in guides/troubleshooting-teams.mdx (first column, and the
   parenthesised CODE) exists verbatim in the backend or CLI source — placeholders like <id> and "..."
   split a message into fragments, and each fragment must exist.
4. Every generated snippet carries the "GENERATED FILE" header (the content itself is checked by
   `go run ./tools/permdoc -check <snippets dir>` in vhb-server).
Exit 1 with a list on any failure.
"""
import argparse, os, re, subprocess, sys

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--beaver", required=True)
    ap.add_argument("--docs", default=".")
    a = ap.parse_args()
    fail = []

    # 1. subcommands
    help_out = sh(f"HOME=$(mktemp -d) {a.beaver} workspace --help").stdout
    m = re.search(r"◆ COMMANDS\n(.*?)\n\n", help_out, re.S)
    subs = [l.split()[0] for l in m.group(1).splitlines() if l.strip()] if m else []
    if not subs: fail.append("could not read the subcommand list from `beaver workspace --help`")
    page = open(f"{a.docs}/cli/workspace.mdx").read()
    for s in subs:
        if not re.search(r"^\| `%s[ `]" % re.escape(s), page, re.M):
            fail.append(f"cli/workspace.mdx has no row for `beaver workspace {s}`")

    # 2. examples use real subcommands (only inside code: fenced blocks and `inline` spans, never prose)
    valid = set(subs)
    for root, _, files in os.walk(a.docs):
        if any(p in root for p in ("node_modules", "/.git", "/features")): continue
        for f in files:
            if not f.endswith(".mdx"): continue
            in_fence = False
            for i, line in enumerate(open(os.path.join(root, f), errors="ignore"), 1):
                if line.strip().startswith("```"):
                    in_fence = not in_fence
                    continue
                code = line if in_fence else " ".join(re.findall(r"`([^`]+)`", line))
                for mm in re.finditer(r"beaver workspace ([a-z][a-z-]+)", code):
                    if mm.group(1) not in valid:
                        fail.append(f"{os.path.join(root, f)}:{i}: `beaver workspace {mm.group(1)}` is not a subcommand")

    # 3. quoted messages exist in source
    def in_source(fragment):
        if len(fragment) < 8: return True
        for base in (a.server, a.cli):
            r = sh(f"grep -rFl --include='*.go' -- {shq(fragment)} {base} 2>/dev/null | grep -v _test.go | head -1")
            if r.stdout.strip(): return True
        return False

    tpage = open(f"{a.docs}/guides/troubleshooting-teams.mdx").read()
    checked = 0
    for line in tpage.splitlines():
        if not line.startswith("| ") or line.startswith("| You see") or line.startswith("| ---"): continue
        first = line.split(" | ")[0][2:].strip()
        spans = re.findall(r"``\s*(.+?)\s*``|`([^`]+)`", first)
        for dbl, sgl in spans:
            text = (dbl or sgl).strip()
            if re.fullmatch(r"[A-Z][A-Z_]+", text):            # an error code
                frags = [text]
            elif text.startswith("--") or text.startswith("beaver "):   # a flag / command, not a message
                continue
            else:
                frags = [f.strip(" .;:'\"") for f in re.split(r"<[^>]*>|\.\.\.|…|\bN\b|\b5\b", text)]
                frags = [f.replace("`", "") for f in frags if len(f.strip()) >= 8]
                # a CLI hint can embed a backticked command; compare the text before it
                frags = [re.split(r"Run |run ", f)[0].strip(" ,;.") for f in frags]
                frags = [f for f in frags if len(f) >= 8]
            for fr in frags:
                checked += 1
                if not in_source(fr) and not in_source(fr.lower()) and not in_source(fr.capitalize()):
                    fail.append(f"guides/troubleshooting-teams.mdx quotes {fr!r}, which is in neither the backend nor the CLI source")

    # 4. generated snippets are marked
    for name in ("team-permission-matrix.mdx", "plan-ladder.mdx"):
        p = f"{a.docs}/snippets/{name}"
        if not os.path.exists(p) or "GENERATED FILE" not in open(p).read(200) :
            fail.append(f"snippets/{name} is missing or lacks the GENERATED FILE header")

    print(f"subcommands checked: {len(subs)}; quoted fragments checked: {checked}")
    if fail:
        print("\n".join("FAIL: " + f for f in fail)); sys.exit(1)
    print("Team docs checks passed")

def shq(s):
    return "'" + s.replace("'", "'\\''") + "'"

if __name__ == "__main__":
    main()
