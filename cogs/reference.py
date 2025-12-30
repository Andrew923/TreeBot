import random

import discord
from discord.ext import commands
import requests
from pydictionary import Dictionary
from serpapi import GoogleSearch

from utils.embeds import EmbedBuilder, EMPTY_CHAR


class ReferenceCog(commands.Cog):
    """Reference commands for definitions, search, and Wolfram Alpha."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wolfram = bot.wolfram
        self.serpapi_key = bot.serpapi_key
        self.rapidapi_headers = bot.rapidapi_headers

    def _urban_define(self, term: str) -> discord.Embed:
        """Fetch definition from Urban Dictionary."""
        response = requests.get(
            "https://mashape-community-urban-dictionary.p.rapidapi.com/define",
            headers=self.rapidapi_headers,
            params={"term": term}
        )

        data = response.json()
        if not data.get('list'):
            return EmbedBuilder.create(
                title=f'Definition of {term}',
                description="Nothing found :("
            )

        result = data['list'][0]
        embed = EmbedBuilder.create(
            title=f'Definition of {term}',
            description=result['definition']
        )
        embed.add_field(
            name="Example",
            value=' '.join(result['example'].split()) or "No example",
            inline=False
        )
        embed.add_field(
            name=EMPTY_CHAR,
            value=f"[Urban Dictionary]({result['permalink']})"
        )
        return embed

    @commands.command(name='define')
    async def define(self, ctx: commands.Context, *, word: str):
        """Define a word using dictionary, falls back to Urban Dictionary."""
        try:
            definitions = Dictionary(word, 5).meanings()
            embed = EmbedBuilder.create(title=f'Definition of {word}')

            count = 0
            for definition in definitions:
                count += 1
                embed.add_field(name=EMPTY_CHAR, value=f"{count}. {definition}", inline=False)

            if count == 0:
                # Fall back to Urban Dictionary
                embed = self._urban_define(word)

            await ctx.send(embed=embed)
        except Exception:
            # Fall back to Urban Dictionary on any error
            embed = self._urban_define(word)
            await ctx.send(embed=embed)

    @commands.command(name='urban')
    async def urban(self, ctx: commands.Context, *, term: str):
        """Look up a term on Urban Dictionary."""
        embed = self._urban_define(term)
        await ctx.send(embed=embed)

    @commands.command(name='wolf', aliases=['wolfram'])
    async def wolfram_alpha(self, ctx: commands.Context, *, query: str):
        """Query Wolfram Alpha."""
        try:
            results = await self.wolfram.aquery(query)
            embed = EmbedBuilder.create(title=query.title())

            for pod in results.pods:
                title = pod.title
                description = ''

                for sub in pod.subpods:
                    if 'plot' in title.lower() and sub.get('img'):
                        embed.set_image(url=sub['img']['@src'])
                    if sub.plaintext:
                        description += sub.plaintext + '\n'

                if not description:
                    continue

                # Highlight results
                if 'result' in title.lower() or 'solutions' in title.lower():
                    description = f'`{description.strip()}`'

                embed.add_field(name=title, value=description[:1024], inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name='search', aliases=['show'])
    async def image_search(self, ctx: commands.Context, *, query: str):
        """Search for an image using Google."""
        params = {
            "q": query,
            "tbm": "isch",
            "api_key": self.serpapi_key
        }

        try:
            result = GoogleSearch(params).get_dict()
            index = random.randint(0, 5)
            link = result['images_results'][index]['thumbnail']
        except Exception:
            link = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Twemoji_1f4a9.svg/176px-Twemoji_1f4a9.svg.png'

        await ctx.send(link)

    @commands.command(name='tinyurl', aliases=['url'])
    async def tinyurl(self, ctx: commands.Context, *, text: str):
        """Generate a TinyURL-style link."""
        slug = '-'.join(text.split())
        await ctx.send(f'https://www.tinyurl.com/{slug}')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle natural language triggers for reference commands."""
        if message.author.bot:
            return

        content = message.content.lower()

        # Handle "what does X mean" pattern
        if content.startswith('what does') and content.endswith('mean'):
            word = ' '.join(content.split()[2:-1])
            if word:
                ctx = await self.bot.get_context(message)
                await self.define(ctx, word=word)
                return

        # Handle "define X" without command prefix
        if content.startswith('define ') and not content.startswith('!define'):
            word = content[7:].strip()
            if word:
                ctx = await self.bot.get_context(message)
                await self.define(ctx, word=word)
                return

        # Handle "urban X" without command prefix
        if content.startswith('urban ') and not content.startswith('!urban'):
            term = content[6:].strip()
            if term:
                ctx = await self.bot.get_context(message)
                await self.urban(ctx, term=term)
                return

        # Handle "wolf X" without command prefix
        if content.startswith('wolf ') and not content.startswith('!wolf'):
            query = content[5:].strip()
            if query:
                ctx = await self.bot.get_context(message)
                await self.wolfram_alpha(ctx, query=query)
                return

        # Handle tinyurl/url triggers
        if content.startswith('tinyurl ') or content.startswith('url '):
            prefix = 'tinyurl ' if content.startswith('tinyurl') else 'url '
            text = content[len(prefix):].strip()
            if text:
                ctx = await self.bot.get_context(message)
                await self.tinyurl(ctx, text=text)


async def setup(bot: commands.Bot):
    await bot.add_cog(ReferenceCog(bot))
