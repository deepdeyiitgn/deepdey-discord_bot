"""Study Partner cog: Virtual study partner with reminders and encouragement."""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import time
from datetime import datetime, timedelta


# Encouraging messages for different situations
REMINDERS = [
    "Focus time! 🎯 Keep going for {minutes} more minutes!",
    "You're doing great! {minutes} minutes left in this session. 💪",
    "Stay focused! Just {minutes} minutes until your next break. ⏰",
    "Keep up the momentum! {minutes} minutes to go! 🚀"
]

ENCOURAGEMENT = [
    "You're making progress! Every minute counts! ⭐",
    "Keep pushing! You're building your future! 🌟",
    "Stay strong! You've got this! 💪",
    "Remember your goals! You're getting closer! 🎯"
]

COMPLETION = [
    "Amazing work! You completed your study session! 🎉",
    "Well done staying focused! Take a well-deserved break! 🌟",
    "You crushed it! Keep up this consistency! 💪",
    "Another productive session complete! You're on fire! 🔥"
]


class Partner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._sessions = {}  # user_id -> {channel_id, end_time, task}
        self._check_sessions.start()

    def cog_unload(self):
        self._check_sessions.cancel()
        # Cancel all active sessions
        for session in self._sessions.values():
            if 'task' in session and not session['task'].done():
                session['task'].cancel()

    async def _send_reminder(self, channel_id: int, user_id: int, minutes: int):
        """Send a reminder message to the user."""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        msg = random.choice(REMINDERS).format(minutes=minutes)
        try:
            await channel.send(f"<@{user_id}> {msg}")
        except Exception:
            pass  # Channel might be deleted or no permissions

    async def _send_encouragement(self, channel_id: int, user_id: int):
        """Send random encouragement."""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        msg = random.choice(ENCOURAGEMENT)
        try:
            await channel.send(f"<@{user_id}> {msg}")
        except Exception:
            pass

    async def _run_session(self, user_id: int, channel_id: int, duration: int):
        """Run a study session with periodic reminders."""
        try:
            # Initial reminder after 5 minutes
            await asyncio.sleep(300)  # 5 minutes
            if user_id not in self._sessions:
                return
            await self._send_reminder(channel_id, user_id, duration - 5)
            
            # Periodic reminders every 15 minutes
            elapsed = 5
            while elapsed < duration:
                await asyncio.sleep(900)  # 15 minutes
                elapsed += 15
                if user_id not in self._sessions:
                    return
                
                if random.random() < 0.3:  # 30% chance of encouragement
                    await self._send_encouragement(channel_id, user_id)
                else:
                    remaining = duration - elapsed
                    if remaining > 0:
                        await self._send_reminder(channel_id, user_id, remaining)
            
            # Session complete
            if user_id in self._sessions:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    msg = random.choice(COMPLETION)
                    await channel.send(f"<@{user_id}> {msg}")
                del self._sessions[user_id]
                
        except asyncio.CancelledError:
            pass
        except Exception:
            if user_id in self._sessions:
                del self._sessions[user_id]

    @tasks.loop(minutes=1)
    async def _check_sessions(self):
        """Clean up expired sessions."""
        now = time.time()
        for user_id, session in list(self._sessions.items()):
            if now >= session['end_time']:
                if 'task' in session and not session['task'].done():
                    session['task'].cancel()
                del self._sessions[user_id]

    @_check_sessions.before_loop
    async def _before_check_sessions(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name='partner')
    async def partner(self, ctx, action: str = None, duration: int = 60):
        """Start/stop study partner mode: !partner start [minutes=60]"""
        if not action:
            if ctx.author.id in self._sessions:
                remaining = int(self._sessions[ctx.author.id]['end_time'] - time.time())
                await ctx.send(f'You have an active session with {remaining//60} minutes remaining.')
            else:
                await ctx.send('Usage: !partner start [minutes=60] | !partner stop')
            return

        if action == 'start':
            if ctx.author.id in self._sessions:
                await ctx.send('You already have an active study session!')
                return
                
            if duration < 15 or duration > 180:
                await ctx.send('Please choose a duration between 15 and 180 minutes.')
                return
                
            # Start new session
            end_time = time.time() + (duration * 60)
            task = asyncio.create_task(
                self._run_session(ctx.author.id, ctx.channel.id, duration)
            )
            self._sessions[ctx.author.id] = {
                'channel_id': ctx.channel.id,
                'end_time': end_time,
                'task': task
            }
            
            await ctx.send(f"Starting {duration} minute study session with you! Let's focus! 💪")
            return

        if action == 'stop':
            if ctx.author.id not in self._sessions:
                await ctx.send('You don\'t have an active study session.')
                return
                
            session = self._sessions[ctx.author.id]
            if 'task' in session and not session['task'].done():
                session['task'].cancel()
            del self._sessions[ctx.author.id]
            
            await ctx.send('Study session ended. Take a break! ⭐')
            return

        await ctx.send('Unknown action. Use: !partner start [minutes] | !partner stop')




async def setup(bot: commands.Bot):
    await bot.add_cog(Partner(bot))