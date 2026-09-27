import { z } from "zod";

// Exact typed projection of the frozen OpenAPI. Extensions live separately below.
export const transactionSchema = z.object({
  handle: z.string(),
  transaction_date: z.string(),
  transaction_type: z.string(),
  amount: z.number().nonnegative(),
  currency: z.string(),
  merchant: z.string().nullable(),
  status: z.string(),
});
export const proposalSchema = z.object({
  action: z.literal("create_dispute"),
  proposal_hash: z.string().regex(/^[a-f0-9]{64}$/),
  expires_at: z.string(),
  policy_rules: z.array(z.string()),
});
export const caseSchema = z.object({
  case_id: z.string(),
  transaction_handle: z.string(),
  status: z.literal("received"),
  policy_rules: z.array(z.string()),
  created_at: z.string(),
});
export const handoffSchema = z.object({
  schema_version: z.literal("1.0"),
  handoff_id: z.string(),
  created_at: z.string(),
  reason_codes: z.array(z.string()),
  priority: z.enum(["normal", "high"]),
  route: z.object({
    queue: z.string(),
    language: z.enum(["es", "pt"]),
    fallback_used: z.boolean(),
  }),
  verified_facts: z.array(transactionSchema),
  actions_taken: z.array(z.string()),
  open_questions: z.array(z.string()),
});
export const planSchema = z
  .object({
    response_type: z.enum([
      "cancelled",
      "offer_human",
      "abstain",
      "choose_transaction",
      "clarify",
      "report_case",
      "confirm_action",
      "explain_status",
    ]),
    outcome: z.enum([
      "cancelled",
      "handoff_created",
      "abstained_out_of_scope",
      "choose_transaction",
      "clarification",
      "dispute_filed",
      "dispute_proposed",
      "explained",
    ]),
    reply: z.string(),
    candidates: z.array(transactionSchema).nullish(),
    transaction: transactionSchema.nullish(),
    proposal: proposalSchema.nullish(),
    case: caseSchema.nullish(),
    handoff: handoffSchema.nullish(),
    policy_rules: z.array(z.string()).nullish(),
    verified: z.boolean().nullish(),
  })
  .superRefine((plan, ctx) => {
    const needs = (ok: unknown, field: string) => {
      if (!ok)
        ctx.addIssue({
          code: "custom",
          message: `Missing ${field}`,
          path: [field],
        });
    };
    if (plan.response_type === "confirm_action") {
      needs(plan.proposal, "proposal");
      needs(plan.transaction, "transaction");
    }
    if (plan.response_type === "report_case") needs(plan.case, "case");
    if (plan.response_type === "offer_human") needs(plan.handoff, "handoff");
    if (plan.response_type === "choose_transaction")
      needs(plan.candidates?.length, "candidates");
  });
export type Transaction = z.infer<typeof transactionSchema>;
export type Plan = z.infer<typeof planSchema>;
export type Handoff = z.infer<typeof handoffSchema>;
export type Role = "customer" | "agent" | "ops";
export type Locale = "es-MX" | "es-CO" | "es-AR" | "pt-BR";
export type Surface = "chat" | "desk" | "ops";
export type Session = { username: string; role: Role; language: "es" | "pt" };
export type Config = {
  fixtures: boolean;
  bankClock: string | null;
  personas: { username: string; label: string; role: Role; locale: Locale }[];
};

// Proposed extensions: feature-flagged fixtures ONLY until the lead adds contracts.
export type DeskPacket = Handoff & {
  conversation_id: string;
  customer_display: string;
  sla_due_at: string;
  status: "waiting" | "claimed" | "resolved";
  claimed_by: string | null;
  evidence: {
    id: string;
    record_ref: string;
    tool: string;
    verified_at: string;
    dataset_version: string;
  }[];
  actions: {
    action: string;
    status: "verified" | "failed";
    evidence_ref: string;
  }[];
};
export type TraceEvent = {
  id: string;
  stage: "Understand" | "Decide" | "Act" | "Verify" | "Escalate";
  state: string;
  tool: string | null;
  rules: string[];
  verified: boolean;
  llm: {
    provider: string;
    model: string;
    prompt_version: string;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    latency_ms: number;
  } | null;
};
export type OpsSnapshot = {
  dataset_version: string;
  bank_clock: string;
  quality: { name: string; passed: boolean; checked: number }[];
  freshness: {
    built_at: string;
    source_as_of: string;
    status: "fresh" | "stale";
  };
  conversations: { id: string; events: TraceEvent[] }[];
  daily_cost: { date: string; usd: number }[];
  results: {
    source: string;
    kind: string;
    cases: number;
    passed: number;
    unsafe: number;
    cost_usd: number;
    human_validated: boolean;
  };
};
