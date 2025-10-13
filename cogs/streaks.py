"""Streak tracking system for study consistency."""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from utils import db


class Streaks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def update_streak(self, user_id: int) -> tuple[int, int, bool]:
        """Update user's streak and return (current_streak, highest_streak, new_achieved)."""
        # Get last study timestamp
        last_log = await db.DB.fetchone(
            'SELECT ts FROM study_logs WHERE user_id = ? ORDER BY ts DESC LIMIT 1',
            (user_id,)
        )
        
        if not last_log:
            # First study session
            await db.DB.execute(
                'INSERT OR REPLACE INTO streaks (user_id, current_streak, highest_streak, last_study) VALUES (?, 1, 1, ?)',
                (user_id, int(datetime.now().timestamp()))
            )
            return 1, 1, True
            
        # Get current streak info
        streak_data = await db.DB.fetchone(
            'SELECT current_streak, highest_streak, last_study FROM streaks WHERE user_id = ?',
            (user_id,)
        )
        
        if not streak_data:
            # Initialize streak
            await db.DB.execute(
                'INSERT INTO streaks (user_id, current_streak, highest_streak, last_study) VALUES (?, 1, 1, ?)',
                (user_id, int(datetime.now().timestamp()))
            )
            return 1, 1, True
            
        current_streak = streak_data['current_streak']
        highest_streak = streak_data['highest_streak']
        last_study = datetime.fromtimestamp(streak_data['last_study'])
        now = datetime.now()
        
        # Check if streak is broken (more than 48 hours since last study)
        if now - last_study > timedelta(hours=48):
            current_streak = 1
        # Check if it's a new day's study (more than 12 hours since last)
        elif now - last_study > timedelta(hours=12):
            current_streak += 1
            if current_streak > highest_streak:
                highest_streak = current_streak
                
        # Update streak data
        await db.DB.execute(
            'UPDATE streaks SET current_streak = ?, highest_streak = ?, last_study = ? WHERE user_id = ?',
            (current_streak, highest_streak, int(now.timestamp()), user_id)
        )
        
        return current_streak, highest_streak, current_streak > streak_data['current_streak']



    @commands.hybrid_command(name='streak')
    async def streak(self, ctx):
        """Check your current study streak"""
        streak_data = await db.DB.fetchone(
            'SELECT current_streak, highest_streak FROM streaks WHERE user_id = ?',
            (ctx.author.id,)
        )
        
        if not streak_data:
            await ctx.send(
                "You haven't started your study streak yet! Log your first study session to begin."
            )
            return
            
        embed = discord.Embed(
            title="🔥 Study Streak",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="Current Streak",
            value=f"{streak_data['current_streak']} days"
        )
        embed.add_field(
            name="Highest Streak",
            value=f"{streak_data['highest_streak']} days"
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    # Create streaks table if it doesn't exist
    await db.DB.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            user_id INTEGER PRIMARY KEY,
            current_streak INTEGER DEFAULT 0,
            highest_streak INTEGER DEFAULT 0,
            last_study INTEGER
        )
    ''')
    
    await bot.add_cog(Streaks(bot))