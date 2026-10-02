# Find test results (Era 21 V110)

Recorded 2026-10-02 by `python3 scripts/find_test.py --record`. Model: a local BM25-style search over title, sidebar title, keywords,
description, headings and body, run twice per task (the task as typed, then its content words); a task passes when its target page is in the navigation and ranks in the top 3 for either run.
The real Mintlify search may rank differently; this is the repeatable proxy, and the live find test with real readers is a launch-gate owner step.

**Before tuning: 19/30 (63%).  After: 30/30 (100%).  Threshold: 90%.**

| # | Task | Before (best rank) | After (best rank) | Target |
| --- | --- | --- | --- | --- |
| 1 | Which interface should I start with? | top 1 | top 1 | `start/choose-your-interface` |
| 2 | Deploy a Dockerfile app from GitHub | top 1 | top 1 | `deploy/from-github` |
| 3 | Deploy from my laptop without GitHub | miss | top 2 | `deploy/from-local-project` |
| 4 | Deploy a docker-compose app | miss | top 1 | `deploy/compose-applications` |
| 5 | Set an environment variable | top 2 | top 2 | `deploy/environment-variables` |
| 6 | My build fails | top 1 | top 1 | `operate/troubleshoot-build` |
| 7 | Add a custom domain | miss | top 1 | `network/domains` |
| 8 | My domain doesn't resolve | top 1 | top 1 | `operate/troubleshoot-domain` |
| 9 | App returns 502/503 | top 1 | top 1 | `operate/troubleshoot-502-503` |
| 10 | Roll back a bad release | miss | top 1 | `deploy/rollback-and-recovery` |
| 11 | Promote staging to production | top 2 | top 1 | `deploy/promote` |
| 12 | Scale to more replicas | top 2 | top 1 | `deploy/scale` |
| 13 | Connect my first machine | top 2 | top 3 | `infrastructure/connect-a-machine` |
| 14 | Machine shows offline | top 1 | top 1 | `operate/troubleshoot-machine-offline` |
| 15 | Create a Beaver Cloud | top 1 | top 1 | `infrastructure/clouds` |
| 16 | Set up an AWS machine | top 1 | top 1 | `infrastructure/aws` |
| 17 | Create a Postgres database | top 1 | top 2 | `data/create-a-service` |
| 18 | Get my database connection string | miss | top 1 | `data/credentials-and-connection-strings` |
| 19 | Connect to my database from my laptop | miss | top 2 | `data/connect-locally` |
| 20 | Back up and restore a database | miss | top 1 | `data/backups-and-restore` |
| 21 | Invite a teammate | top 1 | top 1 | `teams/invite-members` |
| 22 | Give someone production access / approvals | top 1 | top 3 | `teams/production-approvals` |
| 23 | Turn on 2-step verification | top 1 | top 1 | `teams/two-step-verification` |
| 24 | Why can't I deploy — plan limit | top 1 | top 1 | `operate/troubleshoot-plan-limit` |
| 25 | Connect an AI provider for Alie | top 1 | top 1 | `alie/connect-an-ai-provider` |
| 26 | Use the Desktop app to see my machines | miss | top 2 | `interfaces/desktop/infrastructure` |
| 27 | Find a feature in the Dashboard (e.g. build minutes) | miss | top 1 | `interfaces/dashboard/activity-notifications-billing` |
| 28 | Run deploys from CI | top 1 | top 1 | `deploy/ci-cd` |
| 29 | Open ports a machine needs | miss | top 1 | `infrastructure/firewall-requirements` |
| 30 | Is X Dashboard/Desktop/CLI capable of Y? | miss | top 1 | `interfaces/capability-matrix` |

What changed: page titles rewritten to the task a reader types ("Add a custom domain", "Roll back a bad release", "Back up and restore a service"), `keywords` added with the
synonyms people use ("roll back", "connection string", "open ports"), every tutorial, troubleshooting and how-to page now carries keywords, and two benchmark targets that pointed at
pages renamed during the build (#26, #27) were corrected. `check-docs.py` now enforces title length, description length and uniqueness, and keywords.
