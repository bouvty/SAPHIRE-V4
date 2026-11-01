# Self-hosted Saphire V4 Discord bot

The standalone bot is packaged separately for self hosting. It reads the public stock API at `https://api.saphire.rip/v4/stock/members` and does not access Supabase directly.

Run `python main.py` after `pip install -r requirements.txt` and setting `DISCORD_TOKEN` in `.env`. Enable Message Content Intent. Commands: `;help`, `;stock`, `;stock panel`.

On Railway set `ENABLE_DISCORD_BOT=false`, `ENABLE_STOCK_SYNC=true`, and a `DATABASE_URL` for the API/worker. Railway does not run this bot.
