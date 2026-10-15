# variables.tf
# Our personal values have no default, plan STOPS if one is missing.
# Everything else has a default value that works for all 4 group members.

# ===== PERSONAL INFO - Set in terraform.tfvars =====

variable "subscription_id" {
  description = "Your own Azure subscription id: az account show --query id -o tsv"
  type        = string
}

variable "suffix" {
  description = "Your initials. Makes the registry and web app names UNIQUE across all of Azure."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{2,6}$", var.suffix))
    error_message = "Suffix must be 2-6 lowercase letters or digits, example:  \"jh\"."
  }
}

variable "pipeline_cron" {
  description = "When Your deployed pipeline runs, in Swedish time. One hour apart per group member."
  type        = string


  validation {
    condition     = length(split(" ", trimspace(var.pipeline_cron))) == 5
    error_message = "pipeline_cron needs five fields, example: \"0 18 * * *\". See the table in terraform.tfvars.example."
  }
}

variable "app_env" {
  description = "The values from Your .env. Each app will only get the keys it needs."
  type        = map(string)
  sensitive   = true
}

# ===== SHARED INFO - The defaults work for everyone =====

variable "location" {
  description = "Azure region. Change it if your student subscription does NOT allow this one."
  type        = string
  default     = "swedencentral"
}

# Resource group name: RG
variable "resource_group_name" {
  description = "The resource group that owns everything else."
  type        = string
  default     = "rg-flight-punctuality"
}

variable "image_tag" {
  description = "Tag for both images. Bump it (v2, v3, v69 etc) to rebuild and redeploy after a code change."
  type        = string
  default     = "v1"
}

variable "dagster_ui_public" {
  description = "Dagster has no login. Set to false after the demo to close the UI."
  type        = bool
  default     = true
}
