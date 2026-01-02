import discord
from discord.ext import commands

from utils.embeds import EmbedBuilder
from utils.github_storage import GitHubStorage


class ModerationCog(commands.Cog):
    """Moderation commands for tracking deleted/edited messages and pins."""

    # Class-level storage for snipe data (shared across instances)
    snipe_author: dict[int, discord.User] = {}
    snipe_content: dict[int, str] = {}
    editsnipe_before: dict[int, str] = {}
    editsnipe_after: dict[int, str] = {}
    editsnipe_author: dict[int, discord.User] = {}

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = GitHubStorage(bot.github)

    @commands.command(name='snipe')
    async def snipe(self, ctx: commands.Context):
        """See the last deleted message in this channel."""
        channel_id = ctx.channel.id

        if channel_id not in self.snipe_content:
            await ctx.send("Nobody deleted any shit")
            return

        content = self.snipe_content[channel_id]
        author = self.snipe_author.get(channel_id)

        # Check if it's an image URL
        if content.startswith('https://'):
            embed = EmbedBuilder.create(
                title=f"Last deleted message in #{ctx.channel.name}"
            )
            embed.set_image(url=content)
        else:
            embed = EmbedBuilder.create(
                title=f"Last deleted message in #{ctx.channel.name}",
                description=content
            )

        if author:
            embed.set_footer(text=f"This message was sent by {author}")

        await ctx.send(embed=embed)

    @commands.command(name='editsnipe')
    async def editsnipe(self, ctx: commands.Context):
        """See the last edited message in this channel."""
        channel_id = ctx.channel.id

        if channel_id not in self.editsnipe_before:
            await ctx.send("No edits")
            return

        embed = EmbedBuilder.create(
            title=f"Last edited message in #{ctx.channel.name}"
        )
        embed.add_field(name='Before:', value=self.editsnipe_before[channel_id], inline=False)
        embed.add_field(name='After:', value=self.editsnipe_after[channel_id], inline=False)

        author = self.editsnipe_author.get(channel_id)
        if author:
            embed.set_footer(text=f"This message was edited by {author}")

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle eval command without prefix."""
        if message.author.bot:
            return

        if message.content.lower().startswith('eval '):
            code = " ".join(message.content.split()[1:])
            try:
                result = eval(code.strip())
                await message.channel.send(f"```\n{result}\n```")
            except Exception as e:
                await message.channel.send(f"Error: {e}")

    @commands.command(name='pin')
    async def pin(self, ctx: commands.Context, direction: str = None):
        """
        Configure pin forwarding.
        Usage: !pin from (read pins from this channel)
               !pin to (send pins to this channel)
        """
        if not direction:
            await ctx.send("Please specify 'from' or 'to'")
            return

        pins = self.storage.read('pins.json')
        direction = direction.lower()

        if 'from' in direction:
            if 'from' not in pins:
                pins['from'] = []
            pins['from'].append(ctx.channel.id)
            self.storage.write('pins.json', pins)
            await ctx.send('Pins will be read from this channel')
        elif 'to' in direction:
            if 'to' not in pins:
                pins['to'] = []
            pins['to'].append(ctx.channel.id)
            self.storage.write('pins.json', pins)
            await ctx.send('Pins will be posted to this channel')
        else:
            await ctx.send("Please specify 'from' or 'to'")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
