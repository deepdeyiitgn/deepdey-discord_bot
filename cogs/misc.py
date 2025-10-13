import discord
from discord.ext import commands
from discord import app_commands
import datetime
import aiohttp


class Misc(commands.Cog):
    """Small utility commands: time, date, weather (simple via wttr.in)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='time', description='Get current UTC time')
    async def time_cmd(self, ctx: commands.Context):
        """Show current UTC time."""
        now = datetime.datetime.utcnow()
        await ctx.send(f"Current UTC time: {now.strftime('%H:%M:%S')} (UTC)")

    @commands.hybrid_command(name='date', description='Show today\'s date')
    async def date_cmd(self, ctx: commands.Context):
        """Show today's date (UTC)."""
        today = datetime.datetime.utcnow().date()
        await ctx.send(f"Today's date (UTC): {today.isoformat()}")

    @commands.hybrid_command(name='weather', description='Get weather for a location')
    @app_commands.describe(location="Location name, e.g. London or 94016")
    async def weather_cmd(self, ctx: commands.Context, *, location: str = ""):
        """Get simple weather for a location using wttr.in (no API key)."""
        loc = location.strip() or "your location"
        url = f"https://wttr.in/{location.replace(' ', '%20')}?format=3"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=10) as r:
                    text = await r.text()
                    await ctx.send(f"Weather for {loc}: {text}")
        except Exception:
            await ctx.send("Could not fetch weather. Try again later or provide a location.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))
