"""Help cog: lists available commands and descriptions in hybrid form."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='help')
    async def help(self, ctx, cog: Optional[str] = None):
        """Show help for commands. Optionally filter by cog name."""
        # Build embed
        embed = discord.Embed(title="StudyBot Commands", color=discord.Color.blurple())
        if cog:
            # Find commands in specific cog
            cog_obj = self.bot.get_cog(cog.title())
            if not cog_obj:
                await ctx.send(f'Cog not found: {cog}', ephemeral=True)
                return
            cmds = cog_obj.get_commands()
            for c in cmds:
                embed.add_field(name=c.name, value=(c.help or 'No description'), inline=False)
        else:
            # List top-level cogs
            for cog_name, cog_obj in self.bot.cogs.items():
                # Skip internal cogs
                if cog_name.lower() in ['help']:
                    continue
                cmds = [c for c in cog_obj.get_commands() if not c.hidden]
                if not cmds:
                    continue
                desc = []
                for c in cmds:
                    desc.append(f'**{c.name}** — {c.help or ""}')
                embed.add_field(name=cog_name, value='\n'.join(desc)[:1024], inline=False)

        # If invoked as slash, use interaction response if available
        try:
            await ctx.send(embed=embed)
        except Exception:
            # For interaction contexts, fallback
            await ctx.interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))