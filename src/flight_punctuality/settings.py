
"""Shared settings for retrieving Swedavia flight information."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Airport codes used by the data collection process; these are all ten
# airports supported by Swedavia.
AIRPORTS = [
    "ARN", "BMA", "GOT", "MMX", "LLA",
    "UME", "OSD", "VBY", "RNB", "KRN",
]

# Number of calendar dates to retrieve, counting today as the first date.
DAYS_TO_FETCH = 3


def get_dates(days_to_fetch: int) -> list[str]:
    """Return a range of dates ending today, newest first.

    Dates are based on Sweden's local calendar and formatted as ``YYYY-MM-DD``.
    ``days_to_fetch`` includes today and must be at least one.
    """

    if days_to_fetch < 1:
        raise ValueError("days_to_fetch must be at least 1")

    # Use Sweden's local date so the result does not depend on the computer's
    # configured time zone.
    today = datetime.now(ZoneInfo("Europe/Stockholm")).date()

    # Subtract successive calendar days; isoformat() produces YYYY-MM-DD.
    return [
        (today - timedelta(days=i)).isoformat()
        for i in range(days_to_fetch)
    ]
