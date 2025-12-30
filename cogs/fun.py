import datetime
import random

import discord
from discord.ext import commands
from art import text2art

from utils.datetime_utils import DateTimeFormatter
from utils.github_storage import GitHubStorage


class FunCog(commands.Cog):
    """Fun and entertainment commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = GitHubStorage(bot.github)
        self.pokedex = bot.pokedex

    @commands.command(name='pokemon')
    async def pokemon(self, ctx: commands.Context):
        """Catch a random Pokemon! Cooldown: 1 hour."""
        pokemontime = self.storage.read('pokemontime.json')
        user_id = str(ctx.author.id)
        now = datetime.datetime.now()

        try:
            # Check cooldown
            if user_id in pokemontime:
                cooldown_end = pokemontime[user_id]
                if cooldown_end > now:
                    remaining = cooldown_end - now
                    wait_time = DateTimeFormatter.format_duration(remaining)
                    await ctx.send(f"You gotta wait {wait_time} to catch another pokemon bro")
                    return

            # Catch pokemon
            pokemon = self.pokedex.get_pokemon_by_number(random.randint(1, 807))[0]
            await ctx.send(f"Good job, {ctx.author.mention} you caught {pokemon['name']}!")
            await ctx.send(pokemon['sprite'])

            # Update cooldown (1 hour)
            pokemontime[user_id] = now + datetime.timedelta(hours=1)
            self.storage.write('pokemontime.json', pokemontime)

        except KeyError:
            # First time catching
            pokemon = self.pokedex.get_pokemon_by_number(random.randint(1, 807))[0]
            await ctx.send(f"Good job, {ctx.author.mention} you caught {pokemon['name']}!")
            await ctx.send(pokemon['sprite'])

            pokemontime[user_id] = now + datetime.timedelta(hours=1)
            self.storage.write('pokemontime.json', pokemontime)

    @commands.command(name='random')
    async def random_message(self, ctx: commands.Context):
        """Send a random message from the last 300 messages."""
        messages = [msg async for msg in ctx.channel.history(limit=300)]
        if messages:
            msg = random.choice(messages)
            await ctx.send(f"{msg.content}\n{msg.jump_url}")
        else:
            await ctx.send("No messages found in history.")

    @commands.command(name='say')
    async def say(self, ctx: commands.Context, *, text: str):
        """Make the bot repeat what you say."""
        await ctx.send(text)

    @commands.command(name='ascii')
    async def ascii_art(self, ctx: commands.Context, *, text: str):
        """
        Generate ASCII art.
        Add 'small', 'medium', or 'large' at end for size.
        """
        parts = text.split()
        size = 'random'

        if parts and parts[-1].lower() in ('small', 'medium', 'large'):
            size = parts.pop().lower()

        if not parts:
            await ctx.send("Please provide text to convert to ASCII art.")
            return

        # Map size to font
        font_map = {
            'small': 'random-small',
            'medium': 'random-medium',
            'large': 'random-large',
            'random': 'random'
        }
        font = font_map.get(size, 'random')

        try:
            art = text2art(' '.join(parts), font)
            # Discord has a 2000 character limit
            if len(art) > 1990:
                art = art[:1990]
            await ctx.send(f'```{art}```')
        except Exception as e:
            await ctx.send(f"Error generating ASCII art: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle natural language triggers."""
        if message.author.bot:
            return

        if message.content.lower() == 'hello':
            await message.channel.send('Hello!')


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
