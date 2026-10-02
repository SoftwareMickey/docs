# Disclosure boundary — addendum for Dashboard, Desktop and Admin (Era 2 V8)

Extends `features/docs/DISCLOSURE.md` (CLI rules). Internal planning note — not published.

## What a Dashboard / Desktop page may say
- What each screen is for, what it shows, what each control does, what the user will see afterward.
- Status words and badges exactly as shown, and what the user should do for each.
- Plan limits and gates a user can hit (values dated, one source).
- Equivalent CLI command shown by the UI (Desktop's action sheet prints it).

## What it may not say
- Why the platform chose a placement, a node, a route, or a retry (scoring, ranking, heuristics, thresholds).
- Internal job/queue/worker names, internal service names, database/table/field names, private endpoint paths.
- How credentials, tokens, challenges, sessions, backups or syncs work *inside*; only what the user does and sees.
- Detection or abuse-defence logic (firewall intel sources, ban heuristics, rate-limit algorithms beyond the
  user-visible limit and the error returned).
- Anything from `admin-dashboard`: capabilities, moderation tools, operator flows, support tooling.
- Unreleased or hidden UI as if shipped (Desktop Deployments/Observability sections, passkeys while off).

## Screenshots (Invariant 12)
Seeded demo data only; fictional vocabulary from `features/docs/VOCABULARY.md` (`paperclip`, `ada`,
`paperclip.example`); no real emails, hostnames, IPs, tokens, customer names, or account ids; browser chrome
cropped; light and dark variants; alt text states what is shown, not "screenshot".

## Admin decision (D3 — pending owner)
Public docs never reference admin-dashboard. Interim rule until the owner answers: operator runbooks stay
in `admin-dashboard` and the repos' internal `features/*/runbooks`; none enter `mintlify/` navigation.

## Review checklist (apply before merging any new Dashboard/Desktop/security page)
1. Every sentence is observable by a user. 2. No name from the "may not" list. 3. Statuses/limits copied from
UI/source and dated. 4. Hidden/unreleased features flagged "not yet available". 5. Screenshots follow the rules.
6. A reviewer other than the author ticked 1–5 (Era 22 automates 2).
