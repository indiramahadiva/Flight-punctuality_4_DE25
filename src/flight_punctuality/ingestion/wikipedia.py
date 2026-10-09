"""dlt source: Wikipedia reference data (airlines + airports)."""

from io import StringIO

import dlt
import pandas as pd
import requests
from lxml import html

# tell Wikipedia who we are, otherwise it may block us (403)
HEADERS = {"User-Agent": "FlightPunctualityStudentProject/0.1 (school project)"}
AIRLINES_URL = "https://en.wikipedia.org/wiki/List_of_airline_codes"
AIRPORTS_URL = "https://en.wikipedia.org/wiki/List_of_international_airports_by_country"
AIRPORT_COLUMNS = ["Location", "Airport", "IATA Code"]


def _get(url):
    # fetch a page, crash loudly if it fails
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def _to_records(df):
    # DataFrame -> list of dicts, with NaN turned into proper None (null in the db)
    return df.astype(object).where(df.notna(), None).to_dict("records")


@dlt.resource(name="airlines", write_disposition="replace")
def airlines():
    # only one table on the page - load it untouched, cleaning happens in dbt
    table = pd.read_html(StringIO(_get(AIRLINES_URL)))[0]
    yield _to_records(table)


@dlt.resource(name="airports", write_disposition="replace")
def airports():
    page = html.fromstring(_get(AIRPORTS_URL))
    frames = []
    for table in page.xpath("//table[contains(@class, 'wikitable')]"):  # skips navboxes
        # the nearest heading above the table = the country
        heading = table.xpath("preceding::*[self::h2 or self::h3 or self::h4][1]")
        country = heading[0].text_content().strip() if heading else None

        df = pd.read_html(StringIO(html.tostring(table, encoding="unicode")))[0]
        df = df.reindex(
            columns=AIRPORT_COLUMNS
        )  # missing column -> blank instead of crash
        df["Country"] = country
        frames.append(df)

    yield _to_records(pd.concat(frames, ignore_index=True))


@dlt.source(name="wikipedia")
def wikipedia_source():
    return airlines, airports


if __name__ == "__main__":
    # local test only: loads into a DuckDB file in your scratch folder
    pipeline = dlt.pipeline(
        pipeline_name="wikipedia_indira_local",  # personal name so we don't clash with anyone
        destination=dlt.destinations.duckdb("scratch/indira/wikipedia.duckdb"),
        dataset_name="wikipedia_raw",
    )
    print(pipeline.run(wikipedia_source()))
