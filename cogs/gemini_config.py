"""Configure Gemini reply settings per guild

Commands:
- /gemini toggle on|off  -> enable or disable Gemini in the guild
- /gemini channels add <channel> -> add channel to whitelist
- /gemini channels remove <channel> -> remove channel from whitelist
- /gemini channels list -> list whitelisted channels (empty means all channels)

Settings are stored in the project's DB via utils.db.DB key/value helper.
"""
from discord.ext import commands
import discord
from discord import app_commands
import json
from utils.db import DB

class GeminiConfig(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _set_enabled(self, guild_id: int, enabled: bool):
        key = f'gemini_enabled_{guild_id}'
        await DB.set_kv(key, '1' if enabled else '')

    async def _get_enabled(self, guild_id: int) -> bool:
        key = f'gemini_enabled_{guild_id}'
        val = await DB.get_kv(key)
        return bool(val == '1')

    async def _get_channels(self, guild_id: int):
        key = f'gemini_channels_{guild_id}'
        val = await DB.get_kv(key)
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    async def _set_channels(self, guild_id: int, channels: list):
        key = f'gemini_channels_{guild_id}'
        await DB.set_kv(key, json.dumps(channels))

    @commands.hybrid_group(name='gemini', description='Configure Gemini replies')
    async def gemini(self, ctx):
        await ctx.send('Use subcommands: toggle, channels')

    @gemini.command(name='toggle', description='Enable or disable Gemini in this guild')
    @app_commands.describe(state='on to enable, off to disable')
    @commands.has_guild_permissions(administrator=True)
    async def gemini_toggle(self, ctx, state: str):
        state = state.lower().strip()
        if state not in ('on', 'off'):
            await ctx.send('Use "on" or "off"')
            return
        await self._set_enabled(ctx.guild.id, state == 'on')
        await ctx.send(f'Gemini replies turned {state} for this guild.')

    @gemini.command(name='sync', description='Sync Gemini commands to this guild (admin only)')
    @commands.has_guild_permissions(administrator=True)
    async def gemini_sync(self, ctx):
        try:
            # Sync the app commands for this guild only
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f'Synced {len(synced)} commands to this guild.')
        except Exception as e:
            await ctx.send(f'Failed to sync commands: {e}')

    @gemini.group(name='channels', description='Manage channel whitelist for Gemini replies')
    async def gemini_channels(self, ctx):
        await ctx.send('Use add/remove/list subcommands')

    @gemini_channels.command(name='add', description='Add a channel to whitelist')
    @commands.has_guild_permissions(administrator=True)
    async def channels_add(self, ctx, channel: discord.TextChannel):
        lst = await self._get_channels(ctx.guild.id)
        if channel.id in lst:
            await ctx.send('Channel already whitelisted')
            return
        lst.append(channel.id)
        await self._set_channels(ctx.guild.id, lst)
        await ctx.send(f'Added {channel.mention} to Gemini whitelist')

    @gemini_channels.command(name='remove', description='Remove a channel from whitelist')
    @commands.has_guild_permissions(administrator=True)
    async def channels_remove(self, ctx, channel: discord.TextChannel):
        lst = await self._get_channels(ctx.guild.id)
        if channel.id not in lst:
            await ctx.send('Channel not in whitelist')
            return
        lst.remove(channel.id)
        await self._set_channels(ctx.guild.id, lst)
        await ctx.send(f'Removed {channel.mention} from Gemini whitelist')

    @gemini_channels.command(name='list', description='List whitelisted channels')
    async def channels_list(self, ctx):
        lst = await self._get_channels(ctx.guild.id)
        if not lst:
            await ctx.send('No whitelist set: Gemini will operate in all channels (when enabled).')
            return
        mentions = []
        for cid in lst:
            ch = ctx.guild.get_channel(int(cid))
            mentions.append(ch.mention if ch else str(cid))
        await ctx.send('Whitelisted channels: ' + ', '.join(mentions))


async def setup(bot: commands.Bot):
    await bot.add_cog(GeminiConfig(bot))
