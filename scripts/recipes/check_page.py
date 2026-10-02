#!/usr/bin/env python3
"""V99 — the page must not show a Dockerfile the harness did not run. Every ```dockerfile block in deploy/bring-your-own-app.mdx must
equal (ignoring indentation, blank lines and comments) the Dockerfile of one sample app in recipes/."""
import glob, os, re, sys

ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def norm(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


def main():
    page = open(f"{ROOT}/deploy/bring-your-own-app.mdx").read()
    blocks = [norm(b) for b in re.findall(r"```dockerfile[^\n]*\n(.*?)```", page, re.S)]
    apps = [norm(open(p).read()) for p in glob.glob(f"{ROOT}/recipes/*/Dockerfile")]
    bad = [b[0] for b in blocks if b not in apps]
    for b in bad: print(f"FAIL  a Dockerfile on the page (starting {b!r}) matches no sample app in recipes/")
    print(f"{len(blocks)} Dockerfile block(s) on the page, {len(bad)} not backed by a sample app")
    return 1 if bad or not blocks else 0


if __name__ == "__main__":
    sys.exit(main())
