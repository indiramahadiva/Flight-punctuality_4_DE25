# assets_dlt.py, script for our dagster DLT assets.
# dlt sources as our Dagster assets, one asset per dlt resource = one asset per raw table.
# One dlt resource -> one raw table in Snowflake -> one Dagster asset.
import dagster as dg
from dagster_dlt import DagsterDltResource, dlt_assets

# Our dlt pipelines and sources
from flight_punctuality.ingestion.pipelines_swedavia import swedavia_pipeline
from flight_punctuality.ingestion.pipelines_wikipedia import wikipedia_pipeline
from flight_punctuality.ingestion.swedavia import swedavia_source
from flight_punctuality.ingestion.wikipedia import wikipedia_source
from flight_punctuality.settings import AIRPORTS, DAYS_TO_FETCH, get_dates


# used at load time only to read the resource names -> asset keys.
@dlt_assets(
    dlt_source=swedavia_source(AIRPORTS, get_dates(DAYS_TO_FETCH)),
    dlt_pipeline=swedavia_pipeline(),
)
def swedavia_assets(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    # Build the date window inside the run, so it never depends on when or where the code was loaded.
    dates = get_dates(DAYS_TO_FETCH)
    yield from dlt.run(context=context, dlt_source=swedavia_source(AIRPORTS, dates))


@dlt_assets(
    dlt_source=wikipedia_source(),
    dlt_pipeline=wikipedia_pipeline(),
)
def wikipedia_assets(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    # No dates - Will work with full reload of the reference data (Think: write_disposition="replace")
    yield from dlt.run(context=context)
