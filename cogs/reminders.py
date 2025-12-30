import asyncio
import datetime
import re

import discord
from discord.ext import commands

from utils.datetime_utils import DateTimeFormatter
from utils.github_storage import GitHubStorage


class RemindersCog(commands.Cog):
    """Reminder commands for general reminders and Pokemon notifications."""

    POKEMON_CATCH_DELAY = 3 * 60 * 60  # 3 hours in seconds
    MENTION_PATTERN = re.compile(r'<@!?(\d+)>')

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = GitHubStorage(bot.github)

    @commands.command(name='remind')
    async def remind(self, ctx: commands.Context, *, args: str):
        """
        Set a reminder.
        Usage: !remind <time>, <reminder text>
        Example: !remind tomorrow at 3pm, call mom
        """
        if ',' not in args:
            await ctx.send("Please use a comma to separate the time and reminder text.")
            return

        try:
            time_str, reminder = args.split(',', 1)
            reminder = reminder.strip()
            time = DateTimeFormatter.parse(time_str.strip())

            # Calculate delay
            now = datetime.datetime.now(time.tzinfo)
            delay = (time - now).total_seconds()

            if delay <= 0:
                await ctx.send("That time is in the past!")
                return

            formatted_time = DateTimeFormatter.format_datetime(time)
            await ctx.send(f"You will be reminded to {reminder} at {formatted_time}")

            # Wait and send reminder
            await asyncio.sleep(delay)
            await ctx.send(f"{ctx.author.mention} {reminder}")

        except ValueError as e:
            await ctx.send(f"Could not parse the time: {e}")
        except Exception as e:
            await ctx.send(f"Error setting reminder: {e}")

    @commands.command(name='remindpokemon')
    async def remindpokemon(self, ctx: commands.Context, setting: str = None):
        """
        Toggle Pokemon catch reminders.
        Usage: !remindpokemon on/off
        """
        remind_data = self.storage.read('remind.json')
        user_id = str(ctx.author.id)

        if setting is None:
            current = remind_data.get(user_id, 'no')
            status = "on" if current == "yes" else "off"
            await ctx.send(f"Pokemon reminders are currently {status}. Use `!remindpokemon on` or `!remindpokemon off` to change.")
            return

        setting = setting.lower()
        if setting == 'on':
            remind_data[user_id] = "yes"
            self.storage.write('remind.json', remind_data)
            await ctx.send("You will now receive notifications when pokemons are ready")
        elif setting == 'off':
            remind_data[user_id] = "nah"
            self.storage.write('remind.json', remind_data)
            await ctx.send("You will no longer receive notifications when pokemons are ready")
        else:
            await ctx.send("Please specify whether to turn this setting 'on' or 'off'")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle Pokemon catch detection for reminders."""
        if message.author.bot:
            return

        # Check for Pokemon bot catch messages
        try:
            if not message.embeds:
                return

            embed = message.embeds[0].to_dict()
            description = embed.get('description', '')

            if "you've caught" not in description.lower():
                return

            # Extract mentioned user
            matches = self.MENTION_PATTERN.findall(description)
            if not matches:
                return

            user_id = matches[0]
            user = self.bot.get_user(int(user_id))
            if not user:
                return

            # Check if user has reminders enabled
            remind_data = self.storage.read('remind.json')
            if remind_data.get(str(user.id)) != "yes":
                return

            # Wait and send reminder
            await asyncio.sleep(self.POKEMON_CATCH_DELAY)
            await message.channel.send(
                f"{user.mention}, it is time for you to catch the pokemon"
            )

        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(RemindersCog(bot))
