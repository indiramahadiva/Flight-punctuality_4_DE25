# Deploy to Azure

Deploys the pipeline (Dagster) and the dashboard (Streamlit) into your own Azure account with one `terraform apply`. Terraform creates the registry, builds and pushes both images, and creates the apps. Each person deploys their own copy, with their own schedule.

## What gets created

| Resource | Name | Why |
|---|---|---|
| Resource group | `rg-flight-punctuality` | Owns everything else - one `destroy` removes it all |
| Container registry | `acrflight<suffix>` | Holds the two images |
| Managed identity | `id-flight-apps` | Lets both apps pull images without a password |
| Container App | `dagster` | The pipeline. Always one replica running, so the schedule can start |
| Web App | `app-flight-dashboard-<suffix>` | The dashboard |

## Prerequisites

- An Azure account - Azure for Students works
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [Terraform](https://developer.hashicorp.com/terraform/install) 1.9 or later
- [Docker Desktop](https://www.docker.com/products/docker-desktop/), **running** - Terraform builds the images with it
- `.env` filled in - [Run locally](run_locally.md), steps 1-2

## 1. Log in to Azure

```bash
terraform -version                    # 1.9 or later
az version
az login                              # opens the browser - sign in to your own account
az account show --output table        # the active subscription - check that it is yours
az account show --query id -o tsv     # your subscription id, needed in step 2
```

`az login` lists your subscriptions and asks you to pick one. Type the **number** in the first
column (`1`), or press Enter to keep the one marked `*`. Pasting the id gives *Invalid selection*.

Several subscriptions? List them and pick the right one:

```bash
az account list --output table
az account set --subscription "<name or id>"
```

## 2. Fill in your variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Open `terraform.tfvars` and fill in:

| Variable | Value |
|---|---|
| `subscription_id` | The id from step 1 |
| `suffix` | Your initials, lowercase - makes your registry and web app names unique |
| `pipeline_cron` | Your time from the table below |
| `app_env` | The values from your `.env` |

| Person | `pipeline_cron` | Runs at (Swedish time) |
|---|---|---|
| Johnny | `0 18 * * *` | 18:00 |
| Indira | `0 19 * * *` | 19:00 |
| Aira | `0 20 * * *` | 20:00 |
| Christoffer | `0 21 * * *` | 21:00 |

All four deploys write to the same Snowflake account. One hour apart, two runs never share
dlt's temporary tables at the same time.

## 3. Deploy

Still in `terraform/`:

```bash
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

The apply creates the registry, then builds and pushes both images (the slow part, several
minutes), then creates the apps.

## 4. Check it

```bash
terraform output
```

- `dagster_url` - open it, go to **Automation** and click `schedule`. The toggle is **on** and
  *Next tick* shows your time. A stopped schedule has no next tick. Check the toggle, not only the
  time: `0 18 * * *` is also the fallback in `schedules.py`
- `dashboard_url` - the first load takes about 30 seconds while the container and the Snowflake
  warehouse wake up. Reload, and it is fast

A **Materialize** in the Azure Dagster writes to the shared `staging` and `marts`, exactly as locally.

## After a code change

Bump `image_tag` in `terraform.tfvars` (`"v2"`, `"v3"` ...) and run step 3 again.
Terraform rebuilds both images and both apps switch to the new tag.

## After the demo - close the Dagster UI

Dagster has no login. Set `dagster_ui_public = false` in `terraform.tfvars` and run step 3
again. The schedule keeps running, only the UI closes.

## Tear down

```bash
terraform destroy
```

The Container App always runs one replica and the Web App plan is billed per hour, both
for as long as they exist. Destroy when the course is over.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `az acr login` or `docker build` fails | Start Docker Desktop and run step 3 again |
| Registry or web app name already exists | Someone in Azure has that name - change `suffix` |
| `The subscription is not registered to use namespace Microsoft.App` | `az provider register --namespace Microsoft.App`, wait a minute, run step 3 again. Same for `Microsoft.Web` and `Microsoft.ContainerRegistry` |
| Region not allowed by policy | Azure for Students only allows some regions - set `location` in `terraform.tfvars` |
| `The given key does not identify an element in this collection value` | A key is missing in `app_env` - copy every line from `.env` |
| Dagster run fails on Snowflake login | A value in `app_env` is empty or wrong - compare with `.env` |
| Dashboard logs | `az webapp log tail --name app-flight-dashboard-<suffix> --resource-group rg-flight-punctuality` |
| Dagster logs | `az containerapp logs show --name dagster --resource-group rg-flight-punctuality --follow` |
