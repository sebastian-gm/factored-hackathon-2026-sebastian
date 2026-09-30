// Presentation labels only. The server supplies facts, authority and reason IDs.
// Exact meanings from brief §9 and conversation-policy-v3 §3; never route here.
export function handoffReasonLabelKey(reason: string): string {
  const labels: Record<string, string> = {
    "AUTH-01": "reasonSession",
    "AUTH-02": "reasonStepUp",
    "AUTH-03": "reasonOwnership",
    "SCOPE-01": "reasonScope",
    "DATA-01": "reasonData",
    "TXN-01": "reasonRecentHold",
    "TXN-02": "reasonStaleHold",
    "TXN-03": "reasonReversed",
    "TXN-04": "reasonDeclined",
    "DSP-01": "reasonWindow",
    "DSP-02": "reasonIntake",
    "DSP-03": "reasonAdjustment",
    "DSP-04": "reasonTransfer",
    "DSP-05": "reasonAccount",
    "DSP-06": "reasonExistingCase",
    "DSP-07": "reasonAmount",
    "BRD-01": "reasonBorderline",
    "FRD-01": "reasonFraud",
    "ESC-01": "reasonHuman",
    "ESC-02": "reasonLegal",
    "ESC-03": "reasonDistress",
    "ESC-04": "reasonClarification",
    "ESC-05": "reasonComplaints",
    "SEC-01": "reasonSecurity",
    "COM-01": "reasonReadback",
  };
  return labels[reason] ?? "reasonOther";
}
export function deskActionLabelKey(action: string, verified = true): string {
  if (!verified) {
    const attempts: Record<string, string> = {
      create_handoff: "actionHandoffAttempt",
      create_dispute: "actionDisputeAttempt",
      freeze_card: "actionFreezeAttempt",
    };
    return attempts[action] ?? "actionOther";
  }
  const labels: Record<string, string> = {
    create_handoff: "actionHandoff",
    create_dispute: "actionDispute",
    freeze_card: "actionFreeze",
    verify_handoff: "actionVerifyHandoff",
    verify_dispute: "actionVerifyDispute",
    verify_card: "actionVerifyCard",
    log_security_event: "actionSecurity",
    end_session: "actionEndSession",
  };
  return labels[action] ?? "actionOther";
}
export function ruleLabelKey(rule: string): string {
  const labels: Record<string, string> = {
    AUTH: "ruleIdentity",
    TXN: "ruleTransaction",
    DSP: "ruleDispute",
    FRD: "ruleRisk",
    SEC: "ruleSecurity",
    ESC: "ruleHuman",
    COM: "ruleReadback",
  };
  return labels[rule.split("-")[0]] ?? "ruleService";
}
export function queueLabelKey(queue: string): string {
  const labels: Record<string, string> = {
    Fraudes: "teamFraud",
    "Quejas y Reclamos": "teamComplaints",
    "Atención General": "teamGeneral",
  };
  return labels[queue] ?? "humanTeam";
}
export function personaLabelKey(username: string): string | null {
  const labels: Record<string, string> = {
    "demo.es.mx": "personaMX",
    "demo.es.co": "personaCO",
    "demo.es.ar": "personaAR",
    "demo.pt.br": "personaBR",
    "demo.fraud": "personaFraud",
    "demo.agent": "personaAgent",
    "demo.ops": "personaOps",
  };
  return labels[username] ?? null;
}

export function cardTypeLabelKey(productType: string): string {
  const value = productType.toLowerCase();
  if (value.includes("credit")) return "cardCredit";
  if (value.includes("debit")) return "cardDebit";
  return "cardType";
}
