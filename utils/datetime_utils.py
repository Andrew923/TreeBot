import datetime
import dateparser


EDT = datetime.timezone(datetime.timedelta(hours=-4))


class DateTimeFormatter:
    """Centralized date/time formatting with EDT timezone."""

    @classmethod
    def format_time(cls, dt: datetime.datetime) -> str:
        """Format time only (e.g., '3:45 PM')."""
        return dt.astimezone(EDT).strftime('%I:%M %p').lstrip('0')

    @classmethod
    def format_datetime(cls, dt: datetime.datetime) -> str:
        """Format date and time (e.g., '12/30 3:45 PM')."""
        formatted = dt.astimezone(EDT).strftime('%m/%d %I:%M %p')
        # Remove leading zeros from month, day, and hour
        parts = formatted.split()
        date_part = '/'.join(p.lstrip('0') for p in parts[0].split('/'))
        time_part = parts[1].lstrip('0')
        return f"{date_part} {time_part} {parts[2]}"

    @classmethod
    def format_date(cls, dt: datetime.datetime | datetime.date) -> str:
        """Format date only (e.g., '12/30')."""
        if isinstance(dt, datetime.datetime):
            dt = dt.date()
        formatted = dt.strftime('%m/%d')
        return '/'.join(p.lstrip('0') for p in formatted.split('/'))

    @classmethod
    def format_date_long(cls, dt: datetime.datetime | datetime.date) -> str:
        """Format date in long form (e.g., 'Dec 30')."""
        if isinstance(dt, datetime.datetime):
            dt = dt.date()
        formatted = dt.strftime('%b %d')
        parts = formatted.split()
        return f"{parts[0]} {parts[1].lstrip('0')}"

    @classmethod
    def format_duration(cls, td: datetime.timedelta) -> str:
        """Format a timedelta as human-readable duration."""
        total_seconds = int(td.total_seconds())
        if total_seconds < 0:
            return "0 seconds"

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{parts[0]}, {parts[1]} and {parts[2]}"

    @classmethod
    def parse(cls, text: str) -> datetime.datetime:
        """
        Parse natural language date/time string.

        Args:
            text: Natural language date/time string (e.g., 'tomorrow at 3pm')

        Returns:
            Parsed datetime object

        Raises:
            ValueError: If the date cannot be parsed
        """
        settings = {
            'TIMEZONE': 'US/Eastern',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'future',
        }
        result = dateparser.parse(text, settings=settings)
        if result is None:
            raise ValueError(f"Could not parse date: {text}")
        return result

    @classmethod
    def now(cls) -> datetime.datetime:
        """Get current time in EDT."""
        return datetime.datetime.now(EDT)

    @classmethod
    def today(cls) -> datetime.date:
        """Get current date in EDT."""
        return cls.now().date()
