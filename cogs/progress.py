"""Progress cog: track study progress and streaks, weekly reports"""
import discord
from discord.ext import commands, tasks
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import datetime
from discord import app_commands
from utils import db


DATA_PATH = Path(__file__).parent.parent / 'data' / 'progress.json'


class Progress(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = {'users': {}, 'report_channel': None}
        self.weekly_report.start()

    async def cog_load(self):
        self.data = await async_load_json(DATA_PATH, default=self.data)

    def cog_unload(self):
        self.weekly_report.cancel()

    @commands.hybrid_command(name='progress')
    async def progress(self, ctx, action: str = None, subject: str = None, value: int = None):
        """Track progress: !progress update subject value | !progress view"""
        if not action:
            await ctx.send('Usage: !progress update <subject> <value> | !progress view')
            return
            
        if action == 'update':
            if not subject or value is None:
                await ctx.send('Usage: !progress update <subject> <value>')
                return
                
            if value < 0 or value > 100:
                await ctx.send('Progress value must be between 0 and 100.')
                return
                
            guild_id = ctx.guild.id if ctx.guild else None
            await db.DB.set_progress(ctx.author.id, guild_id, subject.lower(), value)
            await ctx.send(f'Updated progress for {subject}: {value}%')
            return
            
        if action == 'view':
            guild_id = ctx.guild.id if ctx.guild else None
            rows = await db.DB.get_progress(ctx.author.id, guild_id)
            if not rows:
                await ctx.send('No progress tracked yet.')
                return
                
            lines = []
            for r in rows:
                subj = r['subject']
                pct = r['percent']
                bar = '█' * (pct // 10) + '░' * ((100 - pct) // 10)
                lines.append(f'{subj.title()}: {bar} {pct}%')
            
            embed = discord.Embed(
                title="📊 Your Study Progress",
                description='\n'.join(lines),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
            
        await ctx.send('Usage: !progress update <subject> <value> | !progress view')

    @tasks.loop(hours=24)
    async def weekly_report(self):
        # Runs daily, but only reports weekly (weekday==0 if desired)
        await self.bot.wait_until_ready()
        if not self.data.get('report_channel'):
            return
        # Check if today is Monday
        if datetime.date.today().weekday() != 0:
            return
        ch_id = self.data['report_channel']
        channel = self.bot.get_channel(ch_id)
        if not channel:
            return
        users = self.data.get('users', {})
        lines = []
        for uid, info in users.items():
            lines.append(f'<@{uid}>: {info.get("minutes",0)} minutes')
        if not lines:
            await channel.send('No progress to report this week.')
            return
        await channel.send('Weekly Progress Report:\n' + '\n'.join(lines))

    @commands.hybrid_command(name='setreportchan')
    @commands.has_permissions(manage_guild=True)
    async def set_report_channel(self, ctx):
        self.data['report_channel'] = ctx.channel.id
        await async_save_json(DATA_PATH, self.data)
        await ctx.send('This channel is now the weekly report channel.')




async def setup(bot: commands.Bot):
    cog = Progress(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
