# Self-hosting

`designlib-mcp` is a stateless [FastMCP](https://github.com/jlowin/fastmcp) server backed by a single **Postgres 16+** database. It speaks both stdio (default) and streamable-HTTP. The runtime has exactly one external dependency — the database — configured through `DATABASE_URL`.

→ Consumer quickstart and tool index live in the [README](../README.md). This document is for **operators** running their own instance.

---

## Configuration

| Env var | Required | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | `postgresql://user:pass@host:5432/dbname`. The only secret. |
| `DESIGNLIB_TRANSPORT` | — | `stdio` | Set to `http` for streamable-HTTP (what hosted clients use). |
| `PORT` | — | `8000` | HTTP bind port. The server binds `0.0.0.0:$PORT`. |

The server also accepts `--http`, `--host`, and `--port` flags, which override the environment.

```bash
designlib-mcp                       # stdio (local MCP clients)
designlib-mcp --http --port 8000    # HTTP, serves /mcp
```

---

## 1. Provision the database

Any plain Postgres 16+ works (managed, Docker, or a Coolify one-click PostgreSQL). You need a connection string for a role that can create tables and read all data.

## 2. Create the schema

`migrations/selfhosted_schema.sql` is the full schema (21 tables + 3 views) — it is the union of `migrations/001..008` with the Supabase row-level-security policies stripped, since a plain Postgres has no `anon` / `authenticated` roles.

```bash
psql "$DATABASE_URL" -f migrations/selfhosted_schema.sql
```

> The numbered `migrations/00N_*.sql` files are the historical Supabase migrations and still contain RLS. For a self-hosted instance use `selfhosted_schema.sql` instead.

## 3. Load catalog data

The catalog data is not stored in git. Two ways to populate it:

- **From an existing Supabase project** (e.g. when migrating): `scripts/export_via_rest.py` pulls every table over the PostgREST API using `SUPABASE_SERVICE_ROLE_KEY` (no database password needed) and writes a self-contained `designlib_data.sql`:

  ```bash
  # reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from .env
  python scripts/export_via_rest.py          # -> designlib_data.sql
  psql "$DATABASE_URL" -f designlib_data.sql
  ```

- **From source inputs:** re-run the `scripts/ingest_*.py` ingest scripts against your database.

Verify the load:

```bash
psql "$DATABASE_URL" -c "SELECT count(*) FROM design_styles;"   # expect 67
```

## 4. Run

```bash
pip install -e .
DATABASE_URL="..." DESIGNLIB_TRANSPORT=http PORT=8000 designlib-mcp
```

Or build the shipped image:

```bash
docker build -t designlib-mcp .
docker run -p 8000:8000 -e DATABASE_URL="..." designlib-mcp
```

The MCP endpoint is then `http://<host>:8000/mcp`.

---

## Deploying on Coolify + Hetzner

The hosted `designlib.app-builders.club` instance runs this way.

1. **Server:** a Hetzner Cloud VM (≥ 4 GB RAM) with [Coolify](https://coolify.io) installed (`curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash`).
2. **Database:** add a **PostgreSQL** resource in Coolify. Note its **internal** connection URL (`postgresql://postgres:<pwd>@<service>:5432/postgres`) — the app and DB share Coolify's Docker network, so the app reaches the DB by its internal hostname.
3. **App:** add a resource from this Git repo, **Build pack: Dockerfile**. Set env:
   - `DATABASE_URL` = the internal Postgres URL from step 2
   - `DESIGNLIB_TRANSPORT=http`, `PORT=8000`
   - **Ports exposes:** `8000`
4. **Schema + data:** run steps 2–3 above against the database once (via the DB container's terminal or `docker exec ... psql`).
5. **Domain:** point a DNS `A` record (e.g. `mcp.example.com`) at the server IP and set it as the app's domain — Coolify issues a Let's Encrypt certificate automatically.
6. **Deploy.** Smoke-test with an MCP client (e.g. `list_animation_facets` should return 120 animations across 8 categories).

---

## Notes

- **Read-only at runtime.** The server only issues `SELECT`s; it never writes. A read-only DB role is sufficient in production.
- **Connection pooling** is handled in-process via `psycopg_pool` — no external pooler (PgBouncer) required for typical MCP traffic.
- **No other secrets.** There is no API key, OAuth, or telemetry endpoint to configure.
