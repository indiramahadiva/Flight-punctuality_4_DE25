"""Extract Swedavia flight data using dlt.
uv run --env-file .env python -m flight_punctuality.ingestion.pipelines
"""

import json
import os
import urllib.request

import dlt

BASE_URL = "https://api.swedavia.se/flightinfo/v2"


def fetch_flights(
    airport: str,
    direction: str,
    date: str,
) -> list[dict]:
    """
    Fetch arrivals or departures from the Swedavia API.

    Args:
        airport: Airport code, e.g. "ARN" for Arlanda.
        direction: Either "arrivals" or "departures".
        date: Date to fetch flight data for (YYYY-MM-DD).

    Returns:
        A list of flight records as dictionaries.
    """

    # Only these two API endpoints are supported.
    if direction not in ("arrivals", "departures"):
        raise ValueError(f"Invalid direction: {direction}")

    url = f"{BASE_URL}/{airport}/{direction}/{date}"

    # Create an HTTP request with the API key for authentication.
    request = urllib.request.Request(
        url,
        headers={
            # Read the API key from environment variables.
            "Ocp-Apim-Subscription-Key": os.environ["SWEDAVIA_API_KEY"],
            "Accept": "application/json",
        },
    )

    # Send the request (30-second timeout) and parse JSON into Python.
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    # Validate the API response before processing the flights.
    # TypeError: The API returned an unexpected data type.
    if not isinstance(data, dict):
        raise TypeError("Expected a JSON object from Swedavia")

    flights = data.get("flights")

    # ValueError: The expected flights collection is missing.
    if flights is None:
        raise ValueError("Missing flights collection")

    # The flights collection must be a list, even if it is empty.
    if not isinstance(flights, list):
        raise TypeError("Expected flights collection to be a list")

    return flights


def create_movement_key(
    flight: dict,
    airport: str,
    direction: str,
) -> str:
    """
    Create a deterministic identifier for each flight movement.

    Combines airport, direction, flight ID, and scheduled UTC time.
    The same input values always generate the same movement key.

    This key allows dlt to match existing records during a merge.
    """

    # Arrivals and departures have different time fields in the API.
    time_field = "arrivalTime" if direction == "arrival" else "departureTime"

    flight_id = flight.get("flightId")

    # Get scheduledUtc from the nested arrivalTime/departureTime dictionary.
    scheduled_utc = (flight.get(time_field) or {}).get("scheduledUtc")

    # Both values are required to identify a flight movement.
    if not flight_id or not scheduled_utc:
        raise ValueError(f"Missing flight identity for {airport} {direction}")

    return f"{airport}|{direction}|{flight_id}|{scheduled_utc}"


# dlt resource: extract arrivals into the arrivals table.
@dlt.resource(
    name="arrivals",  # Destination table name.
    write_disposition="merge",  # Update matching records or insert new ones.
    primary_key="movement_key",  # Column used to match existing records.
)
def arrivals(airports: list[str], dates: list[str]):
    """
    Extract arrival flights for all selected airports and dates.

    Preserve the original API fields and add metadata
    and a movement key to each flight record.
    """

    # Loop through every airport and every requested date.
    for airport in airports:
        for date in dates:
            for flight in fetch_flights(airport, "arrivals", date):
                # yield sends one flight record at a time to dlt.
                yield {
                    **flight,  # Preserve all original API fields.
                    "swedavia_airport": airport,
                    "direction": "arrival",
                    "movement_key": create_movement_key(flight, airport, "arrival"),
                }


# dlt resource: extract departures into the departures table.
@dlt.resource(
    name="departures",  # Destination table name.
    write_disposition="merge",  # Update matching records or insert new ones.
    primary_key="movement_key",  # Column used to match existing records.
)
def departures(airports: list[str], dates: list[str]):
    """
    Extract departure flights for all selected airports and dates.

    Preserve the original API fields and add metadata
    and a movement key to each flight record.
    """

    # Loop through every airport and every requested date.
    for airport in airports:
        for date in dates:
            for flight in fetch_flights(airport, "departures", date):
                yield {
                    **flight,  # Preserve all original API fields.
                    "swedavia_airport": airport,
                    "direction": "departure",
                    "movement_key": create_movement_key(flight, airport, "departure"),
                }


# A dlt source groups multiple resources into one logical data source.
@dlt.source(name="swedavia")
def swedavia_source(airports: list[str], dates: list[str]):
    """
    Group arrivals and departures into one Swedavia dlt source.

    Both resources can be loaded together through a dlt pipeline.
    """

    return [
        arrivals(airports, dates),
        departures(airports, dates),
    ]
