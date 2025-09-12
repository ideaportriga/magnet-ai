terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.7.0"
    }
  }
  backend "http" {
  }
}

provider "azurerm" {
  subscription_id = var.subscription_id
  features {}
}

resource "azurerm_resource_group" "magnet_rg" {
  name     = var.resource_group_name
  location = "westeurope"
  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_container_app_environment" "aca_env" {
  name                = "frontend-env"
  location            = "westeurope"
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "frontend_app" {
  name                         = "${var.environment}-frontend-app"
  container_app_environment_id = azurerm_container_app_environment.aca_env.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  secret {
    name  = "container-registry-password"
    value = var.acr_password
  }

  registry {
    server               = "${var.acr_name}.azurecr.io"
    username             = var.acr_username
    password_secret_name = "container-registry-password"
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    container {
      name   = "frontend"
      image  = "${var.acr_name}.azurecr.io/${var.environment}/magnet-ai-frontend-app:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "CONFIG_AUTH_ENABLED"
        value = "true"
      }

      env {
        name  = "CONFIG_AUTH_PROVIDER"
        value = "Microsoft"
      }

      env {
        name  = "CONFIG_ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "CONFIG_API_AIBRIDGE_BASEURL"
        value = var.aibridge_base_url
      }

      env {
        name  = "CONFIG_API_AGENTS_BASEURL"
        value = var.agents_base_url
      }

      env {
        name  = "CONFIG_API_SALESFORCE_BASEURL"
        value = var.salesforce_base_url
      }

      env {
        name  = "CONFIG_PANEL_BASEURL"
        value = "https://${var.environment}-frontend-panel.wonderfulmeadow-bef11b6a.westeurope.azurecontainerapps.io"
      }

      env {
        name  = "CONFIG_ADMIN_BASEURL"
        value = "https://${var.environment}-frontend-app.wonderfulmeadow-bef11b6a.westeurope.azurecontainerapps.io"
      }

      env {
        name  = "HELP_BASE_URL"
        value = "/help"
      }
    }

    min_replicas = 1
    max_replicas = 1
  }

  depends_on = [azurerm_container_app.frontend_panel]
}

resource "azurerm_container_app" "frontend_panel" {
  name                         = "${var.environment}-frontend-panel"
  container_app_environment_id = azurerm_container_app_environment.aca_env.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  secret {
    name  = "container-registry-password"
    value = var.acr_password
  }

  registry {
    server               = "${var.acr_name}.azurecr.io"
    username             = var.acr_username
    password_secret_name = "container-registry-password"
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    container {
      name   = "frontend"
      image  = "${var.acr_name}.azurecr.io/${var.environment}/magnet-ai-frontend-panel:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "CONFIG_AUTH_ENABLED"
        value = "true"
      }

      env {
        name  = "CONFIG_AUTH_PROVIDER"
        value = "Microsoft"
      }

      env {
        name  = "CONFIG_ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "CONFIG_API_AIBRIDGE_BASEURL"
        value = var.aibridge_base_url
      }

      env {
        name  = "CONFIG_API_AGENTS_BASEURL"
        value = var.agents_base_url
      }

      env {
        name  = "CONFIG_API_SALESFORCE_BASEURL"
        value = var.salesforce_base_url
      }

      env {
        name  = "CONFIG_THEME"
        value = var.theme
      }

      env {
        name  = "CONFIG_PANEL_BASEURL"
        value = "https://${var.environment}-frontend-panel.wonderfulmeadow-bef11b6a.westeurope.azurecontainerapps.io"
      }

      env {
        name  = "CONFIG_ADMIN_BASEURL"
        value = "https://${var.environment}-frontend-app.wonderfulmeadow-bef11b6a.westeurope.azurecontainerapps.io"
      }
    }

    min_replicas = 1
    max_replicas = 1
  }
}
