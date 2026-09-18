# Disclosure Checklist (Era 2 V5)

Operationalizes Invariant 6 — "observable behavior only" — from `00-architecture.docs`,
directly from `docs.txt` rule 6 and this repo's `CLAUDE.md` trade-secret list. Internal
planning artifact; never published.

## The test

For every sentence describing *why* or *how* a command works, ask:

> Would a competitor learn our mechanism from this sentence, or only what the product does?

If the former: cut it, or move it to internal engineering docs (`beaver-cli`/`vhb-server`'s
own docs, outside this repo). If the latter: it's fine, however technical it sounds.

## Named checkpoint terms

Not automatic redactions — a signal to stop and apply the test above. Pulled from the actual
CLI vocabulary found during the Era 1 audit (`statecmd`, `projectcontract`, `cloud`
`network`/`placements`, `edge`/`firewall` rule ordering):

`reconcile` · `drift` · `desired state` · `contract` · `placement` · `routing` · `schema` ·
`orchestration` · `job` · `dispatch` · `queue`

AI-surface additions (Era 11): `tool definition` · `system prompt` · `context injection` ·
`tool-use loop` · `agent harness` · `model routing`

## Worked examples

**Low risk — `machine drain` (wholly observable):**

> `beaver machine drain <name>` stops new workloads from being scheduled onto this machine
> and waits for running containers to finish or be moved before returning. Use `--timeout`
> to bound how long it waits; on timeout, the machine is left in draining state and the
> command exits non-zero — re-run to continue waiting, or `--force` to proceed anyway.

Nothing here describes *how* scheduling or migration is decided — only what the user sees
and controls. Compliant as written.

**Medium risk — `state drift` (needs the checklist, still fine once applied):**

✅ *Compliant:* "`beaver state drift` shows what has changed since your last `apply` — one
row per difference between what you last applied and what's running now."

❌ *Non-compliant:* "`drift` is computed by diffing the reconciler's desired-state graph
against agent-reported container hashes, refreshed on each agent heartbeat."

The second version is the exact shape of leak this whole roadmap exists to prevent — it
names the mechanism (reconciler, desired-state graph, agent heartbeat) instead of the
observable outcome (a list of differences).

**Not published without an explicit pass:** anything under `projectcontract`/`statecmd`
(Era 9) and `mcpcmd`/`alie` tool-approval flows (Era 11) — every sentence run through this
checklist before merge, not sampled.

## How to apply

1. Draft the page using only the command's own `--help` output and source-verified behavior
   (Invariant 1).
2. Read every sentence once, specifically hunting for the checkpoint terms above.
3. For each hit, apply the test. Rewrite to the observable outcome, or cut.
4. For Era 9 and Era 11 pages specifically, do a second full read-through after step 3 —
   these families get two passes, not one (see `09-config-state-and-contracts.docs` V30 and
   `13-verification-and-sustaining-process.docs` V45).
