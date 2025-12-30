import random

import discord
from discord.ext import commands

from utils.datetime_utils import DateTimeFormatter
from utils.embeds import EmbedBuilder
from utils.github_storage import GitHubStorage


class UtilityCog(commands.Cog):
    """Utility commands like time, weather, and help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = GitHubStorage(bot.github)
        self.owm = bot.owm
        self.mgr = self.owm.weather_manager()

    @commands.command(name='help')
    async def help_command(self, ctx: commands.Context):
        """Display all available commands."""
        embed = discord.Embed(color=0x03c6fc)
        embed.set_author(
            name="Tree Commands:",
            icon_url="http://clipart-library.com/img1/1269981.png",
            url="https://github.com/Andrew923/TreeBot"
        )
        embed.add_field(name='!help', value='Sends this message')
        embed.add_field(name='hello', value='I respond with hello')
        embed.add_field(name='!say', value='I repeat what you say')
        embed.add_field(name='!pokemon', value='Catch pokemons')
        embed.add_field(name='!random message', value='I send a random message from the last 300 messages')
        embed.add_field(name='!time', value='the time')
        embed.add_field(name='!store', value='store some message for later')
        embed.add_field(name='!retrieve', value='retrieve your stored stuff')
        embed.add_field(name='!remindpokemon', value='receive reminders for when you can catch pokemon from Toasty')
        embed.add_field(name='!snipe', value='see recently deleted messages')
        embed.add_field(name='!editsnipe', value='see recently edited messages')
        embed.add_field(name='!pin', value="specify 'from' or 'to' to get pinned messages from one channel sent to another")
        embed.add_field(name='!remind', value='be reminded of something')
        embed.add_field(name='!w', value="See weather at a location")
        embed.add_field(name='!define', value='Defines word')
        embed.add_field(name='wolf', value='calls Wolfram Alpha')
        embed.add_field(name='? or ??', value='Ask AI (? for small model, ?? for large)')
        embed.set_footer(text="See the ReadMe at https://github.com/Andrew923/TreeBot#readme")
        await ctx.send(embed=embed)

    @commands.command(name='time')
    async def time_command(self, ctx: commands.Context):
        """Get the current time."""
        if random.randint(1, 3) != 1:
            time_str = DateTimeFormatter.format_time(DateTimeFormatter.now())
            await ctx.send(f"The time is {time_str}")
        else:
            await ctx.send("time for you to get a watch hahaha")

    @commands.command(name='w', aliases=['weather'])
    async def weather(self, ctx: commands.Context, *, args: str = None):
        """
        Get weather information.
        Usage: !w [setup|forecast|in <location>]
        """
        weather_data = self.storage.read('weather.json')
        user_id = str(ctx.author.id)

        # Handle 'in <location>' syntax
        if args and 'in ' in args.lower():
            place = args.lower().replace('in ', '').strip()
        # Handle setup or new user
        elif args and 'setup' in args.lower() or user_id not in weather_data:
            await ctx.send("Setting up location. Please enter city name or coordinates (lat, lon).")

            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                if msg.content.lower() == 'cancel':
                    await ctx.send("Cancelled")
                    return

                if msg.content.replace(' ', '').replace(',', '').replace('.', '').replace('-', '').isdigit() or ',' in msg.content:
                    # Coordinates provided
                    try:
                        parts = msg.content.split(',')
                        lat, lon = float(parts[0].strip()), float(parts[1].strip())
                        geomgr = self.owm.geocoding_manager()
                        place = geomgr.reverse_geocode(lat, lon)[0].name
                    except Exception as e:
                        await ctx.send(f"Error parsing coordinates: {e}")
                        return
                else:
                    place = msg.content

                weather_data[user_id] = place
                self.storage.write('weather.json', weather_data)
            except TimeoutError:
                await ctx.send("Setup timed out.")
                return
        else:
            place = weather_data.get(user_id, 'New York')

        # Get weather data
        try:
            coords = self.owm.geocoding_manager().geocode(place)[0]
            one_call = self.mgr.one_call(coords.lat, coords.lon)
        except Exception as e:
            await ctx.send(f"Could not find weather for '{place}': {e}")
            return

        # Check if forecast requested
        if args and 'forecast' in args.lower():
            await self._send_forecast(ctx, place, one_call, args)
        else:
            await self._send_current(ctx, place, one_call)

    async def _send_current(self, ctx: commands.Context, place: str, one_call):
        """Send current weather."""
        curr = one_call.current
        today = one_call.forecast_daily[0]

        embed = EmbedBuilder.create(
            title=f'Weather in {place}',
            description=curr.detailed_status
        )
        embed.set_thumbnail(url=curr.weather_icon_url())

        curr_temp = curr.temperature('fahrenheit')
        today_temp = today.temperature('fahrenheit')

        temp_info = f"Temperature: {curr_temp['temp']:.0f} °F (Feels like: {curr_temp['feels_like']:.0f} °F)"
        temp_range = f"Low: {today_temp['min']:.0f} °F High: {today_temp['max']:.0f} °F"
        embed.add_field(name=temp_info, value=temp_range, inline=False)

        # Check for rain
        if today.rain:
            times = []
            for i in range(24):
                hour = one_call.forecast_hourly[i]
                if hour.rain:
                    from datetime import datetime
                    time = datetime.fromtimestamp(hour.ref_time)
                    if time.date() == DateTimeFormatter.today():
                        times.append(DateTimeFormatter.format_time(time))
            if times:
                embed.add_field(name="It will rain today!", value=f"Times: {', '.join(times[:6])}")

        await ctx.send(embed=embed)

    async def _send_forecast(self, ctx: commands.Context, place: str, one_call, args: str):
        """Send weather forecast."""
        # Determine number of days
        if 'tomorrow' in args.lower():
            days = 1
        elif args.split()[-1].isdigit():
            days = int(args.split()[-1])
        else:
            days = 4

        for i in range(1, min(days + 1, 8)):  # Max 7 days forecast
            day = one_call.forecast_daily[i]

            if i == 1:
                embed = EmbedBuilder.create(title=f'Forecast for {place}')
            else:
                embed = EmbedBuilder.create()

            embed.set_thumbnail(url=day.weather_icon_url())

            from datetime import datetime
            date = datetime.fromtimestamp(day.ref_time)
            date_str = DateTimeFormatter.format_date_long(date)
            temp = day.temperature('fahrenheit')

            embed.add_field(
                name=date_str,
                value=f"Low: {temp['min']:.0f} °F High: {temp['max']:.0f} °F"
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle natural language time queries."""
        if message.author.bot:
            return

        content = message.content.lower()
        if content.startswith('what time is it') or content.startswith("what's the time"):
            ctx = await self.bot.get_context(message)
            await self.time_command(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
