# definitions.py
# The ONLY file that Dagster starts from.
import dagster as dg
from dagster_dbt import DbtCliResource
from dagster_dlt import DagsterDltResource

# DBT assets
from flight_punctuality.defs.assets_dbt import dbt_models, dbt_project

# DLT assets
from flight_punctuality.defs.assets_dlt import swedavia_assets, wikipedia_assets

# Our JOBS and Schedule
from flight_punctuality.defs.schedules import daily_schedule, pipeline_job

# The key 'dlt' MUST match the parameter name 'dlt' in the ASSET FUNCTIONS.
defs = dg.Definitions(
    assets=[swedavia_assets, wikipedia_assets, dbt_models],
    resources={
        "dlt": DagsterDltResource(),
        "dbt": DbtCliResource(
            project_dir=dbt_project
        ),  # key "dbt" = parameter name in dbt_models
    },
    jobs=[pipeline_job],
    schedules=[daily_schedule],
)
