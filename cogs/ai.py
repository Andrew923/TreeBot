import discord
from discord.ext import commands
import ollama

from utils.ai_context import AIContextBuilder


class AICog(commands.Cog):
    """AI chatbot commands using Ollama with Gemma3 models."""

    MODELS = {
        'small': 'gemma3:1b-it-qat',
        'large': 'gemma3:4b-it-qat'
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.context_builder = AIContextBuilder(bot.github)

    async def _handle_ai_query(
        self,
        ctx: commands.Context,
        model_size: str,
        query: str | None
    ):
        """Handle AI query with context and multimodal support."""
        if not query and not ctx.message.attachments:
            await ctx.send("Please provide a question or attach an image.")
            return

        async with ctx.typing():
            # Build context from channel history and replied message
            context = await self.context_builder.build_context(ctx.message)

            # Prepare the messages for Ollama
            messages = []

            # If we have conversation history, use it
            if context.conversation_history:
                # Use existing conversation history
                messages = context.conversation_history.copy()
            else:
                # New conversation - add system context if available
                if context.system_context:
                    messages.append({
                        'role': 'system',
                        'content': f"You are a helpful assistant. {context.system_context}"
                    })

            # Build user message
            if query:
                user_content = f"Respond very concisely. {query}"
            else:
                user_content = "Respond very concisely. Describe this image."

            user_message = {'role': 'user', 'content': user_content}

            # Add images if present (multimodal support)
            if context.images:
                user_message['images'] = context.images

            messages.append(user_message)

            # Call Ollama
            try:
                response = ollama.chat(
                    model=self.MODELS[model_size],
                    messages=messages
                )
                reply = response['message']['content']

                # Store the conversation
                # Save user message
                self.context_builder.conversation_storage.add_message(
                    thread_id=context.thread_id,
                    role='user',
                    content=user_content,
                    author=ctx.author.display_name,
                    channel_id=ctx.channel.id
                )

                # Save assistant response
                self.context_builder.conversation_storage.add_message(
                    thread_id=context.thread_id,
                    role='assistant',
                    content=reply,
                    channel_id=ctx.channel.id
                )

                # Handle Discord message length limit (2000 chars)
                if len(reply) > 2000:
                    # Split into multiple messages
                    for i in range(0, len(reply), 2000):
                        await ctx.send(reply[i:i+2000])
                else:
                    await ctx.send(reply)

            except Exception as e:
                await ctx.send(f"AI error: {str(e)}")

    @commands.command(name='ask')
    async def ask_small(self, ctx: commands.Context, *, query: str = None):
        """
        Ask the AI (1B model).
        Usage: !ask <question>
        You can also attach images for multimodal queries.
        """
        await self._handle_ai_query(ctx, 'small', query)

    @commands.command(name='ask2')
    async def ask_large(self, ctx: commands.Context, *, query: str = None):
        """
        Ask the AI (4B model).
        Usage: !ask2 <question>
        You can also attach images for multimodal queries.
        """
        await self._handle_ai_query(ctx, 'large', query)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle ? and ?? prefix without command prefix."""
        if message.author.bot:
            return

        content = message.content

        # Skip if it's a command (starts with !)
        if content.startswith('!'):
            return

        # Handle ?? prefix (must check first since it starts with ?)
        if content.startswith('??'):
            query = content[2:].strip()
            ctx = await self.bot.get_context(message)
            await self._handle_ai_query(ctx, 'large', query if query else None)
            return

        # Handle ? prefix
        if content.startswith('?'):
            query = content[1:].strip()
            ctx = await self.bot.get_context(message)
            await self._handle_ai_query(ctx, 'small', query if query else None)
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))
