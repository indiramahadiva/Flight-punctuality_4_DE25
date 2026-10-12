"""Pipeline entry point for ingesting Wikipedia reference data.

This module creates a dlt pipeline and loads the airline and airport
tables from Wikipedia into Snowflake.
"""

import dlt

from flight_punctuality.connections import loader_credentials
from flight_punctuality.ingestion.wikipedia import wikipedia_source


def wikipedia_pipeline() -> dlt.Pipeline:
    """
    Create a dlt pipeline configured to load Wikipedia data into Snowflake.

    Returns:
        A configured dlt pipeline.
    """

    return dlt.pipeline(
        pipeline_name="wikipedia",  # Identifies this pipeline in dlt.
        destination=dlt.destinations.snowflake(
            credentials=loader_credentials()
        ),  # Same Snowflake connection as Swedavia.
        dataset_name="wikipedia_raw",  # Destination schema in Snowflake.
    )


def run_wikipedia_dlt_pipeline():
    """
    Extract the airline and airport tables from Wikipedia.

    Returns:
        Information about the completed dlt load operation.
    """

    # No dates or airports needed: full reload of reference data.
    return wikipedia_pipeline().run(wikipedia_source())


# Only execute automatically when this file is run directly.
# Importing from Dagster will not start an ingestion.
if __name__ == "__main__":
    load_info = run_wikipedia_dlt_pipeline()
    print(load_info)
