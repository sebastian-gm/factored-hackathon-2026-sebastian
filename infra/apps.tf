locals {
  api_url = "https://ca-api-${local.suffix}.${azurerm_container_app_environment.dev.default_domain}"
  web_url = "https://ca-web-${local.suffix}.${azurerm_container_app_environment.dev.default_domain}"
}

resource "azurerm_container_app" "api" {
  count                        = var.deploy_apps ? 1 : 0
  name                         = "ca-api-${local.suffix}"
  resource_group_name          = data.azurerm_resource_group.dev.name
  container_app_environment_id = azurerm_container_app_environment.dev.id
  workload_profile_name        = "Consumption"
  revision_mode                = "Single"
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.api.id]
  }
  registry {
    server   = azurerm_container_registry.images.login_server
    identity = azurerm_user_assigned_identity.api.id
  }
  dynamic "secret" {
    for_each = toset(["postgres-app", "demo-password"])
    content {
      name                = secret.value
      key_vault_secret_id = azurerm_key_vault_secret.secret[secret.value].versionless_id
      identity            = azurerm_user_assigned_identity.api.id
    }
  }
  ingress {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8000
    transport                  = "http"
    ip_security_restriction {
      name             = "owner-only"
      action           = "Allow"
      ip_address_range = "${var.owner_ipv4}/32"
    }
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
  template {
    min_replicas = 0
    max_replicas = 1
    container {
      name   = "api"
      image  = "${azurerm_container_registry.images.login_server}/aclara-api:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"
      dynamic "env" {
        for_each = {
          PGHOST        = azurerm_postgresql_flexible_server.dev.fqdn
          PGPORT        = "5432", PGUSER = "aclara_app", PGDATABASE = "aclara"
          PGSSLMODE     = "verify-full", PGSSLROOTCERT = "/etc/ssl/certs/ca-certificates.crt"
          DEMO_USERNAME = "demo.es.mx", LLM_PROVIDER = "mock"
          BANK_CLOCK    = "2026-06-18T06:00:00Z", WEB_ORIGIN = local.web_url
          RELEASE_SHA   = var.image_tag
          OPS_BACKEND   = "postgres", AGENT_SYSTEM = "P"
        }
        content {
          name  = env.key
          value = env.value
        }
      }
      env {
        name        = "PGPASSWORD"
        secret_name = "postgres-app"
      }
      env {
        name        = "DEMO_PASSWORD"
        secret_name = "demo-password"
      }
      liveness_probe {
        transport        = "HTTP"
        port             = 8000
        path             = "/healthz"
        initial_delay    = 10
        interval_seconds = 30
      }
      readiness_probe {
        transport               = "HTTP"
        port                    = 8000
        path                    = "/readyz"
        interval_seconds        = 10
        timeout                 = 5
        failure_count_threshold = 6
      }
    }
  }
  tags       = merge(local.tags, { release = var.image_tag })
  depends_on = [azurerm_role_assignment.api_pull, azurerm_role_assignment.api_secrets]
}

resource "azurerm_container_app" "web" {
  count                        = var.deploy_apps ? 1 : 0
  name                         = "ca-web-${local.suffix}"
  resource_group_name          = data.azurerm_resource_group.dev.name
  container_app_environment_id = azurerm_container_app_environment.dev.id
  workload_profile_name        = "Consumption"
  revision_mode                = "Single"
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.web.id]
  }
  registry {
    server   = azurerm_container_registry.images.login_server
    identity = azurerm_user_assigned_identity.web.id
  }
  ingress {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 3000
    transport                  = "http"
    ip_security_restriction {
      name             = "owner-only"
      action           = "Allow"
      ip_address_range = "${var.owner_ipv4}/32"
    }
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
  template {
    min_replicas = 0
    max_replicas = 1
    container {
      name   = "web"
      image  = "${azurerm_container_registry.images.login_server}/aclara-web:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"
      env {
        name  = "BROWSER_API_BASE_URL"
        value = local.api_url
      }
      env {
        name  = "RELEASE_SHA"
        value = var.image_tag
      }
      readiness_probe {
        transport        = "HTTP"
        port             = 3000
        path             = "/"
        interval_seconds = 10
        timeout          = 5
      }
    }
  }
  tags       = merge(local.tags, { release = var.image_tag })
  depends_on = [azurerm_role_assignment.web_pull]
}

output "api_url" {
  value = local.api_url
}
output "web_url" {
  value = local.web_url
}
