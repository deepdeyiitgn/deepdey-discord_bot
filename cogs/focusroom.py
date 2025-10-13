"""Focus Room cog: Voice channel study zones with muting."""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import time
from datetime import datetime, timedelta


class FocusRoom(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._focus_channels = {}  # channel_id -> {end_time, allowed_users}
        self._check_channels.start()

    def cog_unload(self):
        self._check_channels.cancel()

    @tasks.loop(seconds=30)
    async def _check_channels(self):
        """Clean up expired focus rooms."""
        now = time.time()
        for channel_id, info in list(self._focus_channels.items()):
            if now >= info['end_time']:
                del self._focus_channels[channel_id]

    @_check_channels.before_loop
    async def _before_check_channels(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Monitor voice channel activity."""
        # Skip bot updates
        if member.bot:
            return
            
        # Check if joined a focus room
        if after.channel and after.channel.id in self._focus_channels:
            focus_info = self._focus_channels[after.channel.id]
            
            # Allow listed users to join
            if member.id in focus_info['allowed_users']:
                return
                
            try:
                # Auto-mute new joiners
                await member.edit(mute=True)
                await member.send(f"This is a focus room in study mode for {len(focus_info['allowed_users'])} users. You've been auto-muted to prevent distractions.")
            except discord.Forbidden:
                pass
                
        # Check if left a focus room and was in allowed users
        if before.channel and before.channel.id in self._focus_channels:
            focus_info = self._focus_channels[before.channel.id]
            if member.id in focus_info['allowed_users']:
                focus_info['allowed_users'].remove(member.id)
                
                # If no allowed users left, end focus mode
                if not focus_info['allowed_users']:
                    del self._focus_channels[before.channel.id]
                    try:
                        # Unmute everyone
                        for m in before.channel.members:
                            await m.edit(mute=False)
                    except discord.Forbidden:
                        pass

    @commands.hybrid_command(name='focusroom')
    @commands.has_permissions(mute_members=True)
    async def focusroom(self, ctx, action: str = None, duration: int = 30):
        """Start/stop focus mode: !focusroom start [minutes=30]"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You need to be in a voice channel to use this command.')
            return
            
        channel = ctx.author.voice.channel
        
        if not action:
            if channel.id in self._focus_channels:
                info = self._focus_channels[channel.id]
                remaining = int(info['end_time'] - time.time())
                await ctx.send(f'This channel is in focus mode for {remaining//60} more minutes.')
            else:
                await ctx.send('Usage: !focusroom start [minutes=30] | !focusroom stop')
            return

        if action == 'start':
            if channel.id in self._focus_channels:
                await ctx.send('This channel is already in focus mode!')
                return
                
            if duration < 5 or duration > 180:
                await ctx.send('Please choose a duration between 5 and 180 minutes.')
                return
                
            # Start focus mode
            end_time = time.time() + (duration * 60)
            self._focus_channels[channel.id] = {
                'end_time': end_time,
                'allowed_users': {m.id for m in channel.members if not m.bot}
            }
            
            # Notify channel
            await ctx.send(f'🎯 Focus mode activated for {duration} minutes! New users will be auto-muted.')
            return

        if action == 'stop':
            if channel.id not in self._focus_channels:
                await ctx.send('This channel is not in focus mode.')
                return
                
            # End focus mode
            del self._focus_channels[channel.id]
            
            # Unmute everyone
            try:
                for member in channel.members:
                    await member.edit(mute=False)
            except discord.Forbidden:
                pass
                
            await ctx.send('Focus mode ended. Channel returned to normal.')
            return

        await ctx.send('Unknown action. Use: !focusroom start [minutes] | !focusroom stop')




async def setup(bot: commands.Bot):
    await bot.add_cog(FocusRoom(bot))