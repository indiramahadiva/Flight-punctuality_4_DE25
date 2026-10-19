"""Airline delay hotspots: airline-by-scheduled-hour heatmap.

The page reads marts.mart_airline_hotspots with the read-only reporting role.
Run from the repository root:
    uv run --env-file .env streamlit run src/flight_punctuality/dashboard/airline_hotspots.py

Until the mart is published to the shared marts schema, preview sample data in
Git Bash (the preview never queries Snowflake):
    AIRLINE_HOTSPOTS_DEMO=1 uv run streamlit run src/flight_punctuality/dashboard/airline_hotspots.py
"""

import os
from datetime import date

import altair as alt
import pandas as pd
import snowflake.connector
import streamlit as st

from flight_punctuality.connections import reporter_credentials

# Same palette and legend conventions as the team's airport heatmap.
HEAT_COLORS = ["#A0BFDC", "#7793AB", "#4F687A", "#263C49"]
SHARE_MAX = 0.25  # 25% or higher uses the darkest shade.
MIN_COMPLETED = 5  # Smaller hourly samples are too uncertain to colour.
MIN_AIRLINE_COMPLETED = 20  # Minimum for the narrative airline comparison.
TOO_LITTLE = f"Too little data (<{MIN_COMPLETED} flights)"
NO_DELAY = "No delays"
STATE_COLORS = {TOO_LITTLE: "#FFFFFF", NO_DELAY: "#DFE0E2"}
OUTLINE_COLOR = "#DFE0E2"
COUNT_COLUMNS = ["movements", "completed", "delayed", "cancelled"]
REQUIRED_COLUMNS = [
    "date_key",
    "swedavia_airport_iata",
    "swedavia_airport_name",
    "airline_icao",
    "airline_name",
    "scheduled_hour",
    "direction",
    *COUNT_COLUMNS,
]


def normalise_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return clean mart data with dates, numeric counts and unique airline labels.

    Snowflake can return uppercase column names and Decimal counts. Missing
    aggregate counts become zero, but invalid text and negative counts fail.
    """
    clean = df.copy()
    clean.columns = clean.columns.str.lower()
    missing = set(REQUIRED_COLUMNS) - set(clean.columns)
    if missing:
        raise ValueError(f"Missing mart columns: {', '.join(sorted(missing))}")

    clean["date_key"] = pd.to_datetime(clean["date_key"]).dt.date
    clean["scheduled_hour"] = pd.to_numeric(clean["scheduled_hour"], errors="raise")
    if clean["scheduled_hour"].isna().any() or (
        (clean["scheduled_hour"] % 1 != 0)
        | ~clean["scheduled_hour"].between(0, 23)
    ).any():
        raise ValueError("Scheduled hours must be whole numbers from 0 to 23")
    clean["scheduled_hour"] = clean["scheduled_hour"].astype(int)

    for column in COUNT_COLUMNS:
        values = pd.to_numeric(clean[column], errors="raise").fillna(0)
        if (values < 0).any() or (values % 1 != 0).any():
            raise ValueError(f"Invalid count values in {column}")
        clean[column] = values.astype(int)

    # The ICAO identifier distinguishes airlines that share a readable name.
    codes = clean["airline_icao"].astype("string").fillna("UNKNOWN").str.strip()
    clean["airline_icao"] = codes.mask(codes == "", "UNKNOWN")
    names = clean["airline_name"].astype("string").fillna("").str.strip()
    names = names.mask(names == "", clean["airline_icao"])
    names = names.mask(names == "UNKNOWN", "Unknown airline")
    clean["airline_name"] = names
    clean["airline_label"] = names + " (" + clean["airline_icao"] + ")"
    clean.loc[clean["airline_icao"] == "UNKNOWN", "airline_label"] = names
    return clean


@st.cache_data(ttl=3600)
def load_airline_hotspots() -> pd.DataFrame:
    """Read the published airline mart, using the shared reporter connection."""
    with snowflake.connector.connect(**reporter_credentials()) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("select * from mart_airline_hotspots")
            data = cursor.fetch_pandas_all()
        finally:
            cursor.close()
    return normalise_data(data)


def filter_movements(
    df: pd.DataFrame,
    start_date: date,
    end_date: date,
    airport_codes: list[str],
    direction: str,
    airline_codes: list[str] | None = None,
) -> pd.DataFrame:
    """Filter by scheduled Swedish date, airport, flight direction and airline."""
    matches = df["date_key"].between(start_date, end_date)
    if airport_codes:
        matches &= df["swedavia_airport_iata"].isin(airport_codes)
    if direction != "All":
        value = {"Arrivals": "ARR", "Departures": "DEP"}[direction]
        matches &= df["direction"] == value
    if airline_codes:
        matches &= df["airline_icao"].isin(airline_codes)
    return df.loc[matches].copy()


def _label_options(df: pd.DataFrame, code: str, label: str) -> dict[str, str]:
    """Build a sorted code-to-label mapping for a filter widget."""
    return (
        df[[code, label]]
        .drop_duplicates()
        .sort_values(label)
        .set_index(code)[label]
        .to_dict()
    )


def summarise(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Sum counts by dimension, then calculate delayed/completed.

    Never average the mart's delayed_share: it gives small groups too much weight.
    Zero completed movements means the rate is unavailable, not 0%.
    """
    grouped = df.groupby(by, as_index=False, dropna=False)[COUNT_COLUMNS].sum()
    denominator = grouped["completed"].where(grouped["completed"] > 0)
    grouped["delayed_share"] = grouped["delayed"] / denominator
    return grouped


