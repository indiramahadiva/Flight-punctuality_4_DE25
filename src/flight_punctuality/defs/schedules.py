# schedules.py script.
# Job = WHAT to run.
# Schedule = WHEN to run it.
import os

import dagster as dg

# All Dagster assets. DBT models will join automatically when they are added into definitions.
pipeline_job = dg.define_asset_job(
    name="pipeline_job",
    selection=dg.AssetSelection.all(),
)


PIPELINE_CRON = os.environ.get("PIPELINE_CRON")

# Daily run at 18:00 Swedish time (without a timezone, CRON will be read as UTC)
daily_schedule = dg.ScheduleDefinition(
    job=pipeline_job,
    cron_schedule=PIPELINE_CRON
    or "0 18 * * *",  # time from .env/tfvars, otherwise at 18:00
    execution_timezone="Europe/Stockholm",  # otherwise cron is read as UTC
    # ON only where PIPELINE_CRON is set, a local Dagster dev run will never accidentally target prod
    default_status=(
        dg.DefaultScheduleStatus.RUNNING
        if PIPELINE_CRON
        else dg.DefaultScheduleStatus.STOPPED
    ),
)
