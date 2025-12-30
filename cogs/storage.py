import discord
from discord.ext import commands

from utils.github_storage import GitHubStorage


class StorageCog(commands.Cog):
    """User storage commands for saving and retrieving data."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = GitHubStorage(bot.github)

    @commands.command(name='store')
    async def store(self, ctx: commands.Context, *, message: str):
        """Store a message for later retrieval."""
        storage_data = self.storage.read('storage.json')
        storage_data[str(ctx.author.id)] = message
        self.storage.write('storage.json', storage_data)
        await ctx.send(f"Stored: {message}")

    @commands.command(name='retrieve')
    async def retrieve(self, ctx: commands.Context):
        """Retrieve your stored message."""
        storage_data = self.storage.read('storage.json')
        user_id = str(ctx.author.id)

        if user_id in storage_data and storage_data[user_id]:
            await ctx.send(storage_data[user_id])
        else:
            await ctx.send("Nothing is stored")


async def setup(bot: commands.Bot):
    await bot.add_cog(StorageCog(bot))
