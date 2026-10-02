# 30-task find test (benchmark — fixed; reused by V110 and V117)

Method: start from the docs home, record clicks (or searches) to reach the page that *answers* the
task. "Today" = measured on the pre-migration tree (2026-10-01) by walking the navigation and
checking whether an answering page exists at all. `target` = page that must answer it after Eras 3–14.

| # | Task (as a user phrases it) | Persona | Today | target |
| --- | --- | --- | --- | --- |
| 1 | Which interface should I start with? | ev | no page | start/choose-your-interface |
| 2 | Deploy a Dockerfile app from GitHub | dev | partial: quickstart (dashboard only), cli/deploy | deploy/from-github |
| 3 | Deploy from my laptop without GitHub | dev | cli/deploy only | deploy/from-local-project |
| 4 | Deploy a docker-compose app | dev | concepts only | deploy/compose-applications |
| 5 | Set an environment variable | dev | deploying/environment-variables (buried in group 6) | deploy/environment-variables |
| 6 | My build fails | dev | no page | operate/troubleshoot-build |
| 7 | Add a custom domain | dev | guides/domains | network/domains |
| 8 | My domain doesn't resolve | ops | no page | operate/troubleshoot-domain |
| 9 | App returns 502/503 | ops | no page | operate/troubleshoot-502-503 |
| 10 | Roll back a bad release | ops | guides/rollback-and-recovery | deploy/rollback-and-recovery |
| 11 | Promote staging to production | lead | cli/promote | deploy/promote |
| 12 | Scale to more replicas | ops | guides/scaling | deploy/scale |
| 13 | Connect my first machine | ops | connect | infrastructure/connect-a-machine |
| 14 | Machine shows offline | ops | no page | operate/troubleshoot-machine-offline |
| 15 | Create a Beaver Cloud | ops | concepts/beaver-cloud + cli/cloud | infrastructure/clouds |
| 16 | Set up an AWS machine | ops | infrastructure-setup/aws | infrastructure/aws |
| 17 | Create a Postgres database | dev | services/postgresql | data/create-a-service |
| 18 | Get my database connection string | dev | concepts only | data/credentials-and-connection-strings |
| 19 | Connect to my database from my laptop | dev | concepts/connecting-to-services-locally | data/connect-locally |
| 20 | Back up and restore a database | ops | concepts/backups-and-restoration | data/backups-and-restore |
| 21 | Invite a teammate | lead | guides/invite-and-manage-members | teams/invite-members |
| 22 | Give someone production access / approvals | lead | concepts/production-safety-and-approvals | teams/production-approvals |
| 23 | Turn on 2-step verification | sec | concepts/two-step-verification | teams/two-step-verification |
| 24 | Why can't I deploy — plan limit | lead | concepts/plans-and-billing | operate/troubleshoot-plan-limit |
| 25 | Connect an AI provider for Alie | dev | concepts/ai-connections-and-alie (thin) | alie/connect-an-ai-provider |
| 26 | Use the Desktop app to see my machines | dev | no page | interfaces/desktop/infrastructure |
| 27 | Find a feature in the Dashboard (e.g. build minutes) | dev | no page | interfaces/dashboard/activity-notifications-billing |
| 28 | Run deploys from CI | dev | concepts/automation | deploy/ci-cd |
| 29 | Open ports a machine needs | ops | infrastructure-setup/firewall-requirements | infrastructure/firewall-requirements |
| 30 | Is X Dashboard/Desktop/CLI capable of Y? | ev | no page | interfaces/capability-matrix |
