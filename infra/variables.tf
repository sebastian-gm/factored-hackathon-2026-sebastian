variable "subscription_id" {
  type      = string
  sensitive = true
}
variable "tenant_id" {
  type      = string
  sensitive = true
}
variable "owner_ipv4" {
  type      = string
  sensitive = true
  validation {
    condition     = can(cidrnetmask("${var.owner_ipv4}/32")) && var.owner_ipv4 != "0.0.0.0"
    error_message = "A single owner IPv4 is required."
  }
}
variable "budget_email" {
  type      = string
  sensitive = true
  validation {
    condition     = can(regex("^[^@ ]+@[^@ ]+\\.[^@ ]+$", var.budget_email))
    error_message = "An alert recipient email is required."
  }
}
variable "budget_start_date" {
  type        = string
  description = "First UTC day of the deployment month, fixed after creation."
}
variable "budget_usd_to_billing_rate" {
  type        = number
  default     = 1
  description = "Documented reference conversion; refresh monthly if billing currency is not USD."
  validation {
    condition     = var.budget_usd_to_billing_rate > 0
    error_message = "A positive currency conversion is required."
  }
}
variable "budget_currency" {
  type        = string
  default     = "USD"
  description = "Expected billing currency for readback; Azure determines the budget currency."
}
variable "image_tag" {
  type        = string
  description = "Full verified origin/main Git commit SHA."
  validation {
    condition     = can(regex("^[a-f0-9]{40}$", var.image_tag))
    error_message = "Use the full main commit SHA."
  }
}
variable "deploy_apps" {
  type        = bool
  default     = false
  description = "Enable only after images are pushed and the database app role is initialized."
}

variable "enable_real_llm" {
  type        = bool
  default     = false
  description = "Owner-approved production OpenRouter route; local default remains mock."
}

variable "enable_submission_warm" {
  type        = bool
  default     = false
  description = "OFF while testing. Enable only with Sebastian's submission-day cost/plan approval."
}

variable "min_replicas" {
  type        = number
  default     = 0
  description = "Both existing apps: 0 while testing, 1 only for the approved sharing window."
  validation {
    condition     = contains([0, 1], var.min_replicas) && (var.min_replicas == 0 || var.enable_submission_warm)
    error_message = "Only 0/1 replicas; 1 requires the separately approved submission warm switch."
  }
}

variable "enable_judge_access" {
  type        = bool
  default     = false
  description = "OFF by default. Public HTTPS web with login and a separate KV judge account; API stays internal. Requires Sebastian approval."
  validation {
    condition     = !var.enable_judge_access || (var.deploy_apps && var.llm_budget_run_id == "")
    error_message = "Judge mode requires deployed apps and normal durable USD 3/day accounting, never a smoke run."
  }
}

variable "llm_budget_run_id" {
  type        = string
  default     = ""
  description = "Optional owner-created cumulative smoke budget in Postgres, in addition to USD 3/day."
  validation {
    condition     = contains(["", "handoff09-smoke", "jev-support-smoke", "option-a-release-smoke", "after-v2-release-smoke"], var.llm_budget_run_id) || can(regex("^pre-v4-(release|latency)-[a-f0-9]{40}$", var.llm_budget_run_id))
    error_message = "Only the approved smoke budget or normal daily accounting is supported."
  }
}

locals {
  location = "eastus2"
  suffix   = "aclara-dev-eastus2"
  tags     = { project = "aclara", environment = "dev", data = "synthetic", managed_by = "terraform" }
}
