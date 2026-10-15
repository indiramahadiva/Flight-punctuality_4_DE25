"""
Prototype
"""

import snowflake.connector
import streamlit as st

from flight_punctuality.connections import reporter_credentials


def render() -> None:
    """Render the page. Add charts later"""
    st.title("Operational Hotspots")
    st.caption("")

    # Placeholder for future KPI cards, filters, charts
    st.empty()


if __name__ == "__main__":
    st.set_page_config(page_title = "Operational Hotspots", layout = "wide")
    render()

    