def prepare_heatmap_grid(data: pd.DataFrame, airline_order: list[str]) -> pd.DataFrame:
    """Build every airline/hour cell and identify low-sample or zero-delay cells."""
    full_grid = pd.MultiIndex.from_product(
        [airline_order, range(24)], names=["airline_label", "scheduled_hour"]
    ).to_frame(index=False)
    grid = full_grid.merge(data, on=["airline_label", "scheduled_hour"], how="left")
    grid[COUNT_COLUMNS] = grid[COUNT_COLUMNS].fillna(0).astype(int)
    grid["hour_label"] = grid["scheduled_hour"].map(lambda hour: f"{hour:02d}")
    grid["rate_label"] = grid["delayed_share"].map(
        lambda share: f"{share:.1%}" if pd.notna(share) else "N/A"
    )

    grid["cell_state"] = None
    grid.loc[grid["completed"] < MIN_COMPLETED, "cell_state"] = TOO_LITTLE
    grid.loc[
        (grid["completed"] >= MIN_COMPLETED) & (grid["delayed"] == 0),
        "cell_state",
    ] = NO_DELAY
    return grid


def airline_heatmap(grid: pd.DataFrame, airline_order: list[str], show_counts: bool = False):
    """Create the team's blue heatmap, replacing airport rows with airlines."""
    x = alt.X(
        "hour_label:O",
        title="Scheduled hour (Swedish time)",
        sort=[f"{hour:02d}" for hour in range(24)],
        axis=alt.Axis(labelAngle=0),
    )
    y = alt.Y(
        "airline_label:N", title=None, sort=airline_order, axis=alt.Axis(labelLimit=290)
    )
    tooltip = [
        alt.Tooltip("airline_label:N", title="Airline"),
        alt.Tooltip("hour_label:N", title="Scheduled hour"),
        alt.Tooltip("completed:Q", title="Completed", format=",.0f"),
        alt.Tooltip("delayed:Q", title="Delayed", format=",.0f"),
        alt.Tooltip("cancelled:Q", title="Cancelled", format=",.0f"),
        alt.Tooltip("rate_label:N", title="Delay rate"),
    ]

    states = list(STATE_COLORS)
    state_cells = (
        alt.Chart(grid[grid["cell_state"].notna()])
        .mark_rect(strokeWidth=2)
        .encode(
            x=x,
            y=y,
            stroke=alt.Stroke(
                "cell_state:N",
                scale=alt.Scale(domain=states, range=[OUTLINE_COLOR, "white"]),
                legend=None,
            ),
            color=alt.Color(
                "cell_state:N",
                title=None,
                scale=alt.Scale(domain=states, range=[STATE_COLORS[s] for s in states]),
                legend=alt.Legend(orient="top", symbolType="square", symbolSize=200),
            ),
            tooltip=[alt.Tooltip("cell_state:N", title="Cell status"), *tooltip],
        )
    )

    delay_cells = (
        alt.Chart(grid[grid["cell_state"].isna()])
        .mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=x,
            y=y,
            color=alt.Color(
                "delayed_share:Q",
                title="Delay rate",
                scale=alt.Scale(domain=[0, SHARE_MAX], range=HEAT_COLORS, clamp=True),
                legend=alt.Legend(format=".0%", orient="top", gradientLength=240),
            ),
            tooltip=tooltip,
        )
    )
    layers = state_cells + delay_cells

    if show_counts:
        counts = grid[grid["completed"] > 0].copy()
        dark = counts["cell_state"].isna() & (
            counts["delayed_share"] >= SHARE_MAX / 2
        )
        counts["text_color"] = dark.map({True: "white", False: "#10120D"})
        labels = (
            alt.Chart(counts)
            .mark_text(fontSize=10)
            .encode(
                x=x,
                y=y,
                text=alt.Text("completed:Q", format=",.0f"),
                color=alt.Color("text_color:N", scale=None),
                tooltip=tooltip,
            )
        )
        layers = layers + labels

    return layers.resolve_scale(color="independent").properties(height=alt.Step(28))


