#!/usr/bin/env python3
"""features/docs-experience — every `beaver ...` command and --flag written in the docs must exist in the real CLI.

  BEAVER_BIN=/path/to/beaver scripts/check-commands.py [--files a.mdx b.mdx] [--all]

Reads fenced code blocks and `inline code` in public pages (not blog/changelog/features), joins `\\` continuations,
walks the command path against `beaver <path> --help`, then checks each flag against that command's OPTIONS.
Placeholders (<x>, [x], {x}, ...) are skipped. Without --all only pages under start/ install/ deploy/ infrastructure/
data/ network/ operate/ teams/ alie/ interfaces/ reference/ are checked (cli/* was verified by features/docs).
Build the binary from source first: `go build -o /tmp/beaver .` in beaver-cli (the installed one may be older).
"""
import glob, os, re, shlex, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.environ.get("BEAVER_BIN", "beaver")
HOME = tempfile.mkdtemp()
cache = {}

def helptext(path):
    key = tuple(path)
    if key not in cache:
        r = subprocess.run([BIN, *path, "--help"], capture_output=True, text=True, env={**os.environ, "HOME": HOME, "NO_COLOR": "1"}, timeout=30)
        cache[key] = r.stdout + r.stderr
    return cache[key]

def top_level_ok(tok):
    t = helptext([tok]).splitlines()
    return bool(t) and t[0].strip().lstrip("◆ ").strip().upper() != "BEAVER CLI"   # unknown/alias tokens fall back to root help

def parse(path):
    t = helptext(path)
    cmds = set(); opts = set()
    if not path:   # root help is sectioned (COMMON COMMANDS, RESOURCES, ...), and some commands are unlisted — probe instead
        return None, set(re.findall(r"(--[a-zA-Z0-9][a-zA-Z0-9-]*)", t.split("◆ OPTIONS")[-1] if "◆ OPTIONS" in t else "")), t
    m = re.search(r"◆ COMMANDS\n(.*?)(?:\n\n|\n◆|\Z)", t, re.S)
    if m:
        for l in m.group(1).splitlines():
            if l.strip() and not l.startswith("    "):
                names = l.split()[0]; cmds.add(names)
                al = re.search(r"\(aliases?: ([^)]*)\)", l)
                if al: cmds.update(a.strip() for a in al.group(1).split(","))
    for o in re.findall(r"(--[a-zA-Z0-9][a-zA-Z0-9-]*)", t.split("◆ OPTIONS")[-1] if "◆ OPTIONS" in t else ""):
        opts.add(o)
    return cmds, opts, t

PLACEHOLDER = re.compile(r"^[<\[{(▸].*|.*[>\]})]$|^\.\.\.$|^\$|^…$|^▸$")
GLOBAL_FLAGS = {"--cwd", "--no-color", "--debug", "--workspace", "--help", "--version", "--json", "--output", "--quiet", "--yes", "--wait", "--timeout"}

def commands_in(text):
    out = []
    lines = text.splitlines(); in_fence = False; buf = ""; start = 0
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence; buf = ""; continue
        cands = []
        if in_fence:
            s = line.strip()
            if buf: s = buf + " " + s
            if s.endswith("\\"): buf = s[:-1].strip(); start = start or i; continue
            buf = ""
            cands.append(s.lstrip("$ ").strip())
        else:
            cands += re.findall(r"`(beaver [^`]+)`", line)
        for c in cands:
            c = re.split(r"\s+(?:\||&&|\|\||;|>|#)\s*", c)[0] if in_fence else c
            if c.startswith("beaver ") or c == "beaver": out.append((i, c))
    return out

def check(cmd):
    try: toks = shlex.split(cmd)
    except ValueError: return None
    toks = toks[1:]
    path = []; i = 0
    while i < len(toks) and not toks[i].startswith("-") and not PLACEHOLDER.match(toks[i]):
        cmds, _, _ = parse(path)
        if (cmds is None and top_level_ok(toks[i])) or (cmds and toks[i] in cmds): path.append(toks[i]); i += 1
        elif cmds is None: return f"unknown command `beaver {toks[i]}`"
        else:
            if cmds and not (re.match(r"^[a-z][a-z0-9-]*$", toks[i]) is None):
                # first non-subcommand token: an argument if the command takes args, else a bad subcommand
                _, _, t = parse(path)
                usage = re.search(r"◆ USAGE\n\s*(.*)", t)
                if usage and not re.search(r"[<\[]", usage.group(1).replace("[flags]", "").replace("[command]", "")):
                    return f"unknown subcommand `{' '.join(['beaver'] + path + [toks[i]])}`"
            break
    # a real subcommand written AFTER a placeholder argument (beaver machine <id> remove) is the wrong order
    if i < len(toks) - 1 and PLACEHOLDER.match(toks[i]) and path:
        cmds, _, _ = parse(path)
        if cmds and toks[i + 1] in cmds:
            return f"`beaver {' '.join(path)} {toks[i]} {toks[i+1]}` — the subcommand goes first: `beaver {' '.join(path)} {toks[i+1]} {toks[i]}`"
    _, opts, ht = parse(path)
    if "◆ OPTIONS" not in ht: return None   # action-style commands (beaver container <name> <action>) list flags per action
    for tk in toks[i:]:
        if tk.startswith("--") and not PLACEHOLDER.match(tk):
            f = tk.split("=")[0]
            if f not in opts and f not in GLOBAL_FLAGS: return f"`{' '.join(['beaver'] + path)}` has no flag {f}"
    return None

def main():
    files = []
    if "--files" in sys.argv: files = sys.argv[sys.argv.index("--files") + 1:]
    else:
        for f in glob.glob(f"{ROOT}/**/*.mdx", recursive=True):
            rel = os.path.relpath(f, ROOT)
            if rel.startswith(("blog/", "changelog/", "features/", "node_modules/")): continue
            if rel.startswith("snippets/") and rel != "snippets/capability-matrix.mdx": continue   # generated from the matrix data
            if rel.startswith("cli/") and "--all" not in sys.argv: continue
            files.append(f)
    bad = 0; n = 0
    for f in sorted(files):
        for ln, c in commands_in(open(f).read()):
            n += 1
            err = check(c)
            if err: bad += 1; print(f"{os.path.relpath(f, ROOT)}:{ln}: {err}   [{c[:80]}]")
    print(f"\n{n} commands checked, {bad} problems")
    sys.exit(1 if bad else 0)

main()
