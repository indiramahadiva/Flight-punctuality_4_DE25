
"""Connection settings for the project's data pipelines."""

import os


def loader_credentials() -> dict[str, str]:
    """
    Get Snowflake connection credentials for the dlt ingestion pipeline.

    Returns:
        A dictionary containing the Snowflake connection settings.
    """

    # Read credentials from environment variables instead of hardcoding
    # usernames and passwords in the source code.
    return {
        "host": os.environ["SNOWFLAKE_ACCOUNT"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "username": os.environ["SNOWFLAKE_LOADER_USER"],
        "password": os.environ["SNOWFLAKE_LOADER_PASSWORD"],
        "role": os.environ["SNOWFLAKE_LOADER_ROLE"],
    }
