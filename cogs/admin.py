"""Admin module for moderation commands.

Commands are available in both prefix (!) and slash (/) versions.
All admin commands require appropriate permissions.
"""
import discord
from discord.ext import commands
try:
    from discord import app_commands
except Exception:
    # Fallback shim for environments where discord.app_commands fails to import
    class _AppCommandsShim:
        def describe(self, **kwargs):
            def decorator(func):
                return func
            return decorator

    app_commands = _AppCommandsShim()
from discord.ui import View, Button
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import asyncio
from typing import Optional
import logging
import sys
import datetime


# Ensure logs directory exists before creating handlers
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Configure logging with UTF-8 encoding and add file/terminal handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_DIR / 'mod_actions.log'), 'a', encoding='utf-8')
    ]
)

logger = logging.getLogger('admin')
logger.setLevel(logging.INFO)

# File handler for audit log (explicitly add to logger so we can customize formatter)
audit_handler = logging.FileHandler(str(LOG_DIR / 'mod_actions.log'), 'a', encoding='utf-8')
audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(audit_handler)

# Terminal handler with colored output
terminal_handler = logging.StreamHandler()
terminal_handler.setFormatter(logging.Formatter('\033[1;33m%(asctime)s - %(levelname)s - %(message)s\033[0m'))
logger.addHandler(terminal_handler)


