// New UI-only response fixtures. No organizer records or evaluation suites are used.
import { planSchema, type Transaction } from "../../src/lib/contracts";
import { deskSchema } from "../../src/lib/staff-contracts";

export function offerFixture(pt: boolean) {
  const transaction: Transaction = {
    handle: "txn_ui_papeleria",
    merchant: pt ? "Papelaria Prisma" : "Papelería Prisma",
    amount: 64.25,
    currency: "USD",
    transaction_date: "2026-06-12T16:30:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  };
  return planSchema.parse({
    response_type: "offer_dispute",
    outcome: "awaiting_dispute_decision",
    reply: pt
      ? "Confira os dados desta compra. Você se lembra dela ou quer pedir uma contestação?"
      : "Revisa los datos de esta compra. ¿La recuerdas o quieres solicitar una disputa?",
    transaction,
  });
}

export function proposalFixture(pt: boolean) {
  return planSchema.parse({
    response_type: "confirm_action",
    outcome: "dispute_proposed",
    reply: pt
      ? "Revise a proposta antes de confirmar."
      : "Revisa la propuesta antes de confirmar.",
    transaction: offerFixture(pt).transaction,
    proposal: {
      action: "create_dispute",
      proposal_hash: "a".repeat(64),
      expires_at: new Date(Date.now() + 120000).toISOString(),
      policy_rules: ["AUTH-02"],
    },
  });
}

export const multiReasonPacket = deskSchema.parse({
  schema_version: "1.0",
  handoff_id: "HO-UI-MULTI",
  conversation_id: "CONV-UI-MULTI",
  created_at: "2026-06-18T06:00:00Z",
  reason_codes: ["AUTH-02", "ESC-02", "FRD-01"],
  primary_reason: "FRD-01",
  priority: "high",
  route: { queue: "Fraudes", language: "es", fallback_used: false },
  verified_facts: [],
  actions_taken: ["create_handoff"],
  open_questions: ["Confirmar qué ayuda necesita la persona."],
  freeze_outcome: "declined",
  customer_display: "Persona de prueba UI",
  sla_due_at: "2026-06-18T12:00:00Z",
  status: "waiting",
  claimed_by: null,
  version: 1,
  verified: true,
  scope: "current_workspace",
  evidence: [],
  actions: [
    {
      action: "create_handoff",
      status: "verified",
      evidence_ref: "UI-HANDOFF-READBACK",
    },
  ],
});
