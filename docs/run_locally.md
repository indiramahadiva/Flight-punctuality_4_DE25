# Run locally

From a fresh clone to a running pipeline and dashboard on your own machine.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - installs Python 3.12 for you
- A Snowflake **trial** account where you can use `SYSADMIN`, `USERADMIN` and `SECURITYADMIN` 
- A Swedavia API key from [apideveloper.swedavia.se](https://apideveloper.swedavia.se/)


> **Trial accounts only.** The three users sign in with a password. Snowflake is phasing out
> password-only sign-in, and trial accounts are exempt. A paid account needs key-pair
> authentication instead, which this project does not set up.

## 1. Set up Snowflake

Run the scripts in `snowflake_setup/` in order, one worksheet each, with **Run all**.
Each script switches to the role it needs.

| Script | Creates |
|---|---|
| `01_warehouse_database.sql` | warehouse `flights_wh`, database `flights_db` |
| `02_roles.sql` | one role per tool: loader, transformer, reporter |
| `03_schemas.sql` | `swedavia_raw`, `wikipedia_raw`, `staging`, `marts`, each owned by its role |
| `04_grants.sql` | the rights each role needs, and nothing more |
| `05_users.sql` | one user per role: `dlt_user`, `dbt_user`, `streamlit_user` |
| `06_verify_grants.sql` | nothing - checks the roles and the users |

Before you run `05_users.sql`, replace its three password placeholders in the worksheet.
Never save the passwords in the file. The same passwords go into `.env` in step 2.


## 2. Fill in .env

```bash
cp .env.example .env
```

Fill in the API key, your Snowflake account (`orgname-accountname`) and the three passwords from step 1.
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