# Saphire V4

Discord.py prefix bot and public FastAPI stock endpoint. Everything configured through environment variables, see .env.example.

## Commands
- `;help`: dynamically lists commands
- `;stock`: view stock in a black embed
- `;stock panel`: create auto-editing stock panel (Manage Server permission required)

Discord renders buttons below embeds; buttons cannot physically be inserted inside embed content.

## Install
1. Apply `sql/001_member_stock.sql` in Supabase.
2. Set `DATABASE_URL` to Supabase Postgres connection string and `DISCORD_TOKEN` to bot token in Railway secret variables; never commit .env.
3. Enable Message Content Intent in Discord Developer Portal and invite bot with Send Messages, Embed Links and Read Message History.
4. Run `pip install -r requirements.txt`.
5. Start with `uvicorn saphire.main:app --host 0.0.0.0 --port 8000`.
6. On Railway, start using `uvicorn saphire.main:app --host 0.0.0.0 --port $PORT`.

Railway runs the persistent bot, stock worker, and public API. To expose under Vercel, configure a rewrite from `/v4/api/:path*` to the Railway public hostname.

## Public API
GET `/v4/api/members/stock`: public, no authentication required. Returns online_members, offline_members, success, last_updated, next_refresh. Returns 503 until first successful sync.

## Stock worker
Every 300 seconds by default, fetches `https://176.100.37.219/api/v2/stock` over verified HTTPS, validates nonnegative integer values, and upserts a singleton record. Keeps last successful values if upstream fails. Only run one worker instance to avoid duplicate polling.

## Logging
Timestamped light blue INFO, light red ERROR and orange LOGGED levels, with ASCII banner and console clearing when bot becomes ready. On restart, persistent buttons remain active; previously posted auto-edit panels must be recreated for countdown updates.
