import asyncio

import discord
from discord.ext import commands

from utils.embeds import EmbedBuilder, EMPTY_CHAR
from utils.github_storage import GitHubStorage
from cogs.moderation import ModerationCog


class ListenersCog(commands.Cog):
    """Event listeners for message deletion, editing, and pin forwarding."""

    SNIPE_EXPIRY = 120  # seconds

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = GitHubStorage(bot.github)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Track deleted messages for snipe command."""
        if message.author.bot:
            return

        channel_id = message.channel.id

        # Store content (attachment URL or text)
        if message.attachments:
            ModerationCog.snipe_content[channel_id] = message.attachments[0].url
        else:
            ModerationCog.snipe_content[channel_id] = message.content

        ModerationCog.snipe_author[channel_id] = message.author

        # Auto-expire after SNIPE_EXPIRY seconds
        await asyncio.sleep(self.SNIPE_EXPIRY)

        # Clean up (only if still the same message)
        if channel_id in ModerationCog.snipe_author:
            if ModerationCog.snipe_author[channel_id] == message.author:
                ModerationCog.snipe_author.pop(channel_id, None)
                ModerationCog.snipe_content.pop(channel_id, None)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Track edited messages and handle pin forwarding."""
        if before.author.bot:
            return

        channel_id = before.channel.id

        # Track content edits for editsnipe
        if before.content != after.content:
            ModerationCog.editsnipe_before[channel_id] = before.content
            ModerationCog.editsnipe_after[channel_id] = after.content
            ModerationCog.editsnipe_author[channel_id] = before.author

            # Auto-expire
            await asyncio.sleep(self.SNIPE_EXPIRY)

            # Clean up (only if still the same edit)
            if channel_id in ModerationCog.editsnipe_author:
                if ModerationCog.editsnipe_author[channel_id] == before.author:
                    ModerationCog.editsnipe_before.pop(channel_id, None)
                    ModerationCog.editsnipe_after.pop(channel_id, None)
                    ModerationCog.editsnipe_author.pop(channel_id, None)

        # Handle pin forwarding
        if not before.pinned and after.pinned:
            await self._handle_pin(after)

    async def _handle_pin(self, message: discord.Message):
        """Forward pinned messages to configured channels."""
        try:
            pins_config = self.storage.read('pins.json')

            if message.channel.id not in pins_config.get('from', []):
                return

            # Find the corresponding 'to' channel
            from_list = pins_config.get('from', [])
            to_list = pins_config.get('to', [])

            if message.channel.id not in from_list:
                return

            index = from_list.index(message.channel.id)
            if index >= len(to_list):
                return

            to_channel_id = to_list[index]
            to_channel = self.bot.get_channel(to_channel_id)

            if not to_channel:
                return

            # Create embed for the pinned message
            if message.attachments:
                embed = EmbedBuilder.create()
                embed.set_image(url=message.attachments[0].url)
            else:
                embed = EmbedBuilder.create(description=message.content)

            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url if message.author.display_avatar else None
            )
            embed.add_field(
                name=EMPTY_CHAR,
                value=f"[Jump to Message]({message.jump_url})"
            )

            await to_channel.send(embed=embed)

            # Unpin the original message
            await message.unpin()

        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ListenersCog(bot))
