# pipeline.tf
# Dagster in a CONTAINER APP: webserver, daemon AND schedule in ONE container.

locals {
  # The keys from app_env the pipeline needs -  dlt (Swedavia + loader) and dbt (transformer)
  pipeline_keys = [
    "SWEDAVIA_API_KEY",
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_LOADER_USER",
    "SNOWFLAKE_LOADER_PASSWORD",
    "SNOWFLAKE_LOADER_ROLE",
    "SNOWFLAKE_TRANSFORMER_USER",
    "SNOWFLAKE_TRANSFORMER_PASSWORD",
    "SNOWFLAKE_TRANSFORMER_ROLE",
  ]
}

# ===== ENVIRONMENT RESOURCE =====
# The counterpart to our compose. 
# No log analytics workspace, logs are STREAMING only which means one less resource.
resource "azurerm_container_app_environment" "main" {
  name                = "cae-flight-punctuality"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

# ===== DAGSTER RESOURCE =====
resource "azurerm_container_app" "dagster" {
  name                         = "dagster"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.apps.id
  }

  # EVERY value our pipeline needs becomes a SECRET. Secret names allow lowercases and dashes ONLY.
  dynamic "secret" {
    for_each = toset(local.pipeline_keys)
    content {
      name  = lower(replace(secret.value, "_", "-"))
      value = var.app_env[secret.value]
    }
  }

  template {
    # At least one replica, the daemon that starts the schedule must always be running
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "dagster"
      image  = local.pipeline_image
      cpu    = 1.0
      memory = "2Gi"

      # The point of the WHOLE deploy -  the schedules time for THIS person.
      # schedules.py reads it with os.environ.get and switches the schedule on.
      env {
        name  = "PIPELINE_CRON"
        value = var.pipeline_cron
      }

      # The secrets as environment variables, with the same names as in .env
      dynamic "env" {
        for_each = toset(local.pipeline_keys)
        content {
          name        = env.value
          secret_name = lower(replace(env.value, "_", "-"))
        }
      }
    }
  }

  ingress {
    external_enabled = var.dagster_ui_public
    target_port      = 3000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  # The image must be in the registry, and the identity must be allowed to pull it
  depends_on = [terraform_data.images, azurerm_role_assignment.acr_pull]
}
