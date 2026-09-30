data "azurerm_resource_group" "dev" {
  name = "rg-${local.suffix}"
}
data "azurerm_client_config" "current" {}

resource "azurerm_container_registry" "images" {
  name                   = "acraclaradeveastus2"
  resource_group_name    = data.azurerm_resource_group.dev.name
  location               = local.location
  sku                    = "Basic"
  admin_enabled          = false
  anonymous_pull_enabled = false
  tags                   = local.tags
}

resource "azurerm_user_assigned_identity" "api" {
  name                = "id-api-${local.suffix}"
  resource_group_name = data.azurerm_resource_group.dev.name
  location            = local.location
  tags                = local.tags
}
resource "azurerm_user_assigned_identity" "web" {
  name                = "id-web-${local.suffix}"
  resource_group_name = data.azurerm_resource_group.dev.name
  location            = local.location
  tags                = local.tags
}
resource "azurerm_role_assignment" "api_pull" {
  scope                = azurerm_container_registry.images.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}
resource "azurerm_role_assignment" "web_pull" {
  scope                = azurerm_container_registry.images.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.web.principal_id
}

resource "azurerm_key_vault" "dev" {
  name                       = "kv-${local.suffix}"
  resource_group_name        = data.azurerm_resource_group.dev.name
  location                   = local.location
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 7
  purge_protection_enabled   = true
  tags                       = local.tags
}
resource "azurerm_role_assignment" "operator_secrets" {
  scope                = azurerm_key_vault.dev.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}
resource "random_password" "secret" {
  for_each         = toset(["postgres-admin", "postgres-app", "demo-password"])
  length           = 40
  special          = true
  override_special = "!#%+-_="
  min_lower        = 1
  min_upper        = 1
  min_numeric      = 1
  min_special      = 1
}
resource "azurerm_key_vault_secret" "secret" {
  for_each     = random_password.secret
  name         = each.key
  value        = each.value.result
  key_vault_id = azurerm_key_vault.dev.id
  depends_on   = [azurerm_role_assignment.operator_secrets]
}
resource "azurerm_role_assignment" "api_secrets" {
  for_each             = toset(["postgres-app", "demo-password"])
  scope                = azurerm_key_vault_secret.secret[each.key].resource_versionless_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# The owner-supplied key is uploaded separately; its value never enters Terraform state.
resource "azurerm_role_assignment" "api_openrouter_secret" {
  count                = var.enable_real_llm ? 1 : 0
  scope                = "${azurerm_key_vault.dev.id}/secrets/openrouter-api-key"
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

resource "azurerm_role_assignment" "api_typesafe_secret" {
  count                = var.enable_real_llm ? 1 : 0
  scope                = "${azurerm_key_vault.dev.id}/secrets/typesafe-api-key"
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# These secrets are created separately after approval. Terraform never reads
# their values into variables, data sources, plans or state.
resource "azurerm_role_assignment" "api_judge_secrets" {
  for_each             = var.enable_judge_access ? toset(["judge-persona", "judge-password"]) : toset([])
  scope                = "${azurerm_key_vault.dev.id}/secrets/${each.key}"
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

resource "azurerm_postgresql_flexible_server" "dev" {
  name                          = "psql-${local.suffix}"
  resource_group_name           = data.azurerm_resource_group.dev.name
  location                      = local.location
  version                       = "16"
  administrator_login           = "aclara_admin"
  administrator_password        = random_password.secret["postgres-admin"].result
  sku_name                      = "B_Standard_B1ms"
  storage_mb                    = 32768
  auto_grow_enabled             = false
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = true
  authentication {
    active_directory_auth_enabled = false
    password_auth_enabled         = true
  }
  tags = local.tags
  lifecycle {
    prevent_destroy = true
    # Azure selects the initial zone; preserve it on subsequent low-cost dev applies.
    ignore_changes = [zone]
  }
}
resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "aclara"
  server_id = azurerm_postgresql_flexible_server.dev.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}
resource "azurerm_postgresql_flexible_server_configuration" "tls" {
  name      = "require_secure_transport"
  server_id = azurerm_postgresql_flexible_server.dev.id
  value     = "on"
}
resource "azurerm_postgresql_flexible_server_firewall_rule" "owner" {
  name             = "OwnerIPv4"
  server_id        = azurerm_postgresql_flexible_server.dev.id
  start_ip_address = var.owner_ipv4
  end_ip_address   = var.owner_ipv4
}
# Owner-approved dev exception: this includes Azure services in other subscriptions.
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "AllowAllAzureServicesAndResourcesWithinAzureIps"
  server_id        = azurerm_postgresql_flexible_server.dev.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_container_app_environment" "dev" {
  name                = "cae-${local.suffix}"
  resource_group_name = data.azurerm_resource_group.dev.name
  location            = local.location
  logs_destination    = "azure-monitor"
  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
  tags = local.tags
}

resource "azurerm_consumption_budget_resource_group" "dev" {
  name              = "budget-${local.suffix}"
  resource_group_id = data.azurerm_resource_group.dev.id
  amount            = floor(50 * var.budget_usd_to_billing_rate * 100) / 100
  time_grain        = "Monthly"
  time_period {
    start_date = var.budget_start_date
  }
  notification {
    enabled        = true
    threshold      = 60
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = [var.budget_email]
  }
  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = [var.budget_email]
  }
}