class ConfirmView(View):
    def __init__(self, author_id: int, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.value = True
        self.stop()
        await interaction.response.edit_message(content='Confirmed', view=None)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.value = False
        self.stop()
        await interaction.response.edit_message(content='Cancelled', view=None)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_action = None
        self.action_timeout = 300  # 5 minutes

    async def log_action(self, action: str, moderator: str, target: str, reason: str = None, success: bool = True):
        """Log moderation action to both file and terminal"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅ SUCCESS" if success else "❌ FAILED"
        
        log_msg = (
            f"[{status}] {action}\n"
            f"Moderator: {moderator}\n"
            f"Target: {target}\n"
            f"Reason: {reason or 'No reason provided'}\n"
            f"Time: {timestamp}\n"
            f"{'-'*50}"
        )
        
        # Log to file
        logger.info(log_msg)
        
        # Store last action for terminal verification
        self.last_action = {
            'action': action,
            'moderator': moderator,
            'target': target,
            'reason': reason,
            'timestamp': timestamp
        }
        
        # Also attempt to post a short summary to the bot's configured log channel (if available)
        try:
            log_channel_id = getattr(self.bot, 'LOG_CHANNEL_ID', None)
            if log_channel_id:
                chan = self.bot.get_channel(int(log_channel_id))
                if chan is not None:
                    summary = f"[{ 'SUCCESS' if success else 'FAILED' }] {action} | Moderator: {moderator} | Target: {target} | Reason: {reason or 'No reason'}"
                    # Fire-and-forget send; don't block logging on failures
                    try:
                        await chan.send(summary)
                    except Exception:
                        pass
        except Exception:
            # keep logging robust; ignore any errors when trying to post to discord
            pass

        return log_msg

    async def verify_terminal(self, ctx_or_interaction) -> bool:
        """Ask for terminal verification of the last mod action"""
        if not self.last_action:
            return False
            
        # Check if the action is still valid (within timeout)
        action_time = datetime.datetime.strptime(self.last_action['timestamp'], "%Y-%m-%d %H:%M:%S")
        if (datetime.datetime.now() - action_time).total_seconds() > self.action_timeout:
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.followup.send("⚠️ Action timed out! Please try again.", ephemeral=True)
            else:
                await ctx_or_interaction.send("⚠️ Action timed out! Please try again.")
            return False
            
        # Format verification message
        verify_msg = (
            "🔐 **Terminal Verification Required**\n"
            f"Action: {self.last_action['action']}\n"
            f"Moderator: {self.last_action['moderator']}\n"
            f"Target: {self.last_action['target']}\n"
            f"Reason: {self.last_action['reason'] or 'No reason provided'}\n\n"
            "Please check the terminal and confirm this action is authorized."
        )
        
        # Send verification request
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.followup.send(verify_msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(verify_msg)
            
        return True

    async def _confirm_interactive(self, ctx_or_interaction, prompt: str) -> bool:
        """Show an ephemeral confirm/cancel UI to the command invoker and return True if confirmed."""
        if isinstance(ctx_or_interaction, commands.Context):
            view = ConfirmView(ctx_or_interaction.author.id)
            await ctx_or_interaction.send(prompt, view=view, ephemeral=False)
            await view.wait()
            return bool(view.value)
        else:
            interaction: discord.Interaction = ctx_or_interaction
            view = ConfirmView(interaction.user.id)
            await interaction.response.send_message(prompt, view=view, ephemeral=True)
            await view.wait()
            return bool(view.value)

    @commands.hybrid_command(name='kick', description='Kick a member from the server')
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="The reason for kicking")
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member (interactive confirmation)"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            # First UI confirmation
            confirmed = await self._confirm_interactive(interaction, f'Confirm kick {member}?')
            if not confirmed:
                await interaction.followup.send('Action cancelled.', ephemeral=True)
                return

            # Log attempt and get terminal verification
            await self.log_action(
                action="KICK",
                moderator=str(interaction.user),
                target=str(member),
                reason=reason
            )
            
            verified = await self.verify_terminal(interaction)
            if not verified:
                return
                
            try:
                await member.kick(reason=reason)
                await self.log_action(
                    action="KICK",
                    moderator=str(interaction.user),
                    target=str(member),
                    reason=reason,
                    success=True
                )
                await interaction.followup.send(f'✅ Successfully kicked {member}.')
            except Exception as e:
                await self.log_action(
                    action="KICK",
                    moderator=str(interaction.user),
                    target=str(member),
                    reason=str(e),
                    success=False
                )
                await interaction.followup.send(f'❌ Failed to kick: {e}')
        else:
            # Same flow for prefix commands
            confirmed = await self._confirm_interactive(ctx, f'Confirm kick {member}?')
            if not confirmed:
                await ctx.send('Action cancelled.')
                return
                
            await self.log_action(
                action="KICK",
                moderator=str(ctx.author),
                target=str(member),
                reason=reason
            )
            
            verified = await self.verify_terminal(ctx)
            if not verified:
                return
                
            try:
                await member.kick(reason=reason)
                await self.log_action(
                    action="KICK",
                    moderator=str(ctx.author),
                    target=str(member),
                    reason=reason,
                    success=True
                )
                await ctx.send(f'✅ Successfully kicked {member}.')
            except Exception as e:
                await self.log_action(
                    action="KICK",
                    moderator=str(ctx.author),
                    target=str(member),
                    reason=str(e),
                    success=False
                )
                await ctx.send(f'❌ Failed to kick: {e}')

    @commands.hybrid_command(name='ban', description='Ban a user from the server')
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user="The user to ban", reason="The reason for banning")
    async def ban(self, ctx, user: discord.User, *, reason: str = None):
        """Ban a user (interactive confirmation)"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            # First UI confirmation
            confirmed = await self._confirm_interactive(interaction, f'Confirm ban {user}?')
            if not confirmed:
                await interaction.followup.send('Action cancelled.', ephemeral=True)
                return
                
            # Log attempt and get terminal verification
            await self.log_action(
                action="BAN",
                moderator=str(interaction.user),
                target=str(user),
                reason=reason
            )
            
            verified = await self.verify_terminal(interaction)
            if not verified:
                return
                
            try:
                await interaction.guild.ban(user, reason=reason)
                await self.log_action(
                    action="BAN",
                    moderator=str(interaction.user),
                    target=str(user),
                    reason=reason,
                    success=True
                )
                await interaction.followup.send(f'✅ Successfully banned {user}.')
            except Exception as e:
                await self.log_action(
                    action="BAN",
                    moderator=str(interaction.user),
                    target=str(user),
                    reason=str(e),
                    success=False
                )
                await interaction.followup.send(f'❌ Failed to ban: {e}')
        else:
            # Same flow for prefix commands
            confirmed = await self._confirm_interactive(ctx, f'Confirm ban {user}?')
            if not confirmed:
                await ctx.send('Action cancelled.')
                return
                
            await self.log_action(
                action="BAN",
                moderator=str(ctx.author),
                target=str(user),
                reason=reason
            )
            
            verified = await self.verify_terminal(ctx)
            if not verified:
                return
                
            try:
                await ctx.guild.ban(user, reason=reason)
                await self.log_action(
                    action="BAN",
                    moderator=str(ctx.author),
                    target=str(user),
                    reason=reason,
                    success=True
                )
                await ctx.send(f'✅ Successfully banned {user}.')
            except Exception as e:
                await self.log_action(
                    action="BAN",
                    moderator=str(ctx.author),
                    target=str(user),
                    reason=str(e),
                    success=False
                )
                await ctx.send(f'❌ Failed to ban: {e}')
            return

    @commands.hybrid_command(name='unban', description='Unban a user from the server')
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="The Discord ID of the user to unban")
    async def unban(self, ctx, user_id: int):
        """Unban a user by ID"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await interaction.response.defer()
            try:
                user = await self.bot.fetch_user(user_id)
                await interaction.guild.unban(user)
                await interaction.followup.send(f'Unbanned {user}.')
            except Exception as e:
                await interaction.followup.send(f'Failed to unban: {e}', ephemeral=True)
        else:
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user}.')
            except Exception as e:
                await ctx.send(f'Failed to unban: {e}')

    @commands.hybrid_command(name='mute', description='Mute a member by adding a role')
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(
        member="The member to mute",
        role_name="The name of the mute role (default: Muted)"
    )
    async def mute(self, ctx, member: discord.Member, role_name: str = 'Muted'):
        """Add a role (mute) to a member"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await interaction.response.defer()
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if not role:
                try:
                    role = await interaction.guild.create_role(name=role_name)
                except Exception as e:
                    await interaction.followup.send(f'Failed to create role: {e}', ephemeral=True)
                    return
            try:
                await member.add_roles(role)
                await interaction.followup.send(f'Added {role_name} to {member}.')
            except Exception as e:
                await interaction.followup.send(f'Failed to add role: {e}', ephemeral=True)
        else:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if not role:
                try:
                    role = await ctx.guild.create_role(name=role_name)
                except Exception as e:
                    await ctx.send(f'Failed to create role: {e}')
                    return
            try:
                await member.add_roles(role)
                await ctx.send(f'Added {role_name} to {member}.')
            except Exception as e:
                await ctx.send(f'Failed to add role: {e}')

    @commands.hybrid_command(name='unmute', description='Remove a mute role from a member')
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(
        member="The member to unmute",
        role_name="The name of the mute role (default: Muted)"
    )
    async def unmute(self, ctx, member: discord.Member, role_name: str = 'Muted'):
        """Remove a role (unmute) from a member"""
        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            await interaction.response.defer()
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if not role:
                await interaction.followup.send('Role not found', ephemeral=True)
                return
            try:
                await member.remove_roles(role)
                await interaction.followup.send(f'Removed {role_name} from {member}.')
            except Exception as e:
                await interaction.followup.send(f'Failed to remove role: {e}', ephemeral=True)
        else:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if not role:
                await ctx.send('Role not found')
                return
            try:
                await member.remove_roles(role)
                await ctx.send(f'Removed {role_name} from {member}.')
            except Exception as e:
                await ctx.send(f'Failed to remove role: {e}')


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
