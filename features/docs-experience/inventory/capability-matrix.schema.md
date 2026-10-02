# capability-matrix.json — schema (Era 2 V9; the full file is built in Era 15 V81)

```json
{
  "tasks": [
    {
      "id": "connect-machine",
      "group": "Infrastructure",
      "task": "Connect a machine",
      "interfaces": {
        "dashboard": { "status": "full|partial|none|planned", "how": "Nodes > Add node", "page": "/infrastructure/connect-a-machine" },
        "desktop":   { "status": "...", "how": "Infrastructure home > Add machine (shows the command)", "page": "..." },
        "cli":       { "status": "full", "how": "`beaver connect`", "page": "/cli/connect" }
      },
      "verified": "verified|source-reviewed", "checked": "YYYY-MM-DD"
    }
  ]
}
```

Rules: status `none` requires a `how` that names the alternative ("Use the CLI: …"); `planned` is never rendered
as available (Invariant 8); every `page` must resolve in docs.json; each page that declares `interfaces:` in
frontmatter must have a matrix row for its task (parity test, Era 15).
