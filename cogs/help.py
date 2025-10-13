"""Help cog: lists available commands and descriptions in hybrid and slash form.

Features:
- `/help` — lists all cogs and their commands
- `/help <cog>` — shows commands for a specific cog (cog name autocomplete)

Each command entry includes: short description, usage, and a simple example.
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_prefix(self) -> str:
        # Try to infer a usable prefix for examples
        prefix = '!'
        try:
            cp = getattr(self.bot, 'command_prefix', None)
            if isinstance(cp, str):
                prefix = cp
            elif isinstance(cp, (list, tuple)) and cp:
                prefix = cp[0]
        except Exception:
            pass
        return prefix

    def _format_command(self, cmd: commands.Command) -> str:
        help_text = cmd.help or 'No description available.'
        # Get signature (params) where available
        sig = ''
        try:
            sig = str(cmd.signature) if getattr(cmd, 'signature', None) else ''
        except Exception:
            sig = ''

        prefix = self._get_prefix()
        usage = f"{prefix}{cmd.name} {sig}".strip()
        example = usage
        # Build a short block with description, usage and example
        value_lines = [f"{help_text}", f"Usage: `{usage}`", f"Example: `{example}`"]
        return '\n'.join(value_lines)

    def _build_embed_for_cog(self, cog_name: Optional[str] = None) -> discord.Embed:
        embed = discord.Embed(title="StudyBot Help", color=discord.Color.blurple())
        embed.set_footer(text="Use /help <cog> to view commands in a specific cog")

        if cog_name:
            cog_obj = self.bot.get_cog(cog_name)
            if not cog_obj:
                embed.description = f"Cog not found: {cog_name}"
                return embed

            cmds = [c for c in cog_obj.get_commands() if not c.hidden]
            if not cmds:
                embed.description = f"No visible commands in {cog_name}."
                return embed

            for c in cmds:
                embed.add_field(name=c.name, value=self._format_command(c), inline=False)
            return embed

        # No cog filter: list all cogs and a short summary of their commands
        for name, cog_obj in self.bot.cogs.items():
            if name.lower() == 'help':
                continue
            cmds = [c for c in cog_obj.get_commands() if not c.hidden]
            if not cmds:
                continue
            lines = []
            for c in cmds:
                # single-line summary per command
                lines.append(f"**{c.name}** — { (c.help or '').splitlines()[0] }")
            value = '\n'.join(lines)
            # ensure field length limit
            embed.add_field(name=name, value=value[:1024], inline=False)

        return embed

    # Hybrid text command (supports both message and slash invocation)
    @commands.hybrid_command(name='help', with_app_command=False)
    async def help(self, ctx: commands.Context, cog: Optional[str] = None):
        """Show help for commands. Optionally filter by cog name."""
        # allow user to pass cog case-insensitively
        if cog:
            cog = cog.title()
        embed = self._build_embed_for_cog(cog)

        # Send via interaction response when available
        if getattr(ctx, 'interaction', None) and ctx.interaction is not None:
            try:
                await ctx.interaction.response.send_message(embed=embed)
            except Exception:
                # fallback to context send
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    # Slash command variant with autocomplete for cog names
    @app_commands.command(name='help', description='Show help for all cogs or a specific cog')
    @app_commands.describe(cog='Cog name to filter (optional)')
    @app_commands.autocomplete(cog=lambda inter, cur: Help._cog_autocomplete_static(inter, cur))
    async def help_slash(self, interaction: discord.Interaction, cog: Optional[str] = None):
        """Slash command entrypoint; delegates to same formatter."""
        if cog:
            cog = cog.title()
        embed = self._build_embed_for_cog(cog)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @staticmethod
    async def _cog_autocomplete_static(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        # Return matching cog names (exclude Help itself)
        bot = interaction.client
        choices: List[app_commands.Choice[str]] = []
        for name in getattr(bot, 'cogs', {}).keys():
            if name.lower() == 'help':
                continue
            if not current or name.lower().startswith(current.lower()):
                choices.append(app_commands.Choice(name=name, value=name))
                if len(choices) >= 25:
                    break
        return choices


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
