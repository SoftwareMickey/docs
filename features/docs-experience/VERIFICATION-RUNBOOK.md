# Verification cadence and freshness (V116)

## Monthly — live walkthrough of the first-steps journeys (docs lead + one person who did not write the pages)
On a clean VM for each OS and a clean browser profile:
1. Sign up, install the CLI, `beaver login` → first deploy of a sample app from `recipes/` (Dashboard path, then CLI path).
2. Connect a machine (Dashboard "add node" and `beaver connect`); deploy to it.
3. Create a service, connect an app, back up and restore.
4. Add a domain (owner-supplied test domain); check TLS.
5. Invite a second account; make a production approval.
6. Desktop: install, sign in, open a project folder, find the machine.
Log every dead end, missing prerequisite, and CLI/Dashboard/Desktop contradiction as a gap or a fix PR. When a step passes live, set `verified: verified` and `lastVerified` on the page; otherwise it stays `source-reviewed`.

## Quarterly — cross-repo audit
Re-run `scripts/build_surfaces.py`, `check-commands.py` against a CLI built from `main`, `check-interface-coverage.py`, `product_links.py`, `gen_help_links.py --check`, `find_test.py`. Diff against the previous quarter's `inventory/`. Every new command, route or section is documented or excluded with a reason.

## Freshness
`python3 scripts/freshness.py` lists verified pages past the 90-day SLA; the nightly job runs it with `--strict`. A stale page is re-verified (re-read the source, re-run its commands) and its `lastVerified` bumped, or downgraded to `source-reviewed` with the reason.

## Monthly — feedback and analytics review (V111/V112)
Mintlify page feedback (thumbs, suggest-edit, raise-issue) is on in `docs.json`. Review failed searches, top exits and low-rated pages; produce a short change list (new keywords, a missing page, a fix) and record it in the `eras_implementation.docs` log. No PII is kept; analytics follow the site's consent policy (Gap 017).
