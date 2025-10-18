# help.py

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
            # Assuming bot stores prefix in command_prefix
            cp = getattr(self.bot, 'command_prefix', '!')
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
            # Check if signature exists before trying to stringify
            sig = str(cmd.signature) if getattr(cmd, 'signature', None) else ''
        except Exception:
            sig = '' # Fallback if signature fails

        prefix = self._get_prefix()
        usage = f"{prefix}{cmd.name} {sig}".strip()
        # Also show slash command usage if available
        usage_slash = f"/{cmd.name} {sig}".strip()

        value_lines = [f"{help_text}", f"Text: `{usage}`", f"Slash: `{usage_slash}`"]
        return '\n'.join(value_lines)

    def _build_embed_for_cog(self, cog_name: Optional[str] = None) -> discord.Embed:
        embed = discord.Embed(title="📖 StudyBot Help", color=discord.Color.blurple())
        embed.set_footer(text="Use /help [cog] to view specific cog commands.")

        if cog_name:
            cog_obj = self.bot.get_cog(cog_name)
            if not cog_obj:
                embed.description = f"❌ Cog not found: `{cog_name}`"
                return embed

            cmds = [c for c in cog_obj.get_commands() if not c.hidden]
            if not cmds:
                embed.description = f"No visible commands in `{cog_name}`."
                return embed

            embed.title = f"📖 Help: {cog_name} Cog"
            prefix = self._get_prefix()
            for c in cmds:
                embed.add_field(name=f"/{c.name} | {prefix}{c.name}", value=self._format_command(c), inline=False)
            return embed

        # No cog filter: list all cogs and a short summary of their commands
        for name, cog_obj in self.bot.cogs.items():
            if name.lower() == 'help': # Don't show the help cog in the main list
                continue
            cmds = [c for c in cog_obj.get_commands() if not c.hidden]
            if not cmds:
                continue

            lines = []
            for c in cmds:
                # single-line summary per command
                summary = (c.help or 'No description.').splitlines()[0]
                lines.append(f"• `/{c.name}` — {summary}")

            value = '\n'.join(lines)
            embed.add_field(name=f"{name} ({len(cmds)} commands)", value=value[:1024], inline=False)

        return embed

    # This is the async autocomplete function that will be used by the slash command.
    async def _cog_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        bot = interaction.client
        choices: List[app_commands.Choice[str]] = []
        for name in getattr(bot, 'cogs', {}).keys():
            if name.lower() == 'help': # Exclude the Help cog itself
                continue
            # Simple substring matching for autocomplete
            if not current or current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=name))
                if len(choices) >= 25: # Discord limit for choices
                    break
        return choices

    # Pure Slash command with autocomplete for cog names
    @app_commands.command(name='help', description='Shows help for commands, optionally filtered by a cog.')
    @app_commands.describe(cog='The name of the cog to get help for.')
    @app_commands.autocomplete(cog=_cog_autocomplete)
    async def help_slash(self, interaction: discord.Interaction, cog: Optional[str] = None):
        """Shows all commands or those in a specific cog."""
        if cog:
             # Attempt to find the correct capitalization if user input differs
            found_cog_name = None
            for name in self.bot.cogs.keys():
                if name.lower() == cog.lower():
                    found_cog_name = name
                    break
            cog = found_cog_name or cog # Use found name or original if no match

        embed = self._build_embed_for_cog(cog)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    # Ensure any old 'help' command registered by discord.py is removed
    # before adding our custom cog.
    try:
        bot.remove_command('help')
    except Exception:
        pass # Ignore if it doesn't exist
    await bot.add_cog(Help(bot))