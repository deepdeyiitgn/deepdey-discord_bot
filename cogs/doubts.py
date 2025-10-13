"""Doubts cog: Ask and manage study-related questions with private threads."""
import discord
from discord.ext import commands
from discord import app_commands
import time
from utils import db


class Doubts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -- Admin configuration helpers (stored in kv) --
    async def _get_doubt_channel(self, guild_id: int):
        val = await db.DB.get_kv(f'doubt_channel_{guild_id}')
        return int(val) if val else None

    async def _set_doubt_channel(self, guild_id: int, channel_id: int):
        await db.DB.set_kv(f'doubt_channel_{guild_id}', str(channel_id))

    async def _get_mentor_role(self, guild_id: int):
        val = await db.DB.get_kv(f'mentor_role_{guild_id}')
        return int(val) if val else None

    async def _set_mentor_role(self, guild_id: int, role_id: int):
        await db.DB.set_kv(f'mentor_role_{guild_id}', str(role_id))

    # ----------------- Commands -----------------
    @commands.hybrid_command(name='doubt')
    async def doubt(self, ctx, *, question: str = None):
        """Ask a doubt: provide your question. Creates a private thread in the configured doubt channel."""
        if not ctx.guild:
            await ctx.send('This command can only be used in a server.', ephemeral=True)
            return

        if not question:
            await ctx.send('Please provide your question. Usage: /doubt <your question>')
            return

        guild_id = ctx.guild.id
        doubt_id = await db.DB.add_doubt(guild_id, ctx.author.id, question, int(time.time()))

        # Create a private thread in configured channel
        channel_id = await self._get_doubt_channel(guild_id)
        if not channel_id:
            await ctx.send('Doubt recorded, but no doubt channel is configured. Mentors cannot see it yet. Contact an admin.', ephemeral=True)
            return

        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            await ctx.send('Configured doubt channel not found. Ask an admin to reconfigure.', ephemeral=True)
            return

        # Create private thread (discord.py: create_thread with type=private_thread requires appropriate permissions)
        try:
            thread = await channel.create_thread(name=f'Doubt-{ctx.author.display_name}-{doubt_id}', type=discord.ChannelType.private_thread)
        except Exception:
            # Fallback: create public thread
            thread = await channel.create_thread(name=f'Doubt-{ctx.author.display_name}-{doubt_id}')

        # Add the asker and mentor role (if configured)
        try:
            await thread.add_user(ctx.author)
        except Exception:
            pass

        mentor_role_id = await self._get_mentor_role(guild_id)
        if mentor_role_id:
            role = ctx.guild.get_role(mentor_role_id)
            if role:
                # invite role members by adding them to the thread
                for member in role.members:
                    try:
                        await thread.add_user(member)
                    except Exception:
                        continue

        # Link thread in DB
        await db.DB.link_doubt_thread(doubt_id, guild_id, channel.id, thread.id, int(time.time()))

        await ctx.send(f'✅ Your doubt has been recorded and a private thread has been created: {thread.mention}', ephemeral=True)



    @commands.hybrid_command(name='claim')
    @commands.has_permissions(manage_messages=True)
    async def claim(self, ctx):
        """Claim the current doubt thread (mentors/admins)"""
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send('This command must be used inside a doubt thread.')
            return

        thread = ctx.channel
        record = await db.DB.get_doubt_by_thread(thread.id)
        if not record:
            await ctx.send('No doubt linked to this thread.')
            return

        await db.DB.claim_doubt_thread(thread.id, ctx.author.id)
        await thread.send(f'✅ This thread has been claimed by {ctx.author.mention}.')
        await ctx.send('You have claimed this doubt thread.', ephemeral=True)

    @commands.hybrid_command(name='close')
    async def close(self, ctx):
        """Close the current doubt thread (asker or claimer or admins)"""
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send('This command must be used inside a doubt thread.')
            return

        thread = ctx.channel
        record = await db.DB.get_doubt_by_thread(thread.id)
        if not record:
            await ctx.send('No doubt linked to this thread.')
            return

        # Permission: asker, claimer, or manage_messages
        asker_id = record['asker_id']
        claimer_id = record['claimed_by'] if 'claimed_by' in record.keys() else None
        if ctx.author.id not in [asker_id, claimer_id] and not ctx.author.guild_permissions.manage_messages:
            await ctx.send('Only the asker, the claimer, or moderators can close this thread.')
            return

        await db.DB.close_doubt_thread(thread.id)
        # mark doubt resolved
        await db.DB.execute('UPDATE doubts SET resolved = 1 WHERE id = ?', (record['doubt_id'],))

        await thread.send('🔒 This doubt has been marked as resolved and the thread will be archived.')
        try:
            await thread.edit(archived=True, locked=True)
        except Exception:
            pass

        await ctx.send('Thread closed.', ephemeral=True)

    @commands.hybrid_command(name='set_doubt_channel')
    @commands.has_permissions(manage_guild=True)
    async def set_doubt_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where doubt threads will be created"""
        await self._set_doubt_channel(ctx.guild.id, channel.id)
        await ctx.send(f'Configured doubt channel: {channel.mention}', ephemeral=True)

    @commands.hybrid_command(name='set_mentor_role')
    @commands.has_permissions(manage_guild=True)
    async def set_mentor_role(self, ctx, role: discord.Role):
        """Set the mentor role for auto-inviting mentors into doubt threads"""
        await self._set_mentor_role(ctx.guild.id, role.id)
        await ctx.send(f'Configured mentor role: {role.name}', ephemeral=True)




async def setup(bot: commands.Bot):
    await bot.add_cog(Doubts(bot))