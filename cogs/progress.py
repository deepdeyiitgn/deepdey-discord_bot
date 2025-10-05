"""Progress cog: track study progress and streaks, weekly reports"""
import discord
from discord.ext import commands, tasks
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import datetime
from discord import app_commands


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

    @commands.command(name='progress')
    async def progress(self, ctx, action: str = None, amount: int = 0):
        """Track progress: !progress log 30 (minutes) | !progress streak | !progress stats"""
        uid = str(ctx.author.id)
        users = self.data.setdefault('users', {})
        user = users.setdefault(uid, {'streak': 0, 'last_seen': None, 'minutes': 0})
        if action == 'log':
            user['minutes'] += amount
            user['last_seen'] = datetime.date.today().isoformat()
            await async_save_json(DATA_PATH, self.data)
            await ctx.send(f'Logged {amount} minutes. Total: {user["minutes"]} min')
            return
        if action == 'streak':
            await ctx.send(f'Current streak: {user.get("streak",0)} days')
            return
        await ctx.send('Usage: progress log <minutes> | progress streak | progress stats')

    @app_commands.command(name='progress', description='Track progress: log minutes or view streak')
    @app_commands.describe(action='log/streak/stats', amount='minutes when logging')
    async def slash_progress(self, interaction: discord.Interaction, action: str = None, amount: int = 0):
        await interaction.response.defer(ephemeral=True)
        uid = str(interaction.user.id)
        users = self.data.setdefault('users', {})
        user = users.setdefault(uid, {'streak': 0, 'last_seen': None, 'minutes': 0})
        if action == 'log':
            user['minutes'] += amount
            user['last_seen'] = datetime.date.today().isoformat()
            await async_save_json(DATA_PATH, self.data)
            await interaction.followup.send(f'Logged {amount} minutes. Total: {user["minutes"]} min', ephemeral=True)
            return
        if action == 'streak':
            await interaction.followup.send(f'Current streak: {user.get("streak",0)} days', ephemeral=True)
            return
        await interaction.followup.send('Usage: /progress action=log|streak|stats amount=<minutes>', ephemeral=True)

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

    @commands.command(name='setreportchan')
    @commands.has_permissions(manage_guild=True)
    async def set_report_channel(self, ctx):
        self.data['report_channel'] = ctx.channel.id
        await async_save_json(DATA_PATH, self.data)
        await ctx.send('This channel is now the weekly report channel.')

    @app_commands.command(name='setreportchan', description='Set this channel as weekly report channel (admin)')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def slash_setreportchan(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.data['report_channel'] = interaction.channel.id
        await async_save_json(DATA_PATH, self.data)
        await interaction.followup.send('This channel is now the weekly report channel.', ephemeral=True)


async def setup(bot: commands.Bot):
    cog = Progress(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
