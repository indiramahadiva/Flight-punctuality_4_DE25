# Run locally

From a fresh clone to a running pipeline and dashboard on your own machine.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - installs Python 3.12 for you
- A Snowflake account where you can use `SYSADMIN`, `USERADMIN` and `SECURITYADMIN` (a trial account works)
- A Swedavia API key from [apideveloper.swedavia.se](https://apideveloper.swedavia.se/)

## 1. Set up Snowflake

Run the scripts in `snowflake_setup/` in order, in a Snowflake worksheet.
Each script switches to the role it needs.

| Script | Creates |
|---|---|
| `01_warehouse_database.sql` | warehouse `flights_wh`, database `flights_db` |
| `02_roles.sql` | one role per tool: loader, transformer, reporter |
| `03_schemas.sql` | `swedavia_raw`, `wikipedia_raw`, `staging`, `marts`, each owned by its role |
| `04_grants.sql` | the rights each role needs, and nothing more |
| `05_verify_grants.sql` | nothing - checks the grants, one role at a time |

Then create one user per role:

```sql
USE ROLE USERADMIN;
CREATE USER IF NOT EXISTS dlt_user       PASSWORD = '<password>' DEFAULT_ROLE = flights_loader      DEFAULT_WAREHOUSE = flights_wh;
CREATE USER IF NOT EXISTS dbt_user       PASSWORD = '<password>' DEFAULT_ROLE = flights_transformer DEFAULT_WAREHOUSE = flights_wh;
CREATE USER IF NOT EXISTS streamlit_user PASSWORD = '<password>' DEFAULT_ROLE = flights_reporter    DEFAULT_WAREHOUSE = flights_wh;

USE ROLE SECURITYADMIN;
GRANT ROLE flights_loader      TO USER dlt_user;
GRANT ROLE flights_transformer TO USER dbt_user;
GRANT ROLE flights_reporter    TO USER streamlit_user;
```

## 2. Fill in .env

```bash
cp .env.example .env
```

Fill in the API key, your Snowflake account (`orgname-accountname`) and the three passwords.
Set `DBT_SCHEMA` to `dbt_<yourname>`: your own schemas when you run dbt by hand.
`PIPELINE_CRON` is left out on purpose. Without it, the schedule stays stopped.

## 3. Install dependencies

```bash
uv sync
uv run dbt deps --project-dir dbt_project
```

`uv sync` installs every dependency group. `dbt deps` installs `dbt_utils`, which the models use.

## 4. Run the pipeline

From the repo root, so Dagster picks up `.env`:

```bash
uv run dagster dev
```

Open http://localhost:3000, go to **Assets** and click **Materialize all**.
Dagster loads the raw data with dlt, then builds and tests the dbt models.

> Dagster always builds into the shared `staging` and `marts` schemas.
> In a shared Snowflake account, tell the group before you run it.

## 5. Open the dashboard

In a second terminal:

```bash
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/app.py
```

Open http://localhost:8501.

## Troubleshooting

| Symptom | Fix |
|---|---|
| dbt says packages are missing | Run `uv run dbt deps --project-dir dbt_project` |
| The dashboard stops with `KeyError: 'SNOWFLAKE_ACCOUNT'` | Start it with `--env-file .env` |
| The dashboard says the table does not exist | Run the pipeline first (step 4) |
| The schedule shows *Stopped* | Expected locally, see step 2 |