"""Delay impact: how late are the delayed flights, and where does the delay time pile up?

Two parts of the hotspots plan, next to the heatmap page:
  * Delay severity: delayed flights split into 15-30, 30-60 and 60+ minutes late
  * Accumulated delay time: all minutes late added up, per airport

Reads marts.mart_operational_hotspots (same mart as the heatmap) with the read-only reporter role.
Run on its own from the repo root:
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/delay_impact.py
"""

import altair as alt
import pandas as pd
import snowflake.connector
import streamlit as st

from flight_punctuality.connections import reporter_credentials

# Severity goes from mild to bad, so one blue from light to dark.
# Same blues as the heatmap. #A0BFDC is skipped: too pale on white.
SEVERITY = {
    "delayed_15_30": ("15–30 min", "#7793AB"),
    "delayed_30_60": ("30–60 min", "#4F687A"),
    "delayed_60_plus": ("60+ min", "#263C49"),
}
SEVERITY_LABELS = [label for label, _ in SEVERITY.values()]
SEVERITY_COLORS = [color for _, color in SEVERITY.values()]
BAR_COLOR = "#4F687A"  # one measure = one colour
SURFACE = "#FFFFFF"  # page background, used for the thin gap between stacked segments
TEXT_COLOR = "#10120D"  # theme text colour, for the labels next to the bars
COUNT_COLUMNS = ["completed", "delayed", *SEVERITY, "delay_minutes"]
MIN_DELAYED = 10  # below this, a few flights swing the mix too much to compare


@st.cache_data(ttl=3600)  # read Snowflake at most once an hour
def load_hotspots() -> pd.DataFrame:
    """Read the mart: one row per date, airport, scheduled hour and direction."""
    with snowflake.connector.connect(**reporter_credentials()) as conn:
        cursor = conn.cursor()
        cursor.execute("select * from mart_operational_hotspots")
        df = cursor.fetch_pandas_all()
    df.columns = df.columns.str.lower()  # Snowflake returns UPPERCASE column names
    df["date_key"] = pd.to_datetime(df["date_key"]).dt.date
    df[COUNT_COLUMNS] = df[COUNT_COLUMNS].apply(
        pd.to_numeric
    )  # Snowflake NUMBER can come back as Decimal
    return df


def fmt(n: float) -> str:
    """6678 -> '6 678', Swedish style."""
    return f"{n:,.0f}".replace(",", " ")


