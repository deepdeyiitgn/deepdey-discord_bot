# focus.py

"""Focus cog: Pomodoro timer and focus sessions."""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import time
from utils import db

# Motivational messages sent after sessions
MOTIVATION = [
    "Great work! Keep up the momentum! 🚀",
    "Another productive session completed! 💪",
    "You're making progress - be proud! ⭐",
    "Stay consistent, stay focused! 🎯",
    "Small steps lead to big achievements! 📚",
    "Your future self will thank you! 🌟",
    "Knowledge is power - keep learning! 🧠",
    "Success is built one session at a time! 💡",
]

class Focus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._active_timers = {}  # user_id -> {end_time, task}

    def cog_unload(self):
        # Cancel any running timers
        for timer in self._active_timers.values():
            if 'task' in timer and not timer['task'].done():
                timer['task'].cancel()

    async def _end_focus_session(self, user_id: int, guild_id: int, channel_id: int, minutes: int):
        """Handle focus session completion."""
        if user_id not in self._active_timers:
            return

        # Get channel and send completion message
        channel = self.bot.get_channel(channel_id)
        if channel:
            msg = random.choice(MOTIVATION)
            await channel.send(f"<@{user_id}> Focus session complete! {msg}")

            # Log the session
            await db.DB.add_study_log(user_id, minutes, int(time.time()), "focus-session", guild_id)
            if guild_id:
                await db.DB.increment_leaderboard(guild_id, user_id, minutes)

        # Cleanup timer
        del self._active_timers[user_id]

    async def _start_timer(self, user_id: int, guild_id: int, channel_id: int, minutes: int):
        """Start a new focus timer for the user."""
        # Cancel existing timer if any
        if user_id in self._active_timers:
            old_timer = self._active_timers[user_id]
            if 'task' in old_timer and not old_timer['task'].done():
                old_timer['task'].cancel()

        # Create new timer
        end_time = time.time() + (minutes * 60)
        task = asyncio.create_task(
            asyncio.sleep(minutes * 60)
        )
        self._active_timers[user_id] = {'end_time': end_time, 'task': task}

        # Wait for completion and cleanup
        try:
            await task
            await self._end_focus_session(user_id, guild_id, channel_id, minutes)
        except asyncio.CancelledError:
            pass

    @commands.hybrid_command(name='focus')
    async def focus(self, ctx, action: str = None, duration: int = 25):
        """Start a Pomodoro focus timer: !focus start [minutes=25]"""
        if action != 'start':
            await ctx.send('Usage: !focus start [minutes=25]')
            return

        if duration < 1 or duration > 120:
            await ctx.send('Please choose a duration between 1 and 120 minutes.')
            return

        guild_id = ctx.guild.id if ctx.guild else None
        await ctx.send(f'Starting {duration} minute focus session. Stay focused! 🎯')

        # Start the timer
        await self._start_timer(ctx.author.id, guild_id, ctx.channel.id, duration)

    @commands.hybrid_command(name='cancel')
    async def cancel(self, ctx):
        """Cancel your active focus timer"""
        try:
            if ctx.author.id not in self._active_timers:
                await ctx.send('You don\'t have an active focus session.')
                return

            timer = self._active_timers[ctx.author.id]
            if 'task' in timer and not timer['task'].done():
                timer['task'].cancel()
                del self._active_timers[ctx.author.id]
                await ctx.send('Focus session cancelled.')
        except Exception as e:
            await ctx.send(f'Error cancelling focus session: {e}')

    @focus.error
    async def focus_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Usage: !focus start [minutes=25]')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Please provide a valid duration in minutes.')
        else:
            await ctx.send(f'Error: {error}')

    @cancel.error
    async def cancel_error(self, ctx, error):
        await ctx.send(f'Error cancelling focus session: {error}')

    @commands.hybrid_command(name='status')
    async def status(self, ctx):
        """Check your current focus session status"""
        if ctx.author.id not in self._active_timers:
            await ctx.send('You don\'t have an active focus session.')
            return

        timer = self._active_timers[ctx.author.id]
        remaining = int(timer['end_time'] - time.time())
        if remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            await ctx.send(f'You have {minutes}m {seconds}s remaining in your focus session.')
        else:
            await ctx.send('Your focus session is ending...')


async def setup(bot):
    await bot.add_cog(Focus(bot))