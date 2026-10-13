# assets_dbt.py
# dbt models as Dagster assets: One asset per model, dbt tests become asset checks
from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# assets_dbt.py -> defs -> flight_punctuality -> src -> repo root
DBT_PROJECT_DIR = Path(__file__).resolve().parents[3] / "dbt_project"

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROJECT_DIR,  # profiles.yml lives next to dbt_project.yml file
    target="prod",  # Dagster builds in the real staging and marts schemas
)

# Under 'dagster dev': runs 'dbt parse' so the manifest is refreshed when the code loads.
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    # build = run + test, in dependency order
    yield from dbt.cli(["build"], context=context).stream()
