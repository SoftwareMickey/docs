# Fictional Example Vocabulary (Era 2 V7)

Fixed cast for every example across `cli/*.mdx`, per Invariant 5 ("examples are adaptable,
never real"). Internal planning note — not published. Family eras (Phase 2) reuse these
names instead of inventing new ones per page, so a reader moving between pages sees one
continuous scenario.

## The project

**`paperclip`** — a small multi-service SaaS app. Chosen for being obviously fictional,
easy to say, and short enough not to crowd out flag syntax in a terminal-width example.

- Repo / local dir: `paperclip/`
- Domain: `paperclip.example` (`.example` is IANA-reserved for documentation — never a
  real, resolvable domain)
- Machines: `srv_web01`, `srv_web02` (app tier), `srv_db01` (database tier)
- Cloud: `paperclip-prod` (a Beaver Cloud grouping `srv_web01`, `srv_web02`, `srv_db01`)

## Services attached to `paperclip`

- **`paperclip-web`** — the application container (the thing `beaver deploy` ships)
- **`paperclip-db`** — a managed Postgres service (`beaver service create postgres
  paperclip-db`)
- **`paperclip-cache`** — a managed Redis service (`beaver service create redis
  paperclip-cache`)

## People

- Example username: `ada` (as in `beaver account profile show --username ada`) — never a
  real name, never the same name used in a security-sensitive example (auth token, MFA
  secret) as in a routine one, to avoid any appearance of a real leaked credential pattern.

## What never appears in an example

- Real IP addresses, real domains, real credential-looking strings (use obviously-fake
  patterns: `sk_example_...`, never a string shaped exactly like a real key format).
- Real company names, real infrastructure identifiers (AWS account IDs, etc.).
- The word "test" or "demo" as the fictional project name — too easily confused with an
  actual test/demo the reader might have.

## Extending this list

If a family era needs a fictional resource this list doesn't cover (e.g. a backup
destination name, a firewall rule name), add it here rather than inventing one locally, so
later pages can reuse it too.
