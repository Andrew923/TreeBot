from dataclasses import dataclass, field, asdict
from typing import Optional
import discord
from github import Github
from utils.github_storage import GitHubStorage


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    author: Optional[str] = None  # Discord username for user messages

    def to_dict(self):
        """Convert to dictionary for storage."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict):
        """Create from dictionary."""
        return ConversationMessage(**data)


@dataclass
class Conversation:
    """A conversation thread with message history."""
    thread_id: str  # Discord message ID that started the thread
    messages: list[ConversationMessage] = field(default_factory=list)
    channel_id: Optional[int] = None

    def to_dict(self):
        """Convert to dictionary for storage."""
        return {
            'thread_id': self.thread_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'channel_id': self.channel_id
        }

    @staticmethod
    def from_dict(data: dict):
        """Create from dictionary."""
        messages = [ConversationMessage.from_dict(msg) for msg in data.get('messages', [])]
        return Conversation(
            thread_id=data['thread_id'],
            messages=messages,
            channel_id=data.get('channel_id')
        )


class ConversationStorage:
    """Manages conversation history storage."""

    MAX_MESSAGES_PER_CONVERSATION = 20  # Limit history to prevent context overflow
    STORAGE_FILE = 'data/conversations.json'

    def __init__(self, github: Github):
        """
        Initialize conversation storage.

        Args:
            github: Authenticated PyGithub instance
        """
        self.storage = GitHubStorage(github)
        self._cache = {}  # In-memory cache for faster access

    def get_conversation(self, thread_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by thread ID.

        Args:
            thread_id: The Discord message ID that started or is part of the thread

        Returns:
            Conversation object if found, None otherwise
        """
        # Check cache first
        if thread_id in self._cache:
            return self._cache[thread_id]

        # Load from storage
        try:
            data = self.storage.get_cached(self.STORAGE_FILE)
            if thread_id in data:
                conversation = Conversation.from_dict(data[thread_id])
                self._cache[thread_id] = conversation
                return conversation
        except Exception:
            # File doesn't exist yet or other error
            pass

        return None

    def save_conversation(self, conversation: Conversation):
        """
        Save or update a conversation.

        Args:
            conversation: The conversation to save
        """
        # Trim conversation if it exceeds max messages
        if len(conversation.messages) > self.MAX_MESSAGES_PER_CONVERSATION:
            # Keep most recent messages
            conversation.messages = conversation.messages[-self.MAX_MESSAGES_PER_CONVERSATION:]

        # Update cache
        self._cache[conversation.thread_id] = conversation

        # Save to storage
        try:
            data = self.storage.read(self.STORAGE_FILE)
        except Exception:
            # File doesn't exist yet, create new data
            data = {}

        data[conversation.thread_id] = conversation.to_dict()

        try:
            self.storage.write(
                self.STORAGE_FILE,
                data,
                'Update conversation history'
            )
        except Exception:
            # File might not exist, try creating it
            # For now, we'll skip this - GitHub will handle file creation
            pass

        # Invalidate cache to ensure fresh reads
        self.storage.invalidate_cache(self.STORAGE_FILE)

    async def find_thread_root(self, message: discord.Message) -> Optional[str]:
        """
        Find the root message ID of a conversation thread.

        Args:
            message: The message to trace back

        Returns:
            The root thread ID (message ID), or None if not part of a thread
        """
        current = message
        root_id = None

        # Trace back through reply chain to find the root
        while current.reference and current.reference.message_id:
            try:
                replied_msg = await current.channel.fetch_message(
                    current.reference.message_id
                )

                # If we replied to a bot message, this is part of a conversation thread
                if replied_msg.author.bot:
                    root_id = str(replied_msg.id)

                    # Check if this bot message itself was a reply (continue thread)
                    if replied_msg.reference and replied_msg.reference.message_id:
                        current = replied_msg
                        continue
                    else:
                        # This bot message started the thread
                        break
                else:
                    # User replied to another user, not part of bot conversation
                    break

            except discord.NotFound:
                break

        return root_id

    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        author: Optional[str] = None,
        channel_id: Optional[int] = None
    ):
        """
        Add a message to a conversation thread.

        Args:
            thread_id: The thread ID
            role: 'user' or 'assistant'
            content: Message content
            author: Discord username (for user messages)
            channel_id: Discord channel ID
        """
        conversation = self.get_conversation(thread_id)

        if conversation is None:
            conversation = Conversation(
                thread_id=thread_id,
                channel_id=channel_id
            )

        message = ConversationMessage(role=role, content=content, author=author)
        conversation.messages.append(message)

        self.save_conversation(conversation)

    def get_messages_for_ollama(self, thread_id: str) -> list[dict]:
        """
        Get conversation messages formatted for Ollama API.

        Args:
            thread_id: The thread ID

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        conversation = self.get_conversation(thread_id)

        if conversation is None:
            return []

        return [
            {'role': msg.role, 'content': msg.content}
            for msg in conversation.messages
        ]
