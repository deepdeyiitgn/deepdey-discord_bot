"""Reactions cog

This cog handles automatic reactions to messages and commands:
- Adds random reactions to user messages
- Adds loading reaction to commands
- Changes loading reaction to random one after command completes
"""
import discord
from discord.ext import commands
import random

# List of positive/fun emojis for random reactions including animated ones
REACTION_EMOJIS = [
    # Standard emojis
    "👍", "❤️", "🎯", "✨", "🌟", "💫", "🎮", "📚", "🎨", "🎭",
    "🎪", "🎯", "🎲", "🎼", "🎵", "🎶", "🎸", "🎹", "🎺", "🎻",
    "🥁", "🎤", "🎧", "🎭", "🎪", "🎨", "🎯", "🎲", "🎰", "🎳",
    "🤖", "👾", "🎃", "🥳", "🤩", "😎", "🦄", "🌈", "⭐", "💝",
    # Discord Animated Emojis (these will be populated from the bot's guilds)
    "<a:loading:1234567890>",  # Will be replaced with actual emoji IDs
    "<a:boost:1234567891>",
    "<a:verified:1234567892>",
    "<a:typing:1234567893>",
    "<a:party_blob:1234567894>",
    "<a:dance:1234567895>",
    "<a:wave:1234567896>",
    "<a:heart:1234567897>",
    "<a:sparkles:1234567898>",
    "<a:cat_vibe:1234567899>"
]

# Loading emoji for commands in progress (animated)
LOADING_EMOJI = "<a:loading:1234567890>"  # Will be replaced with actual emoji ID

class ReactionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_messages = {}  # Store message IDs that are commands
        self.animated_emojis = []  # Store discovered animated emojis

    async def cog_load(self):
        # Collect animated emojis from all guilds the bot is in
        for guild in self.bot.guilds:
            for emoji in guild.emojis:
                if emoji.animated:
                    self.animated_emojis.append(str(emoji))
        
        # Update emoji lists with discovered animated emojis
        if self.animated_emojis:
            # Replace placeholder loading emoji with a real one
            global LOADING_EMOJI
            for emoji in self.animated_emojis:
                if 'loading' in emoji.lower() or 'typing' in emoji.lower():
                    LOADING_EMOJI = emoji
                    break
            
            # Add discovered animated emojis to reaction pool
            global REACTION_EMOJIS
            REACTION_EMOJIS.extend(self.animated_emojis)
            
            # Remove placeholder animated emojis
            REACTION_EMOJIS = [e for e in REACTION_EMOJIS if not (e.startswith('<a:') and ':123456789' in e)]

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages including our own
        if message.author.bot:
            return

        # For regular messages (non-commands), add a random reaction
        if not message.content.startswith(await self.bot.get_prefix(message)):
            # 30% chance to react to regular messages
            if random.random() < 0.3:
                try:
                    await message.add_reaction(random.choice(REACTION_EMOJIS))
                except discord.errors.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_command(self, ctx):
        try:
            # Add loading reaction when command starts
            await ctx.message.add_reaction(LOADING_EMOJI)
            # Store the message ID to track it
            self.command_messages[ctx.message.id] = True
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        try:
            # Remove loading reaction
            await ctx.message.remove_reaction(LOADING_EMOJI, self.bot.user)
            # Add random success reaction
            await ctx.message.add_reaction(random.choice(REACTION_EMOJIS))
            # Clean up tracking
            self.command_messages.pop(ctx.message.id, None)
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            # Remove loading reaction
            await ctx.message.remove_reaction(LOADING_EMOJI, self.bot.user)
            # Add error reaction
            await ctx.message.add_reaction("❌")
            # Clean up tracking
            self.command_messages.pop(ctx.message.id, None)
        except discord.errors.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(ReactionsCog(bot))