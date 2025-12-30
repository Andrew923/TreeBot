import discord
from typing import Any


EMBED_COLOR = 0x03c6fc
EMPTY_CHAR = '\u200b'


class EmbedBuilder:
    """Helper class for consistent embed creation."""

    @staticmethod
    def create(
        title: str | None = None,
        description: str | None = None,
        **kwargs: Any
    ) -> discord.Embed:
        """
        Create a standard embed with bot colors.

        Args:
            title: Embed title
            description: Embed description
            **kwargs: Additional arguments passed to discord.Embed

        Returns:
            Configured discord.Embed instance
        """
        return discord.Embed(
            color=EMBED_COLOR,
            title=title,
            description=description,
            **kwargs
        )

    @staticmethod
    def error(message: str) -> discord.Embed:
        """Create an error embed (red)."""
        return discord.Embed(
            color=0xff0000,
            title='Error',
            description=message
        )

    @staticmethod
    def success(message: str) -> discord.Embed:
        """Create a success embed (green)."""
        return discord.Embed(
            color=0x00ff00,
            title='Success',
            description=message
        )

    @staticmethod
    def list_embed(
        title: str,
        items: list[Any],
        numbered: bool = False,
        show_cancel_footer: bool = True
    ) -> discord.Embed:
        """
        Create an embed with a list of items.

        Args:
            title: Embed title
            items: List of items to display
            numbered: Whether to number the items
            show_cancel_footer: Whether to show "Type 'Cancel' to stop" footer

        Returns:
            Configured discord.Embed instance
        """
        embed = discord.Embed(color=EMBED_COLOR, title=title)
        for i, item in enumerate(items, 1):
            value = f"{i}. {item}" if numbered else str(item)
            embed.add_field(name=EMPTY_CHAR, value=value, inline=False)
        if show_cancel_footer:
            embed.set_footer(text="Type 'Cancel' to stop")
        return embed

    @staticmethod
    def event_embed(
        title: str,
        event_name: str,
        start: str | None = None,
        end: str | None = None,
        location: str | None = None,
        date: str | None = None
    ) -> discord.Embed:
        """
        Create an embed for calendar events.

        Args:
            title: Embed title (e.g., 'New Event', 'Event Deleted')
            event_name: Name of the event
            start: Start time string
            end: End time string
            location: Optional location
            date: Date string (for all-day events)

        Returns:
            Configured discord.Embed instance
        """
        embed = discord.Embed(color=EMBED_COLOR, title=title)

        if date and not start:
            # All-day event
            embed.add_field(name=event_name, value=f"Date: {date}")
        else:
            # Timed event
            value_parts = []
            if location:
                value_parts.append(f"Location: {location}")
            if start:
                value_parts.append(f"From: {start}")
            if end:
                value_parts.append(f"To: {end}")
            embed.add_field(name=event_name, value='\n'.join(value_parts))

        return embed
