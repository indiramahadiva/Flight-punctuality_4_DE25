# outputs.tf
# Values that Azure decides. Shown at the end of apply or again with: terraform output

output "login_server" {
  description = "Your registry. Terraform PUSHES both images HERE."
  value       = azurerm_container_registry.acr.login_server
}

output "dagster_url" {
  description = "Dagster UI. Check under AUTOMATION that the schedule is RUNNING at YOUR time."
  value       = var.dagster_ui_public ? "https://${azurerm_container_app.dagster.ingress[0].fqdn}" : "closed (dagster_ui_public = false)"
}

output "dashboard_url" {
  description = "The Streamlit dashboard. The first start PULLS the image and takes a FEW MINUTES."
  value       = "https://${azurerm_linux_web_app.dashboard.default_hostname}"
}
