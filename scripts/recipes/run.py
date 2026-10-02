#!/usr/bin/env python3
"""features/docs-experience V99 — the recipe harness. For each recipes/<name>/ it builds the Dockerfile, runs the container and asserts:

  1. the image builds
  2. the container starts and stays up
  3. GET <health> returns 200 and a body containing the expected text (and GET / returns 200)
  4. the process is not root (docker exec id -u), and the image declares a HEALTHCHECK
  5. Docker's own health status becomes `healthy`
  6. when the recipe reads PORT, the same image answers on a different PORT (-e PORT=4321)

  run.py                  every recipe
  run.py --pilot          the pilot recipes only (the fast path CI runs on every pull request)
  run.py --only a,b       some recipes
  run.py --stamp          on success write recipes/verified.json (date, docker version, image size)
  run.py --keep           leave the images in place

Requires Docker and network access (base images).
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DOCS_ROOT") or os.path.dirname(os.path.dirname(HERE))
RECIPES = f"{ROOT}/recipes"
BUILD_TIMEOUT, UP_TIMEOUT = 900, 90


def sh(*args, timeout=None, check=False):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=check)


def get(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return None, ""


def host_port(cid, port):
    out = sh("docker", "port", cid, f"{port}/tcp").stdout.strip().splitlines()
    return out[0].rsplit(":", 1)[1] if out else None


def wait_status(cid, want, timeout):
    end = time.time() + timeout
    while time.time() < end:
        s = sh("docker", "inspect", "-f", "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}", cid).stdout.strip()
        state, _, health = s.partition("|")
        if state != "running":
            return False, f"container is {state}"
        if want(health): return True, health
        time.sleep(1)
    return False, "timed out"


def run_container(tag, port, env=None, name=""):
    args = ["docker", "run", "-d", "--name", name, "-p", f"127.0.0.1::{port}", "--health-interval=2s", "--health-timeout=3s", "--health-retries=5", "--health-start-period=1s"]
    for k, v in (env or {}).items(): args += ["-e", f"{k}={v}"]
    r = sh(*args, tag)
    return r.stdout.strip() if r.returncode == 0 else None, r.stderr.strip()


def poll_http(cid, port, path, expect, timeout=UP_TIMEOUT):
    hp = host_port(cid, port)
    end = time.time() + timeout
    while time.time() < end:
        hp = hp or host_port(cid, port)
        if hp:
            code, body = get(f"http://127.0.0.1:{hp}{path}")
            if code == 200 and (not expect or expect in body): return True, hp
        if sh("docker", "inspect", "-f", "{{.State.Running}}", cid).stdout.strip() != "true":
            return False, "container exited: " + sh("docker", "logs", "--tail", "15", cid).stdout[-400:] + sh("docker", "logs", "--tail", "15", cid).stderr[-400:]
        time.sleep(1)
    return False, f"no 200 with {expect!r} on {path} within {timeout}s"


def check(meta, keep):
    name, port = meta["name"], meta["port"]
    tag, cname = f"beaver-recipe-{name}:test", f"beaver-recipe-{name}-{os.getpid()}"
    t0 = time.time(); fails = []; info = {}
    b = sh("docker", "build", "-t", tag, f"{RECIPES}/{name}", timeout=BUILD_TIMEOUT)
    if b.returncode != 0:
        return {"name": name, "ok": False, "fails": ["build failed:\n" + (b.stderr or b.stdout)[-1500:]], "secs": round(time.time() - t0)}
    info["image_mb"] = round(int(sh("docker", "image", "inspect", "-f", "{{.Size}}", tag).stdout.strip() or 0) / 1e6)
    try:
        cid, err = run_container(tag, port, env=meta.get("run_env"), name=cname)
        if not cid:
            fails.append("docker run failed: " + err)
        else:
            ok, detail = poll_http(cid, port, meta["health"], meta["expect"])
            if not ok: fails.append(f"health path: {detail}")
            else:
                code, _ = get(f"http://127.0.0.1:{detail}/")
                if code != 200: fails.append(f"GET / returned {code}, want 200")
                uid = sh("docker", "exec", cid, "id", "-u").stdout.strip()
                if uid in ("", "0"): fails.append(f"runs as root (uid {uid or '?'}) — add a non-root USER")
                hc = sh("docker", "image", "inspect", "-f", "{{if .Config.Healthcheck}}yes{{end}}", tag).stdout.strip()
                if hc != "yes": fails.append("the image declares no HEALTHCHECK")
                else:
                    ok, h = wait_status(cid, lambda s: s == "healthy", 60)
                    if not ok or h != "healthy": fails.append(f"Docker health status never became healthy ({h})")
            sh("docker", "rm", "-f", cid)
            if not fails and meta.get("port_env"):
                alt = 4321
                cid, err = run_container(tag, alt, env={**meta.get("run_env", {}), "PORT": alt}, name=cname + "-p")
                if not cid: fails.append("docker run with PORT override failed: " + err)
                else:
                    ok, d2 = poll_http(cid, alt, meta["health"], meta["expect"], timeout=45)
                    if not ok: fails.append(f"with PORT={alt} the app did not answer: {d2}")
                    sh("docker", "rm", "-f", cid)
    finally:
        sh("docker", "rm", "-f", cname); sh("docker", "rm", "-f", cname + "-p")
        if not keep: sh("docker", "rmi", "-f", tag)
    return {"name": name, "ok": not fails, "fails": fails, "secs": round(time.time() - t0), **info}


def main():
    args = sys.argv[1:]
    names = sorted(d for d in os.listdir(RECIPES) if os.path.exists(f"{RECIPES}/{d}/recipe.json")) if os.path.isdir(RECIPES) else []
    metas = {n: json.load(open(f"{RECIPES}/{n}/recipe.json")) for n in names}
    if "--only" in args: names = [n for n in args[args.index("--only") + 1].split(",") if n in metas]
    elif "--pilot" in args: names = [n for n in names if n in PILOTS]
    if not names:
        print("no recipes selected"); return 2
    results = []
    for n in names:
        r = check(metas[n], "--keep" in args); results.append(r)
        print(("PASS" if r["ok"] else "FAIL") + f"  {n:10} {r['secs']:>4}s" + (f"  {r.get('image_mb', '?')} MB" if r["ok"] else ""), flush=True)
        for f in r["fails"]: print("      " + f.replace("\n", "\n      "))
    bad = [r for r in results if not r["ok"]]
    if "--stamp" in args:
        p = f"{RECIPES}/verified.json"; cur = json.load(open(p)) if os.path.exists(p) else {}
        docker = sh("docker", "version", "--format", "{{.Server.Version}}").stdout.strip()
        for r in results:
            if r["ok"]: cur[r["name"]] = {"date": datetime.date.today().isoformat(), "docker": docker, "image_mb": r.get("image_mb")}
            else: cur.pop(r["name"], None)
        json.dump(dict(sorted(cur.items())), open(p, "w"), indent=2); open(p, "a").write("\n")
    print(f"{len(results) - len(bad)}/{len(results)} recipes green")
    return 1 if bad else 0


PILOTS = ("go-binary", "node-server")

if __name__ == "__main__":
    sys.exit(main())
