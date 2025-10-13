"""Reminders cog: schedule reminders per user with persistence"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from pathlib import Path
from utils.helper import async_load_json, async_save_json, parse_time
import asyncio
import datetime


DATA_PATH = Path(__file__).parent.parent / 'data' / 'reminders.json'


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders = []
        self.check_loop.start()

    async def cog_load(self):
        self.reminders = await async_load_json(DATA_PATH, default=[])

    def cog_unload(self):
        self.check_loop.cancel()

    @tasks.loop(seconds=15)
    async def check_loop(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.utcnow()
        changed = False
        for r in list(self.reminders):
            when = datetime.datetime.fromisoformat(r['when'])
            if now >= when:
                try:
                    ch = self.bot.get_channel(r['channel_id'])
                    await ch.send(f"Reminder for <@{r['user_id']}>: {r['message']}")
                except Exception:
                    pass
                self.reminders.remove(r)
                changed = True
        if changed:
            await async_save_json(DATA_PATH, self.reminders)

    @commands.hybrid_command(name='remind')
    async def remind(self, ctx, timestr: str, *, message: str):
        """Create a reminder: !remind 10m Take a break"""
        try:
            seconds = parse_time(timestr)
        except ValueError:
            await ctx.send('Invalid time. Use formats like 10m, 2h, 1d, 30s')
            return
        when = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        r = {
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id,
            'when': when.isoformat(),
            'message': message,
        }
        self.reminders.append(r)
        await async_save_json(DATA_PATH, self.reminders)
        await ctx.send(f'Reminder set for {timestr} from now.')

    @commands.hybrid_command(name='listreminders')
    async def list_reminders(self, ctx):
        user = ctx.author.id
        items = [r for r in self.reminders if r['user_id'] == user]
        if not items:
            await ctx.send('You have no reminders.')
            return
        out = []
        for i, r in enumerate(items, start=1):
            out.append(f"{i}. At {r['when']}: {r['message']}")
        await ctx.send('\n'.join(out))




async def setup(bot: commands.Bot):
    cog = Reminders(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
