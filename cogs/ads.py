import discord
from discord.ext import commands, tasks
from discord import app_commands
from utils.db import DB
from pathlib import Path
from typing import Optional
import random

BASE_DIR = Path(__file__).parent.parent

STUDY_TIPS = [
    {
        'title': '🎯 Pomodoro Technique',
        'description': 'Study for 25 minutes, take a 5-minute break. After 4 rounds, take a longer 15-30 minute break.',
        'link': 'https://todoist.com/productivity-methods/pomodoro-technique'
    },
    {
        'title': '📚 Active Recall',
        'description': 'Test yourself frequently. Create flashcards, practice problems, or teach concepts to others.',
        'link': 'https://www.youtube.com/watch?v=ukLnPbIffxE'
    },
    {
        'title': '🧠 Mind Mapping',
        'description': 'Create visual connections between related concepts to better understand and remember them.',
        'link': 'https://www.mindmeister.com/blog/mind-mapping-guide/'
    },
    {
        'title': '⏰ Spaced Repetition',
        'description': 'Review material at increasing intervals to optimize long-term retention.',
        'link': 'https://ncase.me/remember/'
    },
    {
        'title': '📝 Cornell Note-Taking',
        'description': 'Divide your notes into questions, notes, and summary sections for better organization.',
        'link': 'http://lsc.cornell.edu/how-to-study/taking-notes/cornell-note-taking-system/'
    }
]

PROMOTIONAL_AD = (
    "Sponsored by Deep Dey - The FUTURE IITIAN 🎯\n"
    "YouTube: https://www.youtube.com/channel/UCrh1Mx5CTTbbkgW5O6iS2Tw/\n"
    "Website: https://www.deepdeyiitk.com\n"
    "Apps: https://apps.deepdeyiitk.com\n"
    "Instagram: https://www.instagram.com/deepdey.official/\n"
    "Discord: @deepdey.official\n"
    "Owner: Deep Dey"
)

DEFAULT_AD = PROMOTIONAL_AD  # For backwards compatibility


