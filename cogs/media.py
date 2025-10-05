"""Media/File Manager Cog

Features
- Lists files in the `media/` folder (and subfolders)
- Sends specified file to a channel (`!sendfile <filename> <#channel>`)
- Slash command `/sendfile` with channel option
- Optionally send a random file (`!sendrandom <#channel>`)
- Only users with manage_guild or administrator permissions can send files
- Uses non-blocking file reads by delegating to an executor
- Supports files up to 5GB in size using chunked uploads

Usage:
 - Prefix: !listfiles
 - Prefix: !sendfile pdf/notes.pdf #general
 - Slash: /sendfile filename:pdf/notes.pdf channel:#general

This cog is intentionally generic and future-proof: it doesn't hard-code
file types or subfolders.
"""
from discord.ext import commands
import discord
from discord import app_commands, File
import io
from pathlib import Path
import asyncio
import os
from typing import Optional
import random
import logging
import math
from utils.db import DB
import aiohttp

# Maximum file size (5GB)
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes
CHUNK_SIZE = 25 * 1024 * 1024  # 25MB chunks


LOGGER = logging.getLogger('studybot.media')
MEDIA_ROOT = Path(__file__).parent.parent / 'media'


class MediaManager(commands.Cog):
    """Cog to manage media files stored in a `media/` folder."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    async def _list_files(self) -> list:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: [p.relative_to(MEDIA_ROOT).as_posix() for p in MEDIA_ROOT.rglob('*') if p.is_file()])

    async def _read_file_for_send(self, relative_path: str) -> Optional[tuple[Path, int]]:
        # Validate path to avoid traversal and confirm the file exists
        target = (MEDIA_ROOT / relative_path).resolve()
        try:
            # Ensure target is inside MEDIA_ROOT
            if not str(target).startswith(str(MEDIA_ROOT.resolve())):
                return None
            if not target.exists() or not target.is_file():
                return None
            size = target.stat().st_size
            if size > MAX_FILE_SIZE:
                return None
            return (target, size)
        except Exception:
            return None

    async def _send_large_file(self, channel: discord.TextChannel, file_path: Path, progress_msg=None):
        """Send a large file in chunks"""
        file_size = file_path.stat().st_size
        chunks = math.ceil(file_size / CHUNK_SIZE)
        
        async def update_progress(current_chunk):
            if progress_msg:
                progress = (current_chunk / chunks) * 100
                await progress_msg.edit(content=f"Uploading: {progress:.1f}% complete...")

        try:
            with open(file_path, 'rb') as f:
                for i in range(chunks):
                    chunk = f.read(CHUNK_SIZE)
                    chunk_file = discord.File(io.BytesIO(chunk), filename=f"{file_path.name}.part{i+1}")
                    await channel.send(file=chunk_file)
                    await update_progress(i + 1)
                
                if progress_msg:
                    await progress_msg.edit(content="Upload complete!")
                return True
        except Exception as e:
            LOGGER.exception('Failed to send large file')
            if progress_msg:
                await progress_msg.edit(content=f"Failed to upload: {str(e)}")
            return False

    async def _get_allowed_role(self, guild_id: int) -> Optional[int]:
        key = f'media_allowed_role_{guild_id}'
        val = await DB.get_kv(key)
        return int(val) if val else None

    async def _check_allowed(self, member: discord.Member) -> bool:
        # Admins are allowed by default
        if member.guild_permissions.manage_guild:
            return True
        rid = await self._get_allowed_role(member.guild.id)
        if not rid:
            return False
        return any(r.id == rid for r in member.roles)

    @commands.command(name='listfiles', help='List available files in media folder')
    async def listfiles(self, ctx: commands.Context):
        files = await self._list_files()
        if not files:
            await ctx.send('No files in media folder.')
            return
        # Send as codeblock to avoid huge embeds; if too long, upload as file
        out = '\n'.join(files)
        if len(out) > 1900:
            await ctx.send(file=File(fp=io.BytesIO(out.encode('utf-8')), filename='media_list.txt'))
            return
        await ctx.send(f'Files:\n{out}')

    @commands.hybrid_command(name='setmediarole', description='Set a role allowed to upload/send media')
    @app_commands.describe(
        role='The role to allow media management access'
    )
    @commands.has_permissions(manage_guild=True)
    async def setmediarole(self, ctx, role: discord.Role):
        await DB.set_kv(f'media_allowed_role_{ctx.guild.id}', str(role.id))
        await ctx.send(f'Set allowed media role to {role.name}')

    @commands.hybrid_command(name='upload', description='Upload a file to the server media folder')
    async def upload(self, ctx):
        """Upload a file to the media folder (Admin or allowed role only)"""
        # Check permissions
        allowed = await self._check_allowed(ctx.author)
        if not allowed:
            await ctx.send('You are not allowed to upload files.')
            return
            
        # Handle both prefix and slash command cases
        attachments = ctx.message.attachments if hasattr(ctx, 'message') else []
        if not attachments:
            await ctx.send('Attach a file to upload using the prefix (!upload) command.')
            return
            
        # Process each attachment
        for att in attachments:
            filename = att.filename
            save_path = MEDIA_ROOT / filename.replace('..', '')
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                data = await att.read()
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, save_path.write_bytes, data)
                await ctx.send(f'✅ Successfully uploaded {filename}')
            except Exception as e:
                LOGGER.exception('Failed to upload')
                await ctx.send(f'❌ Failed to upload {filename}: {e}')

    @app_commands.command(name='listfiles', description='List files in media folder')
    async def slash_listfiles(self, interaction: discord.Interaction):
        files = await self._list_files()
        if not files:
            await interaction.response.send_message('No files in media folder.', ephemeral=True)
            return
        out = '\n'.join(files[:200])
        await interaction.response.send_message(f'Files (first 200):\n{out}', ephemeral=True)

    @commands.hybrid_command(name='sendfile', description='Send a file from media folder to a channel')
    @app_commands.describe(
        filename='Relative file path inside media/',
        channel='Target channel to send the file to'
    )
    @commands.has_permissions(manage_guild=True)
    async def sendfile(self, ctx, filename: str, channel: discord.TextChannel):
        """Send a file from the media folder to a specific channel (Admin only)"""
        await ctx.defer()
        
        result = await self._read_file_for_send(filename)
        if not result:
            await ctx.send('❌ File not found or invalid path.')
            return
            
        target, size = result
        progress_msg = None
        
        try:
            if size > 8 * 1024 * 1024:  # If file is larger than 8MB
                progress_msg = await ctx.send("📤 Starting large file upload...")
                success = await self._send_large_file(channel, target, progress_msg)
                if success:
                    await ctx.send(f'✅ Sent {filename} to {channel.mention} in chunks')
            else:
                await channel.send(file=File(str(target), filename=target.name))
                await ctx.send(f'✅ Sent {filename} to {channel.mention}')
        except Exception as e:
            LOGGER.exception('Failed to send file')
            await ctx.send(f'❌ Failed to send file: {e}')
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)
            return
        
        await interaction.response.defer()
        result = await self._read_file_for_send(filename)
        if not result:
            await interaction.followup.send('File not found or invalid path.', ephemeral=True)
            return
            
        target, size = result
        progress_msg = None
        
        try:
            if size > 8 * 1024 * 1024:  # If file is larger than 8MB
                progress_msg = await interaction.followup.send("Starting large file upload...", wait=True)
                success = await self._send_large_file(channel, target, progress_msg)
                if success:
                    await interaction.followup.send(f'Sent {filename} to {channel.mention} in chunks', ephemeral=True)
            else:
                await channel.send(file=File(str(target), filename=target.name))
                await interaction.followup.send(f'Sent {filename} to {channel.mention}', ephemeral=True)
        except Exception as e:
            LOGGER.exception('Failed to send file (slash)')
            await interaction.followup.send(f'Failed to send file: {e}', ephemeral=True)

    @commands.hybrid_command(name='sendrandom', description='Send a random file from media folder')
    @app_commands.describe(
        channel='Target channel to send the random file to'
    )
    @commands.has_permissions(manage_guild=True)
    async def sendrandom(self, ctx, channel: discord.TextChannel):
        """Send a random file from the media folder to a channel (Admin only)"""
        await ctx.defer()
        
        files = await self._list_files()
        if not files:
            await ctx.send('❌ No files available to send.')
            return
            
        filename = random.choice(files)
        result = await self._read_file_for_send(filename)
        if not result:
            await ctx.send('❌ Failed to access the chosen file.')
            return
            
        target, size = result
        try:
            if size > 8 * 1024 * 1024:  # If file is larger than 8MB
                progress_msg = await ctx.send("📤 Starting large file upload...")
                success = await self._send_large_file(channel, target, progress_msg)
                if success:
                    await ctx.send(f'✅ Sent random file {filename} to {channel.mention} in chunks')
            else:
                await channel.send(file=File(str(target), filename=target.name))
                await ctx.send(f'✅ Sent random file {filename} to {channel.mention}')
        except Exception as e:
            LOGGER.exception('Failed to send random file')
            await ctx.send(f'❌ Failed to send file: {e}')
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)
            return
        await interaction.response.defer()
        files = await self._list_files()
        if not files:
            await interaction.followup.send('No files to send.', ephemeral=True)
            return
        filename = random.choice(files)
        target = await self._read_file_for_send(filename)
        if not target:
            await interaction.followup.send('Failed to find chosen file.', ephemeral=True)
            return
        try:
            await channel.send(file=File(str(target), filename=target.name))
            await interaction.followup.send(f'Sent {filename} to {channel.mention}', ephemeral=True)
        except Exception as e:
            LOGGER.exception('Failed to send random file (slash)')
            await interaction.followup.send(f'Failed to send file: {e}', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MediaManager(bot))
