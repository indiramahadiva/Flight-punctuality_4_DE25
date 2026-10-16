"""Operational Delay Impact & Hotspots: heatmap of delays by airport and scheduled hour.

Reads marts.mart_operational_hotspots with the read-only reporter role.
Run on its own from the repo root:
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/operational_hotspots.py
"""

import altair as alt
import pandas as pd
import snowflake.connector
import streamlit as st

from flight_punctuality.connections import reporter_credentials

# Delay gradient from the group palette: light -> dark blue = little -> much delay.
# #A0BFDC and #263C49 are the palette; the two in between are evenly spaced blends.
HEAT_COLORS = ["#A0BFDC", "#7793AB", "#4F687A", "#263C49"]
SHARE_MAX = 0.25  # 25% delayed or more = darkest, so a few extreme cells do not wash out the rest
MIN_COMPLETED = 5  # below this, a share is too uncertain to colour

# Cells without a delay value, explained in their own legend.
# "Too little data" is white so it fades into the background: the eye should land on the blue.
TOO_LITTLE = f"Too little data (<{MIN_COMPLETED} flights)"
NO_DELAY = "No delays"
STATE_COLORS = {TOO_LITTLE: "#FFFFFF", NO_DELAY: "#DFE0E2"}
OUTLINE_COLOR = "#DFE0E2"  # faint outline so the white cells still show where the grid is
COUNT_COLUMNS = ["movements", "completed", "delayed", "cancelled", "delay_minutes"]


@st.cache_data(ttl=3600)  # read Snowflake at most once an hour
def load_hotspots() -> pd.DataFrame:
    """Read the mart: one row per date, airport, scheduled hour and direction."""
    with snowflake.connector.connect(**reporter_credentials()) as conn:
        cursor = conn.cursor()
        cursor.execute("select * from mart_operational_hotspots")
        df = cursor.fetch_pandas_all()
    df.columns = df.columns.str.lower()  # Snowflake returns UPPERCASE column names
    df["date_key"] = pd.to_datetime(df["date_key"]).dt.date
    df["scheduled_hour"] = df["scheduled_hour"].astype(int)
    df["delay_minutes"] = df["delay_minutes"].astype(float)
    return df