def severity_mix(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Delayed flights per group, split by severity, one row per group and bucket.

    Sum the counts per group, THEN divide. Never average shares.
    Groups with fewer than MIN_DELAYED delayed flights are left out.
    """
    totals = df.groupby(by, as_index=False)[COUNT_COLUMNS].sum()
    totals = totals[totals["delayed"] >= MIN_DELAYED]
    totals["avg_minutes_late"] = totals["delay_minutes"] / totals["delayed"]
    long = totals.melt(
        id_vars=[by, "delayed", "avg_minutes_late"],
        value_vars=list(SEVERITY),
        var_name="bucket",
        value_name="flights",
    )
    long["severity"] = long["bucket"].map(
        {key: label for key, (label, _) in SEVERITY.items()}
    )
    long["order"] = long["bucket"].map({key: i for i, key in enumerate(SEVERITY)})
    long["share"] = long["flights"] / long["delayed"]
    return long


SEVERITY_COLOR = alt.Color(
    "severity:N",
    title="Minutes late",
    scale=alt.Scale(domain=SEVERITY_LABELS, range=SEVERITY_COLORS),
    legend=alt.Legend(orient="top"),
)


def mix_tooltip(label_field: str, label_title: str) -> list:
    return [
        alt.Tooltip(label_field, title=label_title),
        alt.Tooltip("severity:N", title="Minutes late"),
        alt.Tooltip("flights:Q", title="Flights"),
        alt.Tooltip("share:Q", title="Share of delayed", format=".0%"),
        alt.Tooltip("delayed:Q", title="Delayed in total"),
        alt.Tooltip("avg_minutes_late:Q", title="Average minutes late", format=".0f"),
    ]


def airport_mix_chart(long: pd.DataFrame) -> alt.Chart:
    """One bar per airport, split into the three buckets. Worst average delay on top."""
    return (
        alt.Chart(long)
        .mark_bar(stroke=SURFACE, strokeWidth=2)  # thin white gap between the buckets
        .encode(
            x=alt.X(
                "share:Q",
                stack="normalize",
                title="Share of delayed flights",
                axis=alt.Axis(format="%"),
            ),
            y=alt.Y(
                "swedavia_airport_name:N",
                title=None,
                sort=alt.EncodingSortField(
                    field="avg_minutes_late", order="descending"
                ),
                axis=alt.Axis(labelLimit=250),
            ),
            color=SEVERITY_COLOR,
            order=alt.Order("order:Q"),
            tooltip=mix_tooltip("swedavia_airport_name:N", "Airport"),
        )
    )


def delay_hours(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Total delay hours per group. Delayed flights and average minutes late go in the tooltip."""
    out = df.groupby(by, as_index=False)[["delayed", "delay_minutes"]].sum()
    out = out[out["delayed"] > 0]
    out["delay_hours"] = out["delay_minutes"] / 60
    out["avg_minutes_late"] = out["delay_minutes"] / out["delayed"]
    return out


HOURS_TOOLTIP = [
    alt.Tooltip("delay_hours:Q", title="Delay hours", format=",.0f"),
    alt.Tooltip("delayed:Q", title="Delayed flights"),
    alt.Tooltip("avg_minutes_late:Q", title="Average minutes late", format=".0f"),
]


def render() -> None:
    """Draw the page. Can be called from a shared multi-page app."""
    st.title("Delay impact")
    st.caption(
        "How late are the delayed flights, and where does the delay time pile up? "
        "Delayed = landed or departed more than 15 minutes after the scheduled time. "
        "Delay minutes count the full delay of each delayed flight."
    )

    df = load_hotspots()

    # --- Filters, in one row above the charts (same as the other pages) --------
    col_dates, col_airports, col_direction = st.columns([2, 3, 2])
    first_day, last_day = df["date_key"].min(), df["date_key"].max()
    picked_dates = col_dates.date_input(
        "Dates", value=(first_day, last_day), min_value=first_day, max_value=last_day
    )
    picked_airports = col_airports.multiselect(
        "Airports",
        sorted(df["swedavia_airport_name"].unique()),
        placeholder="All airports",
    )
    picked_direction = col_direction.radio(
        "Direction", ["All", "Arrivals", "Departures"], horizontal=True
    )

    # While you pick a range, date_input briefly gives only one date
    start, end = (
        (picked_dates[0], picked_dates[-1]) if picked_dates else (first_day, last_day)
    )
    filtered = df[(df["date_key"] >= start) & (df["date_key"] <= end)]
    if picked_airports:
        filtered = filtered[filtered["swedavia_airport_name"].isin(picked_airports)]
    if picked_direction != "All":
        filtered = filtered[
            filtered["direction"]
            == ("ARR" if picked_direction == "Arrivals" else "DEP")
        ]

    totals = filtered[COUNT_COLUMNS].sum()
    if totals["delayed"] == 0:
        st.info("No delayed flights match the filters.")
        st.stop()

    # --- Key numbers: the headline before the charts -----------------------------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Delayed flights",
        fmt(totals["delayed"]),
        help="Completed and more than 15 minutes late",
    )
    k2.metric(
        "Average minutes late",
        f"{totals['delay_minutes'] / totals['delayed']:.0f} min",
        help="Average over the delayed flights only",
    )
    k3.metric(
        "60+ minutes late",
        fmt(totals["delayed_60_plus"]),
        help=f"{totals['delayed_60_plus'] / totals['delayed']:.0%} of the delayed flights",
    )
    k4.metric(
        "Total delay",
        f"{fmt(totals['delay_minutes'] / 60)} h",
        help="All minutes late added together, for the delayed flights",
    )

    # --- Delay severity ---------------------------------------------------------
    st.header("Delay severity")
    st.subheader("How late are the delayed flights?")
    overall = pd.DataFrame(
        {"severity": SEVERITY_LABELS, "flights": [totals[key] for key in SEVERITY]}
    )
    overall["share"] = overall["flights"] / totals["delayed"]
    overall["label"] = overall.apply(
        lambda r: f"{fmt(r['flights'])}  ({r['share']:.0%})", axis=1
    )

    bars = alt.Chart(overall).encode(
        x=alt.X("flights:Q", title="Delayed flights"),
        y=alt.Y("severity:N", title=None, sort=SEVERITY_LABELS),
    )
    overall_chart = bars.mark_bar(cornerRadiusEnd=4, size=20).encode(
        color=alt.Color(
            "severity:N",
            scale=alt.Scale(domain=SEVERITY_LABELS, range=SEVERITY_COLORS),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("severity:N", title="Minutes late"),
            alt.Tooltip("flights:Q", title="Flights"),
            alt.Tooltip("share:Q", title="Share of delayed", format=".0%"),
        ],
    ) + bars.mark_text(align="left", dx=6, color=TEXT_COLOR).encode(
        text="label:N"
    )  # count and % next to each bar
    st.altair_chart(overall_chart.properties(height=140), width="stretch")

    st.subheader("How late, per airport?")
    st.altair_chart(
        airport_mix_chart(severity_mix(filtered, "swedavia_airport_name")),
        width="stretch",
    )
    st.caption(
        f"Sorted by average minutes late, worst at the top. "
        f"Only airports with at least {MIN_DELAYED} delayed flights are shown."
    )

    # --- Accumulated delay time -------------------------------------------------
    # Totals favour busy airports (Arlanda has the most flights), hence the average in the tooltip
    st.header("Accumulated delay time")
    st.caption(
        "All minutes late added together for the delayed flights. Busy airports collect the most hours "
        "simply because they have more flights; compare with the average minutes late in the tooltip."
    )

    st.subheader("Delay hours per airport")
    hours_airport = delay_hours(filtered, "swedavia_airport_name")
    st.altair_chart(
        alt.Chart(hours_airport)
        .mark_bar(color=BAR_COLOR, cornerRadiusEnd=4)
        .encode(
            x=alt.X("delay_hours:Q", title="Delay hours"),
            y=alt.Y(
                "swedavia_airport_name:N",
                title=None,
                sort="-x",
                axis=alt.Axis(labelLimit=250),
            ),
            tooltip=[
                alt.Tooltip("swedavia_airport_name:N", title="Airport"),
                *HOURS_TOOLTIP,
            ],
        ),
        width="stretch",
    )

    # --- The numbers behind the charts ------------------------------------------
    with st.expander("Show the numbers"):
        table = filtered.groupby("swedavia_airport_name", as_index=False)[
            COUNT_COLUMNS
        ].sum()
        table["avg_minutes_late"] = table["delay_minutes"] / table["delayed"].where(
            table["delayed"] > 0
        )
        st.dataframe(
            table[
                [
                    "swedavia_airport_name",
                    "completed",
                    "delayed",
                    *SEVERITY,
                    "avg_minutes_late",
                    "delay_minutes",
                ]
            ].sort_values("delayed", ascending=False),
            hide_index=True,
            column_config={
                "swedavia_airport_name": "Airport",
                "completed": "Completed",
                "delayed": "Delayed",
                **{key: label for key, (label, _) in SEVERITY.items()},
                "avg_minutes_late": st.column_config.NumberColumn(
                    "Avg minutes late", format="%.0f"
                ),
                "delay_minutes": st.column_config.NumberColumn(
                    "Total delay (min)", format="%.0f"
                ),
            },
        )


if __name__ == "__main__":
    st.set_page_config(page_title="Delay impact", layout="wide")
    render()
