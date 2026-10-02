# Source for the operate/troubleshoot-* pages (Era 11 V65). Run: python3 features/docs-experience/inventory/symptoms.py
# Every command and message below was checked against beaver-cli / vhb-server source or an existing source-verified page.
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
S = [
 dict(slug="troubleshoot-build", title="My build fails", sidebar="Build fails", keywords=["build failed","docker build","push failed","dockerfile error"],
  desc="The build step failed or never started — read the build log, reproduce it, and check the Builder.", aud="developer", itf="dashboard, cli",
  see="The deployment shows **Failed** during the build stages, or stays **Queued** and never starts building.",
  check=["Read the build log: `beaver deploy --logs` (CLI) or the deployment's build history (Dashboard). The failing step is your Dockerfile's own output.",
         "Build it locally from a **fresh clone** of your branch: `docker build .` — if that fails too, it is your Dockerfile.",
         "Check the Builder: on that machine run `beaver doctor`, `beaver docker --auth` and `beaver git --auth`."],
  causes=[("A file the build needs is not committed","The Builder builds the commit you pushed. Anything generated locally or ignored by git is not there. Commit it, or generate it inside the Dockerfile."),
          ("The Builder cannot clone a private repository","The Builder clones with the GitHub login **on that machine**. Run `gh auth login` there and confirm with `beaver git --auth` — it is local, Beaver never sees it."),
          ("Docker Hub login missing or expired on the Builder","The image is pushed under your Docker Hub username. Run `docker login` on the Builder, then confirm with `beaver docker --auth`."),
          ("Builds stay Queued","No machine with the **Builder** role is available in the cloud, or the Builder is offline. `beaver machine list`; see [Machine shows offline](/operate/troubleshoot-machine-offline)."),
          ("Out of disk or memory on the Builder","Clean up old images and build cache on that machine, or use a bigger Builder.")],
  prove="`beaver container <name> rebuild` proves a fixed release builds and passes health checks without sending it live; `beaver preflight --full` does the same on a throwaway candidate.",
  rel=[("Builds","/deploy/builds"),("Your Dockerfile","/deploy/dockerfile-requirements")]),
 dict(slug="troubleshoot-deploy-unhealthy", title="Deployment is stuck or unhealthy", sidebar="Deployment unhealthy", keywords=["deployment stuck","unhealthy","health check failing","rollout"],
  desc="A release will not become healthy, or a stage never finishes — what to check and how to recover.", aud="developer, operator", itf="dashboard, cli",
  see="A deployment stays in one stage ([status words](/operate/deployment-status)), shows **Failed**, or the container keeps restarting.",
  check=["`beaver inspect` — current release, commit, health and the machine it landed on.",
         "`beaver observe --logs` — your app's own output. Look for a crash or a bind error.",
         "`beaver recover` — a read-only diagnosis with a Finding, Evidence and a suggested safe next step."],
  causes=[("The app binds to 127.0.0.1 or the wrong port","Listen on `0.0.0.0` and on the port your configuration says. Read the port from the `PORT` environment variable."),
          ("The health check path does not answer","Beaver waits for the configured HTTP path. Test it from inside the container, or change it: [Health checks](/deploy/health-checks)."),
          ("A required environment variable is missing for this environment","See [Environment variable is missing](/operate/troubleshoot-env-var)."),
          ("Not enough capacity on the cloud","`beaver cloud capacity <cloud>`; add a machine or lower the replica count ([Capacity and placement](/infrastructure/capacity-and-placement)).")],
  prove="A failed deployment does **not** roll back on its own. Under `rolling` the previous version keeps running; under `recreate` it stays down. To recover: `beaver recover --rollback` (last healthy release) or `beaver recover --restart`. See [Rollback and recovery](/deploy/rollback-and-recovery).",
  rel=[("Rollback and recovery","/deploy/rollback-and-recovery"),("Health checks","/deploy/health-checks")]),
 dict(slug="troubleshoot-domain", title="My domain does not resolve", sidebarsym=None, sidebar="Domain does not resolve", keywords=["domain not working","dns","cname","verification pending","repoint dns"],
  desc="Your custom domain does not reach your app — check DNS, verification and the route in one command.", aud="developer, operator", itf="dashboard, cli",
  see="`app.example.com` does not load, or `beaver domain list` shows the domain pending or **repoint DNS**.",
  check=["`beaver route inspect app.example.com` — live DNS, certificate and backend health in one place.",
         "`beaver domain list --container <name>` — the domain's state and any action needed.",
         "Compare the record at your DNS provider with the one `beaver domain add` printed."],
  causes=[("Wrong record type or target","A subdomain needs a **CNAME** to the target Beaver gave you; a bare domain needs **A** record(s) to the addresses it gave you."),
          ("Not propagated yet","DNS changes can take up to a few hours. Run `beaver domain verify <domain-id>` again later."),
          ("Cloudflare proxying is on","Set the record to **DNS only** (grey cloud) so verification and certificate issuance can see it."),
          ("`repoint DNS` in the ACTION column","A CNAME still points at an old Beaver target that no longer resolves. See [Domains](/network/domains#if-beaver-domain-list-says-repoint-dns)."),
          ("You are visiting an old deployment address","Only the app's default address and your attached domains route. Older per-deployment addresses stop answering.")],
  prove="", rel=[("Domains","/network/domains"),("TLS and route checks","/network/tls"),("First domain","/start/first-domain")]),
 dict(slug="troubleshoot-tls", title="Certificate error or certificate not issued", sidebar="Certificate error", keywords=["tls","https","certificate","ssl","not secure"],
  desc="The browser warns about the certificate, or issuance stays pending.", aud="developer, operator", itf="dashboard, cli",
  see="HTTPS shows a warning, or `beaver route inspect` reports the certificate as anything other than active.",
  check=["`beaver route inspect <domain>` — it reports the certificate provider and state.",
         "Confirm DNS resolves to Beaver first: certificates are issued only once it does."],
  causes=[("DNS not correct or not propagated","Fix the record, wait, then `beaver domain verify <domain-id>`."),
          ("Cloudflare proxy in front","Use **DNS only** (grey cloud) while the certificate is issued."),
          ("Wrong address","Use the app's default address `https://<name>.vectorihub.com` or a domain attached with `beaver domain add` — not an older deployment address.")],
  prove="Once DNS is right, re-provision with `beaver domain certificate <domain-id>`.", rel=[("TLS and route checks","/network/tls"),("Domains","/network/domains")]),
 dict(slug="troubleshoot-502-503", title="My app returns 502 or 503", sidebar="502 / 503", keywords=["502","503","bad gateway","service unavailable","app down"],
  desc="Requests reach Beaver but your app does not answer — find out whether it is unhealthy, unreachable or blocked.", aud="developer, operator", itf="dashboard, cli",
  see="Your address answers with a 502 or 503 (or another gateway error) instead of your app.",
  check=["`beaver inspect` — is the release healthy, and where is it running?",
         "`beaver observe --logs` — is your app crashing or erroring?",
         "`beaver route inspect <domain>` — does it report the backend as healthy?",
         "`beaver firewall overview <deployment-id>` — has a rule, ban or **lockdown** been applied?"],
  causes=[("No healthy replica","The health check is failing. See [Deployment is stuck or unhealthy](/operate/troubleshoot-deploy-unhealthy)."),
          ("Wrong port, or bound to localhost","The app must listen on the configured port on `0.0.0.0`."),
          ("The machine is offline","If the Host is offline, see [Machine shows offline](/operate/troubleshoot-machine-offline)."),
          ("Firewall lockdown or private visibility","`beaver firewall lockdown` blocks **all** traffic until `beaver firewall unlock`; `visibility set --private` makes a service unreachable from outside immediately."),
          ("Scaled to zero capacity","`beaver scaling replicas <container>` shows the running replica slots.")],
  prove="", rel=[("Observability","/operate/observability"),("Firewall","/network/firewall")]),
 dict(slug="troubleshoot-machine-offline", title="Machine shows offline", sidebar="Machine offline", keywords=["offline","agent not connecting","machine unreachable","beaverd"],
  desc="Beaver has lost contact with a machine — what offline means, and how to bring the agent back.", aud="operator", itf="dashboard, desktop, cli",
  see="The machine's status is **Offline** (Dashboard Nodes, Desktop Machines, `beaver machine list`).",
  check=["Remember what **offline** means: Beaver has lost visibility and control. **Your containers keep running** — it does not mean your app stopped.",
         "SSH to the machine and run `beaver agent status`, then `beaver agent logs`.",
         "Run `beaver doctor` on the machine."],
  causes=[("The agent is stopped","`beaver agent start` (or `beaver agent restart`)."),
          ("The machine cannot reach the internet","Check outbound rules, DNS and any proxy ([Firewall requirements](/infrastructure/firewall-requirements))."),
          ("The machine is down","Power it on or replace it. A cloud does **not** move work off a lost machine by itself — see [Drain and evacuate](/infrastructure/drain-and-evacuate)."),
          ("The machine was removed or re-enrolled elsewhere","`beaver machine list`; reconnect with `beaver connect` if needed.")],
  prove="", rel=[("Machine and agent operation","/infrastructure/machine-and-agent-operation"),("Status words","/operate/deployment-status")]),
 dict(slug="troubleshoot-connect", title="beaver connect fails", sidebar="Connect fails", keywords=["connect failed","docker not found","permission denied docker","already enrolled"],
  desc="Connecting a machine stops partway — the usual causes and fixes.", aud="operator, developer", itf="cli",
  see="`beaver connect` reports something missing, or stops before the machine appears in Beaver.",
  check=["Run `beaver doctor` — it checks the system, network, Docker, Git, authentication and agent, and changes nothing.",
         "Re-run `beaver connect`. It saves its progress and resumes."],
  causes=[("Docker is not installed or not running","Install Docker Engine and start it; `docker --version` should work."),
          ("Permission errors using Docker","Add your user to the `docker` group (`sudo usermod -aG docker $USER`) and start a new shell."),
          ("No internet","The machine needs outbound access to reach Beaver."),
          ("Already enrolled under a different account","Remove it from that account first, or use a different machine.")],
  prove="", rel=[("Connect a machine","/infrastructure/connect-a-machine"),("Beaver doctor","/install/doctor")]),
 dict(slug="troubleshoot-service-connection", title="My app cannot connect to a service", sidebar="Service connection fails", keywords=["database connection refused","cannot connect to postgres","service unreachable","redis connection"],
  desc="Your application or your laptop cannot reach a managed service.", aud="developer", itf="cli",
  see="Connection refused, timeouts or authentication errors talking to a managed database or broker.",
  check=["`beaver service show <name>` — is it healthy, and is your app listed as attached?",
         "`beaver service attached <app-container>` — confirms the attachment.",
         "Did you **redeploy** after attaching? The connection variables reach the app on the next deployment."],
  causes=[("The service is unhealthy or stopped","`beaver service retry <name>` or `beaver service start <name>`."),
          ("The app has not been redeployed since attaching","Redeploy so the injected variables take effect."),
          ("The app reads the wrong variable names","Variables are `<PREFIX>_URL`, `_HOST`, `_PORT`, `_NAME`, `_USER`, `_PASSWORD`; the prefix is the type's default (for example `DATABASE`, `REDIS`) unless you set `--env-prefix`."),
          ("From your laptop: no tunnel","Services are never on a public port. Open one: `beaver service connect <name> --local-port <port>` ([Connect locally](/data/connect-locally)). An explicit port that is already in use fails."),
          ("A credential was rotated","After `beaver service database rotate`, every place using the old value must reconnect with the new one.")],
  prove="", rel=[("Credentials and connection strings","/data/credentials-and-connection-strings"),("Create a service","/data/create-a-service")]),
 dict(slug="troubleshoot-env-var", title="An environment variable is missing", sidebar="Env var missing", keywords=["env var not set","undefined environment variable","missing config","process.env"],
  desc="Your app does not see a variable you set — per-environment values, redeploys and promotion.", aud="developer", itf="dashboard, cli",
  see="`process.env.X` (or your language's equivalent) is empty in a deployment.",
  check=["`beaver environment vars list <container>` — names set on the container.",
         "`beaver environment vars diff <container>` — compare your local `.env` with what is deployed (names only unless `--reveal`).",
         "Which **environment** is this deployment in? `beaver environment list`."],
  causes=[("You set it after the deploy","`vars push` does not redeploy. Run `beaver deploy` or `beaver container <name> redeploy`."),
          ("It was set for a different environment","Each environment has its **own** variables; [promoting](/deploy/promote) does not carry them over."),
          ("Your `.env` was never pushed","Beaver never reads a local `.env` implicitly. Use `beaver environment vars push` or `beaver deploy --env-file`."),
          ("A quoted value was mangled","Don't pass a pulled `.env` to `docker run --env-file` — quoting rules differ.")],
  prove="", rel=[("Environment variables","/deploy/environment-variables"),("Environments","/deploy/environments")]),
 dict(slug="troubleshoot-repository-access", title="Beaver cannot see or fetch my repository", sidebar="Repository access", keywords=["repository not listed","github app","cannot clone","beaver cannot see your repositories"],
  desc="The repository is missing from the list, or the Builder cannot fetch it.", aud="developer", itf="dashboard, cli",
  see="The Dashboard says *Beaver cannot see your repositories yet*, a repository is missing, or a deploy cannot fetch the commit.",
  check=["`beaver github` — your sign-in methods and each connected GitHub account's health (connected, suspended, disconnected).",
         "Was the repository included when you installed the Beaver GitHub App?"],
  causes=[("Signing in with GitHub is not repository access","They are separate. Grant access with `beaver github install` or **Integrations** in the Dashboard ([why](/teams/signing-in-and-repository-access))."),
          ("The repository was not selected, or the connection is suspended","Re-run `beaver github install` and include it."),
          ("Beaver sees it, but the Builder cannot clone it","The Builder uses the GitHub login on **its own machine**. For a private repository run `gh auth login` there and check `beaver git --auth`."),
          ("The commit is not pushed","The Builder builds what is on GitHub. Push first.")],
  prove="Every message you can see when signing in with GitHub or connecting repositories has its own entry: [Troubleshooting GitHub](/operate/troubleshooting-github). Google sign-in: [Troubleshooting Google](/operate/troubleshooting-google).",
  rel=[("Deploy from GitHub","/deploy/from-github"),("Troubleshooting GitHub","/operate/troubleshooting-github")]),
 dict(slug="troubleshoot-production-approval", title="A production action is refused or needs approval", sidebar="Production approval", keywords=["PRODUCTION_RESTRICTED","protected environment","approval required","cannot deploy to production"],
  desc="You are told you cannot do this in a protected environment — ask, wait, and repeat within the hour.", aud="developer, team-lead", itf="dashboard, desktop, cli",
  see="`you do not have permission to do this in a protected environment` (`PRODUCTION_RESTRICTED`).",
  check=["You are a **Developer** and the environment is **protected** (production by default). Ask an Owner or Admin.",
         "`beaver workspace approvals` — see whether a request is already open."],
  causes=[("No request yet","The message says how to ask. The request waits up to **24 hours**."),
          ("The approval was already used, expired or was for another action","An approval is one-time, valid for **one hour**, for that exact action: `the approval is not valid for this request (already used, expired, or for a different operation)`."),
          ("You are the approver","`you cannot decide your own request` — ask another Owner or Admin. If nobody else can approve, `nobody else in this workspace can approve this request`.")],
  prove="Full list of messages and fixes: [Troubleshooting Teams](/operate/troubleshooting-teams#production-and-approvals).", rel=[("Production approvals","/teams/production-approvals"),("Troubleshooting Teams","/operate/troubleshooting-teams")]),
 dict(slug="troubleshoot-plan-limit", title="A plan limit blocks an action", sidebar="Plan limit", keywords=["plan limit","your plan allows up to","upgrade your plan","seat limit"],
  desc="Beaver refuses because your plan's limit is reached — which limits exist and how to resolve them.", aud="team-lead, developer", itf="dashboard, cli",
  see="`Your plan allows up to N connected machines.` · `…managed services.` · `…repositories.` · `Your plan does not include X services.` · `Your plan allows up to 5 team members.` (`PLAN_LIMIT_REACHED`)",
  check=["`beaver workspace show` — the active workspace, its plan and its limits.",
         "`beaver service catalog` marks the service types your plan includes."],
  causes=[("You have reached a count limit","Remove something you no longer need, or move to a plan with a higher limit. Compare plans in [Plans and billing](/teams/plans-and-billing)."),
          ("The type is not in your plan","Choose another type, or upgrade."),
          ("You are not the Owner","Only the Owner can change the plan: `billing is managed by the workspace Owner`. Ask them, or `beaver billing request-upgrade --plan team` (nothing is charged by a request).")],
  prove="", rel=[("Plans and billing","/teams/plans-and-billing"),("Downgrades and retention","/teams/downgrades-and-retention")]),
 dict(slug="troubleshoot-mfa", title="I am locked out of 2-step verification", sidebar="2-step lockout", keywords=["lost authenticator","recovery code","2fa locked out","mfa recovery"],
  desc="You lost your authenticator and passkeys — the recovery routes and their delays.", aud="team-lead, security", itf="dashboard, cli",
  see="You cannot complete 2-step verification at sign-in.",
  check=["Do you have a **recovery code**? You were shown ten when you turned it on; each works once in place of an authenticator code.",
         "A passkey-required workspace refuses a recovery code with `MFA_PASSKEY_REQUIRED` until you sign in again with your passkey."],
  causes=[("No codes, no authenticator: email recovery","Ask for it on the sign-in page. Confirm the emailed link within **one hour**. Removal then happens after a **72-hour wait**, and every email says how to cancel."),
          ("Support reset","Support can reset it after verification questions. It needs a written reason, a second support person's approval and a 24-hour delay (skipped if you prove you control the mailbox); you can cancel during the delay.")],
  prove="Both routes end with 2-step verification removed and every session signed out, so you set it up fresh. Details: [2-step verification](/teams/two-step-verification#if-you-lose-both).",
  rel=[("2-step verification","/teams/two-step-verification")]),
 dict(slug="troubleshoot-notification", title="A notification did not arrive", sidebar="Notification not received", keywords=["no email","notification missing","digest","on-call"],
  desc="You expected a notification and did not get one — digests, severity and on-call explain most cases.", aud="team-lead, operator", itf="dashboard, cli",
  see="An alert you expected did not reach you.",
  check=["`beaver notifications --unread` — it may be in your inbox even if no message reached you.",
         "`beaver workspace digest` — is a digest holding non-urgent items?",
         "`beaver workspace on-call` — who an alert would actually reach right now."],
  causes=[("It is waiting in a digest","Non-urgent notifications are bundled; **critical and security notifications are never held for a digest**."),
          ("The wrong person is on call","`beaver workspace on-call` shows the same resolution the system uses to page people."),
          ("Severity is lower than you assumed","Filter by severity: `beaver notifications --severity=warning`.")],
  prove="", rel=[("Notifications","/operate/notifications")]),
]