def demo_data() -> pd.DataFrame:
    """Generate fictional examples for developing the page without Snowflake."""
    airports = [("AAA", "Demo Airport North"), ("BBB", "Demo Airport South")]
    airlines = [("DAX", "Sample Airline A"), ("DBX", "Sample Airline B"),
                ("DCX", "Sample Airline C"), ("DDX", "Sample Airline D"),
                ("DEX", "Sample Airline E"), ("DFX", "Sample Airline F")]
    rows = []
    for airline_number, (code, name) in enumerate(airlines):
        for airport_number, (airport_code, airport_name) in enumerate(airports):
            for day in [date(2026, 10, 15), date(2026, 10, 16)]:
                for direction in ["ARR", "DEP"]:
                    for hour in range(24):
                        # Deliberately create quiet hours and different sample sizes.
                        completed = max(0, (hour * 3 + airline_number * 5) % 21 - 3)
                        completed += airport_number
                        delayed = min(
                            completed,
                            round(completed * (0.05 + ((hour + airline_number) % 5) * 0.04)),
                        )
                        cancelled = int(hour == 17 and completed > 0)
                        rows.append(
                            {
                                "date_key": day,
                                "swedavia_airport_iata": airport_code,
                                "swedavia_airport_name": airport_name,
                                "airline_icao": code,
                                "airline_name": name,
                                "scheduled_hour": hour,
                                "direction": direction,
                                "movements": completed + cancelled,
                                "completed": completed,
                                "delayed": delayed,
                                "cancelled": cancelled,
                            }
                        )
    return normalise_data(pd.DataFrame(rows))


