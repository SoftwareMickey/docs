# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A [Mintlify](https://mintlify.com) documentation site for **VectorIHub** (product name "Beaver" appears in some blog/changelog copy). The entire repo is MDX content and a single `docs.json` config — there is no application source code, no package.json, and no test suite.

**Product positioning (current, as of the "Build Once. Deploy Anywhere." repositioning):** VectorIHub is a deployment platform, not a cloud hosting provider. Applications are built from a **required, user-provided `Dockerfile`** — VectorIHub does not auto-generate one or auto-detect frameworks — and deployed consistently across infrastructure providers the customer owns (VPS, AWS, Azure, DigitalOcean). Older content describing "auto-dockerization," zero-config framework detection, or VectorIHub-owned hosting infrastructure is the *previous* product model and should not be reintroduced into current (non-historical) pages. `blog/` and `changelog/` are dated historical records from the earlier model and are intentionally left as-is rather than rewritten.

Every language and framework is still supported under the new model — Docker is language-agnostic — so `languages/`, `runtimes/`, and `frameworks/` still exist, just reframed: each page now shows a sample Dockerfile for that stack (bring-your-own-build) instead of describing auto-detection.

**Do not document how detection/build/deployment works internally** (matching logic, infrastructure-provisioning mechanics, or anything resembling an internal "deployment contract" schema) — these are trade secrets. Public docs describe *what* is supported and *how to use it*, never the internal mechanism.

## Commands

Mintlify docs are previewed with the `mint` CLI (not part of this repo; install globally):

```bash
npm i -g mint          # install the CLI
mint dev                # preview locally at http://localhost:3000
mint dev --port 3333    # run on a custom port
mint broken-links       # validate links across the docs
npm mint update         # update the CLI if the local preview doesn't match production
```

There is no build/lint/test step beyond the above — content correctness is verified by previewing pages and running `mint broken-links`.

## Architecture

**Navigation is centrally defined in `docs.json`.** Adding, removing, or moving a page requires updating the `navigation.tabs[].groups[].pages` array here — files are not auto-discovered. `docs.json` also controls theme colors, logo, navbar links, footer socials, the `global.anchors` top-nav links, and the `contextual` AI-assistant options (copy/chatgpt/claude/cursor/etc. buttons shown on each page).

**Guides nav groups, in order:** Getting started (`documentation`, `installation`, `beaver-doctor`, `cli`, `choose-your-setup`, `connect`, `machine-roles`, `quickstart`) → Infrastructure Setup (`infrastructure-setup`, `infrastructure-setup/aws`, `infrastructure-setup/google-cloud`, `infrastructure-setup/azure`, `infrastructure-setup/custom-vps-providers`, `infrastructure-setup/firewall-requirements`) → Deploying with Docker (`deploying/dockerfile-requirements`, `deploying/deployment-configuration`, `deploying/environment-variables`) → Languages (`languages/javascript`, `languages/go`) → Runtimes (`runtimes/nodejs`, `runtimes/go`) → Frameworks (18 pages under `frameworks/`, one per framework — never nest one framework's content inside another's page). `infrastructure-setup.mdx` at the repo root is the directory/overview page for the Infrastructure Setup group and is also the target of the `global.anchors` "Infrastructure" top-nav link. Adding a new framework means a new file under `frameworks/`, a nav entry, and a card on the relevant `languages/*.mdx` page; adding a new provider means the same pattern under `infrastructure-setup/` + a card on `infrastructure-setup.mdx`.


Note: there used to be a separate "Infrastructure Providers" nav group (`providers/vps`, `providers/aws`, `providers/azure`, `providers/digitalocean`, directory page `infrastructure.mdx`) describing VectorIHub-provisioned dashboard deployments. It has been removed and fully replaced by the "Infrastructure Setup" group above, which reflects the current bring-your-own-machine / `beaver connect` model — do not recreate the old `providers/` pattern.

**Every MDX page requires frontmatter** with at least `title` and `description`; most pages add `sidebarTitle` and `icon` (see any `infrastructure-setup/*.mdx` file for the pattern using Lucide/Font-Awesome-style icon names).

**Content components** are Mintlify's built-in MDX components (`<Card>`, `<CardGroup>`, `<Steps>`, `<Tabs>`, `<CodeGroup>`, `<Accordion>`, `<Note>`/`<Warning>`/`<Info>`/`<Tip>`/`<Check>`/`<Error>`, `<ParamField>`/`<ResponseField>`, `<Update>`, etc.) — the reference catalog for which component to use is in `components.txt` at the repo root. Do not invent new components; use one from this catalog.

**Reusable snippets** live in `snippets/` and are imported into pages to avoid duplicating content (DRY), per the guidance in `snippets/snippet-intro.mdx`.

**Blog** (`blog/`) and **changelog** (`changelog/`) are separate content types. Blog posts reference the repo-root `authors.yml` via `authors: <key>` in frontmatter; changelog entries use their own `changelog/authors.yml` instead, plus `changelog/tags.yml` for tag metadata and the `<Update label="..." description="...">` wrapper component.

`features.mdx` is reachable outside the Guides tab's page tree as the target of the `global.anchors` "Features" top-nav link (alongside `infrastructure-setup.mdx` for "Infrastructure"). `cli.mdx`, `beaver-doctor.mdx`, `connect.mdx`, `choose-your-setup.mdx`, and `machine-roles.mdx` together document the product's own `beaver` CLI and onboarding flow (install → `doctor` → `connect` → pick a role) — unrelated to the `mint` CLI used to preview this repo.

**Images/logos**: light/dark logo variants live in `logo/` and are wired into `docs.json`'s `logo.light`/`logo.dark`; general content images live in `images/`.
