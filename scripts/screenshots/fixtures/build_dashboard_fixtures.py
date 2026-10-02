#!/usr/bin/env python3
"""features/docs-experience V94 — the seeded demo workspace the Dashboard screenshots are taken from.

Everything here is fictional (Invariant 12): the user is Ada Lovelace <ada@beaver.local>, the workspace "Paperclip", hostnames are
*.paperclip.example, addresses are RFC 5737 documentation ranges. The Dashboard has no demo mode, so capture.mjs answers its API calls from
the file this script writes (fixtures/dashboard.json) — shapes follow vhb-client's types (app/dashboard/types.ts, app/workspace/team/types.ts,
app/billing/types.ts). Run:  python3 fixtures/build_dashboard_fixtures.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
NOW = "2026-10-01T09:00:00Z"
def ago(minutes):
    import datetime
    t = datetime.datetime(2026, 10, 1, 9, 0, 0) - datetime.timedelta(minutes=minutes)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")
F = {}
PLAN = {"slug": "team", "label": "Team"}
USER = {"user_id": "usr_ada", "user_name": "ada", "full_name": "Ada Lovelace", "email": "ada@beaver.local", "is_email_verified": True, "mfa_enabled": True,
        "profile_image": "", "created_at": "2026-03-04T10:00:00Z", "UserID": "usr_ada", "FollowersCount": 12}
F["GET /api/me/profile"] = {"user": USER, "status_code": 200}
WS = {"workspace_id": "ws_paperclip", "name": "Paperclip", "kind": "team", "role": "owner", "status": "active", "plan": PLAN, "member_count": 4}
F["GET /api/workspaces"] = {"workspaces": [WS, {"workspace_id": "ws_ada", "name": "Ada Lovelace", "kind": "personal", "role": "owner", "status": "active", "plan": {"slug": "hobby", "label": "Hobby"}, "member_count": 1}]}
PERMS = ["alie.configure", "alie.use", "approval.decide", "audit.read", "billing.manage", "cloud.manage", "container.exec", "container.operate", "deploy.production", "domain.manage", "firewall.manage", "machine.enroll", "machine.manage", "member.invite", "member.manage", "ownership.transfer", "project.create", "project.delete", "project.deploy", "project.redeploy", "project.rollback", "role.change", "secret.read", "secret.write", "service.create", "service.manage", "workspace.delete", "workspace.manage", "workspace.read"]  # the Owner holds all (vhb-server tenant/permissions.go)
F["GET /api/workspace/me"] = {"workspace_id": "ws_paperclip", "name": "Paperclip", "kind": "team", "role": "owner", "permissions": PERMS, "requires": {}, "settings": {"developer_production": False, "developer_machines": True, "developer_secrets": False, "allow_link_invites": True, "protected_environments": ["production"], "require_approval_for": []}, "plan": PLAN}
F["GET /api/workspace/subscription"] = {"plan_id": "team", "has_subscription": True, "status": "active", "billing_cycle": "monthly", "current_period_end": "2026-10-28T00:00:00Z", "cancel_at_period_end": False,
    "seats": {"used": 4, "active": 3, "pending": 1, "suspended": 0, "included": 5, "pack": 5, "limit": 5}, "seat_packs": [], "next_charge": None, "notice": None, "billing_owner": {"name": "Ada Lovelace", "email": "ada@beaver.local"}}
F["GET /api/integrations/status"] = {"github": {"provider": "github", "connected": True, "state": "connected", "accounts": 1, "attention": 0, "checked_at": NOW}}
CONTAINERS = [
  {"container_id": "ctr_api", "name": "paperclip-api", "status": "running", "framework": "Go", "image": "paperclip/api:v185", "git_branch": "main", "domain": "api.paperclip.example", "kind": "standalone", "project_id": "prj_paperclip", "created_at": ago(60 * 24 * 12)},
  {"container_id": "ctr_web", "name": "paperclip-web", "status": "running", "framework": "Next.js", "image": "paperclip/web:v42", "git_branch": "main", "domain": "paperclip.example", "kind": "standalone", "project_id": "prj_paperclip", "created_at": ago(60 * 24 * 20)},
  {"container_id": "ctr_worker", "name": "paperclip-worker", "status": "running", "framework": "Node.js", "image": "paperclip/worker:v12", "git_branch": "main", "kind": "standalone", "project_id": "prj_paperclip", "created_at": ago(60 * 24 * 9)},
  {"container_id": "ctr_docs", "name": "paperclip-docs", "status": "exited", "framework": "Astro", "image": "paperclip/docs:v7", "git_branch": "docs", "kind": "standalone", "project_id": "prj_docs", "created_at": ago(60 * 24 * 40)},
]
F["GET /api/containers"] = {"containers": CONTAINERS}
DEPLOYMENTS = [
  {"deployment_id": "dep_3", "project_id": "prj_paperclip", "container_id": "ctr_api", "status": "success", "image": "paperclip/api:v185", "git_branch": "main", "commit_hash": "1a2b3c4", "commit_msg": "Add refund endpoint", "current": True, "created_at": ago(42), "duration_ms": 98000},
  {"deployment_id": "dep_2", "project_id": "prj_paperclip", "container_id": "ctr_web", "status": "success", "image": "paperclip/web:v42", "git_branch": "main", "commit_hash": "9f8e7d6", "commit_msg": "Update pricing page", "current": True, "created_at": ago(60 * 5), "duration_ms": 141000},
  {"deployment_id": "dep_1", "project_id": "prj_paperclip", "container_id": "ctr_worker", "status": "failed", "image": "paperclip/worker:v13", "git_branch": "main", "commit_hash": "5c4d3e2", "commit_msg": "Retry queue changes", "current": False, "created_at": ago(60 * 26), "duration_ms": 63000},
]
F["GET /api/deployments"] = {"data": DEPLOYMENTS}
F["GET /api/dashboard/summary"] = {"generated_at": NOW, "workspace": {"id": "ws_paperclip", "name": "Paperclip", "kind": "team", "plan": PLAN}, "projects_count": 2, "requests_today": 18420,
  "fleet": {"healthy": 2, "degraded": 1, "offline": 0, "unknown": 0, "firing_alerts": 1},
  "incidents": [{"id": "inc_1", "title": "Disk pressure on build-01", "status": "open", "severity": "warning", "started_at": ago(75), "resolved_at": None}],
  "edge_apps": [{"id": "edge_1", "domain_name": "app.paperclip.example", "status": "active", "ssl_status": "active"}],
  "services": {"items": [{"id": "svc_db", "name": "paperclip-db", "type": "postgres", "status": "healthy"}, {"id": "svc_cache", "name": "paperclip-cache", "type": "redis", "status": "healthy"}], "summary": {"Total": 2, "Unhealthy": 0, "ByType": {"postgres": 1, "redis": 1}}},
  "approvals": [{"id": "apr_1", "source": "cli", "kind": "deploy", "status": "pending", "requested_by_name": "Grace Hopper", "summary": "Deploy paperclip-api to production", "environment": "production", "action": "deploy", "params": {}, "expires_at": "2026-10-02T09:00:00Z"}],
  "notifications": {"unread": 3, "requires_action": 1},
  "activity": [
    {"id": "act_1", "source": "audit", "at": ago(42), "action": "deployment.created", "label": "Ada Lovelace deployed paperclip-api", "actor_name": "Ada Lovelace", "actor_role": "owner", "target_name": "paperclip-api", "outcome": "success"},
    {"id": "act_2", "source": "audit", "at": ago(180), "action": "member.invited", "label": "Ada Lovelace invited grace@beaver.local", "actor_name": "Ada Lovelace", "actor_role": "owner", "target_name": "grace@beaver.local", "outcome": "success"},
    {"id": "act_3", "source": "audit", "at": ago(60 * 5), "action": "deployment.created", "label": "Grace Hopper deployed paperclip-web", "actor_name": "Grace Hopper", "actor_role": "developer", "target_name": "paperclip-web", "outcome": "success"}],
  "usage": {"machines": {"used": 3, "limit": -1, "over_limit": False}, "repositories": {"used": 4, "limit": -1, "over_limit": False}, "managed_services": {"used": 2, "limit": 25, "over_limit": False}, "members": {"used": 4, "limit": 5, "over_limit": False}},
  "billing_plan": {"slug": "team", "label": "Team", "subscription_status": "active", "current_period_end": "2026-10-28T00:00:00Z", "source": "subscription"}}

# ---- Nodes -------------------------------------------------------------------------------------------------------------------------------
MACHINES = [
  {"machine_id": "m_prod01", "name": "prod-01", "hostname": "prod-01.paperclip.example", "role": "host", "availability": "healthy", "health_score": 90, "health_band": "healthy"},
  {"machine_id": "m_prod02", "name": "prod-02", "hostname": "prod-02.paperclip.example", "role": "host", "availability": "healthy", "health_score": 94, "health_band": "healthy"},
  {"machine_id": "m_build01", "name": "build-01", "hostname": "build-01.paperclip.example", "role": "builder", "availability": "degraded", "health_score": 62, "health_band": "degraded"},
]
F["GET /api/machines"] = {"data": MACHINES}
F["GET /api/machines/fleet/overview"] = {"data": {"counts": {"healthy": 2, "degraded": 1, "offline": 0, "unknown": 0}, "machines": [{"machine_id": "m_prod01", "group_id": "g_prod"}, {"machine_id": "m_prod02", "group_id": "g_prod"}, {"machine_id": "m_build01", "group_id": "g_build"}]}}
F["GET /api/machines/groups"] = {"data": [{"id": "g_prod", "name": "Production"}, {"id": "g_build", "name": "Builders"}]}
# ---- Notifications ---------------------------------------------------------------------------------------------------------------------
def note(i, typ, cat, title, msg, sev, minutes, read=False, action=False):
    return {"NotificationID": f"ntf_{i}", "WorkspaceID": "ws_paperclip", "Type": typ, "Category": cat, "Title": title, "Message": msg, "Severity": sev, "RequiresAction": action,
            "RequiresAcknowledgement": action, "Meta": None, "IsRead": read, "AcknowledgedAt": None, "ResolvedAt": None, "ExpiresAt": None, "CreatedAt": ago(minutes),
            "read_at": ago(minutes - 1) if read else None, "unacknowledged": action}
NOTES = [
  note(1, "deploy.build_failed", "deploy", "Build failed for paperclip-worker", "The build for commit 5c4d3e2 failed on build-01. Open the build log for the error.", "critical", 60 * 26, False, True),
  note(2, "approval.requested", "approval", "Approval requested", "Grace Hopper asked to deploy paperclip-api to production.", "warning", 20, False, True),
  note(3, "deploy.succeeded", "deploy", "paperclip-api is live", "Release v185 passed its health check and is serving traffic.", "success", 42, False, False),
  note(4, "domain.verified", "domain", "app.paperclip.example is live over HTTPS", "DNS was verified and the certificate was issued.", "success", 60 * 30, True, False),
  note(5, "team.member_joined", "team", "Grace Hopper joined Paperclip", "Grace joined as a Developer.", "info", 60 * 50, True, False),
]
F["GET /api/notifications"] = {"data": NOTES, "limit": 25, "total": 5}
F["GET /api/notifications/unread-count"] = {"unread_count": 3}
# ---- Billing ---------------------------------------------------------------------------------------------------------------------------
F["GET /api/billing/status"] = {"machines": {"used": 3, "limit": -1, "over_limit": False}, "repositories": {"used": 4, "limit": -1, "over_limit": False}, "managed_services": {"used": 2, "limit": 25, "over_limit": False}, "members": {"used": 4, "limit": 5, "over_limit": False},
  "plan": {"slug": "team", "label": "Team", "billing_cycle": "monthly", "subscription_status": "active", "current_period_end": "2026-10-28T00:00:00Z", "included_seats": 5, "seats": {"included": 5, "extra": 0, "limit": 5, "used": 4, "active": 3, "pending": 1, "suspended": 0}}}
def plan(i, slug, name, price, desc, popular=False):
    return {"plan_id": f"plan_{slug}", "name": name, "slug": slug, "type": "subscription", "description": desc, "cta": "Choose plan", "is_popular": popular, "sort_order": i, "monthly_price": price, "yearly_price": None if price is None else price * 10, "price_label": None,
            "extra_seat_monthly_price": 10 if slug == "team" else None, "extra_seat_yearly_price": 8 if slug == "team" else None, "limits": [{"label": "Machines", "included": True}, {"label": "Managed services", "included": True}]}
F["GET /platform/plans"] = {"plans": [plan(1, "hobby", "Free", 0, "For trying Beaver"), plan(2, "developer", "Developer", 15, "For one builder"), plan(3, "team", "Team", 59, "For a team", True)]}
F["GET /api/workspace/payments"] = {"payments": [
  {"payment_id": "pay_3", "reference": "PCL-2026-0914", "amount": 59, "gateway": "paypal", "status": "success", "created_at": "2026-09-28T09:00:00Z"},
  {"payment_id": "pay_2", "reference": "PCL-2026-0828", "amount": 59, "gateway": "paypal", "status": "success", "created_at": "2026-08-28T09:00:00Z"},
  {"payment_id": "pay_1", "reference": "PCL-2026-0728", "amount": 59, "gateway": "paypal", "status": "success", "created_at": "2026-07-28T09:00:00Z"}]}
# ---- Team ------------------------------------------------------------------------------------------------------------------------------
F["GET /api/workspace/members"] = {"members": [
  {"member_id": "mem_1", "user_id": "usr_ada", "name": "Ada Lovelace", "email": "ada@beaver.local", "role": "owner", "status": "active", "joined_at": "2026-03-04T10:00:00Z", "is_self": True},
  {"member_id": "mem_2", "user_id": "usr_grace", "name": "Grace Hopper", "email": "grace@beaver.local", "role": "developer", "status": "active", "joined_at": "2026-04-12T10:00:00Z", "is_self": False},
  {"member_id": "mem_3", "user_id": "usr_alan", "name": "Alan Turing", "email": "alan@beaver.local", "role": "admin", "status": "active", "joined_at": "2026-05-20T10:00:00Z", "is_self": False}]}
F["GET /api/workspace/seats"] = {"used": 4, "active": 3, "pending": 1, "suspended": 0, "included": 5, "pack": 5, "limit": 5}
F["GET /api/workspace/invites"] = {"invites": [{"invite_id": "inv_1", "email": "katherine@beaver.local", "role": "developer", "status": "pending", "expires_at": "2026-10-08T09:00:00Z", "invited_by_name": "Ada Lovelace", "link_mode": False}]}
F["GET /api/workspace/approvals"] = {"approvals": F["GET /api/dashboard/summary"]["approvals"]}
F["GET /api/workspace/transfer"] = {"transfer": None}
F["GET /api/workspace/feed"] = {"items": F["GET /api/dashboard/summary"]["activity"], "next_cursor": ""}
# ---- Settings --------------------------------------------------------------------------------------------------------------------------
F["GET /api/account/identities"] = {"identities": [{"provider": "github", "provider_username": "ada", "connected": True, "created_at": "2026-03-04T10:00:00Z", "last_used_at": ago(60)}, {"provider": "google", "connected": False}], "account_email": "ada@beaver.local"}
F["GET /api/account/devices"] = {"devices": [
  {"id": "dev_1", "device_name": "ada-laptop", "client_kind": "desktop", "created_at": "2026-09-20T10:00:00Z", "last_seen_at": ago(5), "expires_at": "2026-12-20T10:00:00Z", "revoked_at": None, "current": True, "approved_mfa_kind": "totp"},
  {"id": "dev_2", "device_name": "build-01", "client_kind": "cli", "created_at": "2026-09-02T10:00:00Z", "last_seen_at": ago(60 * 3), "expires_at": "2026-12-02T10:00:00Z", "revoked_at": None, "current": False, "approved_mfa_kind": "totp"},
  {"id": "dev_3", "device_name": "old-laptop", "client_kind": "cli", "created_at": "2026-06-02T10:00:00Z", "last_seen_at": ago(60 * 24 * 30), "expires_at": "2026-09-02T10:00:00Z", "revoked_at": "2026-09-05T10:00:00Z", "current": False, "revoked_reason": "user"}]}
F["GET /api/account/me"] = {"mfa": {"enabled": True, "methods": ["totp"], "recovery_codes_remaining": 8, "recovery_login": False, "recovery_pending": False, "last_verified_at": ago(30), "session_mfa_kind": "totp", "passkeys": 0, "passkeys_available": False, "enforced_by": []}}
F["GET /api/account/security-activity"] = {"items": [{"id": "sa_1", "kind": "login", "at": ago(30), "detail": "Signed in with GitHub"}]}
F["GET /api/mfa/authenticators"] = {"authenticators": []}

# ---- Projects, Edge, Services, Incidents -----------------------------------------------------------------------------------------------
F["GET /api/projects"] = {"projects": [
  {"ProjectID": "prj_paperclip", "Name": "paperclip", "Description": "The Paperclip storefront: API, web app and background worker.", "CreatedAt": "2026-03-10T10:00:00Z"},
  {"ProjectID": "prj_docs", "Name": "paperclip-docs", "Description": "Public documentation site.", "CreatedAt": "2026-05-02T10:00:00Z"}]}
F["GET /api/edge/connected-apps"] = {"connected_apps": [
  {"id": "edge_1", "domain_name": "app.paperclip.example", "origin_url": "https://origin.paperclip.example", "status": "active", "ssl_status": "issued", "record_type": "CNAME", "record_name": "app.paperclip.example", "record_value": "edge.beaver.example", "region": "", "created_at": "2026-08-01T10:00:00Z"},
  {"id": "edge_2", "domain_name": "status.paperclip.example", "origin_url": "https://status-origin.paperclip.example", "status": "verifying_dns", "ssl_status": "pending", "record_type": "CNAME", "record_name": "status.paperclip.example", "record_value": "edge.beaver.example", "region": "", "created_at": "2026-09-30T10:00:00Z"}]}
F["GET /api/services"] = {"data": F["GET /api/dashboard/summary"]["services"]["items"] + [{"id": "svc_search", "name": "paperclip-search", "type": "meilisearch", "status": "provisioning"}], "summary": {"Total": 3, "Unhealthy": 0, "ByType": {"postgres": 1, "redis": 1, "meilisearch": 1}}}
F["GET /api/incidents?status=open"] = {"data": F["GET /api/dashboard/summary"]["incidents"]}
F["GET /api/incidents?status=monitoring"] = {"data": [{"id": "inc_0", "title": "Elevated 5xx on paperclip-api", "status": "monitoring", "severity": "warning", "started_at": ago(60 * 6), "resolved_at": None}]}

json.dump(F, open(os.path.join(HERE, "dashboard.json"), "w"), indent=1)
print(len(F), "endpoints")