def render() -> None:
    """Render the page, with filters and an airline-by-hour heatmap."""
    st.title("Airline Delay Hotspots")
    st.caption(
        "Which airlines and scheduled hours show potential punctuality pressure? "
        "A movement is delayed when completed more than 15 minutes after schedule."
    )

    if os.environ.get("AIRLINE_HOTSPOTS_DEMO") == "1":
        st.warning("SAMPLE DATA PREVIEW — fictional airlines and numbers, not Snowflake results.")
        df = demo_data()
    else:
        try:
            df = load_airline_hotspots()
        except (snowflake.connector.Error, KeyError, ValueError) as exc:
            st.error("Unable to load airline hotspots from the reporting mart.")
            st.caption(
                "Check that mart_airline_hotspots is published in the shared marts "
                "schema and that flights_reporter can SELECT from it. "
                f"Error category: {type(exc).__name__}."
            )
            return

    if df.empty:
        st.info("The airline mart contains no movements.")
        return

    # Filters apply to all metrics and the heatmap.
    airport_names = _label_options(
        df, "swedavia_airport_iata", "swedavia_airport_name"
    )
    first_day, last_day = df["date_key"].min(), df["date_key"].max()
    col_dates, col_airports, col_direction = st.columns([2, 3, 2])
    picked_dates = col_dates.date_input(
        "Dates", value=(first_day, last_day), min_value=first_day, max_value=last_day
    )
    picked_airports = col_airports.multiselect(
        "Airports",
        options=list(airport_names),
        format_func=airport_names.__getitem__,
        placeholder="All airports",
    )
    picked_direction = col_direction.radio(
        "Direction", ["All", "Arrivals", "Departures"], horizontal=True
    )

    if isinstance(picked_dates, (tuple, list)):
        if len(picked_dates) != 2:
            st.info("Select an end date to complete the date range.")
            return
        start_date, end_date = picked_dates
    else:
        start_date = end_date = picked_dates

    with st.expander("More filters"):
        airline_labels = _label_options(df, "airline_icao", "airline_label")
        picked_airlines = st.multiselect(
            "Select specific airlines (optional)",
            options=list(airline_labels),
            format_func=airline_labels.__getitem__,
            placeholder="All airlines",
        )

    filtered = filter_movements(
        df, start_date, end_date, picked_airports, picked_direction, picked_airlines
    )
    if filtered.empty:
        st.info("No flight movements match the selected filters.")
        return

    totals = filtered[COUNT_COLUMNS].sum()
    overall_share = totals["delayed"] / totals["completed"] if totals["completed"] else None
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Completed movements", f"{totals['completed']:,}")
    k2.metric("Delayed movements", f"{totals['delayed']:,}")
    k3.metric("Delay rate", f"{overall_share:.1%}" if overall_share is not None else "N/A")
    k4.metric("Cancelled movements", f"{totals['cancelled']:,}")

    st.subheader("Delay hotspots by airline and scheduled hour")
    by_airline = summarise(filtered, ["airline_label"])
    by_airline = by_airline.sort_values("completed", ascending=False)
    qualified = by_airline[by_airline["completed"] >= MIN_AIRLINE_COMPLETED]
    if not qualified.empty:
        highest = qualified.sort_values("delayed_share", ascending=False).iloc[0]
        st.caption(
            f"Among airlines with at least {MIN_AIRLINE_COMPLETED} completed movements, "
            f"{highest['airline_label']} has the highest overall delay rate "
            f"({highest['delayed_share']:.1%}) in this selection. "
            "This is an observation, not evidence of cause."
        )

    c_limit, c_counts = st.columns([1, 3])
    limit = c_limit.selectbox("Number of airlines shown", [10, 15, 20, 30], index=0)
    show_counts = c_counts.toggle("Show completed movements in each cell")
    airline_order = by_airline.head(limit)["airline_label"].tolist()
    by_hour = summarise(
        filtered[filtered["airline_label"].isin(airline_order)],
        ["airline_label", "scheduled_hour"],
    )
    grid = prepare_heatmap_grid(by_hour, airline_order)
    st.altair_chart(airline_heatmap(grid, airline_order, show_counts), width="stretch")
    st.caption(
        f"Airlines are sorted by completed movements; the busiest {len(airline_order)} "
        f"are shown. Darker blue means a higher delay rate (maximum shade at "
        f"{SHARE_MAX:.0%}). White cells have fewer than {MIN_COMPLETED} completed "
        "movements; grey means no delays. Cancelled movements are excluded from "
        "delay rates. Hours are scheduled local Swedish time."
    )

    with st.expander("Show the numbers"):
        table = by_airline[
            ["airline_label", "completed", "delayed", "delayed_share", "cancelled"]
        ]
        st.dataframe(
            table,
            hide_index=True,
            column_config={
                "airline_label": "Airline",
                "completed": "Completed movements",
                "delayed": "Delayed movements",
                "delayed_share": st.column_config.NumberColumn("Delay rate", format="percent"),
                "cancelled": "Cancelled movements",
            },
        )


if __name__ == "__main__":
    st.set_page_config(page_title="Airline Delay Hotspots", layout="wide")
    render()
