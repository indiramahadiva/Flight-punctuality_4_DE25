# dbt_project

Turns the raw Swedavia and Wikipedia tables into the dimensional model the dashboard reads.

| Folder | Contents | Built as |
|---|---|---|
| `models/staging/` | One cleaned model per source table | views |
| `models/marts/` | Dimensions, the fact table and marts for the dashboard | tables |
| `seeds/` | The ten Swedavia airports | table |
| `tests/` | Singular data tests | - |

Run on its own, from this folder:

```bash
uv run --env-file ../.env dbt build
```

Run by hand, models land in your own schemas (`<DBT_SCHEMA>_staging`, `<DBT_SCHEMA>_marts`).
Run by Dagster, they land in the shared `staging` and `marts`.

Step by step: [Run locally](../docs/run_locally.md)