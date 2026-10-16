# providers.tf
# azurerm translates the resources in this folder into calls against Azures API.

terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}

provider "azurerm" {
  features {}

  # Each members own subscription, from terraform.tfvars. Each member deploys into their own account.
  subscription_id = var.subscription_id
}
