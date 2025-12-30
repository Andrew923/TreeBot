import base64
from dataclasses import dataclass, field
from typing import Optional

import aiohttp
import discord


@dataclass
class MessageContext:
    """Container for message context data."""
    content: str
    author: str
    attachments: list[str] = field(default_factory=list)
    is_reply: bool = False


@dataclass
class AIContext:
    """Container for complete AI query context."""
    messages: list[MessageContext]
    images: list[str]
    system_context: str


class AIContextBuilder:
    """Builds context for AI queries from Discord messages."""

    DEFAULT_HISTORY_LIMIT = 10
    MAX_CONTEXT_LENGTH = 4000
    SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

    async def build_context(
        self,
        message: discord.Message,
        history_limit: int | None = None
    ) -> AIContext:
        """
        Build complete context for AI query.

        Args:
            message: The Discord message that triggered the query
            history_limit: Max number of recent messages to include

        Returns:
            AIContext with messages, images, and formatted system context
        """
        if history_limit is None:
            history_limit = self.DEFAULT_HISTORY_LIMIT

        context_messages: list[MessageContext] = []
        images: list[str] = []

        # 1. Get replied-to message if exists (prioritize this)
        if message.reference and message.reference.message_id:
            try:
                replied_msg = await message.channel.fetch_message(
                    message.reference.message_id
                )
                context_messages.append(
                    MessageContext(
                        content=replied_msg.content,
                        author=replied_msg.author.display_name,
                        is_reply=True
                    )
                )
                # Process replied message attachments
                for att in replied_msg.attachments:
                    if self._is_image(att.filename):
                        img_data = await self._download_attachment(att.url)
                        if img_data:
                            images.append(img_data)
            except discord.NotFound:
                pass

        # 2. Get recent channel history
        history: list[MessageContext] = []
        async for msg in message.channel.history(limit=history_limit, before=message):
            if msg.author.bot:
                continue
            history.append(
                MessageContext(
                    content=msg.content,
                    author=msg.author.display_name
                )
            )
        # Reverse to get chronological order (oldest first)
        context_messages.extend(reversed(history))

        # 3. Process current message attachments
        for att in message.attachments:
            if self._is_image(att.filename):
                img_data = await self._download_attachment(att.url)
                if img_data:
                    images.append(img_data)

        return AIContext(
            messages=context_messages,
            images=images,
            system_context=self._format_context(context_messages)
        )

    def _format_context(self, messages: list[MessageContext]) -> str:
        """Format context messages into a system prompt."""
        if not messages:
            return ""

        lines = ["Recent conversation context:"]
        for msg in messages:
            prefix = "[REPLYING TO] " if msg.is_reply else ""
            # Truncate very long messages
            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            if content.strip():
                lines.append(f"{prefix}{msg.author}: {content}")

        context = "\n".join(lines)
        if len(context) > self.MAX_CONTEXT_LENGTH:
            context = context[:self.MAX_CONTEXT_LENGTH] + "..."
        return context

    def _is_image(self, filename: str) -> bool:
        """Check if filename is a supported image type."""
        return any(
            filename.lower().endswith(ext)
            for ext in self.SUPPORTED_IMAGE_EXTENSIONS
        )

    @staticmethod
    async def _download_attachment(url: str) -> Optional[str]:
        """
        Download attachment and return base64 encoded data.

        Args:
            url: URL of the attachment to download

        Returns:
            Base64 encoded string of the image, or None if download failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return base64.b64encode(data).decode('utf-8')
        except Exception:
            pass
        return None
