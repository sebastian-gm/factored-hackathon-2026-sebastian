// Presentation labels only. The server supplies facts, authority and reason IDs.
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
