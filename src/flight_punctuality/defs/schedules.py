# schedules.py script.
# Job = WHAT to run.
# Schedule = WHEN to run it.
import dagster as dg

# All Dagster assets. DBT models will join automatically when they are added into definitions.
pipeline_job = dg.define_asset_job(
    name="pipeline_job",
    selection=dg.AssetSelection.all(),
)

# Daily run at 18:00 Swedish time (without a timezone, CRON will be read as UTC)
daily_schedule = dg.ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="0 18 * * *",  # minute, hour, day, month, weekday
    execution_timezone="Europe/Stockholm",  # otherwise cron is read as UTC
)
