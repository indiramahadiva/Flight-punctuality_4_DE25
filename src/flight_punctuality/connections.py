
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


def reporter_credentials() -> dict[str, str]:
    """
    Get Snowflake connection settings for the Streamlit dashboard.

    The reporter role can only read the marts schema.

    Returns:
        A dictionary with keyword arguments for snowflake.connector.connect().
    """

    # Same idea as loader_credentials, but with the names the
    # Snowflake connector expects (account, user) instead of dlt's (host, username).
    return {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_REPORTER_USER"],
        "password": os.environ["SNOWFLAKE_REPORTER_PASSWORD"],
        "role": os.environ["SNOWFLAKE_REPORTER_ROLE"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": "marts",
    }