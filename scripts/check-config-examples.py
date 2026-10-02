#!/usr/bin/env python3
"""features/docs-experience V104/V105 — every `.beaver/config.yml` example in the docs must pass the real CLI's `beaver validate`, and every
recipe's Dockerfile must be read by `beaver config inspect` (its EXPOSEd port and HEALTHCHECK are what `beaver init` proposes from).

  BEAVER_BIN=/path/to/beaver scripts/check-config-examples.py
Build the binary from source first: `go build -o /tmp/beaver .` in beaver-cli.
"""
import glob, json, os, re, subprocess, sys, tempfile

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.environ.get("BEAVER_BIN", "beaver")
SKIP = ("features/", "blog/", "changelog/", "node_modules/", "recipes/")
HOME = tempfile.mkdtemp()
ENV = {**os.environ, "HOME": HOME, "NO_COLOR": "1"}
FENCE = re.compile(r"```ya?ml[^\n]*\.beaver/config\.yml[^\n]*\n(.*?)```", re.S)
bad = checked = 0

for f in sorted(glob.glob(f"{ROOT}/**/*.mdx", recursive=True)):
    rel = os.path.relpath(f, ROOT)
    if rel.startswith(SKIP): continue
    for i, m in enumerate(FENCE.finditer(open(f).read()), 1):
        d = tempfile.mkdtemp(); os.makedirs(f"{d}/.beaver")
        open(f"{d}/.beaver/config.yml", "w").write(m.group(1))
        r = subprocess.run([BIN, "validate"], cwd=d, env=ENV, capture_output=True, text=True, timeout=30)
        checked += 1
        if r.returncode != 0:
            bad += 1; print(f"ERROR  {rel} (example {i}): {(r.stdout + r.stderr).strip().splitlines()[0]}")

for meta_path in sorted(glob.glob(f"{ROOT}/recipes/*/recipe.json")):
    d = os.path.dirname(meta_path); meta = json.load(open(meta_path))
    r = subprocess.run([BIN, "config", "inspect"], cwd=d, env=ENV, capture_output=True, text=True, timeout=60)
    out = r.stdout + r.stderr; checked += 1
    if str(meta["port"]) not in out.split("Exposed ports")[-1].split("\n\n")[0] and "Exposed ports" in out or "Dockerfile healthcheck declared" not in out:
        bad += 1; print(f"ERROR  recipes/{meta['name']}: `beaver config inspect` does not report port {meta['port']} and a Dockerfile healthcheck:\n{out.strip()[:400]}")

print(f"{checked} checks · {bad} problems")
sys.exit(1 if bad else 0)
