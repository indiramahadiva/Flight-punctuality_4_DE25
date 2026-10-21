# Commands

Every command runs from the repo root unless it says otherwise.

## Dev or prod?

Only dbt has a dev mode. Where your data lands depends on who runs dbt:

| | Dev | Prod |
|---|---|---|
| Who runs dbt | You, by hand | Dagster: locally, in Docker, on Azure |
| dbt target | `dev`, from `DBT_TARGET` in `.env` | `prod`, set in `assets_dbt.py` |
| dbt writes to | `<DBT_SCHEMA>_staging`, `<DBT_SCHEMA>_marts` | `staging`, `marts` |

dlt always loads into the shared `swedavia_raw` and `wikipedia_raw`, and the dashboard
always reads the shared `marts`. Neither has a dev mode.

## Setup, once

```bash
uv sync                                     # all dependency groups
cp .env.example .env                        # then fill in credentials
uv run dbt deps --project-dir dbt_project   # dbt packages
```

## Dev - your own schemas

dbt runs from `dbt_project/`, where `profiles.yml` lives:

```bash
cd dbt_project
uv run --env-file ../.env dbt build                         # seeds, models and tests
uv run --env-file ../.env dbt build -s +mart_delays_daily   # one model and everything upstream
uv run --env-file ../.env dbt test                          # tests only
cd ..
```

Python checks:

```bash
uv run pytest        # unit tests: dlt source and dashboard
uv run ruff check .  # lint
```

## Prod - the shared schemas

> These write to what the whole group sees. Tell the group before you run them.

```bash
# The whole pipeline: dlt, then dbt build -> http://localhost:3000, "Materialize all"
uv run dagster dev

# The same pipeline in containers -> http://localhost:3000 and http://localhost:8501
docker compose up --build

# One source on its own, without Dagster
uv run --env-file .env python -m flight_punctuality.ingestion.pipelines_swedavia
uv run --env-file .env python -m flight_punctuality.ingestion.pipelines_wikipedia

# dbt into the shared schemas by hand
cd dbt_project
uv run --env-file ../.env dbt build --target prod
cd ..
```

## Dashboard

Reads `marts`, so it shows what the last prod run built. Dev runs never show up there.

```bash
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/main.py
```