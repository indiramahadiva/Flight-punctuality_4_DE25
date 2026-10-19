"""Flight punctuality dashboard: one app with a menu in the sidebar.

Start file for all dashboard pages. Each page lives in its own file and has a
render() function; this file only sets up the app and the navigation.
Run from the repo root:
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/main.py
"""

import streamlit as st

from flight_punctuality.dashboard import (
    airline_hotspots,
    app,
    delay_impact,
    operational_hotspots,
)

# Only once per app, and before anything else is drawn
st.set_page_config(page_title="Flight punctuality", layout="wide")

# All pages, in the order they are shown in the menu.
# url_path is needed because every page function is called render(),
# so Streamlit cannot tell them apart by name.
PAGES = [
    # default=True: shown first, at the app's own address (so no url_path needed)
    st.Page(app.render, title="Overview", default=True),
    st.Page(
        operational_hotspots.render,
        title="Airport hotspots",
        url_path="airport-hotspots",
    ),
    st.Page(
        airline_hotspots.render, title="Airline hotspots", url_path="airline-hotspots"
    ),
    st.Page(delay_impact.render, title="Delay impact", url_path="delay-impact"),
]

# position="hidden": Streamlit's own menu would always sit at the very top of the
# sidebar. We hide it and draw the menu ourselves, so the heading can go above it.
current_page = st.navigation(PAGES, position="hidden")

with st.sidebar:
    st.title("Flight punctuality")
    for page in PAGES:
        st.page_link(page)  # one link per page, text only

    # Where the numbers come from, folded away under the menu
    # (same sources as the README)
    st.divider()
    with st.expander("Data sources", type="compact"):  # compact = no frame
        st.markdown(
            "- [Swedavia FlightInfo API](https://apideveloper.swedavia.se/): "
            "arrivals and departures at Swedavia's ten airports\n"
            "- Wikipedia: [airline codes]"
            "(https://en.wikipedia.org/wiki/List_of_airline_codes) and "
            "[international airports]"
            "(https://en.wikipedia.org/wiki/List_of_international_airports_by_country)"
        )

current_page.run()  # draws the page picked in the menu