# docker

One image per container, both built from the repo root by `docker-compose.yml`:

| File | Container | Port |
|---|---|---|
| `Dockerfile.pipeline` | Dagster, with dlt and dbt | 3000 |
| `Dockerfile.dashboard` | Streamlit | 8501 |

```bash
docker compose up --build
```

Step by step: [Run with Docker](../docs/run_with_docker.md)