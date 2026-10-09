
"""
Basic tests for the Swedavia ingestion logic.
to run test:  uv run pytest -q tests/swedavia_dlt.py
"""

from datetime import date

import pytest

from flight_punctuality.ingestion.swedavia import (
    create_movement_key,
    fetch_flights,
    swedavia_source,
)
from flight_punctuality.settings import get_dates


def test_get_dates():
    """The date window should contain three consecutive days."""
    dates = get_dates(3)

    assert len(dates) == 3
    assert (date.fromisoformat(dates[0]) -
            date.fromisoformat(dates[2])).days == 2


def test_movement_key_is_deterministic():
    """The same flight information should produce the same key."""
    flight = {
        "flightId": "SK123",
        "arrivalTime": {
            "scheduledUtc": "2026-10-09T10:00:00Z"
        },
    }

    first = create_movement_key(flight, "ARN", "arrival")
    second = create_movement_key(flight, "ARN", "arrival")

    assert first == second


def test_missing_flight_identity():
    """Missing identity fields should raise a ValueError."""
    with pytest.raises(ValueError, match="Missing flight identity"):
        create_movement_key({}, "ARN", "arrival")


def test_invalid_direction():
    """An unsupported API direction should be rejected."""
    with pytest.raises(ValueError, match="Invalid direction"):
        fetch_flights("ARN", "invalid", "2026-10-09")


def test_all_airport_date_requests(monkeypatch):
    """Each airport and date must be requested for both directions."""
    calls = []

    def fake_fetch(airport, direction, day):
        calls.append((airport, direction, day))
        return []

    monkeypatch.setattr(
        "flight_punctuality.ingestion.swedavia.fetch_flights",
        fake_fetch,
    )

    source = swedavia_source(
        ["ARN", "GOT"],
        ["2026-10-09", "2026-10-08"],
    )

    list(source)  # Trigger extraction without calling the real API.

    # 2 airports x 2 dates x 2 directions = 8 requests.
    assert len(calls) == 8
    assert {call[1] for call in calls} == {
        "arrivals", "departures"
    }