def summarise(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Sum the counts per group, THEN divide. Never average delayed_share."""
    out = df.groupby(by, as_index=False)[COUNT_COLUMNS].sum()
    completed = out["completed"].where(out["completed"] > 0)
    out["delayed_share"] = (out["delayed"] / completed).fillna(0)
    return out


def hotspot_heatmap(
    grid: pd.DataFrame, airport_order: list[str], show_counts: bool = False
) -> alt.LayerChart:
    """Airports down, hours across, colour = share of completed flights that were delayed.

    Every airport gets all 24 hours, so a missing hour is shown, not left blank.
    Each cell is either a delay value (blue), no delays (grey) or too little data (white).
    show_counts writes the number of completed flights in each cell.
    """
    # Every airport x every hour, so hours without flights become visible cells
    full = pd.MultiIndex.from_product(
        [airport_order, range(24)], names=["swedavia_airport_name", "scheduled_hour"]
    ).to_frame(index=False)
    grid = full.merge(grid, how="left", on=["swedavia_airport_name", "scheduled_hour"])
    grid[COUNT_COLUMNS + ["delayed_share"]] = grid[COUNT_COLUMNS + ["delayed_share"]].fillna(0)
    grid["hour_label"] = grid["scheduled_hour"].map(lambda h: f"{h:02d}")

    # Which state each cell is in. None = it has a delay value and gets a blue shade.
    def state(row: pd.Series) -> str | None:
        if row["completed"] < MIN_COMPLETED:
            return TOO_LITTLE
        if row["delayed"] == 0:
            return NO_DELAY
        return None

    grid["cell_state"] = grid.apply(state, axis=1)
    state_cells = grid[grid["cell_state"].notna()]
    value_cells = grid[grid["cell_state"].isna()]

    x = alt.X(
        "hour_label:O",
        title="Scheduled hour (Swedish time)",
        sort=[f"{h:02d}" for h in range(24)],
        axis=alt.Axis(labelAngle=0),
    )
    y = alt.Y("swedavia_airport_name:N", title=None, sort=airport_order, axis=alt.Axis(labelLimit=250))
    tooltip = [
        alt.Tooltip("swedavia_airport_name:N", title="Airport"),
        alt.Tooltip("hour_label:N", title="Hour"),
        alt.Tooltip("completed:Q", title="Completed"),
        alt.Tooltip("delayed:Q", title="Delayed"),
        alt.Tooltip("delayed_share:Q", title="Delayed share", format=".1%"),
        alt.Tooltip("delay_minutes:Q", title="Delay minutes", format=",.0f"),
    ]

    # Layer 1: the three states, with their own legend
    states = list(STATE_COLORS)
    state_layer = (
        alt.Chart(state_cells)
        .mark_rect(strokeWidth=2)
        .encode(
            x=x,
            y=y,
            # white gaps between cells like the blue ones; the white cells get a faint outline
            stroke=alt.Stroke(
                "cell_state:N",
                scale=alt.Scale(domain=states, range=[OUTLINE_COLOR, "white"]),
                legend=None,
            ),
            color=alt.Color(
                "cell_state:N",
                title=None,
                scale=alt.Scale(domain=states, range=[STATE_COLORS[s] for s in states]),
                legend=alt.Legend(symbolType="square", symbolStrokeColor="#AAABB0", symbolSize=200, orient="top"),
            ),
            tooltip=[alt.Tooltip("cell_state:N", title="Cell")] + tooltip,
        )
    )

    # Layer 2: the delayed share, blue gradient.
    # The gradient ends at SHARE_MAX, not at the single highest cell: one extreme value
    # would otherwise stretch the scale and leave every normal cell the same pale colour.
    value_layer = (
        alt.Chart(value_cells)
        .mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=x,
            y=y,
            color=alt.Color(
                "delayed_share:Q",
                title="Delayed share",
                scale=alt.Scale(domain=[0, SHARE_MAX], range=HEAT_COLORS, clamp=True),
                legend=alt.Legend(format=".0%", orient="top", gradientLength=240),
            ),
            tooltip=tooltip,
        )
    )
    layers = state_layer + value_layer

    # Layer 3 (optional): number of completed flights written in each cell.
    # White text on dark blue, dark text on everything lighter, so it stays readable.
    if show_counts:
        dark = grid["cell_state"].isna() & (grid["delayed_share"] / SHARE_MAX >= 0.5)
        counts = grid[grid["completed"] > 0].assign(text_color=dark.map({True: "white", False: "#10120D"}))
        text_layer = (
            alt.Chart(counts)
            .mark_text(fontSize=10)
            .encode(
                x=x,
                y=y,
                text=alt.Text("completed:Q", format=",.0f"),
                color=alt.Color("text_color:N", scale=None),  # use the colour names as they are
                tooltip=tooltip,
            )
        )
        layers = layers + text_layer

    return (
        layers
        .resolve_scale(color="independent")  # two legends: one gradient, one for the states
        .properties(height=alt.Step(28))
    )


def render() -> None:
    """Draw the page. Can be called from a shared multi-page app."""
    st.title("Operational Delay Impact & Hotspots")
    st.caption(
        "When and where is flight delay disruption most significant? "
        "Delayed = landed or departed more than 15 minutes after the scheduled time."
    )

    df = load_hotspots()

    # --- Filters, in one row above the chart ------------------------------------
    col_dates, col_direction = st.columns(2)
    first_day, last_day = df["date_key"].min(), df["date_key"].max()
    picked_dates = col_dates.date_input(
        "Dates", value=(first_day, last_day), min_value=first_day, max_value=last_day
    )
    picked_direction = col_direction.radio(
        "Direction", ["All", "Arrivals", "Departures"], horizontal=True
    )

    start, end = (picked_dates[0], picked_dates[-1]) if picked_dates else (first_day, last_day)
    filtered = df[(df["date_key"] >= start) & (df["date_key"] <= end)]
    if picked_direction != "All":
        filtered = filtered[filtered["direction"] == ("ARR" if picked_direction == "Arrivals" else "DEP")]

    if filtered.empty:
        st.info("No flights match the filters.")
        st.stop()

    # --- Delay hotspots: airport x scheduled hour --------------------------------
    st.subheader("Delay hotspots by airport and hour")
    grid = summarise(filtered, ["swedavia_airport_name", "scheduled_hour"])

    # Busiest airport on top, so the eye starts where most passengers are
    airport_order = (
        summarise(filtered, ["swedavia_airport_name"])
        .sort_values("completed", ascending=False)["swedavia_airport_name"]
        .tolist()
    )
    show_counts = st.toggle("Show number of flights in each cell")
    st.altair_chart(hotspot_heatmap(grid, airport_order, show_counts), width="stretch")

    st.caption(
        f"Darker blue = larger share of completed flights delayed; {SHARE_MAX:.0%} or more is darkest. "
        f"Hours with fewer than {MIN_COMPLETED} completed flights are left white, "
        "since a few flights can swing the share a lot. Hover over a cell for details."
    )


if __name__ == "__main__":
    st.set_page_config(page_title="Operational Hotspots", layout="wide")
    render()