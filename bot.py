import asyncio
import os
import platform

import discord
from discord.ext import commands
from github import Github
from canvasapi import Canvas
from pyowm.owm import OWM
import wolframalpha
from pokedex import pokedex

# Platform-specific config loading
if platform.uname().node == 'Andrew' or 'oracle' in platform.uname().release:
    import config
    TOKEN = config.discord_token
    GITHUB_TOKEN = config.github_token
    CANVAS_API_KEY = config.API_KEY
    WEATHER_API_KEY = config.weather
    WOLFRAM_APP_ID = config.wolf
    RAPIDAPI_KEY = config.rapidapi
    SERPAPI_KEY = config.serpapi
else:
    TOKEN = os.getenv('config.token')
    GITHUB_TOKEN = os.getenv('github_token')
    CANVAS_API_KEY = os.getenv('canvasapikey')
    WEATHER_API_KEY = os.getenv('weatherkey')
    WOLFRAM_APP_ID = os.getenv('wolf')
    RAPIDAPI_KEY = os.getenv('rapidapi')
    SERPAPI_KEY = os.getenv('serpapi')

# Shared API headers
RAPIDAPI_HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com"
}

# List of cogs to load
COG_EXTENSIONS = [
    'cogs.utility',
    'cogs.fun',
    'cogs.storage',
    'cogs.moderation',
    'cogs.reference',
    'cogs.reminders',
    'cogs.calendar',
    'cogs.canvas',
    'cogs.ai',
    'cogs.listeners',
]


class TreeBot(commands.Bot):
    """Main bot class with shared resources."""

    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)

        # Initialize shared resources
        self.github = Github(GITHUB_TOKEN)
        self.canvas = Canvas('https://canvas.cmu.edu/', CANVAS_API_KEY)
        self.owm = OWM(WEATHER_API_KEY)
        self.wolfram = wolframalpha.Client(WOLFRAM_APP_ID)
        self.pokedex = pokedex.Pokedex()
        self.serpapi_key = SERPAPI_KEY
        self.rapidapi_headers = RAPIDAPI_HEADERS

        # Remove default help command to use custom one
        self.remove_command('help')

    async def setup_hook(self):
        """Load all cog extensions."""
        for extension in COG_EXTENSIONS:
            try:
                await self.load_extension(extension)
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {e}')

    async def on_ready(self):
        """Called when the bot is ready."""
        print(f'We have logged in as {self.user}')


async def main():
    """Main entry point."""
    bot = TreeBot()
    await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