def render(s):
    sidebar = s["sidebar"]
    kws = ", ".join(f'"{k}"' for k in s["keywords"])
    out = f'''---
title: "{s["title"]}"
sidebarTitle: "{sidebar}"
description: "{s["desc"]}"
icon: "triangle-alert"
type: troubleshooting
audience: [{s["aud"]}]
interfaces: [{s["itf"]}]
keywords: [{kws}]
verified: source-reviewed
lastVerified: 2026-10-01
---

import {{ Verified }} from "/snippets/verified.mdx";

<Verified kind="source-reviewed" date="2026-10-01" />

## What you see

{s["see"]}

## Check first

'''
    for i, c in enumerate(s["check"], 1): out += f"{i}. {c}\n"
    out += "\n## Causes and fixes\n\n"
    for t, b in s["causes"]: out += f"### {t}\n\n{b}\n\n"
    if s["prove"]: out += f"## Then\n\n{s['prove']}\n\n"
    out += "## Still stuck\n\nRun `beaver doctor` on the affected machine and collect its output, then contact support at support@vectorihub.com.\n\n## Related\n\n<CardGroup cols={2}>\n"
    for t, h in s["rel"]: out += f'  <Card title="{t}" icon="arrow-right" href="{h}">The page that prevents or explains this.</Card>\n'
    out += "</CardGroup>\n"
    return out

for s in S:
    open(os.path.join(ROOT, "operate", s["slug"] + ".mdx"), "w").write(render(s))
print(len(S), "symptom pages written")
