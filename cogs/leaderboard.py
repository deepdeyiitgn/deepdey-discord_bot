"""Leaderboard cog: Competitive study rankings and XP system."""
import discord
from discord.ext import commands
from discord import app_commands
from utils import db


# XP constants
XP_PER_MINUTE = 10  # Base XP per study minute
STREAK_BONUS = 0.2  # +20% XP per day of streak
FOCUS_BONUS = 0.5   # +50% XP for focus sessions

# Levels (total XP needed)
LEVELS = {
    0: "Beginner Student",
    100: "Focused Learner",
    500: "Knowledge Seeker",
    1000: "Dedicated Scholar",
    2000: "Study Master",
    5000: "Academic Elite",
    10000: "Learning Legend",
    20000: "Wisdom Keeper"
}

# Achievement badges
BADGES = {
    'early_bird': '🌅',  # Study before 8 AM
    'night_owl': '🦉',   # Study after 10 PM
    'streaker': '🔥',    # 7+ day streak
    'focused': '🎯',     # Complete 5+ focus sessions
    'consistent': '⭐',  # Log study 5 days in a row
    'scholar': '📚',     # Log 1000+ total minutes
}


class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_level(self, xp: int) -> tuple:
        """Get level title and next level XP target."""
        current_title = LEVELS[0]
        next_xp = list(LEVELS.keys())[1]
        
        for req_xp, title in sorted(LEVELS.items()):
            if xp >= req_xp:
                current_title = title
            else:
                next_xp = req_xp
                break
                
        return current_title, next_xp

    @commands.hybrid_command(name='rank')
    async def rank(self, ctx):
        """Show your rank and level"""
        if not ctx.guild:
            await ctx.send('This command can only be used in a server.')
            return
            
        # Get stats
        streak = await db.DB.get_streak(ctx.author.id)
        streak_count = streak['count'] if streak else 0
        
        total_logs = await db.DB.get_user_logs(ctx.author.id)
        total_minutes = sum(log['minutes'] for log in total_logs)
        total_xp = total_minutes * XP_PER_MINUTE
        
        # Apply streak bonus
        if streak_count > 0:
            bonus_xp = total_xp * (streak_count * STREAK_BONUS)
            total_xp = int(total_xp + bonus_xp)
        
        # Get level info
        title, next_xp = self._get_level(total_xp)
        xp_needed = next_xp - total_xp
        
        # Format response
        embed = discord.Embed(
            title=f"Study Stats for {ctx.author.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=title, inline=False)
        embed.add_field(name="Total XP", value=f"{total_xp:,} XP", inline=True)
        embed.add_field(name="Next Level", value=f"{xp_needed:,} XP needed", inline=True)
        embed.add_field(name="Study Streak", value=f"{streak_count} days 🔥" if streak_count else "No active streak", inline=True)
        embed.add_field(name="Total Time", value=f"{total_minutes:,} minutes", inline=True)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='leaderboard')
    async def leaderboard(self, ctx, timeframe: str = 'week'):
        """Show server study leaderboard"""
        if not ctx.guild:
            await ctx.send('This command can only be used in a server.')
            return
            
        # Get top 10 users
        leaders = await db.DB.get_leaderboard(ctx.guild.id, limit=10)
        if not leaders:
            await ctx.send('No study logs found for this server.')
            return
        
        # Format leaderboard
        embed = discord.Embed(
            title=f"📊 {ctx.guild.name} Study Leaderboard",
            description="Top students by study time",
            color=discord.Color.gold()
        )
        
        for i, (user_id, minutes) in enumerate(leaders, 1):
            member = ctx.guild.get_member(user_id)
            name = member.name if member else f'User {user_id}'
            
            # Add medals for top 3
            prefix = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'`{i}.`')
            
            embed.add_field(
                name=f"{prefix} {name}",
                value=f"{minutes} minutes studied",
                inline=False
            )
        
        await ctx.send(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(Leaderboard(bot))