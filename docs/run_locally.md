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

### Passwords for 05_users.sql

You make up the three passwords - there is nothing to look up.
At least 16 characters, with an uppercase letter, a lowercase letter and a digit. 
Use only letters and digits: quotes break the SQL and the dbt profile.

Write them in a copy, never in `05_users.sql`. Git ignores every file that starts with `setup_user`:

```bash
cp snowflake_setup/05_users.sql snowflake_setup/setup_users.sql
```

Replace the three placeholders in `setup_users.sql`, paste the whole file into a worksheet and click **Run all**.
Keep the copy. The same passwords go into `.env` in step 2.

## 2. Fill in .env

```bash
cp .env.example .env
```

Fill in the API key, your Snowflake account (`orgname-accountname`) and the three passwords from `setup_users.sql`:

| Placeholder in `05_users.sql` | Line in `.env` |
|---|---|
| `<dlt_password>` | `SNOWFLAKE_LOADER_PASSWORD` |
| `<dbt_password>` | `SNOWFLAKE_TRANSFORMER_PASSWORD` |
| `<streamlit_password>` | `SNOWFLAKE_REPORTER_PASSWORD` |

Set `DBT_SCHEMA` to `dbt_<yourname>`: your own schemas when you run dbt by hand.
Leave every other value as it is. It matches `snowflake_setup/`.
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

Open http://localhost:3000, go to **Lineage** and click **Materialize all** in the top right corner.
Dagster loads the raw data with dlt, then builds and tests the dbt models. Wait until every asset is green.

> Dagster always builds into the shared `staging` and `marts` schemas.
> In a shared Snowflake account, tell the group before you run it.

## 5. Open the dashboard

In a second terminal, once every asset is green - before that the marts do not exist:

```bash
uv run --env-file .env streamlit run src/flight_punctuality/dashboard/app.py
```

Open http://localhost:8501.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `05_users.sql` stops at `SET PASSWORD` | A placeholder is left, or a password breaks the rules in step 1 |
| `git status` lists `05_users.sql` as changed | The passwords went into the original. Run `git restore snowflake_setup/05_users.sql` and use the copy |
| dbt says packages are missing | Run `uv run dbt deps --project-dir dbt_project` |
| The dashboard stops with `KeyError: 'SNOWFLAKE_ACCOUNT'` | Start it with `--env-file .env` |
| The dashboard says the table does not exist | Run the pipeline first (step 4) |
| The schedule shows *Stopped* | Expected locally, see step 2 |
