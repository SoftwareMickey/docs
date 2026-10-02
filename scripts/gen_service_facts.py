#!/usr/bin/env python3
"""features/docs-experience V51 — regenerate the "At a glance" and "Connect from your application" blocks on every
data/services/* page from inventory/service-facts.json (extracted from vhb-server's service type registry).

  scripts/gen_service_facts.py            write the blocks (idempotent; replaces what is between the markers)
  scripts/gen_service_facts.py --check    exit 1 if a page is stale

Hand-written content on each page is never touched. Update service-facts.json when `beaver service catalog` changes.
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = json.load(open(f"{ROOT}/features/docs-experience/inventory/service-facts.json"))
B1, E1 = "{/* BEGIN GENERATED service-facts (scripts/gen_service_facts.py) */}", "{/* END GENERATED service-facts */}"
B2, E2 = "{/* BEGIN GENERATED service-connect (scripts/gen_service_facts.py) */}", "{/* END GENERATED service-connect */}"

CONNECT = {
  "postgres": ('```js Node.js\nimport pg from "pg";\nconst pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });\nconst { rows } = await pool.query("select 1 as ok");\n```\n```python Python\nimport os, psycopg\nwith psycopg.connect(os.environ["DATABASE_URL"]) as conn:\n    print(conn.execute("select 1").fetchone())\n```'),
  "mysql": ('```js Node.js\nimport mysql from "mysql2/promise";\nconst conn = await mysql.createConnection(process.env.DATABASE_URL);\nconst [rows] = await conn.query("select 1 as ok");\n```\n```python Python\nimport os, pymysql\nconn = pymysql.connect(host=os.environ["DATABASE_HOST"], port=int(os.environ["DATABASE_PORT"]),\n                       user=os.environ["DATABASE_USER"], password=os.environ["DATABASE_PASSWORD"],\n                       database=os.environ["DATABASE_NAME"])\n```'),
  "mongodb": ('```js Node.js\nimport { MongoClient } from "mongodb";\nconst client = new MongoClient(process.env.DATABASE_URL);\nawait client.connect();\nconsole.log(await client.db().command({ ping: 1 }));\n```\n```python Python\nimport os\nfrom pymongo import MongoClient\nprint(MongoClient(os.environ["DATABASE_URL"]).admin.command("ping"))\n```'),
  "redis": ('```js Node.js\nimport Redis from "ioredis";\nconst redis = new Redis(process.env.REDIS_URL);\nawait redis.set("hello", "beaver");\nconsole.log(await redis.get("hello"));\n```\n```python Python\nimport os, redis\nr = redis.Redis.from_url(os.environ["REDIS_URL"])\nr.set("hello", "beaver"); print(r.get("hello"))\n```'),
  "rabbitmq": ('```js Node.js\nimport amqp from "amqplib";\nconst conn = await amqp.connect(process.env.RABBITMQ_URL);\nconst ch = await conn.createChannel();\n```\n```python Python\nimport os, pika\nconn = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))\n```'),
  "nats": ('```js Node.js\nimport { connect } from "nats";\nconst nc = await connect({ servers: process.env.NATS_URL });\n```'),
  "meilisearch": ('```js Node.js\nimport { MeiliSearch } from "meilisearch";\nconst client = new MeiliSearch({\n  host: `http://${process.env.MEILI_HOST}:${process.env.MEILI_PORT}`,\n  apiKey: process.env.MEILI_PASSWORD,\n});\nconsole.log(await client.health());\n```'),
  "minio": ('```js Node.js\nimport * as Minio from "minio";\nconst client = new Minio.Client({\n  endPoint: process.env.MINIO_HOST,\n  port: Number(process.env.MINIO_PORT),\n  useSSL: false,\n  accessKey: process.env.MINIO_USER,\n  secretKey: process.env.MINIO_PASSWORD,\n});\n```'),
  "kafka": None,
}
FAMILY = {"postgres": "postgres", "pgvector": "postgres", "postgis": "postgres", "timescaledb": "postgres"}

def facts_block(slug, f):
    t = f["type"]; p = f["prefix"]
    flavors = ""
    if t in ("pgvector", "postgis", "timescaledb"):
        flavors = f"\n| Release flag | `--distribution-version` pins the {t} release (the PostgreSQL version is `--version`) |"
    return f"""## At a glance

