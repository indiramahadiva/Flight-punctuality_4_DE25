# Run with Docker

Runs the pipeline and the dashboard as two separate containers with Docker Compose.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Snowflake set up and `.env` filled in - [Run locally](run_locally.md), steps 1-2

## 1. Build and start

From the repo root:

```bash
docker compose up --build
```

The first build takes a few minutes. Both containers read `.env` through `env_file` in
`docker-compose.yml`. The file itself is never copied into an image.

## 2. Run the pipeline

Open http://localhost:3000, go to **Lineage** and click **Materialize all** in the top right corner.
As when running locally, this writes to the shared `staging` and `marts` schemas.
The schedule shows *Stopped*: `PIPELINE_CRON` is not set, so nothing runs on its own.

## 3. Open the dashboard

Open http://localhost:8501.

## Stop and clean up

```bash
docker compose down      # stops and removes both containers
docker compose down -v   # also removes the volume with Dagster's run history
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Compose cannot find `.env` | Create it first - Run locally, step 2 |
| Port 3000 or 8501 is already in use | Stop `dagster dev` or Streamlit running outside Docker |
| A code change does not show up | Rebuild: `docker compose up --build` |