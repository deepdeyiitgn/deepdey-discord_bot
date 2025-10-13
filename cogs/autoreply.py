"""Auto-reply cog

Features:
 - Auto replies for keywords
 - Learn new keyword->reply pairs
 - Toggle on/off per channel
"""
from discord.ext import commands
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import re
from discord import app_commands
import discord


DATA_PATH = Path(__file__).parent.parent / 'data' / 'autoreply.json'


class AutoReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = {'channels': {}, 'pairs': {}}

    async def cog_load(self):
        self.data = await async_load_json(DATA_PATH, default={'channels': {}, 'pairs': {}})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        ch_cfg = self.data.get('channels', {}).get(str(message.channel.id), True)
        if ch_cfg is False:
            return
        content = message.content.lower()
        for k, v in self.data.get('pairs', {}).items():
            try:
                if re.search(r'\b' + re.escape(k.lower()) + r'\b', content):
                    await message.channel.send(v)
                    return
            except Exception:
                continue

    @commands.hybrid_group(name='autoreply', invoke_without_command=True)
    async def autoreply(self, ctx):
        """Auto-reply management commands"""
        await ctx.send('Use subcommands: add, remove, toggle, list')

    # individual slash commands below (no app_commands.group usage)

    @autoreply.command(name='add')
    @app_commands.describe(
        key='The keyword to trigger the auto-reply',
        reply='The message to send when the keyword is detected'
    )
    @commands.has_permissions(manage_guild=True)
    async def add_pair(self, ctx, key: str, *, reply: str):
        """Add a keyword and its auto-reply message"""
        self.data.setdefault('pairs', {})[key] = reply
        await async_save_json(DATA_PATH, self.data)
        await ctx.send(f'Added auto-reply for "{key}"')

    @autoreply.command(name='remove')
    @app_commands.describe(
        key='The keyword to remove from auto-replies'
    )
    @commands.has_permissions(manage_guild=True)
    async def remove_pair(self, ctx, key: str):
        """Remove a keyword from auto-replies"""
        if key in self.data.get('pairs', {}):
            self.data['pairs'].pop(key, None)
            await async_save_json(DATA_PATH, self.data)
            await ctx.send(f'Removed auto-reply for "{key}"')
        else:
            await ctx.send('Key not found')

    @autoreply.command(name='toggle')
    @commands.has_permissions(manage_guild=True)
    async def toggle_channel(self, ctx):
        """Toggle auto-replies on/off for this channel"""
        ch = str(ctx.channel.id)
        cur = self.data.setdefault('channels', {}).get(ch, True)
        self.data['channels'][ch] = not cur
        await async_save_json(DATA_PATH, self.data)
        await ctx.send(f'Auto-reply for this channel is now {"enabled" if self.data["channels"][ch] else "disabled"}')
        self.data['channels'][ch] = not cur
        await async_save_json(DATA_PATH, self.data)
        await interaction.followup.send(f'Auto-reply for this channel set to {self.data[ch]}', ephemeral=True)

    @autoreply.command(name='list')
    async def list_pairs(self, ctx):
        """List all auto-reply pairs"""
        pairs = self.data.get('pairs', {})
        if not pairs:
            await ctx.send('No auto-replies set.')
            return
            
        embed = discord.Embed(title='Auto-Replies', color=discord.Color.blue())
        for key, value in pairs.items():
            embed.add_field(name=key, value=value, inline=False)
            
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    cog = AutoReply(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
