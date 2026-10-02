# Launch gate — V117 verdict record

**Verdict as of 2026-10-02: NO-GO.** Every check an agent can run passes. The gate also requires things only the owner can do; until the owner reports them done the verdict stays NO-GO (it is never marked done by an agent).

## Mechanical checks (run 2026-10-02, all green)
| Check | Result |
| --- | --- |
| `mint validate`, `mint broken-links` | pass, 0 broken links |
| `check-docs.py --strict` (frontmatter, nav, types, hubs, orphans, parity, terminology, help links, screenshots, findability, reference) | 252 pages · 0 errors · 0 warnings |
| `test_check_docs.py` (every rule fails on a seeded violation) | pass |
| Interface parity (`gen_capability_matrix.py --check`, 75 tasks) | pass |
| Interface coverage (`check-interface-coverage.py`) | 137 routes/sections · 0 errors |
| Disclosure sweep (`check-disclosure.py` + `--fixture`) | 0 hits; the seeded leak fails |
| Typo gate (`check-spelling.py` + `--fixture`) | 0 typos; the seeded typo fails |
| Sample apps — Dockerfile + port contract (`recipes/run.py`) | 3/3 green on Docker 29.1.3; the page shows only Dockerfiles those apps ran (`check_page.py`) |
| CLI commands/flags in the docs vs a CLI built from source | 1,432 checked · 0 problems |
| `.beaver/config.yml` examples vs `beaver validate`; Dockerfiles vs `beaver config inspect` | 6 checks · 0 problems |
| Team docs vs server/CLI (`check-team-docs.py`) | pass |
| Help links (107 keys) and product-emitted URLs | 0 errors |
| Find test (30 tasks, local search proxy) | 30/30 (100%); threshold 90% |
| Freshness (`freshness.py`) | 0 of 81 verified pages past the 90-day SLA |
| Troubleshooting pages | 18 symptom pages (≥ 12) |
| Docs checklist in the five product repos' PR templates | present in all five |

## Owner steps (the reason for NO-GO)
1. **Re-score the scorecard by someone who did not write the pages** (the author cannot grade their own work).
2. **Clean-machine journeys on each interface** — Gap 018/021: no clean VM, second account, provider accounts, owner-supplied domain or connected browser were available. Pages that depend on them are marked `source-reviewed`, not `verified`.
3. **Live find test with real readers** — the 30/30 above is a local search proxy; Mintlify's own ranking may differ.
4. **Decisions still open:** D1 naming model (Gap 002), D2 tab count after a render check at 1280/1024/390 px (Gap 001), D3 where operator docs live (Gap 004), Gap 015 public deployment spec, Gap 016 feedback triage owner, Gap 017 analytics consent.
5. **Owner review** of shared-responsibility and security-checklist claims (Gaps 013, 023).
6. Commit and deploy the docs branch; confirm the docs deploy trigger (Gap 006).

When 1–3 are done and 4–6 answered, re-run this table, update the verdict and date.
