import { z } from "zod";

// Allowlisted API projection, including ADR-0015's accepted additive offer/primary-reason fields.
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
  status: z.string(),
  review_flag: z.boolean().optional(),
  policy_rules: z.array(z.string()),
  created_at: z.string(),
});
export const handoffSchema = z.object({
  schema_version: z.literal("1.0"),
  handoff_id: z.string(),
  created_at: z.string(),
  reason_codes: z.array(z.string()),
  primary_reason: z.string().min(1).nullish(),
  priority: z.enum(["normal", "high"]),
  route: z.object({
    queue: z.string(),
    language: z.enum(["es", "pt"]),
    fallback_used: z.boolean(),
    assignment_pending: z.boolean().optional(),
    specialty_fallback: z.boolean().optional(),
    language_fallback: z.boolean().optional(),
  }),
  verified_facts: z.array(transactionSchema),
  actions_taken: z.array(z.string()),
  open_questions: z.array(z.string()),
  freeze_outcome: z.string().nullish(),
});
export const productSchema = z.object({
  handle: z.string().regex(/^[\w-]{1,80}$/),
  product_type: z.string(),
  status: z.string(),
});
export const cardSchema = z.object({
  handle: z.string(),
  status: z.string(),
  verified: z.literal(true),
});
export const freezeProposalSchema = z.object({
  response_type: z.literal("confirm_action"),
  action: z.literal("freeze_card"),
  handle: z.string(),
  handoff_id: z.string(),
  conversation_id: z.string(),
  proposal_hash: z.string().regex(/^[a-f0-9]{64}$/),
  expires_at: z.string(),
  reply: z.string(),
});
export type Product = z.infer<typeof productSchema>;
export type FreezeProposal = z.infer<typeof freezeProposalSchema>;
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
      "report_status",
      "refuse",
      "offer_dispute",
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
      "status_reported",
      "refused_security",
      "awaiting_dispute_decision",
    ]),
    reply: z.string(),
    candidates: z.array(transactionSchema).nullish(),
    transaction: transactionSchema.nullish(),
    proposal: proposalSchema.nullish(),
    case: caseSchema.nullish(),
    handoff: handoffSchema.nullish(),
    policy_rules: z.array(z.string()).nullish(),
    verified: z.boolean().nullish(),
    session_ended: z.boolean().optional(),
    freeze_offer: z.array(productSchema).nullish(),
    card: cardSchema.nullish(),
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
    if (["report_case", "report_status"].includes(plan.response_type))
      needs(plan.case, "case");
    if (plan.response_type === "offer_human") needs(plan.handoff, "handoff");
    if (plan.response_type === "choose_transaction")
      needs(plan.candidates?.length, "candidates");
    if (
      plan.response_type === "offer_dispute" ||
      plan.outcome === "awaiting_dispute_decision"
    ) {
      needs(plan.response_type === "offer_dispute", "response_type");
      needs(plan.outcome === "awaiting_dispute_decision", "outcome");
      needs(plan.transaction, "transaction");
      // Recognition is a conversation turn, never an action proposal or receipt.
      needs(!plan.proposal && !plan.case && !plan.handoff, "nonterminal_offer");
      needs(
        !plan.session_ended && !plan.freeze_offer?.length,
        "nonterminal_offer",
      );
    }
    if (plan.outcome === "cancelled") {
      needs(plan.response_type === "cancelled", "response_type");
      needs(!plan.proposal && !plan.case, "cancelled_action");
    }
    if (plan.handoff?.primary_reason)
      needs(
        plan.handoff.reason_codes.includes(plan.handoff.primary_reason),
        "primary_reason",
      );
  });
export type Transaction = z.infer<typeof transactionSchema>;
export type Plan = z.infer<typeof planSchema>;
export type Handoff = z.infer<typeof handoffSchema>;
export function orderedReasons(
  packet: Pick<Handoff, "reason_codes" | "primary_reason">,
): string[] {
  const reasons = [...new Set(packet.reason_codes)];
  return packet.primary_reason && reasons.includes(packet.primary_reason)
    ? [
        packet.primary_reason,
        ...reasons.filter((reason) => reason !== packet.primary_reason),
      ]
    : reasons;
}
export type Role = "customer" | "agent" | "ops";
export type Locale = "es-MX" | "es-CO" | "es-AR" | "pt-BR";
export type Surface = "chat" | "desk" | "ops" | "insights";
export type Session = {
  username: string;
  role: Role;
  language: "es" | "pt";
  locale?: Locale;
  bank_clock?: string;
};
export type Config = {
  fixtures: boolean;
  resetEnabled?: boolean;
  bankClock: string | null;
  personas: {
    username: string;
    label: string;
    role: Role;
    locale: Locale;
    demo_stories?: ("explain" | "ambiguous" | "fraud")[];
  }[];
};

// Proposed extensions: feature-flagged fixtures ONLY until the lead adds contracts.
export type DeskPacket = Handoff & {
  conversation_id: string | null;
  version?: number;
  verified?: boolean;
  risk_flags?: string[] | null;
  suggested_next_steps?: string[] | null;
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
export type TraceEvent = import("./trace").TraceEvent;
export type OpsSnapshot = {
  source_kind?: "authored_fixture" | "organizer_serving";
  dataset_version: string;
  bank_clock: string;
  quality: { name: string; passed: boolean; checked: number }[];
  freshness: {
    built_at: string;
    source_as_of: string;
    status: "fresh" | "stale" | "unknown";
  };
  conversations: { id: string; events: TraceEvent[] }[];
  daily_cost: { date: string; usd: number }[];
  metrics?: import("./staff-contracts").WorkspaceMetrics;
  results: {
    source: string;
    kind: string;
    cases: number;
    passed: number;
    unsafe: number;
    cost_usd: number | null;
    human_validated: boolean;
  } | null;
};
