# All identifiers below are synthetic. Both providers are mocked; plans only.
mock_provider "azurerm" {
  mock_data "azurerm_resource_group" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg-authored"
    }
  }
}
mock_provider "random" {}

variables {
  subscription_id   = "00000000-0000-0000-0000-000000000001"
  tenant_id         = "00000000-0000-0000-0000-000000000002"
  owner_ipv4        = "192.0.2.10"
  budget_email      = "fixture@example.invalid"
  budget_start_date = "2026-09-01T00:00:00Z"
  image_tag         = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  deploy_apps       = true
  enable_real_llm   = false
  llm_budget_run_id = ""
}

run "off_defaults" {
  command = plan
  assert {
    condition     = azurerm_container_app.api[0].template[0].min_replicas == 0 && azurerm_container_app.web[0].template[0].min_replicas == 0
    error_message = "Testing must scale both apps to zero."
  }
  assert {
    condition     = length(azurerm_container_app.web[0].ingress[0].ip_security_restriction) == 1 && length(azurerm_role_assignment.api_judge_secrets) == 0
    error_message = "Default must preserve owner ingress and no judge secret access."
  }
  assert {
    condition     = !azurerm_container_app.api[0].ingress[0].external_enabled
    error_message = "API must stay internal."
  }
}

run "warm_plan_only" {
  command = plan
  variables {
    enable_submission_warm = true
    min_replicas           = 1
  }
  assert {
    condition     = azurerm_container_app.api[0].template[0].min_replicas == 1 && azurerm_container_app.web[0].template[0].min_replicas == 1
    error_message = "Approved warm option covers both existing apps."
  }
  assert {
    condition     = length(azurerm_container_app.web[0].ingress[0].ip_security_restriction) == 1
    error_message = "Warm replicas must not change ingress."
  }
}

run "judge_plan_only" {
  command = plan
  variables {
    enable_judge_access = true
    llm_budget_run_id   = "judging-2026-10"
  }
  assert {
    condition     = length(azurerm_container_app.web[0].ingress[0].ip_security_restriction) == 0 && !azurerm_container_app.web[0].ingress[0].allow_insecure_connections
    error_message = "Only approved judge mode opens HTTPS web ingress."
  }
  assert {
    condition     = !azurerm_container_app.api[0].ingress[0].external_enabled && length(azurerm_role_assignment.api_judge_secrets) == 2
    error_message = "API stays internal and receives only the two judge secret scopes."
  }
  assert {
    condition     = alltrue([for s in azurerm_container_app.api[0].secret : s.value == null || s.value == ""])
    error_message = "Container Apps secrets must be Key Vault references, never literal values."
  }
  assert {
    condition     = one([for e in azurerm_container_app.api[0].template[0].container[0].env : e.value if e.name == "LLM_DAILY_BUDGET_USD"]) == "1" && one([for e in azurerm_container_app.api[0].template[0].container[0].env : e.value if e.name == "JUDGE_ACCESS_ENABLED"]) == "true" && one([for e in azurerm_container_app.api[0].template[0].container[0].env : e.value if e.name == "LLM_BUDGET_RUN_ID"]) == "judging-2026-10"
    error_message = "Judge mode, USD 1/day and its lifetime run must be enabled together."
  }
}

run "judge_requires_lifetime_run" {
  command = plan
  variables {
    enable_judge_access = true
  }
  expect_failures = [var.enable_judge_access]
}

run "warm_requires_switch" {
  command = plan
  variables {
    min_replicas = 1
  }
  expect_failures = [var.min_replicas]
}

run "judge_rejects_smoke_lifetime" {
  command = plan
  variables {
    enable_judge_access = true
    llm_budget_run_id   = "after-v2-release-smoke"
  }
  expect_failures = [var.enable_judge_access]
}

run "sha_bound_release_smoke" {
  command = plan
  variables {
    llm_budget_run_id = "pre-v4-release-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  assert {
    condition     = one([for e in azurerm_container_app.api[0].template[0].container[0].env : e.value if e.name == "LLM_BUDGET_RUN_ID"]) == var.llm_budget_run_id && azurerm_container_app.api[0].template[0].min_replicas == 0 && length(azurerm_container_app.web[0].ingress[0].ip_security_restriction) == 1
    error_message = "SHA-bound release accounting must preserve scale-to-zero and owner ingress."
  }
}

run "sha_bound_latency_smoke" {
  command = plan
  variables {
    llm_budget_run_id = "pre-v4-latency-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  assert {
    condition     = one([for e in azurerm_container_app.api[0].template[0].container[0].env : e.value if e.name == "LLM_BUDGET_RUN_ID"]) == var.llm_budget_run_id && !azurerm_container_app.api[0].ingress[0].external_enabled
    error_message = "Latency accounting must bind the exact run and keep the API internal."
  }
}

run "smoke_rejects_short_sha" {
  command = plan
  variables {
    llm_budget_run_id = "pre-v4-release-aaaaaaa"
  }
  expect_failures = [var.llm_budget_run_id]
}

run "smoke_rejects_unapproved_kind" {
  command = plan
  variables {
    llm_budget_run_id = "pre-v4-uncapped-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  expect_failures = [var.llm_budget_run_id]
}

run "judge_rejects_sha_bound_smoke" {
  command = plan
  variables {
    enable_judge_access = true
    llm_budget_run_id   = "pre-v4-latency-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  expect_failures = [var.enable_judge_access]
}

run "burst_scale_off_by_default" {
  command = plan
  assert {
    condition     = azurerm_container_app.api[0].template[0].max_replicas == 1 && length(azurerm_container_app.api[0].template[0].http_scale_rule) == 0
    error_message = "Testing must preserve max 1 and no custom scaling rule."
  }
}

run "burst_scale_plan_only" {
  command = plan
  variables {
    enable_submission_warm  = true
    enable_submission_scale = true
    min_replicas            = 1
  }
  assert {
    condition     = azurerm_container_app.api[0].template[0].min_replicas == 1 && azurerm_container_app.api[0].template[0].max_replicas == 3 && azurerm_container_app.web[0].template[0].min_replicas == 1 && azurerm_container_app.web[0].template[0].max_replicas == 1
    error_message = "Gate A warms both apps; only the API has three-replica burst capacity."
  }
  assert {
    condition     = one(azurerm_container_app.api[0].template[0].http_scale_rule).concurrent_requests == "5" && !azurerm_container_app.api[0].ingress[0].external_enabled && length(azurerm_container_app.web[0].ingress[0].ip_security_restriction) == 1
    error_message = "HTTP scaling must retain internal API and owner-IP web."
  }
  assert {
    condition     = azurerm_container_app.api[0].template[0].container[0].cpu == 0.25 && azurerm_container_app.api[0].template[0].container[0].memory == "0.5Gi"
    error_message = "Gate A does not resize compute."
  }
}

run "burst_scale_requires_warm" {
  command = plan
  variables {
    enable_submission_scale = true
  }
  expect_failures = [var.enable_submission_scale]
}
