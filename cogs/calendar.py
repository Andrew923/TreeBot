import datetime
import os
import platform

import discord
from discord.ext import commands
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials

from utils.datetime_utils import DateTimeFormatter
from utils.embeds import EmbedBuilder


class CalendarCog(commands.Cog):
    """Calendar commands for managing Google Calendar events."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.calendar = self._init_calendar()

    def _init_calendar(self):
        """Initialize Google Calendar client."""
        if platform.uname().node == 'Andrew' or 'oracle' in platform.uname().release:
            # Local development - use default credentials
            return GoogleCalendar("andrewyu41213@gmail.com")
        else:
            # Cloud deployment - use environment variables
            credentials = Credentials(
                token=os.getenv('token'),
                refresh_token=os.getenv('refresh_token'),
                client_id=os.getenv('client_id'),
                client_secret=os.getenv('client_secret'),
                scopes=['https://www.googleapis.com/auth/calendar'],
                token_uri='https://oauth2.googleapis.com/token'
            )
            return GoogleCalendar(credentials=credentials)

    def _format_event_time(self, event) -> str:
        """Format event time for display."""
        if event.location:
            return f"Location: {event.location}\nFrom: {DateTimeFormatter.format_time(event.start)}\nTo: {DateTimeFormatter.format_time(event.end)}"
        return f"From: {DateTimeFormatter.format_time(event.start)}\nTo: {DateTimeFormatter.format_time(event.end)}"

    @commands.command(name='event')
    async def add_event(self, ctx: commands.Context, *, args: str):
        """
        Add a calendar event.
        Usage: !event <start>, <end>, <title>  (for timed event)
               !event <date>, <title>          (for all-day event)
        """
        if ',' not in args:
            await ctx.send("Please use a comma to separate the event time and event title")
            return

        try:
            parts = [p.strip() for p in args.split(',')]

            if len(parts) >= 3:
                # Timed event: start, end, title
                start = DateTimeFormatter.parse(parts[0])
                end = DateTimeFormatter.parse(parts[1])
                title = ', '.join(parts[2:])

                self.calendar.add_event(Event(title, start=start, end=end))

                embed = EmbedBuilder.event_embed(
                    title='New Event',
                    event_name=title,
                    start=DateTimeFormatter.format_datetime(start),
                    end=DateTimeFormatter.format_datetime(end)
                )
            else:
                # All-day event: date, title
                date = DateTimeFormatter.parse(parts[0]).date()
                title = ', '.join(parts[1:])

                self.calendar.add_event(Event(
                    title,
                    start=date,
                    end=date + datetime.timedelta(days=1)
                ))

                embed = EmbedBuilder.event_embed(
                    title='New Event',
                    event_name=title,
                    date=DateTimeFormatter.format_date(date)
                )

            await ctx.send(embed=embed)

        except ValueError as e:
            await ctx.send(f"Could not parse the date/time: {e}")
        except Exception as e:
            await ctx.send(f"Error creating event: {e}")

    @commands.command(name='schedule')
    async def schedule(self, ctx: commands.Context, *, date_str: str = None):
        """
        View schedule for a specific day.
        Usage: !schedule [date]
        """
        try:
            if date_str:
                day = DateTimeFormatter.parse(date_str).date()
            else:
                day = DateTimeFormatter.today()

            events = list(self.calendar[day:day])
            event_count = len(events)
            s = '' if event_count == 1 else 's'

            embed = EmbedBuilder.create(
                title='Schedule',
                description=f"{event_count} event{s} on {DateTimeFormatter.format_date(day)}"
            )

            for event in events:
                embed.add_field(
                    name=event.summary,
                    value=self._format_event_time(event),
                    inline=False
                )

            await ctx.send(embed=embed)

        except ValueError as e:
            await ctx.send(f"Could not parse the date: {e}")
        except Exception as e:
            await ctx.send(f"Error fetching schedule: {e}")

    @commands.command(name='delete')
    async def delete_event(self, ctx: commands.Context, *, date_str: str = None):
        """
        Delete a calendar event.
        Usage: !delete [date]
        """
        try:
            if date_str:
                day = DateTimeFormatter.parse(date_str).date()
            else:
                day = DateTimeFormatter.today()

            events = list(self.calendar[day:day])

            if not events:
                await ctx.send(f"No events found for {DateTimeFormatter.format_date(day)}")
                return

            # Show events for selection
            embed = EmbedBuilder.create(
                title='Delete which event?',
                description='Type the number corresponding to the event'
            )

            for i, event in enumerate(events, 1):
                embed.add_field(
                    name=f"{i}. {event.summary}",
                    value=self._format_event_time(event),
                    inline=False
                )
            embed.set_footer(text="Type 'Cancel' to stop")

            await ctx.send(embed=embed)

            # Wait for user selection
            def check(m):
                if m.content.lower() == 'cancel':
                    return True
                return (m.author == ctx.author and
                        m.channel == ctx.channel and
                        m.content.isdigit() and
                        1 <= int(m.content) <= len(events))

            msg = await self.bot.wait_for('message', check=check, timeout=60.0)

            if msg.content.lower() == 'cancel':
                await ctx.send("Cancelled")
                return

            # Delete selected event
            event_index = int(msg.content) - 1
            event = events[event_index]
            self.calendar.delete_event(event)

            embed = EmbedBuilder.event_embed(
                title='Event Deleted',
                event_name=event.summary,
                date=DateTimeFormatter.format_date(event.start)
            )
            await ctx.send(embed=embed)

        except TimeoutError:
            await ctx.send("Selection timed out")
        except ValueError as e:
            await ctx.send(f"Could not parse the date: {e}")
        except Exception as e:
            await ctx.send(f"Error deleting event: {e}")

    @commands.command(name='update')
    async def update_event(self, ctx: commands.Context, *, date_str: str = None):
        """
        Update a calendar event.
        Usage: !update [date]
        """
        try:
            if date_str:
                day = DateTimeFormatter.parse(date_str).date()
            else:
                day = DateTimeFormatter.today()

            events = list(self.calendar[day:day])

            if not events:
                await ctx.send(f"No events found for {DateTimeFormatter.format_date(day)}")
                return

            # Show events for selection
            embed = EmbedBuilder.create(
                title='Update which event?',
                description='Type the number corresponding to the event'
            )

            for i, event in enumerate(events, 1):
                embed.add_field(
                    name=f"{i}. {event.summary}",
                    value=self._format_event_time(event),
                    inline=False
                )
            embed.set_footer(text="Type 'Cancel' to stop")

            await ctx.send(embed=embed)

            # Wait for event selection
            def check_num(m):
                if m.content.lower() == 'cancel':
                    return True
                return (m.author == ctx.author and
                        m.channel == ctx.channel and
                        m.content.isdigit() and
                        1 <= int(m.content) <= len(events))

            msg = await self.bot.wait_for('message', check=check_num, timeout=60.0)

            if msg.content.lower() == 'cancel':
                await ctx.send("Cancelled")
                return

            # Get selected event
            event_index = int(msg.content) - 1
            event = events[event_index]

            # Show current event details
            embed = EmbedBuilder.create(title='Update Event')
            embed.add_field(
                name=event.summary,
                value=f"Start: {DateTimeFormatter.format_datetime(event.start)}\nEnd: {DateTimeFormatter.format_datetime(event.end)}"
            )
            embed.set_footer(text="Type 'start <time>', 'end <time>', 'summary <text>', 'location <text>', or 'description <text>' to update. Type 'Cancel' to stop.")

            await ctx.send(embed=embed)

            # Wait for update instruction
            def check_update(m):
                if m.content.lower() == 'cancel':
                    return True
                return m.author == ctx.author and m.channel == ctx.channel

            msg = await self.bot.wait_for('message', check=check_update, timeout=60.0)

            if msg.content.lower() == 'cancel':
                await ctx.send("Cancelled")
                return

            # Parse and apply update
            content = msg.content
            if content.lower().startswith('start '):
                event.start = DateTimeFormatter.parse(content[6:].strip())
            elif content.lower().startswith('end '):
                event.end = DateTimeFormatter.parse(content[4:].strip())
            elif content.lower().startswith('summary '):
                event.summary = content[8:].strip()
            elif content.lower().startswith('location '):
                event.location = content[9:].strip()
            elif content.lower().startswith('description '):
                event.description = content[12:].strip()
            else:
                await ctx.send("Invalid update format. Use 'start', 'end', 'summary', 'location', or 'description' followed by the new value.")
                return

            self.calendar.update_event(event)

            embed = EmbedBuilder.create(title='Event Updated')
            embed.add_field(
                name=event.summary,
                value=f"Start: {DateTimeFormatter.format_datetime(event.start)}\nEnd: {DateTimeFormatter.format_datetime(event.end)}"
            )
            await ctx.send(embed=embed)

        except TimeoutError:
            await ctx.send("Selection timed out")
        except ValueError as e:
            await ctx.send(f"Could not parse the input: {e}")
        except Exception as e:
            await ctx.send(f"Error updating event: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(CalendarCog(bot))
