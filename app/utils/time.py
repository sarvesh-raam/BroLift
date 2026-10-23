from datetime import datetime, timedelta, timezone

# India has no DST, so a fixed offset is exact and avoids needing tzdata on Windows
IST = timezone(timedelta(hours=5, minutes=30), 'IST')


def now_local():
    """Current time in IST as a naive datetime.

    Departure times come from <input type="datetime-local"> and are stored naive in
    campus local time, so comparisons must use IST too. The server (Render) runs in
    UTC, and datetime.now() there would be 5.5 hours behind.
    """
    return datetime.now(IST).replace(tzinfo=None)