| | |
| --- | --- |
| Type | `{t}` — `beaver service create <name> --type {t}` |
| Versions | {f['versions']} — confirm with `beaver service catalog` |
| Default size | {f['cpu']} CPU · {f['mem']} MB memory · {f['disk']} GB storage — change with `beaver service resize` |
| Default port | {f['port']} (on the service's private address; never published publicly) |
| Persistence | {'Optional — `--no-persistence` gives a cache-style service with no data volume' if f['persist']=='optional' else 'A data volume is always provisioned'} |
| Isolated resource per application | {f['kind']} — each attached app gets its own, with its own credential |
| Variables injected on attach | `{p}_URL`, `{p}_HOST`, `{p}_PORT`, `{p}_NAME`, `{p}_USER`, `{p}_PASSWORD` (prefix changeable with `--env-prefix`) |{flavors}
"""

def connect_block(slug, f):
    t = f["type"]; p = f["prefix"]; fam = FAMILY.get(t, t)
    code = CONNECT.get(fam)
    body = f"""## Connect from your application

[Attach the service](/start/first-service) to your application, then redeploy so the injected variables reach the container. Your app reads the connection from the environment.

""" + (f"<CodeGroup>\n{code}\n</CodeGroup>\n\n<Note>These snippets are illustrative; check your driver's documentation for options such as TLS and pooling.</Note>\n" if code else
        f"Read `{p}_URL` — for {t} it is the broker address (`host:port`) — and `beaver service reveal <name>` shows the credential. See your Kafka client's documentation for how to supply it.\n")
    backup_line = ("- **Back up:** `beaver service backup <name>` takes a manual backup; see [Backups and restore](/data/backups-and-restore) for schedules, destinations and restore." if f.get("backup") else
                   f"- **Back up:** Beaver backups are **not supported** for {t}. Protect its data another way, and see [Backups and restore](/data/backups-and-restore) for which services are covered.")
    body += f"""
## Verify, back up and troubleshoot

- **Healthy?** `beaver service show <name>` shows status, placement and attached applications. An unhealthy service: `beaver service retry <name>`.
- **From your laptop:** `beaver service connect <name> --local-port {f['port']}` opens a tunnel on `127.0.0.1` ([Connect locally](/data/connect-locally)).
{backup_line}
- **Credentials:** `beaver service reveal <name>` prints the live connection string and records an audit event; rotate one database's credential with `beaver service database rotate <db-name> <service>`.
- **Detach vs delete:** detaching an app ends only its own access. `beaver service delete` keeps the data volume; `beaver service delete-volume` destroys it permanently.
"""
    return body

def put(text, begin, end, block, anchor_regex=None, append=False):
    wrapped = f"{begin}\n\n{block}\n{end}\n"
    if begin in text:
        return re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", lambda m: wrapped, text, flags=re.S)
    if append: return text.rstrip("\n") + "\n\n" + wrapped
    m = re.search(anchor_regex, text, re.M)
    return text[:m.start()] + wrapped + "\n" + text[m.start():] if m else text + "\n" + wrapped

def main():
    check = "--check" in sys.argv; stale = 0
    for slug, f in FACTS.items():
        if slug.startswith("_"): continue
        path = f"{ROOT}/data/services/{slug}.mdx"
        old = open(path).read(); new = old
        new = put(new, B1, E1, facts_block(slug, f), anchor_regex=r"^## ")
        new = put(new, B2, E2, connect_block(slug, f), append=True)
        if new != old:
            stale += 1
            if not check: open(path, "w").write(new)
    print(("stale: " if check else "updated: ") + str(stale))
    sys.exit(1 if check and stale else 0)
main()
