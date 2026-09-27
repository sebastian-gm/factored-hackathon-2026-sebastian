import { z } from "zod";
import { handoffSchema } from "./contracts";

export const personaSchema = z.object({
  username: z.string(),
  label: z.string(),
  role: z.enum(["customer", "agent", "ops"]),
  locale: z.enum(["es-MX", "es-CO", "es-AR", "pt-BR"]),
});
export const identitySchema = personaSchema.omit({ label: true }).extend({
  language: z.enum(["es", "pt"]),
  bank_clock: z.string(),
});
export const deskSchema = handoffSchema.extend({
  conversation_id: z.string().nullable(),
  customer_display: z.string(),
  sla_due_at: z.string(),
  status: z.enum(["waiting", "claimed", "resolved"]),
  claimed_by: z.string().nullable(),
  version: z.number().int().positive(),
  verified: z.literal(true),
  scope: z.literal("current_workspace"),
  evidence: z.array(
    z.object({
      id: z.string(),
      record_ref: z.string(),
      tool: z.string(),
      verified_at: z.string(),
      dataset_version: z.string(),
    }),
  ),
  actions: z.array(
    z.object({
      action: z.string(),
      status: z.enum(["verified", "failed"]),
      evidence_ref: z.string(),
    }),
  ),
  risk_flags: z.array(z.string()).nullish(),
  suggested_next_steps: z.array(z.string()).nullish(),
});
export const traceSchema = z.object({
  conversation_id: z.string(),
  policy_version: z.string(),
  scope: z.literal("current_workspace"),
  events: z.array(
    z.object({
      id: z.string(),
      stage: z.enum(["Understand", "Decide", "Act", "Verify", "Escalate"]),
      state: z.string(),
      tool: z.string().nullable(),
      rules: z.array(z.string()),
      verified: z.boolean(),
      llm: z
        .object({
          provider: z.string(),
          model: z.string(),
          prompt_version: z.string(),
          input_tokens: z.number().int().nonnegative(),
          output_tokens: z.number().int().nonnegative(),
          cost_usd: z.number().nonnegative().nullable(),
          latency_ms: z.number().nonnegative(),
        })
        .nullable(),
    }),
  ),
});
export const metricsSchema = z.object({
  source: z.literal("current_workspace_operations"),
  cases: z.number().int().nonnegative(),
  handoffs: z.number().int().nonnegative(),
  conversations: z.number().int().nonnegative(),
  execution_records: z.number().int().nonnegative(),
  observed_model_cost_usd: z.number().nonnegative(),
  sar: z.null(),
  unsafe_rate: z.null(),
  note: z.string(),
});
export const opsSchema = z.object({
  dataset_version: z.string(),
  bank_clock: z.string(),
  loaded_at: z.string(),
  source_as_of: z.string(),
  source_kind: z.literal("authored_fixture"),
  scope: z.literal("current_workspace"),
  quality: z.array(
    z.object({
      name: z.string(),
      passed: z.boolean(),
      checked: z.number().int().nonnegative(),
    }),
  ),
  metrics: metricsSchema,
  conversation_ids: z.array(z.string()),
});
export const resetProposalSchema = z.object({
  action: z.literal("reset_current_workspace"),
  proposal_hash: z.string().regex(/^[a-f0-9]{64}$/),
  expires_at: z.string(),
  scope: z.literal("current_workspace_operations_except_audit_auth"),
});
export const resetReceiptSchema = z.object({
  receipt_id: z.string().regex(/^[a-f0-9]{64}$/),
  reset: z.boolean(),
  verified: z.literal(true),
  remaining_operations: z.number().int().nonnegative(),
  audit_retained: z.literal(true),
});
export type LiveOps = z.infer<typeof opsSchema>;
export type Trace = z.infer<typeof traceSchema>;
export type ResetProposal = z.infer<typeof resetProposalSchema>;
export type WorkspaceMetrics = z.infer<typeof metricsSchema>;
