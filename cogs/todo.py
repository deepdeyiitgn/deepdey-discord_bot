"""To-do cog: manage tasks per user with optional due dates"""
from discord.ext import commands
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import datetime
from discord import app_commands
import discord


DATA_PATH = Path(__file__).parent.parent / 'data' / 'todos.json'


class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.todos = {}

    async def cog_load(self):
        self.todos = await async_load_json(DATA_PATH, default={})

    @commands.group(name='todo', invoke_without_command=True)
    async def todo(self, ctx):
        await ctx.send('Subcommands: add, list, done')

    @todo.command(name='add')
    async def add_task(self, ctx, *, task_and_due: str):
        """Add a task. Optionally append ' /due YYYY-MM-DD'"""
        due = None
        task = task_and_due
        if ' /due ' in task_and_due:
            task, due_str = task_and_due.split(' /due ', 1)
            try:
                due = datetime.date.fromisoformat(due_str.strip())
            except Exception:
                await ctx.send('Invalid due date format. Use YYYY-MM-DD')
                return
        uid = str(ctx.author.id)
        user_tasks = self.todos.setdefault(uid, [])
        user_tasks.append({'task': task.strip(), 'done': False, 'due': due.isoformat() if due else None})
        await async_save_json(DATA_PATH, self.todos)
        await ctx.send('Task added.')

    @app_commands.command(name='todo_add', description='Add a todo (optionally: /todo_add task /due YYYY-MM-DD)')
    @app_commands.describe(task_and_due='Task description, optionally add " /due YYYY-MM-DD"')
    async def slash_add_task(self, interaction: discord.Interaction, task_and_due: str):
        await interaction.response.defer(ephemeral=True)
        due = None
        task = task_and_due
        if ' /due ' in task_and_due:
            task, due_str = task_and_due.split(' /due ', 1)
            try:
                due = datetime.date.fromisoformat(due_str.strip())
            except Exception:
                await interaction.followup.send('Invalid due date format. Use YYYY-MM-DD', ephemeral=True)
                return
        uid = str(interaction.user.id)
        user_tasks = self.todos.setdefault(uid, [])
        user_tasks.append({'task': task.strip(), 'done': False, 'due': due.isoformat() if due else None})
        await async_save_json(DATA_PATH, self.todos)
        await interaction.followup.send('Task added.', ephemeral=True)

    @todo.command(name='list')
    async def list_tasks(self, ctx):
        uid = str(ctx.author.id)
        tasks = self.todos.get(uid, [])
        if not tasks:
            await ctx.send('No tasks.')
            return
        lines = []
        for i, t in enumerate(tasks, start=1):
            status = '✅' if t.get('done') else '❌'
            due = f" (due {t['due']})" if t.get('due') else ''
            lines.append(f"{i}. {status} {t['task']}{due}")
        await ctx.send('\n'.join(lines))

    @app_commands.command(name='todo_list', description='List your todos')
    async def slash_list_tasks(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        uid = str(interaction.user.id)
        tasks = self.todos.get(uid, [])
        if not tasks:
            await interaction.followup.send('No tasks.', ephemeral=True)
            return
        lines = []
        for i, t in enumerate(tasks, start=1):
            status = '✅' if t.get('done') else '❌'
            due = f" (due {t['due']})" if t.get('due') else ''
            lines.append(f"{i}. {status} {t['task']}{due}")
        await interaction.followup.send('\n'.join(lines), ephemeral=True)

    @todo.command(name='done')
    async def mark_done(self, ctx, index: int):
        uid = str(ctx.author.id)
        tasks = self.todos.get(uid, [])
        if not tasks or index < 1 or index > len(tasks):
            await ctx.send('Invalid task index')
            return
        tasks[index-1]['done'] = True
        await async_save_json(DATA_PATH, self.todos)
        await ctx.send('Marked done.')

    @app_commands.command(name='todo_done', description='Mark a todo as done by index')
    async def slash_mark_done(self, interaction: discord.Interaction, index: int):
        await interaction.response.defer(ephemeral=True)
        uid = str(interaction.user.id)
        tasks = self.todos.get(uid, [])
        if not tasks or index < 1 or index > len(tasks):
            await interaction.followup.send('Invalid task index', ephemeral=True)
            return
        tasks[index-1]['done'] = True
        await async_save_json(DATA_PATH, self.todos)
        await interaction.followup.send('Marked done.', ephemeral=True)


async def setup(bot: commands.Bot):
    cog = Todo(bot)
    await cog.cog_load()
    await bot.add_cog(cog)

