---
title: "{Outcome-phrased title, e.g. Deploy from GitHub}"
sidebarTitle: "{≤ 28 chars}"
description: "{One sentence stating the result the reader gets.}"
icon: "{icon from components.txt}"
type: howto
audience: [developer]
interfaces: [dashboard, desktop, cli]
verified: source-reviewed
lastVerified: 2026-10-01
---

{/*
Era 2 V7 template — Docs Experience. One page, one task, one outcome.
Required order: Before you begin → Steps (one Tab per applicable interface, fixed order Dashboard · Desktop · CLI)
→ Verify → If it fails → Next steps. A tab an interface cannot serve becomes a Note ("Not available in ...").
MDX: never write bare angle-bracket placeholders outside code fences.
*/}

import { Verified } from "/snippets/verified.mdx";

<Verified kind="source-reviewed" date="2026-10-01" />

{One-paragraph lead: what you will do and why a reader would.}

## Before you begin

- {Prerequisite with a link}

## Steps

<Tabs>
  <Tab title="Dashboard">
    {Numbered steps using the exact UI labels.}
  </Tab>
  <Tab title="Desktop">
    {Numbered steps, or a Note: not available here — use the Dashboard or CLI.}
  </Tab>
  <Tab title="CLI">
    ```bash
    beaver {command} {args}
    ```
  </Tab>
</Tabs>

## Verify it worked

{The observable result: a status, a URL that answers, a line of output.}

## If it fails

{Two or three likeliest failures, each linking its troubleshooting page.}

## Next steps

<CardGroup cols={2}>
  <Card title="{Next task}" icon="arrow-right" href="/{next}">{one line}</Card>
  <Card title="{Concept}" icon="book-open" href="/{concept}">{why it works this way}</Card>
</CardGroup>
