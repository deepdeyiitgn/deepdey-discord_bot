"""Extras cog: utility commands like ping, uptime, help, serverinfo, userinfo"""
from discord.ext import commands
from discord import app_commands
import discord
import datetime


class Extras(commands.Cog):
    """Utility commands and slash wrappers"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='ping', help='Ping the bot')
    async def ping(self, ctx: commands.Context):
        before = discord.utils.utcnow()
        msg = await ctx.send('Pong...')
        after = discord.utils.utcnow()
        latency = (after - before).total_seconds() * 1000
        await msg.edit(content=f'Pong! {latency:.2f}ms')

    @commands.hybrid_command(name='uptime', help='Show bot uptime')
    async def uptime(self, ctx: commands.Context):
        if not hasattr(self.bot, 'launch_time'):
            await ctx.send('Uptime unknown')
            return
        delta = datetime.datetime.utcnow() - self.bot.launch_time
        await ctx.send(f'Uptime: {str(delta).split(".")[0]}')

    @commands.hybrid_command(name='serverinfo', help='Show server information')
    async def serverinfo(self, ctx: commands.Context):
        g = ctx.guild
        await ctx.send(f'Server: {g.name} | Members: {g.member_count} | ID: {g.id}')

    @commands.hybrid_command(name='userinfo', help='Show user information')
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(f'User: {member.display_name} | ID: {member.id} | Joined: {member.joined_at}')

    @commands.hybrid_command(name='helpme', help='List commands (shortcut to built-in help)')
    async def helpme(self, ctx: commands.Context):
        # Provide a compact command list combining prefix and slash commands
        prefix_cmds = [c for c in self.bot.commands if not c.hidden]
        lines = ['Prefix commands:']
        for c in prefix_cmds:
            lines.append(f'{c.name} - {c.help or ""}')
        # Slash commands
        lines.append('\nSlash commands:')
        for app in sorted(self.bot.tree.walk_commands(), key=lambda x: x.name):
            lines.append(f'/{app.name} - {app.description or ""}')
        out = '\n'.join(lines)
        if len(out) > 1900:
            await ctx.send('Command list too long. Use /help to view slash commands.')
            return
        await ctx.send(f'``\n{out}\n``')

    @commands.hybrid_command(name='helpall', help='Alias for helpme')
    async def help_alias(self, ctx: commands.Context):
        await self.helpme(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(Extras(bot))
