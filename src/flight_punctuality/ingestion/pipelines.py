"""Pipeline entry point for ingesting Swedavia flight data.

This module creates a dlt pipeline, prepares the airport and date
configuration, and loads the extracted flight data into Snowflake.
"""

import dlt

from flight_punctuality.connections import loader_credentials
from flight_punctuality.ingestion.swedavia import swedavia_source
from flight_punctuality.settings import AIRPORTS, DAYS_TO_FETCH, get_dates


def swedavia_pipeline() -> dlt.Pipeline:
    """
    Create a dlt pipeline configured to load Swedavia data into Snowflake.

    Returns:
        A configured dlt pipeline.
    """

    return dlt.pipeline(
        pipeline_name="swedavia",  # Identifies this pipeline in dlt.
        destination=dlt.destinations.snowflake(
            credentials=loader_credentials()
        ),  # Connect to Snowflake using credentials from connections.py.
        dataset_name="swedavia_raw",  # Destination schema in Snowflake.
    )


def run_pipeline():
    """
    Extract arrivals and departures for all configured airports and dates.

    Returns:
        Information about the completed dlt load operation.
    """

    # Generate the date window, including today.
    dates = get_dates(DAYS_TO_FETCH)

    # Create the pipeline with its Snowflake configuration.
    pipeline = swedavia_pipeline()

    # Extract flight data and load it into Snowflake.
    return pipeline.run(swedavia_source(AIRPORTS, dates))


# Only execute automatically when this file is run directly.
# Importing run_pipeline from Dagster will not start an ingestion.
if __name__ == "__main__":
    load_info = run_pipeline()
    print(load_info)
