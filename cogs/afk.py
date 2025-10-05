"""AFK cog

Commands:
- !afk [reason] or /afk reason: [reason] -> Set AFK with reason and prefix nickname with [AFK]
- !afk remove or /afk reason: remove -> Remove AFK and restore nickname

Behavior:
- Supports both traditional prefix commands and slash commands
- When someone mentions an AFK user, bot posts in channel and DMs the caller with the AFK reason.
- Automatically preserves original nickname and restores it when AFK is removed
"""
from discord.ext import commands
from discord import app_commands
import discord
from utils.db import DB
import asyncio
from typing import Optional


AFK_PREFIX = '[AFK] '


class AFK(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # nothing to load for now
        pass

    async def _get_afk(self, guild_id: int, user_id: int) -> Optional[dict]:
        key = f'afk_{guild_id}_{user_id}'
        val = await DB.get_kv(key)
        if not val:
            return None
        import json
        return json.loads(val)

    async def _set_afk(self, guild_id: int, user_id: int, data: dict):
        import json
        key = f'afk_{guild_id}_{user_id}'
        await DB.set_kv(key, json.dumps(data))

    async def _remove_afk(self, guild_id: int, user_id: int):
        key = f'afk_{guild_id}_{user_id}'
        await DB.set_kv(key, '')

    @commands.hybrid_command(
        name='afk',
        description='Set or remove AFK status with optional reason'
    )
    @app_commands.describe(reason="The reason for going AFK, or 'remove' to disable AFK")
    async def afk(self, ctx, *, reason: str = None):
        """Set or remove AFK status"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            # Try to defer so we have time to make edits
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass

            # Handle in DMs
            if not interaction.guild:
                await interaction.followup.send('This command must be used in a server.', ephemeral=True)
                return

            if reason and reason.lower().strip() == 'remove':
                data = await self._get_afk(interaction.guild.id, interaction.user.id)
                if not data:
                    await interaction.followup.send('You are not AFK.', ephemeral=True)
                    return
                try:
                    orig = data.get('orig_nick')
                    if orig:
                        await interaction.user.edit(nick=orig)
                    else:
                        await interaction.user.edit(nick=None)
                except Exception:
                    pass
                await self._remove_afk(interaction.guild.id, interaction.user.id)
                await interaction.followup.send('AFK removed.', ephemeral=True)
                return

            # Set AFK
            reason = reason or 'Away'
            orig = None
            try:
                orig = interaction.user.nick
                new_nick = (AFK_PREFIX + (orig or interaction.user.name))[:32]
                await interaction.user.edit(nick=new_nick)
            except Exception:
                pass
            await self._set_afk(interaction.guild.id, interaction.user.id, {'reason': reason, 'orig_nick': orig})
            await interaction.followup.send(f'Set AFK: {reason}', ephemeral=True)

        else:
            if reason and reason.lower().strip() == 'remove':
                data = await self._get_afk(ctx.guild.id, ctx.author.id)
                if not data:
                    await ctx.send('You are not AFK.')
                    return
                try:
                    orig = data.get('orig_nick')
                    if orig:
                        await ctx.author.edit(nick=orig)
                    else:
                        await ctx.author.edit(nick=None)
                except Exception:
                    pass
                await self._remove_afk(ctx.guild.id, ctx.author.id)
                await ctx.send('AFK removed.')
                return

            # Set AFK
            reason = reason or 'Away'
            orig = None
            try:
                orig = ctx.author.nick
                new_nick = (AFK_PREFIX + (orig or ctx.author.name))[:32]
                await ctx.author.edit(nick=new_nick)
            except Exception:
                pass
            await self._set_afk(ctx.guild.id, ctx.author.id, {'reason': reason, 'orig_nick': orig})
            await ctx.send(f'Set AFK: {reason}')
        if reason and reason.lower().strip() == 'remove':
            # guard for DMs
            if not interaction.guild:
                await interaction.response.send_message('AFK removal must be used in a server.', ephemeral=True)
                return
            data = await self._get_afk(interaction.guild.id, interaction.user.id)
            if not data:
                await interaction.followup.send('You are not AFK.', ephemeral=True)
                return
            try:
                orig = data.get('orig_nick')
                # fetch member object
                member = interaction.guild.get_member(interaction.user.id)
                if member:
                    await member.edit(nick=orig)
            except Exception:
                pass
            await self._remove_afk(interaction.guild.id, interaction.user.id)
            await interaction.response.send_message('AFK removed.', ephemeral=True)
            return

        reason = reason or 'Away'
        orig = None
        try:
            if not interaction.guild:
                # cannot set guild nick in DMs
                await interaction.response.send_message('AFK can only be set in a server (use the server where you want the AFK tag).', ephemeral=True)
                return
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                orig = member.nick
                new_nick = (AFK_PREFIX + (orig or member.name))[:32]
                await member.edit(nick=new_nick)
        except Exception:
            # ignore nick edit failures but continue
            pass
        await self._set_afk(interaction.guild.id, interaction.user.id, {'reason': reason, 'orig_nick': orig})
        await interaction.response.send_message(f'Set AFK: {reason}', ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # Check mentions
        if not message.mentions:
            return
        notified = set()
        for user in message.mentions:
            afk = await self._get_afk(message.guild.id, user.id)
            if afk and user.id not in notified:
                # send channel message and DM to caller
                try:
                    await message.channel.send(f'{user.display_name} is AFK: {afk.get("reason")}')
                except Exception:
                    pass
                try:
                    await message.author.send(f'{user.display_name} is AFK: {afk.get("reason")}')
                except Exception:
                    pass
                notified.add(user.id)


async def setup(bot: commands.Bot):
    cog = AFK(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
