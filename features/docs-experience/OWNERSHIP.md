# Ownership map (V115)

| Area | Source of truth | Owner role |
| --- | --- | --- |
| Site structure, templates, registries, CI | `mintlify` | docs lead |
| `beaver` commands, flags, output, exit codes | `beaver-cli` | CLI owner |
| Routes, errors, limits, plans, services, notifications | `vhb-server` | backend owner |
| Dashboard screens, labels, help links | `vhb-client` | client owner |
| Desktop sections, settings, terminal | `beaver-desktop` | desktop owner |
| Operator tooling (never public) | `admin-dashboard` | admin owner — private runbook only (Gap 004) |

## The docs checklist
Every product repo has `.github/pull_request_template.md` with a docs checklist: a new or changed command, flag, UI label, limit, status or error message means a docs update in the same release train, or an explicit "no user-visible change".

| Repo | Template |
| --- | --- |
| `beaver-cli` | `.github/pull_request_template.md` (also: `check-commands.py` against the branch) |
| `vhb-server` | `.github/pull_request_template.md` (also: regenerate permission/billing/service tables) |
| `vhb-client` | `.github/pull_request_template.md` (also: help-link registry) |
| `beaver-desktop` | `.github/pull_request_template.md` (also: screenshot pipeline) |
| `admin-dashboard` | `.github/pull_request_template.md` — "update private runbook"; never mention the tool in public docs |

CODEOWNERS for user-facing strings is optional and left to each repo owner; add the docs lead as a reviewer of the strings file if wanted.
