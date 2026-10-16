# terraform

Deploys the pipeline and the dashboard into your own Azure account. The code is the same for all four,
everything personal is in your own `terraform.tfvars`.

| File | Creates |
|---|---|
| `providers.tf` | The azurerm provider, pointed at your subscription |
| `variables.tf` | Every input. Personal values have no default |
| `registry.tf` | Resource group, container registry and the identity that pulls from it |
| `images.tf` | Builds and pushes both images |
| `pipeline.tf` | Dagster in a Container App, on your `pipeline_cron` |
| `dashboard.tf` | Streamlit in a Web App |
| `outputs.tf` | Registry address, Dagster URL and dashboard URL |
| `terraform.tfvars.example` | The template you copy to `terraform.tfvars` |

From this folder:

```bash
terraform init
terraform plan -out tfplan
terraform apply tfplan
terraform destroy    # when you are done, it costs as long as it exists
```

`terraform.tfvars`, `*.tfstate` and `tfplan` hold your secrets in plain text. They and `.terraform/` are in
`.gitignore`. `.terraform.lock.hcl` is committed, so all four get the same provider version.

Step by step: [Deploy to Azure](../docs/deploy_to_azure.md)
