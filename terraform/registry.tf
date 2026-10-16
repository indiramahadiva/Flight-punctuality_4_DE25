# registry.tf
# The resource group, the registry and the identity that is ALLOWED to pull from it.

# ==== RESOURCE GROUP =====
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# ==== CONTAINER REGISTRY =====
# The name here is GLOBAL across Azure and alphanumeric ONLY, therefore the suffix.
# No admin password - The apps pulls with the identity below.
resource "azurerm_container_registry" "acr" {
  name                = "acrflight${var.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
}

# ===== IDENTITY ====
# One identity without a Password that is SHARED by both apps.
resource "azurerm_user_assigned_identity" "apps" {
  name                = "id-flight-apps"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

# ====== ROLE ASSIGNMENT ======
# The identity will pull images from THIS REGISTRY and nothing more.
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
}
