# How this docs site is maintained (V118)

Internal — not published (`features/` is in `.mintignore`). The roadmap lives in `~/Desktop/vhb/beaver-desktop/features/docs-experience`; that folder's `eras_implementation.docs` is the maintenance log.

## The tree rules
- 10 tabs, each opening with a `type: hub` page; no nav group over 12 pages; depth ≤ 2. Empty future pages are never listed.
- Every page has `type` (`hub|concept|howto|tutorial|troubleshooting|reference|interface-guide`), `audience`, and — when it describes a how-to across surfaces — `interfaces` plus a Tab per declared interface.
- Concept pages carry no commands. Commands live in how-tos and the CLI reference.
- **There are no per-framework, per-language or per-runtime pages.** Any app with a Dockerfile and a listening port runs; `deploy/bring-your-own-app` is the one page, backed by the sample apps in `recipes/`. Do not add a framework page; extend the page's checklist or failure table instead.
- Moved or removed pages get a redirect (`inventory/redirects-*.csv` → `scripts/gen_redirects.py`). Never leave a live page as a redirect source.

## Templates and registries
| What | Where |
| --- | --- |
| Page templates | `features/docs-experience/templates/*.tpl` |
| Capability matrix (task × interface) | `snippets/data/capability-matrix.json` → `scripts/gen_capability_matrix.py` |
| Help-link keys (product → docs deep links) | `inventory/help-links.json` → `scripts/gen_help_links.py` |
| Route/section coverage (Dashboard, Desktop) | `inventory/route-coverage.csv` → `scripts/check-interface-coverage.py` |
| Terminology and glossary | `inventory/terminology.csv` → `scripts/gen_reference.py` |
| Disclosure patterns and allowlist | `inventory/disclosure-patterns.txt`, `disclosure-allowlist.txt` |
| Typo list | `inventory/typos.txt` |
| Find-test tasks and results | `scripts/find_test.py`, `inventory/find-test*.md` |
| Sample apps (the Dockerfile + port contract) | `recipes/*`, `scripts/recipes/run.py`, `scripts/recipes/check_page.py` |
| Screenshots | `scripts/screenshots/` (seeded demo data only) |

Generated files say so in their first line; edit the source, regenerate, commit both.

## Scripts and CI (`.github/workflows/docs-check.yml`)
PR fast path: `mint validate`, `mint broken-links`, `check-docs.py --strict`, `test_check_docs.py`, `gen_capability_matrix.py --check`, `check-disclosure.py` (+ `--fixture`), `check-spelling.py` (+ `--fixture`), the two pilot sample apps, `check_page.py`, `freshness.py`. Nightly: all sample apps and `freshness.py --strict`.
Run against the real products before a release: `check-commands.py` (CLI built from source), `check-config-examples.py`, `check-team-docs.py`, `product_links.py`, `gen_help_links.py --check`, `gen_reference.py --check`, `find_test.py`.

## Cadence
See `VERIFICATION-RUNBOOK.md` (monthly walkthrough, quarterly cross-repo audit, 90-day freshness SLA, monthly analytics review). Findings go to `beaver-desktop/features/docs-experience/gaps/` or a fix PR.

## Releases
Docs ship on the same release train as the product change (Invariant 13). Each product repo's PR template carries the docs checklist (`OWNERSHIP.md`).

## Who to ask
See `OWNERSHIP.md`.
