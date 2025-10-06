"""Quotes cog: store and serve quotes, scheduled quote sending"""
from discord.ext import commands, tasks
from discord import app_commands
import discord
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import random
import asyncio


DATA_PATH = Path(__file__).parent.parent / 'data' / 'quotes.json'
QUOTES_TXT = Path(__file__).parent.parent / 'data' / 'quotes.txt'


class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = {'quotes': [], 'channel_id': None, 'interval_minutes': 60}
        self.quote_loop.start()

    async def cog_load(self):
        self.data = await async_load_json(DATA_PATH, default=self.data)
        # if there are no quotes in JSON, try to seed from quotes.txt
        if not self.data.get('quotes') and QUOTES_TXT.exists():
            text = QUOTES_TXT.read_text(encoding='utf-8')
            # split by blank lines or lines
            parts = [line.strip() for line in text.splitlines() if line.strip()]
            if parts:
                self.data['quotes'] = parts
                await async_save_json(DATA_PATH, self.data)

    def cog_unload(self):
        self.quote_loop.cancel()

    @tasks.loop(minutes=30)
    async def quote_loop(self):
        await self.bot.wait_until_ready()
        data = await async_load_json(DATA_PATH, default=self.data)
        ch_id = data.get('channel_id')
        if not ch_id:
            return
        channel = self.bot.get_channel(ch_id)
        if not channel:
            return
        quotes = data.get('quotes', [])
        if not quotes:
            return
        try:
            await channel.send(random.choice(quotes))
        except Exception:
            pass

    @commands.hybrid_command(name='addquote', description='Add a quote to the quote bank')
    @app_commands.describe(quote="The quote to add")
    async def add_quote(self, ctx, *, quote: str):
        """Add a quote to the quote bank"""
        data = await async_load_json(DATA_PATH, default=self.data)
        data.setdefault('quotes', []).append(quote)
        await async_save_json(DATA_PATH, data)
        await ctx.send('Quote added.')

    @app_commands.command(name='addquote', description='Add a quote to the quote bank')
    async def slash_addquote(self, interaction: discord.Interaction, quote: str):
        await interaction.response.defer(ephemeral=True)
        data = await async_load_json(DATA_PATH, default=self.data)
        data.setdefault('quotes', []).append(quote)
        await async_save_json(DATA_PATH, data)
        await interaction.followup.send('Quote added.', ephemeral=True)

    @commands.command(name='listquotes')
    async def list_quotes(self, ctx):
        data = await async_load_json(DATA_PATH, default=self.data)
        quotes = data.get('quotes', [])
        if not quotes:
            await ctx.send('No quotes saved.')
            return
        out = '\n'.join(f'{i+1}. {q}' for i, q in enumerate(quotes[:50]))
        await ctx.send(f'Quotes:\n{out}')

    @app_commands.command(name='listquotes', description='List saved quotes (first 50)')
    async def slash_listquotes(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await async_load_json(DATA_PATH, default=self.data)
        quotes = data.get('quotes', [])
        if not quotes:
            await interaction.followup.send('No quotes saved.', ephemeral=True)
            return
        out = '\n'.join(f'{i+1}. {q}' for i, q in enumerate(quotes[:50]))
        await interaction.followup.send(f'Quotes:\n{out}', ephemeral=True)

    @commands.command(name='setquotechannel')
    @commands.has_permissions(manage_guild=True)
    async def set_quote_channel(self, ctx, interval_minutes: int = 60):
        data = await async_load_json(DATA_PATH, default=self.data)
        data['channel_id'] = ctx.channel.id
        data['interval_minutes'] = interval_minutes
        await async_save_json(DATA_PATH, data)
        await ctx.send(f'Quote channel set to this channel every {interval_minutes} minutes.')

    @app_commands.command(name='setquotechannel', description='Set this channel as quote posting channel and interval in minutes')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def slash_setquotechannel(self, interaction: discord.Interaction, interval_minutes: int = 60):
        await interaction.response.defer(ephemeral=True)
        data = await async_load_json(DATA_PATH, default=self.data)
        data['channel_id'] = interaction.channel.id
        data['interval_minutes'] = interval_minutes
        await async_save_json(DATA_PATH, data)
        await interaction.followup.send(f'Quote channel set to this channel every {interval_minutes} minutes.', ephemeral=True)


async def setup(bot: commands.Bot):
    cog = Quotes(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
