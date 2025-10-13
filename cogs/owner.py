"""Owner commands module for bot management"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
import sys
import datetime

logger = logging.getLogger('owner')

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='bot_restart', description='Restart the bot and reload all files')
    @commands.is_owner()
    async def bot_restart(self, ctx):
        """Restart the bot and reload all files (Owner only)"""
        try:
            await ctx.send("🔄 Restarting bot and reloading all files...")
            # Reload all cogs
            for extension in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(extension)
                except Exception as e:
                    await ctx.send(f"❌ Error reloading {extension}: {e}")
                    return
            # Sync commands
            await self.bot.tree.sync()
            await ctx.send("✅ Bot restarted and all files reloaded successfully!")
        except Exception as e:
            await ctx.send(f"❌ Error during restart: {e}")

async def setup(bot):
    await bot.add_cog(Owner(bot))