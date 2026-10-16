# images.tf
# Terraform both BUILDS and PUSHES both images itself between the registry and the apps.
# REQUIRES that DOCKER DESKTOP IS RUNNING and your AZ LOGIN is done!
# One command PER provisioner so it works the same in CMD, POWERSHELL and BASH.

locals {
  pipeline_image  = "${azurerm_container_registry.acr.login_server}/flight-pipeline:${var.image_tag}"
  dashboard_image = "${azurerm_container_registry.acr.login_server}/flight-dashboard:${var.image_tag}"
}

resource "terraform_data" "images" {
  # Runs again ONLY when the registry or the TAG changes. Bump the image_tag AFTER a code change.
  triggers_replace = [azurerm_container_registry.acr.id, var.image_tag]

  # Docker gets a token for the registry from your AZ login and once its done.
  provisioner "local-exec" {
    command = "az acr login --name ${azurerm_container_registry.acr.name}"

  }

  # Build from the REPO ROOT, the same context as our docker-compose.yml.
  # linux/amd64 is what Azure runs internally, also when building on an ARM Mac computer.
  provisioner "local-exec" {
    command     = "docker build --platform linux/amd64 -f docker/Dockerfile.pipeline -t ${local.pipeline_image} ."
    working_dir = "${path.module}/.."
  }

  provisioner "local-exec" {
    command = "docker push ${local.pipeline_image}"
  }
  provisioner "local-exec" {
    command     = "docker build --platform linux/amd64 -f docker/Dockerfile.dashboard -t ${local.dashboard_image} ."
    working_dir = "${path.module}/.."
  }

  provisioner "local-exec" {
    command = "docker push ${local.dashboard_image}"
  }
}
