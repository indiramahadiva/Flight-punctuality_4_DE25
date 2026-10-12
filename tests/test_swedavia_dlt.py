"""Basic tests for the Swedavia ingestion logic.

Run with: uv run pytest -q tests/test_swedavia_dlt.py
"""

from datetime import date

import pytest

from flight_punctuality.ingestion import swedavia
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
    assert (date.fromisoformat(dates[0]) - date.fromisoformat(dates[2])).days == 2


def test_movement_key_is_deterministic():
    """The same flight information should produce the same key."""
    flight = {
        "flightId": "SK123",
        "arrivalTime": {"scheduledUtc": "2026-10-09T10:00:00Z"},
    }
    first = create_movement_key(flight, "ARN", "arrival")
    second = create_movement_key(flight, "ARN", "arrival")
    assert first == second
    # Preserve keys already loaded by the existing pipeline.
    assert first == "ARN|arrival|SK123|2026-10-09T10:00:00Z"


def test_missing_flight_identity():
    """Missing identity fields should raise a ValueError."""
    with pytest.raises(ValueError, match="Missing flight identity"):
        create_movement_key({}, "ARN", "arrival")


def test_invalid_direction():
    """An unsupported API direction should be rejected."""
    with pytest.raises(ValueError, match="Invalid direction"):
        fetch_flights("ARN", "invalid", "2026-10-09")
    with pytest.raises(ValueError, match="Invalid direction"):
        create_movement_key({}, "ARN", "arrivals")


def test_api_endpoint_mapping(monkeypatch):
    """Plural URLs should be used for singular internal direction values."""
    calls = []
    flights = [{"flightId": "SK123"}]

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"flights": flights}

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return FakeResponse()

    monkeypatch.setenv("SWEDAVIA_API_KEY", "test-key")
    monkeypatch.setattr(swedavia.requests, "get", fake_get)

    assert fetch_flights("ARN", "arrival", "2026-10-09") == flights
    assert fetch_flights("ARN", "departure", "2026-10-09") == flights
    assert calls[0][0].endswith("/ARN/arrivals/2026-10-09")
    assert calls[1][0].endswith("/ARN/departures/2026-10-09")
    assert all(call[1]["Ocp-Apim-Subscription-Key"] == "test-key" for call in calls)
    assert all(call[2] == 30 for call in calls)


def test_all_airport_date_requests(monkeypatch):
    """Each airport and date must be requested for both directions."""
    calls = []

    def fake_fetch(airport, direction, day):
        calls.append((airport, direction, day))
        return []

    monkeypatch.setattr(swedavia, "fetch_flights", fake_fetch)

    source = swedavia_source(
        ["ARN", "GOT"],
        ["2026-10-09", "2026-10-08"],
    )
    list(source)  # Trigger extraction without calling the real API.

    assert len(calls) == 8
    assert {call[1] for call in calls} == {"arrival", "departure"}
