#!/usr/bin/env python3
"""Ties the VPN coexistence troubleshooting page to the server's finding families
(features/vpn-tunnel V53): every `cloud.wireguard_*` family vhb-server can emit must
have exactly one `### \\`family\\`` entry in operate/troubleshoot-cloud-vpns.mdx, and
the page must never tell a reader to remove, rename or stop another VPN.

Not in CI (needs the vhb-server checkout): VHB_SERVER=/path/to/vhb-server python3 scripts/check-tunnel-docs.py
"""
import os
import re
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
server = os.environ.get("VHB_SERVER", os.path.expanduser("~/Desktop/works/vhb-server"))
sev = os.path.join(server, "preflight", "severity.go")
if not os.path.exists(sev):
    print("vhb-server not found (set VHB_SERVER); skipping")
    sys.exit(0)

families = sorted(set(re.findall(r'"(cloud\.wireguard_[a-z_]+)"\s*:', open(sev).read())))
families = [f for f in families if f != "cloud.wireguard_unavailable"]  # the module/tooling finding has its own page
families.append("cloud.cidr_conflict")
page = open(os.path.join(root, "operate", "troubleshoot-cloud-vpns.mdx")).read()
headings = re.findall(r"^### `([a-z_.]+)`", page, re.M)

problems = []
for f in families:
    n = headings.count(f)
    if n != 1:
        problems.append(f"{f}: {n} entries (want exactly 1)")
for h in set(headings):
    if h.startswith("cloud.") and h not in families:
        problems.append(f"{h}: documented but the server no longer declares it")
low = page.lower()
for bad in ("remove or rename the vpn", "uninstall your vpn", "stop your vpn", "disable your vpn", "turn off your vpn"):
    if bad in low:
        problems.append(f"the page tells the reader to {bad}")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print(f"{len(families)} finding families, each documented once")
