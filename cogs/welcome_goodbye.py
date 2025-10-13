"""Welcome and Goodbye message cog

Features:
- Welcome messages when bot joins a server
- Welcome messages when new members join
- Goodbye messages when members leave/are kicked/banned
- Includes sponsor information and study tips
"""
import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
import random
from cogs.ads import PROMOTIONAL_AD, STUDY_TIPS

class WelcomeGoodbye(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_welcome_embed(self, member: discord.Member) -> discord.Embed:
        """Create a welcome embed with sponsor info"""
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}! 👋",
            description=(
                f"Hey {member.mention}! Welcome to our study community!\n\n"
                f"🌟 Get started with a random study tip:\n"
                f"{random.choice(STUDY_TIPS)['description']}\n\n"
                f"Use `/help` or `!help` to see all available commands."
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="📚 Quick Start",
            value=(
                "• Use `/suggest` for AI study help\n"
                "• Track progress with `/streak`\n"
                "• Join study sessions with others\n"
                "• Set reminders with `/remind`"
            ),
            inline=False
        )
        embed.add_field(
            name="🎯 Sponsored By",
            value=PROMOTIONAL_AD,
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed

    async def create_goodbye_embed(self, member: discord.Member, reason: str = None) -> discord.Embed:
        """Create a goodbye embed with sponsor info"""
        embed = discord.Embed(
            title=f"Goodbye from {member.guild.name} 👋",
            description=(
                f"We'll miss you, {member.mention}!\n\n"
                f"Remember to keep up your studies! Here's a parting study tip:\n"
                f"{random.choice(STUDY_TIPS)['description']}"
            ),
            color=discord.Color.blue()
        )
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
            
        embed.add_field(
            name="🎯 Check Out Our Resources",
            value=PROMOTIONAL_AD,
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Send welcome message when bot joins a new server"""
        # Find the system channel or first text channel we can send to
        channel = guild.system_channel or next(
            (ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages),
            None
        )
        if not channel:
            return
            
        embed = discord.Embed(
            title="Thanks for adding StudyBot! 📚",
            description=(
                "I'm here to help make your studies more effective and fun!\n\n"
                "🔹 AI-powered study assistance\n"
                "🔹 Progress tracking and reminders\n"
                "🔹 Interactive study sessions\n"
                "🔹 Games and challenges\n\n"
                "Use `/help` or `!help` to see all commands."
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="🎯 Sponsored By",
            value=PROMOTIONAL_AD,
            inline=False
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Welcome new members"""
        # Find appropriate channel to send welcome message
        channel = member.guild.system_channel or next(
            (ch for ch in member.guild.text_channels if ch.permissions_for(member.guild.me).send_messages),
            None
        )
        if not channel:
            return

        embed = await self.create_welcome_embed(member)
        await channel.send(embed=embed)
        
        # Try to send a DM to the new member
        try:
            personal_embed = discord.Embed(
                title=f"Welcome to {member.guild.name}! 🌟",
                description=(
                    f"Thanks for joining! I'm StudyBot, your AI study companion.\n\n"
                    f"Here's a helpful study tip to get you started:\n"
                    f"{random.choice(STUDY_TIPS)['description']}\n\n"
                    f"Use `/help` or `!help` in the server to see what I can do!"
                ),
                color=discord.Color.green()
            )
            personal_embed.add_field(
                name="🎯 Check Out Our Resources",
                value=PROMOTIONAL_AD,
                inline=False
            )
            await member.send(embed=personal_embed)
        except discord.Forbidden:
            pass  # Can't send DM, that's ok

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaves/kicks/bans"""
        # Find appropriate channel
        channel = member.guild.system_channel or next(
            (ch for ch in member.guild.text_channels if ch.permissions_for(member.guild.me).send_messages),
            None
        )
        if not channel:
            return

        embed = await self.create_goodbye_embed(member)
        await channel.send(embed=embed)
        
        # Try to send a goodbye DM
        try:
            personal_embed = discord.Embed(
                title=f"Goodbye from {member.guild.name} 👋",
                description=(
                    f"We're sad to see you go! Remember to keep up your studies.\n\n"
                    f"Here's one last study tip from me:\n"
                    f"{random.choice(STUDY_TIPS)['description']}"
                ),
                color=discord.Color.blue()
            )
            personal_embed.add_field(
                name="🎯 Stay Connected",
                value=PROMOTIONAL_AD,
                inline=False
            )
            await member.send(embed=personal_embed)
        except discord.Forbidden:
            pass  # Can't send DM, that's ok

async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeGoodbye(bot))