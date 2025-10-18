# extras.py

"""Extras cog: utility commands like ping, uptime, serverinfo, userinfo, and owner commands"""
import discord
from discord.ext import commands
from discord import app_commands # Ensure app_commands is imported for slash commands
import datetime
import time
import os
import zipfile
import io
from typing import Literal # Used for specific choices in slash commands

class Extras(commands.Cog):
    """Utility commands and slash wrappers"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='ping', help='Shows the bot latency')
    async def ping(self, ctx: commands.Context):
        """Calculates the bot's latency and sends it in an embed."""
        latency = self.bot.latency * 1000
        final_message = f"🏓 Pong! **{latency:.2f}ms** ~ A bot By [Deep Dey](https://www.instagram.com/deepdey.official/)"
        embed = discord.Embed(description=final_message, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='uptime', help='Show bot uptime')
    async def uptime(self, ctx: commands.Context):
        """Shows how long the bot has been online."""
        if not hasattr(self.bot, 'start_time'):
            error_embed = discord.Embed(title="Error", description="Uptime is unknown.", color=discord.Color.red())
            await ctx.send(embed=error_embed)
            return

        delta_seconds = time.time() - self.bot.start_time
        # Format uptime string H:MM:SS
        hours, remainder = divmod(int(delta_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_string = f"{hours}:{minutes:02d}:{seconds:02d}"

        final_message = f"Uptime: **{uptime_string}** ~ A bot By [Deep Dey](https://www.instagram.com/deepdey.official/)"
        embed = discord.Embed(description=final_message, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='serverinfo', help='Show server information')
    @commands.guild_only() # This command can only be used in a server
    async def serverinfo(self, ctx: commands.Context):
        g = ctx.guild
        await ctx.send(f'Server: {g.name} | Members: {g.member_count} | ID: {g.id}')

    @commands.hybrid_command(name='userinfo', help='Show user information')
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        joined_at_str = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "N/A"
        await ctx.send(f'User: {member.display_name} | ID: {member.id} | Joined Server: {joined_at_str}')

    # --- Owner-Only Command ---
    @commands.hybrid_command(name='getfiles', description='Download bot files (owner only).')
    @app_commands.describe(scope='Choose "all" (includes secrets, excludes venv/.git) or "some" (excludes secrets/venv/.git).')
    @commands.is_owner()
    async def getfiles(self, ctx: commands.Context, scope: Literal['all', 'some']):
        """Zips and sends the bot's deployed files based on the specified scope."""

        await ctx.defer(ephemeral=True)

        # Common large/unnecessary exclusions
        common_large_exclusions = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.mypy_cache', '.pytest_cache', 'downloads', 'logs'}

        # Files often containing secrets
        secret_files = {'.env', 'config.json', 'settings.yaml', 'credentials.json', 'token.txt', 'cookies.txt'}

        # Data/cache directories often get large
        data_dirs = {'data', 'cache', 'db', '.db'}

        excluded = set() # Start with an empty set

        if scope == 'some':
            # Exclude secrets, large common folders, and data dirs
            excluded.update(common_large_exclusions)
            excluded.update(secret_files)
            excluded.update(data_dirs)
            zip_type = "safe_small"
            print("Zipping files (excluding secrets, venv, .git, data)...")
        elif scope == 'all':
            # Exclude only the largest common folders, keep secrets and data
            excluded.update(common_large_exclusions)
            # Secrets and data are NOT added to excluded here
            zip_type = "full_large"
            print("Zipping ALL files (excluding venv, .git, but INCLUDING secrets and data)...")
        else:
            await ctx.send("Invalid scope. Use `all` or `some`.", ephemeral=True)
            return

        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Determine project root (assuming cogs folder is one level down)
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(script_dir, '..'))
                print(f"Project root identified as: {project_root}")

                for root, dirs, files in os.walk(project_root, topdown=True):
                    # Check if the current directory itself should be excluded
                    root_relative = os.path.relpath(root, project_root)
                    # Skip if the first part of the relative path is in the exclusion set
                    # (e.g., skips walking into 'data/' if 'data' is excluded)
                    if root_relative != '.' and root_relative.split(os.path.sep)[0] in excluded:
                        dirs[:] = [] # Don't descend into this directory
                        continue

                    # Filter subdirectories to exclude from further walking
                    dirs[:] = [d for d in dirs if d not in excluded]

                    for file in files:
                        # Exclude specific files by name
                        if file in excluded:
                            continue

                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_root)

                        # Skip the zip file itself
                        if file.endswith('.zip'):
                             continue

                        print(f"Adding: {arcname}")
                        zipf.write(file_path, arcname)

            zip_buffer.seek(0)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bot_files_{zip_type}_{timestamp}.zip"

            zip_size_mb = zip_buffer.getbuffer().nbytes / (1024 * 1024)
            print(f"Zip file created: {filename}, Size: {zip_size_mb:.2f} MB")

            if zip_size_mb > 24.5: # Check Discord's limit (leave a small margin)
                 await ctx.send(
                    f"Error: The `{zip_type}` zip file is too large ({zip_size_mb:.2f} MB) for Discord. "
                    f"Current exclusions might not be enough. Excluded items/folders: `{', '.join(excluded)}`.",
                    ephemeral=True
                 )
                 return

            await ctx.send(
                f"Here is the `{zip_type}` zip file of the bot's source code ({zip_size_mb:.2f} MB).",
                file=discord.File(zip_buffer, filename=filename),
                ephemeral=True
            )
        except Exception as e:
            await ctx.send(f"An error occurred while creating the zip file: {type(e).__name__} - {e}", ephemeral=True)
            print(f"Zip creation failed: {e}") # Log detailed error


async def setup(bot: commands.Bot):
    await bot.add_cog(Extras(bot))