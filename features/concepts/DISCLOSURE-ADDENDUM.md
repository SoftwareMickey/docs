# Disclosure Addendum — Concept Layer (Era 2 V5)

Extends `/features/docs/DISCLOSURE.md` — read that file first. Everything there applies
unchanged (the test, the general checkpoint-term list, the review procedure). This file
adds only what's specific to writing at concept altitude. Internal planning artifact; never
published.

## Why concept pages carry more risk than command pages

A command reference page can stay compliant while only stating a flag's accepted values and
default. A concept page's entire job is to answer "what is this, why does it work this way,
how does it relate to everything else" — the exact question a competitor also wants
answered. Every family era in this roadmap applies the base disclosure test *more*
aggressively than the sibling roadmap's own command-page eras, not equally.

## Additional checkpoint terms

On top of `/features/docs/DISCLOSURE.md`'s list (`reconcile` · `drift` · `desired state` ·
`contract` · `placement` · `routing` · `schema` · `orchestration` · `job` · `dispatch` ·
`queue`, plus its AI-surface additions):

`scheduling` · `bin-packing` · `capacity planning logic` · `credential provisioning` ·
`attachment mechanism` · `matching` · `auto-detection heuristics` · `health-check algorithm`
· `load-balancing strategy` · `TLS issuance mechanism` · `WAF rule engine` · `backup
encoding/format internals` · `detection logic` · `enforcement architecture` ·
`validation engine`

Extend this list the moment a family era's drafting surfaces a real risk term not already
here (Era 8 V28 names this explicitly as an expected occurrence, not an exception).

## The system diagram rule

`concepts/how-beaver-fits-together.mdx` (Era 3 V6) and any page reusing its diagram may show
**entities and relationships only** — workspace → project → environment → machine/cloud →
deployment → container → service, as boxes and arrows. It must never show **how a decision
between entities is made** (which machine a deployment lands on, which node a replica is
scheduled to). That arrow does not exist in the diagram — only the resulting, already-decided
relationship does.

## Worked examples, concept register

**Compliant** — Services (the topic `concepts-explained.txt` uses as its own worked
example):

> Attaching a PostgreSQL service to your application makes a connection string available to
> it as an environment variable. Your application can use it once the attachment takes
> effect — for most services, that means the next deployment. Detaching removes that
> variable; it does not delete the database itself unless you also delete the service.

**Non-compliant** — same topic, describing mechanism:

> When you attach a service, the platform provisions a scoped credential pair, writes an
> entry to the attachment table linking the service and deployment, and injects the
> resolved connection string into the container's environment at scheduling time.

The second version names the attachment schema, the credential-provisioning step, and the
scheduling-time injection mechanism — exactly the three things `concepts-explained.txt`
names directly as off-limits for this topic.

## Two-pass topics

The following pages require a second, independent full read-through before publishing, not
a single pass — same discipline as the sibling roadmap's Era 9/11 families, because they sit
on the highest-risk vocabulary in this addendum or the base `DISCLOSURE.md` list:

- `concepts/configuration.mdx` (Era 5 V15)
- `concepts/beaver-cloud.mdx` (Era 4 V13)
- `concepts/scaling-and-resources.mdx` (Era 7 V23)
- `concepts/firewall.mdx` (Era 7 V24)
- `concepts/state-and-drift.mdx` (Era 10 V33)
- `concepts/ai-connections-and-alie.mdx` (Era 11 V36)
- `concepts/administrative-commands.mdx`, if it exists (Era 11 V39)

## How to apply

1. Draft the page from the Era 2 template and verified behavior only (Invariant 1).
2. Read every sentence once, hunting for both this file's checkpoint terms and
   `DISCLOSURE.md`'s.
3. For each hit, apply the base test. Rewrite to the observable outcome, or cut.
4. For the two-pass topics above, do a second full read-through after step 3.
5. At Era 13 V44, every page (not just the two-pass list) gets one more independent sweep
   as the roadmap's closing gate.
