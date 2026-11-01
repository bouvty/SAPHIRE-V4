import asyncio
import logging
import os
import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
import discord
from discord.ext import commands
from .settings import settings
from .stock import countdown,relative_stamp
from .logging_setup import logged

ASCII = r''' \
,e,            ,e,                     d8
 "  888-~88e    "   e88~~8e   e88~~ _d88__
888 888  888   888 d888  88b d888     888
888 888  888   888 8888__888 8888     888
888 888  888   888 Y888    , Y888     888
888 888  888   88P  "88___/   "88__/  "88_/
            \_8"
'''
EMBED_COLOR=settings.color

class StockView(discord.ui.View):
    def __init__(self,bot):
        super().__init__(timeout=None)
        self.bot=bot
    @discord.ui.button(label="Refresh stock",style=discord.ButtonStyle.secondary,emoji="🔄",custom_id="saphire:stock:refresh")
    async def refresh(self,interaction:discord.Interaction,button:discord.ui.Button):
        row=await self.bot.stock.get()
        await interaction.response.edit_message(embed=self.bot.make_stock_embed(row),view=self)

class SaphireBot(commands.Bot):
    def __init__(self,stock):
        intents=discord.Intents.default()
        intents.message_content=True
        super().__init__(command_prefix=settings.discord_prefix,intents=intents,help_command=None,
            activity=discord.Streaming(name=settings.discord_stream_name,url=settings.discord_stream_url))
        self.stock=stock
        self.panel_file = Path(os.getenv('STOCK_PANELS_FILE', 'stock_panels.json'))
        self.panels = self.load_panels()
        self.panel_versions = {}
        self.panel_task=None
        self.banner_printed=False
        async def run_help(ctx):
            await self.help_command(ctx)
        async def run_stock(ctx, action: str = ""):
            await self.stock_command(ctx, action)
        self.command(name="help", help="Automatically list all available commands")(run_help)
        self.command(name="stock", help="Display stock; use ;stock panel to post an auto-updating panel")(run_stock)

    def load_panels(self):
        try:
            data = json.loads(self.panel_file.read_text(encoding='utf-8'))
            return {int(k): int(v) for k, v in data.items()}
        except (OSError, ValueError, TypeError):
            return {}

    def save_panels(self):
        tmp = self.panel_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.panels), encoding='utf-8')
        tmp.replace(self.panel_file)

    async def setup_hook(self):
        self.add_view(StockView(self))
        self.panel_task=asyncio.create_task(self.update_panels())

    async def on_ready(self):
        if not self.banner_printed:
            if settings.clear_console_on_ready:
                os.system("cls" if os.name=="nt" else "clear")
            print(ASCII,flush=True)
            logged("ONLINE - %s (%s)",self.user,self.user.id)
            logging.info("Prefix: %s | Servers: %s",settings.discord_prefix,len(self.guilds))
            self.banner_printed=True

    async def on_command_error(self,ctx,error):
        if isinstance(error,commands.CommandNotFound): return
        logging.error("Command failed: %r",error)
        await ctx.send(embed=self.make_embed("Saphire Error", "Unable to run that command."))

    def make_embed(self, author_name, description=None):
        embed = discord.Embed(description=description, color=EMBED_COLOR)
        avatar = self.user.display_avatar.url if self.user else None
        embed.set_author(name=author_name, icon_url=avatar)
        return embed

    def make_stock_embed(self, row):
        now = datetime.now(timezone.utc)
        next_edit = now + timedelta(seconds=60)
        if row and row["updated_at"]:
            stock_text = (
                f"**Discord Members Online**\n{row['online_members']:,}\n\n"
                f"**Discord Members Offline**\n{row['offline_members']:,}"
            )
        else:
            stock_text = "Stock data pending first successful synchronization."
        description = (
            f"{stock_text}\n\n"
            f"**Last Edit**\n<t:{int(now.timestamp())}:R>\n\n"
            f"**Next Edit**\n<t:{int(next_edit.timestamp())}:R>"
        )
        embed = self.make_embed("Saphire Stock Panel", description)
        embed.set_footer(text="Saphire • Auto-updating stock")
        return embed

    async def help_command(self,ctx):
        descriptions = [
            f"**{settings.discord_prefix}{command.name}** — {command.help or 'No description'}"
            for command in sorted(self.commands,key=lambda x:x.name) if not command.hidden
        ]
        await ctx.send(embed=self.make_embed("Saphire Help Panel", "\n".join(descriptions) or "No commands available."))

    async def stock_command(self,ctx,action:str=""):
        if action.lower()=="panel":
            if not ctx.guild or not ctx.author.guild_permissions.manage_guild:
                await ctx.send(embed=self.make_embed("Saphire Permissions", "Manage Server permission required."))
                return
            msg=await ctx.send(embed=self.make_stock_embed(await self.stock.get()),view=StockView(self))
            self.panels[msg.id] = msg.channel.id
            self.save_panels()
            logged("Stock panel posted by %s",ctx.author)
        elif not action:
            await ctx.send(embed=self.make_stock_embed(await self.stock.get()),view=StockView(self))
        else:
            await ctx.send(embed=self.make_embed("Saphire Stock Panel", "Use ;stock panel"))

    async def update_panels(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                row=await self.stock.get()
                # Only edit on new database sync (or once after bot restart).
                for mid, channel_id in list(self.panels.items()):
                    try:
                        channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                        msg = await channel.fetch_message(mid)
                        await msg.edit(embed=self.make_stock_embed(row), view=StockView(self))
                        logged("Stock panel %s updated from Supabase", mid)
                    except discord.NotFound:
                        self.panels.pop(mid, None)
                        self.panel_versions.pop(mid, None)
                        self.save_panels()
                    except discord.Forbidden:
                        logging.warning("Cannot edit stock panel %s; check bot permissions", mid)
                    except discord.HTTPException as exc:
                        logging.warning("Panel update failed %s: %s", mid, exc)
            except Exception as exc:
                logging.error("Panel update loop: %s",exc)
            await asyncio.sleep(60)

    async def close(self):
        if self.panel_task:
            self.panel_task.cancel()
        await super().close()
