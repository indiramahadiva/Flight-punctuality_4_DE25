# dashboard.tf
# Streamlit dashboard in a WEB APP per lab requirements. The plan is the "machine" while the app runs on that machine.

locals {
  # The dashboard only reads our marts, the reporter user and then nothing else
  dashboard_keys = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_REPORTER_USER",
    "SNOWFLAKE_REPORTER_PASSWORD",
    "SNOWFLAKE_REPORTER_ROLE",
  ]
}

# ===== APP SERVICE PLAN =====
# B1 is the smallest tier that reliably runs a container.
# It is Billed per hour while it exists.
# So REMEMBER TO DELETE IT AFTER VIDEO IS DONE TO NOT EAT UP ALL CREDITS!!!!!!
resource "azurerm_service_plan" "dashboard" {
  name                = "asp-flight-dashboard"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"
}

# ===== Our WEB APP =====
# The name will become <name>.azurewebsites.net, global across Azure. Thats why the suffix var.suffix is there
resource "azurerm_linux_web_app" "dashboard" {
  name                = "app-flight-dashboard-${var.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.dashboard.id

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  site_config {
    # Pulls from the registry with the identity, no password required
    container_registry_use_managed_identity       = true
    container_registry_managed_identity_client_id = azurerm_user_assigned_identity.apps.client_id

    # Streamlit talks to the browser over websockets automatically.
    websockets_enabled = true

    application_stack {
      docker_image_name   = "flight-dashboard:${var.image_tag}"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
    }
  }

  # The reporters values as environment variables PLUS the port that STREAMLIT listens on
  app_settings = merge(
    { for key in local.dashboard_keys : key => var.app_env[key] },
    { WEBSITES_PORT = "8501" }
  )

  depends_on = [terraform_data.images, azurerm_role_assignment.acr_pull]
}
