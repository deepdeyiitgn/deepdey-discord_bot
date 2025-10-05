import discord
from discord.ext import commands
from discord import app_commands
import datetime
import aiohttp


class Misc(commands.Cog):
    """Small utility commands: time, date, weather (prefix + slash)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="time")
    async def time_cmd(self, ctx: commands.Context):
        """Show current UTC time."""
        now = datetime.datetime.utcnow()
        await ctx.send(f"Current UTC time: {now.strftime('%H:%M:%S')} (UTC)")

    @app_commands.command(name="time", description="Show current UTC time")
    async def time_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Current UTC time: {datetime.datetime.utcnow().strftime('%H:%M:%S')} (UTC)")

    @commands.command(name="date")
    async def date_cmd(self, ctx: commands.Context):
        """Show today's date (UTC)."""
        today = datetime.datetime.utcnow().date()
        await ctx.send(f"Today's date (UTC): {today.isoformat()}")

    @app_commands.command(name="date", description="Show today's date (UTC)")
    async def date_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Today's date (UTC): {datetime.datetime.utcnow().date().isoformat()}")

    @commands.command(name="weather")
    async def weather_cmd(self, ctx: commands.Context, *, location: str = ""):
        """Get simple weather for a location using wttr.in (no API key)."""
        loc = location.strip() or "your location"
        url = f"https://wttr.in/{location.replace(' ', '%20')}?format=3"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=10) as r:
                    text = await r.text()
        except Exception:
            await ctx.send("Could not fetch weather. Try again later or provide a location.")
            return
        await ctx.send(f"Weather for {loc}: {text}")

    @app_commands.describe(location="Location name, e.g. London or 94016")
    @app_commands.command(name="weather", description="Get a quick weather line for a location")
    async def weather_slash(self, interaction: discord.Interaction, location: str = ""):
        await interaction.response.defer()
        loc = location.strip() or "your location"
        url = f"https://wttr.in/{location.replace(' ', '%20')}?format=3"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=10) as r:
                    text = await r.text()
        except Exception:
            await interaction.followup.send("Could not fetch weather. Try again later or provide a location.")
            return
        await interaction.followup.send(f"Weather for {loc}: {text}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import aiohttp


class Misc(commands.Cog):
    """Small utility commands: time, date, weather (simple via wttr.in)

    Weather uses wttr.in which provides quick CLI-style weather without API key.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='time')
    async def time_cmd(self, ctx: commands.Context):
        now_utc = datetime.datetime.utcnow()
        await ctx.send(f'UTC time: {now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")}')

    @app_commands.command(name='time')
    async def slash_time(self, interaction: discord.Interaction):
        now_utc = datetime.datetime.utcnow()
        await interaction.response.send_message(f'UTC time: {now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")}', ephemeral=True)

    @commands.command(name='date')
    async def date_cmd(self, ctx: commands.Context):
        today = datetime.date.today()
        await ctx.send(f'Today (local): {today.isoformat()}')

    @app_commands.command(name='date')
    async def slash_date(self, interaction: discord.Interaction):
        today = datetime.date.today()
        await interaction.response.send_message(f'Today (local): {today.isoformat()}', ephemeral=True)

    @commands.command(name='weather')
    async def weather_cmd(self, ctx: commands.Context, *, location: str = 'auto'):
        """Simple weather using wttr.in (no API key). Usage: !weather <city>
        Location 'auto' will attempt to detect from IP of server (may be inaccurate).
        """
        url = f'https://wttr.in/{location}?format=3'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        await ctx.send(text)
                    else:
                        await ctx.send('Weather service unavailable.')
            except Exception:
                await ctx.send('Failed to fetch weather.')

    @app_commands.command(name='weather')
    async def slash_weather(self, interaction: discord.Interaction, location: str = 'auto'):
        await interaction.response.defer(ephemeral=True)
        url = f'https://wttr.in/{location}?format=3'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        await interaction.followup.send(text, ephemeral=True)
                    else:
                        await interaction.followup.send('Weather service unavailable.', ephemeral=True)
            except Exception:
                await interaction.followup.send('Failed to fetch weather.', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))
