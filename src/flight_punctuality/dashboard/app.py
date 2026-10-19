"""Flight punctuality dashboard: share of delayed flights at Swedavia's ten airports.

Reads marts.mart_delays_daily with the read-only reporter role.
Overview page of the multi-page dashboard (see main.py).
Run on its own from the repo root:
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/app.py
"""

import altair as alt
import pandas as pd
import snowflake.connector
import streamlit as st

from flight_punctuality.connections import reporter_credentials

BAR_COLOR = "#2a78d6"  # one colour: every chart shows a single measure
MIN_COMPLETED = 20  # airlines with fewer completed flights are too small to compare
TOP_AIRLINES = 15  # the busiest airlines, so the chart stays readable
COUNT_COLUMNS = ["movements", "completed", "delayed", "cancelled"]


@st.cache_data(ttl=3600)  # read Snowflake at most once an hour
def load_mart() -> pd.DataFrame:
    """Read the whole mart. It is small: one row per date, airport, airline and direction."""
    with snowflake.connector.connect(**reporter_credentials()) as conn:
        cursor = conn.cursor()
        cursor.execute("select * from mart_delays_daily")
        df = cursor.fetch_pandas_all()
    df.columns = df.columns.str.lower()  # Snowflake returns UPPERCASE column names
    df["date_key"] = pd.to_datetime(df["date_key"]).dt.date
    return df


def summarise(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Sum the counts per group, THEN divide. Never average delayed_share."""
    out = df.groupby(by, as_index=False)[COUNT_COLUMNS].sum()
    completed = out["completed"].where(out["completed"] > 0)  # avoid dividing by zero
    out["delayed_share"] = (out["delayed"] / completed).fillna(0)
    return out


def share_bars(data: pd.DataFrame, label: str, label_title: str) -> alt.Chart:
    """Horizontal bars of delayed share, highest first."""
    return (
        alt.Chart(data)
        .mark_bar(color=BAR_COLOR, cornerRadiusEnd=4)
        .encode(
            x=alt.X("delayed_share:Q", title="Delayed share", axis=alt.Axis(format="%")),
            y=alt.Y(f"{label}:N", title=None, sort="-x", axis=alt.Axis(labelLimit=250)),
            tooltip=[
                alt.Tooltip(f"{label}:N", title=label_title),
                alt.Tooltip("delayed_share:Q", title="Delayed share", format=".1%"),
                alt.Tooltip("delayed:Q", title="Delayed"),
                alt.Tooltip("completed:Q", title="Completed"),
            ],
        )
    )


def render() -> None:
    """Draw the page. Called from main.py, or directly when this file is run on its own."""
    # --- Header -----------------------------------------------------------------
    st.title("Flight punctuality at Swedavia's airports")
    st.caption(
        "Delayed = landed or departed more than 15 minutes after the scheduled time. "
        "Delayed share = delayed / completed flights. Cancelled flights are shown separately."
    )

    df = load_mart()

    # --- Filters, in one row above the charts ------------------------------------
    col_dates, col_airports, col_direction = st.columns([2, 3, 2])
    first_day, last_day = df["date_key"].min(), df["date_key"].max()
    picked_dates = col_dates.date_input(
        "Dates", value=(first_day, last_day), min_value=first_day, max_value=last_day
    )
    picked_airports = col_airports.multiselect(
        "Airports", sorted(df["swedavia_airport_name"].unique()), placeholder="All airports"
    )
    picked_direction = col_direction.radio(
        "Direction", ["All", "Arrivals", "Departures"], horizontal=True
    )

    # While the user is picking a range, date_input briefly returns only one date
    start, end = (picked_dates[0], picked_dates[-1]) if picked_dates else (first_day, last_day)

    filtered = df[(df["date_key"] >= start) & (df["date_key"] <= end)]
    if picked_airports:
        filtered = filtered[filtered["swedavia_airport_name"].isin(picked_airports)]
    if picked_direction != "All":
        filtered = filtered[filtered["direction"] == ("ARR" if picked_direction == "Arrivals" else "DEP")]

    if filtered.empty:
        st.info("No flights match the filters.")
        st.stop()

    # --- Key numbers --------------------------------------------------------------
    totals = filtered[COUNT_COLUMNS].sum()
    share = totals["delayed"] / totals["completed"] if totals["completed"] else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Movements", f"{totals['movements']:,}".replace(",", " "))
    k2.metric("Completed", f"{totals['completed']:,}".replace(",", " "))
    k3.metric("Delayed share", f"{share:.1%}")
    k4.metric("Cancelled", f"{totals['cancelled']:,}".replace(",", " "))

    # --- Per airport and per airline ---------------------------------------------
    left, right = st.columns(2)

    with left:
        st.subheader("By airport")
        by_airport = summarise(filtered, ["swedavia_airport_name"])
        st.altair_chart(share_bars(by_airport, "swedavia_airport_name", "Airport"), width="stretch")

    with right:
        st.subheader("By airline")
        by_airline = summarise(filtered, ["airline_name"])
        by_airline = by_airline[by_airline["completed"] >= MIN_COMPLETED]
        by_airline = by_airline.nlargest(TOP_AIRLINES, "completed")
        st.altair_chart(share_bars(by_airline, "airline_name", "Airline"), width="stretch")
        st.caption(
            f"The {TOP_AIRLINES} busiest airlines with at least {MIN_COMPLETED} completed flights."
        )

    # --- Per day -------------------------------------------------------------------
    st.subheader("By day")
    by_day = summarise(filtered, ["date_key"])
    by_day["date_key"] = pd.to_datetime(by_day["date_key"])
    day_chart = (
        alt.Chart(by_day)
        .mark_line(color=BAR_COLOR, strokeWidth=2, point=alt.OverlayMarkDef(color=BAR_COLOR, size=64))
        .encode(
            x=alt.X("date_key:T", title=None, axis=alt.Axis(format="%a %d %b", tickCount="day")),
            y=alt.Y("delayed_share:Q", title="Delayed share", axis=alt.Axis(format="%")),
            tooltip=[
                alt.Tooltip("date_key:T", title="Date", format="%A %d %B"),
                alt.Tooltip("delayed_share:Q", title="Delayed share", format=".1%"),
                alt.Tooltip("delayed:Q", title="Delayed"),
                alt.Tooltip("completed:Q", title="Completed"),
                alt.Tooltip("cancelled:Q", title="Cancelled"),
            ],
        )
    )
    st.altair_chart(day_chart, width="stretch")

    # --- The numbers behind the charts --------------------------------------------
    with st.expander("Show the numbers"):
        table = summarise(filtered, ["date_key", "swedavia_airport_name"])
        st.dataframe(
            table,
            hide_index=True,
            column_config={
                "date_key": "Date",
                "swedavia_airport_name": "Airport",
                "delayed_share": st.column_config.NumberColumn("Delayed share", format="percent"),
            },
        )


if __name__ == "__main__":
    st.set_page_config(page_title="Flight punctuality", layout="wide")
    render()