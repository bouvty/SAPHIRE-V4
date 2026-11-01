# Saphire V4

**Bot is self-hosted. Railway runs only the API and 5-minute stock synchronization.**

New Supabase project: **SAPHIRE**, reference `igtoqirlldsdijyumucw`. The database table is `public.stock_members` (online_members, offline_members, updated_at).

## API routes

- `GET https://api.saphire.rip/v4/` — service metadata.
- `GET https://api.saphire.rip/v4/health` — API health.
- `GET https://api.saphire.rip/v4/stock/members` — reads the most recent stock from Supabase; no API key.

## Railway

Set these environment variables on the V4 service:

```env
DATABASE_URL=<new SAPHIRE Supabase Postgres connection string>
ENABLE_DISCORD_BOT=false
ENABLE_STOCK_SYNC=true
STOCK_REFRESH_SECONDS=300
STOCK_SOURCE_URL=https://176.100.37.219/api/v2/stock
```

**Important:** A new Supabase project means the old project's DB URL no longer applies. Never commit the password or connection string to GitHub.

Run `sql/001_member_stock.sql` only if the table does not already exist; it has been created in the new project.

Railway fetches provider stock every 5 minutes, validates both counts, and upserts row id 1 in `stock_members`. The public API only reads the table. On invalid/unreachable source data, existing counts are retained.

## Self-hosted Discord bot

Run `python main.py` inside the provided bot ZIP, using its own `.env` containing `DISCORD_TOKEN` and `API_BASE_URL=https://api.saphire.rip/v4`. Enable Message Content Intent. Commands: `;help`, `;stock`, `;stock panel`.

The self-hosted bot requires no Supabase credentials. Never put a Discord bot token in Railway.
