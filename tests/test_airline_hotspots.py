"""Offline checks for the airline hotspot calculations and heatmap layout.

Run from the project root:
    uv run pytest tests/test_airline_hotspots.py -v
"""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from flight_punctuality.dashboard.airline_hotspots import (
    MIN_COMPLETED,
    NO_DELAY,
    TOO_LITTLE,
    airline_heatmap,
    filter_movements,
    normalise_data,
    prepare_heatmap_grid,
    summarise,
)


def rows() -> pd.DataFrame:
    """A small fictional mart with multiple airports, airlines and directions."""
    return normalise_data(
        pd.DataFrame(
            [
                {
                    "date_key": "2026-10-15",
                    "swedavia_airport_iata": "AAA",
                    "swedavia_airport_name": "Demo North",
                    "airline_icao": "SAM",
                    "airline_name": "Sample Air",
                    "scheduled_hour": 8,
                    "direction": "ARR",
                    "movements": 3,
                    "completed": 2,
                    "delayed": 1,
                    "cancelled": 1,
                },
                {
                    "date_key": "2026-10-15",
                    "swedavia_airport_iata": "BBB",
                    "swedavia_airport_name": "Demo South",
                    "airline_icao": "SAM",
                    "airline_name": "Sample Air",
                    "scheduled_hour": 8,
                    "direction": "DEP",
                    "movements": 98,
                    "completed": 98,
                    "delayed": 9,
                    "cancelled": 0,
                },
                {
                    "date_key": "2026-10-16",
                    "swedavia_airport_iata": "AAA",
                    "swedavia_airport_name": "Demo North",
                    "airline_icao": "ALT",
                    "airline_name": "Alternate Air",
                    "scheduled_hour": 9,
                    "direction": "ARR",
                    "movements": 20,
                    "completed": 20,
                    "delayed": 0,
                    "cancelled": 0,
                },
            ]
        )
    )


def test_weighted_delay_rate_and_cancellation_exclusion():
    grouped = summarise(rows(), ["airline_icao"])
    sample = grouped.set_index("airline_icao").loc["SAM"]
    assert sample["completed"] == 100
    assert sample["delayed"] == 10
    assert sample["cancelled"] == 1
    assert sample["delayed_share"] == pytest.approx(0.10)


def test_zero_completed_is_unavailable():
    df = rows().iloc[[0]].copy()
    df.loc[df.index[0], ["completed", "delayed"]] = 0
    assert pd.isna(summarise(df, ["airline_icao"]).iloc[0]["delayed_share"])


def test_zero_delayed_with_completed_is_zero_percent():
    grouped = summarise(rows(), ["airline_icao"])
    assert grouped.set_index("airline_icao").loc["ALT", "delayed_share"] == 0


def test_hour_grouping_combines_airports_and_directions():
    grouped = summarise(rows(), ["airline_label", "scheduled_hour"])
    sample = grouped[grouped["airline_label"] == "Sample Air (SAM)"].iloc[0]
    assert sample["scheduled_hour"] == 8
    assert sample["completed"] == 100
    assert sample["delayed"] == 10


def test_filters_are_applied_together():
    df = filter_movements(rows(), date(2026, 10, 15), date(2026, 10, 15), ["AAA"], "Arrivals", ["SAM"])
    assert len(df) == 1
    assert df.iloc[0]["completed"] == 2
    assert filter_movements(rows(), date(2026, 10, 15), date(2026, 10, 15), [], "Departures")["completed"].sum() == 98


def test_decimal_and_null_counts():
    df = rows().iloc[[0]].copy()
    df["completed"] = df["completed"].astype(object)
    df.loc[df.index[0], "completed"] = Decimal(2)
    df.loc[df.index[0], "cancelled"] = None
    clean = normalise_data(df)
    assert clean.iloc[0]["completed"] == 2
    assert clean.iloc[0]["cancelled"] == 0


def test_invalid_count_is_reported():
    df = rows()
    df["delayed"] = df["delayed"].astype(object)
    df.loc[df.index[0], "delayed"] = "invalid"
    with pytest.raises(ValueError):
        normalise_data(df)


def test_missing_required_column_is_reported():
    with pytest.raises(ValueError, match="Missing mart columns"):
        normalise_data(rows().drop(columns="completed"))


def test_empty_groups():
    empty = rows().iloc[:0]
    assert summarise(empty, ["airline_icao"]).empty


def test_heatmap_uses_all_24_hours_and_marks_low_samples():
    data = summarise(rows(), ["airline_label", "scheduled_hour"])
    grid = prepare_heatmap_grid(data, ["Sample Air (SAM)", "Alternate Air (ALT)"])
    assert len(grid) == 48
    sample = grid[(grid["airline_label"] == "Sample Air (SAM)") & (grid["scheduled_hour"] == 8)].iloc[0]
    assert sample["completed"] == 100
    assert sample["delayed_share"] == pytest.approx(0.10)
    assert pd.isna(sample["cell_state"])
    alternate = grid[(grid["airline_label"] == "Alternate Air (ALT)") & (grid["scheduled_hour"] == 9)].iloc[0]
    assert alternate["cell_state"] == NO_DELAY
    missing = grid[(grid["airline_label"] == "Sample Air (SAM)") & (grid["scheduled_hour"] == 7)].iloc[0]
    assert missing["completed"] == 0
    assert missing["cell_state"] == TOO_LITTLE
    assert pd.isna(missing["delayed_share"])
    assert missing["rate_label"] == "N/A"


def test_low_volume_group_remains_available():
    data = summarise(rows().iloc[[0]], ["airline_label", "scheduled_hour"])
    grid = prepare_heatmap_grid(data, ["Sample Air (SAM)"])
    sample = grid[grid["scheduled_hour"] == 8].iloc[0]
    assert sample["completed"] < MIN_COMPLETED
    assert sample["delayed_share"] == pytest.approx(0.5)
    assert sample["cell_state"] == TOO_LITTLE


def test_chart_renders_two_layers_and_optional_count_labels():
    data = summarise(rows(), ["airline_label", "scheduled_hour"])
    grid = prepare_heatmap_grid(data, ["Sample Air (SAM)"])
    chart = airline_heatmap(grid, ["Sample Air (SAM)"])
    spec = chart.to_dict()
    assert len(spec["layer"]) == 2
    with_counts = airline_heatmap(grid, ["Sample Air (SAM)"], show_counts=True)
    assert len(with_counts.to_dict()["layer"]) == 3
