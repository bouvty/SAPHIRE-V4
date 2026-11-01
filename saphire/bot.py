import asyncio
import logging
import os
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
        self.panels={}
        self.panel_task=None
        self.banner_printed=False

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
        await ctx.send(embed=discord.Embed(description="Unable to run that command.",color=EMBED_COLOR))

    def make_stock_embed(self,row):
        embed=discord.Embed(title="Saphire • Discord Member Stock",color=EMBED_COLOR)
        if not row or not row["updated_at"]:
            embed.description="Waiting for the first stock sync."
        else:
            embed.add_field(name="Discord members online",value=f"**{row['online_members']:,}**",inline=False)
            embed.add_field(name="Discord members offline",value=f"**{row['offline_members']:,}**",inline=False)
        updated=row["updated_at"] if row else None
        next_dt=updated+timedelta(seconds=settings.stock_refresh_seconds) if updated else None
        remaining=(next_dt-datetime.now(timezone.utc)).total_seconds() if next_dt else 0
        embed.add_field(name="Last updated",value=relative_stamp(updated),inline=True)
        embed.add_field(name="Next refresh",value=countdown(remaining) if next_dt else "Pending",inline=True)
        embed.set_footer(text="Saphire • Auto-updating stock")
        return embed

    @commands.command(name="help",help="Automatically list all available commands")
    async def help_command(self,ctx):
        embed=discord.Embed(title="Saphire • Commands",color=EMBED_COLOR)
        for command in sorted(self.commands,key=lambda x:x.name):
            if not command.hidden:
                embed.add_field(name=settings.discord_prefix+command.name,value=command.help or "No description",inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="stock",help="Display stock; use ;stock panel to post an auto-updating panel")
    async def stock_command(self,ctx,action:str=""):
        if action.lower()=="panel":
            if not ctx.guild or not ctx.author.guild_permissions.manage_guild:
                await ctx.send(embed=discord.Embed(description="Manage Server permission required.",color=EMBED_COLOR))
                return
            msg=await ctx.send(embed=self.make_stock_embed(await self.stock.get()),view=StockView(self))
            self.panels[msg.id]=msg
            logged("Stock panel posted by %s",ctx.author)
        elif not action:
            await ctx.send(embed=self.make_stock_embed(await self.stock.get()),view=StockView(self))
        else:
            await ctx.send(embed=discord.Embed(description="Use ;stock panel",color=EMBED_COLOR))

    async def update_panels(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                row=await self.stock.get()
                for mid,msg in list(self.panels.items()):
                    try:
                        await msg.edit(embed=self.make_stock_embed(row),view=StockView(self))
                    except (discord.Forbidden,discord.NotFound):
                        self.panels.pop(mid,None)
                    except discord.HTTPException as exc:
                        logging.warning("Panel update failed %s: %s",mid,exc)
            except Exception as exc:
                logging.error("Panel update loop: %s",exc)
            await asyncio.sleep(max(10,settings.panel_refresh_seconds))

    async def close(self):
        if self.panel_task:
            self.panel_task.cancel()
        await super().close()
