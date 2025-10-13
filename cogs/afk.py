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
            print(f"[AFK] Received Interaction: user={getattr(interaction, 'user', None)} guild={getattr(interaction, 'guild', None)} reason={reason}")
            # Try to defer so we have time to make edits
            try:
                await interaction.response.defer(ephemeral=True)
                print(f"[AFK] interaction.response.defer called for {interaction.user}")
            except Exception:
                pass

            # Handle in DMs
            if not interaction.guild:
                await interaction.followup.send('This command must be used in a server.', ephemeral=True)
                return

            if reason and reason.lower().strip() == 'remove':
                data = await self._get_afk(interaction.guild.id, interaction.user.id)
                if not data:
                    try:
                        await interaction.followup.send('You are not AFK.', ephemeral=True)
                        print(f"[AFK] followup: user not AFK: {interaction.user}")
                    except Exception:
                        print(f"[AFK] could not send followup: user not AFK: {interaction.user}")
                    return
                try:
                    orig = data.get('orig_nick')
                    # fetch guild Member object to edit nick
                    member = interaction.guild.get_member(interaction.user.id)
                    if member:
                        if orig:
                            await member.edit(nick=orig)
                        else:
                            await member.edit(nick=None)
                    else:
                        print(f"[AFK] member not found in guild for removal: {interaction.user.id}")
                except Exception:
                    print(f"[AFK] exception editing nick during AFK removal for {interaction.user}")
                await self._remove_afk(interaction.guild.id, interaction.user.id)
                try:
                    await interaction.followup.send('AFK removed.', ephemeral=True)
                    print(f"[AFK] AFK removed for {interaction.user}")
                except Exception:
                    print(f"[AFK] could not send followup AFK removed for {interaction.user}")
                return

            # Set AFK
            reason = reason or 'Away'
            orig = None
            try:
                # fetch member object for nickname editing
                member = interaction.guild.get_member(interaction.user.id)
                if member:
                    orig = member.nick
                    new_nick = (AFK_PREFIX + (orig or member.name))[:32]
                    await member.edit(nick=new_nick)
                    print(f"[AFK] set nick for {member} -> {new_nick}")
                else:
                    print(f"[AFK] could not find member in guild to set nick: {interaction.user.id}")
            except Exception:
                print(f"[AFK] exception editing nick for set AFK for {interaction.user}")
            await self._set_afk(interaction.guild.id, interaction.user.id, {'reason': reason, 'orig_nick': orig})
            try:
                await interaction.followup.send(f'Set AFK: {reason}', ephemeral=True)
                print(f"[AFK] Set AFK stored for {interaction.user} reason={reason}")
            except Exception:
                print(f"[AFK] could not send followup set AFK for {interaction.user}")

        else:
            print(f"[AFK] Received Context command: author={ctx.author} guild={getattr(ctx, 'guild', None)} reason={reason}")
            if reason and reason.lower().strip() == 'remove':
                data = await self._get_afk(ctx.guild.id, ctx.author.id)
                if not data:
                    await ctx.send('You are not AFK.')
                    print(f"[AFK] ctx: user not AFK: {ctx.author}")
                    return
                try:
                    orig = data.get('orig_nick')
                    if orig:
                        await ctx.author.edit(nick=orig)
                    else:
                        await ctx.author.edit(nick=None)
                except Exception:
                    print(f"[AFK] exception editing nick during ctx AFK removal for {ctx.author}")
                await self._remove_afk(ctx.guild.id, ctx.author.id)
                await ctx.send('AFK removed.')
                print(f"[AFK] ctx AFK removed for {ctx.author}")
                return

            # Set AFK
            reason = reason or 'Away'
            orig = None
            try:
                orig = ctx.author.nick
                new_nick = (AFK_PREFIX + (orig or ctx.author.name))[:32]
                await ctx.author.edit(nick=new_nick)
                print(f"[AFK] ctx set nick for {ctx.author} -> {new_nick}")
            except Exception:
                print(f"[AFK] exception editing nick during ctx set AFK for {ctx.author}")
            await self._set_afk(ctx.guild.id, ctx.author.id, {'reason': reason, 'orig_nick': orig})
            await ctx.send(f'Set AFK: {reason}')
            print(f"[AFK] ctx Set AFK stored for {ctx.author} reason={reason}")
        # End of command - all interaction and ctx handling is done above in their branches.

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # If the author was AFK, clear their AFK state and restore nickname
        try:
            afk_self = await self._get_afk(message.guild.id, message.author.id)
            if afk_self:
                # restore nickname
                try:
                    orig = afk_self.get('orig_nick')
                    member = message.guild.get_member(message.author.id)
                    if member:
                        if orig:
                            await member.edit(nick=orig)
                        else:
                            await member.edit(nick=None)
                except Exception:
                    pass
                await self._remove_afk(message.guild.id, message.author.id)
                try:
                    await message.channel.send(f'{message.author.display_name}, I removed your AFK since you are back.')
                except Exception:
                    pass
        except Exception:
            pass
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