class AdsCog(commands.Cog):
    """Simple ads injection: after N bot responses in a channel, send an ad message.

    Settings are persisted per-guild using utils.db.DB.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DB()
        # in-memory counters: {(guild_id, channel_id): count}
        self.counters = {}
        # fallback store used if aiosqlite/DB is unavailable
        self._fallback_store = {}
        self._db_available = True

    async def cog_load(self):
        try:
            await self.db.init_db()
            self._db_available = True
        except ImportError:
            # aiosqlite isn't installed; use in-memory fallback but don't fail cog load
            self._db_available = False
        except Exception:
            # other DB init errors: mark unavailable and continue
            self._db_available = False

    async def cog_unload(self):
        await self.db.close_db()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore bot messages and DMs
        if message.author.bot:
            return
        if not message.guild:
            return
        # check if message is a bot response (we'll treat bot messages as responses)
        # Count bot messages in channels; when reaching threshold, send ad
        # This listener increases counter when the bot itself sends a message
        if message.author == self.bot.user:
            key = (message.guild.id, message.channel.id)
            self.counters[key] = self.counters.get(key, 0) + 1
            # fetch threshold from DB; default 2 (user requested 2-3 responses)
            thresh_key = f"ads_threshold_{message.guild.id}"
            raw = await self._get_kv(thresh_key)
            try:
                threshold = int(raw) if raw is not None else 2
            except Exception:
                threshold = 2
            # check enabled flag (default True)
            enabled_key = f"ads_enabled_{message.guild.id}"
            raw_enabled = await self._get_kv(enabled_key)
            enabled = False if raw_enabled == "0" else True
            if not enabled:
                return
            if self.counters[key] >= threshold:
                # send ad (alternating between study tips and promotional)
                is_promo = self.counters.get((message.guild.id, 'promo'), True)
                
                if is_promo:
                    # Send promotional ad
                    ad_text = await self.db.get_kv(f"ads_text_{message.guild.id}")
                    if not ad_text:
                        ad_text = PROMOTIONAL_AD
                    try:
                        # Create promotional embed
                        embed = discord.Embed(
                            title="🎯 Study Resources",
                            description="Join our learning community!",
                            color=discord.Color.gold(),
                            timestamp=message.created_at
                        )
                        
                        # Parse promotional content
                        lines = ad_text.split('\n')
                        for line in lines:
                            if ':' in line:
                                name, value = line.split(':', 1)
                                embed.add_field(name=name.strip(), value=value.strip(), inline=False)
                            else:
                                embed.description += f"\n{line}"
                                
                        embed.set_footer(text="Sponsored Message")
                        await message.channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending ad: {e}")
                        pass
                else:
                    # Send study tip
                    tip = random.choice(STUDY_TIPS)
                    embed = discord.Embed(
                        title=tip['title'],
                        description=tip['description'],
                        color=discord.Color.blue(),
                        url=tip['link']
                    )
                    embed.set_footer(text="Click the title for more info!")
                    try:
                        await message.channel.send(embed=embed)
                    except Exception:
                        pass
                
                # Toggle promotion flag and reset counter
                self.counters[(message.guild.id, 'promo')] = not is_promo
                self.counters[key] = 0

    async def _get_kv(self, key: str):
        """Get a value from DB or fallback store."""
        if self._db_available:
            try:
                return await self.db.get_kv(key)
            except Exception:
                # fallthrough to fallback
                pass
        return self._fallback_store.get(key)

    async def _set_kv(self, key: str, value: str):
        """Set a value in DB or fallback store."""
        if self._db_available:
            try:
                await self.db.set_kv(key, value)
            except Exception:
                self._fallback_store[key] = value
        else:
            self._fallback_store[key] = value

    @commands.hybrid_group(name="ads", invoke_without_command=True)
    async def ads_group(self, ctx: commands.Context):
        """Manage advertisement settings"""
        await ctx.send("Use subcommands: enable, disable, threshold, preview")
        
    @ads_group.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def enable_ads(self, ctx: commands.Context):
        """Enable ads in this server"""
        await self._set_kv(f"ads_enabled_{ctx.guild.id}", "1")
        await ctx.send("✅ Ads enabled!")
        
    @ads_group.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def disable_ads(self, ctx: commands.Context):
        """Disable ads in this server"""
        await self._set_kv(f"ads_enabled_{ctx.guild.id}", "0")
        await ctx.send("❌ Ads disabled!")
        
    @ads_group.command(name="threshold")
    @commands.has_permissions(manage_guild=True)
    async def set_threshold(self, ctx: commands.Context, messages: int):
        """Set how many bot messages before showing an ad"""
        if messages < 1:
            await ctx.send("❌ Threshold must be at least 1!")
            return
        await self._set_kv(f"ads_threshold_{ctx.guild.id}", str(messages))
        await ctx.send(f"✅ Ad threshold set to {messages} messages!")
        
    @ads_group.command(name="preview")
    async def preview_ads(self, ctx: commands.Context):
        """Preview both promotional and study tip ads"""
        # Show promotional ad
        ad_text = await self._get_kv(f"ads_text_{ctx.guild.id}")
        if not ad_text:
            ad_text = PROMOTIONAL_AD
        await ctx.send("📣 Promotional Ad Preview:")
        await ctx.send(ad_text)
        
        # Show random study tip
        tip = random.choice(STUDY_TIPS)
        embed = discord.Embed(
            title=tip['title'],
            description=tip['description'],
            color=discord.Color.blue(),
            url=tip['link']
        )
        embed.set_footer(text="Click the title for more info!")
        await ctx.send("📚 Study Tip Preview:", embed=embed)
        
    async def _set_kv(self, key: str, value: str):
        """Set a value in DB or fallback store."""
        if self._db_available:
            try:
                await self.db.set_kv(key, value)
            except Exception:
                # fall back to memory
                self._fallback_store[key] = value
        else:
            self._fallback_store[key] = value

    @commands.hybrid_group(name="ads", description="Manage advertisement settings", fallback="show")
    @commands.has_guild_permissions(administrator=True)
    async def ads(self, ctx):
        """Show current ads settings"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            if not interaction.guild:
                await interaction.response.send_message('This command works in servers only.', ephemeral=True)
                return
            thresh = await self._get_kv(f"ads_threshold_{interaction.guild.id}") or "2"
            text = await self._get_kv(f"ads_text_{interaction.guild.id}") or DEFAULT_AD
            await interaction.response.send_message(f"Ads threshold: {thresh}\nAds text:\n{text}")
        else:
            thresh_key = f"ads_threshold_{ctx.guild.id}"
            text_key = f"ads_text_{ctx.guild.id}"
            threshold = await self._get_kv(thresh_key) or "3"
            text = await self._get_kv(text_key) or DEFAULT_AD
            await ctx.send(f"Ads threshold: {threshold}\nAds text:\n{text}")

    @ads.command(name="setthreshold", description="Set number of responses before ad")
    @commands.has_guild_permissions(administrator=True)
    @app_commands.describe(count="Number of bot responses before showing an ad")
    async def setthreshold(self, ctx, count: int):
        """Set after how many bot responses an ad is posted (default 3)"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await self._set_kv(f"ads_threshold_{interaction.guild.id}", str(count))
            await interaction.response.send_message(f"Ads threshold set to {count} bot responses.")
        else:
            await self._set_kv(f"ads_threshold_{ctx.guild.id}", str(count))
            await ctx.send(f"Ads threshold set to {count} bot responses.")

    @ads.command(name="settext", description="Set the advertisement text")
    @commands.has_guild_permissions(administrator=True)
    @app_commands.describe(text="The text to show as advertisement")
    async def settext(self, ctx, *, text: str):
        """Set the ads text sent by the bot"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await self._set_kv(f"ads_text_{interaction.guild.id}", text)
            await interaction.response.send_message("Ads text updated.")
        else:
            await self._set_kv(f"ads_text_{ctx.guild.id}", text)
            await ctx.send("Ads text updated.")

    @ads.command(name="enable", description="Enable advertisements")
    @commands.has_guild_permissions(administrator=True)
    async def enable(self, ctx):
        """Enable advertisements for this guild"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await self._set_kv(f"ads_enabled_{interaction.guild.id}", "1")
            await interaction.response.send_message("Ads enabled for this guild.")
        else:
            await self._set_kv(f"ads_enabled_{ctx.guild.id}", "1")
            await ctx.send("Ads enabled for this guild.")

    @ads.command(name="disable", description="Disable advertisements")
    @commands.has_guild_permissions(administrator=True)
    async def disable(self, ctx):
        """Disable advertisements for this guild"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await self._set_kv(f"ads_enabled_{interaction.guild.id}", "0")
            await interaction.response.send_message("Ads disabled for this guild.")
        else:
            await self._set_kv(f"ads_enabled_{ctx.guild.id}", "0")
            await ctx.send("Ads disabled for this guild.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AdsCog(bot))
